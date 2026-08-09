from __future__ import annotations
from typing import Optional, Dict, List, Tuple, Callable, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore    import Qt, QTimer, QElapsedTimer, QEasingCurve, QPointF, QRectF, QEvent, QObject
from PySide6.QtGui     import QColor, QPainter, QFont, QFontMetrics, QPolygonF, QPen, QBrush, QRegion, QPainterPath, QLinearGradient, QRadialGradient
import time
import collections
import statistics
import threading
import math as _math
import uuid

from spear_gui.gui_vars import MONITOR_RESOLUTIONS

_window_layer_registry: List[Tuple[int, List['WindowDef']]] = []

def register_windows(layer: int, windows: List['WindowDef']) -> None:
    _window_layer_registry.append((layer, windows))

def get_ordered_windows() -> List['WindowDef']:
    result = []
    for _, windows in sorted(_window_layer_registry, key=lambda x: x[0]):
        result.extend(windows)
    return result

_events: Dict[str, 'EventDef'] = {}

def register_event(defn: 'EventDef') -> 'EventDef':
    _events[defn.name] = defn
    return defn

def get_event(name: str) -> 'EventDef':
    return _events[name]

_gradients: Dict[str, GradientDef] = {}

def register_gradient(defn: GradientDef) -> GradientDef:
    defn._animated = _AnimatedGradient(defn)
    _gradients[defn.name] = defn
    return defn

def get_gradient(name: str) -> GradientDef:
    return _gradients[name]

_pixmap_cache: Dict[str, Optional['QPixmap']] = {}

def _get_pixmap(path: str):
    from PySide6.QtGui import QPixmap
    if path in _pixmap_cache:
        return _pixmap_cache[path]
    pm = QPixmap(path)
    if pm.isNull():
        print(f'[image] failed to load: {path}')
        _pixmap_cache[path] = None
        return None
    _pixmap_cache[path] = pm
    return pm

_active_override_textboxes: List['AnimatedTextbox'] = []

def get_active_override_textbox() -> Optional['AnimatedTextbox']:
    return _active_override_textboxes[-1] if _active_override_textboxes else None

@dataclass(frozen=True)
class P:
    x: float = 0.0
    y: float = 0.0

@dataclass
class GradientStop:
    position: float
    color:    QColor

class _RectCornerRef:
    __slots__ = ('corner1', 'corner2', 'tl', 'tr', 'br', 'bl')
    def __init__(self, corner1, corner2, tl, tr, br, bl):
        self.corner1 = corner1
        self.corner2 = corner2
        self.tl = tl; self.tr = tr; self.br = br; self.bl = bl

def _resolve_corner(val):
    if isinstance(val, EventDef):
        v = val.value
        return v if isinstance(v, P) else P()
    return val

def _rect_corner_ref_to_points(ref: '_RectCornerRef') -> List[P]:
    c1 = _resolve_corner(ref.corner1)
    c2 = _resolve_corner(ref.corner2)
    return [
        P(c1.x + ref.tl.x, c1.y + ref.tl.y),
        P(c2.x + ref.tr.x, c1.y + ref.tr.y),
        P(c2.x + ref.br.x, c2.y + ref.br.y),
        P(c1.x + ref.bl.x, c2.y + ref.bl.y),
    ]

def RectDef(
    p1:                  P                             = P(), 
    p2:                  P                             = P(), 
    px1:                 P                             = P(), 
    px2:                 P                             = P(),
    tl:                  Optional[Tuple[P, P]]         = None, 
    tr:                  Optional[Tuple[P, P]]         = None,
    br:                  Optional[Tuple[P, P]]         = None, 
    bl:                  Optional[Tuple[P, P]]         = None,
    fill_color:          Optional[QColor]              = QColor(255, 255, 255, 255), 
    outline_color:       Optional[QColor]              = None,
    outline_width:          float                         = 0.0, 
    draw_progress:       Optional[float]               = None,
    uniform_scale:       bool                          = False,
    closed:              bool                          = True,
    h_flip:              bool                          = False, 
    v_flip:              bool                          = False, 
    d_flip:              bool                          = False,
    phases:              Optional[Dict[str, Phase]]    = None,
    gradient:            Optional['GradientDef']       = None,
    gradient_p1:         P                             = P(),
    gradient_px1:        P                             = P(),
    gradient_p2:         P                             = P(),
    gradient_px2:        P                             = P(),
    rot_center_p:        P                             = P(),
    rot_center_px:       P                             = P(),
    rot_target_p:        P                             = P(),
    rot_target_px:       P                             = P(),
    rot_angle_initial:   float                         = 0.0,
    rot_angle:           float                         = 0.0,
    rot_angle_fn:        Any                           = 0.0,
    image_path:          Optional[str]                 = None,
    image_opacity:       float                         = 1.0,
    visible_threshold_x: float                         = 0.0,
    visible_threshold_y: float                         = 0.0,
    phase_override:      Optional[Any]                 = None,
    pos_fn:              Optional[Callable[[], Union[P, List[P]]]] = None
) -> 'PolygonDef':
    def _split(offset):
        if offset is None:
            return P(), P()
        return offset[0], offset[1]

    tl_r, tl_p = _split(tl)
    tr_r, tr_p = _split(tr)
    br_r, br_p = _split(br)
    bl_r, bl_p = _split(bl)

    p  = [P(p1.x + tl_r.x, p1.y + tl_r.y), P(p2.x + tr_r.x, p1.y + tr_r.y), P(p2.x + br_r.x, p2.y + br_r.y), P(p1.x + bl_r.x, p2.y + bl_r.y)]
    px = [P(px1.x + tl_p.x, px1.y + tl_p.y), P(px2.x + tr_p.x, px1.y + tr_p.y), P(px2.x + br_p.x, px2.y + br_p.y), P(px1.x + bl_p.x, px2.y + bl_p.y)]

    return PolygonDef(
        p                   = p,
        px                  = px,
        fill_color          = fill_color    or QColor(0, 0, 0, 0),
        outline_color       = outline_color or QColor(0, 0, 0, 0),
        outline_width       = outline_width,
        draw_progress       = draw_progress,
        uniform_scale       = uniform_scale,
        closed              = closed,
        phases              = phases or {},
        h_flip              = h_flip,
        v_flip              = v_flip,
        d_flip              = d_flip,
        gradient            = gradient,
        gradient_p1         = gradient_p1,
        gradient_px1        = gradient_px1,
        gradient_p2         = gradient_p2,
        gradient_px2        = gradient_px2,
        rot_center_p        = rot_center_p,
        rot_center_px       = rot_center_px,
        rot_target_p        = rot_target_p,
        rot_target_px       = rot_target_px,
        rot_angle_initial   = rot_angle_initial,
        rot_angle           = rot_angle,
        rot_angle_fn        = rot_angle_fn,
        image_path          = image_path,
        image_opacity       = image_opacity,
        visible_threshold_x = visible_threshold_x,
        visible_threshold_y = visible_threshold_y,
        phase_override      = phase_override,
        pos_fn              = pos_fn,
    )

def RectTween(
    p1:            P                     = None, 
    p2:            P                     = None, 
    px1:           P                     = None, 
    px2:           P                     = None,
    tl:            Optional[Tuple[P, P]] = None, 
    tr:            Optional[Tuple[P, P]] = None,
    br:            Optional[Tuple[P, P]] = None, 
    bl:            Optional[Tuple[P, P]] = None,
    fill_color:    Optional[QColor]      = None, 
    outline_color: Optional[QColor]      = None,
    outline_width:    Optional[float]    = None, 
    draw_progress: Optional[float]       = None,
    span:          Tuple[float, float]   = (0, 1),
    start:         float                 = 0.0,             
    dur:           float                 = 0.5,
    ease:          QEasingCurve.Type     = None,
    blend:         bool                  = False,
    prev_phase:    Optional[str]         = None,
    gradient_p1:   Optional[P]           = None,
    gradient_px1:  Optional[P]           = None,
    gradient_p2:   Optional[P]           = None,
    gradient_px2:  Optional[P]           = None
) -> PolygonTween:
    from PySide6.QtCore import QEasingCurve as _QEC
    if ease is None:
        ease = QEasingCurve.OutQuint
 
    def _split(offset):
        if offset is None:
            return None, None
        return offset[0], offset[1]
 
    tl_r, tl_p = _split(tl)
    tr_r, tr_p = _split(tr)
    br_r, br_p = _split(br)
    bl_r, bl_p = _split(bl)
 
    def _has_event(*vals):
        return any(isinstance(v, EventDef) for v in vals)

    def _make_p(base1, base2):
        if base1 is None and base2 is None and tl_r is None and tr_r is None and br_r is None and bl_r is None:
            return None
        if _has_event(base1, base2):
            return _RectCornerRef(
                corner1=base1 if base1 is not None else P(),
                corner2=base2 if base2 is not None else P(),
                tl=tl_r or P(), tr=tr_r or P(), br=br_r or P(), bl=bl_r or P(),
            )
        _p1  = base1  or P()
        _p2  = base2  or P()
        _tlr = tl_r   or P()
        _trr = tr_r   or P()
        _brr = br_r   or P()
        _blr = bl_r   or P()
        return [
            P(_p1.x + _tlr.x, _p1.y + _tlr.y),
            P(_p2.x + _trr.x, _p1.y + _trr.y),
            P(_p2.x + _brr.x, _p2.y + _brr.y),
            P(_p1.x + _blr.x, _p2.y + _blr.y),
        ]

    def _make_px(base1, base2):
        if base1 is None and base2 is None and tl_p is None and tr_p is None and br_p is None and bl_p is None:
            return None
        if _has_event(base1, base2):
            return _RectCornerRef(
                corner1=base1 if base1 is not None else P(),
                corner2=base2 if base2 is not None else P(),
                tl=tl_p or P(), tr=tr_p or P(), br=br_p or P(), bl=bl_p or P(),
            )
        _px1 = base1 or P()
        _px2 = base2 or P()
        _tlp = tl_p  or P()
        _trp = tr_p  or P()
        _brp = br_p  or P()
        _blp = bl_p  or P()
        return [
            P(_px1.x + _tlp.x, _px1.y + _tlp.y),
            P(_px2.x + _trp.x, _px1.y + _trp.y),
            P(_px2.x + _brp.x, _px2.y + _brp.y),
            P(_px1.x + _blp.x, _px2.y + _blp.y),
        ]
 
    return PolygonTween(
        p             = _make_p(p1, p2),
        px            = _make_px(px1, px2),
        fill_color    = fill_color,
        outline_color = outline_color,
        outline_width = outline_width,
        draw_progress = draw_progress,
        start         = start,
        dur           = dur,
        span          = span,
        ease          = ease,
        blend         = blend,
        prev_phase    = prev_phase,
        gradient_p1   = gradient_p1,
        gradient_px1  = gradient_px1,
        gradient_p2   = gradient_p2,
        gradient_px2  = gradient_px2,
    )

        
# ──────────────────────── Polygon ────────────────────────────────

@dataclass
class PolygonDef:
    p:                   List[P]                               = field(default_factory=lambda: [P(0, 0), P(0, 0)])
    px:                  Optional[List[P]]                     = None
    phases:              Optional[Dict[str, Phase]]            = None
    closed:              bool                                  = True
    outline_width:          float                                 = 0.0
    uniform_scale:       bool                                  = False
    fill_color:          Optional[QColor]                      = None
    outline_color:       Optional[QColor]                      = None
    draw_progress:       float                                 = 1.0
    h_flip:              bool                                  = False
    v_flip:              bool                                  = False
    d_flip:              bool                                  = False
    gradient:            Optional['GradientDef']               = None
    gradient_p1:         P                                     = P()
    gradient_px1:        P                                     = P()
    gradient_p2:         P                                     = P()
    gradient_px2:        P                                     = P()
    rot_center_p:        P                                     = field(default_factory=P)
    rot_center_px:       P                                     = field(default_factory=P)
    rot_target_p:        P                                     = field(default_factory=P)
    rot_target_px:       P                                     = field(default_factory=P)
    rot_angle_initial:   float                                 = 0.0
    rot_angle:           float                                 = 0.0
    rot_angle_fn:        Any                                   = 0.0
    image_path:          Optional[str]                         = None
    image_opacity:       float                                 = 1.0
    dynamic_px:          Optional[Callable[[int,int],List[P]]] = None
    visible_threshold_x: float                                 = 0.0
    visible_threshold_y: float                                 = 0.0
    phase_override:      Optional[Any]                         = None
    pos_fn:              Optional[Callable[[], Union[P, List[P]]]] = None
    export_p:            Optional[EventDef]                    = None
    export_px:           Optional[EventDef]                    = None

@dataclass
class PolygonTween:
    # Properties
    p:                 Optional[List[P]]   = None
    px:                Optional[List[P]]   = None
    fill_color:        Optional[QColor]    = None
    outline_color:     Optional[QColor]    = None
    outline_width:        Optional[float]     = None
    draw_progress:     Optional[float]     = None
    _blend_anchor:     Optional[float]     = None
    gradient_p1:       Optional[P]         = None
    gradient_px1:      Optional[P]         = None
    gradient_p2:       Optional[P]         = None
    gradient_px2:      Optional[P]         = None
    rot_center_p:      Optional[P]         = None
    rot_center_px:     Optional[P]         = None
    rot_target_p:      Optional[P]         = None
    rot_target_px:     Optional[P]         = None
    rot_angle_initial: Optional[float]     = None
    rot_angle:         Optional[float]     = None
    # Tween Values
    span:              Tuple[float, float] = (0, 1)
    start:             float               = 0.0
    dur:               float               = 0.5
    ease:              QEasingCurve.Type   = QEasingCurve.OutQuint
    prev_phase:        Optional[str]       = None
    blend:             bool                = False

@dataclass
class GradientDef:
    name:            str
    stops:           List[GradientStop]
    phases:          Dict[str, Phase]   = field(default_factory=dict)
    p1:              P                  = field(default_factory=P)
    px1:             P                  = field(default_factory=P)
    p2:              P                  = field(default_factory=P)
    px2:             P                  = field(default_factory=P)
    radial:          bool               = False
    target:          str                = 'fill'
    phase_event:     Optional[EventDef] = None
    global_position: bool               = False

@dataclass
class GradientTween:
    stops:      Optional[List[GradientStop]] = None
    start:      float                        = 0.0
    dur:        float                        = 0.5
    ease:       QEasingCurve.Type            = QEasingCurve.OutQuint
    prev_phase: Optional[str]               = None
    span:       Tuple[float, float]          = (0, 1)
    blend:      bool                         = False

@dataclass
class TextDef:
    p:                   P                              = field(default_factory=P)
    px:                  P                              = field(default_factory=P)
    text:                str                            = 'Sample Text'
    font_size:           float                          = 10.0
    fill_color:          QColor                         = QColor(255, 255, 255, 255)
    outline_color:       Optional[QColor]               = None
    outline_width:       float                          = 0.0
    gradient:            Optional['GradientDef']        = None
    gradient_p1:         P                              = field(default_factory=P)
    gradient_px1:        P                              = field(default_factory=P)
    gradient_p2:         P                              = field(default_factory=P)
    gradient_px2:        P                              = field(default_factory=P)
    rot_center_p:        P                              = field(default_factory=P)
    rot_center_px:       P                              = field(default_factory=P)
    rot_target_p:        P                              = field(default_factory=P)
    rot_target_px:       P                              = field(default_factory=P)
    rot_angle_initial:   float                          = 0.0
    rot_angle:           float                          = 0.0
    rot_angle_fn:        Any                            = 0.0
    phases:              Optional[Dict[str, Phase]]     = None
    bold:                bool                           = False
    italic:              bool                           = False
    font_family:         str                            = 'Oxanium'
    h_align:             float                          = 0.5
    v_align:             float                          = 0.5
    uniform_scale:       bool                           = False
    text_fn:             Optional[Callable[[Any], str]] = None
    char_display:        float                          = 1.0
    sub_char_clip:       bool                           = False
    backward:            bool                           = False
    phase_override:      Optional[Any]                  = None
    pos_fn:              Optional[Callable[[], P]]      = None
    visible_threshold_x: float                          = 0.0
    visible_threshold_y: float                          = 0.0

# ──────────────────────── Tween dataclasses ──────────────────────

@dataclass
class TextTween:
    # Properties
    p:                 Optional[P]         = None
    px:                Optional[P]         = None
    fill_color:        Optional[QColor]    = None
    outline_color:     Optional[QColor]    = None
    outline_width:     Optional[float]     = None
    gradient_p1:       Optional[P]         = None
    gradient_px1:      Optional[P]         = None
    gradient_p2:       Optional[P]         = None
    gradient_px2:      Optional[P]         = None
    h_align:           Optional[float]     = None
    v_align:           Optional[float]     = None
    font_size:         Optional[float]     = None
    char_display:      Optional[float]     = None
    rot_center_p:      Optional[P]         = None
    rot_center_px:     Optional[P]         = None
    rot_target_p:      Optional[P]         = None
    rot_target_px:     Optional[P]         = None
    rot_angle_initial: Optional[float]     = None
    rot_angle:         Optional[float]     = None
    # Tween Values
    span:              Tuple[float, float] = (0, 1)
    start:             float               = 0.0
    dur:               float               = 0.5
    ease:              QEasingCurve.Type   = QEasingCurve.OutQuint
    prev_phase:        Optional[str]       = None
    blend:             bool                = False

@dataclass
class Reset:
    prev_phase: Optional[str] = None; start: float = 0

@dataclass
class Phase:
    tweens:      list
    line_delay:  float      = 0.0
    loop:        bool       = False
    stop_phases: List[str]  = field(default_factory=lambda: ['close'])
    pulse_event: Optional[Any] = None
    update_retrigger: bool  = False

def TextBlock(
    p:           P                          = P(),
    px:          P                          = P(),
    text:        str                        = 'Sample Text',
    font_size:   float                      = 10.0,
    fill_color:  QColor                     = QColor(255, 255, 255, 255),
    phases:      Optional[Dict[str, Phase]] = None,
    bold:        bool                       = False,
    italic:      bool                       = False,
    font_family: str                        = '',
    h_align:     float                      = 0.0,
    v_align:     float                      = 0.0,
    uniform_scale: bool                     = False,
    text_fn:     Optional[Callable]         = None,
    line_offset: Optional[float]            = None,
    pos_fn:      Optional[Callable[[], P]]  = None,
) -> List['TextDef']:

    lines = text.split('\n')
    n     = len(lines)

    effective_line_offset = font_size if line_offset is None else line_offset

    if n == 1:
        return [TextDef(
            p=p, px=px, text=text, font_size=font_size, fill_color=fill_color,
            phases=phases, bold=bold, italic=italic,
            font_family=font_family, h_align=h_align, v_align=v_align,
            uniform_scale=uniform_scale,
            text_fn=text_fn, pos_fn=pos_fn,
        )]

    result: List[TextDef] = []

    for i, line_text in enumerate(lines):
        line_px = P(px.x, px.y + effective_line_offset * i)
        adjusted_phases: Optional[Dict[str, Phase]] = None
        if phases:
            adjusted_phases = {}
            for phase_name, phase in phases.items():
                new_tweens = []
                for tw in phase.tweens:
                    if isinstance(tw, TextTween):
                        new_tweens.append(TextTween(
                            p          = tw.p,
                            px         = P(tw.px.x, tw.px.y + effective_line_offset * i) if tw.px is not None else None,
                            start      = tw.start,
                            dur        = tw.dur,
                            ease       = tw.ease,
                            fill_color = tw.fill_color,
                            h_align    = tw.h_align,
                            v_align    = tw.v_align,
                            font_size  = tw.font_size,
                            prev_phase = tw.prev_phase,
                            span       = tw.span,
                        ))
                    else:
                        new_tweens.append(tw)
                adjusted_phases[phase_name] = Phase(new_tweens)

        if text_fn is not None:
            def _make_line_fn(line_index: int, fallback: str):
                def _fn(ctx):
                    try:
                        full  = str(text_fn(ctx))
                        parts = full.split('\n')
                        return parts[line_index] if line_index < len(parts) else ''
                    except Exception:
                        return fallback
                return _fn
            resolved_text_fn = _make_line_fn(i, line_text)
            resolved_text    = ''
        else:
            resolved_text_fn = None
            resolved_text    = line_text

        result.append(TextDef(
            p             = p,
            px            = line_px,
            text          = resolved_text,
            font_size     = font_size,
            fill_color    = fill_color,
            phases        = adjusted_phases,
            bold          = bold,
            italic        = italic,
            font_family   = font_family,
            h_align       = h_align,
            v_align       = v_align,
            uniform_scale = uniform_scale,
            text_fn       = resolved_text_fn,
            pos_fn        = pos_fn,
        ))

    return result

def DataTable(
    x:              float,
    y:              float,
    px:             float                    = 0.0,
    py:             float                    = 0.0,
    value_x:        float                    = 0.5,
    value_px:       float                    = 0.0,
    row_height:     float                    = 18.0,
    values:         List[Tuple]              = None,
    unit_gap:       float                    = 4.0,
    fill_color:     QColor                   = None,
    font_size:      float                    = 10.0,
    font_family:    str                      = 'Oxanium',
    bold:           bool                     = False,
    italic:         bool                     = False,
    uniform_scale:  bool                     = True,
    phases:         Dict[str, Phase]         = None,
    char_display:   float                    = 1.0,
    sub_char_clip:  bool                     = False,
    backward:       bool                     = False,
    title:          str                      = '',
    title_font_size: float                   = 12.0,
) -> List[TextDef]:
    values = values or []
    n      = len(values)

    names       = []
    raw_values  = []
    value_units = []
    formats     = []
    for entry in values:
        if isinstance(entry, tuple):
            name = entry[0]
            val  = entry[1] if len(entry) > 1 else ''
            unit = entry[2] if len(entry) > 2 else ''
            fmt  = entry[3] if len(entry) > 3 else None
        else:
            raise ValueError("DataTable: each entry must be a tuple (name, value, unit='', format=None)")
        names.append(name)
        raw_values.append(val)
        value_units.append(unit)
        formats.append(fmt)

    col = fill_color or QColor(255, 255, 255, 200)
    ph  = phases or {}
    result: List[TextDef] = []

    if title:
        title_phases = {}
        for phase_name, phase in ph.items():
            delay = phase.line_delay * 0
            title_phases[phase_name] = Phase(
                [_tw_replace(tw, start=tw.start + delay) if isinstance(tw, TextTween) else tw
                 for tw in phase.tweens],
                line_delay  = 0.0,
                loop        = phase.loop,
                stop_phases = phase.stop_phases,
            )
        result.append(TextDef(
            x             = x,
            y             = y,
            px            = px,
            py            = py,
            text          = title,
            font_size     = title_font_size,
            fill_color    = QColor(col),
            phases        = title_phases,
            bold          = True,
            italic        = True,
            font_family   = font_family,
            h_align       = 0.0,
            v_align       = 1.0,
            uniform_scale = uniform_scale,
            char_display  = char_display,
            sub_char_clip = sub_char_clip,
            backward      = backward,
        ))

    title_offset = 1 if title else 0

    for i in range(n):
        row_py = py + row_height * i
        row_phases: Dict[str, Phase] = {}
        for phase_name, phase in ph.items():
            delay = phase.line_delay * (i + title_offset)
            if delay == 0.0:
                row_phases[phase_name] = phase
            else:
                row_phases[phase_name] = Phase(
                    [_tw_replace(tw, start=tw.start + delay) if isinstance(tw, TextTween) else tw
                     for tw in phase.tweens],
                    line_delay  = 0.0,
                    loop        = phase.loop,
                    stop_phases = phase.stop_phases,
                )

        common = dict(
            font_size     = font_size,
            fill_color    = QColor(col),
            phases        = row_phases,
            bold          = bold,
            italic        = italic,
            font_family   = font_family,
            uniform_scale = uniform_scale,
            char_display  = char_display,
            sub_char_clip = sub_char_clip,
            backward      = backward,
        )

        result.append(TextDef(x=x, y=y, px=px, py=row_py,
            text=names[i], h_align=0.0, v_align=0.0, **common))

        raw_value = raw_values[i]
        fmt_spec  = formats[i]
        unit      = value_units[i]

        if callable(raw_value):
            def _make_value_fn(fn, spec):
                def _fn(ctx):
                    try:    v = fn(ctx)
                    except: v = None
                    if v is None: return '-'
                    try:    return format(v, spec) if spec else str(v)
                    except: return str(v)
                return _fn
            value_text_fn = _make_value_fn(raw_value, fmt_spec)
            value_text    = ''
        else:
            value_text_fn = None
            try:    value_text = format(raw_value, fmt_spec) if fmt_spec else str(raw_value)
            except: value_text = str(raw_value)

        result.append(TextDef(x=value_x, y=y, px=value_px, py=row_py,
            text=value_text, text_fn=value_text_fn,
            h_align=1.0, v_align=0.0, **common))

        result.append(TextDef(x=value_x, y=y, px=value_px + unit_gap, py=row_py,
            text=unit, h_align=0.0, v_align=0.0, **common))

    return result

# ──────────────────────── _TweenDriver ───────────────────────────

class _TweenDriver:
    def __init__(self):
        self.hidden          = False
        self._phase: str     = ''
        self._phase_groups: Dict[str, str] = {}
        self._prev:  str     = ''
        self._idx:   int     = 0
        self._tweens: list   = []
        self._timer          = QElapsedTimer()
        self._pulse_last_value: Any  = None
        self._pulse_checked:    bool = False
        self._resolved_cache: Dict[int, tuple] = {}
        self._retrigger_snapshots: Dict[str, Any] = {}

    def _active_tweens(self, phase, prev, phases: dict) -> list:
        if phase in phases:
            p = phases[phase]
            return [tw for tw in p.tweens if tw.prev_phase is None or tw.prev_phase == prev]
        for key, p in phases.items():
            if isinstance(key, tuple) and phase in key:
                return [tw for tw in p.tweens if tw.prev_phase is None or tw.prev_phase == prev]
        return []

    @property
    def _cur(self): return self._tweens[self._idx] if self._idx < len(self._tweens) else None

    def set_phase(self, phase: str, phases: dict):
        if not phases:
            self.hidden = False
            return
        resolved_phases = {}
        phase_groups = {}
        for key, val in phases.items():
            if isinstance(key, tuple):
                canonical = key[0]
                for k in key:
                    phase_groups[k] = canonical
                    resolved_phases[canonical] = val
            else:
                phase_groups[key] = key
                resolved_phases[key] = val
        canonical     = phase_groups.get(phase, phase)
        cur_canonical = phase_groups.get(self._phase, self._phase)

        if canonical not in resolved_phases:
            return

        phase_def = resolved_phases[canonical]

        if canonical == cur_canonical and self._phase != '' and canonical != 'pulse':
            if phase_def.update_retrigger and self._retrigger_changed(canonical, phase_def):
                pass
            else:
                return

        self._prev  = self._phase
        self._phase = phase
        self._idx   = 0
        self._tweens = [tw if isinstance(tw, Reset) else _resolve_tween_event_refs(tw)
                        for tw in self._active_tweens(canonical, self._prev, resolved_phases)]
        if self._tweens or canonical in resolved_phases:
            self.hidden = False
        while self._idx < len(self._tweens) and isinstance(self._tweens[self._idx], Reset):
            self._reset_to_def()
            self._idx += 1
        self._save_start()
        self._timer.restart()
        self._update_retrigger_snapshot(canonical, phase_def)

        if phase in ('open', 'close'):
            self._pulse_checked = False

    def _is_done(self): return self._idx >= len(self._tweens)
    def phase_done(self): return self._is_done()

    def _drive(self):
        if self.hidden:
            return
        if self._idx >= len(self._tweens):
            return

        elapsed = self._timer.elapsed() / 1000.0
        tweens = self._tweens
        n = len(tweens)

        if n > 0 and elapsed < tweens[self._idx].start if not isinstance(tweens[self._idx], Reset) else False:
            return

        i = self._idx
        while i < n:
            tw = tweens[i]
            group = [tw]
            if len(group) == 1 and getattr(tw, 'span', (0,1)) == (0,1) and not getattr(tw, 'blend', False):
                if elapsed < tw.start:
                    return
                end = tw.start + tw.dur
                if elapsed <= end:
                    local = elapsed - tw.start
                    t = min(1.0, local / tw.dur) if tw.dur > 0 else 1.0
                    v = _ease(t, tw.ease)
                    self._apply(tw, v)
                    self._idx = i
                    return
                else:
                    self._snap_to(tw)
                    self._save_start()
                    self._idx = i + 1
                    i += 1
                    continue
            if isinstance(tw, Reset):
                self._reset_to_def()
                i += 1
                continue

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

            if elapsed < group_start:
                return

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
                if elapsed >= eff_start:
                    self._apply(base, v)
                for btw in group[1:]:
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

    def _save_start(self): pass
    def _snap_to(self, tw): pass
    def _reset_to_def(self): pass
    def _apply(self, tw, v): pass

    def _check_pulse(self, phases: dict) -> None:
        if not phases:
            return
        pulse_phase = None
        for key, p in phases.items():
            name = _phase_key_name(key)
            if name == 'pulse' and p.pulse_event is not None:
                pulse_phase = p
                break
        if pulse_phase is None:
            return

        if self._phase in ('close',):
            return
        if self._phase == 'open' and not self._is_done():
            return

        ev = pulse_phase.pulse_event
        if isinstance(ev, EventDef):
            cur_val = ev.value
        elif callable(ev):
            try:    cur_val = ev()
            except: return
        else:
            cur_val = ev

        if not self._pulse_checked:
            self._pulse_last_value = cur_val
            self._pulse_checked    = True
            return

        if cur_val == 'pulse' and self._pulse_last_value != 'pulse':
            self._pulse_last_value = cur_val
            self._prev  = self._phase
            self._phase = 'pulse'
            self._idx   = 0
            self._tweens = self._active_tweens('pulse', self._prev, phases)
            self._save_start()
            self._timer.restart()
        elif cur_val != 'pulse':
            self._pulse_last_value = cur_val

    def _collect_event_refs(self, phase_def):
        refs = []
        for tw in phase_def.tweens:
            if isinstance(tw, Reset):
                continue
            for attr in ('p', 'px', 'p1', 'p2', 'px1', 'px2'):
                val = getattr(tw, attr, None)
                if isinstance(val, EventDef):
                    refs.append(val)
        return refs

    def _retrigger_changed(self, canonical, phase_def) -> bool:
        refs = self._collect_event_refs(phase_def)
        if not refs:
            return False
        prev_snapshot = self._retrigger_snapshots.get(canonical)
        cur_snapshot  = tuple(list(ev.value) if isinstance(ev.value, list) else ev.value for ev in refs)
        if prev_snapshot is None:
            return False
        return cur_snapshot != prev_snapshot

    def _update_retrigger_snapshot(self, canonical, phase_def):
        refs = self._collect_event_refs(phase_def)
        if refs:
            self._retrigger_snapshots[canonical] = tuple(
                list(ev.value) if isinstance(ev.value, list) else ev.value for ev in refs
            )
        else:
            self._retrigger_snapshots.pop(canonical, None)
    
    def _collect_event_refs(self, phase_def):
        refs = []
        for tw in phase_def.tweens:
            if isinstance(tw, Reset):
                continue
            for attr in ('p', 'px', 'p1', 'p2', 'px1', 'px2'):
                val = getattr(tw, attr, None)
                if isinstance(val, EventDef):
                    refs.append(val)
                elif isinstance(val, _RectCornerRef):
                    if isinstance(val.corner1, EventDef): refs.append(val.corner1)
                    if isinstance(val.corner2, EventDef): refs.append(val.corner2)
        return refs
    
_ALWAYS_PHASE_ORIGINS: Dict[str, float] = {}

class _AlwaysDriver:
    def __init__(self, phase_name: str, phase: Phase, n_p: int) -> None:
        self._phase_name = phase_name
        self._phase      = phase
        self._n          = n_p
        self._stopped    = False
        self._started    = False
 
        self.offset_p:             List[P]          = [P(0.0, 0.0)] * n_p
        self.offset_px:            List[P]          = [P(0.0, 0.0)] * n_p
        self.offset_fill_color:    Optional[QColor] = None
        self.offset_outline_color: Optional[QColor] = None
 
        self._s_pts:     List[P]          = [P(0.0, 0.0)] * n_p
        self._s_px:      List[P]          = [P(0.0, 0.0)] * n_p
        self._s_fill:    Optional[QColor] = None
        self._s_outline: Optional[QColor] = None
 
        self._idx:      int   = 0
        self._loop_origin: float = 0.0

        self._stop_phases_set: set = set()
        for entry in self._phase.stop_phases:
            if isinstance(entry, tuple):
                self._stop_phases_set.update(entry)
            else:
                self._stop_phases_set.add(entry)
 
    def _global_origin(self) -> float:
        if self._phase_name not in _ALWAYS_PHASE_ORIGINS:
            _ALWAYS_PHASE_ORIGINS[self._phase_name] = time.monotonic()
        return _ALWAYS_PHASE_ORIGINS[self._phase_name]
 
    def _elapsed(self) -> float:
        return time.monotonic() - self._loop_origin
 
    def _reset(self) -> None:
        self._stopped = False
        self._idx     = 0
        self.offset_p             = [P(0.0, 0.0)] * self._n
        self.offset_px            = [P(0.0, 0.0)] * self._n
        self.offset_fill_color    = None
        self.offset_outline_color = None
        self._s_pts     = [P(0.0, 0.0)] * self._n
        self._s_px      = [P(0.0, 0.0)] * self._n
        self._s_fill    = None
        self._s_outline = None
        origin  = self._global_origin()
        now     = time.monotonic()
        elapsed = now - origin
 
        if self._phase.loop:
            loop_dur = self._total_loop_dur()
            if loop_dur > 0.0:
                phase_in_loop = elapsed % loop_dur
                self._loop_origin = now - phase_in_loop
                self._fast_forward(phase_in_loop)
            else:
                self._loop_origin = now
        else:
            self._loop_origin = origin
        self._started = True
 
    def _total_loop_dur(self) -> float:
        total = 0.0
        for tw in self._phase.tweens:
            if isinstance(tw, (PolygonTween, TextTween)):
                total = max(total, tw.start + tw.dur)
        return total
 
    def _fast_forward(self, target_elapsed: float) -> None:
        tweens = self._phase.tweens
        n      = len(tweens)
        i      = 0
        while i < n:
            tw = tweens[i]
            if isinstance(tw, Reset):
                self._do_reset_offsets()
                i += 1
                continue
            if not isinstance(tw, (PolygonTween, TextTween)):
                i += 1
                continue
            end = tw.start + tw.dur
            if target_elapsed >= end:
                self._snap_tw(tw)
                self._save_start()
                i += 1
            else:
                self._idx = i
                return
        self._idx = n
 
    def _do_reset_offsets(self) -> None:
        self.offset_p             = [P(0.0, 0.0)] * self._n
        self.offset_px            = [P(0.0, 0.0)] * self._n
        self.offset_fill_color    = None
        self.offset_outline_color = None
        self._s_pts     = [P(0.0, 0.0)] * self._n
        self._s_px      = [P(0.0, 0.0)] * self._n
        self._s_fill    = None
        self._s_outline = None
 
    def _snap_tw(self, tw) -> None:
        if isinstance(tw, PolygonTween):
            if tw.p             is not None: self.offset_p = [P(p.x, p.y) for p in tw.p]
            if tw.px            is not None: self.offset_px = [P(p.x, p.y) for p in tw.px]
            if tw.fill_color    is not None: self.offset_fill_color    = QColor(tw.fill_color)
            if tw.outline_color is not None: self.offset_outline_color = QColor(tw.outline_color)
        elif isinstance(tw, TextTween):
            if tw.x          is not None: self.offset_p = [P(tw.x, self.offset_p[0].y)]
            if tw.y          is not None: self.offset_p = [P(self.offset_p[0].x, tw.y)]
            if tw.px         is not None: self.offset_px = [P(tw.px, self.offset_px[0].y)]
            if tw.py         is not None: self.offset_px = [P(self.offset_px[0].x, tw.py)]
            if tw.fill_color is not None: self.offset_fill_color = QColor(tw.fill_color)
 
    def _save_start(self) -> None:
        self._s_pts     = [P(p.x, p.y) for p in self.offset_p]
        self._s_px      = [P(p.x, p.y) for p in self.offset_px]
        self._s_fill    = QColor(self.offset_fill_color) if self.offset_fill_color    else None
        self._s_outline = QColor(self.offset_outline_color) if self.offset_outline_color else None
 
    def notify_phase(self, phase_name: str, base_phase_done: bool) -> None:
        in_stop = phase_name in self._stop_phases_set
        if in_stop and base_phase_done:
            if not self._stopped:
                self._stopped = True
                self._do_reset_offsets()
        elif not in_stop and not self._started:
            self._reset()
        elif not in_stop and self._stopped:
            self._stopped = False
            self._reset()
 
    def update(self, base_phase_name: str, base_phase_done: bool) -> None:
        if not self._started:
            self._reset()
 
        if base_phase_done and base_phase_name in self._phase.stop_phases:
            if not self._stopped:
                self._stopped = True
                self._do_reset_offsets()
            return
 
        if self._stopped:
            return
 
        elapsed = self._elapsed()
        tweens  = self._phase.tweens
        n       = len(tweens)
        i       = self._idx
 
        while i < n:
            tw = tweens[i]
 
            if isinstance(tw, Reset):
                self._do_reset_offsets()
                self._save_start()
                i += 1
                continue
 
            if not isinstance(tw, (PolygonTween, TextTween)):
                i += 1
                continue
 
            if elapsed < tw.start:
                self._idx = i
                return
 
            end = tw.start + tw.dur
            if elapsed <= end:
                local = elapsed - tw.start
                t = min(1.0, max(0.0, local / tw.dur)) if tw.dur > 0 else 1.0
                v = _ease(t, tw.ease)
                self._apply_tw(tw, v)
                self._idx = i
                return
            else:
                self._snap_tw(tw)
                self._save_start()
                i += 1
 
        self._idx = n
        if self._phase.loop:
            loop_dur = self._total_loop_dur()
            if loop_dur > 0.0:
                self._loop_origin += loop_dur
            self._idx = 0
            self._do_reset_offsets()
            self._s_pts = [P(0.0, 0.0)] * self._n
            self._s_px = [P(0.0, 0.0)] * self._n
            self._s_fill = None
            self._s_outline = None
 
    def _apply_tw(self, tw, v: float) -> None:
        if isinstance(tw, PolygonTween):
            if tw.p is not None:
                for j, (sp, tp) in enumerate(zip(self._s_pts, tw.p)):
                    self.offset_p[j] = P(sp.x + (tp.x - sp.x) * v, sp.y + (tp.y - sp.y) * v)
            if tw.px is not None:
                for j, (sp, tp) in enumerate(zip(self._s_px, tw.px)):
                    self.offset_px[j] = P(sp.x + (tp.x - sp.x) * v, sp.y + (tp.y - sp.y) * v)
            if tw.fill_color is not None:
                src = self._s_fill or QColor(0, 0, 0, 0)
                self.offset_fill_color = lerp_color(src, tw.fill_color, v)
            if tw.outline_color is not None:
                src = self._s_outline or QColor(0, 0, 0, 0)
                self.offset_outline_color = lerp_color(src, tw.outline_color, v)
 
        elif isinstance(tw, TextTween):
            spx = self._s_px[0].x if self._s_px else 0.0
            spy = self._s_px[0].y if self._s_px else 0.0

            sp_x = self._s_pts[0].x if self._s_pts else 0.0
            sp_y = self._s_pts[0].y if self._s_pts else 0.0
            tp_x = tw.x if tw.x is not None else sp_x
            tp_y = tw.y if tw.y is not None else sp_y
            tpx  = tw.px if tw.px is not None else spx
            tpy  = tw.py if tw.py is not None else spy

            new_x  = sp_x + (tp_x - sp_x) * v
            new_y  = sp_y + (tp_y - sp_y) * v
            new_px = spx  + (tpx  - spx)  * v
            new_py = spy  + (tpy  - spy)   * v

            if tw.x  is not None: self.offset_p  = [P(new_x, self.offset_p[0].y)]
            if tw.y  is not None: self.offset_p  = [P(self.offset_p[0].x, new_y)]
            if tw.px is not None: self.offset_px = [P(new_px, self.offset_px[0].y)]
            if tw.py is not None: self.offset_px = [P(self.offset_px[0].x, new_py)]

            if tw.fill_color is not None:
                src = self._s_fill or QColor(0, 0, 0, 0)
                self.offset_fill_color = lerp_color(src, tw.fill_color, v)

 

class _AnimatedGradient(_TweenDriver):
    def __init__(self, defn: GradientDef) -> None:
        super().__init__()
        self.defn      = defn
        self.cur_stops = [GradientStop(s.position, QColor(s.color)) for s in defn.stops]
        self._s_stops  = [GradientStop(s.position, QColor(s.color)) for s in defn.stops]
        self._cur_phase: str = ''

    def _save_start(self) -> None:
        self._s_stops = [GradientStop(s.position, QColor(s.color)) for s in self.cur_stops]
 
    def _reset_to_def(self) -> None:
        self.cur_stops = [GradientStop(s.position, QColor(s.color)) for s in self.defn.stops]
 
    def _snap_to(self, tw: GradientTween) -> None:
        if tw.stops is None or len(tw.stops) != len(self.cur_stops):
            return
        self.cur_stops = [GradientStop(s.position, QColor(s.color)) for s in tw.stops]
 
    def _apply(self, tw: GradientTween, v: float) -> None:
        if tw.stops is None or len(tw.stops) != len(self.cur_stops):
            return
        for i, (src, tgt) in enumerate(zip(self._s_stops, tw.stops)):
            new_pos   = src.position + (tgt.position - src.position) * v
            new_color = lerp_color(src.color, tgt.color, v)
            self.cur_stops[i] = GradientStop(new_pos, new_color)
 
    def _apply_blend(self, tw: GradientTween, v: float) -> None:
        if tw.stops is None or len(tw.stops) != len(self.cur_stops):
            return
        for i, tgt in enumerate(tw.stops):
            cur = self.cur_stops[i]
            new_pos   = cur.position + tgt.position * v
            new_color = lerp_color(cur.color, tgt.color, v)
            self.cur_stops[i] = GradientStop(new_pos, new_color)
 
    def set_phase(self, phase: str) -> None:
        super().set_phase(phase, self.defn.phases)
 
    def _poll_phase_event(self) -> None:
        ev = self.defn.phase_event
        if ev is None:
            return
        val = str(ev.value) if ev.value is not None else ''
        if not val or val == self._cur_phase:
            return
        if val == 'ignore':
            return
        if val == 'pulse':
            if 'pulse' in self.defn.phases:
                pass
            return
        self._cur_phase = val
        self.set_phase(val)

    def update(self) -> None:
        self._poll_phase_event()
        self._drive()
        self._check_pulse(self.defn.phases)
 
    def build_gradient(self, x1: float, y1: float, x2: float, y2: float, radial: bool = False):
        if radial:
            cx, cy   = x1, y1
            ex, ey   = x2, y2
            radius   = _math.sqrt((ex - cx) ** 2 + (ey - cy) ** 2)
            g = QRadialGradient(cx, cy, radius)
            g.setSpread(QRadialGradient.PadSpread)
        else:
            g = QLinearGradient(x1, y1, x2, y2)
            g.setSpread(QLinearGradient.PadSpread)
        for stop in self.cur_stops:
            g.setColorAt(max(0.0, min(1.0, stop.position)), stop.color)
        return g

# ──────────────────────── AnimatedPolygon ────────────────────────
class AnimatedPolygon(_TweenDriver):
    def __init__(self, defn: PolygonDef):
        super().__init__()
        self.defn = defn
        n = len(defn.p)
        _zero_px = [P() for _ in range(n)]

        self._screen_offset = P(0.0, 0.0)
        self.cur_p            = [P(p.x, p.y) for p in defn.p]
        self.cur_px           = [P(p.x, p.y) for p in (defn.px or _zero_px)]
        self.cur_fill_color   = QColor(defn.fill_color)   if defn.fill_color   else QColor(0,0,0,0)
        self.cur_outline_color= QColor(defn.outline_color)if defn.outline_color else QColor(0,0,0,0)
        self.cur_line_width   = defn.outline_width
        self.cur_draw_progress= defn.draw_progress
        self.cur_gradient_p1  = P(defn.gradient_p1.x,  defn.gradient_p1.y)
        self.cur_gradient_px1 = P(defn.gradient_px1.x, defn.gradient_px1.y)
        self.cur_gradient_p2  = P(defn.gradient_p2.x,  defn.gradient_p2.y)
        self.cur_gradient_px2 = P(defn.gradient_px2.x, defn.gradient_px2.y)

        self._sp  = [P(p.x, p.y) for p in self.cur_p]
        self._spx = [P(p.x, p.y) for p in self.cur_px]
        self._sf  = QColor(self.cur_fill_color)
        self._so  = QColor(self.cur_outline_color)
        self._slw = self.cur_line_width
        self._sdp = self.cur_draw_progress
        self._sgp1  = P(defn.gradient_p1.x,  defn.gradient_p1.y)
        self._sgpx1 = P(defn.gradient_px1.x, defn.gradient_px1.y)
        self._sgp2  = P(defn.gradient_p2.x,  defn.gradient_p2.y)
        self._sgpx2 = P(defn.gradient_px2.x, defn.gradient_px2.y)

        self.cur_rot_center_p:      P     = P(defn.rot_center_p.x,  defn.rot_center_p.y)
        self.cur_rot_center_px:     P     = P(defn.rot_center_px.x, defn.rot_center_px.y)
        self.cur_rot_target_p:      P     = P(defn.rot_target_p.x,  defn.rot_target_p.y)
        self.cur_rot_target_px:     P     = P(defn.rot_target_px.x, defn.rot_target_px.y)
        self.cur_rot_angle_initial: float = defn.rot_angle_initial
        self.cur_rot_angle:         float = defn.rot_angle

        self._s_rot_center_p:      P     = P(defn.rot_center_p.x,  defn.rot_center_p.y)
        self._s_rot_center_px:     P     = P(defn.rot_center_px.x, defn.rot_center_px.y)
        self._s_rot_target_p:      P     = P(defn.rot_target_p.x,  defn.rot_target_p.y)
        self._s_rot_target_px:     P     = P(defn.rot_target_px.x, defn.rot_target_px.y)
        self._s_rot_angle_initial: float = defn.rot_angle_initial
        self._s_rot_angle:         float = defn.rot_angle

        self._dirty      = True
        self._cached_poly= QPolygonF()
        self._cached_w   = 0
        self._cached_h   = 0
        self._always_drivers: Dict[str, _AlwaysDriver] = {
            name: _AlwaysDriver(name, phase, len(defn.p))
            for name, phase in (defn.phases or {}).items()
            if _phase_key_name(name).startswith('always')
        }
        self._always_offset_p:      List[P] = [P(0.0, 0.0)] * len(defn.p)
        self._always_offset_px:     List[P] = [P(0.0, 0.0)] * len(defn.p)
        self._always_fill_color:    Optional[QColor] = None
        self._always_outline_color: Optional[QColor] = None
        
        self._dynamic_px_w: int = 0
        self._dynamic_px_h: int = 0
        self._pos_offset: List[P] = [P(0.0, 0.0)] * len(defn.p)

        self._cur_phase = ''


    # ── _TweenDriver hooks ───────────────────────────────────────

    def _save_start(self):
        self._sp  = [P(p.x, p.y) for p in self.cur_p]
        self._spx = [P(p.x, p.y) for p in self.cur_px]
        self._sf  = QColor(self.cur_fill_color)
        self._so  = QColor(self.cur_outline_color)
        self._slw = self.cur_line_width
        self._sdp = self.cur_draw_progress
        self._sgp1  = P(self.cur_gradient_p1.x,  self.cur_gradient_p1.y)
        self._sgpx1 = P(self.cur_gradient_px1.x, self.cur_gradient_px1.y)
        self._sgp2  = P(self.cur_gradient_p2.x,  self.cur_gradient_p2.y)
        self._sgpx2 = P(self.cur_gradient_px2.x, self.cur_gradient_px2.y)
        self._s_rot_center_p      = P(self.cur_rot_center_p.x,  self.cur_rot_center_p.y)
        self._s_rot_center_px     = P(self.cur_rot_center_px.x, self.cur_rot_center_px.y)
        self._s_rot_target_p      = P(self.cur_rot_target_p.x,  self.cur_rot_target_p.y)
        self._s_rot_target_px     = P(self.cur_rot_target_px.x, self.cur_rot_target_px.y)
        self._s_rot_angle_initial = self.cur_rot_angle_initial
        self._s_rot_angle         = self.cur_rot_angle

    def _apply(self, tw: PolygonTween, v: float):
        if tw.p is not None:
            for i, (sp, tp) in enumerate(zip(self._sp, tw.p)):
                nx = sp.x + (tp.x - sp.x) * v if tp.x is not None else sp.x
                ny = sp.y + (tp.y - sp.y) * v if tp.y is not None else sp.y
                self.cur_p[i] = P(nx, ny)
        if tw.px is not None:
            for i, (spx, tpx) in enumerate(zip(self._spx, tw.px)):
                nx = spx.x + (tpx.x - spx.x) * v if tpx.x is not None else spx.x
                ny = spx.y + (tpx.y - spx.y) * v if tpx.y is not None else spx.y
                self.cur_px[i] = P(nx, ny)
        if tw.fill_color    is not None: self.cur_fill_color    = lerp_color(self._sf, tw.fill_color,    v)
        if tw.outline_color is not None: self.cur_outline_color = lerp_color(self._so, tw.outline_color, v)
        if tw.outline_width    is not None: self.cur_line_width    = self._slw + (tw.outline_width - self._slw) * v
        if tw.draw_progress is not None: self.cur_draw_progress = self._sdp + (tw.draw_progress - self._sdp) * v
        if tw.gradient_p1   is not None: self.cur_gradient_p1   = P(self._sgp1.x  + (tw.gradient_p1.x  - self._sgp1.x)  * v, self._sgp1.y  + (tw.gradient_p1.y  - self._sgp1.y)  * v)
        if tw.gradient_px1  is not None: self.cur_gradient_px1  = P(self._sgpx1.x + (tw.gradient_px1.x - self._sgpx1.x) * v, self._sgpx1.y + (tw.gradient_px1.y - self._sgpx1.y) * v)
        if tw.gradient_p2   is not None: self.cur_gradient_p2   = P(self._sgp2.x  + (tw.gradient_p2.x  - self._sgp2.x)  * v, self._sgp2.y  + (tw.gradient_p2.y  - self._sgp2.y)  * v)
        if tw.gradient_px2  is not None: self.cur_gradient_px2  = P(self._sgpx2.x + (tw.gradient_px2.x - self._sgpx2.x) * v, self._sgpx2.y + (tw.gradient_px2.y - self._sgpx2.y) * v)
        if tw.rot_center_p      is not None: self.cur_rot_center_p      = P(self._s_rot_center_p.x  + (tw.rot_center_p.x  - self._s_rot_center_p.x)  * v, self._s_rot_center_p.y  + (tw.rot_center_p.y  - self._s_rot_center_p.y)  * v)
        if tw.rot_center_px     is not None: self.cur_rot_center_px     = P(self._s_rot_center_px.x + (tw.rot_center_px.x - self._s_rot_center_px.x) * v, self._s_rot_center_px.y + (tw.rot_center_px.y - self._s_rot_center_px.y) * v)
        if tw.rot_target_p      is not None: self.cur_rot_target_p      = P(self._s_rot_target_p.x  + (tw.rot_target_p.x  - self._s_rot_target_p.x)  * v, self._s_rot_target_p.y  + (tw.rot_target_p.y  - self._s_rot_target_p.y)  * v)
        if tw.rot_target_px     is not None: self.cur_rot_target_px     = P(self._s_rot_target_px.x + (tw.rot_target_px.x - self._s_rot_target_px.x) * v, self._s_rot_target_px.y + (tw.rot_target_px.y - self._s_rot_target_px.y) * v)
        if tw.rot_angle_initial is not None: self.cur_rot_angle_initial = self._s_rot_angle_initial + (tw.rot_angle_initial - self._s_rot_angle_initial) * v
        if tw.rot_angle         is not None: self.cur_rot_angle         = self._s_rot_angle         + (tw.rot_angle         - self._s_rot_angle)         * v
        self._dirty = True

    def _apply_blend(self, tw: PolygonTween, v: float):
        if tw.p is not None:
            for i, tp in enumerate(tw.p):
                cp = self.cur_p[i]
                self.cur_p[i] = P(cp.x + tp.x * v, cp.y + tp.y * v)
        if tw.px is not None:
            for i, tpx in enumerate(tw.px):
                cpx = self.cur_px[i]
                self.cur_px[i] = P(cpx.x + tpx.x * v, cpx.y + tpx.y * v)
        if tw.fill_color    is not None: self.cur_fill_color    = lerp_color(self.cur_fill_color,    tw.fill_color,    v)
        if tw.outline_color is not None: self.cur_outline_color = lerp_color(self.cur_outline_color, tw.outline_color, v)
        if tw.outline_width    is not None: self.cur_line_width    = self.cur_line_width + (tw.outline_width - self.cur_line_width) * v
        if tw.draw_progress is not None: self.cur_draw_progress = self.cur_draw_progress + (tw.draw_progress - self.cur_draw_progress) * v
        self._dirty = True

    def _snap_to(self, tw: PolygonTween):
        if tw.p             is not None: self.cur_p             = [P(tp.x if tp.x is not None else cp.x, tp.y if tp.y is not None else cp.y) for cp, tp in zip(self.cur_p, tw.p)]
        if tw.px            is not None: self.cur_px            = [P(tpx.x if tpx.x is not None else cpx.x, tpx.y if tpx.y is not None else cpx.y) for cpx, tpx in zip(self.cur_px, tw.px)]
        if tw.fill_color    is not None: self.cur_fill_color    = QColor(tw.fill_color)
        if tw.outline_color is not None: self.cur_outline_color = QColor(tw.outline_color)
        if tw.outline_width    is not None: self.cur_line_width    = tw.outline_width
        if tw.draw_progress is not None: self.cur_draw_progress = tw.draw_progress
        if tw.gradient_p1   is not None: self.cur_gradient_p1   = tw.gradient_p1
        if tw.gradient_px1  is not None: self.cur_gradient_px1  = tw.gradient_px1
        if tw.gradient_p2   is not None: self.cur_gradient_p2   = tw.gradient_p2
        if tw.gradient_px2  is not None: self.cur_gradient_px2  = tw.gradient_px2
        if tw.rot_center_p      is not None: self.cur_rot_center_p      = tw.rot_center_p
        if tw.rot_center_px     is not None: self.cur_rot_center_px     = tw.rot_center_px
        if tw.rot_target_p      is not None: self.cur_rot_target_p      = tw.rot_target_p
        if tw.rot_target_px     is not None: self.cur_rot_target_px     = tw.rot_target_px
        if tw.rot_angle_initial is not None: self.cur_rot_angle_initial = tw.rot_angle_initial
        if tw.rot_angle         is not None: self.cur_rot_angle         = tw.rot_angle
        self._dirty = True

    def _reset_to_def(self):
        d = self.defn
        n = len(d.p)
        self.cur_p             = [P(p.x, p.y) for p in d.p]
        self.cur_px            = [P(p.x, p.y) for p in (d.px or [P()]*n)]
        self.cur_fill_color    = QColor(d.fill_color)    if d.fill_color    else QColor(0,0,0,0)
        self.cur_outline_color = QColor(d.outline_color) if d.outline_color else QColor(0,0,0,0)
        self.cur_line_width    = d.outline_width
        self.cur_draw_progress = d.draw_progress
        self.cur_gradient_p1  = P(d.gradient_p1.x,  d.gradient_p1.y)
        self.cur_gradient_px1 = P(d.gradient_px1.x, d.gradient_px1.y)
        self.cur_gradient_p2  = P(d.gradient_p2.x,  d.gradient_p2.y)
        self.cur_gradient_px2 = P(d.gradient_px2.x, d.gradient_px2.y)
        self.cur_rot_center_p      = P(d.rot_center_p.x,  d.rot_center_p.y)
        self.cur_rot_center_px     = P(d.rot_center_px.x, d.rot_center_px.y)
        self.cur_rot_target_p      = P(d.rot_target_p.x,  d.rot_target_p.y)
        self.cur_rot_target_px     = P(d.rot_target_px.x, d.rot_target_px.y)
        self.cur_rot_angle_initial = d.rot_angle_initial
        self.cur_rot_angle         = d.rot_angle
        self._dirty = True

    def set_phase(self, phase: str):
        super().set_phase(phase, self.defn.phases)
        self._dirty = True
        for driver in self._always_drivers.values():
            driver.notify_phase(phase, False)

    def update(self) -> None:
        pos_fn = self.defn.pos_fn
        if pos_fn is not None:
            try:
                result = pos_fn()
                if result is not None:
                    n = len(self.defn.p)
                    if isinstance(result, P):
                        self._pos_offset = [result] * n
                    else:
                        self._pos_offset = result
                    self._dirty = True
            except Exception as e:
                print(f'[pos_fn error] {e}')
        self._drive()
        self._check_pulse(self.defn.phases or {})

        n = len(self.defn.p)
        sum_pts = [P(0.0, 0.0)] * n
        sum_px  = [P(0.0, 0.0)] * n
        fill_override    = None
        outline_override = None
 
        base_done = self.phase_done()
 
        for driver in self._always_drivers.values():
            driver.update(self._phase, base_done)
 
            for j in range(n):
                op = driver.offset_p[j]
                ox = driver.offset_px[j]
                sum_pts[j] = P(sum_pts[j].x + op.x, sum_pts[j].y + op.y)
                sum_px[j]  = P(sum_px[j].x  + ox.x, sum_px[j].y  + ox.y)
 
            if driver.offset_fill_color is not None:
                fill_override = driver.offset_fill_color
            if driver.offset_outline_color is not None:
                outline_override = driver.offset_outline_color
 
        self._always_offset_p      = sum_pts
        self._always_offset_px     = sum_px
        self._always_fill_color    = fill_override
        self._always_outline_color = outline_override
 
        if any(p.x != 0 or p.y != 0 for p in sum_pts + sum_px):
            self._dirty = True
        
        if self.defn.export_p is not None:
            self.defn.export_p.value = [P(p.x, p.y) for p in self.cur_p]
        if self.defn.export_px is not None:
            self.defn.export_px.value = [P(p.x, p.y) for p in self.cur_px]

    def phase_done(self) -> bool:
        if not self._is_done():
            return False
        if self._phase == 'close':
            for driver in self._always_drivers.values():
                if not driver._stopped:
                    return False
        return True

    # ── Geometry ─────────────────────────────────────────────────

    def _to_screen_pts(self, w: int, h: int, cam_w=MONITOR_RESOLUTIONS[0][0], cam_h=MONITOR_RESOLUTIONS[0][1]) -> List[QPointF]:
        pts = []
        for p, px in zip(self.cur_p, self.cur_px):
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

    def get_polygon(self, widget_w: int, widget_h: int, cam_w: int = MONITOR_RESOLUTIONS[0][0], cam_h: int = MONITOR_RESOLUTIONS[0][1]) -> QPolygonF:
        dynamic_px = self.defn.dynamic_px
        if dynamic_px is not None:
            if widget_w != self._dynamic_px_w or widget_h != self._dynamic_px_h:
                self.cur_px        = dynamic_px(widget_w, widget_h)
                self._spx          = list(self.cur_px)
                self._dynamic_px_w = widget_w
                self._dynamic_px_h = widget_h
                self._dirty        = True

        always_pts = self._always_offset_p
        always_px  = self._always_offset_px
        pos        = self._pos_offset
        has_always = False
        for p in always_pts:
            if p.x or p.y:
                has_always = True
                break
        if not has_always:
            for p in always_px:
                if p.x or p.y:
                    has_always = True
                    break
        has_pos = False
        for p in pos:
            if p.x or p.y:
                has_pos = True
                break

        if not self._dirty and self._cached_w == widget_w and self._cached_h == widget_h:
            if not has_always and not has_pos:
                return self._cached_poly
            pts = []
            if self.defn.uniform_scale:
                s  = min(widget_w / cam_w, widget_h / cam_h)
                cx = s / (widget_w / cam_w)
                cy = s / (widget_h / cam_h)
                for j, qp in enumerate(self._cached_poly):
                    ap  = always_pts[j]
                    apx = always_px[j]
                    po  = pos[j]
                    pts.append(QPointF(qp.x() + ap.x * cx * widget_w + apx.x + po.x,
                                       qp.y() + ap.y * cy * widget_h + apx.y + po.y))
            else:
                for j, qp in enumerate(self._cached_poly):
                    ap  = always_pts[j]
                    apx = always_px[j]
                    po  = pos[j]
                    pts.append(QPointF(qp.x() + ap.x * widget_w + apx.x + po.x,
                                       qp.y() + ap.y * widget_h + apx.y + po.y))
            return QPolygonF(pts)

        pts      = []
        base_pts = []
        if self.defn.uniform_scale:
            s  = min(widget_w / cam_w, widget_h / cam_h)
            cx = s / (widget_w / cam_w)
            cy = s / (widget_h / cam_h)
            for j, (p, px) in enumerate(zip(self.cur_p, self.cur_px)):
                ap  = always_pts[j]
                apx = always_px[j]
                po  = pos[j]
                bx  = (0.5 + (p.x - 0.5) * cx) * widget_w + px.x
                by  = (0.5 + (p.y - 0.5) * cy) * widget_h + px.y
                pts.append(QPointF(bx + po.x + ap.x * cx * widget_w + apx.x,
                                by + po.y + ap.y * cy * widget_h + apx.y))
                base_pts.append(QPointF(bx, by))
        else:
            for j, (p, px) in enumerate(zip(self.cur_p, self.cur_px)):
                ap  = always_pts[j]
                apx = always_px[j]
                po  = pos[j]
                bx  = p.x * widget_w + px.x
                by  = p.y * widget_h + px.y
                pts.append(QPointF(bx + po.x + ap.x * widget_w + apx.x,
                                by + po.y + ap.y * widget_h + apx.y))
                base_pts.append(QPointF(bx, by))

        self._cached_poly = QPolygonF(base_pts)
        self._cached_w    = widget_w
        self._cached_h    = widget_h
        self._dirty       = False
        return QPolygonF(pts)

    # ── Draw ─────────────────────────────────────────────────────
    
    def draw(self, painter: QPainter, w: int, h: int, cam_w: int = MONITOR_RESOLUTIONS[0][0], cam_h: int = MONITOR_RESOLUTIONS[0][1]):
        if self.hidden:
            return

        effective_fill    = self._always_fill_color    if self._always_fill_color    is not None else self.cur_fill_color
        effective_outline = self._always_outline_color if self._always_outline_color is not None else self.cur_outline_color
        lw         = self.cur_line_width
        gd = self.defn.gradient
        has_image   = self.defn.closed and self.defn.image_path is not None
        has_fill    = self.defn.closed and (effective_fill.alpha() > 0 or (gd is not None and gd.target == 'fill') or has_image)
        has_gradient_outline = gd is not None and gd.target == 'outline'
        has_outline = lw > 0 and (effective_outline.alpha() > 0 or has_gradient_outline)
        is_open     = not self.defn.closed

        if not has_fill and not has_outline:
            return

        angle_offset = _resolve_angle_value(self.defn.rot_angle_fn)
        rot = _resolve_rotation(
            self.cur_rot_center_p, self.cur_rot_center_px,
            self.cur_rot_target_p, self.cur_rot_target_px,
            self.cur_rot_angle_initial, self.cur_rot_angle + angle_offset,
            w, h
        )
        if rot is not None:
            cx, cy, angle = rot
            painter.save()
            painter.translate(cx, cy)
            painter.rotate(angle)
            painter.translate(-cx, -cy)

        def _outline_brush():
            gd = self.defn.gradient
            if gd is None or gd.target != 'outline':
                return None

            def _has_point(p, px):
                return p.x != 0 or p.y != 0 or px.x != 0 or px.y != 0

            if gd.global_position:
                gw, gh = get_true_screen_size()
                off = _current_window_screen_offset
                if _has_point(self.cur_gradient_p1, self.cur_gradient_px1) or _has_point(self.cur_gradient_p2, self.cur_gradient_px2):
                    x1 = self.cur_gradient_p1.x * gw + self.cur_gradient_px1.x - off.x
                    y1 = self.cur_gradient_p1.y * gh + self.cur_gradient_px1.y - off.y
                    x2 = self.cur_gradient_p2.x * gw + self.cur_gradient_px2.x - off.x
                    y2 = self.cur_gradient_p2.y * gh + self.cur_gradient_px2.y - off.y
                else:
                    x1 = gd.p1.x * gw + gd.px1.x - off.x
                    y1 = gd.p1.y * gh + gd.px1.y - off.y
                    x2 = gd.p2.x * gw + gd.px2.x - off.x
                    y2 = gd.p2.y * gh + gd.px2.y - off.y
                return gd._animated.build_gradient(x1, y1, x2, y2, radial=gd.radial)

            if _has_point(self.cur_gradient_p1, self.cur_gradient_px1) or _has_point(self.cur_gradient_p2, self.cur_gradient_px2):
                x1 = self.cur_gradient_p1.x * w + self.cur_gradient_px1.x
                y1 = self.cur_gradient_p1.y * h + self.cur_gradient_px1.y
                x2 = self.cur_gradient_p2.x * w + self.cur_gradient_px2.x
                y2 = self.cur_gradient_p2.y * h + self.cur_gradient_px2.y
            else:
                x1 = gd.p1.x * w + gd.px1.x
                y1 = gd.p1.y * h + gd.px1.y
                x2 = gd.p2.x * w + gd.px2.x
                y2 = gd.p2.y * h + gd.px2.y
            return gd._animated.build_gradient(x1, y1, x2, y2, radial=gd.radial)

        pts = list(self.get_polygon(w, h, cam_w, cam_h))

        # dedupe consecutive duplicate points — prevents zero-length segments
        # from reaching Qt's gradient-brushed stroker, which can crash under GL
        if len(pts) >= 2:
            deduped = [pts[0]]
            for pt in pts[1:]:
                prev = deduped[-1]
                if abs(pt.x() - prev.x()) > 1e-6 or abs(pt.y() - prev.y()) > 1e-6:
                    deduped.append(pt)
            pts = deduped

        if is_open:
            if not has_outline or len(pts) < 2:
                if rot is not None: painter.restore()
                return
            gradient_outline = _outline_brush()
            if gradient_outline is not None:
                pen = QPen(QBrush(gradient_outline), lw)
            else:
                pen = QPen(effective_outline)
                pen.setWidthF(lw)
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            _draw_partial_polyline(painter, pts, self.cur_draw_progress)
            painter.setPen(Qt.NoPen)
            if rot is not None: painter.restore()
            return

        def _fill_brush():
            fill = (self._always_fill_color if self._always_fill_color is not None else self.cur_fill_color)
            gd = self.defn.gradient
            if gd is None:
                return fill

            if gd.global_position:
                gw, gh = get_true_screen_size()
                off = _current_window_screen_offset
                def _has_point(p, px):
                    return p.x != 0 or p.y != 0 or px.x != 0 or px.y != 0
                if _has_point(self.cur_gradient_p1, self.cur_gradient_px1) or _has_point(self.cur_gradient_p2, self.cur_gradient_px2):
                    x1 = self.cur_gradient_p1.x * gw + self.cur_gradient_px1.x - off.x
                    y1 = self.cur_gradient_p1.y * gh + self.cur_gradient_px1.y - off.y
                    x2 = self.cur_gradient_p2.x * gw + self.cur_gradient_px2.x - off.x
                    y2 = self.cur_gradient_p2.y * gh + self.cur_gradient_px2.y - off.y
                else:
                    x1 = gd.p1.x * gw + gd.px1.x - off.x
                    y1 = gd.p1.y * gh + gd.px1.y - off.y
                    x2 = gd.p2.x * gw + gd.px2.x - off.x
                    y2 = gd.p2.y * gh + gd.px2.y - off.y
                return gd._animated.build_gradient(x1, y1, x2, y2, radial=gd.radial)

            def _has_point(p, px):
                return p.x != 0 or p.y != 0 or px.x != 0 or px.y != 0
            if _has_point(self.cur_gradient_p1, self.cur_gradient_px1) or _has_point(self.cur_gradient_p2, self.cur_gradient_px2):
                x1 = self.cur_gradient_p1.x  * w + self.cur_gradient_px1.x
                y1 = self.cur_gradient_p1.y  * h + self.cur_gradient_px1.y
                x2 = self.cur_gradient_p2.x  * w + self.cur_gradient_px2.x
                y2 = self.cur_gradient_p2.y  * h + self.cur_gradient_px2.y
            else:
                x1 = gd.p1.x  * w + gd.px1.x
                y1 = gd.p1.y  * h + gd.px1.y
                x2 = gd.p2.x  * w + gd.px2.x
                y2 = gd.p2.y  * h + gd.px2.y
            return gd._animated.build_gradient(x1, y1, x2, y2, radial=gd.radial)

        gradient_outline = _outline_brush()
        poly = QPolygonF(pts)
        pixmap = _get_pixmap(self.defn.image_path) if has_image else None

        def _paint_image():
            painter.save()
            path = QPainterPath()
            path.addPolygon(poly)
            painter.setClipPath(path, Qt.IntersectClip)
            rect = poly.boundingRect()
            if self.defn.image_opacity < 1.0:
                painter.setOpacity(self.defn.image_opacity)
            painter.drawPixmap(rect, pixmap, QRectF(pixmap.rect()))
            painter.restore()

        def _stroke_outline():
            if gradient_outline is not None:
                pen = QPen(QBrush(gradient_outline), lw)
            else:
                pen = QPen(effective_outline)
                pen.setWidthF(lw)
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPolygon(poly)
            painter.setPen(Qt.NoPen)

        if has_fill and not has_outline:
            if pixmap is not None:
                _paint_image()
            else:
                painter.setPen(Qt.NoPen)
                painter.setBrush(_fill_brush())
                painter.drawPolygon(poly)
                painter.setBrush(Qt.NoBrush)
        elif has_outline and not has_fill:
            if len(pts) >= 2:
                _stroke_outline()
        else:
            if len(pts) >= 2:
                if pixmap is not None:
                    _paint_image()
                    _stroke_outline()
                else:
                    if gradient_outline is not None:
                        pen = QPen(QBrush(gradient_outline), lw)
                    else:
                        pen = QPen(effective_outline)
                        pen.setWidthF(lw)
                    pen.setCapStyle(Qt.RoundCap)
                    pen.setJoinStyle(Qt.RoundJoin)
                    painter.setPen(pen)
                    painter.setBrush(_fill_brush())
                    painter.drawPolygon(poly)
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(Qt.NoBrush)
            else:
                if pixmap is not None:
                    _paint_image()
                else:
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(_fill_brush())
                    painter.drawPolygon(poly)
                    painter.setBrush(Qt.NoBrush)

        if rot is not None:
            painter.restore()

class AnimatedText(_TweenDriver):
    def __init__(self, defn: TextDef):
        super().__init__()
        self.defn = defn
        d = defn
        self.cur_p:         P      = P(d.p.x, d.p.y)
        self.cur_px:        P      = P(d.px.x, d.px.y)

        self.cur_color      = QColor(d.fill_color)
        self.cur_font_size  = d.font_size
        self.cur_h_align    = d.h_align
        self.cur_v_align    = d.v_align
        self.cur_char_display = d.char_display
 
        self._sp:           P      = P(d.p.x, d.p.y)
        self._spx:          P      = P(d.px.x, d.px.y)
        self._sc   = QColor(d.fill_color)
        self._sfs  = d.font_size
        self._sha  = d.h_align
        self._sva  = d.v_align
        self._scd  = d.char_display
 
        self._dirty        = True
        self._cached_font  = None
        self._cached_x:  float = -1.0
        self._cached_y:  float = -1.0
        self._cached_px: float = -999.0
        self._cached_py: float = -999.0
        self._cached_dx    = 0
        self._cached_dy    = 0
        self._cached_label = ''
        self._cached_tw    = 0
        selfF_cached_th    = 0
        self._cached_fm: Optional[QFontMetrics] = None
 
        self._always_drivers_t: Dict[str, _AlwaysDriver] = {
            name: _AlwaysDriver(name, phase, 1)
            for name, phase in (defn.phases or {}).items()
            if _phase_key_name(name).startswith('always')
        }
        self._always_x_offset:  float = 0.0
        self._always_y_offset:  float = 0.0
        self._always_px_offset:  float           = 0.0
        self._always_py_offset:  float           = 0.0
        self._always_text_color: Optional[QColor] = None

        self._pos_offset: P = P(0.0, 0.0)

        self.cur_gradient_p1:  P = P(defn.gradient_p1.x,  defn.gradient_p1.y)
        self.cur_gradient_px1: P = P(defn.gradient_px1.x, defn.gradient_px1.y)
        self.cur_gradient_p2:  P = P(defn.gradient_p2.x,  defn.gradient_p2.y)
        self.cur_gradient_px2: P = P(defn.gradient_px2.x, defn.gradient_px2.y)
        self.cur_outline_color: QColor = QColor(defn.outline_color) if defn.outline_color else QColor(0,0,0,0)
        self.cur_outline_width: float  = defn.outline_width

        self._so:   QColor = QColor(defn.outline_color) if defn.outline_color else QColor(0,0,0,0)
        self._slow: float  = defn.outline_width
        self._sgp1:  P = P(defn.gradient_p1.x,  defn.gradient_p1.y)
        self._sgpx1: P = P(defn.gradient_px1.x, defn.gradient_px1.y)
        self._sgp2:  P = P(defn.gradient_p2.x,  defn.gradient_p2.y)
        self._sgpx2: P = P(defn.gradient_px2.x, defn.gradient_px2.y)

        self.cur_rot_center_p:      P     = P(defn.rot_center_p.x,  defn.rot_center_p.y)
        self.cur_rot_center_px:     P     = P(defn.rot_center_px.x, defn.rot_center_px.y)
        self.cur_rot_target_p:      P     = P(defn.rot_target_p.x,  defn.rot_target_p.y)
        self.cur_rot_target_px:     P     = P(defn.rot_target_px.x, defn.rot_target_px.y)
        self.cur_rot_angle_initial: float = defn.rot_angle_initial
        self.cur_rot_angle:         float = defn.rot_angle

        self._s_rot_center_p:      P     = P(defn.rot_center_p.x,  defn.rot_center_p.y)
        self._s_rot_center_px:     P     = P(defn.rot_center_px.x, defn.rot_center_px.y)
        self._s_rot_target_p:      P     = P(defn.rot_target_p.x,  defn.rot_target_p.y)
        self._s_rot_target_px:     P     = P(defn.rot_target_px.x, defn.rot_target_px.y)
        self._s_rot_angle_initial: float = defn.rot_angle_initial
        self._s_rot_angle:         float = defn.rot_angle

    def _save_start(self):
        self._sp    = P(self.cur_p.x,  self.cur_p.y)
        self._spx   = P(self.cur_px.x, self.cur_px.y)
        self._sc    = QColor(self.cur_color)
        self._so    = QColor(self.cur_outline_color)
        self._slow  = self.cur_outline_width
        self._sfs   = self.cur_font_size
        self._sha   = self.cur_h_align
        self._sva   = self.cur_v_align
        self._scd   = self.cur_char_display
        self._sgp1  = P(self.cur_gradient_p1.x,  self.cur_gradient_p1.y)
        self._sgpx1 = P(self.cur_gradient_px1.x, self.cur_gradient_px1.y)
        self._sgp2  = P(self.cur_gradient_p2.x,  self.cur_gradient_p2.y)
        self._sgpx2 = P(self.cur_gradient_px2.x, self.cur_gradient_px2.y)

    def _snap_to(self, tw: TextTween):
        self.cur_p             = P(self._sp.x,  self._sp.y)
        self.cur_px            = P(self._spx.x, self._spx.y)
        self.cur_color         = QColor(self._sc)
        self.cur_outline_color = QColor(self._so)
        self.cur_outline_width = self._slow
        self.cur_h_align       = self._sha
        self.cur_v_align       = self._sva
        self.cur_font_size     = self._sfs
        self.cur_char_display  = self._scd
        self.cur_gradient_p1   = P(self._sgp1.x,  self._sgp1.y)
        self.cur_gradient_px1  = P(self._sgpx1.x, self._sgpx1.y)
        self.cur_gradient_p2   = P(self._sgp2.x,  self._sgp2.y)
        self.cur_gradient_px2  = P(self._sgpx2.x, self._sgpx2.y)
        if tw.p is not None:
            if tw.p.x is not None: self.cur_p  = P(tw.p.x,  self.cur_p.y)
            if tw.p.y is not None: self.cur_p  = P(self.cur_p.x, tw.p.y)
        if tw.px is not None:
            if tw.px.x is not None: self.cur_px = P(tw.px.x, self.cur_px.y)
            if tw.px.y is not None: self.cur_px = P(self.cur_px.x, tw.px.y)
        if tw.fill_color    is not None: self.cur_color         = QColor(tw.fill_color)
        if tw.outline_color is not None: self.cur_outline_color = QColor(tw.outline_color)
        if tw.outline_width is not None: self.cur_outline_width = tw.outline_width
        if tw.h_align       is not None: self.cur_h_align       = tw.h_align
        if tw.v_align       is not None: self.cur_v_align       = tw.v_align
        if tw.font_size     is not None: self.cur_font_size     = tw.font_size
        if tw.char_display  is not None: self.cur_char_display  = tw.char_display
        if tw.gradient_p1   is not None: self.cur_gradient_p1   = tw.gradient_p1
        if tw.gradient_px1  is not None: self.cur_gradient_px1  = tw.gradient_px1
        if tw.gradient_p2   is not None: self.cur_gradient_p2   = tw.gradient_p2
        if tw.gradient_px2  is not None: self.cur_gradient_px2  = tw.gradient_px2
        if tw.rot_center_p      is not None: self.cur_rot_center_p      = tw.rot_center_p
        if tw.rot_center_px     is not None: self.cur_rot_center_px     = tw.rot_center_px
        if tw.rot_target_p      is not None: self.cur_rot_target_p      = tw.rot_target_p
        if tw.rot_target_px     is not None: self.cur_rot_target_px     = tw.rot_target_px
        if tw.rot_angle_initial is not None: self.cur_rot_angle_initial = tw.rot_angle_initial
        if tw.rot_angle         is not None: self.cur_rot_angle         = tw.rot_angle
        self._dirty = True

    def _reset_to_def(self):
        d = self.defn
        self.cur_p             = P(d.p.x, d.p.y)
        self.cur_px            = P(d.px.x, d.px.y)
        self.cur_color         = QColor(d.fill_color)
        self.cur_outline_color = QColor(d.outline_color) if d.outline_color else QColor(0,0,0,0)
        self.cur_outline_width = d.outline_width
        self.cur_font_size     = d.font_size
        self.cur_h_align       = d.h_align
        self.cur_v_align       = d.v_align
        self.cur_char_display  = d.char_display
        self.cur_gradient_p1   = P(d.gradient_p1.x,  d.gradient_p1.y)
        self.cur_gradient_px1  = P(d.gradient_px1.x, d.gradient_px1.y)
        self.cur_gradient_p2   = P(d.gradient_p2.x,  d.gradient_p2.y)
        self.cur_gradient_px2  = P(d.gradient_px2.x, d.gradient_px2.y)
        self.cur_rot_center_p      = P(d.rot_center_p.x,  d.rot_center_p.y)
        self.cur_rot_center_px     = P(d.rot_center_px.x, d.rot_center_px.y)
        self.cur_rot_target_p      = P(d.rot_target_p.x,  d.rot_target_p.y)
        self.cur_rot_target_px     = P(d.rot_target_px.x, d.rot_target_px.y)
        self.cur_rot_angle_initial = d.rot_angle_initial
        self.cur_rot_angle         = d.rot_angle
        self._dirty = True

    def _apply(self, tw: TextTween, v: float):
        if tw.p is not None:
            tx = self._sp.x + (tw.p.x - self._sp.x) * v if tw.p.x is not None else self._sp.x
            ty = self._sp.y + (tw.p.y - self._sp.y) * v if tw.p.y is not None else self._sp.y
            self.cur_p = P(tx, ty)
        if tw.px is not None:
            tx = self._spx.x + (tw.px.x - self._spx.x) * v if tw.px.x is not None else self._spx.x
            ty = self._spx.y + (tw.px.y - self._spx.y) * v if tw.px.y is not None else self._spx.y
            self.cur_px = P(tx, ty)
        if tw.fill_color    is not None: self.cur_color         = lerp_color(self._sc,  tw.fill_color,    v)
        if tw.outline_color is not None: self.cur_outline_color = lerp_color(self._so,  tw.outline_color, v)
        if tw.outline_width is not None: self.cur_outline_width = self._slow + (tw.outline_width - self._slow) * v
        if tw.h_align       is not None: self.cur_h_align       = self._sha  + (tw.h_align       - self._sha)  * v
        if tw.v_align       is not None: self.cur_v_align       = self._sva  + (tw.v_align       - self._sva)  * v
        if tw.font_size     is not None: self.cur_font_size     = self._sfs  + (tw.font_size     - self._sfs)  * v
        if tw.char_display  is not None: self.cur_char_display  = self._scd  + (tw.char_display  - self._scd)  * v
        if tw.gradient_p1   is not None: self.cur_gradient_p1   = P(self._sgp1.x  + (tw.gradient_p1.x  - self._sgp1.x)  * v, self._sgp1.y  + (tw.gradient_p1.y  - self._sgp1.y)  * v)
        if tw.gradient_px1  is not None: self.cur_gradient_px1  = P(self._sgpx1.x + (tw.gradient_px1.x - self._sgpx1.x) * v, self._sgpx1.y + (tw.gradient_px1.y - self._sgpx1.y) * v)
        if tw.gradient_p2   is not None: self.cur_gradient_p2   = P(self._sgp2.x  + (tw.gradient_p2.x  - self._sgp2.x)  * v, self._sgp2.y  + (tw.gradient_p2.y  - self._sgp2.y)  * v)
        if tw.gradient_px2  is not None: self.cur_gradient_px2  = P(self._sgpx2.x + (tw.gradient_px2.x - self._sgpx2.x) * v, self._sgpx2.y + (tw.gradient_px2.y - self._sgpx2.y) * v)
        if tw.rot_center_p      is not None: self.cur_rot_center_p      = P(self._s_rot_center_p.x  + (tw.rot_center_p.x  - self._s_rot_center_p.x)  * v, self._s_rot_center_p.y  + (tw.rot_center_p.y  - self._s_rot_center_p.y)  * v)
        if tw.rot_center_px     is not None: self.cur_rot_center_px     = P(self._s_rot_center_px.x + (tw.rot_center_px.x - self._s_rot_center_px.x) * v, self._s_rot_center_px.y + (tw.rot_center_px.y - self._s_rot_center_px.y) * v)
        if tw.rot_target_p      is not None: self.cur_rot_target_p      = P(self._s_rot_target_p.x  + (tw.rot_target_p.x  - self._s_rot_target_p.x)  * v, self._s_rot_target_p.y  + (tw.rot_target_p.y  - self._s_rot_target_p.y)  * v)
        if tw.rot_target_px     is not None: self.cur_rot_target_px     = P(self._s_rot_target_px.x + (tw.rot_target_px.x - self._s_rot_target_px.x) * v, self._s_rot_target_px.y + (tw.rot_target_px.y - self._s_rot_target_px.y) * v)
        if tw.rot_angle_initial is not None: self.cur_rot_angle_initial = self._s_rot_angle_initial + (tw.rot_angle_initial - self._s_rot_angle_initial) * v
        if tw.rot_angle         is not None: self.cur_rot_angle         = self._s_rot_angle         + (tw.rot_angle         - self._s_rot_angle)         * v
        self._dirty = True
    
    def _apply_blend(self, tw: TextTween, v: float):
        if tw.p is not None:
            nx = self.cur_p.x  + tw.p.x  * v if tw.p.x  is not None else self.cur_p.x
            ny = self.cur_p.y  + tw.p.y  * v if tw.p.y  is not None else self.cur_p.y
            self.cur_p = P(nx, ny)
        if tw.px is not None:
            nx = self.cur_px.x + tw.px.x * v if tw.px.x is not None else self.cur_px.x
            ny = self.cur_px.y + tw.px.y * v if tw.px.y is not None else self.cur_px.y
            self.cur_px = P(nx, ny)
        if tw.fill_color    is not None: self.cur_color         = lerp_color(self.cur_color,         tw.fill_color,    v)
        if tw.outline_color is not None: self.cur_outline_color = lerp_color(self.cur_outline_color, tw.outline_color, v)
        if tw.outline_width is not None: self.cur_outline_width += tw.outline_width * v
        if tw.h_align       is not None: self.cur_h_align       += tw.h_align       * v
        if tw.v_align       is not None: self.cur_v_align       += tw.v_align       * v
        if tw.font_size     is not None: self.cur_font_size     += tw.font_size     * v
        if tw.char_display  is not None: self.cur_char_display  += tw.char_display  * v
        if tw.gradient_p1   is not None: self.cur_gradient_p1   = P(self.cur_gradient_p1.x  + tw.gradient_p1.x  * v, self.cur_gradient_p1.y  + tw.gradient_p1.y  * v)
        if tw.gradient_px1  is not None: self.cur_gradient_px1  = P(self.cur_gradient_px1.x + tw.gradient_px1.x * v, self.cur_gradient_px1.y + tw.gradient_px1.y * v)
        if tw.gradient_p2   is not None: self.cur_gradient_p2   = P(self.cur_gradient_p2.x  + tw.gradient_p2.x  * v, self.cur_gradient_p2.y  + tw.gradient_p2.y  * v)
        if tw.gradient_px2  is not None: self.cur_gradient_px2  = P(self.cur_gradient_px2.x + tw.gradient_px2.x * v, self.cur_gradient_px2.y + tw.gradient_px2.y * v)
        self._dirty = True

    def set_phase(self, phase):
        super().set_phase(phase, self.defn.phases)
        self._dirty = True
        for driver in self._always_drivers_t.values():
            driver.notify_phase(phase, False)
        

    def update(self) -> None:
        pos_fn = self.defn.pos_fn
        if pos_fn is not None:
            try:
                offset = pos_fn()
                if offset is not None:
                    self._pos_offset = offset
                    self._dirty = True
            except Exception:
                pass
        self._drive()
        self._check_pulse(self.defn.phases or {})
 
        sum_px         = 0.0
        sum_py         = 0.0
        sum_x          = 0.0
        sum_y          = 0.0
        color_override = None
        base_done      = self.phase_done()

        for driver in self._always_drivers_t.values():
            driver.update(self._phase, base_done)
            sum_x  += driver.offset_p[0].x
            sum_y  += driver.offset_p[0].y
            sum_px += driver.offset_px[0].x
            sum_py += driver.offset_px[0].y
            if driver.offset_fill_color is not None:
                color_override = driver.offset_fill_color

        self._always_x_offset   = sum_x
        self._always_y_offset   = sum_y
        self._always_px_offset  = sum_px
        self._always_py_offset  = sum_py
        self._always_text_color = color_override
        if sum_px != 0.0 or sum_py != 0.0 or sum_x != 0.0 or sum_y != 0.0:
            self._dirty = True


    def resolve_text(self, context):
        template = self.defn.text or ''
        fn = self.defn.text_fn

        if fn is None:
            return template

        if isinstance(fn, EventDef):
            return str(fn.value)

        if callable(fn):
            try:    raw = fn(context)
            except: raw = ''
            if isinstance(raw, list):
                result = template
                for item in raw:
                    if '<#>' not in result:
                        break
                    result = result.replace('<#>', str(item), 1)
                return result
            value = str(raw)
            return template.replace('<#>', value) if '<#>' in template else value

        if isinstance(fn, list):
            result = template
            for item in fn:
                if '<#>' not in result:
                    break
                if isinstance(item, EventDef):
                    value = str(item.value)
                elif callable(item):
                    try:    value = str(item(context))
                    except: value = ''
                else:
                    value = str(item)
                result = result.replace('<#>', value, 1)
            return result

        return template

    def build_font(self, scale: float = 1.0):
        scaled_size = max(0.5, self.cur_font_size * scale)
        if self._cached_font is None or self._cached_font.pointSizeF() != scaled_size:
            f = QFont()
            if self.defn.font_family: f.setFamily(self.defn.font_family)
            f.setPointSizeF(scaled_size)
            f.setBold(self.defn.bold)
            f.setItalic(self.defn.italic)
            self._cached_font = f
            self._cached_fm   = None
        return self._cached_font

    def resolve_pos(self, widget_w, widget_h, cam_w, cam_h, label, font, scale=1.0):
        if (self._cached_label == label
                and self._cached_tw == widget_w
                and self._cached_th == widget_h
                and self._cached_x  == self.cur_p.x
                and self._cached_y  == self.cur_p.y
                and self._cached_px == self.cur_px.x + self._always_px_offset
                and self._cached_py == self.cur_px.y + self._always_py_offset):
            return self._cached_dx, self._cached_dy
        if self._cached_fm is None or self._dirty:
            self._cached_fm = QFontMetrics(font)
        fm = self._cached_fm
        if self.defn.uniform_scale:
            s  = min(widget_w/cam_w, widget_h/cam_h)
            bx = (0.5+(self.cur_p.x-0.5)*s/(widget_w/cam_w))*widget_w
            by = (0.5+(self.cur_p.y-0.5)*s/(widget_h/cam_h))*widget_h
        else:
            bx = self.cur_p.x*widget_w
            by = self.cur_p.y*widget_h
        bx += self.cur_px.x * scale
        by += self.cur_px.y * scale
        dx = int(bx - self.cur_h_align * fm.horizontalAdvance(label) + self._always_px_offset * scale)
        dy = int(by + fm.ascent() - self.cur_v_align * fm.height()   + self._always_py_offset * scale)
        self._cached_x  = self.cur_p.x
        self._cached_y  = self.cur_p.y
        self._cached_px = self.cur_px.x + self._always_px_offset
        self._cached_py = self.cur_px.y + self._always_py_offset
        self._cached_dx    = dx
        self._cached_dy    = dy
        self._cached_label = label
        self._cached_tw    = widget_w
        self._cached_th    = widget_h
        self._dirty        = False
        return dx, dy
    
    def resolve_display_text(self, full_label: str) -> str:
        cd = self.cur_char_display
        if cd <= 0.0:
            return ''
        if cd >= 1.0:
            return full_label
        n = len(full_label)
        if n == 0:
            return ''
        count = round(cd * n)
        count = max(0, min(n, count))
        if count == 0:
            return ''
        if self.defn.backward:
            return full_label[n - count:]
        return full_label[:count]
    
    def draw_text(self, painter: QPainter, widget_w: int, widget_h: int, cam_w: int, cam_h: int, ctx: Any, scale: float = 1.0) -> None:
        if self.hidden:
            return

        full_label = self.resolve_text(ctx)
        if not full_label:
            return

        cd = self.cur_char_display
        if cd <= 0.0:
            return

        scale      = 1.0 if not self.defn.uniform_scale else scale
        font       = self.build_font(scale)
        fm         = self._cached_fm if self._cached_fm is not None else QFontMetrics(font)
        use_path   = (self.defn.outline_width > 0.0 or self.defn.outline_color is not None or self.defn.gradient is not None)

        orig_p  = self.cur_p
        orig_px = self.cur_px
        self.cur_p  = P(self.cur_p.x  + self._always_x_offset, self.cur_p.y  + self._always_y_offset)
        self.cur_px = P(self.cur_px.x + self._always_px_offset, self.cur_px.y + self._always_py_offset)
        dx, dy = self.resolve_pos(widget_w, widget_h, cam_w, cam_h, full_label, font, scale)
        self.cur_p  = orig_p
        self.cur_px = orig_px

        dx += int(self._pos_offset.x)
        dy += int(self._pos_offset.y)

        fill_color = self._always_text_color if self._always_text_color is not None else self.cur_color

        # apply char_display clipping
        if cd < 1.0 and not self.defn.sub_char_clip:
            display_label = self.resolve_display_text(full_label)
            if not display_label:
                return
            if self.defn.backward:
                disp_w = fm.horizontalAdvance(display_label)
                full_w = fm.horizontalAdvance(full_label)
                dx     = dx + full_w - disp_w
            full_label = display_label

        angle_offset = _resolve_angle_value(self.defn.rot_angle_fn)
        rot = _resolve_rotation(
            self.cur_rot_center_p, self.cur_rot_center_px,
            self.cur_rot_target_p, self.cur_rot_target_px,
            self.cur_rot_angle_initial, self.cur_rot_angle + angle_offset,
            widget_w, widget_h
        )
        if rot is not None:
            rcx, rcy, angle = rot
            painter.save()
            painter.translate(rcx, rcy)
            painter.rotate(angle)
            painter.translate(-rcx, -rcy)

        painter.setFont(font)

        if not use_path:
            # fast path — solid color text
            painter.setPen(fill_color)
            if self.defn.sub_char_clip and cd < 1.0:
                full_w  = fm.horizontalAdvance(full_label)
                clip_w  = full_w * cd
                ascent  = fm.ascent()
                descent = fm.descent()
                clip_x  = (dx + full_w - clip_w) if self.defn.backward else dx
                painter.save()
                painter.setClipRect(QRectF(clip_x, dy - ascent, clip_w, ascent + descent))
                painter.drawText(int(dx), int(dy), full_label)
                painter.restore()
            else:
                painter.drawText(int(dx), int(dy), full_label)
            painter.setPen(Qt.NoPen)
            return

        path = QPainterPath()
        path.addText(dx, dy, font, full_label)

        if self.defn.sub_char_clip and cd < 1.0:
            full_w  = fm.horizontalAdvance(full_label)
            clip_w  = full_w * cd
            ascent  = fm.ascent()
            descent = fm.descent()
            clip_x  = (dx + full_w - clip_w) if self.defn.backward else dx
            painter.save()
            painter.setClipRect(QRectF(clip_x, dy - ascent, clip_w, ascent + descent))

        gd = self.defn.gradient

        def _gradient_brush():
            gd = self.defn.gradient

            def _has(p, px):
                return p.x != 0 or p.y != 0 or px.x != 0 or px.y != 0

            if gd.global_position:
                gw, gh = get_true_screen_size()
                off = _current_window_screen_offset
                if _has(self.cur_gradient_p1, self.cur_gradient_px1) or _has(self.cur_gradient_p2, self.cur_gradient_px2):
                    x1 = self.cur_gradient_p1.x * gw + self.cur_gradient_px1.x - off.x
                    y1 = self.cur_gradient_p1.y * gh + self.cur_gradient_px1.y - off.y
                    x2 = self.cur_gradient_p2.x * gw + self.cur_gradient_px2.x - off.x
                    y2 = self.cur_gradient_p2.y * gh + self.cur_gradient_px2.y - off.y
                else:
                    x1 = gd.p1.x * gw + gd.px1.x - off.x
                    y1 = gd.p1.y * gh + gd.px1.y - off.y
                    x2 = gd.p2.x * gw + gd.px2.x - off.x
                    y2 = gd.p2.y * gh + gd.px2.y - off.y
                return gd._animated.build_gradient(x1, y1, x2, y2, radial=gd.radial)

            if _has(self.cur_gradient_p1, self.cur_gradient_px1) or \
            _has(self.cur_gradient_p2, self.cur_gradient_px2):
                x1 = self.cur_gradient_p1.x  * widget_w + self.cur_gradient_px1.x
                y1 = self.cur_gradient_p1.y  * widget_h + self.cur_gradient_px1.y
                x2 = self.cur_gradient_p2.x  * widget_w + self.cur_gradient_px2.x
                y2 = self.cur_gradient_p2.y  * widget_h + self.cur_gradient_px2.y
            else:
                x1 = gd.p1.x  * widget_w + gd.px1.x
                y1 = gd.p1.y  * widget_h + gd.px1.y
                x2 = gd.p2.x  * widget_w + gd.px2.x
                y2 = gd.p2.y  * widget_h + gd.px2.y
            return gd._animated.build_gradient(x1, y1, x2, y2, radial=gd.radial)

        # fill
        if gd is not None and gd.target == 'fill':
            painter.setPen(Qt.NoPen)
            painter.fillPath(path, _gradient_brush())
        else:
            painter.setPen(Qt.NoPen)
            painter.fillPath(path, fill_color)

        # outline
        if self.cur_outline_width > 0.0 or self.cur_outline_color.alpha() > 0:
            if gd is not None and gd.target == 'outline':
                pen = QPen(_gradient_brush(), self.cur_outline_width)
            else:
                oc = self.cur_outline_color if self.cur_outline_color.alpha() > 0 else fill_color
                pen = QPen(oc, self.cur_outline_width)
            pen.setJoinStyle(Qt.RoundJoin)
            pen.setCapStyle(Qt.RoundCap)
            painter.strokePath(path, pen)

        if self.defn.sub_char_clip and cd < 1.0:
            painter.restore()
        
        if rot is not None:
            painter.restore()

        painter.setPen(Qt.NoPen)

# ──────────────────────── ARC DEF ────────────────────────

@dataclass
class ArcDef:
    center_p:            P                = field(default_factory=P)
    center_px:           P                = field(default_factory=P)
    outer_p:             P                = field(default_factory=P)
    outer_px:            P                = field(default_factory=P)
    inner_p:              Optional[P]      = None
    inner_px:             Optional[P]      = None
    angle_start:          Optional[float]  = None
    angle_end:            Optional[float]  = None
    circle:               bool             = False
    fill_color:           QColor           = field(default_factory=lambda: QColor(255, 255, 255, 255))
    outline_color:        Optional[QColor] = None
    outline_width:        float            = 0.0
    rot_center_p:         P                = field(default_factory=P)
    rot_center_px:        P                = field(default_factory=P)
    rot_target_p:         P                = field(default_factory=P)
    rot_target_px:        P                = field(default_factory=P)
    rot_angle_initial:    float            = 0.0
    rot_angle:            float            = 0.0
    rot_angle_fn:         Any              = 0.0
    hidden:               bool             = False
    phases:               Dict[str, Phase] = field(default_factory=dict)
    visible_threshold_x:  float            = 0.0
    visible_threshold_y:  float            = 0.0

    def __post_init__(self):
        if not self.circle and self.angle_start is None and self.angle_end is None:
            self.circle = True

@dataclass
class ArcTween:
    center_p:          Optional[P]         = None
    center_px:         Optional[P]         = None
    inner_p:           Optional[P]         = None
    inner_px:          Optional[P]         = None
    outer_p:           Optional[P]         = None
    outer_px:          Optional[P]         = None
    angle_start:       Optional[float]     = None
    angle_end:         Optional[float]     = None
    outline_width:     Optional[float]     = None
    rot_center_p:      Optional[P]         = None
    rot_center_px:     Optional[P]         = None
    rot_target_p:      Optional[P]         = None
    rot_target_px:     Optional[P]         = None
    rot_angle_initial: Optional[float]     = None
    rot_angle:         Optional[float]     = None
    start:             float               = 0.0
    dur:               float               = 0.5
    ease:              QEasingCurve.Type   = QEasingCurve.OutQuint
    prev_phase:        Optional[str]       = None
    blend:             bool                = False

class AnimatedArc(_TweenDriver):
    def __init__(self, defn: ArcDef) -> None:
        super().__init__()
        self.defn   = defn
        self.hidden = defn.hidden

        self.cur_center_p     = P(defn.center_p.x, defn.center_p.y)
        self.cur_center_px    = P(defn.center_px.x, defn.center_px.y)
        self.cur_outer_p      = P(defn.outer_p.x, defn.outer_p.y)
        self.cur_outer_px     = P(defn.outer_px.x, defn.outer_px.y)
        self.cur_inner_p      = P(defn.inner_p.x, defn.inner_p.y) if defn.inner_p is not None else None
        self.cur_inner_px     = P(defn.inner_px.x, defn.inner_px.y) if defn.inner_px is not None else None
        self.cur_angle_start  = defn.angle_start
        self.cur_angle_end    = defn.angle_end
        self.cur_outline_width = defn.outline_width

        self.cur_rot_center_p      = P(defn.rot_center_p.x,  defn.rot_center_p.y)
        self.cur_rot_center_px     = P(defn.rot_center_px.x, defn.rot_center_px.y)
        self.cur_rot_target_p      = P(defn.rot_target_p.x,  defn.rot_target_p.y)
        self.cur_rot_target_px     = P(defn.rot_target_px.x, defn.rot_target_px.y)
        self.cur_rot_angle_initial = defn.rot_angle_initial
        self.cur_rot_angle         = defn.rot_angle

        self._save_start()

    # ── _TweenDriver hooks ──────────────────────────────────────

    def _save_start(self):
        self._s_center_p      = P(self.cur_center_p.x, self.cur_center_p.y)
        self._s_center_px     = P(self.cur_center_px.x, self.cur_center_px.y)
        self._s_outer_p       = P(self.cur_outer_p.x, self.cur_outer_p.y)
        self._s_outer_px      = P(self.cur_outer_px.x, self.cur_outer_px.y)
        self._s_inner_p       = P(self.cur_inner_p.x, self.cur_inner_p.y) if self.cur_inner_p is not None else None
        self._s_inner_px      = P(self.cur_inner_px.x, self.cur_inner_px.y) if self.cur_inner_px is not None else None
        self._s_angle_start   = self.cur_angle_start
        self._s_angle_end     = self.cur_angle_end
        self._s_outline_width = self.cur_outline_width
        self._s_rot_center_p      = P(self.cur_rot_center_p.x,  self.cur_rot_center_p.y)
        self._s_rot_center_px     = P(self.cur_rot_center_px.x, self.cur_rot_center_px.y)
        self._s_rot_target_p      = P(self.cur_rot_target_p.x,  self.cur_rot_target_p.y)
        self._s_rot_target_px     = P(self.cur_rot_target_px.x, self.cur_rot_target_px.y)
        self._s_rot_angle_initial = self.cur_rot_angle_initial
        self._s_rot_angle         = self.cur_rot_angle

    def _apply(self, tw: ArcTween, v: float):
        def _lerp_p(cur_val, s_val, tw_val):
            base = s_val if s_val is not None else P(0.0, 0.0)
            nx = base.x + (tw_val.x - base.x) * v if tw_val.x is not None else base.x
            ny = base.y + (tw_val.y - base.y) * v if tw_val.y is not None else base.y
            return P(nx, ny)

        if tw.center_p  is not None: self.cur_center_p  = _lerp_p(self.cur_center_p,  self._s_center_p,  tw.center_p)
        if tw.center_px is not None: self.cur_center_px = _lerp_p(self.cur_center_px, self._s_center_px, tw.center_px)
        if tw.outer_p   is not None: self.cur_outer_p   = _lerp_p(self.cur_outer_p,   self._s_outer_p,   tw.outer_p)
        if tw.outer_px  is not None: self.cur_outer_px  = _lerp_p(self.cur_outer_px,  self._s_outer_px,  tw.outer_px)
        if tw.inner_p   is not None: self.cur_inner_p   = _lerp_p(self.cur_inner_p,   self._s_inner_p,   tw.inner_p)
        if tw.inner_px  is not None: self.cur_inner_px  = _lerp_p(self.cur_inner_px,  self._s_inner_px,  tw.inner_px)

        if tw.angle_start is not None:
            base = self._s_angle_start if self._s_angle_start is not None else 0.0
            self.cur_angle_start = base + (tw.angle_start - base) * v
        if tw.angle_end is not None:
            base = self._s_angle_end if self._s_angle_end is not None else 0.0
            self.cur_angle_end = base + (tw.angle_end - base) * v
        if tw.outline_width is not None:
            self.cur_outline_width = self._s_outline_width + (tw.outline_width - self._s_outline_width) * v

        if tw.rot_center_p      is not None: self.cur_rot_center_p      = P(self._s_rot_center_p.x  + (tw.rot_center_p.x  - self._s_rot_center_p.x)  * v, self._s_rot_center_p.y  + (tw.rot_center_p.y  - self._s_rot_center_p.y)  * v)
        if tw.rot_center_px     is not None: self.cur_rot_center_px     = P(self._s_rot_center_px.x + (tw.rot_center_px.x - self._s_rot_center_px.x) * v, self._s_rot_center_px.y + (tw.rot_center_px.y - self._s_rot_center_px.y) * v)
        if tw.rot_target_p      is not None: self.cur_rot_target_p      = P(self._s_rot_target_p.x  + (tw.rot_target_p.x  - self._s_rot_target_p.x)  * v, self._s_rot_target_p.y  + (tw.rot_target_p.y  - self._s_rot_target_p.y)  * v)
        if tw.rot_target_px     is not None: self.cur_rot_target_px     = P(self._s_rot_target_px.x + (tw.rot_target_px.x - self._s_rot_target_px.x) * v, self._s_rot_target_px.y + (tw.rot_target_px.y - self._s_rot_target_px.y) * v)
        if tw.rot_angle_initial is not None: self.cur_rot_angle_initial = self._s_rot_angle_initial + (tw.rot_angle_initial - self._s_rot_angle_initial) * v
        if tw.rot_angle         is not None: self.cur_rot_angle         = self._s_rot_angle         + (tw.rot_angle         - self._s_rot_angle)         * v
        self._dirty = True

    def _apply_blend(self, tw: ArcTween, v: float):
        def _blend_p(cur_val, tw_val):
            base = cur_val if cur_val is not None else P(0.0, 0.0)
            dx = tw_val.x if tw_val.x is not None else 0.0
            dy = tw_val.y if tw_val.y is not None else 0.0
            return P(base.x + dx * v, base.y + dy * v)

        if tw.center_p  is not None: self.cur_center_p  = _blend_p(self.cur_center_p,  tw.center_p)
        if tw.center_px is not None: self.cur_center_px = _blend_p(self.cur_center_px, tw.center_px)
        if tw.outer_p   is not None: self.cur_outer_p   = _blend_p(self.cur_outer_p,   tw.outer_p)
        if tw.outer_px  is not None: self.cur_outer_px  = _blend_p(self.cur_outer_px,  tw.outer_px)
        if tw.inner_p   is not None: self.cur_inner_p   = _blend_p(self.cur_inner_p,   tw.inner_p)
        if tw.inner_px  is not None: self.cur_inner_px  = _blend_p(self.cur_inner_px,  tw.inner_px)

        if tw.angle_start   is not None: self.cur_angle_start   = (self.cur_angle_start or 0.0) + tw.angle_start * v
        if tw.angle_end     is not None: self.cur_angle_end     = (self.cur_angle_end   or 0.0) + tw.angle_end   * v
        if tw.outline_width is not None: self.cur_outline_width = self.cur_outline_width + tw.outline_width * v
        self._dirty = True

    def _snap_to(self, tw: ArcTween):
        def _snap_p(cur_val, tw_val):
            base = cur_val if cur_val is not None else P(0.0, 0.0)
            nx = tw_val.x if tw_val.x is not None else base.x
            ny = tw_val.y if tw_val.y is not None else base.y
            return P(nx, ny)

        if tw.center_p  is not None: self.cur_center_p  = _snap_p(self.cur_center_p,  tw.center_p)
        if tw.center_px is not None: self.cur_center_px = _snap_p(self.cur_center_px, tw.center_px)
        if tw.outer_p   is not None: self.cur_outer_p   = _snap_p(self.cur_outer_p,   tw.outer_p)
        if tw.outer_px  is not None: self.cur_outer_px  = _snap_p(self.cur_outer_px,  tw.outer_px)
        if tw.inner_p   is not None: self.cur_inner_p   = _snap_p(self.cur_inner_p,   tw.inner_p)
        if tw.inner_px  is not None: self.cur_inner_px  = _snap_p(self.cur_inner_px,  tw.inner_px)

        if tw.angle_start       is not None: self.cur_angle_start       = tw.angle_start
        if tw.angle_end         is not None: self.cur_angle_end         = tw.angle_end
        if tw.outline_width     is not None: self.cur_outline_width     = tw.outline_width
        if tw.rot_center_p      is not None: self.cur_rot_center_p      = tw.rot_center_p
        if tw.rot_center_px     is not None: self.cur_rot_center_px     = tw.rot_center_px
        if tw.rot_target_p      is not None: self.cur_rot_target_p      = tw.rot_target_p
        if tw.rot_target_px     is not None: self.cur_rot_target_px     = tw.rot_target_px
        if tw.rot_angle_initial is not None: self.cur_rot_angle_initial = tw.rot_angle_initial
        if tw.rot_angle         is not None: self.cur_rot_angle         = tw.rot_angle
        self._dirty = True

    def _reset_to_def(self):
        d = self.defn
        self.cur_center_p      = P(d.center_p.x, d.center_p.y)
        self.cur_center_px     = P(d.center_px.x, d.center_px.y)
        self.cur_outer_p       = P(d.outer_p.x, d.outer_p.y)
        self.cur_outer_px      = P(d.outer_px.x, d.outer_px.y)
        self.cur_inner_p       = P(d.inner_p.x, d.inner_p.y) if d.inner_p is not None else None
        self.cur_inner_px      = P(d.inner_px.x, d.inner_px.y) if d.inner_px is not None else None
        self.cur_angle_start   = d.angle_start
        self.cur_angle_end     = d.angle_end
        self.cur_outline_width = d.outline_width
        self.cur_rot_center_p      = P(d.rot_center_p.x,  d.rot_center_p.y)
        self.cur_rot_center_px     = P(d.rot_center_px.x, d.rot_center_px.y)
        self.cur_rot_target_p      = P(d.rot_target_p.x,  d.rot_target_p.y)
        self.cur_rot_target_px     = P(d.rot_target_px.x, d.rot_target_px.y)
        self.cur_rot_angle_initial = d.rot_angle_initial
        self.cur_rot_angle         = d.rot_angle
        self._dirty = True

    def set_phase(self, phase: str):
        super().set_phase(phase, self.defn.phases)
        self._dirty = True

    def phase_done(self) -> bool:
        return self._is_done()

    def update(self) -> None:
        self._drive()
        self._check_pulse(self.defn.phases or {})

    # ── Geometry / Draw ──────────────────────────────────────────

    def _resolve(self, ww: int, wh: int):
        cx = self.cur_center_p.x * ww + self.cur_center_px.x
        cy = self.cur_center_p.y * wh + self.cur_center_px.y

        ox = self.cur_outer_p.x * ww + self.cur_outer_px.x
        oy = self.cur_outer_p.y * wh + self.cur_outer_px.y
        outer_r = _math.sqrt((ox - cx) ** 2 + (oy - cy) ** 2)

        inner_r = None
        if self.cur_inner_p is not None:
            ipx = self.cur_inner_px or P()
            ix = self.cur_inner_p.x * ww + ipx.x
            iy = self.cur_inner_p.y * wh + ipx.y
            r  = _math.sqrt((ix - cx) ** 2 + (iy - cy) ** 2)
            if r > 0.0 and (self.cur_inner_p.x != self.cur_center_p.x or self.cur_inner_p.y != self.cur_center_p.y or
                             ipx.x != self.cur_center_px.x or ipx.y != self.cur_center_px.y):
                inner_r = r

        return cx, cy, outer_r, inner_r

    def draw(self, painter: QPainter, ww: int, wh: int) -> None:
        if self.hidden:
            return

        d = self.defn
        if d.fill_color.alpha() == 0 and (self.cur_outline_width <= 0 or d.outline_color is None or d.outline_color.alpha() == 0):
            return

        cx, cy, outer_r, inner_r = self._resolve(ww, wh)
        if outer_r <= 0:
            return

        angle_offset = _resolve_angle_value(d.rot_angle_fn)
        rot = _resolve_rotation(
            self.cur_rot_center_p, self.cur_rot_center_px,
            self.cur_rot_target_p, self.cur_rot_target_px,
            self.cur_rot_angle_initial, self.cur_rot_angle + angle_offset,
            ww, wh
        )
        if rot is not None:
            rcx, rcy, angle = rot
            painter.save()
            painter.translate(rcx, rcy)
            painter.rotate(angle)
            painter.translate(-rcx, -rcy)

        is_circle = d.circle
        if not is_circle:
            if self.cur_angle_start is None or self.cur_angle_end is None:
                is_circle = True
            else:
                diff = abs(self.cur_angle_end - self.cur_angle_start)
                if diff == 0.0:
                    if rot is not None: painter.restore()
                    return
                elif diff >= 360.0:
                    is_circle = True

        def _build_path() -> QPainterPath:
            path = QPainterPath()
            rect_outer = QRectF(cx - outer_r, cy - outer_r, outer_r * 2, outer_r * 2)

            if is_circle:
                if inner_r is not None and inner_r > 0:
                    path.addEllipse(rect_outer)
                    inner_path = QPainterPath()
                    rect_inner = QRectF(cx - inner_r, cy - inner_r, inner_r * 2, inner_r * 2)
                    inner_path.addEllipse(rect_inner)
                    path = path.subtracted(inner_path)
                else:
                    path.addEllipse(rect_outer)
                return path

            start_our = self.cur_angle_start if self.cur_angle_start is not None else 0.0
            end_our   = self.cur_angle_end   if self.cur_angle_end   is not None else 0.0

            span = end_our - start_our
            span = span % 360.0
            if span == 0.0:
                return path

            qt_start = 90.0 - start_our
            qt_span  = -span

            rect_inner = QRectF(cx - inner_r, cy - inner_r, inner_r * 2, inner_r * 2) if (inner_r is not None and inner_r > 0) else None

            if rect_inner is not None:
                start_rad = _math.radians(start_our - 90.0)
                end_rad   = _math.radians(end_our   - 90.0)
                path.moveTo(cx + outer_r * _math.cos(start_rad), cy + outer_r * _math.sin(start_rad))
                path.arcTo(rect_outer, qt_start, qt_span)
                path.lineTo(cx + inner_r * _math.cos(end_rad), cy + inner_r * _math.sin(end_rad))
                path.arcTo(rect_inner, qt_start + qt_span, -qt_span)
                path.closeSubpath()
            else:
                start_rad = _math.radians(start_our - 90.0)
                path.moveTo(cx, cy)
                path.lineTo(cx + outer_r * _math.cos(start_rad), cy + outer_r * _math.sin(start_rad))
                path.arcTo(rect_outer, qt_start, qt_span)
                path.closeSubpath()

            return path

        path = _build_path()

        painter.setPen(Qt.NoPen)
        painter.setBrush(d.fill_color)
        painter.drawPath(path)
        painter.setBrush(Qt.NoBrush)

        if self.cur_outline_width > 0.0 and d.outline_color is not None and d.outline_color.alpha() > 0:
            pen = QPen(d.outline_color)
            pen.setWidthF(self.cur_outline_width)
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawPath(path)
            painter.setPen(Qt.NoPen)

        if rot is not None:
            painter.restore()

# ──────────────────────── SLIDER DEF ────────────────────────

@dataclass
class SliderDef:
    event_out: Optional[EventDef] = None
    min_val:   float = 0.0
    max_val:   float = 1.0
    step:      float = 0.0
    decimals:  int   = 0
    snap_points: Optional[List[float]] = None

    # track interpolation anchors
    min_track_p:  Optional[List[P]] = None
    min_track_px: Optional[List[P]] = None
    max_track_p:  Optional[List[P]] = None
    max_track_px: Optional[List[P]] = None

    # knob movement anchors
    min_p:  P = field(default_factory=P)
    min_px: P = field(default_factory=P)
    max_p:  P = field(default_factory=P)
    max_px: P = field(default_factory=P)

    track_poly_def:  Optional[PolygonDef]     = None
    fill_poly_def:   Optional[PolygonDef]     = None
    knob_poly_def:   Optional[PolygonDef]     = None
    extra_poly_defs: List[PolygonDef]         = field(default_factory=list)

    min_text_def:     Optional[TextDef] = None
    max_text_def:     Optional[TextDef] = None
    current_text_def: Optional[TextDef] = None
    extra_text_defs:  List[TextDef]     = field(default_factory=list)

    knob_hit_px: float = 10.0
    visible_threshold_x: float = 0.0
    visible_threshold_y: float = 0.0

def BasicSliderDef(
    p1: P = P(), p2: P = P(), px1: P = P(), px2: P = P(),
    event_out: Optional[EventDef] = None,
    min_val: float = 0.0, max_val: float = 1.0, step: float = 0.0, decimals: int = 0,
    label: str = '', unit: str = '',
    font_family: str = 'Oxanium',
    track_h: float = 4.0, knob_size: float = 10.0,
    track_idle: QColor = QColor(255, 255, 255, 40),
    fill_idle: QColor = QColor(200, 220, 255, 60),
    knob_idle: QColor = QColor(255, 255, 255, 220),
    knob_hover: QColor = QColor(255, 255, 255, 255),
    knob_press: QColor = QColor(180, 210, 255, 255),
    text_color: QColor = QColor(200, 220, 255, 255),
) -> SliderDef:
    half = track_h / 2.0
    track_pts_p  = [P(p1.x, p1.y), P(p2.x, p1.y), P(p2.x, p1.y), P(p1.x, p1.y)]
    track_pts_px = [P(px1.x, px1.y - half), P(px2.x, px1.y - half), P(px2.x, px1.y + half), P(px1.x, px1.y + half)]

    return SliderDef(
        event_out=event_out, min_val=min_val, max_val=max_val, step=step, decimals=decimals,
        min_track_p=[P(p1.x, p1.y)] * 4,
        min_track_px=[P(px1.x, px1.y - half), P(px1.x, px1.y - half), P(px1.x, px1.y + half), P(px1.x, px1.y + half)],
        max_track_p=track_pts_p,
        max_track_px=track_pts_px,
        min_p=P(p1.x, p1.y), min_px=P(px1.x, px1.y),
        max_p=P(p2.x, p1.y), max_px=P(px2.x, px1.y),
        track_poly_def=PolygonDef(p=track_pts_p, px=track_pts_px, fill_color=track_idle),
        fill_poly_def=PolygonDef(p=track_pts_p, px=track_pts_px, fill_color=fill_idle),
        knob_poly_def=PolygonDef(
            p=[P(0, 0)] * 4, px=[P(0, -knob_size), P(knob_size, 0), P(0, knob_size), P(-knob_size, 0)],
            fill_color=knob_idle,
            phases={
                'hovered':   Phase([PolygonTween(fill_color=knob_hover, start=0, dur=0.12, ease=QEasingCurve.OutQuint)]),
                'unhovered': Phase([PolygonTween(fill_color=knob_idle,  start=0, dur=0.15, ease=QEasingCurve.OutQuint)]),
                'pressed':   Phase([PolygonTween(fill_color=knob_press, start=0, dur=0.08, ease=QEasingCurve.OutQuint)]),
                'released':  Phase([PolygonTween(fill_color=knob_hover, start=0, dur=0.12, ease=QEasingCurve.OutQuint)]),
            },
        ),
        min_text_def=TextDef(p=P(p1.x, p1.y), px=P(px1.x, px1.y + 14), text='', font_size=9.0, fill_color=text_color, h_align=0.0, v_align=0.0, font_family=font_family),
        max_text_def=TextDef(p=P(p2.x, p1.y), px=P(px2.x, px1.y + 14), text='', font_size=9.0, fill_color=text_color, h_align=1.0, v_align=0.0, font_family=font_family),
        current_text_def=TextDef(p=P(0, 0), px=P(0, -14), text='', font_size=10.0, fill_color=text_color, h_align=0.5, v_align=1.0, font_family=font_family, text_fn=lambda ctx: ctx._current_text_value() if ctx else ''),
        extra_text_defs=[TextDef(p=P(p1.x, p1.y), px=P(px1.x, px1.y - 12), text=label, font_size=9.0, fill_color=text_color, h_align=0.0, v_align=1.0, bold=True, font_family=font_family)] if label else [],
    )


class SliderGroup:
    def __init__(self, defn: SliderDef, cam_w=MONITOR_RESOLUTIONS[0][0], cam_h=MONITOR_RESOLUTIONS[0][1]):
        self.defn  = defn
        self.cam_w = cam_w
        self.cam_h = cam_h

        self._cur_value:     float = 0.0
        self._initial_value: float = 0.0
        self._dragging:      bool  = False
        self._hovered:       bool  = False

        self._track  = AnimatedPolygon(defn.track_poly_def) if defn.track_poly_def else None
        self._fill   = AnimatedPolygon(defn.fill_poly_def)  if defn.fill_poly_def  else None
        self._knob   = AnimatedPolygon(defn.knob_poly_def)  if defn.knob_poly_def  else None
        self._extras = [AnimatedPolygon(d) for d in defn.extra_poly_defs]

        self._min_text     = AnimatedText(defn.min_text_def)     if defn.min_text_def     else None
        self._max_text     = AnimatedText(defn.max_text_def)     if defn.max_text_def     else None
        self._current_text = AnimatedText(defn.current_text_def) if defn.current_text_def else None
        self._extra_texts  = [AnimatedText(d) for d in defn.extra_text_defs]

        if self._min_text is not None:
            self._min_text.defn = _tw_replace(self._min_text.defn, text_fn=lambda ctx: self._format(self.defn.min_val))
        if self._max_text is not None:
            self._max_text.defn = _tw_replace(self._max_text.defn, text_fn=lambda ctx: self._format(self.defn.max_val))

        if self._knob is not None:
            self._knob.defn = _tw_replace(self._knob.defn, pos_fn=lambda: P(self._anchor_x, self._anchor_y))
        if self._current_text is not None:
            self._current_text.defn = _tw_replace(self._current_text.defn, pos_fn=lambda: P(self._anchor_x, self._anchor_y))

        self._anchor_x: float = 0.0
        self._anchor_y: float = 0.0
        self._last_anchor_x: float = 0.0
        self._last_anchor_y: float = 0.0
        self._line_ax: float = 0.0
        self._line_ay: float = 0.0
        self._line_bx: float = 0.0
        self._line_by: float = 0.0

        self.hidden: bool = False

    def _format(self, v: float) -> str:
        dec = self.defn.decimals
        return f'{v:.{dec}f}' if dec > 0 else str(int(round(v)))
    
    def _current_text_value(self) -> str:
        dec = self.defn.decimals
        base = f'{self._cur_value:.{dec}f}' if dec > 0 else str(int(round(self._cur_value)))
        if self.has_change:
            diff = self._cur_value - self._initial_value
            diff_s = f'{diff:+.{dec}f}' if dec > 0 else f'{int(diff):+}'
            return f'{base}  ({diff_s})'
        return base

    def _all_polys(self):
        yield from ([self._track] if self._track else [])
        yield from ([self._fill] if self._fill else [])
        yield from ([self._knob] if self._knob else [])
        yield from self._extras

    def _all_texts(self):
        yield from ([self._min_text] if self._min_text else [])
        yield from ([self._max_text] if self._max_text else [])
        yield from ([self._current_text] if self._current_text else [])
        yield from self._extra_texts

    def init_value(self, ctx):
        # if self.defn.event_out is not None:
        if self.defn.event_out._is_numeric:
            self._cur_value = self._initial_value = float(self.defn.event_out.value)

    def commit(self, ctx):
        self._initial_value = self._cur_value
        # if self.defn.event_out is not None:
        self.defn.event_out.value = self._cur_value

    def revert(self):
        self._cur_value = self._initial_value

    @property
    def has_change(self) -> bool:
        return self._cur_value != self._initial_value

    def set_phase(self, phase: str):
        for p in self._all_polys():
            p.set_phase(phase)
        for t in self._all_texts():
            t.set_phase(phase)

    def phase_done(self) -> bool:
        return all(p.phase_done() for p in self._all_polys()) and all(t.phase_done() for t in self._all_texts())

    def _ratio(self) -> float:
        d = self.defn
        if d.snap_points:
            n = len(d.snap_points)
            if n <= 1:
                return 0.0
            idx = min(range(n), key=lambda i: abs(d.snap_points[i] - self._cur_value))
            return idx / (n - 1)
        if d.max_val == d.min_val:
            return 0.0
        return max(0.0, min(1.0, (self._cur_value - d.min_val) / (d.max_val - d.min_val)))

    def hit_test_knob(self, mx: float, my: float, w: int, h: int) -> bool:
        if self._knob is None:
            return False
        return (abs(mx - self._anchor_x) <= self.defn.knob_hit_px and
                abs(my - self._anchor_y) <= self.defn.knob_hit_px)

    def drag_to(self, mx, my, w, h):
        ax, ay, bx, by = self._line_ax, self._line_ay, self._line_bx, self._line_by
        dx, dy = bx - ax, by - ay
        seg_len_sq = dx * dx + dy * dy
        if seg_len_sq == 0:
            ratio = 0.0
        else:
            ratio = ((mx - ax) * dx + (my - ay) * dy) / seg_len_sq
            ratio = max(0.0, min(1.0, ratio))
        d = self.defn
        if d.snap_points:
            n = len(d.snap_points)
            if n <= 1:
                self._cur_value = d.snap_points[0] if n == 1 else self._cur_value
                return
            idx = round(ratio * (n - 1))
            idx = max(0, min(n - 1, idx))
            self._cur_value = d.snap_points[idx]
            return
        lo, hi, step = d.min_val, d.max_val, d.step
        raw = lo + ratio * (hi - lo)
        if step > 0:
            raw = round(raw / step) * step
        self._cur_value = max(lo, min(hi, raw))

    def update(self, widget_w: int, widget_h: int):
        d = self.defn
        ratio = self._ratio()

        self._line_ax = d.min_p.x * widget_w + d.min_px.x
        self._line_ay = d.min_p.y * widget_h + d.min_px.y
        self._line_bx = d.max_p.x * widget_w + d.max_px.x
        self._line_by = d.max_p.y * widget_h + d.max_px.y
        self._anchor_x = self._line_ax + (self._line_bx - self._line_ax) * ratio
        self._anchor_y = self._line_ay + (self._line_by - self._line_ay) * ratio

        _slider_knob_positions[id(self.defn)] = P(self._anchor_x, self._anchor_y)

        if self._track is not None:
            self._track.update()

        if self._fill is not None:
            self._fill.update()
            if d.min_track_p is not None and d.max_track_p is not None:
                self._fill.cur_p = [P(a.x + (b.x - a.x) * ratio, a.y + (b.y - a.y) * ratio) for a, b in zip(d.min_track_p, d.max_track_p)]
            if d.min_track_px is not None and d.max_track_px is not None:
                self._fill.cur_px = [P(a.x + (b.x - a.x) * ratio, a.y + (b.y - a.y) * ratio) for a, b in zip(d.min_track_px, d.max_track_px)]
            self._fill._dirty = True

        if self._knob is not None:
            self._knob.update()

        for extra in self._extras:
            extra.update()

        if self._min_text is not None:
            self._min_text.update()
        if self._max_text is not None:
            self._max_text.update()
        if self._current_text is not None:
            self._current_text.update()

        for extra in self._extra_texts:
            extra.update()

    def draw(self, painter: QPainter, w: int, h: int, scale: float = 1.0):
        if self.hidden:
            return
        cam_w, cam_h = self.cam_w, self.cam_h
        if self._track is not None: self._track.draw(painter, w, h, cam_w, cam_h)
        if self._fill  is not None: self._fill.draw(painter, w, h, cam_w, cam_h)
        if self._knob  is not None: self._knob.draw(painter, w, h, cam_w, cam_h)
        for extra in self._extras:
            extra.draw(painter, w, h, cam_w, cam_h)
        for text in self._all_texts():
            if text.hidden:
                continue
            text.draw_text(painter, w, h, cam_w, cam_h, self, scale=scale)

# ──────────────────────── BUTTON DEF ────────────────────────

@dataclass
class ButtonDef:
    poly_def:             PolygonDef         = field(default_factory=PolygonDef)
    text_def:             Optional[TextDef]  = None
    extra_poly_defs:      List[PolygonDef]   = field(default_factory=list)
    extra_text_defs:      List[TextDef]      = field(default_factory=list)
    key:                  Optional[int]      = None
    mandatory_keys:       Any                = None
    action:               str                = 'set'
    event_out:            Any                = None
    event_delta:          Any                = None
    hold_when_set:        bool               = False
    phase_override:       Optional[Any]      = None
    on_fire:              Optional[Callable] = None
    continuous_update:    bool               = False
    invisible:            bool               = False
    ignore_click_consume: bool               = False
    ignore_mouse_event:   Any                = None
    visible_threshold_x:  float              = 0.0
    visible_threshold_y:  float              = 0.0

    def __post_init__(self):
        if self.action not in ('set', 'cycle'): self.hold_when_set = False
        if self.action != 'increment': self.continuous_update = False
        self._build_phases()

    def _build_phases(self):
        _dur  = 0.25
        _ease = QEasingCurve.OutQuint

        poly_phases  = dict(self.poly_def.phases or {})
        base_fill    = self.poly_def.fill_color    or QColor(101,  81, 176, 120)
        base_outline = self.poly_def.outline_color or QColor(171, 151, 247, 255)
        base_lw      = self.poly_def.outline_width    if self.poly_def.outline_width > 0 else 1.0
        fill_zero    = QColor(base_fill.red(),    base_fill.green(),    base_fill.blue(),    0)
        outline_zero = QColor(base_outline.red(), base_outline.green(), base_outline.blue(), 0)
        set_outline  = QColor(255, 255, 255, 255)
        hover_fill, click_fill = _derive_button_colors(base_fill)

        pts = self.poly_def.p
        px  = self.poly_def.px or [P()] * len(pts)

        poly_defaults = {
            'open':    Phase([
                PolygonTween(fill_color=fill_zero,    outline_color=outline_zero, outline_width=base_lw, start=0, dur=0,    ease=QEasingCurve.Linear),
                PolygonTween(fill_color=base_fill,    outline_color=base_outline, outline_width=base_lw, start=0, dur=_dur, ease=_ease),
            ]),
            'close':   Phase([PolygonTween(fill_color=fill_zero,   outline_color=outline_zero, outline_width=base_lw, start=0, dur=_dur, ease=_ease)]),
            'hover':   Phase([PolygonTween(fill_color=hover_fill,  outline_color=base_outline, outline_width=base_lw, start=0, dur=_dur, ease=_ease)]),
            'unhover': Phase([PolygonTween(fill_color=base_fill,   outline_color=base_outline, outline_width=base_lw, start=0, dur=_dur, ease=_ease)]),
            'click':   Phase([PolygonTween(fill_color=click_fill,  outline_color=base_outline, outline_width=base_lw, start=0, dur=_dur, ease=_ease)]),
            'release': Phase([PolygonTween(fill_color=hover_fill,  outline_color=base_outline, outline_width=base_lw, start=0, dur=_dur, ease=_ease)]),
            'set':     Phase([PolygonTween(fill_color=click_fill,  outline_color=set_outline,  outline_width=2.0,     start=0, dur=_dur, ease=_ease)]),
        }

        for phase_name, phase in poly_defaults.items():
            if not _phase_key_exists(poly_phases, phase_name):
                poly_phases[phase_name] = phase

        self.poly_def = _tw_replace(self.poly_def,
            fill_color    = fill_zero,
            outline_color = outline_zero,
            phases        = poly_phases,
        )

        if self.text_def is not None:
            text_phases = dict(self.text_def.phases or {})
            base_color  = self.text_def.fill_color or QColor(255, 255, 255, 255)
            text_zero   = QColor(base_color.red(), base_color.green(), base_color.blue(), 0)

            text_defaults = {
                'open':  Phase([TextTween(fill_color=text_zero,  start=0, dur=0,    ease=QEasingCurve.Linear),
                                TextTween(fill_color=base_color, start=0, dur=_dur, ease=_ease)]),
                'close': Phase([TextTween(fill_color=text_zero,  start=0, dur=_dur, ease=_ease)]),
            }

            for phase_name, phase in text_defaults.items():
                if not _phase_key_exists(text_phases, phase_name):
                    text_phases[phase_name] = phase

            self.text_def = _tw_replace(self.text_def,
                fill_color  = base_color,
                phases = text_phases,
            )

class AnimatedButton:
    def __init__(self, defn: ButtonDef, cam_w: int = MONITOR_RESOLUTIONS[0][0], cam_h: int = MONITOR_RESOLUTIONS[0][1]):
        self.defn       = defn
        self.cam_w      = cam_w
        self.cam_h      = cam_h
        self._hovered   = False
        self._pressed   = False
        self._key_held  = False
        self._held      = False
        self._polygon   = AnimatedPolygon(defn.poly_def)
        self._text      = AnimatedText(defn.text_def) if defn.text_def else None
        self._extra_polys = [AnimatedPolygon(d) for d in defn.extra_poly_defs]
        self._extra_texts = [AnimatedText(d) for d in defn.extra_text_defs]

        self._base_phase:        str  = ''          # open/close
        self._interaction_phase: str  = 'unhover'   # hover/unhover/click/release/set
        self._open_done:         bool = False
        self._applied_phase:     str  = ''

        self._cur_phase = ''
        self._last_poly: QPolygonF = QPolygonF()
        self._last_w:     int = 0
        self._last_h:     int = 0
        self._last_phase: str = ''
        self._last_bounds = None
        self._press_poly:QPolygonF = QPolygonF()
        self._last_override_phase: str = ''
        self._last_continuous_time: float = 0.0
        self._continuous_accum: float = 0.0

    def _set_base_phase(self, phase: str):
        if phase not in ('open', 'close'):
            return
        if phase == self._base_phase:
            return
        self._base_phase = phase
        if phase == 'close':
            self._held      = False
            self._pressed   = False
            self._key_held  = False
            self._hovered   = False
            self._interaction_phase = 'unhover'
            self._open_done = False
        elif phase == 'open':
            self._open_done = False
        self._recompute_and_apply()

    def _set_interaction_phase(self, phase: str):
        if phase not in ('hover', 'unhover', 'click', 'release', 'set'):
            return
        if self._held and phase in ('hover', 'unhover', 'release'):
            return
        if self._held and phase == 'click' and self.defn.action != 'cycle':
            return
        if self._pressed and phase in ('hover', 'unhover'):
            return
        self._interaction_phase = phase
        self._recompute_and_apply()

    def _target_phase(self) -> str:
        if self._base_phase == 'close':
            return 'close'
        if self._base_phase == 'open':
            return 'open' if not self._open_done else self._interaction_phase
        return self._base_phase or ''

    def _recompute_and_apply(self):
        target = self._target_phase()
        if not target:
            return
        self._applied_phase = target
        self._cur_phase     = target
        self._polygon.set_phase(target)
        if self._text is not None:
            self._text.set_phase(target)
        for p in self._extra_polys: p.set_phase(target)
        for t in self._extra_texts: t.set_phase(target)

    def _check_held(self):
        if not self.defn.hold_when_set:
            return
        pairs = self._iter_event_pairs()
        if not pairs:
            return
        if self._base_phase == 'close':
            if self._held:
                self._held = False
            return
        if self.defn.action == 'cycle':
            should_hold = True
            for ev, delta, _ in pairs:
                last = delta[-1] if isinstance(delta, list) and delta else delta
                if ev.value != last:
                    should_hold = False
                    break
        elif self.defn.action == 'set':
            should_hold = all(ev.value == delta for ev, delta, _ in pairs)
        else:
            return
        if should_hold and not self._held:
            self._held = True
            self._set_interaction_phase('set')
        elif not should_hold and self._held:
            self._held = False
            self._set_interaction_phase('unhover' if not self._hovered else 'hover')

    def hit_test(self, mx: float, my: float, w: int, h: int) -> bool:
        if self._is_closed:
            return False
        if not self.defn.invisible:
            fill_alpha    = self._polygon.cur_fill_color.alpha()
            outline_alpha = self._polygon.cur_outline_color.alpha()
            if fill_alpha == 0 and outline_alpha == 0:
                return False
        if self._last_bounds is not None:
            x1, y1, x2, y2 = self._last_bounds
            if not (x1 <= mx <= x2 and y1 <= my <= y2):
                return False
        poly = self._last_poly if not self._last_poly.isEmpty() else self._polygon.get_polygon(w, h, self.cam_w, self.cam_h)
        return poly.containsPoint(QPointF(mx, my), Qt.OddEvenFill)

    def _hit_test_press_poly(self, mx: float, my: float) -> bool:
        return self._press_poly.containsPoint(QPointF(mx, my), Qt.OddEvenFill) if not self._press_poly.isEmpty() else False

    def hit_test_global(self, gx: float, gy: float, panel) -> bool:
        return self.hit_test(gx - panel.x(), gy - panel.y(), panel.width(), panel.height())

    def mouse_left_hitbox(self):
        if self._pressed and not self._key_held:
            self._pressed = False
            self._set_interaction_phase('unhover')

    def key_press(self, key: int, held_keys: set = None) -> bool:
        if self._is_closed:
            return False
        if self.defn.key is None or self.defn.key != key or self._key_held:
            return False
        if held_keys is not None and not self._mandatory_keys_held(held_keys):
            return False
        self._key_held  = True
        self._pressed   = True
        self._press_poly = QPolygonF(self._last_poly)
        self._set_interaction_phase('click')
        return True

    def key_release(self, key: int, held_keys: set = None) -> bool:
        if self.defn.key is None or self.defn.key != key or not self._key_held:
            return False
        self._key_held = False
        self._pressed  = False
        if not self.defn.continuous_update:
            self.fire_event()
        self._check_held()
        if not self._held:
            self._set_interaction_phase('release')
            QTimer.singleShot(250, lambda: self._set_interaction_phase('hover' if self._hovered else 'unhover'))
        return True

    def _mandatory_keys_held(self, held_keys: set) -> bool:
        mk = self.defn.mandatory_keys
        if mk is None:
            return True
        keys = mk if isinstance(mk, list) else [mk]
        for k in keys:
            if isinstance(k, tuple):
                key, must_held = k
                if must_held and key not in held_keys:
                    return False
                if not must_held and key in held_keys:
                    return False
            else:
                if k not in held_keys:
                    return False
        return True

    @property
    def _is_closed(self) -> bool:
        return self._base_phase == 'close'

    def update(self, widget_w: int = 0, widget_h: int = 0):
        self._polygon.update()
        if self._text is not None:
            self._text.update()
        for p in self._extra_polys: p.update()
        for t in self._extra_texts: t.update()

        if self._base_phase == 'open' and not self._open_done:
            if self._polygon.phase_done() and (self._text is None or self._text.phase_done()):
                self._open_done = True
                self._recompute_and_apply()

        self._check_held()

        if self.defn.continuous_update:
            is_held = self._key_held or self._pressed
            if is_held:
                now = time.monotonic()
                if self._last_continuous_time == 0.0:
                    self._last_continuous_time = now
                dt = now - self._last_continuous_time
                self._last_continuous_time = now
                for ev, delta, _ in self._iter_event_pairs():
                    if ev is not None and delta is not None and isinstance(ev.value, (int, float)) and not isinstance(ev.value, bool):
                        new_val = ev.value + delta * dt
                        lo, hi  = getattr(ev, 'min_val', None), getattr(ev, 'max_val', None)
                        if lo is not None: new_val = max(float(lo), new_val)
                        if hi is not None: new_val = min(float(hi), new_val)
                        ev.value = new_val
            else:
                self._last_continuous_time = 0.0
                self._continuous_accum     = 0.0

        w, h = max(0, widget_w), max(0, widget_h)
        if w > 0 and h > 0:
            if (self._polygon._dirty or w != self._last_w or h != self._last_h or self._cur_phase != self._last_phase):
                self._polygon._dirty = True
                self._last_poly  = self._polygon.get_polygon(w, h, self.cam_w, self.cam_h)
                if self._last_poly.isEmpty():
                    self._last_bounds = None
                else:
                    it = iter(self._last_poly)
                    first = next(it)
                    x1 = x2 = first.x()
                    y1 = y2 = first.y()
                    for pt in it:
                        px, py = pt.x(), pt.y()
                        if px < x1: x1 = px
                        elif px > x2: x2 = px
                        if py < y1: y1 = py
                        elif py > y2: y2 = py
                    self._last_bounds = (x1, y1, x2, y2)
                self._last_w     = w
                self._last_h     = h
                self._last_phase = self._cur_phase

    def phase_done(self) -> bool:
        text_done = self._text.phase_done() if self._text is not None else True
        extras_done = all(p.phase_done() for p in self._extra_polys) and all(t.phase_done() for t in self._extra_texts)
        return self._polygon.phase_done() and text_done and extras_done

    def _iter_event_pairs(self):
        ev    = self.defn.event_out
        delta = self.defn.event_delta
        if isinstance(ev, (list, tuple)):
            if isinstance(delta, (list, tuple)):
                deltas    = list(delta) + [None] * max(0, len(ev) - len(delta))
                list_mode = True
            else:
                deltas    = [delta] * len(ev)
                list_mode = False
            return [(e, d, list_mode) for e, d in zip(ev, deltas)]
        return [(ev, delta, False)] if ev is not None else []

    def fire_event(self) -> None:
        action = self.defn.action
        pairs  = self._iter_event_pairs()
        if not pairs:
            return

        if action == 'cycle':
            for ev, delta, _ in pairs:
                if ev is None:
                    continue
                if delta is not None and isinstance(delta, list) and len(delta) > 0:
                    try:    idx = delta.index(ev.value)
                    except: idx = -1
                    ev.value = delta[(idx + 1) % len(delta)]
            return

        for ev, delta, list_mode in pairs:
            if ev is None:
                continue
            if action == 'increment':
                if delta is not None and isinstance(ev.value, (int, float)) and not isinstance(ev.value, bool):
                    new_val = ev.value + delta
                    lo, hi  = getattr(ev, 'min_val', None), getattr(ev, 'max_val', None)
                    if lo is not None: new_val = max(float(lo), new_val)
                    if hi is not None: new_val = min(float(hi), new_val)
                    ev.value = int(round(new_val)) if isinstance(ev.value, int) else new_val
            elif action == 'set':
                if delta is not None or list_mode:
                    ev.value = delta
            elif isinstance(ev.value, bool):
                ev.value = (not ev.value) if delta is None else bool(delta)
            elif isinstance(ev.value, (int, float)):
                if delta is None: continue
                new_val = ev.value + delta
                lo, hi  = getattr(ev, 'min_val', None), getattr(ev, 'max_val', None)
                if lo is not None: new_val = max(float(lo), new_val)
                if hi is not None: new_val = min(float(hi), new_val)
                ev.value = int(round(new_val)) if isinstance(ev.value, int) else new_val
            elif isinstance(ev.value, str):
                if delta is not None: ev.value = str(delta)

        if self.defn.on_fire is not None:
            self.defn.on_fire()

    def draw(self, painter: QPainter, w: int, h: int, scale: float = 1.0):
        self._last_poly = self._polygon.get_polygon(w, h, self.cam_w, self.cam_h)
        if self.defn.invisible:
            return

        fill    = self._polygon.cur_fill_color
        outline = self._polygon.cur_outline_color
        lw      = self._polygon.cur_line_width
        if fill.alpha() == 0 and (lw == 0 or outline.alpha() == 0):
            return

        self._last_poly = self._polygon.get_polygon(w, h, self.cam_w, self.cam_h)
        self._polygon.draw(painter, w, h, self.cam_w, self.cam_h)
        for p in self._extra_polys:
            p.draw(painter, w, h, self.cam_w, self.cam_h)
        if self._text is not None and not self._text.hidden:
            label = self._text.resolve_text(None)
            if label:
                text_scale = scale if self._text.defn.uniform_scale else 1.0
                font = self._text.build_font(text_scale)
                painter.setFont(font)
                painter.setPen(self._text.cur_color)
                dx, dy = self._text.resolve_pos(w, h, self.cam_w, self.cam_h, label, font, text_scale)
                painter.drawText(dx, dy, label)
                painter.setPen(Qt.NoPen)
        for t in self._extra_texts:
            if not t.hidden:
                t.draw_text(painter, w, h, self.cam_w, self.cam_h, None, scale=scale)

@dataclass
class Segment:
    key:           Optional[int]   = None
    event_delta:   Any             = None
    weight:        float           = 1.0
    label:         str             = ''
    text_color:    Optional[QColor]= None
    hold_when_set: bool            = True
    color:         Optional[QColor]= None

def SegmentedButtons(
    p1:             P                    = P(),
    p2:             P                    = P(),
    px1:            P                    = P(),
    px2:            P                    = P(),
    poly_def:       Optional[PolygonDef] = PolygonDef(fill_color=QColor(101, 81, 176, 120), outline_color=QColor(171, 151, 247, 255), outline_width=1.0),
    text_def:       Optional[TextDef]    = TextDef(font_size=18.0, fill_color=QColor(255, 255, 255, 255), bold=True),
    segments:       List[Segment]        = None,
    event_out:      Any                  = None,
    gap_px:         float                = 6.0,
    vertical:       bool                 = False,
    reverse_slant:  bool                 = False,
    line_delay:     float                = 0.05,
    cam_w:          int                  = 1920,
    cam_h:          int                  = 1080,
    phase_override: Any                  = None
) -> List[ButtonDef]:
    segments  = segments or []
    n         = len(segments)
    if n == 0:
        return []

    base_poly     = poly_def or PolygonDef()
    fill_color    = base_poly.fill_color    or QColor(101,  81, 176, 120)
    outline_color = base_poly.outline_color or QColor(171, 151, 247, 255)
    outline_width    = base_poly.outline_width    if base_poly.outline_width > 0 else 1.0

    total_weight = sum(s.weight for s in segments)
    half_gap     = gap_px / 2.0

    if not vertical:
        full_cross_px = (p2.y - p1.y) * cam_h + (px2.y - px1.y)
    else:
        full_cross_px = (p2.x - p1.x) * cam_w + (px2.x - px1.x)
    slant = abs(full_cross_px) / 2.0
    s_top = +slant if not reverse_slant else -slant
    s_bot = -slant if not reverse_slant else +slant

    def _norm_split(weight_before, weight_this):
        r0 = weight_before / total_weight
        r1 = (weight_before + weight_this) / total_weight
        return r0, r1

    def _make_poly(i: int, seg: Segment, weight_before: float) -> PolygonDef:
        r0, r1 = _norm_split(weight_before, seg.weight)
        is_only  = n == 1
        is_first = i == 0
        is_last  = i == n - 1
        base_col = seg.color or fill_color

        if not vertical:
            main_n0 = p1.x + (p2.x - p1.x) * r0
            main_n1 = p1.x + (p2.x - p1.x) * r1
            main_px0 = px1.x + (px2.x - px1.x) * r0
            main_px1 = px1.x + (px2.x - px1.x) * r1

            top_n  = p1.y;  bot_n  = p2.y
            mid_n  = (p1.y + p2.y) / 2.0
            top_px = px1.y; bot_px = px2.y
            mid_px = (px1.y + px2.y) / 2.0

            left_gap  = 0.0 if is_first else +half_gap
            right_gap = 0.0 if is_last  else -half_gap

            if is_only:
                p = [
                    P(main_n0, top_n),
                    P(main_n1, top_n),
                    P(main_n1, mid_n),
                    P(main_n1, bot_n),
                    P(main_n0, bot_n),
                    P(main_n0, mid_n),
                ]
                px_pts = [
                    P(main_px0 + slant, top_px),
                    P(main_px1 - slant, top_px),
                    P(main_px1,         mid_px),
                    P(main_px1 - slant, bot_px),
                    P(main_px0 + slant, bot_px),
                    P(main_px0,         mid_px),
                ]
            elif is_first:
                p = [
                    P(main_n0, top_n),
                    P(main_n1, top_n),
                    P(main_n1, bot_n),
                    P(main_n0, bot_n),
                    P(main_n0, mid_n),
                ]
                px_pts = [
                    P(main_px0 + slant,            top_px),
                    P(main_px1 + right_gap + s_top, top_px),
                    P(main_px1 + right_gap + s_bot, bot_px),
                    P(main_px0 + slant,            bot_px),
                    P(main_px0,                    mid_px),
                ]

            elif is_last:
                p = [
                    P(main_n0, top_n),
                    P(main_n1, top_n),
                    P(main_n1, mid_n),
                    P(main_n1, bot_n),
                    P(main_n0, bot_n),
                ]
                px_pts = [
                    P(main_px0 + left_gap + s_top, top_px),
                    P(main_px1 - slant,            top_px),
                    P(main_px1,                    mid_px),
                    P(main_px1 - slant,            bot_px),
                    P(main_px0 + left_gap + s_bot, bot_px),
                ]
            else:
                p = [P(main_n0, top_n),  P(main_n1, top_n),  P(main_n1, bot_n),  P(main_n0, bot_n)]
                px_pts = [
                    P(main_px0 + left_gap  + s_top, top_px),
                    P(main_px1 + right_gap + s_top, top_px),
                    P(main_px1 + right_gap + s_bot, bot_px),
                    P(main_px0 + left_gap  + s_bot, bot_px),
                ]
        else:
            main_n0  = p1.y + (p2.y - p1.y) * r0
            main_n1  = p1.y + (p2.y - p1.y) * r1
            main_px0 = px1.y + (px2.y - px1.y) * r0
            main_px1 = px1.y + (px2.y - px1.y) * r1

            left_n   = p1.x;           right_n  = p2.x
            mid_n    = (p1.x + p2.x) / 2.0
            left_px  = px1.x;          right_px = px2.x
            mid_px   = (px1.x + px2.x) / 2.0

            top_gap  = 0.0 if is_first else +half_gap
            bot_gap  = 0.0 if is_last  else -half_gap

            if is_only:
                p = [
                    P(mid_n,   main_n0),
                    P(right_n, main_n0),
                    P(right_n, main_n1),
                    P(mid_n,   main_n1),
                    P(left_n,  main_n1),
                    P(left_n,  main_n0),
                ]
                px_pts = [
                    P(mid_px,            main_px0),
                    P(right_px,          main_px0 + slant),
                    P(right_px,          main_px1 - slant),
                    P(mid_px,            main_px1),
                    P(left_px,           main_px1 - slant),
                    P(left_px,           main_px0 + slant),
                ]
            elif is_first:
                p = [
                    P(mid_n,   main_n0),
                    P(right_n, main_n0),
                    P(right_n, main_n1),
                    P(left_n,  main_n1),
                    P(left_n,  main_n0),
                ]
                px_pts = [
                    P(mid_px,            main_px0), 
                    P(right_px,          main_px0 + slant),
                    P(right_px + s_top,  main_px1 + bot_gap),
                    P(left_px  + s_bot,  main_px1 + bot_gap),
                    P(left_px,           main_px0 + slant),
                ]
            elif is_last:
                p = [
                    P(left_n,  main_n0),
                    P(right_n, main_n0),
                    P(right_n, main_n1),
                    P(mid_n,   main_n1),
                    P(left_n,  main_n1),
                ]
                px_pts = [
                    P(left_px  + s_top,  main_px0 + top_gap),
                    P(right_px + s_top,  main_px0 + top_gap),
                    P(right_px,          main_px1 - slant),
                    P(mid_px,            main_px1),
                    P(left_px,           main_px1 - slant),
                ]
            else:
                p = [
                    P(left_n,  main_n0),
                    P(right_n, main_n0),
                    P(right_n, main_n1),
                    P(left_n,  main_n1),
                ]
                px_pts = [
                    P(left_px  + s_top,  main_px0 + top_gap),
                    P(right_px + s_top,  main_px0 + top_gap),
                    P(right_px + s_bot,  main_px1 + bot_gap),
                    P(left_px  + s_bot,  main_px1 + bot_gap),
                ]

        def _make_dynamic_px(
            is_only=is_only, is_first=is_first, is_last=is_last,
            main_px0=main_px0, main_px1=main_px1,
            p1=p1, p2=p2, px1=px1, px2=px2,
            vertical=vertical,
            reverse_slant=reverse_slant,
            top_px=px1.y    if not vertical else 0.0,
            bot_px=px2.y    if not vertical else 0.0,
            left_gap=left_gap  if not vertical else 0.0,
            right_gap=right_gap if not vertical else 0.0,
            left_px=px1.x   if vertical else 0.0,
            right_px=px2.x  if vertical else 0.0,
            mid_px=(px1.x+px2.x)/2.0 if vertical else 0.0,
            top_gap=top_gap if vertical else 0.0,
            bot_gap=bot_gap if vertical else 0.0,
        ):
            def _dynamic(ww: int, wh: int) -> List[P]:
                if not vertical:
                    cross_px = (p2.y - p1.y) * wh + (px2.y - px1.y)
                    sl       = abs(cross_px) / 2.0
                    st       = +sl if not reverse_slant else -sl
                    sb       = -sl if not reverse_slant else +sl
                    mid_px_  = (px1.y + px2.y) / 2.0
                    if is_only:
                        return [
                            P(main_px0 + sl, top_px),
                            P(main_px1 - sl, top_px),
                            P(main_px1,      mid_px_),
                            P(main_px1 - sl, bot_px),
                            P(main_px0 + sl, bot_px),
                            P(main_px0,      mid_px_),
                        ]
                    elif is_first:
                        return [
                            P(main_px0 + sl,               top_px),
                            P(main_px1 + right_gap + st,   top_px),
                            P(main_px1 + right_gap + sb,   bot_px),
                            P(main_px0 + sl,               bot_px),
                            P(main_px0,                    mid_px_),
                        ]
                    elif is_last:
                        return [
                            P(main_px0 + left_gap + st,    top_px),
                            P(main_px1 - sl,               top_px),
                            P(main_px1,                    mid_px_),
                            P(main_px1 - sl,               bot_px),
                            P(main_px0 + left_gap + sb,    bot_px),
                        ]
                    else:
                        return [
                            P(main_px0 + left_gap  + st,   top_px),
                            P(main_px1 + right_gap + st,   top_px),
                            P(main_px1 + right_gap + sb,   bot_px),
                            P(main_px0 + left_gap  + sb,   bot_px),
                        ]
                else:
                    cross_px = (p2.x - p1.x) * ww + (px2.x - px1.x)
                    sl       = abs(cross_px) / 2.0
                    st       = +sl if not reverse_slant else -sl
                    sb       = -sl if not reverse_slant else +sl
                    if is_only:
                        return [
                            P(mid_px,   main_px0),
                            P(right_px, main_px0 + sl),
                            P(right_px, main_px1 - sl),
                            P(mid_px,   main_px1),
                            P(left_px,  main_px1 - sl),
                            P(left_px,  main_px0 + sl),
                        ]
                    elif is_first:
                        return [
                            P(mid_px,            main_px0),
                            P(right_px,          main_px0 + sl),
                            P(right_px,          main_px1 + bot_gap + sb),
                            P(left_px,           main_px1 + bot_gap + st),
                            P(left_px,           main_px0 + sl),
                        ]
                    elif is_last:
                        return [
                            P(left_px,           main_px0 + top_gap + st),
                            P(right_px,          main_px0 + top_gap + sb),
                            P(right_px,          main_px1 - sl),
                            P(mid_px,            main_px1),
                            P(left_px,           main_px1 - sl),
                        ]
                    else:
                        return [
                            P(left_px ,     main_px0 + top_gap + st),
                            P(right_px,     main_px0 + top_gap + sb),
                            P(right_px,     main_px1 + bot_gap + sb),
                            P(left_px ,     main_px1 + bot_gap + st),
                        ]
            return _dynamic
        
        return PolygonDef(
            p             = p,
            px            = px_pts,
            fill_color    = base_col,
            outline_color = outline_color,
            outline_width = outline_width,
            closed        = True,
            phases        = {},
            dynamic_px    = _make_dynamic_px(),
        )

    def _make_text(i: int, seg: Segment, weight_before: float) -> Optional[TextDef]:
        if text_def is None and not seg.label:
            return None
        r0, r1   = _norm_split(weight_before, seg.weight)
        r_center = (r0 + r1) / 2.0
        if not vertical:
            cx_n  = p1.x + (p2.x - p1.x) * r_center
            cy_n  = (p1.y + p2.y) / 2.0
            cx_px = px1.x + (px2.x - px1.x) * r_center
            cy_px = (px1.y + px2.y) / 2.0
        else:
            cx_n  = (p1.x + p2.x) / 2.0
            cy_n  = p1.y + (p2.y - p1.y) * r_center
            cx_px = (px1.x + px2.x) / 2.0
            cy_px = px1.y + (px2.y - px1.y) * r_center

        base  = text_def if text_def is not None else TextDef()
        label = seg.label or (base.text if base else '')

        return _tw_replace(base,
            p       = P(cx_n,  cy_n),
            px      = P(cx_px + base.px.x, cy_px + base.px.y),
            text    = label,
            h_align = 0.5,
            v_align = 0.5,
            phases  = {},
        )

    result: List[ButtonDef] = []
    weight_before = 0.0
    for i, seg in enumerate(segments):
        result.append(ButtonDef(
            poly_def      = _make_poly(i, seg, weight_before),
            text_def      = _make_text(i, seg, weight_before),
            key           = seg.key,
            action        = 'set',
            event_out     = event_out,
            event_delta   = seg.event_delta,
            hold_when_set = seg.hold_when_set,
            phase_override= phase_override,
        ))
        weight_before += seg.weight

    return result


def SevenSegmentDisplay(
    p1:            P                    = P(),
    p2:            P                    = P(),
    px1:           P                    = P(),
    px2:           P                    = P(),
    event_out:     Any                  = None,
    poly_def:      Optional[PolygonDef] = None,
    gap_px:        float                = 2.0,
) -> List[ButtonDef]:

    base_poly     = poly_def or PolygonDef()
    fill_color    = base_poly.fill_color    or QColor(101,  81, 176, 120)
    outline_color = base_poly.outline_color or QColor(133, 119, 186, 255)
    outline_width    = base_poly.outline_width    if base_poly.outline_width > 0 else 1.0
    fill_zero     = QColor(fill_color.red(),    fill_color.green(),    fill_color.blue(),    0)
    out_zero      = QColor(outline_color.red(), outline_color.green(), outline_color.blue(), 0)
    set_color     = QColor(255, 0, 0, 100)
    set_outline   = QColor(255, 0, 0, 255)

    seg_events: Dict[str, EventDef] = {}
    for letter in ('a','b','c','d','e','f','g'):
        seg_events[letter] = EventDef(name=f'seg_{letter}', value=False)

    def _update_output():
        bits = ''.join('1' if seg_events[k].value else '0'
                       for k in ('g','f','e','d','c','b','a'))
        if event_out is not None:
            event_out.value = f'0b0{bits}'

    for letter in ('a','b','c','d','e','f','g'):
        seg_events[letter]._watchers.append(lambda v: _update_output())

    seg_gaps = {
        'a': ( 0, -2), 'b': (+1, -1), 'c': (+1, +1),
        'd': ( 0, +2), 'e': (-1, +1), 'f': (-1, -1),
        'g': ( 0,  0),
    }
    vertical_segs = {'b', 'c', 'e', 'f'}

    def _h_pts(cx, cy, hl, ht, gx, gy):
        g = gap_px
        return [
            P(cx - hl       + gx*g, cy          + gy*g),  # left point
            P(cx - hl + ht  + gx*g, cy - ht     + gy*g),  # top-left
            P(cx + hl - ht  + gx*g, cy - ht     + gy*g),  # top-right
            P(cx + hl       + gx*g, cy          + gy*g),  # right point
            P(cx + hl - ht  + gx*g, cy + ht     + gy*g),  # bottom-right
            P(cx - hl + ht  + gx*g, cy + ht     + gy*g),  # bottom-left
        ]

    def _v_pts(cx, cy, hl, ht, gx, gy):
        g = gap_px
        return [
            P(cx          + gx*g, cy - hl       + gy*g),  # top point
            P(cx + ht     + gx*g, cy - hl + ht  + gy*g),  # top-right
            P(cx + ht     + gx*g, cy + hl - ht  + gy*g),  # bottom-right
            P(cx          + gx*g, cy + hl        + gy*g),  # bottom point
            P(cx - ht     + gx*g, cy + hl - ht  + gy*g),  # bottom-left
            P(cx - ht     + gx*g, cy - hl + ht  + gy*g),  # top-left
        ]

    mc_xn  = (p1.x + p2.x) / 2.0
    mc_yn  = (p1.y + p2.y) / 2.0

    def _make_dynamic(letter: str):
        gx, gy  = seg_gaps[letter]
        is_vert = letter in vertical_segs

        def _dynamic(ww: int, wh: int) -> List[P]:
            x1 = p1.x * ww + px1.x
            y1 = p1.y * wh + px1.y
            x2 = p2.x * ww + px2.x
            y2 = p2.y * wh + px2.y

            cx = (x1 + x2) / 2.0
            cy = (y1 + y2) / 2.0

            hl_h = (x2 - x1) / 2.0
            ht   = (y2 - y1) / 2.0

            hl_v = hl_h

            cx_r = cx + hl_h
            cx_l = cx - hl_h

            cy_a = cy - 2.0 * hl_v
            cy_d = cy + 2.0 * hl_v
            cy_g = cy

            cy_upper = cy - hl_v   # center of b, f
            cy_lower = cy + hl_v   # center of c, e

            if letter == 'a':
                return _h_pts(cx,   cy_a,    hl_h, ht, gx, gy)
            elif letter == 'g':
                return _h_pts(cx,   cy_g,    hl_h, ht, gx, gy)
            elif letter == 'd':
                return _h_pts(cx,   cy_d,    hl_h, ht, gx, gy)
            elif letter == 'b':
                return _v_pts(cx_r, cy_upper, hl_v, ht, gx, gy)
            elif letter == 'c':
                return _v_pts(cx_r, cy_lower, hl_v, ht, gx, gy)
            elif letter == 'f':
                return _v_pts(cx_l, cy_upper, hl_v, ht, gx, gy)
            elif letter == 'e':
                return _v_pts(cx_l, cy_lower, hl_v, ht, gx, gy)
            return pts

        return _dynamic
    
    def _make_seg_poly(letter: str) -> PolygonDef:
        hover_fill, click_fill = _derive_button_colors(fill_color)
        active_fill = QColor(220, 60, 60, 255)

        p      = [P(0.0, 0.0)] * 6
        px_pts = [P(0.0, 0.0)] * 6

        merged_phases = {
            'open':    Phase([PolygonTween(fill_color=fill_zero,   outline_color=out_zero,      outline_width=outline_width, start=0, dur=0,    ease=QEasingCurve.Linear),
                              PolygonTween(fill_color=fill_color,  outline_color=outline_color, outline_width=outline_width, start=0, dur=0.25, ease=QEasingCurve.OutQuint)]),
            'close':   Phase([PolygonTween(fill_color=fill_zero,   outline_color=out_zero,      outline_width=outline_width, start=0, dur=0.25, ease=QEasingCurve.OutQuint)]),
            'hover':   Phase([PolygonTween(fill_color=hover_fill,  outline_color=outline_color, outline_width=outline_width, start=0, dur=0.25, ease=QEasingCurve.OutQuint)]),
            'unhover': Phase([PolygonTween(fill_color=fill_color,  outline_color=outline_color, outline_width=outline_width, start=0, dur=0.25, ease=QEasingCurve.OutQuint)]),
            'click':   Phase([PolygonTween(fill_color=click_fill,  outline_color=outline_color, outline_width=outline_width, start=0, dur=0.25, ease=QEasingCurve.OutQuint)]),
            'release': Phase([PolygonTween(fill_color=hover_fill,  outline_color=outline_color, outline_width=outline_width, start=0, dur=0.25, ease=QEasingCurve.OutQuint)]),
            'set':     Phase([PolygonTween(fill_color=set_color,   outline_color=set_outline,   outline_width=2.0,        start=0, dur=0.25, ease=QEasingCurve.OutQuint)]),
            **(base_poly.phases or {}),
        }

        return _tw_replace(base_poly,
            p             = p,
            px            = px_pts,
            fill_color    = fill_color,
            outline_color = outline_color,
            outline_width    = outline_width,
            closed        = True,
            phases        = merged_phases,
            dynamic_px    = _make_dynamic(letter),
        )

    result: List[ButtonDef] = []
    for letter in ('a','b','c','d','e','f','g'):
        result.append(ButtonDef(
            poly_def      = _make_seg_poly(letter),
            text_def      = None,
            key           = None,
            action        = 'cycle',
            event_out     = seg_events[letter],
            event_delta   = [False, True],
            hold_when_set = True,
        ))

    return result


# ──────────────────────── TEXTBOX DEF ────────────────────────

@dataclass
class TextboxDef:
    poly_def:            PolygonDef         = field(default_factory=PolygonDef)
    text_def:            Optional[TextDef]  = None
    preview_text_def:    Optional[TextDef]  = None
    event_out:           Optional[EventDef] = None
    live_event_out:      Optional[EventDef] = None
    clear_event:         Optional[EventDef] = None
    phase_override:      Optional[Any]      = None
    max_length:          float              = 1.0
    max_length_px:       float              = 0.0
    clear_when_sent:     bool               = True
    exit_when_sent:      bool               = True
    override_inputs:     bool               = True
    visible_threshold_x: float              = 0.0
    visible_threshold_y: float              = 0.0

    def __post_init__(self):
        self._build_phases()

    def _build_phases(self):
        _dur  = 0.25
        _ease = QEasingCurve.OutQuint

        poly_phases   = dict(self.poly_def.phases or {})
        base_fill     = self.poly_def.fill_color    or QColor(101,  81, 176, 120)
        base_outline  = self.poly_def.outline_color or QColor(171, 151, 247, 255)
        base_lw       = self.poly_def.outline_width    if self.poly_def.outline_width > 0 else 1.0
        fill_zero     = QColor(base_fill.red(),    base_fill.green(),    base_fill.blue(),    0)
        outline_zero  = QColor(base_outline.red(), base_outline.green(), base_outline.blue(), 0)
        hover_fill, click_fill = _derive_button_colors(base_fill)
        click_outline = QColor(255, 255, 255, 255)

        poly_defaults = {
            'open':    Phase([
                PolygonTween(fill_color=fill_zero,   outline_color=outline_zero,  outline_width=base_lw, start=0, dur=0,    ease=QEasingCurve.Linear),
                PolygonTween(fill_color=base_fill,   outline_color=base_outline,  outline_width=base_lw, start=0, dur=_dur, ease=_ease),
            ]),
            'close':   Phase([PolygonTween(fill_color=fill_zero,   outline_color=outline_zero,  outline_width=base_lw, start=0, dur=_dur, ease=_ease)]),
            'hover':   Phase([PolygonTween(fill_color=hover_fill,  outline_color=base_outline,  outline_width=base_lw, start=0, dur=_dur, ease=_ease)]),
            'unhover': Phase([PolygonTween(fill_color=base_fill,   outline_color=base_outline,  outline_width=base_lw, start=0, dur=_dur, ease=_ease)]),
            'click': Phase([PolygonTween(fill_color=click_fill,  outline_color=click_outline, outline_width=2.0,     start=0, dur=_dur, ease=_ease)]),
        }
        for phase_name, phase in poly_defaults.items():
            if not _phase_key_exists(poly_phases, phase_name):
                poly_phases[phase_name] = phase

        self.poly_def = _tw_replace(self.poly_def,
            fill_color    = fill_zero,
            outline_color = outline_zero,
            phases        = poly_phases,
        )

        if self.text_def is not None:
            text_phases  = dict(self.text_def.phases or {})
            base_color   = self.text_def.fill_color or QColor(255, 255, 255, 255)
            text_zero    = QColor(base_color.red(), base_color.green(), base_color.blue(), 0)
            dim_color    = QColor(base_color.red(), base_color.green(), base_color.blue(), 160)

            text_defaults = {
                'open':    Phase([TextTween(fill_color=text_zero,  start=0, dur=0,    ease=QEasingCurve.Linear),
                                  TextTween(fill_color=dim_color,  start=0, dur=_dur, ease=_ease)]),
                'close':   Phase([TextTween(fill_color=text_zero,  start=0, dur=_dur, ease=_ease)]),
                'hover':   Phase([TextTween(fill_color=base_color, start=0, dur=_dur, ease=_ease)]),
                'unhover': Phase([TextTween(fill_color=dim_color,  start=0, dur=_dur, ease=_ease)]),
                'click': Phase([TextTween(fill_color=base_color, start=0, dur=_dur, ease=_ease)]),
            }
            for phase_name, phase in text_defaults.items():
                if not _phase_key_exists(text_phases, phase_name):
                    text_phases[phase_name] = phase

            self.text_def = _tw_replace(self.text_def,
                fill_color  = text_zero,
                phases = text_phases,
            )


_SHIFT_MAP: Dict[int, str] = {
    Qt.Key_1: '!', Qt.Key_2: '@', Qt.Key_3: '#', Qt.Key_4: '$', Qt.Key_5: '%',
    Qt.Key_6: '^', Qt.Key_7: '&', Qt.Key_8: '*', Qt.Key_9: '(', Qt.Key_0: ')',
    Qt.Key_Minus:        '_', Qt.Key_Equal:     '+',
    Qt.Key_BracketLeft:  '{', Qt.Key_BracketRight: '}',
    Qt.Key_Backslash:    '|', Qt.Key_Semicolon:    ':',
    Qt.Key_Apostrophe:   '"', Qt.Key_Comma:        '<',
    Qt.Key_Period:       '>', Qt.Key_Slash:         '?',
    Qt.Key_QuoteLeft:    '~',
}
_NOSHIFT_MAP: Dict[int, str] = {
    Qt.Key_Minus:        '-', Qt.Key_Equal:        '=',
    Qt.Key_BracketLeft:  '[', Qt.Key_BracketRight: ']',
    Qt.Key_Backslash:    '\\',Qt.Key_Semicolon:    ';',
    Qt.Key_Apostrophe:   "'", Qt.Key_Comma:        ',',
    Qt.Key_Period:       '.', Qt.Key_Slash:         '/',
    Qt.Key_QuoteLeft:    '`', Qt.Key_Space:         ' ',
}

_KEY_REPEAT_DELAY    = 0.4
_KEY_REPEAT_INTERVAL = 0.035

class AnimatedTextbox:
    def __init__(self, defn: TextboxDef, cam_w: int = MONITOR_RESOLUTIONS[0][0], cam_h: int = MONITOR_RESOLUTIONS[0][1]) -> None:
        self.defn    = defn
        self.cam_w   = cam_w
        self.cam_h   = cam_h

        self._polygon      = AnimatedPolygon(defn.poly_def)
        self._text         = AnimatedText(defn.text_def) if defn.text_def else None
        self._preview_text = AnimatedText(defn.preview_text_def) if defn.preview_text_def else None

        self._buffer:    str  = ''
        self._active:    bool = False
        self._hovered:   bool = False
        self._ctrl_held: bool = False

        self._held_key:             Optional[int] = None
        self._held_shift:           bool = False
        self._held_ctrl:            bool = False
        self._next_repeat_time: float = 0.0

        self._base_phase:        str  = ''
        self._interaction_phase: str  = 'unhover'
        self._open_done:         bool = False

        self._cur_phase: str = ''
        self._last_poly: QPolygonF = QPolygonF()
        self._last_override_phase: str = ''

        self._set_base_phase('open')
        self.hidden: bool = False

    def _set_base_phase(self, phase: str) -> None:
        if phase not in ('open', 'close'):
            return
        if phase == self._base_phase:
            return
        self._base_phase = phase
        if phase == 'close':
            self._active   = False
            self._hovered  = False
            self._held_key = None
            if self in _active_override_textboxes:
                _active_override_textboxes.remove(self)
            self._interaction_phase = 'unhover'
            self._open_done = False
        elif phase == 'open':
            self._open_done = False
        self._recompute_and_apply()

    def _set_interaction_phase(self, phase: str) -> None:
        if phase not in ('hover', 'unhover', 'click'):
            return
        self._interaction_phase = phase
        self._recompute_and_apply()

    def _target_phase(self) -> str:
        if self._base_phase == 'close':
            return 'close'
        if self._base_phase == 'open':
            return 'open' if not self._open_done else self._interaction_phase
        return self._base_phase or ''

    def _recompute_and_apply(self) -> None:
        target = self._target_phase()
        if not target:
            return
        self._cur_phase = target
        self._polygon.set_phase(target)
        if self._text is not None:
            self._text.set_phase(target)
        if self._preview_text is not None:
            self._preview_text.set_phase(target)

    def hit_test(self, mx: float, my: float, w: int, h: int) -> bool:
        if not self._last_poly.isEmpty():
            return self._last_poly.containsPoint(QPointF(mx, my), Qt.OddEvenFill)
        return False

    def _send(self) -> None:
        if self.defn.event_out is not None:
            self.defn.event_out.value = self._buffer
        if self.defn.clear_when_sent:
            self._buffer = ''
        if self.defn.exit_when_sent:
            self._deactivate()

    def _activate(self) -> None:
        self._active = True
        if self.defn.override_inputs and self not in _active_override_textboxes:
            _active_override_textboxes.append(self)
        self._set_interaction_phase('click')

    def _deactivate(self) -> None:
        self._active   = False
        self._held_key = None
        if self in _active_override_textboxes:
            _active_override_textboxes.remove(self)
        self._set_interaction_phase('hover' if self._hovered else 'unhover')

    def _apply_key_action(self, key: int, shift: bool, ctrl: bool) -> bool:
        if key == Qt.Key_Backspace:
            if ctrl:
                s = self._buffer.rstrip(' ')
                idx = len(s)
                while idx > 0 and s[idx - 1] != ' ':
                    idx -= 1
                self._buffer = s[:idx]
            else:
                self._buffer = self._buffer[:-1]
            return True

        if key == Qt.Key_V and ctrl:
            try:
                text = QApplication.clipboard().text()
            except Exception:
                text = ''
            if text:
                self._buffer += text.replace('\r', '').replace('\n', ' ')
            return True

        ch = self._resolve_char(key, shift)
        if ch is not None:
            self._buffer += ch
            return True

        return False

    def key_press(self, key: int, shift: bool = False, ctrl: bool = False) -> bool:
        if key in (Qt.Key_Control, Qt.Key_Meta):
            self._ctrl_held = True
            return self._active and self.defn.override_inputs

        if not self._active:
            return False

        if key in (Qt.Key_Return, Qt.Key_Enter):
            self._send()
            return True

        if key == Qt.Key_Escape:
            self._deactivate()
            return True

        eff_ctrl = ctrl or self._ctrl_held
        handled = self._apply_key_action(key, shift, eff_ctrl)
        if handled:
            if not (key == Qt.Key_V and eff_ctrl):
                self._held_key         = key
                self._held_shift       = shift
                self._held_ctrl        = eff_ctrl
                self._next_repeat_time = time.monotonic() + _KEY_REPEAT_DELAY
            return True

        return self.defn.override_inputs

    def key_release(self, key: int) -> bool:
        if key in (Qt.Key_Control, Qt.Key_Meta):
            self._ctrl_held = False
        if self._held_key == key:
            self._held_key = None
        return self._active and self.defn.override_inputs

    def _resolve_char(self, key: int, shift: bool) -> Optional[str]:
        if Qt.Key_A <= key <= Qt.Key_Z:
            ch = chr(key)
            return ch if shift else ch.lower()
        if Qt.Key_0 <= key <= Qt.Key_9:
            if shift:
                return _SHIFT_MAP.get(key)
            return chr(key)
        if 32 <= key <= 126:
            return chr(key)
        if shift and key in _SHIFT_MAP:
            return _SHIFT_MAP[key]
        if not shift and key in _NOSHIFT_MAP:
            return _NOSHIFT_MAP[key]
        return None

    def mouse_press(self, mx: float, my: float, w: int, h: int) -> bool:
        if self.hit_test(mx, my, w, h):
            self._activate()
            return True
        if self._active:
            self._deactivate()
        return False

    def mouse_move(self, mx: float, my: float, w: int, h: int) -> None:
        hit = self.hit_test(mx, my, w, h)
        if hit != self._hovered:
            self._hovered = hit
            if not self._active:
                self._set_interaction_phase('hover' if hit else 'unhover')

    def mouse_release(self, mx: float, my: float, w: int, h: int) -> None:
        pass

    def _resolve_display_text(self, w: int, h: int) -> str:
        if self._text is None:
            return self._buffer
        d = self.defn
        clip_w_n = d.max_length * w + d.max_length_px
        font = self._text.build_font(1.0)
        fm   = QFontMetrics(font)
        text = self._buffer
        while text and fm.horizontalAdvance(text) > clip_w_n:
            text = text[:-1]
        return text

    def update(self, widget_w: int = 0, widget_h: int = 0) -> None:
        if self.defn.clear_event is not None and self.defn.clear_event.value:
            self._buffer = ''

        if self._active and self._held_key is not None:
            now = time.monotonic()
            while now >= self._next_repeat_time:
                self._apply_key_action(self._held_key, self._held_shift, self._held_ctrl)
                self._next_repeat_time += _KEY_REPEAT_INTERVAL
        elif self._held_key is not None and not self._active:
            self._held_key = None

        self._polygon.update()
        if self._text is not None:
            buf = self._buffer
            self._text.defn = _tw_replace(self._text.defn, text_fn=lambda ctx, b=buf: b)
            self._text.update()
        if self._preview_text is not None:
            self._preview_text.update()

        if self._base_phase == 'open' and not self._open_done:
            if self._polygon.phase_done() and (self._text is None or self._text.phase_done()):
                self._open_done = True
                self._recompute_and_apply()

        if self.defn.live_event_out is not None:
            self.defn.live_event_out.value = self._buffer

        w, h = max(1, widget_w), max(1, widget_h)
        self._polygon._dirty = True
        self._last_poly = self._polygon.get_polygon(w, h, self.cam_w, self.cam_h)

    def phase_done(self) -> bool:
        text_done = self._text.phase_done() if self._text is not None else True
        return self._polygon.phase_done() and text_done

    def draw(self, painter: QPainter, w: int, h: int, scale: float = 1.0) -> None:
        if self.hidden:
            return
        self._polygon.draw(painter, w, h, self.cam_w, self.cam_h)

        show_preview = (not self._buffer) and (not self._active) and self._preview_text is not None
        if show_preview:
            if not self._preview_text.hidden:
                text_scale = scale if self._preview_text.defn.uniform_scale else 1.0
                font  = self._preview_text.build_font(text_scale)
                label = self._preview_text.resolve_text(None)
                painter.setFont(font)
                painter.setPen(self._preview_text.cur_color)
                dx, dy = self._preview_text.resolve_pos(w, h, self.cam_w, self.cam_h, label, font, text_scale)
                painter.drawText(dx, dy, label)
                painter.setPen(Qt.NoPen)
            return

        if self._text is not None and not self._text.hidden:
            display = self._resolve_display_text(w, h)
            text_scale = scale if self._text.defn.uniform_scale else 1.0
            font = self._text.build_font(text_scale)
            fm   = QFontMetrics(font)
            painter.setFont(font)
            painter.setPen(self._text.cur_color)
            dx, dy = self._text.resolve_pos(w, h, self.cam_w, self.cam_h, display, font, text_scale)
            painter.drawText(dx, dy, display)
            if self._active and int(time.monotonic() * 2) % 2 == 0:
                cursor_x = dx + fm.horizontalAdvance(display)
                cursor_y_top = dy - fm.ascent()
                cursor_y_bot = dy + fm.descent()
                pen = QPen(self._text.cur_color)
                pen.setWidthF(1.5)
                painter.setPen(pen)
                painter.drawLine(QPointF(cursor_x, cursor_y_top), QPointF(cursor_x, cursor_y_bot))
            painter.setPen(Qt.NoPen)









# ──────────────────────── GRAPH DEF ────────────────────────
 
@dataclass
class GraphDef:
    p1:              P                       = field(default_factory=P)
    p2:              P                       = field(default_factory=P)
    px1:             P                       = field(default_factory=P)
    px2:             P                       = field(default_factory=P)
    series:          List[SeriesDef]         = field(default_factory=list)
    max_time:        Any                     = 10.0
    start_display_time: Any                  = 0.0
    end_display_time:   Any                  = None
    value_range:     Tuple[float, float]     = (0.0, 0.0)
    value_color:     QColor                  = QColor(255, 255, 255, 255)
    ease_dur:        float                   = 0.3
    ease_type:       QEasingCurve.Type       = QEasingCurve.OutQuint
    dynamic_scale:   float                   = 0.0
    show_minmax:     bool                    = False
    show_step:       bool                    = False
    step_count:      Any                     = 0
    size_minmax:     float                   = 10.0
    size_step:       float                   = 9.0
    size_name:       float                   = 9.0
    label_align:     str                     = 'right'
    name_align:            str               = 'left'
    font_family:           str               = 'Oxanium SemiBold'
    bound_min_max_text:    bool              = True
    bound_name_text:       bool              = True
    auto_adjust_name_pos:  bool              = True
    stack:           Any                     = False
    update_interval: Any                     = 0.0
    hidden:          bool                    = False
    phase_override:  Optional[Any]           = None
    visible_threshold_x: float = 0.0
    visible_threshold_y: float = 0.0

@dataclass
class SeriesDef:
    value_fn:     Optional[Callable[[Any], Optional[float]]] = None
    data_fn:      Optional[Callable[[Any], List[float]]]     = None
    name:         str     = ''                # NEW
    color:        QColor  = field(default_factory=lambda: QColor(255, 255, 255, 255))
    outline_width:   float   = 1.5
    fill_opacity: float   = 0.0
    smooth:       bool    = False


class _SeriesState: 
    def __init__(self) -> None:
        self.waypoints: List[Tuple[float, float]] = []
        self.tip_committed: Optional[float] = None
        self.tip_display:   Optional[float] = None
        self.tip_start:     float           = 0.0
        self.tip_t0:        float           = 0.0
        self.pending_values:      List[float] = []
        self.last_data_fn_result: List[float] = []
 
class AnimatedGraph:
    def __init__(self, defn: GraphDef) -> None:
        self.defn   = defn
        self.hidden = defn.hidden
        self._series: List[_SeriesState] = [_SeriesState() for _ in defn.series]
        self._range_lo_tgt:   float = defn.value_range[0]
        self._range_hi_tgt:   float = defn.value_range[1]
        self._range_lo:       float = defn.value_range[0]
        self._range_hi:       float = defn.value_range[1]
        self._range_lo_start: float = defn.value_range[0]
        self._range_hi_start: float = defn.value_range[1]
        self._range_ease_t0:  float = 0.0
        self._range_easing:   bool  = False
        self._last_update_time: float = 0.0

        # cached per-frame resolved values (set at top of draw()/tick())
        self._max_time_cached:          float = _resolve_numeric_value(defn.max_time, 10.0)
        self._start_display_time:       float = 0.0
        self._end_display_time:         float = self._max_time_cached
        self._stack_cached:             bool  = False
        self._update_interval_cached:  float = _resolve_numeric_value(defn.update_interval, 0.0)

        # ── open/close fade state ──────────────────────────────────
        self._base_phase:          str   = ''
        self._fade_from:           float = 0.0
        self._fade_to:             float = 0.0
        self._fade_t0:             float = 0.0
        self._fade_dur:            float = 0.5
        self._last_override_phase: str   = ''

    def set_phase(self, phase: str) -> None:
        if phase not in ('open', 'close'):
            return
        if phase == self._base_phase:
            return
        self._base_phase = phase
        now = time.monotonic()
        self._fade_from = self._current_fade(now)
        self._fade_to   = 1.0 if phase == 'open' else 0.0
        self._fade_t0   = now

    def _current_fade(self, now: float) -> float:
        if self._fade_dur <= 0.0:
            return self._fade_to
        t = (now - self._fade_t0) / self._fade_dur
        t = max(0.0, min(1.0, t))
        v = _ease(t, QEasingCurve.OutQuint)
        return self._fade_from + (self._fade_to - self._fade_from) * v

    def _screen_rect(self, ww: int, wh: int) -> Tuple[float, float, float, float]:
        d  = self.defn
        x1 = d.p1.x * ww + d.px1.x
        y1 = d.p1.y * wh + d.px1.y
        x2 = d.p2.x * ww + d.px2.x
        y2 = d.p2.y * wh + d.px2.y
        return x1, y1, x2 - x1, y2 - y1

    def _refresh_time_window(self) -> None:
        d = self.defn
        self._max_time_cached = max(0.0001, _resolve_numeric_value(d.max_time, 10.0))
        s = _resolve_numeric_value(d.start_display_time, 0.0)
        if d.end_display_time is None:
            e = self._max_time_cached
        else:
            e = _resolve_numeric_value(d.end_display_time, self._max_time_cached)
        if s > e:
            s, e = e, s
        self._start_display_time = s
        self._end_display_time   = e
        self._stack_cached = _resolve_bool_value(d.stack)
        self._update_interval_cached = max(0.0, _resolve_numeric_value(d.update_interval, 0.0))

    def _time_to_x(self, abs_t: float, now: float, left: float, width: float) -> float:
        span = self._end_display_time - self._start_display_time
        if span <= 0:
            return left + width
        left_time = now - self._end_display_time
        return left + (abs_t - left_time) / span * width

    def _x_to_time(self, x: float, now: float, left: float, width: float) -> float:
        span = self._end_display_time - self._start_display_time
        if span <= 0 or width <= 0:
            return now - self._start_display_time
        left_time = now - self._end_display_time
        frac = (x - left) / width
        return left_time + frac * span

    def _value_to_y(self, value: float, top: float, height: float, lo: float, hi: float) -> float:
        ratio = (value - lo) / (hi - lo) if hi != lo else 0.5
        return top + height * (1.0 - max(0.0, min(1.0, ratio)))

    @property
    def _max_time(self) -> float:
        return self._max_time_cached

    def _tip_display_value(self, st: _SeriesState, now: float) -> Optional[float]:
        if st.tip_committed is None:
            return None
        if st.tip_display is None:
            return st.tip_committed
        elapsed = now - st.tip_t0
        dur     = self.defn.ease_dur
        if dur <= 0.0 or elapsed >= dur:
            return st.tip_committed
        v = _ease(elapsed / dur, self.defn.ease_type)
        return st.tip_start + (st.tip_committed - st.tip_start) * v

    def _push_value(self, st: _SeriesState, value: float, now: float) -> None:
        if st.tip_committed is None:
            st.tip_committed = value
            st.tip_display   = value
            st.tip_start     = value
            st.tip_t0        = now
            st.waypoints.append((now, value))
            return

        cur = self._tip_display_value(st, now)
        st.tip_start     = cur if cur is not None else st.tip_committed
        st.tip_display   = st.tip_start
        st.tip_committed = value
        st.tip_t0        = now

        st.waypoints.append((now, value))
        self._prune(st, now)

    def _prune(self, st: _SeriesState, now: float) -> None:
        cutoff  = now - max(self._max_time, self._end_display_time)
        outside = [i for i, (t, _) in enumerate(st.waypoints) if t < cutoff]
        if len(outside) > 1:
            st.waypoints = st.waypoints[outside[-1]:]

    def _step_value_at_time(self, st: _SeriesState, query_t: float, now: float) -> float:
        if st.tip_committed is None:
            return 0.0
        wps = st.waypoints
        if not wps:
            return st.tip_committed
        if query_t >= wps[-1][0]:
            return st.tip_committed
        if query_t <= wps[0][0]:
            return wps[0][1]
        for i in range(len(wps) - 1):
            if wps[i][0] <= query_t < wps[i + 1][0]:
                return wps[i][1]
        return wps[-1][1]

    def _step_value_at_x(self, st, now, rx, rw, x):
        query_t = self._x_to_time(x, now, rx, rw)
        v = self._value_at_time(st, query_t, now)
        if v is None:
            v = 0.0
        return max(0.0, v)

    def _compute_target_range(self, now: float) -> Tuple[float, float]:
        d            = self.defn
        base_lo, base_hi = d.value_range
        step         = d.dynamic_scale

        if self._stack_cached:
            all_times: set = {now}
            for st in self._series:
                for abs_t, _ in st.waypoints:
                    all_times.add(abs_t)
            sums = [
                sum(max(0.0, self._step_value_at_time(st, t, now))
                    for st in self._series)
                for t in all_times
            ]
            raw_lo = min(sums) if sums else base_lo
            raw_hi = max(sums) if sums else base_hi
        else:
            values: List[float] = []
            for st in self._series:
                values.extend(v for _, v in st.waypoints)
                if st.tip_committed is not None:
                    values.append(st.tip_committed)
            raw_lo = min(values) if values else base_lo
            raw_hi = max(values) if values else base_hi

        if step > 0:
            new_lo = _math.floor(raw_lo / step) * step
            new_hi = _math.ceil(raw_hi  / step) * step
        else:
            new_lo, new_hi = raw_lo, raw_hi

        return (min(new_lo, base_lo), max(new_hi, base_hi))

    def _update_dynamic_range(self, now: float) -> None:
        lo, hi = self._compute_target_range(now)
        if lo == self._range_lo_tgt and hi == self._range_hi_tgt:
            return
        cur_lo, cur_hi       = self._effective_range_eased(now)
        self._range_lo_start = cur_lo
        self._range_hi_start = cur_hi
        self._range_lo_tgt   = lo
        self._range_hi_tgt   = hi
        self._range_ease_t0  = now
        self._range_easing   = True

    def _effective_range_eased(self, now: float) -> Tuple[float, float]:
        if self.defn.dynamic_scale == 0.0:
            return self.defn.value_range
        if not self._range_easing:
            return (self._range_lo, self._range_hi)
        elapsed = now - self._range_ease_t0
        dur     = self.defn.ease_dur
        if dur <= 0.0 or elapsed >= dur:
            self._range_lo     = self._range_lo_tgt
            self._range_hi     = self._range_hi_tgt
            self._range_easing = False
            return (self._range_lo, self._range_hi)
        v  = _ease(elapsed / dur, self.defn.ease_type)
        lo = self._range_lo_start + (self._range_lo_tgt - self._range_lo_start) * v
        hi = self._range_hi_start + (self._range_hi_tgt - self._range_hi_start) * v
        self._range_lo = lo
        self._range_hi = hi
        return (lo, hi)

    def _build_pts(self, st: _SeriesState, now: float, rx: float, ry: float, rw: float, rh: float, lo: float, hi: float) -> List[QPointF]:
        if st.tip_committed is None:
            return []

        left_time  = now - self._end_display_time
        right_time = now - self._start_display_time

        def to_pt(t: float, v: float) -> QPointF:
            return QPointF(self._time_to_x(t, now, rx, rw), self._value_to_y(v, ry, rh, lo, hi))

        pts: List[QPointF] = []

        left_val = self._value_at_time(st, left_time, now)
        if left_val is None:
            left_val = st.waypoints[0][1] if st.waypoints else st.tip_committed
        pts.append(to_pt(left_time, left_val))

        for t, v in st.waypoints:
            if left_time < t < right_time:
                pts.append(to_pt(t, v))

        if self._start_display_time <= 0.0:
            tip_val = self._tip_display_value(st, now)
            if tip_val is None:
                tip_val = st.tip_committed
            pts.append(to_pt(right_time, tip_val))
        else:
            right_val = self._value_at_time(st, right_time, now)
            if right_val is None:
                right_val = st.tip_committed
            pts.append(to_pt(right_time, right_val))

        return pts

    def _collect_x_boundaries(self, now: float, rx: float, rw: float) -> List[float]:
        left_time  = now - self._end_display_time
        right_time = now - self._start_display_time
        xs: set = {rx, rx + rw}
        for st in self._series:
            for abs_t, _ in st.waypoints:
                if left_time <= abs_t <= right_time:
                    xs.add(self._time_to_x(abs_t, now, rx, rw))
        return sorted(xs)

    def _build_stacked_pts(self, now: float, rx: float, ry: float, rw: float, rh: float, lo: float, hi: float) -> List[List[QPointF]]:
        xs       = self._collect_x_boundaries(now, rx, rw)
        n_ser    = len(self._series)
        bottom_y = ry + rh
        span     = hi - lo
        ppu      = rh / span if span != 0 else 0.0

        tops: List[List[float]] = [[] for _ in range(n_ser)]
        for x in xs:
            cum_px = 0.0
            for si, st in enumerate(self._series):
                v = self._step_value_at_x(st, now, rx, rw, x)
                cum_px += v * ppu
                tops[si].append(bottom_y - cum_px)

        return [
            [QPointF(xs[xi], tops[si][xi]) for xi in range(len(xs))]
            for si in range(n_ser)
        ]

    def _value_at_time(self, st: _SeriesState, query_t: float, now: float) -> Optional[float]:
        if st.tip_committed is None:
            return None
        wps = st.waypoints
        if not wps:
            return st.tip_committed if query_t >= st.tip_t0 else None
        if query_t <= wps[0][0]:
            return wps[0][1]
        if query_t >= wps[-1][0]:
            return st.tip_committed if query_t >= st.tip_t0 else wps[-1][1]
        for i in range(len(wps) - 1):
            t0, v0 = wps[i]
            t1, v1 = wps[i + 1]
            if t0 <= query_t <= t1:
                frac = (query_t - t0) / (t1 - t0) if t1 > t0 else 0.0
                return v0 + (v1 - v0) * frac
        return wps[-1][1]

    def tick(self, now: float) -> None:
        d = self.defn
        self._refresh_time_window()
        for st in self._series:
            self._prune(st, now)
        if d.dynamic_scale != 0.0:
            self._update_dynamic_range(now)
        if self._update_interval_cached > 0.0 and now - self._last_update_time >= self._update_interval_cached:
            self._last_update_time = now
            for sd, st in zip(d.series, self._series):
                if st.pending_values:
                    val = sum(st.pending_values) / len(st.pending_values)
                    st.pending_values.clear()
                elif st.tip_committed is not None:
                    val = st.tip_committed
                else:
                    continue
                self._push_value(st, val, now)

    def _ingest(self, ctx: Any, now: float) -> None:
        d = self.defn
        for sd, st in zip(d.series, self._series):
            if sd.value_fn is not None:
                try:    raw = sd.value_fn(ctx)
                except: raw = None
                if raw is not None:
                    if self._update_interval_cached > 0.0:
                        st.pending_values.append(float(raw))
                    else:
                        self._push_value(st, float(raw), now)
            elif sd.data_fn is not None:
                try:    samples = sd.data_fn(ctx) or []
                except: samples = []
                if samples != st.last_data_fn_result:
                    if not st.last_data_fn_result and samples:
                        n = len(samples)
                        for i, val in enumerate(samples):
                            fake_t = now - self._max_time * (1.0 - (i + 1) / n)
                            st.waypoints.append((fake_t, float(val)))
                        last = float(samples[-1])
                        st.tip_committed = last
                        st.tip_display   = last
                        st.tip_start     = last
                        st.tip_t0        = now
                    else:
                        new_vals = samples[len(st.last_data_fn_result):]
                        if self._update_interval_cached > 0.0:
                            st.pending_values.extend(float(v) for v in new_vals)
                        else:
                            for val in new_vals:
                                self._push_value(st, float(val), now)
                    st.last_data_fn_result = list(samples)

    def _fade_color(self, c: QColor, alpha_mult: float) -> QColor:
        out = QColor(c)
        out.setAlpha(int(c.alpha() * alpha_mult))
        return out

    def _draw_labels(self, painter: QPainter, rx: float, ry: float, rw: float, rh: float, alpha_mult: float) -> None:
        d = self.defn

        show_minmax = d.show_minmax
        show_step  = d.show_step
        step_count  = int(d.step_count() if callable(d.step_count) else d.step_count)
        size_minmax = d.size_minmax
        size_step   = d.size_step

        if not show_minmax and (not show_step or step_count <= 0):
            return

        if d.dynamic_scale != 0.0:
            lo = self._range_lo_tgt
            hi = self._range_hi_tgt
        else:
            lo, hi = d.value_range

        base_color = self._fade_color(d.value_color, alpha_mult)

        def _fmt(v: float) -> str:
            if v == int(v):
                return str(int(v))
            mag = abs(v)
            if mag == 0:
                return '0'
            decimals = max(0, 2 - int(_math.floor(_math.log10(mag)))) if mag >= 1 else 3
            return f'{v:.{decimals}f}'.rstrip('0').rstrip('.')

        def _label_color():
            c = QColor(base_color)
            c.setAlpha(int(c.alpha() * (180 / 255)))
            return c

        def _make_label_font(font_size: float):
            f = QFont()
            f.setFamily(d.font_family)
            f.setPointSizeF(max(0.5, font_size))
            return f, QFontMetrics(f)

        def _draw_at(text: str, font_size: float, y_center: float, align: str, bound: Optional[str]) -> None:
            f, fm = _make_label_font(font_size)
            if bound == 'below':      # entire text must sit below y_center (top of text at y_center)
                y = int(y_center + fm.ascent())
            elif bound == 'above':    # entire text must sit above y_center (bottom of text at y_center)
                y = int(y_center - fm.descent())
            else:
                y = int(y_center + fm.ascent() * 0.5 - fm.descent() * 0.5)
            x = int(rx - 4 - fm.horizontalAdvance(text)) if align == 'right' else int(rx + 4)
            painter.setFont(f)
            painter.setPen(_label_color())
            painter.drawText(x, y, text)
            painter.setPen(Qt.NoPen)

        align = d.label_align

        if show_minmax:
            _draw_at(_fmt(hi), size_minmax, ry,      align, 'below' if d.bound_min_max_text else None)
            _draw_at(_fmt(lo), size_minmax, ry + rh,  align, 'above' if d.bound_min_max_text else None)

        if show_step and step_count > 0:
            for i in range(1, step_count + 1):
                ratio = i / (step_count + 1)
                _draw_at(_fmt(lo + ratio * (hi - lo)), size_step, ry + rh * (1.0 - ratio), align, None)

    def _draw_series_names(self, painter: QPainter, d: 'GraphDef', tip_points: List[Optional[QPointF]], alpha_mult: float, ry: float, rh: float) -> None:
        f = QFont()
        f.setFamily(d.font_family)
        f.setPointSizeF(max(0.5, d.size_name))
        fm = QFontMetrics(f)
        label_height = fm.height()
        half_h = (fm.ascent() + fm.descent()) / 2.0

        entries = [(i, sd, tp) for i, (sd, tp) in enumerate(zip(d.series, tip_points)) if sd.name and tp is not None]
        if not entries:
            return

        min_y = ry + half_h
        max_y = ry + rh - half_h
        bounds_valid = d.bound_name_text and min_y <= max_y

        def _clamp(v: float) -> float:
            return max(min_y, min(max_y, v))

        if d.auto_adjust_name_pos and len(entries) > 1:
            order = sorted(range(len(entries)), key=lambda k: entries[k][2].y())
            desired = [entries[k][2].y() for k in order]
            if bounds_valid:
                desired = [_clamp(v) for v in desired]

            adjusted = self._declutter_positions(desired, label_height * 1.1)

            if bounds_valid and adjusted:
                lo_over = min_y - adjusted[0]
                hi_over = adjusted[-1] - max_y
                if lo_over > 0 and hi_over > 0:
                    shift = (lo_over - hi_over) / 2.0   # can't fully fit either side — split the difference
                elif lo_over > 0:
                    shift = lo_over
                elif hi_over > 0:
                    shift = -hi_over
                else:
                    shift = 0.0
                if shift != 0.0:
                    adjusted = [v + shift for v in adjusted]
                adjusted = [_clamp(v) for v in adjusted]

            y_for_entry = {}
            for pos_in_order, k in enumerate(order):
                y_for_entry[k] = adjusted[pos_in_order]
        else:
            y_for_entry = {k: entries[k][2].y() for k in range(len(entries))}
            if bounds_valid:
                y_for_entry = {k: _clamp(v) for k, v in y_for_entry.items()}

        painter.setFont(f)
        for k, (si, sd, tip_pt) in enumerate(entries):
            color = self._fade_color(sd.color, alpha_mult)
            label_y = y_for_entry[k]
            ly = int(label_y + fm.ascent() * 0.5 - fm.descent() * 0.5)
            if d.name_align == 'left':
                lx = int(tip_pt.x() - 4 - fm.horizontalAdvance(sd.name))
            else:
                lx = int(tip_pt.x() + 4)
            painter.setPen(color)
            painter.drawText(lx, ly, sd.name)
        painter.setPen(Qt.NoPen)

    def draw(self, painter: QPainter, widget_w: int, widget_h: int, ctx: Any = None, cam_w: int = MONITOR_RESOLUTIONS[0][0], cam_h: int = MONITOR_RESOLUTIONS[0][1]) -> None:
        if self.hidden:
            return

        now = time.monotonic()
        d   = self.defn

        self._refresh_time_window()

        alpha_mult = self._current_fade(now)
        if alpha_mult <= 0.0:
            return

        self._ingest(ctx, now)

        rx, ry, rw, rh = self._screen_rect(widget_w, widget_h)
        if rw <= 0 or rh <= 0:
            return

        lo, hi   = self._effective_range_eased(now)
        bottom_y = ry + rh

        if self._stack_cached:
            all_pts = self._build_stacked_pts(now, rx, ry, rw, rh, lo, hi)
        else:
            all_pts = [self._build_pts(st, now, rx, ry, rw, rh, lo, hi) for st in self._series]

        painter.save()
        painter.setClipRect(int(rx), int(ry), int(rw + 1), int(rh + 1))

        tip_points: List[Optional[QPointF]] = [None] * len(d.series)

        for si, (sd, st) in enumerate(zip(d.series, self._series)):
            pts = all_pts[si]
            if not pts:
                continue

            series_color = self._fade_color(sd.color, alpha_mult)

            if sd.fill_opacity > 0.0:
                fill_color = QColor(sd.color)
                fill_color.setAlphaF(sd.fill_opacity * alpha_mult)
                fill_poly  = QPolygonF()
                if self._stack_cached and si > 0:
                    for pt in pts:
                        fill_poly.append(pt)
                    for pt in reversed(all_pts[si - 1]):
                        fill_poly.append(pt)
                else:
                    fill_poly.append(QPointF(pts[0].x(), bottom_y))
                    for pt in pts:
                        fill_poly.append(pt)
                    fill_poly.append(QPointF(pts[-1].x(), bottom_y))
                painter.setPen(Qt.NoPen)
                painter.setBrush(fill_color)
                painter.drawPolygon(fill_poly)
                painter.setBrush(Qt.NoBrush)

            if sd.outline_width > 0.0:
                pen = QPen(series_color)
                pen.setWidthF(sd.outline_width)
                pen.setCapStyle(Qt.RoundCap)
                pen.setJoinStyle(Qt.RoundJoin)
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                for i in range(len(pts) - 1):
                    painter.drawLine(pts[i], pts[i + 1])
                painter.setPen(Qt.NoPen)

            tip_points[si] = pts[-1]

        painter.restore()
        self._draw_labels(painter, rx, ry, rw, rh, alpha_mult)
        self._draw_series_names(painter, d, tip_points, alpha_mult, ry, rh)
    
    def _declutter_positions(self, desired: List[float], min_gap: float) -> List[float]:
        n = len(desired)
        if n == 0:
            return []
        stack = [{'sum': d, 'count': 1} for d in desired]
        i = 1
        while i < len(stack):
            c1, c2 = stack[i - 1], stack[i]
            avg1 = c1['sum'] / c1['count']
            avg2 = c2['sum'] / c2['count']
            required = min_gap * (c1['count'] + c2['count']) / 2.0
            if avg2 - avg1 < required:
                merged = {'sum': c1['sum'] + c2['sum'], 'count': c1['count'] + c2['count']}
                stack[i - 1:i + 1] = [merged]
                i = max(1, i - 1)
            else:
                i += 1
        positions: List[float] = []
        for cluster in stack:
            avg = cluster['sum'] / cluster['count']
            k = cluster['count']
            start = avg - min_gap * (k - 1) / 2.0
            for j in range(k):
                positions.append(start + j * min_gap)
        return positions

# ──────────────────────── PIE DEF ────────────────────────

@dataclass
class PieDef:
    p1:         P                    = field(default_factory=P)
    p2:         P                    = field(default_factory=P)
    px1:        P                    = field(default_factory=P)
    px2:        P                    = field(default_factory=P)
    names:      List[str]            = field(default_factory=list)
    value_fns:  List[Callable[[Any], Optional[float]]] = field(default_factory=list)
    colors:     List[QColor]         = field(default_factory=list)
    border_width:  float             = 0.0
    fill_opacity:  float             = 1.0
    direction:  str                  = 'horizontal'   # 'horizontal' or 'vertical'
    size_label: float                = 9.0
    size_name:  float                = 9.0
    ease_dur:   float                = 0.3
    ease_type:  QEasingCurve.Type    = QEasingCurve.OutQuint
    hidden:     bool                 = False
    visible_threshold_x: float = 0.0
    visible_threshold_y: float = 0.0

class AnimatedPie:
    def __init__(self, defn: PieDef) -> None:
        self.defn   = defn
        self.hidden = defn.hidden
        
        n           = len(defn.names)
        self._raw_values:  List[Optional[float]] = [None] * n
        self._cur_ratios:  List[float]           = [1.0 / n] * n
        self._tgt_ratios:  List[float]           = [1.0 / n] * n
        self._start_ratios: List[float]          = [1.0 / n] * n
        self._ease_t0:      float                = 0.0
        self._easing:       bool                 = False

    def _screen_rect(self, ww: int, wh: int) -> Tuple[float, float, float, float]:
        d  = self.defn
        x1 = d.p1.x * ww + d.px1.x
        y1 = d.p1.y * wh + d.px1.y
        x2 = d.p2.x * ww + d.px2.x
        y2 = d.p2.y * wh + d.px2.y
        return x1, y1, x2 - x1, y2 - y1

    def _recompute_targets(self) -> None:
        vals   = [v for v in self._raw_values if v is not None and v > 0]
        n      = len(self.defn.names)
        total  = sum(v for v in self._raw_values if v is not None and v > 0)

        if total <= 0:
            new_tgt = [1.0 / n] * n
        else:
            new_tgt = []
            for v in self._raw_values:
                if v is not None and v > 0:
                    new_tgt.append(v / total)
                else:
                    new_tgt.append(0.0)

        if new_tgt == self._tgt_ratios:
            return

        now = time.monotonic()
        if self._easing:
            elapsed = now - self._ease_t0
            dur     = self.defn.ease_dur
            t       = min(1.0, elapsed / dur) if dur > 0 else 1.0
            v       = _ease(t, self.defn.ease_type)
            self._start_ratios = [s + (tgt - s) * v for s, tgt in zip(self._start_ratios, self._tgt_ratios)]
        else:
            self._start_ratios = list(self._cur_ratios)

        self._tgt_ratios = new_tgt
        self._ease_t0    = now
        self._easing     = True

    def update(self, ctx: Any) -> None:
        changed = False
        for i, fn in enumerate(self.defn.value_fns):
            try:
                raw = fn(ctx)
            except Exception:
                raw = None
            if raw != self._raw_values[i]:
                self._raw_values[i] = raw
                changed = True
        if changed:
            self._recompute_targets()

    def _advance_ease(self, now: float) -> None:
        if not self._easing:
            return
        elapsed = now - self._ease_t0
        dur     = self.defn.ease_dur
        if dur <= 0.0 or elapsed >= dur:
            self._cur_ratios = list(self._tgt_ratios)
            self._easing     = False
            return
        t = elapsed / dur
        v = _ease(t, self.defn.ease_type)
        self._cur_ratios = [s + (tgt - s) * v for s, tgt in zip(self._start_ratios, self._tgt_ratios)]

    def draw(self, painter: QPainter, widget_w: int, widget_h: int, cam_w: int = MONITOR_RESOLUTIONS[0][0], cam_h: int = MONITOR_RESOLUTIONS[0][1]) -> None:
        if self.hidden:
            return

        now = time.monotonic()
        self._advance_ease(now)

        d = self.defn
        rx, ry, rw, rh = self._screen_rect(widget_w, widget_h)
        if rw <= 0 or rh <= 0:
            return

        n          = len(d.names)
        ratios     = self._cur_ratios
        horizontal = d.direction == 'horizontal'
        total_span = rw if horizontal else rh

        cursor = 0.0
        segments: List[Tuple[float, float, float, float, int]] = []
        for i, ratio in enumerate(ratios):
            span = total_span * ratio
            if horizontal:
                segments.append((rx + cursor, ry, span, rh, i))
            else:
                segments.append((rx, ry + cursor, rw, span, i))
            cursor += span

        painter.setPen(Qt.NoPen)
        for x, y, w, h, i in segments:
            if w < 0.5 or h < 0.5:
                continue
            color = QColor(d.colors[i] if i < len(d.colors) else QColor(255, 255, 255))
            color.setAlphaF(d.fill_opacity)
            painter.setBrush(color)
            painter.drawRect(QRectF(x, y, w, h))
        painter.setBrush(Qt.NoBrush)

        pct_font = QFont()
        pct_font.setPointSizeF(max(0.5, d.size_label))
        pct_fm = QFontMetrics(pct_font)
        painter.setFont(pct_font)

        for x, y, w, h, i in segments:
            if w < 0.5 or h < 0.5:
                continue
            pct   = ratios[i] * 100.0
            label = f'{pct:.1f}%'
            tw    = pct_fm.horizontalAdvance(label)
            th    = pct_fm.height()

            fits  = (tw + 8 <= w) if horizontal else (th + 4 <= h)
            if not fits:
                continue

            lx = int(x + (w - tw) / 2)
            ly = int(y + h / 2 + pct_fm.ascent() * 0.5 - pct_fm.descent() * 0.5)

            color = d.colors[i] if i < len(d.colors) else QColor(255, 255, 255)
            painter.setPen(color)
            painter.drawText(lx, ly, label)

        name_font = QFont()
        name_font.setPointSizeF(max(0.5, d.size_name))
        name_fm = QFontMetrics(name_font)
        painter.setFont(name_font)

        for x, y, w, h, i in segments:
            if w < 0.5 or h < 0.5:
                continue
            name = d.names[i] if i < len(d.names) else ''
            if not name:
                continue

            color = d.colors[i] if i < len(d.colors) else QColor(255, 255, 255)
            painter.setPen(color)

            nx = int(x)
            ny = int(y - name_fm.descent() - 2)
            painter.drawText(nx, ny, name)

        painter.setPen(Qt.NoPen)

        if d.border_width > 0.0:
            half = d.border_width / 2.0
            for x, y, w, h, i in segments:
                if w < 0.5 or h < 0.5:
                    continue
                color = d.colors[i] if i < len(d.colors) else QColor(255, 255, 255)
                pen = QPen(color)
                pen.setWidthF(d.border_width * 2.0)
                pen.setJoinStyle(Qt.MiterJoin)
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                painter.save()
                painter.setClipRect(QRectF(x, y, w, h))
                painter.drawRect(QRectF(x, y, w, h))
                painter.restore()
            painter.setPen(Qt.NoPen)

# ──────────────────────── WINDOW DEF ────────────────────────
@dataclass
class WindowDef:
    p1:                     P                       = field(default_factory=P)
    p2:                     P                       = field(default_factory=P)
    px1:                    P                       = field(default_factory=P)
    px2:                    P                       = field(default_factory=P)
    force_open:             bool                    = False
    force_close:            bool                    = False
    phase_event:            Any                     = None
    hidden_event:           Optional[Any]           = None
    phase_fn:               Optional[Callable[str]] = None
    phases:                 Dict[str, Phase]        = field(default_factory=dict)
    listener_defs:          List[EventListener]     = field(default_factory=list)
    polygon_defs:           List[PolygonDef]        = field(default_factory=list)
    arc_defs:               List[ArcDef]            = field(default_factory=list)
    text_defs:              List[TextDef]           = field(default_factory=list)
    graph_defs:             List[GraphDef]          = field(default_factory=list)
    pie_defs:               List[PieDef]            = field(default_factory=list)
    slider_defs:            List[SliderDef]         = field(default_factory=list)
    button_defs:            List[ButtonDef]         = field(default_factory=list)
    textbox_defs:           List[TextboxDef]        = field(default_factory=list)
    sub_windows:            List['WindowDef']       = field(default_factory=list)
    use_parent_close_phase: bool                    = True
    draggable:              bool                    = False
    drag_boundary_p1:       P                       = field(default_factory=P)
    drag_boundary_p2:       P                       = field(default_factory=lambda: P(1.0, 1.0))
    drag_boundary_px1:      P                       = field(default_factory=P)
    drag_boundary_px2:      P                       = field(default_factory=P)
    scalable:               bool                    = False
    min_scale_w:            float                   = 0.05
    min_scale_h:            float                   = 0.05
    scale_edge_px:          float                   = 16.0
    grid_snap:              bool                    = True
    grid_snap_pixel:        bool                    = False
    grid_snap_x:            int                     = 19
    grid_snap_y:            int                     = 11
    force_boundary:         bool                    = False
    sticky_boundary:        bool                    = False
    spawn_event:            Optional[EventDef]      = None
    spawn_static_values:    List[Any]               = field(default_factory=list)
    spawn_event_group:      Optional[str]           = None
    spawn_tick_increment:   bool                    = False
    spawn_delete_threshold: int                     = 1
    spawn_limit:            int                     = 100
    deselect_event:         Optional[EventDef]      = None
    select_event:           Optional[EventDef]      = None
    spawn_name_event_fn:    Optional[Callable[[str], EventDef]] = None
    on_spawn:               Optional[Callable[[str, List[Any]], None]] = None
    on_despawn:             Optional[Callable[[str], None]]            = None
    export_p1:              Optional[EventDef]      = None
    export_p2:              Optional[EventDef]      = None
    export_px1:             Optional[EventDef]      = None
    export_px2:             Optional[EventDef]      = None
    ignore_click_consume: bool = False
    ignore_mouse_event:   Any  = None

@dataclass
class WindowTween:
    p1:   Optional[P]          = None
    p2:   Optional[P]          = None
    px1:  P                    = None
    px2:  P                    = None
    start: float               = 0.0
    dur:   float               = 0.5
    ease:  QEasingCurve.Type   = QEasingCurve.OutQuint
    prev_phase: Optional[str]  = None

class AnimatedWindow:
    def __init__(self, defn: WindowDef, cam_w: int = MONITOR_RESOLUTIONS[0][0], cam_h: int = MONITOR_RESOLUTIONS[0][1]) -> None:
        self.defn   = defn
        _animated_window_registry[id(defn)] = self
        self.cam_w  = cam_w
        self.cam_h  = cam_h

        self._win_retrigger_snapshots: Dict[str, Any] = {}

        self._sub_windows: List[AnimatedWindow] = [AnimatedWindow(d, cam_w, cam_h) for d in defn.sub_windows]
        self._polygons  = [AnimatedPolygon(d) for d in defn.polygon_defs]
        self._arcs      = [AnimatedArc(d)     for d in defn.arc_defs]
        self._texts     = [AnimatedText(d)    for d in defn.text_defs]
        self._graphs    = [AnimatedGraph(d)   for d in defn.graph_defs]
        self._pies      = [AnimatedPie(d)     for d in defn.pie_defs]
        self._sliders   = [SliderGroup(d, cam_w, cam_h) for d in defn.slider_defs]
        self._buttons   = [AnimatedButton(d, cam_w, cam_h) for d in defn.button_defs]
        self._textboxes = [AnimatedTextbox(d, cam_w, cam_h) for d in defn.textbox_defs]
        self._listeners = list(defn.listener_defs)

        for btn, bd in zip(self._buttons, defn.button_defs):
            if bd.phase_override is not None:
                ov = bd.phase_override
                val = ov.value if hasattr(ov, 'value') else (ov() if callable(ov) else ov)
                phase = str(val) if val is not None else ''
                if phase not in ('open', 'close'):
                    phase = 'close'
                btn._last_override_phase = phase
                btn._set_base_phase(phase)
        
        for tb, td in zip(self._textboxes, defn.textbox_defs):
            if td.phase_override is not None:
                ov = td.phase_override
                val = ov.value if hasattr(ov, 'value') else (ov() if callable(ov) else ov)
                phase = str(val) if val is not None else ''
                if phase not in ('open', 'close'):
                    phase = 'close'
                tb._last_override_phase = phase
                tb._set_base_phase(phase)
        
        for g, gd in zip(self._graphs, defn.graph_defs):
            if gd.phase_override is not None:
                ov = gd.phase_override
                val = ov.value if hasattr(ov, 'value') else (ov() if callable(ov) else ov)
                phase = str(val) if val is not None else ''
                if phase not in ('open', 'close'):
                    phase = 'close'
                g._last_override_phase = phase
                g.set_phase(phase)

        self._btn_grid: Dict[tuple, List[int]] = {}
        self._btn_bounds: List[Optional[tuple]] = [None] * len(self._buttons)
        self._grid_cell_size: int = 64
        self._grid_w: int = 0
        self._grid_h: int = 0
        self._last_mouse_lx: float = -1.0
        self._last_mouse_ly: float = -1.0

        self._held_keys: set = set()

        self._dragging_slider: Optional[SliderGroup] = None
        self._cur_phase: str = ''

        self._cur_p1  = P(defn.p1.x,  defn.p1.y)
        self._cur_p2  = P(defn.p2.x,  defn.p2.y)
        self._cur_px1 = P(defn.px1.x, defn.px1.y)
        self._cur_px2 = P(defn.px2.x, defn.px2.y)
        self._s_p1    = self._cur_p1
        self._s_p2    = self._cur_p2
        self._s_px1   = self._cur_px1
        self._s_px2   = self._cur_px2
        self._win_tweens: List[WindowTween] = []
        self._win_timer   = QElapsedTimer()
        self._win_timer.restart()
        self._win_idx: int = 0
        self._win_prev_phase: str = ''
        self._parent_w: int = 0
        self._parent_h: int = 0

        for sl in self._sliders:
            sl.init_value(None)
        self._broadcast('open')

        if defn.phase_event is not None and defn.phase_event is not GROUP_EVENT:
            if isinstance(defn.phase_event, (list, tuple)):
                if not defn.phase_event[0].value:
                    defn.phase_event[0].value = 'open'
            else:
                if not defn.phase_event.value:
                    defn.phase_event.value = 'open'

        self._last_mouse_lx: float = -1.0
        self._last_mouse_ly: float = -1.0

        self._sys_fps_event:        Optional[EventDef] = None
        self._sys_mouse_event:      Optional[EventDef] = None
        self._sys_frame_time_event: Optional[EventDef] = None

        self._fps_samples:    collections.deque = collections.deque(maxlen=60)
        self._last_frame_time: float = 0.0

        self._dragging_window:  bool  = False
        self._drag_start_mx:    float = 0.0
        self._drag_start_my:    float = 0.0
        self._drag_start_p1x:   float = 0.0
        self._drag_start_p1y:   float = 0.0
        self._drag_start_px1x:  float = 0.0
        self._drag_start_px1y:  float = 0.0
        self._drag_start_p2x:   float = 0.0
        self._drag_start_p2y:   float = 0.0
        self._drag_start_px2x:  float = 0.0
        self._drag_start_px2y:  float = 0.0
        self._drag_parent_w: int = 0
        self._drag_parent_h: int = 0

        self._scaling_window:   bool  = False
        self._scale_edge:       str   = ''   # 'l', 'r', 't', 'b', 'tl', 'tr', 'bl', 'br'
        self._scale_start_mx:   float = 0.0
        self._scale_start_my:   float = 0.0
        self._scale_start_p1x:  float = 0.0
        self._scale_start_p1y:  float = 0.0
        self._scale_start_px1x: float = 0.0
        self._scale_start_px1y: float = 0.0
        self._scale_start_p2x:  float = 0.0
        self._scale_start_p2y:  float = 0.0
        self._scale_start_px2x: float = 0.0
        self._scale_start_px2y: float = 0.0

        self._snap_tween_active:  bool  = False
        self._sticky_sides:       set   = set()
        self._snap_tween_t0:      float = 0.0
        self._snap_tween_dur:     float = 0.5
        self._snap_from_p1x:      float = 0.0
        self._snap_from_p1y:      float = 0.0
        self._snap_from_p2x:      float = 0.0
        self._snap_from_p2y:      float = 0.0
        self._snap_to_p1x:        float = 0.0
        self._snap_to_p1y:        float = 0.0
        self._snap_to_p2x:        float = 0.0
        self._snap_to_p2y:        float = 0.0
        self._snap_from_px1x:     float = 0.0
        self._snap_from_px1y:     float = 0.0
        self._snap_from_px2x:     float = 0.0
        self._snap_from_px2y:     float = 0.0
        self._snap_to_px1x:       float = 0.0
        self._snap_to_px1y:       float = 0.0
        self._snap_to_px2x:       float = 0.0
        self._snap_to_px2y:       float = 0.0

        self._spawned:          List[_SpawnedInstance] = []
        self._last_ipw:         int   = 0
        self._last_iph:         int   = 0
        self._spawn_watched:    bool  = False

        if defn.spawn_event is not None:
            self.hidden = True
        else:
            self.hidden = False

        if defn.spawn_event is not None:
            defn.spawn_event._watchers.append(self._on_spawn_trigger)

        self._group_event:          Optional[EventDef] = None
        self._instance_phase_event: Optional[EventDef] = None
        self._statics: List[Any] = []

        self._last_screen_wx: float = 0.0
        self._last_screen_wy: float = 0.0
        self._last_screen_ww: float = 0.0
        self._last_screen_wh: float = 0.0

        self._force_open_active:  bool = False
        self._force_close_active: bool = False
        self._force_open_done:    bool = False
        self._prev_force_phase:   str  = ''
        self._force_open_pending: bool = defn.force_open
        self._force_open_triggered: bool = False

        if defn.spawn_event is None:
            initial_phase = 'open'
            if defn.phase_event is not None and defn.phase_event is not GROUP_EVENT:
                ev = defn.phase_event
                if isinstance(ev, (list, tuple)):
                    val = str(ev[0].value) if ev[0].value else 'open'
                else:
                    val = str(ev.value) if ev.value else 'open'
                initial_phase = val
            self._broadcast(initial_phase)
        else:
            self.hidden = True

    def _screen_rect(self, ww: int, wh: int) -> Tuple[float, float, float, float]:
        x1 = self._cur_p1.x  * ww + self._cur_px1.x
        y1 = self._cur_p1.y  * wh + self._cur_px1.y
        x2 = self._cur_p2.x  * ww + self._cur_px2.x
        y2 = self._cur_p2.y  * wh + self._cur_px2.y
        return x1, y1, x2 - x1, y2 - y1

    def _broadcast(self, phase: str) -> None:
        prev = self._cur_phase
        self._cur_phase = phase
        for p, pd in zip(self._polygons, self.defn.polygon_defs):
            if pd.phase_override is None:
                p.set_phase(phase)
        for a in self._arcs:
            a.set_phase(phase)
        for t, td in zip(self._texts, self.defn.text_defs):
            if td.phase_override is None:
                t.set_phase(phase)
        for sl  in self._sliders:  sl.set_phase(phase)
        for btn, bd in zip(self._buttons, self.defn.button_defs):
            if bd.phase_override is None and phase in ('open', 'close'):
                btn._set_base_phase(phase)
        for tb, td in zip(self._textboxes, self.defn.textbox_defs):
            if td.phase_override is None:
                tb._set_base_phase(phase)
        for g, gd in zip(self._graphs, self.defn.graph_defs):
            if gd.phase_override is None:
                g.set_phase(phase)
        for sw in self._sub_windows:
            if sw.defn.spawn_event is not None:
                continue
            if not _phase_key_exists(sw.defn.phases, phase):
                sw._broadcast(phase)
        wp = self.defn.phases.get(phase)
        if wp:
            self._win_tweens = [_resolve_tween_event_refs(tw) for tw in wp.tweens if tw.prev_phase is None or tw.prev_phase == prev]
            self._update_window_retrigger_snapshot(phase, wp)
        else:
            self._win_tweens = []
        self._win_idx        = 0
        self._win_prev_phase = prev
        self._s_p1  = self._cur_p1;  self._s_p2  = self._cur_p2
        self._s_px1 = self._cur_px1; self._s_px2 = self._cur_px2
        self._win_timer.restart()
    
    def _rebuild_btn_grid(self, ww: int, wh: int) -> None:
        cell = self._grid_cell_size
        self._btn_grid.clear()
        self._grid_w = ww
        self._grid_h = wh

        for i, btn in enumerate(self._buttons):
            poly = btn._last_poly
            if poly is None or poly.isEmpty():
                self._btn_bounds[i] = None
                continue

            xs = [pt.x() for pt in poly]
            ys = [pt.y() for pt in poly]
            x1, y1, x2, y2 = min(xs), min(ys), max(xs), max(ys)
            self._btn_bounds[i] = (x1, y1, x2, y2)

            cx0 = int(x1 // cell)
            cy0 = int(y1 // cell)
            cx1 = int(x2 // cell)
            cy1 = int(y2 // cell)
            for cx in range(cx0, cx1 + 1):
                for cy in range(cy0, cy1 + 1):
                    key = (cx, cy)
                    if key not in self._btn_grid:
                        self._btn_grid[key] = []
                    if i not in self._btn_grid[key]:
                        self._btn_grid[key].append(i)
    
    def _btn_candidates(self, lx: float, ly: float) -> List[int]:
        cell = self._grid_cell_size
        key  = (int(lx // cell), int(ly // cell))
        return self._btn_grid.get(key, [])

    def _poll_phase_event(self) -> None:
        ev = self._instance_phase_event or self.defn.phase_event
        if ev is None:
            return
        fn = self.defn.phase_fn
        if isinstance(ev, (list, tuple)):
            result = fn(*[e.value for e in ev]) if fn else str(ev[0].value)
        else:
            result = fn(ev.value) if fn else str(ev.value)
        if result is None:
            result = str(ev.value) if not isinstance(ev, (list,tuple)) else str(ev[0].value)

        if result != self._cur_phase:
            self._broadcast(result)
        else:
            phase_def = self.defn.phases.get(result)
            if phase_def is not None and getattr(phase_def, 'update_retrigger', False) and self._window_retrigger_changed(result, phase_def):
                self._broadcast(result)
    
    def _poll_force_phases(self) -> None:
        d = self.defn

        if d.force_open and not self._force_open_active and not self._force_open_done:
            self._force_open_active = True
            for p in self._polygons: p.set_phase('open')
            for t in self._texts:    t.set_phase('open')
            for a in self._arcs:     a.set_phase('open')

        if d.force_close and self._cur_phase == 'close' and self._prev_force_phase != 'close' and not self._force_close_active:
            self._force_close_active = True
            for p in self._polygons: p.set_phase('close')
            for t in self._texts:    t.set_phase('close')
            for a in self._arcs:     a.set_phase('close')

        self._prev_force_phase = self._cur_phase

        if self._force_open_active:
            if all(p.phase_done() for p in self._polygons) and all(t.phase_done() for t in self._texts):
                self._force_open_active = False
                self._force_open_done   = True

        if self._force_close_active:
            if all(p.phase_done() for p in self._polygons) and all(t.phase_done() for t in self._texts):
                self._force_close_active = False

    def _tick_win_tweens(self) -> None:
        tweens = self._win_tweens
        if not tweens or self._win_idx >= len(tweens):
            return
        elapsed = self._win_timer.elapsed() / 1000.0
        tw = tweens[self._win_idx]
        if elapsed < tw.start:
            return
        t = min(1.0, (elapsed - tw.start) / tw.dur) if tw.dur > 0 else 1.0
        v = _ease(t, tw.ease)

        if tw.p1 is not None:
            nx = self._s_p1.x + (tw.p1.x - self._s_p1.x) * v if tw.p1.x is not None else self._s_p1.x
            ny = self._s_p1.y + (tw.p1.y - self._s_p1.y) * v if tw.p1.y is not None else self._s_p1.y
            self._cur_p1 = P(nx, ny)

        if tw.p2 is not None:
            nx = self._s_p2.x + (tw.p2.x - self._s_p2.x) * v if tw.p2.x is not None else self._s_p2.x
            ny = self._s_p2.y + (tw.p2.y - self._s_p2.y) * v if tw.p2.y is not None else self._s_p2.y
            self._cur_p2 = P(nx, ny)

        if tw.px1 is not None:
            nx = self._s_px1.x + (tw.px1.x - self._s_px1.x) * v if tw.px1.x is not None else self._s_px1.x
            ny = self._s_px1.y + (tw.px1.y - self._s_px1.y) * v if tw.px1.y is not None else self._s_px1.y
            self._cur_px1 = P(nx, ny)

        if tw.px2 is not None:
            nx = self._s_px2.x + (tw.px2.x - self._s_px2.x) * v if tw.px2.x is not None else self._s_px2.x
            ny = self._s_px2.y + (tw.px2.y - self._s_px2.y) * v if tw.px2.y is not None else self._s_px2.y
            self._cur_px2 = P(nx, ny)

        if t >= 1.0:
            self._s_p1  = self._cur_p1
            self._s_p2  = self._cur_p2
            self._s_px1 = self._cur_px1
            self._s_px2 = self._cur_px2
            self._win_idx += 1

    def tick(self, now: float) -> None:
        if self.defn.hidden_event is not None:
            self.hidden = _resolve_bool_value(self.defn.hidden_event)
        if self.hidden: return
        self._poll_phase_event()
        if self._snap_tween_active:
            elapsed = now - self._snap_tween_t0
            dur     = self._snap_tween_dur
            if elapsed >= dur:
                self._cur_p1  = P(self._snap_to_p1x, self._snap_to_p1y)
                self._cur_p2  = P(self._snap_to_p2x, self._snap_to_p2y)
                self._cur_px1 = P(self._snap_to_px1x, self._snap_to_px1y)
                self._cur_px2 = P(self._snap_to_px2x, self._snap_to_px2y)
                self._snap_tween_active = False
            else:
                v = 1.0 - (1.0 - elapsed / dur) ** 5
                self._cur_p1 = P(
                    self._snap_from_p1x + (self._snap_to_p1x - self._snap_from_p1x) * v,
                    self._snap_from_p1y + (self._snap_to_p1y - self._snap_from_p1y) * v,
                )
                self._cur_p2 = P(
                    self._snap_from_p2x + (self._snap_to_p2x - self._snap_from_p2x) * v,
                    self._snap_from_p2y + (self._snap_to_p2y - self._snap_from_p2y) * v,
                )
                self._cur_px1 = P(
                    self._snap_from_px1x + (self._snap_to_px1x - self._snap_from_px1x) * v,
                    self._snap_from_px1y + (self._snap_to_px1y - self._snap_from_px1y) * v,
                )
                self._cur_px2 = P(
                    self._snap_from_px2x + (self._snap_to_px2x - self._snap_from_px2x) * v,
                    self._snap_from_px2y + (self._snap_to_px2y - self._snap_from_px2y) * v,
                )
        if self._cur_phase == 'close' and self._is_done():
            has_always = any(
                not d._stopped
                for p in self._polygons
                for d in p._always_drivers.values()
            )
            if not has_always:
                self._last_frame_time = now
                return
        self._tick_win_tweens()
        self._tick_spawn(None, 
                        self._last_ipw if self._last_ipw > 0 else self.cam_w,
                        self._last_iph if self._last_iph > 0 else self.cam_h,
                        now)
        for g in self._graphs:
            g.tick(now)
        for sw in self._sub_windows:
            if sw.defn.spawn_event is None:
                sw.tick(now)
        if self._last_frame_time > 0.0:
            dt = now - self._last_frame_time
            self._fps_samples.append(dt)
            avg_dt = sum(self._fps_samples) / len(self._fps_samples)
            SYS_FPS.value        = round(1.0 / avg_dt if avg_dt > 0 else 0.0, 1)
            SYS_FRAME_TIME.value = round(avg_dt * 1000.0, 2)
        self._last_frame_time = now

    def update(self, ctx, widget_w, widget_h, _parent_abs_x=0.0, _parent_abs_y=0.0):
        if self.hidden: return

        global _current_update_window
        _prev_update_window = _current_update_window
        _current_update_window = self
        try:
            wx, wy, ww, wh = self._screen_rect(widget_w, widget_h)
            if not (self._dragging_window or self._scaling_window):
                if self.defn.sticky_boundary:
                    self._sync_sticky_boundary(widget_w, widget_h, moved_sides=set())
                if self.defn.force_boundary:
                    self._clamp_to_boundary(widget_w, widget_h)
                if self.defn.force_boundary or self.defn.sticky_boundary:
                    wx, wy, ww, wh = self._screen_rect(widget_w, widget_h)
            if self.defn.export_p1  is not None: self.defn.export_p1.value  = P(self._cur_p1.x,  self._cur_p1.y)
            if self.defn.export_p2  is not None: self.defn.export_p2.value  = P(self._cur_p2.x,  self._cur_p2.y)
            if self.defn.export_px1 is not None: self.defn.export_px1.value = P(self._cur_px1.x, self._cur_px1.y)
            if self.defn.export_px2 is not None: self.defn.export_px2.value = P(self._cur_px2.x, self._cur_px2.y)
            self._abs_wx = _parent_abs_x + wx
            self._abs_wy = _parent_abs_y + wy
            self._abs_ww = ww
            self._abs_wh = wh
            ipw, iph = int(ww), int(wh)
            self._last_ipw = ipw
            self._last_iph = iph

            if self._cur_phase == 'close' and self._is_done():
                has_always = any(
                    not d._stopped
                    for p in self._polygons
                    for d in p._always_drivers.values()
                )
                if not has_always:
                    return

            if ww > 0 and wh > 0:
                mx = SYS_MOUSE_X.value
                my = SYS_MOUSE_Y.value
                _window_mouse_norm[id(self.defn)] = P(
                    (mx - wx) / ww,
                    (my - wy) / wh,
                )
                _window_size_px[id(self.defn)] = P(ww, wh)

            if self._force_open_pending:
                if not self._force_open_triggered and self._cur_phase == 'open':
                    self._force_open_triggered = True
                    for p in self._polygons: p.set_phase('open')
                    for t in self._texts:    t.set_phase('open')
                    for a in self._arcs:     a.set_phase('open')
                if self._force_open_triggered:
                    if all(p.phase_done() for p in self._polygons) and \
                    all(t.phase_done() for t in self._texts):
                        self._force_open_pending = False

            if self._force_close_active:
                if self._cur_phase == 'close' and self._prev_force_phase != 'close':
                    for p in self._polygons: p.set_phase('close')
                    for t in self._texts:    t.set_phase('close')
                    for a in self._arcs:     a.set_phase('close')
                if all(p.phase_done() for p in self._polygons) and \
                all(t.phase_done() for t in self._texts):
                    self._force_close_active = False
            self._prev_force_phase = self._cur_phase

            _pulse_resets: List[EventDef] = []

            # Listeners
            for gl in self._listeners:
                gl.tick(ctx)

            # Polygons
            for p, pd in zip(self._polygons, self.defn.polygon_defs):
                has_active_always = any(
                    not d._stopped for d in p._always_drivers.values()
                ) if p._always_drivers else False

                if self._force_open_pending or self._force_close_active:
                    p.update()
                    continue

                visible = _check_visible_threshold(pd, ww, wh, self.cam_w, self.cam_h)
                if not visible:
                    if _phase_key_exists(pd.phases or {}, 'threshold'):
                        p.hidden = False
                        if p._phase != 'threshold':
                            p.set_phase('threshold')
                        p.update()
                    else:
                        p.hidden = True
                        if has_active_always:
                            p.update()
                    continue

                p.hidden = False
                if p._phase == 'threshold':
                    p.set_phase('open')

                ov = p.defn.phase_override
                if ov is not None:
                    phase = ov() if callable(ov) else str(ov.value) if hasattr(ov, 'value') else str(ov)
                    phase = str(phase) if phase is not None else ''
                    if phase and phase != p._phase:
                        if _phase_key_exists(p.defn.phases or {}, phase):
                            p.set_phase(phase)

                if p._phase:
                    cur_phase_def = _get_phase_def(pd.phases or {}, p._phase)
                    if cur_phase_def is not None and getattr(cur_phase_def, 'update_retrigger', False):
                        p.set_phase(p._phase)

                p.update()

            for a in self._arcs:
                a.update()

            # Texts
            for t, td in zip(self._texts, self.defn.text_defs):
                has_active_always = any(
                    not d._stopped for d in t._always_drivers_t.values()
                ) if t._always_drivers_t else False

                if self._force_open_pending or self._force_close_active:
                    t.update()
                    continue

                visible = _check_visible_threshold(td, ww, wh, self.cam_w, self.cam_h)
                if not visible:
                    if _phase_key_exists(td.phases or {}, 'threshold'):
                        t.hidden = False
                        if t._phase != 'threshold':
                            t.set_phase('threshold')
                        t.update()
                    else:
                        t.hidden = True
                        if has_active_always:
                            t.update()
                    continue

                t.hidden = False
                if t._phase == 'threshold':
                    t.set_phase('open')

                ov = t.defn.phase_override
                if ov is not None:
                    phase = ov() if callable(ov) else str(ov.value) if hasattr(ov, 'value') else str(ov)
                    phase = str(phase) if phase is not None else ''
                    if phase and phase != t._phase:
                        if _phase_key_exists(t.defn.phases or {}, phase):
                            t.set_phase(phase)
                if t._phase:
                    cur_phase_def = _get_phase_def(td.phases or {}, t._phase)
                    if cur_phase_def is not None and getattr(cur_phase_def, 'update_retrigger', False):
                        t.set_phase(t._phase)

                t.update()

            # Pies
            for pie in self._pies: pie.update(ctx)

            # Sliders
            for sl in self._sliders: sl.update(int(ww), int(wh))

            # Buttons
            for btn, bd in zip(self._buttons, self.defn.button_defs):
                ov = bd.phase_override
                if ov is not None:
                    phase = ov() if callable(ov) else str(ov.value) if hasattr(ov, 'value') else str(ov)
                    phase = str(phase) if phase is not None else ''
                    # if bd.event_out is get_event('targeted_marker'):
                        # print(f'[poll] ov.value={ov.value!r} phase={phase!r} last={btn._last_override_phase!r} cur_phase={btn._cur_phase!r}')
                    if phase and phase != btn._last_override_phase:
                        btn._last_override_phase = phase
                        if phase in ('open', 'close'):
                            btn._set_base_phase(phase)
                btn.update(int(ww), int(wh))

            # Textboxes
            for tb, td in zip(self._textboxes, self.defn.textbox_defs):
                ov = td.phase_override
                if ov is not None:
                    phase = ov() if callable(ov) else str(ov.value) if hasattr(ov, 'value') else str(ov)
                    phase = str(phase) if phase is not None else ''
                    if phase and phase != tb._last_override_phase:
                        tb._last_override_phase = phase
                        if phase in ('open', 'close'):
                            tb._set_base_phase(phase)
                tb.update(int(ww), int(wh))

            # Graphs
            for g, gd in zip(self._graphs, self.defn.graph_defs):
                ov = gd.phase_override
                if ov is not None:
                    phase = ov() if callable(ov) else str(ov.value) if hasattr(ov, 'value') else str(ov)
                    phase = str(phase) if phase is not None else ''
                    if phase and phase != g._last_override_phase:
                        g._last_override_phase = phase
                        if phase in ('open', 'close'):
                            g.set_phase(phase)

            # Sub windows
            for sw in self._sub_windows:
                if sw.defn.spawn_event is not None: continue
                sw.update(ctx, ipw, iph, _parent_abs_x=self._abs_wx, _parent_abs_y=self._abs_wy)

            ipw, iph = int(ww), int(wh)
            self._last_ipw = ipw
            self._last_iph = iph

            for inst in self._spawned:
                inst.window.update(ctx, ipw, iph, _parent_abs_x=self._abs_wx, _parent_abs_y=self._abs_wy)
        finally:
            _current_update_window = _prev_update_window

    def draw(self, painter, widget_w, widget_h, ctx=None):
        if self.hidden:
            return
        if self._cur_phase == 'close' and self._is_done():
            return
        wx, wy, ww, wh = self._screen_rect(widget_w, widget_h)
        if ww <= 0 or wh <= 0:
            return
        scale = min(ww / self.cam_w, wh / self.cam_h)

        global _current_window_screen_offset, _current_update_window
        parent_offset = _current_window_screen_offset
        _current_window_screen_offset = P(parent_offset.x + wx, parent_offset.y + wy)

        _prev_update_window = _current_update_window
        _current_update_window = self
        try:
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.translate(wx, wy)
            painter.setClipRect(QRectF(0, 0, ww, wh))
            iww, iwh = int(ww), int(wh)

            for poly in self._polygons:
                poly.draw(painter, iww, iwh, self.cam_w, self.cam_h)
            for arc in self._arcs:
                arc.draw(painter, iww, iwh)
            for text in self._texts:
                if text.hidden: continue
                text.draw_text(painter, iww, iwh, self.cam_w, self.cam_h, ctx, scale=scale)
            for g in self._graphs:
                g.draw(painter, iww, iwh, ctx, self.cam_w, self.cam_h)
            for pie in self._pies:
                pie.draw(painter, iww, iwh, self.cam_w, self.cam_h)
            for sl in self._sliders:
                sl.draw(painter, iww, iwh, scale=scale)
            for btn in self._buttons:
                btn.draw(painter, iww, iwh, scale=scale)
            for tb in self._textboxes:
                tb.draw(painter, iww, iwh, scale=scale)

            for sw in self._sub_windows:
                if sw.defn.spawn_event is not None:
                    continue
                sw.draw(painter, iww, iwh, ctx)
            for inst in self._spawned:
                inst.window.draw(painter, iww, iwh, ctx)

            painter.restore()
        finally:
            _current_update_window = _prev_update_window
            _current_window_screen_offset = parent_offset

    def _to_local(self, mx: float, my: float, widget_w: int, widget_h: int) -> Tuple[float, float, float, float]:
        wx, wy, ww, wh = self._screen_rect(widget_w, widget_h)
        return mx - wx, my - wy, ww, wh
    
    def mouse_press(self, mx: float, my: float, widget_w: int, widget_h: int) -> bool:
        if self.hidden:
            return False
        ignored = _resolve_bool_value(self.defn.ignore_mouse_event)
        if ignored:
            return False
        wx, wy, ww, wh = self._screen_rect(widget_w, widget_h)
        ipw, iph = int(ww), int(wh)
        for inst in reversed(self._spawned):
            if inst.window.mouse_press(mx - wx, my - wy, ipw, iph):
                return True
        for sw in self._sub_windows:
            sw._parent_w = ipw
            sw._parent_h = iph
        for sw in reversed(self._sub_windows):
            if sw.mouse_press(mx - wx, my - wy, ipw, iph):
                return True

        lx = mx - wx
        ly = my - wy

        hit_tb = None
        for tb in self._textboxes:
            if hit_tb is None and tb.hit_test(lx, ly, ipw, iph):
                hit_tb = tb

        hit_sl = None
        if hit_tb is None:
            for sl in self._sliders:
                if sl.hit_test_knob(lx, ly, ipw, iph):
                    hit_sl = sl
                    break

        hit_btn = None
        btn_fired = False
        if hit_tb is None and hit_sl is None:
            for btn in self._buttons:
                if self._resolve_ignore_mouse(btn.defn.ignore_mouse_event):
                    continue
                if btn.hit_test(lx, ly, ipw, iph):
                    if not btn._mandatory_keys_held(self._held_keys):
                        continue
                    btn._pressed    = True
                    btn._press_poly = QPolygonF(btn._last_poly)
                    btn._set_interaction_phase('click')
                    btn_fired = True
                    hit_btn   = btn
                    if not btn.defn.ignore_click_consume:
                        return True

        hit_interactive = hit_tb is not None or hit_sl is not None or btn_fired
        inside = (0 <= lx <= ipw and 0 <= ly <= iph)

        if self.defn.scalable and not hit_interactive and inside:
            edge = self._detect_edge(lx, ly, ipw, iph)
            if edge:
                self._scaling_window    = True
                self._scale_edge        = edge
                self._scale_start_mx    = mx
                self._scale_start_my    = my
                self._scale_start_p1x   = self._cur_p1.x
                self._scale_start_p1y   = self._cur_p1.y
                self._scale_start_px1x  = self._cur_px1.x
                self._scale_start_px1y  = self._cur_px1.y
                self._scale_start_p2x   = self._cur_p2.x
                self._scale_start_p2y   = self._cur_p2.y
                self._scale_start_px2x  = self._cur_px2.x
                self._scale_start_px2y  = self._cur_px2.y
                self._cancel_active_phases()
                return not self.defn.ignore_click_consume

        if self.defn.draggable and not hit_interactive and inside:
            self._dragging_window    = True
            self._drag_start_mx      = mx
            self._drag_start_my      = my
            self._drag_start_p1x     = self._cur_p1.x
            self._drag_start_p1y     = self._cur_p1.y
            self._drag_start_px1x    = self._cur_px1.x
            self._drag_start_px1y    = self._cur_px1.y
            self._drag_start_p2x     = self._cur_p2.x
            self._drag_start_p2y     = self._cur_p2.y
            self._drag_start_px2x    = self._cur_px2.x
            self._drag_start_px2y    = self._cur_px2.y
            self._cancel_active_phases()
            return not self.defn.ignore_click_consume

        for tb in self._textboxes:
            if tb is hit_tb:
                tb._activate()
            elif tb._active:
                tb._deactivate()
        if hit_tb is not None:
            return True

        if hit_sl is not None:
            self._dragging_slider = hit_sl
            hit_sl._dragging = True
            hit_sl.drag_to(lx, ly, ipw, iph)
            hit_sl.commit(None)
            hit_sl.set_phase('pressed')
            return True

        if hit_btn is not None:
            return True

        return False

    def mouse_move(self, mx, my, widget_w, widget_h):
        if self.hidden:
            return False
        if _resolve_bool_value(self.defn.ignore_mouse_event):
            return
        if self._parent_w == 0 and self._parent_h == 0:
            SYS_MOUSE.value       = (mx, my)
            SYS_MOUSE_X.value     = mx
            SYS_MOUSE_Y.value     = my
            SYS_MOUSE_ABS_X.value = mx
            SYS_MOUSE_ABS_Y.value = my

        pw = self._parent_w if self._parent_w > 0 else widget_w
        ph = self._parent_h if self._parent_h > 0 else widget_h

        if self._scaling_window:
            dx_n = (mx - self._scale_start_mx) / pw
            dy_n = (my - self._scale_start_my) / ph
            e    = self._scale_edge
            d    = self.defn

            new_p1x  = self._scale_start_p1x
            new_p1y  = self._scale_start_p1y
            new_p2x  = self._scale_start_p2x
            new_p2y  = self._scale_start_p2y

            if 'l' in e:
                new_p1x = min(self._scale_start_p1x + dx_n,
                            self._scale_start_p2x - d.min_scale_w)
            if 'r' in e:
                new_p2x = max(self._scale_start_p2x + dx_n,
                            self._scale_start_p1x + d.min_scale_w)
            if 't' in e:
                new_p1y = min(self._scale_start_p1y + dy_n,
                            self._scale_start_p2y - d.min_scale_h)
            if 'b' in e:
                new_p2y = max(self._scale_start_p2y + dy_n,
                            self._scale_start_p1y + d.min_scale_h)

            bx1_px = d.drag_boundary_p1.x * pw + d.drag_boundary_px1.x
            by1_px = d.drag_boundary_p1.y * ph + d.drag_boundary_px1.y
            bx2_px = d.drag_boundary_p2.x * pw + d.drag_boundary_px2.x
            by2_px = d.drag_boundary_p2.y * ph + d.drag_boundary_px2.y

            px1x, px1y = self._scale_start_px1x, self._scale_start_px1y
            px2x, px2y = self._scale_start_px2x, self._scale_start_px2y

            new_x1_px = max(bx1_px, new_p1x * pw + px1x)
            new_y1_px = max(by1_px, new_p1y * ph + px1y)
            new_x2_px = min(bx2_px, new_p2x * pw + px2x)
            new_y2_px = min(by2_px, new_p2y * ph + px2y)

            new_p1x = (new_x1_px - px1x) / pw
            new_p1y = (new_y1_px - px1y) / ph
            new_p2x = (new_x2_px - px2x) / pw
            new_p2y = (new_y2_px - px2y) / ph

            if new_p2x - new_p1x < d.min_scale_w:
                if 'l' in e: new_p1x = new_p2x - d.min_scale_w
                else:         new_p2x = new_p1x + d.min_scale_w
            if new_p2y - new_p1y < d.min_scale_h:
                if 't' in e: new_p1y = new_p2y - d.min_scale_h
                else:         new_p2y = new_p1y + d.min_scale_h

            self._cur_p1  = P(new_p1x, new_p1y)
            self._cur_p2  = P(new_p2x, new_p2y)
            self._cur_px1 = P(px1x, px1y)
            self._cur_px2 = P(px2x, px2y)
            if self.defn.sticky_boundary:
                self._sync_sticky_boundary(pw, ph, moved_sides=set(e))
            return True

        if self._dragging_window:
            dx_n = (mx - self._drag_start_mx) / pw
            dy_n = (my - self._drag_start_my) / ph
            self._cur_p1  = P(self._drag_start_p1x  + dx_n, self._drag_start_p1y  + dy_n)
            self._cur_p2  = P(self._drag_start_p2x  + dx_n, self._drag_start_p2y  + dy_n)
            self._cur_px1 = P(self._drag_start_px1x,         self._drag_start_px1y)
            self._cur_px2 = P(self._drag_start_px2x,         self._drag_start_px2y)
            self._clamp_to_boundary(pw, ph)
            if self.defn.sticky_boundary:
                self._sync_sticky_boundary(pw, ph, moved_sides={'l', 'r', 't', 'b'})
            return True

        wx, wy, ww, wh = self._screen_rect(widget_w, widget_h)
        ipw, iph = int(ww), int(wh)
        for inst in reversed(self._spawned):
            inst.window.mouse_move(mx - wx, my - wy, ipw, iph)
        for sw in self._sub_windows:
            sw._parent_w = ipw
            sw._parent_h = iph
        for sw in reversed(self._sub_windows):
            sw.mouse_move(mx - wx, my - wy, ipw, iph)

        lx = mx - wx
        ly = my - wy
        if self._dragging_slider is not None:
            self._dragging_slider.drag_to(lx, ly, ipw, iph)
            self._dragging_slider.commit(None)
            return True
        for tb in self._textboxes:
            tb.mouse_move(lx, ly, ipw, iph)
        for sl in self._sliders:
            hit = sl.hit_test_knob(lx, ly, ipw, iph)
            if hit != sl._hovered:
                sl._hovered = hit
                sl.set_phase('hovered' if hit else 'unhovered')
        for btn in self._buttons:
            if self._resolve_ignore_mouse(btn.defn.ignore_mouse_event):
                continue
            hit = btn.hit_test(lx, ly, ipw, iph)
            if hit != btn._hovered:
                btn._hovered = hit
                btn._set_interaction_phase('hover' if hit else 'unhover')
            if not hit and btn._pressed and not btn._key_held:
                btn.mouse_left_hitbox()
        return False

    def mouse_release(self, mx: float, my: float, widget_w: int, widget_h: int) -> bool:
        if self.hidden:
            return False
        if _resolve_bool_value(self.defn.ignore_mouse_event):
            return False
        if self._scaling_window:
            self._scaling_window = False
            self._scale_edge     = ''
            self._start_snap_tween(time.monotonic(), widget_w, widget_h)
            return True

        if self._dragging_window:
            self._dragging_window = False
            self._start_snap_tween(time.monotonic(), widget_w, widget_h)
            return True

        wx, wy, ww, wh = self._screen_rect(widget_w, widget_h)
        ipw, iph = int(ww), int(wh)
        for inst in reversed(self._spawned):
            if inst.window.mouse_release(mx - wx, my - wy, ipw, iph):
                return True
        for sw in reversed(self._sub_windows):
            if sw.mouse_release(mx - wx, my - wy, ipw, iph):
                return True

        lx, ly, _, _ = self._to_local(mx, my, widget_w, widget_h)
        sl = self._dragging_slider
        if sl is not None:
            sl._dragging = sl._pressed = False
            sl.set_phase('released')
            sl.commit(None)
            self._dragging_slider = None
            hovered = sl._hovered
            QTimer.singleShot(150, lambda: sl.set_phase('hovered' if hovered else 'unhovered'))
            return True
        for btn in self._buttons:
            if self._resolve_ignore_mouse(btn.defn.ignore_mouse_event):
                continue
            if btn._pressed:
                btn._pressed = False
                btn._set_interaction_phase('release')
                if not btn.defn.continuous_update:
                    if btn._hit_test_press_poly(lx, ly):
                        btn.fire_event()
                        btn._check_held()
                if not btn._held:
                    QTimer.singleShot(250, lambda b=btn: b._set_interaction_phase('hover' if b._hovered else 'unhover'))
                if not btn.defn.ignore_click_consume:
                    return True
        return False
        
    def key_press(self, key: int) -> bool:
        if self.hidden:
            return False
        self._held_keys.add(key)
        mods  = QApplication.keyboardModifiers()
        shift = bool(mods & Qt.ShiftModifier)
        ctrl  = bool(mods & Qt.ControlModifier)

        for inst in reversed(self._spawned):
            if inst.window.key_press(key):
                return True
        for sw in reversed(self._sub_windows):
            if sw.defn.spawn_event is not None: continue
            if sw.key_press(key):
                return True

        consumed = False
        for tb in self._textboxes:
            if tb._active:
                if tb.key_press(key, shift=shift, ctrl=ctrl):
                    if tb.defn.override_inputs:
                        return True
                    consumed = True
        for btn in self._buttons:
            if btn.key_press(key, self._held_keys):
                consumed = True
        return consumed

    def key_release(self, key: int) -> bool:
        if self.hidden:
            return False
        self._held_keys.discard(key)
        for inst in reversed(self._spawned):
            if inst.window.key_release(key):
                return True
        for sw in reversed(self._sub_windows):
            if sw.defn.spawn_event is not None: continue
            if sw.key_release(key):
                return True

        consumed = False
        for tb in self._textboxes:
            if tb.key_release(key):
                if tb.defn.override_inputs:
                    return True
                consumed = True
        for btn in self._buttons:
            if btn.key_release(key, self._held_keys):
                consumed = True
        return consumed
            
    def mouse_leave(self) -> None:
        for sl in self._sliders:
            if sl._hovered:
                sl._hovered = False
                sl.set_phase('unhover')
        for btn in self._buttons:
            if btn._hovered:
                btn._hovered = False
                btn._set_interaction_phase('unhover')
    
    def _resolve_ignore_mouse(self, val) -> bool:
        return _resolve_bool_value(val)
    
    def _snap_to_grid(self, p1x: float, p1y: float, p2x: float, p2y: float, parent_w: int, parent_h: int) -> Tuple[float, float, float, float]:
        d = self.defn

        if d.grid_snap_pixel:
            return self._snap_to_grid_px(p1x, p1y, p2x, p2y, parent_w, parent_h)

        bx1 = d.drag_boundary_p1.x
        by1 = d.drag_boundary_p1.y
        bx2 = d.drag_boundary_p2.x
        by2 = d.drag_boundary_p2.y

        gx, gy = max(1, d.grid_snap_x), max(1, d.grid_snap_y)
        step_x = (bx2 - bx1) / gx
        step_y = (by2 - by1) / gy

        def _snap(v, origin, step):
            if step <= 0:
                return v
            return origin + round((v - origin) / step) * step

        s_p1x = _snap(p1x, bx1, step_x)
        s_p1y = _snap(p1y, by1, step_y)
        s_p2x = _snap(p2x, bx1, step_x)
        s_p2y = _snap(p2y, by1, step_y)

        if s_p2x <= s_p1x: s_p2x = s_p1x + step_x
        if s_p2y <= s_p1y: s_p2y = s_p1y + step_y
        return s_p1x, s_p1y, s_p2x, s_p2y

    def _snap_to_grid_px(self, p1x: float, p1y: float, p2x: float, p2y: float, parent_w: int, parent_h: int) -> Tuple[float, float, float, float]:
        d = self.defn
        gx_px = max(1.0, float(d.grid_snap_x))
        gy_px = max(1.0, float(d.grid_snap_y))

        # boundary in true pixels relative to parent
        bx1 = d.drag_boundary_p1.x * parent_w + d.drag_boundary_px1.x
        by1 = d.drag_boundary_p1.y * parent_h + d.drag_boundary_px1.y
        bx2 = d.drag_boundary_p2.x * parent_w + d.drag_boundary_px2.x
        by2 = d.drag_boundary_p2.y * parent_h + d.drag_boundary_px2.y

        center_x = parent_w * 0.5
        center_y = parent_h * 0.5

        def _snap_px(v_px, boundary_lo, boundary_hi):
            grid_pt = round(v_px / gx_px) * gx_px if gx_px == gy_px else v_px
            return grid_pt

        def _snap_axis(v_px, center, step, boundary_lo, boundary_hi):
            rel = v_px - center
            snapped_rel = round(rel / step) * step
            snapped = center + snapped_rel
            candidates = [snapped]
            if boundary_lo is not None:
                candidates.append(boundary_lo)
            if boundary_hi is not None:
                candidates.append(boundary_hi)
            return min(candidates, key=lambda c: abs(c - v_px))

        win_x1_px = p1x * parent_w
        win_y1_px = p1y * parent_h
        win_x2_px = p2x * parent_w
        win_y2_px = p2y * parent_h

        s_x1_px = _snap_axis(win_x1_px, center_x, gx_px, bx1, bx2)
        s_y1_px = _snap_axis(win_y1_px, center_y, gy_px, by1, by2)
        s_x2_px = _snap_axis(win_x2_px, center_x, gx_px, bx1, bx2)
        s_y2_px = _snap_axis(win_y2_px, center_y, gy_px, by1, by2)

        s_p1x, s_p1y = s_x1_px / parent_w, s_y1_px / parent_h
        s_p2x, s_p2y = s_x2_px / parent_w, s_y2_px / parent_h

        if s_p2x <= s_p1x: s_p2x = s_p1x + gx_px / parent_w
        if s_p2y <= s_p1y: s_p2y = s_p1y + gy_px / parent_h
        return s_p1x, s_p1y, s_p2x, s_p2y
    
    def _start_snap_tween(self, now: float, parent_w: int = None, parent_h: int = None) -> None:
        d = self.defn
        if not d.grid_snap or (d.grid_snap_x <= 0):
            return
        pw = parent_w if parent_w else (self._parent_w if self._parent_w > 0 else self.cam_w)
        ph = parent_h if parent_h else (self._parent_h if self._parent_h > 0 else self.cam_h)
        s_p1x, s_p1y, s_p2x, s_p2y = self._snap_to_grid(self._cur_p1.x, self._cur_p1.y, self._cur_p2.x, self._cur_p2.y, pw, ph)
        if (s_p1x == self._cur_p1.x and s_p1y == self._cur_p1.y and s_p2x == self._cur_p2.x and s_p2y == self._cur_p2.y):
            return
        self._snap_from_p1x = self._cur_p1.x
        self._snap_from_p1y = self._cur_p1.y
        self._snap_from_p2x = self._cur_p2.x
        self._snap_from_p2y = self._cur_p2.y
        self._snap_to_p1x   = s_p1x
        self._snap_to_p1y   = s_p1y
        self._snap_to_p2x   = s_p2x
        self._snap_to_p2y   = s_p2y
        self._snap_from_px1x = self._cur_px1.x
        self._snap_from_px1y = self._cur_px1.y
        self._snap_from_px2x = self._cur_px2.x
        self._snap_from_px2y = self._cur_px2.y
        self._snap_to_px1x   = self._cur_px1.x
        self._snap_to_px1y   = self._cur_px1.y
        self._snap_to_px2x   = self._cur_px2.x
        self._snap_to_px2y   = self._cur_px2.y
        self._snap_tween_t0     = now
        self._snap_tween_active = True
    
    def animate_to_rect(self, p1: P, p2: P, px1: P, px2: P, dur: float = 0.4) -> None:
        now = time.monotonic()
        self._snap_from_p1x = self._cur_p1.x
        self._snap_from_p1y = self._cur_p1.y
        self._snap_from_p2x = self._cur_p2.x
        self._snap_from_p2y = self._cur_p2.y
        self._snap_to_p1x   = p1.x
        self._snap_to_p1y   = p1.y
        self._snap_to_p2x   = p2.x
        self._snap_to_p2y   = p2.y
        self._snap_from_px1x = self._cur_px1.x
        self._snap_from_px1y = self._cur_px1.y
        self._snap_from_px2x = self._cur_px2.x
        self._snap_from_px2y = self._cur_px2.y
        self._snap_to_px1x   = px1.x
        self._snap_to_px1y   = px1.y
        self._snap_to_px2x   = px2.x
        self._snap_to_px2y   = px2.y
        self._snap_tween_dur    = dur
        self._snap_tween_t0     = now
        self._snap_tween_active = True
    
    def set_rect_instant(self, p1: P, p2: P, px1: Optional[P] = None, px2: Optional[P] = None) -> None:
        self._dragging_window   = False
        self._scaling_window    = False
        self._snap_tween_active = False
        self._win_tweens        = []
        self._win_idx           = 0
        self._sticky_sides      = set()

        self._cur_p1 = P(p1.x, p1.y)
        self._cur_p2 = P(p2.x, p2.y)
        if px1 is not None:
            self._cur_px1 = P(px1.x, px1.y)
        if px2 is not None:
            self._cur_px2 = P(px2.x, px2.y)

        self._s_p1  = self._cur_p1
        self._s_p2  = self._cur_p2
        self._s_px1 = self._cur_px1
        self._s_px2 = self._cur_px2
        

    def _on_spawn_trigger(self, value) -> None:
        pass

    def _tick_spawn(self, ctx: Any, widget_w: int, widget_h: int, now: float) -> None:
        d = self.defn

        for wdef in d.sub_windows:
            if wdef.spawn_event is None:
                continue
            ev = wdef.spawn_event
            if ev.value is True or ev.value == True:
                ev.value = False
                active = [s for s in self._spawned
                        if s.window.defn is wdef]
                if len(active) >= wdef.spawn_limit:
                    continue
                self._do_spawn(wdef, widget_w, widget_h)

        wx, wy, ww, wh = self._screen_rect(widget_w, widget_h)
        ipw, iph = int(ww), int(wh)
        to_remove = []
        for inst in self._spawned:
            sw   = inst.window
            dev  = inst.group_event
            wdef = sw.defn

            if wdef.use_parent_close_phase and self._cur_phase == 'close':
                if sw._cur_phase != 'close':
                    sw._broadcast('close')
                    inst.closing = True

            if not inst.closing:
                try:
                    cur_val = int(float(dev.value))
                except (TypeError, ValueError):
                    cur_val = 0
                # print(f'[tick_spawn] inst={inst.obj_id} cur_val={cur_val} threshold={wdef.spawn_delete_threshold}')
                if cur_val >= wdef.spawn_delete_threshold:
                    inst.closing = True
                    if _phase_key_exists(wdef.phases, 'close'):
                        sw._broadcast('close')
                    else:
                        to_remove.append(inst)
            else:
                if sw._cur_phase == 'close' and sw._is_done():
                    to_remove.append(inst)
                elif sw._cur_phase != 'close':
                    to_remove.append(inst)

            sw.tick(now)

        for inst in to_remove:
            self._remove_spawn(inst)

    def _do_spawn(self, wdef: WindowDef, widget_w: int, widget_h: int) -> _SpawnedInstance:
        global _current_spawn_window
        _current_spawn_window = self

        group = wdef.spawn_event_group or ''

        if wdef.spawn_tick_increment and group:
            for inst in self._spawned:
                if inst.window.defn is wdef:
                    inst.group_event.value = int(inst.group_event.value) + 1

        group_ev = _alloc_group_event(group) if group else EventDef(name='_anon', value=0)

        statics: List[Any] = []
        for entry in wdef.spawn_static_values:
            if isinstance(entry, EventDef):
                statics.append(entry.value)
            elif callable(entry):
                try:    statics.append(entry())
                except: statics.append(None)
            else:
                statics.append(entry)

        _current_spawn_window = None

        sw        = AnimatedWindow(wdef, self.cam_w, self.cam_h)
        sw.hidden = False
        sw._group_event = group_ev
        sw._statics     = statics

        if wdef.phase_event is GROUP_EVENT:
            sw._instance_phase_event = group_ev

        obj_id = self._make_id()

        if wdef.on_spawn is not None:
            try:
                wdef.on_spawn(obj_id, statics)
            except Exception as e:
                print(f'[on_spawn] error: {e}')

        def _resolve(val):
            if isinstance(val, _StaticRef):
                idx = val.index
                return statics[idx] if idx < len(statics) else None
            if val is GROUP_EVENT:
                return group_ev
            if val is SELECT_EVENT:
                return wdef.select_event
            if val is SELF_ID:
                return obj_id
            return val

        def _resolve_p(p: P) -> P:
            if not isinstance(p, P):
                return p
            x = statics[p.x.index] if isinstance(p.x, _StaticRef) else p.x
            y = statics[p.y.index] if isinstance(p.y, _StaticRef) else p.y
            return P(x if x is not None else 0.0,
                    y if y is not None else 0.0)

        def _patch_pos_fn(fn):
            if fn is None:
                return None
            try:
                defaults = fn.__defaults__ or ()
                if any(isinstance(df, _StaticRef) for df in defaults):
                    resolved = tuple(
                        statics[df.index] if isinstance(df, _StaticRef) else df
                        for df in defaults
                    )
                    return _patch_fn_defaults(fn, resolved)
            except Exception as e:
                print(f'[pos_fn] error: {e}')
            return fn

        for poly in sw._polygons:
            d = poly.defn

            new_pts     = [_resolve_p(p) for p in d.p]
            new_px      = [_resolve_p(p) for p in d.px] if d.px else None
            new_fill    = _resolve(d.fill_color)
            new_outline = _resolve(d.outline_color)
            new_pos_fn  = _patch_pos_fn(d.pos_fn)
            new_phase_override = d.phase_override
            if new_phase_override is SELF_ID:
                _this_id = obj_id
                # new_phase_override = lambda _id=_this_id: (lambda r: (print(f'[diamond] id={_id} target={get_event("targeted_marker").value} -> {r}'), r)[1])('selected' if get_event('targeted_marker').value == _id else 'unselected')
                # new_phase_override = lambda _id=_this_id: 'selected' if get_event('targeted_marker').value == _id else 'unselected'

            changed = (
                new_pts != d.p or new_px != d.px or
                new_fill is not d.fill_color or new_outline is not d.outline_color or
                new_pos_fn is not d.pos_fn or new_phase_override is not d.phase_override
            )
            if changed:
                poly.defn = _tw_replace(poly.defn,
                    p=new_pts, px=new_px, fill_color=new_fill, outline_color=new_outline,
                    pos_fn=new_pos_fn, phase_override=new_phase_override,
                )
                poly.cur_p      = list(new_pts)
                poly._sp        = list(new_pts)
                if new_px:
                    poly.cur_px = list(new_px)
                    poly._spx   = list(new_px)
                if new_fill is not None and new_fill is not d.fill_color:
                    poly.cur_fill_color = QColor(new_fill)
                    poly._sf            = QColor(new_fill)
                if new_outline is not None and new_outline is not d.outline_color:
                    poly.cur_outline_color = QColor(new_outline)
                    poly._so               = QColor(new_outline)
                poly._dirty = True

        for text in sw._texts:
            d  = text.defn
            fn = d.text_fn

            if fn is GROUP_EVENT:
                text.defn = _tw_replace(text.defn,
                    text_fn=lambda ctx, e=group_ev: str(e.value))
            elif fn is SELF_ID:
                if wdef.spawn_name_event_fn is not None:
                    ev = wdef.spawn_name_event_fn(obj_id)
                    text.defn = _tw_replace(text.defn, text_fn=lambda ctx, e=ev: str(e.value))
                else:
                    text.defn = _tw_replace(text.defn, text_fn=lambda ctx, s=str(obj_id): s)
            elif isinstance(fn, EventDef):
                snapped = str(fn.value)
                text.defn = _tw_replace(text.defn,
                    text_fn=lambda ctx, s=snapped: s)
            elif isinstance(fn, _StaticRef):
                idx     = fn.index
                snapped = str(statics[idx]) if idx < len(statics) else ''
                text.defn = _tw_replace(text.defn,
                    text_fn=lambda ctx, s=snapped: s)

            d      = text.defn
            new_p  = P(
                statics[d.p.x.index] if isinstance(d.p.x, _StaticRef) else d.p.x,
                statics[d.p.y.index] if isinstance(d.p.y, _StaticRef) else d.p.y,
            )
            new_px = P(
                statics[d.px.x.index] if isinstance(d.px.x, _StaticRef) else d.px.x,
                statics[d.px.y.index] if isinstance(d.px.y, _StaticRef) else d.px.y,
            )
            new_color  = _resolve(d.fill_color)
            new_pos_fn = _patch_pos_fn(d.pos_fn)

            pos_changed = any(isinstance(v, _StaticRef) for v in (d.p.x, d.p.y, d.px.x, d.px.y))
            col_changed = new_color is not d.fill_color
            pfn_changed = new_pos_fn is not d.pos_fn

            if pos_changed or col_changed or pfn_changed:
                text.defn = _tw_replace(text.defn,
                    p      = new_p,
                    px     = new_px,
                    fill_color  = new_color  if col_changed else d.fill_color,
                    pos_fn = new_pos_fn if pfn_changed else d.pos_fn,
                )
            if pos_changed:
                text.cur_p  = new_p
                text.cur_px = new_px
                text._sp    = new_p
                text._spx   = new_px
                text._dirty = True
            if col_changed:
                text.cur_color = QColor(new_color)
                text._sc       = QColor(new_color)
        
        for btn in sw._buttons:
            d = btn.defn

            new_out   = _resolve(d.event_out)
            if d.event_delta is GROUP_EVENT:
                new_delta = wdef.spawn_delete_threshold
            else:
                new_delta = _resolve(d.event_delta)

            pd          = d.poly_def
            new_pts     = [_resolve_p(p) for p in pd.p]
            new_px      = [_resolve_p(p) for p in pd.px] if pd.px else None
            new_fill    = _resolve(pd.fill_color)
            new_outline = _resolve(pd.outline_color)
            new_pos_fn  = _patch_pos_fn(pd.pos_fn)

            new_poly = _tw_replace(pd,
                p             = new_pts,
                px            = new_px,
                fill_color    = new_fill    if new_fill    is not pd.fill_color    else pd.fill_color,
                outline_color = new_outline if new_outline is not pd.outline_color else pd.outline_color,
                pos_fn        = new_pos_fn,
            )

            btn.defn     = _tw_replace(d,
                poly_def    = new_poly,
                event_out   = new_out,
                event_delta = new_delta,
            )
            btn._polygon = AnimatedPolygon(new_poly)
            btn._polygon.set_phase(sw._cur_phase)

            if btn._text is not None:
                t  = btn._text
                td = t.defn
                tn_x  = statics[td.x.index]  if isinstance(td.x,  _StaticRef) else td.x
                tn_y  = statics[td.y.index]  if isinstance(td.y,  _StaticRef) else td.y
                tn_px = statics[td.px.index] if isinstance(td.px, _StaticRef) else td.px
                tn_py = statics[td.py.index] if isinstance(td.py, _StaticRef) else td.py
                tn_color  = _resolve(td.fill_color)
                tn_pos_fn = _patch_pos_fn(td.pos_fn)

                if any(isinstance(v, _StaticRef) for v in (td.x, td.y, td.px, td.py)):
                    t.defn  = _tw_replace(t.defn,
                        x=tn_x, y=tn_y, px=tn_px, py=tn_py)
                    t.cur_x  = tn_x;  t._sx  = tn_x
                    t.cur_y  = tn_y;  t._sy  = tn_y
                    t.cur_px = tn_px; t._spx = tn_px
                    t.cur_py = tn_py; t._spy = tn_py
                    t._dirty = True
                if tn_color is not td.fill_color:
                    t.defn     = _tw_replace(t.defn, fill_color=tn_color)
                    t.cur_color = QColor(tn_color)
                    t._sc       = QColor(tn_color)
                if tn_pos_fn is not td.pos_fn:
                    t.defn = _tw_replace(t.defn, pos_fn=tn_pos_fn)

        wx, wy, ww, wh = self._screen_rect(widget_w, widget_h)
        sw._parent_w = int(ww)
        sw._parent_h = int(wh)

        sw._broadcast('open')

        inst   = _SpawnedInstance(obj_id=obj_id, window=sw, group_event=group_ev)
        self._spawned.append(inst)
        return inst

    def _make_id(self) -> str:
        return str(uuid.uuid4())

    def _remove_spawn(self, inst: _SpawnedInstance) -> None:
        wdef  = inst.window.defn
        group = wdef.spawn_event_group or ''
        if group:
            _free_group_event(group, inst.group_event)
        if wdef.on_despawn is not None:
            try:
                wdef.on_despawn(inst.obj_id)
            except Exception as e:
                print(f'[on_despawn] error: {e}')
        if inst in self._spawned:
            self._spawned.remove(inst)

    def _is_done(self) -> bool:
        poly_done = all(p.phase_done() for p in self._polygons)
        arc_done  = all(a.phase_done() for a in self._arcs)
        text_done = all(t.phase_done() for t in self._texts)
        btn_done  = all(b.phase_done() for b in self._buttons)
        return poly_done and arc_done and text_done and btn_done

    def _clamp_to_boundary(self, parent_w: int, parent_h: int) -> None:
        d = self.defn

        bx1 = d.drag_boundary_p1.x * parent_w + d.drag_boundary_px1.x
        by1 = d.drag_boundary_p1.y * parent_h + d.drag_boundary_px1.y
        bx2 = d.drag_boundary_p2.x * parent_w + d.drag_boundary_px2.x
        by2 = d.drag_boundary_p2.y * parent_h + d.drag_boundary_px2.y

        win_x1 = self._cur_p1.x * parent_w + self._cur_px1.x
        win_y1 = self._cur_p1.y * parent_h + self._cur_px1.y
        win_x2 = self._cur_p2.x * parent_w + self._cur_px2.x
        win_y2 = self._cur_p2.y * parent_h + self._cur_px2.y

        win_w = win_x2 - win_x1
        win_h = win_y2 - win_y1

        new_x1 = max(bx1, min(bx2 - win_w, win_x1))
        new_y1 = max(by1, min(by2 - win_h, win_y1))

        dx_px = new_x1 - win_x1
        dy_px = new_y1 - win_y1

        dx_n = dx_px / parent_w if parent_w else 0.0
        dy_n = dy_px / parent_h if parent_h else 0.0

        self._cur_p1 = P(self._cur_p1.x + dx_n, self._cur_p1.y + dy_n)
        self._cur_p2 = P(self._cur_p2.x + dx_n, self._cur_p2.y + dy_n)
    
    def _boundary_edges_px(self, pw: int, ph: int) -> Dict[str, float]:
        d = self.defn
        return {
            'l': d.drag_boundary_p1.x * pw + d.drag_boundary_px1.x,
            'r': d.drag_boundary_p2.x * pw + d.drag_boundary_px2.x,
            't': d.drag_boundary_p1.y * ph + d.drag_boundary_px1.y,
            'b': d.drag_boundary_p2.y * ph + d.drag_boundary_px2.y,
        }

    def _window_edges_px(self, pw: int, ph: int) -> Dict[str, float]:
        return {
            'l': self._cur_p1.x * pw + self._cur_px1.x,
            'r': self._cur_p2.x * pw + self._cur_px2.x,
            't': self._cur_p1.y * ph + self._cur_px1.y,
            'b': self._cur_p2.y * ph + self._cur_px2.y,
        }

    def _sync_sticky_boundary(self, pw: int, ph: int, moved_sides: Optional[set] = None, eps: float = 1.0) -> None:
        if not self.defn.sticky_boundary or pw <= 0 or ph <= 0:
            return
        moved_sides = moved_sides or set()
        edge_px = self._window_edges_px(pw, ph)
        bnd_px  = self._boundary_edges_px(pw, ph)

        for side in moved_sides:
            if abs(edge_px[side] - bnd_px[side]) <= eps:
                self._sticky_sides.add(side)
            else:
                self._sticky_sides.discard(side)

        p1x, p1y = self._cur_p1.x, self._cur_p1.y
        p2x, p2y = self._cur_p2.x, self._cur_p2.y

        for side in ('l', 'r', 't', 'b'):
            if side in moved_sides:
                continue
            if side in self._sticky_sides:
                if side == 'l': p1x = (bnd_px['l'] - self._cur_px1.x) / pw
                if side == 'r': p2x = (bnd_px['r'] - self._cur_px2.x) / pw
                if side == 't': p1y = (bnd_px['t'] - self._cur_px1.y) / ph
                if side == 'b': p2y = (bnd_px['b'] - self._cur_px2.y) / ph
            elif abs(edge_px[side] - bnd_px[side]) <= eps:
                self._sticky_sides.add(side)

        self._cur_p1 = P(p1x, p1y)
        self._cur_p2 = P(p2x, p2y)
    
    def _cancel_active_phases(self) -> None:
        for p in self._polygons:
            if p._phase not in ('open', 'close', ''):
                p.set_phase('open')
        for t in self._texts:
            if t._phase not in ('open', 'close', ''):
                t.set_phase('open')
        for btn in self._buttons:
            if btn._cur_phase not in ('open', 'close', ''):
                btn._pressed   = False
                btn._key_held  = False
                btn._hovered   = False
                btn._set_interaction_phase('unhover')
        for sl in self._sliders:
            if sl._dragging:
                sl._dragging = False
                sl.set_phase('released')
        for tb in self._textboxes:
            if tb._active:
                tb._deactivate()
        for sw in self._sub_windows:
            sw._cancel_active_phases()

    def _detect_edge(self, lx: float, ly: float, pw: int, ph: int) -> str:
        d     = self.defn.scale_edge_px
        left  = lx <= d
        right = lx >= pw - d
        top   = ly <= d
        bot   = ly >= ph - d

        if top    and left:  return 'tl'
        if top    and right: return 'tr'
        if bot    and left:  return 'bl'
        if bot    and right: return 'br'
        if left:             return 'l'
        if right:            return 'r'
        if top:              return 't'
        if bot:              return 'b'
        return ''
    
    def _window_retrigger_changed(self, phase_name, phase_def) -> bool:
        refs = _collect_tween_event_refs(phase_def)
        if not refs:
            return False
        prev = self._win_retrigger_snapshots.get(phase_name)
        if prev is None:
            return False
        return _snapshot_event_refs(refs) != prev

    def _update_window_retrigger_snapshot(self, phase_name, phase_def):
        refs = _collect_tween_event_refs(phase_def)
        if refs:
            self._win_retrigger_snapshots[phase_name] = _snapshot_event_refs(refs)
        else:
            self._win_retrigger_snapshots.pop(phase_name, None)

# ──────────────────────── EVENT DEF ────────────────────────

_pending_pulse_resets: List[EventDef] = []

@dataclass
class EventDef:
    name:      str
    value:     Any                          = None
    min_val:   Optional[Union[int, float]]  = None
    max_val:   Optional[Union[int, float]]  = None
    step:      Optional[Union[int, float]]  = None
    label:     str                          = ''
    unit:      str                          = ''
    delay:     float                        = 0.0
    _watchers: List[Callable]               = field(default_factory=list, repr=False, compare=False)

    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)
        if name == 'value':
            if value == 'pulse':
                if self not in _pending_pulse_resets:
                    _pending_pulse_resets.append(self)
            for w in self.__dict__.get('_watchers', []):
                try: w(value)
                except: pass

    @property
    def _is_numeric(self) -> bool:
        return isinstance(self.value, (int, float)) and not isinstance(self.value, bool)

    def _clamp(self, v: float) -> Union[int, float]:
        if self.min_val is not None: v = max(float(self.min_val), v)
        if self.max_val is not None: v = min(float(self.max_val), v)
        if self.step:                v = round(v / self.step) * self.step
        return int(round(v)) if isinstance(self.value, int) else float(v)

    def set_numeric(self, v: float) -> None:
        if self._is_numeric:
            self.value = self._clamp(v)

# ──────────────────────── EVENT LISTENER ────────────────────────

@dataclass
class EventListener:
    value_fn:         Callable[[Any], Any]             = None
    targets:          List[EventDef]                   = field(default_factory=list)
    passthrough:      bool                             = False
    transform:        Optional[Callable[[Any], Any]]   = None
    conditions:       List[Callable[[Any], bool]]      = field(default_factory=list)
    values:           List[Any]                        = field(default_factory=list)
    wait_for_updates: Optional[Callable[Any]]          = None
    skip_none:        bool                             = True
    _last_value:      Any                              = field(default=None, init=False, repr=False, compare=False)

    def _validate(self) -> bool:
        if self.passthrough:
            return True
        return len(self.values) == len(self.conditions) + 1

    def tick(self, ctx: Any) -> None:
        try:
            raw = self.value_fn(ctx) if callable(self.value_fn) else self.value_fn
        except Exception:
            raw = None

        if raw is None and self.skip_none:
            return

        if self.wait_for_updates is not None:
            if callable(self.wait_for_updates):
                try:
                    cur = self.wait_for_updates(ctx)
                except Exception:
                    return
            elif isinstance(self.wait_for_updates, EventDef):
                cur = self.wait_for_updates.value
            else:
                cur = self.wait_for_updates
            if cur == self._last_value:
                return
            if cur == 'ignore':   # skip reset-triggered firings
                self._last_value = cur
                return
            # print(self._last_value, cur)
            self._last_value = cur

        if self.passthrough:
            if self.transform is None:
                output = raw
            elif callable(self.transform):
                output = self.transform(raw)
            else:
                output = self.transform
        else:
            if not self._validate():
                return
            output = self.values[-1]
            for condition, value in zip(self.conditions, self.values):
                try:
                    if condition(raw):
                        output = value
                        break
                except Exception:
                    continue

        for target in self.targets:
            # if target.name == 'selected_marker_phase':
                # print(f'[listener] raw={raw!r} -> output={output!r}')
            target.value = output    








# I'll organise this later

@dataclass 
class _SpawnedInstance:
    obj_id:      str
    window:      'AnimatedWindow'
    group_event: EventDef
    closing:     bool = False


_spawn_group_events: Dict[str, List[EventDef]] = {}
GROUP_EVENT = '__group_event__'
SNAPSHOT_EVENT = '__snapshot_event__'
SELECT_EVENT = '__select_event__'
SELF_ID = '__self_id__'

def _snap_phase(animated_obj):
    for tw in animated_obj._tweens:
        if not isinstance(tw, Reset):
            animated_obj._snap_to(tw)
    animated_obj._idx = len(animated_obj._tweens)
    if hasattr(animated_obj, '_dirty'):
        animated_obj._dirty = True

def _alloc_group_event(group: str) -> EventDef:
    existing = _spawn_group_events.setdefault(group, [])
    used = {int(e.name[len(group):]) for e in existing if e.name[len(group):].isdigit()}
    idx = 1
    while idx in used:
        idx += 1
    ev = EventDef(name=f'{group}{idx}', value=0)
    existing.append(ev)
    return ev

def _free_group_event(group: str, ev: EventDef) -> None:
    lst = _spawn_group_events.get(group, [])
    if ev in lst:
        lst.remove(ev)

def get_spawn_events(group: str) -> List[EventDef]:
    return list(_spawn_group_events.get(group, []))

def get_spawn_event(group: str, index: int) -> Optional[EventDef]:
    name = f'{group}{index}'
    for ev in _spawn_group_events.get(group, []):
        if ev.name == name:
            return ev
    return None

class _StaticRef:
    __slots__ = ('index',)
    def __init__(self, index: int):
        self.index = index

def STATIC(index: int) -> _StaticRef:
    return _StaticRef(index)

def delete_spawned_by_id(parent_window: AnimatedWindow, obj_id: str) -> None:
    for inst in parent_window._spawned:
        if inst.obj_id == obj_id:
            inst.group_event.value = inst.window.defn.spawn_delete_threshold
            return

def clear_spawned_by_group(parent_window: AnimatedWindow, group: str) -> None:
    for inst in parent_window._spawned:
        if inst.window.defn.spawn_event_group == group:
            inst.group_event.value = inst.window.defn.spawn_delete_threshold

def _patch_fn_defaults(fn: Callable, new_defaults: tuple) -> Callable:
    import types
    try:
        return types.FunctionType(
            fn.__code__,
            fn.__globals__,
            fn.__name__,
            new_defaults,
            fn.__closure__,
        )
    except Exception as e:
        print(f'[_patch_fn_defaults] failed: {e}')
        return fn

_window_mouse_norm: Dict[int, P] = {}
_window_size_px: Dict[int, P] = {}

def get_window_size_px(wdef: 'WindowDef') -> P:
    return _window_size_px.get(id(wdef), P(0.0, 0.0))


_true_screen_w: int = MONITOR_RESOLUTIONS[0][0]
_true_screen_h: int = MONITOR_RESOLUTIONS[0][1]
_current_window_screen_offset: P = P(0.0, 0.0)

_slider_knob_positions: Dict[int, P] = {}

def get_slider_knob_pos(slider_def: 'SliderDef') -> P:
    return _slider_knob_positions.get(id(slider_def), P(0.0, 0.0))

def get_mouse_norm(wdef: 'WindowDef') -> P:
    return _window_mouse_norm.get(id(wdef), P(0.0, 0.0))

_current_spawn_window: Optional['AnimatedWindow'] = None
_current_update_window: Optional['AnimatedWindow'] = None

def get_own_window_size_px() -> P:
    if _current_update_window is None:
        return P(0.0, 0.0)
    return _window_size_px.get(id(_current_update_window.defn), P(0.0, 0.0))

def get_spawn_mouse_norm() -> P:
    if _current_spawn_window is None:
        return P(0.0, 0.0)
    w = _current_spawn_window
    if w._abs_ww <= 0 or w._abs_wh <= 0:
        return P(0.0, 0.0)
    return P(
        (SYS_MOUSE_ABS_X.value - w._abs_wx) / w._abs_ww,
        (SYS_MOUSE_ABS_Y.value - w._abs_wy) / w._abs_wh,
    )

def get_spawn_mouse_offset_px() -> P:
    if _current_spawn_window is None:
        return P(0.0, 0.0)
    w = _current_spawn_window
    if w._abs_ww <= 0 or w._abs_wh <= 0:
        return P(0.0, 0.0)
    return P(
        (SYS_MOUSE_ABS_X.value - w._abs_wx) - w._abs_ww / 2.0,
        (SYS_MOUSE_ABS_Y.value - w._abs_wy) - w._abs_wh / 2.0,
    )

def _reset_phase_override_event(ov) -> None:
    if ov is None:
        return
    try:
        if callable(ov):
            import inspect
            src = inspect.getclosurevars(ov)
            for val in list(src.nonlocals.values()) + list(src.globals.values()):
                if isinstance(val, EventDef):
                    val.value = None
                    return
    except Exception:
        pass

def _check_visible_threshold(defn: Any, ww: float, wh: float, cam_w: int, cam_h: int) -> bool:
    tx = defn.visible_threshold_x
    ty = defn.visible_threshold_y
    if tx > 0.0:
        px_thresh = tx * cam_w if tx <= 1.0 else tx
        if ww < px_thresh:
            return False
    if ty > 0.0:
        py_thresh = ty * cam_h if ty <= 1.0 else ty
        if wh < py_thresh:
            return False
    return True

_animated_window_registry: Dict[int, 'AnimatedWindow'] = {}

def get_animated_window(defn: 'WindowDef') -> Optional['AnimatedWindow']:
    return _animated_window_registry.get(id(defn))





# ──────────────────────── DATA CHANNEL ────────────────────────

def _is_numeric(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


class DataChannel:
    def __init__(self, name: str, max_samples: int = 100, unit: str = '') -> None:
        self.name        = name
        self.max_samples = max_samples
        self.unit        = unit
        self._lock   = threading.Lock()
        self._buffer: collections.deque[Any] = collections.deque(maxlen=max_samples)
        self._push_count = 0

    def push(self, value: Any) -> None:
        with self._lock:
            self._buffer.append(value)
            self._push_count += 1

    @property
    def latest(self) -> Optional[Any]:
        with self._lock:
            return self._buffer[-1] if self._buffer else None

    @property
    def samples(self) -> List[Any]:
        with self._lock:
            return list(self._buffer)

    @property
    def count(self) -> int:
        with self._lock:
            return len(self._buffer)

    def average(self) -> Optional[float]:
        with self._lock:
            data = [v for v in self._buffer if _is_numeric(v)]
        return statistics.mean(data) if data else None

    def minimum(self) -> Optional[float]:
        with self._lock:
            data = [v for v in self._buffer if _is_numeric(v)]
        return min(data) if data else None

    def maximum(self) -> Optional[float]:
        with self._lock:
            data = [v for v in self._buffer if _is_numeric(v)]
        return max(data) if data else None

    def delta(self) -> Optional[float]:
        with self._lock:
            if len(self._buffer) < 2:
                return None
            a, b = self._buffer[-2], self._buffer[-1]
        if not (_is_numeric(a) and _is_numeric(b)):
            return None
        return b - a

    def trend(self) -> Optional[float]:
        with self._lock:
            data = [v for v in self._buffer if _is_numeric(v)]
        n = len(data)
        if n < 2:
            return None
        xs    = range(n)
        x_bar = (n - 1) / 2.0
        y_bar = sum(data) / n
        num   = sum((x - x_bar) * (y - y_bar) for x, y in zip(xs, data))
        den   = sum((x - x_bar) ** 2 for x in xs)
        return num / den if den else 0.0

    def snapshot(self) -> Dict[str, Any]:
        raw     = self.samples
        numeric = [v for v in raw if _is_numeric(v)]
        n_raw   = len(raw)
        n_num   = len(numeric)

        lat = raw[-1] if raw else None
        avg = statistics.mean(numeric) if numeric else None
        mn  = min(numeric)             if numeric else None
        mx  = max(numeric)             if numeric else None

        if n_raw >= 2 and _is_numeric(raw[-1]) and _is_numeric(raw[-2]):
            dlt = raw[-1] - raw[-2]
        else:
            dlt = None

        if n_num >= 2:
            x_bar = (n_num - 1) / 2.0
            y_bar = avg
            num   = sum((x - x_bar) * (y - y_bar) for x, y in enumerate(numeric))
            den   = sum((x - x_bar) ** 2 for x in range(n_num))
            slope = num / den if den else 0.0
        else:
            slope = None

        return {
            'latest':  lat,
            'average': avg,
            'minimum': mn,
            'maximum': mx,
            'delta':   dlt,
            'trend':   slope,
            'samples': raw,
            'count':   n_raw,
            'push_count': self._push_count,
            'unit':    self.unit,
        }

# ──────────────────────── Helpers ────────────────────────

def set_true_screen_size(w: int, h: int) -> None:
    global _true_screen_w, _true_screen_h
    _true_screen_w, _true_screen_h = w, h

def get_true_screen_size() -> Tuple[int, int]:
    return _true_screen_w, _true_screen_h

def reset_window_screen_offset() -> None:
    global _current_window_screen_offset
    _current_window_screen_offset = P(0.0, 0.0)

def _ease(t: float, curve) -> float:
    # Common curves
    if curve == QEasingCurve.OutQuint:  return 1.0 - (1.0 - t) ** 5
    if curve == QEasingCurve.Linear:    return t
    if curve == QEasingCurve.OutCubic:  return 1.0 - (1.0 - t) ** 3
    if curve == QEasingCurve.OutQuad:   return 1.0 - (1.0 - t) ** 2
    # Less common curves
    if curve == QEasingCurve.OutCirc:
        t2 = t - 1.0; return _math.sqrt(max(0.0, 1.0 - t2 * t2))
    if curve == QEasingCurve.InQuint:   return t ** 5
    if curve == QEasingCurve.InOutCirc:
        if t < 0.5:
            return 0.5 * (1.0 - _math.sqrt(max(0.0, 1.0 - 4.0 * t * t)))
        t2 = 2.0 * t - 2.0; return 0.5 * (_math.sqrt(max(0.0, 1.0 - t2 * t2)) + 1.0)
    if curve == QEasingCurve.OutBack:
        c = 1.70158; t2 = t - 1.0
        return 1.0 + (c + 1.0) * t2 ** 3 + c * t2 ** 2
    if curve == QEasingCurve.InOutQuad:
        if t < 0.5: return 2.0 * t * t
        return 1.0 - (-2.0 * t + 2.0) ** 2 * 0.5
    if curve == QEasingCurve.InCirc:    return 1.0 - _math.sqrt(max(0.0, 1.0 - t * t))
    if curve == QEasingCurve.InCubic:   return t ** 3
    if curve == QEasingCurve.InQuad:    return t * t
    if curve == QEasingCurve.OutSine:   return _math.sin(t * _math.pi * 0.5)
    if curve == QEasingCurve.InSine:    return 1.0 - _math.cos(t * _math.pi * 0.5)
    c = QEasingCurve(curve); return c.valueForProgress(t)

def _ease_inverse(y: float, curve) -> float:
    if y <= 0.0: return 0.0
    if y >= 1.0: return 1.0
    if curve == QEasingCurve.Linear:    return y
    if curve == QEasingCurve.OutQuint:  return 1.0 - (1.0 - y) ** 0.2
    if curve == QEasingCurve.InQuint:   return y ** 0.2
    if curve == QEasingCurve.OutCubic:  return 1.0 - (1.0 - y) ** (1/3)
    if curve == QEasingCurve.InCubic:   return y ** (1/3)
    if curve == QEasingCurve.OutQuad:   return 1.0 - _math.sqrt(1.0 - y)
    if curve == QEasingCurve.InQuad:    return _math.sqrt(y)
    if curve == QEasingCurve.OutCirc:   return _math.sqrt(1.0 - (1.0 - y)**2)
    if curve == QEasingCurve.InCirc:    return _math.sqrt(1.0 - (1.0 - y*y))
    lo, hi = 0.0, 1.0
    for _ in range(24):
        mid = (lo + hi) * 0.5
        if _ease(mid, curve) < y: lo = mid
        else: hi = mid
    return (lo + hi) * 0.5

def _tw_replace(tw, **kwargs):
    d = {**tw.__dict__, **kwargs}
    return type(tw)(**d)

def lerp_color(src: QColor, dst: QColor, v: float) -> QColor:
    if v <= 0.0: return QColor(src)
    if v >= 1.0: return QColor(dst)
    iv = 1.0 - v
    return QColor(
        int(src.red()   * iv + dst.red()   * v + 0.5),
        int(src.green() * iv + dst.green() * v + 0.5),
        int(src.blue()  * iv + dst.blue()  * v + 0.5),
        int(src.alpha() * iv + dst.alpha() * v + 0.5),
    )

def _with_alpha(color, alpha):
    c=QColor(color); c.setAlpha(alpha); return c

def _derive_button_colors(base: QColor):
    avg = (base.red() + base.green() + base.blue()) / 3 / 255
    is_light = avg >= 0.5
    factor_hover = 0.75 if is_light else 1.4
    factor_click = 0.55 if is_light else 1.7
    def _scale(c, f): return max(0, min(255, int(c * f)))
    hover = QColor(_scale(base.red(), factor_hover),_scale(base.green(), factor_hover),_scale(base.blue(),  factor_hover),base.alpha())
    click = QColor(_scale(base.red(), factor_click),_scale(base.green(), factor_click),_scale(base.blue(),  factor_click),base.alpha())
    return hover, click

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
                p             = _pts(tw.p, prev_blended) if tw.p is not None else None,
                px            = _pxs(tw.px) if tw.px is not None else None,
                fill_color    = tw.fill_color,
                outline_color = tw.outline_color,
                outline_width    = tw.outline_width,
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
        p             = _pts(defn.p),
        px            = _pxs(defn.px) if defn.px is not None else None,
        fill_color    = defn.fill_color,
        outline_color = defn.outline_color,
        outline_width    = defn.outline_width,
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

def _draw_partial_polyline(painter: QPainter, pts: List[QPointF], t: float) -> None:
    if len(pts) < 2 or t <= 0:
        return
    if t >= 1.0:
        for i in range(len(pts) - 1):
            if pts[i] == pts[i + 1]:
                continue
            painter.drawLine(pts[i], pts[i + 1])
        return
    lengths = [_math.sqrt((pts[i+1].x()-pts[i].x())**2 + (pts[i+1].y()-pts[i].y())**2) for i in range(len(pts) - 1)]
    total = sum(lengths)
    if total == 0:
        return
    target = total * t
    acc = 0.0
    for i, seg_len in enumerate(lengths):
        if acc >= target:
            break
        if seg_len == 0:
            continue
        rem = target - acc
        if rem >= seg_len:
            painter.drawLine(pts[i], pts[i + 1])
            acc += seg_len
        else:
            frac = rem / seg_len
            painter.drawLine(pts[i], QPointF(pts[i].x() + (pts[i+1].x() - pts[i].x()) * frac, pts[i].y() + (pts[i+1].y() - pts[i].y()) * frac))
            break


def _resolve_rotation(cur_rot_center_p, cur_rot_center_px, cur_rot_target_p, cur_rot_target_px, cur_rot_angle_initial, cur_rot_angle, ww: int, wh: int) -> Optional[Tuple[float, float, float]]:
    net = cur_rot_angle - cur_rot_angle_initial
    if net == 0.0:
        return None

    cx = cur_rot_center_p.x * ww + cur_rot_center_px.x
    cy = cur_rot_center_p.y * wh + cur_rot_center_px.y

    return cx, cy, net

def _resolve_angle_value(val, ctx=None) -> float:
    if val is None:
        return 0.0
    if isinstance(val, EventDef):
        v = val.value
        return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else 0.0
    if callable(val):
        try:
            v = val()
        except TypeError:
            try:
                v = val(ctx)
            except Exception:
                return 0.0
        except Exception:
            return 0.0
        return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else 0.0
    if isinstance(val, (int, float)):
        return float(val)
    return 0.0

def _resolve_bool_value(val) -> bool:
    if val is None:
        return False
    if isinstance(val, EventDef):
        return bool(val.value)
    if callable(val):
        try:    return bool(val())
        except: return False
    return bool(val)

def _resolve_numeric_value(val, default: float = 0.0) -> float:
    if val is None:
        return default
    if isinstance(val, EventDef):
        v = val.value
        return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else default
    if callable(val):
        try:
            v = val()
            return float(v) if isinstance(v, (int, float)) else default
        except Exception: 
            return default
    if isinstance(val, (int, float)):
        return float(val)
    return default

def _resolve_tween_event_refs(tw):
    changes = {}

    if isinstance(tw, PolygonTween):
        for attr in ('p', 'px'):
            val = getattr(tw, attr)
            if isinstance(val, _RectCornerRef):
                changes[attr] = _rect_corner_ref_to_points(val)
            elif isinstance(val, EventDef):
                ev_val = val.value
                if isinstance(ev_val, list):
                    changes[attr] = [P(pt.x, pt.y) for pt in ev_val if isinstance(pt, P)]
                elif isinstance(ev_val, P):
                    changes[attr] = [P(ev_val.x, ev_val.y)]

    elif isinstance(tw, TextTween):
        for attr in ('p', 'px'):
            val = getattr(tw, attr)
            if isinstance(val, EventDef):
                ev_val = val.value
                if isinstance(ev_val, P):
                    changes[attr] = P(ev_val.x, ev_val.y)
                elif isinstance(ev_val, list) and ev_val and isinstance(ev_val[0], P):
                    changes[attr] = P(ev_val[0].x, ev_val[0].y)

    elif isinstance(tw, WindowTween):
        for attr in ('p1', 'p2', 'px1', 'px2'):
            val = getattr(tw, attr)
            if isinstance(val, EventDef):
                ev_val = val.value
                if isinstance(ev_val, P):
                    changes[attr] = P(ev_val.x, ev_val.y)

    if changes:
        return _tw_replace(tw, **changes)
    return tw

def _collect_tween_event_refs(phase_def):
    refs = []
    for tw in phase_def.tweens:
        if isinstance(tw, Reset):
            continue
        for attr in ('p', 'px', 'p1', 'p2', 'px1', 'px2'):
            val = getattr(tw, attr, None)
            if isinstance(val, EventDef):
                refs.append(val)
    return refs

def _snapshot_event_refs(refs):
    return tuple(list(ev.value) if isinstance(ev.value, list) else ev.value for ev in refs)


# ──────────────────────── PHASE KEYS ────────────────────────

class PhaseKey:
    __slots__ = ('name',)
    def __init__(self, name: str) -> None:
        self.name = name
    def __repr__(self) -> str:
        return f'PhaseKey({self.name!r})'
    def __str__(self) -> str:
        return self.name
    def __hash__(self) -> int:
        return hash(self.name)
    def __eq__(self, other) -> bool:
        if isinstance(other, PhaseKey):
            return self.name == other.name
        if isinstance(other, str):
            return self.name == other
        return NotImplemented

# Common phases
P_OPEN     = PhaseKey('open')
P_CLOSE    = PhaseKey('close')
P_HOVER    = PhaseKey('hover')
P_UNHOVER  = PhaseKey('unhover')
P_CLICK    = PhaseKey('click')
P_RELEASE  = PhaseKey('release')
P_SET      = PhaseKey('set')
P_ALWAYS   = PhaseKey('always')

def _get_phase_def(phases: dict, phase: str):
    if phase in phases:
        return phases[phase]
    for key, val in phases.items():
        if isinstance(key, tuple) and phase in key:
            return val
    return None

def _phase_key_exists(phases: dict, name) -> bool:
    if name in phases:
        return True
    for key in phases:
        if isinstance(key, tuple) and name in key:
            return True
    return False

def _phase_key_name(key) -> str:
    if isinstance(key, PhaseKey): return key.name
    if isinstance(key, str):      return key
    if isinstance(key, tuple):    return _phase_key_name(key[0])
    return str(key)

SYS_FPS        = EventDef(name='__sys_fps__',        value=0.0)
SYS_FRAME_TIME = EventDef(name='__sys_frame_time__', value=0.0)   # ms per frame
SYS_MOUSE      = EventDef(name='__sys_mouse__',      value=(0.0, 0.0))
SYS_MOUSE_X    = EventDef(name='__sys_mouse_x__',    value=0.0)
SYS_MOUSE_Y    = EventDef(name='__sys_mouse_y__',    value=0.0)
SYS_MOUSE_ABS_X = EventDef(name='__sys_mouse_abs_x__', value=0.0)
SYS_MOUSE_ABS_Y = EventDef(name='__sys_mouse_abs_y__', value=0.0)