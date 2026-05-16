extends CharacterBody3D

@export var enemy_name: String = "Bell Saint"
@export var face_player: bool = true
@export var slow_turn_speed: float = 0.75
@export var idle_sway_amount: float = 0.035
@export var pulse_speed: float = 0.65
@export var touch_damage: int = 15
@export var damage_range: float = 1.35
@export var damage_cooldown: float = 1.4

@onready var model_root: Node3D = $ModelRoot
@onready var bell_glow: OmniLight3D = $BellGlow

var _time: float = 0.0
var _damage_timer: float = 0.0

func _ready() -> void:
	add_to_group("enemy")
	add_to_group("bell_saint")

func _process(delta: float) -> void:
	_time += delta
	if _damage_timer > 0.0:
		_damage_timer -= delta

	_idle_motion()
	_face_player_slowly(delta)
	_light_pulse()
	_try_touch_damage()

func _idle_motion() -> void:
	if model_root == null:
		return

	model_root.rotation_degrees.z = sin(_time * pulse_speed) * idle_sway_amount * 20.0
	model_root.rotation_degrees.x = sin(_time * pulse_speed * 0.7) * idle_sway_amount * 8.0
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

	bell_glow.light_energy = 1.05 + sin(_time * 2.2) * 0.18 + sin(_time * 7.4) * 0.06

func _try_touch_damage() -> void:
	if _damage_timer > 0.0:
		return

	var player := get_tree().get_first_node_in_group("player") as Node3D
	if player == null:
		return

	if global_position.distance_to(player.global_position) <= damage_range:
		if player.has_method("take_damage"):
			player.take_damage(touch_damage, enemy_name)
			_damage_timer = damage_cooldown
