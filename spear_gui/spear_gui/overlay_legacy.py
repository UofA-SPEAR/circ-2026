from __future__ import annotations
from typing import Optional, Dict, List, Tuple, Callable, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore    import Qt, QTimer, QElapsedTimer, QEasingCurve, QPointF, QRectF, QEvent, QObject
from PySide6.QtGui     import QColor, QPainter, QFont, QFontMetrics, QPolygonF, QPen, QRegion, QPainterPath, QLinearGradient
import time
import collections
import statistics
import threading
import math as _math

# I have no idea what needs importing, camera_node's system will eventually be remade to use the new system.
from spear_gui.overlay_system import (
    AnimatedPolygon, AnimatedText,
    PolygonDef, PolygonTween, TextDef, TextTween, TextBlock, DataTable,
    Phase, Reset, P, Rect, RectTween,
    expand_defs,
    GraphDef, SeriesDef, AnimatedGraph, PieDef, AnimatedPie,
    AttributeDef, SliderGroupDef, SliderDef, SliderGroup,
    make_track_def, make_knob_def, make_mark_fill_def, make_mark_tick_def,
    SliderTextDefs,
    ButtonDef, AnimatedButton,
    WindowDef, WindowTween, AnimatedWindow,
    EventDef, EventListener,
    GradientDef, GradientStop, GradientTween,
)

# SLIDERS
def make_track_def(
    p:         P     = P(),
    px:        P     = P(),
    length:    float = 0.0,
    length_px: float = 0.0,
    h_px:      float = 4.0,
    fill_color:    QColor = None,
    outline_color: QColor = None,
    phases: Dict[str, Phase] = None,
) -> PolygonDef:
    half = h_px / 2.0
    fc = fill_color    or QColor(255, 255, 255, 40)
    oc = outline_color or QColor(0, 0, 0, 0)
    return PolygonDef(
        p  = [P(p.x, p.y), P(p.x+length, p.y), P(p.x+length, p.y), P(p.x, p.y)],
        px = [P(px.x, px.y-half), P(px.x+length_px, px.y-half),
              P(px.x+length_px, px.y+half), P(px.x, px.y+half)],
        fill_color    = fc,
        outline_color = oc,
        closed        = True,
        phases        = phases or {},
    )

def make_knob_def(
    fill_color: QColor = None,
    phases: Dict[str, Phase] = None,
) -> PolygonDef:
    fc = fill_color or QColor(255, 255, 255)
    return PolygonDef(
        p             = [P(0, 0), P(0, 0), P(0, 0), P(0, 0)],
        px            = [P(0, 0), P(0, 0), P(0, 0), P(0, 0)],
        fill_color    = fc,
        outline_color = QColor(0, 0, 0, 0),
        closed        = True,
        phases        = phases or {},
    )

def make_mark_fill_def(
    p:      P     = P(),
    px:     P     = P(),
    h_px:   float = 8.0,
    fill_color: QColor = None,
    phases: Dict[str, Phase] = None,
) -> PolygonDef:
    half = h_px / 2.0
    fc   = fill_color or QColor(255, 255, 255, 60)
    return PolygonDef(
        p  = [P(p.x, p.y)] * 4,
        px = [P(px.x, px.y-half), P(px.x, px.y-half),
              P(px.x, px.y+half), P(px.x, px.y+half)],
        fill_color    = fc,
        outline_color = QColor(0, 0, 0, 0),
        closed        = True,
        phases        = phases or {},
    )

def make_mark_tick_def(
    p:      P     = P(),
    px:     P     = P(),
    w_px:   float = 3.0,
    h_px:   float = 14.0,
    fill_color: QColor = None,
    phases: Dict[str, Phase] = None,
) -> PolygonDef:
    hw = w_px / 2.0
    hh = h_px / 2.0
    fc = fill_color or QColor(255, 255, 255, 200)
    return PolygonDef(
        p  = [P(p.x, p.y)] * 4,
        px = [P(px.x-hw, px.y-hh), P(px.x+hw, px.y-hh),
              P(px.x+hw, px.y+hh), P(px.x-hw, px.y+hh)],
        fill_color    = fc,
        outline_color = QColor(0, 0, 0, 0),
        closed        = True,
        phases        = phases or {},
    )


@dataclass
class SliderTextDefs:
    label:   Optional[TextDef] = None   # anchored near track P1, static
    min_val: Optional[TextDef] = None   # anchored at track P1
    max_val: Optional[TextDef] = None   # anchored at track P2
    current: Optional[TextDef] = None   # follows knob (px injected each frame)


# ──────────────────────── AnimatedOverlay ────────────────────────

class AnimatedOverlay(QWidget):
    TICK_MS = 16

    def __init__(self, polygon_defs, parent=None, cam_w=1920, cam_h=1080, text_defs=None):
        super().__init__(parent)
        if parent is None:
            self.setWindowFlags(Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint|Qt.Window)
            self.setAttribute(Qt.WA_TranslucentBackground)
        else:
            # Child overlay — sits directly inside the parent container.
            # WA_NoSystemBackground + no auto-fill lets our painter draw
            # transparent content over whatever is below.
            self.setAttribute(Qt.WA_NoSystemBackground)
            self.setAttribute(Qt.WA_OpaquePaintEvent, False)
            self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.cam_w = cam_w; self.cam_h = cam_h
        self._polygons = [AnimatedPolygon(d) for d in polygon_defs]
        self._texts    = [AnimatedText(d)    for d in (text_defs or [])]
        self._context  = None; self._click_target = None
        self._closing  = False; self._inline = False; self._cleaned_up = False
        self._tick_timer = QTimer(self)
        self._tick_timer.setInterval(self.TICK_MS)
        self._tick_timer.timeout.connect(self._tick)

    def set_context(self, ctx): self._context=ctx
    def set_inline(self): self._inline=True

    def _broadcast(self, phase):
        for p in self._polygons: p.set_phase(phase)
        for t in self._texts:    t.set_phase(phase)

    def _tick_elements(self):
        any_visible = any_animating = False
        for p in self._polygons:
            p.update()
            if not p.hidden:
                any_visible = True
                if not p.phase_done(): any_animating = True
        for t in self._texts:
            t.update()
            if not t.hidden or t.defn.always_visible:
                any_visible = True
                if not t.phase_done(): any_animating = True
        return any_visible, any_animating

    def _tick(self, external=False):
        any_visible, _ = self._tick_elements()
        if self._closing:
            if self._all_done(): self._cleanup(); return
        else:
            if not any_visible: self._cleanup(); return
        if not external: self.update()

    def _tick_externally(self): self._tick(external=True)
    def close(self):
        if not self._closing:
            self._closing=True; self._broadcast('close')

    def _cleanup(self):
        self._cleaned_up=True
        self._tick_timer.stop()
        if self.parent() is not None or not self._inline:
            self.hide()
        try:
            app=QApplication.instance()
            if app:
                for w in app.allWidgets():
                    for attr in ('loading_overlay','selection_overlay'):
                        if getattr(w,attr,None) is self: setattr(w,attr,None); break
        except Exception: pass
        self.deleteLater()

    def mousePressEvent(self, event):
        if event.button()==Qt.LeftButton and self._click_target is not None:
            try: self._click_target.clicked.emit()
            except RuntimeError: self._click_target=None
        super().mousePressEvent(event)

    def draw_into(self, painter, x, y, w, h):
        painter.save()
        painter.translate(x, y)
        painter.setClipRect(QRectF(0, 0, w, h))
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        for poly in self._polygons:
            poly.draw(painter, w, h, self.cam_w, self.cam_h)
        for text in self._texts:
            if text.hidden: continue
            text.draw_text(painter, w, h, cam_w, cam_h, ctx)
        painter.restore()

    def paintEvent(self, event):
        painter = QPainter(self)
        if not painter.isActive(): return
        if self.parent() is None:
            painter.setCompositionMode(QPainter.CompositionMode_Source)
            painter.fillRect(self.rect(), Qt.transparent)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        else:
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        self.draw_into(painter, 0, 0, self.width(), self.height())
        painter.end()

# ──────────────────────── InlineOverlay ──────────────────────────

class InlineOverlay(QObject):
    def __init__(self, polygon_defs, cam_w=1920, cam_h=1080, text_defs=None):
        super().__init__()
        self.cam_w = cam_w; self.cam_h = cam_h
        self._polygons      = [AnimatedPolygon(d) for d in polygon_defs]
        self._texts         = [AnimatedText(d)    for d in (text_defs or [])]
        self._context       = None; self._click_target = None
        self._closing       = False; self._done = False
        self._static_pixmap = None; self._needs_bake = False
        self._baked_w = 0; self._baked_h = 0

    def set_context(self, ctx): self._context = ctx

    def _broadcast(self, phase):
        self._static_pixmap = None; self._needs_bake = False
        for p in self._polygons: p.set_phase(phase)
        for t in self._texts:    t.set_phase(phase)

    def close(self):
        if not self._closing:
            self._closing = True
            self._broadcast('close')

    def tick(self):
        if self._done: return False
        if self._static_pixmap is not None: return False
        any_visible = False; any_animating = False
        for p in self._polygons:
            p.update()
            if not p.hidden:
                any_visible = True
                if not p.phase_done(): any_animating = True
        for t in self._texts:
            t.update()
            if not t.hidden or t.defn.always_visible:
                any_visible = True
                if not t.phase_done(): any_animating = True
        if self._closing:
            if not any_animating: self._done = True; return False
            return True
        if not any_visible: self._done = True; return False
        if not any_animating: self._needs_bake = True; return True
        return True

    def _paint_elements(self, painter, w, h):
        for poly in self._polygons:
            poly.draw(painter, w, h, self.cam_w, self.cam_h)
        for text in self._texts:
            if text.hidden: continue
            text.draw_text(painter, w, h, cam_w, cam_h, ctx)

    def _draw(self, painter, w, h):
        """Draw at widget size (w, h) into an already-translated painter."""
        if self._needs_bake and not self._closing:
            from PySide6.QtGui import QPixmap
            px = QPixmap(w, h)
            px.fill(Qt.transparent)
            p2 = QPainter(px)
            p2.setRenderHint(QPainter.Antialiasing)
            self._paint_elements(p2, w, h)
            p2.end()
            self._static_pixmap = px
            self._baked_w = w; self._baked_h = h
            self._needs_bake = False
        if (self._static_pixmap is not None
                and self._baked_w == w and self._baked_h == h):
            painter.drawPixmap(0, 0, self._static_pixmap)
            return
        self._paint_elements(painter, w, h)

    def draw_into(self, painter, x, y, w, h):
        painter.save()
        painter.translate(x, y)
        painter.setClipRect(0, 0, w, h)
        self._draw(painter, w, h)
        painter.restore()

# ──────────────────────── OVERLAY ──────────────────────────



class _OverlayBase:
    def _base_init(self, polygon_defs, cam_w, cam_h, text_defs):
        self.cam_w      = cam_w
        self.cam_h      = cam_h
        self._polygons  = [AnimatedPolygon(d) for d in polygon_defs]
        self._texts     = [AnimatedText(d)    for d in (text_defs or [])]
        self._context   = None
        self._closing   = False

    def _broadcast(self, phase):
        for p in self._polygons: p.set_phase(phase)
        for t in self._texts:    t.set_phase(phase)

    def _tick_elements(self):
        any_visible = any_animating = False
        for p in self._polygons:
            p.update()
            if not p.hidden:
                any_visible = True
                if not p.phase_done(): any_animating = True
        for t in self._texts:
            t.update()
            if not t.hidden or t.defn.always_visible:
                any_visible = True
                if not t.phase_done(): any_animating = True
        return any_visible, any_animating

    def _all_done(self):
        return (all(p.phase_done() for p in self._polygons) and
                all(t.phase_done() for t in self._texts))

    def _paint_elements(self, painter, w, h):
        for poly in self._polygons:
            poly.draw(painter, w, h, self.cam_w, self.cam_h)
        for text in self._texts:
            if text.hidden: continue
            text.draw_text(painter, w, h, cam_w, cam_h, ctx)

class _LoadingMixin:
    def start(self):
        self._broadcast('create')

    def notify_loaded(self):
        if any(p._phase == 'loaded' for p in self._polygons): return
        QTimer.singleShot(50, lambda: self._broadcast('loaded'))

class _SelectionMixin:
    def _sel_init(self):
        self._pending_unfocus      = None
        self._last_selection_phase = 'selected'

    def start(self):
        self._last_selection_phase = 'selected'
        self._broadcast('selected')

    def notify_reselected(self):
        if self._pending_unfocus is not None:
            self._pending_unfocus.stop(); self._pending_unfocus = None
        self._last_selection_phase = 'selected'
        self._broadcast('selected')

    def notify_deselected(self):
        if self._last_selection_phase == 'unselected': return
        self._last_selection_phase = 'unselected'
        self._broadcast('unselected')

    def notify_focused(self):
        if self._pending_unfocus is not None:
            self._pending_unfocus.stop(); self._pending_unfocus = None; return
        self._broadcast(self._last_selection_phase)

    def notify_unfocused(self):
        if self._pending_unfocus is not None: return
        t = QTimer(); t.setSingleShot(True); t.setInterval(0)
        t.timeout.connect(self._do_notify_unfocused)
        t.start(); self._pending_unfocus = t

    def _do_notify_unfocused(self):
        self._pending_unfocus = None
        self._broadcast('unfocused')


class LoadingOverlay(_LoadingMixin, AnimatedOverlay):
    def __init__(self, parent=None, cam_w=1920, cam_h=1080):
        from spear_gui.overlay_defs import LOADING_DEFS, LOADING_TEXT_DEFS
        super().__init__(LOADING_DEFS, parent=parent, cam_w=cam_w, cam_h=cam_h, text_defs=LOADING_TEXT_DEFS)
    def start(self):
        super().start(); self.show(); self._tick_timer.start()

class InlineLoadingOverlay(_LoadingMixin, InlineOverlay):
    def __init__(self, cam_w=1920, cam_h=1080):
        from spear_gui.overlay_defs import LOADING_DEFS, LOADING_TEXT_DEFS
        super().__init__(LOADING_DEFS, cam_w=cam_w, cam_h=cam_h, text_defs=LOADING_TEXT_DEFS)

class SelectionOverlay(_SelectionMixin, AnimatedOverlay):
    def __init__(self, parent=None, cam_w=1920, cam_h=1080):
        from spear_gui.overlay_defs import SELECTION_DEFS, SELECTION_TEXT_DEFS
        super().__init__(SELECTION_DEFS, parent=parent, cam_w=cam_w, cam_h=cam_h, text_defs=SELECTION_TEXT_DEFS)
        self._sel_init()
    def start(self):
        super().start(); self.show(); self._tick_timer.start()

class InlineSelectionOverlay(_SelectionMixin, InlineOverlay):
    def __init__(self, cam_w=1920, cam_h=1080):
        from spear_gui.overlay_defs import SELECTION_DEFS, SELECTION_TEXT_DEFS
        super().__init__(SELECTION_DEFS, cam_w=cam_w, cam_h=cam_h, text_defs=SELECTION_TEXT_DEFS)
        self._sel_init()



# ──────────────────────── OverlayCanvas ─────────────────────────

class OverlayCanvas(QWidget):
    TICK_MS = 16

    def __init__(self, parent, external_tick=False):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)  # already there but confirm
        self.setAutoFillBackground(False)
        self.setGeometry(parent.rect())
        self._entries: dict = {}
        self._external_tick = external_tick
        if not external_tick:
            self._tick_timer = QTimer(self)
            self._tick_timer.setInterval(self.TICK_MS)
            self._tick_timer.timeout.connect(self._tick)

    def resizeToParent(self):
        if self.parent():
            self.setGeometry(self.parent().rect())
            self.raise_()

    def register(self, cam_widget, loading_ov=None, selection_ov=None):
        entry = self._entries.setdefault(cam_widget, [None, None])
        if loading_ov   is not None: entry[0] = loading_ov
        if selection_ov is not None: entry[1] = selection_ov
        if not self._external_tick and not self._tick_timer.isActive():
            self._tick_timer.start()
        self.raise_()

    def unregister(self, cam_widget):
        self._entries.pop(cam_widget, None)

    def get_loading(self, cam_widget):
        return self._entries.get(cam_widget, [None, None])[0]

    def get_selection(self, cam_widget):
        return self._entries.get(cam_widget, [None, None])[1]

    def _tick(self):
        dead = []
        dirty_region = QRegion()
        for cw, (lo, so) in list(self._entries.items()):
            try:
                g = cw.geometry()
            except RuntimeError:
                dead.append(cw); continue
            lo_active = lo is not None and lo.tick()
            so_active = so is not None and so.tick()
            if lo is not None and lo._done:
                self._entries[cw][0] = None
            if so is not None and so._done:
                self._entries[cw][1] = None
            if lo_active or so_active:
                dirty_region |= QRegion(g)
        for cw in dead:
            self.unregister(cw)
        if not dirty_region.isEmpty():
            self.raise_()
            self.update(dirty_region)
        elif not self._external_tick:
            self._tick_timer.stop()

    def external_tick(self):
        self._tick()

    def has_active(self) -> bool:
        for lo, so in self._entries.values():
            if lo is not None and not lo._done: return True
            if so is not None and not so._done: return True
        return False

    def paintEvent(self, event):
        if not self._entries:
            return
        painter = QPainter(self)
        if not painter.isActive():
            return
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        painter.setRenderHint(QPainter.Antialiasing)
        clip = event.region()
        for cw, (lo, so) in self._entries.items():
            if lo is None and so is None:
                continue
            try:
                g = cw.geometry()
            except RuntimeError:
                continue
            if not clip.intersects(g):
                continue
            x, y, w, h = g.x(), g.y(), g.width(), g.height()
            painter.save()
            painter.translate(x, y)
            painter.setClipRect(0, 0, w, h)
            if lo is not None and not lo._done:
                lo._draw(painter, w, h)
            if so is not None and not so._done:
                so._draw(painter, w, h)
            painter.restore()
        painter.end()


# ──────────────────────── SettingsOverlay ────────────────────────

class SettingsOverlay(QWidget):
    TICK_MS=16

    def __init__(self, polygon_defs, text_defs, slider_defs, button_defs, cam_w=1920, cam_h=1080):
        super().__init__(None)
        self.setWindowFlags(Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint|Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True); self.setFocusPolicy(Qt.StrongFocus)
        self.cam_w = cam_w; self.cam_h = cam_h
        self._polygons = [AnimatedPolygon(d) for d in polygon_defs]
        self._texts    = [AnimatedText(d)    for d in text_defs]
        self._sliders  = [SliderGroup(d, cam_w, cam_h) for d in slider_defs]
        self._buttons  = [AnimatedButton(d, cam_w, cam_h) for d in button_defs]
        self._context  = self._on_apply = self._on_cancel = None
        self._dragging_slider = None; self._closing = False; self._mouse_filter = None
        self._tick_timer = QTimer(self)
        self._tick_timer.setInterval(self.TICK_MS)
        self._tick_timer.timeout.connect(self._tick)

    def open(self,context,on_apply=None,on_cancel=None):
        self._context=context; self._on_apply=on_apply; self._on_cancel=on_cancel; self._closing=False
        for sl in self._sliders:
            sl.init_value(context); sl.set_phase('open')
        for btn in self._buttons: btn._set_phase('open')
        self._broadcast('open')
        self.show(); self.raise_(); self.activateWindow(); self.clearMask()
        app=QApplication.instance()
        if app:
            f=SettingsMouseFilter(self); 
            # f.set_panel(self)
            app.installEventFilter(f)
            self._mouse_filter=f
        self._tick_timer.start()

    def close_panel(self):
        if not self._closing:
            self._closing=True; self._broadcast('close')
            for sl in self._sliders: sl.set_phase('close')
            for btn in self._buttons: btn._set_phase('close')

    def _broadcast(self, phase):
        for p in self._polygons: p.set_phase(phase)
        for t in self._texts:    t.set_phase(phase)

    def _tick(self):
        for p   in self._polygons: p.update()
        for t   in self._texts:    t.update()
        for sl  in self._sliders:  sl.update(self.width(), self.height())
        for btn in self._buttons:  btn.update()
        if self._closing:
            sl_done = all(sl.phase_done() for sl in self._sliders)
            if (all(p.phase_done() for p in self._polygons) and
                    all(t.phase_done() for t in self._texts) and
                    sl_done and all(b.phase_done() for b in self._buttons)):
                self._tick_timer.stop(); self.hide()
                if self._mouse_filter:
                    app = QApplication.instance()
                    if app: app.removeEventFilter(self._mouse_filter)
                    self._mouse_filter = None
                self.deleteLater(); return
        self.update()

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton: return
        mx, my = event.position().x(), event.position().y()
        w, h = self.width(), self.height()
        for sl in self._sliders:
            if sl.hit_test_knob(mx, my, w, h):
                self._dragging_slider = sl
                sl._dragging = True
                sl.drag_to(mx, my, w, h)
                sl.set_phase('pressed')
                return
        for btn in self._buttons:
            if btn.hit_test(mx, my, w, h):
                btn._pressed = True; btn._set_phase('pressed'); return

    def mouseMoveEvent(self,event):
        mx,my=event.position().x(),event.position().y(); w,h=self.width(),self.height()
        if self._dragging_slider is not None: self._dragging_slider.drag_to(mx,my,w,h); return
        for sl in self._sliders:
            now=sl.hit_test_knob(mx,my,w,h)
            if now!=sl._hovered: sl._hovered=now; sl.set_phase('hovered' if now else 'unhovered')
        for btn in self._buttons:
            now=btn.hit_test(mx,my,w,h)
            if now!=btn._hovered: btn._hovered=now; btn._set_phase('hovered' if now else 'unhovered')

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton: return
        mx, my = event.position().x(), event.position().y()
        w, h = self.width(), self.height()
        if self._dragging_slider is not None:
            sl = self._dragging_slider
            sl._pressed = sl._dragging = False
            sl.set_phase('released')
            self._dragging_slider = None
            hovered = sl._hovered
            QTimer.singleShot(150, lambda: sl.set_phase('hovered' if hovered else 'unhovered'))
            return
        for btn in self._buttons:
            if btn._pressed:
                btn._pressed = False; btn._set_phase('released')
                if btn.hit_test(mx, my, w, h): 
                    btn.fire_event()
                    self._handle_button(btn)
                return

    def leaveEvent(self,event):
        for sl in self._sliders:
            if sl._hovered: sl._hovered=False; sl.set_phase('unhovered')
        for btn in self._buttons:
            if btn._hovered: btn._hovered=False; btn._set_phase('unhovered')

    def resizeEvent(self,event): super().resizeEvent(event); self.clearMask()

    def _handle_button(self,btn):
        if btn.defn.action=='apply':
            if self._context:
                for sl in self._sliders: sl.commit(self._context)
            if self._on_apply: self._on_apply()
        else:
            for sl in self._sliders: sl.revert()
            if self._on_cancel: self._on_cancel()
        self.close_panel()

    def paintEvent(self, event):
        painter = QPainter(self)
        if not painter.isActive(): return
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1))
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        w, h = self.width(), self.height()
        for poly in self._polygons:
            poly.draw(painter, w, h, self.cam_w, self.cam_h)
        for text in self._texts:
            if text.hidden: continue
            text.draw_text(painter, w, h, cam_w, cam_h, ctx)
        for sl  in self._sliders: sl.draw(painter, w, h)
        for btn in self._buttons: btn.draw(painter, w, h)
        painter.end()

from spear_gui.gui_vars import CAMERA_LAYOUT, CAMERA_LAYOUT_NAMES

NUM_CAM_SLOTS     = len(CAMERA_LAYOUT)
NUM_DISPLAY_MODES = len(CAMERA_LAYOUT[0])
MAX_ACTIVE_CAMS   = NUM_CAM_SLOTS


def cam_pos(cam_index: int, display_style: int, active_cams: int):
    if cam_index < 0 or cam_index >= NUM_CAM_SLOTS:
        return None
    display_style = display_style % NUM_DISPLAY_MODES
    style = CAMERA_LAYOUT[cam_index][display_style]
    lookup = active_cams - cam_index
    if lookup < 0:
        return None
    return style[max(0, min(lookup, len(style) - 1))]


# ──────────────────────── Preview geometry ───────────────────────

BOX_W  = 0.32
BOX_H  = 0.28
BOX_Y  = 0.38

# slot -2,-1,0,+1,+2  (±2 are pre-loaded just off-screen)
SLOT_CX = {-2: 0.50 - 0.72,
           -1: 0.50 - 0.36,
            0: 0.50,
            1: 0.50 + 0.36,
            2: 0.50 + 0.72}

SIDE_SCALE  = 0.72
SIDE_ALPHA  = 140

SCROLL_DUR  = 0.30   # display mode scroll animation
CAM_DUR     = 0.25   # camera count change animation
OPEN_DUR    = 0.40
CLOSE_DUR   = 0.30

# ──────────────────────── PreviewBoxDef ──────────────────────────

@dataclass
class PreviewBoxDef:
    slots:            Dict[int, PolygonDef]
    label_font_size:  float = 14.0
    label_font_family:str   = 'Oxanium SemiBold'
    name_font_size:   float = 11.0
    cam_w:            int   = 1920
    cam_h:            int   = 1080


# ──────────────────────── CamRect ────────────────────────────────

@dataclass
class CamRect:
    cx: float; cy: float; cw: float; ch: float
    index: int = 0        # 0-based camera slot index
    alpha: int = 255
    _sx: float = 0.0; _sy: float = 0.0; _sw: float = 0.0; _sh: float = 0.0
    _tx: float = 0.0; _ty: float = 0.0; _tw: float = 0.0; _th: float = 0.0
    _s_alpha: int = 255;  _t_alpha: int = 255
    _elapsed: QElapsedTimer = field(default_factory=QElapsedTimer)
    _dur: float = 0.0; _ease: QEasingCurve.Type = QEasingCurve.OutQuint
    _active: bool = False

    def snap(self, x, y, w, h, a=255):
        self.cx=x; self.cy=y; self.cw=w; self.ch=h; self.alpha=a
        self._active=False

    def tween_to(self, x, y, w, h, dur, ease=QEasingCurve.OutQuint, a=255):
        self._sx=self.cx; self._sy=self.cy; self._sw=self.cw; self._sh=self.ch
        self._s_alpha=self.alpha
        self._tx=x; self._ty=y; self._tw=w; self._th=h; self._t_alpha=a
        self._dur=dur; self._ease=ease; self._active=True
        self._elapsed.restart()

    def update(self):
        if not self._active: return
        t = min(1.0, self._elapsed.elapsed()/1000.0/self._dur) if self._dur>0 else 1.0
        v = _ease(t, self._ease)
        self.cx = self._sx+(self._tx-self._sx)*v
        self.cy = self._sy+(self._ty-self._sy)*v
        self.cw = self._sw+(self._tw-self._sw)*v
        self.ch = self._sh+(self._th-self._sh)*v
        self.alpha = int(self._s_alpha+(self._t_alpha-self._s_alpha)*v)
        if t >= 1.0:
            self.cx=self._tx; self.cy=self._ty; self.cw=self._tw; self.ch=self._th
            self.alpha=self._t_alpha; self._active=False

    def done(self): return not self._active


def _box_points(cx: float, scale: float) -> Tuple[P, P]:
    """Return p1, p2 normalised corners for a box at cx with scale."""
    bw = BOX_W * scale
    bh = BOX_H * scale
    return P(cx - bw/2, BOX_Y), P(cx + bw/2, BOX_Y + bh)

def _slot_poly(cx: float, scale: float, alpha: int) -> PolygonDef:
    p1, p2 = _box_points(cx, scale)
    fill    = QColor(255, 255, 255, max(0, int(alpha * 0.10)))
    outline = QColor(255, 255, 255, alpha)
    def _pts(a, b):
        return [P(a.x, a.y), P(b.x, a.y), P(b.x, b.y), P(a.x, b.y)]
    return PolygonDef(
        points=_pts(p1, p2), px=[P(0,0)]*4,
        fill_color=fill, outline_color=outline,
        line_width=2.0, closed=True, phases={},
    )

# ──────────────────────── PreviewBox ─────────────────────────────
class PreviewBox:
    def __init__(self, slot: int, display_mode: int, num_cams: int, defn: PreviewBoxDef):
        self.slot         = slot
        self.display_mode = (display_mode + slot) % NUM_DISPLAY_MODES
        self.num_cams     = num_cams
        self.defn         = defn

        poly_def = defn.slots.get(slot, defn.slots[0])
        self._box_poly = AnimatedPolygon(poly_def)

        self._scx   = SLOT_CX.get(slot, 0.5)
        self._scale = 1.0 if slot == 0 else SIDE_SCALE
        self._s_scx = self._scx;   self._t_scx   = self._scx
        self._s_scale = self._scale; self._t_scale = self._scale
        self._scx_dur = 0.0; self._scx_ease = QEasingCurve.OutQuint
        self._scx_timer = QElapsedTimer(); self._scx_active = False

        self.cams: List[CamRect] = [CamRect(0,0,0,0,index=i) for i in range(NUM_CAM_SLOTS)]
        self._apply_positions(self.display_mode, num_cams, snap=True, alpha=-1)

    def _base_alpha(self, override: int) -> int:
        if override >= 0: return override
        sd = self.defn.slots.get(self.slot, list(self.defn.slots.values())[0])
        return sd.outline_color.alpha() if sd.outline_color else 255

    def _box_screen(self, sw: int, sh: int) -> Tuple[float, float, float, float]:
        pts = list(self._box_poly.get_polygon(sw, sh))
        if not pts: return 0, 0, 100, 100
        xs = [p.x() for p in pts]; ys = [p.y() for p in pts]
        x1 = min(xs); y1 = min(ys)
        return x1, y1, max(xs)-x1, max(ys)-y1

    def _apply_positions(self, display_mode: int, num_cams: int,
                         snap: bool, alpha: int,
                         dur=None, ease=None):
        d = self.defn
        if dur  is None: dur  = d.cam_dur
        if ease is None: ease = d.cam_ease
        a = self._base_alpha(alpha)
        for cr in self.cams:
            pos = cam_pos(cr.index, display_mode, num_cams)
            if pos is None:
                cr.snap(cr.cx, cr.cy, 0, 0, 0)
            else:
                x, y, w, h = pos
                lookup = num_cams - cr.index
                tile_alpha = a if lookup >= 1 else 0
                if snap: cr.snap(x, y, w, h, tile_alpha)
                else:    cr.tween_to(x, y, w, h, dur, ease, tile_alpha)

    def snap_to(self, display_mode: int, num_cams: int, alpha: int = -1):
        self.display_mode = display_mode; self.num_cams = num_cams
        self._apply_positions(display_mode, num_cams, snap=True, alpha=alpha)

    def tween_to(self, display_mode: int, num_cams: int, dur: float,
                 ease=QEasingCurve.OutQuint, alpha: int = -1):
        self.display_mode = display_mode; self.num_cams = num_cams
        self._apply_positions(display_mode, num_cams, snap=False,
                              alpha=alpha, dur=dur, ease=ease)

    def tween_scx(self, target: float, dur: float,
                  ease=QEasingCurve.OutQuint):
        self._s_scx = self._scx; self._t_scx = target
        self._scx_dur = dur; self._scx_ease = ease
        self._scx_active = True; self._scx_timer.restart()

    def tween_scale(self, target: float):
        self._s_scale = self._scale; self._t_scale = target

    def update(self):
        if self._scx_active:
            raw = self._scx_timer.elapsed() / 1000.0
            t   = min(1.0, raw / self._scx_dur) if self._scx_dur > 0 else 1.0
            v   = _ease(t, self._scx_ease)
            self._scx   = self._s_scx   + (self._t_scx   - self._s_scx)   * v
            self._scale = self._s_scale + (self._t_scale - self._s_scale) * v
            if t >= 1.0:
                self._scx   = self._t_scx
                self._scale = self._t_scale
                self._scx_active = False
        self._box_poly.update()
        for cr in self.cams:
            cr.update()

    def all_done(self) -> bool:
        return (not self._scx_active and
                self._box_poly.phase_done() and
                all(c.done() for c in self.cams))

    def draw(self, painter: QPainter, sw: int, sh: int, label_font: QFont):
        bx, by, bw, bh = self._box_screen(sw, sh)
        is_centre = abs(self._scx - 0.5) < 0.08

        # Layout name
        name       = CAMERA_LAYOUT_NAMES[self.display_mode % len(CAMERA_LAYOUT_NAMES)]
        size_name  = 13.0 if is_centre else 9.0
        name_alpha = 255  if is_centre else SIDE_ALPHA
        name_font  = _make_font('Oxanium SemiBold', size_name)
        name_fm    = QFontMetrics(name_font)
        name_x     = int(bx + (bw - name_fm.horizontalAdvance(name)) / 2)
        name_y     = int(by - 8)
        painter.setFont(name_font)
        painter.setPen(QColor(255, 255, 255, name_alpha))
        painter.drawText(name_x, name_y, name)
        painter.setPen(Qt.NoPen)

        # Box outline via polygon
        self._box_poly.draw(painter, sw, sh, self.defn.cam_w, self.defn.cam_h)

        painter.save()
        painter.setClipRect(QRectF(bx, by, bw, bh))
        fm = QFontMetrics(label_font)

        for cr in self.cams:
            if cr.alpha <= 0 or cr.cw <= 0 or cr.ch <= 0: continue
            rx = bx + cr.cx * bw;  ry = by + cr.cy * bh
            rw = cr.cw * bw;       rh = cr.ch * bh
            cx1 = max(rx, bx);     cy1 = max(ry, by)
            cx2 = min(rx+rw, bx+bw); cy2 = min(ry+rh, by+bh)
            rw2 = cx2 - cx1;       rh2 = cy2 - cy1
            if rw2 < 1 or rh2 < 1: continue

            fill = QColor(255,255,255, max(0, min(255, int(cr.alpha * 0.10))))
            painter.setBrush(fill); painter.setPen(Qt.NoPen)
            painter.drawRect(QRectF(cx1, cy1, rw2, rh2))

            cam_pen = QPen(QColor(255,255,255, max(0, min(255, cr.alpha))))
            cam_pen.setWidthF(2.0)
            painter.setPen(cam_pen); painter.setBrush(Qt.NoBrush)
            painter.drawRect(QRectF(cx1, cy1, rw2, rh2))
            painter.setPen(Qt.NoPen)

            lbl = str(cr.index + 1)
            painter.setFont(label_font)
            painter.setPen(QColor(255,255,255, cr.alpha))
            tx = int(cx1 + (rw2 - fm.horizontalAdvance(lbl)) / 2)
            ty = int(cy1 + (rh2 + fm.ascent()) / 2 - fm.descent())
            painter.drawText(tx, ty, lbl)
            painter.setPen(Qt.NoPen)

        painter.restore()

# ──────────────────────── ScrollSystem ───────────────────────────
class ScrollSystem:
    def __init__(self, current_idx: int, num_cams: int, defn: PreviewBoxDef):
        self._num_cams  = max(1, min(num_cams, MAX_ACTIVE_CAMS))
        self._defn      = defn
        self._scrolling = False
        self._order: List[int] = list(range(NUM_DISPLAY_MODES))
        start = current_idx % NUM_DISPLAY_MODES
        self._order = self._order[start:] + self._order[:start]

        self._polys: Dict[int, AnimatedPolygon] = {
            s: AnimatedPolygon(defn.slots[s]) for s in (-2, -1, 0, 1, 2)
        }
        self._cams: Dict[int, List[CamRect]] = {
            s: [CamRect(0,0,0,0,index=i) for i in range(NUM_CAM_SLOTS)]
            for s in (-2, -1, 0, 1, 2)
        }
        self._snap_all()
        self._trigger_open()


    def _mode_for_slot(self, slot: int) -> int:
        return self._order[slot % len(self._order)]
    
    def _snap_all(self):
        for s in (-2, -1, 0, 1, 2):
            mode  = self._mode_for_slot(s)
            alpha = 255 if s == 0 else (SIDE_ALPHA if abs(s) == 1 else 0)
            for cr in self._cams[s]:
                pos = cam_pos(cr.index, mode, self._num_cams)
                if pos is None:
                    cr.snap(cr.cx, cr.cy, 0, 0, 0)
                else:
                    x, y, w, h = pos
                    lookup = self._num_cams - cr.index
                    cr.snap(x, y, w, h, alpha if lookup >= 1 else 0)
    
    def _tween_all_cams(self, dur: float, ease):
        for s in (-2, -1, 0, 1, 2):
            mode  = self._mode_for_slot(s)
            alpha = 255 if s == 0 else (SIDE_ALPHA if abs(s) == 1 else 0)
            for cr in self._cams[s]:
                pos = cam_pos(cr.index, mode, self._num_cams)
                if pos is None:
                    cr.tween_to(cr.cx, cr.cy, 0, 0, dur, ease, 0)
                else:
                    x, y, w, h = pos
                    lookup = self._num_cams - cr.index
                    cr.tween_to(x, y, w, h, dur, ease,
                                alpha if lookup >= 1 else 0)
    
    def _trigger_open(self):
        for poly in self._polys.values():
            poly.set_phase('open')
    
    def scroll(self, direction: int):
        if self._scrolling: return
        self._scrolling = True

        dur  = SCROLL_DUR
        ease = QEasingCurve.OutQuint
        slot0_def = self._defn.slots.get(0)
        if slot0_def:
            p = slot0_def.phases.get('open')
            if p and p.tweens:
                tw = p.tweens[0]
                dur  = tw.start + tw.dur
                ease = tw.ease

        for s, poly in self._polys.items():
            dest_slot = s - direction
            dest_def  = self._defn.slots.get(dest_slot)

            if dest_def is None:
                src_def = self._defn.slots.get(s)
                close_p = src_def.phases.get('close') if src_def else None
                if close_p and close_p.tweens:
                    dest_tw = close_p.tweens[-1]
                else:
                    continue
            else:
                open_p = dest_def.phases.get('open')
                if not open_p or not open_p.tweens: continue
                dest_tw = open_p.tweens[-1]

            poly._sp  = [P(p.x, p.y) for p in poly.cur_points]
            poly._spx = [P(p.x, p.y) for p in poly.cur_px]
            poly._sf  = QColor(poly.cur_fill_color)
            poly._so  = QColor(poly.cur_outline_color)
            poly._tweens = [PolygonTween(
                points        = dest_tw.points,
                px            = dest_tw.px,
                fill_color    = dest_tw.fill_color,
                outline_color = dest_tw.outline_color,
                start         = 0.0,
                dur           = dur,
                ease          = ease,
                span          = (0, 1),
            )]
            poly._idx   = 0
            poly.hidden = False
            poly._dirty = True
            poly._timer.restart()

        for s in (-2, -1, 0, 1, 2):
            mode  = self._mode_for_slot(s)
            dest_slot = s - direction
            alpha = 255 if dest_slot == 0 else (SIDE_ALPHA if abs(dest_slot) == 1 else 0)
            if dest_slot not in (-2, -1, 0, 1, 2):
                alpha = 0
            for cr in self._cams[s]:
                pos = cam_pos(cr.index, mode, self._num_cams)
                if pos is None:
                    cr.tween_to(cr.cx, cr.cy, 0, 0, dur, ease, 0)
                else:
                    x, y, w, h = pos
                    lookup = self._num_cams - cr.index
                    cr.tween_to(x, y, w, h, dur, ease,
                                alpha if lookup >= 1 else 0)

        self._pending_dir = direction
        QTimer.singleShot(int(dur * 1000) + 50, self._finish_scroll)

    def _finish_scroll(self):
        if self._pending_dir > 0:
            self._order = self._order[1:] + [self._order[0]]
        else:
            self._order = [self._order[-1]] + self._order[:-1]

        for s, poly in self._polys.items():
            slot_def = self._defn.slots.get(s)
            if slot_def is None: continue
            open_p = slot_def.phases.get('open')
            if not open_p or not open_p.tweens: continue
            tw = open_p.tweens[-1]
            poly.cur_points = [P(p.x, p.y) for p in tw.points]
            poly.cur_px     = [P(p.x, p.y) for p in (tw.px or [P()] * len(tw.points))]
            if tw.fill_color    is not None: poly.cur_fill_color    = QColor(tw.fill_color)
            if tw.outline_color is not None: poly.cur_outline_color = QColor(tw.outline_color)
            poly._sp     = [P(p.x, p.y) for p in poly.cur_points]
            poly._spx    = [P(p.x, p.y) for p in poly.cur_px]
            poly._sf     = QColor(poly.cur_fill_color)
            poly._so     = QColor(poly.cur_outline_color)
            poly._tweens = []
            poly._idx    = 0
            poly._dirty  = True
            poly.hidden  = False

        self._snap_all()
        self._scrolling = False

    def open_anim(self):
        self._snap_all()
        for s in (-2, -1, 0, 1, 2):
            if abs(s) == 2: continue
            mode  = self._mode_for_slot(s)
            alpha = 255 if s == 0 else SIDE_ALPHA
            for cr in self._cams[s]:
                tgt_pos = cam_pos(cr.index, mode, self._num_cams)
                if tgt_pos is not None:
                    sx, sy, sw, sh = CAMERA_LAYOUT[cr.index][mode][0]
                    cr.snap(sx, sy, sw, sh, 0)
                    x, y, w, h = tgt_pos
                    lookup = self._num_cams - cr.index
                    cr.tween_to(x, y, w, h, OPEN_DUR, QEasingCurve.OutQuint,
                                alpha if lookup >= 1 else 0)
        self._trigger_open()

    def close_anim(self):
        for s in (-2, -1, 0, 1, 2):
            mode = self._mode_for_slot(s)
            for cr in self._cams[s]:
                if cr.alpha > 0 or cr.cw > 0:
                    sx, sy, sw, sh = CAMERA_LAYOUT[cr.index][mode][0]
                    cr.tween_to(sx, sy, sw, sh, CLOSE_DUR, QEasingCurve.InQuint, 0)
        for poly in self._polys.values():
            poly.set_phase('close')

    def set_num_cams(self, num_cams: int):
        self._num_cams = max(1, min(num_cams, MAX_ACTIVE_CAMS))
        self._tween_all_cams(CAM_DUR, QEasingCurve.OutQuint)

    def update(self):
        for poly in self._polys.values(): poly.update()
        for cams  in self._cams.values():
            for cr in cams: cr.update()

    def draw(self, painter: QPainter, sw: int, sh: int):
        d          = self._defn
        label_font = _make_font(d.label_font_family, d.label_font_size)
        name_size  = d.name_font_size

        for s in (-2, 2, -1, 1, 0):
            poly = self._polys[s]
            poly.draw(painter, sw, sh, d.cam_w, d.cam_h)

            pts = list(poly.get_polygon(sw, sh, d.cam_w, d.cam_h))
            if not pts: continue
            xs = [p.x() for p in pts]; ys = [p.y() for p in pts]
            bx = min(xs); by = min(ys)
            bw = max(xs) - bx; bh = max(ys) - by
            if bw < 1 or bh < 1: continue

            mode = self._mode_for_slot(s)

            name       = CAMERA_LAYOUT_NAMES[mode % len(CAMERA_LAYOUT_NAMES)]
            name_font  = _make_font(d.label_font_family, name_size)
            name_fm    = QFontMetrics(name_font)
            painter.setFont(name_font)
            painter.setPen(QColor(255, 255, 255, 255 if s == 0 else SIDE_ALPHA))
            painter.drawText(
                int(bx + (bw - name_fm.horizontalAdvance(name)) / 2),
                int(by - 6),
                name,
            )
            painter.setPen(Qt.NoPen)

            painter.save()
            painter.setClipRect(QRectF(bx, by, bw, bh))
            fm = QFontMetrics(label_font)
            for cr in self._cams[s]:
                if cr.alpha <= 0 or cr.cw <= 0 or cr.ch <= 0: continue
                rx = bx + cr.cx * bw;  ry = by + cr.cy * bh
                rw = cr.cw * bw;       rh = cr.ch * bh
                cx1 = max(rx, bx);     cy1 = max(ry, by)
                cx2 = min(rx+rw, bx+bw); cy2 = min(ry+rh, by+bh)
                rw2 = cx2-cx1; rh2 = cy2-cy1
                if rw2 < 1 or rh2 < 1: continue
                painter.setBrush(QColor(255,255,255, max(0,min(255,int(cr.alpha*0.10)))))
                painter.setPen(Qt.NoPen)
                painter.drawRect(QRectF(cx1,cy1,rw2,rh2))
                pen = QPen(QColor(255,255,255, max(0,min(255,cr.alpha))))
                pen.setWidthF(2.0)
                painter.setPen(pen); painter.setBrush(Qt.NoBrush)
                painter.drawRect(QRectF(cx1,cy1,rw2,rh2))
                painter.setPen(Qt.NoPen)
                lbl = str(cr.index + 1)
                painter.setFont(label_font)
                painter.setPen(QColor(255,255,255,cr.alpha))
                painter.drawText(
                    int(cx1+(rw2-fm.horizontalAdvance(lbl))/2),
                    int(cy1+(rh2+fm.ascent())/2-fm.descent()),
                    lbl,
                )
                painter.setPen(Qt.NoPen)
            painter.restore()

    def all_done(self) -> bool:
        return (all(p.phase_done() for p in self._polys.values()) and
                all(cr.done() for cams in self._cams.values() for cr in cams))

    @property
    def display_mode(self) -> int: return self._order[0]
    @property
    def num_cams(self) -> int:     return self._num_cams
    @property
    def scrolling(self) -> bool:   return self._scrolling

# ──────────────────────── CameraSelectOverlay ────────────────────

class CameraSelectOverlay(QWidget):
    TICK_MS = 16

    def __init__(self, parent=None, cam_w=1920, cam_h=1080,
                 initial_display_mode=0, initial_cams=2):
        super().__init__(None)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True); self.setFocusPolicy(Qt.StrongFocus)
        self.cam_w = cam_w; self.cam_h = cam_h
        self._initial_display_mode = initial_display_mode % NUM_DISPLAY_MODES
        self._initial_cams         = max(1, min(initial_cams, MAX_ACTIVE_CAMS))
        self._closing = False
        self._on_apply = self._on_cancel = None
        self._filter = None
        from spear_gui.overlay_defs import CS_DEFS, CS_TEXT_DEFS, CS_BUTTON_DEFS, PREVIEW_BOX_DEF
        self._polygons  = [AnimatedPolygon(d)               for d in CS_DEFS]
        self._texts     = [AnimatedText(d)                  for d in CS_TEXT_DEFS]
        self._buttons   = [AnimatedButton(d, cam_w, cam_h)  for d in CS_BUTTON_DEFS]
        self._scroll    = ScrollSystem(self._initial_display_mode, self._initial_cams, PREVIEW_BOX_DEF)
        self._tile_font = _make_font('Oxanium SemiBold', 14.0)
        self._tick_timer = QTimer(self)
        self._tick_timer.setInterval(self.TICK_MS)
        self._tick_timer.timeout.connect(self._tick)

    # ── Public API ───────────────────────────────────────────────

    def open(self, on_apply=None, on_cancel=None):
        from spear_gui.overlay_defs import PREVIEW_BOX_DEF
        self._on_apply  = on_apply
        self._on_cancel = on_cancel
        self._closing   = False
        self._scroll = ScrollSystem(self._initial_display_mode, self._initial_cams, PREVIEW_BOX_DEF)
        self._broadcast('open')
        for btn in self._buttons: btn._set_phase('open')
        self._scroll.open_anim()
        self.show(); self.raise_(); self.activateWindow(); self.clearMask()
        f = _CSFilter(self); QApplication.instance().installEventFilter(f)
        self._filter = f
        self._tick_timer.start()

    def close_panel(self):
        if self._closing: return
        self._closing = True
        self._broadcast('close')
        for btn in self._buttons: btn._set_phase('close')
        self._scroll.close_anim()

    def _broadcast(self, phase: str):
        for p in self._polygons: p.set_phase(phase)
        for t in self._texts:    t.set_phase(phase)

    # ── Controls ─────────────────────────────────────────────────

    def scroll_display_mode(self, direction: int): # Left/Right Buttons
        if self._closing: return
        self._scroll.scroll(direction)

    def change_cams(self, delta: int): # Up/Down Buttons
        if self._closing: return
        new_n = max(1, min(MAX_ACTIVE_CAMS, self._scroll.num_cams + delta))
        if new_n == self._scroll.num_cams: return
        self._scroll.set_num_cams(new_n)

    # ── Handle buttons ───────────────────────────────────────────

    def _handle_button(self, btn: AnimatedButton):
        action = btn.defn.action
        if action == 'apply':
            if self._on_apply:
                self._on_apply(self._scroll.display_mode, self._scroll.num_cams)
        elif action == 'cancel':
            if self._on_cancel: self._on_cancel()
        elif action == 'scroll_left':
            self.scroll_display_mode(-1); return
        elif action == 'scroll_right':
            self.scroll_display_mode(+1); return
        elif action == 'cam_up':
            self.change_cams(+1); return
        elif action == 'cam_down':
            self.change_cams(-1); return
        if action in ('apply', 'cancel'):
            self.close_panel()

    # ── Tick ─────────────────────────────────────────────────────

    def _tick(self):
        for p   in self._polygons: p.update()
        for t   in self._texts:    t.update()
        for btn in self._buttons:  btn.update()
        self._scroll.update()
        if self._closing:
            if (all(p.phase_done() for p in self._polygons) and
                    all(t.phase_done() for t in self._texts) and
                    all(b.phase_done() for b in self._buttons) and
                    self._scroll.all_done()):
                self._tick_timer.stop(); self.hide()
                if self._filter:
                    QApplication.instance().removeEventFilter(self._filter)
                    self._filter = None
                self.deleteLater(); return
        self.update()

    # ── Input ────────────────────────────────────────────────────

    def keyPressEvent(self, event):
        k = event.key()
        if   k == Qt.Key_Left:  self.scroll_display_mode(-1)
        elif k == Qt.Key_Right: self.scroll_display_mode(+1)
        elif k == Qt.Key_Up:    self.change_cams(+1)
        elif k == Qt.Key_Down:  self.change_cams(-1)
        elif k in (Qt.Key_Return, Qt.Key_Enter):
            self._handle_button(next(b for b in self._buttons if b.defn.action == 'apply'))
        elif k == Qt.Key_Escape:
            self._handle_button(next(b for b in self._buttons if b.defn.action == 'cancel'))

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton: return
        mx, my = event.position().x(), event.position().y()
        w, h   = self.width(), self.height()
        for btn in self._buttons:
            if btn.hit_test(mx, my, w, h):
                btn._pressed = True; btn._set_phase('pressed'); return

    def mouseMoveEvent(self, event):
        mx, my = event.position().x(), event.position().y()
        w, h   = self.width(), self.height()
        for btn in self._buttons:
            now = btn.hit_test(mx, my, w, h)
            if now != btn._hovered:
                btn._hovered = now
                btn._set_phase('hovered' if now else 'unhovered')

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton: return
        mx, my = event.position().x(), event.position().y()
        w, h   = self.width(), self.height()
        for btn in self._buttons:
            if btn._pressed:
                btn._pressed = False; btn._set_phase('released')
                if btn.hit_test(mx, my, w, h):
                    btn.fire_event()
                    self._handle_button(btn)
                return

    def leaveEvent(self, event):
        for btn in self._buttons:
            if btn._hovered: btn._hovered = False; btn._set_phase('unhovered')

    def resizeEvent(self, event):
        super().resizeEvent(event); self.clearMask()

    # ── Paint ────────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        if not painter.isActive(): return
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1))
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        w, h = self.width(), self.height()
        for poly in self._polygons:
            poly.draw(painter, w, h, self.cam_w, self.cam_h)
        self._scroll.draw(painter, w, h)
        ctx = {
            'display_mode': self._scroll.display_mode,
            'num_cams':     self._scroll.num_cams,
            'max_cams':     MAX_ACTIVE_CAMS,
            'num_modes':    NUM_DISPLAY_MODES,
        }
        for text in self._texts:
            if text.hidden: continue
            text.draw_text(painter, w, h, cam_w, cam_h, ctx)
        for btn in self._buttons: btn.draw(painter, w, h)
        painter.end()


# ──────────────────────── _CSFilter ──────────────────────────────
def _filter_buttons(panel, event) -> bool:
    t = event.type()
    if t not in (QEvent.MouseButtonPress, QEvent.MouseButtonRelease, QEvent.MouseMove):
        return False
    gpos = event.globalPosition() if hasattr(event, 'globalPosition') else event.globalPos()
    g  = panel.mapToGlobal(panel.rect().topLeft())
    lx = gpos.x() - g.x(); ly = gpos.y() - g.y()
    pw = float(panel.width()); ph = float(panel.height())

    if t == QEvent.MouseButtonPress:
        if event.button() != Qt.LeftButton: return False
        for btn in panel._buttons:
            if btn.hit_test(lx, ly, pw, ph):
                btn._pressed = True; btn._set_phase('pressed'); return True
        if hasattr(panel, '_sliders'):
            for sl in panel._sliders:
                if sl.hit_test_knob(lx, ly, pw, ph):
                    panel._dragging_slider = sl
                    sl._pressed = True; sl.set_phase('pressed'); return True
        return False

    elif t == QEvent.MouseButtonRelease:
        if event.button() != Qt.LeftButton: return False
        if hasattr(panel, '_dragging_slider') and panel._dragging_slider is not None:
            sl = panel._dragging_slider
            sl._pressed = sl._dragging = False
            sl.set_phase('released')
            panel._dragging_slider = None
            hovered = sl._hovered
            QTimer.singleShot(150, lambda: sl.set_phase('hovered' if hovered else 'unhovered'))
            return True
        for btn in panel._buttons:
            if btn._pressed:
                btn._pressed = False
                btn._set_phase('released')
                if btn._hit_test_press_poly(lx, ly):
                    btn.fire_event()
                    panel._handle_button(btn)
                return True
        return False

    else:  # MouseMove
        if hasattr(panel, '_dragging_slider') and panel._dragging_slider is not None:
            panel._dragging_slider.drag_to(lx, ly, pw, ph); return True
        if hasattr(panel, '_sliders'):
            for sl in panel._sliders:
                now = sl.hit_test_knob(lx, ly, pw, ph)
                if now != sl._hovered:
                    sl._hovered = now; sl.set_phase('hovered' if sl._hovered else 'unhovered')
        for btn in panel._buttons:
            now = btn.hit_test(lx, ly, pw, ph)
            if now != btn._hovered:
                btn._hovered = now; btn._set_phase('hovered' if now else 'unhovered')
        return False


class SettingsMouseFilter(QObject):
    def __init__(self, panel): super().__init__(panel); self._panel = panel
    def eventFilter(self, obj, event):
        if self._panel is None or self._panel._closing: return False
        return _filter_buttons(self._panel, event)

class _CSFilter(QObject):
    def __init__(self, panel): super().__init__(panel); self._panel = panel
    def eventFilter(self, obj, event):
        if self._panel is None or self._panel._closing: return False
        return _filter_buttons(self._panel, event) 




# The following code aren't used anywhere and is kept just in case, delete once you confirmed these are no longer needed

# def _resolve_pt(P, w, h): return QPointF(P.x*w+P.px, P.y*h+P.py)


# def _interp_baseline_y(baseline: List[QPointF], x: float, fallback_y: float) -> float:
#     if not baseline:
#         return fallback_y
#     if x <= baseline[0].x():
#         return baseline[0].y()
#     if x >= baseline[-1].x():
#         return baseline[-1].y()
#     for i in range(len(baseline) - 1):
#         x0, x1 = baseline[i].x(), baseline[i + 1].x()
#         if x0 <= x <= x1:
#             t = (x - x0) / (x1 - x0) if x1 != x0 else 0.0
#             return baseline[i].y() + (baseline[i + 1].y() - baseline[i].y()) * t
#     return fallback_y
 





@dataclass
class AttributeDef:
    value_fn: Callable[[Any], float]
    set_fn:   Callable[[Any, float], None]
    min_val:  float = 0.0
    max_val:  float = 0.0
    step:     float = 0.0
    label:    str = ''
    unit:     str = ''
    delay:    float = 0.0