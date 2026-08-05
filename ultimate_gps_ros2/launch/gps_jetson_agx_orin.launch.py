"""Launch Ultimate GPS on the Jetson AGX Orin J30 UART."""

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
import os


def generate_launch_description():
    package_share = get_package_share_directory("ultimate_gps_ros2")
    config = os.path.join(
        package_share,
        "config",
        "jetson_agx_orin.yaml",
    )

    return LaunchDescription(
        [
            Node(
                package="ultimate_gps_ros2",
                executable="ultimate_gps_node",
                name="ultimate_gps",
                output="screen",
                parameters=[config],
            )
        ]
    )
