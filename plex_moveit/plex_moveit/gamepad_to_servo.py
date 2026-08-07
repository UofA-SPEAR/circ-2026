from ast import For
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from geometry_msgs.msg import TwistStamped
from control_msgs.msg import JointJog

class gamepad_to_servo(Node):
    def __init__(self):
        super().__init__('gamepad_to_servo')
        self.joy_sub = self.create_subscription(Joy, '/joy', self.joy_cb, 10)
        self.twist_pub = self.create_publisher(TwistStamped, '/servo_node/delta_twist_cmds', 10)
        self.joint_pub = self.create_publisher(JointJog, '/servo_node/delta_joint_cmds', 10)
        # self.joint_pub = self.create_publisher(TwistStamped, '/pad_chatter', 10)
        self.joint_mode = True
        self.last_button_press = None

        # Sensitivity cycling
        self.sens_levels = [0.0125, 0.05, 0.10, 0.15, 0.20, 0.25]
        self.sens_idx = 0
        self.sens = self.sens_levels[self.sens_idx]
        self.last_sens_button_press = None  # separate edge-detect state from mode toggle
        self.last_dpad_vertical = 0.0  # edge-detect state for up/down

    def joy_cb(self, msg):
        # Toggle mode with a button press, e.g. Y button (index 3 on Xbox)
        if msg.buttons[3] and not self.last_button_press:
            self.joint_mode = not self.joint_mode
            self.get_logger().info(f'Joint mode = {self.joint_mode}')
        self.last_button_press = msg.buttons[3]

        # Cycle sensitivity with A button (index 0)
        if msg.buttons[0] and not self.last_sens_button_press:
            self.sens_idx = (self.sens_idx + 1) % len(self.sens_levels)
            self.sens = self.sens_levels[self.sens_idx]
            self.get_logger().info(f'Sensitivity = {self.sens}')
        self.last_sens_button_press = msg.buttons[0]

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

        if self.joint_mode:
            self.publish_joint_cmds(msg)
        else:
            self.publish_twist_cmds(msg)

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
    
    
        #twist.twist.linear.z = msg.axes[0] #forward-backward
        #twist.twist.angular.z = (msg.axes[2] - msg.axes[5])*0.5 #rotation
        # Do we add rotation right now or should we wait?

        self.twist_pub.publish(twist)

def main():
    rclpy.init()
    rclpy.spin(gamepad_to_servo())

