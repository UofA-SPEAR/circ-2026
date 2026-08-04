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

WINDOW_LAYER = 0

# ──────────────────────── BACKGROUND ────────────────────────
background_polygons = [
    RectDef(p1=P(0, 0), p2=P(1, 1), fill_color=QColor(0, 0, 0, 255))
]

register_gradient(GradientDef(
    name='startup_grid', p1=P(0.5, 0.5), p2=P(1, 1), radial=True, target='outline', stops=[
        GradientStop(0.0, QColor(255, 255, 255, 50)),
        GradientStop(1.0, QColor(255, 255, 255, 0)),
    ],
))

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

background_window = WindowDef(p1=P(0.0, 0.0), p2=P(1.0, 1.0), polygon_defs = background_polygons)





# ──────────────────────── SUBSCRIPTION VALUES ────────────────────────

register_event(EventDef(name='startup_subscription_phase', value='waiting'))
register_event(EventDef(name='startup_phase', value='waiting'))
register_event(EventDef(name='startup_phase_flip', value='open'))

subscription_list = ['test_value1', 'test_value2', 'test_value3', 'test_value4', 'test_value5', 'test_value6', 'test_value7', 'test_value8', 'test_value9', 'test_value10']
subscription_columns = 2
subscription_listeners = []
subscription_polygons = []
subscription_texts = []
for i in range(len(subscription_list)):
    x = i % subscription_columns
    y = math.floor(i / subscription_columns)
    target_x = (x / (subscription_columns - 1)) / 15 + 0.85
    target_y = y / 20 + 0.1
    name = f'sub_sample_pulse{i}'
    name_solid = f'sub_sample_pulse{i}_solid'
    delay = 0.05 * i
    delay_close = 0.01 * i
    register_event(EventDef(name=name, value=0))
    register_gradient(GradientDef(
        name=name, p1=P(target_x, target_y), p2=P(target_x, target_y), px1=P(0, 0), px2=P(-60, 0), target='fill', phase_event=get_event('startup_subscription_phase'),
        stops=[GradientStop(0.0, QColor(100, 0, 0, 255)), GradientStop(1.0, QColor(255, 0, 0, 0))], 
        phases={'pulse': Phase([
            GradientTween(stops=[GradientStop(0.0, QColor(0, 100, 0, 255)), GradientStop(1.0, QColor(0, 255, 0, 0))], start=0, dur=0, ease=QEasingCurve.OutQuint),
            GradientTween(stops=[GradientStop(0.0, QColor(0, 0, 0, 0)), GradientStop(1.0, QColor(0, 0, 0, 0))], start=0, dur=1, ease=QEasingCurve.OutQuint),
            ], pulse_event=get_event(name))
        }
    ))
    register_gradient(GradientDef(
        name=name_solid, p1=P(0, 0), p2=P(1, 1), px1=P(0, 0), px2=P(0, 0), target='fill', phase_event=get_event('startup_subscription_phase'),
        stops=[GradientStop(0.0, QColor(255, 0, 0, 255)), GradientStop(1.0, QColor(255, 0, 0, 255))], 
        phases={'pulse': Phase([
            GradientTween(stops=[GradientStop(0.0, QColor(0, 255, 0, 255)), GradientStop(1.0, QColor(0, 255, 0, 255))], start=0, dur=0, ease=QEasingCurve.OutQuint),
            GradientTween(stops=[GradientStop(0.0, QColor(0, 100, 0, 255)), GradientStop(1.0, QColor(0, 100, 0, 255))], start=0, dur=1, ease=QEasingCurve.OutQuint),
            ], pulse_event=get_event(name))
        }
    ))
    subscription_listeners += [
        EventListener(value_fn='pulse', targets=[get_event(name)], passthrough=True, wait_for_updates=lambda ctx, s=subscription_list[i]: ctx[s]['push_count']),
    ]
    subscription_polygons += [
        PolygonDef(p=[P(target_x + 0.5, target_y)]*4, px=[P(0, -15), P(0, 15), P(-60, 15), P(-60, -15)], gradient=get_gradient(name), 
        # phase_override=get_event('startup_subscription_phase'), 
        phases={
            'open': Phase([PolygonTween(p=[P(target_x, target_y)]*4, start=delay, dur=2.0, ease=QEasingCurve.OutQuint)]),
            'close': Phase([PolygonTween(p=[P(target_x, target_y - 1)]*4, start=delay_close, dur=1.0, ease=QEasingCurve.InQuint)])
        }),
        PolygonDef(p=[P(target_x + 0.5, target_y)]*6, px=[P(-3, 12), P(-3, -12), P(0, -15), P(3, -12), P(3, 12), P(0, 15)], gradient=get_gradient(name_solid), 
        # phase_override=get_event('startup_subscription_phase'), 
        phases={
            'open': Phase([PolygonTween(p=[P(target_x, target_y)]*6, start=delay, dur=2.0, ease=QEasingCurve.OutQuint)]),
            'close': Phase([PolygonTween(p=[P(target_x, target_y - 1)]*6, start=delay_close, dur=1.0, ease=QEasingCurve.InQuint)])
        }),
    ]
    subscription_texts += [
        TextDef(p=P(target_x + 0.5, target_y), px=P(7, 0), h_align=0, text=subscription_list[i], phases={
            'open': Phase([TextTween(p=P(target_x, target_y), start=delay, dur=2.0, ease=QEasingCurve.OutQuint)]),
            'close': Phase([TextTween(p=P(target_x, target_y - 1), start=delay_close, dur=1.0, ease=QEasingCurve.InQuint)])
        }),
        TextDef(p=P(target_x + 0.5, target_y), px=P(-7, 0), h_align=1, text_fn=lambda ctx, s=subscription_list[i]: ctx[s]['push_count'], phases={
            'open': Phase([TextTween(p=P(target_x, target_y), start=delay, dur=2.0, ease=QEasingCurve.OutQuint)]),
            'close': Phase([TextTween(p=P(target_x, target_y - 1), start=delay_close, dur=1.0, ease=QEasingCurve.InQuint)])
        }),
    ]
subscription_window = WindowDef(p1=P(0.0, 0.0), p2=P(1.0, 1.0), force_open=True, phase_event=get_event('startup_subscription_phase'), listener_defs = subscription_listeners, polygon_defs = subscription_polygons, text_defs = subscription_texts)

def count_data_received(ctx):
    if not ctx:
        return 0
    num = 0
    for s in subscription_list:
        data = ctx.get(s)
        if data and data.get('push_count', 0) > 0:
            num += 1
    return num

# ──────────────────────── SUBSCRIPTION VALUES ────────────────────────

register_gradient(GradientDef(
    name='launch_text_outline1', p1=P(0.5, 0.5), p2=P(0.5, 0.5), px1=P(-300, -150), px2=P(300, 150), target='outline', phase_event=get_event('startup_phase_flip'), stops=[
        GradientStop(0.0, QColor(50, 50, 50, 255)),
        GradientStop(0.5, QColor(50, 50, 50, 255)),
        GradientStop(0.5001, QColor(50, 50, 50, 0)),
    ],
    phases={'close': Phase([GradientTween(stops=[
        GradientStop(0.0, QColor(50, 50, 50, 0)),
        GradientStop(0.5, QColor(50, 50, 50, 0)),
        GradientStop(0.5001, QColor(50, 50, 50, 0)),
        ], start=0, dur=1, ease=QEasingCurve.OutQuint)])
    }
))
register_gradient(GradientDef(
    name='launch_text_outline2', p1=P(0.5, 0.5), p2=P(0.5, 0.5), px1=P(-300, -150), px2=P(300, 150), target='outline', phase_event=get_event('startup_phase_flip'), stops=[
        GradientStop(0.0, QColor(50, 50, 50, 0)),
        GradientStop(0.5, QColor(50, 50, 50, 0)),
        GradientStop(0.5001, QColor(50, 50, 50, 255)),
    ],
    phases={'close': Phase([GradientTween(stops=[
        GradientStop(0.0, QColor(50, 50, 50, 0)),
        GradientStop(0.5, QColor(50, 50, 50, 0)),
        GradientStop(0.5001, QColor(50, 50, 50, 0)),
        ], start=0, dur=1, ease=QEasingCurve.OutQuint)])
    }
))

register_gradient(GradientDef(
    name='startup_border_top', p1=P(0, 0), p2=P(0, 0.1), target='fill', phase_event=get_event('startup_phase'), stops=[
        GradientStop(0.0, QColor(171, 151, 247, 0)),
        GradientStop(1.0, QColor(171, 151, 247, 0)),
    ],
    phases={'open': Phase([GradientTween(stops=[
        GradientStop(0.0, QColor(171, 151, 247, 40)),
        GradientStop(1.0, QColor(171, 151, 247, 0)),
        ], start=0, dur=1, ease=QEasingCurve.OutQuint)])
    }
))

register_gradient(GradientDef(
    name='startup_border_bottom', p1=P(0, 0.9), p2=P(0, 1), target='fill', phase_event=get_event('startup_phase'), stops=[
        GradientStop(0.0, QColor(171, 151, 247, 0)),
        GradientStop(1.0, QColor(171, 151, 247, 0)),
    ],
    phases={'open': Phase([GradientTween(stops=[
        GradientStop(0.0, QColor(171, 151, 247, 0)),
        GradientStop(1.0, QColor(171, 151, 247, 40)),
        ], start=0, dur=1, ease=QEasingCurve.OutQuint)])
    }
))

register_gradient(GradientDef(
    name='alt_color_fill', p1=P(0, 0), p2=P(1, 1), target='fill', phase_event=get_event('startup_phase'), global_position=True, stops=[
        GradientStop(0.0, QColor(171, 151, 247, 255)),
        GradientStop(1.0, QColor(242, 179, 249, 255)),
    ],
))

register_gradient(GradientDef(
    name='alt_color_fill_translucent', p1=P(0, 0), p2=P(1, 1), target='fill', phase_event=get_event('startup_phase'), global_position=True, stops=[
        GradientStop(0.0, QColor(171, 151, 247, 0)),
        GradientStop(1.0, QColor(242, 179, 249, 0)),
    ],
    phases={'open': Phase([GradientTween(stops=[
        GradientStop(0.0, QColor(171, 151, 247, 50)),
        GradientStop(1.0, QColor(242, 179, 249, 50)),
        ], start=1, dur=1, ease=QEasingCurve.OutQuint)])
    }
))


register_gradient(GradientDef(
    name='alt_color_outline', p1=P(0, 0), p2=P(1, 1), target='outline', phase_event=get_event('startup_phase'), global_position=True, stops=[
        GradientStop(0.0, QColor(171, 151, 247, 255)),
        GradientStop(1.0, QColor(242, 179, 249, 255)),
    ],
))

alt_color = QColor(171, 151, 247, 255)

startup_window_always_poly = []
for i in range(-1, 10):
    x1 = i / 20
    x2 = (21 - i) / 20
    startup_window_always_poly.append(
        PolygonDef(p=[P(x1, 0)]*4, px=[P(-20, 13), P(15, 13), P(20, 18), P(-15, 18)], gradient=get_gradient('alt_color_fill_translucent'), phase_override=get_event('startup_phase'), phases={
            'always': Phase([PolygonTween(p=[P(0.05, 0)]*4, start=0, dur=3, ease=QEasingCurve.Linear)], loop=True, stop_phases=['close'])
        }),
    )
    startup_window_always_poly.append(
        PolygonDef(p=[P(x2, 1)]*4, px=[P(-20, -18), P(15, -18), P(20, -13), P(-15, -13)], gradient=get_gradient('alt_color_fill_translucent'), phase_override=get_event('startup_phase'), phases={
            'always': Phase([PolygonTween(p=[P(-0.05, 0)]*4, start=0, dur=3, ease=QEasingCurve.Linear)], loop=True, stop_phases=['close'])
        }),
    )
for i in range(11, 22):
    x1 = i / 20
    x2 = (21 - i) / 20
    startup_window_always_poly.append(
        PolygonDef(p=[P(x1, 0)]*4, px=[P(-15, 13), P(20, 13), P(15, 18), P(-20, 18)], gradient=get_gradient('alt_color_fill_translucent'), phase_override=get_event('startup_phase'), phases={
            'always': Phase([PolygonTween(p=[P(0.05, 0)]*4, start=0, dur=3, ease=QEasingCurve.Linear)], loop=True, stop_phases=['close'])
        }),
    )
    startup_window_always_poly.append(
        PolygonDef(p=[P(x2, 1)]*4, px=[P(-15, -18), P(20, -18), P(15, -13), P(-20, -13)], gradient=get_gradient('alt_color_fill_translucent'), phase_override=get_event('startup_phase'), phases={
            'always': Phase([PolygonTween(p=[P(-0.05, 0)]*4, start=0, dur=3, ease=QEasingCurve.Linear)], loop=True, stop_phases=['close'])
        }),
    )

startup_window = WindowDef(
    p1=P(0.0, 0.0), p2=P(1.0, 1.0),
    polygon_defs=startup_window_always_poly + [
        # ─ Top/Bottom ─
        # Gradient
        RectDef(p1=P(0, 0), p2=P(1, 0.1), phase_override=get_event('startup_phase'), gradient=get_gradient('startup_border_top')),
        RectDef(p1=P(0, 0.9), p2=P(1, 1), phase_override=get_event('startup_phase'), gradient=get_gradient('startup_border_bottom')),

        # Progress Bar
        RectDef(p1=P(0.5, 0.75), p2=P(0.5, 0.75), px1=P(-200, -5), px2=P(200, 5), phase_override=get_event('startup_phase'), phases={
            'open': Phase([RectTween(p1=P(1, 0.50), p2=P(1.0, 0.50), px1=P(-500, -5), px2=P(-100, 5), start=0.0, dur=1.0, ease=QEasingCurve.OutQuint, blend=True)]),
            'close': Phase([RectTween(p1=P(1, 0.50), p2=P(1, 0.50), px1=P(-100, -5), px2=P(-100, 5), start=0, dur=1.0, ease=QEasingCurve.OutQuint)]),
        }),
        PolygonDef(p=[P(1, 0.5)]*4, px=[P(-500, 10), P(-500, 10), P(-500, 30), P(-500, 30)], fill_color=QColor(0, 0, 0, 255), outline_color=QColor(255, 255, 255, 255), outline_width=0, phase_override=get_event('startup_phase'), phases={
            'open': Phase([PolygonTween(start=0, dur=1.0, ease=QEasingCurve.Linear),
                           PolygonTween(outline_width=1.0, start=1.0, dur=0, ease=QEasingCurve.Linear),
                           PolygonTween(px=[P(-499, 10), P(-300, 10), P(-320, 30), P(-499, 30)], start=1.0, dur=1.0, ease=QEasingCurve.OutQuint)], ),
            'close': Phase([PolygonTween(outline_color=QColor(255, 255, 255, 0), px=[P(-300, 10), P(-300, 10), P(-320, 30), P(-320, 30)], start=0, dur=1.0, ease=QEasingCurve.OutQuint)])
        }),
    ],
    text_defs=[
        TextDef(
            p=P(0.5, 0.5), px=P(0, 0), text='SPEAR', bold=True, italic=True, font_size=400, fill_color=QColor(255,255,255,0), outline_width=4,
            gradient=get_gradient('launch_text_outline1'), phase_override=get_event('startup_phase_flip'), phases={
                'close': Phase([TextTween(px=P(-50, 100), start=0, dur=1.0, ease=QEasingCurve.OutQuint)])
            }
        ),
        TextDef(
            p=P(0.5, 0.5), px=P(0, 0), text='SPEAR', bold=True, italic=True, font_size=400, fill_color=QColor(255,255,255,0), outline_width=4,
            gradient=get_gradient('launch_text_outline2'), phase_override=get_event('startup_phase_flip'), phases={
                'close': Phase([TextTween(px=P(50, -100), start=0, dur=1.0, ease=QEasingCurve.OutQuint)])
            }
        ),
        TextDef(
            p=P(0.5, 0.75), px=P(0, -7), text='DATA RECEIVED', font_size=20, h_align=0.5, v_align=1.0, fill_color=QColor(255,255,255,255),
            phase_override=get_event('startup_phase'), phases={
                'open': Phase([TextTween(p=P(1, 0.5), px=P(-500, -5), char_display=1, h_align=0.0, start=0, dur=1.0, ease=QEasingCurve.OutQuint)]),
                'close': Phase([TextTween(char_display=0, start=0.0, dur=1.0, ease=QEasingCurve.OutQuint)]),
            }
        ),
        TextDef(
            p=P(0.5, 0.75), px=P(0, 7), text='<#>%', font_size=20, h_align=0.5, v_align=0.0, fill_color=QColor(255,255,255,255),
            text_fn=lambda ctx: round(count_data_received(ctx) / len(subscription_list) * 100),
            phase_override=get_event('startup_phase'), phases={
                'open': Phase([TextTween(p=P(1, 0.5), px=P(-100, -5), char_display=1, h_align=1.0, v_align=1.0, start=0, dur=1.0, ease=QEasingCurve.OutQuint)]),
                'close': Phase([TextTween(char_display=0, start=0.0, dur=1.0, ease=QEasingCurve.OutQuint)]),
            }
        ),
        TextDef(
            p=P(1, 0.5), px=P(-100, 12), text='<#>/<#>', font_size=20, h_align=1.0, v_align=0.0, char_display=0, sub_char_clip=True, backward=True, fill_color=QColor(255,255,255,255),
            text_fn=lambda ctx: [count_data_received(ctx), len(subscription_list)],
            phase_override=get_event('startup_phase'), phases={
                'open': Phase([TextTween(char_display=1, start=0.9, dur=1.0, ease=QEasingCurve.OutQuint)]),
                'close': Phase([TextTween(char_display=0, start=0.0, dur=1.0, ease=QEasingCurve.OutQuint)]),
            }
        ),
        TextDef(
            p=P(0, 0), px=P(50, 15), text='PREVIEW', bold=True, italic=True, font_size=110, h_align=0.0, v_align=0.0, char_display=0, sub_char_clip=True, fill_color=QColor(255, 255, 255, 50), outline_color=QColor(20, 20, 20, 255), outline_width=1,
            phase_override=get_event('startup_phase'), phases={
                'open': Phase([TextTween(char_display=1, start=0, dur=1.0, ease=QEasingCurve.OutQuint)]),
                'close': Phase([TextTween(char_display=0, start=0, dur=1.0, ease=QEasingCurve.OutQuint)]),
            }
        ),
        # TextDef(
        #     p=P(0, 0), px=P(50, 125), text='PREVIEW', bold=True, italic=True, font_size=110, h_align=0.0, v_align=0.0, char_display=0, sub_char_clip=True, fill_color=QColor(255, 255, 255, 50), outline_color=QColor(20, 20, 20, 255), outline_width=1,
        #     phase_override=get_event('startup_phase'), phases={
        #         'open': Phase([TextTween(char_display=1, start=0, dur=1.0, ease=QEasingCurve.OutQuint)])
        #     }
        # ),
        TextDef(
            p=P(1, 0), px=P(-70, 15), text='SUBSCRIPTIONS', bold=True, font_size=70, h_align=1.0, v_align=0.0, char_display=0, sub_char_clip=True, backward=True, fill_color=QColor(255,255,255,0), gradient=get_gradient('alt_color_outline'), outline_width=2,
            phase_override=get_event('startup_phase'), phases={
                'open': Phase([TextTween(char_display=1, start=0, dur=1.0, ease=QEasingCurve.OutQuint)]),
                'close': Phase([TextTween(char_display=0, start=0.0, dur=1.0, ease=QEasingCurve.OutQuint)]),
            }
        ),
        TextDef(
            p=P(1, 0.5), px=P(-495, 30), text='FORCE PROCEED ➡', font_size=13, h_align=0.0, v_align=1.0, char_display=0, sub_char_clip=True, fill_color=QColor(100,100,100,255),
            phase_override=get_event('startup_phase'), phases={
                'open': Phase([TextTween(char_display=1, start=1.0, dur=1.0, ease=QEasingCurve.OutQuint)]),
                'close': Phase([TextTween(char_display=0, start=0.0, dur=1.0, ease=QEasingCurve.OutQuint)]),
            }
        ),
        TextDef(
            p=P(1, 0.5), px=P(-300, 11), text='SHIFT + SPACE', italic=True, font_size=8, h_align=0.0, v_align=0, char_display=0, sub_char_clip=True, fill_color=QColor(100,100,100,255),
            phase_override=get_event('startup_phase'), phases={
                'open': Phase([TextTween(char_display=1, start=1.0, dur=1.0, ease=QEasingCurve.OutQuint)]),
                'close': Phase([TextTween(char_display=0, start=0.0, dur=1.0, ease=QEasingCurve.OutQuint)]),
            }
        ),
    ],
    button_defs=[
        ButtonDef(key=Qt.Key_Space, mandatory_keys=(Qt.Key_Shift, False), 
                  event_out=[get_event('main_page'), get_event('startup_phase_flip'), get_event('startup_phase'), get_event('startup_subscription_phase')], 
                  event_delta=['close', 'close', 'open', 'open']),
        ButtonDef(key=Qt.Key_Space, mandatory_keys=Qt.Key_Shift, 
                  event_out=[get_event('main_page'), get_event('startup_phase_flip'), get_event('startup_phase'), get_event('startup_subscription_phase')], 
                  event_delta=['open', 'open', 'close', 'close']),

        # ButtonDef(poly_def=PolygonDef(p=[P(1, 0.5)]*4, px=[P(-500, 5), P(-300, 5), P(-320, 25), P(-500, 25)], fill_color=QColor(255, 255, 255, 255), phases={
        #     'open': Phase([PolygonTween(px=[P(-500, 5), P(-300, 5), P(-320, 25), P(-500, 25)], start=0, dur=1.0, ease=QEasingCurve.OutQuint)])
        # }),
        # key=Qt.Key_Space, event_out=get_event('startup_subscription_phase'), event_delta='open'),
    ],
    # p=P(1, 0.5), px=P(-500, -5),
    # pie_defs=[
    #     PieDef(
    #         p1=P(0.4, 0.6), p2=P(0.6, 0.7),
    #         names=[''] * 9,
    #         value_fns=[lambda ctx, i=i: ctx[f'test_value{i+1}']['latest'] for i in range(9)],
    #         colors=[QColor(255,106,106), QColor(255,111,151), QColor(255,126,192),
    #                 QColor(238,145,227), QColor(214,165,252), QColor(187,184,255),
    #                 QColor(164,200,255), QColor(150,213,255), QColor(149,224,255)],
    #         border_width=1.0, fill_opacity=0.1, direction='horizontal',
    #         size_label=0.0, size_name=9.0, ease_dur=0.4, ease_type=QEasingCurve.OutQuint,
    #     ),
    # ]
)

WINDOW_DEFS = []
WINDOW_DEFS.append(background_window)
WINDOW_DEFS.append(subscription_window)
WINDOW_DEFS.append(startup_window)

register_windows(WINDOW_LAYER, WINDOW_DEFS)


OVERLAY_WINDOWS = [
    WindowDef(
        p1=P(0.0, 0.0), p2=P(1.0, 1.0),
        polygon_defs=[
            # Fill
            RectDef(p1=P(0, 0), p2=P(1, 0), gradient=get_gradient('alt_color_fill'), phase_override=get_event('startup_phase'), phases={
                'open': Phase([RectTween(px2=P(0, 10), start=0, dur=1.0, ease=QEasingCurve.OutQuint)])
            }),
            RectDef(p1=P(0, 1), p2=P(1, 1), gradient=get_gradient('alt_color_fill'), phase_override=get_event('startup_phase'), phases={
                'open': Phase([RectTween(px1=P(0, -10), start=0, dur=1.0, ease=QEasingCurve.OutQuint)])
            }),
            # Center
            PolygonDef(p=[P(0.5, 0)]*4, px=[P(0, 0), P(0, 0), P(0, 20), P(0, 20)], gradient=get_gradient('alt_color_fill'), phase_override=get_event('startup_phase'), phases={
                'open': Phase([PolygonTween(px=[P(-165, 0), P(165, 0), P(145, 20), P(-145, 20)], start=0.5, dur=1.25, ease=QEasingCurve.OutExpo)])
            }),
            PolygonDef(p=[P(0.5, 1)]*4, px=[P(0, 0), P(0, 0), P(0, -20), P(0, -20)], gradient=get_gradient('alt_color_fill'), phase_override=get_event('startup_phase'), phases={
                'open': Phase([PolygonTween(px=[P(-165, 0), P(165, 0), P(145, -20), P(-145, -20)], start=0.5, dur=1.25, ease=QEasingCurve.OutExpo)])
            }),

            # ─ Left/Right ─
            # Fill
            PolygonDef(p=[P(0, 0)]*4, px=[P(0, 0), P(10, 0), P(10, 0), P(0, 0)], gradient=get_gradient('alt_color_fill'), phase_override=get_event('startup_phase'), phases={
                'open': Phase([PolygonTween(px=[P(0, 0), P(10, 0), P(10, 50), P(0, 60)], start=0, dur=1.0, ease=QEasingCurve.OutQuint)])
            }),
            PolygonDef(p=[P(1, 0)]*4, px=[P(0, 0), P(-10, 0), P(-10, 0), P(0, 0)], gradient=get_gradient('alt_color_fill'), phase_override=get_event('startup_phase'), phases={
                'open': Phase([PolygonTween(px=[P(0, 0), P(-10, 0), P(-10, 50), P(0, 60)], start=0, dur=1.0, ease=QEasingCurve.OutQuint)])
            }),
            PolygonDef(p=[P(0, 1)]*4, px=[P(0, 0), P(10, 0), P(10, 0), P(0, 0)], gradient=get_gradient('alt_color_fill'), phase_override=get_event('startup_phase'), phases={
                'open': Phase([PolygonTween(px=[P(0, 0), P(10, 0), P(10, -50), P(0, -60)], start=0, dur=1.0, ease=QEasingCurve.OutQuint)])
            }),
            PolygonDef(p=[P(1, 1)]*4, px=[P(0, 0), P(-10, 0), P(-10, 0), P(0, 0)], gradient=get_gradient('alt_color_fill'), phase_override=get_event('startup_phase'), phases={
                'open': Phase([PolygonTween(px=[P(0, 0), P(-10, 0), P(-10, -50), P(0, -60)], start=0, dur=1.0, ease=QEasingCurve.OutQuint)])
            }),
            # Line
            PolygonDef(p=[P(0, 0), P(0, 0.4), P(0, 0.4), P(0, 1)], px=[P(30, 30), P(30, -15), P(60, 15), P(60, -30)], fill_color=QColor(255, 255, 255, 0), outline_color=QColor(255, 255, 255, 255), outline_width=2, draw_progress=0, closed=False, phase_override=get_event('startup_phase'), phases={
                'open': Phase([PolygonTween(draw_progress=1, start=0, dur=2.5, ease=QEasingCurve.OutExpo)])
            }),
            PolygonDef(p=[P(1, 1), P(1, 0.6), P(1, 0.6), P(1, 0)], px=[P(-30, -30), P(-30, 15), P(-60, -15), P(-60, 30)], fill_color=QColor(255, 255, 255, 0), outline_color=QColor(255, 255, 255, 255), outline_width=2, draw_progress=0, closed=False, phase_override=get_event('startup_phase'), phases={
                'open': Phase([PolygonTween(draw_progress=1, start=0, dur=2.5, ease=QEasingCurve.OutExpo)])
            }),

            # Line Rects
            # Top Left
            RectDef(p1=P(0, 0), p2=P(0, 0), px1=P(27, 50), px2=P(33, 50), fill_color=QColor(255, 255, 255, 255), phase_override=get_event('startup_phase'), phases={
                'open': Phase([RectTween(px1=P(27, 50 - 10), px2=P(33, 50 + 10), start=0.5, dur=1.0, ease=QEasingCurve.OutQuint)]),
                'always': Phase([RectTween(px1=P(0, 30), px2=P(0, 30), start=0.0, dur=10.0, ease=QEasingCurve.InOutSine),
                                RectTween(px1=P(0, 0), px2=P(0, 0), start=10.0, dur=10.0, ease=QEasingCurve.InOutSine)], loop=True, stop_phases=['close']),
            }),
            RectDef(p1=P(0, 0), p2=P(0, 0), px1=P(27, 50 + 70), px2=P(33, 50 + 70), fill_color=QColor(255, 255, 255, 255), phase_override=get_event('startup_phase'), phases={
                'open': Phase([RectTween(px1=P(27, 50 + 30), px2=P(33, 50 + 110), start=0.5, dur=1.0, ease=QEasingCurve.OutQuint)]),
                'always': Phase([RectTween(px1=P(0, 25), px2=P(0, 25), start=0.0, dur=10.0, ease=QEasingCurve.InOutSine),
                                RectTween(px1=P(0, 0), px2=P(0, 0), start=10.0, dur=10.0, ease=QEasingCurve.InOutSine)], loop=True, stop_phases=['close']),
            }),
            RectDef(p1=P(0, 0), p2=P(0, 0), px1=P(27, 50 + 140), px2=P(33, 50 + 140), fill_color=QColor(255, 255, 255, 255), phase_override=get_event('startup_phase'), phases={
                'open': Phase([RectTween(px1=P(27, 50 + 130), px2=P(33, 50 + 150), start=0.5, dur=1.0, ease=QEasingCurve.OutQuint)]),
                'always': Phase([RectTween(px1=P(0, 20), px2=P(0, 20), start=0.0, dur=10.0, ease=QEasingCurve.InOutSine),
                                RectTween(px1=P(0, 0), px2=P(0, 0), start=10.0, dur=10.0, ease=QEasingCurve.InOutSine)], loop=True, stop_phases=['close']),
            }),
            # Bottom Left
            RectDef(p1=P(0, 1), p2=P(0, 1), px1=P(57, -50), px2=P(63, -50), fill_color=QColor(255, 255, 255, 255), phase_override=get_event('startup_phase'), phases={
                'open': Phase([RectTween(px1=P(57, -50 - 10), px2=P(63, -50 + 10), start=0.5, dur=1.0, ease=QEasingCurve.OutQuint)]),
                'always': Phase([RectTween(px1=P(0, -20), px2=P(0, -20), start=0.0, dur=10.0, ease=QEasingCurve.InOutSine),
                                RectTween(px1=P(0, 0), px2=P(0, 0), start=10.0, dur=10.0, ease=QEasingCurve.InOutSine)], loop=True, stop_phases=['close']),
            }),
            RectDef(p1=P(0, 1), p2=P(0, 1), px1=P(57, -50 - 70), px2=P(63, -50 - 70), fill_color=QColor(255, 255, 255, 255), phase_override=get_event('startup_phase'), phases={
                'open': Phase([RectTween(px1=P(57, -50 - 30), px2=P(63, -50 - 110), start=0.5, dur=1.0, ease=QEasingCurve.OutQuint)]),
                'always': Phase([RectTween(px1=P(0, -25), px2=P(0, -25), start=0.0, dur=10.0, ease=QEasingCurve.InOutSine),
                                RectTween(px1=P(0, 0), px2=P(0, 0), start=10.0, dur=10.0, ease=QEasingCurve.InOutSine)], loop=True, stop_phases=['close']),
            }),
            RectDef(p1=P(0, 1), p2=P(0, 1), px1=P(57, -50 - 140), px2=P(63, -50 - 140), fill_color=QColor(255, 255, 255, 255), phase_override=get_event('startup_phase'), phases={
                'open': Phase([RectTween(px1=P(57, -50 - 130), px2=P(63, -50 - 150), start=0.5, dur=1.0, ease=QEasingCurve.OutQuint)]),
                'always': Phase([RectTween(px1=P(0, -30), px2=P(0, -30), start=0.0, dur=10.0, ease=QEasingCurve.InOutSine),
                                RectTween(px1=P(0, 0), px2=P(0, 0), start=10.0, dur=10.0, ease=QEasingCurve.InOutSine)], loop=True, stop_phases=['close']),
            }),
            # Top Right
            RectDef(p1=P(1, 0), p2=P(1, 0), px1=P(-63, 50), px2=P(-57, 50), fill_color=QColor(255, 255, 255, 255), phase_override=get_event('startup_phase'), phases={
                'open': Phase([RectTween(px1=P(-63, 50 - 10), px2=P(-57, 50 + 10), start=0.5, dur=1.0, ease=QEasingCurve.OutQuint)]),
                'always': Phase([RectTween(px1=P(0, 30), px2=P(0, 30), start=0.0, dur=10.0, ease=QEasingCurve.InOutSine),
                                RectTween(px1=P(0, 0), px2=P(0, 0), start=10.0, dur=10.0, ease=QEasingCurve.InOutSine)], loop=True, stop_phases=['close']),
            }),
            RectDef(p1=P(1, 0), p2=P(1, 0), px1=P(-63, 50 + 70), px2=P(-57, 50 + 70), fill_color=QColor(255, 255, 255, 255), phase_override=get_event('startup_phase'), phases={
                'open': Phase([RectTween(px1=P(-63, 50 + 110), px2=P(-57, 50 + 30), start=0.5, dur=1.0, ease=QEasingCurve.OutQuint)]),
                'always': Phase([RectTween(px1=P(0, 25), px2=P(0, 25), start=0.0, dur=10.0, ease=QEasingCurve.InOutSine),
                                RectTween(px1=P(0, 0), px2=P(0, 0), start=10.0, dur=10.0, ease=QEasingCurve.InOutSine)], loop=True, stop_phases=['close']),
            }),
            RectDef(p1=P(1, 0), p2=P(1, 0), px1=P(-63, 50 + 140), px2=P(-57, 50 + 140), fill_color=QColor(255, 255, 255, 255), phase_override=get_event('startup_phase'), phases={
                'open': Phase([RectTween(px1=P(-63, 50 + 150), px2=P(-57, 50 + 130), start=0.5, dur=1.0, ease=QEasingCurve.OutQuint)]),
                'always': Phase([RectTween(px1=P(0, 20), px2=P(0, 20), start=0.0, dur=10.0, ease=QEasingCurve.InOutSine),
                                RectTween(px1=P(0, 0), px2=P(0, 0), start=10.0, dur=10.0, ease=QEasingCurve.InOutSine)], loop=True, stop_phases=['close']),
            }),
            # Bottom Right
            RectDef(p1=P(1, 1), p2=P(1, 1), px1=P(-33, -50), px2=P(-27, -50), fill_color=QColor(255, 255, 255, 255), phase_override=get_event('startup_phase'), phases={
                'open': Phase([RectTween(px1=P(-33, -50 - 10), px2=P(-27, -50 + 10), start=0.5, dur=1.0, ease=QEasingCurve.OutQuint)]),
                'always': Phase([RectTween(px1=P(0, -20), px2=P(0, -20), start=0.0, dur=10.0, ease=QEasingCurve.InOutSine),
                                RectTween(px1=P(0, 0), px2=P(0, 0), start=10.0, dur=10.0, ease=QEasingCurve.InOutSine)], loop=True, stop_phases=['close']),
            }),
            RectDef(p1=P(1, 1), p2=P(1, 1), px1=P(-33, -50 - 70), px2=P(-27, -50 - 70), fill_color=QColor(255, 255, 255, 255), phase_override=get_event('startup_phase'), phases={
                'open': Phase([RectTween(px1=P(-33, -50 - 110), px2=P(-27, -50 - 30), start=0.5, dur=1.0, ease=QEasingCurve.OutQuint)]),
                'always': Phase([RectTween(px1=P(0, -25), px2=P(0, -25), start=0.0, dur=10.0, ease=QEasingCurve.InOutSine),
                                RectTween(px1=P(0, 0), px2=P(0, 0), start=10.0, dur=10.0, ease=QEasingCurve.InOutSine)], loop=True, stop_phases=['close']),
            }),
            RectDef(p1=P(1, 1), p2=P(1, 1), px1=P(-33, -50 - 140), px2=P(-27, -50 - 140), fill_color=QColor(255, 255, 255, 255), phase_override=get_event('startup_phase'), phases={
                'open': Phase([RectTween(px1=P(-33, -50 - 150), px2=P(-27, -50 - 130), start=0.5, dur=1.0, ease=QEasingCurve.OutQuint)]),
                'always': Phase([RectTween(px1=P(0, -30), px2=P(0, -30), start=0.0, dur=10.0, ease=QEasingCurve.InOutSine),
                                RectTween(px1=P(0, 0), px2=P(0, 0), start=10.0, dur=10.0, ease=QEasingCurve.InOutSine)], loop=True, stop_phases=['close']),
            }),

            # Hovering Objects
            PolygonDef(p=[P(0, 0.4)]*4, px=[P(45, 6), P(55, 16), P(55, 16), P(45, 6)], fill_color=QColor(255, 255, 255, 255), phase_override=get_event('startup_phase'), phases={
                'open': Phase([PolygonTween(px=[P(45, 6), P(55, 16), P(55, 45), P(45, 55)], start=0, dur=1.0, ease=QEasingCurve.OutQuint)])
            }),
            PolygonDef(p=[P(1, 0.6)]*4, px=[P(-45, -6), P(-55, -16), P(-55, -16), P(-45, -6)], fill_color=QColor(255, 255, 255, 255), phase_override=get_event('startup_phase'), phases={
                'open': Phase([PolygonTween(px=[P(-45, -6), P(-55, -16), P(-55, -45), P(-45, -55)], start=0, dur=1.0, ease=QEasingCurve.OutQuint)])
            }),

            PolygonDef(p=[P(0, 0.4)]*4, px=[P(50, 56), P(55, 51), P(55, 51), P(50, 56)], fill_color=QColor(255, 255, 255, 255), phase_override=get_event('startup_phase'), phases={
                'open': Phase([PolygonTween(px=[P(50, 56), P(55, 51), P(55, 101), P(50, 96)], start=0, dur=1.0, ease=QEasingCurve.OutQuint)])
            }),
            PolygonDef(p=[P(1, 0.6)]*4, px=[P(-50, -56), P(-55, -51), P(-55, -51), P(-50, -56)], fill_color=QColor(255, 255, 255, 255), phase_override=get_event('startup_phase'), phases={
                'open': Phase([PolygonTween(px=[P(-50, -56), P(-55, -51), P(-55, -101), P(-50, -96)], start=0, dur=1.0, ease=QEasingCurve.OutQuint)])
            }),

            # Colored Hover

            PolygonDef(p=[P(0, 5)]*4, px=[P(5, -71), P(15, -61), P(15, -60), P(5, -70)], gradient=get_gradient('alt_color_fill_translucent'), phase_override=get_event('startup_phase'), phases={
                'open': Phase([PolygonTween(p=[P(0, 1)]*4, start=0, dur=0.0, ease=QEasingCurve.OutQuint)]),
                'always': Phase([PolygonTween(px=[P(0, -200), P(0, -200), P(0, 0), P(0, 0)], start=0.0, dur=20.0, ease=QEasingCurve.InOutSine),
                                PolygonTween(px=[P(0, 0), P(0, 0), P(0, 0), P(0, 0)], start=20.0, dur=20.0, ease=QEasingCurve.InOutSine)], loop=True, stop_phases=['close']),
            }),
            PolygonDef(p=[P(0, 1)]*4, px=[P(5, -70), P(15, -60), P(15, -60), P(5, -70)], gradient=get_gradient('alt_color_fill'), phase_override=get_event('startup_phase'), phases={
                'open': Phase([PolygonTween(px=[P(5, -110), P(15, -100), P(15, -60), P(5, -70)], start=0, dur=1.0, ease=QEasingCurve.OutQuint)]),
                'always': Phase([PolygonTween(px=[P(0, -200), P(0, -200), P(0, -200), P(0, -200)], start=0.0, dur=20.0, ease=QEasingCurve.InOutSine),
                                PolygonTween(px=[P(0, 0), P(0, 0), P(0, 0), P(0, 0)], start=20.0, dur=20.0, ease=QEasingCurve.InOutSine)], loop=True, stop_phases=['close']),
            }),

            PolygonDef(p=[P(1, 5)]*4, px=[P(-5, 71), P(-15, 61), P(-15, 60), P(-5, 70)], gradient=get_gradient('alt_color_fill_translucent'), phase_override=get_event('startup_phase'), phases={
                'open': Phase([PolygonTween(p=[P(1, 0)]*4, start=0, dur=0.0, ease=QEasingCurve.OutQuint)]),
                'always': Phase([PolygonTween(px=[P(0, 200), P(0, 200), P(0, 0), P(0, 0)], start=0.0, dur=20.0, ease=QEasingCurve.InOutSine),
                                PolygonTween(px=[P(0, 0), P(0, 0), P(0, 0), P(0, 0)], start=20.0, dur=20.0, ease=QEasingCurve.InOutSine)], loop=True, stop_phases=['close']),
            }),
            PolygonDef(p=[P(1, 0)]*4, px=[P(-5, 70), P(-15, 60), P(-15, 60), P(-5, 70)], gradient=get_gradient('alt_color_fill'), phase_override=get_event('startup_phase'), phases={
                'open': Phase([PolygonTween(px=[P(-5, 110), P(-15, 100), P(-15, 60), P(-5, 70)], start=0, dur=1.0, ease=QEasingCurve.OutQuint)]),
                'always': Phase([PolygonTween(px=[P(0, 200), P(0, 200), P(0, 200), P(0, 200)], start=0.0, dur=20.0, ease=QEasingCurve.InOutSine),
                                PolygonTween(px=[P(0, 0), P(0, 0), P(0, 0), P(0, 0)], start=20.0, dur=20.0, ease=QEasingCurve.InOutSine)], loop=True, stop_phases=['close']),
            }),
        ],
        text_defs=[
            # Time
            TextDef(
                p=P(0.5, 0), px=P(0, 1), text='- <#> -', font_size=15, h_align=0.5, v_align=0.0, fill_color=QColor(0,0,0,0), text_fn=lambda ctx: datetime.now(ZoneInfo('America/Edmonton')).time().replace(microsecond=0),
                phase_override=get_event('startup_phase'), phases={
                    'open': Phase([TextTween(fill_color=QColor(0, 0, 0, 255), start=0.5, dur=1.0, ease=QEasingCurve.OutQuint)])
                }
            ),
            TextDef(
                p=P(0.5, 1), px=P(0, 0), text='SPEAR', font_size=15, h_align=0.5, v_align=1.0, fill_color=QColor(0,0,0,0),
                phase_override=get_event('startup_phase'), phases={
                    'open': Phase([TextTween(fill_color=QColor(0, 0, 0, 255), start=0.5, dur=1.0, ease=QEasingCurve.OutQuint)])
                }
            ),
        ]
    )
]

register_windows(9, OVERLAY_WINDOWS)
