extends Node3D

@export var enemy_name: String = "Ritual Enemy"
@export var face_player: bool = true

func _ready() -> void:
    add_to_group("enemy")

func _process(_delta: float) -> void:
    if not face_player:
        return

    var player := get_tree().get_first_node_in_group("player") as Node3D
    if player == null:
        return

    var target := Vector3(player.global_position.x, global_position.y, player.global_position.z)
    if global_position.distance_to(target) > 0.1:
        look_at(target, Vector3.UP)
