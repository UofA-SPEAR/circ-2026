#!/usr/bin/env python3
"""
plex_drive — joystick to Ackermann-style rover drive.

Reads /joy_drive, converts throttle/steer/direction-switch into per-wheel
steer angles and wheel speeds using an instantaneous-center-of-rotation
(ICR) model, and publishes those to the steer and drive controllers.

Every turn is treated as a circle: pick a point off to one side (the ICR),
aim each steered wheel tangent to the circle through that point, and spin
each wheel at a speed proportional to its distance from that point.
"""

import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from std_msgs.msg import Float64MultiArray


# ---------------------------------------------------------------------------
# EDIT ME: wheel order must match the `joints:` list in your controller YAML
# ---------------------------------------------------------------------------
WHEELS = [
    "front_left",
    "front_right",
    "mid_left",
    "mid_right",
    "back_left",
    "back_right",
]

STEERED_WHEELS = [
    "front_right",
    "front_left",
]

# ---------------------------------------------------------------------------
# EDIT ME: rover geometry (metres)
# ---------------------------------------------------------------------------
WHEELBASE_WIDTH = 0.4191   # left-to-right distance between wheels (track width)
MID_FRONT_DIST = 0.3937    # distance from middle axle to front axle
BACK_MID_DIST = 0.3937     # distance from back axle to middle axle
WHEEL_RADIUS = 0.167      # metres, used to convert m/s -> rad/s

# Wheel positions in the robot frame: x = forward, y = left.
# Middle axle is the origin along x.
WHEEL_POS = {
    "front_left":  (MID_FRONT_DIST, WHEELBASE_WIDTH / 2.0),
    "front_right": (MID_FRONT_DIST, -WHEELBASE_WIDTH / 2.0),
    "mid_left":    (0.0, WHEELBASE_WIDTH / 2.0),
    "mid_right":   (0.0, -WHEELBASE_WIDTH / 2.0),
    "back_left":   (-BACK_MID_DIST, WHEELBASE_WIDTH / 2.0),
    "back_right":  (-BACK_MID_DIST, -WHEELBASE_WIDTH / 2.0),
}

# ---------------------------------------------------------------------------
# EDIT ME: joystick mapping / tuning
# ---------------------------------------------------------------------------
THROTTLE_AXIS = 1
STEER_AXIS = 3
FORWARD_BUTTON = 2
REVERSE_BUTTON = 3

MAX_SPEED = 1.0          # m/s at full throttle
MIN_TURN_RADIUS = 0.5    # metres, radius at full steering deflection
STEER_DEADZONE = 0.02    # ignore tiny stick noise -> straight line
STEER_SIGN = -1           # flip to -1 if right-stick turns the rover left
THROTTLE_DEADZONE = 0.05 # treat throttle within this of -1 as exactly -1

JOY_TIMEOUT = 1.0         # seconds
RATE_HZ = 50.0


class PlexDrive(Node):

    def __init__(self):
        super().__init__("plex_drive")

        self.last_joy = None
        self.last_joy_time = None

        self.steer_pub = self.create_publisher(
            Float64MultiArray, "/steer_position_controller/commands", 10)
        self.drive_pub = self.create_publisher(
            Float64MultiArray, "/drive_velocity_controller/commands", 10)

        self.create_subscription(Joy, "/joy_drive", self.joy_callback, 10)

        self.create_timer(1.0 / RATE_HZ, self.update)

    def joy_callback(self, msg: Joy):
        self.last_joy = msg
        self.last_joy_time = self.get_clock().now()

    def update(self):
        timed_out = (
            self.last_joy is None
            or (self.get_clock().now() - self.last_joy_time).nanoseconds * 1e-9 > JOY_TIMEOUT
        )

        if timed_out:
            self.publish_stop()
            return

        joy = self.last_joy

        # --- direction from the 3-position switch ---
        forward = joy.buttons[FORWARD_BUTTON] if len(joy.buttons) > FORWARD_BUTTON else 0
        reverse = joy.buttons[REVERSE_BUTTON] if len(joy.buttons) > REVERSE_BUTTON else 0
        if forward and not reverse:
            direction = 1.0
        elif reverse and not forward:
            direction = -1.0
        else:
            direction = 0.0  # neutral -> no motion regardless of throttle

        # --- magnitude from throttle, sign from switch ---
        # Throttle stick doesn't spring back: -1 = zero, +1 = full.
        throttle = joy.axes[THROTTLE_AXIS] if len(joy.axes) > THROTTLE_AXIS else -1.0
        throttle = max(-1.0, min(1.0, throttle))          # clamp calibration overshoot
        if throttle < -1.0 + THROTTLE_DEADZONE:
            throttle = -1.0                                # snap near-rest to exactly zero
        throttle_norm = (throttle - 1.0) / -2.0             # -1..1 -> 0..1
        speed = throttle_norm * MAX_SPEED * direction

        # --- steering stick -> curvature (1 / turn radius) ---
        steer = joy.axes[STEER_AXIS] if len(joy.axes) > STEER_AXIS else 0.0
        if abs(steer) < STEER_DEADZONE:
            steer = 0.0
        # curvature, signed: positive = turn right, negative = turn left.
        # Using curvature instead of radius keeps this well-behaved through
        # zero (radius = 1/curvature would blow up at the deadzone).
        curvature = STEER_SIGN * steer / MIN_TURN_RADIUS

        angles = {}
        speeds = {}

        for name in WHEELS:
            x, y = WHEEL_POS[name]
            tangent_x = 1.0 - y * curvature
            tangent_y = curvature * x
            ratio = math.hypot(tangent_x, tangent_y)  # -> 1.0 when curvature == 0

            if name in STEERED_WHEELS:
                angles[name] = math.atan2(tangent_y, tangent_x)

            speeds[name] = speed * ratio

        self.publish(angles, speeds)

    def publish(self, angles, speeds):
        steer_msg = Float64MultiArray()
        steer_msg.data = [angles.get(name, 0.0) for name in STEERED_WHEELS]
        self.steer_pub.publish(steer_msg)

        drive_msg = Float64MultiArray()
        drive_msg.data = [speeds[name] / WHEEL_RADIUS for name in WHEELS]
        self.drive_pub.publish(drive_msg)

    def publish_stop(self):
        steer_msg = Float64MultiArray()
        steer_msg.data = [0.0 for _ in STEERED_WHEELS]
        self.steer_pub.publish(steer_msg)

        drive_msg = Float64MultiArray()
        drive_msg.data = [0.0 for _ in WHEELS]
        self.drive_pub.publish(drive_msg)


def main(args=None):
    rclpy.init(args=args)
    node = PlexDrive()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()