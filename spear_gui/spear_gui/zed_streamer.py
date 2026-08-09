#!/usr/bin/env python3
import json
import threading

import rclpy
from rclpy.node import Node
from diagnostic_msgs.srv import AddDiagnostics

import gi
gi.require_version("Gst", "1.0")
from gi.repository import Gst


# camera-resolution enum values for zedsrc (from the Stereolabs docs).
RESOLUTIONS = {
    "HD2K": 0,      # 2208x1242, USB3 only
    "HD1080": 1,    # 1920x1080, USB3/GMSL2
    "HD1200": 2,    # 1920x1200, GMSL2 only
    "HD720": 3,     # 1280x720,  USB3 only
    "SVGA": 4,      # 960x600,   GMSL2 only
    "VGA": 5,       # 672x376,   USB3 only
}

# 30 FPS is NOT valid at every zedsrc resolution: on GMSL2, HD1200 and SVGA
# require 60. This table assumes GMSL2 (ZED X) cameras.
# VERIFY against your camera model with: gst-inspect-1.0 zedsrc
FPS = {
    "HD2K": 15,
    "HD1080": 30,
    "HD1200": 60,
    "HD720": 30,
    "SVGA": 60,
    "VGA": 30,
}


def build_pipeline(camera_sn, receiver_ip, port, resolution, bitrate):
    return (
        f"zedsrc "
        f"camera-sn={camera_sn} "
        f"camera-resolution={RESOLUTIONS[resolution]} "
        f"camera-fps={FPS[resolution]} "
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


class ZedStreamer(Node):
    def __init__(self):
        super().__init__("zed_streamer")

        self.declare_parameter("camera_sns", [0])
        self.declare_parameter("ports", [5006])
        self.declare_parameter("receiver_ip", "192.168.10.11")
        self.declare_parameter("resolution", "HD1080")
        self.declare_parameter("bitrate", 4000000)

        g = lambda n: self.get_parameter(n).value

        sns, ports = g("camera_sns"), g("ports")
        if len(sns) != len(ports):
            raise ValueError(
                f"camera_sns ({len(sns)}) and ports ({len(ports)}) "
                f"must be the same length"
            )

        self.receiver_ip = g("receiver_ip")

        # per-camera config; the restart service mutates this
        self.cams = {}
        for sn, port in zip(sns, ports):
            self.cams[int(sn)] = {
                "port": port,
                "resolution": g("resolution"),
                "bitrate": g("bitrate"),
                "pipeline": None,
            }

        Gst.init(None)
        self.lock = threading.Lock()

        self.srv = self.create_service(
            AddDiagnostics, "~/restart_camera", self.on_restart
        )

        # build off __init__ so a slow camera open can't make the process
        # unkillable; one-shot timer fires once spin() is running
        self.start_timer = self.create_timer(0.1, self.start_all)

    # ---------- pipeline management ----------

    def stop(self, sn):
        cam = self.cams[sn]
        if cam["pipeline"] is not None:
            cam["pipeline"].set_state(Gst.State.NULL)
            cam["pipeline"] = None

    def start(self, sn):
        cam = self.cams[sn]
        pipeline_str = build_pipeline(
            sn, self.receiver_ip, cam["port"], cam["resolution"], cam["bitrate"]
        )
        self.get_logger().info(f"[{sn}] {pipeline_str}")

        pipeline = Gst.parse_launch(pipeline_str)
        bus = pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_bus_message, sn)

        pipeline.set_state(Gst.State.PLAYING)
        cam["pipeline"] = pipeline
        self.get_logger().info(
            f"[{sn}] streaming -> {self.receiver_ip}:{cam['port']} "
            f"({cam['resolution']} @ {cam['bitrate']})"
        )

    def start_all(self):
        self.start_timer.cancel()
        started = 0
        with self.lock:
            for sn in self.cams:
                try:
                    self.start(sn)
                    started += 1
                except Exception as e:
                    self.get_logger().error(f"[{sn}] failed to start: {e}")
        self.get_logger().info(f"{started}/{len(self.cams)} streams running")

    # ---------- service ----------

    def on_restart(self, request, response):
        # request.load_namespace carries the JSON payload:
        #   {"camera_sn": 44249482, "resolution": "HD1080", "bitrate": 4000000}
        # resolution and bitrate are optional; omitted keys keep current value.
        try:
            req = json.loads(request.load_namespace)
        except Exception as e:
            response.success = False
            response.message = f"bad json: {e}"
            return response

        sn = req.get("camera_sn")
        if sn is None:
            response.success = False
            response.message = "missing camera_sn"
            return response
        sn = int(sn)

        if sn not in self.cams:
            response.success = False
            response.message = f"unknown camera_sn {sn}, have {list(self.cams)}"
            return response

        resolution = req.get("resolution")
        if resolution is not None and resolution not in RESOLUTIONS:
            response.success = False
            response.message = (
                f"unknown resolution {resolution}, "
                f"expected one of {list(RESOLUTIONS)}"
            )
            return response

        # lock serializes restarts so two cameras never init at once
        with self.lock:
            cam = self.cams[sn]
            if resolution is not None:
                cam["resolution"] = resolution
            if req.get("bitrate") is not None:
                cam["bitrate"] = int(req["bitrate"])

            self.get_logger().info(f"[{sn}] restarting")
            try:
                self.stop(sn)
                self.start(sn)
            except Exception as e:
                self.get_logger().error(f"[{sn}] restart failed: {e}")
                response.success = False
                response.message = f"restart failed: {e}"
                return response

        response.success = True
        response.message = (
            f"{sn} restarted at {cam['resolution']} bitrate {cam['bitrate']}"
        )
        return response

    # ---------- bus ----------

    def on_bus_message(self, bus, msg, sn):
        if msg.type == Gst.MessageType.ERROR:
            err, dbg = msg.parse_error()
            self.get_logger().error(f"[{sn}] gst error: {err} | {dbg}")
        elif msg.type == Gst.MessageType.EOS:
            self.get_logger().warn(f"[{sn}] gst EOS")

    def destroy_node(self):
        for sn in self.cams:
            self.stop(sn)
        super().destroy_node()


def main():
    rclpy.init()
    node = ZedStreamer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()