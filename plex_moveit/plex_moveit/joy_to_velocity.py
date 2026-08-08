import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from std_msgs.msg import Float64MultiArray


class JoyToVelocity(Node):
    def __init__(self):
        super().__init__('joy_to_velocity')
        # self.pub = self.create_publisher(Float64MultiArray, 'current_controller/commands', 10)
        self.pub = self.create_publisher(Float64MultiArray, 'velocity_controller/commands', 10)
        self.create_subscription(Joy, 'joy', self.joy_cb, 10)

    def joy_cb(self, msg):
        cmd = Float64MultiArray()
        cmd.data = [msg.axes[0]*10] * 3
        self.pub.publish(cmd)


def main():
    rclpy.init()
    rclpy.spin(JoyToVelocity())
    rclpy.shutdown()


if __name__ == '__main__':
    main()