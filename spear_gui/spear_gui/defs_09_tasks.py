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

WINDOW_LAYER = 1

register_event(EventDef(name='task_window', value='1. Snack Run'))
register_event(EventDef(name='task_window_pulse', value=''))
register_event(EventDef(name='task_window_text', value=''))

register_event(EventDef(name='hardware_fault_phase', value='close'))
register_event(EventDef(name='wire_window_phase', value='close'))

register_gradient(GradientDef(
    name='task_window_pulse', p1=P(0, 0), p2=P(0, 0), px1=P(415, 0), px2=P(700, 0), target='fill', stops=[
        GradientStop(0.0, QColor(171, 151, 247, 0)),
        GradientStop(1.0, QColor(171, 151, 247, 0)),
    ], phases={'pulse': Phase([
        GradientTween(stops=[GradientStop(0.0, QColor(171, 151, 247, 255)), GradientStop(1.0, QColor(171, 151, 247, 0))], start=0, dur=0, ease=QEasingCurve.Linear),
        GradientTween(stops=[GradientStop(0.0, QColor(171, 151, 247, 0)), GradientStop(1.0, QColor(171, 151, 247, 0))], start=0, dur=0.9, ease=QEasingCurve.OutQuint)
        ], pulse_event=get_event('task_window_pulse'))
    }
))




register_gradient(GradientDef(
    name='hardware_fault_gradient', p1=P(0.5, 0), p2=P(0.5, 0), px1=P(-300, 0), px2=P(300, 0), target='fill', phase_event = get_event('hardware_fault_phase'), stops=[
        GradientStop(0.0, QColor(171, 151, 247, 0)),
        GradientStop(0.5, QColor(171, 151, 247, 0)),
        GradientStop(1.0, QColor(171, 151, 247, 0)),
    ], phases={'open': Phase([GradientTween(stops=[GradientStop(0.0, QColor(171, 151, 247, 0)), GradientStop(0.5, QColor(171, 151, 247, 255)), GradientStop(1.0, QColor(171, 151, 247, 0))], start=0, dur=0.9, ease=QEasingCurve.OutQuint)]),
               'close': Phase([GradientTween(stops=[GradientStop(0.0, QColor(171, 151, 247, 0)), GradientStop(0.5, QColor(171, 151, 247, 0)), GradientStop(1.0, QColor(171, 151, 247, 0))], start=0, dur=0.9, ease=QEasingCurve.OutQuint)]),
    }
))


# HARDWARE FAULT
register_event(EventDef(name='hardware_fault_byte1-1', value='0b00000000'))
register_event(EventDef(name='hardware_fault_byte2-1', value='0b00000000'))
register_event(EventDef(name='hardware_fault_byte3-1', value='0b00000000'))
register_event(EventDef(name='hardware_fault_byte4-1', value='0b00000000'))
register_event(EventDef(name='hardware_fault_byte1-2', value='0b00000000'))
register_event(EventDef(name='hardware_fault_byte2-2', value='0b00000000'))
register_event(EventDef(name='hardware_fault_byte3-2', value='0b00000000'))
register_event(EventDef(name='hardware_fault_byte4-2', value='0b00000000'))

register_event(EventDef(name='hardware_fault_xor1', value='0b00000000'))
register_event(EventDef(name='hardware_fault_xor2', value='0b00000000'))
register_event(EventDef(name='hardware_fault_xor3', value='0b00000000'))
register_event(EventDef(name='hardware_fault_xor4', value='0b00000000'))

register_event(EventDef(name='hardware_fault_char1', value=''))
register_event(EventDef(name='hardware_fault_char2', value=''))
register_event(EventDef(name='hardware_fault_char3', value=''))
register_event(EventDef(name='hardware_fault_char4', value=''))

register_event(EventDef(name='hardware_fault_valid_char1', value='×'))
register_event(EventDef(name='hardware_fault_valid_char2', value='×'))
register_event(EventDef(name='hardware_fault_valid_char3', value='×'))
register_event(EventDef(name='hardware_fault_valid_char4', value='×'))

register_event(EventDef(name='hardware_fault_invalid_char1', value='×'))
register_event(EventDef(name='hardware_fault_invalid_char2', value='×'))
register_event(EventDef(name='hardware_fault_invalid_char3', value='×'))
register_event(EventDef(name='hardware_fault_invalid_char4', value='×'))

hardware_fault_window = WindowDef(
    p1=P(0.0, 0.0), p2=P(1.0, 1.0),
    phase_event = get_event('hardware_fault_phase'),
    listener_defs=[
        EventListener(value_fn=lambda ctx: (get_event('hardware_fault_byte1-1').value, get_event('hardware_fault_byte1-2').value), targets=[get_event('hardware_fault_xor1')], passthrough=True, transform=lambda v: f'0b{int(v[0], 2) ^ int(v[1], 2):08b}'),
        EventListener(value_fn=lambda ctx: (get_event('hardware_fault_byte2-1').value, get_event('hardware_fault_byte2-2').value), targets=[get_event('hardware_fault_xor2')], passthrough=True, transform=lambda v: f'0b{int(v[0], 2) ^ int(v[1], 2):08b}'),
        EventListener(value_fn=lambda ctx: (get_event('hardware_fault_byte3-1').value, get_event('hardware_fault_byte3-2').value), targets=[get_event('hardware_fault_xor3')], passthrough=True, transform=lambda v: f'0b{int(v[0], 2) ^ int(v[1], 2):08b}'),
        EventListener(value_fn=lambda ctx: (get_event('hardware_fault_byte4-1').value, get_event('hardware_fault_byte4-2').value), targets=[get_event('hardware_fault_xor4')], passthrough=True, transform=lambda v: f'0b{int(v[0], 2) ^ int(v[1], 2):08b}'),

        EventListener(value_fn=lambda ctx: get_event('hardware_fault_xor1').value, targets=[get_event('hardware_fault_char1')], passthrough=True, transform=lambda v: chr(int(v, 2)) if 32 <= int(v, 2) <= 126 else ''),
        EventListener(value_fn=lambda ctx: get_event('hardware_fault_xor2').value, targets=[get_event('hardware_fault_char2')], passthrough=True, transform=lambda v: chr(int(v, 2)) if 32 <= int(v, 2) <= 126 else ''),
        EventListener(value_fn=lambda ctx: get_event('hardware_fault_xor3').value, targets=[get_event('hardware_fault_char3')], passthrough=True, transform=lambda v: chr(int(v, 2)) if 32 <= int(v, 2) <= 126 else ''),
        EventListener(value_fn=lambda ctx: get_event('hardware_fault_xor4').value, targets=[get_event('hardware_fault_char4')], passthrough=True, transform=lambda v: chr(int(v, 2)) if 32 <= int(v, 2) <= 126 else ''),

        EventListener(value_fn=lambda ctx: get_event('hardware_fault_char1').value, targets=[get_event('hardware_fault_valid_char1')], passthrough=True, transform=lambda v: v if v.lower() in ('u', 'd', 'l', 'r') else ''),
        EventListener(value_fn=lambda ctx: get_event('hardware_fault_char2').value, targets=[get_event('hardware_fault_valid_char2')], passthrough=True, transform=lambda v: v if v.lower() in ('u', 'd', 'l', 'r') else ''),
        EventListener(value_fn=lambda ctx: get_event('hardware_fault_char3').value, targets=[get_event('hardware_fault_valid_char3')], passthrough=True, transform=lambda v: v if v.lower() in ('u', 'd', 'l', 'r') else ''),
        EventListener(value_fn=lambda ctx: get_event('hardware_fault_char4').value, targets=[get_event('hardware_fault_valid_char4')], passthrough=True, transform=lambda v: v if v.lower() in ('u', 'd', 'l', 'r') else ''),
        
        EventListener(value_fn=lambda ctx: get_event('hardware_fault_valid_char1').value, targets=[get_event('hardware_fault_invalid_char1')], conditions=[lambda v: v != ''], values=['', '×']),
        EventListener(value_fn=lambda ctx: get_event('hardware_fault_valid_char2').value, targets=[get_event('hardware_fault_invalid_char2')], conditions=[lambda v: v != ''], values=['', '×']),
        EventListener(value_fn=lambda ctx: get_event('hardware_fault_valid_char3').value, targets=[get_event('hardware_fault_invalid_char3')], conditions=[lambda v: v != ''], values=['', '×']),
        EventListener(value_fn=lambda ctx: get_event('hardware_fault_valid_char4').value, targets=[get_event('hardware_fault_invalid_char4')], conditions=[lambda v: v != ''], values=['', '×']),
    ],
    text_defs=[
        TextDef(p=P(0.50, 0.42), px=P(0, 30), text='XOR', font_size=16.0, fill_color=QColor(171, 151, 247, 0), h_align=0.5, v_align=0.5, phases={
            'open': Phase([Reset(), TextTween(px=P(0, 0), fill_color=QColor(171, 151, 247, 255), start=0, dur=1.2, ease=QEasingCurve.OutBack)]),
            'close': Phase([TextTween(px=P(0, 30), fill_color=QColor(171, 151, 247, 0), start=0, dur=1, ease=QEasingCurve.OutQuint)]),
        }),
        TextDef(p=P(0.50, 0.74), px=P(0, 30), text='KEY', font_size=16.0, fill_color=QColor(171, 151, 247, 0), h_align=0.5, v_align=0.5, phases={
            'open': Phase([Reset(), TextTween(px=P(0, 0), fill_color=QColor(171, 151, 247, 255), start=0.0, dur=1.5, ease=QEasingCurve.OutBack)]),
            'close': Phase([TextTween(px=P(0, 30), fill_color=QColor(171, 151, 247, 0), start=0, dur=1, ease=QEasingCurve.OutQuint)]),
        }),

        # NUMBER ORDER
        TextDef(p=P(0.50 - (0.39 + 0.24) / 2, 0.42), px=P(0, -30), text='1', font_size=24.0, fill_color=QColor(171, 151, 247, 0), h_align=0.5, v_align=0.5, phases={
            'open': Phase([Reset(), TextTween(px=P(0, 0), fill_color=QColor(171, 151, 247, 255), start=0, dur=0.7, ease=QEasingCurve.OutQuint)]),
            'close': Phase([TextTween(px=P(0, 30), fill_color=QColor(171, 151, 247, 0), start=0, dur=1, ease=QEasingCurve.OutQuint)]),
        }),
        TextDef(p=P(0.50 - (0.18 + 0.03) / 2, 0.42), px=P(0, -30), text='2', font_size=24.0, fill_color=QColor(171, 151, 247, 0), h_align=0.5, v_align=0.5, phases={
            'open': Phase([Reset(), TextTween(px=P(0, 0), fill_color=QColor(171, 151, 247, 255), start=0, dur=0.8, ease=QEasingCurve.OutQuint)]),
            'close': Phase([TextTween(px=P(0, 30), fill_color=QColor(171, 151, 247, 0), start=0, dur=0.9, ease=QEasingCurve.OutQuint)]),
        }),
        TextDef(p=P(0.50 + (0.03 + 0.18) / 2, 0.42), px=P(0, -30), text='3', font_size=24.0, fill_color=QColor(171, 151, 247, 0), h_align=0.5, v_align=0.5, phases={
            'open': Phase([Reset(), TextTween(px=P(0, 0), fill_color=QColor(171, 151, 247, 255), start=0, dur=0.9, ease=QEasingCurve.OutQuint)]),
            'close': Phase([TextTween(px=P(0, 30), fill_color=QColor(171, 151, 247, 0), start=0, dur=0.8, ease=QEasingCurve.OutQuint)]),
        }),
        TextDef(p=P(0.50 + (0.24 + 0.39) / 2, 0.42), px=P(0, -30), text='4', font_size=24.0, fill_color=QColor(171, 151, 247, 0), h_align=0.5, v_align=0.5, phases={
            'open': Phase([Reset(), TextTween(px=P(0, 0), fill_color=QColor(171, 151, 247, 255), start=0, dur=1, ease=QEasingCurve.OutQuint)]),
            'close': Phase([TextTween(px=P(0, 30), fill_color=QColor(171, 151, 247, 0), start=0, dur=0.7, ease=QEasingCurve.OutQuint)]),
        }),
        
        # TRUE CHAR VALUE
        TextDef(p=P(0.50 - (0.39 + 0.24) / 2, 0.73), px=P(0, -30), text='<#>', font_size=12.0, bold=True, fill_color=QColor(171, 151, 247, 255), h_align=0.5, v_align=0.5,
            text_fn=lambda ctx: get_event('hardware_fault_char1').value if get_event('hardware_fault_char1').value != get_event('hardware_fault_valid_char1').value else '', phases={
                'open': Phase([Reset(), TextTween(px=P(0, 0), fill_color=QColor(171, 151, 247, 255), start=0, dur=0.7, ease=QEasingCurve.OutQuint)]),
                'close': Phase([TextTween(px=P(0, 30), fill_color=QColor(171, 151, 247, 0), start=0, dur=1.0, ease=QEasingCurve.OutQuint)]),
            }
        ),
        TextDef(p=P(0.50 - (0.18 + 0.03) / 2, 0.73), px=P(0, -30), text='<#>', font_size=12.0, bold=True, fill_color=QColor(171, 151, 247, 255), h_align=0.5, v_align=0.5,
            text_fn=lambda ctx: get_event('hardware_fault_char2').value if get_event('hardware_fault_char2').value != get_event('hardware_fault_valid_char2').value else '', phases={
                'open': Phase([Reset(), TextTween(px=P(0, 0), fill_color=QColor(171, 151, 247, 255), start=0, dur=0.8, ease=QEasingCurve.OutQuint)]),
                'close': Phase([TextTween(px=P(0, 30), fill_color=QColor(171, 151, 247, 0), start=0, dur=0.9, ease=QEasingCurve.OutQuint)]),
            }
        ),
        TextDef(p=P(0.50 + (0.03 + 0.18) / 2, 0.73), px=P(0, -30), text='<#>', font_size=12.0, bold=True, fill_color=QColor(171, 151, 247, 255), h_align=0.5, v_align=0.5,
            text_fn=lambda ctx: get_event('hardware_fault_char3').value if get_event('hardware_fault_char3').value != get_event('hardware_fault_valid_char3').value else '', phases={
                'open': Phase([Reset(), TextTween(px=P(0, 0), fill_color=QColor(171, 151, 247, 255), start=0, dur=0.9, ease=QEasingCurve.OutQuint)]),
                'close': Phase([TextTween(px=P(0, 30), fill_color=QColor(171, 151, 247, 0), start=0, dur=0.8, ease=QEasingCurve.OutQuint)]),
            }
        ),
        TextDef(p=P(0.50 + (0.24 + 0.39) / 2, 0.73), px=P(0, -30), text='<#>', font_size=12.0, bold=True, fill_color=QColor(171, 151, 247, 255), h_align=0.5, v_align=0.5,
            text_fn=lambda ctx: get_event('hardware_fault_char4').value if get_event('hardware_fault_char4').value != get_event('hardware_fault_valid_char4').value else '', phases={
                'open': Phase([Reset(), TextTween(px=P(0, 0), fill_color=QColor(171, 151, 247, 255), start=0, dur=1.0, ease=QEasingCurve.OutQuint)]),
                'close': Phase([TextTween(px=P(0, 30), fill_color=QColor(171, 151, 247, 0), start=0, dur=0.7, ease=QEasingCurve.OutQuint)]),
            }
        ),

        # VALID CHAR VALUE
        TextDef(p=P(0.50 - (0.39 + 0.24) / 2, 0.702), px=P(0, -30), text='<#>', font_size=24.0, bold=True, fill_color=QColor(171, 151, 247, 255), h_align=0.5, v_align=0.5,
            text_fn=lambda ctx: get_event('hardware_fault_valid_char1').value, phases={
                'open': Phase([Reset(), TextTween(px=P(0, 0), fill_color=QColor(171, 151, 247, 255), start=0, dur=0.7, ease=QEasingCurve.OutQuint)]),
                'close': Phase([TextTween(px=P(0, 30), fill_color=QColor(171, 151, 247, 0), start=0, dur=1.0, ease=QEasingCurve.OutQuint)]),
            }
        ),
        TextDef(p=P(0.50 - (0.18 + 0.03) / 2, 0.702), px=P(0, -30), text='<#>', font_size=24.0, bold=True, fill_color=QColor(171, 151, 247, 255), h_align=0.5, v_align=0.5,
            text_fn=lambda ctx: get_event('hardware_fault_valid_char2').value, phases={
                'open': Phase([Reset(), TextTween(px=P(0, 0), fill_color=QColor(171, 151, 247, 255), start=0, dur=0.8, ease=QEasingCurve.OutQuint)]),
                'close': Phase([TextTween(px=P(0, 30), fill_color=QColor(171, 151, 247, 0), start=0, dur=0.9, ease=QEasingCurve.OutQuint)]),
            }
        ),
        TextDef(p=P(0.50 + (0.03 + 0.18) / 2, 0.702), px=P(0, -30), text='<#>', font_size=24.0, bold=True, fill_color=QColor(171, 151, 247, 255), h_align=0.5, v_align=0.5,
            text_fn=lambda ctx: get_event('hardware_fault_valid_char3').value, phases={
                'open': Phase([Reset(), TextTween(px=P(0, 0), fill_color=QColor(171, 151, 247, 255), start=0, dur=0.9, ease=QEasingCurve.OutQuint)]),
                'close': Phase([TextTween(px=P(0, 30), fill_color=QColor(171, 151, 247, 0), start=0, dur=0.8, ease=QEasingCurve.OutQuint)]),
            }
        ),
        TextDef(p=P(0.50 + (0.24 + 0.39) / 2, 0.702), px=P(0, -30), text='<#>', font_size=24.0, bold=True, fill_color=QColor(171, 151, 247, 255), h_align=0.5, v_align=0.5,
            text_fn=lambda ctx: get_event('hardware_fault_valid_char4').value, phases={
                'open': Phase([Reset(), TextTween(px=P(0, 0), fill_color=QColor(171, 151, 247, 255), start=0, dur=1.0, ease=QEasingCurve.OutQuint)]),
                'close': Phase([TextTween(px=P(0, 30), fill_color=QColor(171, 151, 247, 0), start=0, dur=0.7, ease=QEasingCurve.OutQuint)]),
            }
        ),

        # INVALID CHAR INDICATOR
        TextDef(p=P(0.50 - (0.39 + 0.24) / 2, 0.702), px=P(0, -30), text='<#>', font_size=48, fill_color=QColor(0, 0, 0, 0), outline_color=QColor(255, 0, 0, 0), outline_width=1, h_align=0.5, v_align=0.5,
            text_fn=lambda ctx: get_event('hardware_fault_invalid_char1').value, phases={
                'open': Phase([Reset(), TextTween(px=P(0, 0), outline_color=QColor(255, 0, 0, 255), start=0, dur=0.7, ease=QEasingCurve.OutQuint)]),
                'close': Phase([TextTween(px=P(0, 30), outline_color=QColor(255, 0, 0, 0), start=0, dur=1.0, ease=QEasingCurve.OutQuint)]),
            }
        ),
        TextDef(p=P(0.50 - (0.18 + 0.03) / 2, 0.702), px=P(0, -30), text='<#>', font_size=48, fill_color=QColor(0, 0, 0, 0), outline_color=QColor(255, 0, 0, 0), outline_width=1, h_align=0.5, v_align=0.5,
            text_fn=lambda ctx: get_event('hardware_fault_invalid_char2').value, phases={
                'open': Phase([Reset(), TextTween(px=P(0, 0), outline_color=QColor(255, 0, 0, 255), start=0, dur=0.8, ease=QEasingCurve.OutQuint)]),
                'close': Phase([TextTween(px=P(0, 30), outline_color=QColor(255, 0, 0, 0), start=0, dur=0.9, ease=QEasingCurve.OutQuint)]),
            }
        ),
        TextDef(p=P(0.50 + (0.03 + 0.18) / 2, 0.702), px=P(0, -30), text='<#>', font_size=48, fill_color=QColor(0, 0, 0, 0), outline_color=QColor(255, 0, 0, 0), outline_width=1, h_align=0.5, v_align=0.5,
            text_fn=lambda ctx: get_event('hardware_fault_invalid_char3').value, phases={
                'open': Phase([Reset(), TextTween(px=P(0, 0), outline_color=QColor(255, 0, 0, 255), start=0, dur=0.9, ease=QEasingCurve.OutQuint)]),
                'close': Phase([TextTween(px=P(0, 30), outline_color=QColor(255, 0, 0, 0), start=0, dur=0.8, ease=QEasingCurve.OutQuint)]),
            }
        ),
        TextDef(p=P(0.50 + (0.24 + 0.39) / 2, 0.702), px=P(0, -30), text='<#>', font_size=48, fill_color=QColor(0, 0, 0, 0), outline_color=QColor(255, 0, 0, 0), outline_width=1, h_align=0.5, v_align=0.5,
            text_fn=lambda ctx: get_event('hardware_fault_invalid_char4').value, phases={
                'open': Phase([Reset(), TextTween(px=P(0, 0), outline_color=QColor(255, 0, 0, 255), start=0, dur=1.0, ease=QEasingCurve.OutQuint)]),
                'close': Phase([TextTween(px=P(0, 30), outline_color=QColor(255, 0, 0, 0), start=0, dur=0.7, ease=QEasingCurve.OutQuint)]),
            }
        ),

        # RIGHT ARROW CHARS
        TextDef(p=P(0.50 - (0.24 + 0.18) / 2, 0.702), px=P(0, -30), text='➡', font_size=24.0, italic=True, fill_color=QColor(171, 151, 247, 0), h_align=0.5, v_align=0.5,
            phases={
                'open': Phase([Reset(), TextTween(px=P(0, 0), fill_color=QColor(171, 151, 247, 127), start=0.1, dur=0.8, ease=QEasingCurve.OutQuint)]),
                'close': Phase([TextTween(px=P(0, 30), fill_color=QColor(171, 151, 247, 0), start=0, dur=1.0, ease=QEasingCurve.OutQuint)]),
            }
        ),
        TextDef(p=P(0.50, 0.702), px=P(0, -30), text='➡', font_size=24.0, italic=True, fill_color=QColor(171, 151, 247, 0), h_align=0.5, v_align=0.5,
            phases={
                'open': Phase([Reset(), TextTween(px=P(0, 0), fill_color=QColor(171, 151, 247, 127), start=0.1, dur=0.9, ease=QEasingCurve.OutQuint)]),
                'close': Phase([TextTween(px=P(0, 30), fill_color=QColor(171, 151, 247, 0), start=0, dur=0.9, ease=QEasingCurve.OutQuint)]),
            }
        ),
        TextDef(p=P(0.50 + (0.18 + 0.24) / 2, 0.702), px=P(0, -30), text='➡', font_size=24.0, italic=True, fill_color=QColor(171, 151, 247, 0), h_align=0.5, v_align=0.5,
            phases={
                'open': Phase([Reset(), TextTween(px=P(0, 0), fill_color=QColor(171, 151, 247, 127), start=0.1, dur=1.0, ease=QEasingCurve.OutQuint)]),
                'close': Phase([TextTween(px=P(0, 30), fill_color=QColor(171, 151, 247, 0), start=0, dur=0.8, ease=QEasingCurve.OutQuint)]),
            }
        ),
    ],
    polygon_defs=[
        RectDef(p1=P(0.5, 0.68), p2=P(0.5, 0.68), px1=P(-300, -31), px2=P(300, -29), gradient=get_gradient('hardware_fault_gradient'), phases={
            'open': Phase([Reset(), RectTween(px1=P(-300, -1), px2=P(300, 1), start=0, dur=1, ease=QEasingCurve.OutQuint)]),
            'close': Phase([RectTween(px1=P(-300, 29), px2=P(300, 31), start=0, dur=1, ease=QEasingCurve.OutQuint)]),
        }),
        PolygonDef(p=[P(0.5, 0.68)]*4, px=[P(-5, -30), P(0, -35), P(5, -30)], gradient=get_gradient('hardware_fault_gradient'), phases={
            'open': Phase([Reset(), PolygonTween(px=[P(-5, 0), P(0, -5), P(5, 0)], start=0, dur=1, ease=QEasingCurve.OutQuint)]),
            'close': Phase([PolygonTween(px=[P(-5, 30), P(0, 25), P(5, 30)], start=0, dur=1, ease=QEasingCurve.OutQuint)]),
        }),
        RectDef(p1=P(0.5, 0.72), p2=P(0.5, 0.72), px1=P(-300, -31), px2=P(300, -29), gradient=get_gradient('hardware_fault_gradient'), phases={
            'open': Phase([Reset(), RectTween(px1=P(-300, -1), px2=P(300, 1), start=0, dur=1, ease=QEasingCurve.OutQuint)]),
            'close': Phase([RectTween(px1=P(-300, 29), px2=P(300, 31), start=0, dur=1, ease=QEasingCurve.OutQuint)]),
        }),
        PolygonDef(p=[P(0.5, 0.72)]*4, px=[P(-5, -30), P(0, -25), P(5, -30)], gradient=get_gradient('hardware_fault_gradient'), phases={
            'open': Phase([Reset(), PolygonTween(px=[P(-5, 0), P(0, 5), P(5, 0)], start=0, dur=1, ease=QEasingCurve.OutQuint)]),
            'close': Phase([PolygonTween(px=[P(-5, 30), P(0, 35), P(5, 30)], start=0, dur=1, ease=QEasingCurve.OutQuint)]),
        }),
    ],
    button_defs=[
        # Row 1
        *SevenSegmentDisplay(p1=P(0.50 - 0.39, 0.28), p2=P(0.50 - 0.24, 0.30), px1=P(0, 0), px2=P(0, 0), event_out=get_event('hardware_fault_byte1-1')),
        *SevenSegmentDisplay(p1=P(0.50 - 0.18, 0.28), p2=P(0.50 - 0.03, 0.30), px1=P(0, 0), px2=P(0, 0), event_out=get_event('hardware_fault_byte2-1')),
        *SevenSegmentDisplay(p1=P(0.50 + 0.03, 0.28), p2=P(0.50 + 0.18, 0.30), px1=P(0, 0), px2=P(0, 0), event_out=get_event('hardware_fault_byte3-1')),
        *SevenSegmentDisplay(p1=P(0.50 + 0.24, 0.28), p2=P(0.50 + 0.39, 0.30), px1=P(0, 0), px2=P(0, 0), event_out=get_event('hardware_fault_byte4-1')),
        # Row 2
        *SevenSegmentDisplay(p1=P(0.50 - 0.39, 0.54), p2=P(0.50 - 0.24, 0.56), px1=P(0, 0), px2=P(0, 0), event_out=get_event('hardware_fault_byte1-2')),
        *SevenSegmentDisplay(p1=P(0.50 - 0.18, 0.54), p2=P(0.50 - 0.03, 0.56), px1=P(0, 0), px2=P(0, 0), event_out=get_event('hardware_fault_byte2-2')),
        *SevenSegmentDisplay(p1=P(0.50 + 0.03, 0.54), p2=P(0.50 + 0.18, 0.56), px1=P(0, 0), px2=P(0, 0), event_out=get_event('hardware_fault_byte3-2')),
        *SevenSegmentDisplay(p1=P(0.50 + 0.24, 0.54), p2=P(0.50 + 0.39, 0.56), px1=P(0, 0), px2=P(0, 0), event_out=get_event('hardware_fault_byte4-2')),
    ],
)














register_event(EventDef(name='wire_count', value=None))
register_event(EventDef(name='wire_red_count', value=None))
register_event(EventDef(name='wire_yellow_count', value=None))
register_event(EventDef(name='wire_blue_count', value=None))
register_event(EventDef(name='wire_white_count', value=None))
register_event(EventDef(name='wire_black_count', value=None))
register_event(EventDef(name='wire_last_color', value=None))

register_event(EventDef(name='wire_cut_target', value=None))
register_event(EventDef(name='wire_cut_target_pulse', value=0))

# 3 WIRES - RED /        / BLUE / WHITE
register_event(EventDef(name='wire_c3-1', value=False)) # 0 RED
register_event(EventDef(name='wire_c3-2', value=False)) # LAST = WHITE
register_event(EventDef(name='wire_c3-3', value=False)) # ≥2 BLUE

# 4 WIRES - RED / YELLOW / BLUE /       /
register_event(EventDef(name='wire_c4-1', value=False)) # ≥2 RED
register_event(EventDef(name='wire_c4-2', value=False)) # LAST = YELLOW + 0 RED
register_event(EventDef(name='wire_c4-3', value=False)) # 1 BLUE
register_event(EventDef(name='wire_c4-4', value=False)) # ≥2 YELLOW

# 5 WIRES - RED / YELLOW /      /       / BLACK
register_event(EventDef(name='wire_c5-1', value=False)) # LAST = BLACK
register_event(EventDef(name='wire_c5-2', value=False)) # 1 RED + ≥2 YELLOW
register_event(EventDef(name='wire_c5-3', value=False)) # 0 BLACK

# 6 WIRES - RED / YELLOW /      / WHITE
register_event(EventDef(name='wire_c6-1', value=False)) # 0 YELLOW
register_event(EventDef(name='wire_c6-2', value=False)) # 1 YELLOW + ≥2 WHITE
register_event(EventDef(name='wire_c6-3', value=False)) # 0 RED


register_gradient(GradientDef(
    name='camera_access_gradient', p1=P(0.2, 0), p2=P(0.8, 0), target='fill', phase_event = get_event('wire_window_phase'), stops=[
        GradientStop(0.0, QColor(171, 151, 247, 0)),
        GradientStop(0.5, QColor(171, 151, 247, 0)),
        GradientStop(1.0, QColor(171, 151, 247, 0)),
    ], phases={'open': Phase([GradientTween(stops=[GradientStop(0.0, QColor(171, 151, 247, 0)), GradientStop(0.5, QColor(171, 151, 247, 255)), GradientStop(1.0, QColor(171, 151, 247, 0))], start=0, dur=0.9, ease=QEasingCurve.OutQuint)]),
               'close': Phase([GradientTween(stops=[GradientStop(0.0, QColor(171, 151, 247, 0)), GradientStop(0.5, QColor(171, 151, 247, 0)), GradientStop(1.0, QColor(171, 151, 247, 0))], start=0, dur=0.9, ease=QEasingCurve.OutQuint)]),
    }
))

register_gradient(GradientDef(
    name='wire_cut_target_pulse', p1=P(0.5, 0), p2=P(0.5, 0), px1=P(-350, 0), px2=P(350, 0), target='fill', stops=[
        GradientStop(0.0, QColor(171, 151, 247, 0)),
        GradientStop(0.5, QColor(171, 151, 247, 0)),
        GradientStop(1.0, QColor(171, 151, 247, 0)),
    ], phases={'pulse': Phase([
        GradientTween(stops=[GradientStop(0.0, QColor(171, 151, 247, 0)), GradientStop(0.5, QColor(171, 151, 247, 255)), GradientStop(1.0, QColor(171, 151, 247, 0))], start=0, dur=0, ease=QEasingCurve.Linear),
        GradientTween(stops=[GradientStop(0.0, QColor(171, 151, 247, 0)), GradientStop(0.5, QColor(171, 151, 247, 0)), GradientStop(1.0, QColor(171, 151, 247, 0))], start=0, dur=0.9, ease=QEasingCurve.OutQuint)
        ], pulse_event=get_event('wire_cut_target_pulse'))
    }
))

# CAMERA ACCESS PANEL
camera_access_window = WindowDef(
    p1=P(0.0, 0.0), p2=P(1.0, 1.0),
    phase_event = [get_event('wire_window_phase'), get_event('wire_count')],
    phase_fn = lambda a, b: a if a in ('open', 'close') else f'wire={b}' if isinstance(b, int) else a,
    listener_defs=[
        # 3 WIRE CONDITIONS
        EventListener(targets = [get_event('wire_c3-1')], value_fn = lambda ctx: get_event('wire_red_count').value,                                           conditions = [lambda v: v == 0],                         values = [True, False], skip_none=False),
        EventListener(targets = [get_event('wire_c3-2')], value_fn = lambda ctx: get_event('wire_last_color').value,                                          conditions = [lambda v: v == 'white'],                   values = [True, False], skip_none=False),
        EventListener(targets = [get_event('wire_c3-3')], value_fn = lambda ctx: get_event('wire_blue_count').value,                                          conditions = [lambda v: v > 1],                          values = [True, False], skip_none=False),
        # 4 WIRE CONDITIONS
        EventListener(targets = [get_event('wire_c4-1')], value_fn = lambda ctx: get_event('wire_red_count').value,                                           conditions = [lambda v: v > 1],                          values = [True, False], skip_none=False),
        EventListener(targets = [get_event('wire_c4-2')], value_fn = lambda ctx: (get_event('wire_last_color').value, get_event('wire_red_count').value),     conditions = [lambda v: v[0] == 'yellow' and v[1] == 0], values = [True, False], skip_none=False),
        EventListener(targets = [get_event('wire_c4-3')], value_fn = lambda ctx: get_event('wire_blue_count').value,                                          conditions = [lambda v: v == 1],                         values = [True, False], skip_none=False),
        EventListener(targets = [get_event('wire_c4-4')], value_fn = lambda ctx: get_event('wire_yellow_count').value,                                        conditions = [lambda v: v > 1],                          values = [True, False], skip_none=False),
        # 5 WIRE CONDITIONS
        EventListener(targets = [get_event('wire_c5-1')], value_fn = lambda ctx: get_event('wire_last_color').value,                                          conditions = [lambda v: v == 'black'],                   values = [True, False], skip_none=False),
        EventListener(targets = [get_event('wire_c5-2')], value_fn = lambda ctx: (get_event('wire_red_count').value, get_event('wire_yellow_count').value),   conditions = [lambda v: v[0] == 1 and v[1] > 1],         values = [True, False], skip_none=False),
        EventListener(targets = [get_event('wire_c5-3')], value_fn = lambda ctx: get_event('wire_black_count').value,                                         conditions = [lambda v: v == 0],                         values = [True, False], skip_none=False),
        # 6 WIRE CONDITIONS
        EventListener(targets = [get_event('wire_c6-1')], value_fn = lambda ctx: get_event('wire_yellow_count').value,                                        conditions = [lambda v: v == 0],                         values = [True, False], skip_none=False),
        EventListener(targets = [get_event('wire_c6-2')], value_fn = lambda ctx: (get_event('wire_yellow_count').value, get_event('wire_white_count').value), conditions = [lambda v: v[0] == 1 and v[1] > 1],         values = [True, False], skip_none=False),
        EventListener(targets = [get_event('wire_c6-3')], value_fn = lambda ctx: get_event('wire_red_count').value,                                           conditions = [lambda v: v == 0],                         values = [True, False], skip_none=False),
        # WIRE CUT TARGET
        EventListener(targets = [get_event('wire_cut_target')], 
        value_fn = lambda ctx: (get_event('wire_count').value, 
                                get_event('wire_c3-1').value, get_event('wire_c3-2').value, get_event('wire_c3-3').value,
                                get_event('wire_c4-1').value, get_event('wire_c4-2').value, get_event('wire_c4-3').value, get_event('wire_c4-4').value,
                                get_event('wire_c5-1').value, get_event('wire_c5-2').value, get_event('wire_c5-3').value,
                                get_event('wire_c6-1').value, get_event('wire_c6-2').value, get_event('wire_c6-3').value,
                                get_event('wire_red_count').value, get_event('wire_yellow_count').value, get_event('wire_blue_count').value, get_event('wire_white_count').value, get_event('wire_black_count').value, get_event('wire_last_color').value),
        conditions = [lambda v: v[0] == 3 and v[1],
                      lambda v: v[0] == 3 and v[2] and v[14] != None,
                      lambda v: v[0] == 3 and v[3] and v[14] != None and v[19] != None,
                      lambda v: v[0] == 3 and v[14] != None and v[16] != None and v[19] != None, 
                      lambda v: v[0] == 4 and v[4],
                      lambda v: v[0] == 4 and v[5] and v[14] != None,
                      lambda v: v[0] == 4 and v[6] and v[14] != None and v[19] != None,
                      lambda v: v[0] == 4 and v[7] and v[14] != None and v[16] != None and v[19] != None,
                      lambda v: v[0] == 4 and v[14] != None and v[15] != None and v[16] != None and v[19] != None, 
                      lambda v: v[0] == 5 and v[8],
                      lambda v: v[0] == 5 and v[9] and v[19] != None,
                      lambda v: v[0] == 5 and v[10] and v[14] != None and v[15] != None and v[19] != None,
                      lambda v: v[0] == 5 and v[14] != None and v[15] != None and v[18] != None and v[19] != None,
                      lambda v: v[0] == 6 and v[11],
                      lambda v: v[0] == 6 and v[12] and v[15] != None,
                      lambda v: v[0] == 6 and v[13] and v[17] != None,
                      lambda v: v[0] == 6 and v[14] != None and v[15] != None and v[17] != None],
        values = ['2ND', '3RD', 'LAST BLUE', '3RD',
                  'LAST RED', '1ST', '1ST', '4TH', '2ND',
                  '4TH', '1ST', '2ND', '5TH',
                  '3RD', '4TH', '6TH', '2ND', ''], skip_none=False),
        EventListener(value_fn='pulse', targets=[get_event('wire_cut_target_pulse')], passthrough=True, wait_for_updates=lambda ctx: get_event('wire_cut_target').value),
    ],
    polygon_defs=[
        # WIRE CUT TARGET
        RectDef(p1=P(0.5, 0.92), p2=P(0.5, 0.92), px1=P(-350, -5), px2=P(350, 45), gradient=get_gradient('wire_cut_target_pulse')),

        # WIRES
        PolygonDef(p=[P(0.5 - 0.20, 0.75)]*4, px=[P(-10, -150), P(0, -140), P(0, 140), P(-10, 150)], closed=False, draw_progress=0.0, fill_color=QColor(255,255,255,0), outline_color=QColor(100, 100, 100, 0), outline_width=4, 
            phase_override=lambda: (
                'close' if get_event('wire_window_phase').value == 'close' else
                'open'  if get_event('wire_count').value == 3 or get_event('wire_count').value == 4 or get_event('wire_count').value == 5 or get_event('wire_count').value == 6 else
                'dim'
            ),
            phases={
                P_OPEN:  Phase([PolygonTween(outline_color=QColor(255, 255, 255, 255), draw_progress=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
                'dim':   Phase([PolygonTween(outline_color=QColor(100, 100, 100, 255), draw_progress=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
                P_CLOSE: Phase([PolygonTween(outline_color=QColor(100, 100, 100, 0),   draw_progress=0.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)])}
        ),
        PolygonDef(p=[P(0.5 - 0.12, 0.75)]*4, px=[P(-10, -160), P(0, -150), P(0, 150), P(-10, 160)], closed=False, draw_progress=0.0, fill_color=QColor(255,255,255,0), outline_color=QColor(100, 100, 100, 0), outline_width=4, 
            phase_override=lambda: (
                'close' if get_event('wire_window_phase').value == 'close' else
                'open'  if get_event('wire_count').value == 3 or get_event('wire_count').value == 4 or get_event('wire_count').value == 5 or get_event('wire_count').value == 6 else
                'dim'
            ),
            phases={
                P_OPEN:  Phase([PolygonTween(outline_color=QColor(255, 255, 255, 255), draw_progress=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
                'dim':   Phase([PolygonTween(outline_color=QColor(100, 100, 100, 255), draw_progress=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
                P_CLOSE: Phase([PolygonTween(outline_color=QColor(100, 100, 100, 0),   draw_progress=0.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)])}
        ),
        PolygonDef(p=[P(0.5 - 0.04, 0.75)]*4, px=[P(-10, -170), P(0, -160), P(0, 160), P(-10, 170)], closed=False, draw_progress=0.0, fill_color=QColor(255,255,255,0), outline_color=QColor(100, 100, 100, 0), outline_width=4, 
            phase_override=lambda: (
                'close' if get_event('wire_window_phase').value == 'close' else
                'open'  if get_event('wire_count').value == 3 or get_event('wire_count').value == 4 or get_event('wire_count').value == 5 or get_event('wire_count').value == 6 else
                'dim'
            ),
            phases={
                P_OPEN:  Phase([PolygonTween(outline_color=QColor(255, 255, 255, 255), draw_progress=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
                'dim':   Phase([PolygonTween(outline_color=QColor(100, 100, 100, 255), draw_progress=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
                P_CLOSE: Phase([PolygonTween(outline_color=QColor(100, 100, 100, 0),   draw_progress=0.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)])}
        ),
        PolygonDef(p=[P(0.5 + 0.04, 0.75)]*4, px=[P(10, -170), P(0, -160), P(0, 160), P(10, 170)], closed=False, draw_progress=0.0, fill_color=QColor(255,255,255,0), outline_color=QColor(100, 100, 100, 0), outline_width=4, 
            phase_override=lambda: (
                'close' if get_event('wire_window_phase').value == 'close' else
                'open'  if get_event('wire_count').value == 4 or get_event('wire_count').value == 5 or get_event('wire_count').value == 6 else
                'dim'
            ),
            phases={
                P_OPEN:  Phase([PolygonTween(outline_color=QColor(255, 255, 255, 255), draw_progress=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
                'dim':   Phase([PolygonTween(outline_color=QColor(100, 100, 100, 255), draw_progress=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
                P_CLOSE: Phase([PolygonTween(outline_color=QColor(100, 100, 100, 0),   draw_progress=0.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)])}
        ),
        PolygonDef(p=[P(0.5 + 0.12, 0.75)]*4, px=[P(10, -160), P(0, -150), P(0, 150), P(10, 160)], closed=False, draw_progress=0.0, fill_color=QColor(255,255,255,0), outline_color=QColor(100, 100, 100, 0), outline_width=4, 
            phase_override=lambda: (
                'close' if get_event('wire_window_phase').value == 'close' else
                'open'  if get_event('wire_count').value == 5 or get_event('wire_count').value == 6 else
                'dim'
            ),
            phases={
                P_OPEN:  Phase([PolygonTween(outline_color=QColor(255, 255, 255, 255), draw_progress=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
                'dim':   Phase([PolygonTween(outline_color=QColor(100, 100, 100, 255), draw_progress=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
                P_CLOSE: Phase([PolygonTween(outline_color=QColor(100, 100, 100, 0),   draw_progress=0.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)])}
        ),
        PolygonDef(p=[P(0.5 + 0.20, 0.75)]*4, px=[P(10, -150), P(0, -140), P(0, 140), P(10, 150)], closed=False, draw_progress=0.0, fill_color=QColor(255,255,255,0), outline_color=QColor(100, 100, 100, 0), outline_width=4, 
            phase_override=lambda: (
                'close' if get_event('wire_window_phase').value == 'close' else
                'open'  if get_event('wire_count').value == 6 else
                'dim'
            ),
            phases={
                P_OPEN:  Phase([PolygonTween(outline_color=QColor(255, 255, 255, 255), draw_progress=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
                'dim':   Phase([PolygonTween(outline_color=QColor(100, 100, 100, 255), draw_progress=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
                P_CLOSE: Phase([PolygonTween(outline_color=QColor(100, 100, 100, 0),   draw_progress=0.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)])}
        ),
        
        # Container
        RectDef(p1=P(0.20, 0.65), p2=P(0.80, 0.65), px1=P(0, 19), px2=P(0, 21), gradient=get_gradient('camera_access_gradient'), phases={
            'open': Phase([Reset(), RectTween(px1=P(0, -1), px2=P(0, 1), start=0.00, dur=1.00, ease=QEasingCurve.OutQuint)]),
            'close': Phase([RectTween(px1=P(0, 19), px2=P(0, 21), start=0.00, dur=1.00, ease=QEasingCurve.OutQuint)])}),
        RectDef(p1=P(0.20, 0.65), p2=P(0.80, 0.65), px1=P(0, 21), px2=P(0, 23), gradient=get_gradient('camera_access_gradient'), phases={
            'open': Phase([Reset(), RectTween(p1=P(0.20, 0.85), p2=P(0.80, 0.85), px1=P(0, -1), px2=P(0, 1), start=0.00, dur=1.50, ease=QEasingCurve.OutQuint)]),
            'close': Phase([RectTween(p1=P(0.20, 0.65), p2=P(0.80, 0.65), px1=P(0, 21), px2=P(0, 23), start=0.00, dur=1.50, ease=QEasingCurve.OutQuint)])}),
    ],
    text_defs=[
        # WIRE NUMBER LABEL
        TextDef(p=P(0.5 - 0.20, 0.75), text='1', bold=True, font_size=30.0, h_align=0.5, v_align=0.5, fill_color=QColor(0, 0, 0, 0), outline_color=QColor(100, 100, 100, 0), outline_width=2, 
            phase_override=lambda: (
                'close' if get_event('wire_window_phase').value == 'close' else
                'open'  if get_event('wire_count').value == 3 or get_event('wire_count').value == 4 or get_event('wire_count').value == 5 or get_event('wire_count').value == 6 else
                'close'
            ),
            phases={
                P_OPEN:  Phase([TextTween(fill_color=QColor(0, 0, 0, 255), outline_color=QColor(255, 255, 255, 255), start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
                P_CLOSE: Phase([TextTween(fill_color=QColor(0, 0, 0, 0), outline_color=QColor(100, 100, 100, 0),   start=0, dur=0.5, ease=QEasingCurve.OutQuint)])}
        ),
        TextDef(p=P(0.5 - 0.12, 0.75), text='2', bold=True, font_size=30.0, h_align=0.5, v_align=0.5, fill_color=QColor(0, 0, 0, 0), outline_color=QColor(100, 100, 100, 0), outline_width=2, 
            phase_override=lambda: (
                'close' if get_event('wire_window_phase').value == 'close' else
                'open'  if get_event('wire_count').value == 3 or get_event('wire_count').value == 4 or get_event('wire_count').value == 5 or get_event('wire_count').value == 6 else
                'close'
            ),
            phases={
                P_OPEN:  Phase([TextTween(fill_color=QColor(0, 0, 0, 255), outline_color=QColor(255, 255, 255, 255), start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
                P_CLOSE: Phase([TextTween(fill_color=QColor(0, 0, 0, 0), outline_color=QColor(100, 100, 100, 0),   start=0, dur=0.5, ease=QEasingCurve.OutQuint)])}
        ),
        TextDef(p=P(0.5 - 0.04, 0.75), text='3', bold=True, font_size=30.0, h_align=0.5, v_align=0.5, fill_color=QColor(0, 0, 0, 0), outline_color=QColor(100, 100, 100, 0), outline_width=2, 
            phase_override=lambda: (
                'close' if get_event('wire_window_phase').value == 'close' else
                'open'  if get_event('wire_count').value == 3 or get_event('wire_count').value == 4 or get_event('wire_count').value == 5 or get_event('wire_count').value == 6 else
                'close'
            ),
            phases={
                P_OPEN:  Phase([TextTween(fill_color=QColor(0, 0, 0, 255), outline_color=QColor(255, 255, 255, 255), start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
                P_CLOSE: Phase([TextTween(fill_color=QColor(0, 0, 0, 0), outline_color=QColor(100, 100, 100, 0),   start=0, dur=0.5, ease=QEasingCurve.OutQuint)])}
        ),
        TextDef(p=P(0.5 + 0.04, 0.75), text='4', bold=True, font_size=30.0, h_align=0.5, v_align=0.5, fill_color=QColor(0, 0, 0, 0), outline_color=QColor(100, 100, 100, 0), outline_width=2, 
            phase_override=lambda: (
                'close' if get_event('wire_window_phase').value == 'close' else
                'open'  if get_event('wire_count').value == 4 or get_event('wire_count').value == 5 or get_event('wire_count').value == 6 else
                'close'
            ),
            phases={
                P_OPEN:  Phase([TextTween(fill_color=QColor(0, 0, 0, 255), outline_color=QColor(255, 255, 255, 255), start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
                P_CLOSE: Phase([TextTween(fill_color=QColor(0, 0, 0, 0), outline_color=QColor(100, 100, 100, 0),   start=0, dur=0.5, ease=QEasingCurve.OutQuint)])}
        ),
        TextDef(p=P(0.5 + 0.12, 0.75), text='5', bold=True, font_size=30.0, h_align=0.5, v_align=0.5, fill_color=QColor(0, 0, 0, 0), outline_color=QColor(100, 100, 100, 0), outline_width=2, 
            phase_override=lambda: (
                'close' if get_event('wire_window_phase').value == 'close' else
                'open'  if get_event('wire_count').value == 5 or get_event('wire_count').value == 6 else
                'close'
            ),
            phases={
                P_OPEN:  Phase([TextTween(fill_color=QColor(0, 0, 0, 255), outline_color=QColor(255, 255, 255, 255), start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
                P_CLOSE: Phase([TextTween(fill_color=QColor(0, 0, 0, 0), outline_color=QColor(100, 100, 100, 0),   start=0, dur=0.5, ease=QEasingCurve.OutQuint)])}
        ),
        TextDef(p=P(0.5 + 0.20, 0.75), text='6', bold=True, font_size=30.0, h_align=0.5, v_align=0.5, fill_color=QColor(0, 0, 0, 0), outline_color=QColor(100, 100, 100, 0), outline_width=2, 
            phase_override=lambda: (
                'close' if get_event('wire_window_phase').value == 'close' else
                'open'  if get_event('wire_count').value == 6 else
                'close'
            ),
            phases={
                P_OPEN:  Phase([TextTween(fill_color=QColor(0, 0, 0, 255), outline_color=QColor(255, 255, 255, 255), start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
                P_CLOSE: Phase([TextTween(fill_color=QColor(0, 0, 0, 0), outline_color=QColor(100, 100, 100, 0),   start=0, dur=0.5, ease=QEasingCurve.OutQuint)])}
        ),
        


        TextDef(p=P(0.00, 0.00), px=P(15, 140), text='CAMERA ACCESS PANEL', font_size=20.0, bold=True, h_align=0.0, v_align=0.0, char_display=0.0, sub_char_clip=True, fill_color=QColor(255,255,255,0), gradient=get_gradient('alt_color_outline'), outline_width=1, phases={
                P_OPEN:  Phase([Reset(), TextTween(char_display=1, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
                P_CLOSE: Phase([         TextTween(char_display=0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)])}
        ),

        # WIRE COUNT
        TextDef(p=P(0.00, 0.20), px=P(10, 0), text='WIRE COUNT', font_size=20.0, fill_color=QColor(171, 151, 247, 255), h_align=0.0, v_align=0.5, char_display=0.0, sub_char_clip=True, phases={
                P_OPEN:  Phase([Reset(), TextTween(char_display=1, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
                P_CLOSE: Phase([         TextTween(char_display=0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)])}
        ),

        # ── THREE WIRES
        TextDef(p=P(0.00, 0.30), px=P(10, 0), text='RED WIRE COUNT', font_size=20.0, fill_color=QColor(171, 151, 247, 50), h_align=0.0, v_align=0.5, char_display=0.0, sub_char_clip=True, 
            phase_override=lambda: (
                'close' if get_event('wire_window_phase').value == 'close' else
                'open'  if get_event('wire_count').value == 3 else
                'open'  if get_event('wire_count').value == 4 else
                'open'  if get_event('wire_count').value == 5 and not get_event('wire_c5-1').value else
                'open'  if get_event('wire_count').value == 6 and not get_event('wire_c6-1').value and not get_event('wire_c6-2').value else
                'dim'
            ),
            phases={
                P_OPEN:  Phase([TextTween(fill_color=QColor(171, 151, 247, 255), char_display=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
                'dim':   Phase([TextTween(fill_color=QColor(171, 151, 247, 50),  char_display=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
                P_CLOSE: Phase([TextTween(char_display=0.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)])},
        ),
        TextDef(p=P(0.00, 0.35), px=P(10, 0), text='YELLOW WIRE COUNT', font_size=20.0, fill_color=QColor(171, 151, 247, 50), h_align=0.0, v_align=0.5, char_display=0.0, sub_char_clip=True, 
            phase_override=lambda: (
                'close' if get_event('wire_window_phase').value == 'close' else
                'open' if get_event('wire_count').value == 4 and not get_event('wire_c4-1').value and not get_event('wire_c4-2').value and not get_event('wire_c4-3').value else
                'open' if get_event('wire_count').value == 5 and not get_event('wire_c5-1').value else 
                'open' if get_event('wire_count').value == 6 else 
                'dim'
            ), phases={
                P_OPEN:  Phase([TextTween(fill_color=QColor(171, 151, 247, 255), char_display=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
                'dim':   Phase([TextTween(fill_color=QColor(171, 151, 247, 50), char_display=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
                P_CLOSE: Phase([TextTween(char_display=0.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)])},
        ),
        TextDef(p=P(0.00, 0.40), px=P(10, 0), text='BLUE WIRE COUNT', font_size=20.0, fill_color=QColor(171, 151, 247, 50), h_align=0.0, v_align=0.5, char_display=0.0, sub_char_clip=True,
            phase_override=lambda: (
                'close' if get_event('wire_window_phase').value == 'close' else
                'open' if get_event('wire_count').value == 3 and not get_event('wire_c3-1').value and not get_event('wire_c3-2').value else 
                'open' if get_event('wire_count').value == 4 and not get_event('wire_c4-1').value and not get_event('wire_c4-2').value else
                'dim'
            ), phases={
                P_OPEN:  Phase([TextTween(fill_color=QColor(171, 151, 247, 255), char_display=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
                'dim':   Phase([TextTween(fill_color=QColor(171, 151, 247, 50), char_display=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
                P_CLOSE: Phase([TextTween(char_display=0.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)])},
        ),
        TextDef(p=P(0.00, 0.45), px=P(10, 0), text='WHITE WIRE COUNT', font_size=20.0, fill_color=QColor(171, 151, 247, 50), h_align=0.0, v_align=0.5, char_display=0.0, sub_char_clip=True, 
            phase_override=lambda: (
                'close' if get_event('wire_window_phase').value == 'close' else
                'open' if get_event('wire_count').value == 6 and not get_event('wire_c6-1').value else
                'dim'
            ), phases={
                P_OPEN:  Phase([TextTween(fill_color=QColor(171, 151, 247, 255), char_display=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
                'dim':   Phase([TextTween(fill_color=QColor(171, 151, 247, 50), char_display=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
                P_CLOSE: Phase([TextTween(char_display=0.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)])},
        ),
        TextDef(p=P(0.00, 0.50), px=P(10, 0), text='BLACK WIRE COUNT', font_size=20.0, fill_color=QColor(171, 151, 247, 50), h_align=0.0, v_align=0.5, char_display=0.0, sub_char_clip=True,
            phase_override=lambda: (
                'close' if get_event('wire_window_phase').value == 'close' else
                'open' if get_event('wire_count').value == 5 and not get_event('wire_c5-1').value and not get_event('wire_c5-2').value else
                'dim'
            ), phases={
                P_OPEN:  Phase([TextTween(fill_color=QColor(171, 151, 247, 255), char_display=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
                'dim':   Phase([TextTween(fill_color=QColor(171, 151, 247, 50), char_display=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
                P_CLOSE: Phase([TextTween(char_display=0.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)])},
        ),
        TextDef(p=P(0.00, 0.55), px=P(10, 0), text='LAST WIRE COLOR', font_size=20.0, fill_color=QColor(171, 151, 247, 50), h_align=0.0, v_align=0.5, char_display=0.0, sub_char_clip=True,
            phase_override=lambda: (
                'close' if get_event('wire_window_phase').value == 'close' else
                'open' if get_event('wire_count').value == 3 and not get_event('wire_c3-1').value else
                'open' if get_event('wire_count').value == 4 and not get_event('wire_c4-1').value else
                'open' if get_event('wire_count').value == 5 else
                'dim'
            ), phases={
                P_OPEN:  Phase([TextTween(fill_color=QColor(171, 151, 247, 255), char_display=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
                'dim':   Phase([TextTween(fill_color=QColor(171, 151, 247, 50), char_display=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
                P_CLOSE: Phase([TextTween(char_display=0.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)])},
        ),
        # INSTRUCTIONS
        TextDef(p=P(0.50, 0.92), text='CUT THE <#> WIRE', font_size=32.0, bold=True, fill_color=QColor(171, 151, 247, 255), h_align=0.5, v_align=0, char_display=0.0, sub_char_clip=True,
            text_fn=lambda ctx: get_event('wire_cut_target').value, phase_override=lambda: (
                'close' if get_event('wire_window_phase').value == 'close' else
                'open' if get_event('wire_cut_target').value != '' else
                'close'
            ), phases={
                P_OPEN:  Phase([TextTween(char_display=1.0, start=0, dur=0.0, ease=QEasingCurve.Linear)]),
                P_CLOSE: Phase([TextTween(char_display=0.0, start=0, dur=0.0, ease=QEasingCurve.OutQuint)])},
        ),
    ],
    button_defs=[
        *SegmentedButtons(
            p1=P(1.00, 0.18), p2=P(1.00, 0.22), px1=P(-410, 0), px2=P(-10, 0), event_out=get_event('wire_count'), segments=[
                Segment(event_delta=3, weight=1, label='3'),
                Segment(event_delta=4, weight=1, label='4'),
                Segment(event_delta=5, weight=1, label='5'),
                Segment(event_delta=6, weight=1, label='6'),
            ],
        ),
        *SegmentedButtons(
            p1=P(1.00, 0.28), p2=P(1.00, 0.32), px1=P(-410 + 40, 0), px2=P(-10 - 40, 0), event_out=get_event('wire_red_count'), 
            phase_override=lambda: (
                'close' if get_event('wire_window_phase').value == 'close' else
                'open' if get_event('wire_count').value == 3 else 
                'open' if get_event('wire_count').value == 4 else 
                'open' if get_event('wire_count').value == 5 and not get_event('wire_c5-1').value else 
                'open' if get_event('wire_count').value == 6 and not get_event('wire_c6-1').value and not get_event('wire_c6-2').value else 
                'close'
            ), segments=[
                Segment(event_delta=0, weight=1, label='0'),
                Segment(event_delta=1, weight=1, label='1'),
                Segment(event_delta=2, weight=2, label='≥2'),
            ],
        ),
        *SegmentedButtons(
            p1=P(1.00, 0.33), p2=P(1.00, 0.37), px1=P(-410 + 40, 0), px2=P(-10 - 40, 0), event_out=get_event('wire_yellow_count'), 
            phase_override=lambda: (
                'close' if get_event('wire_window_phase').value == 'close' else
                'open' if get_event('wire_count').value == 4 and not get_event('wire_c4-1').value and not get_event('wire_c4-2').value and not get_event('wire_c4-3').value else
                'open' if get_event('wire_count').value == 5 and not get_event('wire_c5-1').value else 
                'open' if get_event('wire_count').value == 6 else 
                'close'
            ), segments=[
                Segment(event_delta=0, weight=1, label='0'),
                Segment(event_delta=1, weight=1, label='1'),
                Segment(event_delta=2, weight=2, label='≥2'),
            ],
        ),
        *SegmentedButtons(
            p1=P(1.00, 0.38), p2=P(1.00, 0.42), px1=P(-410 + 40, 0), px2=P(-10 - 40, 0), event_out=get_event('wire_blue_count'), 
            phase_override=lambda: (
                'close' if get_event('wire_window_phase').value == 'close' else
                'open' if get_event('wire_count').value == 3 and not get_event('wire_c3-1').value and not get_event('wire_c3-2').value else 
                'open' if get_event('wire_count').value == 4 and not get_event('wire_c4-1').value and not get_event('wire_c4-2').value else
                'close'
            ), segments=[
                Segment(event_delta=0, weight=1, label='0'),
                Segment(event_delta=1, weight=1, label='1'),
                Segment(event_delta=2, weight=2, label='≥2'),
            ],
        ),
        *SegmentedButtons(
            p1=P(1.00, 0.43), p2=P(1.00, 0.47), px1=P(-410 + 40, 0), px2=P(-10 - 40, 0), event_out=get_event('wire_white_count'), 
            phase_override=lambda: (
                'close' if get_event('wire_window_phase').value == 'close' else
                'open' if get_event('wire_count').value == 6 and not get_event('wire_c6-1').value else
                'close'
            ), segments=[
                Segment(event_delta=1, weight=1, label='≤1'),
                Segment(event_delta=2, weight=1, label='≥2'),
            ],
        ),
        *SegmentedButtons(
            p1=P(1.00, 0.48), p2=P(1.00, 0.52), px1=P(-410 + 40, 0), px2=P(-10 - 40, 0), event_out=get_event('wire_black_count'), 
            phase_override=lambda: (
                'close' if get_event('wire_window_phase').value == 'close' else
                'open' if get_event('wire_count').value == 5 and not get_event('wire_c5-1').value and not get_event('wire_c5-2').value else
                'close'
            ), segments=[
                Segment(event_delta=0, weight=1, label='0'),
                Segment(event_delta=1, weight=1, label='≥1'),
            ],
        ),
        *SegmentedButtons(
            p1=P(1.00, 0.53), p2=P(1.00, 0.57), px1=P(-410, 0), px2=P(-10, 0), event_out=get_event('wire_last_color'), 
            phase_override=lambda: (
                'close' if get_event('wire_window_phase').value == 'close' else
                'open' if get_event('wire_count').value == 3 and not get_event('wire_c3-1').value else
                'open' if get_event('wire_count').value == 4 and not get_event('wire_c4-1').value else
                'open' if get_event('wire_count').value == 5 else
                'close'
            ), segments=[
                Segment(event_delta='yellow', weight=1, label='YELLOW'),
                Segment(event_delta='white', weight=1, label='WHITE'),
                Segment(event_delta='black', weight=1, label='BLACK'),
            ],
        ),

        # RESET VALUES
        *SegmentedButtons(
            p1=P(1.00, 0.235), p2=P(1.00, 0.265), px1=P(-410 + 130, 0), px2=P(-10 - 130, 0), event_out=[get_event('wire_count'), get_event('wire_red_count'), get_event('wire_yellow_count'), get_event('wire_blue_count'), get_event('wire_white_count'), get_event('wire_black_count'), get_event('wire_last_color')], 
            text_def=TextDef(font_size=14.0, fill_color=QColor(255, 255, 255, 255), bold=True),
            phase_override=lambda: (
                'close' if get_event('wire_window_phase').value == 'close' else
                'open' if get_event('wire_count').value == 3 or get_event('wire_count').value == 4 or get_event('wire_count').value == 5 or get_event('wire_count').value == 6 else
                'close'
            ), segments=[
                Segment(event_delta=[None, None, None, None, None, None, None], weight=1, label='RESET'),
            ],
        ),
    ],
)









tasks_window = WindowDef(
    p1=P(0.5, 0.0), p2=P(1.0, 1.0),
    hidden_event=get_event('window_disabled_task'),
    phase_event=get_event('content_phase_task'),
    phases={
        'open': Phase([WindowTween(p1=get_event('task_window_p1'), p2=get_event('task_window_p2'), px1=get_event('task_window_px1'), px2=get_event('task_window_px2'), start=0.0, dur=1.0, ease=QEasingCurve.OutQuint)], update_retrigger=True)
    },
    listener_defs=[
        EventListener(value_fn=True, targets=[get_event('new_log')], passthrough=True, wait_for_updates=get_event('textbox_test_value')),
        EventListener(value_fn='pulse', targets=[get_event('task_window_pulse')], passthrough=True, wait_for_updates=lambda ctx: get_event('task_window').value),
        EventListener(value_fn=lambda ctx: get_event('task_window').value, targets=[get_event('task_window_text')], passthrough=True,),
        EventListener(value_fn=lambda ctx: (get_event('task_window').value, get_event('content_phase_task').value), targets=[get_event('wire_window_phase')], conditions=[lambda v: v[0] == '2. Heist Mission' and v[1] != 'close'], values=['open', 'close']),
        EventListener(value_fn=lambda ctx: (get_event('task_window').value, get_event('content_phase_task').value), targets=[get_event('hardware_fault_phase')], conditions=[lambda v: v[0] == '1. Snack Run' and v[1] != 'close'], values=['open', 'close']),
    ],
    polygon_defs=[
        PolygonDef(p=[P(1, 0.5), P(1, 0.5), P(1, 0.5), P(1, 0.5)], px=[P(-62, 0), P(-70, 0), P(-70, 0), P(-62, 0)], fill_color=QColor(255, 255, 255, 0), outline_width=2, closed=False, gradient=get_gradient('alt_color_outline'), phases={
            'open': Phase([PolygonTween(p=[P(1, 0), P(1, 0), P(1, 1), P(1, 1)], px=[P(-62, 25 - 8), P(-70, 25), P(-70, -25), P(-62, -25 + 8)], start=0.0, dur=0.5, ease=QEasingCurve.OutQuint),
                            PolygonTween(p=[P(0, 0), P(0, 0), P(0, 1), P(0, 1)], px=[P(9, 25 - 8), P(1, 25), P(1, -25), P(9, -25 + 8)], start=0.5, dur=1.0, ease=QEasingCurve.OutQuint)]),
            'close': Phase([PolygonTween(px=[P(-62, 0), P(-70, 0), P(-70, 0), P(-62, 0)], start=0, dur=0.5, ease=QEasingCurve.OutQuint)])
        },),
        RectDef(p1=P(0, 0), p2=P(0, 0), px1=P(1, 95 - 3), px2=P(700, 130 + 3), gradient=get_gradient('task_window_pulse')),
    ],
    text_defs=[
        TextDef(p=P(1, 0), px=P(15, 15), text='TASKS', bold=True, font_size=70, h_align=0.0, v_align=0.0, char_display=0, sub_char_clip=True, fill_color=QColor(255,255,255,0), gradient=get_gradient('alt_color_outline'), outline_width=2, phases={
                'open': Phase([TextTween(p=P(0, 0), char_display=1, start=0.5, dur=1.0, ease=QEasingCurve.OutQuint)]),
                'close': Phase([TextTween(char_display=0, start=0.0, dur=1.0, ease=QEasingCurve.OutQuint)]),
            }
        ),
        TextDef(p=P(1, 0), px=P(15, 95), text='<#>', font_size=30, h_align=0.0, v_align=0.0, char_display=0, sub_char_clip=True, fill_color=QColor(255,255,255,0), gradient=get_gradient('alt_color_fill'), outline_width=0, 
            text_fn=lambda ctx: get_event('task_window_text').value, phases={
                'open': Phase([TextTween(p=P(0, 0), char_display=1, start=0.5, dur=1.0, ease=QEasingCurve.OutQuint)]),
                'close': Phase([TextTween(char_display=0, start=0.0, dur=1.0, ease=QEasingCurve.OutQuint)]),
            }
        ),
    ],
    button_defs=[
        *SegmentedButtons(
            p1=P(0.45, 0.03), p2=P(0.95, 0.06), px1=P(0, 0), px2=P(0, 0), event_out=get_event('task_window'), 
            text_def=TextDef(font_size=12.0, fill_color=QColor(255, 255, 255, 255), bold=True),
            segments=[
                Segment(event_delta='', weight=1, label='MAIN'),
                Segment(event_delta='1. Snack Run', weight=1, label='SNK'),
                Segment(event_delta='2. Heist Mission', weight=1, label='HST'),
                Segment(event_delta='3. RoverCooked', weight=1, label='RVC'),
                Segment(event_delta='4. Refreshment Delivery', weight=1, label='DLV'),
                Segment(event_delta='5. Exploration Proposal', weight=1, label='EXP'),
            ],
        ),
    ],
    sub_windows=[
        hardware_fault_window, camera_access_window
    ]
    
)








WINDOW_DEFS = []
WINDOW_DEFS.append(tasks_window)
# WINDOW_DEFS.append(hardware_fault_window)
# WINDOW_DEFS.append(camera_access_window)


register_windows(WINDOW_LAYER, WINDOW_DEFS)
