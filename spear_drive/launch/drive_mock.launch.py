from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    package_share = FindPackageShare("spear_drive")
    controller_config = PathJoinSubstitution(
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
    robot_description = {
        "robot_description": Command(
            [
                FindExecutable(name="xacro"),
                " ",
                PathJoinSubstitution(
                    [package_share, "description", "drive_mock.urdf.xacro"]
                ),
            ]
        )
    }

    control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[robot_description, controller_config, profile_config],
        output="screen",
    )
    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[robot_description],
        output="screen",
    )
    joint_state_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
        output="screen",
    )
    drive_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["spear_drive_controller", "--controller-manager", "/controller_manager"],
        output="screen",
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "profile",
                default_value="crawl",
                choices=["crawl", "wet", "normal"],
                description="Drivetrain limits used by the mock controller",
            ),
            control_node,
            robot_state_publisher,
            joint_state_spawner,
            RegisterEventHandler(
                OnProcessExit(
                    target_action=joint_state_spawner,
                    on_exit=[drive_spawner],
                )
            ),
        ]
    )
