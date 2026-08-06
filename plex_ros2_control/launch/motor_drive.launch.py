# Copyright 2023 ICube Laboratory, University of Strasbourg
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from launch import LaunchDescription
from launch.conditions import IfCondition
from launch.substitutions import Command, FindExecutable, PathJoinSubstitution, LaunchConfiguration
from launch.actions import DeclareLaunchArgument

from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    # Declare arguments
    declared_arguments = []
    declared_arguments.append(
        DeclareLaunchArgument(
            'description_file',
            default_value='motor_drive.config.xacro',
            description='URDF/XACRO description file with the axis.',
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            'use_drive',
            default_value='false',
            choices=['true', 'false'],
            description='Append rover slaves 6-15 to the shared EtherCAT master.',
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            'use_arm_controllers',
            default_value='true',
            choices=['true', 'false'],
            description=(
                'Load arm controllers on the shared EtherCAT master. The master '
                'can remain available to the drivetrain when this is false.'
            ),
        )
    )

    description_file = LaunchConfiguration('description_file')
    use_drive = LaunchConfiguration('use_drive')
    use_arm_controllers = LaunchConfiguration('use_arm_controllers')

    # Get URDF via xacro
    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution(
                [
                    FindPackageShare("plex_ethercat"),
                    "description/config",
                    description_file,
                ]
            ),
            ' use_drive:=',
            use_drive,
        ]
    )
    robot_description = {"robot_description": robot_description_content}

    robot_controllers = PathJoinSubstitution(
        [
            FindPackageShare("plex_ros2_control"),
            "config",
            "controllers.yaml",
        ]
    )

    control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[robot_description, robot_controllers],
        output="both",
    )
    robot_state_pub_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[robot_description],
    )

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "-c", "/controller_manager"],
    )

    trajectory_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["trajectory_controller", "-c", "/controller_manager", "--inactive"],
        condition=IfCondition(use_arm_controllers),
    )

    position_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["position_controller", "-c", "/controller_manager"],
        condition=IfCondition(use_arm_controllers),
    )

    velocity_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["velocity_controller", "-c", "/controller_manager"],
        condition=IfCondition(use_arm_controllers),
    )

    effort_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["effort_controller", "-c", "/controller_manager"],
        condition=IfCondition(use_arm_controllers),
    )

    control_word_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["control_word_controller", "-c", "/controller_manager"],
        condition=IfCondition(use_arm_controllers),
    )

    nodes = [
        control_node,
        robot_state_pub_node,
        joint_state_broadcaster_spawner,
        trajectory_controller_spawner,
        # position_controller_spawner,
        velocity_controller_spawner,
        # effort_controller_spawner,
        control_word_controller_spawner,
    ]

    return LaunchDescription(
        declared_arguments +
        nodes)
