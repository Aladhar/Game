extends SceneTree

const SCENE_PATH := "res://scenes/blockout/suburban_horror_blockout.tscn"

var scene: Node
var player: CharacterBody3D
var failed := false

func _init() -> void:
    call_deferred("_run")

func _run() -> void:
    scene = load(SCENE_PATH).instantiate()
    root.add_child(scene)
    await process_frame

    player = scene.get_node("Player") as CharacterBody3D
    _expect_player_stamina()
    if _stop_if_failed():
        return
    _expect_player_crouch()
    if _stop_if_failed():
        return
    _expect_stamina_ui()
    if _stop_if_failed():
        return
    _expect_local_rain()
    if _stop_if_failed():
        return

    _release_input()
    print("PLAYER SYSTEMS CHECK PASSED")
    quit(0)

func _expect_player_stamina() -> void:
    var max_stamina := float(player.get("max_stamina"))
    player.set("stamina", max_stamina)
    player.set("stamina_regen_timer", 0.0)

    Input.action_press("move_forward")
    Input.action_press("sprint")
    player._apply_movement(1.0)
    var drained_stamina := float(player.get("stamina"))
    if drained_stamina >= max_stamina:
        _fail("Sprint did not drain stamina.")
        return

    Input.action_release("sprint")
    player.set("stamina_regen_timer", 0.0)
    player._apply_movement(1.0)
    if float(player.get("stamina")) <= drained_stamina:
        _fail("Stamina did not regenerate after sprint release.")

func _expect_player_crouch() -> void:
    var camera_pivot := player.get_node("CameraPivot") as Node3D
    var body_collision := player.get_node("CollisionShape3D") as CollisionShape3D
    var capsule := body_collision.shape as CapsuleShape3D
    var standing_height := capsule.height
    var standing_camera_y := camera_pivot.position.y

    Input.action_press("crouch")
    player._apply_movement(0.1)
    player._apply_crouch(0.5)

    if not bool(player.get("is_crouching")):
        _fail("Crouch input did not set player crouching.")
        return
    if camera_pivot.position.y >= standing_camera_y:
        _fail("Crouch did not lower the camera pivot.")
        return
    if capsule.height >= standing_height:
        _fail("Crouch did not reduce the collision capsule height.")
        return

    Input.action_release("crouch")

func _expect_stamina_ui() -> void:
    var stamina_bar := scene.get("stamina_bar") as ProgressBar
    if stamina_bar == null:
        _fail("Blockout stamina bar was not created.")
        return

    player.set("stamina", 42.0)
    player._emit_stamina_if_changed()
    if not is_equal_approx(float(stamina_bar.value), 42.0):
        _fail("Stamina bar did not update from player stamina signal.")

func _expect_local_rain() -> void:
    var effects_root := scene.get_node("EffectsRoot")
    if effects_root.get_node_or_null("LocalRainParticles") == null:
        _fail("Missing local rain particles.")
        return
    if effects_root.get_node_or_null("NearCameraRainStreaks") == null:
        _fail("Missing near-camera rain particles.")
        return
    if effects_root.get_node_or_null("LocalRainSplashHints") == null:
        _fail("Missing local rain splash particles.")

func _release_input() -> void:
    Input.action_release("move_forward")
    Input.action_release("sprint")
    Input.action_release("crouch")

func _fail(message: String) -> void:
    _release_input()
    push_error(message)
    failed = true

func _stop_if_failed() -> bool:
    if failed:
        quit(1)
        return true
    return false
