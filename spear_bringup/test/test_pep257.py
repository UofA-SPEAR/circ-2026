"""Run docstring style validation for spear_bringup."""

from ament_pep257.main import main
import pytest


@pytest.mark.linter
@pytest.mark.pep257
def test_pep257():
    """Check package Python docstrings with the ROS 2 configuration."""
    assert main(argv=["."]) == 0, "Found docstring style errors"
