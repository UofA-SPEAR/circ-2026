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

# When you make a new file, name the file and import it to main_gui.py
# You may do anything you like in the file, such as using for loops to create similar objects, but remember to have all windows contained inside the WINDOW_DEF list for it to be registered.

# Note that EventDefs and GradientDefs needs to have unique names as they will be shared across all other files.
# When making EventDefs and GradientDefs, call register_event() or register_gradient() with the EventDef/GradientDef inside.
# Refer to the documentation if you are confused on what to do.

# get_event() and get_gradient() only works when obtaining an event/gradient declared in the same file or a file index lower than the current file.
# This means that if you want a previous file to have access to the event/gradient, declare it in either shared_events.py/shared_gradient.py or the lowest index file that needs the event/gradient based on organizational needs.
# Generally, events/gradients that gets used a lot should be put in shared_events.py/shared_gradients.py

WINDOW_LAYER = 0

WINDOW_DEFS = []

register_windows(WINDOW_LAYER, WINDOW_DEFS)
