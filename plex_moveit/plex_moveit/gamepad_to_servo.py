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
        self.joint_mode = True
        self.last_button_press = None

    def joy_cb(self, msg):
        # Toggle mode with a button press, e.g. Y button (index 3 on Xbox)
        # Toggles between direct EE manipulation and single joint manipulation
        if msg.buttons[3] and not self.last_button_press:  # <---------------------------  May or may not be mapped to [3]. YOu should check this
            self.joint_mode = not self.joint_mode
            self.get_logger().info(f'Joint mode = {self.joint_mode}')

        if self.joint_mode:
            self.publish_joint_cmds(msg)
        else:
            self.publish_twist_cmds(msg)

        self.last_button_press = msg.buttons[3]

# We use this to move each joint individually

    def publish_joint_cmds(self, msg):
        joint_cmd = JointJog()
        joint_cmd.header.stamp = self.get_clock().now().to_msg()
        joint_cmd.header.frame_id = 'base_link'

        # Map each stick axis to a joint
        joint_cmd.joint_names = ['joint_1', 'joint_2', 'joint_3', 'joint_4', 'joint_5', 'joint_6']
        joint_cmd.velocities = [
            msg.axes[0],   # left stick left/right → joint_1
            msg.axes[1],   # left stick up/down  → joint_2
            msg.axes[4],   # right stick up/down → joint_3
            msg.axes[3],   # right stick left/right → joint_4
            (msg.buttons[4] - msg.buttons[5])*0.5,   # bumpers → joint_5
            (msg.axes[2] - msg.axes[5])*0.5,   # triggers → joint_6
        ]

        self.joint_pub.publish(joint_cmd)

# If we want to move the end effector to a point in space, we use this

    def publish_twist_cmds(self, msg):
        twist = TwistStamped()
        twist.header.stamp = self.get_clock().now().to_msg()
        twist.header.frame_id = "base_link"

        # Using the analog sticks for Cartesian control: left stick for linear, right stick for angular
        twist.twist.linear.x = msg.axes[1]*0.02  # forward-backward
        twist.twist.linear.y = msg.axes[0]*0.02   # left-right
        twist.twist.linear.z = (msg.axes[2] - msg.axes[5])*0.02   # up-down 


        twist.twist.angular.x = msg.axes[3]*0.02
        twist.twist.angular.y = msg.axes[4]*0.02 
        twist.twist.angular.z = ((msg.buttons[4] - msg.buttons[5])*0.5)*0.02 
        
    
        #twist.twist.linear.z = msg.axes[0] #forward-backward
        #twist.twist.angular.z = (msg.axes[2] - msg.axes[5])*0.5 #rotation
        # Do we add rotation right now or should we wait?

        self.twist_pub.publish(twist)

def main():
    rclpy.init()
    rclpy.spin(gamepad_to_servo())

