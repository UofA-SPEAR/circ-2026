"""Run Python style validation for spear_bringup."""

from ament_flake8.main import main_with_errors
import pytest


@pytest.mark.flake8
@pytest.mark.linter
def test_flake8():
    """Check package Python sources with the ROS 2 flake8 configuration."""
    return_code, errors = main_with_errors(argv=[])
    assert return_code == 0, "Found %d style errors:\n" % len(errors) + "\n".join(
        errors
    )
