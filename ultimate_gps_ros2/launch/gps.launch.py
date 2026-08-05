"""Launch the Ultimate GPS driver with competition-friendly arguments."""

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
import os


def generate_launch_description():
    package_share = get_package_share_directory("ultimate_gps_ros2")
    default_config = os.path.join(package_share, "config", "gps.yaml")

    port = LaunchConfiguration("port")
    baud_rate = LaunchConfiguration("baud_rate")
    update_rate_hz = LaunchConfiguration("update_rate_hz")
    configure_receiver = LaunchConfiguration("configure_receiver")

    return LaunchDescription(
        [
            DeclareLaunchArgument("port", default_value="/dev/ttyUSB0"),
            DeclareLaunchArgument("baud_rate", default_value="9600"),
            DeclareLaunchArgument("update_rate_hz", default_value="5"),
            DeclareLaunchArgument("configure_receiver", default_value="true"),
            Node(
                package="ultimate_gps_ros2",
                executable="ultimate_gps_node",
                name="ultimate_gps",
                output="screen",
                parameters=[
                    default_config,
                    {
                        "port": port,
                        "baud_rate": ParameterValue(baud_rate, value_type=int),
                        "update_rate_hz": ParameterValue(
                            update_rate_hz,
                            value_type=int,
                        ),
                        "configure_receiver": ParameterValue(
                            configure_receiver,
                            value_type=bool,
                        ),
                    },
                ],
            ),
        ]
    )
