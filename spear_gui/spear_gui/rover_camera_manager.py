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
import time
import sys
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

# ──────────────────────── Config ────────────────────────

RECEIVER_IP = "192.168.10.11"  # IP of the machine receiving the stream
BITRATE     = 4000000           # bits per second

# Auto-reconnect behaviour for streams that die (e.g. the Jetson Argus
# daemon dropping a camera's socket under load). Backoff doubles per
# consecutive failure and resets after a stream has run cleanly for a while.
RETRY_BASE_DELAY   = 2      # seconds before first retry
RETRY_MAX_DELAY    = 30     # cap on backoff
RETRY_RESET_AFTER  = 60     # seconds of healthy streaming before backoff resets

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

def build_pipeline(source, camera_sn, port, exposure, gain):
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
        f"! nvv4l2h265enc bitrate={BITRATE} preset-level=2 "
        f"! h265parse "
        f"! rtph265pay config-interval=1 pt=96 "
        f"! udpsink host={RECEIVER_IP} port={port} sync=false"
    )

# ──────────────────────── Camera Stream ────────────────────────

# Serializes every pipeline open (initial start AND retries) across all
# streams. Opening a ZED camera blocks for seconds at a time and can hold
# the GIL while doing it; with several streams retrying concurrently that
# starved the main thread badly enough that SIGINT (Ctrl+C) stopped being
# processed at all. It also hammers the Argus daemon with simultaneous
# open attempts right when it's least able to cope. One at a time avoids both.
_pipeline_open_lock = threading.Lock()


class CameraStream:
    def __init__(self, config, logger):
        self.source    = config["source"]
        self.camera_sn = config["camera_sn"]
        self.port      = config["port"]
        self.exposure  = config["exposure"]
        self.gain      = config["gain"]
        self.logger    = logger
        self.pipeline  = None
        self.loop      = None
        self.thread    = None
        self._lock     = threading.Lock()

        self._stopping        = False   # True during an intentional/final stop
        self._retry_count     = 0
        self._retry_timer     = None
        self._retry_scheduled = False   # guards against duplicate retries for one failed attempt
        self._failure_lock    = threading.Lock()
        self._started_at      = None

    def start(self):
        with self._lock:
            self._start_pipeline()

    def _start_pipeline(self):
        pipeline_str = build_pipeline(self.source, self.camera_sn, self.port, self.exposure, self.gain)
        self.logger.info(f"[{self.source} sn {self.camera_sn}] pipeline: {pipeline_str}")

        # Only one stream may be mid-open (the blocking camera-open call) at
        # a time — see _pipeline_open_lock above.
        with _pipeline_open_lock:
            self.pipeline = Gst.parse_launch(pipeline_str)
            if not self.pipeline:
                self.logger.error(f"[{self.source} sn {self.camera_sn}] failed to create pipeline")
                self._handle_failure()
                return

            bus = self.pipeline.get_bus()
            bus.add_signal_watch()
            self.loop = GLib.MainLoop()
            bus.connect("message", self._on_message)

            ret = self.pipeline.set_state(Gst.State.PLAYING)
            if ret == Gst.StateChangeReturn.FAILURE:
                self.logger.error(f"[{self.source} sn {self.camera_sn}] failed to set pipeline to PLAYING")
                self._handle_failure()
                return

        self.logger.info(f"[{self.source} sn {self.camera_sn}] streaming to {RECEIVER_IP}:{self.port}")
        self._started_at = time.monotonic()
        self.thread = threading.Thread(target=self.loop.run, daemon=True)
        self.thread.start()

    def restart(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                self.logger.warn(f"[{self.source} sn {self.camera_sn}] unknown setting '{key}', ignoring")

        self.logger.info(f"[{self.source} sn {self.camera_sn}] restarting with exposure={self.exposure} gain={self.gain}")

        self._cancel_retry_timer()
        self._retry_count = 0
        with self._lock:
            self._stop_pipeline()
            self._start_pipeline()

    def stop(self):
        self._stopping = True
        self._cancel_retry_timer()
        with self._lock:
            self._stop_pipeline()

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
            self.loop.quit()
            self._handle_failure()
        elif message.type == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            self.logger.error(f"[{self.source} sn {self.camera_sn}] error: {err}")
            self.logger.error(f"[{self.source} sn {self.camera_sn}] debug: {debug}")
            self.loop.quit()
            self._handle_failure()

    # ─────────────── Auto-reconnect ───────────────
    # Runs on the GStreamer bus-callback thread (which is `self.thread`), so
    # the actual restart is deferred to a timer thread — stop_pipeline()
    # joins self.thread, and a thread can't join itself.

    def _handle_failure(self):
        # A single failed open/stream can raise multiple signals for the
        # same event (a synchronous set_state() FAILURE plus one or more
        # async bus ERROR messages). Only the first schedules a retry;
        # the rest are ignored until that retry attempt actually runs.
        with self._failure_lock:
            if self._stopping or self._retry_scheduled:
                return
            self._retry_scheduled = True

        if self._started_at is not None and (time.monotonic() - self._started_at) > RETRY_RESET_AFTER:
            self._retry_count = 0

        delay = min(RETRY_BASE_DELAY * (2 ** self._retry_count), RETRY_MAX_DELAY)
        self._retry_count += 1

        self.logger.warn(
            f"[{self.source} sn {self.camera_sn}] stream died, retrying in {delay:.0f}s "
            f"(attempt {self._retry_count})"
        )
        self._retry_timer = threading.Timer(delay, self._auto_restart)
        self._retry_timer.daemon = True
        self._retry_timer.start()

    def _auto_restart(self):
        with self._failure_lock:
            self._retry_scheduled = False
        if self._stopping:
            return
        with self._lock:
            self._stop_pipeline()
            self._start_pipeline()

    def _cancel_retry_timer(self):
        with self._failure_lock:
            self._retry_scheduled = False
        if self._retry_timer:
            self._retry_timer.cancel()
            self._retry_timer = None

# ──────────────────────── ROS2 Node ────────────────────────

class CameraSenderNode(Node):
    def __init__(self):
        super().__init__('camera_sender_node')
        Gst.init(None)

        self.streams = {}
        for cam in CAMERAS:
            stream = CameraStream(cam, self.get_logger())
            self.streams[cam["port"]] = stream

        self.get_logger().info(f"Starting {len(self.streams)} camera stream(s)...")
        self.get_logger().info(f"Receiver: {RECEIVER_IP}")
        for port, stream in self.streams.items():
            self.get_logger().info(f"  {stream.source} camera-sn={stream.camera_sn} -> port {port}")

        for stream in self.streams.values():
            stream.start()

        self.create_subscription(String, 'camera_settings', self._on_settings, 10)
        self.get_logger().info("Listening for settings on /camera_settings")
        self.get_logger().info("  Format: '<port>,<setting>=<value>,<setting>=<value>,...'")
        self.get_logger().info("  Settings: exposure, gain")

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

            supported = {"exposure", "gain"}
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

            self.streams[port].restart(**kwargs)

        except Exception as e:
            self.get_logger().error(f"Failed to parse settings message '{msg.data}': {e}")

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
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == "__main__":
    main()