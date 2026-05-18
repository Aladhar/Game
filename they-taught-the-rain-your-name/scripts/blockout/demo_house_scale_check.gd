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
    _expect_first_house_upper_story()
    var house_names := [
        "House_02_BlindWindows",
        "House_03_DoorBoarded",
        "House_04_ClothPorch",
        "House_05_SplitLevel",
        "House_06_TarpedRoof",
        "House_07_BellPorch",
        "House_08_ChainGarage",
        "House_09_PhotoWindows",
        "House_10_DuplicateFacade"
    ]
    for house_name in house_names:
        _expect_non_enterable_house_scale(house_name)

    if failed:
        quit(1)
        return

    print("HOUSE SCALE CHECK PASSED")
    quit(0)

func _expect_first_house_upper_story() -> void:
    _expect_mesh("House_01_FirstEnterable_ReadableExterior_LeftWall", 7.0)
    _expect_mesh("House_01_FirstEnterable_Facade_FirstStory_LeftOfDoor", 4.0)
    _expect_mesh("House_01_FirstEnterable_Facade_FirstStory_RightOfDoor", 4.0)
    _expect_mesh("House_01_FirstEnterable_Facade_DoorHeader_OneCleanLintel", 1.0)
    _expect_mesh("House_01_FirstEnterable_Facade_SecondStory_ContinuousFace", 3.2)
    _expect_mesh("House_01_FirstEnterable_EntryFrame_BuiltInTopHeader", 0.1)
    _expect_mesh("House_01_FirstEnterable_UpperFloor_DarkWindowLeft", 0.8)
    _expect_mesh("House_01_FirstEnterable_UpperFloor_DarkWindowRight", 0.8)
    _expect_mesh("House_01_FirstEnterable_Roof_Blockout", 1.0)

func _expect_non_enterable_house_scale(prefix: String) -> void:
    _expect_mesh(prefix + "_FirstStory_Mass_12x10m", 4.0)
    _expect_mesh(prefix + "_SecondStory_Mass_Blockout", 3.2)
    _expect_mesh(prefix + "_StoryBreak_BoardBand", 0.1)
    _expect_mesh(prefix + "_SecondFloor_LeftWindow", 0.8)
    _expect_mesh(prefix + "_SecondFloor_RightWindow", 0.8)

func _expect_mesh(node_name: String, min_height: float) -> void:
    var node := world_root.get_node_or_null(node_name) as MeshInstance3D
    if node == null:
        _fail("Missing expected house scale node: " + node_name)
        return
    var aabb := node.get_aabb()
    if aabb.size.y < min_height:
        _fail(node_name + " is too short. height=" + str(aabb.size.y))

func _fail(message: String) -> void:
    push_error(message)
    failed = true
