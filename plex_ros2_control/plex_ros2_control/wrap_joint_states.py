"""Publish continuous arm joint positions in MoveIt's canonical angle range."""

import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


def wrap_to_pi(angle: float) -> float:
    """Return an equivalent angle in [-pi, pi]."""
    return math.atan2(math.sin(angle), math.cos(angle))


class JointStateWrapper(Node):
    """Wrap selected joint positions without changing hardware feedback."""

    def __init__(self) -> None:
        super().__init__('joint_state_wrapper')

        self.declare_parameter(
            'continuous_joints',
            [f'joint_{index}' for index in range(1, 7)],
        )
        self.declare_parameter('input_topic', '/jsb/joint_states')
        self.declare_parameter('output_topic', '/joint_states')

        self._continuous_joints = set(
            self.get_parameter('continuous_joints').value
        )
        input_topic = self.get_parameter('input_topic').value
        output_topic = self.get_parameter('output_topic').value

        if input_topic == output_topic:
            raise ValueError('input_topic and output_topic must be different')

        self._publisher = self.create_publisher(
            JointState,
            output_topic,
            10,
        )
        self._subscription = self.create_subscription(
            JointState,
            input_topic,
            self._joint_state_callback,
            10,
        )

        self.get_logger().info(
            f'Wrapping {sorted(self._continuous_joints)} from '
            f'{input_topic} to {output_topic}'
        )

    def _joint_state_callback(self, message: JointState) -> None:
        wrapped = JointState()
        wrapped.header = message.header
        wrapped.name = list(message.name)
        wrapped.position = list(message.position)
        wrapped.velocity = list(message.velocity)
        wrapped.effort = list(message.effort)

        for index, joint_name in enumerate(wrapped.name):
            is_continuous = joint_name in self._continuous_joints
            if is_continuous and index < len(wrapped.position):
                wrapped.position[index] = wrap_to_pi(wrapped.position[index])

        self._publisher.publish(wrapped)


def main(args=None) -> None:
    """Run the joint-state wrapping node."""
    rclpy.init(args=args)
    node = JointStateWrapper()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
