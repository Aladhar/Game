extends SceneTree

const SCENE_PATH := "res://scenes/blockout/suburban_horror_blockout.tscn"
const DemoDirectorScript := preload("res://scripts/blockout/demo_director.gd")

var scene: Node
var director: DemoDirector
var failed := false

func _init() -> void:
    call_deferred("_run")

func _run() -> void:
    scene = load(SCENE_PATH).instantiate()
    root.add_child(scene)
    await process_frame

    director = scene.get_node("DemoDirector") as DemoDirector
    _expect_groups({
        "before_park": true,
        "before_cul_de_sac": true,
        "before_church": true,
        "before_basement": true,
        "cul_de_sac_funnel": true,
        "church_funnel": true
    })
    if _stop_if_failed():
        return

    director.complete_first_house()
    scene._set_phase(scene.DemoPhase.PARK_LURE)
    _expect_groups({
        "before_park": false,
        "before_cul_de_sac": true,
        "before_church": true,
        "before_basement": true,
        "cul_de_sac_funnel": true,
        "church_funnel": true
    })
    if _stop_if_failed():
        return

    director.advance(DemoDirectorScript.PARK_DONE)
    scene._set_phase(scene.DemoPhase.CUL_DE_SAC)
    _expect_groups({
        "before_park": false,
        "before_cul_de_sac": false,
        "before_church": true,
        "before_basement": true,
        "cul_de_sac_funnel": true,
        "church_funnel": true
    })
    if _stop_if_failed():
        return

    director.advance(DemoDirectorScript.CUL_DE_SAC_DONE)
    scene._set_phase(scene.DemoPhase.CHURCH_UNLOCKED)
    _expect_groups({
        "before_park": false,
        "before_cul_de_sac": false,
        "before_church": false,
        "before_basement": true,
        "cul_de_sac_funnel": false,
        "church_funnel": true
    })
    if _stop_if_failed():
        return

    director.advance(DemoDirectorScript.CHURCH_DONE)
    scene._set_phase(scene.DemoPhase.TUNNEL_PRESSURE)
    _expect_groups({
        "before_park": false,
        "before_cul_de_sac": false,
        "before_church": false,
        "before_basement": true,
        "cul_de_sac_funnel": false,
        "church_funnel": false
    })
    if _stop_if_failed():
        return

    scene.church_notice_inspected = true
    scene._set_phase(scene.DemoPhase.TUNNEL_PRESSURE)
    _expect_groups({
        "before_park": false,
        "before_cul_de_sac": false,
        "before_church": false,
        "before_basement": false,
        "cul_de_sac_funnel": false,
        "church_funnel": false
    })
    if _stop_if_failed():
        return

    print("SOFT ROUTE BLOCKS CHECK PASSED")
    quit(0)

func _expect_groups(expectations: Dictionary) -> void:
    for group_name in expectations.keys():
        var expected_visible := bool(expectations[group_name])
        var blocks: Array = scene.soft_route_blocks.get(group_name, [])
        if blocks.is_empty():
            _fail("Missing soft route group: " + group_name)
            return
        for block in blocks:
            var block_node := block as Node3D
            if block_node == null:
                continue
            if block_node.visible != expected_visible:
                _fail(group_name + " visibility expected " + str(expected_visible) + " for " + block_node.name)
                return

func _fail(message: String) -> void:
    push_error(message)
    failed = true

func _stop_if_failed() -> bool:
    if failed:
        quit(1)
        return true
    return false
