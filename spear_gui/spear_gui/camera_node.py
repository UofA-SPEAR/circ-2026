import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')
from gi.repository import Gst, GstVideo, GLib
import sys
import rclpy
from rclpy.node import Node
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import QThread, Signal, QTimer, QEasingCurve, Qt, QObject, QEvent, QElapsedTimer
from PySide6.QtGui import QColor, QPainter, QFontDatabase, QFont, QPen, QFontMetrics
from PySide6.QtCore import QPointF, QRectF
from std_msgs.msg import String
from collections import deque
from PySide6.QtCore import qInstallMessageHandler
from typing import Optional
from spear_gui.gui_vars import CAMERA_LAYOUT
from spear_gui.overlay_system_camera import LoadingOverlay, SelectionOverlay, SettingsOverlay, CameraSelectOverlay, OverlayCanvas, InlineLoadingOverlay, InlineSelectionOverlay
from spear_gui.overlay_defs_camera import (
    SETTING_DEFS, SETTING_TEXT_DEFS,
    SETTING_SLIDER_DEFS, SETTING_BUTTON_DEFS,
)

def _qt_message_handler(mode, context, message):
    if 'Painter not active' in message or 'painter' in message.lower() and 'not active' in message.lower():
        return
    print(message)

qInstallMessageHandler(_qt_message_handler)

# ──────────────────────── Key Event Filter ────────────────────────
class KeyEventFilter(QObject):
    def __init__(self, node):
        super().__init__()
        self.node = node

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            key = event.text()
            if key:
                msg = String()
                msg.data = key
                self.node.key_pub.publish(msg)
                print(f"[KeyEventFilter] Published key: {key}")
            elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
                msg = String()
                msg.data = '\r'
                self.node.key_pub.publish(msg)
                print(f"[KeyEventFilter] Published key: Enter")
            return True
        return False

# ──────────────────────── GStreamer (appsink) ────────────────────────

class GStreamerVideoWidget(QWidget):
    """Displays a GStreamer pipeline using appsink + Qt paintEvent.

    This avoids all X11/XWayland window-stacking issues — frames arrive as
    raw RGB buffers, get wrapped as QPixmap, and are drawn by Qt's normal
    paint system. The OverlayCanvas sits on top as a plain child widget with
    no compositor tricks needed.
    """
    clicked  = Signal()

    _frame_ready = Signal(object)   # carries (bytes, width, height)

    def __init__(self, pipeline_str, use_overlay=True,
                 camera_width=1920, camera_height=1080, parent=None):
        super().__init__(parent)
        self.pipeline_str   = pipeline_str
        self.use_overlay    = use_overlay
        self.camera_width   = camera_width
        self.camera_height  = camera_height
        self.video_resize_enabled = True

        # Public alias expected by camera_node
        self.video_surface  = self
        self.thread         = _AppSinkThread(pipeline_str, parent=self)

        self._pixmap: Optional['QPixmap'] = None
        self._pix_lock = False   # simple flag, always accessed from main thread

        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_OpaquePaintEvent)
        self.setAttribute(Qt.WA_NoSystemBackground)

        # Wire thread signals → Qt main-thread slots
        self.thread.frame_ready.connect(self._on_new_frame,
                                        Qt.ConnectionType.QueuedConnection)
        self.thread.error_sig.connect(self.on_error)
        self.thread.finished_sig.connect(self.on_finished)

    # ── public API used by camera_node ──────────────────────────────

    def start(self):
        if not self.use_overlay:
            return
        self.show()
        QApplication.processEvents()
        self.thread.start()

    def stop(self):
        if self.thread is not None:
            # Detach from parent before stopping so deleteLater on the widget
            # doesn't destroy the thread while it's still running
            self.thread.setParent(None)
            self.thread.stop_pipeline()
            if not self.thread.wait(3000):
                print("[GStreamerVideoWidget] thread did not stop in 3s, forcing")
                self.thread.terminate()
                self.thread.wait(1000)
    def apply_video_resize(self):
        self.update()

    def update_video_render_rectangle(self, w, h):
        self.update()

    # ── frame handling ───────────────────────────────────────────────

    def _on_new_frame(self, frame_data):
        data, w, h = frame_data
        from PySide6.QtGui import QImage, QPixmap
        img = QImage(data, w, h, w * 3, QImage.Format.Format_RGB888)
        self._pixmap = QPixmap.fromImage(img)
        self.update()

    # ── painting ─────────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        if not painter.isActive():
            return
        if self._pixmap is not None:
            painter.drawPixmap(self.rect(), self._pixmap)
        else:
            painter.fillRect(self.rect(), QColor(13, 13, 13))
        painter.end()

    # ── input ────────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def on_error(self, msg):
        print(f"GStreamer error: {msg}")

    def _on_video_loaded(self):
        pass

    def on_finished(self):
        print("Pipeline finished.")


class _AppSinkThread(QThread):
    """Runs the GStreamer GLib main loop and pushes frames to the widget."""

    frame_ready  = Signal(object)   # (bytes, width, height)
    error_sig    = Signal(str)
    video_loaded = Signal()   # name expected by camera_node
    loaded_sig   = Signal()
    finished_sig = Signal()

    def __init__(self, pipeline_str, parent=None):
        super().__init__(parent)
        self.pipeline_str = pipeline_str
        self.pipeline     = None
        self.loop         = GLib.MainLoop()
        self._loaded      = False

        # Expose .pipeline attribute expected by camera_node tween code
        Gst.init(None)
        try:
            self.pipeline = Gst.parse_launch(self.pipeline_str)
            if not self.pipeline:
                raise RuntimeError("parse_launch returned None")

            appsink = self.pipeline.get_by_name("appsink0")
            if appsink is None:
                # Try finding any appsink by interface
                for e in self.pipeline.iterate_elements():
                    if hasattr(e, 'pull_sample'):
                        appsink = e
                        break
            if appsink is None:
                raise RuntimeError("No appsink found in pipeline")

            appsink.set_property("emit-signals", True)
            appsink.set_property("sync", True)
            appsink.set_property("max-buffers", 2)
            appsink.set_property("drop", True)
            appsink.connect("new-sample", self._on_new_sample)

            bus = self.pipeline.get_bus()
            bus.add_signal_watch()
            bus.connect("message", self._on_message)
        except Exception as e:
            print(f"[AppSinkThread] Pipeline creation failed: {e}", file=sys.stderr)
            self.error_sig.emit(str(e))
            self.pipeline = None

    def _on_new_sample(self, appsink):
        sample = appsink.emit("pull-sample")
        if sample is None:
            return Gst.FlowReturn.OK
        try:
            buf  = sample.get_buffer()
            caps = sample.get_caps()
            st   = caps.get_structure(0)
            w    = st.get_value("width")
            h    = st.get_value("height")
            data = buf.extract_dup(0, buf.get_size())
            self.frame_ready.emit((data, w, h))
        except Exception as e:
            print(f"[AppSinkThread] frame error: {e}", file=sys.stderr)
        return Gst.FlowReturn.OK

    def _on_message(self, bus, message):
        mtype = message.type
        if mtype == Gst.MessageType.EOS:
            self.loop.quit()
        elif mtype == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print(f"[GStreamer ERROR] {err}", file=sys.stderr)
            self.error_sig.emit(str(err))
            self.loop.quit()
        elif mtype == Gst.MessageType.ASYNC_DONE and not self._loaded:
            self._loaded = True
            self.video_loaded.emit()
            self.loaded_sig.emit()
        return True

    def run(self):
        if not self.pipeline:
                return
        ret = self.pipeline.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            self.error_sig.emit("Failed to set pipeline PLAYING")
            return
        self.loop.run()
        self.finished_sig.emit()

    def stop_pipeline(self):
        if self.loop and self.loop.is_running():
            self.loop.quit()
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)




class PlaceholderCameraWidget(QWidget):
    clicked = Signal()

    def __init__(self, camera_width=1920, camera_height=1080, parent=None):
        super().__init__(parent)
        self.camera_width  = camera_width
        self.camera_height = camera_height
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #0d0d0d;")

    def stop(self): pass

    def _rebuild_cache(self, w, h):
        from PySide6.QtGui import QPixmap
        px = QPixmap(w, h)
        px.fill(QColor(13, 13, 13))
        p = QPainter(px)
        p.setRenderHint(QPainter.Antialiasing)

        pen = QPen(QColor(255, 255, 255, 18))
        pen.setWidthF(1.0)
        p.setPen(pen)
        step = max(40, min(w, h) // 8)
        for gx in range(0, w, step):
            p.drawLine(gx, 0, gx, h)
        for gy in range(0, h, step):
            p.drawLine(0, gy, w, gy)

        cx, cy = w / 2, h / 2
        icon_w, icon_h = min(w * 0.18, 80), min(h * 0.14, 54)
        body = QRectF(cx - icon_w/2, cy - icon_h/2, icon_w, icon_h)
        p.setBrush(Qt.NoBrush)
        pen2 = QPen(QColor(255, 255, 255, 50))
        pen2.setWidthF(2.0)
        p.setPen(pen2)
        p.drawRoundedRect(body, 4, 4)
        lens_r = min(icon_w, icon_h) * 0.26
        p.drawEllipse(QPointF(cx, cy), lens_r, lens_r)
        notch_w = icon_w * 0.22
        notch_h = icon_h * 0.25
        notch = QRectF(cx - notch_w/2, body.top() - notch_h, notch_w, notch_h)
        p.drawRoundedRect(notch, 2, 2)

        f = QFont()
        f.setFamily("Oxanium SemiBold")
        f.setPointSizeF(max(6.0, min(h * 0.03, 11.0)))
        p.setFont(f)
        p.setPen(QColor(255, 255, 255, 55))
        fm = QFontMetrics(f)
        label = "NO SIGNAL"
        p.drawText(int(cx - fm.horizontalAdvance(label) / 2),
                   int(cy + icon_h / 2 + fm.ascent() + 6), label)
        p.end()
        self._cache = px
        self._cache_w = w
        self._cache_h = h

    def paintEvent(self, event):
        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            return
        if (not hasattr(self, '_cache') or
                self._cache_w != w or self._cache_h != h):
            self._rebuild_cache(w, h)
        painter = QPainter(self)
        if painter.isActive():
            painter.drawPixmap(0, 0, self._cache)
            painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

class ResizableContainer(QWidget):
    resized = Signal()
    moved = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resized.emit()

    def moveEvent(self, event):
        super().moveEvent(event)
        self.moved.emit()

# ──────────────────────── Camera Node ────────────────────────

class CameraConfig:
    names = ["ZED X One #1", "ZED X One #2", "ZED X One #3", "ZED X One #4", "ZED X One #5", "ZED X One #6", "ZED X Mini #1", "ZED X Mini #2"]
    serials = [302801647, 303928833, 305325257, 307142683, 308873104, 309256978, 44249482, 58896881]
    default_resolutions = [4, 4, 6, 0, 0, 0, 0, 0]
    camera_ids = [0, 1, 0, 3, 4, 5, 6, 7]
    ratios = [[1920, 1080]] * 8
    layout = CAMERA_LAYOUT

class Camera:
    def __init__(self, position, default_resolution):
        self.serial = None
        self.camera_id = 0
        self.index = -1
        self.position = position
        self.active = False
        self.border_ready = False
        self.widget = None
        self.pipeline = None
        self.source_type = None
        self.resolution = default_resolution
        self.exposure = 5000
        self.gain = 40
        self.gamma = 2
        self.pending_exposure = None
        self.pending_gain = None
        self.pending_gamma = None
        self.port = None

    def has_pending_changes(self):
        return any(v is not None for v in [self.pending_exposure, self.pending_gain, self.pending_gamma])

    def apply_pending(self):
        if self.pending_exposure is not None:
            self.exposure = self.pending_exposure
            self.pending_exposure = None
        if self.pending_gain is not None:
            self.gain = self.pending_gain
            self.pending_gain = None
        if self.pending_gamma is not None:
            self.gamma = self.pending_gamma
            self.pending_gamma = None

    def discard_pending(self):
        self.pending_exposure = None
        self.pending_gain = None
        self.pending_gamma = None


class CameraNode(Node):
    def __init__(self):
        super().__init__('camera_node')

        self.container = None
        self.command_queue = deque()
        self.processing_command = False

        self.config = CameraConfig()
        self.cameras = [Camera(i, self.config.default_resolutions[i]) for i in range(len(self.config.serials))]

        self.current_index = 0
        self.focused_camera = None
        self.focus_mode = False
        self.switching_mode = False
        self.display_mode = 2

        self.always_remove_inactive_cams = True
        self._tweens: dict = {}
        self._master_timer = QTimer()
        self._master_timer.setInterval(16)
        self._master_timer.timeout.connect(self._master_tick)
        self._settings_panel = None
        self._cam_select_panel = None

        self.key_pub = self.create_publisher(String, "key", 10)
        self.key_subscription = self.create_subscription(
            String, 'key', self.key_listener, 10
        )

        self.zed_sources = {
            "zedxone": "zedxonesrc",
            "zed": "zedsrc",
        }

        self.available_zed_sources = {
            name: self.check_gstreamer_element(element)
            for name, element in self.zed_sources.items()
        }

        print(f"Checking available ZED GStreamer elements:")
        for name, element in self.zed_sources.items():
            status = "✓ Available" if self.available_zed_sources[name] else "✗ Not found"
            print(f"  {element}: {status}")

        if not any(self.available_zed_sources.values()):
            self.get_logger().warn(
                "\033[93mWarning: No ZED SDK cameras detected. Camera display is disabled.\033[0m"
            )

        self.video_sink = self.find_best_video_sink()
        print(f"Using video sink: {self.video_sink}")

        # appsink works everywhere — no overlay/native-window needed
        self.use_video_overlay = True

        self.camera_info = {
            302801647: {"type": "ZED X One", "source": "zedxonesrc", "camera_id": 0,
                        "name": "ZED X ONE #1", "exposure": 10000, "gain": 30000, "gamma": 2, "port": 5000},
            303928833: {"type": "ZED X One", "source": "zedxonesrc", "camera_id": 1,
                        "name": "ZED X ONE #2", "exposure": 10000, "gain": 30000, "gamma": 2, "port": 5001},
            305325257: {"type": "ZED X One", "source": "zedxonesrc", "camera_id": 2,
                        "name": "ZED X ONE #3", "exposure": 10000, "gain": 30000, "gamma": 2, "port": 5002},
            307142683: {"type": "ZED X One", "source": "zedxonesrc", "camera_id": 3,
                        "name": "ZED X ONE #4", "exposure": 10000, "gain": 30000, "gamma": 2, "port": 5003},
            308873104: {"type": "ZED X One", "source": "zedxonesrc", "camera_id": 4,
                        "name": "ZED X ONE #5", "exposure": 10000, "gain": 30000, "gamma": 2, "port": 5004},
            309256978: {"type": "ZED X One", "source": "zedxonesrc", "camera_id": 5,
                        "name": "ZED X ONE #6", "exposure": 10000, "gain": 30000, "gamma": 2, "port": 5005},
            44249482:  {"type": "ZED X Mini", "source": "zedsrc",    "camera_id": 0,
                        "name": "ZED X MINI #1", "exposure": 10000, "gain": 30000, "gamma": 2, "port": 5006},
            58896881:  {"type": "ZED X Mini", "source": "zedsrc",    "camera_id": 1,
                        "name": "ZED X MINI #2", "exposure": 10000, "gain": 30000, "gamma": 2, "port": 5007},
        }

        print(f"\nConfigured cameras:")
        for serial, info in self.camera_info.items():
            print(f"  Serial {serial}: {info['type']} using {info['source']} (camera-id={info['camera_id']})")

    # ──────────────────────── Setup ────────────────────────

    def check_gstreamer_element(self, element_name):
        try:
            Gst.init(None)
            return Gst.ElementFactory.make(element_name, None) is not None
        except Exception as e:
            self.get_logger().error(f"\033[91mError: Failed to check GStreamer element: {e}\033[0m")
            return False

    def find_best_video_sink(self):
        # Using appsink — no display sink needed
        print("Using appsink for frame delivery")
        return 'appsink'

    def setup_gui(self, parent=None):
        self.container = ResizableContainer(parent)
        self.container.setMinimumSize(400, 200)
        self.container.resize(800, 400)
        self.container.setStyleSheet("background-color: #2b2b2b;")
        self.container.resized.connect(self.on_container_resized)
        # With appsink the video is drawn by Qt paintEvent — no native X11
        # windows involved. OverlayCanvas is a plain child widget that sits
        # on top via normal Qt stacking. No compositor tricks needed.
        self._overlay_canvas = OverlayCanvas(self.container, external_tick=True)
        self._overlay_canvas.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._overlay_canvas.raise_()
        self._master_timer.start()
        print("GUI setup complete.")

    def _reposition_overlay(self):
        if not self._overlay_canvas or not self.container:
            return
        global_pos = self.container.mapToGlobal(self.container.rect().topLeft())
        cw, ch = self.container.width(), self.container.height()
        self._overlay_canvas.setGeometry(global_pos.x(), global_pos.y(), cw, ch)
        self._overlay_canvas.raise_()

    def on_container_resized(self):
        self.set_camera_positions()
        if self._overlay_canvas:
            self._overlay_canvas.resizeToParent()
        # Keep any open panels filling the container
        for panel in [self._settings_panel, self._cam_select_panel]:
            if panel is not None:
                try:
                    panel.setGeometry(self.container.rect())
                    panel.raise_()
                except RuntimeError:
                    pass
        if self._overlay_canvas and self._settings_panel is None and self._cam_select_panel is None:
            self._overlay_canvas.raise_()

    # ──────────────────────── Key Listener ────────────────────────

    def key_listener(self, key_msg):
        key = key_msg.data
        print(f"Received key: {key}")
        self.command_queue.append(key.lower())
        if not self.processing_command:
            self.process_command_queue()

    def process_command_queue(self):
        if not self.command_queue:
            self.processing_command = False
            return
        self.processing_command = True
        key = self.command_queue.popleft()
        match key:
            case 'p':
                print("Exiting...")
                rclpy.shutdown()
                return
            case 'w':
                self.activate_camera()
            case 's':
                self.deactivate_camera()
            case 'e':
                self.select_next_camera(1)
            case 'q':
                self.select_next_camera(-1)
            case 'd':
                self.move_index(1)
            case 'a':
                self.move_index(-1)
            case 'm':
                self.change_display(1)
            case 'n':
                self.change_display(-1)
            case 't':
                self.show_cam_select_panel()
            case 'f':
                self.toggle_focus()
            case 'r':
                self.toggle_switching_mode()
                print(f'Switch Mode: {self.switching_mode}')
            case key if key in ['0', '1', '2', '3', '4', '5', '6', '7']:
                if self.switching_mode:
                    self.switch_cameras(int(key))
                    self.switching_mode = False
                else:
                    print(f'Failed to swap with {key}')
        self.update_camera_borders()
        self.print_infomation()
        self.cleanup_orphaned_widgets()
        QTimer.singleShot(20, self.process_command_queue)

    # ──────────────────────── Camera Utilities ────────────────────────

    def get_available_index(self):
        used = {cam.index for cam in self.cameras if cam.index != -1}
        unused = [i for i in range(len(self.cameras)) if i not in used]
        return unused[0] if unused else None

    # ──────────────────────── Settings Panel ────────────────────────

    def show_settings_panel(self, cam):
        # Guard against stale references
        for attr in ('_settings_panel', '_cam_select_panel'):
            panel = getattr(self, attr)
            if panel is not None:
                try:
                    _ = panel.isVisible()
                except RuntimeError:
                    setattr(self, attr, None)
        if self._settings_panel is not None or self._cam_select_panel is not None:
            return

        panel = SettingsOverlay(
            SETTING_DEFS, SETTING_TEXT_DEFS,
            SETTING_SLIDER_DEFS, SETTING_BUTTON_DEFS,
            cam_w=1920, cam_h=1080,
            parent=self.container,
        )
        panel.setGeometry(self.container.rect())

        def on_apply():
            cam.apply_pending()
            geom = cam.widget.geometry()
            self.remove_widget(cam)
            self.create_camera_widget(cam)
            cam.widget.setGeometry(geom)
            self._settings_panel = None

        def on_cancel():
            cam.discard_pending()
            self._settings_panel = None

        panel.open(cam, on_apply=on_apply, on_cancel=on_cancel)
        self._settings_panel = panel
        # Clear the reference when the panel destroys itself
        panel.destroyed.connect(lambda: setattr(self, '_settings_panel', None))
        panel.raise_()

    def show_cam_select_panel(self):
        # Guard against stale reference to deleted C++ panel object
        if self._cam_select_panel is not None:
            try:
                _ = self._cam_select_panel.isVisible()
            except RuntimeError:
                self._cam_select_panel = None
        if self._cam_select_panel is not None:
            return

        active_cams = len([c for c in self.cameras if c.active])

        panel = CameraSelectOverlay(
            cam_w=1920, cam_h=1080,
            initial_display_mode=self.display_mode,
            initial_cams=active_cams,
            parent=self.container,
        )
        panel.setGeometry(self.container.rect())

        def on_apply(display_mode, num_cams):
            self.display_mode = display_mode

            active = [c for c in self.cameras if c.active]
            while len(active) < num_cams:
                self.activate_camera()
                active = [c for c in self.cameras if c.active]

            while len(active) > num_cams:
                active = [c for c in self.cameras if c.active]
                if active:
                    self.current_index = active[-1].position
                self.deactivate_camera()
                active = [c for c in self.cameras if c.active]

            active = [c for c in self.cameras if c.active]
            if active:
                self.current_index = active[-1].position
            self.update_camera_borders()

            self.set_camera_positions()
            self._cam_select_panel = None

        def on_cancel():
            self._cam_select_panel = None

        panel.open(on_apply=on_apply, on_cancel=on_cancel)
        self._cam_select_panel = panel
        # Clear the reference when the panel destroys itself
        panel.destroyed.connect(lambda: setattr(self, '_cam_select_panel', None))
        panel.raise_()
        if self._overlay_canvas:
            self._overlay_canvas.stackUnder(panel)

    # ──────────────────────── Activation / Deactivation ────────────────────────

    def activate_camera(self):
        inactive = [c for c in self.cameras if not c.active]
        if not inactive:
            print("No inactive camera slots.")
            return

        cam = next(cam for cam in self.cameras if not cam.active)
        cam.active = True

        active_indexes = {c.index for c in self.cameras if c.active and c is not cam}
        if cam.index in (-1, *active_indexes):
            cam.index = self.get_available_index()

        cam.serial = self.config.serials[cam.index]

        if cam.serial in self.camera_info:
            info = self.camera_info[cam.serial]
            cam.name        = info["name"]
            cam.source_type = info["source"]
            cam.camera_id   = info["camera_id"]
            cam.exposure    = info.get("exposure")
            cam.gain        = info.get("gain")
            cam.gamma       = info.get("gamma")

            source_available = False
            for name, element in self.zed_sources.items():
                if element == cam.source_type and self.available_zed_sources.get(name):
                    source_available = True
                    break

            if source_available:
                print(f"Activated {info['type']} (Serial: {cam.serial}, Source: {cam.source_type}, Camera ID: {cam.camera_id})")
            else:
                print(f"ERROR: {info['type']} requires {cam.source_type} which is not available!")
                cam.source_type = None
                cam.camera_id = 0
                cam.port = info.get("port")
                print(f"Falling back to H265 stream on port {cam.port}")
        else:
            cam.camera_id = self.config.camera_ids[cam.index]
            if self.available_zed_sources.get("zedxone"):
                cam.source_type = "zedxonesrc"
                print(f"Warning: Using zedxonesrc for unknown camera serial {cam.serial}")
            else:
                cam.source_type = None
                cam.port = 5000 + cam.index
                print(f"Warning: Unknown serial {cam.serial}, falling back to H265 stream on port {cam.port}")

        self.current_index = cam.position
        print(f'Current Camera: {self.current_index}')
        self.create_camera_widget(cam)
        self.set_camera_positions()

    def deactivate_camera(self):
        if self.current_index is None:
            print("No camera currently selected.")
            return

        cam = self.cameras[self.current_index]
        if not cam.active:
            print(f"Camera {self.current_index} is not active.")
            return

        cam.discard_pending()
        cam.border_ready = False

        original_pos = cam.position
        cam.active = False
        active_positions = [c.position for c in self.cameras if c.active]
        if not active_positions:
            for c in self.cameras:
                self.remove_widget(c)
            self.current_index = None
            QApplication.processEvents()
            self.cleanup_orphaned_widgets()
            self.set_camera_positions()
            return

        max_pos = max(active_positions)

        for c in self.cameras:
            if (not c.active) and c.position > max_pos:
                self.remove_widget(c)

        if self.always_remove_inactive_cams:
            self.remove_widget(cam)
            found_inactive = True
            while found_inactive:
                found_inactive = False
                for i in range(len(self.cameras)):
                    if not self.cameras[i].active and self.cameras[i].position < max_pos:
                        found_inactive = True
                        self.select_camera(i, True)
                        self.switch_cameras(i + 1, True)
        elif cam.position > max_pos:
            self.remove_widget(cam)
        else:
            if cam.widget:
                self.stop_animation_for_widget(cam.widget)
                cam.widget.stop()

        candidates = [p for p in active_positions if p < self.current_index]
        self.current_index = max(candidates) if candidates else self.current_index
        if self.always_remove_inactive_cams:
            self.select_camera(original_pos, True)
            if not self.cameras[self.current_index].active:
                self.select_camera(max(candidates), True)

        QApplication.processEvents()
        self.cleanup_orphaned_widgets()
        self.set_camera_positions()

    # ──────────────────────── Selection ────────────────────────

    def select_camera(self, index, bypass_inactive=False):
        if not bypass_inactive and not self.cameras[index].active:
            print(f"Camera {index} not active")
            return
        if bypass_inactive:
            index = next((c.position for c in self.cameras if c.position == index), 0)
        self.current_index = index
        print(f"Current Index: {index}")

    def select_next_camera(self, direction):
        if self.current_index is None:
            print("No camera currently selected.")
            return
        active_positions = [c.position for c in self.cameras if c.active]
        if not active_positions:
            print("No active cameras.")
            return
        max_pos = max(active_positions)
        self.current_index = (self.current_index + direction) % (max_pos + 1)

    def change_display(self, direction):
        self.display_mode = (self.display_mode + direction) % len(self.config.layout[0])
        self.set_camera_positions()

    def toggle_focus(self):
        if self.current_index is None:
            return
        cam = self.cameras[self.current_index]
        if not cam.active or not cam.widget:
            return

        if not self.focus_mode:
            self.focus_mode = True
            self.focused_camera = self.current_index

            for c in self.cameras:
                if c.position == self.focused_camera:
                    continue
                ov = self._overlay_canvas.get_selection(c.widget) if c.widget else None
                if ov:
                    ov.notify_unfocused()

            cam.widget.raise_()
            self.stop_animation_for_widget(cam.widget)
            self.tween_position_and_size(cam.widget, 0, 0, self.container.width(), self.container.height(), duration=500)
        else:
            prev_focused = self.focused_camera
            self.focus_mode = False
            self.focused_camera = None

            for c in self.cameras:
                if c.position == prev_focused:
                    continue
                ov = self._overlay_canvas.get_selection(c.widget) if c.widget else None
                if ov:
                    if c.position == self.current_index and c.active:
                        ov.notify_reselected()
                    else:
                        ov.notify_focused()

            self.set_camera_positions()

    def toggle_switching_mode(self):
        self.switching_mode = not self.switching_mode

    def switch_cameras(self, target_pos, bypass_inactive=False):
        cam_current = next((c for c in self.cameras if c.position == self.current_index), None)
        cam_target = next((c for c in self.cameras if c.position == target_pos), None)
        active_positions = [c.position for c in self.cameras if c.active]

        restrictions = [
            [not cam_current, 'No current camera. '],
            [not cam_target, 'No target camera. '],
            [not active_positions, 'No active positions. '],
            [cam_target and max(active_positions) < cam_target.position, 'Target camera is beyond max active positions. ']
        ]
        if not bypass_inactive:
            fail_reason = ''.join([r[1] for r in restrictions if r[0]])
            if len(fail_reason) > 0:
                print(f'Failed to switch due to the following reason(s):\n{fail_reason}')
                return
        print(f"Switched cameras {self.current_index} <-> {target_pos}")

        attrs_to_swap = ['index', 'active']
        for attr in attrs_to_swap:
            temp = getattr(cam_current, attr)
            setattr(cam_current, attr, getattr(cam_target, attr))
            setattr(cam_target, attr, temp)

        cam_current.widget, cam_target.widget = cam_target.widget, cam_current.widget

        self.switching_mode = False
        self.set_camera_positions()

    # ──────────────────────── Move Index ────────────────────────

    def move_index(self, direction):
        if self.current_index is None:
            print("No camera currently selected.")
            return

        cam = self.cameras[self.current_index]
        if not cam.active:
            print(f"Camera {self.current_index} is not active.")
            return

        start_index = cam.index
        current_index = start_index

        for _ in range(len(self.cameras)):
            current_index = (current_index + direction) % len(self.cameras)
            active_indexes = [c.index for c in list(filter(lambda c: c.active, self.cameras))]
            if current_index not in active_indexes or current_index == start_index:
                cam.index = current_index
                cam.serial = self.config.serials[cam.index]
                if cam.serial in self.camera_info:
                    info = self.camera_info[cam.serial]
                    cam.source_type = info["source"]
                    cam.camera_id = info["camera_id"]
                else:
                    cam.camera_id = self.config.camera_ids[cam.index]
                break

    # ──────────────────────── Camera Widgets ────────────────────────

    def create_camera_widget(self, cam):
        active_positions = [c.position for c in self.cameras if c.active] + [cam.position]
        max_pos = max(active_positions)

        layouts = self.config.layout[cam.position][self.display_mode]
        dims = layouts[max(0, min(max_pos + 1 - cam.position, len(layouts) - 1))]
        x = round(dims[0] * self.container.width())
        y = round(dims[1] * self.container.height())
        w = round(dims[2] * self.container.width())
        h = round(dims[3] * self.container.height())

        cam_ratio = self.config.ratios[cam.index] if cam.index >= 0 else [1920, 1080]
        cam_w, cam_h = cam_ratio[0], cam_ratio[1]

        if cam.port is not None:
            use_camera = self.use_video_overlay
            port = cam.port
            pipeline = (
                f"udpsrc port={port} "
                f"! application/x-rtp,encoding-name=H265,payload=96 "
                f"! rtph265depay "
                f"! h265parse "
                f"! avdec_h265 "
                f"! videoconvert "
                f"! video/x-raw,format=RGB "
                f"! queue max-size-buffers=2 leaky=downstream "
                f"! appsink name=appsink0 emit-signals=true sync=true max-buffers=2 drop=true"
            )
            print(f"[create_camera_widget] Stream pipeline for port {port}: {pipeline}")
        elif cam.source_type is not None:
            use_camera = self.use_video_overlay
            src = cam.source_type
            cid = cam.camera_id
            exp = cam.exposure
            gain = cam.gain
            gamma = cam.gamma

            if src == "zedxonesrc":
                cam_props = (
                    f"camera-id={cid} "
                    f"ctrl-auto-exposure=false "
                    f"ctrl-auto-exposure-range-min={exp} "
                    f"ctrl-auto-exposure-range-max={exp} "
                    f"ctrl-exposure-time={exp} "
                    f"ctrl-analog-gain={gain} "
                    f"ctrl-gamma={gamma}"
                )
            elif src == "zedsrc":
                cam_props = f"camera-id={cid} "

            pipeline = (
                f"{src} {cam_props} "
                f"! queue ! videoconvert "
                f"! video/x-raw,format=RGB "
                f"! appsink name=appsink0 emit-signals=true sync=true max-buffers=2 drop=true"
            )
        else:
            use_camera = False
            pipeline = None

        try:
            if use_camera:
                camera_feed_widget = GStreamerVideoWidget(
                    pipeline,
                    use_overlay=True,
                    camera_width=cam_w,
                    camera_height=cam_h,
                    parent=self.container
                )
            else:
                camera_feed_widget = PlaceholderCameraWidget(
                    camera_width=cam_w,
                    camera_height=cam_h,
                    parent=self.container
                )

            camera_feed_widget.setGeometry(x, y, w, h)
            camera_feed_widget.show()

            def on_widget_clicked(pos=cam.position, c=cam):
                if self._settings_panel is not None:
                    return
                if self._cam_select_panel is not None:
                    return
                if self.current_index == pos and c.active:
                    self.show_settings_panel(c)
                else:
                    self.select_camera(pos)
                    self.update_camera_borders()

            camera_feed_widget.clicked.connect(on_widget_clicked)

            overlay = InlineLoadingOverlay(cam_w=cam_w, cam_h=cam_h)
            overlay._click_target = camera_feed_widget
            self._overlay_canvas.register(camera_feed_widget, loading_ov=overlay)
            overlay.start()

            if use_camera:
                QApplication.processEvents()
                camera_feed_widget.start()

                pipeline_ok = (camera_feed_widget.thread is not None and
                               camera_feed_widget.thread.pipeline is not None)

                if pipeline_ok:
                    def on_video_loaded(c=cam, w=camera_feed_widget, ov=overlay):
                        if ov:
                            ov.notify_loaded()
                        def _reveal_border():
                            c.border_ready = True
                            self.update_camera_borders()
                        QTimer.singleShot(1000, _reveal_border)
                    camera_feed_widget.thread.video_loaded.connect(on_video_loaded)
                else:
                    # Pipeline failed to initialise — treat as placeholder
                    QTimer.singleShot(300, lambda ov=overlay, c=cam: (
                        ov.notify_loaded(),
                        setattr(c, 'border_ready', True),
                        self.update_camera_borders()
                    ))
            else:
                QTimer.singleShot(300, lambda ov=overlay, c=cam: (
                    ov.notify_loaded(),
                    setattr(c, 'border_ready', True),
                    self.update_camera_borders()
                ))

            cam.widget = camera_feed_widget
        except Exception as e:
            self.get_logger().error(f"Failed to create camera widget: {e}")
            fallback = PlaceholderCameraWidget(
                camera_width=cam_w, camera_height=cam_h,
                parent=self.container
            )
            fallback.setGeometry(x, y, w, h)
            fallback.show()
            cam.widget = fallback

    def set_camera_positions(self):
        active_positions = [c.position for c in self.cameras if c.active]
        if not active_positions:
            return
        max_pos = max(active_positions)

        active_count = len(active_positions)
        for i, cam in enumerate(self.cameras):
            if not cam.widget:
                continue
            if not cam.active:
                self.stop_animation_for_widget(cam.widget)
                continue

            cam_rank = sorted(active_positions).index(cam.position)
            layouts = self.config.layout[cam_rank][self.display_mode]
            dims = layouts[max(0, min(active_count - cam_rank, len(layouts) - 1))]

            x = round(dims[0] * self.container.width())
            y = round(dims[1] * self.container.height())
            w = round(dims[2] * self.container.width())
            h = round(dims[3] * self.container.height())

            self.tween_position_and_size(cam.widget, x, y, w, h, duration=500)

    def cleanup_orphaned_widgets(self):
        if not self.container:
            return
        valid_widgets = {id(cam.widget) for cam in self.cameras if cam.widget}
        valid_widgets.add(id(self._overlay_canvas))
        # Preserve any open panels — they're legitimate container children
        for panel in [self._settings_panel, self._cam_select_panel]:
            if panel is not None:
                try:
                    valid_widgets.add(id(panel))
                except RuntimeError:
                    pass
        for child in self.container.children():
            if not isinstance(child, QWidget):
                continue
            child_id = id(child)
            if child_id not in valid_widgets and child_id != id(self.container):
                self.stop_animation_for_widget(child)
                child.hide()
                child.deleteLater()

    def update_camera_borders(self):
        for cam in self.cameras:
            if not cam.widget:
                continue

            is_selected = (cam.position == self.current_index and cam.active)
            existing = self._overlay_canvas.get_selection(cam.widget)

            if cam.active and cam.border_ready and existing is None:
                try:
                    cam_w = cam.widget.camera_width
                    cam_h = cam.widget.camera_height
                except AttributeError:
                    cam_w, cam_h = 1920, 1080
                overlay = InlineSelectionOverlay(cam_w=cam_w, cam_h=cam_h)
                overlay._click_target = cam.widget
                overlay.set_context(cam)
                self._overlay_canvas.register(cam.widget, selection_ov=overlay)
                overlay.start()
                existing = overlay

            if is_selected:
                if not cam.border_ready:
                    continue
                if existing is not None:
                    existing.notify_reselected()
                    if self.focus_mode and cam.position != self.focused_camera:
                        existing.notify_unfocused()
            else:
                if existing is not None:
                    existing.notify_deselected()

    # ──────────────────────── Tween Animation ────────────────────────

    def remove_widget(self, cam):
        print(f"[remove_widget] cam.position={cam.position} widget={cam.widget}")
        if cam.widget:
            self._overlay_canvas.unregister(cam.widget)
            if hasattr(cam.widget, 'stop'):
                cam.widget.stop()
            cam.widget.hide()
            cam.widget.deleteLater()
            cam.widget = None
            if self.container:
                self.container.update()
            print(f"[remove_widget] done, widget set to None")

    def _master_tick(self):
        done = []
        for wid, tw in self._tweens.items():
            widget = tw['widget']
            if not widget or widget.parent() is None:
                done.append(wid); continue
            tw['elapsed'] += 16
            elapsed = tw['elapsed']
            duration = tw['duration']
            t = elapsed / duration if elapsed < duration else 1.0
            v = 1.0 - (1.0 - t) ** 5
            sg = tw['start_geom']
            sx = sg.x();  sy = sg.y()
            sw = sg.width(); sh = sg.height()
            nx = int(sx + (tw['end_x'] - sx) * v)
            ny = int(sy + (tw['end_y'] - sy) * v)
            nw = int(sw + (tw['end_w'] - sw) * v)
            nh = int(sh + (tw['end_h'] - sh) * v)
            if nx != sx or ny != sy or nw != sw or nh != sh or t < 1.0:
                widget.setGeometry(nx, ny, nw, nh)
                if hasattr(widget, 'update_video_render_rectangle'):
                    widget.update_video_render_rectangle(nw, nh)
            if t >= 1.0:
                done.append(wid)
                if hasattr(widget, 'video_resize_enabled'):
                    widget.video_resize_enabled = True
                    widget.apply_video_resize()
                if hasattr(widget, 'thread') and widget.thread and widget.thread.pipeline:
                    widget.thread.pipeline.set_state(Gst.State.PLAYING)
        for wid in done:
            self._tweens.pop(wid, None)

        if self._overlay_canvas:
            self._overlay_canvas.external_tick()
            # Only raise the overlay when no fullscreen panel is open —
            # panels are child widgets too and need to stay on top.
            if self._settings_panel is None and self._cam_select_panel is None:
                self._overlay_canvas.raise_()
        # Keep the timer always running — stopping it causes stale frames on
        # XWayland because ximagesink won't flush until Qt issues a paint event.
    def stop_animation_for_widget(self, widget):
        if not widget: return
        wid = id(widget)
        if wid in self._tweens:
            self._tweens.pop(wid)
            if hasattr(widget, 'video_resize_enabled'):
                widget.video_resize_enabled = True
    def tween_position_and_size(self, widget, end_x, end_y, end_w, end_h, ease_style=QEasingCurve.OutQuint, duration=500):
        if not widget or not widget.parent():
            return
        self.stop_animation_for_widget(widget)
        if hasattr(widget, 'video_resize_enabled'):
            widget.video_resize_enabled = False
        if hasattr(widget, 'thread') and widget.thread and widget.thread.pipeline:
            widget.thread.pipeline.set_state(Gst.State.PAUSED)
        self._tweens[id(widget)] = {
            'widget':     widget,
            'start_geom': widget.geometry(),
            'end_x': end_x, 'end_y': end_y,
            'end_w': end_w, 'end_h': end_h,
            'elapsed':  0,
            'duration': max(1, duration),
        }
        if not self._master_timer.isActive():
            self._master_timer.start()

    # ──────────────────────── Print Information ────────────────────────

    def print_infomation(self):
        print(f"Current Selected: {self.current_index}")
        print(f"{'Pos':>3} | {'Active':>6} | {'Index':>5} | {'Serial':>9} | {'CamID':>5} | {'X':>4} | {'Y':>4} | {'W':>4} | {'H':>4}")
        print("-" * 75)
        for cam in self.cameras:
            widget = cam.widget
            if widget:
                geom = widget.geometry()
                x, y, w, h = geom.x(), geom.y(), geom.width(), geom.height()
            else:
                x = y = w = h = 0
            active_str = "\033[92mTrue  \033[0m" if cam.active else "\033[91mFalse \033[0m"
            serial_str = str(cam.serial) if cam.serial else "N/A"
            print(f"{cam.position:>3} | {active_str} | {cam.index:>5} | {serial_str:>9} | {cam.camera_id:>5} | {x:>4} | {y:>4} | {w:>4} | {h:>4}")


def main():
    import os
    os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
    rclpy.init()
    node = CameraNode()

    app = QApplication([])

    import os
    font_path = os.path.join(os.path.dirname(__file__), "Oxanium-VariableFont.ttf")
    QFontDatabase.addApplicationFont(font_path)

    key_filter = KeyEventFilter(node)
    app.installEventFilter(key_filter)

    node.setup_gui()
    node.container.show()
    QApplication.processEvents()
    if node._overlay_canvas:
        node._overlay_canvas.raise_()

    def on_app_state_changed(state):
        for cam in node.cameras:
            if not cam.widget:
                continue
            existing = node._overlay_canvas.get_selection(cam.widget)
            if existing is None:
                continue
            if state == Qt.ApplicationActive:
                existing.notify_focused()
            else:
                existing.notify_unfocused()

    app.applicationStateChanged.connect(on_app_state_changed)

    timer = QTimer()
    timer.timeout.connect(lambda: rclpy.spin_once(node, timeout_sec=0))
    timer.start(30)

    app.exec()

    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()