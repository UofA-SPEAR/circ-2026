"""Pure helpers for bounded and defensive gamepad command mapping."""

from typing import Sequence, Tuple


def axis_value(
    axes: Sequence[float],
    index: int,
    deadzone: float,
) -> float:
    """Return a bounded axis value, or zero for a missing/noisy axis."""
    if index < 0 or index >= len(axes):
        return 0.0
    value = max(-1.0, min(1.0, float(axes[index])))
    return 0.0 if abs(value) < deadzone else value


def button_pressed(buttons: Sequence[int], index: int) -> bool:
    """Return a button state without allowing an invalid mapping to move."""
    return 0 <= index < len(buttons) and bool(buttons[index])


def joint_velocities(
    axes: Sequence[float],
    buttons: Sequence[int],
    sensitivity: float,
    deadzone: float,
) -> Tuple[float, ...]:
    """Map the established SPEAR controller layout to six joint commands."""
    scale = max(0.0, float(sensitivity)) * 2.0
    left_bumper = float(button_pressed(buttons, 4))
    right_bumper = float(button_pressed(buttons, 5))
    return (
        axis_value(axes, 0, deadzone) * scale,
        axis_value(axes, 1, deadzone) * scale,
        axis_value(axes, 4, deadzone) * scale,
        axis_value(axes, 3, deadzone) * scale,
        (left_bumper - right_bumper) * 0.5 * scale,
        (
            axis_value(axes, 2, deadzone)
            - axis_value(axes, 5, deadzone)
        )
        * 0.5
        * scale,
    )


def twist_components(
    axes: Sequence[float],
    buttons: Sequence[int],
    sensitivity: float,
    deadzone: float,
) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
    """Return unitless linear and angular Cartesian command components."""
    scale = max(0.0, float(sensitivity))
    left_bumper = float(button_pressed(buttons, 4))
    right_bumper = float(button_pressed(buttons, 5))
    linear = (
        axis_value(axes, 1, deadzone) * scale,
        axis_value(axes, 0, deadzone) * scale,
        (
            axis_value(axes, 2, deadzone)
            - axis_value(axes, 5, deadzone)
        )
        * 0.5
        * scale,
    )
    angular = (
        -(left_bumper - right_bumper) * scale * 2.0,
        axis_value(axes, 4, deadzone) * scale * 2.0,
        axis_value(axes, 3, deadzone) * scale * 2.0,
    )
    return linear, angular
