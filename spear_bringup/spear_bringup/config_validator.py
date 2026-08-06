"""Validate machine-checkable competition drivetrain configuration contracts."""

import argparse
from dataclasses import dataclass
import math
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import yaml


@dataclass(frozen=True)
class ValidationIssue:
    """A validation result that is actionable during competition preflight."""

    level: str
    message: str


PLACEHOLDER_ARRAYS = {
    "wheel_x": [0.50, 0.50, 0.00, 0.00, -0.50, -0.50],
    "wheel_y": [0.35, -0.35, 0.35, -0.35, 0.35, -0.35],
    "wheel_radius": [0.13] * 6,
    "drive_gear_ratio": [1.0] * 6,
    "encoder_counts_per_motor_revolution": [28.0] * 6,
    "steering_min": [-0.78] * 4,
    "steering_max": [0.78] * 4,
}

EXPECTED_ARRAY_LENGTHS = {
    "drive_joints": 6,
    "steering_joints": 4,
    "wheel_x": 6,
    "wheel_y": 6,
    "wheel_radius": 6,
    "drive_gear_ratio": 6,
    "encoder_counts_per_motor_revolution": 6,
    "drive_direction": 6,
    "steering_min": 4,
    "steering_max": 4,
    "steering_gear_ratio": 4,
    "steering_direction": 4,
    "steering_offset": 4,
}

NUMERIC_ARRAYS = set(EXPECTED_ARRAY_LENGTHS) - {"drive_joints", "steering_joints"}


def _load_yaml(path: Path) -> Mapping[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        loaded = yaml.safe_load(stream)
    if not isinstance(loaded, dict):
        raise ValueError(f"{path} does not contain a YAML mapping")
    return loaded


def _numeric_sequence(values: Any) -> bool:
    return isinstance(values, list) and all(
        isinstance(value, (int, float)) and math.isfinite(float(value))
        for value in values
    )


def validate_drive_config(path: Path) -> list[ValidationIssue]:
    """Validate dimensions, ranges, and removal of known placeholder values."""
    issues: list[ValidationIssue] = []
    document = _load_yaml(path)
    try:
        parameters = document["spear_drive_controller"]["ros__parameters"]
    except (KeyError, TypeError) as error:
        raise ValueError(f"{path} is missing spear_drive_controller parameters") from error

    for name, expected_length in EXPECTED_ARRAY_LENGTHS.items():
        values = parameters.get(name)
        if not isinstance(values, list) or len(values) != expected_length:
            issues.append(
                ValidationIssue(
                    "FAIL",
                    f"{name} must contain exactly {expected_length} entries",
                )
            )
        elif name in NUMERIC_ARRAYS and not _numeric_sequence(values):
            issues.append(
                ValidationIssue(
                    "FAIL",
                    f"{name} must contain only finite numeric values",
                )
            )

    raw_drive_joints = parameters.get("drive_joints", [])
    raw_steering_joints = parameters.get("steering_joints", [])
    drive_joints = raw_drive_joints if isinstance(raw_drive_joints, list) else []
    steering_joints = (
        raw_steering_joints if isinstance(raw_steering_joints, list) else []
    )
    joint_names = [*drive_joints, *steering_joints]
    if (
        not all(isinstance(name, str) and name for name in joint_names)
        or len(set(joint_names)) != 10
    ):
        issues.append(
            ValidationIssue(
                "FAIL",
                "all six drive and four steering joint names must be nonempty and unique",
            )
        )

    for name, placeholder in PLACEHOLDER_ARRAYS.items():
        if parameters.get(name) == placeholder:
            issues.append(
                ValidationIssue(
                    "FAIL",
                    f"{name} still matches the unmeasured placeholder values",
                )
            )

    positive_arrays = (
        "wheel_radius",
        "drive_gear_ratio",
        "encoder_counts_per_motor_revolution",
        "steering_gear_ratio",
    )
    for name in positive_arrays:
        values = parameters.get(name)
        if _numeric_sequence(values) and any(float(value) <= 0.0 for value in values):
            issues.append(ValidationIssue("FAIL", f"{name} values must be positive"))

    for name in ("drive_direction", "steering_direction"):
        values = parameters.get(name)
        if _numeric_sequence(values) and any(abs(float(value)) != 1.0 for value in values):
            issues.append(ValidationIssue("FAIL", f"{name} values must be -1 or 1"))

    minimums = parameters.get("steering_min")
    maximums = parameters.get("steering_max")
    if _numeric_sequence(minimums) and _numeric_sequence(maximums):
        if len(minimums) == len(maximums) and any(
            float(minimum) >= float(maximum)
            for minimum, maximum in zip(minimums, maximums)
        ):
            issues.append(
                ValidationIssue(
                    "FAIL",
                    "every steering_min value must be less than steering_max",
                )
            )

    current_limit = parameters.get("max_motor_current")
    if not isinstance(current_limit, (int, float)) or not 0.0 < float(current_limit) <= 3.0:
        issues.append(
            ValidationIssue(
                "FAIL",
                "max_motor_current must be positive and no greater than the 3 A firmware limit",
            )
        )

    return issues


def validate_actuator_map(path: Path) -> list[ValidationIssue]:
    """Validate the single-master physical bus ordering contract."""
    issues: list[ValidationIssue] = []
    document = _load_yaml(path)
    try:
        ethercat = document["ethercat"]
        arm_positions = ethercat["existing_arm_slave_positions"]
        rover_entries = ethercat["required_physical_order"]
    except (KeyError, TypeError) as error:
        raise ValueError(f"{path} is missing the EtherCAT ordering contract") from error

    rover_positions = [entry.get("position") for entry in rover_entries]
    rover_joints = [entry.get("joint") for entry in rover_entries]
    rover_roles = [entry.get("role") for entry in rover_entries]
    if arm_positions != list(range(6)):
        issues.append(ValidationIssue("FAIL", "arm slave positions must be 0 through 5"))
    if rover_positions != list(range(6, 16)):
        issues.append(ValidationIssue("FAIL", "rover slave positions must be 6 through 15"))
    if len(set(rover_joints)) != 10:
        issues.append(ValidationIssue("FAIL", "all ten rover EtherCAT joints must be unique"))
    if rover_roles != ["drive"] * 6 + ["steering"] * 4:
        issues.append(
            ValidationIssue(
                "FAIL",
                "positions 6-11 must be drive and 12-15 must be steering",
            )
        )
    if ethercat.get("master_id") != 0:
        issues.append(ValidationIssue("FAIL", "the shared EtherCAT master must remain master 0"))
    return issues


def validate_pdo_identity(
    brushed_path: Path,
    stepper_path: Path,
) -> list[ValidationIssue]:
    """Report the known identity collision and validate essential brushed PDOs."""
    issues: list[ValidationIssue] = []
    brushed = _load_yaml(brushed_path)
    stepper = _load_yaml(stepper_path)

    if (
        brushed.get("vendor_id") == stepper.get("vendor_id")
        and brushed.get("product_id") == stepper.get("product_id")
    ):
        issues.append(
            ValidationIssue(
                "WARN",
                "brushed and stepper firmware still share an EtherCAT "
                "identity; verify every bus position",
            )
        )

    rpdo_channels = brushed.get("rpdo", [{}])[0].get("channels", [])
    tpdo_channels = brushed.get("tpdo", [{}])[0].get("channels", [])
    command_interfaces = {
        (channel.get("index"), channel.get("sub_index")): channel.get(
            "command_interface"
        )
        for channel in rpdo_channels
    }
    state_interfaces = {
        (channel.get("index"), channel.get("sub_index")): channel.get(
            "state_interface"
        )
        for channel in tpdo_channels
    }
    required_commands = {
        (0x7000, 1): "control_word",
        (0x7000, 2): "current",
    }
    required_states = {
        (0x6000, 1): "status_word",
        (0x6000, 2): "current",
        (0x6000, 3): "encoder_counts_per_second",
        (0x6000, 4): "encoder_counts",
        (0x6000, 5): "duty_cycle",
    }
    if any(command_interfaces.get(key) != value for key, value in required_commands.items()):
        issues.append(ValidationIssue("FAIL", "brushed RPDO command contract changed"))
    if any(state_interfaces.get(key) != value for key, value in required_states.items()):
        issues.append(ValidationIssue("FAIL", "brushed TPDO state contract changed"))

    rpdo_by_address = {
        (channel.get("index"), channel.get("sub_index")): channel
        for channel in rpdo_channels
    }
    tpdo_by_address = {
        (channel.get("index"), channel.get("sub_index")): channel
        for channel in tpdo_channels
    }
    if rpdo_by_address.get((0x7000, 2), {}).get("factor") != 1000.0:
        issues.append(
            ValidationIssue("FAIL", "brushed target current must convert A to mA")
        )
    if tpdo_by_address.get((0x6000, 2), {}).get("factor") != 0.001:
        issues.append(
            ValidationIssue("FAIL", "brushed measured current must convert mA to A")
        )

    sdo_values = {
        (entry.get("index"), entry.get("sub_index")): entry.get("value")
        for entry in brushed.get("sdo", [])
    }
    if sdo_values.get((0x8000, 1)) != 0:
        issues.append(ValidationIssue("FAIL", "brushed firmware must start in current mode"))
    if sdo_values.get((0x8000, 2)) != 3000:
        issues.append(
            ValidationIssue("FAIL", "brushed firmware current limit must remain 3000 mA")
        )
    return issues


def validate_all(
    drive_config: Path,
    actuator_map: Path,
    brushed_config: Path,
    stepper_config: Path,
) -> list[ValidationIssue]:
    """Run every static competition configuration validation."""
    validators: Iterable[tuple] = (
        (validate_drive_config, (drive_config,)),
        (validate_actuator_map, (actuator_map,)),
        (validate_pdo_identity, (brushed_config, stepper_config)),
    )
    issues: list[ValidationIssue] = []
    for validator, arguments in validators:
        try:
            issues.extend(validator(*arguments))
        except (OSError, ValueError, yaml.YAMLError) as error:
            issues.append(ValidationIssue("FAIL", str(error)))
    return issues


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--drive-config", type=Path, required=True)
    parser.add_argument("--actuator-map", type=Path, required=True)
    parser.add_argument("--brushed-config", type=Path, required=True)
    parser.add_argument("--stepper-config", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Print validation results and return nonzero for unsafe configuration."""
    arguments = _parser().parse_args(argv)
    issues = validate_all(
        arguments.drive_config,
        arguments.actuator_map,
        arguments.brushed_config,
        arguments.stepper_config,
    )
    for issue in issues:
        print(f"{issue.level}: {issue.message}")
    failures = sum(issue.level == "FAIL" for issue in issues)
    warnings = sum(issue.level == "WARN" for issue in issues)
    if not issues:
        print("PASS: competition configuration contracts are valid")
    print(f"Configuration result: {failures} failure(s), {warnings} warning(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
