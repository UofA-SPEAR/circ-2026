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
    get_spawn_event, GROUP_EVENT, STATIC, get_spawn_mouse_norm, get_spawn_mouse_offset_px
)
from spear_gui.defs_02_shared_events import make_slider
import numpy as np

register_event(EventDef(name="graph_time", value=3600.0))
register_event(EventDef(name="graph_steps", value=4))

WINDOW_LAYER = 0

text_defs_list = []
graph_defs_list = []
graph_points = [
    [P(0.0, 0.00), P(0.3, 0.34), P(10, 25), P(-30, -10)],
    [P(0.3, 0.00), P(0.6, 0.34), P(0, 25), P(-30, -10)],
    [P(0.0, 0.34), P(0.3, 0.66), P(10, 10), P(-30, -10)],
    [P(0.3, 0.34), P(0.6, 0.66), P(0, 10), P(-30, -10)],
    [P(0.0, 0.66), P(0.3, 1.00), P(10, 10), P(-30, -25)],
    [P(0.3, 0.66), P(0.6, 1.00), P(0, 10), P(-30, -25)],
]

motor_vals=[
    [P(0.00, 1/3), P(1.00, 1/3), P(0.00, 1/2), P(1.00, 1/2), P(0.00, 2/3), P(1.00, 2/3)],
    ['FL', 'FR', 'ML', 'MR', 'BL', 'BR'],
    [(0.0, 1.0), (1.0, 1.0), (0.0, 0.5), (1.0, 0.5), (0.0, 0.0), (1.0, 0.0)],
    ['AMP', 'VOLT', 'RPM', 'ROT'],
    [30, -30, 30, -30, 30, -30],
    [-18, -18, -10, -10, 0, 0],
    ['test_value1', 'test_value2', 'test_value3', 'test_value4'],
    [(0.0, 1.0), (1.0, 1.0), (0.0, 0.5), (1.0, 0.5), (0.0, 0.0), (1.0, 0.0)],
]
for i in range(0, 6, 2):
    text_defs_list.append(TextDef(p=P(0.5, motor_vals[0][i].y), px=P(0, motor_vals[5][i]),      text=motor_vals[3][0], bold=True, h_align=0.5, v_align=motor_vals[2][i][1], font_size=9.0, fill_color=QColor(255, 255, 255, 170)))
    text_defs_list.append(TextDef(p=P(0.5, motor_vals[0][i].y), px=P(0, motor_vals[5][i] + 10), text=motor_vals[3][1], bold=True, h_align=0.5, v_align=motor_vals[2][i][1], font_size=9.0, fill_color=QColor(255, 255, 255, 170)))
    text_defs_list.append(TextDef(p=P(0.5, motor_vals[0][i].y), px=P(0, motor_vals[5][i] + 20), text=motor_vals[3][2], bold=True, h_align=0.5, v_align=motor_vals[2][i][1], font_size=9.0, fill_color=QColor(255, 255, 255, 170)))

for i in range(6):
    text_defs_list.append(TextDef(p=motor_vals[0][i], px=P((10 + 4 * round(((i + 1) % 5) / 4)) * np.sign(0.5 - motor_vals[2][i][0]), 0), text=motor_vals[1][i], italic=True, h_align=motor_vals[2][i][0], v_align=motor_vals[2][i][1], font_size=15.0, fill_color=QColor(255, 255, 255, 255)))

    text_defs_list.append(TextDef(p=P(0.5, motor_vals[0][i].y), px=P(20 * -np.sign(motor_vals[4][i]), motor_vals[5][i]),      text='<#>', h_align=1-motor_vals[2][i][0], v_align=motor_vals[2][i][1], font_size=9.0, font_family='Oxanium', fill_color=QColor(255, 255, 255, 170), text_fn=lambda ctx: '{:.2f}'.format(ctx[motor_vals[6][0]]['latest'])))
    text_defs_list.append(TextDef(p=P(0.5, motor_vals[0][i].y), px=P(20 * -np.sign(motor_vals[4][i]), motor_vals[5][i] + 10), text='<#>', h_align=1-motor_vals[2][i][0], v_align=motor_vals[2][i][1], font_size=9.0, font_family='Oxanium', fill_color=QColor(255, 255, 255, 170), text_fn=lambda ctx: '{:.2f}'.format(ctx[motor_vals[6][1]]['latest'])))
    text_defs_list.append(TextDef(p=P(0.5, motor_vals[0][i].y), px=P(20 * -np.sign(motor_vals[4][i]), motor_vals[5][i] + 20), text='<#>', h_align=1-motor_vals[2][i][0], v_align=motor_vals[2][i][1], font_size=9.0, font_family='Oxanium', fill_color=QColor(255, 255, 255, 170), text_fn=lambda ctx: (f'{round(ctx[motor_vals[6][2]]["latest"])}')))
    text_defs_list.append(TextDef(p=P(0.5, motor_vals[0][i].y), px=P(40 * -np.sign(motor_vals[4][i]), motor_vals[5][i] + 20), text='<#>', bold=True, h_align=1-motor_vals[2][i][0], v_align=motor_vals[2][i][1], font_size=9.0, font_family='Oxanium', fill_color=QColor(255, 100, 100, 170), text_fn=lambda ctx: (f'{round(ctx[motor_vals[6][3]]["latest"])}')))

for i in range(6):
    if i == 2 or i == 3:
        continue
    p_y = 0 if i < 3 else 1
    px_y = 0 if i < 3 else -18
    
    text_defs_list.append(TextDef(p=P(0.5, p_y), px=P(20 * -np.sign(motor_vals[4][i]), px_y),      text='<#>', h_align=1-motor_vals[2][i][0], v_align=1-motor_vals[2][i][1], font_size=9.0, font_family='Oxanium', fill_color=QColor(255, 255, 255, 170), text_fn=lambda ctx: '{:.2f}'.format(ctx[motor_vals[6][0]]['latest'])))
    text_defs_list.append(TextDef(p=P(0.5, p_y), px=P(20 * -np.sign(motor_vals[4][i]), px_y + 10), text='<#>', h_align=1-motor_vals[2][i][0], v_align=1-motor_vals[2][i][1], font_size=9.0, font_family='Oxanium', fill_color=QColor(255, 255, 255, 170), text_fn=lambda ctx: '{:.2f}'.format(ctx[motor_vals[6][1]]['latest'])))
    text_defs_list.append(TextDef(p=P(0.5, p_y), px=P(20 * -np.sign(motor_vals[4][i]), px_y + 20), text='<#>', h_align=1-motor_vals[2][i][0], v_align=1-motor_vals[2][i][1], font_size=9.0, font_family='Oxanium', fill_color=QColor(255, 255, 255, 170), text_fn=lambda ctx: (f'{round(ctx[motor_vals[6][2]]["latest"])}')))
    text_defs_list.append(TextDef(p=P(0.5, p_y), px=P(40 * -np.sign(motor_vals[4][i]), px_y + 20), text='<#>', bold=True, h_align=1-motor_vals[2][i][0], v_align=1-motor_vals[2][i][1], font_size=9.0, font_family='Oxanium', fill_color=QColor(255, 100, 100, 170), text_fn=lambda ctx: (f'{round(ctx[motor_vals[6][3]]["latest"])}')))
    
    if i == 1 or i == 4:
        continue

    text_defs_list.append(TextDef(p=P(0.5, p_y), px=P(0, px_y),      text=motor_vals[3][0], bold=True, h_align=0.5, v_align=1-motor_vals[2][i][1], font_size=9.0, fill_color=QColor(255, 255, 255, 170)))
    text_defs_list.append(TextDef(p=P(0.5, p_y), px=P(0, px_y + 10), text=motor_vals[3][1], bold=True, h_align=0.5, v_align=1-motor_vals[2][i][1], font_size=9.0, fill_color=QColor(255, 255, 255, 170)))
    text_defs_list.append(TextDef(p=P(0.5, p_y), px=P(0, px_y + 20), text=motor_vals[3][3], bold=True, h_align=0.5, v_align=1-motor_vals[2][i][1], font_size=9.0, fill_color=QColor(255, 255, 255, 170)))


graph_series=[
    [
        SeriesDef(value_fn=lambda ctx: ctx['test_value1']['latest'], name='value1', color=QColor(255, 106, 106, 255), outline_width=1.0, fill_opacity=0.08),
    ],
    [
        SeriesDef(value_fn=lambda ctx: ctx['joint_1_bus_voltage']['latest'], name='value1', color=QColor(255, 106, 106, 255), outline_width=1.0, fill_opacity=0.08),
        SeriesDef(value_fn=lambda ctx: ctx['joint_2_bus_voltage']['latest'], name='value2', color=QColor(255, 111, 151, 255), outline_width=1.0, fill_opacity=0.08),
        SeriesDef(value_fn=lambda ctx: ctx['joint_3_bus_voltage']['latest'], name='value3', color=QColor(255, 126, 192, 255), outline_width=1.0, fill_opacity=0.08),
        SeriesDef(value_fn=lambda ctx: ctx['joint_4_bus_voltage']['latest'], name='value4', color=QColor(238, 145, 227, 255), outline_width=1.0, fill_opacity=0.08),
        SeriesDef(value_fn=lambda ctx: ctx['joint_5_bus_voltage']['latest'], name='value5', color=QColor(214, 165, 252, 255), outline_width=1.0, fill_opacity=0.08),
    ],
    [
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
    [
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
    [
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
    [
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
]
graph_active =              [False, False, False, False, False, False]
graph_stack =               [False, False, True, True, True, True]
graph_max_time =            [360, 10, 10, 10, 10, 10]
graph_start_display_time =  [0, 0, 0, 0, 0, 0]
graph_end_display_time =    [360, 10, 10, 10, 10, 10]
graph_value_range =         [(0, 10), (0, 50), (0, 100), (0, 100), (0, 100), (0, 100)]
graph_update_interval =     [5, 1, 1, 1, 1, 1]

graph_text_defs_list = []
graph_names=[
    'BATTERY', 
    'ARM BUS VOLTAGE',# 'DRIVE MOTOR VOLTAGE', 
    'DRIVE MOTOR AMPS', 
    'DRIVE MOTOR RPM', 
    'STEER MOTOR VOLTAGE', 
    'STEER MOTOR AMPS',
    'STEER MOTOR RPM',
    'ARM MOTOR VOLTAGE',
    'ARM MOTOR AMPS',
    'POWER CONSUMPTION PER SYSTEM',
    'JETSON',
]

info_texts = []
info_buttons = []
info_sliders = []
total_graphs = 6

for i in range(total_graphs):
    register_event(EventDef(name=f'graph_{i}_active',             value=graph_active[i]))
    register_event(EventDef(name=f'graph_{i}_max_time',           value=graph_max_time[i]))
    register_event(EventDef(name=f'graph_{i}_start_display_time', value=graph_start_display_time[i]))
    register_event(EventDef(name=f'graph_{i}_end_display_time',   value=graph_end_display_time[i]))
    register_event(EventDef(name=f'graph_{i}_update_interval',    value=graph_update_interval[i]))
    
    edge_px = 75
    gap_px = 20
    max_width = 1920
    available_x = max_width - 2 * edge_px - (total_graphs - 1) * gap_px
    section_w = available_x / total_graphs
    p_x1 = (edge_px + i * (section_w + gap_px)) / max_width
    p_x2 = (edge_px + i * (section_w + gap_px) + section_w) / max_width
    text_p = P((p_x1 + p_x2) / 2, 0.1)
    button_p = P((p_x1 + p_x2) / 2, 0.2)
    button_px1 = P(-20, -20)
    button_px2 = P(20, 20)
    slider_p1 = P(p_x1, 0.3)
    slider_p2 = P(p_x2, 0.3)
    info_texts.append(TextDef(p=text_p, text=graph_names[i]))
    info_buttons.append(ButtonDef(poly_def=RectDef(p1=button_p, p2=button_p, px1=button_px1, px2=button_px2, fill_color=QColor(171, 151, 247, 255)), event_out=get_event(f'graph_{i}_active'), action='cycle', event_delta=[True, False], hold_when_set=True))
    info_sliders.append(make_slider(event_name=f'graph_{i}_max_time', p1=slider_p1, p2=slider_p2, px1=P(0, 0), px2=P(0, 0), half=3.0, min_val=10, max_val=1800, step=10))

graph_sub_windows = []
for i in range(6):
    graph_sub_windows.append(
        WindowDef(
            p1=graph_points[i][0], p2=graph_points[i][1],
            draggable=True, scalable=True, grid_snap_pixel=True, grid_snap_x=10, grid_snap_y=10,
            polygon_defs=[
                RectDef(p1=P(0, 0), p2=P(1, 1), fill_color=QColor(0, 0, 0, 0), outline_color=QColor(255, 255, 255, 255), outline_width=2)
            ],
            text_defs=[
                TextDef(
                    p=P(0.5, 0),
                    px=P(0, 3),
                    h_align=0.5, v_align=0.0,
                    text=graph_names[i], font_size=12.0,
                )
            ],
            graph_defs=[
                GraphDef(
                    p1=P(0, 0), p2=P(1, 1),
                    series =                graph_series[i],
                    max_time =              graph_max_time[i],
                    start_display_time =    graph_start_display_time[i],
                    end_display_time =      graph_end_display_time[i],
                    value_range=            graph_value_range[i],
                    value_color=QColor(255, 255, 255, 255),
                    ease_dur=0.9,
                    ease_type=QEasingCurve.OutQuint,
                    dynamic_scale=5.0,
                    show_minmax = True,
                    show_step = True,
                    step_count = lambda: int(get_event('graph_steps').value),
                    label_align='left',
                    size_minmax = 8.0,
                    size_step = 8.0,
                    size_name = 8.0,
                    stack=graph_stack[i],
                    update_interval=graph_update_interval[i],
                )
            ]
        )
    )

BAR_WIDTH       = 6.0
BAR_GAP         = 0.0
BAR_MAX_HEIGHT  = 45.0
BAR_DAMP_K      = 60.0
BAR_BASELINE_DY = 0.0

def _rpm_to_height(rpm: float, max_height: float = BAR_MAX_HEIGHT, k: float = BAR_DAMP_K) -> float:
    if rpm == 0:
        return 0.0
    return math.copysign(max_height * (2.0 / math.pi) * math.atan(abs(rpm) / k), rpm)

motor_rpm_actual_events = [register_event(EventDef(name=f'motor_{i}_rpm_actual', value=0.0)) for i in range(6)]
motor_rpm_cmd_events    = [register_event(EventDef(name=f'motor_{i}_rpm_cmd',    value=0.0)) for i in range(6)]

MOTOR_RPM_ACTUAL_KEYS = [f'test_value{(i % 9) + 1}' for i in range(6)]
MOTOR_RPM_CMD_KEYS    = [f'test_value{((i + 4) % 9) + 1}' for i in range(6)]

motor_rpm_listeners = []
for i in range(6):
    motor_rpm_listeners.append(EventListener(
        value_fn=(lambda ctx, key=MOTOR_RPM_ACTUAL_KEYS[i]: ctx.get(key, {}).get('latest')),
        targets=[motor_rpm_actual_events[i]], passthrough=True, skip_none=False,
        transform=lambda v: v if v is not None else 0.0,
    ))
    motor_rpm_listeners.append(EventListener(
        value_fn=(lambda ctx, key=MOTOR_RPM_CMD_KEYS[i]: ctx.get(key, {}).get('latest')),
        targets=[motor_rpm_cmd_events[i]], passthrough=True, skip_none=False,
        transform=lambda v: v if v is not None else 0.0,
    ))

def _make_rpm_bar_pos_fn(ev: EventDef):
    def _fn():
        try:
            rpm = float(ev.value)
        except (TypeError, ValueError):
            rpm = 0.0
        dy = -_rpm_to_height(rpm)
        return [P(0.0, 0.0), P(0.0, 0.0), P(0.0, dy), P(0.0, dy)]
    return _fn

motor_rpm_bar_polys = []
for i in range(6):
    anchor = motor_vals[0][i]
    px_base_x = 54 * np.sign(motor_vals[4][i])
    px_base_y = 20 * round(i / 2 - 1.1)
    actual_x0, actual_x1 = px_base_x - (BAR_GAP / 2 + BAR_WIDTH), px_base_x - (BAR_GAP / 2)
    cmd_x0,    cmd_x1    = px_base_x + (BAR_GAP / 2),            px_base_x + (BAR_GAP / 2 + BAR_WIDTH)

    motor_rpm_bar_polys.append(PolygonDef(   # real RPM bar
        p=[anchor] * 4,
        px=[P(actual_x0, px_base_y + BAR_BASELINE_DY), P(actual_x1, px_base_y + BAR_BASELINE_DY), P(actual_x1, px_base_y + BAR_BASELINE_DY), P(actual_x0, px_base_y + BAR_BASELINE_DY)],
        gradient=get_gradient('alt_color_fill'),
        pos_fn=_make_rpm_bar_pos_fn(motor_rpm_actual_events[i]),
    ))
    motor_rpm_bar_polys.append(PolygonDef(   # commanded RPM bar
        p=[anchor] * 4,
        px=[P(cmd_x0, px_base_y + BAR_BASELINE_DY), P(cmd_x1, px_base_y + BAR_BASELINE_DY), P(cmd_x1, px_base_y + BAR_BASELINE_DY), P(cmd_x0, px_base_y + BAR_BASELINE_DY)],
        fill_color=QColor(255, 255, 255, 255),
        pos_fn=_make_rpm_bar_pos_fn(motor_rpm_cmd_events[i]),
    ))
    # motor_rpm_bar_polys.append(PolygonDef(
    #     p=[anchor, anchor],
    #     px=[P(actual_x0 - 2, BAR_BASELINE_DY), P(cmd_x1 + 2, BAR_BASELINE_DY)],
    #     closed=False, outline_color=QColor(255, 255, 255, 255), outline_width=1.0,
    # ))

motor_rot_angles_polys = []
motor_rot_actual_events = [register_event(EventDef(name=f'motor_{i}_rot_actual', value=0.0)) for i in range(4)]
motor_rot_cmd_events    = [register_event(EventDef(name=f'motor_{i}_rot_cmd',    value=0.0)) for i in range(4)]

MOTOR_ROT_ACTUAL_KEYS = [f'test_value{(i % 9) + 1}' for i in range(6)]
MOTOR_ROT_CMD_KEYS    = [f'test_value{((i + 4) % 9) + 1}' for i in range(6)]

for i in range(4):
    motor_rpm_listeners.append(EventListener(
        value_fn=(lambda ctx, key=MOTOR_ROT_ACTUAL_KEYS[i]: ctx.get(key, {}).get('latest')),
        targets=[motor_rot_actual_events[i]], passthrough=True, skip_none=False,
        transform=lambda v: 5 * v - 20 if v is not None else 0.0,
    ))
    motor_rpm_listeners.append(EventListener(
        value_fn=(lambda ctx, key=MOTOR_ROT_CMD_KEYS[i]: ctx.get(key, {}).get('latest')),
        targets=[motor_rot_cmd_events[i]], passthrough=True, skip_none=False,
        transform=lambda v: 5 * v - 20 if v is not None else 0.0,
    ))

needle_info=[
    [P(0.125, 1/6), P(0.875, 1/6), P(0.125, 5/6), P(0.875, 5/6)],
    [0, 0, 0, 0]
]

for i in range(4):
    motor_rot_angles_polys.append( # COMMANDED
        PolygonDef(p=[needle_info[0][i]]*6, px=[P(needle_info[1][i] - 9, 18), P(needle_info[1][i] - 11, 0), P(needle_info[1][i] - 9, -18), P(needle_info[1][i] + 9, -18), P(needle_info[1][i] + 11, 0), P(needle_info[1][i] + 9, 18)], 
            fill_color=QColor(0, 0, 0, 0), outline_color=QColor(255, 0, 0, 255), outline_width=1,
            rot_center_p=needle_info[0][i], rot_center_px=P(needle_info[1][i], 0), rot_angle=0,
            rot_angle_fn=motor_rot_cmd_events[i],
        ),
    )
    motor_rot_angles_polys.append( # REAL FILL
        PolygonDef(p=[needle_info[0][i]]*6, px=[P(needle_info[1][i] - 9, 18), P(needle_info[1][i] - 11, 0), P(needle_info[1][i] - 9, -18), P(needle_info[1][i] + 9, -18), P(needle_info[1][i] + 11, 0), P(needle_info[1][i] + 9, 18)], 
            fill_color=QColor(255, 255, 255, 127),
            rot_center_p=needle_info[0][i], rot_center_px=P(needle_info[1][i], 0), rot_angle=0,
            rot_angle_fn=motor_rot_actual_events[i],
        ),
    )
    motor_rot_angles_polys.append( # REAL OUTLINE
        PolygonDef(p=[needle_info[0][i]]*6, px=[P(needle_info[1][i] - 9, 18), P(needle_info[1][i] - 11, 0), P(needle_info[1][i] - 9, -18), P(needle_info[1][i] + 9, -18), P(needle_info[1][i] + 11, 0), P(needle_info[1][i] + 9, 18)], 
            gradient=get_gradient('alt_color_outline'), fill_color=QColor(0, 0, 0, 0), outline_width=2, 
            rot_center_p=needle_info[0][i], rot_center_px=P(needle_info[1][i], 0), rot_angle=0,
            rot_angle_fn=motor_rot_actual_events[i],
        ),
    )

    needle_py_sign = -1 if i <= 1 else 1
    motor_rot_angles_polys.append( # COMMANDED
        PolygonDef(p=[needle_info[0][i]]*4, px=[P(needle_info[1][i], needle_py_sign * 23), P(needle_info[1][i] - 2, needle_py_sign * 25), P(needle_info[1][i], needle_py_sign * 35), P(needle_info[1][i] + 2, needle_py_sign * 25)], 
            fill_color=QColor(0, 0, 0, 0), outline_color=QColor(255, 0, 0, 255), outline_width=1,
            rot_center_p=needle_info[0][i], rot_center_px=P(needle_info[1][i], 0), rot_angle=0,
            rot_angle_fn=motor_rot_cmd_events[i],
        ),
    )
    motor_rot_angles_polys.append( # REAL FILL
        PolygonDef(p=[needle_info[0][i]]*4, px=[P(needle_info[1][i], needle_py_sign * 23), P(needle_info[1][i] - 2, needle_py_sign * 25), P(needle_info[1][i], needle_py_sign * 35), P(needle_info[1][i] + 2, needle_py_sign * 25)], 
            gradient=get_gradient('alt_color_outline'), fill_color=QColor(0, 0, 0, 0), outline_width=2, 
            rot_center_p=needle_info[0][i], rot_center_px=P(needle_info[1][i], 0), rot_angle=0,
            rot_angle_fn=motor_rot_actual_events[i],
        ),
    )
    motor_rot_angles_polys.append( # REAL OUTLINE
        PolygonDef(p=[needle_info[0][i]]*4, px=[P(needle_info[1][i], needle_py_sign * 23), P(needle_info[1][i] - 2, needle_py_sign * 25), P(needle_info[1][i], needle_py_sign * 35), P(needle_info[1][i] + 2, needle_py_sign * 25)], 
            gradient=get_gradient('alt_color_outline'), fill_color=QColor(0, 0, 0, 0), outline_width=2, 
            rot_center_p=needle_info[0][i], rot_center_px=P(needle_info[1][i], 0), rot_angle=0,
            rot_angle_fn=motor_rot_actual_events[i],
        ),
    )


info_window = WindowDef(
    p1=P(0.0, 0.6), p2=P(0.5, 1.0), px1=P(0, 0), px2=P(-157, 0),
    hidden_event=get_event('window_disabled_info'),
    phase_event=get_event('content_phase_info'),
    phases={
        'open': Phase([WindowTween(p1=get_event('info_window_p1'), p2=get_event('info_window_p2'), px1=get_event('info_window_px1'), px2=get_event('info_window_px2'), start=0.0, dur=1.0, ease=QEasingCurve.OutQuint)], update_retrigger=True)
    },
    listener_defs=motor_rpm_listeners,
    sub_windows=graph_sub_windows + [
        WindowDef(
            p1=P(1, 0), p2=P(1, 0), px1=P(-275, 0), px2=P(-25, 300),
            draggable=True, grid_snap_pixel=True, grid_snap_x=10, grid_snap_y=10,
            polygon_defs=[
                PolygonDef(p=[P(0, 0), P(0.25, 0), P(0.25, 0), P(0.5, 0), P(0.5, 1/3), P(0.5, 1/3), P(0.5, 1/3), P(0, 1/3)], px=[P(0,  5), P(-30,  5), P(0,  35), P(-5,  35), P(-5, -37), P(-17, -37), P(-17, 0), P(0, 0)], fill_color=QColor(50, 50, 50, 190)),
                PolygonDef(p=[P(1, 0), P(0.75, 0), P(0.75, 0), P(0.5, 0), P(0.5, 1/3), P(0.5, 1/3), P(0.5, 1/3), P(1, 1/3)], px=[P(0,  5), P( 30,  5), P(0,  35), P( 5,  35), P( 5, -37), P( 17, -37), P( 17, 0), P(0, 0)], fill_color=QColor(50, 50, 50, 190)),
                PolygonDef(p=[P(0, 1), P(0.25, 1), P(0.25, 1), P(0.5, 1), P(0.5, 2/3), P(0.5, 2/3), P(0.5, 2/3), P(0, 2/3)], px=[P(0, -5), P(-30, -5), P(0, -35), P(-5, -35), P(-5,  37), P(-17,  37), P(-17, 0), P(0, 0)], fill_color=QColor(50, 50, 50, 190)),
                PolygonDef(p=[P(1, 1), P(0.75, 1), P(0.75, 1), P(0.5, 1), P(0.5, 2/3), P(0.5, 2/3), P(0.5, 2/3), P(1, 2/3)], px=[P(0, -5), P( 30, -5), P(0, -35), P( 5, -35), P( 5,  37), P( 17,  37), P( 17, 0), P(0, 0)], fill_color=QColor(50, 50, 50, 190)),
                
                PolygonDef(p=[P(0.25, 0), P(0.5, 0), P(0.5, 0), P(0.25, 0)], px=[P(-28, 0), P(-17, 0), P(-17,  30), P( 2,  30)], fill_color=QColor(50, 50, 50, 190)),
                PolygonDef(p=[P(0.75, 0), P(0.5, 0), P(0.5, 0), P(0.75, 0)], px=[P( 28, 0), P( 17, 0), P( 17,  30), P(-2,  30)], fill_color=QColor(50, 50, 50, 190)),
                PolygonDef(p=[P(0.25, 1), P(0.5, 1), P(0.5, 1), P(0.25, 1)], px=[P(-28, 0), P(-17, 0), P(-17, -30), P( 2, -30)], fill_color=QColor(50, 50, 50, 190)),
                PolygonDef(p=[P(0.75, 1), P(0.5, 1), P(0.5, 1), P(0.75, 1)], px=[P( 28, 0), P( 17, 0), P( 17, -30), P(-2, -30)], fill_color=QColor(50, 50, 50, 190)),
                

                PolygonDef(p=[P(0, 1/3), P(0, 1/3), P(0, 1/2), P(0, 2/3), P(0, 2/3), P(0, 1/2)], px=[P( 5 + 0, -25), P( 5 +  30, -25), P( 5 +  40, 0), P( 5 +  30, 25), P( 5 + 0, 25), P( 5 +  10, 0)], fill_color=QColor(25, 25, 25, 190)),
                PolygonDef(p=[P(1, 1/3), P(1, 1/3), P(1, 1/2), P(1, 2/3), P(1, 2/3), P(1, 1/2)], px=[P(-5 + 0, -25), P(-5 + -30, -25), P(-5 + -40, 0), P(-5 + -30, 25), P(-5 + 0, 25), P(-5 + -10, 0)], fill_color=QColor(25, 25, 25, 190)),
            
                PolygonDef(p=[P(0.5, 0.5), P(0.5, 0.5)], px=[P(0, -45), P(0, -23)], outline_color=QColor(255, 255, 255, 170), outline_width=2),
                PolygonDef(p=[P(0.5, 0.5), P(0.5, 0.5)], px=[P(0,  45), P(0,  23)], outline_color=QColor(255, 255, 255, 170), outline_width=2),

            ] + motor_rpm_bar_polys + motor_rot_angles_polys,
            text_defs=[
            ] + text_defs_list,
        )
    ]
)

WINDOW_DEFS = []
WINDOW_DEFS.append(info_window)

register_windows(WINDOW_LAYER, WINDOW_DEFS)

WINDOW_DEFS=[
    WindowDef(
        p1=P(0.0, 0.0), p2=P(1.0, 1.0),
        phase_event=get_event('info_setting_phase'),
        polygon_defs=[

        ],
        text_defs=[
            TextDef(p=P(0.5, 0), px=P(0, 40), text='INFO DISPLAY SETTINGS', font_size=30, h_align=0.5, v_align=0.5, char_display=0.0, sub_char_clip=True, phases={
                'open':  Phase([TextTween(char_display=1.0, start=0, dur=1.0, ease=QEasingCurve.OutQuint)]),
                'close': Phase([TextTween(char_display=0.0, start=0, dur=1.0, ease=QEasingCurve.OutQuint)]),
            })
        ] + info_texts,
        button_defs=info_buttons,
        slider_defs=info_sliders,

    )
]

register_windows(9, WINDOW_DEFS)


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