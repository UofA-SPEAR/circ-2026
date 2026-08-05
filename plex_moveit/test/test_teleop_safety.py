"""Unit tests for motion mapping and deliberate arm arming."""

from math import inf, nan

from plex_moveit.teleop_safety import (
    ArmingGate,
    ControllerMapping,
    axis_value,
    button_pressed,
    joint_velocities,
    mapping_available,
    motion_inputs_neutral,
    twist_components,
)


MAPPING = ControllerMapping()
NEUTRAL_AXES = [0.0, 0.0, 0.0, 0.0, -1.0, -1.0]
NEUTRAL_BUTTONS = [0] * 13


def test_missing_inputs_are_safe():
    assert axis_value([], 7, 0.08) == 0.0
    assert not button_pressed([], 6)
    assert joint_velocities([], [], 0.1, 0.08) == (0.0,) * 6
    assert not mapping_available([], [], MAPPING, (6, 3, 0, 11, 12))


def test_deadzone_axis_clamping_and_nonfinite_values():
    assert axis_value([0.02], 0, 0.08) == 0.0
    assert axis_value([2.0], 0, 0.08) == 1.0
    assert axis_value([-2.0], 0, 0.08) == -1.0
    assert axis_value([nan], 0, 0.08) == 0.0
    assert axis_value([inf], 0, 0.08) == 0.0


def test_standard_mapping_is_available():
    assert mapping_available(
        NEUTRAL_AXES,
        NEUTRAL_BUTTONS,
        MAPPING,
        (6, 3, 0, 11, 12),
    )
    invalid_axes = list(NEUTRAL_AXES)
    invalid_axes[2] = nan
    assert not mapping_available(
        invalid_axes,
        NEUTRAL_BUTTONS,
        MAPPING,
        (6, 3, 0, 11, 12),
    )


def test_neutral_detection_handles_centered_triggers():
    assert motion_inputs_neutral(
        NEUTRAL_AXES, NEUTRAL_BUTTONS, MAPPING, 0.12
    )
    centered_triggers = [0.0] * 6
    assert motion_inputs_neutral(
        centered_triggers, NEUTRAL_BUTTONS, MAPPING, 0.12
    )


def test_neutral_detection_rejects_every_motion_control():
    for axis_index in range(4):
        axes = list(NEUTRAL_AXES)
        axes[axis_index] = 0.5
        assert not motion_inputs_neutral(
            axes, NEUTRAL_BUTTONS, MAPPING, 0.12
        )

    axes = list(NEUTRAL_AXES)
    axes[4] = 0.0
    assert not motion_inputs_neutral(
        axes, NEUTRAL_BUTTONS, MAPPING, 0.12
    )

    buttons = list(NEUTRAL_BUTTONS)
    buttons[9] = 1
    assert not motion_inputs_neutral(
        NEUTRAL_AXES, buttons, MAPPING, 0.12
    )


def test_joint_commands_use_standardized_layout_and_are_bounded():
    axes = [1.0, -1.0, 0.5, -0.5, 1.0, -1.0]
    buttons = [0] * 13
    buttons[9] = 1
    values = joint_velocities(axes, buttons, 0.1, 0.08)
    assert values == (0.2, -0.2, -0.1, 0.1, 0.1, 0.2)
    assert max(abs(value) for value in values) <= 0.2


def test_cartesian_mapping_matches_documented_controls():
    axes = [1.0, -1.0, 0.5, -0.5, 1.0, -1.0]
    buttons = [0] * 13
    buttons[10] = 1
    linear, angular = twist_components(axes, buttons, 0.1, 0.08)
    assert linear == (-0.1, 0.1, 0.1)
    assert angular == (0.1, -0.1, -0.1)


def test_arming_requires_initial_deadman_release():
    gate = ArmingGate(0.15)
    assert gate.update(True, True, 0.0) == "release_required"
    assert not gate.enabled
    assert gate.update(False, True, 0.1) == "deadman_released"


def test_arming_requires_neutral_hold():
    gate = ArmingGate(0.15)
    gate.update(False, True, 0.0)
    assert gate.update(True, False, 0.1) == "neutral_required"
    assert gate.update(True, True, 0.2) == "neutral_hold"
    assert gate.update(True, True, 0.34) == "neutral_hold"
    assert gate.update(True, True, 0.35) == "armed"
    assert gate.enabled


def test_armed_gate_allows_motion_until_deadman_release():
    gate = ArmingGate(0.0)
    gate.update(False, True, 0.0)
    assert gate.update(True, True, 0.1) == "armed"
    assert gate.update(True, False, 0.2) == "armed"
    assert gate.update(False, False, 0.3) == "deadman_released"
    assert not gate.enabled


def test_timeout_requires_another_release_before_rearming():
    gate = ArmingGate(0.0)
    gate.update(False, True, 0.0)
    gate.update(True, True, 0.1)
    gate.timeout()
    assert gate.update(True, True, 0.2) == "release_required"
    gate.update(False, True, 0.3)
    assert gate.update(True, True, 0.4) == "armed"
