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

register_event(EventDef(name='map_window_p1',  value=P(0, 0)))
register_event(EventDef(name='map_window_p2',  value=P(0, 0))) 
register_event(EventDef(name='map_window_px1', value=P(0, 0))) 
register_event(EventDef(name='map_window_px2', value=P(0, 0))) 

register_event(EventDef(name='logger_window_p1',  value=P(0, 0))) 
register_event(EventDef(name='logger_window_p2',  value=P(0, 0)))  
register_event(EventDef(name='logger_window_px1', value=P(0, 0))) 
register_event(EventDef(name='logger_window_px2', value=P(0, 0))) 

register_event(EventDef(name='info_window_p1',  value=P(0, 0))) 
register_event(EventDef(name='info_window_p2',  value=P(0, 0))) 
register_event(EventDef(name='info_window_px1', value=P(0, 0))) 
register_event(EventDef(name='info_window_px2', value=P(0, 0))) 

register_event(EventDef(name='task_window_p1',  value=P(0, 0))) 
register_event(EventDef(name='task_window_p2',  value=P(0, 0)))  
register_event(EventDef(name='task_window_px1', value=P(0, 0))) 
register_event(EventDef(name='task_window_px2', value=P(0, 0))) 