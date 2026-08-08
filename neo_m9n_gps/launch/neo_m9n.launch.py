"""Launch the u-blox NEO-M9N serial driver."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description() -> LaunchDescription:
    """Create the configurable receiver launch description."""
    package_share = get_package_share_directory('neo_m9n_gps')
    default_config = os.path.join(package_share, 'config', 'neo_m9n.yaml')

    return LaunchDescription([
        DeclareLaunchArgument(
            'config',
            default_value=default_config,
            description='Path to the NEO-M9N ROS parameter file',
        ),
        DeclareLaunchArgument(
            'port',
            default_value='auto',
            description='Serial device path or auto',
        ),
        DeclareLaunchArgument(
            'baud',
            default_value='38400',
            description='Receiver UART baud rate',
        ),
        DeclareLaunchArgument(
            'namespace',
            default_value='gps',
            description='ROS namespace for GPS topics',
        ),
        Node(
            package='neo_m9n_gps',
            executable='gps_node',
            name='neo_m9n_gps',
            namespace=LaunchConfiguration('namespace'),
            output='screen',
            parameters=[
                LaunchConfiguration('config'),
                {
                    'port': LaunchConfiguration('port'),
                    'baud': ParameterValue(
                        LaunchConfiguration('baud'), value_type=int
                    ),
                },
            ],
        ),
    ])
