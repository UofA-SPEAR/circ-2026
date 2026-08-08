from rclpy.node import Node
from sensor_msgs.msg import Joy
from geometry_msgs.msg import TwistStamped
from std_msgs.msg import Float64MultiArray



class drive_teleop(Node):
    def __init__(self):
        super.__init__('drive_teleop')
        self.joy_sub = self.create_subscription(Joy, '/joy', self.joy_cb, 10)
        self.pub = self.create_publisher(TwistStamped, '/velocity_controller/commands', 10)
        self.multiplier = 10
    
    def joy_cb(self, msg):
        self.pub_twist_cmds(msg)

    def pub_drive_cmds(self, msg):
        mult = self.multiplier

        cmd = Float64MultiArray
        cmd.data = [msg.axes[1]*mult]*6
        self.pub(cmd)

    def pub_steering_cmds(self, msg):
        mult = self.multiplier

        cmd = Float64MultiArray
        cmd.data = [msg.axes[3]*mult]*2
        self.pub(cmd)



    def main():
        rclpy.init()
        rclpy.spin(drive_teleop())

if __name__ == '__main__':
    main()









import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from std_msgs.msg import Float64MultiArray


class JoyToVelocity(Node):
    def __init__(self):
        super().__init__('joy_to_velocity')
        self.pub = self.create_publisher(Float64MultiArray, 'current_controller/commands', 10)
        # self.pub = self.create_publisher(Float64MultiArray, 'velocity_controller/commands', 10)
        self.create_subscription(Joy, 'joy', self.joy_cb, 10)

    def joy_cb(self, msg):
        cmd = Float64MultiArray()
        cmd.data = [msg.axes[0]*1000] * 3
        self.pub.publish(cmd)


def main():
    rclpy.init()
    rclpy.spin(JoyToVelocity())
    rclpy.shutdown()


if __name__ == '__main__':
    main()