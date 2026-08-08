from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple
import math

from PySide6.QtCore import Qt, QEasingCurve
from PySide6.QtGui  import QColor

from spear_gui.overlay_system import (
    P, Reset, Phase, expand_defs,
    PolygonDef, PolygonTween, RectDef, RectTween,                              # PolygonDef
    ArcDef,                                                                    # ArcDef
    TextDef, TextTween, TextBlock, DataTable,                                  # TextDef
    BasicSliderDef, SliderDef,                                                 # SliderDef
    ButtonDef, SegmentedButtons, Segment, SevenSegmentDisplay,                 # ButtonDef
    TextboxDef,                                                                # TextboxDef
    GraphDef, SeriesDef,                                                       # GraphDef
    PieDef,                                                                    # PieDef
    WindowDef, WindowTween, register_windows,                                  # WindowDef
    EventDef, EventListener, register_event, get_event,                        # EventDef
    GradientDef, GradientStop, GradientTween, register_gradient, get_gradient, # GradientDef

    P_OPEN, P_CLOSE, P_HOVER, P_UNHOVER, P_CLICK, P_RELEASE, P_SET, P_ALWAYS,
    SYS_FPS, SYS_FRAME_TIME, SYS_MOUSE, SYS_MOUSE_X, SYS_MOUSE_Y,
    get_spawn_event, GROUP_EVENT, STATIC, get_spawn_mouse_norm, get_spawn_mouse_offset_px, get_own_window_size_px,
    get_animated_window
)

from datetime import datetime
from zoneinfo import ZoneInfo

WINDOW_LAYER = 10


register_gradient(GradientDef(
    name='startup_grid', p1=P(0.5, 0.5), p2=P(1, 1), radial=True, target='outline', stops=[
        GradientStop(0.0, QColor(0, 0, 0, 0)),
        GradientStop(1.0, QColor(0, 0, 0, 0)),
    ], phase_event=get_event('layout_page'), phases={
        'open': Phase([GradientTween(stops=[GradientStop(0.0, QColor(0, 0, 0, 50)), GradientStop(1.0, QColor(0, 0, 0, 0))], start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
        'close': Phase([GradientTween(stops=[GradientStop(0.0, QColor(0, 0, 0, 0)), GradientStop(1.0, QColor(0, 0, 0, 0))], start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
    }
))

register_gradient(GradientDef(
    name='layout_white_fill', p1=P(0, 0), p2=P(1, 1), px1=P(-3, -3), px2=P(3, 3), target='fill', global_position=True, stops=[
        GradientStop(0.0, QColor(170, 170, 170, 255)),
        GradientStop(0.0001, QColor(170, 170, 170, 255)),
        GradientStop(0.0002, QColor(170, 170, 170, 0)),
        GradientStop(1.0, QColor(170, 170, 170, 0)),
    ], phase_event=get_event('layout_page'), phases={
        'open': Phase([GradientTween(stops=[GradientStop(0.0, QColor(170, 170, 170, 255)), GradientStop(0.9998, QColor(170, 170, 170, 255)), GradientStop(0.9999, QColor(170, 170, 170, 0)), GradientStop(1.00, QColor(170, 170, 170, 0))], start=0, dur=1.0, ease=QEasingCurve.OutExpo)]),
        'close': Phase([GradientTween(stops=[GradientStop(0.0, QColor(170, 170, 170, 255)), GradientStop(0.0001, QColor(170, 170, 170, 255)), GradientStop(0.0002, QColor(170, 170, 170, 0)), GradientStop(1.00, QColor(170, 170, 170, 0))], start=0, dur=1.0, ease=QEasingCurve.OutExpo)]),
    }
))

register_gradient(GradientDef(
    name='layout_black_fill', p1=P(0, 0), p2=P(1, 1), px1=P(-3, -3), px2=P(3, 3), target='fill', global_position=True, stops=[
        GradientStop(0.0, QColor(0, 0, 0, 255)),
        GradientStop(0.0001, QColor(0, 0, 0, 255)),
        GradientStop(0.0002, QColor(0, 0, 0, 0)),
        GradientStop(1.0, QColor(0, 0, 0, 0)),
    ], phase_event=get_event('layout_page'), phases={
        'open': Phase([GradientTween(stops=[GradientStop(0.0, QColor(0, 0, 0, 255)), GradientStop(0.9998, QColor(0, 0, 0, 255)), GradientStop(0.9999, QColor(0, 0, 0, 0)), GradientStop(1.00, QColor(0, 0, 0, 0))], start=0, dur=1.0, ease=QEasingCurve.OutExpo)]),
        'close': Phase([GradientTween(stops=[GradientStop(0.0, QColor(0, 0, 0, 255)), GradientStop(0.0001, QColor(0, 0, 0, 255)), GradientStop(0.0002, QColor(0, 0, 0, 0)), GradientStop(1.00, QColor(0, 0, 0, 0))], start=0, dur=1.0, ease=QEasingCurve.OutExpo)]),
    }
))

register_gradient(GradientDef(
    name='layout_black_outline', p1=P(0, 0), p2=P(1, 1), px1=P(-3, -3), px2=P(3, 3), target='outline', global_position=True, stops=[
        GradientStop(0.0, QColor(0, 0, 0, 255)),
        GradientStop(0.0001, QColor(0, 0, 0, 255)),
        GradientStop(0.0002, QColor(0, 0, 0, 0)),
        GradientStop(1.0, QColor(0, 0, 0, 0)),
    ], phase_event=get_event('layout_page'), phases={
        'open': Phase([GradientTween(stops=[GradientStop(0.0, QColor(0, 0, 0, 255)), GradientStop(0.9998, QColor(0, 0, 0, 255)), GradientStop(0.9999, QColor(0, 0, 0, 0)), GradientStop(1.00, QColor(0, 0, 0, 0))], start=0, dur=1.0, ease=QEasingCurve.OutExpo)]),
        'close': Phase([GradientTween(stops=[GradientStop(0.0, QColor(0, 0, 0, 255)), GradientStop(0.0001, QColor(0, 0, 0, 255)), GradientStop(0.0002, QColor(0, 0, 0, 0)), GradientStop(1.00, QColor(0, 0, 0, 0))], start=0, dur=1.0, ease=QEasingCurve.OutExpo)]),
    }
))

register_gradient(GradientDef(
    name='layout_black_translucent_fill', p1=P(0, 0), p2=P(1, 1), px1=P(-3, -3), px2=P(3, 3), target='fill', global_position=True, stops=[
        GradientStop(0.0, QColor(0, 0, 0, 100)),
        GradientStop(0.0001, QColor(0, 0, 0, 100)),
        GradientStop(0.0002, QColor(0, 0, 0, 0)),
        GradientStop(1.0, QColor(0, 0, 0, 0)),
    ], phase_event=get_event('layout_page'), phases={
        'open': Phase([GradientTween(stops=[GradientStop(0.0, QColor(0, 0, 0, 100)), GradientStop(0.9998, QColor(0, 0, 0, 100)), GradientStop(0.9999, QColor(0, 0, 0, 0)), GradientStop(1.00, QColor(0, 0, 0, 0))], start=0, dur=1.0, ease=QEasingCurve.OutExpo)]),
        'close': Phase([GradientTween(stops=[GradientStop(0.0, QColor(0, 0, 0, 100)), GradientStop(0.0001, QColor(0, 0, 0, 100)), GradientStop(0.0002, QColor(0, 0, 0, 0)), GradientStop(1.00, QColor(0, 0, 0, 0))], start=0, dur=1.0, ease=QEasingCurve.OutExpo)]),
    }
))

register_gradient(GradientDef(
    name='layout_red_fill', p1=P(0, 0), p2=P(1, 1), px1=P(-3, -3), px2=P(3, 3), target='fill', global_position=True, stops=[
        GradientStop(0.0, QColor(150, 0, 0, 100)),
        GradientStop(0.0001, QColor(150, 0, 0, 100)),
        GradientStop(0.0002, QColor(150, 0, 0, 0)),
        GradientStop(1.0, QColor(150, 0, 0, 0)),
    ], phase_event=get_event('layout_page'), phases={
        'open': Phase([GradientTween(stops=[GradientStop(0.0, QColor(150, 0, 0, 100)), GradientStop(0.9998, QColor(150, 0, 0, 100)), GradientStop(0.9999, QColor(150, 0, 0, 0)), GradientStop(1.00, QColor(150, 0, 0, 0))], start=0, dur=1.0, ease=QEasingCurve.OutExpo)]),
        'close': Phase([GradientTween(stops=[GradientStop(0.0, QColor(150, 0, 0, 100)), GradientStop(0.0001, QColor(150, 0, 0, 100)), GradientStop(0.0002, QColor(150, 0, 0, 0)), GradientStop(1.00, QColor(150, 0, 0, 0))], start=0, dur=1.0, ease=QEasingCurve.OutExpo)]),
    }
))

register_gradient(GradientDef(
    name='layout_overlap_detected', p1=P(0, 0), p2=P(1, 1), px1=P(-3, -3), px2=P(3, 3), target='fill', global_position=True, stops=[
        GradientStop(0.0, QColor(150, 0, 0, 100)),
        GradientStop(0.0001, QColor(150, 0, 0, 100)),
        GradientStop(0.0002, QColor(150, 0, 0, 0)),
        GradientStop(1.0, QColor(150, 0, 0, 0)),
    ], phase_event=get_event('layout_overlap_phase'), phases={
        'open': Phase([GradientTween(stops=[GradientStop(0.0, QColor(150, 0, 0, 100)), GradientStop(0.9998, QColor(150, 0, 0, 100)), GradientStop(0.9999, QColor(150, 0, 0, 0)), GradientStop(1.00, QColor(150, 0, 0, 0))], start=0, dur=1.0, ease=QEasingCurve.OutExpo)]),
        'close': Phase([GradientTween(stops=[GradientStop(0.0, QColor(150, 0, 0, 100)), GradientStop(0.0001, QColor(150, 0, 0, 100)), GradientStop(0.0002, QColor(150, 0, 0, 0)), GradientStop(1.00, QColor(150, 0, 0, 0))], start=0, dur=1.0, ease=QEasingCurve.OutExpo)]),
    }
))





background_polygons = [
    RectDef(p1=P(0, 0), p2=P(1, 1), gradient=get_gradient('layout_white_fill'), phase_override=get_event('layout_page'))
]

for i in range(19):
    px = (i - 9) * 120
    background_polygons += [
        PolygonDef(p=[P(0.5, 0), P(0.5, 1)], px=[P(px, 0), P(px, 0)], outline_color=QColor(255, 255, 255, 10), gradient=get_gradient('startup_grid'), outline_width=1),
    ]
for i in range(11):
    py = (i - 5) * 120
    background_polygons += [
        PolygonDef(p=[P(0, 0.5), P(1, 0.5)], px=[P(0, py), P(0, py)], outline_color=QColor(255, 255, 255, 10), gradient=get_gradient('startup_grid'), outline_width=1, phases={
            'always': Phase([PolygonTween(px=[P(0, 120), P(0, 120)], start=0.0, dur=5.0, ease=QEasingCurve.Linear)], loop=True, stop_phases=['close']),
        }),
    ]




WINDOW_NAMES = ['map', 'logger', 'info', 'task']

def _make_hidden_event(name: str):
    def _fn():
        if not get_event('layout_mode').value:
            return False
        sel = get_event('layout_selected_window').value
        if sel is not None:
            return sel != name
        return get_event(f'window_disabled_{name}').value
    return _fn

def _toggle_window_selection(name: str):
    def _fn():
        if not get_event('layout_mode').value:
            return
        cur = get_event('layout_selected_window').value
        get_event('layout_selected_window').value = None if cur == name else name
    return _fn

def _toggle_disable_selected():
    if not get_event('layout_mode').value:
        return
    sel = get_event('layout_selected_window').value
    if sel is None:
        return
    ev = get_event(f'window_disabled_{sel}')
    ev.value = not ev.value

def _reset_layout_selection():
    get_event('layout_selected_window').value = None

def _window_highlight_phase(name: str):
    def _fn():
        sel = get_event('layout_selected_window').value
        if sel != name:
            return 'unselected'
        return 'selected_disabled' if get_event(f'window_disabled_{name}').value else 'selected_enabled'
    return _fn

def _make_highlight_outline(name: str) -> RectDef:
    return RectDef(
        p1=P(0, 0), p2=P(1, 1), fill_color=QColor(0, 0, 0, 0), outline_color=QColor(0, 0, 0, 0), outline_width=8,
        phase_override=_window_highlight_phase(name),
        phases={
            'unselected':        Phase([RectTween(outline_color=QColor(0, 0, 0, 0),       start=0, dur=0.3, ease=QEasingCurve.OutQuint)]),
            'selected_enabled':  Phase([RectTween(outline_color=QColor(80, 220, 120, 255), start=0, dur=0.3, ease=QEasingCurve.OutQuint)]),
            'selected_disabled': Phase([RectTween(outline_color=QColor(220, 80, 80, 255),  start=0, dur=0.3, ease=QEasingCurve.OutQuint)]),
        },
    )





WINDOW_EXPORTS = {
    'map':    ('map_window_p1', 'map_window_px1', 'map_window_p2', 'map_window_px2'),
    'logger': ('logger_window_p1', 'logger_window_px1', 'logger_window_p2', 'logger_window_px2'),
    'info':   ('info_window_p1', 'info_window_px1', 'info_window_p2', 'info_window_px2'),
    'task':  ('task_window_p1', 'task_window_px1', 'task_window_p2', 'task_window_px2'),
}

def _window_abs_rect(name: str, W: float, H: float) -> Tuple[float, float, float, float]:
    p1n, px1n, p2n, px2n = WINDOW_EXPORTS[name]
    p1, px1 = get_event(p1n).value, get_event(px1n).value
    p2, px2 = get_event(p2n).value, get_event(px2n).value
    x1, y1 = p1.x * W + px1.x, p1.y * H + px1.y
    x2, y2 = p2.x * W + px2.x, p2.y * H + px2.y
    return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))

def _rects_overlap(a, b) -> bool:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    return ax1 < bx2 and bx1 < ax2 and ay1 < by2 and by1 < ay2

def _check_overlap(args) -> None:
    from spear_gui.overlay_system import get_true_screen_size
    W, H = get_true_screen_size()
    if W <= 0 or H <= 0:
        return None
    active = [n for n in WINDOW_NAMES if not get_event(f'window_disabled_{n}').value]
    rects = [_window_abs_rect(n, W, H) for n in active]
    overlap = any(
        _rects_overlap(rects[i], rects[j])
        for i in range(len(rects)) for j in range(i + 1, len(rects))
    )
    get_event('layout_overlap_detected').value = overlap
    return None

FULLSCREEN_P1  = P(0, 0)
FULLSCREEN_P2  = P(1, 1)
FULLSCREEN_PX1 = P(70, 0)
FULLSCREEN_PX2 = P(-70, 0)

register_event(EventDef(name='fullscreen_selection', value=None))

register_event(EventDef(name='layout_win_map_base_p1',  value=P(0.0, 0.0)))
register_event(EventDef(name='layout_win_map_base_p2',  value=P(1040/1920, 0.6)))
register_event(EventDef(name='layout_win_map_base_px1', value=P(0, 0)))
register_event(EventDef(name='layout_win_map_base_px2', value=P(0, 0)))

register_event(EventDef(name='layout_win_logger_base_p1',  value=P((740+70)/1920, 0.0)))
register_event(EventDef(name='layout_win_logger_base_p2',  value=P(1-(740+70)/1920, 1.0)))
register_event(EventDef(name='layout_win_logger_base_px1', value=P(0, 0)))
register_event(EventDef(name='layout_win_logger_base_px2', value=P(0, 0)))

register_event(EventDef(name='layout_win_info_base_p1',  value=P(0.0, 0.6)))
register_event(EventDef(name='layout_win_info_base_p2',  value=P(1040/1920, 1.0)))
register_event(EventDef(name='layout_win_info_base_px1', value=P(0, 0)))
register_event(EventDef(name='layout_win_info_base_px2', value=P(0, 0)))

register_event(EventDef(name='layout_win_task_base_p1',  value=P(1-(740)/1920, 0.0)))
register_event(EventDef(name='layout_win_task_base_p2',  value=P(1.0, 1.0)))
register_event(EventDef(name='layout_win_task_base_px1', value=P(0, 0)))
register_event(EventDef(name='layout_win_task_base_px2', value=P(0, 0)))

def _toggle_fullscreen_window(name: str):
    def _fn():
        prev    = get_event('fullscreen_selection').value
        new_sel = None if prev == name else name
        if prev is not None:
            anim_prev = get_animated_window(WINDOW_DEF_REFS[prev])
            if anim_prev is not None:
                anim_prev.set_rect_instant(
                    get_event(f'layout_win_{prev}_base_p1').value,
                    get_event(f'layout_win_{prev}_base_p2').value,
                    get_event(f'layout_win_{prev}_base_px1').value,
                    get_event(f'layout_win_{prev}_base_px2').value,
                )

        get_event('fullscreen_selection').value = new_sel

        if new_sel is not None:
            anim_new = get_animated_window(WINDOW_DEF_REFS[new_sel])
            if anim_new is not None:
                anim_new.set_rect_instant(FULLSCREEN_P1, FULLSCREEN_P2, FULLSCREEN_PX1, FULLSCREEN_PX2)
    return _fn

def _content_phase_excluded(name: str):
    def _fn(v):
        sel = v[1]
        return sel is not None and sel != name
    return _fn

def _clear_fullscreen_on_layout_mode(v):
    if v:
        cur = get_event('fullscreen_selection').value
        if cur is not None:
            _toggle_fullscreen_window(cur)()   # reverts cur to base, clears selection
    return None

def _key_1_4_action(name: str):
    toggle_fs = _toggle_fullscreen_window(name)
    def _fn():
        if get_event('layout_mode').value:
            cur = get_event('layout_selected_window').value
            get_event('layout_selected_window').value = None if cur == name else name
        else:
            toggle_fs()
    return _fn

# MAP WINDOW
map_window = WindowDef(
    p1=P(0.0, 0.0), p2=P((1040-70)/1920, 0.6), px1=P(0, 0), px2=P(0, 0),
    hidden_event=_make_hidden_event('map'),
    export_p1=get_event('map_window_p1'),
    export_p2=get_event('map_window_p2'),
    export_px1=get_event('map_window_px1'),
    export_px2=get_event('map_window_px2'),
    draggable=True, scalable=True, grid_snap_pixel=True, force_boundary=True, sticky_boundary=True, grid_snap_x=10, grid_snap_y=10, drag_boundary_px1=P(70, 0), drag_boundary_px2=P(-70, 0),
    ignore_mouse_event=lambda: not get_event('layout_mode').value,
    polygon_defs=[
        RectDef(p1=P(0, 0), p2=P(1, 0), px2=P(0, 10), gradient=get_gradient('layout_black_fill')),
        RectDef(p1=P(0, 1), p2=P(1, 1), px1=P(0, -10), gradient=get_gradient('layout_black_fill')),
        RectDef(p1=P(0, 0), p2=P(1, 1), fill_color=QColor(255, 0, 0, 0), gradient=get_gradient('layout_black_outline'), outline_width=4),
        RectDef(p1=P(0, 0), p2=P(1, 0), px2=P(0, 40), fill_color=QColor(255, 0, 0, 0), gradient=get_gradient('layout_black_outline'), outline_width=2),
        _make_highlight_outline('map')
    ],
    text_defs=[
        TextDef(p=P(0, 0), px=P(2, 38), text='1.', bold=True, h_align=0, v_align=1, font_size=16, gradient=get_gradient('layout_black_fill')),
        TextDef(p=P(0, 0), px=P(2, 42), text='MAP', bold=True, h_align=0, v_align=0, font_size=70, gradient=get_gradient('layout_black_fill')),
        TextDef(p=P(0, 0), px=P(32, 38), text='<#> x <#>', h_align=0, v_align=1, font_size=16, gradient=get_gradient('layout_black_fill'), text_fn=lambda ctx: [
            f'{get_own_window_size_px().x:.0f}',
            f'{get_own_window_size_px().y:.0f}',
        ])
    ]
)

# LOGGER WINDOW
logger_window = WindowDef(
    p1=P((740+70)/1920, 0.0), p2=P(1-(740+70)/1920, 1.0), px1=P(0, 0), px2=P(0, 0),
    hidden_event=_make_hidden_event('logger'),
    export_p1=get_event('logger_window_p1'),
    export_p2=get_event('logger_window_p2'),
    export_px1=get_event('logger_window_px1'),
    export_px2=get_event('logger_window_px2'),
    draggable=True, scalable=True, grid_snap_pixel=True, force_boundary=True, sticky_boundary=True, grid_snap_x=10, grid_snap_y=10, drag_boundary_px1=P(70, 0), drag_boundary_px2=P(-70, 0),
    ignore_mouse_event=lambda: not get_event('layout_mode').value,
    polygon_defs=[
        RectDef(p1=P(0, 0), p2=P(1, 0), px2=P(0, 10), gradient=get_gradient('layout_black_fill')),
        RectDef(p1=P(0, 1), p2=P(1, 1), px1=P(0, -10), gradient=get_gradient('layout_black_fill')),
        RectDef(p1=P(0, 0), p2=P(1, 1), fill_color=QColor(255, 0, 0, 0), gradient=get_gradient('layout_black_outline'), outline_width=4),
        RectDef(p1=P(0, 0), p2=P(1, 0), px2=P(0, 40), fill_color=QColor(255, 0, 0, 0), gradient=get_gradient('layout_black_outline'), outline_width=2),
        _make_highlight_outline('logger')
    ],
    text_defs=[
        TextDef(p=P(0, 0), px=P(2, 38), text='2.', bold=True, h_align=0, v_align=1, font_size=16, gradient=get_gradient('layout_black_fill')),
        TextDef(p=P(0, 0), px=P(2, 42), text='LOGGER', bold=True, h_align=0, v_align=0, font_size=70, gradient=get_gradient('layout_black_fill')),
        TextDef(p=P(0, 0), px=P(32, 38), text='<#> x <#>', h_align=0, v_align=1, font_size=16, gradient=get_gradient('layout_black_fill'), text_fn=lambda ctx: [
            f'{get_own_window_size_px().x:.0f}',
            f'{get_own_window_size_px().y:.0f}',
        ])
    ]
)

# INFO WINDOW
info_window = WindowDef(
    p1=P(0.0, 0.6), p2=P((1040-70)/1920, 1.0), px1=P(0, 0), px2=P(0, 0),
    hidden_event=_make_hidden_event('info'),
    export_p1=get_event('info_window_p1'),
    export_p2=get_event('info_window_p2'),
    export_px1=get_event('info_window_px1'),
    export_px2=get_event('info_window_px2'),
    draggable=True, scalable=True, grid_snap_pixel=True, force_boundary=True, sticky_boundary=True, grid_snap_x=10, grid_snap_y=10, drag_boundary_px1=P(70, 0), drag_boundary_px2=P(-70, 0),
    ignore_mouse_event=lambda: not get_event('layout_mode').value,
    polygon_defs=[
        RectDef(p1=P(0, 0), p2=P(1, 0), px2=P(0, 10), gradient=get_gradient('layout_black_fill')),
        RectDef(p1=P(0, 1), p2=P(1, 1), px1=P(0, -10), gradient=get_gradient('layout_black_fill')),
        RectDef(p1=P(0, 0), p2=P(1, 1), fill_color=QColor(255, 0, 0, 0), gradient=get_gradient('layout_black_outline'), outline_width=4),
        RectDef(p1=P(0, 0), p2=P(1, 0), px2=P(0, 40), fill_color=QColor(255, 0, 0, 0), gradient=get_gradient('layout_black_outline'), outline_width=2),
        _make_highlight_outline('info')
    ],
    text_defs=[
        TextDef(p=P(0, 0), px=P(2, 38), text='3.', bold=True, h_align=0, v_align=1, font_size=16, gradient=get_gradient('layout_black_fill')),
        TextDef(p=P(0, 0), px=P(2, 42), text='INFO DISPLAY', bold=True, h_align=0, v_align=0, font_size=70, gradient=get_gradient('layout_black_fill')),
        TextDef(p=P(0, 0), px=P(32, 38), text='<#> x <#>', h_align=0, v_align=1, font_size=16, gradient=get_gradient('layout_black_fill'), text_fn=lambda ctx: [
            f'{get_own_window_size_px().x:.0f}',
            f'{get_own_window_size_px().y:.0f}',
        ])
    ]
)
# TASK WINDOW
task_window = WindowDef(
    p1=P(1-(740-70)/1920, 0.0), p2=P(1.0, 1.0), px1=P(0, 0), px2=P(0, 0),
    hidden_event=_make_hidden_event('task'),
    export_p1=get_event('task_window_p1'),
    export_p2=get_event('task_window_p2'),
    export_px1=get_event('task_window_px1'),
    export_px2=get_event('task_window_px2'),
    draggable=True, scalable=True, grid_snap_pixel=True, force_boundary=True, sticky_boundary=True, grid_snap_x=10, grid_snap_y=10, drag_boundary_px1=P(70, 0), drag_boundary_px2=P(-70, 0),
    ignore_mouse_event=lambda: not get_event('layout_mode').value,
    polygon_defs=[
        RectDef(p1=P(0, 0), p2=P(1, 0), px2=P(0, 10), gradient=get_gradient('layout_black_fill')),
        RectDef(p1=P(0, 1), p2=P(1, 1), px1=P(0, -10), gradient=get_gradient('layout_black_fill')),
        RectDef(p1=P(0, 0), p2=P(1, 1), fill_color=QColor(255, 0, 0, 0), gradient=get_gradient('layout_black_outline'), outline_width=4),
        RectDef(p1=P(0, 0), p2=P(1, 0), px2=P(0, 40), fill_color=QColor(255, 0, 0, 0), gradient=get_gradient('layout_black_outline'), outline_width=2),
        _make_highlight_outline('task')
    ],
    text_defs=[
        TextDef(p=P(0, 0), px=P(2, 38), text='4.', bold=True, h_align=0, v_align=1, font_size=16, gradient=get_gradient('layout_black_fill')),
        TextDef(p=P(0, 0), px=P(2, 42), text='TASKS', bold=True, h_align=0, v_align=0, font_size=70, gradient=get_gradient('layout_black_fill')),
        TextDef(p=P(0, 0), px=P(32, 38), text='<#> x <#>', h_align=0, v_align=1, font_size=16, gradient=get_gradient('layout_black_fill'), text_fn=lambda ctx: [
            f'{get_own_window_size_px().x:.0f}',
            f'{get_own_window_size_px().y:.0f}',
        ])
    ],
)

WINDOW_DEF_REFS = {'map': map_window, 'logger': logger_window, 'info': info_window, 'task': task_window}
_content_phase_listeners = [
    EventListener(
        value_fn=lambda ctx: (get_event('main_page').value, get_event('fullscreen_selection').value),
        targets=[get_event(f'content_phase_{name}')],
        conditions=[lambda v: v[0] == 'close', _content_phase_excluded(name)],
        values=['close', 'close', 'open'],
    )
    for name in WINDOW_NAMES
]

layout_window = WindowDef(
    p1=P(0.0, 0.0), p2=P(1, 1),
    listener_defs=[
        EventListener(value_fn=lambda ctx: get_event('layout_mode').value, targets=[get_event('layout_page')], conditions=[lambda v: v], values=['open', 'close']),
        EventListener(value_fn=lambda ctx: True, targets=[], passthrough=True, transform=_check_overlap),
        EventListener(value_fn=lambda ctx: (get_event('layout_mode').value, get_event('layout_overlap_detected').value), targets=[get_event('layout_overlap_phase')], conditions=[lambda v: v[0] and v[1]], values=['open', 'close']),
        EventListener(value_fn=lambda ctx: get_event('layout_mode').value, targets=[], passthrough=True, transform=_clear_fullscreen_on_layout_mode),
    ] + _content_phase_listeners,
    polygon_defs=background_polygons + [
        PolygonDef(p=[P(0.5, 0.7)]*4, px=[P(-130 - 2, -50), P(-120 + 2, -50), P(-120, 25), P(-130, 25)], gradient=get_gradient('layout_overlap_detected'), 
        phase_override=get_event('layout_overlap_phase'), phases={
            'open': Phase([Reset(), PolygonTween(p=[P(0.5, 0.6)]*4, start=0, dur=0.85, ease=QEasingCurve.OutQuint)]),
            'close': Phase([PolygonTween(p=[P(0.5, 0.7)]*4, start=0, dur=0.85, ease=QEasingCurve.OutQuint)]),
        }),
        RectDef(p1=P(0.5, 0.7), p2=P(0.5, 0.7), px1=P(-130, 40), px2=P(-120, 50), gradient=get_gradient('layout_overlap_detected'), 
        phase_override=get_event('layout_overlap_phase'), phases={
            'open': Phase([Reset(), RectTween(p1=P(0.5, 0.6), p2=P(0.5, 0.6), start=0, dur=0.85, ease=QEasingCurve.OutQuint)]),
            'close': Phase([RectTween(p1=P(0.5, 0.7), p2=P(0.5, 0.7), start=0, dur=0.85, ease=QEasingCurve.OutQuint)]),
        }),
        PolygonDef(p=[P(0.5, 0.7)]*4, px=[P(120 - 2, -50), P(130 + 2, -50), P(130, 25), P(120, 25)], gradient=get_gradient('layout_overlap_detected'), 
        phase_override=get_event('layout_overlap_phase'), phases={
            'open': Phase([Reset(), PolygonTween(p=[P(0.5, 0.6)]*4, start=0, dur=0.85, ease=QEasingCurve.OutQuint)]),
            'close': Phase([PolygonTween(p=[P(0.5, 0.7)]*4, start=0, dur=0.85, ease=QEasingCurve.OutQuint)]),
        }),
        RectDef(p1=P(0.5, 0.7), p2=P(0.5, 0.7), px1=P(120, 40), px2=P(130, 50), gradient=get_gradient('layout_overlap_detected'), 
        phase_override=get_event('layout_overlap_phase'), phases={
            'open': Phase([Reset(), RectTween(p1=P(0.5, 0.6), p2=P(0.5, 0.6), start=0, dur=0.85, ease=QEasingCurve.OutQuint)]),
            'close': Phase([RectTween(p1=P(0.5, 0.7), p2=P(0.5, 0.7), start=0, dur=0.85, ease=QEasingCurve.OutQuint)]),
        }),
    ],
    text_defs=[
        TextDef(p=P(0.4, 0.5), px=P(0, -2), text='EDITING LAYOUT', bold=True, h_align=0.5, v_align=1, font_size=100, gradient=get_gradient('layout_black_translucent_fill'), phase_override=get_event('layout_page'), phases={
            'open': Phase([Reset(), TextTween(p=P(0.5, 0.5), start=0, dur=0.85, ease=QEasingCurve.OutQuint)]),
            'close': Phase([TextTween(p=P(0.6, 0.5), start=0, dur=0.85, ease=QEasingCurve.OutQuint)]),
        }),
        TextDef(p=P(0.6, 0.5), px=P(0, 2), text='PRESS [L] TO CONFIRM EDITS', bold=True, h_align=0.5, v_align=0.5, font_size=30, gradient=get_gradient('layout_black_translucent_fill'), phase_override=get_event('layout_page'), phases={
            'open': Phase([Reset(), TextTween(p=P(0.5, 0.5), start=0, dur=0.85, ease=QEasingCurve.OutQuint)]),
            'close': Phase([TextTween(p=P(0.4, 0.5), start=0, dur=0.85, ease=QEasingCurve.OutQuint)]),
        }),
        TextDef(p=P(0.5, 0.7), px=P(0, -2), text='OVERLAP', bold=True, h_align=0.5, v_align=1.0, font_size=30, gradient=get_gradient('layout_overlap_detected'), 
        phase_override=get_event('layout_overlap_phase'), phases={
            'open': Phase([Reset(), TextTween(p=P(0.5, 0.6), start=0, dur=0.85, ease=QEasingCurve.OutQuint)]),
            'close': Phase([TextTween(p=P(0.5, 0.7), start=0, dur=0.85, ease=QEasingCurve.OutQuint)]),
        }),
        TextDef(p=P(0.5, 0.7), px=P(0, 2), text='DETECTED', bold=True, h_align=0.5, v_align=0.0, font_size=30, gradient=get_gradient('layout_overlap_detected'), 
        phase_override=get_event('layout_overlap_phase'), phases={
            'open': Phase([Reset(), TextTween(p=P(0.5, 0.6), start=0, dur=0.85, ease=QEasingCurve.OutQuint)]),
            'close': Phase([TextTween(p=P(0.5, 0.7), start=0, dur=0.85, ease=QEasingCurve.OutQuint)]),
        }),
    ],
    button_defs=[
        ButtonDef(key=Qt.Key_L, event_out=get_event('layout_mode'), action='cycle', event_delta=[True, False], on_fire=_reset_layout_selection),
        ButtonDef(key=Qt.Key_1, action='set', event_out=get_event('layout_selected_window'), event_delta=None, on_fire=_key_1_4_action('map')),
        ButtonDef(key=Qt.Key_2, action='set', event_out=get_event('layout_selected_window'), event_delta=None, on_fire=_key_1_4_action('logger')),
        ButtonDef(key=Qt.Key_3, action='set', event_out=get_event('layout_selected_window'), event_delta=None, on_fire=_key_1_4_action('info')),
        ButtonDef(key=Qt.Key_4, action='set', event_out=get_event('layout_selected_window'), event_delta=None, on_fire=_key_1_4_action('task')),
        ButtonDef(key=Qt.Key_D, action='set', event_out=get_event('layout_selected_window'), event_delta=None, on_fire=_toggle_disable_selected),
    ],
    sub_windows=[map_window, logger_window, info_window, task_window]
)

overlay_window = WindowDef(
    p1=P(0.0, 0.0), p2=P(1, 1),
    polygon_defs=[
        # RED BORDER LIMITS
        RectDef(p1=P(0, 0), p2=P(0, 1), px1=P(0, 0), px2=P(70, 0), gradient=get_gradient('layout_red_fill'), phase_override=get_event('layout_page')),
        RectDef(p1=P(1, 0), p2=P(1, 1), px1=P(-70, 0), px2=P(0, 0), gradient=get_gradient('layout_red_fill'), phase_override=get_event('layout_page')),

        # BLACK OUTLINE DETAIL
        RectDef(p1=P(0, 0), p2=P(1, 0), px2=P(0, 10), gradient=get_gradient('layout_black_fill'), phase_override=get_event('layout_page')),
        RectDef(p1=P(0, 1), p2=P(1, 1), px1=P(0, -10), gradient=get_gradient('layout_black_fill'), phase_override=get_event('layout_page')),
        PolygonDef(p=[P(0.5, 0)]*4, px=[P(-165, 0), P(165, 0), P(145, 20), P(-145, 20)], gradient=get_gradient('layout_black_fill'), phase_override=get_event('layout_page')),
        PolygonDef(p=[P(0.5, 1)]*4, px=[P(-165, 0), P(165, 0), P(145, -20), P(-145, -20)], gradient=get_gradient('layout_black_fill'), phase_override=get_event('layout_page')),
        PolygonDef(p=[P(0, 0)]*4, px=[P(0, 0), P(10, 0), P(10, 50), P(0, 60)], gradient=get_gradient('layout_black_fill'), phase_override=get_event('layout_page')),
        PolygonDef(p=[P(1, 0)]*4, px=[P(0, 0), P(-10, 0), P(-10, 50), P(0, 60)], gradient=get_gradient('layout_black_fill'), phase_override=get_event('layout_page')),
        PolygonDef(p=[P(0, 1)]*4, px=[P(0, 0), P(10, 0), P(10, -50), P(0, -60)], gradient=get_gradient('layout_black_fill'), phase_override=get_event('layout_page')),
        PolygonDef(p=[P(1, 1)]*4, px=[P(0, 0), P(-10, 0), P(-10, -50), P(0, -60)], gradient=get_gradient('layout_black_fill'), phase_override=get_event('layout_page')),
    ],
    text_defs=[
        TextDef(p=P(0.5, 0), px=P(0, 1), text='- <#> -', font_size=15, h_align=0.5, v_align=0.0, gradient=get_gradient('layout_white_fill'), text_fn=lambda ctx: datetime.now(ZoneInfo('America/Edmonton')).time().replace(microsecond=0)),
        TextDef(p=P(0.5, 1), px=P(0, 0), text='SPEAR', font_size=15, h_align=0.5, v_align=1.0, gradient=get_gradient('layout_white_fill')),
    ],
)

WINDOW_DEFS = []
WINDOW_DEFS.append(task_window)
WINDOW_DEFS.append(layout_window)
WINDOW_DEFS.append(overlay_window)

register_windows(WINDOW_LAYER, WINDOW_DEFS)


# task_window = WindowDef(
#     p1=P(0.0, 0.0), p2=P(0.5, 0.5),
#     phase_event=get_event('task_window_p1'),   # any live event just to keep polling active
#     phase_fn=lambda v: 'sync',
#     phases={
#         'sync': Phase([WindowTween(p1=get_event('task_window_p1'), p2=get_event('task_window_p2'), start=0, dur=0, ease=QEasingCurve.OutQuint)], update_retrigger=True)
#     },
#     polygon_defs=[
#         RectDef(p1=P(0, 0), p2=P(1, 1), fill_color=QColor(0, 255, 0, 50))
#     ],
# )


# register_event(EventDef(name='cam_loading_phase', value='create'))

# WINDOW_DEFS = [
#     WindowDef(
#         p1=P(0, 0), p2=P(1, 1),
#         button_defs=[
#             ButtonDef(key=Qt.Key_L, event_out=get_event('cam_loading_phase'), action='cycle', event_delta=['create', 'loaded']),
#         ],
#         phase_event=get_event('cam_loading_phase'),
#         polygon_defs=[
#             # Background T/B/L/R
#             RectDef(p1=P(0.00,0.00), p2=P(1.00,0.50), fill_color=QColor(10,10,14), phases={
#                 'loaded': Phase([RectTween(p1=P(0.00,0.00), p2=P(1.00,0.00), start=0.30, dur=1.00, ease=QEasingCurve.OutQuint)])}),
#             RectDef(p1=P(0.00,0.50), p2=P(1.00,1.00), fill_color=QColor(10,10,14), phases={
#                 'loaded': Phase([RectTween(p1=P(0.00,1.00), p2=P(1.00,1.00), start=0.30, dur=1.00, ease=QEasingCurve.OutQuint)])}),
#             RectDef(p1=P(0.00,0.00), p2=P(0.50,1.00), fill_color=QColor(10,10,14), phases={
#                 'loaded': Phase([RectTween(p1=P(0.00,0.00), p2=P(0.00,1.00), start=0.30, dur=1.00, ease=QEasingCurve.OutQuint)])}),
#             RectDef(p1=P(0.50,0.00), p2=P(1.00,1.00), fill_color=QColor(10,10,14), phases={
#                 'loaded': Phase([RectTween(p1=P(1.00,0.00), p2=P(1.00,1.00), start=0.30, dur=1.00, ease=QEasingCurve.OutQuint)])}),

#             # Background Border T/B/L/R
#             RectDef(p1=P(0.50,0.50), p2=P(0.50,0.50), px1=P(0,-1), px2=P(0,0), fill_color=QColor(255,255,255), phases={
#                 'loaded': Phase([
#                     RectTween(p1=P(0.00,0.00), p2=P(1.00,0.00), px1=P(0,-1), px2=P(0,0),  fill_color=QColor(255,255,255),              start=0.30, dur=1.00, ease=QEasingCurve.OutQuint),
#                     RectTween(p1=P(0.00,0.00), p2=P(1.00,0.00), px1=P(0,-1), px2=P(0,0),  fill_color=QColor(255,255,255,0),             start=2.50, dur=1.00, ease=QEasingCurve.InQuint)])}),
#             RectDef(p1=P(0.50,0.50), p2=P(0.50,0.50), px1=P(0,0),  px2=P(0,1), fill_color=QColor(255,255,255), phases={
#                 'loaded': Phase([
#                     RectTween(p1=P(0.00,1.00), p2=P(1.00,1.00), px1=P(0,0),  px2=P(0,1),  fill_color=QColor(255,255,255),              start=0.30, dur=1.00, ease=QEasingCurve.OutQuint),
#                     RectTween(p1=P(0.00,1.00), p2=P(1.00,1.00), px1=P(0,0),  px2=P(0,1),  fill_color=QColor(255,255,255,0),             start=2.50, dur=1.00, ease=QEasingCurve.InQuint)])}),
#             RectDef(p1=P(0.50,0.50), p2=P(0.50,0.50), px1=P(-1,0), px2=P(0,0), fill_color=QColor(255,255,255), phases={
#                 'loaded': Phase([
#                     RectTween(p1=P(0.00,0.00), p2=P(0.00,1.00), px1=P(-1,0), px2=P(0,0),  fill_color=QColor(255,255,255),              start=0.30, dur=1.00, ease=QEasingCurve.OutQuint),
#                     RectTween(p1=P(0.00,0.00), p2=P(0.00,1.00), px1=P(-1,0), px2=P(0,0),  fill_color=QColor(255,255,255,0),             start=2.50, dur=1.00, ease=QEasingCurve.InQuint)])}),
#             RectDef(p1=P(0.50,0.50), p2=P(0.50,0.50), px1=P(0,0),  px2=P(1,0), fill_color=QColor(255,255,255), phases={
#                 'loaded': Phase([
#                     RectTween(p1=P(1.00,0.00), p2=P(1.00,1.00), px1=P(0,0),  px2=P(1,0),  fill_color=QColor(255,255,255),              start=0.30, dur=1.00, ease=QEasingCurve.OutQuint),
#                     RectTween(p1=P(1.00,0.00), p2=P(1.00,1.00), px1=P(0,0),  px2=P(1,0),  fill_color=QColor(255,255,255,0),             start=2.50, dur=1.00, ease=QEasingCurve.InQuint)])}),

#             # Horizontal Corner TL/TR/BL/BR
#             RectDef(p1=P(0.00,-0.01), p2=P(0.50,-0.01), fill_color=QColor(255,255,255), uniform_scale=True, phases={
#                 'create': Phase([
#                     RectTween(p1=P(0.30,0.47), p2=P(0.50,0.48),                                                                         start=0.30, dur=0.25, ease=QEasingCurve.OutCirc),
#                     RectTween(p1=P(0.25,0.45), p2=P(0.35,0.46), tr=(P(0,0), P(0,0)),                                                    start=0.55, dur=0.50, ease=QEasingCurve.InOutCirc)]),
#                 'loaded': Phase([
#                     RectTween(p1=P(0.25,0.45), p2=P(0.25,0.46),                                                                         start=0.30, dur=0.30, ease=QEasingCurve.OutCirc)])}),
#             RectDef(p1=P(0.50,-0.01), p2=P(1.00,-0.01), fill_color=QColor(255,255,255), uniform_scale=True, phases={
#                 'create': Phase([
#                     RectTween(p1=P(0.50,0.47), p2=P(0.70,0.48),                                                                         start=0.30, dur=0.25, ease=QEasingCurve.OutCirc),
#                     RectTween(p1=P(0.65,0.45), p2=P(0.75,0.46), tl=(P(0,0), P(0,0)),                                                    start=0.55, dur=0.50, ease=QEasingCurve.InOutCirc)]),
#                 'loaded': Phase([
#                     RectTween(p1=P(0.75,0.45), p2=P(0.75,0.46),                                                                         start=0.30, dur=0.30, ease=QEasingCurve.OutCirc)])}),
#             RectDef(p1=P(0.00,1.00), p2=P(0.50,1.00), fill_color=QColor(255,255,255), uniform_scale=True, phases={
#                 'create': Phase([
#                     RectTween(p1=P(0.30,0.52), p2=P(0.50,0.53),                                                                         start=0.30, dur=0.25, ease=QEasingCurve.OutCirc),
#                     RectTween(p1=P(0.25,0.54), p2=P(0.35,0.55), br=(P(0,0), P(0,0)),                                                    start=0.55, dur=0.50, ease=QEasingCurve.InOutCirc)]),
#                 'loaded': Phase([
#                     RectTween(p1=P(0.25,0.54), p2=P(0.25,0.55),                                                                         start=0.30, dur=0.30, ease=QEasingCurve.OutCirc)])}),
#             RectDef(p1=P(0.50,1.00), p2=P(1.00,1.00), fill_color=QColor(255,255,255), uniform_scale=True, phases={
#                 'create': Phase([
#                     RectTween(p1=P(0.50,0.52), p2=P(0.70,0.53),                                                                         start=0.30, dur=0.25, ease=QEasingCurve.OutCirc),
#                     RectTween(p1=P(0.65,0.54), p2=P(0.75,0.55), bl=(P(0,0), P(0,0)),                                                    start=0.55, dur=0.50, ease=QEasingCurve.InOutCirc)]),
#                 'loaded': Phase([
#                     RectTween(p1=P(0.75,0.54), p2=P(0.75,0.55),                                                                         start=0.30, dur=0.30, ease=QEasingCurve.OutCirc)])}),

#             # Horizontal Thin Corner TL/TR/BL/BR
#             RectDef(p1=P(0.30,0.475), p2=P(0.50,0.480), fill_color=QColor(255,255,255), uniform_scale=True, phases={
#                 'create': Phase([
#                     RectTween(p1=P(0.30,0.475),  p2=P(0.50,0.480),                                                                      start=0.55, dur=0.00, ease=QEasingCurve.InOutCirc),
#                     RectTween(p1=P(0.345,0.455), p2=P(0.445,0.460), tr=(P(0,0), P(0,0)),                                                start=0.55, dur=0.50, ease=QEasingCurve.InOutCirc),
#                     RectTween(p1=P(0.345,0.455), p2=P(0.395,0.460), tr=(P(0,0), P(0,0)),                                                start=1.05, dur=1.75, ease=QEasingCurve.InCirc)]),
#                 'loaded': Phase([
#                     RectTween(p1=P(0.345,0.455), p2=P(0.345,0.460),                                                                     start=0.00, dur=0.30, ease=QEasingCurve.OutCirc)])}),
#             RectDef(p1=P(0.50,0.475), p2=P(0.70,0.480), fill_color=QColor(255,255,255), uniform_scale=True, phases={
#                 'create': Phase([
#                     RectTween(p1=P(0.50,0.475),  p2=P(0.70,0.480),                                                                      start=0.55, dur=0.00, ease=QEasingCurve.InOutCirc),
#                     RectTween(p1=P(0.555,0.455), p2=P(0.655,0.460), tl=(P(0,0), P(0,0)),                                                start=0.55, dur=0.50, ease=QEasingCurve.InOutCirc),
#                     RectTween(p1=P(0.605,0.455), p2=P(0.655,0.460), tl=(P(0,0), P(0,0)),                                                start=1.05, dur=1.75, ease=QEasingCurve.InCirc)]),
#                 'loaded': Phase([
#                     RectTween(p1=P(0.655,0.455), p2=P(0.655,0.460),                                                                     start=0.00, dur=0.30, ease=QEasingCurve.OutCirc)])}),
#             RectDef(p1=P(0.30,0.52), p2=P(0.50,0.525), fill_color=QColor(255,255,255), uniform_scale=True, phases={
#                 'create': Phase([
#                     RectTween(p1=P(0.30,0.52),   p2=P(0.50,0.525),                                                                      start=0.55, dur=0.00, ease=QEasingCurve.InOutCirc),
#                     RectTween(p1=P(0.345,0.54),  p2=P(0.445,0.545), br=(P(0,0), P(0,0)),                                                start=0.55, dur=0.50, ease=QEasingCurve.InOutCirc),
#                     RectTween(p1=P(0.345,0.54),  p2=P(0.395,0.545), br=(P(0,0), P(0,0)),                                                start=1.05, dur=1.75, ease=QEasingCurve.InCirc)]),
#                 'loaded': Phase([
#                     RectTween(p1=P(0.345,0.54),  p2=P(0.345,0.545),                                                                     start=0.00, dur=0.30, ease=QEasingCurve.OutCirc)])}),
#             RectDef(p1=P(0.50,0.52), p2=P(0.70,0.525), fill_color=QColor(255,255,255), uniform_scale=True, phases={
#                 'create': Phase([
#                     RectTween(p1=P(0.50,0.52),   p2=P(0.70,0.525),                                                                      start=0.55, dur=0.00, ease=QEasingCurve.InOutCirc),
#                     RectTween(p1=P(0.555,0.54),  p2=P(0.655,0.545), bl=(P(0,0), P(0,0)),                                                start=0.55, dur=0.50, ease=QEasingCurve.InOutCirc),
#                     RectTween(p1=P(0.605,0.54),  p2=P(0.655,0.545), bl=(P(0,0), P(0,0)),                                                start=1.05, dur=1.75, ease=QEasingCurve.InCirc)]),
#                 'loaded': Phase([
#                     RectTween(p1=P(0.655,0.54),  p2=P(0.655,0.545),                                                                     start=0.00, dur=0.30, ease=QEasingCurve.OutCirc)])}),

#             # Vertical Corner TL/BL/TR/BR
#             RectDef(p1=P(0.00,0.00), p2=P(0.005625,0.50), fill_color=QColor(255,255,255), uniform_scale=True, phases={
#                 'create': Phase([
#                     RectTween(p1=P(0.30,0.47),  p2=P(0.305625,0.50),                                                                    start=0.30, dur=0.25, ease=QEasingCurve.OutCirc),
#                     RectTween(p1=P(0.25,0.45),  p2=P(0.255625,0.47),                                                                    start=0.55, dur=0.50, ease=QEasingCurve.InOutCirc)]),
#                 'loaded': Phase([
#                     RectTween(p1=P(0.25,0.47),  p2=P(0.255625,0.47),                                                                    start=0.60, dur=0.30, ease=QEasingCurve.OutCirc)])}),
#             RectDef(p1=P(0.00,0.50), p2=P(0.005625,1.00), fill_color=QColor(255,255,255), uniform_scale=True, phases={
#                 'create': Phase([
#                     RectTween(p1=P(0.30,0.50),  p2=P(0.305625,0.53),                                                                    start=0.30, dur=0.25, ease=QEasingCurve.OutCirc),
#                     RectTween(p1=P(0.25,0.53),  p2=P(0.255625,0.55),                                                                    start=0.55, dur=0.50, ease=QEasingCurve.InOutCirc)]),
#                 'loaded': Phase([
#                     RectTween(p1=P(0.25,0.53),  p2=P(0.255625,0.53),                                                                    start=0.60, dur=0.30, ease=QEasingCurve.OutCirc)])}),
#             RectDef(p1=P(1.00,0.00), p2=P(1.005625,0.50), fill_color=QColor(255,255,255), uniform_scale=True, phases={
#                 'create': Phase([
#                     RectTween(p1=P(0.694375,0.47), p2=P(0.70,0.50),                                                                     start=0.30, dur=0.25, ease=QEasingCurve.OutCirc),
#                     RectTween(p1=P(0.744375,0.45), p2=P(0.75,0.47),                                                                     start=0.55, dur=0.50, ease=QEasingCurve.InOutCirc)]),
#                 'loaded': Phase([
#                     RectTween(p1=P(0.744375,0.47), p2=P(0.75,0.47),                                                                     start=0.60, dur=0.30, ease=QEasingCurve.OutCirc)])}),
#             RectDef(p1=P(1.00,0.00), p2=P(1.005625,0.50), fill_color=QColor(255,255,255), uniform_scale=True, phases={
#                 'create': Phase([
#                     RectTween(p1=P(0.694375,0.50), p2=P(0.70,0.53),                                                                     start=0.30, dur=0.25, ease=QEasingCurve.OutCirc),
#                     RectTween(p1=P(0.744375,0.53), p2=P(0.75,0.55),                                                                     start=0.55, dur=0.50, ease=QEasingCurve.InOutCirc)]),
#                 'loaded': Phase([
#                     RectTween(p1=P(0.744375,0.53), p2=P(0.75,0.53),                                                                     start=0.60, dur=0.30, ease=QEasingCurve.OutCirc)])}),

#             # Large Square L/R
#             RectDef(p1=P(0.50,0.50), p2=P(0.50,0.50), fill_color=QColor(180,180,180), uniform_scale=True, phases={
#                 'create': Phase([
#                     RectTween(p1=P(0.50-10/1920,0.50-10/1080), p2=P(0.50+10/1920,0.50+10/1080),                                        start=0.00, dur=0.30, ease=QEasingCurve.OutCirc),
#                     RectTween(p1=P(0.23,        0.50-10/1080), p2=P(0.23+20/1920,0.50+10/1080),                                        start=0.30, dur=1.00, ease=QEasingCurve.OutBack)]),
#                 'loaded': Phase([
#                     RectTween(p1=P(0.25,        0.50-10/1080), p2=P(0.255625,    0.50+10/1080), fill_color=QColor(255,255,255),        start=0.30, dur=0.30, ease=QEasingCurve.OutCirc),
#                     RectTween(p1=P(0.25,        0.50),          p2=P(0.255625,    0.50),                                                start=0.90, dur=0.30, ease=QEasingCurve.OutCirc)])}),
#             RectDef(p1=P(0.50,0.50), p2=P(0.50,0.50), fill_color=QColor(180,180,180), uniform_scale=True, phases={
#                 'create': Phase([
#                     RectTween(p1=P(0.50-10/1920,0.50-10/1080), p2=P(0.50+10/1920,0.50+10/1080),                                        start=0.00, dur=0.30, ease=QEasingCurve.OutCirc),
#                     RectTween(p1=P(0.77-20/1920,0.50-10/1080), p2=P(0.77,        0.50+10/1080),                                        start=0.30, dur=1.00, ease=QEasingCurve.OutBack)]),
#                 'loaded': Phase([
#                     RectTween(p1=P(0.75-0.005625,0.50-10/1080), p2=P(0.75,       0.50+10/1080), fill_color=QColor(255,255,255),        start=0.30, dur=0.30, ease=QEasingCurve.OutCirc),
#                     RectTween(p1=P(0.75-0.005625,0.50),          p2=P(0.75,       0.50),                                                start=0.90, dur=0.30, ease=QEasingCurve.OutCirc)])}),

#             # Small Square TL/TR/BL/BR
#             RectDef(p1=P(0.50,0.50), p2=P(0.50,0.50), fill_color=QColor(180,180,180), uniform_scale=True, phases={
#                 'create': Phase([
#                     RectTween(p1=P(0.50-5/1920, 0.50-5/1080),  p2=P(0.50+5/1920, 0.50+5/1080),                                        start=0.00, dur=0.30, ease=QEasingCurve.OutCirc),
#                     RectTween(p1=P(0.50-70/1920,0.50-70/1080), p2=P(0.50-60/1920,0.50-60/1080),                                        start=0.30, dur=1.00, ease=QEasingCurve.OutBack)]),
#                 'loaded': Phase([
#                     RectTween(p1=P(0.50-5/1920, 0.50-70/1080), p2=P(0.50+5/1920, 0.50-60/1080), fill_color=QColor(255,255,255),       start=0.30, dur=0.30, ease=QEasingCurve.OutCirc),
#                     RectTween(p1=P(0.50,        0.50),           p2=P(0.50,        0.50),                                               start=0.60, dur=0.30, ease=QEasingCurve.OutCirc)])}),
#             RectDef(p1=P(0.50,0.50), p2=P(0.50,0.50), fill_color=QColor(180,180,180), uniform_scale=True, phases={
#                 'create': Phase([
#                     RectTween(p1=P(0.50-5/1920, 0.50-5/1080),  p2=P(0.50+5/1920, 0.50+5/1080),                                        start=0.00, dur=0.30, ease=QEasingCurve.OutCirc),
#                     RectTween(p1=P(0.50+70/1920,0.50-70/1080), p2=P(0.50+80/1920,0.50-60/1080),                                        start=0.30, dur=1.00, ease=QEasingCurve.OutBack)]),
#                 'loaded': Phase([
#                     RectTween(p1=P(0.50-5/1920, 0.50-70/1080), p2=P(0.50+5/1920, 0.50-60/1080), fill_color=QColor(255,255,255),       start=0.30, dur=0.30, ease=QEasingCurve.OutCirc),
#                     RectTween(p1=P(0.50,        0.50),           p2=P(0.50,        0.50),                                               start=0.60, dur=0.30, ease=QEasingCurve.OutCirc)])}),
#             RectDef(p1=P(0.50,0.50), p2=P(0.50,0.50), fill_color=QColor(180,180,180), uniform_scale=True, phases={
#                 'create': Phase([
#                     RectTween(p1=P(0.50-5/1920, 0.50-5/1080),  p2=P(0.50+5/1920, 0.50+5/1080),                                        start=0.00, dur=0.30, ease=QEasingCurve.OutCirc),
#                     RectTween(p1=P(0.50-70/1920,0.50+70/1080), p2=P(0.50-60/1920,0.50+80/1080),                                        start=0.30, dur=1.00, ease=QEasingCurve.OutBack)]),
#                 'loaded': Phase([
#                     RectTween(p1=P(0.50-5/1920, 0.50+70/1080), p2=P(0.50+5/1920, 0.50+80/1080), fill_color=QColor(255,255,255),       start=0.30, dur=0.30, ease=QEasingCurve.OutCirc),
#                     RectTween(p1=P(0.50,        0.50),           p2=P(0.50,        0.50),                                               start=0.60, dur=0.30, ease=QEasingCurve.OutCirc)])}),
#             RectDef(p1=P(0.50,0.50), p2=P(0.50,0.50), fill_color=QColor(180,180,180), uniform_scale=True, phases={
#                 'create': Phase([
#                     RectTween(p1=P(0.50-5/1920, 0.50-5/1080),  p2=P(0.50+5/1920, 0.50+5/1080),                                        start=0.00, dur=0.30, ease=QEasingCurve.OutCirc),
#                     RectTween(p1=P(0.50+70/1920,0.50+70/1080), p2=P(0.50+80/1920,0.50+80/1080),                                        start=0.30, dur=1.00, ease=QEasingCurve.OutBack)]),
#                 'loaded': Phase([
#                     RectTween(p1=P(0.50-5/1920, 0.50+70/1080), p2=P(0.50+5/1920, 0.50+80/1080), fill_color=QColor(255,255,255),       start=0.30, dur=0.30, ease=QEasingCurve.OutCirc),
#                     RectTween(p1=P(0.50,        0.50),           p2=P(0.50,        0.50),                                               start=0.60, dur=0.30, ease=QEasingCurve.OutCirc)])}),

#             # Progress Bar Outline T/B/L/R
#             RectDef(p1=P(0.50,0.50), p2=P(0.50,0.50), fill_color=QColor(120,120,120), uniform_scale=True, phases={
#                 'create': Phase([
#                     RectTween(p1=P(0.25+0.005625*2,0.45+0.01*2), p2=P(0.25+0.005625*2+0.05625-0.005625*2*2, 0.45+0.01*2+0.0025),      start=0.30, dur=0.70, ease=QEasingCurve.InOutQuad),
#                     RectTween(p1=P(0.25+0.005625*2,0.45+0.01*2), p2=P(0.75-0.005625*2,                       0.45+0.01*2+0.0025),      start=1.00, dur=1.00, ease=QEasingCurve.InOutQuad)]),
#                 'loaded': Phase([
#                     RectTween(p1=P(0.25+0.005625*2,0.45+0.01*2), p2=P(0.75-0.005625*2,                       0.45+0.01*2+0.0025), fill_color=QColor(255,255,255), start=0.30, dur=0.30, ease=QEasingCurve.InOutQuad),
#                     RectTween(p1=P(0.05+0.005625*2,0.45+0.01*2), p2=P(0.05+0.005625*2,                       0.45+0.01*2+0.0025),                                 start=0.60, dur=1.20, ease=QEasingCurve.OutQuint)])}),
#             RectDef(p1=P(0.50,0.50), p2=P(0.50,0.50), fill_color=QColor(120,120,120), uniform_scale=True, phases={
#                 'create': Phase([
#                     RectTween(p1=P(0.25+0.005625*2,0.55-0.01*2-0.0025), p2=P(0.25+0.005625*2+0.05625-0.005625*2*2, 0.55-0.01*2),      start=0.30, dur=0.70, ease=QEasingCurve.InOutQuad),
#                     RectTween(p1=P(0.25+0.005625*2,0.55-0.01*2-0.0025), p2=P(0.75-0.005625*2,                       0.55-0.01*2),      start=1.00, dur=1.00, ease=QEasingCurve.InOutQuad)]),
#                 'loaded': Phase([
#                     RectTween(p1=P(0.25+0.005625*2,0.55-0.01*2-0.0025), p2=P(0.75-0.005625*2,                       0.55-0.01*2), fill_color=QColor(255,255,255), start=0.30, dur=0.30, ease=QEasingCurve.InOutQuad),
#                     RectTween(p1=P(0.95+0.005625*2,0.55-0.01*2-0.0025), p2=P(0.95+0.005625*2,                       0.55-0.01*2),                                 start=0.60, dur=1.20, ease=QEasingCurve.OutQuint)])}),
#             RectDef(p1=P(0.50,0.50), p2=P(0.50,0.50), fill_color=QColor(120,120,120), uniform_scale=True, phases={
#                 'create': Phase([
#                     RectTween(p1=P(0.25+0.005625*2,0.45+0.01*2), p2=P(0.25+0.005625*2+0.00140625, 0.55-0.01*2),                        start=0.30, dur=0.70, ease=QEasingCurve.InOutQuad)]),
#                 'loaded': Phase([
#                     RectTween(p1=P(0.25+0.005625*2,0.55-0.01*2), p2=P(0.25+0.005625*2+0.00140625, 0.55-0.01*2), fill_color=QColor(255,255,255), start=0.30, dur=0.30, ease=QEasingCurve.OutCirc)])}),
#             RectDef(p1=P(0.50,0.50), p2=P(0.50,0.50), fill_color=QColor(120,120,120), uniform_scale=True, phases={
#                 'create': Phase([
#                     RectTween(p1=P(0.25+0.005625*2+0.05625-0.005625*2*2,0.45+0.01*2), p2=P(0.25+0.005625*2+0.05625-0.005625*2*2+0.00140625, 0.55-0.01*2), start=0.30, dur=0.70, ease=QEasingCurve.InOutQuad),
#                     RectTween(p1=P(0.75-0.005625*2-0.00140625,           0.45+0.01*2), p2=P(0.75-0.005625*2,                               0.55-0.01*2), start=1.00, dur=1.00, ease=QEasingCurve.InOutQuad)]),
#                 'loaded': Phase([
#                     RectTween(p1=P(0.75-0.005625*2-0.00140625,0.45+0.01*2), p2=P(0.75-0.005625*2, 0.45+0.01*2), fill_color=QColor(255,255,255), start=0.30, dur=0.30, ease=QEasingCurve.OutCirc)])}),

#             # Progress Bar
#             RectDef(p1=P(0.50,0.45+0.01*3), p2=P(0.50,0.55-0.01*3), fill_color=QColor(255,255,255), uniform_scale=True, phases={
#                 'create': Phase([
#                     RectTween(p1=P(0.25+0.005625*3,0.45+0.01*3), p2=P(0.25+0.005625*3+0.05625-0.005625*3*2, 0.55-0.01*3),              start=0.30, dur=0.70, ease=QEasingCurve.InOutQuad),
#                     RectTween(p1=P(0.25+0.005625*3,0.45+0.01*3), p2=P(0.75-0.005625*3,                       0.55-0.01*3),              start=1.00, dur=1.80, ease=QEasingCurve.InOutCirc)]),
#                 'loaded': Phase([
#                     RectTween(p1=P(0.25+0.005625*3,0.45+0.01*3), p2=P(0.75-0.005625*3, 0.55-0.01*3),                                   start=0.00, dur=0.30, ease=QEasingCurve.OutCirc),
#                     RectTween(p1=P(0.50,          0.45+0.01*3), p2=P(0.50,             0.55-0.01*3),                                    start=0.30, dur=0.25, ease=QEasingCurve.OutCirc)])}),
#         ]
#     )
# ]


# register_windows(WINDOW_LAYER, WINDOW_DEFS)
