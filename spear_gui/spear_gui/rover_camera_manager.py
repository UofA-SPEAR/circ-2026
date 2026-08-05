#!/usr/bin/env python3
"""
Jetson Camera Sender - ROS2 Node
---------------------------------
Streams multiple ZED cameras over UDP to a receiver machine.
Uses NVIDIA GPU-accelerated H.265 encoding (nvv4l2h265enc).
Listens on /camera_settings to update exposure/gain and restart streams.

Usage:
    python3 jetson_camera_sender.py
    ros2 run <package> jetson_camera_sender

Publishing settings:
    ros2 topic pub --once /camera_settings std_msgs/msg/String "data: '5000,exposure=10000,gain=30000'"
    # Format: "<port>,<setting>=<value>,<setting>=<value>,..."


Serials = [302801647, 303928833, 305325257, 307142683, 308873104, 309256978, 44249482, 58896881]


for zedsrc you control which image you get out via the stream-type property in the pipeline:
0 Left image only (default)
1 Right image only
2 Both left + right (composite, use zeddemux to split)
3 Depth map only
4 Left + depth (composite, use zeddemux to split)

"""

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import threading
import sys
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

# ──────────────────────── Config ────────────────────────

DEFAULT_RECEIVER_IP = "192.168.8.224"
DEFAULT_BITRATE = 1500000

CAMERAS = [
    {"camera_sn": 302801647, "source": "zedxonesrc", "port": 5000, "exposure": 10000, "gain": 30000},
    {"camera_sn": 303928833, "source": "zedxonesrc", "port": 5001, "exposure": 10000, "gain": 30000},
    {"camera_sn": 305325257, "source": "zedxonesrc", "port": 5002, "exposure": 10000, "gain": 30000},
    {"camera_sn": 307142683, "source": "zedxonesrc", "port": 5003, "exposure": 10000, "gain": 30000},
    {"camera_sn": 308873104, "source": "zedxonesrc", "port": 5004, "exposure": 10000, "gain": 30000},
    {"camera_sn": 309256978, "source": "zedxonesrc", "port": 5005, "exposure": 10000, "gain": 30000},
    {"camera_sn": 44249482, "source": "zedsrc", "port": 5006, "exposure": 10000, "gain": 30000},
    {"camera_sn": 58896881, "source": "zedsrc", "port": 5007, "exposure": 10000, "gain": 30000},
]

# ──────────────────────── Pipeline ────────────────────────

def build_pipeline(
    source,
    camera_sn,
    port,
    exposure,
    gain,
    receiver_ip,
    bitrate,
):
    if source == "zedxonesrc":
        src_props = (
            f"camera-sn={camera_sn} "
            f"ctrl-auto-exposure=false "
            f"ctrl-auto-exposure-range-min={exposure} "
            f"ctrl-auto-exposure-range-max={exposure} "
            f"ctrl-exposure-time={exposure} "
            f"ctrl-analog-gain={gain} "
        )
    elif source == "zedsrc":
        src_props = f"camera-sn={camera_sn} "
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
        f"! udpsink host={receiver_ip} port={port} sync=false async=false"
    )

# ──────────────────────── Camera Stream ────────────────────────

class CameraStream:
    def __init__(self, config, logger, receiver_ip, bitrate, enabled):
        self.source    = config["source"]
        self.camera_sn = config["camera_sn"]
        self.port      = config["port"]
        self.exposure  = config["exposure"]
        self.gain      = config["gain"]
        self.receiver_ip = receiver_ip
        self.bitrate = bitrate
        self.logger    = logger
        self.pipeline  = None
        self.loop      = None
        self.thread    = None
        self._lock     = threading.Lock()
        self.enabled = enabled
        self.failed = False
        self.last_failure = 0.0

    def start(self):
        self.enabled = True
        with self._lock:
            self._start_pipeline()

    def _start_pipeline(self):
        if not self.enabled or self.pipeline is not None:
            return
        pipeline_str = build_pipeline(
            self.source,
            self.camera_sn,
            self.port,
            self.exposure,
            self.gain,
            self.receiver_ip,
            self.bitrate,
        )
        self.logger.info(f"[{self.source} sn {self.camera_sn}] pipeline: {pipeline_str}")

        self.pipeline = Gst.parse_launch(pipeline_str)
        if not self.pipeline:
            self.logger.error(f"[{self.source} sn {self.camera_sn}] failed to create pipeline")
            self.failed = True
            self.last_failure = time.monotonic()
            return

        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        self.loop = GLib.MainLoop()
        bus.connect("message", self._on_message)

        ret = self.pipeline.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            self.logger.error(f"[{self.source} sn {self.camera_sn}] failed to set pipeline to PLAYING")
            self.failed = True
            self.last_failure = time.monotonic()
            return

        self.failed = False
        self.logger.info(
            f"[{self.source} sn {self.camera_sn}] streaming to "
            f"{self.receiver_ip}:{self.port} at {self.bitrate} bit/s"
        )
        self.thread = threading.Thread(target=self.loop.run, daemon=True)
        self.thread.start()

    def restart(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                self.logger.warn(f"[{self.source} sn {self.camera_sn}] unknown setting '{key}', ignoring")

        self.logger.info(f"[{self.source} sn {self.camera_sn}] restarting with exposure={self.exposure} gain={self.gain}")

        with self._lock:
            self._stop_pipeline()
            self._start_pipeline()

    def stop(self):
        self.enabled = False
        with self._lock:
            self._stop_pipeline()

    def set_enabled(self, enabled):
        if enabled:
            self.start()
        else:
            self.stop()

    def ensure_running(self):
        if not self.enabled or not self.failed:
            return
        if time.monotonic() - self.last_failure < 5.0:
            return
        with self._lock:
            self._stop_pipeline()
            self._start_pipeline()

    def _stop_pipeline(self):
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)
            self.pipeline = None
        if self.loop:
            self.loop.quit()
            self.loop = None
        if self.thread:
            self.thread.join(timeout=2)
            self.thread = None
        self.logger.info(f"[{self.source} sn {self.camera_sn}] stopped")

    def _on_message(self, bus, message):
        if message.type == Gst.MessageType.EOS:
            self.logger.info(f"[{self.source} sn {self.camera_sn}] end of stream")
            self.failed = True
            self.last_failure = time.monotonic()
            self.loop.quit()
        elif message.type == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            self.logger.error(f"[{self.source} sn {self.camera_sn}] error: {err}")
            self.logger.error(f"[{self.source} sn {self.camera_sn}] debug: {debug}")
            self.failed = True
            self.last_failure = time.monotonic()
            self.loop.quit()

# ──────────────────────── ROS2 Node ────────────────────────

class CameraSenderNode(Node):
    def __init__(self):
        super().__init__('camera_sender_node')
        Gst.init(None)

        self.declare_parameter('receiver_ip', DEFAULT_RECEIVER_IP)
        self.declare_parameter('bitrate', DEFAULT_BITRATE)
        self.declare_parameter(
            'enabled_ports',
            [camera['port'] for camera in CAMERAS],
        )
        receiver_ip = str(self.get_parameter('receiver_ip').value).strip()
        bitrate = max(
            250000,
            min(8000000, int(self.get_parameter('bitrate').value)),
        )
        enabled_ports = {
            int(port) for port in self.get_parameter('enabled_ports').value
        }
        if not receiver_ip:
            raise ValueError('receiver_ip cannot be empty')

        self.streams = {}
        for cam in CAMERAS:
            stream = CameraStream(
                cam,
                self.get_logger(),
                receiver_ip,
                bitrate,
                cam['port'] in enabled_ports,
            )
            self.streams[cam["port"]] = stream

        self.get_logger().info(f"Starting {len(self.streams)} camera stream(s)...")
        self.get_logger().info(f"Receiver: {receiver_ip}")
        self.get_logger().info(
            f"Configured video budget: {bitrate * len(enabled_ports)} bit/s"
        )
        for port, stream in self.streams.items():
            self.get_logger().info(f"  {stream.source} camera-sn={stream.camera_sn} -> port {port}")

        for stream in self.streams.values():
            if stream.enabled:
                stream.start()

        self.create_subscription(String, 'camera_settings', self._on_settings, 10)
        self.create_timer(2.0, self._monitor_streams)
        self.get_logger().info("Listening for settings on /camera_settings")
        self.get_logger().info("  Format: '<port>,<setting>=<value>,<setting>=<value>,...'")
        self.get_logger().info("  Settings: exposure, gain, bitrate, enabled")

    def _on_settings(self, msg):
        try:
            parts = msg.data.strip().split(',')
            if len(parts) < 2:
                self.get_logger().error(f"Invalid format: '{msg.data}' — expected '<port>,<setting>=<value>,...'")
                return

            port = int(parts[0])

            if port not in self.streams:
                self.get_logger().error(f"No stream on port {port}. Available: {list(self.streams.keys())}")
                return

            supported = {"exposure", "gain", "bitrate", "enabled"}
            kwargs = {}
            for part in parts[1:]:
                if '=' not in part:
                    self.get_logger().error(f"Invalid setting '{part}' — expected '<setting>=<value>'")
                    return
                key, val = part.split('=', 1)
                key = key.strip().lower()
                if key not in supported:
                    self.get_logger().error(f"Unknown setting '{key}'. Supported: {supported}")
                    return
                kwargs[key] = int(val)

            enabled = kwargs.pop('enabled', None)
            if enabled is not None and enabled not in (0, 1):
                self.get_logger().error('enabled must be 0 or 1')
                return
            bitrate = kwargs.get('bitrate')
            if bitrate is not None:
                kwargs['bitrate'] = max(250000, min(8000000, bitrate))
            if kwargs:
                self.streams[port].restart(**kwargs)
            if enabled is not None:
                self.streams[port].set_enabled(bool(enabled))

        except Exception as e:
            self.get_logger().error(f"Failed to parse settings message '{msg.data}': {e}")

    def _monitor_streams(self):
        for stream in self.streams.values():
            stream.ensure_running()

    def shutdown(self):
        self.get_logger().info("Shutting down streams...")
        for stream in self.streams.values():
            stream.stop()

# ──────────────────────── Main ────────────────────────

def main():
    rclpy.init()
    node = CameraSenderNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.shutdown()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()
