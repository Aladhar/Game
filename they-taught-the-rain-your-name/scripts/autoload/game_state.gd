extends Node

signal act_changed(act: int)
signal memory_intensity_changed(value: float)
signal game_lost(reason: String)
signal warning_changed(text: String)

var current_act: int = 0
var memory_intensity: float = 0.0
var game_over: bool = false
var player_name: String = "Visitor"

func reset_game() -> void:
    current_act = 0
    memory_intensity = 0.0
    game_over = false
    act_changed.emit(current_act)
    memory_intensity_changed.emit(memory_intensity)
    warning_changed.emit("Do not answer repeated sounds.")

func set_act(value: int) -> void:
    current_act = value
    act_changed.emit(current_act)

func add_memory_intensity(amount: float) -> void:
    if game_over:
        return
    memory_intensity = clamp(memory_intensity + amount, 0.0, 100.0)
    memory_intensity_changed.emit(memory_intensity)

func reduce_memory_intensity(amount: float) -> void:
    memory_intensity = clamp(memory_intensity - amount, 0.0, 100.0)
    memory_intensity_changed.emit(memory_intensity)

func show_warning(text: String) -> void:
    warning_changed.emit(text)

func lose_game(reason: String) -> void:
    if game_over:
        return
    game_over = true
    game_lost.emit(reason)
