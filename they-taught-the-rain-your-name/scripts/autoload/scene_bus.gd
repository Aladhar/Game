extends Node

signal sound_event_recorded(event_data: Dictionary)
signal rain_imitation_requested(event_data: Dictionary)
signal rain_imitation_played(event_data: Dictionary)
signal ritual_rule_changed(rule_text: String)
signal enemy_stage_changed(enemy_name: String, stage: int)
signal debug_line_requested(text: String)
