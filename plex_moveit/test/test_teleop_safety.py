"""Unit tests for motion command mapping and defensive input handling."""

from plex_moveit.teleop_safety import (
    axis_value,
    button_pressed,
    joint_velocities,
    twist_components,
)


def test_missing_inputs_are_safe():
    assert axis_value([], 7, 0.08) == 0.0
    assert not button_pressed([], 6)
    assert joint_velocities([], [], 0.1, 0.08) == (0.0,) * 6


def test_deadzone_and_axis_clamping():
    assert axis_value([0.02], 0, 0.08) == 0.0
    assert axis_value([2.0], 0, 0.08) == 1.0
    assert axis_value([-2.0], 0, 0.08) == -1.0


def test_joint_commands_are_bounded():
    axes = [1.0, -1.0, 1.0, -1.0, 1.0, -1.0, 0.0, 0.0]
    buttons = [0, 0, 0, 0, 1, 0]
    values = joint_velocities(axes, buttons, 0.1, 0.08)
    assert len(values) == 6
    assert max(abs(value) for value in values) <= 0.2


def test_twist_commands_are_bounded():
    axes = [1.0] * 8
    buttons = [0, 0, 0, 0, 1, 0]
    linear, angular = twist_components(axes, buttons, 0.1, 0.08)
    assert max(abs(value) for value in linear) <= 0.1
    assert max(abs(value) for value in angular) <= 0.2
