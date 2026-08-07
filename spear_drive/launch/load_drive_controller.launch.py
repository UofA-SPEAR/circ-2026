from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    package_share = FindPackageShare("spear_drive")
    base_config = PathJoinSubstitution(
        [package_share, "config", "drive_controller.yaml"]
    )
    profile_config = PathJoinSubstitution(
        [
            package_share,
            "config",
            "profiles",
            [LaunchConfiguration("profile"), ".yaml"],
        ]
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "controller_manager",
                default_value="/controller_manager",
                description="Existing controller manager that owns EtherCAT master 0",
            ),
            DeclareLaunchArgument(
                "profile",
                default_value="crawl",
                choices=["crawl", "wet", "normal"],
                description="Drivetrain limits loaded before activation",
            ),
            Node(
                package="controller_manager",
                executable="spawner",
                arguments=[
                    "spear_drive_controller",
                    "--controller-manager",
                    LaunchConfiguration("controller_manager"),
                    "--controller-type",
                    "spear_drive/SpearDriveController",
                    "--param-file",
                    base_config,
                    "--param-file",
                    profile_config,
                ],
                output="screen",
            ),
        ]
    )
