"""Fail-safe gamepad adapter for MoveIt Servo."""

import time

from control_msgs.msg import JointJog
from geometry_msgs.msg import TwistStamped
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy

from .teleop_safety import (
    axis_value,
    button_pressed,
    joint_velocities,
    twist_components,
)


JOINT_NAMES = [f"joint_{index}" for index in range(1, 7)]


class GamepadToServo(Node):
    """Publish commands only while a deadman button and Joy heartbeat exist."""

    def __init__(self) -> None:
        super().__init__("gamepad_to_servo")

        self.declare_parameter("deadman_button", 6)
        self.declare_parameter("mode_button", 3)
        self.declare_parameter("sensitivity_button", 0)
        self.declare_parameter("dpad_vertical_axis", 7)
        self.declare_parameter("joy_timeout_sec", 0.30)
        self.declare_parameter("deadzone", 0.08)
        self.declare_parameter("command_frame", "Link_6")

        self._deadman_button = int(
            self.get_parameter("deadman_button").value
        )
        self._mode_button = int(self.get_parameter("mode_button").value)
        self._sensitivity_button = int(
            self.get_parameter("sensitivity_button").value
        )
        self._dpad_axis = int(
            self.get_parameter("dpad_vertical_axis").value
        )
        self._joy_timeout_sec = max(
            0.10,
            float(self.get_parameter("joy_timeout_sec").value),
        )
        self._deadzone = max(
            0.0,
            min(0.5, float(self.get_parameter("deadzone").value)),
        )
        self._command_frame = str(
            self.get_parameter("command_frame").value
        )

        self._joint_mode = True
        self._sensitivity_levels = [0.0125, 0.025, 0.05, 0.075, 0.10]
        self._sensitivity_index = 0
        self._last_mode_button = False
        self._last_sensitivity_button = False
        self._last_dpad = 0.0
        self._last_joy_time = None
        self._motion_enabled = False

        self._twist_publisher = self.create_publisher(
            TwistStamped,
            "/servo_node/delta_twist_cmds",
            10,
        )
        self._joint_publisher = self.create_publisher(
            JointJog,
            "/servo_node/delta_joint_cmds",
            10,
        )
        self._joy_subscription = self.create_subscription(
            Joy,
            "/joy",
            self._joy_callback,
            10,
        )
        self._watchdog_timer = self.create_timer(0.05, self._watchdog)

        self.get_logger().info(
            "Arm teleop disarmed; hold Joy button "
            f"{self._deadman_button} to command motion"
        )

    @property
    def _sensitivity(self) -> float:
        return self._sensitivity_levels[self._sensitivity_index]

    def _joy_callback(self, message: Joy) -> None:
        self._last_joy_time = time.monotonic()
        deadman = button_pressed(message.buttons, self._deadman_button)

        mode_pressed = button_pressed(message.buttons, self._mode_button)
        if mode_pressed and not self._last_mode_button:
            self._publish_stop()
            self._joint_mode = not self._joint_mode
            mode = "joint" if self._joint_mode else "Cartesian"
            self.get_logger().info(f"Arm command mode: {mode}")
        self._last_mode_button = mode_pressed

        sensitivity_pressed = button_pressed(
            message.buttons,
            self._sensitivity_button,
        )
        if sensitivity_pressed and not self._last_sensitivity_button:
            self._sensitivity_index = (
                self._sensitivity_index + 1
            ) % len(self._sensitivity_levels)
            self.get_logger().info(
                f"Arm sensitivity: {self._sensitivity:.4f}"
            )
        self._last_sensitivity_button = sensitivity_pressed

        dpad = axis_value(message.axes, self._dpad_axis, 0.5)
        if dpad > 0.5 and self._last_dpad <= 0.5:
            self._sensitivity_index = min(
                self._sensitivity_index + 1,
                len(self._sensitivity_levels) - 1,
            )
        elif dpad < -0.5 and self._last_dpad >= -0.5:
            self._sensitivity_index = max(self._sensitivity_index - 1, 0)
        self._last_dpad = dpad

        if not deadman:
            if self._motion_enabled:
                self.get_logger().info("Arm teleop disarmed")
            self._publish_stop()
            self._motion_enabled = False
            return

        if not self._motion_enabled:
            self.get_logger().info("Arm teleop armed")
        self._motion_enabled = True
        if self._joint_mode:
            self._publish_joint_command(message)
        else:
            self._publish_twist_command(message)

    def _publish_joint_command(self, message: Joy) -> None:
        command = JointJog()
        command.header.stamp = self.get_clock().now().to_msg()
        command.header.frame_id = "base_link"
        command.joint_names = JOINT_NAMES
        command.velocities = list(
            joint_velocities(
                message.axes,
                message.buttons,
                self._sensitivity,
                self._deadzone,
            )
        )
        self._joint_publisher.publish(command)

    def _publish_twist_command(self, message: Joy) -> None:
        linear, angular = twist_components(
            message.axes,
            message.buttons,
            self._sensitivity,
            self._deadzone,
        )
        command = TwistStamped()
        command.header.stamp = self.get_clock().now().to_msg()
        command.header.frame_id = self._command_frame
        command.twist.linear.x, command.twist.linear.y = linear[:2]
        command.twist.linear.z = linear[2]
        command.twist.angular.x, command.twist.angular.y = angular[:2]
        command.twist.angular.z = angular[2]
        self._twist_publisher.publish(command)

    def _publish_stop(self) -> None:
        now = self.get_clock().now().to_msg()
        joint_command = JointJog()
        joint_command.header.stamp = now
        joint_command.header.frame_id = "base_link"
        joint_command.joint_names = JOINT_NAMES
        joint_command.velocities = [0.0] * len(JOINT_NAMES)
        self._joint_publisher.publish(joint_command)

        twist_command = TwistStamped()
        twist_command.header.stamp = now
        twist_command.header.frame_id = self._command_frame
        self._twist_publisher.publish(twist_command)

    def _watchdog(self) -> None:
        if self._last_joy_time is None:
            return
        if time.monotonic() - self._last_joy_time <= self._joy_timeout_sec:
            return
        if self._motion_enabled:
            self.get_logger().error(
                "Joy heartbeat timed out; commanding an arm stop"
            )
        self._motion_enabled = False
        self._publish_stop()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = GamepadToServo()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node._publish_stop()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
