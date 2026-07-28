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

    # Path to your ZeroErr EtherCAT configuration file
    ethercat_config = os.path.join(
        get_package_share_directory('plex_arm_urdf_3'),
        'config',
        'zeroerr_drive_config.yaml'
    )
    
    rviz_config = os.path.join(
        get_package_share_directory("plex_arm_urdf_3"),
        'config', 
        'plex_arm_moveit.rviz'
    )

    servo_params_path = os.path.join(
    get_package_share_directory("plex_arm_urdf_3"),
    "config", "servo_params.yaml"
    )

    with open(servo_params_path, 'r') as f:
        servo_yaml = yaml.safe_load(f)

    moveit_config = MoveItConfigsBuilder(
        "plex_arm_urdf_3", 
        package_name="plex_arm_urdf_3"
    ).to_moveit_configs()

    ros2_controllers_path = os.path.join(
        get_package_share_directory("plex_arm_urdf_3"),
        "config", "ros2_controllers.yaml"
    )

    robot_state_publisher = Node(
        package = 'robot_state_publisher',
        executable = 'robot_state_publisher',
        name = 'robot_state_publisher',
        parameters = [
        moveit_config.robot_description,
        {'use_sim_time': True}],
        output = 'screen'
    )

    joint_state_publisher_gui = Node(
        package = 'joint_state_publisher_gui',
        executable= 'joint_state_publisher_gui',
        name = 'joint_state_publisher_gui',
        parameters = [
            moveit_config.robot_description,
            {'use_sim_time': True,}]
    )

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
        
    servo_params = servo_yaml['servo_node']['ros__parameters']

    ros2_control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        output="screen",
        parameters=[
            ros2_controllers_path,
            moveit_config.robot_description,
        ],
    )

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
    )

    arm_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["plex_arm_controller"],
    )

    joy_node = Node(
        package="joy",
        executable="joy_node",
        name="joy_node",
    )

    gamepad_node = Node(
        package ="plex_arm_urdf_3",
        executable="gamepad_to_servo",
        name="gamepad_to_servo"
    )

    keyboard_node = Node(
        package = "plex_arm_urdf_3",
        executable = "keyboard_to_servo",
        name= "keyboard_to_servo"
    )

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
                get_package_share_directory("plex_arm_urdf_3"),
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

    # Hardware Node definition
    HW_control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[
            moveit_config.robot_description,
            ethercat_config             
        ],
        output="screen",
    )

    return LaunchDescription([
        # robot_state_publisher,
        # joint_state_publisher_gui,
        rviz_node,
        # ros2_control_node,
        # joint_state_broadcaster_spawner,
        # arm_controller_spawner,
        # joy_node,
        gamepad_node,
        # keyboard_node,
        servo_node,
        move_group,
        start_servo,
        # HW_control_node
    ])