"""Pure, ROS-independent safety helpers for arm gamepad control."""

from dataclasses import dataclass
import math
from typing import Sequence, Tuple


@dataclass(frozen=True)
class ControllerMapping:
    """SDL game-controller indexes published by ``game_controller_node``."""

    left_x_axis: int = 0
    left_y_axis: int = 1
    right_x_axis: int = 2
    right_y_axis: int = 3
    left_trigger_axis: int = 4
    right_trigger_axis: int = 5
    left_shoulder_button: int = 9
    right_shoulder_button: int = 10

    @property
    def motion_axes(self) -> Tuple[int, ...]:
        return (
            self.left_x_axis,
            self.left_y_axis,
            self.right_x_axis,
            self.right_y_axis,
            self.left_trigger_axis,
            self.right_trigger_axis,
        )

    @property
    def motion_buttons(self) -> Tuple[int, ...]:
        return (self.left_shoulder_button, self.right_shoulder_button)


def _finite_nonnegative(value: float) -> float:
    try:
        converted = float(value)
    except (TypeError, ValueError):
        return 0.0
    return converted if math.isfinite(converted) and converted >= 0.0 else 0.0


def axis_value(
    axes: Sequence[float],
    index: int,
    deadzone: float,
) -> float:
    """Return a bounded finite axis value, or zero for invalid/noisy input."""
    if index < 0 or index >= len(axes):
        return 0.0
    try:
        value = float(axes[index])
    except (TypeError, ValueError):
        return 0.0
    if not math.isfinite(value):
        return 0.0
    value = max(-1.0, min(1.0, value))
    return 0.0 if abs(value) < _finite_nonnegative(deadzone) else value


def button_pressed(buttons: Sequence[int], index: int) -> bool:
    """Return a button state without allowing an invalid mapping to move."""
    return 0 <= index < len(buttons) and bool(buttons[index])


def mapping_available(
    axes: Sequence[float],
    buttons: Sequence[int],
    mapping: ControllerMapping,
    required_buttons: Sequence[int] = (),
) -> bool:
    """Confirm that every configured control index exists in a Joy message."""
    all_buttons = mapping.motion_buttons + tuple(required_buttons)
    if not all(index >= 0 and index < len(axes) for index in mapping.motion_axes):
        return False
    if not all(index >= 0 and index < len(buttons) for index in all_buttons):
        return False
    try:
        return all(math.isfinite(float(axes[index])) for index in mapping.motion_axes)
    except (TypeError, ValueError):
        return False


def trigger_difference(
    axes: Sequence[float],
    mapping: ControllerMapping,
    deadzone: float,
) -> float:
    """Return a centered, bounded differential trigger command."""
    difference = (
        axis_value(axes, mapping.left_trigger_axis, deadzone)
        - axis_value(axes, mapping.right_trigger_axis, deadzone)
    ) * 0.5
    return max(-1.0, min(1.0, difference))


def motion_inputs_neutral(
    axes: Sequence[float],
    buttons: Sequence[int],
    mapping: ControllerMapping,
    threshold: float,
) -> bool:
    """Return true only when every motion-producing control is neutral."""
    if not mapping_available(axes, buttons, mapping):
        return False
    limit = min(0.5, _finite_nonnegative(threshold))
    stick_axes = (
        mapping.left_x_axis,
        mapping.left_y_axis,
        mapping.right_x_axis,
        mapping.right_y_axis,
    )
    return (
        all(abs(axis_value(axes, index, 0.0)) <= limit for index in stick_axes)
        and abs(trigger_difference(axes, mapping, 0.0)) <= limit
        and not any(button_pressed(buttons, index) for index in mapping.motion_buttons)
    )


def joint_velocities(
    axes: Sequence[float],
    buttons: Sequence[int],
    sensitivity: float,
    deadzone: float,
    mapping: ControllerMapping = ControllerMapping(),
) -> Tuple[float, ...]:
    """Map a standardized game controller to six bounded joint commands."""
    scale = min(1.0, _finite_nonnegative(sensitivity) * 2.0)
    left_shoulder = float(
        button_pressed(buttons, mapping.left_shoulder_button)
    )
    right_shoulder = float(
        button_pressed(buttons, mapping.right_shoulder_button)
    )
    return (
        axis_value(axes, mapping.left_x_axis, deadzone) * scale,
        axis_value(axes, mapping.left_y_axis, deadzone) * scale,
        axis_value(axes, mapping.right_y_axis, deadzone) * scale,
        axis_value(axes, mapping.right_x_axis, deadzone) * scale,
        (left_shoulder - right_shoulder) * 0.5 * scale,
        trigger_difference(axes, mapping, deadzone) * scale,
    )


def twist_components(
    axes: Sequence[float],
    buttons: Sequence[int],
    sensitivity: float,
    deadzone: float,
    mapping: ControllerMapping = ControllerMapping(),
) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
    """Map a controller to bounded Cartesian linear and angular commands."""
    scale = min(1.0, _finite_nonnegative(sensitivity))
    left_shoulder = float(
        button_pressed(buttons, mapping.left_shoulder_button)
    )
    right_shoulder = float(
        button_pressed(buttons, mapping.right_shoulder_button)
    )
    linear = (
        axis_value(axes, mapping.left_y_axis, deadzone) * scale,
        axis_value(axes, mapping.left_x_axis, deadzone) * scale,
        trigger_difference(axes, mapping, deadzone) * scale,
    )
    angular = (
        axis_value(axes, mapping.right_x_axis, deadzone) * scale * 2.0,
        axis_value(axes, mapping.right_y_axis, deadzone) * scale * 2.0,
        (left_shoulder - right_shoulder) * scale,
    )
    return linear, angular


class ArmingGate:
    """Require a deadman release and neutral hold before enabling motion."""

    def __init__(self, neutral_hold_sec: float = 0.15) -> None:
        self.neutral_hold_sec = _finite_nonnegative(neutral_hold_sec)
        self.enabled = False
        self._release_seen = False
        self._neutral_since = None

    def update(self, deadman: bool, neutral: bool, now: float) -> str:
        """Update the gate and return a stable operator-facing state reason."""
        if not deadman:
            self.enabled = False
            self._release_seen = True
            self._neutral_since = None
            return "deadman_released"

        if not self._release_seen:
            self.enabled = False
            self._neutral_since = None
            return "release_required"

        if self.enabled:
            return "armed"

        if not neutral:
            self._neutral_since = None
            return "neutral_required"

        timestamp = float(now)
        if self._neutral_since is None:
            self._neutral_since = timestamp
        if timestamp - self._neutral_since + 1e-9 < self.neutral_hold_sec:
            return "neutral_hold"

        self.enabled = True
        return "armed"

    def timeout(self) -> None:
        """Latch motion off until the deadman is observed released again."""
        self.enabled = False
        self._release_seen = False
        self._neutral_since = None
