#!/usr/bin/env python3
"""
ZED Camera Sender - ROS2 Node (single camera)
-----------------------------------------------
Owns exactly one ZED camera and streams it over UDP using NVIDIA GPU H.265
encoding (nvv4l2h265enc). One of these runs per physical camera — launch
one instance per camera via a launch file rather than looping over cameras
inside a single process. That way a stuck/wedged camera (blocking camera
opens on Jetson can hold the GIL indefinitely and even survive Ctrl+C) can
only ever take down its own process, never the other cameras.

Listens on /camera_settings (shared across all camera nodes) and only acts
on messages addressed to its own port; ignores everything else.

Actual camera opens are serialized across all running instances via a flock
on a shared file (see _StaggeredOpen). The process keeps that startup gate
until its first encoded buffer arrives, rather than releasing it when the
asynchronous PLAYING transition is merely requested. The wait is bounded so
one wedged camera can only delay the others, not block them forever.

Usage (standalone, for testing one camera):
    ros2 run spear_gui camera_sender_node --ros-args \\
        -p camera_sn:=302801647 -p source:=zedxonesrc -p port:=5000 \\
        -p receiver_ip:=192.168.10.11 -p exposure:=10000 -p gain:=30000

Publishing settings (same wire format as before, shared across all cameras):
    ros2 topic pub --once /camera_settings std_msgs/msg/String "data: '5000,exposure=10000,gain=30000'"
    # Format: "<port>,<setting>=<value>,<setting>=<value>,..."
"""

import fcntl
import threading
import time

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from spear_gui.camera_pipeline import build_pipeline

# Auto-reconnect behaviour for a stream that dies (e.g. the Jetson Argus
# daemon dropping the camera's socket under load). Backoff doubles per
# consecutive failure and resets after the stream has run cleanly for a
# while.
RETRY_BASE_DELAY  = 2    # seconds before first retry
RETRY_MAX_DELAY   = 30   # cap on backoff
RETRY_RESET_AFTER = 60   # seconds of healthy streaming before backoff resets

# Camera opens are staggered across ALL camera_sender_node processes via a
# flock on this shared file — every camera is its own OS process now, so a
# plain in-process lock can't reach across them. Without this, launching N
# cameras together means N simultaneous cold-opens hammering zed_x_daemon /
# nvargus-daemon at once, which is exactly the kind of load that has
# triggered real kernel-driver bugs in this camera stack. The wait is
# bounded so a genuinely wedged camera can only delay others, never block
# them forever — that would defeat the point of splitting cameras into
# separate processes in the first place.
_OPEN_LOCK_PATH    = "/tmp/.camera_sender_open.lock"
_OPEN_LOCK_TIMEOUT = 60    # seconds to wait for another camera to finish opening
_OPEN_LOCK_POLL    = 0.2

# A process does not release the global startup gate merely because GStreamer
# accepted PLAYING. It holds the gate until an encoded RTP buffer is observed,
# or until this timeout expires. This is the important distinction between a
# requested state transition and a camera that is genuinely producing frames.
FIRST_BUFFER_TIMEOUT = 20.0


class _StaggeredOpen:
    def __init__(self, logger=None, label=""):
        self._logger = logger
        self._label  = label
        self._got_lock = False

    def __enter__(self):
        self._fd = open(_OPEN_LOCK_PATH, "w")
        deadline = time.monotonic() + _OPEN_LOCK_TIMEOUT
        while True:
            try:
                fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                self._got_lock = True
                return self
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    # Proceed unlocked rather than wait forever on a wedged
                    # holder — but this is exactly the condition that lets
                    # opens pile up and collide, so make it loud.
                    if self._logger:
                        self._logger.warn(
                            f"{self._label}gave up waiting {_OPEN_LOCK_TIMEOUT}s for another "
                            f"camera to finish opening — proceeding unlocked, another camera "
                            f"may be wedged"
                        )
                    return self
                time.sleep(_OPEN_LOCK_POLL)

    def __exit__(self, *exc_info):
        try:
            if self._got_lock:
                fcntl.flock(self._fd, fcntl.LOCK_UN)
        finally:
            self._fd.close()


class CameraSenderNode(Node):
    def __init__(self, node_name='camera_sender_node', **node_kwargs):
        super().__init__(node_name, **node_kwargs)
        Gst.init(None)

        self.declare_parameter('camera_sn', 302801647)
        self.declare_parameter('source', 'zedxonesrc')
        self.declare_parameter('port', 5000)
        self.declare_parameter('receiver_ip', '192.168.10.11')
        self.declare_parameter('bitrate', 4000000)
        self.declare_parameter('exposure', 10000)
        self.declare_parameter('gain', 30000)
        self.declare_parameter('camera_resolution', 2)
        self.declare_parameter('camera_fps', 30)
        self.declare_parameter('stream_type', 0)
        self.declare_parameter('first_buffer_timeout', FIRST_BUFFER_TIMEOUT)

        self.camera_sn   = self.get_parameter('camera_sn').value
        self.source      = self.get_parameter('source').value
        self.port        = self.get_parameter('port').value
        self.receiver_ip = self.get_parameter('receiver_ip').value
        self.bitrate     = self.get_parameter('bitrate').value
        self.exposure    = self.get_parameter('exposure').value
        self.gain        = self.get_parameter('gain').value
        self.camera_resolution = self.get_parameter('camera_resolution').value
        self.camera_fps = self.get_parameter('camera_fps').value
        self.stream_type = self.get_parameter('stream_type').value
        self.first_buffer_timeout = self.get_parameter(
            'first_buffer_timeout'
        ).value

        self.pipeline = None
        self.loop     = None
        self.thread   = None
        self._lock    = threading.Lock()

        self._stopping        = False   # True during an intentional/final stop
        self._retry_count     = 0
        self._retry_timer     = None
        self._retry_scheduled = False   # guards against duplicate retries for one failed attempt
        self._failure_lock    = threading.Lock()
        self._started_at      = None
        self._startup_event   = threading.Event()
        self._first_buffer_seen = False

        # Heartbeat for an external watchdog: as long as this process is
        # alive and not wedged, `status` publishes periodically. A watchdog
        # noticing this topic go stale is the signal a wedged camera needs
        # to be killed and respawned — see the discussion this came out of.
        self._status     = 'starting'
        self.status_pub  = self.create_publisher(String, 'status', 10)
        self.create_timer(2.0, self._publish_heartbeat)

        self.get_logger().info(
            f"[{self.source} sn {self.camera_sn}] -> {self.receiver_ip}:{self.port}"
        )

        self.create_subscription(String, 'camera_settings', self._on_settings, 10)

        self.start()

    # ──────────────────────── Pipeline lifecycle ────────────────────────

    def start(self):
        with self._lock:
            self._start_pipeline()

    def _start_pipeline(self):
        self._startup_event.clear()
        self._first_buffer_seen = False
        self._set_status('opening')

        pipeline_str = build_pipeline(
            self.source, self.camera_sn, self.receiver_ip, self.port,
            self.bitrate, self.exposure, self.gain,
            self.camera_resolution, self.camera_fps, self.stream_type,
        )
        self.get_logger().info(f"pipeline: {pipeline_str}")

        # Stagger the actual open against every other camera_sender_node
        # process — see _StaggeredOpen above.
        with _StaggeredOpen(self.get_logger(), f"port {self.port}: "):
            try:
                self.pipeline = Gst.parse_launch(pipeline_str)
            except GLib.Error as exc:
                self.get_logger().error(f"failed to create pipeline: {exc}")
                self._handle_failure()
                return

            if not self.pipeline:
                self.get_logger().error("failed to create pipeline")
                self._handle_failure()
                return

            bus = self.pipeline.get_bus()
            bus.add_signal_watch()
            self.loop = GLib.MainLoop()
            bus.connect("message", self._on_message)

            payloader = self.pipeline.get_by_name('pay')
            if payloader is None:
                self.get_logger().error("pipeline has no RTP payloader")
                self._handle_failure()
                self._stop_pipeline()
                return

            payloader.get_static_pad('src').add_probe(
                Gst.PadProbeType.BUFFER,
                self._on_first_encoded_buffer,
            )

            # Run the bus loop before requesting PLAYING so asynchronous
            # startup errors can wake the first-buffer wait immediately.
            self.thread = threading.Thread(target=self.loop.run, daemon=True)
            self.thread.start()

            ret = self.pipeline.set_state(Gst.State.PLAYING)
            if ret == Gst.StateChangeReturn.FAILURE:
                self.get_logger().error("failed to set pipeline to PLAYING")
                self._handle_failure()
                self._stop_pipeline()
                return

            self.get_logger().info(
                "PLAYING requested; waiting for the first encoded buffer "
                f"(timeout {self.first_buffer_timeout:.1f}s)"
            )
            self._startup_event.wait(timeout=self.first_buffer_timeout)

            if not self._first_buffer_seen:
                self.get_logger().error(
                    "camera produced no encoded buffers during startup"
                )
                self._handle_failure()
                self._stop_pipeline()
                return

        self.get_logger().info(
            f"first encoded buffer received; streaming to "
            f"{self.receiver_ip}:{self.port}"
        )
        self._started_at = time.monotonic()
        self._set_status('streaming')

    def _on_first_encoded_buffer(self, pad, info):
        """Confirm real data flow, then remove this one-shot pad probe."""
        self._first_buffer_seen = True
        self._startup_event.set()
        return Gst.PadProbeReturn.REMOVE

    def restart(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                self.get_logger().warn(f"unknown setting '{key}', ignoring")

        self.get_logger().info(f"restarting with exposure={self.exposure} gain={self.gain}")

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
        self._set_status('stopped')

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
        self.get_logger().info("stopped")

    def _on_message(self, bus, message):
        if message.type == Gst.MessageType.EOS:
            self.get_logger().info("end of stream")
            self._startup_event.set()
            if self.loop:
                self.loop.quit()
            self._handle_failure()
        elif message.type == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            self.get_logger().error(f"error: {err}")
            self.get_logger().error(f"debug: {debug}")
            self._startup_event.set()
            if self.loop:
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

        self._set_status('retrying')

        if self._started_at is not None and (time.monotonic() - self._started_at) > RETRY_RESET_AFTER:
            self._retry_count = 0

        delay = min(RETRY_BASE_DELAY * (2 ** self._retry_count), RETRY_MAX_DELAY)
        self._retry_count += 1

        self.get_logger().warn(f"stream died, retrying in {delay:.0f}s (attempt {self._retry_count})")
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

    # ──────────────────────── Settings ────────────────────────

    def _on_settings(self, msg):
        try:
            parts = msg.data.strip().split(',')
            if len(parts) < 2:
                return

            port = int(parts[0])
            if port != self.port:
                return  # addressed to a different camera

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

            self.restart(**kwargs)

        except Exception as e:
            self.get_logger().error(f"Failed to parse settings message '{msg.data}': {e}")

    # ──────────────────────── Heartbeat ────────────────────────

    def _set_status(self, status):
        self._status = status
        self._publish_heartbeat()

    def _publish_heartbeat(self):
        if not rclpy.ok():
            return
        msg = String()
        msg.data = f"{self._status}|sn={self.camera_sn}|port={self.port}"
        try:
            self.status_pub.publish(msg)
        except Exception:
            pass  # context was torn down between the ok() check and publish()

    def shutdown(self):
        self.get_logger().info("shutting down")
        self.stop()


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
