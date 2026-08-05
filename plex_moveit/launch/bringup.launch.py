from launch import LaunchDescription
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder
from ament_index_python.packages import get_package_share_directory
from moveit_configs_utils.launches import PythonLaunchDescriptionSource, generate_demo_launch
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import TimerAction
from launch.actions import ExecuteProcess
import yaml
import os

def generate_launch_description():
    
    rviz_config = os.path.join(
        get_package_share_directory("plex_moveit"),
        'config', 
        'plex_arm_moveit.rviz'
    )

    servo_params_path = os.path.join(
    get_package_share_directory("plex_moveit"),
    "config", "servo_params.yaml"
    )

    with open(servo_params_path, 'r') as f:
        servo_yaml = yaml.safe_load(f)

    moveit_config = MoveItConfigsBuilder(
        "plex", 
        package_name="plex_moveit"
    ).to_moveit_configs()


    rviz_node = Node(
        package = 'rviz2',
        executable = 'rviz2',
        name = 'rviz2',
        arguments = [rviz_config],
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
        ],
        output ='screen'
    )

    gamepad_node = Node(
        package ="plex_moveit",
        executable="gamepad_to_servo",
        name="gamepad_to_servo"
    )

    damper_node = Node(
            package ="plex_moveit",
            executable="damper",
            name="damper"
    )

    keyboard_node = Node(
        package = "plex_moveit",
        executable = "keyboard_to_servo",
        name= "keyboard_to_servo"
    )
    
    joy_node = Node(
        package="joy",
        executable="joy_node",
        name="joy_node",
    )

    servo_params = servo_yaml['servo_node']['ros__parameters']

    servo_node = Node(
        package="moveit_servo",
        executable="servo_node_main",
        name="servo_node",
        output="screen",
        arguments=[{'use_intra_process_comms' : True}],
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            servo_params,
        ],
    )

    move_group = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("plex_moveit"),
                "launch", "move_group.launch.py"
            )
        )
    )
    
    start_servo = TimerAction(
        period=10.0,  # wait 15 seconds for servo_node to finish starting up
        actions=[
            ExecuteProcess(
                cmd=['ros2', 'service', 'call', '/servo_node/start_servo', 
                     'std_srvs/srv/Trigger', '{}'],
                output='screen'
            )
        ]
    )


    return LaunchDescription([
        rviz_node,
        joy_node,
        gamepad_node,
        damper_node,
        # keyboard_node,
        servo_node,
        move_group,
        start_servo,
    ])