extends SceneTree

const SCENE_PATH := "res://scenes/blockout/suburban_horror_blockout.tscn"

var scene: Node
var player: CharacterBody3D
var world_root: Node
var failed := false

func _init() -> void:
    call_deferred("_run")

func _run() -> void:
    scene = load(SCENE_PATH).instantiate()
    root.add_child(scene)
    await process_frame

    player = scene.get_node("Player") as CharacterBody3D
    world_root = scene.get_node("WorldRoot")

    _expect_world_bounds()
    if _stop_if_failed():
        return
    _expect_fall_recovery()
    if _stop_if_failed():
        return

    print("WORLD BOUNDS CHECK PASSED")
    quit(0)

func _expect_world_bounds() -> void:
    var required := [
        "WorldBounds_FogWall_North",
        "WorldBounds_FogWall_South",
        "WorldBounds_FogWall_West",
        "WorldBounds_FogWall_East",
        "ArrivalBounds_LeftFloodedDitch_NoEscape",
        "ArrivalBounds_RightFloodedDitch_NoEscape",
        "ArrivalBounds_BackFloodedWash_NoEscape"
    ]
    for node_name in required:
        var node := world_root.get_node_or_null(node_name) as MeshInstance3D
        if node == null:
            _fail("Missing world bound: " + node_name)
            return
        if not node.has_meta("collision_node"):
            _fail("World bound has no collision: " + node_name)
            return

func _expect_fall_recovery() -> void:
    player.global_position = Vector3(12, -12, 40)
    player.velocity = Vector3(4, -20, 2)
    scene._update_player_fall_protection()

    if player.global_position.y < 0.5:
        _fail("Fall recovery did not return player to playable height.")
        return
    if player.velocity.length() > 0.01:
        _fail("Fall recovery did not clear player velocity.")

    player.global_position = Vector3(120, 1.1, 88)
    player.velocity = Vector3(9, 0, 0)
    scene._update_player_fall_protection()
    if player.global_position.x > 80.0:
        _fail("Out-of-bounds side escape did not recover player.")
        return
    if player.velocity.length() > 0.01:
        _fail("Out-of-bounds side escape did not clear player velocity.")

func _fail(message: String) -> void:
    push_error(message)
    failed = true

func _stop_if_failed() -> bool:
    if failed:
        quit(1)
        return true
    return false
