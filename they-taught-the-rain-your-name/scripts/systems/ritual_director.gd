extends Node

@export var carrier_threshold: float = 30.0
@export var name_threshold: float = 75.0

var carrier_revealed: bool = false
var name_warning_given: bool = false

func _ready() -> void:
    GameState.reset_game()
    GameState.memory_intensity_changed.connect(_on_memory_intensity_changed)
    SceneBus.ritual_rule_changed.emit("Do not answer repeated sounds.")
    GameState.show_warning("Emergency broadcast: do not answer repeated sounds.")

func _on_memory_intensity_changed(value: float) -> void:
    if value >= 8.0 and GameState.current_act == 0:
        GameState.set_act(1)
        GameState.show_warning("Greyhollow is listening.")

    if value >= carrier_threshold and not carrier_revealed:
        carrier_revealed = true
        SceneBus.enemy_stage_changed.emit("PenanceCarrier", 1)
        GameState.show_warning("Something is carrying the sounds you made.")

    if value >= name_threshold and not name_warning_given:
        name_warning_given = true
        SceneBus.ritual_rule_changed.emit("If the rain says your name, do not answer.")
        GameState.show_warning("The broadcast almost said your name.")
