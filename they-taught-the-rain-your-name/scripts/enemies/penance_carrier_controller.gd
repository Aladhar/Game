extends CharacterBody3D

@export var enemy_name: String = "Penance Carrier"
@export var face_player: bool = true
@export var slow_turn_speed: float = 1.15
@export var idle_sway_amount: float = 0.035
@export var idle_sway_speed: float = 0.65

@onready var model_root: Node3D = $ModelRoot
@onready var candle_glow: OmniLight3D = $CandleGlow

var _time: float = 0.0

func _ready() -> void:
	add_to_group("enemy")
	add_to_group("penance_carrier")

func _process(delta: float) -> void:
	_time += delta
	_apply_idle_sway()
	_face_player_slowly(delta)
	_flicker_candle()

func _apply_idle_sway() -> void:
	if model_root == null:
		return

	model_root.rotation_degrees.z = sin(_time * idle_sway_speed) * idle_sway_amount * 18.0
	model_root.position.y = sin(_time * idle_sway_speed * 0.75) * idle_sway_amount

func _face_player_slowly(delta: float) -> void:
	if not face_player:
		return

	var player := get_tree().get_first_node_in_group("player") as Node3D
	if player == null:
		return

	var to_player := player.global_position - global_position
	to_player.y = 0.0

	if to_player.length() < 0.25:
		return

	var target_yaw := atan2(-to_player.x, -to_player.z)
	rotation.y = lerp_angle(rotation.y, target_yaw, slow_turn_speed * delta)

func _flicker_candle() -> void:
	if candle_glow == null:
		return

	candle_glow.light_energy = 1.45 + sin(_time * 7.0) * 0.14 + sin(_time * 13.7) * 0.06
