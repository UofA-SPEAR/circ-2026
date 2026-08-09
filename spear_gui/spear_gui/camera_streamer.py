#!/usr/bin/env python3
import rclpy
from rclpy.node import Node

import gi
gi.require_version("Gst", "1.0")
from gi.repository import Gst


def build_pipeline(source, camera_sn, receiver_ip, port, bitrate, exposure, gain):
    if source == "zedxonesrc":
        src_props = (
            f"camera-sn={camera_sn} "
            f"ctrl-auto-exposure=false "
            f"ctrl-auto-exposure-range-min={exposure} "
            f"ctrl-auto-exposure-range-max={exposure} "
            f"ctrl-exposure-time={exposure} "
            f"ctrl-analog-gain={gain} "
        )
    else:
        src_props = f"camera-sn={camera_sn} "

    return (
        f"{source} {src_props}"
        f"! queue "
        f"! videoconvert "
        f"! video/x-raw,format=BGRx "
        f"! nvvidconv "
        f"! video/x-raw(memory:NVMM),format=NV12 "
        f"! nvv4l2h265enc bitrate={bitrate} preset-level=2 "
        f"! h265parse "
        f"! rtph265pay config-interval=1 pt=96 "
        f"! udpsink host={receiver_ip} port={port} sync=false"
    )


class CameraStreamNode(Node):
    def __init__(self):
        super().__init__("camera_stream")

        # parallel arrays, one entry per camera
        self.declare_parameter("camera_sns", [0])
        self.declare_parameter("sources", ["zedxonesrc"])
        self.declare_parameter("ports", [5000])
        # shared settings
        self.declare_parameter("receiver_ip", "192.168.10.11")
        self.declare_parameter("bitrate", 4000000)
        self.declare_parameter("exposure", 10000)
        self.declare_parameter("gain", 30000)

        g = lambda n: self.get_parameter(n).value

        sns, sources, ports = g("camera_sns"), g("sources"), g("ports")
        if not (len(sns) == len(sources) == len(ports)):
            raise ValueError(
                f"camera_sns ({len(sns)}), sources ({len(sources)}) and "
                f"ports ({len(ports)}) must be the same length"
            )

        Gst.init(None)
        self.pipelines = []

        for sn, source, port in zip(sns, sources, ports):
            pipeline_str = build_pipeline(
                source, sn, g("receiver_ip"), port,
                g("bitrate"), g("exposure"), g("gain"),
            )
            self.get_logger().info(f"[{sn}] {pipeline_str}")

            try:
                pipeline = Gst.parse_launch(pipeline_str)
            except Exception as e:
                self.get_logger().error(f"[{sn}] failed to build pipeline: {e}")
                continue

            bus = pipeline.get_bus()
            bus.add_signal_watch()
            bus.connect("message", self.on_bus_message, sn)

            pipeline.set_state(Gst.State.PLAYING)
            self.pipelines.append((sn, pipeline))
            self.get_logger().info(f"[{sn}] streaming -> {g('receiver_ip')}:{port}")

        self.get_logger().info(f"{len(self.pipelines)}/{len(sns)} streams running")

    def on_bus_message(self, bus, msg, sn):
        # one camera dying doesn't take down the others
        if msg.type == Gst.MessageType.ERROR:
            err, dbg = msg.parse_error()
            self.get_logger().error(f"[{sn}] gst error: {err} | {dbg}")
        elif msg.type == Gst.MessageType.EOS:
            self.get_logger().warn(f"[{sn}] gst EOS")

    def destroy_node(self):
        for sn, pipeline in self.pipelines:
            pipeline.set_state(Gst.State.NULL)
        super().destroy_node()


def main():
    rclpy.init()
    node = CameraStreamNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()