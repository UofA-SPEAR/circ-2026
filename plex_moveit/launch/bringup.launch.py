"""Bring up MoveIt Servo with conservative competition defaults."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
    TimerAction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder
import yaml


def generate_launch_description():
    """Launch Servo, joystick input, MoveGroup, and optional RViz."""
    package_share = get_package_share_directory("plex_moveit")
    servo_params_path = os.path.join(
        package_share,
        "config",
        "servo_params.yaml",
    )
    with open(servo_params_path, "r", encoding="utf-8") as stream:
        servo_yaml = yaml.safe_load(stream)

    moveit_config = MoveItConfigsBuilder(
        "plex",
        package_name="plex_moveit",
    ).to_moveit_configs()

    use_joy = LaunchConfiguration("use_joy")
    use_rviz = LaunchConfiguration("use_rviz")

    joy_node = Node(
        package="joy",
        executable="joy_node",
        name="joy_node",
        condition=IfCondition(use_joy),
        parameters=[{"autorepeat_rate": 30.0, "deadzone": 0.08}],
        output="screen",
    )
    gamepad_node = Node(
        package="plex_moveit",
        executable="gamepad_to_servo",
        name="gamepad_to_servo",
        condition=IfCondition(use_joy),
        output="screen",
    )
    servo_node = Node(
        package="moveit_servo",
        executable="servo_node_main",
        name="servo_node",
        output="screen",
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            servo_yaml["servo_node"]["ros__parameters"],
        ],
    )
    move_group = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(package_share, "launch", "move_group.launch.py")
        )
    )
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        condition=IfCondition(use_rviz),
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
        ],
        output="screen",
    )
    start_servo = TimerAction(
        period=5.0,
        actions=[
            ExecuteProcess(
                cmd=[
                    "ros2",
                    "service",
                    "call",
                    "/servo_node/start_servo",
                    "std_srvs/srv/Trigger",
                    "{}",
                ],
                output="screen",
            )
        ],
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_joy", default_value="true"),
            DeclareLaunchArgument("use_rviz", default_value="false"),
            joy_node,
            gamepad_node,
            servo_node,
            move_group,
            rviz_node,
            start_servo,
        ]
    )
