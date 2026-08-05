"""Launch Ultimate GPS on the Jetson AGX Orin J30 UART."""

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import os


def generate_launch_description():
    package_share = get_package_share_directory("ultimate_gps_ros2")
    config = os.path.join(
        package_share,
        "config",
        "jetson_agx_orin.yaml",
    )
    mission_config = os.path.join(
        package_share,
        "config",
        "mission.yaml",
    )
    waypoints_file = LaunchConfiguration("waypoints_file")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "waypoints_file",
                default_value="",
                description="Ordered gate CSV supplied during task setup",
            ),
            Node(
                package="ultimate_gps_ros2",
                executable="ultimate_gps_node",
                name="ultimate_gps",
                output="screen",
                parameters=[config],
            ),
            Node(
                package="ultimate_gps_ros2",
                executable="gps_mission_node",
                name="gps_mission",
                output="screen",
                parameters=[
                    mission_config,
                    {"waypoints_file": waypoints_file},
                ],
            ),
        ]
    )
