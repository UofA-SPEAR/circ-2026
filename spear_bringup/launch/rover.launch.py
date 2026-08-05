"""Launch competition-critical software on the Jetson."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def _include(package, launch_file, condition, arguments=None):
    source = PythonLaunchDescriptionSource(
        os.path.join(
            get_package_share_directory(package),
            "launch",
            launch_file,
        )
    )
    return IncludeLaunchDescription(
        source,
        condition=IfCondition(condition),
        launch_arguments=(arguments or {}).items(),
    )


def generate_launch_description():
    """Build the rover-side competition launch description."""
    use_gps = LaunchConfiguration("use_gps")
    use_cameras = LaunchConfiguration("use_cameras")
    use_arm = LaunchConfiguration("use_arm")
    waypoint_file = LaunchConfiguration("waypoint_file")
    receiver_ip = LaunchConfiguration("receiver_ip")
    camera_bitrate = LaunchConfiguration("camera_bitrate")
    use_rviz = LaunchConfiguration("use_rviz")

    camera_config = os.path.join(
        get_package_share_directory("spear_gui"),
        "config",
        "camera_sender.yaml",
    )
    camera_sender = Node(
        package="spear_gui",
        executable="rover_camera_manager",
        name="camera_sender_node",
        condition=IfCondition(use_cameras),
        output="screen",
        parameters=[
            camera_config,
            {
                "receiver_ip": receiver_ip,
                "bitrate": ParameterValue(camera_bitrate, value_type=int),
            },
        ],
        respawn=True,
        respawn_delay=3.0,
    )

    gps = _include(
        "ultimate_gps_ros2",
        "gps_jetson_agx_orin.launch.py",
        use_gps,
        {"waypoints_file": waypoint_file},
    )
    arm_control = _include(
        "plex_ros2_control",
        "motor_drive.launch.py",
        use_arm,
    )
    arm_servo = _include(
        "plex_moveit",
        "bringup.launch.py",
        use_arm,
        {
            "use_gamepad_adapter": "true",
            "start_joy_driver": "false",
            "use_rviz": use_rviz,
        },
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_gps", default_value="true"),
            DeclareLaunchArgument("use_cameras", default_value="true"),
            DeclareLaunchArgument("use_arm", default_value="true"),
            DeclareLaunchArgument("use_rviz", default_value="false"),
            DeclareLaunchArgument(
                "waypoint_file",
                default_value="",
                description="Absolute path to ordered task waypoint CSV",
            ),
            DeclareLaunchArgument(
                "receiver_ip",
                default_value="192.168.8.224",
                description="Base-station address for RTP camera streams",
            ),
            DeclareLaunchArgument("camera_bitrate", default_value="1500000"),
            gps,
            camera_sender,
            arm_control,
            arm_servo,
        ]
    )
