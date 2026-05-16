extends CharacterBody3D

@export var enemy_name: String = "Bell Saint"
@export var face_player: bool = true
@export var slow_turn_speed: float = 0.9
@export var idle_sway_amount: float = 0.025
@export var pulse_speed: float = 0.85

@onready var model_root: Node3D = $ModelRoot
@onready var bell_glow: OmniLight3D = $BellGlow

var _time: float = 0.0

func _ready() -> void:
	add_to_group("enemy")
	add_to_group("bell_saint")

func _process(delta: float) -> void:
	_time += delta
	_idle_motion()
	_face_player_slowly(delta)
	_light_pulse()

func _idle_motion() -> void:
	if model_root == null:
		return

	model_root.rotation_degrees.z = sin(_time * pulse_speed) * idle_sway_amount * 20.0
	model_root.position.y = sin(_time * pulse_speed * 0.6) * idle_sway_amount

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

func _light_pulse() -> void:
	if bell_glow == null:
		return

	bell_glow.light_energy = 0.9 + sin(_time * 2.8) * 0.16 + sin(_time * 8.1) * 0.04
