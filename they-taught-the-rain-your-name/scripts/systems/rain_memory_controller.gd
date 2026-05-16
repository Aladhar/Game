extends Node

@export var first_imitation_delay: float = 7.0
@export var repeat_interval: float = 10.0
@export var minimum_memory_to_imitate: float = 4.0

var sound_tracker: Node = null
var imitation_timer: float = 0.0
var has_first_imitation_played: bool = false

func _ready() -> void:
    sound_tracker = get_node_or_null("../SoundEventTracker")
    imitation_timer = first_imitation_delay

func _process(delta: float) -> void:
    if GameState.game_over:
        return

    if GameState.memory_intensity < minimum_memory_to_imitate:
        return

    imitation_timer -= delta

    if imitation_timer <= 0.0:
        play_rain_imitation()
        imitation_timer = repeat_interval

func play_rain_imitation() -> void:
    if sound_tracker == null:
        return

    if not sound_tracker.has_method("get_most_repeated_type"):
        return

    if not sound_tracker.has_method("get_latest_event_of_type"):
        return

    var event_type = sound_tracker.call("get_most_repeated_type")

    if str(event_type) == "":
        return

    var event_data = sound_tracker.call("get_latest_event_of_type", str(event_type))

    if typeof(event_data) != TYPE_DICTIONARY:
        return

    if event_data.is_empty():
        return

    SceneBus.rain_imitation_requested.emit(event_data)
    SceneBus.rain_imitation_played.emit(event_data)

    if not has_first_imitation_played:
        has_first_imitation_played = true
        GameState.show_warning("The rain repeated you.")
        SceneBus.ritual_rule_changed.emit("Do not trust familiar sounds.")
    else:
        GameState.show_warning("You heard yourself in the storm.")

    AudioManager.play_rain_imitation(event_data)
