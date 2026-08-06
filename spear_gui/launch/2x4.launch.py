from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    receiver_ip = "192.168.10.11"
    bitrate = 4000000
    exposure = 10000
    gain = 30000

    camera_stream_0 = Node(
        package="spear_gui",
        executable="camera_streamer",
        name="camera_stream_0",
        output="screen",
        emulate_tty=True,
        parameters=[{
            "camera_sns": [302801647, 303928833],
            "sources": ["zedxonesrc", "zedxonesrc"],
            "ports": [5000, 5001],
            "receiver_ip": receiver_ip,
            "bitrate": bitrate,
            "exposure": exposure,
            "gain": gain,
        }],
    )

    camera_stream_1 = Node(
        package="spear_gui",
        executable="camera_streamer",
        name="camera_stream_1",
        output="screen",
        emulate_tty=True,
        parameters=[{
            "camera_sns": [305325257, 307142683],
            "sources": ["zedxonesrc", "zedxonesrc"],
            "ports": [5002, 5003],
            "receiver_ip": receiver_ip,
            "bitrate": bitrate,
            "exposure": exposure,
            "gain": gain,
        }],
    )

    camera_stream_2 = Node(
        package="spear_gui",
        executable="camera_streamer",
        name="camera_stream_2",
        output="screen",
        emulate_tty=True,
        parameters=[{
            "camera_sns": [308873104, 309256978],
            "sources": ["zedxonesrc", "zedxonesrc"],
            "ports": [5004, 5005],
            "receiver_ip": receiver_ip,
            "bitrate": bitrate,
            "exposure": exposure,
            "gain": gain,
        }],
    )

    camera_stream_3 = Node(
        package="spear_gui",
        executable="camera_streamer",
        name="camera_stream_3",
        output="screen",
        emulate_tty=True,
        parameters=[{
            "camera_sns": [44249482, 58896881],
            "sources": ["zedsrc", "zedsrc"],
            "ports": [5006, 5007],
            "receiver_ip": receiver_ip,
            "bitrate": bitrate,
            "exposure": exposure,
            "gain": gain,
        }],
    )

    return LaunchDescription([
        camera_stream_0,
        camera_stream_1,
        camera_stream_2,
        camera_stream_3,
    ])