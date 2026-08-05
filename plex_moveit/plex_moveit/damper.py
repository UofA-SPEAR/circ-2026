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
        max_dv = self.max_accel * dt

        dv = min(-max_dv, min(dv, max_dv))
        self.x_vel_current += dv

        out = TwistStamped
        out.header.frame_id = msg.header.frame_id
        
        out.twist.linear.x = self.x_vel_current
        out.twist.linear.y = msg.twist.linear.y
        out.twist.linear.z = msg.twist.linear.z
        out.twist.angular.z = msg.twist.angular.x
        out.twist.angular.y = msg.twist.angular.y
        out.twist.angular.z = msg.twist.angular.z

        return out

   
def main():
       rclpy.init()
       rclpy.spin(damper())

if __name__ == '__main__':
    main()