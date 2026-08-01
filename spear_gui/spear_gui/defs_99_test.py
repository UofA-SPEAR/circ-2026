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
    get_spawn_event, GROUP_EVENT, STATIC, get_spawn_mouse_norm, get_spawn_mouse_offset_px, get_own_window_size_px
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

# MAP WINDOW
map_window = WindowDef(
    p1=P(0.0, 0.0), p2=P((740-70)/1920, 0.6), px1=P(0, 0), px2=P(0, 0),
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
    p1=P(0.0, 0.6), p2=P((740-70)/1920, 1.0), px1=P(0, 0), px2=P(0, 0),
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
    ],
    text_defs=[
        TextDef(p=P(0, 0), px=P(2, 38), text='5.', bold=True, h_align=0, v_align=1, font_size=16, gradient=get_gradient('layout_black_fill')),
        TextDef(p=P(0, 0), px=P(2, 42), text='TASKS', bold=True, h_align=0, v_align=0, font_size=70, gradient=get_gradient('layout_black_fill')),
        TextDef(p=P(0, 0), px=P(32, 38), text='<#> x <#>', h_align=0, v_align=1, font_size=16, gradient=get_gradient('layout_black_fill'), text_fn=lambda ctx: [
            f'{get_own_window_size_px().x:.0f}',
            f'{get_own_window_size_px().y:.0f}',
        ])
    ],
    button_defs=[
        ButtonDef(poly_def=RectDef(p1=P(1, 0), p2=P(1, 0), px1=P(-40, 0), px2=P(0, 40), gradient=get_gradient('layout_black_fill')), event_out=get_event('force_hide_map_window'), action='cycle', event_delta=[True, False]),
    ],
)

layout_window = WindowDef(
    p1=P(0.0, 0.0), p2=P(1, 1),
    listener_defs=[
        EventListener(value_fn=lambda ctx: get_event('layout_mode').value, targets=[get_event('layout_page')], conditions=[lambda v: v], values=['open', 'close']),
    ],
    polygon_defs=background_polygons + [
        PolygonDef(p=[P(0.5, 0.7)]*4, px=[P(-130 - 2, -50), P(-120 + 2, -50), P(-120, 25), P(-130, 25)], gradient=get_gradient('layout_red_fill'), phase_override=get_event('layout_page'), phases={
            'open': Phase([Reset(), PolygonTween(p=[P(0.5, 0.6)]*4, start=0, dur=0.85, ease=QEasingCurve.OutQuint)]),
            'close': Phase([PolygonTween(p=[P(0.5, 0.7)]*4, start=0, dur=0.85, ease=QEasingCurve.OutQuint)]),
        }),
        RectDef(p1=P(0.5, 0.7), p2=P(0.5, 0.7), px1=P(-130, 40), px2=P(-120, 50), gradient=get_gradient('layout_red_fill'), phase_override=get_event('layout_page'), phases={
            'open': Phase([Reset(), RectTween(p1=P(0.5, 0.6), p2=P(0.5, 0.6), start=0, dur=0.85, ease=QEasingCurve.OutQuint)]),
            'close': Phase([RectTween(p1=P(0.5, 0.7), p2=P(0.5, 0.7), start=0, dur=0.85, ease=QEasingCurve.OutQuint)]),
        }),
        PolygonDef(p=[P(0.5, 0.7)]*4, px=[P(120 - 2, -50), P(130 + 2, -50), P(130, 25), P(120, 25)], gradient=get_gradient('layout_red_fill'), phase_override=get_event('layout_page'), phases={
            'open': Phase([Reset(), PolygonTween(p=[P(0.5, 0.6)]*4, start=0, dur=0.85, ease=QEasingCurve.OutQuint)]),
            'close': Phase([PolygonTween(p=[P(0.5, 0.7)]*4, start=0, dur=0.85, ease=QEasingCurve.OutQuint)]),
        }),
        RectDef(p1=P(0.5, 0.7), p2=P(0.5, 0.7), px1=P(120, 40), px2=P(130, 50), gradient=get_gradient('layout_red_fill'), phase_override=get_event('layout_page'), phases={
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
        TextDef(p=P(0.5, 0.7), px=P(0, -2), text='OVERLAP', bold=True, h_align=0.5, v_align=1.0, font_size=30, gradient=get_gradient('layout_red_fill'), phase_override=get_event('layout_page'), phases={
            'open': Phase([Reset(), TextTween(p=P(0.5, 0.6), start=0, dur=0.85, ease=QEasingCurve.OutQuint)]),
            'close': Phase([TextTween(p=P(0.5, 0.7), start=0, dur=0.85, ease=QEasingCurve.OutQuint)]),
        }),
        TextDef(p=P(0.5, 0.7), px=P(0, 2), text='DETECTED', bold=True, h_align=0.5, v_align=0.0, font_size=30, gradient=get_gradient('layout_red_fill'), phase_override=get_event('layout_page'), phases={
            'open': Phase([Reset(), TextTween(p=P(0.5, 0.6), start=0, dur=0.85, ease=QEasingCurve.OutQuint)]),
            'close': Phase([TextTween(p=P(0.5, 0.7), start=0, dur=0.85, ease=QEasingCurve.OutQuint)]),
        }),
    ],
    button_defs=[
        ButtonDef(key=Qt.Key_L, event_out=get_event('layout_mode'), action='cycle', event_delta=[True, False]),
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


WINDOW_DEFS = []
# WINDOW_DEFS.append(task_window)
WINDOW_DEFS.append(layout_window)
WINDOW_DEFS.append(overlay_window)

register_windows(WINDOW_LAYER, WINDOW_DEFS)
