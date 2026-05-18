extends SceneTree

const SCENE_PATH := "res://scenes/blockout/suburban_horror_blockout.tscn"

var scene: Node
var world_root: Node
var failed := false

func _init() -> void:
    call_deferred("_run")

func _run() -> void:
    scene = load(SCENE_PATH).instantiate()
    root.add_child(scene)
    await process_frame

    world_root = scene.get_node("WorldRoot")
    _print_category("PORCH / APPROACH", ["House_01_FirstEnterable_Porch", "FirstHouse_ClearEntry", "FirstHouse_EntryRamp"])
    _print_category("DOORWAY / ENTRY READ", ["Doorway", "Facade_", "EntryFrame", "OpenDoor"])
    _print_category("WINDOW GLOW", ["House_01_FirstEnterable_LeftWindow", "House_01_FirstEnterable_RightWindow", "WarmLightSpill"])
    _print_category("INTERIOR SLABS", ["FirstHouse_BackWall", "FirstHouse_LeftWall", "FirstHouse_RightWall", "FirstHouse_Ceiling"])
    _print_category("FIRST ROOM OBJECTIVE", ["FirstHouse_InteriorFloor", "FirstHouse_Table", "FirstHouse_Clue", "FirstHouse_Photo"])

    _expect_node_missing("FirstHouse_FrontWall_LeftOfDoor")
    if _stop_if_failed():
        return
    _expect_node_missing("FirstHouse_FrontWall_RightOfDoor")
    if _stop_if_failed():
        return
    _expect_node_missing("House_01_FirstEnterable_DoorwayInset_ShadowBox")
    if _stop_if_failed():
        return
    _expect_node_missing("House_01_FirstEnterable_LeftWindow")
    if _stop_if_failed():
        return
    _expect_node_missing("House_01_FirstEnterable_RightWindow")
    if _stop_if_failed():
        return
    _expect_node_missing("House_01_FirstEnterable_PenanceRelics_DoorPlank")
    if _stop_if_failed():
        return
    _expect_node_missing("FirstHouse_BackWall")
    if _stop_if_failed():
        return
    _expect_node_missing("FirstHouse_LeftWall")
    if _stop_if_failed():
        return
    _expect_node_missing("FirstHouse_RightWall")
    if _stop_if_failed():
        return
    _expect_no_player_height_blockers_in_entry_lane()
    if _stop_if_failed():
        return
    _expect_low_threshold("House_01_FirstEnterable_Porch", 0.26)
    if _stop_if_failed():
        return
    _expect_low_threshold("FirstHouse_EntryRamp_NoStepSnag", 0.28)
    if _stop_if_failed():
        return
    _expect_penance_reveal_one_shot()
    if _stop_if_failed():
        return

    print("FIRST HOUSE ENTRY CHECK PASSED")
    quit(0)

func _print_category(label: String, fragments: Array[String]) -> void:
    print("-- ", label, " --")
    for child in world_root.get_children():
        for fragment in fragments:
            if child.name.contains(fragment):
                print(_describe_node(child))
                break

func _describe_node(node: Node) -> String:
    var node_3d := node as Node3D
    var text := node.name + " type=" + node.get_class()
    if node_3d != null:
        text += " pos=" + str(node_3d.global_position.snapped(Vector3(0.01, 0.01, 0.01)))
        text += " rot=" + str(node_3d.rotation_degrees.snapped(Vector3(0.01, 0.01, 0.01)))

    var mesh_instance := node as MeshInstance3D
    if mesh_instance != null and mesh_instance.mesh is BoxMesh:
        text += " size=" + str((mesh_instance.mesh as BoxMesh).size.snapped(Vector3(0.01, 0.01, 0.01)))
        text += " collision=" + str(mesh_instance.has_meta("collision_node"))

    var body := node as StaticBody3D
    if body != null:
        var shape := _first_collision_shape(body)
        if shape != null and shape.shape is BoxShape3D:
            text += " collider_size=" + str((shape.shape as BoxShape3D).size.snapped(Vector3(0.01, 0.01, 0.01)))
    return text

func _expect_node_missing(node_name: String) -> void:
    if world_root.find_child(node_name, true, false) != null:
        _fail(node_name + " should not exist; it narrows the first-house threshold.")

func _expect_no_player_height_blockers_in_entry_lane() -> void:
    var lane_min := Vector3(23.0, 0.3, 35.4)
    var lane_max := Vector3(25.0, 2.2, 43.0)
    var allowed_fragments: Array[String] = ["Floor", "ClearEntry", "EntryRamp", "Porch"]

    for child in world_root.get_children():
        var body := child as StaticBody3D
        if body == null:
            continue
        if _name_has_any(body.name, allowed_fragments):
            continue

        var shape := _first_collision_shape(body)
        if shape == null or not (shape.shape is BoxShape3D):
            continue

        var size := (shape.shape as BoxShape3D).size
        var half := size * 0.5
        var body_min := body.global_position - half
        var body_max := body.global_position + half
        if _boxes_overlap(body_min, body_max, lane_min, lane_max):
            _fail("Entry lane is blocked at player height by " + body.name + " pos=" + str(body.global_position) + " size=" + str(size))
            return

func _expect_low_threshold(mesh_name: String, max_top_y: float) -> void:
    var mesh := world_root.find_child(mesh_name, true, false) as MeshInstance3D
    if mesh == null or not (mesh.mesh is BoxMesh):
        _fail("Missing threshold mesh " + mesh_name)

    var size := (mesh.mesh as BoxMesh).size
    var top_y := mesh.global_position.y + (size.y * 0.5)
    if top_y > max_top_y:
        _fail(mesh_name + " threshold top is too high: " + str(top_y))

func _expect_penance_reveal_one_shot() -> void:
    scene._trigger_first_house_penance_reveal()
    scene.first_house_penance_timer = 1.23
    scene._trigger_first_house_penance_reveal()
    if not is_equal_approx(scene.first_house_penance_timer, 1.23):
        _fail("First-house Penance reveal replayed instead of staying one-shot.")

func _first_collision_shape(body: StaticBody3D) -> CollisionShape3D:
    for child in body.get_children():
        if child is CollisionShape3D:
            return child
    return null

func _boxes_overlap(a_min: Vector3, a_max: Vector3, b_min: Vector3, b_max: Vector3) -> bool:
    return a_min.x <= b_max.x and a_max.x >= b_min.x \
        and a_min.y <= b_max.y and a_max.y >= b_min.y \
        and a_min.z <= b_max.z and a_max.z >= b_min.z

func _name_has_any(node_name: String, fragments: Array[String]) -> bool:
    for fragment in fragments:
        if node_name.contains(fragment):
            return true
    return false

func _fail(message: String) -> void:
    push_error(message)
    failed = true

func _stop_if_failed() -> bool:
    if failed:
        quit(1)
        return true
    return false
