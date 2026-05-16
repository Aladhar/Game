extends Node

@export var max_events: int = 64

var events: Array[Dictionary] = []
var event_counts: Dictionary = {}

func _ready() -> void:
    SceneBus.sound_event_recorded.connect(_on_sound_event_recorded)

func _on_sound_event_recorded(event_data: Dictionary) -> void:
    var clean_event := event_data.duplicate()
    clean_event["time"] = Time.get_ticks_msec() / 1000.0
    clean_event["act"] = GameState.current_act

    events.push_front(clean_event)
    while events.size() > max_events:
        events.pop_back()

    var event_type := str(clean_event.get("type", "unknown"))
    event_counts[event_type] = int(event_counts.get(event_type, 0)) + 1

    var intensity := float(clean_event.get("intensity", 0.5))
    GameState.add_memory_intensity(intensity * 1.8)

func get_recent_events() -> Array[Dictionary]:
    return events.duplicate()

func get_most_repeated_type() -> String:
    var best_type := ""
    var best_count := -1

    for key in event_counts.keys():
        var count := int(event_counts[key])
        if count > best_count:
            best_count = count
            best_type = str(key)

    return best_type

func get_latest_event_of_type(event_type: String) -> Dictionary:
    for event_data in events:
        if str(event_data.get("type", "")) == event_type:
            return event_data
    return {}
