"""Tests for continuous-joint angle wrapping."""

import math

import pytest

from plex_ros2_control.wrap_joint_states import wrap_to_pi


@pytest.mark.parametrize(
    ('angle', 'expected'),
    [
        (0.0, 0.0),
        (math.pi / 2.0, math.pi / 2.0),
        (-math.pi / 2.0, -math.pi / 2.0),
        (math.pi + 0.1, -math.pi + 0.1),
        (-math.pi - 0.1, math.pi - 0.1),
        (4.0 * math.pi + 0.25, 0.25),
    ],
)
def test_wrap_to_pi(angle, expected):
    """Angles should wrap to their expected canonical equivalents."""
    assert wrap_to_pi(angle) == pytest.approx(expected)


def test_wrap_to_pi_preserves_equivalent_rotation():
    """Wrapping should not change the represented physical rotation."""
    angle = 11.3
    wrapped = wrap_to_pi(angle)

    assert -math.pi <= wrapped <= math.pi
    assert math.sin(wrapped) == pytest.approx(math.sin(angle))
    assert math.cos(wrapped) == pytest.approx(math.cos(angle))
