from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    device_id = LaunchConfiguration("device_id")
    config = PathJoinSubstitution(
        [FindPackageShare("spear_drive"), "config", "drive_controller.yaml"]
    )
    profile_config = PathJoinSubstitution(
        [
            FindPackageShare("spear_drive"),
            "config",
            "profiles",
            [LaunchConfiguration("profile"), ".yaml"],
        ]
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "device_id",
                default_value="1",
                description="Linux joystick index dedicated to rover drive",
            ),
            DeclareLaunchArgument(
                "profile",
                default_value="crawl",
                choices=["crawl", "wet", "normal"],
                description="Drive joystick speed profile",
            ),
            Node(
                package="joy",
                executable="game_controller_node",
                namespace="drive",
                name="game_controller",
                parameters=[
                    {
                        "device_id": ParameterValue(device_id, value_type=int),
                        "deadzone": 0.05,
                        "autorepeat_rate": 30.0,
                    }
                ],
                output="screen",
            ),
            Node(
                package="spear_drive",
                executable="drive_teleop",
                name="drive_teleop",
                parameters=[config, profile_config],
                output="screen",
            ),
        ]
    )
