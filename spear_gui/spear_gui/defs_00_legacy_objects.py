# This file is kept as a reference from testing objects to work.
# Note that this file will not be maintained, so most objects in here may not work correctly.

from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple

from PySide6.QtCore import Qt, QEasingCurve
from PySide6.QtGui  import QColor

from spear_gui.overlay_system import (
    P, Reset, Phase, expand_defs,
    PolygonDef, PolygonTween, RectDef, RectTween, # PolygonDef
    ArcDef, # ArcDef
    TextDef, TextTween, TextBlock, DataTable, # TextDef
    SliderDef, # SliderDef
    ButtonDef, SegmentedButtons, Segment, SevenSegmentDisplay, # ButtonDef
    TextboxDef,
    GraphDef, SeriesDef, # GraphDef
    PieDef, # PieDef
    WindowDef, WindowTween, # WindowDef
    EventDef, EventListener, # EventDef
    GradientDef, GradientStop, GradientTween, _AnimatedGradient, register_gradient, # GradientDef

    P_OPEN, P_CLOSE, P_HOVER, P_UNHOVER, P_CLICK, P_RELEASE, P_SET, P_ALWAYS,
    SYS_FPS, SYS_FRAME_TIME, SYS_MOUSE, SYS_MOUSE_X, SYS_MOUSE_Y,
    get_spawn_event, GROUP_EVENT, STATIC, get_spawn_mouse_norm
)

# ──────────────────────── EVENT DEFS ────────────────────────

MAIN_EVENT_DEFS = [
    EventDef(name='graph_steps', value=4),
    EventDef(name='graph_stack', value=True),
    EventDef(name='graph_time',  value=10.0),
    EventDef(name='window1_phase', value='open'),
    EventDef(name='window2_phase', value='open'),
    EventDef(name='window3_phase', value='open'),
    EventDef(name='window4_phase', value='open'),
    EventDef(name='window5_phase', value='close'),

    EventDef(name='random_phase', value='big'),
    EventDef(name='test_event', value='test_value4'),
    EventDef(name='square_x', value=0),
    EventDef(name='square_y', value=0),
    EventDef(name='textbox_test_value', value='nothing'),
    EventDef(name='new_log', value=False),
    EventDef(name='spawn_dot', value=False),
    EventDef(name='dot_x',     value=0.5),
    EventDef(name='dot_y',     value=0.5),


    EventDef(name='sub_sample_pulse', value=None),
    EventDef(name='sub_sample_pulse2', value=None),


    # MAP
    EventDef(name='pos_x',     value=-112.710534),
    EventDef(name='pos_y',     value=51.465185),
    EventDef(name='map_pos_x',     value=0),
    EventDef(name='map_pos_y',     value=0),
    EventDef(name='spawn_marker',     value=False),
    EventDef(name='map_prompt_phase', value='close'),
    EventDef(name='map_zoom',     value=1),
    EventDef(name='map_marker_x',     value=0),
    EventDef(name='map_marker_y',     value=0),

   

    # HEIST MISSION VALUES
    EventDef(name='wire_window_phase', value='open'),
    EventDef(name='wire_count', value=None),
    # WIRE COUNT = 3
    EventDef(name='wire_red_count', value=None),
    EventDef(name='wire_yellow_count', value=None),
    EventDef(name='wire_blue_count', value=None),
    EventDef(name='wire_white_count', value=None),
    EventDef(name='wire_black_count', value=None),
    EventDef(name='wire_last_color', value=None),

    # 3 WIRES - RED /        / BLUE / WHITE
    EventDef(name='wire_c3-1', value=False), # 0 RED
    EventDef(name='wire_c3-2', value=False), # LAST = WHITE
    EventDef(name='wire_c3-3', value=False), # ≥2 BLUE

    # 4 WIRES - RED / YELLOW / BLUE /       /
    EventDef(name='wire_c4-1', value=False), # ≥2 RED
    EventDef(name='wire_c4-2', value=False), # LAST = YELLOW + 0 RED
    EventDef(name='wire_c4-3', value=False), # 1 BLUE
    EventDef(name='wire_c4-4', value=False), # ≥2 YELLOW

    # 5 WIRES - RED / YELLOW /      /       / BLACK
    EventDef(name='wire_c5-1', value=False), # LAST = BLACK
    EventDef(name='wire_c5-2', value=False), # 1 RED + ≥2 YELLOW
    EventDef(name='wire_c5-3', value=False), # 0 BLACK

    # 6 WIRES - RED / YELLOW /      / WHITE
    EventDef(name='wire_c6-1', value=False), # 0 YELLOW
    EventDef(name='wire_c6-2', value=False), # 1 YELLOW + ≥2 WHITE
    EventDef(name='wire_c6-3', value=False), # 0 RED

    # HARDWARE FAULT
    EventDef(name='hardware_fault_byte1-1', value='0b00000000'),
    EventDef(name='hardware_fault_byte2-1', value='0b00000000'),
    EventDef(name='hardware_fault_byte3-1', value='0b00000000'),
    EventDef(name='hardware_fault_byte4-1', value='0b00000000'),
    EventDef(name='hardware_fault_byte1-2', value='0b00000000'),
    EventDef(name='hardware_fault_byte2-2', value='0b00000000'),
    EventDef(name='hardware_fault_byte3-2', value='0b00000000'),
    EventDef(name='hardware_fault_byte4-2', value='0b00000000'),

    EventDef(name='hardware_fault_xor1', value='0b00000000'),
    EventDef(name='hardware_fault_xor2', value='0b00000000'),
    EventDef(name='hardware_fault_xor3', value='0b00000000'),
    EventDef(name='hardware_fault_xor4', value='0b00000000'),

    EventDef(name='hardware_fault_char1', value=''),
    EventDef(name='hardware_fault_char2', value=''),
    EventDef(name='hardware_fault_char3', value=''),
    EventDef(name='hardware_fault_char4', value=''),

]

_ev = {e.name: e for e in MAIN_EVENT_DEFS}

MAIN_POLYGON_DEFS = expand_defs([])
MAIN_GRAPH_DEFS   = []
MAIN_PIE_DEFS     = []
MAIN_TEXT_DEFS    = []

# ──────────────────────── WINDOW DEFS ────────────────────────

MAIN_GRADIENT_DEFS = [
    GradientDef(
        name='launch_text_outline1', p1=P(0.5, 0.5), p2=P(0.5, 0.5), px1=P(-300, -150), px2=P(300, 150), target='outline', stops=[
            GradientStop(0.0, QColor(50, 50, 50, 255)),
            GradientStop(0.5, QColor(50, 50, 50, 255)),
            GradientStop(0.5001, QColor(50, 50, 50, 0)),
        ],
    ),
    GradientDef(
        name='launch_text_outline2', p1=P(0.5, 0.5), p2=P(0.5, 0.5), px1=P(-300, -150), px2=P(300, 150), target='outline', stops=[
            GradientStop(0.0, QColor(50, 50, 50, 0)),
            GradientStop(0.5, QColor(50, 50, 50, 0)),
            GradientStop(0.5001, QColor(50, 50, 50, 255)),
        ],
    ),



    GradientDef(
        name='sub_sample_pulse', p1=P(0.9, 0.5), p2=P(0.9, 0.5), px1=P(0, 0), px2=P(-60, 0), target='fill', phase_event=_ev['sub_sample_pulse'],
        stops=[GradientStop(0.0, QColor(0, 255, 0, 255)), GradientStop(1.0, QColor(0, 0, 0, 255))], 
        phases={'pulse': Phase([
            GradientTween(stops=[GradientStop(0.0, QColor(0, 100, 0, 255)), GradientStop(1.0, QColor(0, 255, 0, 0))], start=0, dur=0, ease=QEasingCurve.OutQuint),
            GradientTween(stops=[GradientStop(0.0, QColor(0, 0, 0, 0)), GradientStop(1.0, QColor(0, 0, 0, 0))], start=0, dur=1, ease=QEasingCurve.OutQuint),
            ])
        }
    ),

    GradientDef(
        name='sub_sample_pulse2', p1=P(0.9, 0.7), p2=P(0.9, 0.7), px1=P(0, 0), px2=P(-60, 0), target='fill', phase_event=_ev['sub_sample_pulse2'],
        stops=[GradientStop(0.0, QColor(0, 255, 0, 255)), GradientStop(1.0, QColor(0, 0, 0, 255))], 
        phases={'pulse': Phase([
            GradientTween(stops=[GradientStop(0.0, QColor(0, 100, 0, 255)), GradientStop(1.0, QColor(0, 255, 0, 0))], start=0, dur=0, ease=QEasingCurve.OutQuint),
            GradientTween(stops=[GradientStop(0.0, QColor(0, 0, 0, 0)), GradientStop(1.0, QColor(0, 0, 0, 0))], start=0, dur=1, ease=QEasingCurve.OutQuint),
            ])
        }
    ),
]

_gd = {g.name: g for g in MAIN_GRADIENT_DEFS}
for g in _gd.values():
    g._animated = _AnimatedGradient(g)
    register_gradient(g.name, g)

# all DataTables shared the same phases so this is a bandaid solution for simplifying for now
data_table_phase = {
    P_OPEN:  Phase([TextTween(char_display=1.0, color=QColor(200, 220, 255, 220), start=0.6, dur=0.7, ease=QEasingCurve.OutQuint)], line_delay=0.05),
    P_CLOSE: Phase([TextTween(char_display=0.0, color=QColor(200, 220, 255,   0), start=0.0, dur=0.5, ease=QEasingCurve.OutQuint)], line_delay=0.00),
}


MAIN_WINDOW_DEFS = [


    WindowDef(
        p1=P(0.0, 0.0), p2=P(1.0, 1.0),
        polygon_defs=[
            # PolygonDef(p=[P(0, 0), P(0, 0), P(0, 1), P(0, 1)], px=[P(0, 0), P(50, 50), P(50, -50), P(0, 0)], fill_color=QColor(255, 255, 255, 255),
            # pos_fn=lambda: [P(0, 0), P(SYS_MOUSE_X.value / 10, SYS_MOUSE_Y.value / 10), P(SYS_MOUSE_X.value / 10, SYS_MOUSE_Y.value / 10), P(0, 0)]),
            PolygonDef(p=[P(0.5, 0.5)]*4, px=[P(-100, -5), P(100, -5), P(100, 5), P(-100, 5)], fill_color=QColor(255, 255, 255, 255), rot_center_p=P(0.5, 0.5), rot_target_p=P(0.5, 0.5), rot_angle_initial=0, phases={
                'open': Phase([PolygonTween(rot_angle=700, start=0, dur=5.0, ease=QEasingCurve.OutQuint)])
            }),
        ],
        text_defs=[
            # TextDef(
            #     p=P(0.5, 0.5), px=P(-100, -150), text='LAUNCHING', bold=True, italic=True, v_align=1, font_size=100, color=QColor(255,255,255,0), outline_width=2,
            #     gradient=_gd['launch_text_outline1'],
            # ),
            TextDef(
                p=P(0.5, 0.5), px=P(-50, 100), text='SPEAR', bold=True, italic=True, font_size=400, color=QColor(255,255,255,0), outline_width=4,
                gradient=_gd['launch_text_outline1'], phases={
                    'open': Phase([TextTween(px=P(0, 0), start=0, dur=1.0, ease=QEasingCurve.OutBack)])
                }
            ),
            TextDef(
                p=P(0.5, 0.5), px=P(50, -100), text='SPEAR', bold=True, italic=True, font_size=400, color=QColor(255,255,255,0), outline_width=4,
                gradient=_gd['launch_text_outline2'], phases={
                    'open': Phase([TextTween(px=P(0, 0), start=0, dur=1.0, ease=QEasingCurve.OutBack)])
                }
            ),
        ],
        sub_windows=[
            WindowDef(p1=P(0.50, 0.00), p2=P(0.60, 0.10),
                draggable=True, scalable=True,
                polygon_defs=[
                    RectDef(p1=P(0, 0), p2=P(1, 1),
                        fill_color=QColor(255, 255, 255, 50),
                        outline_color=QColor(255, 255, 255, 255),
                        line_width=2,
                    ),
                ],
                text_defs=[
                    TextDef(p=P(0.5, 0.5), text='LOGGER', font_size=150.0, bold=True, color=QColor(255, 255, 255, 255), h_align=0.5, v_align=0.5),
                ],
            ),
            WindowDef(p1=P(0.50, 0.10), p2=P(0.60, 0.20),
                draggable=True, scalable=True,
                polygon_defs=[
                    RectDef(p1=P(0, 0), p2=P(1, 1),
                        fill_color=QColor(255, 255, 255, 50),
                        outline_color=QColor(255, 255, 255, 255),
                        line_width=2,
                    ),
                ],
                text_defs=[
                    TextDef(p=P(0.5, 0.5), text='MOTOR INFOMATION', font_size=150.0, bold=True, color=QColor(255, 255, 255, 255), h_align=0.5, v_align=0.5),
                ],
            ),
            WindowDef(p1=P(0.50, 0.20), p2=P(0.60, 0.30),
                draggable=True, scalable=True,
                polygon_defs=[
                    RectDef(p1=P(0, 0), p2=P(1, 1),
                        fill_color=QColor(255, 255, 255, 50),
                        outline_color=QColor(255, 255, 255, 255),
                        line_width=2,
                    ),
                ],
                text_defs=[
                    TextDef(p=P(0.5, 0.5), text='ARM INFOMATION', font_size=150.0, bold=True, color=QColor(255, 255, 255, 255), h_align=0.5, v_align=0.5),
                ],
            ),
            WindowDef(p1=P(0.50, 0.30), p2=P(0.60, 0.40),
                draggable=True, scalable=True,
                polygon_defs=[
                    RectDef(p1=P(0, 0), p2=P(1, 1),
                        fill_color=QColor(255, 255, 255, 50),
                        outline_color=QColor(255, 255, 255, 255),
                        line_width=2,
                    ),
                ],
                text_defs=[
                    TextDef(p=P(0.5, 0.5), text='ARM VISUAL', font_size=150.0, bold=True, color=QColor(255, 255, 255, 255), h_align=0.5, v_align=0.5),
                ],
            ),
            WindowDef(p1=P(0.50, 0.40), p2=P(0.60, 0.50),
                draggable=True, scalable=True,
                polygon_defs=[
                    RectDef(p1=P(0, 0), p2=P(1, 1),
                        fill_color=QColor(255, 255, 255, 50),
                        outline_color=QColor(255, 255, 255, 255),
                        line_width=2,
                    ),
                ],
                text_defs=[
                    TextDef(p=P(0.5, 0.5), text='TASKS', font_size=150.0, bold=True, color=QColor(255, 255, 255, 255), h_align=0.5, v_align=0.5),
                ],
            ),
            WindowDef(p1=P(0.50, 0.50), p2=P(0.60, 0.60),
                draggable=True, scalable=True,
                polygon_defs=[
                    RectDef(p1=P(0, 0), p2=P(1, 1),
                        fill_color=QColor(255, 255, 255, 50),
                        outline_color=QColor(255, 255, 255, 255),
                        line_width=2,
                    ),
                ],
                text_defs=[
                    TextDef(p=P(0.5, 0.5), text='SCIENCE INFO', font_size=150.0, bold=True, color=QColor(255, 255, 255, 255), h_align=0.5, v_align=0.5),
                ],
            ),
            WindowDef(p1=P(0.50, 0.60), p2=P(0.60, 0.70),
                draggable=True, scalable=True,
                polygon_defs=[
                    RectDef(p1=P(0, 0), p2=P(1, 1),
                        fill_color=QColor(255, 255, 255, 50),
                        outline_color=QColor(255, 255, 255, 255),
                        line_width=2,
                    ),
                ],
                text_defs=[
                    TextDef(p=P(0.5, 0.5), text='JETSON INFO', font_size=150.0, bold=True, color=QColor(255, 255, 255, 255), h_align=0.5, v_align=0.5),
                ],
            ),
            WindowDef(p1=P(0.50, 0.70), p2=P(0.60, 0.80),
                draggable=True, scalable=True,
                polygon_defs=[
                    RectDef(p1=P(0, 0), p2=P(1, 1),
                        fill_color=QColor(255, 255, 255, 50),
                        outline_color=QColor(255, 255, 255, 255),
                        line_width=2,
                    ),
                ],
                text_defs=[
                    TextDef(p=P(0.5, 0.5), text='EXTRA 1', font_size=150.0, bold=True, color=QColor(255, 255, 255, 255), h_align=0.5, v_align=0.5),
                ],
            ),
            WindowDef(p1=P(0.50, 0.80), p2=P(0.60, 0.90),
                draggable=True, scalable=True,
                polygon_defs=[
                    RectDef(p1=P(0, 0), p2=P(1, 1),
                        fill_color=QColor(255, 255, 255, 50),
                        outline_color=QColor(255, 255, 255, 255),
                        line_width=2,
                    ),
                ],
                text_defs=[
                    TextDef(p=P(0.5, 0.5), text='EXTRA 2', font_size=150.0, bold=True, color=QColor(255, 255, 255, 255), h_align=0.5, v_align=0.5),
                ],
            ),
            WindowDef(p1=P(0.50, 0.90), p2=P(0.60, 1.00),
                draggable=True, scalable=True,
                polygon_defs=[
                    RectDef(p1=P(0, 0), p2=P(1, 1),
                        fill_color=QColor(255, 255, 255, 50),
                        outline_color=QColor(255, 255, 255, 255),
                        line_width=2,
                    ),
                ],
                text_defs=[
                    TextDef(p=P(0.5, 0.5), text='EXTRA 3', font_size=150.0, bold=True, color=QColor(255, 255, 255, 255), h_align=0.5, v_align=0.5),
                ],
            ),
        ]

    ),
    WindowDef(
        p1=P(0.0, 0.0), p2=P(1.0, 1.0),
        listener_defs=[
            EventListener(value_fn='pulse', targets=[_ev['sub_sample_pulse']], passthrough=True, wait_for_updates=lambda ctx: ctx['test_value1']['push_count']),
            EventListener(value_fn='pulse', targets=[_ev['sub_sample_pulse2']], passthrough=True, wait_for_updates=lambda ctx: ctx['test_value8']['push_count']),
        ],
        polygon_defs=[
            PolygonDef(p=[P(0.9, 0.5)]*4, px=[P(0, -15), P(0, 15), P(-60, 15), P(-60, -15)], gradient=_gd['sub_sample_pulse'], phase_override=lambda: _ev['sub_sample_pulse'].value),

            PolygonDef(p=[P(0.9, 0.5)]*6, px=[P(-3, 12), P(-3, -12), P(0, -15), P(3, -12), P(3, 12), P(0, 15)], fill_color=QColor(255, 0, 0, 255), phase_override=lambda: _ev['sub_sample_pulse'].value, phases={
                'pulse': Phase([
                        PolygonTween(fill_color=QColor(0, 255, 0, 255), start=0, dur=0.0, ease=QEasingCurve.OutQuint),
                        PolygonTween(fill_color=QColor(0, 100, 0, 255), start=0, dur=1.0, ease=QEasingCurve.OutQuint),
                    ])
                }
            ),

            PolygonDef(p=[P(0.9, 0.7)]*4, px=[P(0, -15), P(0, 15), P(-60, 15), P(-60, -15)], gradient=_gd['sub_sample_pulse2'], phase_override=lambda: _ev['sub_sample_pulse2'].value),

            PolygonDef(p=[P(0.9, 0.7)]*6, px=[P(-3, 12), P(-3, -12), P(0, -15), P(3, -12), P(3, 12), P(0, 15)], fill_color=QColor(255, 0, 0, 255), phase_override=lambda: _ev['sub_sample_pulse'].value, phases={
                'pulse': Phase([
                        PolygonTween(fill_color=QColor(0, 255, 0, 255), start=0, dur=0.0, ease=QEasingCurve.OutQuint),
                        PolygonTween(fill_color=QColor(0, 100, 0, 255), start=0, dur=1.0, ease=QEasingCurve.OutQuint),
                    ])
                }
            )
        ],
        arc_defs=[
            ArcDef(center_p=P(0.5, 0.5), inner_p=P(0.55, 0.5), outer_p=P(0.6, 0.5), angle_start=0, angle_end=45/4)
        ],
        text_defs=[
            TextDef(p=P(0.9, 0.5), px=P(7, 0), h_align=0, text = 'test_value1', uniform_scale=False),
            TextDef(p=P(0.9, 0.5), px=P(-7, 0), h_align=1, text_fn = lambda ctx: ctx['test_value1']['push_count'], uniform_scale=False),
            TextDef(p=P(0.9, 0.7), px=P(7, 0), h_align=0, text = 'test_value8', uniform_scale=False),
            TextDef(p=P(0.9, 0.7), px=P(-7, 0), h_align=1, text_fn = lambda ctx: ctx['test_value8']['push_count'], uniform_scale=False),
        ]
    ),

    # Map
    WindowDef(
        p1=P(0.0, 0.0), p2=P(0.0, 0.0), px1=P(0, 0), px2=P(400, 400),
        listener_defs=[
            EventListener(value_fn=lambda ctx: _ev['pos_x'].value, targets=[_ev['map_pos_x']], passthrough=True, transform=lambda v: (v + 112.710534) / 0.0000001),
            EventListener(value_fn=lambda ctx: _ev['pos_y'].value, targets=[_ev['map_pos_y']], passthrough=True, transform=lambda v: (v - 51.465185) / 0.0000001),
        ],
        polygon_defs=[
            RectDef(p1=P(0.0, 0.0), p2=P(1.0, 1.0), fill_color=QColor(255, 255, 255, 10), outline_color=QColor(255, 255, 255, 255), line_width=1),
            PolygonDef(p=[P(0.5, 0.5)]*4, px=[P(-10, 0), P(0, -10), P(10, 0), P(0, 10)], fill_color=QColor(200, 200, 255, 255)),
        ],
        text_defs=[
            TextDef(p=P(0.5, 0), px=P(0, 2), font_size=20, v_align=0, text='N', uniform_scale=False),
            TextDef(p=P(0.5, 1), px=P(0, -2), font_size=20, v_align=1, text='S', uniform_scale=False),
            TextDef(p=P(0, 0.5), px=P(2, 0), font_size=20, h_align=0, text='W', uniform_scale=False),
            TextDef(p=P(1, 0.5), px=P(-2, 2), font_size=20, h_align=1, text='E', uniform_scale=False),
            TextDef(p=P(0, 1), px=P(2, -2), text='(<#>, <#>)', font_size=10, h_align=0, v_align=1, uniform_scale=False,
                text_fn=lambda ctx: [f"{_ev['map_pos_x'].value:.7f}", f"{_ev['map_pos_y'].value:.7f}"],
            ),
        ],
        button_defs=[
            ButtonDef(key=Qt.Key_Up, action='increment', continuous_update=True, event_out=_ev['pos_y'], event_delta=0.00001),
            ButtonDef(key=Qt.Key_Down, action='increment', continuous_update=True, event_out=_ev['pos_y'], event_delta=-0.00001),
            ButtonDef(key=Qt.Key_Left, action='increment', continuous_update=True, event_out=_ev['pos_x'], event_delta=0.00001),
            ButtonDef(key=Qt.Key_Right, action='increment', continuous_update=True, event_out=_ev['pos_x'], event_delta=-0.00001),
            ButtonDef(poly_def=RectDef(p1=P(0, 0), p2=P(1, 1)), key=Qt.Key_P, mandatory_keys=Qt.Key_Shift, action='set', event_out=_ev['spawn_marker'], event_delta=True, invisible=True),
        ],
        slider_defs=[
            # SliderDef(p=P(0.5, 1), px=P(70, -15), length=0.5, length_px=-85, event_out=_ev['map_zoom'], min_val=0.1, max_val=2.9, step=0.1, label='ZOOM', unit='', decimals=1)
        ],
        sub_windows=[
            WindowDef(
                p1=P(0, 0), p2=P(1, 1),
                polygon_defs=[
                    PolygonDef(p=[P(STATIC(0), STATIC(1))]*4, px=[P(-10, 0), P(0, -10), P(10, 0), P(0, 10)], fill_color=QColor(255, 200, 200, 255),
                        pos_fn=lambda: P(_ev['map_pos_x'].value, _ev['map_pos_y'].value)
                    ),
                ],
                text_defs=[
                    TextDef(p=P(STATIC(0), STATIC(1)), px=P(0, -10), font_size=10, v_align=1, text='MARKER', uniform_scale=False, color=QColor(255, 200, 200, 255),
                        pos_fn=lambda: P(_ev['map_pos_x'].value, _ev['map_pos_y'].value)
                    ),
                ],
                button_defs=[
                    ButtonDef(poly_def=PolygonDef(p=[P(STATIC(0), STATIC(1))]*4, px=[P(-10, 0), P(0, -10), P(10, 0), P(0, 10)], fill_color=QColor(255, 200, 200, 255),
                        pos_fn=lambda: P(_ev['map_pos_x'].value / 2, _ev['map_pos_y'].value / 2)
                    ),
                        action='set',
                        event_out=GROUP_EVENT,
                        event_delta=1,
                    )
                ],
                spawn_event=_ev['spawn_marker'],
                spawn_event_group='marker',
                phase_event=GROUP_EVENT,
                spawn_delete_threshold=1,
                spawn_static_values=[
                    lambda: get_spawn_mouse_norm().x - _ev['map_pos_x'].value / 400,
                    lambda: get_spawn_mouse_norm().y - _ev['map_pos_y'].value / 400,
                ],
            ),
            # WindowDef(
            #     p1=P(0, 0.25), p2=P(1, 0.75),
            #     phase_event=_ev['map_prompt_phase'],
            #     polygon_defs=[
            #         RectDef(p1=P(0, 0), p2=P(1, 1), fill_color=QColor(255, 255, 255, 0), phases={
            #             'open': Phase([RectTween(fill_color=QColor(255, 255, 255, 100), start=0, dur=1.0, ease=QEasingCurve.OutQuint)]),
            #             'close': Phase([RectTween(fill_color=QColor(255, 255, 255, 0), start=0, dur=1.0, ease=QEasingCurve.OutQuint)])
            #         }),
            #     ],
            #     text_defs=[
            #         TextDef(x=0.5, y=0, font_size=10, v_align=0, text='CREATING MARKER', uniform_scale=False, color=QColor(255, 255, 255, 0), phases={
            #             'open': Phase([TextTween(color=QColor(255, 255, 255, 255), start=0, dur=1.0, ease=QEasingCurve.OutQuint)]),
            #             'close': Phase([TextTween(color=QColor(255, 255, 255, 0), start=0, dur=1.0, ease=QEasingCurve.OutQuint)])
            #         }),
            #     ],
            # )
        ]
    ),



    

    # WindowDef(
    #     p1=P(0.0, 0.0), p2=P(1.0, 1.0),
    #     phase_event=_ev['random_phase'],
    #     listener_defs=[
    #         EventListener(value_fn=lambda ctx: ctx['test_value1']['latest'], targets=[_ev['random_phase']], conditions=[lambda v: v > 5], values=['big', 'small']),
    #     ],
    #     polygon_defs=[
    #         PolygonDef(points=[P(0.0, 0.0), P(0.1, 0.0), P(0.1, 0.1), P(0.0, 0.1)], fill_color=QColor(20, 20, 20, 255), phases={
    #                 'big':  Phase([PolygonTween(fill_color=QColor(20, 255, 20, 255), start=0.0, dur=0.5, ease=QEasingCurve.OutQuint)]),
    #                 'small':  Phase([PolygonTween(fill_color=QColor(255, 20, 20, 255), start=0.0, dur=0.5, ease=QEasingCurve.OutQuint)])}),
    #     ]
    # ),

    # WindowDef(
    #     p1=P(0.50, 0.00), p2=P(1.00, 0.50),
    #     phase_event=_ev['window3_phase'],
    #     phases={
    #         'phase1':  Phase([WindowTween(p1=P(0.00, 0.50), p2=P(0.50, 1.00), start=0.00, dur=1.00, ease=QEasingCurve.OutQuint)]),
    #         'phase2': Phase([WindowTween(p1=P(0.00, 0.00), p2=P(0.30, 0.30), start=0.00, dur=1.00, ease=QEasingCurve.OutQuint)]),
    #         'phase3':  Phase([WindowTween(p1=P(0.00, 0.00), p2=P(1.00, 0.25), start=0.00, dur=1.00, ease=QEasingCurve.OutQuint)]),
    #     },
    #     polygon_defs=[
    #         RectDef(p1=P(0.00, 0.00), p2=P(1.00, 1.00), fill_color=QColor(255, 255, 255, 50)),
    #         RectDef(p1=P(0.50, 0.50), p2=P(0.50, 0.50), px1=P(-5, -5), px2=P(5, 5), fill_color=QColor(255, 0, 0, 255)),
    #         RectDef(p1=P(0.20, 0.20), p2=P(0.40, 0.40), fill_color=QColor(0, 255, 0, 255)),
    #         RectDef(p1=P(0.60, 0.20), p2=P(0.80, 0.40), fill_color=QColor(0, 0, 0, 0), outline_color=QColor(0, 0, 255, 255), line_width=2),
    #         PolygonDef(points=[P(0.50, 0.60), P(0.30, 0.80), P(0.70, 0.80)], fill_color=QColor(255, 255, 0, 255))
    #     ],
    #     text_defs=[
    #         TextDef(x=0.50, y=0.00, text='This is a single text', font_size=9.0, color=QColor(255, 255, 255, 255), h_align=0.5, v_align=0.0),
    #         TextDef(x=0.50, y=0.10, text='Test Value 1: <#>', font_size=9.0, color=QColor(255, 255, 255, 255), h_align=0.5, v_align=0.0,
    #         text_fn=lambda ctx: (f"{ctx['test_value1']['latest']:.4f}" if ctx and ctx['test_value1']['latest'] is not None else "-")),
    #         *TextBlock(x=0.00, y=0.90, text='This is a block of text\nThis appears in another line.\nThis appears on the last line.', font_size=9.0, color=QColor(255, 255, 255, 255), h_align=0.0, v_align=0.5)
    #     ],
    # ),


    # POWER INFOMATION
    WindowDef(
        p1=P(0.00, 0.75), p2=P(0.25, 1.00),
        phase_event=_ev['window1_phase'],
        phases={
            'phase1':  Phase([WindowTween(p1=P(0.00, 0.50), p2=P(0.50, 1.00), start=0.00, dur=1.00, ease=QEasingCurve.OutQuint)]),
            'phase2': Phase([WindowTween(p1=P(0.00, 0.00), p2=P(0.30, 0.30), start=0.00, dur=1.00, ease=QEasingCurve.OutQuint)]),
            'phase3':  Phase([WindowTween(p1=P(0.00, 0.00), p2=P(1.00, 0.25), start=0.00, dur=1.00, ease=QEasingCurve.OutQuint)]),
        },
        polygon_defs=[
            PolygonDef(
                p=[P(0.0, 0.0), P(1.0, 0.0), P(1.0, 1.0), P(0.0, 1.0)],
                fill_color=QColor(20, 20, 20, 255),
                phases={
                    'phase1':  Phase([PolygonTween(p=[P(0.0,0.0), P(1.0,0.0), P(1.0,1.0), P(0.0,1.0)],
                                    fill_color=QColor(20, 20, 20, 255),
                                    start=0.0, dur=1.0, ease=QEasingCurve.OutQuint)]),
                    'phase2': Phase([PolygonTween(p=[P(0.0,0.0), P(1.0,0.0), P(1.0,1.0), P(0.0,1.0)],
                                    fill_color=QColor(40, 0, 40, 255),
                                    start=0.0, dur=1.0, ease=QEasingCurve.InQuint)]),
                },
            ),
        ],
        text_defs=[
            TextDef(p=P(0.50, 0.00), text='POWER CONSUMPTION', font_size=9.0, color=QColor(255, 255, 255, 0), h_align=0.5, v_align=0, uniform_scale=False,
                phases={
                    'open':  Phase([TextTween(color=QColor(255, 255, 255, 255), start=0.00, dur=1.00, ease=QEasingCurve.OutQuint)]),
                    'close': Phase([TextTween(color=QColor(255, 255, 255, 0), start=0.00, dur=1.00, ease=QEasingCurve.OutQuint)]),
                }),
            TextDef(p=P(1.00, 0.00), text='77%', font_size=9.0, color=QColor(255, 255, 255, 0), h_align=1, v_align=0, uniform_scale=False,
                phases={
                    'open':  Phase([TextTween(color=QColor(255, 255, 255, 255), start=0.00, dur=1.00, ease=QEasingCurve.OutQuint)]),
                    'close': Phase([TextTween(color=QColor(255, 255, 255, 0), start=0.00, dur=1.00, ease=QEasingCurve.OutQuint)]),
                }),
            TextDef(p=P(0.50, 0.90), text='kWh: <#>', font_size=9.0, color=QColor(255, 255, 255, 255), h_align=0.5, v_align=1.0, uniform_scale=False,
                text_fn=lambda ctx: (
                    f"{sum(ctx[f'test_value{i}']['average'] for i in range(1, 10)):.4f}"
                    if ctx and ctx['test_value1']['average'] is not None else "-"
                ),
                phases={
                    'open':  Phase([TextTween(color=QColor(255, 255, 255, 255), start=0.00, dur=1.00, ease=QEasingCurve.OutQuint)]),
                    'close': Phase([TextTween(color=QColor(255, 255, 255, 0), start=0.00, dur=1.00, ease=QEasingCurve.OutQuint)]),
                }),
        ],
        graph_defs=[
            GraphDef(
                p1=P(0.00, 0.05), p2=P(1.00, 0.85),
                series=[
                    SeriesDef(value_fn=lambda ctx: ctx['test_value1']['latest'], color=QColor(255, 106, 106, 255), line_width=1.0, fill_opacity=0.08),
                    SeriesDef(value_fn=lambda ctx: ctx['test_value2']['latest'], color=QColor(255, 111, 151, 255), line_width=1.0, fill_opacity=0.08),
                    SeriesDef(value_fn=lambda ctx: ctx['test_value3']['latest'], color=QColor(255, 126, 192, 255), line_width=1.0, fill_opacity=0.08),
                    SeriesDef(value_fn=lambda ctx: ctx['test_value4']['latest'], color=QColor(238, 145, 227, 255), line_width=1.0, fill_opacity=0.08),
                    SeriesDef(value_fn=lambda ctx: ctx['test_value5']['latest'], color=QColor(214, 165, 252, 255), line_width=1.0, fill_opacity=0.08),
                    SeriesDef(value_fn=lambda ctx: ctx['test_value6']['latest'], color=QColor(187, 184, 255, 255), line_width=1.0, fill_opacity=0.08),
                    SeriesDef(value_fn=lambda ctx: ctx['test_value7']['latest'], color=QColor(164, 200, 255, 255), line_width=1.0, fill_opacity=0.08),
                    SeriesDef(value_fn=lambda ctx: ctx['test_value8']['latest'], color=QColor(150, 213, 255, 255), line_width=1.0, fill_opacity=0.08),
                    SeriesDef(value_fn=lambda ctx: ctx['test_value9']['latest'], color=QColor(149, 224, 255, 255), line_width=1.0, fill_opacity=0.08),
                ],
                max_time=lambda: float(_ev['graph_time'].value),
                value_range=(0.0, 100.0),
                value_color=QColor(255, 255, 255, 255),
                ease_dur=0.3,
                ease_type=QEasingCurve.OutQuint,
                dynamic_scale=5.0,
                show_minmax = True,
                show_step = True,
                step_count = lambda: int(_ev['graph_steps'].value),
                label_align='left',
                stack=lambda: bool(_ev['graph_stack'].value),
                update_interval=1,
            ),
        ],
        pie_defs=[
            PieDef(
                p1=P(0.00, 0.93), p2=P(1.00, 0.95),
                names=[''] * 9,
                value_fns=[lambda ctx, i=i: ctx[f'test_value{i+1}']['latest'] for i in range(9)],
                colors=[QColor(255,106,106), QColor(255,111,151), QColor(255,126,192),
                        QColor(238,145,227), QColor(214,165,252), QColor(187,184,255),
                        QColor(164,200,255), QColor(150,213,255), QColor(149,224,255)],
                border_width=1.0, fill_opacity=0.1, direction='horizontal',
                size_label=0.0, size_name=9.0, ease_dur=0.4, ease_type=QEasingCurve.OutQuint,
            ),
            PieDef(
                p1=P(0.00, 0.95), p2=P(1.00, 1.00),
                names=[''] * 9,
                value_fns=[lambda ctx, i=i: ctx[f'test_value{i+1}']['average'] for i in range(9)],
                colors=[QColor(255,106,106), QColor(255,111,151), QColor(255,126,192),
                        QColor(238,145,227), QColor(214,165,252), QColor(187,184,255),
                        QColor(164,200,255), QColor(150,213,255), QColor(149,224,255)],
                border_width=1.0, fill_opacity=0.1, direction='horizontal',
                size_label=9.0, size_name=9.0, ease_dur=0.4, ease_type=QEasingCurve.OutQuint,
            ),
        ],
    ),
    
    # LOGGER
    WindowDef(
        p1=P(0.25, 0.50), p2=P(0.75, 1.00),
        phase_event=_ev['window2_phase'],
        textbox_defs=[
                TextboxDef(poly_def=RectDef(p1=P(0, 1), p2=P(1, 1), px1=P(0, -20), fill_color=QColor(0, 0, 0, 255), outline_color=QColor(255, 255, 255, 255), line_width=1), text_def=TextDef(p=P(0, 1), px=P(4, -15), h_align=0, font_size=15, color=QColor(255, 255, 255, 255), uniform_scale=False), event_out = _ev['textbox_test_value']),
        ],
        sub_windows=[
            WindowDef(
                p1=P(0, 1), p2=P(1, 1),
                spawn_event=_ev['new_log'],
                spawn_event_group='log',
                spawn_tick_increment=True,
                spawn_delete_threshold=6,
                spawn_limit=10,
                phase_event=GROUP_EVENT,                          # inject group_ev per instance
                phase_fn=lambda v: str(int(v)) if int(v) > 0 else 'open',
                phases={
                    P_OPEN:  Phase([WindowTween(px1=P(0, -40), px2=P(0, -20), start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
                    '1':  Phase([WindowTween(px1=P(0, -60), px2=P(0, -40), start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
                    '2':  Phase([WindowTween(px1=P(0, -80), px2=P(0, -60), start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
                    '3':  Phase([WindowTween(px1=P(0, -100), px2=P(0, -80), start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
                    '4':  Phase([WindowTween(px1=P(0, -120), px2=P(0, -100), start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
                    '5':  Phase([WindowTween(px1=P(0, -140), px2=P(0, -120), start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
                    P_CLOSE:  Phase([WindowTween(px1=P(0, -160), px2=P(0, -140), start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
                },
                text_defs=[
                    TextDef(
                        p=P(0, 0.5),
                        text='log entry',
                        font_size=15.0,
                        color=QColor(255, 255, 255, 200),
                        h_align=0.0, v_align=0.5,
                        text_fn=_ev['textbox_test_value'], uniform_scale=False,
                    )
                ],
            ),
        ]
    ),


    # WindowDef(
    #     p1=P(0.50, 0.50), p2=P(1.00, 1.00),
    #     phase_event=_ev['window2_phase'],
    #     text_defs=[
    #         TextDef(x=0.50, y=0.10, text='Number: <#>', font_size=9.0, color=QColor(255, 255, 255, 255), h_align=0.5, v_align=0.0,
    #         text_fn=lambda ctx: _ev['graph_steps'].value),
    #     ],
    #     slider_defs=[
    #         SliderDef(x=0.20, y=0.40, lx=0.60, attr=AttributeDef(value_fn=lambda ctx: _ev['graph_steps'].value, set_fn  =lambda ctx, v: None, min_val=0, max_val=10, step=1, label='GRAPH STEPS', unit=''), event_out=_ev['graph_steps']),
    #         SliderDef(x=0.20, y=0.60, lx=0.60, attr=AttributeDef(value_fn=lambda ctx: _ev['graph_time'].value, set_fn  =lambda ctx, v: None, min_val=1, max_val=60, step=1, label='GRAPH TIME', unit='s'), event_out=_ev['graph_time']),
    #     ],
    #     button_defs=[
    #         ButtonDef(key=Qt.Key_A, action='increment', event_out=_ev['graph_steps'], event_delta=10),
    #         ButtonDef(
    #             poly=ButtonDiamond(p=P(0.25, 0.25), px=P(0, 0), size=40),
    #             label='+', text_color=QColor(160, 255, 160, 255),
    #             key=Qt.Key_Up, action='increment', event_out=_ev['graph_steps'], event_delta=1,
    #         ),
    #         ButtonDef(
    #             poly=ButtonDiamond(p=P(0.50, 0.25), px=P(0, 0), size=40),
    #             label='−', text_color=QColor(255, 160, 160, 255),
    #             key=Qt.Key_Down, action='increment', event_out=_ev['graph_steps'], event_delta=-1,
    #         ),
    #         ButtonDef(
    #             poly=ButtonDiamond(p=P(0.75, 0.25), px=P(0, 0), size=40),
    #             label='set', text_color=QColor(255, 255, 255, 220),
    #             action='set', event_out=_ev['graph_steps'], event_delta=4,
    #         ),
    #         ButtonDef(
    #             poly=ButtonDiamond(p=P(0.25, 0.75), px=P(0, 0), size=40),
    #             label='1', text_color=QColor(255, 255, 255, 220),
    #             key=Qt.Key_Left, action='set', event_out=_ev['window4_phase'], event_delta='open',
    #         ),
    #         ButtonDef(
    #             poly=ButtonDiamond(p=P(0.50, 0.75), px=P(0, 0), size=40),
    #             label='2', text_color=QColor(255, 255, 255, 220),
    #             key=Qt.Key_Right, action='set', event_out=_ev['window4_phase'], event_delta='close',
    #         ),
    #         ButtonDef(
    #             poly=ButtonDiamond(p=P(0.75, 0.75), px=P(0, 0), size=40),
    #             label='3', text_color=QColor(255, 255, 255, 220),
    #             action='set', event_out=_ev['window4_phase'], event_delta='whwhwhw',
    #         ),
    #     ],
    # ),

    # WindowDef(
    #     p1=P(0.0, 0.0), p2=P(1.0, 1.0),
    #     phase_event=_ev['window4_phase'],
    #     gradient_defs=[WHITE_GRADIENT],
    #     polygon_defs=[

    #         # BOTTOM LEFT BEVEL CORNER
    #         PolygonDef(
    #             points=[P(0, 1), P(0, 1), P(0, 1), P(0, 1)],
    #             px=[P(0, -90), P(10, -90), P(90, -10), P(90, 0)],
    #             fill_color = QColor(255, 255, 255, 0),
    #             outline_color = QColor(100, 100, 100, 255),
    #             line_width = 2,
    #             closed=False,
    #             draw_progress=0,
    #             d_flip=True,
    #             phases={
    #                 P_OPEN: Phase([PolygonTween(draw_progress=1, start=0.0, dur=1.0, ease=QEasingCurve.OutQuint)]),
    #                 P_CLOSE: Phase([Reset()]),
    #             },
    #         ),
    #         PolygonDef(
    #             points=[P(0, 1), P(0, 1), P(0, 1), P(0, 1), P(0, 1), P(0, 1)],
    #             px=[P(3, -88), P(8, -88), P(18, -78), P(15, -78), P(7, -85), P(3, -85)],
    #             fill_color = QColor(255, 255, 255, 0),
    #             phases={
    #                 P_OPEN: Phase([PolygonTween(fill_color=QColor(255, 255, 255, 255), start=1.0, dur=0.5, ease=QEasingCurve.OutQuint)]),
    #                 P_CLOSE: Phase([Reset()]),
    #             },
    #         ),
    #         PolygonDef(
    #             points=[P(0, 1), P(0, 1), P(0, 1), P(0, 1), P(0, 1), P(0, 1)],
    #             px=[P(88, -3), P(88, -8), P(78, -18), P(78, -15), P(85, -7), P(85, -3)],
    #             fill_color = QColor(255, 255, 255, 0),
    #             phases={
    #                 P_OPEN: Phase([PolygonTween(fill_color=QColor(255, 255, 255, 255), start=1.0, dur=0.5, ease=QEasingCurve.OutQuint)]),
    #                 P_CLOSE: Phase([Reset()]),
    #             },
    #         ),
    #         PolygonDef(
    #             points=[P(0, 1), P(0, 1), P(0, 1), P(0, 1)],
    #             px=[P(16, -75), P(19, -75), P(75, -19), P(75, -16)],
    #             fill_color = QColor(255, 255, 255, 0),
    #             phases={
    #                 P_OPEN: Phase([PolygonTween(fill_color=QColor(255, 255, 255, 255), start=1.0, dur=0.5, ease=QEasingCurve.OutQuint)]),
    #                 P_CLOSE: Phase([Reset()]),
    #             },
    #         ),
    #         PolygonDef(
    #             points=[P(0.0, 1.0), P(0.0, 1.0), P(0.0, 1.0), P(0.0, 1.0)],
    #             px=[P(19, -75), P(19, -100), P(100, -19), P(75, -19)],
    #             gradient=WHITE_GRADIENT,
    #             gradient_p1=P(0.0, 1.0), gradient_px1=P(40, -40),
    #             gradient_p2=P(0.0, 1.0), gradient_px2=P(41, -41),
    #             phases={
    #                 P_OPEN: Phase([PolygonTween(gradient_px1=P(49, -49), gradient_px2=P(60, -60), start=1.0, dur=0.5, ease=QEasingCurve.OutQuint)]),
    #                 P_CLOSE: Phase([Reset()]),
    #             },
    #         ),

    #         # BOTTOM LINE
    #         PolygonDef(
    #             points=[P(1, 1), P(0, 1), P(0, 1), P(0, 0)],
    #             px=[P(0, -15), P(95, -15), P(15, -95), P(15, 100)],
    #             fill_color = QColor(255, 255, 255, 0),
    #             outline_color = QColor(100, 100, 100, 255),
    #             line_width = 2,
    #             closed=False,
    #             draw_progress=0,
    #             d_flip=True,
    #             phases={
    #                 P_OPEN: Phase([PolygonTween(draw_progress=1, start=0.0, dur=1.0, ease=QEasingCurve.OutQuint)]),
    #                 P_CLOSE: Phase([Reset()]),
    #             },
    #         ),

    #         RectDef(P(0.40, 0.40), P(0.60, 0.60), fill_color=QColor(255, 255, 255, 255), phases={
    #             P_OPEN: Phase([Reset(),
    #                 RectTween(P(0.20, 0.40), P(0.40, 0.60), start=0.00, dur=2.00, ease=QEasingCurve.OutSine, blend=True),
    #                 RectTween(P(0.00, 0.20), P(0.00, 0.20), start=1.00, dur=0.70, ease=QEasingCurve.OutSine)])}),





    #         # Same gradient, different polygon shape and anchor direction (vertical)
    #         PolygonDef(
    #             points=[P(0.6, 0.2), P(0.9, 0.2), P(0.9, 0.5), P(0.6, 0.5)],
    #             closed=True,
    #             gradient=WHITE_GRADIENT,
    #             gradient_p1=P(0.6, 0.2), gradient_px1=P(0, 0),
    #             gradient_p2=P(0.6, 0.5), gradient_px2=P(0, 0),
    #             phases={},
    #         ),

    #         PolygonDef(
    #             points=[P(0.5, 0.5), P(0.5, 0.5), P(0.5, 0.5), P(0.5, 0.5)],
    #             px=[P(-35, -35), P(-15, -35), P(-15, -15), P(-35, -15)],
    #             closed=True,
    #             fill_color=QColor(100, 150, 255, 180),
    #             phases={
    #                 P_OPEN: Phase([PolygonTween(fill_color=QColor(100, 150, 255, 180), start=0.0, dur=2, ease=QEasingCurve.OutQuint),
    #                 PolygonTween(fill_color=QColor(255, 0, 0, 180), start=2.0, dur=2, ease=QEasingCurve.OutQuint)
    #                 ]),
    #                 P_CLOSE: Phase([PolygonTween(fill_color=QColor(100, 150, 255, 0), start=0.0, dur=0.3, ease=QEasingCurve.InQuint)]),
    #                 'always': Phase(
    #                     tweens=[
    #                         PolygonTween(px=[P(50, 0), P(50, 0), P(50, 0), P(50, 0)], start=0.0, dur=0.5, ease=QEasingCurve.OutQuint),
    #                         PolygonTween(px=[P(50, 50), P(50, 50), P(50, 50), P(50, 50)], start=0.5, dur=0.5, ease=QEasingCurve.OutQuint),
    #                         PolygonTween(px=[P(0, 50), P(0, 50), P(0, 50), P(0, 50)], start=1.0, dur=0.5, ease=QEasingCurve.OutQuint),
    #                         PolygonTween(px=[P(0, 0), P(0, 0), P(0, 0), P(0, 0)], start=1.5, dur=0.5, ease=QEasingCurve.OutQuint),
    #                     ],
    #                     loop=True,
    #                     stop_phases=['close'],
    #                 ),
    #             },
    #         ),
    #         # Fix desync for always phases
    #         PolygonDef(
    #             points=[P(0.5, 0.5), P(0.5, 0.5), P(0.5, 0.5), P(0.5, 0.5)],
    #             px=[P(15, 15), P(35, 15), P(35, 35), P(15, 35)],
    #             closed=True,
    #             fill_color=QColor(255, 150, 255, 180),
    #             phases={
    #                 P_OPEN: Phase([PolygonTween(fill_color=QColor(255, 150, 255, 180), start=0.0, dur=0.4, ease=QEasingCurve.OutQuint)]),
    #                 P_CLOSE: Phase([PolygonTween(fill_color=QColor(255, 150, 255, 90), start=0.0, dur=0.3, ease=QEasingCurve.InQuint)]),
    #                 'always': Phase(
    #                     tweens=[
    #                         PolygonTween(px=[P(-50, 0), P(-50, 0), P(-50, 0), P(-50, 0)], start=0.0, dur=0.5, ease=QEasingCurve.OutQuint),
    #                         PolygonTween(px=[P(-50, -50), P(-50, -50), P(-50, -50), P(-50, -50)], start=0.5, dur=0.5, ease=QEasingCurve.OutQuint),
    #                         PolygonTween(px=[P(0, -50), P(0, -50), P(0, -50), P(0, -50)], start=1.0, dur=0.5, ease=QEasingCurve.OutQuint),
    #                         PolygonTween(px=[P(0, 0), P(0, 0), P(0, 0), P(0, 0)], start=1.5, dur=0.5, ease=QEasingCurve.OutQuint),
    #                     ],
    #                     loop=True,
    #                     stop_phases=['no'],
    #                 ),
    #             },
    #         ),
    #     ],
    #     text_defs=[
    #         TextDef(x=1.00, y=0.50, px=0, py=10, text='TEST TEST TEST TEST TEST TEST TEST TEST TEST', font_size=30.0, color=QColor(255, 255, 255, 127), bold=True, italic=True, h_align=0, v_align=0,
    #             phases={
    #                 P_OPEN: Phase([Reset(), TextTween(x=0.00, start=0, dur=1, ease=QEasingCurve.OutQuint)]),
    #                 P_CLOSE: Phase([TextTween(x=-2.00, start=0, dur=1, ease=QEasingCurve.InQuint)]),
    #                 'always': Phase([
    #                     TextTween(px=-62.2, start=0.0, dur=1, ease=QEasingCurve.InOutQuad),
    #                     TextTween(px=0, start=1, dur=1, ease=QEasingCurve.InOutQuad),
    #                 ], loop=True, stop_phases=['close']),
    #             },
    #         ),
    #         # TextDef(x=0.00, y=0.50, px=0, py=10, text='TEST', font_size=30.0, color=QColor(255, 0, 0, 127), bold=True, italic=True, h_align=0, v_align=0,
    #         # ),
    #         # TextDef(x=0.30, y=0.00, px=0, py=10, text='LAUNCHING SPEAR_GUI', font_size=30.0, char_display=0.0, sub_char_clip=True, backward=True, color=QColor(255, 255, 255, 127), bold=True, italic=True, h_align=0, v_align=0,
    #         #     phases={
    #         #         P_OPEN: Phase([TextTween(x=0.00, px=10, char_display=1.0, color=QColor(255, 255, 255, 255), start=0.0, dur=1.0, ease=QEasingCurve.OutQuint)]),
    #         #         P_CLOSE: Phase([Reset()]),
    #         #     },
    #         # ),
    #         # Make text blending, then use this version
    #         TextDef(x=0.50, y=0.00, px=10, py=10, text='PLACEHOLDER TEXT', font_size=30.0, char_display=0.0, sub_char_clip=True, color=QColor(255, 255, 255, 127), bold=True, italic=True, h_align=0, v_align=0,
    #             phases={
    #                 P_OPEN: Phase([TextTween(char_display=1.0, color=QColor(255, 255, 255, 255), start=0.0, dur=2.5, ease=QEasingCurve.OutQuint, blend=True),
    #                                TextTween(x=-0.50, start=0.0, dur=1.5, ease=QEasingCurve.OutQuint)]),
    #                 P_CLOSE: Phase([Reset()]),
    #             },
    #         ),
    #     ],
    # ),
    # HARDWARE FAULT
    WindowDef(
        p1=P(0.0, 0.0), p2=P(0.5, 1.0),
        listener_defs=[
            EventListener(value_fn=lambda ctx: (_ev['hardware_fault_byte1-1'].value, _ev['hardware_fault_byte1-2'].value), targets=[_ev['hardware_fault_xor1']], passthrough=True, transform=lambda v: f'0b{int(v[0], 2) ^ int(v[1], 2):08b}'),
            EventListener(value_fn=lambda ctx: (_ev['hardware_fault_byte2-1'].value, _ev['hardware_fault_byte2-2'].value), targets=[_ev['hardware_fault_xor2']], passthrough=True, transform=lambda v: f'0b{int(v[0], 2) ^ int(v[1], 2):08b}'),
            EventListener(value_fn=lambda ctx: (_ev['hardware_fault_byte3-1'].value, _ev['hardware_fault_byte3-2'].value), targets=[_ev['hardware_fault_xor3']], passthrough=True, transform=lambda v: f'0b{int(v[0], 2) ^ int(v[1], 2):08b}'),
            EventListener(value_fn=lambda ctx: (_ev['hardware_fault_byte4-1'].value, _ev['hardware_fault_byte4-2'].value), targets=[_ev['hardware_fault_xor4']], passthrough=True, transform=lambda v: f'0b{int(v[0], 2) ^ int(v[1], 2):08b}'),

            EventListener(value_fn=lambda ctx: _ev['hardware_fault_xor1'].value, targets=[_ev['hardware_fault_char1']], passthrough=True, transform=lambda v: chr(int(v, 2)) if 32 <= int(v, 2) <= 126 else ''),
            EventListener(value_fn=lambda ctx: _ev['hardware_fault_xor2'].value, targets=[_ev['hardware_fault_char2']], passthrough=True, transform=lambda v: chr(int(v, 2)) if 32 <= int(v, 2) <= 126 else ''),
            EventListener(value_fn=lambda ctx: _ev['hardware_fault_xor3'].value, targets=[_ev['hardware_fault_char3']], passthrough=True, transform=lambda v: chr(int(v, 2)) if 32 <= int(v, 2) <= 126 else ''),
            EventListener(value_fn=lambda ctx: _ev['hardware_fault_xor4'].value, targets=[_ev['hardware_fault_char4']], passthrough=True, transform=lambda v: chr(int(v, 2)) if 32 <= int(v, 2) <= 126 else ''),
         
         
         
            EventListener(value_fn=lambda ctx: ctx['test_value1']['latest'], targets=[_ev['textbox_test_value']], passthrough=True),
            EventListener(value_fn=True, targets=[_ev['new_log']], passthrough=True, wait_for_updates=_ev['textbox_test_value']),
        ]
        ,
        text_defs=[
            # TextDef(p=P(0.50, 0.80), text='KEY = [<#>]', font_size=32.0, bold=True, color=QColor(171, 151, 247, 255), h_align=0.5, v_align=0.0,
            #     text_fn=lambda ctx: _ev['hardware_fault_char1'].value + _ev['hardware_fault_char2'].value + _ev['hardware_fault_char3'].value + _ev['hardware_fault_char4'].value,
            # ),

            # TextDef(p=P(0.50, 0.85), text='', font_size=32.0, bold=True, color=QColor(171, 151, 247, 255), h_align=0.5, v_align=0.0,
            #     text_fn=lambda ctx: _ev['textbox_test_value'].value,
            # ),

            # TextDef(p=P(0.50, 0.90), text='Value: <#>', font_size=32.0, bold=True, color=QColor(171, 151, 247, 255), h_align=0.5, v_align=0.0,
            #     text_fn=lambda ctx: ctx[_ev['test_event'].value]['latest'],
            # ),
        ],
        polygon_defs=[
            # RectDef(
            #     p1=P(0.5, 0.5), p2=P(0.5, 0.5),
            #     px1=P(-10, -10), px2=P(10, 10),
            #     fill_color=QColor(255, 255, 255, 255),
            #     pos_fn=lambda: P(_ev['square_x'].value, _ev['square_y'].value)
            # ),
        ],
        button_defs=[
            # ButtonDef(key=Qt.Key_W, action='increment', continuous_update=True, event_out=_ev['square_y'], event_delta=-100),
            # ButtonDef(key=Qt.Key_S, action='increment', continuous_update=True, event_out=_ev['square_y'], event_delta=100),
            # ButtonDef(key=Qt.Key_A, action='increment', continuous_update=True, event_out=_ev['square_x'], event_delta=-100),
            # ButtonDef(key=Qt.Key_D, action='increment', continuous_update=True, event_out=_ev['square_x'], event_delta=100),
            # # Row 1
            *SevenSegmentDisplay(p1=P(0.20, 0.19), p2=P(0.32, 0.21), px1=P(0, 0), px2=P(0, 0), event_out=_ev['hardware_fault_byte1-1']),
            *SevenSegmentDisplay(p1=P(0.36, 0.19), p2=P(0.48, 0.21), px1=P(0, 0), px2=P(0, 0), event_out=_ev['hardware_fault_byte2-1']),
            *SevenSegmentDisplay(p1=P(0.52, 0.19), p2=P(0.64, 0.21), px1=P(0, 0), px2=P(0, 0), event_out=_ev['hardware_fault_byte3-1']),
            *SevenSegmentDisplay(p1=P(0.68, 0.19), p2=P(0.80, 0.21), px1=P(0, 0), px2=P(0, 0), event_out=_ev['hardware_fault_byte4-1']),
            # Row 2
            *SevenSegmentDisplay(p1=P(0.20, 0.49), p2=P(0.32, 0.51), px1=P(0, 0), px2=P(0, 0), event_out=_ev['hardware_fault_byte1-2']),
            *SevenSegmentDisplay(p1=P(0.36, 0.49), p2=P(0.48, 0.51), px1=P(0, 0), px2=P(0, 0), event_out=_ev['hardware_fault_byte2-2']),
            *SevenSegmentDisplay(p1=P(0.52, 0.49), p2=P(0.64, 0.51), px1=P(0, 0), px2=P(0, 0), event_out=_ev['hardware_fault_byte3-2']),
            *SevenSegmentDisplay(p1=P(0.68, 0.49), p2=P(0.80, 0.51), px1=P(0, 0), px2=P(0, 0), event_out=_ev['hardware_fault_byte4-2']),


            # ButtonDef(key=Qt.Key_W, action='set', event_out=_ev['new_log'], event_delta=True),
            # ButtonDef(key=Qt.Key_S, action='set', event_out=_ev['spawn_dot'], event_delta=True),
        ],
        textbox_defs=[
            # TextboxDef(poly_def=RectDef(p1=P(0.1, 0.8), p2=P(0.45, 0.9)), text_def=TextDef(p=P(0.12, 0.85), h_align=0, v_align=0.5, font_size=30, color=QColor(0, 0, 0, 255), uniform_scale=False), event_out = _ev['textbox_test_value']),
            # TextboxDef(poly_def=RectDef(p1=P(0.55, 0.8), p2=P(0.9, 0.9)), text_def=TextDef(p=P(0.57, 0.85), h_align=0, v_align=0.5, font_size=30, color=QColor(0, 0, 0, 255), uniform_scale=False), event_out = _ev['test_event'])
        ],
        sub_windows=[
            
            # WindowDef(
            #     p1=P(0.50, 0.90), p2=P(1.00, 1.00),
            #     spawn_event=_ev['new_log'],
            #     spawn_event_group='log',
            #     spawn_tick_increment=True,
            #     spawn_delete_threshold=6,
            #     spawn_limit=10,
            #     phase_event=GROUP_EVENT,
            #     phase_fn=lambda v: str(int(v)) if int(v) > 0 else 'open',
            #     phases={
            #         P_OPEN:  Phase([WindowTween(p1=P(0.50, 0.90 - 0.00), p2=P(1.00, 1.00), start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
            #         '1':     Phase([WindowTween(p1=P(0.50, 0.90 - 0.05), p2=P(1.00, 1.00 - 0.05), start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
            #         '2':     Phase([WindowTween(p1=P(0.50, 0.90 - 0.10), p2=P(1.00, 1.00 - 0.10), start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
            #         '3':     Phase([WindowTween(p1=P(0.50, 0.90 - 0.15), p2=P(1.00, 1.00 - 0.15), start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
            #         '4':     Phase([WindowTween(p1=P(0.50, 0.90 - 0.20), p2=P(1.00, 1.00 - 0.20), start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
            #         '5':     Phase([WindowTween(p1=P(0.50, 0.90 - 0.25), p2=P(1.00, 1.00 - 0.25), start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
            #         P_CLOSE: Phase([WindowTween(p1=P(0.50, 0.90 - 0.30), p2=P(1.50, 1.00 - 0.30), start=0, dur=0.5, ease=QEasingCurve.InQuint)]),
            #     },
            #     text_defs=[
            #         TextDef(
            #             p=P(0, 0.5),
            #             text='log entry',
            #             font_size=20.0,
            #             color=QColor(255, 255, 255, 200),
            #             h_align=0.0, v_align=0.5,
            #             text_fn=_ev['textbox_test_value'], uniform_scale=False,
            #         )
            #     ],
            # ),

            # WindowDef(
            #     p1=P(0.0, 0.0), p2=P(1.0, 1.0),
            #     spawn_event=_ev['spawn_dot'],
            #     spawn_event_group='dot',
            #     spawn_tick_increment=False,
            #     spawn_delete_threshold=1,
            #     spawn_limit=20,
            #     phase_event=GROUP_EVENT,
            #     phase_fn=lambda v: 'close' if int(v) >= 1 else 'open',
            #     phases={
            #         P_OPEN:  Phase([WindowTween(p1=P(0,0), p2=P(1,1), start=0, dur=0.0)]),
            #         P_CLOSE: Phase([WindowTween(p1=P(0,0), p2=P(1,1), start=0, dur=0.3)]),
            #     },
            #     polygon_defs=[
            #         RectDef(
            #             p1=P(0.5, 0.5), p2=P(0.5, 0.5),
            #             px1=P(-5, -5),  px2=P(5, 5),
            #             fill_color=QColor(255, 100, 100, 255),
            #             pos_fn=lambda: P(_ev['dot_x'].value, _ev['dot_y'].value),
            #         )
            #     ],
            #     button_defs=[
            #         ButtonDef(
            #             poly_def=RectDef(
            #                 p1=P(0.5, 0.5), p2=P(0.5, 0.5),
            #                 px1=P(-10, -10), px2=P(10, 10),
            #                 fill_color=QColor(200, 100, 100, 80),
            #                 outline_color=QColor(255, 100, 100, 200),
            #                 line_width=1.0,
            #             ),
            #             action='set',
            #             event_out=GROUP_EVENT,
            #             event_delta=GROUP_EVENT,
            #         )
            #     ],
            # ),



            # WindowDef(p1=P(0.40, 0.45), p2=P(0.60, 0.55),
            #     draggable=True, scalable=True,
            #     polygon_defs=[
            #         RectDef(p1=P(0, 0), p2=P(1, 1),
            #             fill_color=QColor(255, 255, 255, 50),
            #             outline_color=QColor(255, 255, 255, 255),
            #             line_width=2,
            #         ),
            #     ],
            #     text_defs=[
            #         TextDef(p=P(0.5, 0.5), text='TEST', font_size=150.0, bold=True, color=QColor(255, 255, 255, 255), h_align=0.5, v_align=0.5),
            #     ],
            #     sub_windows=[
            #         WindowDef(p1=P(0.40, 0.45), p2=P(0.60, 0.55),
            #             draggable=True, scalable=True,
            #             polygon_defs=[
            #                 RectDef(p1=P(0, 0), p2=P(1, 1),
            #                     fill_color=QColor(255, 255, 255, 50),
            #                     outline_color=QColor(255, 255, 255, 255),
            #                     line_width=2,
            #                 ),
            #             ],
            #             text_defs=[
            #                 TextDef(p=P(0.5, 0.5), text='TEST', font_size=150.0, bold=True, color=QColor(255, 255, 255, 255), h_align=0.5, v_align=0.5),
            #             ],
            #         ),
            #     ]
            # ),
        ]
    ),

    # # CAMERA ACCESS PANEL
    # WindowDef(
    #     p1=P(0.0, 0.0), p2=P(1.0, 1.0),
    #     phase_event = [_ev['wire_window_phase'], _ev['wire_count']],
    #     phase_fn    = lambda a, b: f'wire={b}' if isinstance(b, int) else a,
    #     listener_defs=[
    #         # 3 WIRE CONDITIONS
    #         EventListener(targets = [_ev['wire_c3-1']], value_fn = lambda ctx: _ev['wire_red_count'].value,                                     conditions = [lambda v: v == 0],                         values = [True, False]),
    #         EventListener(targets = [_ev['wire_c3-2']], value_fn = lambda ctx: _ev['wire_last_color'].value,                                    conditions = [lambda v: v == 'white'],                   values = [True, False]),
    #         EventListener(targets = [_ev['wire_c3-3']], value_fn = lambda ctx: _ev['wire_blue_count'].value,                                    conditions = [lambda v: v > 1],                          values = [True, False]),
    #         # 4 WIRE CONDITIONS
    #         EventListener(targets = [_ev['wire_c4-1']], value_fn = lambda ctx: _ev['wire_red_count'].value,                                     conditions = [lambda v: v > 1],                          values = [True, False]),
    #         EventListener(targets = [_ev['wire_c4-2']], value_fn = lambda ctx: (_ev['wire_last_color'].value, _ev['wire_red_count'].value),     conditions = [lambda v: v[0] == 'yellow' and v[1] == 0], values = [True, False]),
    #         EventListener(targets = [_ev['wire_c4-3']], value_fn = lambda ctx: _ev['wire_blue_count'].value,                                    conditions = [lambda v: v == 1],                         values = [True, False]),
    #         EventListener(targets = [_ev['wire_c4-4']], value_fn = lambda ctx: _ev['wire_yellow_count'].value,                                  conditions = [lambda v: v > 1],                          values = [True, False]),
    #         # 5 WIRE CONDITIONS
    #         EventListener(targets = [_ev['wire_c5-1']], value_fn = lambda ctx: _ev['wire_last_color'].value,                                    conditions = [lambda v: v == 'black'],                   values = [True, False]),
    #         EventListener(targets = [_ev['wire_c5-2']], value_fn = lambda ctx: (_ev['wire_red_count'].value, _ev['wire_yellow_count'].value),   conditions = [lambda v: v[0] == 1 and v[1] > 1],         values = [True, False]),
    #         EventListener(targets = [_ev['wire_c5-3']], value_fn = lambda ctx: _ev['wire_black_count'].value,                                   conditions = [lambda v: v == 0],                         values = [True, False]),
    #         # 6 WIRE CONDITIONS
    #         EventListener(targets = [_ev['wire_c6-1']], value_fn = lambda ctx: _ev['wire_yellow_count'].value,                                  conditions = [lambda v: v == 0],                         values = [True, False]),
    #         EventListener(targets = [_ev['wire_c6-2']], value_fn = lambda ctx: (_ev['wire_yellow_count'].value, _ev['wire_white_count'].value), conditions = [lambda v: v[0] == 1 and v[1] > 1],         values = [True, False]),
    #         EventListener(targets = [_ev['wire_c6-3']], value_fn = lambda ctx: _ev['wire_red_count'].value,                                     conditions = [lambda v: v == 0],                         values = [True, False]),
    #     ],
    #     polygon_defs=[
    #         RectDef(p1=P(0.73-0.002, 0.55), p2=P(0.73+0.002, 0.55), fill_color=QColor(255, 255, 255, 255), phases={
    #             'wire=3': Phase([RectTween(p1=P(0.73-0.002, 0.55), p2=P(0.73+0.002, 0.85), start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)]),
    #             'wire=4': Phase([RectTween(p1=P(0.73-0.01-0.002, 0.55), p2=P(0.73-0.01+0.002, 0.85), start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)]),
    #             'wire=5': Phase([RectTween(p1=P(0.73-0.02-0.002, 0.55), p2=P(0.73-0.02+0.002, 0.85), start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)]),
    #             'wire=6': Phase([RectTween(p1=P(0.73-0.03-0.002, 0.55), p2=P(0.73-0.03+0.002, 0.85), start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)])}),
    #         RectDef(p1=P(0.75-0.002, 0.55), p2=P(0.75+0.002, 0.55), fill_color=QColor(255, 255, 255, 255), phases={
    #             'wire=3': Phase([RectTween(p1=P(0.75-0.002, 0.55), p2=P(0.75+0.002, 0.85), start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)]),
    #             'wire=4': Phase([RectTween(p1=P(0.75-0.01-0.002, 0.55), p2=P(0.75-0.01+0.002, 0.85), start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)]),
    #             'wire=5': Phase([RectTween(p1=P(0.75-0.02-0.002, 0.55), p2=P(0.75-0.02+0.002, 0.85), start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)]),
    #             'wire=6': Phase([RectTween(p1=P(0.75-0.03-0.002, 0.55), p2=P(0.75-0.03+0.002, 0.85), start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)])}),
    #         RectDef(p1=P(0.77-0.002, 0.55), p2=P(0.77+0.002, 0.55), fill_color=QColor(255, 255, 255, 255), phases={
    #             'wire=3': Phase([RectTween(p1=P(0.77-0.002, 0.55), p2=P(0.77+0.002, 0.85), start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)]),
    #             'wire=4': Phase([RectTween(p1=P(0.77-0.01-0.002, 0.55), p2=P(0.77-0.01+0.002, 0.85), start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)]),
    #             'wire=5': Phase([RectTween(p1=P(0.77-0.02-0.002, 0.55), p2=P(0.77-0.02+0.002, 0.85), start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)]),
    #             'wire=6': Phase([RectTween(p1=P(0.77-0.03-0.002, 0.55), p2=P(0.77-0.03+0.002, 0.85), start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)])}),
    #         RectDef(p1=P(0.79-0.002, 0.55), p2=P(0.79+0.002, 0.55), fill_color=QColor(255, 255, 255, 255), phases={
    #             'wire=3': Phase([RectTween(p1=P(0.79-0.002, 0.55), p2=P(0.79+0.002, 0.55), start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)]),
    #             'wire=4': Phase([RectTween(p1=P(0.79-0.01-0.002, 0.55), p2=P(0.79-0.01+0.002, 0.85), start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)]),
    #             'wire=5': Phase([RectTween(p1=P(0.79-0.02-0.002, 0.55), p2=P(0.79-0.02+0.002, 0.85), start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)]),
    #             'wire=6': Phase([RectTween(p1=P(0.79-0.03-0.002, 0.55), p2=P(0.79-0.03+0.002, 0.85), start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)])}),
    #         RectDef(p1=P(0.81-0.002, 0.55), p2=P(0.81+0.002, 0.55), fill_color=QColor(255, 255, 255, 255), phases={
    #             'wire=3': Phase([RectTween(p1=P(0.81-0.002, 0.55), p2=P(0.81+0.002, 0.55), start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)]),
    #             'wire=4': Phase([RectTween(p1=P(0.81-0.01-0.002, 0.55), p2=P(0.81-0.01+0.002, 0.55), start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)]),
    #             'wire=5': Phase([RectTween(p1=P(0.81-0.02-0.002, 0.55), p2=P(0.81-0.02+0.002, 0.85), start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)]),
    #             'wire=6': Phase([RectTween(p1=P(0.81-0.03-0.002, 0.55), p2=P(0.81-0.03+0.002, 0.85), start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)])}),
    #         RectDef(p1=P(0.83-0.002, 0.55), p2=P(0.83+0.002, 0.55), fill_color=QColor(255, 255, 255, 255), phases={
    #             'wire=3': Phase([RectTween(p1=P(0.83-0.002, 0.55), p2=P(0.83+0.002, 0.55), start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)]),
    #             'wire=4': Phase([RectTween(p1=P(0.83-0.01-0.002, 0.55), p2=P(0.83-0.01+0.002, 0.55), start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)]),
    #             'wire=5': Phase([RectTween(p1=P(0.83-0.02-0.002, 0.55), p2=P(0.83-0.02+0.002, 0.55), start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)]),
    #             'wire=6': Phase([RectTween(p1=P(0.83-0.03-0.002, 0.55), p2=P(0.83-0.03+0.002, 0.85), start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)])}),
    #         RectDef(p1=P(0.68, 0.58), p2=P(0.82, 0.82), fill_color=QColor(171, 151, 247, 0), outline_color=QColor(171, 151, 247, 0), line_width=1.0, phases={
    #             ('wire=3', 'wire=4', 'wire=5', 'wire=6'): Phase([RectTween(p1=P(0.68, 0.58), p2=P(0.82, 0.82), outline_color=QColor(171, 151, 247, 255), start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)])}),
    #     ],
    #     text_defs=[
    #         TextDef(x=0.50, y=0.00, px=10, text='CAMERA ACCESS PANEL', font_size=32.0, bold=True, color=QColor(171, 151, 247, 255), h_align=0.0, v_align=0.0, char_display=0.0, sub_char_clip=True, phases={
    #                 P_OPEN:  Phase([Reset(), TextTween(char_display=1, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
    #                 P_CLOSE: Phase([         TextTween(char_display=0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)])}
    #         ),

    #         # WIRE COUNT
    #         TextDef(x=0.50, y=0.10, px=10, text='WIRE COUNT', font_size=20.0, color=QColor(171, 151, 247, 255), h_align=0.0, v_align=0.5, char_display=0.0, sub_char_clip=True, phases={
    #                 P_OPEN:  Phase([Reset(), TextTween(char_display=1, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
    #                 P_CLOSE: Phase([         TextTween(char_display=0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)])}
    #         ),

    #         # ── THREE WIRES
    #         TextDef(x=0.50, y=0.20, px=10, text='RED WIRE COUNT', font_size=20.0, color=QColor(171, 151, 247, 255), h_align=0.0, v_align=0.5, char_display=0.0, sub_char_clip=True, 
    #             phase_override=lambda: (
    #                 'open' if _ev['wire_count'].value == 3 else 
    #                 'open' if _ev['wire_count'].value == 4 else 
    #                 'open' if _ev['wire_count'].value == 5 and not _ev['wire_c5-1'].value else 
    #                 'open' if _ev['wire_count'].value == 6 and not _ev['wire_c6-1'].value and not _ev['wire_c6-2'].value else 
    #                 'dim'
    #             ), phases={
    #                 P_OPEN:  Phase([TextTween(color=QColor(171, 151, 247, 255), char_display=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
    #                 'dim':   Phase([TextTween(color=QColor(171, 151, 247, 100), char_display=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
    #                 P_CLOSE: Phase([TextTween(char_display=0.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)])},
    #         ),
    #         TextDef(x=0.50, y=0.25, px=10, text='YELLOW WIRE COUNT', font_size=20.0, color=QColor(171, 151, 247, 255), h_align=0.0, v_align=0.5, char_display=0.0, sub_char_clip=True, 
    #             phase_override=lambda: (
    #                 'open' if _ev['wire_count'].value == 4 and not _ev['wire_c4-1'].value and not _ev['wire_c4-2'].value and not _ev['wire_c4-3'].value else
    #                 'open' if _ev['wire_count'].value == 5 and not _ev['wire_c5-1'].value else 
    #                 'open' if _ev['wire_count'].value == 6 else 
    #                 'dim'
    #             ), phases={
    #                 P_OPEN:  Phase([TextTween(color=QColor(171, 151, 247, 255), char_display=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
    #                 'dim':   Phase([TextTween(color=QColor(171, 151, 247, 100), char_display=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
    #                 P_CLOSE: Phase([TextTween(char_display=0.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)])},
    #         ),
    #         TextDef(x=0.50, y=0.30, px=10, text='BLUE WIRE COUNT', font_size=20.0, color=QColor(171, 151, 247, 255), h_align=0.0, v_align=0.5, char_display=0.0, sub_char_clip=True,
    #             phase_override=lambda: (
    #                 'open' if _ev['wire_count'].value == 3 and not _ev['wire_c3-1'].value and not _ev['wire_c3-2'].value else 
    #                 'open' if _ev['wire_count'].value == 4 and not _ev['wire_c4-1'].value and not _ev['wire_c4-2'].value else
    #                 'dim'
    #             ), phases={
    #                 P_OPEN:  Phase([TextTween(color=QColor(171, 151, 247, 255), char_display=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
    #                 'dim':   Phase([TextTween(color=QColor(171, 151, 247, 100), char_display=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
    #                 P_CLOSE: Phase([TextTween(char_display=0.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)])},
    #         ),
    #         TextDef(x=0.50, y=0.35, px=10, text='WHITE WIRE COUNT', font_size=20.0, color=QColor(171, 151, 247, 255), h_align=0.0, v_align=0.5, char_display=0.0, sub_char_clip=True, 
    #             phase_override=lambda: (
    #                 'open' if _ev['wire_count'].value == 6 and not _ev['wire_c6-1'].value else
    #                 'dim'
    #             ), phases={
    #                 P_OPEN:  Phase([TextTween(color=QColor(171, 151, 247, 255), char_display=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
    #                 'dim':   Phase([TextTween(color=QColor(171, 151, 247, 100), char_display=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
    #                 P_CLOSE: Phase([TextTween(char_display=0.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)])},
    #         ),
    #         TextDef(x=0.50, y=0.40, px=10, text='BLACK WIRE COUNT', font_size=20.0, color=QColor(171, 151, 247, 255), h_align=0.0, v_align=0.5, char_display=0.0, sub_char_clip=True,
    #             phase_override=lambda: (
    #                 'open' if _ev['wire_count'].value == 5 and not _ev['wire_c5-1'].value and not _ev['wire_c5-2'].value else
    #                 'dim'
    #             ), phases={
    #                 P_OPEN:  Phase([TextTween(color=QColor(171, 151, 247, 255), char_display=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
    #                 'dim':   Phase([TextTween(color=QColor(171, 151, 247, 100), char_display=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
    #                 P_CLOSE: Phase([TextTween(char_display=0.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)])},
    #         ),
    #         TextDef(x=0.50, y=0.45, px=10, text='LAST WIRE COLOR', font_size=20.0, color=QColor(171, 151, 247, 255), h_align=0.0, v_align=0.5, char_display=0.0, sub_char_clip=True,
    #             phase_override=lambda: (
    #                 'open' if _ev['wire_count'].value == 3 and not _ev['wire_c3-1'].value else
    #                 'open' if _ev['wire_count'].value == 4 and not _ev['wire_c4-1'].value else
    #                 'open' if _ev['wire_count'].value == 5 else
    #                 'dim'
    #             ), phases={
    #                 P_OPEN:  Phase([TextTween(color=QColor(171, 151, 247, 255), char_display=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
    #                 'dim':   Phase([TextTween(color=QColor(171, 151, 247, 100), char_display=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
    #                 P_CLOSE: Phase([TextTween(char_display=0.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)])},
    #         ),
    #         # INSTRUCTIONS
    #         TextDef(x=0.75, y=0.90, text='CUT THE FIRST WIRE', font_size=32.0, bold=True, color=QColor(171, 151, 247, 255), h_align=0.5, v_align=0.0, char_display=0.0, sub_char_clip=True,
    #             phase_override=lambda: (
    #                 'open' if _ev['wire_count'].value == 4 and not _ev['wire_c4-1'].value and (_ev['wire_c4-2'].value or _ev['wire_c4-3'].value) else 
    #                 'open' if _ev['wire_count'].value == 5 and not _ev['wire_c5-1'].value and _ev['wire_c5-2'].value else 
    #                 'close'
    #             ), phases={
    #                 P_OPEN:  Phase([Reset(), TextTween(char_display=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
    #                 P_CLOSE: Phase([         TextTween(char_display=0.0, h_align=-0.5, start=0, dur=0.5, ease=QEasingCurve.OutQuint)])},
    #         ),

    #         TextDef(x=0.75, y=0.90, text='CUT THE SECOND WIRE', font_size=32.0, bold=True, color=QColor(171, 151, 247, 255), h_align=0.5, v_align=0.0, char_display=0.0, sub_char_clip=True,
    #             phase_override=lambda: (
    #                 'open' if _ev['wire_count'].value == 3 and _ev['wire_c3-1'].value else 
    #                 'open' if _ev['wire_count'].value == 4 and not _ev['wire_c4-1'].value and not _ev['wire_c4-2'].value and not _ev['wire_c4-3'].value and not _ev['wire_c4-4'].value else 
    #                 'open' if _ev['wire_count'].value == 5 and not _ev['wire_c5-1'].value and not _ev['wire_c5-2'].value and _ev['wire_c5-3'].value else 
    #                 'open' if _ev['wire_count'].value == 6 and not _ev['wire_c6-1'].value and not _ev['wire_c6-2'].value and not _ev['wire_c6-3'].value else 
    #                 'close'
    #             ), phases={
    #                 P_OPEN:  Phase([Reset(), TextTween(char_display=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
    #                 P_CLOSE: Phase([         TextTween(char_display=0.0, h_align=-0.5, start=0, dur=0.5, ease=QEasingCurve.OutQuint)])},
    #         ),
    #         TextDef(x=0.75, y=0.90, text='CUT THE THIRD WIRE', font_size=32.0, bold=True, color=QColor(171, 151, 247, 255), h_align=0.5, v_align=0.0, char_display=0.0, sub_char_clip=True,
    #             phase_override=lambda: (
    #                 'open' if _ev['wire_count'].value == 6 and _ev['wire_c6-1'].value else 
    #                 'close'
    #             ), phases={
    #                 P_OPEN:  Phase([Reset(), TextTween(char_display=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
    #                 P_CLOSE: Phase([         TextTween(char_display=0.0, h_align=-0.5, start=0, dur=0.5, ease=QEasingCurve.OutQuint)])},
    #         ),
    #         TextDef(x=0.75, y=0.90, text='CUT THE FOURTH WIRE', font_size=32.0, bold=True, color=QColor(171, 151, 247, 255), h_align=0.5, v_align=0.0, char_display=0.0, sub_char_clip=True,
    #             phase_override=lambda: (
    #                 'open' if _ev['wire_count'].value == 5 and _ev['wire_c5-1'].value else 
    #                 'open' if _ev['wire_count'].value == 6 and not _ev['wire_c6-1'].value and _ev['wire_c6-2'].value else 
    #                 'close'
    #             ), phases={
    #                 P_OPEN:  Phase([Reset(), TextTween(char_display=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
    #                 P_CLOSE: Phase([         TextTween(char_display=0.0, h_align=-0.5, start=0, dur=0.5, ease=QEasingCurve.OutQuint)])},
    #         ),

    #         TextDef(x=0.75, y=0.90, text='CUT THE LAST WIRE', font_size=32.0, bold=True, color=QColor(171, 151, 247, 255), h_align=0.5, v_align=0.0, char_display=0.0, sub_char_clip=True,
    #             phase_override=lambda: (
    #                 'open' if _ev['wire_count'].value == 3 and ((not _ev['wire_c3-1'].value and _ev['wire_c3-2'].value) or (not _ev['wire_c3-1'].value and not _ev['wire_c3-2'].value and not _ev['wire_c3-3'].value)) else 
    #                 'open' if _ev['wire_count'].value == 4 and not _ev['wire_c4-1'].value and not _ev['wire_c4-2'].value and not _ev['wire_c4-3'].value and _ev['wire_c4-4'].value else 
    #                 'open' if _ev['wire_count'].value == 5 and not _ev['wire_c5-1'].value and not _ev['wire_c5-2'].value and not _ev['wire_c5-3'].value else 
    #                 'open' if _ev['wire_count'].value == 6 and not _ev['wire_c6-1'].value and not _ev['wire_c6-2'].value and _ev['wire_c6-3'].value else 
    #                 'close'
    #             ), phases={
    #                 P_OPEN:  Phase([Reset(), TextTween(char_display=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
    #                 P_CLOSE: Phase([         TextTween(char_display=0.0, h_align=-0.5, start=0, dur=0.5, ease=QEasingCurve.OutQuint)])},
    #         ),

    #         TextDef(x=0.75, y=0.90, text='CUT THE LAST RED WIRE', font_size=32.0, bold=True, color=QColor(171, 151, 247, 255), h_align=0.5, v_align=0.0, char_display=0.0, sub_char_clip=True,
    #             phase_override=lambda: (
    #                 'open' if _ev['wire_count'].value == 4 and _ev['wire_c4-1'].value else 
    #                 'close'
    #             ), phases={
    #                 P_OPEN:  Phase([Reset(), TextTween(char_display=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
    #                 P_CLOSE: Phase([         TextTween(char_display=0.0, h_align=-0.5, start=0, dur=0.5, ease=QEasingCurve.OutQuint)])},
    #         ),
    #         TextDef(x=0.75, y=0.90, text='CUT THE LAST BLUE WIRE', font_size=32.0, bold=True, color=QColor(171, 151, 247, 255), h_align=0.5, v_align=0.0, char_display=0.0, sub_char_clip=True,
    #             phase_override=lambda: (
    #                 'open' if _ev['wire_count'].value == 3 and not _ev['wire_c3-1'].value and not _ev['wire_c3-2'].value and _ev['wire_c3-3'].value else 
    #                 'close'
    #             ), phases={
    #                 P_OPEN:  Phase([Reset(), TextTween(char_display=1.0, start=0, dur=0.5, ease=QEasingCurve.OutQuint)]),
    #                 P_CLOSE: Phase([         TextTween(char_display=0.0, h_align=-0.5, start=0, dur=0.5, ease=QEasingCurve.OutQuint)])},
    #         ),
    #     ],
    #     button_defs=[
    #         *SegmentedButtons(
    #             p1=P(0.75, 0.08), p2=P(0.95, 0.12), px1=P(0, 0), px2=P(0, 0), event_out=_ev['wire_count'], segments=[
    #                 Segment(key=Qt.Key_3, event_delta=3, weight=1, label='3'),
    #                 Segment(key=Qt.Key_4, event_delta=4, weight=1, label='4'),
    #                 Segment(key=Qt.Key_5, event_delta=5, weight=1, label='5'),
    #                 Segment(key=Qt.Key_6, event_delta=6, weight=1, label='6'),
    #             ],
    #         ),
    #         *SegmentedButtons(
    #             p1=P(0.775, 0.18), p2=P(0.925, 0.22), px1=P(0, 0), px2=P(0, 0), event_out=_ev['wire_red_count'], 
    #             phase_override=lambda: (
    #                 'open' if _ev['wire_count'].value == 3 else 
    #                 'open' if _ev['wire_count'].value == 4 else 
    #                 'open' if _ev['wire_count'].value == 5 and not _ev['wire_c5-1'].value else 
    #                 'open' if _ev['wire_count'].value == 6 and not _ev['wire_c6-1'].value and not _ev['wire_c6-2'].value else 
    #                 'close'
    #             ), segments=[
    #                 Segment(key=Qt.Key_3, event_delta=0, weight=1, label='0'),
    #                 Segment(key=Qt.Key_4, event_delta=1, weight=1, label='1'),
    #                 Segment(key=Qt.Key_4, event_delta=2, weight=2, label='≥2'),
    #             ],
    #         ),
    #         *SegmentedButtons(
    #             p1=P(0.775, 0.23), p2=P(0.925, 0.27), px1=P(0, 0), px2=P(0, 0), event_out=_ev['wire_yellow_count'], 
    #             phase_override=lambda: (
    #                 'open' if _ev['wire_count'].value == 4 and not _ev['wire_c4-1'].value and not _ev['wire_c4-2'].value and not _ev['wire_c4-3'].value else
    #                 'open' if _ev['wire_count'].value == 5 and not _ev['wire_c5-1'].value else 
    #                 'open' if _ev['wire_count'].value == 6 else 
    #                 'close'
    #             ), segments=[
    #                 Segment(key=Qt.Key_3, event_delta=0, weight=1, label='0'),
    #                 Segment(key=Qt.Key_4, event_delta=1, weight=1, label='1'),
    #                 Segment(key=Qt.Key_4, event_delta=2, weight=2, label='≥2'),
    #             ],
    #         ),
    #         *SegmentedButtons(
    #             p1=P(0.775, 0.28), p2=P(0.925, 0.32), px1=P(0, 0), px2=P(0, 0), event_out=_ev['wire_blue_count'], 
    #             phase_override=lambda: (
    #                 'open' if _ev['wire_count'].value == 3 and not _ev['wire_c3-1'].value and not _ev['wire_c3-2'].value else 
    #                 'open' if _ev['wire_count'].value == 4 and not _ev['wire_c4-1'].value and not _ev['wire_c4-2'].value else
    #                 'close'
    #             ), segments=[
    #                 Segment(key=Qt.Key_3, event_delta=0, weight=1, label='0'),
    #                 Segment(key=Qt.Key_4, event_delta=1, weight=1, label='1'),
    #                 Segment(key=Qt.Key_4, event_delta=2, weight=2, label='≥2'),
    #             ],
    #         ),
    #         *SegmentedButtons(
    #             p1=P(0.775, 0.33), p2=P(0.925, 0.37), px1=P(0, 0), px2=P(0, 0), event_out=_ev['wire_white_count'], 
    #             phase_override=lambda: (
    #                 'open' if _ev['wire_count'].value == 6 and not _ev['wire_c6-1'].value else
    #                 'close'
    #             ), segments=[
    #                 Segment(key=Qt.Key_4, event_delta=1, weight=1, label='≤1'),
    #                 Segment(key=Qt.Key_4, event_delta=2, weight=1, label='≥2'),
    #             ],
    #         ),
    #         *SegmentedButtons(
    #             p1=P(0.775, 0.38), p2=P(0.925, 0.42), px1=P(0, 0), px2=P(0, 0), event_out=_ev['wire_black_count'], 
    #             phase_override=lambda: (
    #                 'open' if _ev['wire_count'].value == 5 and not _ev['wire_c5-1'].value and not _ev['wire_c5-2'].value else
    #                 'close'
    #             ), segments=[
    #                 Segment(key=Qt.Key_3, event_delta=0, weight=1, label='0'),
    #                 Segment(key=Qt.Key_4, event_delta=1, weight=1, label='≥1'),
    #             ],
    #         ),
    #         *SegmentedButtons(
    #             p1=P(0.75, 0.43), p2=P(0.95, 0.47), px1=P(0, 0), px2=P(0, 0), event_out=_ev['wire_last_color'], 
    #             phase_override=lambda: (
    #                 'open' if _ev['wire_count'].value == 3 and not _ev['wire_c3-1'].value else
    #                 'open' if _ev['wire_count'].value == 4 and not _ev['wire_c4-1'].value else
    #                 'open' if _ev['wire_count'].value == 5 else
    #                 'close'
    #             ), segments=[
    #                 Segment(key=Qt.Key_3, event_delta='yellow', weight=1, label='YELLOW'),
    #                 Segment(key=Qt.Key_4, event_delta='white', weight=1, label='WHITE'),
    #                 Segment(key=Qt.Key_4, event_delta='black', weight=1, label='BLACK'),
    #             ],
    #         ),
    #     ],
    # ),
    # WindowDef(
    #     p1=P(0.0, 0.0), p2=P(1.0, 1.0),
    #     button_defs=[
    #         # This assigns actions to keybinds on your keyboard (W/S opens/closes window5, UpArrow/DownArrow changes the subscription topic for one of the events)
    #         ButtonDef(key=Qt.Key_W, action='set', event_out=_ev['window5_phase'], event_delta='open'),
    #         ButtonDef(key=Qt.Key_S, action='set', event_out=_ev['window5_phase'], event_delta='close'),
    #         ButtonDef(key=Qt.Key_Up, action='set', event_out=_ev['test_event'], event_delta='test_value9'),
    #         ButtonDef(key=Qt.Key_Down, action='set', event_out=_ev['test_event'], event_delta='test_value1'),
    #     ]
    # ),
    
    # WindowDef(
    #     p1=P(0.5, 0.5), p2=P(0.5, 0.5),
    #     phase_event=_ev['window5_phase'],
    #     phases={
    #         'open':  WindowPhase([WindowTween(p1=P(0.00, 0.00), p2=P(1.00, 1.00), start=0.00, dur=1.00, ease=QEasingCurve.OutQuint)]),
    #         'close': WindowPhase([WindowTween(p1=P(0.50, 0.50), p2=P(0.50, 0.50), start=0.00, dur=1.00, ease=QEasingCurve.OutQuint)]),
    #     },
    #     polygon_defs=[
    #         Rect(p1=P(0, 0), p2=P(1, 1), fill_color=QColor(0, 0, 0, 255)),
    #         Rect(p1=P(0, 0), p2=P(0, 1), px2=P(1, 0), fill_color=QColor(255, 255, 255, 255)),
    #         Rect(p1=P(1, 0), p2=P(1, 1), px1=P(-1, 0), fill_color=QColor(255, 255, 255, 255)),
    #         Rect(p1=P(0, 0), p2=P(1, 0), px2=P(0, 1), fill_color=QColor(255, 255, 255, 255)),
    #         Rect(p1=P(0, 1), p2=P(1, 1), px1=P(0, -1), fill_color=QColor(255, 255, 255, 255)),
    #     ],
    #     text_defs=[
    #         # Data tables takes in a list of values, which are a tuple of the following values:
    #         # 0 = Name   (string label on the left of the table)
    #         # 1 = Value  (the number that will be displayed, this typically is where you take reference of a subscription, such as in these examples)
    #         # 2 = Unit   (displayed string directly behind the value number)
    #         # 3 = Format (can be used if you want to display a certain number of decimal points)

    #         # Note that you could get away with making the tables in a for loop, as the only difference really is just the x, y, value_x, and values data
    #         # Doing this is similar to what i did with assigning each DataTable the same phase
    #         # There will be a better way to make similar objects faster in a cleaner way in the future

    #         *DataTable(x=0, y=0, px=0, py=20, value_x=0.9/6, value_px=0, title='', color=QColor(200, 220, 255, 220), row_height=18.0, char_display=0.0, sub_char_clip=True, phases=data_table_phase, values=[
    #                 ('STEER DEG ',      lambda ctx: ctx['test_value1']['latest'], 'rad', '.2f'),
    #                 ('STEER DEG (REQ)', lambda ctx: ctx['test_value2']['latest'], 'rad', '.2f'),
    #         ]),
    #         *DataTable(x=3/6, y=0, px=0, py=20, value_x=3.9/6, value_px=0, title='', color=QColor(200, 220, 255, 220), row_height=18.0, char_display=0.0, sub_char_clip=True, phases=data_table_phase, values=[
    #                 ('STEER DEG ',      lambda ctx: ctx['test_value3']['latest'], 'rad', '.2f'),
    #                 ('STEER DEG (REQ)', lambda ctx: ctx['test_value4']['latest'], 'rad', '.2f'),
    #         ]),
    #         *DataTable(x=0, y=4/6, px=0, py=20, value_x=0.9/6, value_px=0, title='', color=QColor(200, 220, 255, 220), row_height=18.0, char_display=0.0, sub_char_clip=True, phases=data_table_phase, values=[
    #                 ('STEER DEG ',      lambda ctx: ctx['test_value5']['latest'], 'rad', '.2f'),
    #                 ('STEER DEG (REQ)', lambda ctx: ctx['test_value6']['latest'], 'rad', '.2f'),
    #         ]),
    #         *DataTable(x=3/6, y=4/6, px=0, py=20, value_x=3.9/6, value_px=0, title='', color=QColor(200, 220, 255, 220), row_height=18.0, char_display=0.0, sub_char_clip=True, phases=data_table_phase, values=[
    #                 ('STEER DEG ',      lambda ctx: ctx['test_value7']['latest'], 'rad', '.2f'),
    #                 ('STEER DEG (REQ)', lambda ctx: ctx['test_value8']['latest'], 'rad', '.2f'),
    #         ]),

    #         *DataTable(x=1/6, y=1/6, px=0, py=20, value_x=1.9/6, value_px=0, title='FRONT LEFT', color=QColor(200, 220, 255, 220), row_height=18.0, char_display=0.0, sub_char_clip=True, phases=data_table_phase, values=[
    #                 ('AMPS',      lambda ctx: ctx['test_value1']['latest'],           'A',   '.2f'),
    #                 ('VOLTS',     lambda ctx: ctx['test_value2']['latest'],           'V',   '.2f'),
    #                 ('RPM',       lambda ctx: ctx['test_value3']['latest'],           'r/m', '.1f'),
    #                 ('RPM (REQ)', lambda ctx: ctx[_ev['test_event'].value]['latest'], 'r/m', '.1f'), # If you saw the comment next to the ButtonDefs, this is the subscription topic that changes (this is purely just to test changing topics)
    #         ]),
    #         *DataTable(x=2/6, y=1/6, px=0, py=20, value_x=2.9/6, value_px=0, title='FRONT RIGHT', color=QColor(200, 220, 255, 220), row_height=18.0, char_display=0.0, sub_char_clip=True, phases=data_table_phase, values=[
    #                 ('AMPS',      lambda ctx: ctx['test_value5']['latest'], 'A',   '.2f'),
    #                 ('VOLTS',     lambda ctx: ctx['test_value6']['latest'], 'V',   '.2f'),
    #                 ('RPM',       lambda ctx: ctx['test_value7']['latest'], 'r/m', '.1f'),
    #                 ('RPM (REQ)', lambda ctx: ctx['test_value8']['latest'], 'r/m', '.1f'),
    #         ]),
    #         *DataTable(x=1/6, y=2/6, px=0, py=20, value_x=1.9/6, value_px=0, title='MIDDLE LEFT', color=QColor(200, 220, 255, 220), row_height=18.0, char_display=0.0, sub_char_clip=True, phases=data_table_phase, values=[
    #                 ('AMPS',      lambda ctx: ctx['test_value1']['latest'], 'A',   '.2f'),
    #                 ('VOLTS',     lambda ctx: ctx['test_value2']['latest'], 'V',   '.2f'),
    #                 ('RPM',       lambda ctx: ctx['test_value3']['latest'], 'r/m', '.1f'),
    #                 ('RPM (REQ)', lambda ctx: ctx['test_value4']['latest'], 'r/m', '.1f'),
    #         ]),
    #         *DataTable(x=2/6, y=2/6, px=0, py=20, value_x=2.9/6, value_px=0, title='MIDDLE RIGHT', color=QColor(200, 220, 255, 220), row_height=18.0, char_display=0.0, sub_char_clip=True, phases=data_table_phase, values=[
    #                 ('AMPS',      lambda ctx: ctx['test_value5']['latest'], 'A',   '.2f'),
    #                 ('VOLTS',     lambda ctx: ctx['test_value6']['latest'], 'V',   '.2f'),
    #                 ('RPM',       lambda ctx: ctx['test_value7']['latest'], 'r/m', '.1f'),   
    #                 ('RPM (REQ)', lambda ctx: ctx['test_value8']['latest'], 'r/m', '.1f'),
    #         ]),
    #         *DataTable(x=1/6, y=3/6, px=0, py=20, value_x=1.9/6, value_px=0, title='MIDDLE LEFT', color=QColor(200, 220, 255, 220), row_height=18.0, char_display=0.0, sub_char_clip=True, phases=data_table_phase, values=[
    #                 ('AMPS',      lambda ctx: ctx['test_value1']['latest'], 'A',   '.2f'),
    #                 ('VOLTS',     lambda ctx: ctx['test_value2']['latest'], 'V',   '.2f'),
    #                 ('RPM',       lambda ctx: ctx['test_value3']['latest'], 'r/m', '.1f'),
    #                 ('RPM (REQ)', lambda ctx: ctx['test_value4']['latest'], 'r/m', '.1f'),
    #         ]),
    #         *DataTable(x=2/6, y=3/6, px=0, py=20, value_x=2.9/6, value_px=0, title='MIDDLE RIGHT', color=QColor(200, 220, 255, 220), row_height=18.0, char_display=0.0, sub_char_clip=True, phases=data_table_phase, values=[
    #                 ('AMPS',      lambda ctx: ctx['test_value5']['latest'], 'A',   '.2f'),
    #                 ('VOLTS',     lambda ctx: ctx['test_value6']['latest'], 'V',   '.2f'),
    #                 ('RPM',       lambda ctx: ctx['test_value7']['latest'], 'r/m', '.1f'),
    #                 ('RPM (REQ)', lambda ctx: ctx['test_value8']['latest'], 'r/m', '.1f'),
    #         ]),

    #         *DataTable(x=4/6, y=0/7, px=0, py=20, value_x=4.9/6, value_px=0, title='ARM 0', color=QColor(200, 220, 255, 220), row_height=18.0, char_display=0.0, sub_char_clip=True, phases=data_table_phase, values=[
    #                 ('AMPS',        lambda ctx: ctx['test_value5']['latest'], 'A',   '.2f'),
    #                 ('VOLTS',       lambda ctx: ctx['test_value6']['latest'], 'V',   '.2f'),
    #                 ('RPM',         lambda ctx: ctx['test_value7']['latest'], 'r/m', '.1f'),
    #                 ('ENCODER IN',  lambda ctx: ctx['test_value8']['latest'], 'r/m', '.1f'),
    #                 ('ENCODER OUT', lambda ctx: ctx['test_value9']['latest'], 'r/m', '.1f'),
    #         ]),
    #         *DataTable(x=4/6, y=1/7, px=0, py=20, value_x=4.9/6, value_px=0, title='ARM 1', color=QColor(200, 220, 255, 220), row_height=18.0, char_display=0.0, sub_char_clip=True, phases=data_table_phase, values=[
    #                 ('AMPS',        lambda ctx: ctx['test_value5']['latest'], 'A',   '.2f'),
    #                 ('VOLTS',       lambda ctx: ctx['test_value6']['latest'], 'V',   '.2f'),
    #                 ('RPM',         lambda ctx: ctx['test_value7']['latest'], 'r/m', '.1f'),
    #                 ('ENCODER IN',  lambda ctx: ctx['test_value8']['latest'], 'r/m', '.1f'),
    #                 ('ENCODER OUT', lambda ctx: ctx['test_value9']['latest'], 'r/m', '.1f'),
    #         ]),
    #         *DataTable(x=4/6, y=2/7, px=0, py=20, value_x=4.9/6, value_px=0, title='ARM 2', color=QColor(200, 220, 255, 220), row_height=18.0, char_display=0.0, sub_char_clip=True, phases=data_table_phase, values=[
    #                 ('AMPS',        lambda ctx: ctx['test_value5']['latest'], 'A',   '.2f'),
    #                 ('VOLTS',       lambda ctx: ctx['test_value6']['latest'], 'V',   '.2f'),
    #                 ('RPM',         lambda ctx: ctx['test_value7']['latest'], 'r/m', '.1f'),
    #                 ('ENCODER IN',  lambda ctx: ctx['test_value8']['latest'], 'r/m', '.1f'),
    #                 ('ENCODER OUT', lambda ctx: ctx['test_value9']['latest'], 'r/m', '.1f'),
    #         ]),
    #         *DataTable(x=4/6, y=3/7, px=0, py=20, value_x=4.9/6, value_px=0, title='ARM 3', color=QColor(200, 220, 255, 220), row_height=18.0, char_display=0.0, sub_char_clip=True, phases=data_table_phase, values=[
    #                 ('AMPS',        lambda ctx: ctx['test_value5']['latest'], 'A',   '.2f'),
    #                 ('VOLTS',       lambda ctx: ctx['test_value6']['latest'], 'V',   '.2f'),
    #                 ('RPM',         lambda ctx: ctx['test_value7']['latest'], 'r/m', '.1f'),
    #                 ('ENCODER IN',  lambda ctx: ctx['test_value8']['latest'], 'r/m', '.1f'),
    #                 ('ENCODER OUT', lambda ctx: ctx['test_value9']['latest'], 'r/m', '.1f'),
    #         ]),
    #         *DataTable(x=4/6, y=4/7, px=0, py=20, value_x=4.9/6, value_px=0, title='ARM 4', color=QColor(200, 220, 255, 220), row_height=18.0, char_display=0.0, sub_char_clip=True, phases=data_table_phase, values=[
    #                 ('AMPS',        lambda ctx: ctx['test_value5']['latest'], 'A',   '.2f'),
    #                 ('VOLTS',       lambda ctx: ctx['test_value6']['latest'], 'V',   '.2f'),
    #                 ('RPM',         lambda ctx: ctx['test_value7']['latest'], 'r/m', '.1f'),
    #                 ('ENCODER IN',  lambda ctx: ctx['test_value8']['latest'], 'r/m', '.1f'),
    #                 ('ENCODER OUT', lambda ctx: ctx['test_value9']['latest'], 'r/m', '.1f'),
    #         ]),
    #         *DataTable(x=4/6, y=5/7, px=0, py=20, value_x=4.9/6, value_px=0, title='ARM 5', color=QColor(200, 220, 255, 220), row_height=18.0, char_display=0.0, sub_char_clip=True, phases=data_table_phase, values=[
    #                 ('AMPS',        lambda ctx: ctx['test_value5']['latest'], 'A',   '.2f'),
    #                 ('VOLTS',       lambda ctx: ctx['test_value6']['latest'], 'V',   '.2f'),
    #                 ('RPM',         lambda ctx: ctx['test_value7']['latest'], 'r/m', '.1f'),
    #                 ('ENCODER IN',  lambda ctx: ctx['test_value8']['latest'], 'r/m', '.1f'),
    #                 ('ENCODER OUT', lambda ctx: ctx['test_value9']['latest'], 'r/m', '.1f'),
    #         ]),
    #         *DataTable(x=4/6, y=6/7, px=0, py=20, value_x=4.9/6, value_px=0, title='ARM 6', color=QColor(200, 220, 255, 220), row_height=18.0, char_display=0.0, sub_char_clip=True, phases=data_table_phase, values=[
    #                 ('AMPS',        lambda ctx: ctx['test_value5']['latest'], 'A',   '.2f'),
    #                 ('VOLTS',       lambda ctx: ctx['test_value6']['latest'], 'V',   '.2f'),
    #                 ('RPM',         lambda ctx: ctx['test_value7']['latest'], 'r/m', '.1f'),
    #                 ('ENCODER IN',  lambda ctx: ctx['test_value8']['latest'], 'r/m', '.1f'),
    #                 ('ENCODER OUT', lambda ctx: ctx['test_value9']['latest'], 'r/m', '.1f'),
    #         ]),
    #         *DataTable(x=5/6, y=0, px=0, py=20, value_x=5.9/6, value_px=0, title='MISC DATA', color=QColor(200, 220, 255, 220), row_height=18.0, char_display=0.0, sub_char_clip=True, phases=data_table_phase, values=[
    #                 ('INTERNAL TEMP', lambda ctx: ctx['test_value5']['latest'], '°C',   '.2f'),
    #                 ('EXTERNAL TEMP', lambda ctx: ctx['test_value5']['latest'], '°C',   '.2f'),
    #                 ('CPU',           lambda ctx: ctx['test_value6']['latest'], '%',    '.2f'),
    #                 ('RAM',           lambda ctx: ctx['test_value7']['latest'], '%',    '.1f'),
    #                 ('BATTERY',       lambda ctx: ctx['test_value8']['latest'], '%',    '.1f'),
    #                 ('VOLTAGE',       lambda ctx: ctx['test_value9']['latest'], 'V',    '.1f'),
    #                 ('CONNECTION',    lambda ctx: ctx['test_value9']['latest'], 'Mbps', '.1f'),
    #                 ('LATENCY',       lambda ctx: ctx['test_value9']['latest'], 'ms',   '.1f'),
    #         ]),
    #     ],
    # ),
]




    # Any time you want to make an object, it should be contained within a WindowDef object to allow modularity.
    # To make objects, call the class of the object, in this case, callin WindowDef() will create a WindowDef object.
    # By default, this creates a WindowDef at points P(0, 0) to P(0, 0), where the first values indicates the TOP-LEFT x and y points, and the second values indicates the BOTTOM-RIGHT x and y points.
    # These values are obviouslly not what we want, so define the p1, p2, px1, and px2 values to create a boundary that feasible for what we want.
    # TASK 1. Create a WindowDef that is centered in the screen, and is rectangle of 400px by 400px.








    # You should notice that running it does nothing, this is expected as we do not have anything contained in the window.
    # RectDef/PolygonDef are objects that creates a shape using defined points. (Note that RectDefs are automatically converted into PolygonDefs)
    # To visualise this, make a RectDef inside this window that spans across the whole window.
    # TASK 2. Make a RectDef that spans accross the whole window, with a white fill color of 10 alpha, a white outline color of 255 alpha, and a line width of 1px








    # For the map to be useful, we need to do a few additional things.
    # TextDef are objects that creates a text at a given point.
    # First, add some text along the x and y axis of the map
    # TASK 3. Make 4 TextDef objects, corresponding to the North, South, East, West. The text should be a single letter and aligned on the edge of each side.
    #         The text should be white, have a font size of 20px, and for now, disable uniform_scale. It is recomended to have a small pixel offset for each text so that the text isnt directly touching the borders.








    # Next, we should store the coordinates of the rover. Even though we currently do not have access to the rover's information, we can still make values that can be used as a subscription later on.
    # In order to do this, we would need some EventDef objects. Note that EventDef objects are different than typical objects, and is defined inside MAIN_EVENT_DEFS
    # EventDef are values that are stored and used for other usage. This is useful especially for values that can change.
    # TASK 4. Make 2 EventDef objects, name them 'pos_x' and 'pos_y'. Assign x to -112.710534, and y to 51.465185. This acts as the latitude and longitude of the rover.
    #         Make a TextDef object with a font size of 10px aligned at the bottom-left of the map, this should show the 'coordinates' of the rover. An example may look like this '(150, 85)'
    #         It is recomended that you round the position to a certain decimal number when displaying the text.








    # Since we want these EventDef values to change, we can use buttons to si`  1qmulate movement of the rover.
    # ButtonDef are objects that can modify values in many different ways.
    # We also need to convert the latitude and longitude into appropriate values for displaying position on our map.
    # EventListener evaluates EventDefs based on given conditions, useful for converting data.
    # TASK 5. Make 4 ButtonDef objects, these buttons should target directional keys (WASD or Arrow Keys), and modify the values to where it changes both x and y values by 0.00001 every second when held.
    #         Make 2 EventDef objects, call these map_pos_x and map_pos_y and set it to 0.
    #         Make 2 EventListener objects. This takes the rover's position, and updates the map's position. This should have passthrough = True, and uses a transform equation that negates the base position, and divides the result by / 0.0000001.








    # We now see the coordinates change when we move, now lets focus on the objects within the map.
    # TASK 6. Make a PolygonDef that acts as the rover's position, this should be a diamond and using a reasonable size and color. This will be at the center of the screen and will not move.
    #         Make another PolygonDef with the same size and different color, but with their pos_fn using the rover's x and y values with another offset. This will act as a marker for now.
    #         Make a TextDef that acts as the marker's name. You can name this anything for now. It should be above the marker with a font size of 8px with the same color as the marker.








    # This visualises the rover and the marker, but it would be useful if we made it so that there could be multiple markers.
    # Spawnable objects can be made by creating a WindowDef with a valid spawn_event value.
    # Since we want all objects to be contained in the map window, we can assign this window to the sub_windows list.
    # TASK 7. Move the PolygonDef that acts as the marker and the related TextDef into its own WindowDef, then assign it to the main window's sub_windows list.
    #         Do not worry about spawn_events as this will be done in the next task.








    # Now that we have the the window prepared, we can make it spawnable.
    # Spawned objects require an EventDef's value to become True. Once it reads its true, it spawns the window and sets the value to False.
    # An easy way to do this is to make a ButtonDef that when interacted with, sets this value to True, then spawns the WindowDef.
    # TASK 8. Make an EventDef named 'spawn_marker' set to False. Then add a button that sets this value to True when interacted.
    #         Once the EventDef and ButtonDef is made, make the WindowDef spawnable.








    # Spawning these markers works, however you should notice that they all spawn on the exact same spot.
    # A solution to this is to make markers spawn at the spot you click on the map.
    # get_spawn_mouse_norm() is a function you can call that takes the mouse's normalized position relative to the current window it is being used in.
    # You can use get_spawn_mouse_norm().x to get the mouse's normalized x value and get_spawn_mouse_norm().y to get the mouse's normalized y value.
    # TASK 9. Using spawn_static_values, set the values to the normalized mouse values and use these values to set the polygon's position.
    #         Make sure you consider the offsets of the pos values.
    #         Afterwards, make an invisible button that covers the whole map. Clicking on it will spawn a marker, you may optionally keep the key input if you like.








    # Now that we can create markers, we can begin by adding other important features.
    # Being able to zoom is important on a map, we can make a slider to allow this.
    # Sliders are objects that modifies values within a defined range.
    # TASK 10. Make an EventDef named 'zoom', and set it to 1.
    #          Make a SliderDef that modifies the value, range should be reasonable and have a minimum zoom above 0.
    #          (Skip implementing marker position changes based on zoom as this step is complicated.)








    # Currently there is no way to remove a marker. One simple way is to make the marker itself a button and to detect that input.
    # We can use phases to tell what state the window is in.
    # TASK 11. Use phase_event to let the window know its current state, and make the button set the phase to the delete threshold.
    #          (Take note of the descriptions of spawn_event_group and spawn_delete_threshold)








    # All markers also share the exact same text, which can be confusing. 
    # One solution is to prompt the user for inputs for the name before placing the marker.
    # First, lets make a window that pops up when the user attempts to place a marker. We will use phases to show and hide this prompt.
    # TASK 12. Create a new WindowDef inside sub_windows.
    #          Make a RectDef, this will act as the visible fill of the prompt.
    #          Make a TextDef, this will be a description at the top of the prompt.
    #          Make an EventDef named 'map_prompt_phase', this will output only 2 strings, either 'open', or 'close' (default) The WindowDef should have its own phase_event that takes in the new EventDef.
    #          Add phases to RectDef and TextDef. This should include a phase for 'open', and 'close'. Have the color of both objects invisible for base values and 'close' phase, and visible during 'open' phase.
    #          Make a test button that cycles through 'open' and 'close' phase, this should open and close the prompt.
    







    # Lets now make the prompt functional.
    # TASK 13. Make 2 EventDef named 'map_marker_x' and 'map_marker_y', set them to 0.
    #          Make 2 EventListeners both with wait_for_updates that targets 'map_prompt_phase', takes in the mouse's normalized position, and outputs to the new EventDefs.
    #          spawn_static_values should be modified to take the 'map_marker_x' and 'map_marker_y' position instead of the mouse's normalized position.
    #          Make a ButtonDef inside the prompt window that triggers the spawning of the marker (this should behave like the invisible button).
    #          The invisible button that triggers upon clicking on the map should be modified to set 'map_prompt_phase' to 'open'.
    #          Make a EventListener with wait_for_updates that waits for the marker to be spawned before setting 'map_prompt_phase' to 'close'.
    







    # With the prompt working, we can now implement changing the marker's text.
    # TASK 14. Make a EventDef named 'map_marker_name', set it to ''.
    #          Make a TextboxDef within the prompt window, this will output its values to 'map_marker_name'.
    #          Update the marker to receive the marker's name as the displayed text.





