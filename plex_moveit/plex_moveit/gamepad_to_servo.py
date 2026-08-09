import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from geometry_msgs.msg import TwistStamped
from control_msgs.msg import JointJog
from std_msgs.msg import Float64MultiArray


class gamepad_to_servo(Node):
    def __init__(self):
        super().__init__('gamepad_to_servo')
        self.joy_sub = self.create_subscription(Joy, '/joy_arm', self.joy_cb, 10)
        # self.twist_pub = self.create_publisher(TwistStamped, '/gamepad_to_servo/twist_raw', 10)
        self.twist_pub = self.create_publisher(TwistStamped, '/servo_node/delta_twist_cmds', 10)
        self.joint_pub = self.create_publisher(JointJog, '/servo_node/delta_joint_cmds', 10)
        self.gripper_pub = self.create_publisher(
            Float64MultiArray, '/gripper_current_controller/commands', 10)
        self.joint_mode = True
        self.last_button_press = None

        # Sensitivity cycling
        self.sens_levels = [0.0125, 0.05, 0.10, 0.15, 0.20, 0.25]
        self.sens_idx = 0
        self.sens = self.sens_levels[self.sens_idx]
        self.last_sens_button_press = None  # separate edge-detect state from mode toggle
        self.last_dpad_vertical = 0.0  # edge-detect state for up/down

        # Gripper current control (all values in mA)
        self.grip_step = 50.0          # mA per d-pad press
        self.grip_limit = 1000.0       # hard clamp on accumulator and output
        self.grip_squeeze = -800.0      # A button
        self.grip_release = 800.0     # B button
        self.grip_accum = 0.0
        self.last_dpad_horizontal = 0.0  # edge-detect state for left/right
        self.last_b_button = 0           # edge-detect state for B

    def joy_cb(self, msg):
        # Toggle mode with a button press, e.g. Y button (index 3 on Xbox)
        if msg.buttons[3] and not self.last_button_press:
            self.joint_mode = not self.joint_mode
            self.get_logger().info(f'Joint mode = {self.joint_mode}')
        self.last_button_press = msg.buttons[3]

        # D-pad up/down cycles sensitivity
        dpad_vertical = msg.axes[7]
        if dpad_vertical == 1.0 and self.last_dpad_vertical != 1.0:
            self.sens_idx = min(self.sens_idx + 1, len(self.sens_levels) - 1)
            self.sens = self.sens_levels[self.sens_idx]
            self.get_logger().info(f'Sensitivity = {self.sens}')
        elif dpad_vertical == -1.0 and self.last_dpad_vertical != -1.0:
            self.sens_idx = max(self.sens_idx - 1, 0)
            self.sens = self.sens_levels[self.sens_idx]
            self.get_logger().info(f'Sensitivity = {self.sens}')
        self.last_dpad_vertical = dpad_vertical

        self.publish_gripper_cmd(msg)

        if self.joint_mode:
            self.publish_joint_cmds(msg)
        else:
            self.publish_twist_cmds(msg)

# Gripper is current-controlled only, so we just stream a single mA value

    def publish_gripper_cmd(self, msg):
        # D-pad left/right steps the accumulator, one step per press (edge detected)
        dpad_horizontal = msg.axes[6]
        if dpad_horizontal == 1.0 and self.last_dpad_horizontal != 1.0:
            self.grip_accum = min(self.grip_accum + self.grip_step, self.grip_limit)
            self.get_logger().info(f'Gripper accumulator = {self.grip_accum} mA')
        elif dpad_horizontal == -1.0 and self.last_dpad_horizontal != -1.0:
            self.grip_accum = max(self.grip_accum - self.grip_step, -self.grip_limit)
            self.get_logger().info(f'Gripper accumulator = {self.grip_accum} mA')
        self.last_dpad_horizontal = dpad_horizontal

        # B zeroes the accumulator on the press edge, then holds -800 mA while down
        if msg.buttons[1] and not self.last_b_button:
            self.grip_accum = 0.0
            self.get_logger().info('Gripper accumulator reset')
        self.last_b_button = msg.buttons[1]

        # While-held overrides. B wins over A if both are down.
        if msg.buttons[1]:
            current = self.grip_release
        elif msg.buttons[0]:
            current = min(self.grip_accum, self.grip_squeeze)
        else:
            current = self.grip_accum

        current = max(-self.grip_limit, min(self.grip_limit, current))

        grip_cmd = Float64MultiArray()
        grip_cmd.data = [float(current)]
        self.gripper_pub.publish(grip_cmd)

# We use this to move each joint individually

    def publish_joint_cmds(self, msg):
        joint_cmd = JointJog()
        joint_cmd.header.stamp = self.get_clock().now().to_msg()
        joint_cmd.header.frame_id = 'base_link'

        # Map each stick axis to a joint
        joint_cmd.joint_names = ['joint_1', 'joint_2', 'joint_3', 'joint_4', 'joint_5', 'joint_6']
        joint_cmd.velocities = [
            msg.axes[0]*self.sens*2,   # left stick left/right → joint_1
            msg.axes[1]*self.sens*2,   # left stick up/down  → joint_2
            msg.axes[4]*self.sens*2,   # right stick up/down → joint_3
            msg.axes[3]*self.sens*2,   # right stick left/right → joint_4
            (msg.buttons[4] - msg.buttons[5])*0.5*self.sens*2,   # bumpers → joint_5
            (msg.axes[2] - msg.axes[5])*0.5*self.sens*2,   # triggers → joint_6
        ]

        self.joint_pub.publish(joint_cmd)

# If we want to move the end effector to a point in space, we use this

    def publish_twist_cmds(self, msg):
        twist = TwistStamped()
        twist.header.stamp = self.get_clock().now().to_msg()
        twist.header.frame_id = "Link_6"

        # Using the analog sticks for Cartesian control: left stick for linear, right stick for angular
        twist.twist.linear.z = msg.axes[1]*self.sens  # forward-backward
        twist.twist.linear.y = msg.axes[0]*self.sens   # left-right
        twist.twist.linear.x = ((msg.axes[2] - msg.axes[5])/2)*self.sens   # up-down

        twist.twist.angular.x = ((msg.buttons[4] - msg.buttons[5]))*self.sens*2*-1
        twist.twist.angular.y = -msg.axes[4]*self.sens*2
        twist.twist.angular.z = msg.axes[3]*self.sens*2

        self.twist_pub.publish(twist)


def main():
    rclpy.init()
    rclpy.spin(gamepad_to_servo())