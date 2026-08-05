#!/usr/bin/env python3
"""
jetson_camera_sender.py

Single-process, multi-camera ZED -> H265/RTP/UDP sender for Jetson AGX Orin.

Why single-process:
  Orin's VIC hardware exposes a fixed ceiling of ~8 concurrent hardware
  sessions, shared *system-wide*, not per-process. Running 8 cameras as 8
  separate OS processes hits that ceiling on the 8th camera with
  "Couldn't create nvvic Session: Cannot allocate memory", which cascades
  into a fatal `double free or corruption (fasttop)` / SIGABRT. NVIDIA's
  confirmed fix (see AGX Orin forum thread, JetPack r36.3) is to run all
  pipelines inside a single process instead of one process per pipeline.

Fault isolation without separate processes:
  Each camera gets its own Gst.Pipeline + GLib.MainLoop running in its own
  Python thread. Errors are handled via the pipeline's *bus* (ERROR/EOS
  messages), not via exceptions, since native GStreamer/Argus failures do
  not raise Python exceptions. A bus ERROR triggers an ordered teardown
  (set_state(NULL) + blocking get_state() to confirm the state change
  actually completed) before the pipeline is rebuilt and retried with
  exponential backoff. Waiting for confirmed NULL state, rather than
  assuming set_state() is synchronous, is what avoids racing a new
  pipeline's Argus client against the old one's still-in-progress teardown
  (the likely source of the double-free).

Known limitation:
  A true native SIGABRT (double free inside libnvbufsurftransform.so /
  Argus) kills the whole process regardless of Python-level structure --
  no amount of try/except here can catch a native abort. This design
  minimizes the race that triggers it, but does not guarantee it can never
  happen. If it recurs, the next fallback is process-level isolation with
  an explicit cap on total concurrent VIC sessions across processes (e.g.
  launch a 9th camera process only after one of the existing ones exits),
  rather than 8 unconstrained simultaneous processes.
"""

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

import threading
import time
import logging
import signal
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
RETRY_BASE_DELAY  = 2      # seconds before first retry
RETRY_MAX_DELAY   = 30     # cap on backoff
RETRY_RESET_AFTER = 60     # seconds of healthy streaming before backoff resets

# Grace period after a pipeline reaches confirmed NULL state before we
# rebuild + restart it. Gives the Argus/GMSL backend time to fully release
# its camera handle so the new pipeline doesn't race the old one's teardown.
TEARDOWN_GRACE_PERIOD = 1.5   # seconds

# How long to block waiting for set_state(NULL) to actually complete before
# giving up and moving on anyway (defensive upper bound; state changes
# should normally confirm in well under this).
STATE_CHANGE_TIMEOUT_NS = 5 * Gst.SECOND if False else 5_000_000_000

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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(threadName)s: %(message)s",
)
log = logging.getLogger("jetson_camera_sender")


# ──────────────────────── Pipeline string ────────────────────────

def build_pipeline_str(source, camera_sn, port, exposure, gain):
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


# ──────────────────────── CameraStream ────────────────────────

class CameraStream:
    """
    Owns one camera's Gst.Pipeline + GLib.MainLoop + dedicated thread.

    Lifecycle per attempt:
      _run_once() builds the pipeline, sets it PLAYING, attaches a bus
      watch, and blocks on its own MainLoop until the bus watch calls
      loop.quit() (on ERROR or EOS) or stop() is called externally.
      Afterwards the pipeline is torn down and its NULL state is confirmed
      before returning, so the caller can safely retry.
    """

    def __init__(self, camera_sn, source, port, exposure, gain):
        self.camera_sn = camera_sn
        self.source = source
        self.port = port
        self.exposure = exposure
        self.gain = gain
        self.name = f"cam[{source}:{camera_sn}]"

        self._stop_requested = threading.Event()
        self._thread = threading.Thread(target=self._run_forever, name=self.name, daemon=True)

        self._pipeline = None
        self._loop = None
        self._loop_lock = threading.Lock()

    # ---- public API ----

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop_requested.set()
        with self._loop_lock:
            if self._loop is not None and self._loop.is_running():
                self._loop.quit()

    def join(self, timeout=None):
        self._thread.join(timeout)

    # ---- internals ----

    def _run_forever(self):
        backoff = RETRY_BASE_DELAY
        while not self._stop_requested.is_set():
            attempt_start = time.monotonic()
            try:
                exit_reason = self._run_once()
            except Exception:
                log.exception(f"{self.name}: unhandled exception in pipeline attempt")
                exit_reason = "exception"

            if self._stop_requested.is_set():
                log.info(f"{self.name}: stop requested, exiting")
                return

            ran_for = time.monotonic() - attempt_start
            if ran_for >= RETRY_RESET_AFTER:
                # Ran cleanly long enough -- reset backoff.
                backoff = RETRY_BASE_DELAY
                log.info(f"{self.name}: ran {ran_for:.1f}s before '{exit_reason}', "
                         f"resetting backoff to {backoff}s")
            else:
                log.warning(f"{self.name}: died after only {ran_for:.1f}s ('{exit_reason}'), "
                            f"retrying in {backoff}s")

            # Sleep in small increments so stop() is responsive.
            slept = 0.0
            while slept < backoff and not self._stop_requested.is_set():
                time.sleep(0.25)
                slept += 0.25

            backoff = min(backoff * 2, RETRY_MAX_DELAY)

    def _run_once(self):
        """
        Build, run, and tear down one pipeline attempt.
        Returns a short string describing why the attempt ended.
        """
        pipeline_str = build_pipeline_str(
            self.source, self.camera_sn, self.port, self.exposure, self.gain
        )
        log.info(f"{self.name}: building pipeline")

        # CRITICAL: give this thread its own private GLib main context and
        # push it as the thread-default *before* creating the pipeline/bus.
        # Without this, Gst.parse_launch()/bus.add_signal_watch()/
        # GLib.MainLoop() all fall back to the process-wide global-default
        # GMainContext, which every camera thread would then share. That
        # causes bus messages for one camera to be dispatched on a
        # *different* camera's thread, and multiple threads iterating the
        # same context concurrently -- especially during a pipeline
        # teardown racing other threads' normal operation (e.g. unplugging
        # one camera while 7 others are streaming) -- is a direct path to
        # the segfault you hit. Each camera must be fully isolated at the
        # GLib context level, not just at the Python/thread level.
        context = GLib.MainContext.new()
        context.push_thread_default()

        try:
            pipeline = Gst.parse_launch(pipeline_str)
            loop = GLib.MainLoop(context)

            exit_reason = {"value": "unknown"}

            bus = pipeline.get_bus()
            bus.add_signal_watch()

            def on_message(bus, message, *_):
                t = message.type
                if t == Gst.MessageType.ERROR:
                    err, debug = message.parse_error()
                    log.error(f"{self.name}: GStreamer ERROR from "
                              f"{message.src.get_name() if message.src else '?'}: "
                              f"{err} ({debug})")
                    exit_reason["value"] = f"error: {err}"
                    loop.quit()
                elif t == Gst.MessageType.EOS:
                    log.warning(f"{self.name}: received EOS")
                    exit_reason["value"] = "eos"
                    loop.quit()
                elif t == Gst.MessageType.WARNING:
                    warn, debug = message.parse_warning()
                    log.warning(f"{self.name}: GStreamer WARNING: {warn} ({debug})")
                elif t == Gst.MessageType.STATE_CHANGED:
                    if message.src == pipeline:
                        old, new, pending = message.parse_state_changed()
                        log.debug(f"{self.name}: pipeline state {old.value_nick} -> {new.value_nick}")

            bus.connect("message", on_message)

            with self._loop_lock:
                self._pipeline = pipeline
                self._loop = loop

            ret = pipeline.set_state(Gst.State.PLAYING)
            if ret == Gst.StateChangeReturn.FAILURE:
                log.error(f"{self.name}: set_state(PLAYING) failed synchronously")
                exit_reason["value"] = "playing_failed"
                self._teardown(pipeline)
                with self._loop_lock:
                    self._pipeline = None
                    self._loop = None
                return exit_reason["value"]

            try:
                loop.run()
            finally:
                self._teardown(pipeline)
                with self._loop_lock:
                    self._pipeline = None
                    self._loop = None

            # Give Argus/GMSL time to fully release the camera handle before
            # this thread's next attempt (or before the process considers
            # this camera "down") rebuilds a new pipeline against the same
            # camera-sn.
            if not self._stop_requested.is_set():
                time.sleep(TEARDOWN_GRACE_PERIOD)

            return exit_reason["value"]
        finally:
            # Always pop the thread-default context, even on exception,
            # so this thread doesn't leave a stale context pushed before
            # its next retry iteration.
            context.pop_thread_default()

    @staticmethod
    def _teardown(pipeline):
        """
        Ordered, *confirmed* teardown. set_state() is asynchronous -- we
        block on get_state() with a timeout so we know the pipeline (and
        its Argus/VIC resources) has actually reached NULL before this
        function returns, instead of assuming the call was synchronous.
        This is the key defense against racing a new pipeline's camera
        open against the old one's still-in-flight teardown.
        """
        try:
            pipeline.set_state(Gst.State.NULL)
            state_ret, state, pending = pipeline.get_state(STATE_CHANGE_TIMEOUT_NS)
            if state != Gst.State.NULL:
                log.warning(f"pipeline did not confirm NULL state within timeout "
                            f"(got {state.value_nick}, ret={state_ret})")
        except Exception:
            log.exception("exception during pipeline teardown")


# ──────────────────────── ROS2 Node ────────────────────────

class MultiCameraSenderNode(Node):
    """
    Thin ROS2 wrapper: owns all CameraStream instances for this process
    and publishes basic status. Kept separate from CameraStream so the
    GStreamer/threading logic has no ROS2 dependency.
    """

    def __init__(self):
        super().__init__('jetson_camera_sender')
        self.streams = []
        self.status_pub = self.create_publisher(String, 'camera_sender/status', 10)
        self._status_timer = self.create_timer(5.0, self._publish_status)

    def start_all(self, camera_configs):
        for cfg in camera_configs:
            stream = CameraStream(
                camera_sn=cfg["camera_sn"],
                source=cfg["source"],
                port=cfg["port"],
                exposure=cfg["exposure"],
                gain=cfg["gain"],
            )
            self.streams.append(stream)

        # Stagger starts slightly so all 8 don't hit Argus/VIC session
        # creation in the same instant on process startup.
        for stream in self.streams:
            stream.start()
            time.sleep(0.3)

    def stop_all(self):
        self.get_logger().info("stopping all camera streams")
        for stream in self.streams:
            stream.stop()
        for stream in self.streams:
            stream.join(timeout=10)

    def _publish_status(self):
        alive = sum(1 for s in self.streams if s._thread.is_alive())
        msg = String()
        msg.data = f"{alive}/{len(self.streams)} camera threads alive"
        self.status_pub.publish(msg)


# ──────────────────────── main ────────────────────────

def main():
    Gst.init(None)
    rclpy.init()

    node = MultiCameraSenderNode()
    node.start_all(CAMERAS)

    def handle_sigint(signum, frame):
        node.get_logger().info("SIGINT received, shutting down")
        node.stop_all()
        rclpy.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.stop_all()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()