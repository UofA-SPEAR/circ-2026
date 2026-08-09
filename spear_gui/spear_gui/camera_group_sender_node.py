#!/usr/bin/env python3
"""Run one isolated two-camera sender process.

Each child camera remains an independent ROS node and GStreamer pipeline.  A
normal GStreamer failure is retried per camera.  If a native ZED/NVIDIA crash
terminates the process, ROS launch respawns this two-camera group without
taking down the other six streams.
"""

import argparse

import rclpy
from rclpy.executors import MultiThreadedExecutor
from rclpy.parameter import Parameter

from spear_gui.camera_groups import get_camera_group
from spear_gui.camera_sender_node import CameraSenderNode


def _parse_args(args=None):
    parser = argparse.ArgumentParser(
        description="Run one isolated two-camera rover streaming group."
    )
    parser.add_argument("--group-index", type=int, required=True)
    parser.add_argument("--receiver-ip", required=True)
    parser.add_argument("--bitrate", type=int, default=4000000)
    parser.add_argument("--camera-resolution", type=int, default=2)
    parser.add_argument("--camera-fps", type=int, default=30)
    parser.add_argument("--stream-type", type=int, default=0)
    return parser.parse_known_args(args)


def _camera_overrides(camera, options):
    values = {
        "camera_sn": camera["camera_sn"],
        "source": camera["source"],
        "port": camera["port"],
        "receiver_ip": options.receiver_ip,
        "bitrate": options.bitrate,
        "exposure": camera["exposure"],
        "gain": camera["gain"],
        "camera_resolution": options.camera_resolution,
        "camera_fps": options.camera_fps,
        "stream_type": options.stream_type,
    }
    return [Parameter(name, value=value) for name, value in values.items()]


def main(args=None):
    options, ros_args = _parse_args(args)
    camera_group = get_camera_group(options.group_index)

    rclpy.init(args=ros_args)
    nodes = []
    executor = MultiThreadedExecutor(num_threads=4)

    try:
        # Construction starts each pipeline. Do this sequentially so the
        # second encoder is not allocated until the first emits real data.
        for camera in camera_group:
            node = CameraSenderNode(
                node_name=f"camera_sender_{camera['port']}",
                parameter_overrides=_camera_overrides(camera, options),
            )
            nodes.append(node)
            executor.add_node(node)

        ports = ", ".join(str(camera["port"]) for camera in camera_group)
        nodes[0].get_logger().info(
            f"camera group {options.group_index} ready (UDP ports {ports})"
        )
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        for node in nodes:
            try:
                executor.remove_node(node)
                node.shutdown()
                node.destroy_node()
            except Exception:
                pass
        executor.shutdown()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
