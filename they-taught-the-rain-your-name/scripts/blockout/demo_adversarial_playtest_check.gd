extends SceneTree

const SCENE_PATH := "res://scenes/blockout/suburban_horror_blockout.tscn"
const DemoDirectorScript := preload("res://scripts/blockout/demo_director.gd")

var scene: Node
var player: Node
var director: Node
var failed := false

func _init() -> void:
    call_deferred("_run")

func _run() -> void:
    await _load_fresh_scene()
    _pass_wrong_order_events_do_not_advance()
    if _stop_if_failed():
        return

    await _load_fresh_scene()
    _pass_first_house_objective_cannot_be_skipped()
    if _stop_if_failed():
        return

    await _load_fresh_scene()
    _pass_church_notice_cannot_be_skipped()
    if _stop_if_failed():
        return

    await _load_fresh_scene()
    _pass_backtracking_does_not_replay_or_regress()
    if _stop_if_failed():
        return

    print("ADVERSARIAL PLAYTEST CHECK PASSED")
    quit(0)

func _load_fresh_scene() -> void:
    if scene != null:
        scene.queue_free()
        await process_frame
    scene = load(SCENE_PATH).instantiate()
    root.add_child(scene)
    await process_frame
    player = scene.get_node("Player")
    director = scene.get_node("DemoDirector")

func _pass_wrong_order_events_do_not_advance() -> void:
    print("BREAK PASS: trigger major destination events before their prerequisites.")
    _enter("Event_Park_LightsFlicker")
    _enter("Event_CulDeSac_LightningPenanceAngle")
    _enter("Event_Church_Threshold")
    _enter("Event_Church_BasementEntrance")
    _enter("Event_Tunnel_PressureStarts")
    _enter("Event_TunnelExit_FinalHouseBecomesReachable")
    _enter("Event_FosterHouse_FinalApproach")
    _enter("Event_FirstHouse_HallwayStretch")
    _enter("Event_FirstHouse_DoorAppearsInWall")

    _expect_state(DemoDirectorScript.START, "Wrong-order events advanced the demo state.")
    _expect_bool(scene.final_house_unlocked, false, "Final house unlocked before basement completion.")
    _expect_bool(scene.hallway_stretched, false, "First-house hallway stretched before the photo objective.")
    _expect_bool(scene.door_revealed, false, "Appearing door revealed before the photo objective.")

func _pass_first_house_objective_cannot_be_skipped() -> void:
    print("BREAK PASS: enter first house, ignore the photo, and push deeper into hallway triggers.")
    _enter("Event_FirstHouse_FrontApproach")
    _enter("Event_FirstHouse_Entry")
    _enter("Event_FirstHouse_HallwayStretch")
    _enter("Event_FirstHouse_DoorAppearsInWall")

    _expect_state(DemoDirectorScript.START, "Entering the house without inspecting the photo advanced progression.")
    _expect_bool(director.first_house_entered, true, "First-house entry flag did not set.")
    _expect_bool(scene.hallway_stretched, false, "Hallway stretched before first-house completion.")
    _expect_bool(scene.door_revealed, false, "Appearing door revealed before first-house completion.")

    _inspect_first_house_photo()
    _expect_state(DemoDirectorScript.HOUSE_DONE, "Photo inspection did not complete the first-house objective.")
    _expect_bool(scene.door_revealed, true, "Appearing door did not reveal after first-house completion.")
    _enter("Event_FirstHouse_HallwayStretch")
    _expect_bool(scene.hallway_stretched, true, "Hallway stretch did not fire after first-house completion.")

func _pass_church_notice_cannot_be_skipped() -> void:
    print("BREAK PASS: reach the church and try to enter the basement without inspecting the notice.")
    _complete_route_to_church()
    _enter("Event_Church_BasementEntrance")
    _enter("Event_Tunnel_PressureStarts")
    _expect_state(DemoDirectorScript.CHURCH_DONE, "Basement progressed without the church notice.")
    _expect_bool(scene.church_notice_inspected, false, "Church notice flag set without interaction.")

    _inspect_church_notice()
    _expect_bool(scene.church_notice_inspected, true, "Church notice interaction did not set the gate flag.")
    _enter("Event_Tunnel_PressureStarts")
    _expect_state(DemoDirectorScript.BASEMENT_DONE, "Basement did not progress after inspecting the church notice.")

func _pass_backtracking_does_not_replay_or_regress() -> void:
    print("BREAK PASS: complete the route, then backtrack through old triggers.")
    _complete_route_to_church()
    _inspect_church_notice()
    _enter("Event_Tunnel_PressureStarts")
    _enter("Event_TunnelExit_FinalHouseBecomesReachable")
    _enter("Event_FosterHouse_FinalApproach")
    _expect_state(DemoDirectorScript.DEMO_DONE, "Happy-path route did not reach demo done.")

    var reveal_timer: float = scene.first_house_penance_timer
    _enter("Event_FirstHouse_FrontApproach")
    _enter("Event_FirstHouse_Entry")
    _enter("Event_Park_LightsFlicker")
    _enter("Event_CulDeSac_LightningPenanceAngle")
    _enter("Event_Church_Threshold")
    _expect_state(DemoDirectorScript.DEMO_DONE, "Backtracking regressed the final state.")
    if not is_equal_approx(scene.first_house_penance_timer, reveal_timer):
        _fail("First-house Penance reveal replayed during backtracking.")

func _complete_route_to_church() -> void:
    _enter("Event_FirstHouse_FrontApproach")
    _enter("Event_FirstHouse_Entry")
    _inspect_first_house_photo()
    _enter("Event_Park_LightsFlicker")
    _enter("Event_CulDeSac_LightningPenanceAngle")
    _enter("Event_Church_Threshold")
    _expect_state(DemoDirectorScript.CHURCH_DONE, "Route setup did not reach church.")

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

func _expect_state(expected_state: String, message: String) -> void:
    if director.state != expected_state:
        _fail(message + " expected=" + expected_state + " actual=" + director.state)

func _expect_bool(actual: bool, expected: bool, message: String) -> void:
    if actual != expected:
        _fail(message + " expected=" + str(expected) + " actual=" + str(actual))

func _fail(message: String) -> void:
    push_error(message)
    failed = true

func _stop_if_failed() -> bool:
    if failed:
        quit(1)
        return true
    return false
