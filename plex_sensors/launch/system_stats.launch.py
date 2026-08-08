from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    publish_rate_hz = DeclareLaunchArgument(
        'publish_rate_hz', default_value='1.0',
        description='How often (Hz) to publish each system stat.',
    )
    enable_jtop = DeclareLaunchArgument(
        'enable_jtop', default_value='true',
        description='Publish Jetson GPU/power/engine metrics via jtop (Jetson only).',
    )

    node = Node(
        package='plex_sensors',
        executable='system_stats',
        name='system_stats',
        parameters=[{
            'publish_rate_hz': LaunchConfiguration('publish_rate_hz'),
            'enable_jtop': LaunchConfiguration('enable_jtop'),
        }],
        output='screen',
    )

    return LaunchDescription([publish_rate_hz, enable_jtop, node])
