#!/usr/bin/env python3
"""
multi_camera_streamer_node.py

ROS2 (rclpy) node that launches and manages 8 independent GStreamer
streaming pipelines (ZED X One / ZED GMSL cameras -> H265 -> RTP/UDP).

Design goals (per requirements):
  - Single process, single node, managing all 8 pipelines internally.
  - A camera missing/failing at launch must NOT prevent the others from
    starting, and must NOT crash the node.
  - A camera that fails/disconnects at runtime must NOT kill the node or
    affect the other cameras.
  - Failure detection per pipeline is via the GStreamer bus (ERROR/EOS
    messages), which is what a driver-level GMSL disconnect surfaces as.
  - IMPORTANT: when a camera dies at runtime (disconnect), the node marks
    it dead but does NOT tear its pipeline down. Calling set_state(NULL) on
    a disconnected ZED/GMSL device crashes inside NVIDIA/Stereolabs native
    code (sl::Camera::close -> libnvargus), and a native segfault cannot be
    caught from Python, so it would take the whole node (all 8 cameras)
    down. The dead pipeline is intentionally left in place (leaked). This is
    a deliberate trade: a leaked idle pipeline in exchange for the node
    surviving a mid-stream unplug. Full recovery of that camera requires a
    process restart, which is acceptable because GMSL cannot be hot-
    replugged in this deployment anyway.
  - GMSL cameras cannot be hot-replugged in this deployment, so once a
    camera is marked dead, the node makes no further attempt to recover
    it (no retry loop). It stays down until the process/host is restarted.
  - No ROS topics/services are published. This node's job is purely to
    keep the GStreamer streams alive.

Requires: PyGObject (gi) with Gst 1.0, rclpy.
"""

import threading
import time

import rclpy
from rclpy.node import Node

import gi
gi.require_version("Gst", "1.0")
from gi.repository import Gst, GLib  # noqa: E402


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

RECEIVER_IP = "192.168.10.11"  # IP of the machine receiving the stream
BITRATE = 4000000              # bits per second

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

def build_pipeline_str(source: str, camera_sn: int, port: int, exposure: int, gain: int) -> str:
    """Build the gst-launch style pipeline description string for one camera."""
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
        f"{source} name=src {src_props}"
        f"! queue "
        f"! videoconvert "
        f"! video/x-raw,format=BGRx "
        f"! nvvidconv "
        f"! video/x-raw(memory:NVMM),format=NV12 "
        f"! nvv4l2h265enc bitrate={BITRATE} preset-level=2 "
        f"! h265parse "
        f"! rtph265pay config-interval=1 pt=96 "
        f"! udpsink name=sink host={RECEIVER_IP} port={port} sync=false"
    )


class CameraStream:
    """
    Owns one GStreamer pipeline for one camera, including its bus watch
    and buffer-flow liveness tracking. All failures are isolated here and
    reported to the parent node via logging; nothing raises out of this
    class during normal operation.
    """

    def __init__(self, node: Node, cam_cfg: dict):
        self.node = node
        self.cfg = cam_cfg
        self.camera_sn = cam_cfg["camera_sn"]
        self.port = cam_cfg["port"]

        self.pipeline: Gst.Pipeline | None = None
        self.bus_watch_id = None

        self.lock = threading.Lock()
        self.alive = False
        self.started_at = 0.0
        # Set True when the camera dies at runtime (bus ERROR/EOS = device
        # disconnected). Once set, we must NEVER call set_state(NULL) on this
        # pipeline: the ZED close() path segfaults on a vanished device.
        self.failed_at_runtime = False

    # ---- lifecycle ------------------------------------------------------

    def start(self) -> bool:
        """
        Build and start the pipeline. Returns True if the pipeline reached
        at least PLAYING request state without immediate error. Any
        exception is caught and logged; failure here just leaves this
        camera marked not-alive, it does not propagate.
        """
        pipeline_str = build_pipeline_str(
            self.cfg["source"], self.camera_sn, self.port,
            self.cfg["exposure"], self.cfg["gain"],
        )

        try:
            self.node.get_logger().info(
                f"[cam {self.camera_sn}] starting pipeline on port {self.port}"
            )
            pipeline = Gst.parse_launch(pipeline_str)
        except GLib.Error as e:
            self.node.get_logger().error(
                f"[cam {self.camera_sn}] failed to construct pipeline: {e}"
            )
            return False
        except Exception as e:  # defensive: never let a bad camera kill the node
            self.node.get_logger().error(
                f"[cam {self.camera_sn}] unexpected error constructing pipeline: {e}"
            )
            return False

        self.pipeline = pipeline

        # Bus watch for ERROR / EOS / WARNING
        bus = pipeline.get_bus()
        bus.add_signal_watch()
        self.bus_watch_id = bus.connect("message", self._on_bus_message)

        ret = pipeline.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            self.node.get_logger().error(
                f"[cam {self.camera_sn}] pipeline refused to enter PLAYING state"
            )
            self._teardown_locked()
            return False

        now = time.monotonic()
        with self.lock:
            self.alive = True
            self.started_at = now

        self.node.get_logger().info(f"[cam {self.camera_sn}] pipeline PLAYING")
        return True

    def stop(self, reason: str = "shutdown"):
        """
        Clean teardown for a STILL-HEALTHY pipeline (e.g. node shutdown of a
        camera whose device is still physically present). This calls
        set_state(NULL), which runs the ZED close() path in native code.
        That path is ONLY safe when the device still exists.

        NEVER call this on a camera that has died at runtime (unplugged):
        for that use mark_failed(), which deliberately skips teardown. As a
        safety net this method also refuses to tear down a pipeline flagged
        failed_at_runtime, so a stray shutdown call can't trigger the crash.
        """
        with self.lock:
            if self.failed_at_runtime:
                # Device is gone. Touching the pipeline (set_state NULL ->
                # sl::Camera::close) segfaults in native code. Leave it be.
                self.alive = False
                return
            was_alive = self.alive
            self.alive = False
        if was_alive:
            self.node.get_logger().warn(f"[cam {self.camera_sn}] stopping pipeline ({reason})")
        self._teardown_locked()

    def mark_failed(self, reason: str):
        """
        Runtime-failure handler: the device died mid-stream (bus ERROR/EOS).

        Marks the camera dead but DELIBERATELY does not tear the pipeline
        down. set_state(NULL) on a disconnected ZED/GMSL device crashes
        inside libnvargus/libsl_zed (sl::Camera::close), and a native
        segfault cannot be caught from Python, so it would take the whole
        node — and every other camera — down with it.

        The pipeline is intentionally left in place (leaked). It will never
        stream again and is only recovered by restarting the process, which
        matches the GMSL no-hot-replug constraint. This is the trade that
        keeps one camera's disconnect from killing the node.
        """
        with self.lock:
            already = self.failed_at_runtime
            self.alive = False
            self.failed_at_runtime = True
        if not already:
            self.node.get_logger().warn(
                f"[cam {self.camera_sn}] marking dead WITHOUT teardown ({reason}); "
                f"pipeline intentionally left in place to avoid native close() crash"
            )

    def _teardown_locked(self):
        if self.pipeline is not None:
            try:
                bus = self.pipeline.get_bus()
                if self.bus_watch_id is not None:
                    bus.disconnect(self.bus_watch_id)
                    self.bus_watch_id = None
                bus.remove_signal_watch()
            except Exception:
                pass
            try:
                self.pipeline.set_state(Gst.State.NULL)
            except Exception:
                pass
            self.pipeline = None

    # ---- callbacks --------------------------------------------------------

    def _on_bus_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.ERROR:
            with self.lock:
                already = self.failed_at_runtime
            if not already:
                err, debug = message.parse_error()
                self.node.get_logger().error(
                    f"[cam {self.camera_sn}] GStreamer ERROR: {err} ({debug})"
                )
            # Runtime failure: mark dead but DO NOT tear down (see mark_failed).
            self.mark_failed(reason="bus error")
        elif t == Gst.MessageType.EOS:
            with self.lock:
                already = self.failed_at_runtime
            if not already:
                self.node.get_logger().error(
                    f"[cam {self.camera_sn}] GStreamer EOS received unexpectedly"
                )
            self.mark_failed(reason="unexpected EOS")
        elif t == Gst.MessageType.WARNING:
            warn, debug = message.parse_warning()
            self.node.get_logger().warn(
                f"[cam {self.camera_sn}] GStreamer WARNING: {warn} ({debug})"
            )
        # Other message types (STATE_CHANGED, STREAM_STATUS, etc.) are ignored.
        return True


class MultiCameraStreamerNode(Node):
    def __init__(self):
        super().__init__("multi_camera_streamer_node")

        Gst.init(None)

        self.streams: dict[int, CameraStream] = {}
        for cam_cfg in CAMERAS:
            self.streams[cam_cfg["camera_sn"]] = CameraStream(self, cam_cfg)

        # Start each camera independently; a failure on one must not stop
        # the loop from attempting the rest.
        started, failed = 0, 0
        for sn, stream in self.streams.items():
            try:
                ok = stream.start()
            except Exception as e:
                # Absolute last-resort guard: this should not be reachable
                # since start() already catches internally, but we do not
                # want any camera to be able to take the node down.
                self.get_logger().error(f"[cam {sn}] unexpected exception during start: {e}")
                ok = False
            if ok:
                started += 1
            else:
                failed += 1

        self.get_logger().info(
            f"Startup complete: {started}/{len(self.streams)} cameras streaming, "
            f"{failed} failed to start"
        )

        # GLib main loop drives the GStreamer bus callbacks; run it on a
        # dedicated background thread so it never blocks rclpy spinning.
        self._glib_loop = GLib.MainLoop()
        self._glib_thread = threading.Thread(
            target=self._run_glib_loop, name="gst-glib-loop", daemon=True
        )
        self._glib_thread.start()

        # Periodic status log, driven by the ROS2 timer (main thread).
        self.create_timer(30.0, self._log_status)

    def _run_glib_loop(self):
        try:
            self._glib_loop.run()
        except Exception as e:
            # If the GLib loop itself dies, bus messages stop being processed,
            # but rclpy and the watchdog keep running; log loudly.
            self.get_logger().error(f"GLib main loop crashed: {e}")

    def _log_status(self):
        alive = [sn for sn, s in self.streams.items() if s.alive]
        dead = [sn for sn, s in self.streams.items() if not s.alive]
        self.get_logger().info(
            f"Status: {len(alive)}/{len(self.streams)} live. "
            f"Live={alive} Dead={dead}"
        )

    def destroy_node(self):
        self.get_logger().info("Shutting down, stopping all pipelines...")
        # stop() tears down only still-healthy pipelines; cameras that failed
        # at runtime are skipped internally so we never hit the ZED close()
        # crash on an already-disconnected device.
        for stream in self.streams.values():
            try:
                stream.stop(reason="node shutdown")
            except Exception:
                pass
        try:
            if self._glib_loop.is_running():
                self._glib_loop.quit()
        except Exception:
            pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = MultiCameraStreamerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()