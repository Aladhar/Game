extends SceneTree

const SCENE_PATH := "res://scenes/blockout/suburban_horror_blockout.tscn"
const DemoDirectorScript := preload("res://scripts/blockout/demo_director.gd")

var scene: Node
var player: Node
var director: Node

func _init() -> void:
    call_deferred("_run")

func _run() -> void:
    scene = load(SCENE_PATH).instantiate()
    root.add_child(scene)
    await process_frame

    player = scene.get_node("Player")
    director = scene.get_node("DemoDirector")

    _expect(DemoDirectorScript.START)
    _enter("Event_FirstHouse_FrontApproach")
    _expect(DemoDirectorScript.START)
    _expect_flag("first_house_approached", true)
    _expect_flag("first_house_reveal_done", true)
    _enter("Event_Park_LightsFlicker")
    _expect(DemoDirectorScript.START)
    _enter("Event_FirstHouse_Entry")
    _expect_flag("first_house_entered", true)
    _inspect_first_house_photo()
    _expect(DemoDirectorScript.HOUSE_DONE)
    _enter("Event_Park_LightsFlicker")
    _expect(DemoDirectorScript.PARK_DONE)
    _enter("Event_CulDeSac_LightningPenanceAngle")
    _expect(DemoDirectorScript.CUL_DE_SAC_DONE)
    _enter("Event_Church_Threshold")
    _expect(DemoDirectorScript.CHURCH_DONE)
    _inspect_church_notice()
    _enter("Event_Tunnel_PressureStarts")
    _expect(DemoDirectorScript.BASEMENT_DONE)
    _enter("Event_TunnelExit_FinalHouseBecomesReachable")
    _enter("Event_FosterHouse_FinalApproach")
    _expect(DemoDirectorScript.DEMO_DONE)

    print("DEMO SKELETON SMOKE TEST PASSED")
    quit(0)

func _enter(event_name: String) -> void:
    scene._on_event_area_body_entered(player, event_name)

func _inspect_first_house_photo() -> void:
    var area := scene.get_node("EventRoot/Interact_FirstHouse_BlankPhoto")
    scene._on_interactable_body_entered(player, area)
    scene._try_interact()

func _inspect_church_notice() -> void:
    var area := scene.get_node("EventRoot/Interact_Church_InternalHandlingNotice")
    scene._on_interactable_body_entered(player, area)
    scene._try_interact()

func _expect(expected_state: String) -> void:
    if director.state != expected_state:
        push_error("Expected state " + expected_state + " but got " + director.state)
        quit(1)

func _expect_flag(flag_name: String, expected_value: bool) -> void:
    if director.get(flag_name) != expected_value:
        push_error("Expected " + flag_name + "=" + str(expected_value) + " but got " + str(director.get(flag_name)))
        quit(1)
