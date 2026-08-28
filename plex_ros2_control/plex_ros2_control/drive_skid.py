import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from std_msgs.msg import Float64MultiArray
from dataclasses import dataclass

@dataclass
class Wheel:
    name: str
    is_right: bool


WHEELS = [
    Wheel(name="front_left", is_right=False),
    Wheel(name="front_right", is_right=True),
    Wheel(name="mid_left", is_right=False),
    Wheel(name="mid_right", is_right=True),
    Wheel(name="back_left", is_right=False),
    Wheel(name="back_right", is_right=True),
]
WHEEL_RADIUS_M = 0.0889


THROTTLE_AXIS = 1
THROTTLE_DEADBAND_PCT = 0.015 # under this % throttle, consider 0

STEER_AXIS = 3
STEER_DEADBAND_PCT = 0.05 # under this % steer either side, consider 0
STEER_POWER = 1.0 # float (0,1] controlling how powerfully to steer while moving

FORWARD_BUTTON = 2
REVERSE_BUTTON = 3
IN_PLACE_STEER_BUTTON = 4

MAX_SPEED = 2.0 # m/s at full throttle
MAX_SPEED_IN_PLACE_STEER = 0.5 # how fast the wheels move (m/s) at max deflection during in-place steering

SAFETY_TIMEOUT = 1.5 # after this many seconds of no joy update, stop
RATE_HZ = 50

def remap_range(value: float, old_range: tuple, new_range: tuple, clip_output: bool = True):
    """Remap value from (old_range[0], old_range[1]) to (new_range[0], new_range[1])"""
    out = new_range[0] + (value - old_range[0]) * (new_range[1] - new_range[0]) / (old_range[1] - old_range[0])
    if clip_output:
        out = max(out, min(new_range[0], new_range[1]))
        out = min(out, max(new_range[0], new_range[1]))
    return out

def speed_to_radial_speed(speed_m_s: float):
    return speed_m_s / WHEEL_RADIUS_M

class SkidDrive(Node):
    def __init__(self):
        super().__init__("skid_drive")

        self.last_joy_time = None

        self.drive_pub = self.create_publisher(Float64MultiArray, "/drive_velocity_controller/commands", 10)
        self.create_subscription(Joy, "/joy_drive", self.joy_callback, 10)

        self.create_timer(1.0 / RATE_HZ, self.check_timeout)

        self.last_mode = ""
        self.safety_stop: bool = False

    def joy_callback(self, msg: Joy):
        self.last_joy_time = self.get_clock().now()
        self.safety_stop = False
        in_place_steer = msg.buttons[IN_PLACE_STEER_BUTTON]

        throttle_pct = remap_range(msg.axes[THROTTLE_AXIS], (1, -1), (0, 1))
        throttle_pct = 0 if throttle_pct < THROTTLE_DEADBAND_PCT else throttle_pct

        steer_left_desire = remap_range(msg.axes[STEER_AXIS], (0, 1), (0, 1))
        steer_left_desire = 0 if steer_left_desire < STEER_DEADBAND_PCT else steer_left_desire
        steer_right_desire = remap_range(msg.axes[STEER_AXIS], (0, -1), (0, 1))
        steer_right_desire = 0 if steer_right_desire < STEER_DEADBAND_PCT else steer_right_desire

        if in_place_steer:
            if not self.last_mode == "in-place steer":
                self.get_logger().info("Switching to In-place steering")
            self.last_mode = "in-place steer"

            right_relative_desire = steer_right_desire - steer_left_desire
            right_relative_rad_s_desire = speed_to_radial_speed(right_relative_desire * MAX_SPEED_IN_PLACE_STEER)
            self.send_in_place_steering(right_relative_rad_s_desire)

        else:
            if not self.last_mode == "drive":
                self.get_logger().info("Switching to Drive Mode")
            self.last_mode = "drive"

            right_wheel_multiplier = remap_range(steer_right_desire, (0, 1), (1, (1-STEER_POWER)))
            left_wheel_multiplier = remap_range(steer_left_desire, (0, 1), (1, (1-STEER_POWER)))
            rad_per_sec_desired = remap_range(throttle_pct, (0, 1), (0, speed_to_radial_speed(MAX_SPEED)))

            # controlled by the forward/reverse.
            forward_backward_throttle_mult = 0
            go_forward = msg.buttons[FORWARD_BUTTON]
            go_backward = msg.buttons[REVERSE_BUTTON]

            if (go_forward and not go_backward):
                forward_backward_throttle_mult = 1.0
            if (go_backward and not go_forward):
                forward_backward_throttle_mult = -1.0
            
            rad_per_sec_desired *= forward_backward_throttle_mult
            self.send_drive_mode_commands(rad_per_sec_desired, left_wheel_multiplier, right_wheel_multiplier)

    

    def send_drive_mode_commands(self, base_rad_s: float, left_mult: float, right_mult:float):
        motor_command = []
        for i, wheel in enumerate(WHEELS):
            wheel_command = base_rad_s
            if wheel.is_right:
                wheel_command *= right_mult
            else:
                wheel_command *= left_mult
            motor_command.append(wheel_command)
        message = Float64MultiArray()
        message.data = motor_command
        self.drive_pub.publish(message)

    def send_in_place_steering(self, right_forward_rad_s: float):
        """Send in-place steering command, driven by how much forward the right wheels should go"""
        motor_command = []
        for i, wheel in enumerate(WHEELS):
            if wheel.is_right:
                motor_command.append(right_forward_rad_s)
            else:
                motor_command.append(-1 * right_forward_rad_s)
        message = Float64MultiArray()
        message.data = motor_command
        self.drive_pub.publish(message)



    def check_timeout(self):
        if self.last_joy_time is None:
            return
        now = self.get_clock().now()
        if (now - self.last_joy_time).nanoseconds / 1e9 > SAFETY_TIMEOUT:
            if not self.safety_stop:
                self.get_logger().warning(f"No update for >= {SAFETY_TIMEOUT} seconds, stopping!")
                self.safety_stop = True
            stop_drive = Float64MultiArray()
            stop_drive.data = [0.0]*len(WHEELS)
            self.drive_pub.publish(stop_drive)

    
def main(args=None):
    rclpy.init(args=args)
    node = SkidDrive()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()