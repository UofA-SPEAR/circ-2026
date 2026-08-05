"""Competition-focused, fail-safe gamepad adapter for MoveIt Servo."""

import json
import time
from typing import Tuple

from control_msgs.msg import JointJog
from geometry_msgs.msg import TwistStamped
import rclpy
from rclpy.node import Node
from rclpy.qos import (
    DurabilityPolicy,
    HistoryPolicy,
    QoSProfile,
    ReliabilityPolicy,
    qos_profile_sensor_data,
)
from sensor_msgs.msg import Joy
from std_msgs.msg import String

from .teleop_safety import (
    ArmingGate,
    ControllerMapping,
    button_pressed,
    joint_velocities,
    mapping_available,
    motion_inputs_neutral,
    twist_components,
)


JOINT_NAMES = [f"joint_{index}" for index in range(1, 7)]


class GamepadToServo(Node):
    """Publish bounded commands only after deliberate, neutral arming."""

    def __init__(self) -> None:
        super().__init__("gamepad_to_servo")

        self.declare_parameter("deadman_button", 6)
        self.declare_parameter("mode_button", 3)
        self.declare_parameter("sensitivity_button", 0)
        self.declare_parameter("dpad_up_button", 11)
        self.declare_parameter("dpad_down_button", 12)
        self.declare_parameter("left_x_axis", 0)
        self.declare_parameter("left_y_axis", 1)
        self.declare_parameter("right_x_axis", 2)
        self.declare_parameter("right_y_axis", 3)
        self.declare_parameter("left_trigger_axis", 4)
        self.declare_parameter("right_trigger_axis", 5)
        self.declare_parameter("left_shoulder_button", 9)
        self.declare_parameter("right_shoulder_button", 10)
        self.declare_parameter("joy_timeout_sec", 0.30)
        self.declare_parameter("deadzone", 0.08)
        self.declare_parameter("neutral_threshold", 0.12)
        self.declare_parameter("neutral_hold_sec", 0.15)
        self.declare_parameter("command_frame", "base_link")
        self.declare_parameter("joy_topic", "/joy")
        self.declare_parameter(
            "joint_command_topic", "/servo_node/delta_joint_cmds"
        )
        self.declare_parameter(
            "twist_command_topic", "/servo_node/delta_twist_cmds"
        )
        self.declare_parameter("status_topic", "/arm/teleop/status")

        int_parameter = self.get_parameter
        self._deadman_button = int(int_parameter("deadman_button").value)
        self._mode_button = int(int_parameter("mode_button").value)
        self._sensitivity_button = int(
            int_parameter("sensitivity_button").value
        )
        self._dpad_up_button = int(int_parameter("dpad_up_button").value)
        self._dpad_down_button = int(
            int_parameter("dpad_down_button").value
        )
        self._mapping = ControllerMapping(
            left_x_axis=int(int_parameter("left_x_axis").value),
            left_y_axis=int(int_parameter("left_y_axis").value),
            right_x_axis=int(int_parameter("right_x_axis").value),
            right_y_axis=int(int_parameter("right_y_axis").value),
            left_trigger_axis=int(int_parameter("left_trigger_axis").value),
            right_trigger_axis=int(
                int_parameter("right_trigger_axis").value
            ),
            left_shoulder_button=int(
                int_parameter("left_shoulder_button").value
            ),
            right_shoulder_button=int(
                int_parameter("right_shoulder_button").value
            ),
        )
        self._joy_timeout_sec = max(
            0.10, float(self.get_parameter("joy_timeout_sec").value)
        )
        self._deadzone = max(
            0.0, min(0.5, float(self.get_parameter("deadzone").value))
        )
        self._neutral_threshold = max(
            self._deadzone,
            min(0.5, float(self.get_parameter("neutral_threshold").value)),
        )
        self._command_frame = str(self.get_parameter("command_frame").value)
        joy_topic = str(self.get_parameter("joy_topic").value)
        joint_command_topic = str(
            self.get_parameter("joint_command_topic").value
        )
        twist_command_topic = str(
            self.get_parameter("twist_command_topic").value
        )
        status_topic = str(self.get_parameter("status_topic").value)
        self._arming_gate = ArmingGate(
            float(self.get_parameter("neutral_hold_sec").value)
        )

        self._joint_mode = True
        self._sensitivity_levels = [0.0125, 0.025, 0.05, 0.075, 0.10]
        self._sensitivity_index = 0
        self._last_button_states = {}
        self._last_joy_time = None
        self._timed_out = False
        self._mapping_valid = False
        self._last_state = "waiting_for_controller"

        self._twist_publisher = self.create_publisher(
            TwistStamped, twist_command_topic, 10
        )
        self._joint_publisher = self.create_publisher(
            JointJog, joint_command_topic, 10
        )
        status_qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )
        self._status_publisher = self.create_publisher(
            String, status_topic, status_qos
        )
        self._joy_subscription = self.create_subscription(
            Joy, joy_topic, self._joy_callback, qos_profile_sensor_data
        )
        self._watchdog_timer = self.create_timer(0.05, self._watchdog)
        self._status_timer = self.create_timer(0.5, self._publish_status)

        self.get_logger().info(
            "Arm teleop locked: release START, center all controls, then hold "
            "START to arm"
        )
        self._publish_status()

    @property
    def _sensitivity(self) -> float:
        return self._sensitivity_levels[self._sensitivity_index]

    def _required_buttons(self) -> Tuple[int, ...]:
        return (
            self._deadman_button,
            self._mode_button,
            self._sensitivity_button,
            self._dpad_up_button,
            self._dpad_down_button,
        )

    def _rising_edge(self, message: Joy, index: int) -> bool:
        current = button_pressed(message.buttons, index)
        previous = self._last_button_states.get(index, current)
        self._last_button_states[index] = current
        return current and not previous

    def _update_button_history(self, message: Joy) -> None:
        for index in self._required_buttons():
            if index not in self._last_button_states:
                self._last_button_states[index] = button_pressed(
                    message.buttons, index
                )

    def _handle_disarmed_settings(self, message: Joy) -> None:
        if self._rising_edge(message, self._mode_button):
            self._joint_mode = not self._joint_mode
            self._publish_stop()
            mode = "joint" if self._joint_mode else "Cartesian"
            self.get_logger().info(f"Arm command mode: {mode}")

        if self._rising_edge(message, self._sensitivity_button):
            self._sensitivity_index = (
                self._sensitivity_index + 1
            ) % len(self._sensitivity_levels)
            self._report_sensitivity()

        dpad_up = self._rising_edge(message, self._dpad_up_button)
        dpad_down = self._rising_edge(message, self._dpad_down_button)
        if dpad_up:
            self._sensitivity_index = min(
                self._sensitivity_index + 1,
                len(self._sensitivity_levels) - 1,
            )
        elif dpad_down:
            self._sensitivity_index = max(self._sensitivity_index - 1, 0)
        if dpad_up or dpad_down:
            self._report_sensitivity()

    def _report_sensitivity(self) -> None:
        self.get_logger().info(
            f"Arm sensitivity: {self._sensitivity:.4f}"
        )
        self._publish_status()

    def _set_state(self, state: str) -> None:
        if state == self._last_state:
            return
        previous = self._last_state
        self._last_state = state
        if state == "armed":
            self.get_logger().info("Arm teleop ARMED")
        elif previous == "armed":
            self.get_logger().warning(f"Arm teleop DISARMED: {state}")
        self._publish_status()

    def _joy_callback(self, message: Joy) -> None:
        now = time.monotonic()
        self._last_joy_time = now
        self._timed_out = False
        self._update_button_history(message)

        mapping_valid = mapping_available(
            message.axes,
            message.buttons,
            self._mapping,
            self._required_buttons(),
        )
        if not mapping_valid:
            if self._mapping_valid:
                self.get_logger().error(
                    "Controller mapping became invalid; motion locked"
                )
            self._mapping_valid = False
            self._arming_gate.timeout()
            self._publish_stop()
            self._set_state("mapping_invalid")
            return
        if not self._mapping_valid:
            self.get_logger().info(
                f"Controller mapping accepted: {len(message.axes)} axes, "
                f"{len(message.buttons)} buttons"
            )
        self._mapping_valid = True

        deadman = button_pressed(message.buttons, self._deadman_button)
        if not deadman:
            self._handle_disarmed_settings(message)
        else:
            # Track edges while armed so a held settings button cannot trigger
            # when the deadman is subsequently released.
            for index in (
                self._mode_button,
                self._sensitivity_button,
                self._dpad_up_button,
                self._dpad_down_button,
            ):
                self._last_button_states[index] = button_pressed(
                    message.buttons, index
                )

        neutral = motion_inputs_neutral(
            message.axes,
            message.buttons,
            self._mapping,
            self._neutral_threshold,
        )
        state = self._arming_gate.update(deadman, neutral, now)
        self._set_state(state)
        if not self._arming_gate.enabled:
            self._publish_stop()
            return

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
                self._mapping,
            )
        )
        self._joint_publisher.publish(command)

    def _publish_twist_command(self, message: Joy) -> None:
        linear, angular = twist_components(
            message.axes,
            message.buttons,
            self._sensitivity,
            self._deadzone,
            self._mapping,
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

    def _publish_status(self) -> None:
        age = None
        if self._last_joy_time is not None:
            age = max(0.0, time.monotonic() - self._last_joy_time)
        status = {
            "armed": self._arming_gate.enabled,
            "connected": age is not None and age <= self._joy_timeout_sec,
            "mapping_valid": self._mapping_valid,
            "mode": "joint" if self._joint_mode else "cartesian",
            "reason": self._last_state,
            "sensitivity": self._sensitivity,
            "joy_age_sec": None if age is None else round(age, 3),
        }
        message = String()
        message.data = json.dumps(status, separators=(",", ":"))
        self._status_publisher.publish(message)

    def _watchdog(self) -> None:
        if self._last_joy_time is None:
            return
        if time.monotonic() - self._last_joy_time <= self._joy_timeout_sec:
            return
        if self._timed_out:
            return
        self._timed_out = True
        self._arming_gate.timeout()
        self._publish_stop()
        self._set_state("controller_timeout")
        self.get_logger().error(
            "Joy heartbeat timed out; arm locked until deadman release"
        )


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
