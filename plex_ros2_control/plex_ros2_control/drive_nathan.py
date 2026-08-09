#!/usr/bin/env python3
"""
Kipp rover drive node (ros2_control version).

Single node: reads the drone-style transmitter on /manual/joy and publishes
joint commands to two forward command controllers.

    /drive_controller/commands     std_msgs/Float64MultiArray  (6 x rad/s)
    /steering_controller/commands  std_msgs/Float64MultiArray  (4 x rad)

Joint ordering (must match the `joints:` list in your controller YAML):
    drive:    [front_left, middle_left, back_left, front_right, middle_right, back_right]
    steering: [front_left, back_left, front_right, back_right]

Transmitter mapping:
    axes[1]     throttle, +1 idle -> -1 full, no return-to-center
    axes[3]     steering, -1 -> +1
    buttons[2]  forward   (held, from a 3-position switch)
    buttons[3]  reverse   (held, mutually exclusive with buttons[2])
    buttons[4]  in-place steering (held)

Geometry is precomputed at startup into a lookup table over omega. Both the
corner angles and the per-wheel speed ratios depend only on omega, never on
throttle, so the whole turn geometry can be baked once and the control loop
reduces to a table index plus a multiply.

Commands are sent RAW -- no right-side inversion, no steering sign flips.
Flip the INVERT_* constants below if the URDF axes turn out mirrored.
"""

import math
from dataclasses import dataclass
from typing import Tuple

import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import ReentrantCallbackGroup

from sensor_msgs.msg import Joy
from std_msgs.msg import Float64MultiArray

# --- Chassis geometry ---------------------------------------------------------

TRACK_WIDTH = 0.4191     # T, left wheels to right wheels (m)
LEN_FRONT = 0.3937       # L1, middle axle to front axle (m)
LEN_BACK = 0.3937      # L2, middle axle to back axle (m)
WHEEL_RADIUS = 0.176    # m, converts m/s -> rad/s

HALF_TRACK = TRACK_WIDTH / 2.0


@dataclass(frozen=True)
class Wheel:
    """A wheel's position in the body frame: x forward, y left, origin at the
    middle axle centre."""
    key: str
    x: float
    y: float
    steered: bool


# Order here IS the drive controller command order. Do not reorder without
# also changing the `joints:` list in the controller YAML.
WHEELS: Tuple[Wheel, ...] = (
    Wheel("front_left",    LEN_FRONT,  HALF_TRACK, True),
    Wheel("middle_left",   0.0,        HALF_TRACK, False),
    Wheel("back_left",    -LEN_BACK,   HALF_TRACK, True),
    Wheel("front_right",   LEN_FRONT, -HALF_TRACK, True),
    Wheel("middle_right",  0.0,       -HALF_TRACK, False),
    Wheel("back_right",   -LEN_BACK,  -HALF_TRACK, True),
)

# Order here IS the steering controller command order.
STEERED_WHEELS: Tuple[Wheel, ...] = (
    WHEELS[0],  # front_left
    WHEELS[2],  # back_left
    WHEELS[3],  # front_right
    WHEELS[5],  # back_right
)

# In-place steering angles are DERIVED from the chassis geometry (see
# build_point_turn_geometry) as the r -> 0 limit of the same turn solver.
# Set this to a dict keyed by wheel name to override the derived values with
# empirically measured ones -- e.g. if real toe, kingpin offset, or module
# zero errors mean the geometric ideal is not what actually stops the scrub.
POINT_TURN_ANGLE_OVERRIDE = None

# The values that shipped on the old CAN node, kept for reference. These are
# ~4-5 degrees shy of the derived geometry and are not consistent with any
# single track width, which suggests they were hand-tuned rather than solved.
LEGACY_ROTATE_ANGLES = {
    "front_left": -0.880,
    "front_right": 0.880,
    "back_left": 1.035,
    "back_right": -1.035,
}

# --- Tunables -----------------------------------------------------------------

PUBLISH_RATE = 50.0         # Hz
VELOCITY_LIMIT = 0.5        # m/s, cap applied to the FASTEST wheel

# Steering geometry is deliberately independent of throttle. This is the
# reference speed the turn radius is derived from: r = REFERENCE_SPEED / omega.
# Changing it rescales how sharply a given stick deflection turns.
REFERENCE_SPEED = 1.0

# Hard floor on turn radius. Guards the r - y term against crossing zero (which
# would flip an inner wheel's angle discontinuously) if max_angular_speed is
# ever raised. Must stay comfortably above HALF_TRACK.
MIN_TURN_RADIUS = 0.60

MAX_ANGULAR_SPEED = 1.0     # rad/s at full steering stick

# Lookup table resolution over the omega range. 401 entries across +/-1.0 rad/s
# gives 0.005 rad/s steps, far finer than the stick or the modules resolve.
LUT_STEPS = 401

# Raw axes[1] values at the two ends of throttle travel. Normalized to 0..1
# internally, so swapping these two numbers flips the axis direction.
THROTTLE_RAW_IDLE = 1.0     # stick position meaning "no throttle"
THROTTLE_RAW_FULL = -1.0    # stick position meaning "full throttle"

THROTTLE_DEADBAND = 0.02    # ignore normalized throttle below this
STEERING_DEADBAND = 0.05    # ignore steering stick below this

# Seconds to hold the drive wheels at zero while the corner modules swing
# between Ackermann and point-turn geometry. Set to 0.0 to disable.
MODE_SETTLE_TIME = 0.5

# Flip these if the URDF joint axes are mirrored on one side.
INVERT_RIGHT_DRIVE = False
INVERT_STEERING = False

# Joy indices
AXIS_THROTTLE = 1
AXIS_STEERING = 3
BUTTON_FORWARD = 2
BUTTON_REVERSE = 3
BUTTON_INPLACE = 4


@dataclass(frozen=True)
class TurnGeometry:
    """Precomputed geometry for one omega. `ratios` are per-wheel multipliers
    on the rover centre speed, aligned to WHEELS. `angles` are radians, aligned
    to STEERED_WHEELS. `max_ratio` is the largest ratio, used to scale the
    command so the fastest wheel -- not the average -- respects the limit."""
    angles: Tuple[float, ...]
    ratios: Tuple[float, ...]
    max_ratio: float


def clamp(value, low, high):
    return max(low, min(high, value))


def build_turn_geometry(omega: float) -> TurnGeometry:
    """
    Solve the corner angles and wheel speed ratios for one turn rate.

    Both come off the SAME circle: turning centre at (0, r) with
    r = REFERENCE_SPEED / omega. Each steered wheel is aimed so its axle line
    passes through that centre, and each wheel's speed ratio is its distance
    from that centre over the rover centre's distance. That consistency is the
    whole point -- steering and drive must describe one arc, not two.
    """
    if abs(omega) < 1e-6:
        # Straight ahead: no steering, every wheel at rover speed.
        return TurnGeometry(
            angles=tuple(0.0 for _ in STEERED_WHEELS),
            ratios=tuple(1.0 for _ in WHEELS),
            max_ratio=1.0,
        )

    r = REFERENCE_SPEED / omega
    if abs(r) < MIN_TURN_RADIUS:
        r = math.copysign(MIN_TURN_RADIUS, r)

    # atan (not atan2) keeps every angle inside (-pi/2, pi/2); the sign of
    # (r - y) carries the left/right sense correctly on its own.
    angles = tuple(math.atan(w.x / (r - w.y)) for w in STEERED_WHEELS)

    ratios = tuple(
        math.sqrt(w.x * w.x + (w.y - r) ** 2) / abs(r) for w in WHEELS
    )

    return TurnGeometry(angles=angles, ratios=ratios, max_ratio=max(ratios))


def build_point_turn_geometry() -> TurnGeometry:
    """
    Solve in-place steering as the r -> 0 limit of build_turn_geometry: the
    turning centre collapses onto the body origin.

    Each wheel must be tangent to a circle about the origin, so its heading is
    atan(x / -y), and its speed scales with its distance from the origin,
    sqrt(x^2 + y^2). Corners toe inwards; the middle wheels sit at x = 0, so
    their tangent is dead ahead -- which is exactly why they can be unsteered.

    Ratios are normalized against the FURTHEST wheel, so max_ratio is 1.0 and
    a commanded speed of VELOCITY_LIMIT puts the fastest wheel on the limit.
    """
    if POINT_TURN_ANGLE_OVERRIDE is not None:
        angles = tuple(POINT_TURN_ANGLE_OVERRIDE[w.key] for w in STEERED_WHEELS)
    else:
        angles = tuple(math.atan(w.x / -w.y) for w in STEERED_WHEELS)

    radii = tuple(math.hypot(w.x, w.y) for w in WHEELS)
    furthest = max(radii)
    ratios = tuple(d / furthest for d in radii)

    return TurnGeometry(angles=angles, ratios=ratios, max_ratio=1.0)


class KippDriveController(Node):
    def __init__(self):
        super().__init__("kipp_drive_controller")

        self.callback_group = ReentrantCallbackGroup()

        # Full throttle maps to exactly VELOCITY_LIMIT so the top of the stick
        # travel does something instead of saturating against the clamp.
        self.max_linear_speed = VELOCITY_LIMIT
        self.max_angular_speed = MAX_ANGULAR_SPEED

        # --- Precomputed geometry ---
        self._lut = tuple(
            build_turn_geometry(
                -self.max_angular_speed
                + 2.0 * self.max_angular_speed * i / (LUT_STEPS - 1)
            )
            for i in range(LUT_STEPS)
        )
        self._point_turn = build_point_turn_geometry()
        self._zero_drive = tuple(0.0 for _ in WHEELS)
        self._zero_steer = tuple(0.0 for _ in STEERED_WHEELS)
        self._right_mask = tuple(w.y < 0 for w in WHEELS)

        # Command state, written by joy_callback, read by paced_commands
        self.throttle = 0.0
        self.steering = 0.0
        self.direction = 0      # +1 forward, -1 reverse, 0 neutral
        self.rotate = False

        # Mode-transition state
        self.prev_rotate = False
        self.mode_change_time = None

        self.joy_sub = self.create_subscription(
            Joy, "/joy_drive", self.joy_callback, 10,
            callback_group=self.callback_group,
        )
        self.drive_pub = self.create_publisher(
            Float64MultiArray, "/drive_velocity_controller/commands", 10,
            callback_group=self.callback_group,
        )
        self.steering_pub = self.create_publisher(
            Float64MultiArray, "/steer_position_controller/commands", 10,
            callback_group=self.callback_group,
        )

        self.timer = self.create_timer(
            1.0 / PUBLISH_RATE, self.paced_commands,
            callback_group=self.callback_group,
        )

        # Publish zeros once after discovery settles so the controllers do not
        # start on a stale command from a previous run.
        self._startup_timer = self.create_timer(
            1.0, self._publish_startup_zeros, callback_group=self.callback_group
        )

        self.get_logger().info(
            "kipp_drive_controller up at %.0f Hz, %d turn geometries precomputed"
            % (PUBLISH_RATE, LUT_STEPS)
        )

    # --- Startup ------------------------------------------------------------

    def _publish_startup_zeros(self):
        self.publish_drive(self._zero_drive)
        self.publish_steering(self._zero_steer)
        self._startup_timer.cancel()

    # --- Input --------------------------------------------------------------

    def joy_callback(self, msg):
        # Throttle has no return-to-center, so it holds whatever the operator
        # last set it to. Map raw axis onto 0..1 via the configured travel ends.
        span = THROTTLE_RAW_FULL - THROTTLE_RAW_IDLE
        throttle = (msg.axes[AXIS_THROTTLE] - THROTTLE_RAW_IDLE) / span
        throttle = clamp(throttle, 0.0, 1.0)
        self.throttle = 0.0 if throttle < THROTTLE_DEADBAND else throttle

        steering = msg.axes[AXIS_STEERING]
        self.steering = 0.0 if abs(steering) < STEERING_DEADBAND else steering

        # 3-position switch. The two buttons are mutually exclusive, but guard
        # against both reading high (bad frame, switch bounce) by treating that
        # as neutral rather than picking one.
        forward = bool(msg.buttons[BUTTON_FORWARD])
        reverse = bool(msg.buttons[BUTTON_REVERSE])
        if forward and not reverse:
            self.direction = 1
        elif reverse and not forward:
            self.direction = -1
        else:
            self.direction = 0

        rotate = bool(msg.buttons[BUTTON_INPLACE])
        if rotate != self.prev_rotate:
            self.mode_change_time = self.get_clock().now()
            self.prev_rotate = rotate
        self.rotate = rotate

    # --- Main loop ----------------------------------------------------------

    def paced_commands(self):
        if self.rotate:
            angles = self._point_turn.angles
            speeds = self.rotate_velocities()
        else:
            geom = self.lookup_geometry(-self.steering * self.max_angular_speed)
            angles = geom.angles
            speeds = self.drive_velocities(geom)

        # While the corner modules slew between geometries, hold the drive
        # wheels still. Steering keeps publishing so the modules get there;
        # only the drive command is suppressed.
        if self.in_mode_transition():
            speeds = self._zero_drive

        self.publish_steering(angles)
        self.publish_drive(speeds)

    def lookup_geometry(self, omega) -> TurnGeometry:
        omega = clamp(omega, -self.max_angular_speed, self.max_angular_speed)
        frac = (omega + self.max_angular_speed) / (2.0 * self.max_angular_speed)
        return self._lut[int(round(frac * (LUT_STEPS - 1)))]

    def in_mode_transition(self):
        if MODE_SETTLE_TIME <= 0.0 or self.mode_change_time is None:
            return False
        elapsed = (self.get_clock().now() - self.mode_change_time).nanoseconds / 1e9
        if elapsed >= MODE_SETTLE_TIME:
            self.mode_change_time = None
            return False
        return True

    # --- Velocity resolution ------------------------------------------------

    def drive_velocities(self, geom: TurnGeometry):
        """
        Wheel speeds in m/s for normal driving.

        Neutral switch means no drive at all regardless of stick or throttle --
        the wheels still steer, they just do not roll.

        The limit is applied to the fastest wheel rather than to the rover
        centre, so the outer wheels can never be commanded past VELOCITY_LIMIT
        on a tight arc.
        """
        if self.direction == 0:
            return self._zero_drive

        v = self.direction * self.throttle * self.max_linear_speed
        v = clamp(v, -VELOCITY_LIMIT / geom.max_ratio,
                  VELOCITY_LIMIT / geom.max_ratio)
        return tuple(v * ratio for ratio in geom.ratios)

    def rotate_velocities(self):
        """
        Wheel speeds for in-place steering, corners toed inwards.

        Each wheel sits at a different distance from the body origin -- back
        corners furthest, middle wheels closest -- so their speeds must differ
        in the same proportion or they fight each other. Magnitude comes from
        the throttle, spin direction from the steering stick. The forward and
        reverse switch has no meaningful sense for a point turn, so it acts as
        an arming interlock: neutral means no spin.
        """
        if self.direction == 0 or self.steering == 0.0:
            return self._zero_drive

        speed = clamp(self.throttle * self.max_linear_speed,
                      -VELOCITY_LIMIT, VELOCITY_LIMIT)
        spin = math.copysign(speed, -self.steering)
        return tuple(
            (spin if right else -spin) * ratio
            for right, ratio in zip(self._right_mask, self._point_turn.ratios)
        )

    # --- Publishing ---------------------------------------------------------

    def publish_drive(self, speeds):
        """speeds: m/s per wheel, aligned to WHEELS."""
        data = []
        for value, is_right in zip(speeds, self._right_mask):
            omega_wheel = value / WHEEL_RADIUS
            if INVERT_RIGHT_DRIVE and is_right:
                omega_wheel = -omega_wheel
            data.append(float(omega_wheel))
        msg = Float64MultiArray()
        msg.data = data
        self.drive_pub.publish(msg)

    def publish_steering(self, angles):
        """angles: radians per corner, aligned to STEERED_WHEELS."""
        sign = -1.0 if INVERT_STEERING else 1.0
        msg = Float64MultiArray()
        msg.data = [float(sign * a) for a in angles]
        self.steering_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = KippDriveController()
    executor = MultiThreadedExecutor()
    try:
        rclpy.spin(node, executor=executor)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()