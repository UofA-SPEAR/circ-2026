"""overlay_system.py — Overlay engine, settings panel, camera select: all classes.
Def tables live in overlay_defs_camera.py.
"""
from __future__ import annotations
from typing import Optional, Dict, List, Tuple, Callable, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore    import Qt, QTimer, QElapsedTimer, QEasingCurve, QPointF, QRectF, QEvent, QObject
from PySide6.QtGui     import QColor, QPainter, QFont, QFontMetrics, QPolygonF, QPen, QRegion

# ──────────────────────── Easing cache ───────────────────────────

import math as _math
_HALF_PI = _math.pi / 2

def _ease(t: float, curve) -> float:
    if curve == QEasingCurve.OutQuint:  return 1.0 - (1.0 - t) ** 5
    if curve == QEasingCurve.OutCirc:
        t2 = t - 1.0; return _math.sqrt(1.0 - t2 * t2)
    if curve == QEasingCurve.InQuint:   return t ** 5
    if curve == QEasingCurve.InOutCirc:
        if t < 0.5:
            return 0.5 * (1.0 - _math.sqrt(1.0 - 4.0 * t * t))
        t2 = 2.0 * t - 2.0; return 0.5 * (_math.sqrt(1.0 - t2 * t2) + 1.0)
    if curve == QEasingCurve.OutBack:
        c = 1.70158; t2 = t - 1.0
        return 1.0 + (c + 1.0) * t2 ** 3 + c * t2 ** 2
    if curve == QEasingCurve.InOutQuad:
        if t < 0.5: return 2.0 * t * t
        return 1.0 - (-2.0 * t + 2.0) ** 2 / 2.0
    if curve == QEasingCurve.InCirc:    return 1.0 - _math.sqrt(1.0 - t * t)
    if curve == QEasingCurve.Linear:    return t
    if curve == QEasingCurve.OutCubic:  return 1.0 - (1.0 - t) ** 3
    if curve == QEasingCurve.InCubic:   return t ** 3
    if curve == QEasingCurve.OutQuad:   return 1.0 - (1.0 - t) ** 2
    if curve == QEasingCurve.InQuad:    return t * t
    if curve == QEasingCurve.OutSine:   return _math.sin(t * _HALF_PI)
    if curve == QEasingCurve.InSine:    return 1.0 - _math.cos(t * _HALF_PI)
    # Fallback for any unlisted curve
    c = QEasingCurve(curve); return c.valueForProgress(t)


# ──────────────────────── Rect ───────────────────────────────────

@dataclass(frozen=True)
class P:
    x: float = 0.0; y: float = 0.0

def Rect(
    p1: P, p2: P, px1: P = P(), px2: P = P(),
    tl: Optional[Tuple[P, P]] = None, tr: Optional[Tuple[P, P]] = None,
    br: Optional[Tuple[P, P]] = None, bl: Optional[Tuple[P, P]] = None,
    fill_color:    Optional[QColor] = None, outline_color: Optional[QColor] = None,
    line_width:    float = 0.0,
    uniform_scale: bool  = False,
    closed:        bool  = True,
    phases: Optional[Dict[str, Phase]] = None,
    h_flip = False, v_flip = False, d_flip = False
) -> 'PolygonDef':
    def _split(offset):
        if offset is None:
            return P(), P()
        return offset[0], offset[1]

    tl_r, tl_p = _split(tl)
    tr_r, tr_p = _split(tr)
    br_r, br_p = _split(br)
    bl_r, bl_p = _split(bl)

    points = [P(p1.x + tl_r.x, p1.y + tl_r.y), P(p2.x + tr_r.x, p1.y + tr_r.y), P(p2.x + br_r.x, p2.y + br_r.y), P(p1.x + bl_r.x, p2.y + bl_r.y)]
    px = [P(px1.x + tl_p.x, px1.y + tl_p.y), P(px2.x + tr_p.x, px1.y + tr_p.y), P(px2.x + br_p.x, px2.y + br_p.y), P(px1.x + bl_p.x, px2.y + bl_p.y)]

    return PolygonDef(
        points        = points,
        px            = px,
        fill_color    = fill_color    or QColor(0, 0, 0, 0),
        outline_color = outline_color or QColor(0, 0, 0, 0),
        line_width    = line_width,
        uniform_scale = uniform_scale,
        closed        = closed,
        phases        = phases or {},
        h_flip        = h_flip,
        v_flip        = v_flip,
        d_flip        = d_flip,
    )

def RectTween(
    p1: P, p2: P, px1: P = P(), px2: P = P(),
    tl: Optional[Tuple[P, P]] = None, tr: Optional[Tuple[P, P]] = None,
    br: Optional[Tuple[P, P]] = None, bl: Optional[Tuple[P, P]] = None,
    fill_color:    Optional[QColor] = None, outline_color: Optional[QColor] = None,
    line_width:    Optional[float]  = None, draw_progress: Optional[float]  = None,
    span:          Tuple[float, float] = (0, 1),
    start:         float = 0.0,             dur: float = 0.5,
    ease:          QEasingCurve.Type = QEasingCurve.OutQuint,
    blend:         bool             = False,
    prev_phase:    Optional[str]    = None,
) -> PolygonTween:
    def _split(offset):
        if offset is None:
            return P(), P()
        return offset[0], offset[1]

    tl_r, tl_p = _split(tl)
    tr_r, tr_p = _split(tr)
    br_r, br_p = _split(br)
    bl_r, bl_p = _split(bl)

    points = [P(p1.x + tl_r.x, p1.y + tl_r.y), P(p2.x + tr_r.x, p1.y + tr_r.y), P(p2.x + br_r.x, p2.y + br_r.y), P(p1.x + bl_r.x, p2.y + bl_r.y)]
    px = [P(px1.x + tl_p.x, px1.y + tl_p.y), P(px2.x + tr_p.x, px1.y + tr_p.y), P(px2.x + br_p.x, px2.y + br_p.y), P(px1.x + bl_p.x, px2.y + bl_p.y)]

    return PolygonTween(
        points        = points,
        px            = px,
        fill_color    = fill_color,
        outline_color = outline_color,
        line_width    = line_width,
        draw_progress = draw_progress,
        start         = start,
        dur           = dur,
        span          = span,
        ease          = ease,
        blend         = blend,
        prev_phase    = prev_phase,
    )

        
# ──────────────────────── Polygon ────────────────────────────────

@dataclass
class PolygonTween:
    points:        List[P]
    px:            Optional[List[P]]        = None
    span:          Tuple[float, float]      = (0, 1)
    start:         float                    = 0.0
    dur:           float                    = 0.5
    ease:          QEasingCurve.Type        = QEasingCurve.OutQuint
    blend:         bool                     = False
    fill_color:    Optional[QColor]         = None
    outline_color: Optional[QColor]         = None
    line_width:    Optional[float]          = None
    draw_progress: Optional[float]          = None
    prev_phase:    Optional[str]            = None
    _blend_anchor: Optional[float]          = None

@dataclass
class PolygonDef:
    points:        List[P]
    phases:        Dict[str, Phase]
    closed:        bool            = True
    line_width:    float           = 0.0
    uniform_scale: bool            = False
    px:            Optional[List[P]] = None
    fill_color:    Optional[QColor]  = None
    outline_color: Optional[QColor]  = None
    draw_progress: float             = 1.0
    h_flip:        bool              = False
    v_flip:        bool              = False
    d_flip:        bool              = False


# ──────────────────────── Geometry helpers ───────────────────────

def lerp_color(src, dst, v):
    sr=src.red();   dr=dst.red()
    sg=src.green(); dg=dst.green()
    sb=src.blue();  db=dst.blue()
    sa=src.alpha(); da=dst.alpha()
    return QColor(int(sr+(dr-sr)*v), int(sg+(dg-sg)*v), int(sb+(db-sb)*v), int(sa+(da-sa)*v))

# ──────────────────────── Tween dataclasses ──────────────────────

@dataclass
class Tween:
    rect: Rect; start: float; dur: float; ease: QEasingCurve.Type
    color: Optional[QColor] = None; px: Rect = field(default_factory=Rect)
    prev_phase: Optional[str] = None

@dataclass
class TextTween:
    x: float; y: float; start: float; dur: float; ease: QEasingCurve.Type
    color: Optional[QColor] = None; h_align: float = 0.0; v_align: float = 0.0
    font_size: Optional[float] = None; px: float = 0.0; py: float = 0.0
    prev_phase: Optional[str] = None
    span: Tuple[float, float] = (0, 1)

@dataclass
class Reset:
    prev_phase: Optional[str] = None; start: float = 0

@dataclass
class Phase:
    tweens: list


# ──────────────────────── _TweenDriver ───────────────────────────

class _TweenDriver:
    def __init__(self):
        self.hidden          = False
        self._phase: str     = ''
        self._prev:  str     = ''
        self._idx:   int     = 0
        self._tweens: list   = []
        self._timer          = QElapsedTimer()

    def _active_tweens(self, phase: str, prev: str, phases: dict) -> list:
        p = phases.get(phase)
        return [tw for tw in (p.tweens if p else [])
                if tw.prev_phase is None or tw.prev_phase == prev]

    @property
    def _cur(self): return self._tweens[self._idx] if self._idx < len(self._tweens) else None

    def set_phase(self, phase: str, phases: dict):
        self._prev   = self._phase; self._phase = phase
        self._idx    = 0
        self._tweens = self._active_tweens(phase, self._prev, phases)
        if self._tweens or phase in phases:
            self.hidden = False
        while self._idx < len(self._tweens) and isinstance(self._tweens[self._idx], Reset):
            self._reset_to_def()
            self._idx += 1
        self._save_start(); self._timer.restart()

    def _is_done(self): return self._idx >= len(self._tweens)
    def phase_done(self): return self._is_done()

    def _drive(self, hide_when_done=False):
        if self.hidden:
            return

        elapsed = self._timer.elapsed() / 1000.0
        tweens = self._tweens
        n = len(tweens)

        def _ease_inverse(y: float, curve) -> float:
            if y <= 0.0: return 0.0
            if y >= 1.0: return 1.0
            lo, hi = 0.0, 1.0
            for _ in range(48):
                mid = (lo + hi) * 0.5
                if _ease(mid, curve) < y:
                    lo = mid
                else:
                    hi = mid
            return (lo + hi) * 0.5

        i = self._idx
        while i < n:
            tw = tweens[i]
            if isinstance(tw, Reset):
                self._reset_to_def()
                i += 1
                continue

            group = [tw]
            if getattr(tw, "blend", False):
                j = i + 1
                while j < n:
                    group.append(tweens[j])
                    if not getattr(tweens[j], "blend", False):
                        j += 1
                        break
                    j += 1
            else:
                j = i + 1

            group_start = min(t.start for t in group)
            def _eff_end(tw):
                span = getattr(tw, 'span')
                t1   = _ease_inverse(span[1], tw.ease)
                return tw.start + t1 * tw.dur
            group_end      = max(_eff_end(tw) for tw in group)
            base_eff_end   = _eff_end(group[0])

            # Case A: not started yet
            if elapsed < group_start:
                return

            # Case B: active
            if elapsed <= group_end:
                base      = group[0]
                span      = getattr(base, 'span')
                s0, s1    = span
                t0        = _ease_inverse(s0, base.ease)
                t1        = _ease_inverse(s1, base.ease)
                eff_start = base.start + t0 * base.dur
                eff_dur   = (t1 - t0) * base.dur
                local     = elapsed - eff_start
                t         = min(1.0, max(0.0, local / eff_dur)) if eff_dur > 0 else 1.0
                v         = (_ease(t0 + t * (t1 - t0), base.ease) - s0) / (s1 - s0) if s1 > s0 else 1.0
                # Only apply base if we're within its window
                if elapsed >= eff_start:
                    self._apply(base, v)
                for btw in group[1:]:
                    # Each blend tween uses its own independent timing
                    span_b      = getattr(btw, 'span')
                    s0b, s1b    = span_b
                    t0b         = _ease_inverse(s0b, btw.ease)
                    t1b         = _ease_inverse(s1b, btw.ease)
                    eff_start_b = btw.start + t0b * btw.dur
                    eff_dur_b   = (t1b - t0b) * btw.dur
                    local_b     = elapsed - eff_start_b
                    if local_b < 0: continue
                    tb  = min(1.0, max(0.0, local_b / eff_dur_b)) if eff_dur_b > 0 else 1.0
                    vb  = (_ease(t0b + tb * (t1b - t0b), btw.ease) - s0b) / (s1b - s0b) if s1b > s0b else 1.0
                    self._apply_blend(btw, vb)
                self._idx = i
                return

            # Case C: finished
            else:
                self._snap_to(group[0])
                for btw in group[1:]:
                    span_b      = getattr(btw, 'span')
                    s0b, s1b    = span_b
                    t0b         = _ease_inverse(s0b, btw.ease)
                    t1b         = _ease_inverse(s1b, btw.ease)
                    eff_start_b = btw.start + t0b * btw.dur
                    eff_dur_b   = (t1b - t0b) * btw.dur
                    local_b     = group_end - eff_start_b
                    if local_b <= 0: continue
                    tb  = min(1.0, max(0.0, local_b / eff_dur_b)) if eff_dur_b > 0 else 1.0
                    vb  = (_ease(t0b + tb * (t1b - t0b), btw.ease) - s0b) / (s1b - s0b) if s1b > s0b else 1.0
                    self._apply_blend(btw, vb)
                self._save_start()
                if j <= i: j = i + 1
                self._idx = j
                i = j
                continue

        self._idx = n
        if hide_when_done:
            self.hidden = True
    
    def _save_start(self): pass
    def _snap_to(self, tw): pass
    def _reset_to_def(self): pass
    def _apply(self, tw, v): pass


@dataclass
class TextDef:
    x: float; y: float; text: str; font_size: float; color: QColor
    phases: Dict[str, Phase]; bold: bool; italic: bool; font_family: str
    h_align: float; v_align: float; uniform_scale: bool
    px: float = 0.0; py: float = 0.0
    text_fn: Optional[Callable[[Any], str]] = None; always_visible: bool = False


# ──────────────────────── AnimatedPolygon ────────────────────────
class AnimatedPolygon(_TweenDriver):
    def __init__(self, defn: PolygonDef):
        super().__init__()
        self.defn = defn
        n = len(defn.points)
        _zero_px = [P() for _ in range(n)]

        self._screen_offset = P(0.0, 0.0)
        self.cur_points       = [P(p.x, p.y) for p in defn.points]
        self.cur_px           = [P(p.x, p.y) for p in (defn.px or _zero_px)]
        self.cur_fill_color   = QColor(defn.fill_color)   if defn.fill_color   else QColor(0,0,0,0)
        self.cur_outline_color= QColor(defn.outline_color)if defn.outline_color else QColor(0,0,0,0)
        self.cur_line_width   = defn.line_width
        self.cur_draw_progress= defn.draw_progress

        self._sp  = [P(p.x, p.y) for p in self.cur_points]
        self._spx = [P(p.x, p.y) for p in self.cur_px]
        self._sf  = QColor(self.cur_fill_color)
        self._so  = QColor(self.cur_outline_color)
        self._slw = self.cur_line_width
        self._sdp = self.cur_draw_progress

        self._dirty      = True
        self._cached_poly= QPolygonF()
        self._cached_w   = 0
        self._cached_h   = 0

    # ── _TweenDriver hooks ───────────────────────────────────────

    def _save_start(self):
        self._sp  = [P(p.x, p.y) for p in self.cur_points]
        self._spx = [P(p.x, p.y) for p in self.cur_px]
        self._sf  = QColor(self.cur_fill_color)
        self._so  = QColor(self.cur_outline_color)
        self._slw = self.cur_line_width
        self._sdp = self.cur_draw_progress

    def _apply(self, tw: PolygonTween, v: float):
        for i, (sp, tp) in enumerate(zip(self._sp, tw.points)):
            self.cur_points[i] = P(sp.x + (tp.x - sp.x) * v,
                                   sp.y + (tp.y - sp.y) * v)
        if tw.px is not None:
            for i, (spx, tpx) in enumerate(zip(self._spx, tw.px)):
                self.cur_px[i] = P(spx.x + (tpx.x - spx.x) * v,
                                   spx.y + (tpx.y - spx.y) * v)
        if tw.fill_color    is not None: self.cur_fill_color    = lerp_color(self._sf, tw.fill_color,    v)
        if tw.outline_color is not None: self.cur_outline_color = lerp_color(self._so, tw.outline_color, v)
        if tw.line_width    is not None: self.cur_line_width    = self._slw + (tw.line_width - self._slw) * v
        if tw.draw_progress is not None: self.cur_draw_progress = self._sdp + (tw.draw_progress - self._sdp) * v
        self._dirty = True

    def _apply_blend(self, tw: PolygonTween, v: float):
        for i, tp in enumerate(tw.points):
            cp = self.cur_points[i]
            self.cur_points[i] = P(cp.x + tp.x * v, cp.y + tp.y * v)
        if tw.px is not None:
            for i, tpx in enumerate(tw.px):
                cpx = self.cur_px[i]
                self.cur_px[i] = P(cpx.x + tpx.x * v, cpx.y + tpx.y * v)
        if tw.fill_color    is not None: self.cur_fill_color    = lerp_color(self.cur_fill_color,    tw.fill_color,    v)
        if tw.outline_color is not None: self.cur_outline_color = lerp_color(self.cur_outline_color, tw.outline_color, v)
        if tw.line_width    is not None: self.cur_line_width    = self.cur_line_width + (tw.line_width - self.cur_line_width) * v
        if tw.draw_progress is not None: self.cur_draw_progress = self.cur_draw_progress + (tw.draw_progress - self.cur_draw_progress) * v
        self._dirty = True

    def _snap_to(self, tw: PolygonTween):
        self.cur_points = [P(p.x, p.y) for p in tw.points]
        if tw.px            is not None: self.cur_px            = [P(p.x, p.y) for p in tw.px]
        if tw.fill_color    is not None: self.cur_fill_color    = QColor(tw.fill_color)
        if tw.outline_color is not None: self.cur_outline_color = QColor(tw.outline_color)
        if tw.line_width    is not None: self.cur_line_width    = tw.line_width
        if tw.draw_progress is not None: self.cur_draw_progress = tw.draw_progress
        self._dirty = True

    def _reset_to_def(self):
        d = self.defn
        n = len(d.points)
        self.cur_points        = [P(p.x, p.y) for p in d.points]
        self.cur_px            = [P(p.x, p.y) for p in (d.px or [P()]*n)]
        self.cur_fill_color    = QColor(d.fill_color)    if d.fill_color    else QColor(0,0,0,0)
        self.cur_outline_color = QColor(d.outline_color) if d.outline_color else QColor(0,0,0,0)
        self.cur_line_width    = d.line_width
        self.cur_draw_progress = d.draw_progress
        self._dirty = True

    def set_phase(self, phase: str):
        super().set_phase(phase, self.defn.phases)
        self._dirty = True

    def update(self):
        self._drive(hide_when_done=False)

    def phase_done(self) -> bool:
        return self._is_done()

    # ── Geometry ─────────────────────────────────────────────────

    def _to_screen_pts(self, w: int, h: int, cam_w=1920, cam_h=1080) -> List[QPointF]:
        pts = []
        for p, px in zip(self.cur_points, self.cur_px):
            if self.defn.uniform_scale:
                s  = min(w / cam_w, h / cam_h)
                cx = s / (w / cam_w)
                cy = s / (h / cam_h)
                sx = (0.5 + (p.x - 0.5) * cx) * w + px.x
                sy = (0.5 + (p.y - 0.5) * cy) * h + px.y
            else:
                sx = p.x * w + px.x
                sy = p.y * h + px.y
            pts.append(QPointF(sx, sy))
        return pts

    def get_polygon(self, widget_w: int, widget_h: int, cam_w: int = 1920, cam_h: int = 1080) -> QPolygonF:
        if not self._dirty and self._cached_w == widget_w and self._cached_h == widget_h:
            return self._cached_poly
        pts = []
        ox, oy = self._screen_offset.x, self._screen_offset.y
        for p, px in zip(self.cur_points, self.cur_px):
            if self.defn.uniform_scale:
                s = min(widget_w / cam_w, widget_h / cam_h)
                cx = s / (widget_w / cam_w)
                cy = s / (widget_h / cam_h)
                sx = (0.5 + (p.x - 0.5) * cx) * widget_w + px.x + ox
                sy = (0.5 + (p.y - 0.5) * cy) * widget_h + px.y + oy
            else:
                sx = p.x * widget_w + px.x + ox
                sy = p.y * widget_h + px.y + oy
            pts.append(QPointF(sx, sy))
        self._cached_poly = QPolygonF(pts)
        self._cached_w = widget_w
        self._cached_h = widget_h
        self._dirty = False
        return self._cached_poly

    # ── Draw ─────────────────────────────────────────────────────

    def draw(self, painter: QPainter, w: int, h: int,
            cam_w: int = 1920, cam_h: int = 1080):
        if self.hidden:
            return
        pts = list(self.get_polygon(w, h, cam_w, cam_h))

        has_fill    = self.defn.closed and self.cur_fill_color.alpha() > 0
        has_outline = self.cur_line_width > 0 and self.cur_outline_color.alpha() > 0
        is_open     = not self.defn.closed

        if is_open:
            if not has_outline:
                return
            pen = QPen(self.cur_outline_color)
            pen.setWidthF(self.cur_line_width)
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            _draw_partial_polyline(painter, pts, self.cur_draw_progress)
            painter.setPen(Qt.NoPen)
            return

        poly = QPolygonF(pts)

        if has_fill and not has_outline:
            painter.setPen(Qt.NoPen)
            painter.setBrush(self.cur_fill_color)
            painter.drawPolygon(poly)

        elif has_outline and not has_fill:
            pen = QPen(self.cur_outline_color)
            pen.setWidthF(self.cur_line_width)
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPolygon(poly)
            painter.setPen(Qt.NoPen)

        elif has_fill and has_outline:
            pen = QPen(self.cur_outline_color)
            pen.setWidthF(self.cur_line_width)
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(self.cur_fill_color)
            painter.drawPolygon(poly)
            painter.setPen(Qt.NoPen)
    
class AnimatedText(_TweenDriver):
    def __init__(self, defn: TextDef):
        super().__init__()
        self.defn = defn; d = defn
        self.cur_x=d.x; self.cur_y=d.y; self.cur_px=d.px; self.cur_py=d.py
        self.cur_color=QColor(d.color); self.cur_font_size=d.font_size
        self.cur_h_align=d.h_align; self.cur_v_align=d.v_align
        self._sx=d.x; self._sy=d.y; self._spx=d.px; self._spy=d.py
        self._sc=QColor(d.color); self._sfs=d.font_size
        self._sha=d.h_align; self._sva=d.v_align
        self._dirty = True
        self._cached_font = None
        self._cached_dx = 0; self._cached_dy = 0
        self._cached_label = ''
        self._cached_tw = 0; self._cached_th = 0

    def _save_start(self):
        self._sx=self.cur_x; self._sy=self.cur_y
        self._spx=self.cur_px; self._spy=self.cur_py
        self._sc=QColor(self.cur_color); self._sfs=self.cur_font_size
        self._sha=self.cur_h_align; self._sva=self.cur_v_align

    def _snap_to(self, tw):
        self.cur_x=tw.x; self.cur_y=tw.y; self.cur_px=tw.px; self.cur_py=tw.py
        self.cur_h_align=tw.h_align; self.cur_v_align=tw.v_align
        if tw.color is not None:     self.cur_color     = QColor(tw.color)
        if tw.font_size is not None: self.cur_font_size = tw.font_size
        self._dirty = True

    def _reset_to_def(self):
        d = self.defn
        self.cur_x=d.x; self.cur_y=d.y; self.cur_px=d.px; self.cur_py=d.py
        self.cur_color=QColor(d.color); self.cur_font_size=d.font_size
        self.cur_h_align=d.h_align; self.cur_v_align=d.v_align
        self._dirty = True

    def _apply(self, tw, v):
        self.cur_x       = self._sx  + (tw.x       - self._sx)  * v
        self.cur_y       = self._sy  + (tw.y       - self._sy)  * v
        self.cur_px      = self._spx + (tw.px      - self._spx) * v
        self.cur_py      = self._spy + (tw.py      - self._spy) * v
        self.cur_h_align = self._sha + (tw.h_align - self._sha) * v
        self.cur_v_align = self._sva + (tw.v_align - self._sva) * v
        if tw.font_size is not None: self.cur_font_size = self._sfs + (tw.font_size - self._sfs) * v
        if tw.color is not None:     self.cur_color = lerp_color(self._sc, tw.color, v)
        self._dirty = True

    def set_phase(self, phase):
        super().set_phase(phase, self.defn.phases)
        self._dirty = True

    def update(self): self._drive(hide_when_done=not self.defn.always_visible)

    def resolve_text(self, context):
        template = self.defn.text or ''
        if self.defn.text_fn is not None and context is not None:
            try:    value = str(self.defn.text_fn(context))
            except: value = ''
            return template.replace('<#>', value) if '<#>' in template else value
        return template

    def build_font(self):
        if (self._cached_font is None or self._dirty):
            f = QFont()
            if self.defn.font_family: f.setFamily(self.defn.font_family)
            f.setPointSizeF(max(0.5, self.cur_font_size))
            f.setBold(self.defn.bold); f.setItalic(self.defn.italic)
            self._cached_font = f
        return self._cached_font

    def resolve_pos(self, widget_w, widget_h, cam_w, cam_h, label, font):
        if (not self._dirty and self._cached_label == label
                and self._cached_tw == widget_w and self._cached_th == widget_h):
            return self._cached_dx, self._cached_dy
        fm = QFontMetrics(font)
        if self.defn.uniform_scale:
            s  = min(widget_w/cam_w, widget_h/cam_h)
            bx = (0.5+(self.cur_x-0.5)*s/(widget_w/cam_w))*widget_w
            by = (0.5+(self.cur_y-0.5)*s/(widget_h/cam_h))*widget_h
        else:
            bx = self.cur_x*widget_w; by = self.cur_y*widget_h
        bx += self.cur_px; by += self.cur_py
        dx = int(bx - self.cur_h_align*fm.horizontalAdvance(label))
        dy = int(by + fm.ascent() - self.cur_v_align*fm.height())
        self._cached_dx = dx; self._cached_dy = dy
        self._cached_label = label
        self._cached_tw = widget_w; self._cached_th = widget_h
        self._dirty = False
        return dx, dy


# ──────────────────────── Line ───────────────────────────────────

def _resolve_pt(P, w, h): return QPointF(P.x*w+P.px, P.y*h+P.py)

def _draw_partial_polyline(painter: QPainter, pts: List[QPointF], t: float) -> None:
    if len(pts) < 2 or t <= 0:
        return
    if t >= 1.0:
        for i in range(len(pts) - 1):
            painter.drawLine(pts[i], pts[i + 1])
        return
    lengths = [
        _math.sqrt((pts[i+1].x()-pts[i].x())**2 + (pts[i+1].y()-pts[i].y())**2)
        for i in range(len(pts) - 1)
    ]
    total = sum(lengths)
    if total == 0:
        return
    target = total * t
    acc = 0.0
    for i, seg_len in enumerate(lengths):
        if acc >= target:
            break
        rem = target - acc
        if rem >= seg_len:
            painter.drawLine(pts[i], pts[i + 1])
            acc += seg_len
        else:
            frac = rem / seg_len if seg_len > 0 else 1.0
            painter.drawLine(
                pts[i],
                QPointF(
                    pts[i].x() + (pts[i+1].x() - pts[i].x()) * frac,
                    pts[i].y() + (pts[i+1].y() - pts[i].y()) * frac,
                ),
            )
            break


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
            label = text.resolve_text(self._context)
            if not label: continue
            font = text.build_font()
            painter.setFont(font); painter.setPen(text.cur_color)
            dx, dy = text.resolve_pos(w, h, self.cam_w, self.cam_h, label, font)
            painter.drawText(dx, dy, label)
            painter.setPen(Qt.NoPen)
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
            label = text.resolve_text(self._context)
            if not label: continue
            font = text.build_font()
            painter.setFont(font); painter.setPen(text.cur_color)
            dx, dy = text.resolve_pos(w, h, self.cam_w, self.cam_h, label, font)
            painter.drawText(dx, dy, label)
            painter.setPen(Qt.NoPen)

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
            label = text.resolve_text(self._context)
            if not label: continue
            font = text.build_font()
            painter.setFont(font)
            painter.setPen(text.cur_color)
            dx, dy = text.resolve_pos(w, h, self.cam_w, self.cam_h, label, font)
            painter.drawText(dx, dy, label)
            painter.setPen(Qt.NoPen)

class _LoadingMixin:
    def start(self):
        self._broadcast('create')

    def notify_loaded(self):
        if any(p._phase == 'loaded' for p in self._polygons): return
        QTimer.singleShot(50, self._do_loaded)

    def _do_loaded(self):
        self._broadcast('loaded')
        # The loaded animation takes ~1.8s max. After 2.5s, force _done=True
        # regardless of whether every sub-tween reports phase_done — some
        # tweens use easing curves whose _ease_inverse bisection doesn't
        # converge to exactly t=1.0, leaving them perpetually "active".
        QTimer.singleShot(2500, self._force_done)

    def _force_done(self):
        self._done = True

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
        from spear_gui.overlay_defs_camera_camera import LOADING_DEFS, LOADING_TEXT_DEFS
        super().__init__(LOADING_DEFS, parent=parent, cam_w=cam_w, cam_h=cam_h, text_defs=LOADING_TEXT_DEFS)
    def start(self):
        super().start(); self.show(); self._tick_timer.start()

class InlineLoadingOverlay(_LoadingMixin, InlineOverlay):
    def __init__(self, cam_w=1920, cam_h=1080):
        from spear_gui.overlay_defs_camera import LOADING_DEFS, LOADING_TEXT_DEFS
        super().__init__(LOADING_DEFS, cam_w=cam_w, cam_h=cam_h, text_defs=LOADING_TEXT_DEFS)

class SelectionOverlay(_SelectionMixin, AnimatedOverlay):
    def __init__(self, parent=None, cam_w=1920, cam_h=1080):
        from spear_gui.overlay_defs_camera import SELECTION_DEFS, SELECTION_TEXT_DEFS
        super().__init__(SELECTION_DEFS, parent=parent, cam_w=cam_w, cam_h=cam_h, text_defs=SELECTION_TEXT_DEFS)
        self._sel_init()
    def start(self):
        super().start(); self.show(); self._tick_timer.start()

class InlineSelectionOverlay(_SelectionMixin, InlineOverlay):
    def __init__(self, cam_w=1920, cam_h=1080):
        from spear_gui.overlay_defs_camera import SELECTION_DEFS, SELECTION_TEXT_DEFS
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

# ──────────────────────── Helpers ────────────────────────────────

def _with_alpha(color, alpha):
    c=QColor(color); c.setAlpha(alpha); return c

def _make_font(family, size):
    f=QFont(); f.setFamily(family); f.setPointSizeF(max(0.5,size)); return f

def _flip_p(p: P, h: bool, v: bool, blended: bool = False) -> P:
    if blended:
        return P(-p.x if h else p.x, -p.y if v else p.y)
    return P(1.0 - p.x if h else p.x, 1.0 - p.y if v else p.y)

def _flip_px(p: P, h: bool, v: bool) -> P:
    return P(-p.x if h else p.x, -p.y if v else p.y)

def _flip_polygon_def(defn: PolygonDef, h: bool, v: bool) -> PolygonDef:
    def _pts(pts, blended: bool = False):
        return [_flip_p(p, h, v, blended) for p in pts]
    def _pxs(pts):
        return [_flip_px(p, h, v) for p in pts]
    def _flip_tween(tw, prev_blended: bool):
        if isinstance(tw, Reset):
            return tw
        if isinstance(tw, PolygonTween):
            return PolygonTween(
                points        = _pts(tw.points, prev_blended),
                px            = _pxs(tw.px) if tw.px is not None else None,
                fill_color    = tw.fill_color,
                outline_color = tw.outline_color,
                line_width    = tw.line_width,
                draw_progress = tw.draw_progress,
                start         = tw.start,
                dur           = tw.dur,
                ease          = tw.ease,
                blend         = tw.blend,
                prev_phase    = tw.prev_phase,
                span          = tw.span,
            )
        return tw
    def _flip_phase(phase):
        tweens = []
        prev_blended = False
        for tw in phase.tweens:
            tweens.append(_flip_tween(tw, prev_blended))
            prev_blended = isinstance(tw, PolygonTween) and bool(tw.blend)
        return Phase(tweens)

    return PolygonDef(
        points        = _pts(defn.points),
        px            = _pxs(defn.px) if defn.px is not None else None,
        fill_color    = defn.fill_color,
        outline_color = defn.outline_color,
        line_width    = defn.line_width,
        uniform_scale = defn.uniform_scale,
        closed        = defn.closed,
        draw_progress = defn.draw_progress,
        phases        = {k: _flip_phase(v) for k, v in defn.phases.items()},
    )

def expand_defs(defs: List[PolygonDef]) -> List[PolygonDef]:
    result = []
    for defn in defs:
        result.append(defn)
        h = getattr(defn, 'h_flip', False)
        v = getattr(defn, 'v_flip', False)
        d = getattr(defn, 'd_flip', False)
        if h: result.append(_flip_polygon_def(defn, h=True,  v=False))
        if v: result.append(_flip_polygon_def(defn, h=False, v=True))
        if d: result.append(_flip_polygon_def(defn, h=True,  v=True))
    return result

# ──────────────────────── Slider system ──────────────────────────

@dataclass
class AttributeDef:
    value_fn: Callable[[Any], float]
    set_fn:   Callable[[Any, float], None]
    min_val:  float
    max_val:  float
    step:     float
    label:    str = ''
    unit:     str = ''
    delay:    float = 0.0


KNOB_SIZE_PX   = 8.0   # diamond half-extent
KNOB_HIT_PX    = 14.0  # square hit-box half-extent


def make_track_def(
    x: float, y: float, px: float, py: float,
    lx: float, lpx: float,
    h_px: float = 4.0,
    fill_color:    QColor = None,
    outline_color: QColor = None,
    phases: Dict[str, Phase] = None,
) -> PolygonDef:
    half = h_px / 2.0
    fc = fill_color    or QColor(255, 255, 255, 40)
    oc = outline_color or QColor(0, 0, 0, 0)
    return PolygonDef(
        points        = [P(x,      y), P(x + lx, y), P(x + lx, y), P(x,      y)],
        px            = [P(px, py - half), P(px + lpx, py - half),
                         P(px + lpx, py + half), P(px, py + half)],
        fill_color    = fc,
        outline_color = oc,
        closed        = True,
        phases        = phases or {},
    )


def make_knob_def(
    fill_color: QColor = None,
    phases: Dict[str, Phase] = None,
) -> PolygonDef:
    # All 4 points share the same normalised position (injected at runtime).
    # Only px offsets define the diamond shape.
    s  = KNOB_SIZE_PX
    fc = fill_color or QColor(255, 255, 255)
    return PolygonDef(
        points        = [P(0, 0), P(0, 0), P(0, 0), P(0, 0)],
        px            = [P(0, 0), P(0, 0), P(0, 0), P(0, 0)],
        fill_color    = fc,
        outline_color = QColor(0, 0, 0, 0),
        closed        = True,
        phases        = phases or {},
    )


def make_mark_fill_def(
    x: float, y: float, px: float, py: float,
    h_px: float = 8.0,
    fill_color: QColor = None,
    phases: Dict[str, Phase] = None,
) -> PolygonDef:
    """Fill bar between initial-value and knob position.
    Width is injected at runtime; only the left anchor is baked in."""
    half = h_px / 2.0
    fc   = fill_color or QColor(255, 255, 255, 60)
    return PolygonDef(
        points        = [P(x, y), P(x, y), P(x, y), P(x, y)],
        px            = [P(px, py - half), P(px, py - half),
                         P(px, py + half), P(px, py + half)],
        fill_color    = fc,
        outline_color = QColor(0, 0, 0, 0),
        closed        = True,
        phases        = phases or {},
    )


def make_mark_tick_def(
    x: float, y: float, px: float, py: float,
    w_px: float = 3.0,
    h_px: float = 14.0,
    fill_color: QColor = None,
    phases: Dict[str, Phase] = None,
) -> PolygonDef:
    """Thin vertical tick at the initial-value position.
    Position injected at runtime."""
    hw = w_px / 2.0
    hh = h_px / 2.0
    fc = fill_color or QColor(255, 255, 255, 200)
    return PolygonDef(
        points        = [P(x, y), P(x, y), P(x, y), P(x, y)],
        px            = [P(px - hw, py - hh), P(px + hw, py - hh),
                         P(px + hw, py + hh), P(px - hw, py + hh)],
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


@dataclass
class SliderGroupDef:
    x:   float;  y:   float
    px:  float = 0.0;  py: float = 0.0
    lx:  float = 0.0;  lpx: float = 0.0
    attr:   AttributeDef   = None
    track:  PolygonDef     = None
    knob:   PolygonDef     = None
    mark_fill: PolygonDef  = None
    mark_tick: PolygonDef  = None
    texts:  SliderTextDefs = field(default_factory=SliderTextDefs)
    phases: Dict[str, Phase] = field(default_factory=dict)
    delay: float = 0.0


# ──────────────────────── SliderGroup ────────────────────────────

class SliderGroup:
    def __init__(self, defn: SliderGroupDef, cam_w: int = 1920, cam_h: int = 1080):
        self.defn  = defn
        self.cam_w = cam_w
        self.cam_h = cam_h

        self._cur_value:     float = 0.0
        self._initial_value: float = 0.0
        self._dragging:      bool  = False
        self._hovered:       bool  = False

        self._track      = AnimatedPolygon(defn.track)     if defn.track     else None
        self._knob       = AnimatedPolygon(defn.knob)      if defn.knob      else None
        self._mark_fill  = AnimatedPolygon(defn.mark_fill) if defn.mark_fill else None
        self._mark_tick  = AnimatedPolygon(defn.mark_tick) if defn.mark_tick else None

        self._text_label   = AnimatedText(defn.texts.label)   if defn.texts.label   else None
        self._text_min     = AnimatedText(defn.texts.min_val) if defn.texts.min_val else None
        self._text_max     = AnimatedText(defn.texts.max_val) if defn.texts.max_val else None
        self._text_current = AnimatedText(defn.texts.current) if defn.texts.current else None

        _group_def = PolygonDef(
            points=[P(0, 0)], px=[P(0, 30)],   # <-- start offset, tween brings it to (0,0)
            fill_color=QColor(0, 0, 0, 0),
            outline_color=QColor(0, 0, 0, 0),
            closed=True,
            phases=defn.phases,
        )
        self._group = AnimatedPolygon(_group_def)

        self._track_x1: float = 0.0
        self._track_y1: float = 0.0
        self._track_x2: float = 0.0
        self._track_y2: float = 0.0
        self._knob_sx:  float = 0.0
        self._knob_sy:  float = 0.0
        self._knob_base_px: Optional[List[P]] = None
        self._last_knob_sx: float = 0.0
        self._last_knob_sy: float = 0.0
        self._last_text_min_x:  float = 0.0
        self._last_text_min_y:  float = 0.0
        self._last_text_max_x:  float = 0.0
        self._last_text_max_y:  float = 0.0
        self._last_text_cur_x:  float = 0.0
        self._last_text_cur_y:  float = 0.0
        self._snap_knob_to_start: bool = False

    def init_value(self, ctx):
        if self.defn.attr:
            self._cur_value = self._initial_value = self.defn.attr.value_fn(ctx)

    def commit(self, ctx):
        if self.defn.attr:
            self.defn.attr.set_fn(ctx, self._cur_value)
            self._initial_value = self._cur_value

    def revert(self):
        self._cur_value = self._initial_value

    @property
    def has_change(self) -> bool:
        return self._cur_value != self._initial_value

    def set_phase(self, phase: str):
        for comp in (self._track, self._knob, self._mark_fill,
                    self._mark_tick, self._group):
            if comp is not None:
                comp.set_phase(phase)
        for text in (self._text_label, self._text_min,
                    self._text_max, self._text_current):
            if text is not None:
                text.set_phase(phase)
        if phase == 'open':
            self._snap_knob_to_start = True
        if phase == 'open' and self.defn.delay != 0.0:
            delay = self.defn.delay
            for comp in (self._track, self._knob, self._mark_fill,
                        self._mark_tick, self._group):
                if comp is not None:
                    comp._tweens = [
                        type(tw)(**{**tw.__dict__, 'start': tw.start + delay})
                        if not isinstance(tw, Reset) else tw
                        for tw in comp._tweens
                    ]
            for text in (self._text_label, self._text_min,
                        self._text_max, self._text_current):
                if text is not None:
                    text._tweens = [
                        type(tw)(**{**tw.__dict__, 'start': tw.start + delay})
                        if not isinstance(tw, Reset) else tw
                        for tw in text._tweens
                    ]
        if phase == 'open' and self._knob is not None:
            self._knob_sx = self._track_x1
            self._last_knob_sx = self._track_x1
            self._last_knob_sy = self._track_y1
        if self._knob is not None:
            self._knob._spx = [
                P(p.x - self._last_knob_sx, p.y - self._last_knob_sy)
                for p in self._knob._spx
            ]
        if self._text_min is not None:
            self._text_min._spx -= self._last_text_min_x
            self._text_min._spy -= self._last_text_min_y
        if self._text_max is not None:
            self._text_max._spx -= self._last_text_max_x
            self._text_max._spy -= self._last_text_max_y
        if self._text_current is not None:
            self._text_current._spx -= self._last_text_cur_x
            self._text_current._spy -= self._last_text_cur_y

    def phase_done(self) -> bool:
        comps = [self._track, self._knob, self._mark_fill,
                 self._mark_tick, self._group,
                 self._text_label, self._text_min,
                 self._text_max,   self._text_current]
        return all(c.phase_done() for c in comps if c is not None)

    def hit_test_knob(self, mx: float, my: float, w: int, h: int) -> bool:
        return (abs(mx - self._knob_sx) <= KNOB_HIT_PX and
                abs(my - self._knob_sy) <= KNOB_HIT_PX)

    def drag_to(self, mx: float, my: float, w: int, h: int):
        span = self._track_x2 - self._track_x1
        if span == 0:
            return
        ratio = max(0.0, min(1.0, (mx - self._track_x1) / span))
        attr  = self.defn.attr
        if attr is None:
            return
        raw = attr.min_val + ratio * (attr.max_val - attr.min_val)
        if attr.step > 0:
            raw = round(raw / attr.step) * attr.step
        self._cur_value = max(attr.min_val, min(attr.max_val, raw))

    def update(self, widget_w: int, widget_h: int):
        # 1. Tick group
        self._group.update()
        gp  = self._group.cur_points[0]
        gpx = self._group.cur_px[0]
        g_dx = gp.x * widget_w + gpx.x
        g_dy = gp.y * widget_h + gpx.y

        # 2. Track End Points
        d = self.defn
        self._track_x1 = d.x * widget_w + d.px + g_dx
        self._track_y1 = d.y * widget_h + d.py + g_dy
        self._track_x2 = (d.x + d.lx) * widget_w + d.px + d.lpx + g_dx
        self._track_y2 = self._track_y1

        # 3. Track Screen Position
        if self._track is not None:
            self._track._screen_offset = P(g_dx, g_dy)
            self._track._dirty = True
            self._track.update()

        # 4. Knob Position
        attr = d.attr
        if attr and (attr.max_val - attr.min_val) != 0:
            ratio = (self._cur_value - attr.min_val) / (attr.max_val - attr.min_val)
        else:
            ratio = 0.0
        ratio = max(0.0, min(1.0, ratio))
        self._knob_sx = self._track_x1 + ratio * (self._track_x2 - self._track_x1)
        self._knob_sy = self._track_y1
        if self._snap_knob_to_start:
            print(f'{self._knob_sx} + {self._track_x1}')
            self._knob._spx = [
                P(self._track_x1 - self._knob_sx, self._track_y1 - self._knob_sy)
                for p in self._knob.cur_px
            ]
            self._last_knob_sx = self._track_x1
            self._last_knob_sy = self._track_y1
            self._snap_knob_to_start = False

        # 5. Initial Mark Position
        if attr and (attr.max_val - attr.min_val) != 0:
            init_ratio = (self._initial_value - attr.min_val) / (attr.max_val - attr.min_val)
        else:
            init_ratio = 0.0
        init_ratio = max(0.0, min(1.0, init_ratio))
        self._init_sx = self._track_x1 + init_ratio * (self._track_x2 - self._track_x1)

        # 6. Knob
        if self._knob is not None:
            self._knob.cur_px = [
                P(p.x - self._last_knob_sx, p.y - self._last_knob_sy)
                for p in self._knob.cur_px
            ]
            self._knob.update()
            self._knob.cur_px = [
                P(p.x + self._knob_sx, p.y + self._knob_sy)
                for p in self._knob.cur_px
            ]
            self._last_knob_sx = self._knob_sx
            self._last_knob_sy = self._knob_sy
            self._knob._dirty = True

        # 7. Mark Fill
        if self._mark_fill is not None:
            self._mark_fill.update()
            left_x  = min(self._knob_sx, self._init_sx)
            right_x = max(self._knob_sx, self._init_sx)
            half = (self.defn.mark_fill.px[2].y - self.defn.mark_fill.px[0].y) / 2
            self._mark_fill.cur_points = [P(0, 0)] * 4
            self._mark_fill.cur_px = [
                P(left_x,  self._knob_sy - half),
                P(right_x, self._knob_sy - half),
                P(right_x, self._knob_sy + half),
                P(left_x,  self._knob_sy + half),
            ]
            self._mark_fill._dirty = True

        # 8. Mark Tick
        if self._mark_tick is not None:
            self._mark_tick.update()
            base_px = self.defn.mark_tick.px or [P(0, 0)] * 4
            self._mark_tick.cur_points = [P(0, 0)] * 4
            self._mark_tick.cur_px = [
                P(base_px[0].x + self._init_sx, base_px[0].y + self._knob_sy),
                P(base_px[1].x + self._init_sx, base_px[1].y + self._knob_sy),
                P(base_px[2].x + self._init_sx, base_px[2].y + self._knob_sy),
                P(base_px[3].x + self._init_sx, base_px[3].y + self._knob_sy),
            ]
            self._mark_tick._dirty = True

        # 9. Label text
        if self._text_label is not None:
            self._text_label.update()

        if self._text_min is not None:
            self._text_min.cur_px -= self._last_text_min_x
            self._text_min.cur_py -= self._last_text_min_y
            self._text_min.update()
            self._text_min.cur_x   = 0.0
            self._text_min.cur_y   = 0.0
            self._text_min.cur_px  = self._track_x1 + self._text_min.cur_px
            self._text_min.cur_py  = self._track_y1 + self._text_min.cur_py
            self._last_text_min_x  = self._track_x1
            self._last_text_min_y  = self._track_y1
            self._text_min._dirty  = True

        if self._text_max is not None:
            self._text_max.cur_px -= self._last_text_max_x
            self._text_max.cur_py -= self._last_text_max_y
            self._text_max.update()
            self._text_max.cur_x   = 0.0
            self._text_max.cur_y   = 0.0
            self._text_max.cur_px  = self._track_x2 + self._text_max.cur_px
            self._text_max.cur_py  = self._track_y1 + self._text_max.cur_py
            self._last_text_max_x  = self._track_x2
            self._last_text_max_y  = self._track_y1
            self._text_max._dirty  = True

        if self._text_current is not None:
            self._text_current.cur_px -= self._last_text_cur_x
            self._text_current.cur_py -= self._last_text_cur_y
            self._text_current.update()
            self._text_current.cur_x   = 0.0
            self._text_current.cur_y   = 0.0
            self._text_current.cur_px  = self._knob_sx + self._text_current.cur_px
            self._text_current.cur_py  = self._knob_sy + self._text_current.cur_py
            self._last_text_cur_x      = self._knob_sx
            self._last_text_cur_y      = self._knob_sy
            self._text_current._dirty  = True
        
            
    def draw(self, painter: QPainter, w: int, h: int):
        cam_w, cam_h = self.cam_w, self.cam_h
        if self._track     is not None: self._track.draw(painter, w, h, cam_w, cam_h)
        if self._mark_fill is not None: self._mark_fill.draw(painter, w, h, cam_w, cam_h)
        if self._mark_tick is not None: self._mark_tick.draw(painter, w, h, cam_w, cam_h)
        if self._knob      is not None: self._knob.draw(painter, w, h, cam_w, cam_h)
        for text in (self._text_label, self._text_min,
                    self._text_max, self._text_current):
            if text is None or text.hidden:
                continue
            label = text.resolve_text(self)
            if not label:
                continue
            font  = text.build_font()
            painter.setFont(font)
            painter.setPen(text.cur_color)
            dx, dy = text.resolve_pos(w, h, cam_w, cam_h, label, font)
            painter.drawText(dx, dy, label)
            painter.setPen(Qt.NoPen)

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

@dataclass
class ButtonDef:
    poly:   PolygonDef
    label:  str
    action: str
    hx1:    P = field(default_factory=P)
    hx2:    P = field(default_factory=P)
    hpx1:   P = field(default_factory=P)
    hpx2:   P = field(default_factory=P)
    text:   Optional[TextDef] = None
    font_family: str   = 'Oxanium SemiBold'
    font_size:   float = 10.0
    text_color:  QColor = field(default_factory=lambda: QColor(255, 255, 255))

# ──────────────────────── AnimatedButton ─────────────────────────
class AnimatedButton:
    def __init__(self, defn: ButtonDef, cam_w: int = 1920, cam_h: int = 1080):
        self.defn     = defn
        self.cam_w    = cam_w
        self.cam_h    = cam_h
        self._hovered = False
        self._pressed = False
        self._polygon = AnimatedPolygon(defn.poly)
        self._text    = AnimatedText(defn.text) if defn.text else None
        self._locked  = False
        self._cur_phase = ''

    def _set_phase(self, phase: str):
        # Always allow open to interrupt close, always allow open/close to set
        if self._locked and phase not in ('open', 'close'):
            return
        self._cur_phase = phase
        self._locked = phase in ('open', 'close')
        self._polygon.set_phase(phase)
        if self._text is not None:
            self._text.set_phase(phase)

    def _hit_rect(self, w: int, h: int) -> Tuple[float, float, float, float]:
        d  = self.defn
        x1 = d.hx1.x * w + d.hpx1.x
        y1 = d.hx1.y * h + d.hpx1.y
        x2 = d.hx2.x * w + d.hpx2.x
        y2 = d.hx2.y * h + d.hpx2.y
        return x1, y1, x2, y2

    def hit_test(self, mx: float, my: float, w: int, h: int) -> bool:
        poly = self._polygon.get_polygon(w, h, self.cam_w, self.cam_h)
        return poly.containsPoint(QPointF(mx, my), Qt.OddEvenFill)

    def hit_test_global(self, gx: float, gy: float, panel) -> bool:
        return self.hit_test(gx - panel.x(), gy - panel.y(), panel.width(), panel.height())

    def update(self):
        self._polygon.update()
        if self._text is not None:
            self._text.update()
        if self._locked and self._polygon.phase_done():
            self._locked = False

    def phase_done(self) -> bool:
        text_done = self._text.phase_done() if self._text is not None else True
        return self._polygon.phase_done() and text_done

    def draw(self, painter: QPainter, w: int, h: int):
        self._polygon.draw(painter, w, h, self.cam_w, self.cam_h)
        if self._text is not None and not self._text.hidden:
            label = self._text.resolve_text(None)
            if label:
                font = self._text.build_font()
                painter.setFont(font)
                painter.setPen(self._text.cur_color)
                dx, dy = self._text.resolve_pos(w, h, self.cam_w, self.cam_h, label, font)
                painter.drawText(dx, dy, label)
                painter.setPen(Qt.NoPen)
        elif self.defn.label:
            # fallback: center label in polygon bounding rect
            poly = self._polygon.get_polygon(w, h, self.cam_w, self.cam_h)
            r    = poly.boundingRect()
            f    = _make_font(self.defn.font_family, self.defn.font_size)
            fm   = QFontMetrics(f)
            painter.setFont(f)
            painter.setPen(self.defn.text_color)
            painter.drawText(
                int(r.x() + (r.width()  - fm.horizontalAdvance(self.defn.label)) / 2),
                int(r.y() + (r.height() + fm.ascent()) / 2 - fm.descent()),
                self.defn.label,
            )
            painter.setPen(Qt.NoPen)

# ──────────────────────── SettingsOverlay ────────────────────────

class SettingsOverlay(QWidget):
    TICK_MS=16

    def __init__(self, polygon_defs, text_defs, slider_defs, button_defs, cam_w=1920, cam_h=1080, parent=None):
        super().__init__(parent)
        if parent is None:
            # Legacy: standalone top-level window
            self.setWindowFlags(Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint|Qt.Window)
            self.setAttribute(Qt.WA_TranslucentBackground)
        else:
            # Child widget filling the container — no window flags needed,
            # WA_NoSystemBackground lets QPainter draw transparent content.
            self.setAttribute(Qt.WA_NoSystemBackground)
            self.setAutoFillBackground(False)
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
        self.show(); self.raise_()
        if self.parent() is None:
            self.activateWindow()
        self.clearMask()
        app=QApplication.instance()
        if app:
            f=SettingsMouseFilter(self)
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
            sl.set_phase('hovered' if sl._hovered else 'unhovered')
            self._dragging_slider = None
            return
        for btn in self._buttons:
            if btn._pressed:
                btn._pressed = False; btn._set_phase('released')
                if btn.hit_test(mx, my, w, h): self._handle_button(btn)
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
        painter.setRenderHint(QPainter.Antialiasing)
        if self.parent() is None:
            # Top-level: clear to transparent first
            painter.setCompositionMode(QPainter.CompositionMode_Source)
            painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        else:
            # Child widget: just fill with the panel background color
            painter.fillRect(self.rect(), QColor(8, 8, 14, 230))
        painter.setPen(Qt.NoPen)
        w, h = self.width(), self.height()
        for poly in self._polygons:
            poly.draw(painter, w, h, self.cam_w, self.cam_h)
        for text in self._texts:
            if text.hidden: continue
            label = text.resolve_text(self._context)
            if not label: continue
            font = text.build_font(); painter.setFont(font); painter.setPen(text.cur_color)
            dx, dy = text.resolve_pos(w, h, self.cam_w, self.cam_h, label, font)
            painter.drawText(dx, dy, label); painter.setPen(Qt.NoPen)
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
        name_size  = 13.0 if is_centre else 9.0
        name_alpha = 255  if is_centre else SIDE_ALPHA
        name_font  = _make_font('Oxanium SemiBold', name_size)
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
        super().__init__(parent)
        if parent is None:
            # Legacy: standalone top-level window
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Window)
            self.setAttribute(Qt.WA_TranslucentBackground)
        else:
            # Child widget filling the container
            self.setAttribute(Qt.WA_NoSystemBackground)
            self.setAutoFillBackground(False)
        self.setMouseTracking(True); self.setFocusPolicy(Qt.StrongFocus)
        self.cam_w = cam_w; self.cam_h = cam_h
        self._initial_display_mode = initial_display_mode % NUM_DISPLAY_MODES
        self._initial_cams         = max(1, min(initial_cams, MAX_ACTIVE_CAMS))
        self._closing = False
        self._on_apply = self._on_cancel = None
        self._filter = None
        from spear_gui.overlay_defs_camera import CS_DEFS, CS_TEXT_DEFS, CS_BUTTON_DEFS, PREVIEW_BOX_DEF
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
        from spear_gui.overlay_defs_camera import PREVIEW_BOX_DEF
        self._on_apply  = on_apply
        self._on_cancel = on_cancel
        self._closing   = False
        self._scroll = ScrollSystem(self._initial_display_mode, self._initial_cams, PREVIEW_BOX_DEF)
        self._broadcast('open')
        for btn in self._buttons: btn._set_phase('open')
        self._scroll.open_anim()
        self.show(); self.raise_()
        if self.parent() is None:
            self.activateWindow()
        self.clearMask()
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
                if btn.hit_test(mx, my, w, h): self._handle_button(btn)
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
        painter.setRenderHint(QPainter.Antialiasing)
        if self.parent() is None:
            painter.setCompositionMode(QPainter.CompositionMode_Source)
            painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        else:
            painter.fillRect(self.rect(), QColor(8, 8, 14, 230))
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
            label = text.resolve_text(ctx)
            if not label: continue
            font = text.build_font(); painter.setFont(font); painter.setPen(text.cur_color)
            dx, dy = text.resolve_pos(w, h, self.cam_w, self.cam_h, label, font)
            painter.drawText(dx, dy, label); painter.setPen(Qt.NoPen)
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
            sl = panel._dragging_slider; sl._pressed = sl._dragging = False
            sl.set_phase('hovered' if sl._hovered else 'unhovered')
            panel._dragging_slider = None; return True
        for btn in panel._buttons:
            if btn._pressed:
                btn._pressed = False; btn._set_phase('released')
                if btn.hit_test(lx, ly, pw, ph): panel._handle_button(btn)
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