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
    SliderDef,                                                                 # SliderDef
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
import numpy as np

register_event(EventDef(name="graph_time", value=3600.0))
register_event(EventDef(name="graph_steps", value=4))

WINDOW_LAYER = 0

text_defs_list = []
graph_defs_list = []
text_strs=['GRAPH 1', 'GRAPH 2', 'GRAPH 3', 'GRAPH 4', 'GRAPH 5', 'GRAPH 6']
graph_points = [
    [P(0.0, 0.00), P(0.3, 0.34), P(10, 25), P(-30, -10)],
    [P(0.3, 0.00), P(0.6, 0.34), P(0, 25), P(-30, -10)],
    [P(0.0, 0.34), P(0.3, 0.66), P(10, 10), P(-30, -10)],
    [P(0.3, 0.34), P(0.6, 0.66), P(0, 10), P(-30, -10)],
    [P(0.0, 0.66), P(0.3, 1.00), P(10, 10), P(-30, -25)],
    [P(0.3, 0.66), P(0.6, 1.00), P(0, 10), P(-30, -25)],
]
motor_vals=[
    [P(0.75, 0.20), P(1.00, 0.20), P(0.75, 0.30), P(1.00, 0.30), P(0.75, 0.40), P(1.00, 0.40)],
    ['FL', 'FR', 'ML', 'MR', 'BL', 'BR'],
    [(0.0, 1.0), (1.0, 1.0), (0.0, 0.5), (1.0, 0.5), (0.0, 0.0), (1.0, 0.0)],
    ['AMP', 'VOLT', 'RPM'],
    [30, -30, 30, -30, 30, -30],
    [-20, -20, -10, -10, 0, 0],
    ['test_value1', 'test_value2', 'test_value3'],
    [(0.0, 1.0), (1.0, 1.0), (0.0, 0.5), (1.0, 0.5), (0.0, 0.0), (1.0, 0.0)],
]
for i in range(6):
    text_defs_list.append(TextDef(p=motor_vals[0][i], px=P(0, 0), text=motor_vals[1][i], h_align=motor_vals[2][i][0], v_align=motor_vals[2][i][1], font_size=15.0, fill_color=QColor(255, 255, 255, 255)))

    text_defs_list.append(TextDef(p=motor_vals[0][i], px=P(motor_vals[4][i], motor_vals[5][i]),      text=motor_vals[3][0], h_align=motor_vals[2][i][0], v_align=motor_vals[2][i][1], font_size=9.0, fill_color=QColor(255, 255, 255, 170)))
    text_defs_list.append(TextDef(p=motor_vals[0][i], px=P(motor_vals[4][i], motor_vals[5][i] + 10), text=motor_vals[3][1], h_align=motor_vals[2][i][0], v_align=motor_vals[2][i][1], font_size=9.0, fill_color=QColor(255, 255, 255, 170)))
    text_defs_list.append(TextDef(p=motor_vals[0][i], px=P(motor_vals[4][i], motor_vals[5][i] + 20), text=motor_vals[3][2], h_align=motor_vals[2][i][0], v_align=motor_vals[2][i][1], font_size=9.0, fill_color=QColor(255, 255, 255, 170)))

    text_defs_list.append(TextDef(p=P(0.875, motor_vals[0][i].y), px=P(5 * -np.sign(motor_vals[4][i]), motor_vals[5][i]),      text='<#>', h_align=1-motor_vals[2][i][0], v_align=motor_vals[2][i][1], font_size=9.0, fill_color=QColor(255, 255, 255, 170), text_fn=lambda ctx: '{:.4f}'.format(ctx[motor_vals[6][0]]['latest'])))
    text_defs_list.append(TextDef(p=P(0.875, motor_vals[0][i].y), px=P(5 * -np.sign(motor_vals[4][i]), motor_vals[5][i] + 10), text='<#>', h_align=1-motor_vals[2][i][0], v_align=motor_vals[2][i][1], font_size=9.0, fill_color=QColor(255, 255, 255, 170), text_fn=lambda ctx: '{:.4f}'.format(ctx[motor_vals[6][1]]['latest'])))
    text_defs_list.append(TextDef(p=P(0.875, motor_vals[0][i].y), px=P(5 * -np.sign(motor_vals[4][i]), motor_vals[5][i] + 20), text='<#>', h_align=1-motor_vals[2][i][0], v_align=motor_vals[2][i][1], font_size=9.0, fill_color=QColor(255, 255, 255, 170), text_fn=lambda ctx: '{:.4f}'.format(ctx[motor_vals[6][2]]['latest'])))

for i in range(6):
    text_defs_list.append(TextDef(
        p=P((graph_points[i][0].x + graph_points[i][1].x) / 2, graph_points[i][0].y),
        px=P((graph_points[i][2].x + graph_points[i][3].x) / 2, graph_points[i][2].y),
        h_align=0.5, v_align=1.0,
        text=text_strs[i], font_size=10.0,
    ))
    graph_defs_list.append(GraphDef(
        p1=graph_points[i][0], p2=graph_points[i][1], px1=graph_points[i][2], px2=graph_points[i][3],
        series=[
            SeriesDef(value_fn=lambda ctx: ctx['test_value1']['latest'], name='value1', color=QColor(255, 106, 106, 255), outline_width=1.0, fill_opacity=0.08),
            SeriesDef(value_fn=lambda ctx: ctx['test_value2']['latest'], name='value2', color=QColor(255, 111, 151, 255), outline_width=1.0, fill_opacity=0.08),
            SeriesDef(value_fn=lambda ctx: ctx['test_value3']['latest'], name='value3', color=QColor(255, 126, 192, 255), outline_width=1.0, fill_opacity=0.08),
            SeriesDef(value_fn=lambda ctx: ctx['test_value4']['latest'], name='value4', color=QColor(238, 145, 227, 255), outline_width=1.0, fill_opacity=0.08),
            SeriesDef(value_fn=lambda ctx: ctx['test_value5']['latest'], name='value5', color=QColor(214, 165, 252, 255), outline_width=1.0, fill_opacity=0.08),
            SeriesDef(value_fn=lambda ctx: ctx['test_value6']['latest'], name='value6', color=QColor(187, 184, 255, 255), outline_width=1.0, fill_opacity=0.08),
            SeriesDef(value_fn=lambda ctx: ctx['test_value7']['latest'], name='value7', color=QColor(164, 200, 255, 255), outline_width=1.0, fill_opacity=0.08),
            SeriesDef(value_fn=lambda ctx: ctx['test_value8']['latest'], name='value8', color=QColor(150, 213, 255, 255), outline_width=1.0, fill_opacity=0.08),
            SeriesDef(value_fn=lambda ctx: ctx['test_value9']['latest'], name='value9', color=QColor(149, 224, 255, 255), outline_width=1.0, fill_opacity=0.08),
        ],
        max_time=10.0,#lambda: float(get_event('graph_time').value),
        start_display_time = 1.0,
        end_display_time = 10.0,
        value_range=(0.0, 100.0),
        value_color=QColor(255, 255, 255, 255),
        ease_dur=0.3,
        ease_type=QEasingCurve.OutQuint,
        dynamic_scale=5.0,
        show_minmax = True,
        show_step = True,
        step_count = lambda: int(get_event('graph_steps').value),
        label_align='left',
        size_minmax = 6.0,
        size_step = 6.0,
        size_name = 6.0,
        stack=True,
        update_interval=1,
    ))

info_window = WindowDef(
    p1=P(0.0, 0.6), p2=P(0.5, 1.0), px1=P(0, 0), px2=P(-157, 0),
    hidden_event=get_event('window_disabled_info'),
    phase_event=get_event('content_phase_info'),
    phases={
        'open': Phase([WindowTween(p1=get_event('info_window_p1'), p2=get_event('info_window_p2'), px1=get_event('info_window_px1'), px2=get_event('info_window_px2'), start=0.0, dur=1.0, ease=QEasingCurve.OutQuint)], update_retrigger=True)
    },
    polygon_defs=[
        # PolygonDef(p=[P(1, 1), P(1, 1)], px=[P(0, 0), P(0, 0)], fill_color=QColor(255, 255, 255, 0), outline_width=2, closed=False, gradient=get_gradient('alt_color_outline'), phase_override=get_event('main_page'), phases={
        #     'open': Phase([PolygonTween(p=[P(0, 0), P(1, 0)], px=[P(0, 0), P(0, 0)], start=1.0, dur=0.5, ease=QEasingCurve.OutQuint)])
        # }),
        RectDef(p1=P(0.75, 0), p2=P(0.875, 0.20), px1=P(0, 0), px2=P(-5, 0), fill_color=QColor(50, 50, 50, 255)),
        RectDef(p1=P(0.875, 0), p2=P(1.00, 0.20), px1=P(5, 0), px2=P(0, 0), fill_color=QColor(50, 50, 50, 255)),
        RectDef(p1=P(0.75, 0.40), p2=P(0.875, 0.60), px1=P(0, 0), px2=P(-5, 0), fill_color=QColor(50, 50, 50, 255)),
        RectDef(p1=P(0.875, 0.40), p2=P(1.00, 0.60), px1=P(5, 0), px2=P(0, 0), fill_color=QColor(50, 50, 50, 255)),
    ],
    text_defs=[
    ] + text_defs_list,
    graph_defs=graph_defs_list,
)

WINDOW_DEFS = []
WINDOW_DEFS.append(info_window)

register_windows(WINDOW_LAYER, WINDOW_DEFS)

# WINDOW_LAYER = 2

# register_event(EventDef(name='size',     value=10))

# WINDOW_DEFS = [
#     WindowDef(
#         p1=P(0.5, 0.5), p2=P(0.5, 0.5), px1=P(-940, -520), px2=P(940, 520),
#         polygon_defs=[
#             RectDef(p1=P(0, 0.0), p2=P(1, 1), fill_color=QColor(30, 30, 30)),
#         ],
#     ),
#     WindowDef(
#         p1=P(0.5, 0.5), p2=P(0.5, 0.5), px1=P(-920, -500), px2=P(920, 500),
#         polygon_defs=[
#             RectDef(p1=P(0, 0), p2=P(0.18, 0.2), px1=P(-5, -5), px2=P(5, 5), fill_color=QColor(50, 50, 50)),
#             RectDef(p1=P(0.2, 0), p2=P(0.38, 0.2), px1=P(-5, -5), px2=P(5, 5), fill_color=QColor(50, 50, 50)),
#             RectDef(p1=P(0, 0.4), p2=P(0.18, 0.61), px1=P(-5, -5), px2=P(5, 5), fill_color=QColor(50, 50, 50)),
#             RectDef(p1=P(0.2, 0.4), p2=P(0.38, 0.61), px1=P(-5, -5), px2=P(5, 5), fill_color=QColor(50, 50, 50)),

#             RectDef(p1=P(0, 0), p2=P(0.38, 0.61), px1=P(-5, -5), px2=P(5, 5), outline_width=2, outline_color=QColor(255, 255, 255, 255), fill_color=QColor(50, 50, 50, 0)),
#         ],
#         text_defs=[
#             #----------------------------------- Steer info
#             # steer 0
#             TextDef(p=P(0, 0), px=P(0, 0), h_align=0, v_align=0, font_size=get_event("size").value, text="STEER 0", bold=True, fill_color=QColor(180, 180, 255, 255), uniform_scale=False),
#             TextDef(p=P(0, 0), px=P(0, 20), h_align=0, v_align=0, font_size=get_event("size").value, text="Amps: <#> A", text_fn= lambda ctx: f"{ctx[f'amps_wheel_0']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0, 0), px=P(0, 40), h_align=0, v_align=0, font_size=get_event("size").value, text="Volts: <#> V", text_fn= lambda ctx: f"{ctx[f'volts_wheel_0']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0, 0), px=P(0, 60), h_align=0, v_align=0, font_size=get_event("size").value, text="RPM: <#> RPM", text_fn= lambda ctx: f"{ctx[f'rpm_wheel_0']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0, 0), px=P(0, 80), h_align=0, v_align=0, font_size=get_event("size").value, text="Degrees: <#> rad", text_fn= lambda ctx: f"{ctx[f'steer_angle_0']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0, 0), px=P(0, 100), h_align=0, v_align=0, font_size=get_event("size").value, text="Req_degrees: <#> rad", text_fn= lambda ctx: f"{ctx[f'req_steer_angle_0']['latest']:.2f}", uniform_scale=False),
#             # steer 1
#             TextDef(p=P(0.3, 0), px=P(0, 0), h_align=0, v_align=0, font_size=get_event("size").value, text="STEER 1", bold=True, fill_color=QColor(180, 180, 255, 255), uniform_scale=False),
#             TextDef(p=P(0.3, 0), px=P(0, 20), h_align=0, v_align=0, font_size=get_event("size").value, text="Amps: <#> A", text_fn= lambda ctx: f"{ctx[f'amps_wheel_1']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.3, 0), px=P(0, 40), h_align=0, v_align=0, font_size=get_event("size").value, text="Volts: <#> V", text_fn= lambda ctx: f"{ctx[f'volts_wheel_1']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.3, 0), px=P(0, 60), h_align=0, v_align=0, font_size=get_event("size").value, text="RPM: <#> RPM", text_fn= lambda ctx: f"{ctx[f'rpm_wheel_1']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.3, 0), px=P(0, 80), h_align=0, v_align=0, font_size=get_event("size").value, text="Degrees: <#> rad", text_fn= lambda ctx: f"{ctx[f'steer_angle_1']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.3, 0), px=P(0, 100), h_align=0, v_align=0, font_size=get_event("size").value, text="Req_degrees: <#> rad", text_fn= lambda ctx: f"{ctx[f'req_steer_angle_1']['latest']:.2f}", uniform_scale=False),
#             # steer 4
#             TextDef(p=P(0, 0.5), px=P(0, 0), h_align=0, v_align=0, font_size=get_event("size").value, text="STEER 4", bold=True, fill_color=QColor(180, 180, 255, 255), uniform_scale=False),
#             TextDef(p=P(0, 0.5), px=P(0, 20), h_align=0, v_align=0, font_size=get_event("size").value, text="Amps: <#> A", text_fn= lambda ctx: f"{ctx[f'amps_wheel_4']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0, 0.5), px=P(0, 40), h_align=0, v_align=0, font_size=get_event("size").value, text="Volts: <#> V", text_fn= lambda ctx: f"{ctx[f'volts_wheel_4']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0, 0.5), px=P(0, 60), h_align=0, v_align=0, font_size=get_event("size").value, text="RPM: <#> RPM", text_fn= lambda ctx: f"{ctx[f'rpm_wheel_4']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0, 0.5), px=P(0, 80), h_align=0, v_align=0, font_size=get_event("size").value, text="Degrees: <#> rad", text_fn= lambda ctx: f"{ctx[f'steer_angle_4']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0, 0.5), px=P(0, 100), h_align=0, v_align=0, font_size=get_event("size").value, text="Req_degrees: <#> rad", text_fn= lambda ctx: f"{ctx[f'req_steer_angle_4']['latest']:.2f}", uniform_scale=False),
#             # steer 5
#             TextDef(p=P(0.3, 0.5), px=P(0, 0), h_align=0, v_align=0, font_size=get_event("size").value, text="STEER 5", bold=True, fill_color=QColor(180, 180, 255, 255), uniform_scale=False),
#             TextDef(p=P(0.3, 0.5), px=P(0, 20), h_align=0, v_align=0, font_size=get_event("size").value, text="Amps: <#> A", text_fn= lambda ctx: f"{ctx[f'amps_wheel_5']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.3, 0.5), px=P(0, 40), h_align=0, v_align=0, font_size=get_event("size").value, text="Volts: <#> V", text_fn= lambda ctx: f"{ctx[f'volts_wheel_5']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.3, 0.5), px=P(0, 60), h_align=0, v_align=0, font_size=get_event("size").value, text="RPM: <#> RPM", text_fn= lambda ctx: f"{ctx[f'rpm_wheel_5']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.3, 0.5), px=P(0, 80), h_align=0, v_align=0, font_size=get_event("size").value, text="Degrees: <#> rad", text_fn= lambda ctx: f"{ctx[f'steer_angle_5']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.3, 0.5), px=P(0, 100), h_align=0, v_align=0, font_size=get_event("size").value, text="Req_degrees: <#> rad", text_fn= lambda ctx: f"{ctx[f'req_steer_angle_5']['latest']:.2f}", uniform_scale=False),

#             #----------------------------------- Wheel info
#             # wheel 0
#             TextDef(p=P(0.1, 0.1), px=P(0, 0), h_align=0, v_align=0, font_size=get_event("size").value, text="WHEEL 0", bold=True, fill_color=QColor(180, 180, 255, 255), uniform_scale=False),
#             TextDef(p=P(0.1, 0.1), px=P(0, 20), h_align=0, v_align=0, font_size=get_event("size").value, text="Amps: <#> A", text_fn= lambda ctx: f"{ctx[f'amps_wheel_0']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.1, 0.1), px=P(0, 40), h_align=0, v_align=0, font_size=get_event("size").value, text="Volts: <#> V", text_fn= lambda ctx: f"{ctx[f'volts_wheel_0']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.1, 0.1), px=P(0, 60), h_align=0, v_align=0, font_size=get_event("size").value, text="RPM: <#> RPM", text_fn= lambda ctx: f"{ctx[f'rpm_wheel_0']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.1, 0.1), px=P(0, 80), h_align=0, v_align=0, font_size=get_event("size").value, text="Req_RPM : <#> RPM", text_fn= lambda ctx: f"{ctx[f'req_rpm_wheel_0']['latest']:.2f}", uniform_scale=False),
#             # wheel 1
#             TextDef(p=P(0.2, 0.1), px=P(0, 0), h_align=0, v_align=0, font_size=get_event("size").value, text="WHEEL 1", bold=True, fill_color=QColor(180, 180, 255, 255), uniform_scale=False),
#             TextDef(p=P(0.2, 0.1), px=P(0, 20), h_align=0, v_align=0, font_size=get_event("size").value, text="Amps: <#> A", text_fn= lambda ctx: f"{ctx[f'amps_wheel_1']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.2, 0.1), px=P(0, 40), h_align=0, v_align=0, font_size=get_event("size").value, text="Volts: <#> V", text_fn= lambda ctx: f"{ctx[f'volts_wheel_1']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.2, 0.1), px=P(0, 60), h_align=0, v_align=0, font_size=get_event("size").value, text="RPM: <#> RPM", text_fn= lambda ctx: f"{ctx[f'rpm_wheel_1']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.2, 0.1), px=P(0, 80), h_align=0, v_align=0, font_size=get_event("size").value, text="Req_RPM : <#> RPM", text_fn= lambda ctx: f"{ctx[f'req_rpm_wheel_1']['latest']:.2f}", uniform_scale=False),
#             # wheel 2
#             TextDef(p=P(0.1, 0.25), px=P(0, 0), h_align=0, v_align=0, font_size=get_event("size").value, text="WHEEL 2", bold=True, fill_color=QColor(180, 180, 255, 255), uniform_scale=False),
#             TextDef(p=P(0.1, 0.25), px=P(0, 20), h_align=0, v_align=0, font_size=get_event("size").value, text="Amps: <#> A", text_fn= lambda ctx: f"{ctx[f'amps_wheel_2']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.1, 0.25), px=P(0, 40), h_align=0, v_align=0, font_size=get_event("size").value, text="Volts: <#> V", text_fn= lambda ctx: f"{ctx[f'volts_wheel_2']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.1, 0.25), px=P(0, 60), h_align=0, v_align=0, font_size=get_event("size").value, text="RPM: <#> RPM", text_fn= lambda ctx: f"{ctx[f'rpm_wheel_2']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.1, 0.25), px=P(0, 80), h_align=0, v_align=0, font_size=get_event("size").value, text="Req_RPM : <#> RPM", text_fn= lambda ctx: f"{ctx[f'req_rpm_wheel_2']['latest']:.2f}", uniform_scale=False),
#             # wheel 3
#             TextDef(p=P(0.2, 0.25), px=P(0, 0), h_align=0, v_align=0, font_size=get_event("size").value, text="WHEEL 3", bold=True, fill_color=QColor(180, 180, 255, 255), uniform_scale=False),
#             TextDef(p=P(0.2, 0.25), px=P(0, 20), h_align=0, v_align=0, font_size=get_event("size").value, text="Amps: <#> A", text_fn= lambda ctx: f"{ctx[f'amps_wheel_3']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.2, 0.25), px=P(0, 40), h_align=0, v_align=0, font_size=get_event("size").value, text="Volts: <#> V", text_fn= lambda ctx: f"{ctx[f'volts_wheel_3']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.2, 0.25), px=P(0, 60), h_align=0, v_align=0, font_size=get_event("size").value, text="RPM: <#> RPM", text_fn= lambda ctx: f"{ctx[f'rpm_wheel_3']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.2, 0.25), px=P(0, 80), h_align=0, v_align=0, font_size=get_event("size").value, text="Req_RPM : <#> RPM", text_fn= lambda ctx: f"{ctx[f'req_rpm_wheel_3']['latest']:.2f}", uniform_scale=False),
#             # wheel 4
#             TextDef(p=P(0.1, 0.4), px=P(0, 0), h_align=0, v_align=0, font_size=get_event("size").value, text="WHEEL 4", bold=True, fill_color=QColor(180, 180, 255, 255), uniform_scale=False),
#             TextDef(p=P(0.1, 0.4), px=P(0, 20), h_align=0, v_align=0, font_size=get_event("size").value, text="Amps: <#> A", text_fn= lambda ctx: f"{ctx[f'amps_wheel_4']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.1, 0.4), px=P(0, 40), h_align=0, v_align=0, font_size=get_event("size").value, text="Volts: <#> V", text_fn= lambda ctx: f"{ctx[f'volts_wheel_4']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.1, 0.4), px=P(0, 60), h_align=0, v_align=0, font_size=get_event("size").value, text="RPM: <#> RPM", text_fn= lambda ctx: f"{ctx[f'rpm_wheel_4']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.1, 0.4), px=P(0, 80), h_align=0, v_align=0, font_size=get_event("size").value, text="Req_RPM : <#> RPM", text_fn= lambda ctx: f"{ctx[f'req_rpm_wheel_4']['latest']:.2f}", uniform_scale=False),
#             # wheel 5
#             TextDef(p=P(0.2, 0.4), px=P(0, 0), h_align=0, v_align=0, font_size=get_event("size").value, text="WHEEL 5", bold=True, fill_color=QColor(180, 180, 255, 255), uniform_scale=False),
#             TextDef(p=P(0.2, 0.4), px=P(0, 20), h_align=0, v_align=0, font_size=get_event("size").value, text="Amps: <#> A", text_fn= lambda ctx: f"{ctx[f'amps_wheel_5']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.2, 0.4), px=P(0, 40), h_align=0, v_align=0, font_size=get_event("size").value, text="Volts: <#> V", text_fn= lambda ctx: f"{ctx[f'volts_wheel_5']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.2, 0.4), px=P(0, 60), h_align=0, v_align=0, font_size=get_event("size").value, text="RPM: <#> RPM", text_fn= lambda ctx: f"{ctx[f'rpm_wheel_5']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.2, 0.4), px=P(0, 80), h_align=0, v_align=0, font_size=get_event("size").value, text="Req_RPM : <#> rpm", text_fn= lambda ctx: f"{ctx[f'req_rpm_wheel_5']['latest']:.2f}", uniform_scale=False),

#             #----------------------------------- Arm info
#             # Arm 5
#             TextDef(p=P(0.4, 0), px=P(0, 0), h_align=0, v_align=0, font_size=get_event("size").value, text="Hand joint (Arm 5)", bold=True, fill_color=QColor(180, 255, 180, 255), uniform_scale=False),
#             TextDef(p=P(0.4, 0), px=P(0, 20), h_align=0, v_align=0, font_size=get_event("size").value, text="Amps: <#> A", text_fn= lambda ctx: f"{ctx[f'amps_arm_5']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.4, 0), px=P(0, 40), h_align=0, v_align=0, font_size=get_event("size").value, text="Volts: <#> V", text_fn= lambda ctx: f"{ctx[f'volts_arm_5']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.4, 0), px=P(0, 60), h_align=0, v_align=0, font_size=get_event("size").value, text="RPM: <#> RPM", text_fn= lambda ctx: f"{ctx[f'rpm_arm_5']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.4, 0), px=P(0, 80), h_align=0, v_align=0, font_size=get_event("size").value, text="Encoder in: <#> deg", text_fn= lambda ctx: f"{ctx[f'encoder_in_5']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.4, 0), px=P(0, 100), h_align=0, v_align=0, font_size=get_event("size").value, text="Encoder out: <#> deg", text_fn= lambda ctx: f"{ctx[f'encoder_out_5']['latest']:.2f}", uniform_scale=False),

#             # Arm 4
#             TextDef(p=P(0.4, 0.15), px=P(0, 0), h_align=0, v_align=0, font_size=get_event("size").value, text="Rotation joint 2 (Arm 4)", bold=True, fill_color=QColor(180, 255, 180, 255), uniform_scale=False),
#             TextDef(p=P(0.4, 0.15), px=P(0, 20), h_align=0, v_align=0, font_size=get_event("size").value, text="Amps: <#> A", text_fn= lambda ctx: f"{ctx[f'amps_arm_4']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.4, 0.15), px=P(0, 40), h_align=0, v_align=0, font_size=get_event("size").value, text="Volts: <#> V", text_fn= lambda ctx: f"{ctx[f'volts_arm_4']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.4, 0.15), px=P(0, 60), h_align=0, v_align=0, font_size=get_event("size").value, text="RPM: <#> RPM", text_fn= lambda ctx: f"{ctx[f'rpm_arm_4']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.4, 0.15), px=P(0, 80), h_align=0, v_align=0, font_size=get_event("size").value, text="Encoder in: <#> deg", text_fn= lambda ctx: f"{ctx[f'encoder_in_4']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.4, 0.15), px=P(0, 100), h_align=0, v_align=0, font_size=get_event("size").value, text="Encoder out: <#> deg", text_fn= lambda ctx: f"{ctx[f'encoder_out_4']['latest']:.2f}", uniform_scale=False),

#           # Arm 3
#             TextDef(p=P(0.4, 0.30), px=P(0, 0), h_align=0, v_align=0, font_size=get_event("size").value, text="Bending joint 2 (Arm 3)", bold=True, fill_color=QColor(180, 255, 180, 255), uniform_scale=False),
#             TextDef(p=P(0.4, 0.30), px=P(0, 20), h_align=0, v_align=0, font_size=get_event("size").value, text="Amps: <#> A", text_fn= lambda ctx: f"{ctx[f'amps_arm_3']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.4, 0.30), px=P(0, 40), h_align=0, v_align=0, font_size=get_event("size").value, text="Volts: <#> V", text_fn= lambda ctx: f"{ctx[f'volts_arm_3']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.4, 0.30), px=P(0, 60), h_align=0, v_align=0, font_size=get_event("size").value, text="RPM: <#> RPM", text_fn= lambda ctx: f"{ctx[f'rpm_arm_3']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.4, 0.30), px=P(0, 80), h_align=0, v_align=0, font_size=get_event("size").value, text="Encoder in: <#> deg", text_fn= lambda ctx: f"{ctx[f'encoder_in_3']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.4, 0.30), px=P(0, 100), h_align=0, v_align=0, font_size=get_event("size").value, text="Encoder out: <#> deg", text_fn= lambda ctx: f"{ctx[f'encoder_out_3']['latest']:.2f}", uniform_scale=False),

#             # Arm 2
#             TextDef(p=P(0.4, 0.45), px=P(0, 0), h_align=0, v_align=0, font_size=get_event("size").value, text="Rotation joint 1 (Arm 2)", bold=True, fill_color=QColor(180, 255, 180, 255), uniform_scale=False),
#             TextDef(p=P(0.4, 0.45), px=P(0, 20), h_align=0, v_align=0, font_size=get_event("size").value, text="Amps: <#> A", text_fn= lambda ctx: f"{ctx[f'amps_arm_2']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.4, 0.45), px=P(0, 40), h_align=0, v_align=0, font_size=get_event("size").value, text="Volts: <#> V", text_fn= lambda ctx: f"{ctx[f'volts_arm_2']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.4, 0.45), px=P(0, 60), h_align=0, v_align=0, font_size=get_event("size").value, text="RPM: <#> RPM", text_fn= lambda ctx: f"{ctx[f'rpm_arm_2']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.4, 0.45), px=P(0, 80), h_align=0, v_align=0, font_size=get_event("size").value, text="Encoder in: <#> deg", text_fn= lambda ctx: f"{ctx[f'encoder_in_2']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.4, 0.45), px=P(0, 100), h_align=0, v_align=0, font_size=get_event("size").value, text="Encoder out: <#> deg", text_fn= lambda ctx: f"{ctx[f'encoder_out_2']['latest']:.2f}", uniform_scale=False),

#             # Arm 1
#             TextDef(p=P(0.4, 0.60), px=P(0, 0), h_align=0, v_align=0, font_size=get_event("size").value, text="Bending joint 1 (Arm 1)", bold=True, fill_color=QColor(180, 255, 180, 255), uniform_scale=False),
#             TextDef(p=P(0.4, 0.60), px=P(0, 20), h_align=0, v_align=0, font_size=get_event("size").value, text="Amps: <#> A", text_fn= lambda ctx: f"{ctx[f'amps_arm_1']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.4, 0.60), px=P(0, 40), h_align=0, v_align=0, font_size=get_event("size").value, text="Volts: <#> V", text_fn= lambda ctx: f"{ctx[f'volts_arm_1']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.4, 0.60), px=P(0, 60), h_align=0, v_align=0, font_size=get_event("size").value, text="RPM: <#> RPM", text_fn= lambda ctx: f"{ctx[f'rpm_arm_1']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.4, 0.60), px=P(0, 80), h_align=0, v_align=0, font_size=get_event("size").value, text="Encoder in: <#> deg", text_fn= lambda ctx: f"{ctx[f'encoder_in_1']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.4, 0.60), px=P(0, 100), h_align=0, v_align=0, font_size=get_event("size").value, text="Encoder out: <#> deg", text_fn= lambda ctx: f"{ctx[f'encoder_out_1']['latest']:.2f}", uniform_scale=False),

#             # Arm 0
#             TextDef(p=P(0.4, 0.75), px=P(0, 0), h_align=0, v_align=0, font_size=get_event("size").value, text="Base (Arm 0)", bold=True, fill_color=QColor(180, 255, 180, 255), uniform_scale=False),
#             TextDef(p=P(0.4, 0.75), px=P(0, 20), h_align=0, v_align=0, font_size=get_event("size").value, text="Amps: <#> A", text_fn= lambda ctx: f"{ctx[f'amps_arm_0']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.4, 0.75), px=P(0, 40), h_align=0, v_align=0, font_size=get_event("size").value, text="Volts: <#> V", text_fn= lambda ctx: f"{ctx[f'volts_arm_0']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.4, 0.75), px=P(0, 60), h_align=0, v_align=0, font_size=get_event("size").value, text="RPM: <#> RPM", text_fn= lambda ctx: f"{ctx[f'rpm_arm_0']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.4, 0.75), px=P(0, 80), h_align=0, v_align=0, font_size=get_event("size").value, text="Encoder in: <#> deg", text_fn= lambda ctx: f"{ctx[f'encoder_in_0']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.4, 0.75), px=P(0, 100), h_align=0, v_align=0, font_size=get_event("size").value, text="Encoder out: <#> deg", text_fn= lambda ctx: f"{ctx[f'encoder_out_0']['latest']:.2f}", uniform_scale=False),

#             # ----------------------------------- Rover Motion
#             TextDef(p=P(0.6, 0), px=P(0, 0), h_align=0, v_align=0, font_size=get_event("size").value, text="Rover Motion", bold=True, fill_color=QColor(255, 180, 180, 255), uniform_scale=False),
#             TextDef(p=P(0.6, 0), px=P(0, 20), h_align=0, v_align=0, font_size=get_event("size").value, text="Speed: <#> km/h", text_fn= lambda ctx: f"{ctx[f'Speed']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.6, 0), px=P(0, 40), h_align=0, v_align=0, font_size=get_event("size").value, text="Heading: <#>°", text_fn= lambda ctx: f"{ctx[f'directon_degrees']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.6, 0), px=P(0, 60), h_align=0, v_align=0, font_size=get_event("size").value, text="Pitch: <#>°", text_fn= lambda ctx: f"{ctx[f'pitch']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.6, 0), px=P(0, 80), h_align=0, v_align=0, font_size=get_event("size").value, text="Roll: <#>°", text_fn= lambda ctx: f"{ctx[f'roll']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.6, 0), px=P(0, 100), h_align=0, v_align=0, font_size=get_event("size").value, text="Yaw: <#>°", text_fn= lambda ctx: f"{ctx[f'yaw']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.6, 0), px=P(0, 120), h_align=0, v_align=0, font_size=get_event("size").value, text="Acceleration: <#> m/s^2", text_fn= lambda ctx: f"{ctx[f'acceleration']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.6, 0), px=P(0, 140), h_align=0, v_align=0, font_size=get_event("size").value, text="Angular Velocity: <#> ω", text_fn= lambda ctx: f"{ctx[f'angular_velocity']['latest']:.2f}", uniform_scale=False),

#             # ------------------------------------ Battery
#             TextDef(p=P(0.8, 0), px=P(0, 0), h_align=0, v_align=0, font_size=get_event("size").value, text="Battery", bold=True, fill_color=QColor(255, 255, 150, 255), uniform_scale=False),
#             TextDef(p=P(0.8, 0), px=P(0, 20), h_align=0, v_align=0, font_size=get_event("size").value, text="Battery %: <#> %", text_fn= lambda ctx: f"{ctx[f'batt_percentage']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.8, 0), px=P(0, 40), h_align=0, v_align=0, font_size=get_event("size").value, text="Current Capacity: <#> Ah", text_fn= lambda ctx: f"{ctx[f'cur_batt_capacity']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.8, 0), px=P(0, 60), h_align=0, v_align=0, font_size=get_event("size").value, text="Max Capacity: <#> Ah", text_fn= lambda ctx: f"{ctx[f'max_batt_capacity']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.8, 0), px=P(0, 80), h_align=0, v_align=0, font_size=get_event("size").value, text="Voltage: <#> V", text_fn= lambda ctx: f"{ctx[f'batt_voltage']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.8, 0), px=P(0, 100), h_align=0, v_align=0, font_size=get_event("size").value, text="Current: <#> A", text_fn= lambda ctx: f"{ctx[f'batt_amps']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.8, 0), px=P(0, 120), h_align=0, v_align=0, font_size=get_event("size").value, text="Estimated runtime: <#> hrs", text_fn= lambda ctx: f"{ctx[f'est_batt_runtime']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.8, 0), px=P(0, 140), h_align=0, v_align=0, font_size=get_event("size").value, text="Power consumption: <#> kWh", text_fn= lambda ctx: f"{ctx[f'batt_pwr_consump']['latest']:.2f}", uniform_scale=False),

#             # ----------------------------------- Power consumption
#             TextDef(p=P(0.6, 0.2), px=P(0, 0), h_align=0, v_align=0, font_size=get_event("size").value, text="POWER CONSUMPTION", bold=True, fill_color=QColor(150, 255, 255, 255), uniform_scale=False),
#             TextDef(p=P(0.6, 0.2), px=P(0, 20), h_align=0, v_align=0, font_size=get_event("size").value, text="Total Power Consumption: <#> kWh", text_fn= lambda ctx: f"{ctx[f'tot_pwr_consump']['latest']:.2f}", uniform_scale=False),
#             # per system
#             TextDef(p=P(0.6, 0.2), px=P(0, 60), h_align=0, v_align=0, font_size=get_event("size").value, text="Per System", bold=True, fill_color=QColor(150, 255, 255, 255), uniform_scale=False),
#             TextDef(p=P(0.6, 0.2), px=P(0, 80), h_align=0, v_align=0, font_size=get_event("size").value, text="Drive: <#> kWh", text_fn= lambda ctx: f"{ctx[f'max_batt_capacity']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.6, 0.2), px=P(0, 100), h_align=0, v_align=0, font_size=get_event("size").value, text="Arm: <#> kWh", text_fn= lambda ctx: f"{ctx[f'batt_voltage']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.6, 0.2), px=P(0, 120), h_align=0, v_align=0, font_size=get_event("size").value, text="Science: <#> kWh", text_fn= lambda ctx: f"{ctx[f'batt_amps']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.6, 0.2), px=P(0, 140), h_align=0, v_align=0, font_size=get_event("size").value, text="Jetson: <#> kWh", text_fn= lambda ctx: f"{ctx[f'est_batt_runtime']['latest']:.2f}", uniform_scale=False),

#             # ----------------------------------- Science
#             TextDef(p=P(0.8, 0.2), px=P(0, 0), h_align=0, v_align=0, font_size=get_event("size").value, text="Science", bold=True, fill_color=QColor(255, 150, 255, 255), uniform_scale=False),
#             TextDef(p=P(0.8, 0.2), px=P(0, 20), h_align=0, v_align=0, font_size=get_event("size").value, text="Latitude: <#> DD", text_fn= lambda ctx: f"{ctx[f'latitude']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.8, 0.2), px=P(0, 40), h_align=0, v_align=0, font_size=get_event("size").value, text="Longitude: <#> DD", text_fn= lambda ctx: f"{ctx[f'longitude']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.8, 0.2), px=P(0, 60), h_align=0, v_align=0, font_size=get_event("size").value, text="Cardinal Dir: <#>", text_fn= lambda ctx: f"{ctx[f'cardinal_dir']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.8, 0.2), px=P(0, 80), h_align=0, v_align=0, font_size=get_event("size").value, text="External Tempurature: <#> °C", text_fn= lambda ctx: f"{ctx[f'ext_temp']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.8, 0.2), px=P(0, 100), h_align=0, v_align=0, font_size=get_event("size").value, text="Humidity: <#> %", text_fn= lambda ctx: f"{ctx[f'humidity']['latest']:.2f}", uniform_scale=False),

#             # ----------------------------------- Jetson
#             TextDef(p=P(0.6, 0.4), px=P(0, 0), h_align=0, v_align=0, font_size=get_event("size").value, text="Jetson", bold=True, fill_color=QColor(150, 180, 255, 255), uniform_scale=False),
#             TextDef(p=P(0.6, 0.4), px=P(0, 20), h_align=0, v_align=0, font_size=get_event("size").value, text="CPU usage: <#> %", text_fn= lambda ctx: f"{ctx[f'CPU_usage']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.6, 0.4), px=P(0, 40), h_align=0, v_align=0, font_size=get_event("size").value, text="GPU usage: <#> %", text_fn= lambda ctx: f"{ctx[f'GPU_usage']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.6, 0.4), px=P(0, 60), h_align=0, v_align=0, font_size=get_event("size").value, text="RAM usage: <#>%", text_fn= lambda ctx: f"{ctx[f'RAM_usage']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.6, 0.4), px=P(0, 80), h_align=0, v_align=0, font_size=get_event("size").value, text="Network usage: <#> %", text_fn= lambda ctx: f"{ctx[f'network_usage']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.6, 0.4), px=P(0, 100), h_align=0, v_align=0, font_size=get_event("size").value, text="Jetson power: <#> W", text_fn= lambda ctx: f"{ctx[f'jetson_power']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.6, 0.4), px=P(0, 120), h_align=0, v_align=0, font_size=get_event("size").value, text="NVENC: <#> %", text_fn= lambda ctx: f"{ctx[f'NVENC']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.6, 0.4), px=P(0, 140), h_align=0, v_align=0, font_size=get_event("size").value, text="NVDEC: <#> %", text_fn= lambda ctx: f"{ctx[f'NVDEC']['latest']:.2f}", uniform_scale=False),
#             TextDef(p=P(0.6, 0.4), px=P(0, 160), h_align=0, v_align=0, font_size=get_event("size").value, text="VIC: <#> %", text_fn= lambda ctx: f"{ctx[f'VIC']['latest']:.2f}", uniform_scale=False),
#         ]
#     ),
# ]

# WINDOW_DEFS = []
# WINDOW_DEFS.append(info_window)

# register_windows(WINDOW_LAYER, WINDOW_DEFS)