from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

# One entry per physical camera. Each becomes its own camera_sender_node
# process (see spear_gui/camera_sender_node.py) so a wedged camera can only
# ever take down its own process, never the others.
CAMERAS = [
    {"camera_sn": 302801647, "source": "zedxonesrc", "port": 5000, "exposure": 10000, "gain": 30000},
    {"camera_sn": 303928833, "source": "zedxonesrc", "port": 5001, "exposure": 10000, "gain": 30000},
    {"camera_sn": 305325257, "source": "zedxonesrc", "port": 5002, "exposure": 10000, "gain": 30000},
    {"camera_sn": 307142683, "source": "zedxonesrc", "port": 5003, "exposure": 10000, "gain": 30000},
    {"camera_sn": 308873104, "source": "zedxonesrc", "port": 5004, "exposure": 10000, "gain": 30000},
    {"camera_sn": 309256978, "source": "zedxonesrc", "port": 5005, "exposure": 10000, "gain": 30000},
    {"camera_sn": 44249482,  "source": "zedsrc",     "port": 5006, "exposure": 10000, "gain": 30000},
    {"camera_sn": 58896881,  "source": "zedsrc",     "port": 5007, "exposure": 10000, "gain": 30000},
]

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

    # Processes start independently for crash isolation. The shared startup
    # gate in camera_sender_node is held until the preceding camera emits its
    # first encoded buffer, so this small launch spacing is not relied upon for
    # correctness.
    camera_nodes = [
        TimerAction(
            period=i * 2.0,
            actions=[
                Node(
                    package="spear_gui",
                    executable="camera_sender_node",
                    name=f"camera_sender_{cam['port']}",
                    parameters=[{
                        "camera_sn": cam["camera_sn"],
                        "source": cam["source"],
                        "port": cam["port"],
                        "receiver_ip": receiver_ip,
                        "exposure": cam["exposure"],
                        "gain": cam["gain"],
                        "camera_resolution": CAMERA_RESOLUTION,
                        "camera_fps": CAMERA_FPS,
                        "stream_type": STREAM_TYPE,
                    }],
                    output="screen",
                    respawn=True,
                    respawn_delay=5.0,
                )
            ],
        )
        for i, cam in enumerate(CAMERAS)
    ]

    return LaunchDescription([
        receiver_ip_arg,
        *camera_nodes,
    ])
