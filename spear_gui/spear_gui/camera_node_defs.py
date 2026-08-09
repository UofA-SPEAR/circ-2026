from __future__ import annotations
from typing import Callable, List
from PySide6.QtCore import QEasingCurve
from PySide6.QtGui  import QColor

from spear_gui.overlay_system import (
    Rect, RectTween,
    Phase, TextDef, TextTween, Reset,
    AttributeDef, SliderGroupDef, SliderTextDefs,
    make_track_def, make_knob_def, make_mark_fill_def, make_mark_tick_def,
    ButtonDef, PreviewBoxDef, _slot_poly,
    P, PolygonDef, PolygonTween, expand_defs
)

# ──────────────────────── LOADING OVERLAY ────────────────────────

LOADING_DEFS = expand_defs([
    Rect(P(0.00,-0.01), P(0.50,-0.01), fill_color=QColor(255,255,255), uniform_scale=True, phases={
        'create': Phase([
            RectTween(P(0.30,0.47), P(0.50,0.48),                                                                         start=0.30, dur=0.25, ease=QEasingCurve.OutCirc),
            RectTween(P(0.25,0.45), P(0.35,0.46), tr=(P(0,0), P(0,0)),                                                    start=0.55, dur=0.50, ease=QEasingCurve.InOutCirc)]),
        'loaded': Phase([
            RectTween(P(0.25,0.45), P(0.25,0.46),                                                                         start=0.30, dur=0.30, ease=QEasingCurve.OutCirc)])}),
])
# LOADING_DEFS = expand_defs([
#     # Background T/B/L/R
#     Rect(P(0.00,0.00), P(1.00,0.50), fill_color=QColor(10,10,14), phases={
#         'loaded': Phase([RectTween(P(0.00,0.00), P(1.00,0.00), start=0.30, dur=1.00, ease=QEasingCurve.OutQuint)])}),
#     Rect(P(0.00,0.50), P(1.00,1.00), fill_color=QColor(10,10,14), phases={
#         'loaded': Phase([RectTween(P(0.00,1.00), P(1.00,1.00), start=0.30, dur=1.00, ease=QEasingCurve.OutQuint)])}),
#     Rect(P(0.00,0.00), P(0.50,1.00), fill_color=QColor(10,10,14), phases={
#         'loaded': Phase([RectTween(P(0.00,0.00), P(0.00,1.00), start=0.30, dur=1.00, ease=QEasingCurve.OutQuint)])}),
#     Rect(P(0.50,0.00), P(1.00,1.00), fill_color=QColor(10,10,14), phases={
#         'loaded': Phase([RectTween(P(1.00,0.00), P(1.00,1.00), start=0.30, dur=1.00, ease=QEasingCurve.OutQuint)])}),

#     # Background Border T/B/L/R
#     Rect(P(0.50,0.50), P(0.50,0.50), px1=P(0,-1), px2=P(0,0), fill_color=QColor(255,255,255), phases={
#         'loaded': Phase([
#             RectTween(P(0.00,0.00), P(1.00,0.00), px1=P(0,-1), px2=P(0,0),  fill_color=QColor(255,255,255),              start=0.30, dur=1.00, ease=QEasingCurve.OutQuint),
#             RectTween(P(0.00,0.00), P(1.00,0.00), px1=P(0,-1), px2=P(0,0),  fill_color=QColor(255,255,255,0),             start=2.50, dur=1.00, ease=QEasingCurve.InQuint)])}),
#     Rect(P(0.50,0.50), P(0.50,0.50), px1=P(0,0),  px2=P(0,1), fill_color=QColor(255,255,255), phases={
#         'loaded': Phase([
#             RectTween(P(0.00,1.00), P(1.00,1.00), px1=P(0,0),  px2=P(0,1),  fill_color=QColor(255,255,255),              start=0.30, dur=1.00, ease=QEasingCurve.OutQuint),
#             RectTween(P(0.00,1.00), P(1.00,1.00), px1=P(0,0),  px2=P(0,1),  fill_color=QColor(255,255,255,0),             start=2.50, dur=1.00, ease=QEasingCurve.InQuint)])}),
#     Rect(P(0.50,0.50), P(0.50,0.50), px1=P(-1,0), px2=P(0,0), fill_color=QColor(255,255,255), phases={
#         'loaded': Phase([
#             RectTween(P(0.00,0.00), P(0.00,1.00), px1=P(-1,0), px2=P(0,0),  fill_color=QColor(255,255,255),              start=0.30, dur=1.00, ease=QEasingCurve.OutQuint),
#             RectTween(P(0.00,0.00), P(0.00,1.00), px1=P(-1,0), px2=P(0,0),  fill_color=QColor(255,255,255,0),             start=2.50, dur=1.00, ease=QEasingCurve.InQuint)])}),
#     Rect(P(0.50,0.50), P(0.50,0.50), px1=P(0,0),  px2=P(1,0), fill_color=QColor(255,255,255), phases={
#         'loaded': Phase([
#             RectTween(P(1.00,0.00), P(1.00,1.00), px1=P(0,0),  px2=P(1,0),  fill_color=QColor(255,255,255),              start=0.30, dur=1.00, ease=QEasingCurve.OutQuint),
#             RectTween(P(1.00,0.00), P(1.00,1.00), px1=P(0,0),  px2=P(1,0),  fill_color=QColor(255,255,255,0),             start=2.50, dur=1.00, ease=QEasingCurve.InQuint)])}),

#     # Horizontal Corner TL/TR/BL/BR
#     Rect(P(0.00,-0.01), P(0.50,-0.01), fill_color=QColor(255,255,255), uniform_scale=True, phases={
#         'create': Phase([
#             RectTween(P(0.30,0.47), P(0.50,0.48),                                                                         start=0.30, dur=0.25, ease=QEasingCurve.OutCirc),
#             RectTween(P(0.25,0.45), P(0.35,0.46), tr=(P(0,0), P(0,0)),                                                    start=0.55, dur=0.50, ease=QEasingCurve.InOutCirc)]),
#         'loaded': Phase([
#             RectTween(P(0.25,0.45), P(0.25,0.46),                                                                         start=0.30, dur=0.30, ease=QEasingCurve.OutCirc)])}),
#     Rect(P(0.50,-0.01), P(1.00,-0.01), fill_color=QColor(255,255,255), uniform_scale=True, phases={
#         'create': Phase([
#             RectTween(P(0.50,0.47), P(0.70,0.48),                                                                         start=0.30, dur=0.25, ease=QEasingCurve.OutCirc),
#             RectTween(P(0.65,0.45), P(0.75,0.46), tl=(P(0,0), P(0,0)),                                                    start=0.55, dur=0.50, ease=QEasingCurve.InOutCirc)]),
#         'loaded': Phase([
#             RectTween(P(0.75,0.45), P(0.75,0.46),                                                                         start=0.30, dur=0.30, ease=QEasingCurve.OutCirc)])}),
#     Rect(P(0.00,1.00), P(0.50,1.00), fill_color=QColor(255,255,255), uniform_scale=True, phases={
#         'create': Phase([
#             RectTween(P(0.30,0.52), P(0.50,0.53),                                                                         start=0.30, dur=0.25, ease=QEasingCurve.OutCirc),
#             RectTween(P(0.25,0.54), P(0.35,0.55), br=(P(0,0), P(0,0)),                                                    start=0.55, dur=0.50, ease=QEasingCurve.InOutCirc)]),
#         'loaded': Phase([
#             RectTween(P(0.25,0.54), P(0.25,0.55),                                                                         start=0.30, dur=0.30, ease=QEasingCurve.OutCirc)])}),
#     Rect(P(0.50,1.00), P(1.00,1.00), fill_color=QColor(255,255,255), uniform_scale=True, phases={
#         'create': Phase([
#             RectTween(P(0.50,0.52), P(0.70,0.53),                                                                         start=0.30, dur=0.25, ease=QEasingCurve.OutCirc),
#             RectTween(P(0.65,0.54), P(0.75,0.55), bl=(P(0,0), P(0,0)),                                                    start=0.55, dur=0.50, ease=QEasingCurve.InOutCirc)]),
#         'loaded': Phase([
#             RectTween(P(0.75,0.54), P(0.75,0.55),                                                                         start=0.30, dur=0.30, ease=QEasingCurve.OutCirc)])}),

#     # Horizontal Thin Corner TL/TR/BL/BR
#     Rect(P(0.30,0.475), P(0.50,0.480), fill_color=QColor(255,255,255), uniform_scale=True, phases={
#         'create': Phase([
#             RectTween(P(0.30,0.475),  P(0.50,0.480),                                                                      start=0.55, dur=0.00, ease=QEasingCurve.InOutCirc),
#             RectTween(P(0.345,0.455), P(0.445,0.460), tr=(P(0,0), P(0,0)),                                                start=0.55, dur=0.50, ease=QEasingCurve.InOutCirc),
#             RectTween(P(0.345,0.455), P(0.395,0.460), tr=(P(0,0), P(0,0)),                                                start=1.05, dur=1.75, ease=QEasingCurve.InCirc)]),
#         'loaded': Phase([
#             RectTween(P(0.345,0.455), P(0.345,0.460),                                                                     start=0.00, dur=0.30, ease=QEasingCurve.OutCirc)])}),
#     Rect(P(0.50,0.475), P(0.70,0.480), fill_color=QColor(255,255,255), uniform_scale=True, phases={
#         'create': Phase([
#             RectTween(P(0.50,0.475),  P(0.70,0.480),                                                                      start=0.55, dur=0.00, ease=QEasingCurve.InOutCirc),
#             RectTween(P(0.555,0.455), P(0.655,0.460), tl=(P(0,0), P(0,0)),                                                start=0.55, dur=0.50, ease=QEasingCurve.InOutCirc),
#             RectTween(P(0.605,0.455), P(0.655,0.460), tl=(P(0,0), P(0,0)),                                                start=1.05, dur=1.75, ease=QEasingCurve.InCirc)]),
#         'loaded': Phase([
#             RectTween(P(0.655,0.455), P(0.655,0.460),                                                                     start=0.00, dur=0.30, ease=QEasingCurve.OutCirc)])}),
#     Rect(P(0.30,0.52), P(0.50,0.525), fill_color=QColor(255,255,255), uniform_scale=True, phases={
#         'create': Phase([
#             RectTween(P(0.30,0.52),   P(0.50,0.525),                                                                      start=0.55, dur=0.00, ease=QEasingCurve.InOutCirc),
#             RectTween(P(0.345,0.54),  P(0.445,0.545), br=(P(0,0), P(0,0)),                                                start=0.55, dur=0.50, ease=QEasingCurve.InOutCirc),
#             RectTween(P(0.345,0.54),  P(0.395,0.545), br=(P(0,0), P(0,0)),                                                start=1.05, dur=1.75, ease=QEasingCurve.InCirc)]),
#         'loaded': Phase([
#             RectTween(P(0.345,0.54),  P(0.345,0.545),                                                                     start=0.00, dur=0.30, ease=QEasingCurve.OutCirc)])}),
#     Rect(P(0.50,0.52), P(0.70,0.525), fill_color=QColor(255,255,255), uniform_scale=True, phases={
#         'create': Phase([
#             RectTween(P(0.50,0.52),   P(0.70,0.525),                                                                      start=0.55, dur=0.00, ease=QEasingCurve.InOutCirc),
#             RectTween(P(0.555,0.54),  P(0.655,0.545), bl=(P(0,0), P(0,0)),                                                start=0.55, dur=0.50, ease=QEasingCurve.InOutCirc),
#             RectTween(P(0.605,0.54),  P(0.655,0.545), bl=(P(0,0), P(0,0)),                                                start=1.05, dur=1.75, ease=QEasingCurve.InCirc)]),
#         'loaded': Phase([
#             RectTween(P(0.655,0.54),  P(0.655,0.545),                                                                     start=0.00, dur=0.30, ease=QEasingCurve.OutCirc)])}),

#     # Vertical Corner TL/BL/TR/BR
#     Rect(P(0.00,0.00), P(0.005625,0.50), fill_color=QColor(255,255,255), uniform_scale=True, phases={
#         'create': Phase([
#             RectTween(P(0.30,0.47),  P(0.305625,0.50),                                                                    start=0.30, dur=0.25, ease=QEasingCurve.OutCirc),
#             RectTween(P(0.25,0.45),  P(0.255625,0.47),                                                                    start=0.55, dur=0.50, ease=QEasingCurve.InOutCirc)]),
#         'loaded': Phase([
#             RectTween(P(0.25,0.47),  P(0.255625,0.47),                                                                    start=0.60, dur=0.30, ease=QEasingCurve.OutCirc)])}),
#     Rect(P(0.00,0.50), P(0.005625,1.00), fill_color=QColor(255,255,255), uniform_scale=True, phases={
#         'create': Phase([
#             RectTween(P(0.30,0.50),  P(0.305625,0.53),                                                                    start=0.30, dur=0.25, ease=QEasingCurve.OutCirc),
#             RectTween(P(0.25,0.53),  P(0.255625,0.55),                                                                    start=0.55, dur=0.50, ease=QEasingCurve.InOutCirc)]),
#         'loaded': Phase([
#             RectTween(P(0.25,0.53),  P(0.255625,0.53),                                                                    start=0.60, dur=0.30, ease=QEasingCurve.OutCirc)])}),
#     Rect(P(1.00,0.00), P(1.005625,0.50), fill_color=QColor(255,255,255), uniform_scale=True, phases={
#         'create': Phase([
#             RectTween(P(0.694375,0.47), P(0.70,0.50),                                                                     start=0.30, dur=0.25, ease=QEasingCurve.OutCirc),
#             RectTween(P(0.744375,0.45), P(0.75,0.47),                                                                     start=0.55, dur=0.50, ease=QEasingCurve.InOutCirc)]),
#         'loaded': Phase([
#             RectTween(P(0.744375,0.47), P(0.75,0.47),                                                                     start=0.60, dur=0.30, ease=QEasingCurve.OutCirc)])}),
#     Rect(P(1.00,0.00), P(1.005625,0.50), fill_color=QColor(255,255,255), uniform_scale=True, phases={
#         'create': Phase([
#             RectTween(P(0.694375,0.50), P(0.70,0.53),                                                                     start=0.30, dur=0.25, ease=QEasingCurve.OutCirc),
#             RectTween(P(0.744375,0.53), P(0.75,0.55),                                                                     start=0.55, dur=0.50, ease=QEasingCurve.InOutCirc)]),
#         'loaded': Phase([
#             RectTween(P(0.744375,0.53), P(0.75,0.53),                                                                     start=0.60, dur=0.30, ease=QEasingCurve.OutCirc)])}),

#     # Large Square L/R
#     Rect(P(0.50,0.50), P(0.50,0.50), fill_color=QColor(180,180,180), uniform_scale=True, phases={
#         'create': Phase([
#             RectTween(P(0.50-10/1920,0.50-10/1080), P(0.50+10/1920,0.50+10/1080),                                        start=0.00, dur=0.30, ease=QEasingCurve.OutCirc),
#             RectTween(P(0.23,        0.50-10/1080), P(0.23+20/1920,0.50+10/1080),                                        start=0.30, dur=1.00, ease=QEasingCurve.OutBack)]),
#         'loaded': Phase([
#             RectTween(P(0.25,        0.50-10/1080), P(0.255625,    0.50+10/1080), fill_color=QColor(255,255,255),        start=0.30, dur=0.30, ease=QEasingCurve.OutCirc),
#             RectTween(P(0.25,        0.50),          P(0.255625,    0.50),                                                start=0.90, dur=0.30, ease=QEasingCurve.OutCirc)])}),
#     Rect(P(0.50,0.50), P(0.50,0.50), fill_color=QColor(180,180,180), uniform_scale=True, phases={
#         'create': Phase([
#             RectTween(P(0.50-10/1920,0.50-10/1080), P(0.50+10/1920,0.50+10/1080),                                        start=0.00, dur=0.30, ease=QEasingCurve.OutCirc),
#             RectTween(P(0.77-20/1920,0.50-10/1080), P(0.77,        0.50+10/1080),                                        start=0.30, dur=1.00, ease=QEasingCurve.OutBack)]),
#         'loaded': Phase([
#             RectTween(P(0.75-0.005625,0.50-10/1080), P(0.75,       0.50+10/1080), fill_color=QColor(255,255,255),        start=0.30, dur=0.30, ease=QEasingCurve.OutCirc),
#             RectTween(P(0.75-0.005625,0.50),          P(0.75,       0.50),                                                start=0.90, dur=0.30, ease=QEasingCurve.OutCirc)])}),

#     # Small Square TL/TR/BL/BR
#     Rect(P(0.50,0.50), P(0.50,0.50), fill_color=QColor(180,180,180), uniform_scale=True, phases={
#         'create': Phase([
#             RectTween(P(0.50-5/1920, 0.50-5/1080),  P(0.50+5/1920, 0.50+5/1080),                                        start=0.00, dur=0.30, ease=QEasingCurve.OutCirc),
#             RectTween(P(0.50-70/1920,0.50-70/1080), P(0.50-60/1920,0.50-60/1080),                                        start=0.30, dur=1.00, ease=QEasingCurve.OutBack)]),
#         'loaded': Phase([
#             RectTween(P(0.50-5/1920, 0.50-70/1080), P(0.50+5/1920, 0.50-60/1080), fill_color=QColor(255,255,255),       start=0.30, dur=0.30, ease=QEasingCurve.OutCirc),
#             RectTween(P(0.50,        0.50),           P(0.50,        0.50),                                               start=0.60, dur=0.30, ease=QEasingCurve.OutCirc)])}),
#     Rect(P(0.50,0.50), P(0.50,0.50), fill_color=QColor(180,180,180), uniform_scale=True, phases={
#         'create': Phase([
#             RectTween(P(0.50-5/1920, 0.50-5/1080),  P(0.50+5/1920, 0.50+5/1080),                                        start=0.00, dur=0.30, ease=QEasingCurve.OutCirc),
#             RectTween(P(0.50+70/1920,0.50-70/1080), P(0.50+80/1920,0.50-60/1080),                                        start=0.30, dur=1.00, ease=QEasingCurve.OutBack)]),
#         'loaded': Phase([
#             RectTween(P(0.50-5/1920, 0.50-70/1080), P(0.50+5/1920, 0.50-60/1080), fill_color=QColor(255,255,255),       start=0.30, dur=0.30, ease=QEasingCurve.OutCirc),
#             RectTween(P(0.50,        0.50),           P(0.50,        0.50),                                               start=0.60, dur=0.30, ease=QEasingCurve.OutCirc)])}),
#     Rect(P(0.50,0.50), P(0.50,0.50), fill_color=QColor(180,180,180), uniform_scale=True, phases={
#         'create': Phase([
#             RectTween(P(0.50-5/1920, 0.50-5/1080),  P(0.50+5/1920, 0.50+5/1080),                                        start=0.00, dur=0.30, ease=QEasingCurve.OutCirc),
#             RectTween(P(0.50-70/1920,0.50+70/1080), P(0.50-60/1920,0.50+80/1080),                                        start=0.30, dur=1.00, ease=QEasingCurve.OutBack)]),
#         'loaded': Phase([
#             RectTween(P(0.50-5/1920, 0.50+70/1080), P(0.50+5/1920, 0.50+80/1080), fill_color=QColor(255,255,255),       start=0.30, dur=0.30, ease=QEasingCurve.OutCirc),
#             RectTween(P(0.50,        0.50),           P(0.50,        0.50),                                               start=0.60, dur=0.30, ease=QEasingCurve.OutCirc)])}),
#     Rect(P(0.50,0.50), P(0.50,0.50), fill_color=QColor(180,180,180), uniform_scale=True, phases={
#         'create': Phase([
#             RectTween(P(0.50-5/1920, 0.50-5/1080),  P(0.50+5/1920, 0.50+5/1080),                                        start=0.00, dur=0.30, ease=QEasingCurve.OutCirc),
#             RectTween(P(0.50+70/1920,0.50+70/1080), P(0.50+80/1920,0.50+80/1080),                                        start=0.30, dur=1.00, ease=QEasingCurve.OutBack)]),
#         'loaded': Phase([
#             RectTween(P(0.50-5/1920, 0.50+70/1080), P(0.50+5/1920, 0.50+80/1080), fill_color=QColor(255,255,255),       start=0.30, dur=0.30, ease=QEasingCurve.OutCirc),
#             RectTween(P(0.50,        0.50),           P(0.50,        0.50),                                               start=0.60, dur=0.30, ease=QEasingCurve.OutCirc)])}),

#     # Progress Bar Outline T/B/L/R
#     Rect(P(0.50,0.50), P(0.50,0.50), fill_color=QColor(120,120,120), uniform_scale=True, phases={
#         'create': Phase([
#             RectTween(P(0.25+0.005625*2,0.45+0.01*2), P(0.25+0.005625*2+0.05625-0.005625*2*2, 0.45+0.01*2+0.0025),      start=0.30, dur=0.70, ease=QEasingCurve.InOutQuad),
#             RectTween(P(0.25+0.005625*2,0.45+0.01*2), P(0.75-0.005625*2,                       0.45+0.01*2+0.0025),      start=1.00, dur=1.00, ease=QEasingCurve.InOutQuad)]),
#         'loaded': Phase([
#             RectTween(P(0.25+0.005625*2,0.45+0.01*2), P(0.75-0.005625*2,                       0.45+0.01*2+0.0025), fill_color=QColor(255,255,255), start=0.30, dur=0.30, ease=QEasingCurve.InOutQuad),
#             RectTween(P(0.05+0.005625*2,0.45+0.01*2), P(0.05+0.005625*2,                       0.45+0.01*2+0.0025),                                 start=0.60, dur=1.20, ease=QEasingCurve.OutQuint)])}),
#     Rect(P(0.50,0.50), P(0.50,0.50), fill_color=QColor(120,120,120), uniform_scale=True, phases={
#         'create': Phase([
#             RectTween(P(0.25+0.005625*2,0.55-0.01*2-0.0025), P(0.25+0.005625*2+0.05625-0.005625*2*2, 0.55-0.01*2),      start=0.30, dur=0.70, ease=QEasingCurve.InOutQuad),
#             RectTween(P(0.25+0.005625*2,0.55-0.01*2-0.0025), P(0.75-0.005625*2,                       0.55-0.01*2),      start=1.00, dur=1.00, ease=QEasingCurve.InOutQuad)]),
#         'loaded': Phase([
#             RectTween(P(0.25+0.005625*2,0.55-0.01*2-0.0025), P(0.75-0.005625*2,                       0.55-0.01*2), fill_color=QColor(255,255,255), start=0.30, dur=0.30, ease=QEasingCurve.InOutQuad),
#             RectTween(P(0.95+0.005625*2,0.55-0.01*2-0.0025), P(0.95+0.005625*2,                       0.55-0.01*2),                                 start=0.60, dur=1.20, ease=QEasingCurve.OutQuint)])}),
#     Rect(P(0.50,0.50), P(0.50,0.50), fill_color=QColor(120,120,120), uniform_scale=True, phases={
#         'create': Phase([
#             RectTween(P(0.25+0.005625*2,0.45+0.01*2), P(0.25+0.005625*2+0.00140625, 0.55-0.01*2),                        start=0.30, dur=0.70, ease=QEasingCurve.InOutQuad)]),
#         'loaded': Phase([
#             RectTween(P(0.25+0.005625*2,0.55-0.01*2), P(0.25+0.005625*2+0.00140625, 0.55-0.01*2), fill_color=QColor(255,255,255), start=0.30, dur=0.30, ease=QEasingCurve.OutCirc)])}),
#     Rect(P(0.50,0.50), P(0.50,0.50), fill_color=QColor(120,120,120), uniform_scale=True, phases={
#         'create': Phase([
#             RectTween(P(0.25+0.005625*2+0.05625-0.005625*2*2,0.45+0.01*2), P(0.25+0.005625*2+0.05625-0.005625*2*2+0.00140625, 0.55-0.01*2), start=0.30, dur=0.70, ease=QEasingCurve.InOutQuad),
#             RectTween(P(0.75-0.005625*2-0.00140625,           0.45+0.01*2), P(0.75-0.005625*2,                               0.55-0.01*2), start=1.00, dur=1.00, ease=QEasingCurve.InOutQuad)]),
#         'loaded': Phase([
#             RectTween(P(0.75-0.005625*2-0.00140625,0.45+0.01*2), P(0.75-0.005625*2, 0.45+0.01*2), fill_color=QColor(255,255,255), start=0.30, dur=0.30, ease=QEasingCurve.OutCirc)])}),

#     # Progress Bar
#     Rect(P(0.50,0.45+0.01*3), P(0.50,0.55-0.01*3), fill_color=QColor(255,255,255), uniform_scale=True, phases={
#         'create': Phase([
#             RectTween(P(0.25+0.005625*3,0.45+0.01*3), P(0.25+0.005625*3+0.05625-0.005625*3*2, 0.55-0.01*3),              start=0.30, dur=0.70, ease=QEasingCurve.InOutQuad),
#             RectTween(P(0.25+0.005625*3,0.45+0.01*3), P(0.75-0.005625*3,                       0.55-0.01*3),              start=1.00, dur=1.80, ease=QEasingCurve.InOutCirc)]),
#         'loaded': Phase([
#             RectTween(P(0.25+0.005625*3,0.45+0.01*3), P(0.75-0.005625*3, 0.55-0.01*3),                                   start=0.00, dur=0.30, ease=QEasingCurve.OutCirc),
#             RectTween(P(0.50,          0.45+0.01*3), P(0.50,             0.55-0.01*3),                                    start=0.30, dur=0.25, ease=QEasingCurve.OutCirc)])}),
# ])

LOADING_TEXT_DEFS = []

# ──────────────────────── SELECTION OVERLAY ────────────────────────

SELECTION_DEFS = expand_defs([
    # Outline T/B/L/R
    # Rect(P(0.00,0.00), P(0.00,0.00), px1=P(0,0),  px2=P(0,2),  fill_color=QColor(255,255,255), phases={
    #     'selected':   Phase([RectTween(P(0.00,0.00), P(1.00,0.00), px1=P(0,0),  px2=P(0,2),  fill_color=QColor(255,255,255), start=0.00, dur=1.00, ease=QEasingCurve.OutQuint)]),
    #     'unselected': Phase([RectTween(P(0.00,0.00), P(1.00,0.00), px1=P(0,0),  px2=P(0,2),  fill_color=QColor(127,127,127), start=0.00, dur=1.00, ease=QEasingCurve.OutQuint)]),
    #     'unfocused':  Phase([RectTween(P(0.00,0.00), P(0.00,0.00), px1=P(0,0),  px2=P(0,2),  fill_color=QColor(127,127,127), start=0.00, dur=1.00, ease=QEasingCurve.OutQuint)])}),
    # Rect(P(1.00,1.00), P(1.00,1.00), px1=P(0,-2), px2=P(0,0),  fill_color=QColor(255,255,255), phases={
    #     'selected':   Phase([RectTween(P(0.00,1.00), P(1.00,1.00), px1=P(0,-2), px2=P(0,0),  fill_color=QColor(255,255,255), start=0.00, dur=1.00, ease=QEasingCurve.OutQuint)]),
    #     'unselected': Phase([RectTween(P(0.00,1.00), P(1.00,1.00), px1=P(0,-2), px2=P(0,0),  fill_color=QColor(127,127,127), start=0.00, dur=1.00, ease=QEasingCurve.OutQuint)]),
    #     'unfocused':  Phase([RectTween(P(0.00,1.00), P(1.00,1.00), px1=P(0,-2), px2=P(0,0),  fill_color=QColor(127,127,127), start=0.00, dur=1.00, ease=QEasingCurve.OutQuint)])}),
    # Rect(P(0.00,0.00), P(0.00,0.00), px1=P(0,0),  px2=P(2,0),  fill_color=QColor(255,255,255), phases={
    #     'selected':   Phase([RectTween(P(0.00,0.00), P(0.00,1.00), px1=P(0,0),  px2=P(2,0),  fill_color=QColor(255,255,255), start=0.00, dur=1.00, ease=QEasingCurve.OutQuint)]),
    #     'unselected': Phase([RectTween(P(0.00,0.00), P(0.00,1.00), px1=P(0,0),  px2=P(2,0),  fill_color=QColor(127,127,127), start=0.00, dur=1.00, ease=QEasingCurve.OutQuint)]),
    #     'unfocused':  Phase([RectTween(P(0.00,0.00), P(0.00,0.00), px1=P(0,0),  px2=P(2,0),  fill_color=QColor(127,127,127), start=0.00, dur=1.00, ease=QEasingCurve.OutQuint)])}),
    # Rect(P(1.00,1.00), P(1.00,1.00), px1=P(-2,0), px2=P(0,0),  fill_color=QColor(255,255,255), phases={
    #     'selected':   Phase([RectTween(P(1.00,0.00), P(1.00,1.00), px1=P(-2,0), px2=P(0,0),  fill_color=QColor(255,255,255), start=0.00, dur=1.00, ease=QEasingCurve.OutQuint)]),
    #     'unselected': Phase([RectTween(P(1.00,0.00), P(1.00,1.00), px1=P(-2,0), px2=P(0,0),  fill_color=QColor(127,127,127), start=0.00, dur=1.00, ease=QEasingCurve.OutQuint)]),
    #     'unfocused':  Phase([RectTween(P(1.00,1.00), P(1.00,1.00), px1=P(-2,0), px2=P(0,0),  fill_color=QColor(127,127,127), start=0.00, dur=1.00, ease=QEasingCurve.OutQuint)])}),

    # # Corner H/V
    # Rect(P(0.00,0.00), P(0.00,0.00), px1=P(0,10), px2=P(0,15), br=(P(0,0),P(-5,0)), fill_color=QColor(255,255,255), d_flip=True, phases={
    #     'selected':   Phase([Reset(),
    #                          RectTween(P(0.00,0.00), P(1.00,0.00), px1=P(-30,10), px2=P(-10,15),bl=(P(0,0),P(5,0)), br=(P(0,0),P(-5,0)), start=0.00, dur=1.00, span=(0, 0.6), ease=QEasingCurve.OutQuint, blend=True),
    #                          RectTween(P(1.00, 0), P(0, 0), px1=P(0, 0), px2=P(0, 0),                                                    start=0.00, dur=1.35, ease=QEasingCurve.OutQuint)]),
    #     'unselected': Phase([RectTween(P(1.00,0.00), P(1.00,0.00), px1=P(-30,10), px2=P(-10,15),                                         start=0.00, dur=0.00, span=(0, 0.3), ease=QEasingCurve.OutQuint),
    #                          RectTween(P(1.00,0.00), P(1.00,0.00), px1=P(-10,10), px2=P(-10,15), start=0.00, dur=1.00, span=(0, 0.3), ease=QEasingCurve.OutQuint)])}),
    
    # Rect(P(1.00,0.00), P(1.00,0.00), px1=P(-15,10), px2=P(-10,15), tl=(P(0,0),P(0,5)), br=(P(0,0),P(0,-5)), d_flip=True, fill_color=QColor(255,255,255), phases={
    #     'selected':   Phase([Reset(),
    #                          RectTween(P(1.00,0.00), P(1.00,0.00), px1=P(-15, 10), px2=P(-10, 90), br=(P(0,0),P(0,5)),                                                     start=0, dur=1.00, span=(0.6, 1), ease=QEasingCurve.OutQuint)]),
    #     'unselected': Phase([RectTween(P(1.00,0.00), P(1.00,0.00), px1=P(-15, 10), px2=P(-10, 90), br=(P(0,0),P(0,5)),                                                     start=0, dur=1.00, span=(0, 0.3), ease=QEasingCurve.OutQuint),
    #                          RectTween(P(1.00,1.20), P(1.00,1.20), px1=P(-15,0), px2=P(-10,50), tr=(P(0,0),P(0,-5)), br=(P(0,0),P(0,5)), fill_color=QColor(255,255,255,0), start=0, dur=1.00, span=(0.3, 1), ease=QEasingCurve.OutQuint)])}),
    
])

SELECTION_TEXT_DEFS = [
    # TextDef(x=1.00, y=0.00, text='', font_size=14.0, color=QColor(255,255,255,0), phases={
    #     'selected':   Phase([TextTween(x=1.00, y=0.00, start=0.00, dur=0.40, ease=QEasingCurve.OutQuint, color=QColor(255,255,255,220), h_align=1.00, v_align=0.00, font_size=14.0, px=-20, py=15)]),
    #     'unselected': Phase([TextTween(x=1.00, y=0.00, start=0.00, dur=0.30, ease=QEasingCurve.OutQuint, color=QColor(255,255,255,80),  h_align=1.00, v_align=0.00, font_size=14.0, px=-20, py=15)]),
    #     'unfocused':  Phase([TextTween(x=1.00, y=0.00, start=0.00, dur=0.40, ease=QEasingCurve.OutQuint, color=QColor(255,255,255,0),   h_align=1.00, v_align=0.00, font_size=14.0, px=-20, py=15)]),
    # }, bold=True, h_align=1.00, v_align=0.00, px=0, py=15, text_fn=lambda cam: cam.name),
    # TextDef(x=1.00, y=0.00, text='', font_size=14.0, color=QColor(255,255,255,0), phases={
    #     'selected':   Phase([TextTween(x=1.00, y=0.00, start=0.00, dur=0.40, ease=QEasingCurve.OutQuint, color=QColor(255,255,255,220), h_align=1.00, v_align=0.00, font_size=14.0, px=-20, py=35)]),
    #     'unselected': Phase([TextTween(x=1.00, y=0.00, start=0.00, dur=0.30, ease=QEasingCurve.OutQuint, color=QColor(255,255,255,80),  h_align=1.00, v_align=0.00, font_size=14.0, px=-20, py=35)]),
    #     'unfocused':  Phase([TextTween(x=1.00, y=0.00, start=0.00, dur=0.40, ease=QEasingCurve.OutQuint, color=QColor(255,255,255,0),   h_align=1.00, v_align=0.00, font_size=14.0, px=-20, py=35)]),
    # }, bold=True, h_align=1.00, v_align=0.00, px=0, py=15, text_fn=lambda cam: cam.serial),
    # TextDef(x=0.00, y=0.00, text='CAMERA #<#>', font_size=14.0, color=QColor(255,255,255,0), phases={
    #     'selected':   Phase([TextTween(x=0.00, y=0.00, start=0.00, dur=0.40, ease=QEasingCurve.OutQuint, color=QColor(255,255,255,220), h_align=0.00, v_align=0.00, font_size=14.0, px=20, py=15)]),
    #     'unselected': Phase([TextTween(x=0.00, y=0.00, start=0.00, dur=0.30, ease=QEasingCurve.OutQuint, color=QColor(255,255,255,80),  h_align=0.00, v_align=0.00, font_size=14.0, px=20, py=15)]),
    #     'unfocused':  Phase([TextTween(x=0.00, y=0.00, start=0.00, dur=0.40, ease=QEasingCurve.OutQuint, color=QColor(255,255,255,0),   h_align=0.00, v_align=0.00, font_size=14.0, px=20, py=15)]),
    # }, bold=True, h_align=1.00, v_align=0.00, px=0, py=15, text_fn=lambda cam: cam.position),
    # TextDef(x=0.00, y=1.00, text='EXPOSURE: <#>', font_size=9.0, color=QColor(255,255,255,0), phases={
    #     'selected':   Phase([TextTween(x=0.00, y=1.00, start=0.00, dur=0.40, ease=QEasingCurve.OutQuint, color=QColor(255,255,255,220), h_align=0.00, v_align=1.00, font_size=9.0, px=20, py=-15)]),
    #     'unselected': Phase([TextTween(x=0.00, y=1.00, start=0.00, dur=0.30, ease=QEasingCurve.OutQuint, color=QColor(255,255,255,80),  h_align=0.00, v_align=1.00, font_size=9.0, px=20, py=-15)]),
    #     'unfocused':  Phase([TextTween(x=0.00, y=1.00, start=0.00, dur=0.40, ease=QEasingCurve.OutQuint, color=QColor(255,255,255,0),   h_align=0.00, v_align=1.00, font_size=9.0, px=20, py=-15)]),
    # }, h_align=1.00, v_align=1.00, px=0, py=-15, text_fn=lambda cam: cam.exposure),
    # TextDef(x=0.00, y=1.00, text='GAIN: <#>', font_size=9.0, color=QColor(255,255,255,0), phases={
    #     'selected':   Phase([TextTween(x=0.00, y=1.00, start=0.00, dur=0.40, ease=QEasingCurve.OutQuint, color=QColor(255,255,255,220), h_align=0.00, v_align=1.00, font_size=9.0, px=20, py=-30)]),
    #     'unselected': Phase([TextTween(x=0.00, y=1.00, start=0.00, dur=0.30, ease=QEasingCurve.OutQuint, color=QColor(255,255,255,80),  h_align=0.00, v_align=1.00, font_size=9.0, px=20, py=-30)]),
    #     'unfocused':  Phase([TextTween(x=0.00, y=1.00, start=0.00, dur=0.40, ease=QEasingCurve.OutQuint, color=QColor(255,255,255,0),   h_align=0.00, v_align=1.00, font_size=9.0, px=20, py=-30)]),
    # }, h_align=1.00, v_align=1.00, px=0, py=-15, text_fn=lambda cam: cam.gain),
    # TextDef(x=0.00, y=1.00, text='GAMMA: <#>', font_size=9.0, color=QColor(255,255,255,0), phases={
    #     'selected':   Phase([TextTween(x=0.00, y=1.00, start=0.00, dur=0.40, ease=QEasingCurve.OutQuint, color=QColor(255,255,255,220), h_align=0.00, v_align=1.00, font_size=9.0, px=20, py=-45)]),
    #     'unselected': Phase([TextTween(x=0.00, y=1.00, start=0.00, dur=0.30, ease=QEasingCurve.OutQuint, color=QColor(255,255,255,80),  h_align=0.00, v_align=1.00, font_size=9.0, px=20, py=-45)]),
    #     'unfocused':  Phase([TextTween(x=0.00, y=1.00, start=0.00, dur=0.40, ease=QEasingCurve.OutQuint, color=QColor(255,255,255,0),   h_align=0.00, v_align=1.00, font_size=9.0, px=20, py=-45)]),
    # }, h_align=1.00, v_align=1.00, px=0, py=-15, text_fn=lambda cam: cam.gamma),
]

# ──────────────────────── SETTING OVERLAY ────────────────────────

def _val_text(unit: str) -> Callable[[float, float], str]:
    def fn(val: float, delta: float) -> str:
        s = f"{int(val)}{unit}"
        if delta != 0: s += f"  ({int(delta):+})"
        return s
    return fn

CATEGORY_DEFS = expand_defs([
    # Darken Background
    Rect(P(0.00,0.00), P(1.00,1.00), fill_color=QColor(8,8,8,0), phases={
        'open':  Phase([RectTween(P(0.00,0.00), P(1.00,1.00), fill_color=QColor(8,8,8,120), start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)]),
        'close': Phase([RectTween(P(0.00,0.00), P(1.00,1.00), fill_color=QColor(8,8,8,0),   start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)])}),

    # Title Highlight
    Rect(P(0, 0.1), P(0,0.1), px1=P(-10, -30), px2=P(-6, 20), br=(P(0, 0), P(0, -4)), fill_color=QColor(255,255,255,0), phases={
        'open':  Phase([Reset(), RectTween(P(0.05, 0.1), P(0.05,0.1), px1=P(-10, -30), px2=P(-6, 20), br=(P(0, 0), P(0, -4)), fill_color=QColor(255,255,255,255), start=0.50, dur=1.60, ease=QEasingCurve.OutQuint)]),
        'close': Phase([RectTween(P(0, 0.1), P(0,0.1), px1=P(-10, -30), px2=P(-6, 20), br=(P(0, 0), P(0, -4)), fill_color=QColor(255,255,255,0),           start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)])}),


    PolygonDef(
        points=[P(0.00,0.50), P(0.25,0.50), P(0.25,0.50), P(1.00,0.50), P(1.00,0.50), P(0.75,0.50), P(0.75,0.50), P(0.00,0.50)],
        px=    [P(-2,0),       P(0,0),        P(0,0),        P(2,0),        P(2,0),        P(0,0),        P(0,0),        P(-2,0)],
        fill_color=QColor(8,8,8,200), outline_color=QColor(255,255,255,0), closed=True, line_width=2.0, phases={
            'open':  Phase([Reset(),
                            PolygonTween(points=[P(0.00,0.10), P(0.25,0.10), P(0.25,0.10), P(1.00,0.10), P(1.00,0.90), P(0.75,0.90), P(0.75,0.90), P(0.00,0.90)],
                                         px=[P(0,30), P(0,30), P(30,0), P(0,0), P(0,-30), P(0,-30), P(-30,0), P(0,0)],
                                         fill_color=QColor(8,8,8,200), outline_color=QColor(255,255,255,255), start=0.00, dur=0.75, ease=QEasingCurve.OutQuint)]),
            'close': Phase([PolygonTween(points=[P(0.00,0.50), P(0.25,0.50), P(0.25,0.50), P(1.00,0.50), P(1.00,0.50), P(0.75,0.50), P(0.75,0.50), P(0.00,0.50)],
                                         px=[P(0,0), P(0,0), P(0,0), P(0,0), P(0,0), P(0,0), P(0,0), P(0,0)],
                                         fill_color=QColor(8,8,8,200), outline_color=QColor(255,255,255,0), start=0.00, dur=0.75, ease=QEasingCurve.OutQuint)]),
        }),
    PolygonDef(
        points=[P(0.25,0.50), P(0.25,0.50), P(0.25,0.50), P(0.25,0.50)],
        px=    [P(0,0),       P(0,0),        P(0,0),        P(0,0)],
        fill_color=QColor(255,255,255,0), outline_color=QColor(255,255,255,0), closed=True, line_width=2, d_flip=True, phases={
            'open':  Phase([Reset(),
                            PolygonTween(points=[P(0.25,0.10), P(0.25,0.10), P(0.25,0.10), P(0.25,0.10)], px=[P(15,15), P(0,30), P(0,30), P(15,15)], fill_color=QColor(255,255,255,255), outline_color=QColor(255,255,255,255), start=0.00, dur=0.75, ease=QEasingCurve.OutQuint, blend=True),
                            PolygonTween(points=[P(0.00,0.00), P(0.00,0.00), P(-0.20,0.00), P(-0.20,0.00)], px=[P(0,0), P(0,0), P(0,0), P(0,0)],     fill_color=QColor(255,255,255,255), outline_color=QColor(255,255,255,255), start=0.00, dur=2.00, ease=QEasingCurve.OutQuint)]),
            'close': Phase([PolygonTween(points=[P(0.25,0.50), P(0.25,0.50), P(0.25,0.50), P(0.25,0.50)], px=[P(0,0), P(0,0), P(0,0), P(0,0)],       fill_color=QColor(255,255,255,0),   outline_color=QColor(255,255,255,0),   start=0.00, dur=0.75, ease=QEasingCurve.OutQuint)]),
        }),
])

SETTING_DEFS = CATEGORY_DEFS

SETTING_TEXT_DEFS = [
    TextDef(x=0.165, y=0.10, text='CAMERA SETTINGS', font_size=25.0, color=QColor(255,255,255,0), phases={
        'open':  Phase([Reset(), TextTween(x=0.05, y=0.10, start=0.00, dur=2.00, ease=QEasingCurve.OutQuint, color=QColor(255,255,255,255))]),
        'close': Phase([         TextTween(x=0.165, y=0.10, start=0.00, dur=0.50, ease=QEasingCurve.OutQuint, color=QColor(255,255,255,0))]),
    }, bold=True, italic=True, font_family='Oxanium SemiBold', h_align=0, v_align=1.0, uniform_scale=False, px=10, py=10, always_visible=True),
]








# ── Shared phase builders ─────────────────────────────────────────

def _track_phases(y: float) -> Dict[str, Phase]:
    return {
        'open':     Phase([PolygonTween(points=[P(0.25,y), P(0.25,y), P(0.25,y), P(0.25,y)], fill_color=QColor(255,255,255,40), start=0.00, dur=0.00, ease=QEasingCurve.OutQuint),
                           PolygonTween(points=[P(0.25,y), P(0.75,y), P(0.75,y), P(0.25,y)], fill_color=QColor(255,255,255,40), start=0.20, dur=1.00, ease=QEasingCurve.OutQuint)]),
        'changed':  Phase([PolygonTween(points=[P(0.25,y), P(0.75,y), P(0.75,y), P(0.25,y)], fill_color=QColor(255,255,255,255), start=0.00, dur=1.00, ease=QEasingCurve.OutQuint)]),
        'reverted': Phase([PolygonTween(points=[P(0.25,y), P(0.75,y), P(0.75,y), P(0.25,y)], fill_color=QColor(255,255,255,40), start=0.00, dur=1.00, ease=QEasingCurve.OutQuint)]),
        'close':    Phase([PolygonTween(points=[P(0.25,y), P(0.25,y), P(0.25,y), P(0.25,y)], fill_color=QColor(255,255,255,0), start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)]),
    }

def _knob_phases() -> Dict[str, Phase]:
    s = 12
    return {
        'open':      Phase([PolygonTween(points=[P(0,0),P(0,0),P(0,0),P(0,0)], px=[P(0,-s),P(s,0),P(0,s),P(-s,0)],                     fill_color=QColor(255,255,255),   start=0.00, dur=1.00, ease=QEasingCurve.OutQuint)]),
        'hovered':   Phase([PolygonTween(points=[P(0,0),P(0,0),P(0,0),P(0,0)], px=[P(0,-s*1.35),P(s*1.35,0),P(0,s*1.35),P(-s*1.35,0)], fill_color=QColor(255,255,255),   start=0.00, dur=0.15, ease=QEasingCurve.OutQuint)]),
        'unhovered': Phase([PolygonTween(points=[P(0,0),P(0,0),P(0,0),P(0,0)], px=[P(0,-s),P(s,0),P(0,s),P(-s,0)],                     fill_color=QColor(255,255,255),   start=0.00, dur=0.15, ease=QEasingCurve.OutQuint)]),
        'pressed':   Phase([PolygonTween(points=[P(0,0),P(0,0),P(0,0),P(0,0)], px=[P(0,-s*0.85),P(s*0.85,0),P(0,s*0.85),P(-s*0.85,0)], fill_color=QColor(180,180,180),   start=0.00, dur=0.08, ease=QEasingCurve.OutQuint)]),
        'released':  Phase([PolygonTween(points=[P(0,0),P(0,0),P(0,0),P(0,0)], px=[P(0,-s*1.35),P(s*1.35,0),P(0,s*1.35),P(-s*1.35,0)], fill_color=QColor(255,255,255),   start=0.00, dur=0.12, ease=QEasingCurve.OutBack)]),
        'close':     Phase([PolygonTween(points=[P(0,0),P(0,0),P(0,0),P(0,0)], px=[P(0,0),P(0,0),P(0,0),P(0,0)],                       fill_color=QColor(255,255,255,0), start=0.00, dur=0.20, ease=QEasingCurve.InQuint)]),
    }

def _mark_phases() -> Dict[str, Phase]:
    return {
        'visible': Phase([PolygonTween(points=[P(0,0),P(0,0),P(0,0),P(0,0)], fill_color=QColor(255,255,255,255), start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)]),
        'hidden':  Phase([PolygonTween(points=[P(0,0),P(0,0),P(0,0),P(0,0)], fill_color=QColor(255,255,255,0), start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)]),
        'close':   Phase([PolygonTween(points=[P(0,0),P(0,0),P(0,0),P(0,0)], fill_color=QColor(255,255,255,0), start=0.00, dur=0.30, ease=QEasingCurve.InQuint)]),
    }

def _group_phases(y: float) -> Dict[str, Phase]:
    return {
        'open':  Phase([PolygonTween(points=[P(0, 0)], px=[P(0, 0)], start=0.20, dur=0.50, ease=QEasingCurve.OutQuint)]),
        'close': Phase([PolygonTween(points=[P(0, 0)], px=[P(0, 0)], start=0.00, dur=0.40, ease=QEasingCurve.InQuint)]),
    }

def _slider_texts(x: float, y: float, label: str, unit: str) -> SliderTextDefs:
    col_dim  = QColor(255, 255, 255, 180)
    col_full = QColor(255, 255, 255, 255)
    col_zero = QColor(255, 255, 255, 0)
    fam      = 'Oxanium SemiBold'
    return SliderTextDefs(
        label = TextDef(x=x, y=y, px=-110.0, py=0, text=label, font_size=18.0, color=col_zero, phases={
                'open':     Phase([TextTween(x=x, y=y, start=0.00, dur=1.50, ease=QEasingCurve.OutQuint, color= col_dim, h_align=1.0, v_align=0.5, font_size=18.0, px=-15, py=0)]),
                'close':    Phase([TextTween(x=x, y=y, start=0.00, dur=0.30, ease=QEasingCurve.InQuint,  color=col_zero, h_align=1.0, v_align=0.5, font_size=18.0, px=-15, py=0)])},
            bold=True, italic=True, font_family=fam, h_align=1.0, v_align=0.5, uniform_scale=False, always_visible=True),
        min_val = TextDef(x=x, y=y, px=-100.0, py=14.0, text='', font_size=13.0, color=col_zero, phases={
                'open':     Phase([TextTween(x=x, y=y, start=0.00, dur=1.50, ease=QEasingCurve.OutQuint, color= col_dim, h_align=0.0, v_align=0.0, font_size=13.0, px=0, py=14)]),
                'close':    Phase([TextTween(x=x, y=y, start=0.00, dur=0.30, ease=QEasingCurve.InQuint,  color=col_zero, h_align=0.0, v_align=0.0, font_size=13.0, px=0, py=14)])},
            bold=False, italic=False, font_family=fam, h_align=0.0, v_align=0.0, uniform_scale=False, always_visible=True, text_fn=lambda ctx: f"{int(ctx.defn.attr.min_val)}{unit}" if ctx else ''),
        max_val = TextDef(x=x, y=y, px=100.0, py=14.0, text='', font_size=13.0, color=col_zero, phases={
                'open':     Phase([TextTween(x=x, y=y, start=0.00, dur=1.50, ease=QEasingCurve.OutQuint, color= col_dim, h_align=1.0, v_align=0.0, font_size=13.0, px=0, py=14)]),
                'close':    Phase([TextTween(x=x, y=y, start=0.00, dur=0.30, ease=QEasingCurve.InQuint,  color=col_zero, h_align=1.0, v_align=0.0, font_size=13.0, px=0, py=14)])},
            bold=False, italic=False, font_family=fam, h_align=1.0, v_align=0.0, uniform_scale=False, always_visible=True, text_fn=lambda ctx: f"{int(ctx.defn.attr.max_val)}{unit}" if ctx else ''),
        current = TextDef(x=0.0, y=0.0, px=0.0, py=-14.0, text='', font_size=13.0, color=col_zero, phases={
                'open':     Phase([TextTween(x=0.0, y=0.0, start=0.00, dur=1.50,  ease=QEasingCurve.OutQuint, color=col_dim,  h_align=0.5, v_align=1.0, font_size=13.0, px=0, py=-14)]),
                'changed':  Phase([TextTween(x=0.0, y=0.0, start=0.00, dur=0.20,  ease=QEasingCurve.OutQuint, color=col_full, h_align=0.5, v_align=1.0, font_size=13.0, px=0, py=-14)]),
                'reverted': Phase([TextTween(x=0.0, y=0.0, start=0.00, dur=0.20,  ease=QEasingCurve.OutQuint, color=col_dim,  h_align=0.5, v_align=1.0, font_size=13.0, px=0, py=-14)]),
                'close':    Phase([TextTween(x=0.0, y=0.0, start=0.00, dur=0.30,  ease=QEasingCurve.InQuint,  color=col_zero, h_align=0.5, v_align=1.0, font_size=13.0, px=0, py=-14)])},
            bold=False, italic=False, font_family=fam, h_align=0.5, v_align=1.0, uniform_scale=False, always_visible=True, text_fn=lambda sg: (f"{int(sg._cur_value)}{sg.defn.attr.unit}" + (f"  ({int(sg._cur_value - sg._initial_value):+})" if sg.has_change else '')) if sg else ''),
    )


# ── Slider defs ───────────────────────────────────────────────────

def _make_slider(y: float, attr: AttributeDef) -> SliderGroupDef:
    return SliderGroupDef(
        x=0.25, y=y, px=0.0, py=0.0,
        lx=0.50, lpx=0.0,
        attr      = attr,
        track     = make_track_def(0.25, y, 0, 0, 0.00, 0, h_px=6,
                        fill_color=QColor(255,255,255,40),
                        phases=_track_phases(y)),
        knob      = make_knob_def(phases=_knob_phases()),
        mark_fill = make_mark_fill_def(0.25, y, 0, 0, h_px=10,
                        fill_color=QColor(255,255,255,60),
                        phases=_mark_phases()),
        mark_tick = make_mark_tick_def(0.25, y, 0, 0,
                        w_px=3, h_px=16,
                        fill_color=QColor(255,255,255,200),
                        phases=_mark_phases()),
        texts     = _slider_texts(0.25, y, attr.label, attr.unit),
        phases    = _group_phases(y),
        delay     = attr.delay
    )


SETTING_SLIDER_DEFS = [
    _make_slider(0.30, AttributeDef(
        value_fn = lambda ctx: ctx.exposure,
        set_fn   = lambda ctx, v: setattr(ctx, 'pending_exposure', int(v)),
        min_val=5000, max_val=60000, step=1000, label='EXPOSURE', unit='µs', delay=0.0,
    )),
    _make_slider(0.40, AttributeDef(
        value_fn = lambda ctx: ctx.gain,
        set_fn   = lambda ctx, v: setattr(ctx, 'pending_gain', int(v)),
        min_val=0, max_val=30000, step=1000, label='GAIN', unit='', delay=0.1,
    )),
    _make_slider(0.50, AttributeDef(
        value_fn = lambda ctx: ctx.gamma,
        set_fn   = lambda ctx, v: setattr(ctx, 'pending_gamma', int(v)),
        min_val=2, max_val=9, step=1, label='GAMMA', unit='', delay=0.2,
    )),
]


SETTING_BUTTON_DEFS = [
    ButtonDef(
        poly = PolygonDef(
            points = [P(0.5,0.9), P(0.5,0.9), P(0.5,0.9), P(0.5,0.9), P(0.5,0.9)],
            px     = [P(0,-51), P(0,-51), P(0,-31), P(0,-11), P(0,-11)],
            fill_color=QColor(60,60,60), closed=True, phases={
                'open':      Phase([PolygonTween(points=[P(0.5,0.9)]*5, px=[P(15 + 0,-51), P(15 + -200,-51), P(15 + -220,-31), P(15 + -200,-11), P(15 + -40,-11)], fill_color=QColor(60,60,60),   start=0.00, dur=0.75, ease=QEasingCurve.OutQuint)]),
                'hovered':   Phase([PolygonTween(points=[P(0.5,0.9)]*5, px=[P(15 + 0,-51), P(15 + -200,-51), P(15 + -220,-31), P(15 + -200,-11), P(15 + -40,-11)], fill_color=QColor(85,85,85),   start=0.00, dur=0.12, ease=QEasingCurve.OutQuint)]),
                'unhovered': Phase([PolygonTween(points=[P(0.5,0.9)]*5, px=[P(15 + 0,-51), P(15 + -200,-51), P(15 + -220,-31), P(15 + -200,-11), P(15 + -40,-11)], fill_color=QColor(60,60,60),   start=0.00, dur=0.15, ease=QEasingCurve.OutQuint)]),
                'pressed':   Phase([PolygonTween(points=[P(0.5,0.9)]*5, px=[P(15 + 0,-51), P(15 + -200,-51), P(15 + -220,-31), P(15 + -200,-11), P(15 + -40,-11)], fill_color=QColor(145,145,145),start=0.00, dur=0.06, ease=QEasingCurve.OutQuint)]),
                'released':  Phase([PolygonTween(points=[P(0.5,0.9)]*5, px=[P(15 + 0,-51), P(15 + -200,-51), P(15 + -220,-31), P(15 + -200,-11), P(15 + -40,-11)], fill_color=QColor(85,85,85),   start=0.00, dur=0.10, ease=QEasingCurve.OutBack)]),
                'close':     Phase([PolygonTween(points=[P(0.5,0.9)]*5, px=[P(15 + 0,-51), P(15 + 0,-51), P(15 + -20,-31), P(15 + -40,-11), P(15 + -40,-11)], fill_color=QColor(60,60,60), start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)]),
            }),
        label='CANCEL', action='cancel',
        text_color=QColor(255,255,255),
    ),
    ButtonDef(
        poly = PolygonDef(
            points = [P(0.5,0.9), P(0.5,0.9), P(0.5,0.9), P(0.5,0.9), P(0.5,0.9)],
            px     = [P(0,-11), P(0,-11), P(0,-31), P(0,-51), P(0,-51)],
            fill_color=QColor(255,255,255), closed=True, phases={
                'open':      Phase([PolygonTween(points=[P(0.5,0.9)]*5, px=[P(-15 + 0,-11), P(-15 + 200,-11), P(-15 + 220,-31), P(-15 + 200,-51), P(-15 + 40,-51)], fill_color=QColor(255,255,255),   start=0.00, dur=0.75, ease=QEasingCurve.OutQuint)]),
                'hovered':   Phase([PolygonTween(points=[P(0.5,0.9)]*5, px=[P(-15 + 0,-11), P(-15 + 200,-11), P(-15 + 220,-31), P(-15 + 200,-51), P(-15 + 40,-51)], fill_color=QColor(220,220,220),   start=0.00, dur=0.12, ease=QEasingCurve.OutQuint)]),
                'unhovered': Phase([PolygonTween(points=[P(0.5,0.9)]*5, px=[P(-15 + 0,-11), P(-15 + 200,-11), P(-15 + 220,-31), P(-15 + 200,-51), P(-15 + 40,-51)], fill_color=QColor(255,255,255),   start=0.00, dur=0.15, ease=QEasingCurve.OutQuint)]),
                'pressed':   Phase([PolygonTween(points=[P(0.5,0.9)]*5, px=[P(-15 + 0,-11), P(-15 + 200,-11), P(-15 + 220,-31), P(-15 + 200,-51), P(-15 + 40,-51)], fill_color=QColor(160,160,160),   start=0.00, dur=0.06, ease=QEasingCurve.OutQuint)]),
                'released':  Phase([PolygonTween(points=[P(0.5,0.9)]*5, px=[P(-15 + 0,-11), P(-15 + 200,-11), P(-15 + 220,-31), P(-15 + 200,-51), P(-15 + 40,-51)], fill_color=QColor(220,220,220),   start=0.00, dur=0.10, ease=QEasingCurve.OutBack)]),
                'close':     Phase([PolygonTween(points=[P(0.5,0.9)]*5, px=[P(-15 + 0,-11), P(-15 + 0,-11), P(-15 + 20,-31), P(-15 + 40,-51), P(-15 + 40,-51)], fill_color=QColor(255,255,255), start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)]),
            }),
        label='APPLY', action='apply',
        text_color=QColor(10,10,14),
    ),
]

# ──────────────────────── CAMERA SELECT OVERLAY ──────────────────

CS_DEFS = CATEGORY_DEFS + expand_defs([
    PolygonDef(
        points=[P(0.5,0.9), P(0.5,0.9), P(0.5,0.9), P(0.5,0.9)],
        px=    [P(-82, -122), P(-82, -122), P(-82, -122), P(-82, -122)],
        fill_color=QColor(255,255,255), closed=True, h_flip=True, phases={
            'open':  Phase([Reset(),
                            PolygonTween(points=[P(0.5,0.9)]*4,
                                         px=[P(-82, -122), P(-96,-122), P(-84,-124), P(-76,-134)],
                                         fill_color=QColor(255,255,255), start=0.00, dur=0.65, ease=QEasingCurve.OutQuint)]),
            'close': Phase([PolygonTween(points=[P(0.5,0.9)]*4,
                                         px=[P(-82, -122), P(-82, -122), P(-82, -122), P(-82, -122)],
                                         fill_color=QColor(255,255,255), start=0.00, dur=0.65, ease=QEasingCurve.OutQuint)]),
        }),
])

CS_TEXT_DEFS = [
    TextDef(0.165, 0.10, 'DISPLAY MODE', 25.0, QColor(255,255,255,0), phases={
        'open':  Phase([Reset(), TextTween(x=0.05, y=0.10, start=0.00, dur=2.00, ease=QEasingCurve.OutQuint, color=QColor(255,255,255,255), h_align=0, v_align=1.0, font_size=25.0, px=10, py=10)]),
        'close': Phase([         TextTween(x=0.165, y=0.10, start=0.00, dur=0.50, ease=QEasingCurve.OutQuint, color=QColor(255,255,255,0),   h_align=0, v_align=1.0, font_size=25.0, px=10, py=10)]),
    }, bold=True, italic=True, font_family='Oxanium SemiBold', h_align=0, v_align=1.0, uniform_scale=False, always_visible=True),
    TextDef(0.50, 0.90, '', 14.0, QColor(255,255,255,0), phases={
        'open':  Phase([Reset(), TextTween(x=0.50, y=0.90, start=0.10, dur=0.30, ease=QEasingCurve.OutQuint, color=QColor(255,255,255,180), h_align=0.5, v_align=1.0, font_size=9.0, px=0, py=-162)]),
        'close': Phase([         TextTween(x=0.50, y=0.90, start=0.00, dur=0.20, ease=QEasingCurve.InQuint,  color=QColor(255,255,255,0),   h_align=0.5, v_align=1.0, font_size=9.0, px=0, py=-162)]),
    }, bold=False, italic=False, font_family='Oxanium SemiBold', h_align=0.5, v_align=1.0, uniform_scale=False, px=0, py=-162, always_visible=True,
       text_fn=lambda ctx: f"LAYOUT  {ctx['display_mode']+1} / {ctx['num_modes']}"),
    TextDef(0.50, 0.90, '', 14.0, QColor(255,255,255,0), phases={
        'open':  Phase([Reset(), TextTween(x=0.50, y=0.90, start=0.10, dur=0.30, ease=QEasingCurve.OutQuint, color=QColor(255,255,255,200), h_align=0.5, v_align=0.0, font_size=9.0, px=0, py=-78)]),
        'close': Phase([         TextTween(x=0.50, y=0.90, start=0.00, dur=0.20, ease=QEasingCurve.InQuint,  color=QColor(255,255,255,0),   h_align=0.5, v_align=0.0, font_size=9.0, px=0, py=-78)]),
    }, bold=False, italic=False, font_family='Oxanium SemiBold', h_align=0.5, v_align=0.0, uniform_scale=False, px=0, py=-78, always_visible=True,
       text_fn=lambda ctx: f"CAM  {ctx['num_cams']} / {ctx['max_cams']}"),
]

def _cs_btn_phases(idle_col, hover_col, press_col, px, open_start=0.15, open_dur=0.30, close_dur=0.20):
    return {
        'open':      Phase([PolygonTween(points=[P(0.5,0.9)]*5, px=px, fill_color=idle_col,  start=open_start, dur=open_dur,  ease=QEasingCurve.OutQuint)]),
        'hovered':   Phase([PolygonTween(points=[P(0.5,0.9)]*5, px=px, fill_color=hover_col, start=0.00,       dur=0.12,      ease=QEasingCurve.OutQuint)]),
        'unhovered': Phase([PolygonTween(points=[P(0.5,0.9)]*5, px=px, fill_color=idle_col,  start=0.00,       dur=0.15,      ease=QEasingCurve.OutQuint)]),
        'pressed':   Phase([PolygonTween(points=[P(0.5,0.9)]*5, px=px, fill_color=press_col, start=0.00,       dur=0.06,      ease=QEasingCurve.OutQuint)]),
        'released':  Phase([PolygonTween(points=[P(0.5,0.9)]*5, px=px, fill_color=hover_col, start=0.00,       dur=0.10,      ease=QEasingCurve.OutBack)]),
        'close':     Phase([PolygonTween(points=[P(0.5,0.9)]*5, px=px, fill_color=QColor(255,255,255,0), start=0.00, dur=close_dur, ease=QEasingCurve.InQuint)]),
    }

_idle  = QColor(255,255,255,30)
_hover = QColor(255,255,255,60)
_press = QColor(255,255,255,100)
_zero  = QColor(255,255,255,0)

_cam_up_px    = [P(-60,-162), P(60,-162), P(80,-122), P(-80,-122)]
_cam_down_px  = [P(-80,-120), P(80,-120), P(60,-80), P(-60,-80)]
_scroll_l_px  = [P(-202,-120), P(-82,-120), P(-62,-80), P(-222,-80)]
_scroll_r_px  = [P(82,-120), P(202,-120), P(222,-80), P(62,-80)]

CS_BUTTON_DEFS = [
    ButtonDef(
        poly=PolygonDef(
            points=[P(0.5,0.9)]*5, px=_cam_up_px,
            fill_color=_zero, closed=True,
            phases=_cs_btn_phases(_idle, _hover, _press, _cam_up_px, open_start=0.15, open_dur=0.30, close_dur=0.20)),
        label='+', action='cam_up', text_color=QColor(255,255,255)),

    ButtonDef(
        poly=PolygonDef(
            points=[P(0.5,0.9)]*5, px=_cam_down_px,
            fill_color=_zero, closed=True,
            phases=_cs_btn_phases(_idle, _hover, _press, _cam_down_px, open_start=0.15, open_dur=0.30, close_dur=0.20)),
        label='−', action='cam_down', text_color=QColor(255,255,255)),

    ButtonDef(
        poly=PolygonDef(
            points=[P(0.5,0.9)]*5, px=_scroll_l_px,
            fill_color=_zero, closed=True,
            phases=_cs_btn_phases(_idle, _hover, _press, _scroll_l_px, open_start=0.10, open_dur=0.30, close_dur=0.20)),
        label='◀', action='scroll_left', text_color=QColor(255,255,255)),

    ButtonDef(
        poly=PolygonDef(
            points=[P(0.5,0.9)]*5, px=_scroll_r_px,
            fill_color=_zero, closed=True,
            phases=_cs_btn_phases(_idle, _hover, _press, _scroll_r_px, open_start=0.10, open_dur=0.30, close_dur=0.20)),
        label='▶', action='scroll_right', text_color=QColor(255,255,255)),
]

CS_BUTTON_DEFS += SETTING_BUTTON_DEFS

PREVIEW_BOX_DEF = PreviewBoxDef(
    label_font_size   = 14.0,
    label_font_family = 'Oxanium SemiBold',
    name_font_size    = 11.0,
    slots = {
        -2: Rect(P(-0.16, 0.5), P(-0.02, 0.5), fill_color=QColor(255,255,255,25), outline_color=QColor(255,255,255,), line_width=2.0, phases={
            'open':  Phase([RectTween(P(-0.16, 0.43), P(-0.02, 0.57), fill_color=QColor(255,255,255,50), outline_color=QColor(255,255,255,255), start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)]),
            'close': Phase([RectTween(P(-0.16, 0.50), P(-0.02, 0.50), fill_color=QColor(255,255,255,25), outline_color=QColor(255,255,255,),  start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)]),
        }),
        -1: Rect(P(0.075, 0.5), P(0.275, 0.5), fill_color=QColor(255,255,255,25), outline_color=QColor(255,255,255,), line_width=2.0, phases={
            'open':  Phase([RectTween(P(0.075, 0.40), P(0.275, 0.60), fill_color=QColor(255,255,255,50), outline_color=QColor(255,255,255,255), start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)]),
            'close': Phase([RectTween(P(0.075, 0.50), P(0.275, 0.50), fill_color=QColor(255,255,255,25), outline_color=QColor(255,255,255,),  start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)]),
        }),
        0: Rect(P(0.35, 0.50), P(0.65, 0.50), fill_color=QColor(255,255,255,25), outline_color=QColor(255,255,255,), line_width=2.0, phases={
            'open':  Phase([RectTween(P(0.35, 0.35), P(0.65, 0.65), fill_color=QColor(255,255,255,50), outline_color=QColor(255,255,255,255), start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)]),
            'close': Phase([RectTween(P(0.35, 0.50), P(0.65, 0.50), fill_color=QColor(255,255,255,25), outline_color=QColor(255,255,255,),  start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)]),
        }),
        1: Rect(P(0.725, 0.50), P(0.925, 0.50), fill_color=QColor(255,255,255,25), outline_color=QColor(255,255,255,), line_width=2.0, phases={
            'open':  Phase([RectTween(P(0.725, 0.40), P(0.925, 0.60), fill_color=QColor(255,255,255,50), outline_color=QColor(255,255,255,255), start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)]),
            'close': Phase([RectTween(P(0.725, 0.50), P(0.925, 0.50), fill_color=QColor(255,255,255,25), outline_color=QColor(255,255,255,),  start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)]),
        }),
        2: Rect(P(1.02, 0.50), P(1.16, 0.50), fill_color=QColor(255,255,255,25), outline_color=QColor(255,255,255,), line_width=2.0, phases={
            'open':  Phase([RectTween(P(1.02, 0.43), P(1.16, 0.57), fill_color=QColor(255,255,255,50), outline_color=QColor(255,255,255,255), start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)]),
            'close': Phase([RectTween(P(1.02, 0.50), P(1.16, 0.50), fill_color=QColor(255,255,255,25), outline_color=QColor(255,255,255,),  start=0.00, dur=0.50, ease=QEasingCurve.OutQuint)]),
        }),
    }
)