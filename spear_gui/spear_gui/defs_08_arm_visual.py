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

WINDOW_LAYER = 0

WINDOW_DEFS = []

register_windows(WINDOW_LAYER, WINDOW_DEFS)
