from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

from spear_gui.camera_groups import CAMERA_GROUPS

# Both ZED X One and ZED X Mini support HD1200 at 30 FPS. Pinning the mode is
# important because ports 4/5 and 6/7 share capture-card groups, and plugin
# defaults can vary between ZED SDK releases.
CAMERA_RESOLUTION = 2  # HD1200 (1920x1200)
CAMERA_FPS = 30
STREAM_TYPE = 0       # left RGB image from stereo cameras


def generate_launch_description():

    receiver_ip_arg = DeclareLaunchArgument(
        'receiver_ip',
        default_value='192.168.10.11',
        description='IP of the machine receiving the camera streams.',
    )
    receiver_ip = LaunchConfiguration('receiver_ip')

    # Eight separate native multimedia contexts fail while the same eight
    # encoders work in one process. Four two-camera workers preserve useful
    # crash isolation without exhausting the Jetson's process-local ZED /
    # NVENC resources. A native crash loses at most one pair; launch respawns
    # only that pair.
    camera_groups = [
        TimerAction(
            period=i * 4.0,
            actions=[
                Node(
                    package="spear_gui",
                    executable="camera_group_sender_node",
                    arguments=[
                        "--group-index", str(i),
                        "--receiver-ip", receiver_ip,
                        "--camera-resolution", str(CAMERA_RESOLUTION),
                        "--camera-fps", str(CAMERA_FPS),
                        "--stream-type", str(STREAM_TYPE),
                    ],
                    output="screen",
                    respawn=True,
                    respawn_delay=10.0,
                )
            ],
        )
        for i, _ in enumerate(CAMERA_GROUPS)
    ]

    return LaunchDescription([
        receiver_ip_arg,
        *camera_groups,
    ])
