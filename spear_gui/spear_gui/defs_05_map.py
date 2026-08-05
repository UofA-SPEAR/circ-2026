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
import os

WINDOW_LAYER = 0

map_w = 0
map_h = 0
map_p1_x = 0
map_p1_y = 0
map_p2_x = 0
map_p2_y = 0
map_file = 'map_0.png'

def dms_to_decimal(degrees: float, minutes: float, seconds: float, direction: str) -> float:
    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
    if direction.upper() in ['S', 'W']:
        decimal = -decimal
    print(f'{degrees}°, {minutes}\', {seconds}" {direction} -> {round(decimal, 6)}')
    return round(decimal, 6)

def render_map(map_id: int):
    if map_id == 0:
        map_file = 'map_0.png'
        map_w = 3584
        map_h = 3072
        map_p1_x=-110.79643249511719
        map_p1_y=38.410558250946075
        map_p2_x=-110.78681945800781
        map_p2_y=38.40410147066252
    elif map_id == 1:
        map_file = 'map_1.png'
        map_w = 5120
        map_h = 5376
        map_p1_x=dms_to_decimal(53, 31, 52, 'N')
        map_p1_y=dms_to_decimal(113, 31, 52, 'W')
        map_p2_x=dms_to_decimal(53, 31, 22, 'N')
        map_p2_y=dms_to_decimal(113, 31, 4, 'W')

map_file = 'map_1.png'
map_w = 5120
map_h = 5376
map_p1_y=dms_to_decimal(53, 31, 52, 'N')
map_p1_x=dms_to_decimal(113, 31, 52, 'W')
map_p2_y=dms_to_decimal(53, 31, 22, 'N')
map_p2_x=dms_to_decimal(113, 31, 4, 'W')
# render_map(1)

# MAP DATA
register_event(EventDef(name='initial_map_image_px1', value=P(-map_w/2, -map_h/2))) 
register_event(EventDef(name='initial_map_image_px2', value=P(map_w/2, map_h/2))) 
register_event(EventDef(name='map_image_px1', value=P(0, 0))) 
register_event(EventDef(name='map_image_px2', value=P(0, 0))) 

# MAP CORDS
register_event(EventDef(name='p1_pos_x', value=map_p1_x))  # top left corner longitude
register_event(EventDef(name='p1_pos_y', value=map_p1_y))  # top left corner latitude
register_event(EventDef(name='p2_pos_x', value=map_p2_x))  # bottom right corner longitude
register_event(EventDef(name='p2_pos_y', value=map_p2_y))  # bottom right corner latitude

# GENERIC MAP VALUES
register_event(EventDef(name='pos_x',        value=map_p1_x / 2 + map_p2_x / 2))
register_event(EventDef(name='pos_y',        value=map_p1_y / 2 + map_p2_y / 2))
register_event(EventDef(name='map_pos_x',    value=0))
register_event(EventDef(name='map_pos_y',    value=0))
register_event(EventDef(name='map_zoom',     value=1))
register_event(EventDef(name='map_marker_x', value=0))
register_event(EventDef(name='map_marker_y', value=0))
register_event(EventDef(name='map_phase',    value='open'))

# POINTERS
register_event(EventDef(name='map_direction_angle',     value=0.0))
register_event(EventDef(name='map_target_marker_angle', value=0.0))

# SELECTED MARKER
register_event(EventDef(name='targeted_marker',   value=None))
register_event(EventDef(name='marker_name_input', value=''))
register_event(EventDef(name='spawn_marker',      value=False))
register_event(EventDef(name='selected_marker_phase',    value='close'))

# MARKER SPAWN VALUES
register_event(EventDef(name='marker_lat_input', value=''))
register_event(EventDef(name='marker_lon_input', value=''))
register_event(EventDef(name='clear_marker_coord_inputs', value=False))
register_event(EventDef(name='spawn_marker_source', value='mouse'))

# ROUTE TRACKER
register_event(EventDef(name='route_active', value=False))
register_event(EventDef(name='route_spawn_point', value=False))

register_gradient(GradientDef(name="needle_1", p1=P(0.50, 0.50), p2=P(0.50, 0.50), px1=P(0, 0), px2=P(0, 100), radial=True, target="fill", stops=[
        GradientStop(0.0, QColor(245, 69, 69, 255)),
        GradientStop(1.0, QColor(245, 69, 69, 50)),
    ]
))

register_gradient(GradientDef(name="needle_2", p1=P(0.50, 0.50), p2=P(0.50, 0.50), px1=P(0, 0), px2=P(0, 50), radial=True, phase_event=get_event('selected_marker_phase'), target="fill", stops=[
        GradientStop(0.0, QColor(69, 69, 245, 0)),
        GradientStop(1.0, QColor(69, 69, 245, 0)),
    ], phases = {
        'open': Phase([GradientTween(stops=[GradientStop(0.0, QColor(69, 69, 245, 255)), GradientStop(1.0, QColor(69, 69, 245, 50))], start=0, dur=1.0, ease=QEasingCurve.OutQuint)]),
        'close': Phase([GradientTween(stops=[GradientStop(0.0, QColor(69, 69, 245, 0)), GradientStop(1.0, QColor(69, 69, 245, 0))], start=0, dur=1.0, ease=QEasingCurve.OutQuint)]),
    }
))


register_gradient(GradientDef(name="no_marker_selected_text", p1=P(1, 0), p2=P(1, 0), px1=P(0, 30), px2=P(0, 60), phase_event=get_event('selected_marker_phase'), target="fill", stops=[
        GradientStop(0.0, QColor(255, 255, 255, 255)),
        GradientStop(0.99998, QColor(255, 255, 255, 255)),
        GradientStop(0.99999, QColor(255, 255, 255, 0)),
        GradientStop(1.0, QColor(255, 255, 255, 0)),
    ], phases = {
        'close': Phase([GradientTween(stops=[GradientStop(0.0, QColor(255, 255, 255, 255)), GradientStop(0.99998, QColor(255, 255, 255, 255)), GradientStop(0.99999, QColor(255, 255, 255, 0)), GradientStop(1.0, QColor(255, 255, 255, 0))], start=0, dur=0.4, ease=QEasingCurve.OutQuint)]),
        'open':  Phase([GradientTween(stops=[GradientStop(0.0, QColor(255, 255, 255, 255)), GradientStop(0.00001, QColor(255, 255, 255, 255)), GradientStop(0.00002, QColor(255, 255, 255, 0)), GradientStop(1.0, QColor(255, 255, 255, 0))], start=0, dur=0.4, ease=QEasingCurve.OutQuint)]),
    }
))

register_gradient(GradientDef(name="marker_selected_text", p1=P(1, 0), p2=P(1, 0), px1=P(0, 30), px2=P(0, 60), phase_event=get_event('selected_marker_phase'), target="fill", stops=[
        GradientStop(0.49998, QColor(255, 255, 255, 0)),
        GradientStop(0.49999, QColor(255, 255, 255, 255)),
        GradientStop(0.5, QColor(255, 255, 255, 255)),
        GradientStop(0.50001, QColor(255, 255, 255, 255)),
        GradientStop(0.50002, QColor(255, 255, 255, 0)),
    ], phases = {
        'open':  Phase([GradientTween(stops=[GradientStop(0.49998, QColor(255, 255, 255, 0)), GradientStop(0.49999, QColor(255, 255, 255, 255)), GradientStop(0.5, QColor(255, 255, 255, 255)), GradientStop(0.50001, QColor(255, 255, 255, 255)), GradientStop(0.50002, QColor(255, 255, 255, 0))], start=0, dur=0.4, ease=QEasingCurve.OutQuint)]),
        'close': Phase([GradientTween(stops=[GradientStop(0, QColor(255, 255, 255, 0)), GradientStop(0.00001, QColor(255, 255, 255, 255)), GradientStop(0.5, QColor(255, 255, 255, 255)), GradientStop(0.99999, QColor(255, 255, 255, 255)), GradientStop(1, QColor(255, 255, 255, 0))], start=0, dur=0.4, ease=QEasingCurve.OutQuint)]),
    }
))

register_gradient(GradientDef(name='map_grid_line', p1=P(0.5, 0.5), p2=P(1, 1), radial=True, target='outline', stops=[
    GradientStop(0.0, QColor(255, 255, 255, 90)),
    GradientStop(1.0, QColor(255, 255, 255, 0)),
]))

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

p1, p2   = P(0.6, 1), P(1, 1)
px1, px2 = P(0, -25), P(-25, -25)
half     = 3.0

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
    event_out=get_event('map_zoom'),
    min_val=0.1, max_val=4, step=0.05, decimals=2,

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
    extra_text_defs=[
        TextDef(p=P(p2.x, p2.y), px=P(px2.x, px2.y - 2), text='ZOOM', bold=True, font_size=30.0, fill_color=QColor(171, 151, 247, 150), h_align=1.0, v_align=1.0),
    ],
)


# BasicSliderDef(
#     p1=P(0.25, 0.75), p2=P(0.75, 0.75),
#     px1=P(70, -15), px2=P(-15, -15),
#     event_out=get_event('map_zoom'),
#     min_val=0.1, max_val=2.9, step=0.1,
#     label='ZOOM', unit='', decimals=1,
# )







# map_info_window = WindowDef(
#     p1=P(0, 0), p2=P(0.4375, 1), px1=P(40, 40), px2=P(-2, -40),
#     polygon_defs=[
#         # directional needle
#         PolygonDef(p=[P(0.75, 0.37), P(0.75, 0.37), P(0.75, 0.37), P(0.75, 0.37)], px=[P(0, -90), P(7, 0), P(0, 10), P(-7, 0)], gradient=get_gradient('needle'), 
#             rot_center_p=P(0.75, 0.37),
#             # rot_angle_initial=get_event('map_direction_angle'), This line is causing a segmentation fault and idk how to fix it
#         )
#     ],
#     arc_defs=[
#         ArcDef(center_p=P(0.75, 0.37), inner_p=P(0.75, 0.4), inner_px=P(100, 0), outer_p= P(0.75, 0.4), outer_px=P(103, 0), fill_color=QColor(255, 255, 255, 255), outline_width=0),
#     ],
#     text_defs=[
#         TextDef(p=P(0, 0), px=P(0, 0), font_size=25, h_align=0, v_align=0, text='Latitude:   <#> DD', text_fn= lambda ctx: f"{ctx['test_value1']['latest']:.7f}", uniform_scale=False),
#         TextDef(p=P(0, 0), px=P(0, 50), font_size=25, h_align=0, v_align=0, text='Longitude:   <#> DD', text_fn= lambda ctx: f"{ctx['test_value2']['latest']:.7f}", uniform_scale=False),
        
#         TextDef(p=P(0, 0.15), px=P(0, 0), font_size=15, h_align=0, v_align=0, text='Current Speed:   <#> km/h', text_fn= lambda ctx: f"{ctx['test_value3']['latest']:.2f}", uniform_scale=False),
#         TextDef(p=P(0, 0.15), px=P(0, 30), font_size=15, h_align=0, v_align=0, text='Acceleration:   <#> m/s^2', text_fn= lambda ctx: f"{ctx['test_value4']['latest']:.2f}", uniform_scale=False),
#         TextDef(p=P(0, 0.15), px=P(0, 60), font_size=15, h_align=0, v_align=0, text='Anglular Velocity:   <#> ω', text_fn= lambda ctx: f"{ctx['test_value5']['latest']:.2f}", uniform_scale=False),
        
#         TextDef(p=P(0.5, 0.15), px=P(0, 0), font_size=15, h_align=0, v_align=0, text='Pitch:   <#> °', text_fn= lambda ctx: f"{ctx['test_value6']['latest']:.2f}", uniform_scale=False),
#         TextDef(p=P(0.5, 0.15), px=P(0, 30), font_size=15, h_align=0, v_align=0, text='Yaw:   <#> °', text_fn= lambda ctx: f"{ctx['test_value7']['latest']:.2f}", uniform_scale=False),
#         TextDef(p=P(0.5, 0.15), px=P(0, 60), font_size=15, h_align=0, v_align=0, text='Roll:   <#> °', text_fn= lambda ctx: f"{ctx['test_value8']['latest']:.2f}", uniform_scale=False),
        
#         TextDef(p=P(0.75, 0.37), px=P(0, -110), font_size=10, h_align=0.5, v_align=1, text='N', uniform_scale=False),
#         TextDef(p=P(0.75, 0.37), px=P(0, 110), font_size=10, h_align=0.5, v_align=0, text='S', uniform_scale=False),
#         TextDef(p=P(0.75, 0.37), px=P(110, 0), font_size=10, h_align=0, v_align=0.5, text='E', uniform_scale=False),
#         TextDef(p=P(0.75, 0.37), px=P(-110, 0), font_size=10, h_align=1, v_align=0.5, text='W', uniform_scale=False),

#         TextDef(p=P(0, 0.37), px=P(0, -25), font_size=25, h_align=0, v_align=0, text='degrees:   <#> °', text_fn= lambda ctx: f"{ctx['test_value4']['latest']:.2f}", uniform_scale=False),
#         TextDef(p=P(0, 0.37), px=P(0, 25), font_size=25, h_align=0, v_align=0, text='Cardinal dir:   <#>', text_fn= lambda ctx: f"{ctx['test_value4']['latest']:.2f}", uniform_scale=False),
        
#         # -------------- markers
#         TextDef(p=P(0.15, 0.5), px=P(0, 0), font_size=25, h_align=0.5, v_align=0, text='Markers:', uniform_scale=False, fill_color=QColor(255, 255, 255, 190)),
#         TextDef(p=P(0.5, 0.5), px=P(0, 0), font_size=25, h_align=0.5, v_align=0, text='Latitude:', uniform_scale=False, fill_color=QColor(255, 255, 255, 190)),
#         TextDef(p=P(0.85, 0.5), px=P(0, 0), font_size=25, h_align=0.5, v_align=0, text='Longitude:', uniform_scale=False, fill_color=QColor(255, 255, 255, 190)),
#     ],
#     button_defs=[
#         # for creating markers
#         ButtonDef(
#             poly_def = RectDef(p1=P(0.75, 0.9), p2=P(0.75, 0.9), px1=P(2, 0), px2=P(140, 40), fill_color=QColor(240, 100, 230, 200), outline_color=QColor(220, 200, 255, 255), outline_width=1),
#             text_def = TextDef(p=P(0.75, 0.9), px=P(10, 10), font_size=12, h_align=0, v_align=0, text='Create Marker', uniform_scale=False, fill_color=QColor(50, 10, 40, 255)),
#         ),
#         # for rotating needle
#         ButtonDef(key=Qt.Key_Left, action='increment', continuous_update=True, event_out=get_event('map_direction_angle'), event_delta=0.5),
#         ButtonDef(key=Qt.Key_Right, action='increment', continuous_update=True, event_out=get_event('map_direction_angle'), event_delta=-0.5),
#     ],
#     textbox_defs=[
#         TextboxDef(
#             poly_def = RectDef(p1=P(0, 0.9), p2=P(0, 0.9), px1=P(2, 0), px2=P(180, 40), fill_color=QColor(255, 255, 255, 40), outline_color=QColor(220, 200, 255, 255), outline_width=1),
#             text_def = TextDef(p=P(0.0, 0.9), px=P(10, 10), font_size=12, h_align=0, v_align=0, text='Marker Name', uniform_scale=False, fill_color=QColor(255, 255, 255, 255)),
#             max_length = 0, max_length_px = 160
#         ),
#         TextboxDef(
#             poly_def = RectDef(p1=P(0.25, 0.9), p2=P(0.25, 0.9), px1=P(2, 0), px2=P(180, 40), fill_color=QColor(255, 255, 255, 40), outline_color=QColor(220, 200, 255, 255), outline_width=1),
#             text_def = TextDef(p=P(0.25, 0.9), px=P(10, 10), font_size=12, h_align=0, v_align=0, text='Latitude', uniform_scale=False, fill_color=QColor(255, 255, 255, 255)),
#             max_length = 0, max_length_px = 160
#         ),
#         TextboxDef(
#             poly_def = RectDef(p1=P(0.50, 0.9), p2=P(0.50, 0.9), px1=P(2, 0), px2=P(180, 40), fill_color=QColor(255, 255, 255, 40), outline_color=QColor(220, 200, 255, 255), outline_width=1),
#             text_def = TextDef(p=P(0.50, 0.9), px=P(10, 10), font_size=12, h_align=0, v_align=0, text='Longitude', uniform_scale=False, fill_color=QColor(255, 255, 255, 255)),
#             max_length = 0, max_length_px = 160
#         ),
#     ],
#     slider_defs=[
#         slider_def
#     ],
# )


def _delete_targeted_marker():
    marker_id = get_event('targeted_marker').value
    if not marker_id:
        return
    anim = get_animated_window(map_display_window)
    if anim is None:
        get_event('targeted_marker').value = None
        return
    delete_spawned_by_id(anim, marker_id)
    get_event('targeted_marker').value = None

def _deselect_targeted_marker():
    marker_id = get_event('targeted_marker').value
    if not marker_id:
        return
    anim = get_animated_window(map_display_window)
    if anim is None:
        get_event('targeted_marker').value = None
        return
    get_event('targeted_marker').value = None

_marker_names: Dict[str, EventDef] = {}

def get_marker_name_event(obj_id: str) -> EventDef:
    if obj_id not in _marker_names:
        _marker_names[obj_id] = EventDef(name=f'marker_name_{obj_id}', value='MARKER')
    return _marker_names[obj_id]

_marker_positions: Dict[str, Tuple[float, float]] = {}

def _register_marker_position(obj_id: str, statics: list) -> None:
    _marker_positions[obj_id] = (statics[0], statics[1])

def _unregister_marker_position(obj_id: str) -> None:
    _marker_positions.pop(obj_id, None)

def _compute_target_marker_angle(args) -> float:
    target_id, cur_x, cur_y = args
    if not target_id:
        return get_event('map_target_marker_angle').value  # hold last value
    pos = _marker_positions.get(target_id)
    if pos is None:
        return get_event('map_target_marker_angle').value  # hold last value
    marker_x, marker_y = pos
    dx = marker_x + cur_x
    dy = marker_y + cur_y
    # 0=north(-y), 90=east(+x), 180=south(+y), 270=west(-x)
    return math.degrees(math.atan2(dx, -dy)) % 360






SCREEN_OFFSET_LIMIT = 30000.0  # must be under the ±32767 QPainterPath limit

def _latlon_to_map_px(lat: float, lon: float) -> Tuple[float, float]:
    p1x, p2x = get_event('p1_pos_x').value, get_event('p2_pos_x').value
    p1y, p2y = get_event('p1_pos_y').value, get_event('p2_pos_y').value
    ipx1, ipx2 = get_event('initial_map_image_px1').value, get_event('initial_map_image_px2').value
    tx = (lon - p1x) / (p2x - p1x) if p2x != p1x else 0.0
    ty = (lat - p1y) / (p2y - p1y) if p2y != p1y else 0.0
    tx = max(-5.0, min(6.0, tx))
    ty = max(-5.0, min(6.0, ty))
    map_px_x = ipx1.x + tx * (ipx2.x - ipx1.x)
    map_px_y = ipx1.y + ty * (ipx2.y - ipx1.y)
    return map_px_x, map_px_y

def _compute_map_pos_x(args) -> float:
    lon, lat, *_ = args
    px_x, _ = _latlon_to_map_px(lat, lon)
    return -px_x

def _compute_map_pos_y(args) -> float:
    lon, lat, *_ = args
    _, px_y = _latlon_to_map_px(lat, lon)
    return -px_y

def _clamp_screen(v: float) -> float:
    return max(-SCREEN_OFFSET_LIMIT, min(SCREEN_OFFSET_LIMIT, v))

def _map_to_screen_offset(map_x: float, map_y: float) -> P:
    mpx  = get_event('map_pos_x').value
    mpy  = get_event('map_pos_y').value
    zoom = get_event('map_zoom').value
    return P(_clamp_screen((map_x + mpx) * zoom), _clamp_screen((map_y + mpy) * zoom))




def _reset_spawn_source_mouse():
    get_event('spawn_marker_source').value = 'mouse'

from PySide6.QtCore import QTimer

def _spawn_marker_from_coords():
    lat_raw = get_event('marker_lat_input').value
    lon_raw = get_event('marker_lon_input').value
    try:
        lat = float(lat_raw.strip())
        lon = float(lon_raw.strip())
    except (TypeError, ValueError, AttributeError) as e:
        print(f'[spawn_from_coords] invalid input — lat={lat_raw!r} lon={lon_raw!r} error={e}')
        return
    if not (-90.0 <= lat <= 90.0):
        print(f'[spawn_from_coords] lat={lat} out of valid range [-90, 90] — did you swap lat/lon?')
        return
    if not (-180.0 <= lon <= 180.0):
        print(f'[spawn_from_coords] lon={lon} out of valid range [-180, 180] — did you swap lat/lon?')
        return
    print(f'[spawn_from_coords] spawning at lat={lat} lon={lon}')
    get_event('spawn_marker_source').value = 'coords'
    get_event('spawn_marker').value = True
    get_event('clear_marker_coord_inputs').value = True
    QTimer.singleShot(0, lambda: setattr(get_event('clear_marker_coord_inputs'), 'value', False))




_route_last_point_px: Optional[Tuple[float, float]] = None
ROUTE_POINT_THRESHOLD_PX = 2.0

def _register_route_point(obj_id, statics):
    global _route_last_point_px
    _route_last_point_px = (statics[0], statics[1])
    if not get_event('route_active').value:
        _route_last_point_px = None

def _route_start():
    if get_event('route_active').value:
        return
    get_event('route_active').value = True
    get_event('route_spawn_point').value = True

def _route_stop():
    if not get_event('route_active').value:
        return
    get_event('route_active').value = False
    get_event('route_spawn_point').value = True

def _route_tick(args):
    active, mpx, mpy = args
    if not active or _route_last_point_px is None:
        return None
    player_x, player_y = -mpx, -mpy
    lx, ly = _route_last_point_px
    if math.hypot(player_x - lx, player_y - ly) >= ROUTE_POINT_THRESHOLD_PX:
        get_event('route_spawn_point').value = True
    return None

def _route_clear():
    global _route_last_point_px
    anim = get_animated_window(map_display_window)
    if anim is not None:
        clear_spawned_by_group(anim, 'routepoint')
    _route_last_point_px = None












def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi    = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))

def _meters_per_map_px_x() -> float:
    p1y = get_event('p1_pos_y').value
    p1x = get_event('p1_pos_x').value
    p2x = get_event('p2_pos_x').value
    ipx1 = get_event('initial_map_image_px1').value
    ipx2 = get_event('initial_map_image_px2').value
    dist_m  = _haversine_m(p1y, p1x, p1y, p2x)
    px_span = abs(ipx2.x - ipx1.x)
    return dist_m / px_span if px_span > 0 else 0.0

_NICE_SCALE_STEPS_M = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000]
SCALE_BAR_TARGET_PX = 120.0

def _pick_nice_scale(target_m: float) -> float:
    if target_m <= 0:
        return _NICE_SCALE_STEPS_M[0]
    best = _NICE_SCALE_STEPS_M[0]
    for step in _NICE_SCALE_STEPS_M:
        if step <= target_m:
            best = step
        else:
            break
    return best

def _current_scale_bar() -> Tuple[float, float]:
    """Returns (distance_in_meters, bar_width_in_screen_px)."""
    mppx = _meters_per_map_px_x()
    zoom = get_event('map_zoom').value
    if mppx <= 0 or zoom <= 0:
        return 0.0, 0.0
    meters_per_screen_px = mppx / zoom
    if meters_per_screen_px <= 0:
        return 0.0, 0.0
    target_m = SCALE_BAR_TARGET_PX * meters_per_screen_px
    nice_m   = _pick_nice_scale(target_m)
    bar_px   = nice_m / meters_per_screen_px
    return nice_m, bar_px

def _scale_bar_offsets() -> List[P]:
    _, bar_px = _current_scale_bar()
    base_x, base_y, h = 20.0, -20.0, 4.0
    return [
        P(base_x, base_y - h),
        P(base_x, base_y + h),
        P(base_x + bar_px, base_y + h),
        P(base_x + bar_px, base_y - h),
    ]

def _scale_bar_text_pos() -> P:
    _, bar_px = _current_scale_bar()
    base_x, base_y, h = 20.0, -20.0, 4.0
    return P(base_x + bar_px / 2.0, base_y - h - 4.0)

def _scale_bar_text(ctx) -> str:
    nice_m, _ = _current_scale_bar()
    if nice_m >= 1000:
        return f'{nice_m / 1000:.0f} km'
    return f'{nice_m:.0f} m'


GRID_LINE_COUNT = 30

def _grid_spacing_map_px() -> float:
    mppx = _meters_per_map_px_x()
    if mppx <= 0:
        return 0.0
    nice_m, _ = _current_scale_bar()
    return nice_m / mppx

def _map_x_to_screen(map_x: float) -> float:
    mpx  = get_event('map_pos_x').value
    zoom = get_event('map_zoom').value
    return _clamp_screen((map_x + mpx) * zoom)

def _map_y_to_screen(map_y: float) -> float:
    mpy  = get_event('map_pos_y').value
    zoom = get_event('map_zoom').value
    return _clamp_screen((map_y + mpy) * zoom)

def _make_vertical_gridline_pos_fn(index: int):
    def _fn():
        spacing = _grid_spacing_map_px()
        return P(_map_x_to_screen(index * spacing), 0.0)
    return _fn

def _make_horizontal_gridline_pos_fn(index: int):
    def _fn():
        spacing = _grid_spacing_map_px()
        return P(0.0, _map_y_to_screen(index * spacing))
    return _fn

map_grid_lines: List[PolygonDef] = []
for i in range(-GRID_LINE_COUNT, GRID_LINE_COUNT + 1):
    map_grid_lines.append(PolygonDef(
        p=[P(0.5, 0.0), P(0.5, 1.0)], px=[P(0, 0), P(0, 0)], closed=False,
        outline_color=QColor(255, 255, 255, 90), outline_width=1.0,
        gradient=get_gradient('map_grid_line'),
        pos_fn=_make_vertical_gridline_pos_fn(i),
    ))
    map_grid_lines.append(PolygonDef(
        p=[P(0.0, 0.5), P(1.0, 0.5)], px=[P(0, 0), P(0, 0)], closed=False,
        outline_color=QColor(255, 255, 255, 90), outline_width=1.0,
        gradient=get_gradient('map_grid_line'),
        pos_fn=_make_horizontal_gridline_pos_fn(i),
    ))











map_info_window = WindowDef(
    p1=P(0.0, 0.0), p2=P(1.0, 1.0),
    phase_event=get_event('map_phase'),
    polygon_defs=[
        PolygonDef(p=[P(0, 1)] * 4, px=[P(0, 0)] * 4, fill_color=QColor(255, 255, 255, 200), outline_color=QColor(0, 0, 0, 160), outline_width=1.0, pos_fn=lambda: _scale_bar_offsets()),
    ],
    text_defs=[
        TextDef(p=P(0, 0), px=P(10, 12), text='SPAWN MARKER', font_size=14, bold=True, fill_color=QColor(171, 151, 247, 255), h_align=0.0, v_align=0),
        TextDef(p=P(1, 0), px=P(-10, 12), text='MARKER INFO', font_size=14, bold=True, fill_color=QColor(171, 151, 247, 255), h_align=1.0, v_align=0),
        TextDef(p=P(1, 0), px=P(-10, 30), text='NO MARKER SELECTED', font_size=11, fill_color=QColor(255, 255, 255, 255), h_align=1.0, v_align=0, gradient=get_gradient('no_marker_selected_text')),
            # text_fn=lambda ctx: 'NO MARKER SELECTED' if not get_event('targeted_marker').value else f"selected: {get_event('targeted_marker').value}"),
        # TextDef(p=P(1, 0), px=P(-10, 40), font_size=11, fill_color=QColor(200, 200, 220, 200), h_align=1.0, v_align=0,
        #     text_fn=lambda ctx: get_event('selected_marker_phase').value)
        TextDef(p=P(0, 1), px=P(0, 0), font_size=10, h_align=0.5, v_align=1.0, fill_color=QColor(255, 255, 255, 255), uniform_scale=False, text_fn=_scale_bar_text, pos_fn=lambda: _scale_bar_text_pos()),
    ],
    textbox_defs=[
        TextboxDef(
            poly_def=RectDef(p1=P(1.0, 0.0), p2=P(1.0, 0.0), px1=P(-250, 30), px2=P(-100, 60), fill_color=QColor(101, 81, 176, 120), outline_color=QColor(171, 151, 247, 255), outline_width=0,
            phases={
                'open':  Phase([RectTween(fill_color=QColor(101, 81, 176, 120), outline_width=1, px1=P(-250, 30), px2=P(-100, 60), start=0, dur=0.4, ease=QEasingCurve.OutQuint)]),
                'close': Phase([RectTween(fill_color=QColor(101, 81, 176, 120), outline_width=0, px1=P(-250, 45), px2=P(-100, 45), start=0, dur=0.4, ease=QEasingCurve.OutQuint)]),
            }),
            text_def=TextDef(p=P(1.0, 0.0), px=P(-175, 45), fill_color=QColor(255, 255, 255, 255), font_size=12, h_align=0.5, v_align=0.5, gradient=get_gradient('marker_selected_text'),
            phases={
                'open': Phase([TextTween(fill_color=QColor(255, 255, 255, 255), start=0, dur=0.4, ease=QEasingCurve.OutQuint)]),
                'close': Phase([TextTween(fill_color=QColor(255, 255, 255, 0), start=0, dur=0.4, ease=QEasingCurve.OutQuint)]),
            }),
            preview_text_def=TextDef(p=P(1.0, 0.0), px=P(-175, 45), text='RENAME', font_size=12, h_align=0.5, v_align=0.5, fill_color=QColor(255,255,255,255), gradient=get_gradient('marker_selected_text'),
            phases={
                'open': Phase([TextTween(fill_color=QColor(255, 255, 255, 255), start=0, dur=0.4, ease=QEasingCurve.OutQuint)]),
                'close': Phase([TextTween(fill_color=QColor(255, 255, 255, 0), start=0, dur=0.4, ease=QEasingCurve.OutQuint)]),
            }),
            phase_override=get_event('selected_marker_phase'),
            event_out=get_event('marker_name_input'),
            max_length_px=150,
            clear_when_sent=True,
            override_inputs=True,
            exit_when_sent=True,
        ),

        TextboxDef(
            poly_def=RectDef(p1=P(0.0, 0.0), p2=P(0.0, 0.0), px1=P(5, 30), px2=P(105, 60), fill_color=QColor(101, 81, 176, 120), outline_color=QColor(171, 151, 247, 255), outline_width=1),
            text_def=TextDef(p=P(0.0, 0.0), px=P(55, 45), fill_color=QColor(255, 255, 255, 255), font_size=12, h_align=0.5, v_align=0.5),
            preview_text_def=TextDef(p=P(0.0, 0.0), px=P(55, 45), text='LATITUDE', font_size=12, h_align=0.5, v_align=0.5, fill_color=QColor(255,255,255,255),
            phases={
                'open': Phase([TextTween(fill_color=QColor(255, 255, 255, 255), start=0, dur=0.4, ease=QEasingCurve.OutQuint)]),
                'close': Phase([TextTween(fill_color=QColor(255, 255, 255, 0), start=0, dur=0.4, ease=QEasingCurve.OutQuint)]),
            }),
            live_event_out=get_event('marker_lat_input'),
            clear_event=get_event('clear_marker_coord_inputs'),
            max_length_px=100,
            override_inputs=True,
            exit_when_sent=True,
            clear_when_sent=False,
        ),
        TextboxDef(
            poly_def=RectDef(p1=P(0.0, 0.0), p2=P(0.0, 0.0), px1=P(110, 30), px2=P(210, 60), fill_color=QColor(101, 81, 176, 120), outline_color=QColor(171, 151, 247, 255), outline_width=1),
            text_def=TextDef(p=P(0.0, 0.0), px=P(160, 45), fill_color=QColor(255, 255, 255, 255), font_size=12, h_align=0.5, v_align=0.5),
            preview_text_def=TextDef(p=P(0.0, 0.0), px=P(160, 45), text='LONGITUDE', font_size=12, h_align=0.5, v_align=0.5, fill_color=QColor(255,255,255,255),
            phases={
                'open': Phase([TextTween(fill_color=QColor(255, 255, 255, 255), start=0, dur=0.4, ease=QEasingCurve.OutQuint)]),
                'close': Phase([TextTween(fill_color=QColor(255, 255, 255, 0), start=0, dur=0.4, ease=QEasingCurve.OutQuint)]),
            }),
            live_event_out=get_event('marker_lon_input'),
            clear_event=get_event('clear_marker_coord_inputs'),
            max_length_px=100,
            override_inputs=True,
            exit_when_sent=True,
            clear_when_sent=False,
        ),
    ],
    button_defs=[
        ButtonDef(
            poly_def=RectDef(p1=P(1.0, 0.0), p2=P(1.0, 0.0), px1=P(-95, 45), px2=P(-5, 45), fill_color=QColor(150, 40, 40, 180), outline_color=QColor(220, 80, 80, 0), outline_width=0, phase_override=get_event('selected_marker_phase'), 
            phases={
                'open':  Phase([RectTween(fill_color=QColor(150, 40, 40, 180), px1=P(-95, 30), px2=P(-5, 60), start=0, dur=0.4, ease=QEasingCurve.OutQuint)]),
                'close': Phase([RectTween(fill_color=QColor(150, 40, 40, 180), px1=P(-95, 45), px2=P(-5, 45), start=0, dur=0.4, ease=QEasingCurve.OutQuint)]),
            }),
            text_def=TextDef(p=P(1.0, 0.0), px=P(-50, 45), text='DELETE', bold=True, font_size=12, h_align=0.5, v_align=0.5, fill_color=QColor(255, 255, 255, 255), gradient=get_gradient('marker_selected_text'), phase_override=get_event('selected_marker_phase'),
            phases={
                'open': Phase([TextTween(fill_color=QColor(255, 255, 255, 255), start=0, dur=0.4, ease=QEasingCurve.OutQuint)]),
                'close': Phase([TextTween(fill_color=QColor(255, 255, 255, 0), start=0, dur=0.4, ease=QEasingCurve.OutQuint)]),
            }),
            phase_override=get_event('selected_marker_phase'),
            action='set',
            event_out=get_event('targeted_marker'),
            event_delta=None,
            on_fire=_delete_targeted_marker,
        ),
        ButtonDef(
            poly_def=RectDef(p1=P(0.0, 0.0), p2=P(0.0, 0.0), px1=P(215, 30), px2=P(275, 60), fill_color=QColor(60, 130, 80, 180), outline_color=QColor(90, 200, 130, 255), outline_width=1),
            text_def=TextDef(p=P(0.0, 0.0), px=P(245, 45), text='SPAWN', bold=True, font_size=12, h_align=0.5, v_align=0.5, fill_color=QColor(255, 255, 255, 255)),
            action='set',
            event_out=get_event('spawn_marker_source'),
            event_delta=None,
            on_fire=_spawn_marker_from_coords,
        ),
        ButtonDef(
            poly_def=RectDef(p1=P(0.0, 0.0), p2=P(0.0, 0.0), px1=P(5, 70), px2=P(85, 100), fill_color=QColor(60, 130, 80, 180), outline_color=QColor(90, 200, 130, 255), outline_width=1),
            text_def=TextDef(p=P(0.0, 0.0), px=P(45, 85), text='START', bold=True, font_size=11, h_align=0.5, v_align=0.5, fill_color=QColor(255, 255, 255, 255)),
            action='set', event_out=get_event('route_active'), event_delta=None,
            on_fire=_route_start,
        ),
        ButtonDef(
            poly_def=RectDef(p1=P(0.0, 0.0), p2=P(0.0, 0.0), px1=P(90, 70), px2=P(170, 100), fill_color=QColor(150, 40, 40, 180), outline_color=QColor(220, 80, 80, 255), outline_width=1),
            text_def=TextDef(p=P(0.0, 0.0), px=P(130, 85), text='STOP', bold=True, font_size=11, h_align=0.5, v_align=0.5, fill_color=QColor(255, 255, 255, 255)),
            action='set', event_out=get_event('route_active'), event_delta=None,
            on_fire=_route_stop,
        ),
        ButtonDef(
            poly_def=RectDef(p1=P(0.0, 0.0), p2=P(0.0, 0.0), px1=P(175, 70), px2=P(255, 100), fill_color=QColor(90, 90, 100, 180), outline_color=QColor(150, 150, 165, 255), outline_width=1),
            text_def=TextDef(p=P(0.0, 0.0), px=P(215, 85), text='CLEAR', bold=True, font_size=11, h_align=0.5, v_align=0.5, fill_color=QColor(255, 255, 255, 255)),
            action='set', event_out=get_event('route_active'), event_delta=None,
            on_fire=_route_clear,
        ),
    ],
    slider_defs=[
        slider_def
    ],
)


map_image_window = WindowDef(
    p1=P(0.0, 0.0), p2=P(1.0, 1.0), px1=P(0, 0), px2=P(0, 0),
    phase_event=get_event('main_page'),
    listener_defs=[
        EventListener(value_fn=lambda ctx: (get_event('initial_map_image_px1').value, get_event('map_zoom').value, get_event('map_pos_x').value, get_event('map_pos_y').value), targets=[get_event('map_image_px1')], passthrough=True, transform=lambda v: P(_clamp_screen((v[0].x + v[2]) * v[1]), _clamp_screen((v[0].y + v[3]) * v[1]))),
        EventListener(value_fn=lambda ctx: (get_event('initial_map_image_px2').value, get_event('map_zoom').value, get_event('map_pos_x').value, get_event('map_pos_y').value), targets=[get_event('map_image_px2')], passthrough=True, transform=lambda v: P(_clamp_screen((v[0].x + v[2]) * v[1]), _clamp_screen((v[0].y + v[3]) * v[1]))),
    ],
    polygon_defs=[
        RectDef(p1=P(0.5, 0.5), p2=P(0.5, 0.5), px1=P(-500, -500), px2=P(500, 500),
            image_path=os.path.join(os.path.dirname(__file__), map_file),
            phases={
                'open': Phase([RectTween(px1=get_event('map_image_px1'), px2=get_event('map_image_px2'), start=0.0, dur=0.0, ease=QEasingCurve.Linear)], update_retrigger=True)
            },
        ),
        RectDef(p1=P(0, 0), p2=P(1, 1), fill_color=QColor(0, 0, 0, 127)),
    ],
    # text_defs=[
    #     TextDef(p=P(0.5, 0.5), text='(<#>, <#>)', font_size=20, h_align=0, v_align=1, uniform_scale=False,
    #         text_fn=lambda ctx: [
    #             f"{get_event('map_image_px1').value.x:.2f}, {get_event('map_image_px1').value.y:.2f}",
    #             f"{get_event('map_image_px2').value.x:.2f}, {get_event('map_image_px2').value.y:.2f}",
    #         ],
    #     ),
    # ]
)

map_display_window = WindowDef(
    p1=P(0.0, 0.0), p2=P(1.0, 1.0), px1=P(0, 0), px2=P(0, 0),
    phase_event=get_event('map_phase'),
    deselect_event=get_event('targeted_marker'),
    listener_defs=[
        EventListener(
            value_fn=lambda ctx: (get_event('pos_x').value, get_event('pos_y').value, get_event('p1_pos_x').value, get_event('p1_pos_y').value, get_event('p2_pos_x').value, get_event('p2_pos_y').value),
            targets=[get_event('map_pos_x')], passthrough=True, transform=_compute_map_pos_x,
        ),
        EventListener(
            value_fn=lambda ctx: (get_event('pos_x').value, get_event('pos_y').value, get_event('p1_pos_x').value, get_event('p1_pos_y').value, get_event('p2_pos_x').value, get_event('p2_pos_y').value),
            targets=[get_event('map_pos_y')], passthrough=True, transform=_compute_map_pos_y,
        ),
        EventListener(value_fn=lambda ctx: get_event('targeted_marker').value, targets=[get_event('selected_marker_phase')], skip_none=False, conditions=[lambda v: bool(v)], values=['open', 'close']),
        EventListener(
            value_fn=lambda ctx: (get_event('route_active').value, get_event('map_pos_x').value, get_event('map_pos_y').value),
            targets=[], passthrough=True, transform=_route_tick,
        ),
    ],
    polygon_defs=[
        RectDef(p1=P(0.0, 0.0), p2=P(1.0, 1.0), fill_color=QColor(255, 255, 255, 10), outline_color=QColor(255, 255, 255, 255), outline_width=1),
        *map_grid_lines,
        PolygonDef(p=[P(0.5, 0.5)]*4, px=[P(-10, 0), P(0, -10), P(10, 0), P(0, 10)], fill_color=QColor(200, 200, 255, 255)),
        PolygonDef(p=[P(0.5, 0.5), P(0.5, 0.5), P(0.5, 0.5), P(0.5, 0.5)], px=[P(0, -100), P(6, -21), P(0, -15), P(-6, -21)], gradient=get_gradient('needle_1'), outline_color=QColor(255, 0, 0, 255), outline_width=1.0, 
            rot_center_p=P(0.5, 0.5), rot_angle=0,
            rot_angle_fn=lambda: get_event('map_direction_angle').value,
        ),
        PolygonDef(p=[P(0.5, 0.5), P(0.5, 0.5), P(0.5, 0.5), P(0.5, 0.5)], px=[P(0, -65), P(4, -19), P(0, -15), P(-4, -19)], gradient=get_gradient('needle_2'), outline_color=QColor(0, 0, 255, 255), outline_width=1.0, 
            rot_center_p=P(0.5, 0.5), rot_angle=0,
            rot_angle_fn=lambda: get_event('map_target_marker_angle').value,
        ),
    ],
    text_defs=[
        TextDef(p=P(0.5, 0), px=P(0, 20), font_size=20, v_align=0, text='N', uniform_scale=False),
        TextDef(p=P(0.5, 1), px=P(0, -20), font_size=20, v_align=1, text='S', uniform_scale=False),
        TextDef(p=P(0, 0.5), px=P(20, 0), font_size=20, h_align=0, text='W', uniform_scale=False),
        TextDef(p=P(1, 0.5), px=P(-20, 0), font_size=20, h_align=1, text='E', uniform_scale=False),
        TextDef(p=P(0, 1), px=P(2, -2), text='(<#>, <#>)', font_size=10, h_align=0, v_align=1, uniform_scale=False,
            text_fn=lambda ctx: [f"{get_event('map_pos_x').value:.7f}", f"{get_event('map_pos_y').value:.7f}"],
        ),
    ],
    button_defs=[
        ButtonDef(key=Qt.Key_Up, action='increment', continuous_update=True, event_out=get_event('pos_y'), event_delta=0.0001),
        ButtonDef(key=Qt.Key_Down, action='increment', continuous_update=True, event_out=get_event('pos_y'), event_delta=-0.0001),
        ButtonDef(key=Qt.Key_Right, action='increment', continuous_update=True, event_out=get_event('pos_x'), event_delta=0.0001),
        ButtonDef(key=Qt.Key_Left, action='increment', continuous_update=True, event_out=get_event('pos_x'), event_delta=-0.0001),
        ButtonDef(poly_def=RectDef(p1=P(0, 0), p2=P(1, 1)), key=Qt.Key_P, mandatory_keys=Qt.Key_Shift, action='set',
            event_out=get_event('spawn_marker'), event_delta=True, invisible=True, ignore_click_consume=True,
            on_fire=_reset_spawn_source_mouse),
    ],
    sub_windows=[
        WindowDef(
            p1=P(0, 0), p2=P(1, 1),
            polygon_defs=[
                PolygonDef(
                    p=[P(0.5, 0.5)] * 2, px=[P(0, 0), P(0, 0)], closed=False,
                    outline_color=QColor(0, 255, 0, 150), outline_width=2.0,
                    pos_fn=lambda self_x=STATIC(0), self_y=STATIC(1), prev_x=STATIC(2), prev_y=STATIC(3): [
                        _map_to_screen_offset(prev_x, prev_y),
                        _map_to_screen_offset(self_x, self_y),
                    ],
                ),
                PolygonDef(
                    p=[P(0.5, 0.5)] * 4, px=[P(-4, 0), P(0, -4), P(4, 0), P(0, 4)],
                    fill_color=QColor(0, 255, 0, 255),
                    pos_fn=lambda self_x=STATIC(0), self_y=STATIC(1): _map_to_screen_offset(self_x, self_y),
                ),
            ],
            spawn_event=get_event('route_spawn_point'),
            spawn_event_group='routepoint',
            spawn_delete_threshold=1,
            spawn_limit=9999,
            on_spawn=_register_route_point,
            spawn_static_values=[
                lambda: -get_event('map_pos_x').value,
                lambda: -get_event('map_pos_y').value,
                lambda: _route_last_point_px[0] if _route_last_point_px is not None else -get_event('map_pos_x').value,
                lambda: _route_last_point_px[1] if _route_last_point_px is not None else -get_event('map_pos_y').value,
            ],
        ),
        WindowDef(
            p1=P(0, 0), p2=P(1, 1),
            spawn_name_event_fn=get_marker_name_event,
            select_event=get_event('targeted_marker'),
            polygon_defs=[
                PolygonDef(
                    p=[P(0.5, 0.5)]*3, px=[P(-5, -5), P(-10, 0), P(-5, 5)], closed=False,
                    fill_color=QColor(0, 0, 0, 0),
                    outline_color=QColor(171, 151, 247, 0), outline_width=2.0,
                    pos_fn=lambda marker_x=STATIC(0), marker_y=STATIC(1): _map_to_screen_offset(marker_x, marker_y),
                    phase_override=SELF_ID,
                    phases={
                        'unselected': Phase([PolygonTween(px=[P(-5, -5), P(-10, 0), P(-5, 5)], outline_color=QColor(171, 151, 247, 0),   start=0, dur=0.2, ease=QEasingCurve.OutQuint)]),
                        'selected':   Phase([PolygonTween(px=[P(-17, -5), P(-22, 0), P(-17, 5)], outline_color=QColor(171, 151, 247, 255), start=0, dur=0.25, ease=QEasingCurve.OutBack)]),
                    },
                ),
                PolygonDef(
                    p=[P(0.5, 0.5)]*3, px=[P(5, -5), P(10, 0), P(5, 5)], closed=False,
                    fill_color=QColor(0, 0, 0, 0),
                    outline_color=QColor(171, 151, 247, 0), outline_width=2.0,
                    pos_fn=lambda marker_x=STATIC(0), marker_y=STATIC(1): _map_to_screen_offset(marker_x, marker_y),
                    phase_override=SELF_ID,
                    phases={
                        'unselected': Phase([PolygonTween(px=[P(5, -5), P(10, 0), P(5, 5)], outline_color=QColor(171, 151, 247, 0),   start=0, dur=0.2, ease=QEasingCurve.OutQuint)]),
                        'selected':   Phase([PolygonTween(px=[P(17, -5), P(22, 0), P(17, 5)], outline_color=QColor(171, 151, 247, 255), start=0, dur=0.25, ease=QEasingCurve.OutBack)]),
                    },
                ),
            ],
            text_defs=[
                TextDef(p=P(0.5, 0.5), px=P(0, -10), font_size=10, v_align=1, uniform_scale=False, fill_color=QColor(171, 151, 247, 255),
                    text_fn=SELF_ID,
                    pos_fn=lambda marker_x=STATIC(0), marker_y=STATIC(1): _map_to_screen_offset(marker_x, marker_y),
                ),
            ],
            button_defs=[
                ButtonDef(
                    poly_def=PolygonDef(p=[P(0.5, 0.5)]*4, px=[P(-10, 0), P(0, -10), P(10, 0), P(0, 10)], fill_color=QColor(171/8, 151/8, 247/8, 255),
                        pos_fn=lambda marker_x=STATIC(0), marker_y=STATIC(1): _map_to_screen_offset(marker_x, marker_y),
                    ),
                    action='set',
                    event_out=SELECT_EVENT,
                    event_delta=SELF_ID,
                )
            ],
            spawn_event=get_event('spawn_marker'),
            spawn_event_group='marker',
            phase_event=GROUP_EVENT,
            spawn_delete_threshold=1,
            on_spawn=_register_marker_position,
            on_despawn=_unregister_marker_position,
            spawn_static_values=[
                lambda: (_latlon_to_map_px(float(get_event('marker_lat_input').value), float(get_event('marker_lon_input').value))[0]
                        if get_event('spawn_marker_source').value == 'coords'
                        else -get_event('map_pos_x').value + get_spawn_mouse_offset_px().x / get_event('map_zoom').value),
                lambda: (_latlon_to_map_px(float(get_event('marker_lat_input').value), float(get_event('marker_lon_input').value))[1]
                        if get_event('spawn_marker_source').value == 'coords'
                        else -get_event('map_pos_y').value + get_spawn_mouse_offset_px().y / get_event('map_zoom').value),
                lambda: 'MARKER',
            ],
        ),
    ]
)


map_window = WindowDef(
    p1=P(0.0, 0.0), p2=P(0.4, 0.4),
    hidden_event=get_event('window_disabled_map'),
    phase_event=get_event('content_phase_map'),
    phases={
        'open': Phase([WindowTween(p1=get_event('map_window_p1'), p2=get_event('map_window_p2'), px1=get_event('map_window_px1'), px2=get_event('map_window_px2'), start=0.0, dur=1.0, ease=QEasingCurve.OutQuint)], update_retrigger=True)
    },
    listener_defs=[
        EventListener(
            value_fn=lambda ctx: get_event('marker_name_input').value,
            targets=[],
            passthrough=True,
            wait_for_updates=lambda ctx: get_event('marker_name_input').value,
            transform=lambda v: (get_marker_name_event(get_event('targeted_marker').value).__setattr__('value', v), v)[1] if get_event('targeted_marker').value else None,
        ),
        EventListener(
            value_fn=lambda ctx: (get_event('targeted_marker').value, get_event('map_pos_x').value, get_event('map_pos_y').value),
            targets=[get_event('map_target_marker_angle')],
            passthrough=True,
            transform=_compute_target_marker_angle,
        ),
    ],
    polygon_defs=[
        RectDef(p1=P(0, 0), p2=P(1, 1), fill_color=QColor(0, 0, 0, 155))
    ],
    button_defs=[
        ButtonDef(key=Qt.Key_E, action='increment', continuous_update=True, event_out=get_event('map_direction_angle'), event_delta=45),
        ButtonDef(key=Qt.Key_Q, action='increment', continuous_update=True, event_out=get_event('map_direction_angle'), event_delta=-45),
        ButtonDef(poly_def=RectDef(p1=P(0, 0), p2=P(1, 1), fill_color=QColor(255, 0, 0, 100)), key=Qt.Key_O, action='set',
            event_out=get_event('targeted_marker'),
            event_delta=None,
            on_fire=_deselect_targeted_marker, invisible=True),
    ],

    sub_windows=[map_image_window, map_display_window, map_info_window]
)

WINDOW_DEFS = []
WINDOW_DEFS.append(map_window)

register_windows(WINDOW_LAYER, WINDOW_DEFS)