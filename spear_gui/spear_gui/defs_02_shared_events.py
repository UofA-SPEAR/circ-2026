from spear_gui.overlay_system import (
    P, EventDef, register_event
)

# ──────────────────────── EVENT DEFS ────────────────────────

register_event(EventDef(name='main_page', value='close'))

register_event(EventDef(name='layout_mode', value=False))
register_event(EventDef(name='layout_mode_flip', value=True))
register_event(EventDef(name='layout_page', value='close'))

register_event(EventDef(name='force_hide_map_window',    value=False))
register_event(EventDef(name='force_hide_logger_window', value=False))
register_event(EventDef(name='force_hide_info_window',   value=False))
register_event(EventDef(name='force_hide_task_window',   value=False))

# Window Points
register_event(EventDef(name='map_window_p1',  value=P(0, 0)))
register_event(EventDef(name='map_window_p2',  value=P(0, 0))) 
register_event(EventDef(name='logger_window_p1',  value=P(0, 0))) 
register_event(EventDef(name='logger_window_p2',  value=P(0, 0)))  
register_event(EventDef(name='info_window_p1',  value=P(0, 0))) 
register_event(EventDef(name='info_window_p2',  value=P(0, 0))) 
register_event(EventDef(name='task_window_p1',  value=P(0, 0))) 
register_event(EventDef(name='task_window_p2',  value=P(0, 0)))  

register_event(EventDef(name='map_window_px1',  value=P(0, 0)))
register_event(EventDef(name='map_window_px2',  value=P(0, 0))) 
register_event(EventDef(name='logger_window_px1',  value=P(0, 0))) 
register_event(EventDef(name='logger_window_px2',  value=P(0, 0)))  
register_event(EventDef(name='info_window_px1',  value=P(0, 0))) 
register_event(EventDef(name='info_window_px2',  value=P(0, 0))) 
register_event(EventDef(name='task_window_px1',  value=P(0, 0))) 
register_event(EventDef(name='task_window_px2',  value=P(0, 0)))  

register_event(EventDef(name='base_map_window_p1',  value=P(0, 0)))
register_event(EventDef(name='base_map_window_p2',  value=P(0, 0))) 
register_event(EventDef(name='base_logger_window_p1',  value=P(0, 0))) 
register_event(EventDef(name='base_logger_window_p2',  value=P(0, 0)))  
register_event(EventDef(name='base_info_window_p1',  value=P(0, 0))) 
register_event(EventDef(name='base_info_window_p2',  value=P(0, 0))) 
register_event(EventDef(name='base_task_window_p1',  value=P(0, 0))) 
register_event(EventDef(name='base_task_window_p2',  value=P(0, 0)))  

register_event(EventDef(name='base_map_window_px1',  value=P(0, 0)))
register_event(EventDef(name='base_map_window_px2',  value=P(0, 0))) 
register_event(EventDef(name='base_logger_window_px1',  value=P(0, 0))) 
register_event(EventDef(name='base_logger_window_px2',  value=P(0, 0)))  
register_event(EventDef(name='base_info_window_px1',  value=P(0, 0))) 
register_event(EventDef(name='base_info_window_px2',  value=P(0, 0))) 
register_event(EventDef(name='base_task_window_px1',  value=P(0, 0))) 
register_event(EventDef(name='base_task_window_px2',  value=P(0, 0)))  

# Fullscreened window bools
register_event(EventDef(name='window_fullscreen_map',    value=False))
register_event(EventDef(name='window_fullscreen_logger', value=False))
register_event(EventDef(name='window_fullscreen_info',   value=False))
register_event(EventDef(name='window_fullscreen_task',  value=False))

register_event(EventDef(name='fullscreen_window_p1',  value=P(0, 0)))  
register_event(EventDef(name='fullscreen_window_p2',  value=P(1, 1)))  
register_event(EventDef(name='fullscreen_window_px1', value=P(70, 0)))  
register_event(EventDef(name='fullscreen_window_px2', value=P(-70, 0)))  

register_event(EventDef(name='content_phase_map', value='open'))
register_event(EventDef(name='content_phase_logger', value='open'))
register_event(EventDef(name='content_phase_info', value='open'))
register_event(EventDef(name='content_phase_task', value='open'))

# Layout mode
register_event(EventDef(name='layout_selected_window',  value=None))
register_event(EventDef(name='window_disabled_map',     value=False))
register_event(EventDef(name='window_disabled_logger',  value=False))
register_event(EventDef(name='window_disabled_info',    value=False))
register_event(EventDef(name='window_disabled_task',   value=False))
register_event(EventDef(name='layout_overlap_detected', value=False))
register_event(EventDef(name='layout_overlap_phase',    value='close'))