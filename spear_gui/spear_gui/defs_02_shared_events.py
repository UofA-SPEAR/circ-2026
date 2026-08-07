from spear_gui.overlay_system import (
    P, EventDef, register_event
)

# ──────────────────────── EVENT DEFS ────────────────────────

register_event(EventDef(name='main_page', value='close'))

register_event(EventDef(name='layout_mode', value=False))
register_event(EventDef(name='layout_mode_flip', value=True))
register_event(EventDef(name='layout_page', value='close'))

register_event(EventDef(name='info_setting_phase', value='close'))

register_event(EventDef(name='force_hide_map_window',    value=False))
register_event(EventDef(name='force_hide_logger_window', value=False))
register_event(EventDef(name='force_hide_info_window',   value=False))
register_event(EventDef(name='force_hide_task_window',   value=False))

# Window Points
register_event(EventDef(name='map_window_p1',  value=P(0, 0)))
register_event(EventDef(name='map_window_p2',  value=P(0, 0))) 
register_event(EventDef(name='logger_window_p1',  value=P(0, 0))) 
register_event(EventDef(name='logger_window_p2',  value=P(0, 0)))  
register_event(EventDef(name='info_window_p1',  value=P(0, 0))) 
register_event(EventDef(name='info_window_p2',  value=P(0, 0))) 
register_event(EventDef(name='task_window_p1',  value=P(0, 0))) 
register_event(EventDef(name='task_window_p2',  value=P(0, 0)))  

register_event(EventDef(name='map_window_px1',  value=P(0, 0)))
register_event(EventDef(name='map_window_px2',  value=P(0, 0))) 
register_event(EventDef(name='logger_window_px1',  value=P(0, 0))) 
register_event(EventDef(name='logger_window_px2',  value=P(0, 0)))  
register_event(EventDef(name='info_window_px1',  value=P(0, 0))) 
register_event(EventDef(name='info_window_px2',  value=P(0, 0))) 
register_event(EventDef(name='task_window_px1',  value=P(0, 0))) 
register_event(EventDef(name='task_window_px2',  value=P(0, 0)))  

register_event(EventDef(name='base_map_window_p1',  value=P(0, 0)))
register_event(EventDef(name='base_map_window_p2',  value=P(0, 0))) 
register_event(EventDef(name='base_logger_window_p1',  value=P(0, 0))) 
register_event(EventDef(name='base_logger_window_p2',  value=P(0, 0)))  
register_event(EventDef(name='base_info_window_p1',  value=P(0, 0))) 
register_event(EventDef(name='base_info_window_p2',  value=P(0, 0))) 
register_event(EventDef(name='base_task_window_p1',  value=P(0, 0))) 
register_event(EventDef(name='base_task_window_p2',  value=P(0, 0)))  

register_event(EventDef(name='base_map_window_px1',  value=P(0, 0)))
register_event(EventDef(name='base_map_window_px2',  value=P(0, 0))) 
register_event(EventDef(name='base_logger_window_px1',  value=P(0, 0))) 
register_event(EventDef(name='base_logger_window_px2',  value=P(0, 0)))  
register_event(EventDef(name='base_info_window_px1',  value=P(0, 0))) 
register_event(EventDef(name='base_info_window_px2',  value=P(0, 0))) 
register_event(EventDef(name='base_task_window_px1',  value=P(0, 0))) 
register_event(EventDef(name='base_task_window_px2',  value=P(0, 0)))  

# Fullscreened window bools
register_event(EventDef(name='window_fullscreen_map',    value=False))
register_event(EventDef(name='window_fullscreen_logger', value=False))
register_event(EventDef(name='window_fullscreen_info',   value=False))
register_event(EventDef(name='window_fullscreen_task',  value=False))

register_event(EventDef(name='fullscreen_window_p1',  value=P(0, 0)))  
register_event(EventDef(name='fullscreen_window_p2',  value=P(1, 1)))  
register_event(EventDef(name='fullscreen_window_px1', value=P(70, 0)))  
register_event(EventDef(name='fullscreen_window_px2', value=P(-70, 0)))  

register_event(EventDef(name='content_phase_map', value='open'))
register_event(EventDef(name='content_phase_logger', value='open'))
register_event(EventDef(name='content_phase_info', value='open'))
register_event(EventDef(name='content_phase_task', value='open'))

# Layout mode
register_event(EventDef(name='layout_selected_window',  value=None))
register_event(EventDef(name='window_disabled_map',     value=False))
register_event(EventDef(name='window_disabled_logger',  value=True))
register_event(EventDef(name='window_disabled_info',    value=False))
register_event(EventDef(name='window_disabled_task',   value=False))
register_event(EventDef(name='layout_overlap_detected', value=False))
register_event(EventDef(name='layout_overlap_phase',    value='close'))



# export this to use this i just copied this from the map cause im so lazy


from typing import Any, Callable, Dict, List, Optional, Tuple
import math

from PySide6.QtCore import Qt, QEasingCurve
from PySide6.QtGui  import QColor

from spear_gui.overlay_system import (
    P, Reset, Phase, expand_defs,
    PolygonDef, PolygonTween, RectDef, RectTween,                              # PolygonDef
    ArcDef,                                                                    # ArcDef
    TextDef, TextTween, TextBlock, DataTable,                                  # TextDef
    BasicSliderDef, SliderDef, get_slider_knob_pos,                            # SliderDef
    ButtonDef, SegmentedButtons, Segment, SevenSegmentDisplay,                 # ButtonDef
    TextboxDef,                                                                # TextboxDef
    GraphDef, SeriesDef,                                                       # GraphDef
    PieDef,                                                                    # PieDef
    WindowDef, WindowTween, register_windows,                                  # WindowDef
    EventDef, EventListener, register_event, get_event,                        # EventDef
    GradientDef, GradientStop, GradientTween, register_gradient, get_gradient, # GradientDef

    P_OPEN, P_CLOSE, P_HOVER, P_UNHOVER, P_CLICK, P_RELEASE, P_SET, P_ALWAYS,
    SYS_FPS, SYS_FRAME_TIME, SYS_MOUSE, SYS_MOUSE_X, SYS_MOUSE_Y,
    get_spawn_event, GROUP_EVENT, SELECT_EVENT, SELF_ID, STATIC,
    get_spawn_mouse_norm, get_spawn_mouse_offset_px,
    get_animated_window, delete_spawned_by_id, clear_spawned_by_group
)


def make_slider(event_name = '', p1=P(0.6, 1), p2=P(1, 1), px1=P(0, 0), px2=P(0, 0), half=3.0, min_val=0, max_val=1, step=0, decimals=0):
    def _hex_track_px(px1: P, px2: P, half: float) -> List[P]:
        cy = px1.y
        return [
            P(px1.x - half, cy),          # left tip
            P(px1.x,        cy - half),   # top-left
            P(px2.x,        cy - half),   # top-right
            P(px2.x + half, cy),          # right tip
            P(px2.x,        cy + half),   # bottom-right
            P(px1.x,        cy + half),   # bottom-left
        ]

    cy = px1.y
    min_track_px = [
        P(px1.x - half, cy),
        P(px1.x,        cy - half),
        P(px1.x,        cy - half),
        P(px1.x,        cy),
        P(px1.x,        cy + half),
        P(px1.x,        cy + half),
    ]
    max_track_px = _hex_track_px(px1, px2, half)

    track_p  = [P(p1.x, p1.y), P(p1.x, p1.y), P(p2.x, p2.y), P(p2.x, p2.y), P(p2.x, p2.y), P(p1.x, p1.y)]
    min_track_p = track_p
    max_track_p = track_p
    track_px = _hex_track_px(px1, px2, half)
    collapsed_px = [P(px1.x - half, px1.y), P(px1.x, px1.y - half), P(px1.x, px1.y - half), P(px1.x + half, px1.y), P(px1.x, px1.y + half), P(px1.x, px1.y + half)]


    slider_def = SliderDef(
        event_out=get_event(event_name),
        min_val=min_val, max_val=max_val, step=step, decimals=decimals,

        min_track_p=[P(p1.x, p1.y)] * 6, min_track_px=collapsed_px,
        max_track_p=track_p,             max_track_px=track_px,

        min_p=P(p1.x, p1.y), min_px=P(px1.x, px1.y),
        max_p=P(p2.x, p1.y), max_px=P(px2.x, px1.y),

        track_poly_def=PolygonDef(
            p=track_p, px=track_px, closed=True,
            fill_color=QColor(255, 255, 255, 30),
            # outline_color=QColor(255, 255, 255, 120), outline_width=1.5,
        ),
        fill_poly_def=PolygonDef(
            p=track_p, px=track_px, closed=True,
            fill_color=QColor(171, 151, 247, 150),
        ),

        knob_poly_def=PolygonDef(
            p=[P(0, 0)] * 4, px=[P(0, -7), P(7, 0), P(0, 7), P(-7, 0)], closed=True,
            fill_color=QColor(255, 255, 255, 220),
            phases={
                'hovered':   Phase([PolygonTween(fill_color=QColor(171, 151, 247, 255), start=0, dur=0.12, ease=QEasingCurve.OutQuint)]),
                'unhovered': Phase([PolygonTween(fill_color=QColor(171, 151, 247, 255), start=0, dur=0.15, ease=QEasingCurve.OutQuint)]),
                'pressed':   Phase([PolygonTween(fill_color=QColor(171, 151, 247, 255), start=0, dur=0.08, ease=QEasingCurve.OutQuint)]),
                'released':  Phase([PolygonTween(fill_color=QColor(171, 151, 247, 255), start=0, dur=0.12, ease=QEasingCurve.OutQuint)]),
            },
        ),

        extra_poly_defs=[
            PolygonDef(
                p=[P(0, 0)] * 4, px=[P(0, -7), P(7, 0), P(0, 7), P(-7, 0)], closed=True,
                fill_color=QColor(0, 0, 0, 0),
                outline_color=QColor(255, 255, 255, 0), outline_width=2.0,
                pos_fn=lambda: get_slider_knob_pos(slider_def),
                phases={
                    'open':      Phase([PolygonTween(px=[P(0,-7),P(7,0),P(0,7),P(-7,0)],     outline_color=QColor(255, 255, 255, 0),   start=0, dur=0.0,  ease=QEasingCurve.Linear)]),
                    'pressed':   Phase([PolygonTween(px=[P(0,-20),P(20,0),P(0,20),P(-20,0)], outline_color=QColor(255, 255, 255, 255), start=0, dur=0.3, ease=QEasingCurve.OutQuint)]),
                    'released':  Phase([PolygonTween(px=[P(0,-7),P(7,0),P(0,7),P(-7,0)],     outline_color=QColor(255, 255, 255, 0),   start=0, dur=0.3,  ease=QEasingCurve.OutQuint)]),
                },
            ),
        ],

        # min_text_def=TextDef(p=P(p1.x, p1.y), px=P(px1.x, px1.y + 14), font_size=9.0, fill_color=QColor(171, 151, 247, 255), h_align=0.0, v_align=0.0),
        # max_text_def=TextDef(p=P(p2.x, p1.y), px=P(px2.x, px1.y + 14), font_size=9.0, fill_color=QColor(171, 151, 247, 255), h_align=1.0, v_align=0.0),
        current_text_def=TextDef(p=P(0, 0), px=P(0, -14), font_size=10.0, fill_color=QColor(171, 151, 247, 255), h_align=0.5, v_align=1.0, text_fn=lambda ctx: ctx._current_text_value() if ctx else '', phases={
            # 'open':      Phase([TextTween(px=[P(0,-7),P(7,0),P(0,7),P(-7,0)],   outline_color=QColor(255,255,255,0),   start=0, dur=0.0,  ease=QEasingCurve.Linear)]),
            'pressed':   Phase([TextTween(px=P(0, -27), start=0, dur=0.3, ease=QEasingCurve.OutQuint)]),
            'released':  Phase([TextTween(px=P(0, -14), start=0, dur=0.3, ease=QEasingCurve.OutQuint)]),
        },),
        # extra_text_defs=[
            # TextDef(p=P(p2.x, p2.y), px=P(px2.x, px2.y - 2), text='ZOOM', bold=True, font_size=30.0, fill_color=QColor(171, 151, 247, 80), h_align=1.0, v_align=1.0),
        # ],
    )
    return slider_def