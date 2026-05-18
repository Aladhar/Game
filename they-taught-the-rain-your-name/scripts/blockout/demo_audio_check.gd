extends SceneTree

const SCENE_PATH := "res://scenes/blockout/suburban_horror_blockout.tscn"

var scene: Node
var audio_manager: Node
var scene_bus: Node
var failed := false

func _init() -> void:
    call_deferred("_run")

func _run() -> void:
    scene = load(SCENE_PATH).instantiate()
    root.add_child(scene)
    await process_frame
    await process_frame

    audio_manager = root.get_node_or_null("AudioManager")
    scene_bus = root.get_node_or_null("SceneBus")
    if audio_manager == null:
        _fail("AudioManager autoload was not found.")
    if scene_bus == null:
        _fail("SceneBus autoload was not found.")
    if failed:
        quit(1)
        return

    _expect_storm_bed()
    audio_manager.call("play_thunder", true)
    audio_manager.call("play_ritual_stinger", "audio_check")
    audio_manager.call("play_ui_warning", "audio_check")
    scene_bus.emit_signal("sound_event_recorded", {
        "type": "knock",
        "position": Vector3(0, 1, 0),
        "source": "audio_check"
    })
    scene_bus.emit_signal("rain_imitation_requested", {
        "type": "sprint_step",
        "position": Vector3(0, 1, 0),
        "source": "audio_check"
    })
    await process_frame

    _expect_child(audio_manager, "Thunder")
    _expect_child(audio_manager, "RitualStinger_audio_check")
    _expect_child(audio_manager, "UIWarning")
    _expect_root_descendant("PlayerKnock")
    _expect_root_descendant("RainCopiesStep")

    if failed:
        quit(1)
        return

    print("DEMO AUDIO CHECK PASSED")
    quit(0)

func _expect_storm_bed() -> void:
    var rain_bed_player := audio_manager.get("rain_bed_player") as AudioStreamPlayer
    var wind_bed_player := audio_manager.get("wind_bed_player") as AudioStreamPlayer
    if rain_bed_player == null:
        _fail("Rain bed player was not created.")
        return
    if wind_bed_player == null:
        _fail("Wind bed player was not created.")
        return
    if not rain_bed_player.playing:
        _fail("Rain bed player is not playing.")
    if not wind_bed_player.playing:
        _fail("Wind bed player is not playing.")

func _expect_child(parent: Node, child_name: String) -> void:
    if parent.get_node_or_null(child_name) == null:
        _fail("Missing audio child: " + child_name)

func _expect_root_descendant(child_name: String) -> void:
    if root.find_child(child_name, true, false) == null:
        _fail("Missing root audio one-shot: " + child_name)

func _fail(message: String) -> void:
    push_error(message)
    failed = true
