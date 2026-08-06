"""Tests for drivetrain and EtherCAT competition contracts."""

from copy import deepcopy
from pathlib import Path

import yaml

from spear_bringup.config_validator import (
    PLACEHOLDER_ARRAYS,
    validate_actuator_map,
    validate_drive_config,
    validate_pdo_identity,
)


WORKSPACE = Path(__file__).resolve().parents[2]
DRIVE_CONFIG = WORKSPACE / "spear_drive/config/drive_controller.yaml"
ACTUATOR_MAP = WORKSPACE / "spear_drive/config/actuator_map.yaml"
BRUSHED_CONFIG = WORKSPACE / "spear_drive/config/brushed_dc_config.yaml"
STEPPER_CONFIG = WORKSPACE / "plex_ethercat/config/stepper_config.yaml"


def _write_calibrated_config(tmp_path):
    document = yaml.safe_load(DRIVE_CONFIG.read_text(encoding="utf-8"))
    parameters = document["spear_drive_controller"]["ros__parameters"]
    for name, placeholder in PLACEHOLDER_ARRAYS.items():
        parameters[name] = [
            float(value) + 0.001 * (index + 1)
            for index, value in enumerate(placeholder)
        ]
    output = tmp_path / "drive_controller.yaml"
    output.write_text(yaml.safe_dump(document), encoding="utf-8")
    return output


def test_known_placeholder_is_rejected(tmp_path):
    """A copied placeholder array makes competition preflight fail."""
    config = _write_calibrated_config(tmp_path)
    document = yaml.safe_load(config.read_text(encoding="utf-8"))
    parameters = document["spear_drive_controller"]["ros__parameters"]
    parameters["wheel_radius"] = deepcopy(PLACEHOLDER_ARRAYS["wheel_radius"])
    config.write_text(yaml.safe_dump(document), encoding="utf-8")

    issues = validate_drive_config(config)

    assert any(
        issue.level == "FAIL" and "wheel_radius" in issue.message
        for issue in issues
    )


def test_measured_drive_config_passes_static_checks(tmp_path):
    """Plausible measured values satisfy the machine-checkable constraints."""
    issues = validate_drive_config(_write_calibrated_config(tmp_path))

    assert not [issue for issue in issues if issue.level == "FAIL"]


def test_bus_positions_are_contiguous_and_unique():
    """The checked-in actuator map preserves the one-master 0–15 order."""
    issues = validate_actuator_map(ACTUATOR_MAP)

    assert not [issue for issue in issues if issue.level == "FAIL"]


def test_brushed_pdo_contract_and_identity_warning():
    """Essential brushed interfaces remain stable and collision stays visible."""
    issues = validate_pdo_identity(BRUSHED_CONFIG, STEPPER_CONFIG)

    assert not [issue for issue in issues if issue.level == "FAIL"]
    assert any("share an EtherCAT identity" in issue.message for issue in issues)
