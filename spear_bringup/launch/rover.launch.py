"""Launch competition-critical software on the Jetson."""

import os

from ament_index_python.packages import (
    get_package_prefix,
    get_package_share_directory,
)
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    LaunchConfiguration,
    PythonExpression,
)
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
    use_drive = LaunchConfiguration("use_drive")
    drive_profile = LaunchConfiguration("drive_profile")
    waypoint_file = LaunchConfiguration("waypoint_file")
    receiver_ip = LaunchConfiguration("receiver_ip")
    camera_bitrate = LaunchConfiguration("camera_bitrate")
    use_rviz = LaunchConfiguration("use_rviz")
    record_bag = LaunchConfiguration("record_bag")
    bag_output_root = LaunchConfiguration("bag_output_root")
    bag_max_duration_sec = LaunchConfiguration("bag_max_duration_sec")
    bag_max_total_size_mb = LaunchConfiguration("bag_max_total_size_mb")

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
    recorder = ExecuteProcess(
        cmd=[
            os.path.join(
                get_package_prefix("spear_bringup"),
                "lib",
                "spear_bringup",
                "bounded_recorder",
            ),
            "--output-root",
            bag_output_root,
            "--max-duration-sec",
            bag_max_duration_sec,
            "--max-total-size-mb",
            bag_max_total_size_mb,
        ],
        condition=IfCondition(record_bag),
        output="screen",
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
        PythonExpression(
            ["'", use_arm, "' == 'true' or '", use_drive, "' == 'true'"]
        ),
        {
            "use_drive": use_drive,
            "use_arm_controllers": use_arm,
        },
    )
    drive_control = _include(
        "spear_drive",
        "load_drive_controller.launch.py",
        use_drive,
        {"profile": drive_profile},
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
            DeclareLaunchArgument("use_drive", default_value="true"),
            DeclareLaunchArgument(
                "drive_profile",
                default_value="crawl",
                choices=["crawl", "wet", "normal"],
            ),
            DeclareLaunchArgument("use_rviz", default_value="false"),
            DeclareLaunchArgument("record_bag", default_value="true"),
            DeclareLaunchArgument(
                "bag_output_root",
                default_value="~/.ros/spear_bags",
                description="Directory for bounded competition rosbags",
            ),
            DeclareLaunchArgument(
                "bag_max_duration_sec",
                default_value="7200",
                description="Stop recording after this many seconds",
            ),
            DeclareLaunchArgument(
                "bag_max_total_size_mb",
                default_value="10240",
                description="Stop recording once this bag reaches this size",
            ),
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
            recorder,
            camera_sender,
            arm_control,
            drive_control,
            arm_servo,
        ]
    )
