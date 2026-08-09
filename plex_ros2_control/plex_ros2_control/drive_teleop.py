import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from std_msgs.msg import Float64MultiArray


class DriveTeleop(Node):
    def __init__(self):
        super().__init__('drive_teleop')

        self.joy_sub = self.create_subscription(
            Joy, '/joy_arm', self.joy_cb, 10)

        self.drive_pub = self.create_publisher(
            Float64MultiArray, '/steer_velocity_controller/commands', 10)

        self.multiplier = 2.0

    def joy_cb(self, msg):
        if len(msg.axes) < 4:
            self.get_logger().warn('Joy message has too few axes; ignoring.')
            return
        self.pub_drive_cmds(msg)

    def pub_drive_cmds(self, msg):
        cmd = Float64MultiArray()
        cmd.data = [msg.axes[1] * self.multiplier]
        self.drive_pub.publish(cmd)

def main():
    rclpy.init()
    node = DriveTeleop()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()