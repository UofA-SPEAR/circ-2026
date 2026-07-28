import sys
import termios
import tty
import select

import rclpy
from rclpy.node import Node
from control_msgs.msg import JointJog


# Each key maps to (joint_index, direction). Press once -> one jog command.
# q/a, w/s, e/d, r/f, t/g, y/h  give +/- for joints 1-6.
KEY_BINDINGS = {
    'q': (0, 1.0),  'a': (0, -1.0),   # joint_1
    'w': (1, 1.0),  's': (1, -1.0),   # joint_2
    'e': (2, 1.0),  'd': (2, -1.0),   # joint_3
    'r': (3, 1.0),  'f': (3, -1.0),   # joint_4
    't': (4, 1.0),  'g': (4, -1.0),   # joint_5
    'y': (5, 1.0),  'h': (5, -1.0),   # joint_6
}

JOINT_NAMES = ['joint_1', 'joint_2', 'joint_3', 'joint_4', 'joint_5', 'joint_6']

INSTRUCTIONS = """
Keyboard joint jog teleop
--------------------------
  q/a : joint_1 +/-
  w/s : joint_2 +/-
  e/d : joint_3 +/-
  r/f : joint_4 +/-
  t/g : joint_5 +/-
  y/h : joint_6 +/-

  x   : quit

Each keypress publishes ONE JointJog message (velocity = +/-0.5)
on /servo_node/delta_joint_cmds, then immediately zeroes out.
--------------------------
"""


def get_key(settings, timeout=0.1):
    """Non-blocking single character read from stdin."""
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], timeout)
    if rlist:
        key = sys.stdin.read(1)
    else:
        key = ''
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key


class KeyboardToServo(Node):
    def __init__(self):
        super().__init__('keyboard_to_servo')
        self.joint_pub = self.create_publisher(JointJog, '/servo_node/delta_joint_cmds', 10)
        self.speed = 0.5  # rad/s-ish jog velocity, tune as needed

    def publish_joint_cmd(self, joint_index, direction):
        velocities = [0.0] * 6
        velocities[joint_index] = direction * self.speed

        joint_cmd = JointJog()
        joint_cmd.header.stamp = self.get_clock().now().to_msg()
        joint_cmd.header.frame_id = 'base_link'
        joint_cmd.joint_names = JOINT_NAMES
        joint_cmd.velocities = velocities

        self.joint_pub.publish(joint_cmd)
        self.get_logger().info(
            f'{JOINT_NAMES[joint_index]}: {velocities[joint_index]:+.2f}'
        )


def main():
    settings = termios.tcgetattr(sys.stdin)

    rclpy.init()
    node = KeyboardToServo()

    print(INSTRUCTIONS)

    try:
        while rclpy.ok():
            key = get_key(settings)

            if key == 'x':
                break

            if key in KEY_BINDINGS:
                joint_index, direction = KEY_BINDINGS[key]
                node.publish_joint_cmd(joint_index, direction)

            rclpy.spin_once(node, timeout_sec=0.0)

    except Exception as e:
        print(e)

    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()