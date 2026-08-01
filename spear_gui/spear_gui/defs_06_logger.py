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
    get_spawn_event, GROUP_EVENT, STATIC, get_spawn_mouse_norm, get_spawn_mouse_offset_px
)

from datetime import datetime
from zoneinfo import ZoneInfo

register_event(EventDef(name="textbox_test_value", value=''))
register_event(EventDef(name="new_log", value=None))

WINDOW_LAYER = 0

logger_phases = {}
for i in range(100):
    y = -70 - i * 15
    name = 'open' if i == 0 else 'close' if i == 100 else str(i)
    logger_phases[name] = Phase([WindowTween(px1=P(9, y - 10), px2=P(-9, y + 10), start=0, dur=0.5, ease=QEasingCurve.OutQuint)])

logger_window = WindowDef(
    p1=P(0.0, 0.0), p2=P(0.5, 1.0),
    phase_event=get_event('main_page'),
    phases={
        'open': Phase([WindowTween(p1=get_event('logger_window_p1'), p2=get_event('logger_window_p2'), px1=get_event('logger_window_px1'), px2=get_event('logger_window_px2'), start=0.0, dur=1.0, ease=QEasingCurve.OutQuint)], update_retrigger=True)
    },
    # phase_event=get_event('main_page'),
    # phases={
    #     'open': Phase([WindowTween(p1=P(0.5, 0.0), p2=P(0.5, 1.0), px1=P(-157 - 8, 0), px2=P(157 + 8, 0), start=0.5, dur=1.0, ease=QEasingCurve.OutQuint)])
    # },
    listener_defs=[
        EventListener(value_fn=lambda ctx: ctx['test_value1']['latest'], targets=[get_event('textbox_test_value')], passthrough=True),
        EventListener(value_fn=True, targets=[get_event('new_log')], passthrough=True, wait_for_updates=get_event('textbox_test_value')),
    ],
    polygon_defs=[
        RectDef(p1=P(0, 0.5), p2=P(0, 0.5), px1=P(70, 0), px2=P(70, 0), fill_color=QColor(0, 0, 0, 200), phase_override=get_event('main_page'), phases={
            'open': Phase([RectTween(p1=P(0, 0), p2=P(1, 1), px1=P(9, 25), px2=P(-9, -25), start=0.5, dur=0.5, ease=QEasingCurve.OutQuint)])
        }),
        PolygonDef(p=[P(0, 0.5), P(0, 0.5), P(0, 0.5), P(0, 0.5)], px=[P(62, 0), P(70, 0), P(70, 0), P(62, 0)], fill_color=QColor(255, 255, 255, 0), outline_width=2, closed=False, gradient=get_gradient('alt_color_outline'), phase_override=get_event('main_page'), phases={
            'open': Phase([PolygonTween(p=[P(0, 0), P(0, 0), P(0, 1), P(0, 1)], px=[P(62, 25 - 8), P(70, 25), P(70, -25), P(62, -25 + 8)], start=0.0, dur=0.5, ease=QEasingCurve.OutQuint),
                            PolygonTween(p=[P(0, 0), P(0, 0), P(0, 1), P(0, 1)], px=[P(1, 25 - 8), P(9, 25), P(9, -25), P(1, -25 + 8)], start=0.5, dur=1.0, ease=QEasingCurve.OutQuint)])
        },)
    ],
    text_defs=[
        # TextDef(p=P(0.5, 0), px=P(0, 0), text='LOGGER', bold=True, font_size=70, h_align=0.5, v_align=1.0, char_display=0, sub_char_clip=True, fill_color=QColor(255,255,255,0), gradient=get_gradient('alt_color_outline'), outline_width=2, phases={
        #         'open': Phase([TextTween(px=P(0, 22), v_align=0.0, char_display=1, start=0.5, dur=1.0, ease=QEasingCurve.OutQuint)]),
        #         'close': Phase([TextTween(px=P(0, 0), v_align=1.0, start=0.0, dur=1.0, ease=QEasingCurve.OutQuint)]),
        #     }
        # ),
    ],
    sub_windows=[
        WindowDef(
            p1=P(0.00, 1.00), p2=P(1.00, 1.00), px1=P(9, -10), px2=P(-9, 10),
            spawn_event=get_event('new_log'),
            spawn_event_group='log',
            spawn_tick_increment=True,
            spawn_delete_threshold=100,
            spawn_limit=101,
            spawn_static_values=[lambda: datetime.now(ZoneInfo("America/Edmonton")).strftime("%H:%M:%S.%f")[:-4]],
            phase_event=GROUP_EVENT,
            phase_fn=lambda v: str(int(v)) if int(v) > 0 else 'open',
            phases=logger_phases,
            text_defs=[
                TextDef(
                    p=P(0, 0.5), px=P(90, 0),
                    text='log entry',
                    font_size=10.0,
                    fill_color=QColor(255, 255, 255, 200),
                    h_align=0.0, v_align=0.5,
                    text_fn=get_event('textbox_test_value'),
                ),
                TextDef(
                    p=P(0, 0.5), px=P(1, 0),
                    text='log entry',
                    font_size=10.0,
                    fill_color=QColor(255, 255, 255, 200),
                    h_align=0.0, v_align=0.5,
                    text_fn=STATIC(0)
                )
            ],
        ),
    ]
    
)

WINDOW_DEFS = []
WINDOW_DEFS.append(logger_window)

register_windows(WINDOW_LAYER, WINDOW_DEFS)