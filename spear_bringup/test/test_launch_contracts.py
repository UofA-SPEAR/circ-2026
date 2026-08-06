"""Static launch and Xacro contracts that do not require rover hardware."""

import ast
from pathlib import Path
import xml.etree.ElementTree as ElementTree


WORKSPACE = Path(__file__).resolve().parents[2]
BRINGUP = WORKSPACE / "spear_bringup/launch"
MOTOR_LAUNCH = WORKSPACE / "plex_ros2_control/launch/motor_drive.launch.py"
DRIVE_XACRO = (
    WORKSPACE
    / "spear_drive/description/ros2_control/drive_interfaces.ros2_control.xacro"
)
SHARED_XACRO = (
    WORKSPACE
    / "plex_ethercat/description/ros2_control/motor_drive.ros2_control.xacro"
)
XACRO_NAMESPACE = "http://www.ros.org/wiki/xacro"


def _declared_launch_arguments(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    arguments = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        function = node.func
        name = function.id if isinstance(function, ast.Name) else ""
        if name == "DeclareLaunchArgument" and isinstance(node.args[0], ast.Constant):
            arguments.add(node.args[0].value)
    return arguments


def test_base_station_declares_two_controller_contract():
    """One launch owns distinct arm and drive gamepad configuration."""
    arguments = _declared_launch_arguments(BRINGUP / "base_station.launch.py")

    assert {
        "use_arm_gamepad",
        "use_drive_gamepad",
        "gamepad_device_id",
        "drive_gamepad_device_id",
        "drive_profile",
    } <= arguments


def test_rover_declares_bounded_recording_contract():
    """Competition recording limits remain explicit launch arguments."""
    arguments = _declared_launch_arguments(BRINGUP / "rover.launch.py")

    assert {
        "record_bag",
        "bag_output_root",
        "bag_max_duration_sec",
        "bag_max_total_size_mb",
    } <= arguments


def test_shared_hardware_can_disable_only_arm_controllers():
    """Drive-only operation does not require loading arm motion controllers."""
    arguments = _declared_launch_arguments(MOTOR_LAUNCH)

    assert "use_arm_controllers" in arguments
    assert "use_drive" in arguments


def test_drive_slave_positions_are_exactly_six_through_fifteen():
    """The drivetrain appends ten modules after the six arm slaves."""
    root = ElementTree.parse(DRIVE_XACRO).getroot()
    calls = [
        element
        for element in root.iter()
        if element.tag
        in {
            f"{{{XACRO_NAMESPACE}}}drive_slave",
            f"{{{XACRO_NAMESPACE}}}steering_slave",
        }
    ]

    assert [int(call.attrib["slave_position"]) for call in calls] == list(
        range(6, 16)
    )
    assert len({call.attrib["joint"] for call in calls}) == 10


def test_shared_xacro_has_one_master_and_conditional_drive_macro():
    """Arm and drivetrain remain inside one EtherCAT ros2_control system."""
    root = ElementTree.parse(SHARED_XACRO).getroot()
    ros2_controls = list(root.iter("ros2_control"))
    master_plugins = [
        plugin
        for plugin in root.iter("plugin")
        if plugin.text == "ethercat_driver/EthercatDriver"
    ]
    drive_calls = list(
        root.iter(f"{{{XACRO_NAMESPACE}}}spear_drive_ethercat_joints")
    )

    assert len(ros2_controls) == 1
    assert len(master_plugins) == 1
    assert len(drive_calls) == 1
