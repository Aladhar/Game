extends SceneTree

const ROOT_DIRS := [
    "res://scenes",
    "res://scripts",
]

const REQUIRED_MODEL_REFS := {
    "res://scenes/enemies/penance_carrier.tscn": "res://assets/models/enemies/penance_carrier/penance_carrier_end_goal_v21_multi_region_reference_baseline.glb",
    "res://scenes/enemies/bell_saint.tscn": "res://assets/models/enemies/bell_saint/bell_saint_v6h_final_form_pass.glb",
}

const ACTIVE_ENEMY_SCENES := [
    "res://scenes/enemies/penance_carrier.tscn",
    "res://scenes/enemies/bell_saint.tscn",
    "res://scenes/enemies/rain_hunter.tscn",
    "res://scenes/enemies/lantern_bride.tscn",
    "res://scenes/enemies/club_man.tscn",
    "res://scenes/enemies/crooked_scarecrow.tscn",
]

var failed := false

func _init() -> void:
    call_deferred("_run")

func _run() -> void:
    for root_dir in ROOT_DIRS:
        _scan_directory(root_dir)
    _expect_required_model_refs()
    _expect_active_enemy_scenes_load()

    if failed:
        quit(1)
        return

    print("ASSET REFERENCE CHECK PASSED")
    quit(0)

func _scan_directory(path: String) -> void:
    var dir := DirAccess.open(path)
    if dir == null:
        _fail("Could not open asset reference scan directory: " + path)
        return

    dir.list_dir_begin()
    var entry := dir.get_next()
    while entry != "":
        if entry == "." or entry == "..":
            entry = dir.get_next()
            continue

        var child_path := path.path_join(entry)
        if dir.current_is_dir():
            _scan_directory(child_path)
        elif child_path.ends_with(".tscn"):
            _check_scene_file(child_path)

        entry = dir.get_next()
    dir.list_dir_end()

func _check_scene_file(path: String) -> void:
    var file := FileAccess.open(path, FileAccess.READ)
    if file == null:
        _fail("Could not read scene file: " + path)
        return

    var text := file.get_as_text()
    for resource_path in _extract_res_paths(text):
        if not FileAccess.file_exists(resource_path):
            _fail(path + " references missing asset: " + resource_path)

func _extract_res_paths(text: String) -> Array[String]:
    var paths: Array[String] = []
    var marker := "path=\"res://"
    var search_from := 0

    while true:
        var start := text.find(marker, search_from)
        if start == -1:
            break

        var path_start := start + len("path=\"")
        var path_end := text.find("\"", path_start)
        if path_end == -1:
            break

        paths.append(text.substr(path_start, path_end - path_start))
        search_from = path_end + 1

    return paths

func _expect_required_model_refs() -> void:
    for scene_path in REQUIRED_MODEL_REFS.keys():
        var expected_path: String = REQUIRED_MODEL_REFS[scene_path]
        var file := FileAccess.open(scene_path, FileAccess.READ)
        if file == null:
            _fail("Could not read required scene: " + scene_path)
            continue

        var text := file.get_as_text()
        if text.find(expected_path) == -1:
            _fail(scene_path + " does not reference expected model: " + expected_path)

func _expect_active_enemy_scenes_load() -> void:
    for scene_path in ACTIVE_ENEMY_SCENES:
        var packed_scene := load(scene_path) as PackedScene
        if packed_scene == null:
            _fail("Could not load active enemy scene: " + scene_path)
            continue

        var instance := packed_scene.instantiate()
        if instance == null:
            _fail("Could not instantiate active enemy scene: " + scene_path)
            continue

        instance.queue_free()

func _fail(message: String) -> void:
    push_error(message)
    failed = true
