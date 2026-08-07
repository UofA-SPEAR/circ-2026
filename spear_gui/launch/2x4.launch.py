from launch import LaunchDescription
from launch.actions import TimerAction
from launch_ros.actions import Node


def generate_launch_description():

    receiver_ip = "192.168.10.11"
    bitrate = 4000000

    # zedsrc goes first and alone: it is the slowest to init and loses the
    # race against the zedxonesrc groups if they all start together
    zed_0 = Node(
        package="spear_gui",
        executable="zed_streamer",
        name="zed_stream_0",
        output="screen",
        emulate_tty=True,
        parameters=[{
            "camera_sns": [44249482, 58896881],
            "ports": [5006, 5007],
            "receiver_ip": receiver_ip,
            "resolution": "HD1080",
            "bitrate": bitrate,
        }],
    )

    zedxone_0 = Node(
        package="spear_gui",
        executable="zedxone_streamer",
        name="zedxone_stream_0",
        output="screen",
        emulate_tty=True,
        parameters=[{
            "camera_sns": [302801647, 303928833],
            "ports": [5000, 5001],
            "receiver_ip": receiver_ip,
            "resolution": "HD1200",
            "bitrate": bitrate,
        }],
    )

    zedxone_1 = Node(
        package="spear_gui",
        executable="zedxone_streamer",
        name="zedxone_stream_1",
        output="screen",
        emulate_tty=True,
        parameters=[{
            "camera_sns": [305325257, 307142683],
            "ports": [5002, 5003],
            "receiver_ip": receiver_ip,
            "resolution": "HD1200",
            "bitrate": bitrate,
        }],
    )

    zedxone_2 = Node(
        package="spear_gui",
        executable="zedxone_streamer",
        name="zedxone_stream_2",
        output="screen",
        emulate_tty=True,
        parameters=[{
            "camera_sns": [308873104, 309256978],
            "ports": [5004, 5005],
            "receiver_ip": receiver_ip,
            "resolution": "HD1200",
            "bitrate": bitrate,
        }],
    )

    return LaunchDescription([
        zed_0,
        TimerAction(period=8.0,  actions=[zedxone_0]),
        TimerAction(period=16.0, actions=[zedxone_1]),
        TimerAction(period=24.0, actions=[zedxone_2]),
    ])