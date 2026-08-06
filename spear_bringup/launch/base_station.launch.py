"""Launch the reliable operator-facing base-station applications."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    """Build the base-station launch description."""
    use_camera = LaunchConfiguration("use_camera")
    use_mission_panel = LaunchConfiguration("use_mission_panel")
    use_main_gui = LaunchConfiguration("use_main_gui")
    use_arm_gamepad = LaunchConfiguration("use_arm_gamepad")
    use_drive_gamepad = LaunchConfiguration("use_drive_gamepad")
    gamepad_device_id = LaunchConfiguration("gamepad_device_id")
    drive_gamepad_device_id = LaunchConfiguration("drive_gamepad_device_id")
    drive_profile = LaunchConfiguration("drive_profile")

    drive_teleop = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("spear_drive"),
                "launch",
                "drive_teleop.launch.py",
            )
        ),
        condition=IfCondition(use_drive_gamepad),
        launch_arguments={
            "device_id": drive_gamepad_device_id,
            "profile": drive_profile,
        }.items(),
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_camera", default_value="true"),
            DeclareLaunchArgument("use_mission_panel", default_value="true"),
            DeclareLaunchArgument("use_main_gui", default_value="false"),
            DeclareLaunchArgument("use_arm_gamepad", default_value="true"),
            DeclareLaunchArgument("use_drive_gamepad", default_value="true"),
            DeclareLaunchArgument(
                "gamepad_device_id",
                default_value="0",
                description="SDL arm-controller device index",
            ),
            DeclareLaunchArgument(
                "drive_gamepad_device_id",
                default_value="1",
                description="SDL drive-controller device index",
            ),
            DeclareLaunchArgument(
                "drive_profile",
                default_value="crawl",
                choices=["crawl", "wet", "normal"],
                description="Drive joystick speed profile",
            ),
            Node(
                package="joy",
                executable="game_controller_node",
                name="arm_game_controller",
                condition=IfCondition(use_arm_gamepad),
                parameters=[
                    {
                        "device_id": ParameterValue(
                            gamepad_device_id,
                            value_type=int,
                        ),
                        "autorepeat_rate": 30.0,
                        "deadzone": 0.08,
                    }
                ],
                output="screen",
                respawn=True,
                respawn_delay=2.0,
            ),
            drive_teleop,
            Node(
                package="spear_gui",
                executable="camera_node",
                name="camera_node",
                condition=IfCondition(use_camera),
                output="screen",
                respawn=True,
                respawn_delay=3.0,
            ),
            Node(
                package="spear_gui",
                executable="gps_mission_panel",
                name="gps_mission_panel",
                condition=IfCondition(use_mission_panel),
                output="screen",
                respawn=True,
                respawn_delay=3.0,
            ),
            Node(
                package="spear_gui",
                executable="main_gui",
                name="main_overlay_node",
                condition=IfCondition(use_main_gui),
                output="screen",
            ),
        ]
    )
