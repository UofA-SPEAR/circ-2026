"""Launch the reliable operator-facing base-station applications."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    """Build the base-station launch description."""
    use_camera = LaunchConfiguration("use_camera")
    use_mission_panel = LaunchConfiguration("use_mission_panel")
    use_main_gui = LaunchConfiguration("use_main_gui")
    use_arm_gamepad = LaunchConfiguration("use_arm_gamepad")
    gamepad_device_id = LaunchConfiguration("gamepad_device_id")
    return LaunchDescription(
        [
            DeclareLaunchArgument("use_camera", default_value="true"),
            DeclareLaunchArgument("use_mission_panel", default_value="true"),
            DeclareLaunchArgument("use_main_gui", default_value="false"),
            DeclareLaunchArgument("use_arm_gamepad", default_value="true"),
            DeclareLaunchArgument(
                "gamepad_device_id",
                default_value="0",
                description="SDL arm-controller device index",
            ),
            Node(
                package="joy",
                executable="game_controller_node",
                name="arm_game_controller",
                condition=IfCondition(use_arm_gamepad),
                parameters=[
                    {
                        "device_id": ParameterValue(
                            gamepad_device_id,
                            value_type=int,
                        ),
                        "autorepeat_rate": 30.0,
                        "deadzone": 0.08,
                    }
                ],
                output="screen",
                respawn=True,
                respawn_delay=2.0,
            ),
            Node(
                package="spear_gui",
                executable="camera_node",
                name="camera_node",
                condition=IfCondition(use_camera),
                output="screen",
                respawn=True,
                respawn_delay=3.0,
            ),
            Node(
                package="spear_gui",
                executable="gps_mission_panel",
                name="gps_mission_panel",
                condition=IfCondition(use_mission_panel),
                output="screen",
                respawn=True,
                respawn_delay=3.0,
            ),
            Node(
                package="spear_gui",
                executable="main_gui",
                name="main_overlay_node",
                condition=IfCondition(use_main_gui),
                output="screen",
            ),
        ]
    )
