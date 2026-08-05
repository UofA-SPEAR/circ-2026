import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TwistStamped


class damper(Node):
    def __init__(self):
        super().__init__('damper')
        self.pad_sub = self.create_subscription(TwistStamped, '/gamepad_to_servo/twist_raw', self.pad_cb, 10)
        self.limited_pub = self.create_publisher(TwistStamped, '/servo_node/delta_twist_cmds', 10)

        self.max_accel = 0.5 # units: rad/s^2
        self.x_vel_current = 0.0
        self.last_time = None


    def pad_cb(self, msg):
        now = self.get_clock().now()

        if self.last_time is None:
            # First message: nothing to compare against yet, just accept it
            dt = 0.0
        else:
            dt = (now - self.last_time).nanoseconds / 1e9 # extract duration object as an integer and convert to seconds

        self.last_time = now

        limited_twist = self.accel_limiter(msg, dt)
        self.limited_pub.publish(limited_twist)

    def accel_limiter(self, msg, dt):
        x_vel_target = msg.twist.linear.x
        dv = x_vel_target - self.x_vel_current

        self.x_vel_current += dv

        max_dv = min()


        








   
def main():
       rclpy.init()
       rclpy.spin(damper())

if __name__ == '__main__':
    main()