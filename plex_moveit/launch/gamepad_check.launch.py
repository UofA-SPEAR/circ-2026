"""Safely validate a controller without connecting commands to MoveIt Servo."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    """Launch the controller and adapter on isolated command topics."""
    gamepad_config = os.path.join(
        get_package_share_directory("plex_moveit"),
        "config",
        "gamepad.yaml",
    )
    device_id = LaunchConfiguration("gamepad_device_id")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "gamepad_device_id",
                default_value="0",
                description="SDL game-controller device index",
            ),
            Node(
                package="joy",
                executable="game_controller_node",
                name="game_controller_check",
                parameters=[
                    {
                        "device_id": ParameterValue(
                            device_id,
                            value_type=int,
                        ),
                        "autorepeat_rate": 30.0,
                        "deadzone": 0.08,
                    }
                ],
                output="screen",
            ),
            Node(
                package="plex_moveit",
                executable="gamepad_to_servo",
                name="gamepad_to_servo_check",
                parameters=[
                    gamepad_config,
                    {
                        "joint_command_topic": (
                            "/arm/teleop_check/joint_commands"
                        ),
                        "twist_command_topic": (
                            "/arm/teleop_check/twist_commands"
                        ),
                        "status_topic": "/arm/teleop_check/status",
                    },
                ],
                output="screen",
            ),
        ]
    )
