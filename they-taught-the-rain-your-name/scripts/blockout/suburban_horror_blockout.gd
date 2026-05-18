extends Node3D

const DemoDirectorScript := preload("res://scripts/blockout/demo_director.gd")

enum DemoPhase {
    ARRIVAL,
    FIRST_HOUSE,
    FIRST_HOUSE_CLUE,
    PARK_LURE,
    CUL_DE_SAC,
    CHURCH_UNLOCKED,
    TUNNEL_PRESSURE,
    FOSTER_HOUSE_REVEAL,
    DEMO_COMPLETE
}

@onready var world_environment: WorldEnvironment = $WorldEnvironment
@onready var storm_light: DirectionalLight3D = $StormLight
@onready var debug_visibility_light: DirectionalLight3D = $DebugVisibilityLight
@onready var world_root: Node3D = $WorldRoot
@onready var event_root: Node3D = $EventRoot
@onready var demo_director: DemoDirector = $DemoDirector
@onready var player: Node3D = $Player

@export var debug_visibility_enabled: bool = true

var mat_road: StandardMaterial3D
var mat_sidewalk: StandardMaterial3D
var mat_ground: StandardMaterial3D
var mat_house: StandardMaterial3D
var mat_rotten_wood: StandardMaterial3D
var mat_wet_cloth: StandardMaterial3D
var mat_rusted_metal: StandardMaterial3D
var mat_chain: StandardMaterial3D
var mat_candle: StandardMaterial3D
var mat_photo: StandardMaterial3D
var mat_water: StandardMaterial3D
var mat_dark: StandardMaterial3D
var mat_window: StandardMaterial3D
var mat_dead_window: StandardMaterial3D
var mat_entry_spill: StandardMaterial3D
var mat_concrete: StandardMaterial3D

var flicker_lights: Array[OmniLight3D] = []
var penance_silhouette: Node3D
var final_house_barrier: Node3D
var final_house_road: Node3D
var church_door_blocker: Node3D
var route_gate_to_park: Node3D
var route_gate_to_cul_de_sac: Node3D
var route_gate_to_church: Node3D
var route_gate_to_basement: Node3D
var soft_route_blocks: Dictionary = {}
var appearing_door: Node3D
var false_wall_patch: Node3D
var stretch_hallway_section: Node3D
var first_house_penance: Node3D
var penance_chase_proxy: Node3D
var foster_house_reveal_light: OmniLight3D
var objective_canvas: CanvasLayer
var objective_label: Label
var interact_prompt_label: Label
var inspection_label: Label
var title_card_label: Label
var stamina_bar: ProgressBar
var current_interactable: Area3D
var player_camera: Camera3D
var demo_phase: int = DemoPhase.ARRIVAL
var fired_events: Dictionary = {}
var lightning_timer: float = 0.0
var lightning_cooldown: float = 0.0
var thunder_audio_cooldown: float = 0.0
var first_house_penance_timer: float = 0.0
var inspection_timer: float = 0.0
var default_camera_fov: float = 78.0
var park_lure_pulse_timer: float = 0.0
var tunnel_pressure_timer: float = 0.0
var title_card_timer: float = 0.0
var final_house_unlocked: bool = false
var hallway_stretched: bool = false
var door_revealed: bool = false
var objective_overlay_visible: bool = true
var tunnel_pressure_active: bool = false
var church_notice_inspected: bool = false
var last_safe_player_position: Vector3 = Vector3(0, 1.1, 102)

func _ready() -> void:
    GameState.reset_game()
    Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)
    _ensure_demo_input()
    _make_materials()
    _configure_environment()
    _build_objective_overlay()
    _build_blockout()
    _register_event_areas()
    player_camera = get_tree().get_first_node_in_group("player_camera") as Camera3D
    if player_camera != null:
        default_camera_fov = player_camera.fov
    _connect_player_ui()
    AudioManager.start_demo_storm_bed()
    demo_director.reset()
    _set_phase(DemoPhase.ARRIVAL)

func _input(event: InputEvent) -> void:
    if event.is_action_pressed("toggle_debug_visibility"):
        debug_visibility_enabled = not debug_visibility_enabled
        _configure_environment()
        get_viewport().set_input_as_handled()
    elif event.is_action_pressed("toggle_objective_overlay"):
        objective_overlay_visible = not objective_overlay_visible
        if objective_canvas != null:
            objective_canvas.visible = objective_overlay_visible
        get_viewport().set_input_as_handled()
    elif event.is_action_pressed("advance_demo_phase"):
        _debug_advance_phase()
        get_viewport().set_input_as_handled()
    elif event.is_action_pressed("interact"):
        _try_interact()
        get_viewport().set_input_as_handled()

func _process(delta: float) -> void:
    _update_player_fall_protection()
    _update_flicker_lights(delta)
    _update_lightning(delta)
    _update_demo_timers(delta)
    _update_inspection(delta)
    _update_tunnel_pressure(delta)

func _update_player_fall_protection() -> void:
    if player == null:
        return

    if player.global_position.y > -0.8 and _is_inside_playable_bounds(player.global_position):
        last_safe_player_position = player.global_position
        return

    if player.global_position.y < -8.0 or not _is_inside_playable_bounds(player.global_position):
        player.global_position = _fallback_position_for_current_state()
        if player is CharacterBody3D:
            (player as CharacterBody3D).velocity = Vector3.ZERO
        GameState.show_warning("The rain pushed you back onto the road.")
        AudioManager.play_ui_warning("fall_recovery")

func _is_inside_playable_bounds(pos: Vector3) -> bool:
    return pos.x > -101.5 and pos.x < 73.5 and pos.z > -118.5 and pos.z < 113.5

func _fallback_position_for_current_state() -> Vector3:
    if last_safe_player_position.y > -0.8 and _is_inside_playable_bounds(last_safe_player_position):
        return last_safe_player_position + Vector3(0, 0.35, 0)

    match demo_director.state:
        DemoDirectorScript.START:
            return Vector3(0, 1.1, 86)
        DemoDirectorScript.HOUSE_DONE:
            return Vector3(-12, 1.1, 25)
        DemoDirectorScript.PARK_DONE:
            return Vector3(-64, 1.1, -15)
        DemoDirectorScript.CUL_DE_SAC_DONE:
            return Vector3(42, 1.1, 18)
        DemoDirectorScript.CHURCH_DONE:
            return Vector3(28, 1.1, 3)
        DemoDirectorScript.BASEMENT_DONE:
            return Vector3(0, 1.1, -70)
        _:
            return Vector3(0, 1.1, 86)

func _make_materials() -> void:
    mat_road = _make_mat(Color(0.012, 0.013, 0.016), 0.92, 0.0)
    mat_sidewalk = _make_mat(Color(0.22, 0.23, 0.24), 0.86, 0.0)
    mat_ground = _make_mat(Color(0.018, 0.027, 0.020), 0.94, 0.0)
    mat_house = _make_mat(Color(0.18, 0.19, 0.19), 0.78, 0.0)
    mat_rotten_wood = _make_mat(Color(0.14, 0.095, 0.058), 0.96, 0.0)
    mat_wet_cloth = _make_mat(Color(0.045, 0.055, 0.062), 0.98, 0.0)
    mat_rusted_metal = _make_mat(Color(0.22, 0.095, 0.035), 0.88, 0.45)
    mat_chain = _make_mat(Color(0.11, 0.095, 0.08), 0.72, 0.7)
    mat_photo = _make_mat(Color(0.42, 0.35, 0.25), 0.9, 0.0)
    mat_concrete = _make_mat(Color(0.12, 0.13, 0.13), 0.9, 0.0)
    mat_dark = _make_mat(Color(0.006, 0.007, 0.009), 0.95, 0.0)

    mat_water = _make_mat(Color(0.035, 0.07, 0.09, 0.58), 0.24, 0.0)
    mat_water.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA

    mat_window = StandardMaterial3D.new()
    mat_window.albedo_color = Color(0.55, 0.43, 0.22)
    mat_window.emission_enabled = true
    mat_window.emission = Color(0.95, 0.62, 0.22)
    mat_window.emission_energy_multiplier = 0.32
    mat_window.roughness = 0.45

    mat_dead_window = StandardMaterial3D.new()
    mat_dead_window.albedo_color = Color(0.025, 0.028, 0.03)
    mat_dead_window.roughness = 0.92

    mat_entry_spill = StandardMaterial3D.new()
    mat_entry_spill.albedo_color = Color(0.36, 0.22, 0.10, 0.62)
    mat_entry_spill.emission_enabled = true
    mat_entry_spill.emission = Color(0.85, 0.42, 0.12)
    mat_entry_spill.emission_energy_multiplier = 0.10
    mat_entry_spill.roughness = 0.72
    mat_entry_spill.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA

    mat_candle = StandardMaterial3D.new()
    mat_candle.albedo_color = Color(0.9, 0.72, 0.42)
    mat_candle.emission_enabled = true
    mat_candle.emission = Color(1.0, 0.48, 0.15)
    mat_candle.emission_energy_multiplier = 1.55
    mat_candle.roughness = 0.65

func _make_mat(color: Color, roughness: float, metallic: float) -> StandardMaterial3D:
    var material := StandardMaterial3D.new()
    material.albedo_color = color
    material.roughness = roughness
    material.metallic = metallic
    return material

func _configure_environment() -> void:
    var env := Environment.new()
    env.background_mode = Environment.BG_COLOR
    env.background_color = Color(0.002, 0.004, 0.007)
    env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    env.ambient_light_color = Color(0.17, 0.20, 0.22) if debug_visibility_enabled else Color(0.025, 0.034, 0.042)
    env.ambient_light_energy = 0.9 if debug_visibility_enabled else 0.18
    env.fog_enabled = true
    env.fog_density = 0.018 if debug_visibility_enabled else 0.072
    env.fog_light_color = Color(0.12, 0.16, 0.18)
    env.fog_light_energy = 0.45 if debug_visibility_enabled else 0.18
    env.volumetric_fog_enabled = true
    env.volumetric_fog_density = 0.010 if debug_visibility_enabled else 0.045
    env.volumetric_fog_albedo = Color(0.18, 0.22, 0.24)
    env.glow_enabled = true
    env.glow_intensity = 0.24
    env.glow_strength = 0.55
    world_environment.environment = env

    storm_light.light_energy = 0.45 if debug_visibility_enabled else 0.035
    storm_light.light_color = Color(0.38, 0.48, 0.62)
    debug_visibility_light.visible = debug_visibility_enabled
    debug_visibility_light.light_energy = 0.85 if debug_visibility_enabled else 0.0

func _build_blockout() -> void:
    _build_ground_and_roads()
    _build_world_edge_containment()
    _build_arrival_street()
    _build_neighborhood_houses()
    _build_park()
    _build_cul_de_sac()
    _build_final_house()
    _build_first_house_interior()
    _build_church_community_center()
    _build_storm_drain_tunnels()
    _build_penance_silhouette()
    _build_sightline_fences_and_props()
    _build_temporary_route_blockers()
    _build_soft_progression_blocks()
    _build_demo_critical_path_props()

func _build_ground_and_roads() -> void:
    _add_box("NeighborhoodGround_150m_x_180m", Vector3(0, -0.08, -10), Vector3(150, 0.12, 180), mat_ground, true)

    _add_box("MainLoop_Road_South", Vector3(0, 0.0, 25), Vector3(112, 0.08, 8), mat_road, true)
    _add_box("MainLoop_Road_North", Vector3(0, 0.0, -55), Vector3(112, 0.08, 8), mat_road, true)
    _add_box("MainLoop_Road_West", Vector3(-52, 0.0, -15), Vector3(8, 0.08, 80), mat_road, true)
    _add_box("MainLoop_Road_East", Vector3(52, 0.0, -15), Vector3(8, 0.08, 80), mat_road, true)

    _add_sidewalk_pair("SouthLoopSidewalk", Vector3(0, 0.04, 25), Vector3(114, 0.08, 1.4), true)
    _add_sidewalk_pair("NorthLoopSidewalk", Vector3(0, 0.04, -55), Vector3(114, 0.08, 1.4), true)
    _add_sidewalk_pair("WestLoopSidewalk", Vector3(-52, 0.04, -15), Vector3(1.4, 0.08, 82), false)
    _add_sidewalk_pair("EastLoopSidewalk", Vector3(52, 0.04, -15), Vector3(1.4, 0.08, 82), false)

    _add_box("CentralDrainageDitch", Vector3(0, -0.015, -15), Vector3(5, 0.05, 72), mat_water, false)
    _scatter_puddles([
        Vector3(-12, 0.055, 25), Vector3(17, 0.055, 22), Vector3(48, 0.055, -4),
        Vector3(-51, 0.055, -32), Vector3(9, 0.055, -55), Vector3(-30, 0.055, -55),
        Vector3(3, 0.055, 62), Vector3(-5, 0.055, 82)
    ])

func _build_world_edge_containment() -> void:
    _add_box("WorldBounds_FogWall_North", Vector3(0, 2.6, -119), Vector3(178, 5.2, 2.4), mat_wet_cloth, true)
    _add_box("WorldBounds_FogWall_South", Vector3(0, 2.6, 114), Vector3(178, 5.2, 2.4), mat_wet_cloth, true)
    _add_box("WorldBounds_FogWall_West", Vector3(-102, 2.6, -8), Vector3(2.4, 5.2, 236), mat_wet_cloth, true)
    _add_box("WorldBounds_FogWall_East", Vector3(74, 2.6, -8), Vector3(2.4, 5.2, 236), mat_wet_cloth, true)
    _add_chain_fence("WorldBounds_NorthFence_Readable", Vector3(0, 0.8, -121.6), 130, false)
    _add_chain_fence("WorldBounds_SouthFence_Readable", Vector3(0, 0.8, 116.6), 130, false)
    _add_chain_fence("WorldBounds_WestFence_Readable", Vector3(-104.6, 0.8, -8), 210, true)
    _add_chain_fence("WorldBounds_EastFence_Readable", Vector3(76.6, 0.8, -8), 210, true)
    _add_box("ArrivalBounds_LeftFloodedDitch_NoEscape", Vector3(-13.0, 1.0, 74), Vector3(2.2, 2.0, 83), mat_water, true)
    _add_box("ArrivalBounds_RightFloodedDitch_NoEscape", Vector3(13.0, 1.0, 74), Vector3(2.2, 2.0, 83), mat_water, true)
    _add_box("ArrivalBounds_BackFloodedWash_NoEscape", Vector3(0, 1.0, 111.5), Vector3(32.0, 2.0, 2.4), mat_water, true)
    _add_chain_fence("ArrivalBounds_LeftFence_Readable", Vector3(-12.0, 0.8, 74), 80, true)
    _add_chain_fence("ArrivalBounds_RightFence_Readable", Vector3(12.0, 0.8, 74), 80, true)

func _add_sidewalk_pair(base_name: String, pos: Vector3, size: Vector3, along_x: bool) -> void:
    if along_x:
        _add_box(base_name + "_A", pos + Vector3(0, 0, 5.1), size, mat_sidewalk, true)
        _add_box(base_name + "_B", pos + Vector3(0, 0, -5.1), size, mat_sidewalk, true)
    else:
        _add_box(base_name + "_A", pos + Vector3(5.1, 0, 0), size, mat_sidewalk, true)
        _add_box(base_name + "_B", pos + Vector3(-5.1, 0, 0), size, mat_sidewalk, true)

func _build_arrival_street() -> void:
    _add_box("ArrivalStreet_Road_80m", Vector3(0, 0.0, 69), Vector3(9, 0.08, 84), mat_road, true)
    _add_box("ArrivalStreet_LeftSidewalk", Vector3(-6, 0.04, 69), Vector3(1.4, 0.08, 84), mat_sidewalk, true)
    _add_box("ArrivalStreet_RightSidewalk", Vector3(6, 0.04, 69), Vector3(1.4, 0.08, 84), mat_sidewalk, true)
    _add_box("ArrivalStreet_FogWall_Back", Vector3(0, 2.5, 114), Vector3(34, 5, 1), mat_wet_cloth, false)
    _add_box("ArrivalCar_Abandoned_01", Vector3(-2.2, 0.7, 47), Vector3(2.0, 1.0, 4.4), mat_rusted_metal, true, Vector3(0, 0.22, 0))
    _add_box("ArrivalCar_CavedRoof", Vector3(-2.2, 1.35, 47), Vector3(1.7, 0.35, 3.2), mat_dark, false, Vector3(0, 0.22, 0))
    _add_streetlight("ArrivalStreetLight_01", Vector3(7.2, 0, 91), 0.55)
    _add_streetlight("ArrivalStreetLight_02", Vector3(-7.2, 0, 58), 0.40)
    _add_streetlight("ArrivalStreetLight_03_Failing", Vector3(7.2, 0, 32), 0.25)
    _add_box("Arrival_HouseBeacon_WarmReflectionTrail_A", Vector3(2.0, 0.07, 63), Vector3(1.0, 0.025, 7.5), mat_entry_spill, false, Vector3(0, 0.12, 0))
    _add_box("Arrival_HouseBeacon_WarmReflectionTrail_B", Vector3(4.6, 0.07, 44), Vector3(1.1, 0.025, 9.5), mat_entry_spill, false, Vector3(0, -0.15, 0))
    _add_box("Arrival_HouseBeacon_WarmReflectionTrail_C", Vector3(13.5, 0.075, 31.5), Vector3(1.2, 0.025, 10.0), mat_entry_spill, false, Vector3(0, 1.05, 0))
    _add_box("FirstHouse_FarWarmUpperWindowBeacon", Vector3(24, 5.7, 41.08), Vector3(2.4, 1.3, 0.10), mat_window, false)
    _add_chain_fence("ArrivalRoad_EndlessFence_Left", Vector3(-10.2, 0.65, 75), 36.0, true)
    _add_chain_fence("ArrivalRoad_EndlessFence_Right", Vector3(10.2, 0.65, 75), 36.0, true)

func _build_neighborhood_houses() -> void:
    var houses := [
        {"name": "House_01_FirstEnterable", "pos": Vector3(24, 0, 36), "rot": 0.0, "enterable": true},
        {"name": "House_02_BlindWindows", "pos": Vector3(-24, 0, 36), "rot": 0.0, "enterable": false},
        {"name": "House_03_DoorBoarded", "pos": Vector3(64, 0, 9), "rot": -1.5708, "enterable": false},
        {"name": "House_04_ClothPorch", "pos": Vector3(64, 0, -26), "rot": -1.5708, "enterable": false},
        {"name": "House_05_SplitLevel", "pos": Vector3(31, 0, -67), "rot": 3.14159, "enterable": false},
        {"name": "House_06_TarpedRoof", "pos": Vector3(-8, 0, -68), "rot": 3.14159, "enterable": false},
        {"name": "House_07_BellPorch", "pos": Vector3(-39, 0, -68), "rot": 3.14159, "enterable": false},
        {"name": "House_08_ChainGarage", "pos": Vector3(-65, 0, -33), "rot": 1.5708, "enterable": false},
        {"name": "House_09_PhotoWindows", "pos": Vector3(-65, 0, 8), "rot": 1.5708, "enterable": false},
        {"name": "House_10_DuplicateFacade", "pos": Vector3(-27, 0, 13), "rot": -0.05, "enterable": false}
    ]

    for data in houses:
        _build_house_blockout(
            String(data["name"]),
            data["pos"],
            float(data["rot"]),
            bool(data["enterable"])
        )

func _build_house_blockout(house_name: String, pos: Vector3, rot_y: float, enterable: bool) -> void:
    var rot := Vector3(0, rot_y, 0)
    var house_mat := mat_rotten_wood if house_name.contains("Door") or house_name.contains("Bell") else mat_house
    var house_width := 12.0
    var house_depth := 9.6
    var first_story_height := 4.7
    var second_story_height := 3.9
    var front_z := 4.82
    var rear_z := -4.75
    var door_width := 3.6
    var door_height := 3.25
    if not enterable:
        _add_box(house_name + "_FirstStory_Mass_12x10m", pos + Vector3(0, first_story_height * 0.5, 0), Vector3(house_width, first_story_height, house_depth), house_mat, true, rot)
        _add_box(house_name + "_SecondStory_Mass_Blockout", pos + Vector3(0, first_story_height + second_story_height * 0.5, -0.25), Vector3(10.7, second_story_height, 8.4), house_mat, true, rot)
        _add_box(house_name + "_StoryBreak_BoardBand", pos + Vector3(0, first_story_height + 0.02, 4.95), Vector3(12.4, 0.22, 0.18), mat_rotten_wood, false, rot)
    else:
        var full_height := first_story_height + second_story_height
        var lower_side_width := (house_width - door_width) * 0.5
        var header_height := first_story_height - door_height
        _add_box(house_name + "_ReadableExterior_LeftWall", pos + Vector3(-5.85, full_height * 0.5, 0), Vector3(0.32, full_height, house_depth), house_mat, true, rot)
        _add_box(house_name + "_ReadableExterior_RightWall", pos + Vector3(5.85, full_height * 0.5, 0), Vector3(0.32, full_height, house_depth), house_mat, true, rot)
        _add_box(house_name + "_ReadableExterior_BackWall", pos + Vector3(0, full_height * 0.5, rear_z), Vector3(house_width, full_height, 0.32), house_mat, true, rot)
        _add_box(house_name + "_Facade_FirstStory_LeftOfDoor", pos + Vector3(-(door_width * 0.5 + lower_side_width * 0.5), first_story_height * 0.5, front_z), Vector3(lower_side_width, first_story_height, 0.32), house_mat, true, rot)
        _add_box(house_name + "_Facade_FirstStory_RightOfDoor", pos + Vector3(door_width * 0.5 + lower_side_width * 0.5, first_story_height * 0.5, front_z), Vector3(lower_side_width, first_story_height, 0.32), house_mat, true, rot)
        _add_box(house_name + "_Facade_DoorHeader_OneCleanLintel", pos + Vector3(0, door_height + header_height * 0.5, front_z), Vector3(door_width + 0.62, header_height, 0.34), house_mat, true, rot)
        _add_box(house_name + "_Facade_SecondStory_ContinuousFace", pos + Vector3(0, first_story_height + second_story_height * 0.5, front_z), Vector3(house_width, second_story_height, 0.32), house_mat, true, rot)
        _add_box(house_name + "_Facade_StoryBreak_SingleTrim", pos + Vector3(0, first_story_height + 0.02, 5.02), Vector3(12.2, 0.20, 0.14), mat_rotten_wood, false, rot)
        _add_box(house_name + "_UpperFloor_DarkWindowLeft", pos + Vector3(-3.25, 6.25, 5.02), Vector3(1.25, 1.0, 0.08), mat_dead_window, false, rot)
        _add_box(house_name + "_UpperFloor_DarkWindowRight", pos + Vector3(3.25, 6.25, 5.02), Vector3(1.25, 1.0, 0.08), mat_dead_window, false, rot)
        _add_box(house_name + "_EntryFrame_BuiltInLeftJamb", pos + Vector3(-(door_width * 0.5 + 0.08), door_height * 0.5, 5.03), Vector3(0.18, door_height, 0.18), mat_rotten_wood, false, rot)
        _add_box(house_name + "_EntryFrame_BuiltInRightJamb", pos + Vector3(door_width * 0.5 + 0.08, door_height * 0.5, 5.03), Vector3(0.18, door_height, 0.18), mat_rotten_wood, false, rot)
        _add_box(house_name + "_EntryFrame_BuiltInTopHeader", pos + Vector3(0, door_height + 0.08, 5.03), Vector3(door_width + 0.5, 0.18, 0.18), mat_rotten_wood, false, rot)
    var roof_size := Vector3(13.7, 1.35, 11.8) if enterable else Vector3(12.2, 1.35, 9.8)
    var roof_pos := pos + (Vector3(0, 8.35, 0.45) if enterable else Vector3(0, 8.65, -0.25))
    _add_box(house_name + "_Roof_Blockout", roof_pos, roof_size, mat_dark, true, rot)
    if enterable:
        _add_box(house_name + "_FrontRoofOverhang_CleanRead", pos + Vector3(0, 4.95, 5.72), Vector3(12.8, 0.28, 1.35), mat_dark, true, rot)
    var porch_center_y := 0.13 if enterable else 0.35
    var porch_height := 0.14 if enterable else 0.55
    _add_box(house_name + "_Porch", pos + _rotated(Vector3(0, porch_center_y, 5.35), rot_y), Vector3(7.2, porch_height, 2.3), mat_rotten_wood, true, rot)
    if enterable:
        _add_box(house_name + "_OpenDoor_ParkedLeft", pos + _rotated(Vector3(-1.55, 1.45, 5.18), rot_y), Vector3(0.17, 2.75, 1.15), mat_rotten_wood, false, Vector3(0, rot_y - 0.92, 0))
    else:
        _add_box(house_name + "_Door_Motif", pos + _rotated(Vector3(0, 1.3, 5.96), rot_y), Vector3(1.2, 2.4, 0.16), mat_rotten_wood, false, rot)
    if not enterable:
        _add_box(house_name + "_GroundFloor_LeftWindow", pos + _rotated(Vector3(-3.1, 2.45, 5.82), rot_y), Vector3(1.55, 1.05, 0.12), mat_dead_window, false, rot)
        _add_box(house_name + "_GroundFloor_RightWindow", pos + _rotated(Vector3(3.15, 2.45, 5.82), rot_y), Vector3(1.55, 1.05, 0.12), mat_dead_window, false, rot)
        _add_box(house_name + "_SecondFloor_LeftWindow", pos + _rotated(Vector3(-2.8, 6.6, 5.12), rot_y), Vector3(1.45, 1.0, 0.12), mat_dead_window, false, rot)
        _add_box(house_name + "_SecondFloor_RightWindow", pos + _rotated(Vector3(2.8, 6.6, 5.12), rot_y), Vector3(1.45, 1.0, 0.12), mat_dead_window, false, rot)
    if not enterable:
        _add_relic_cluster(house_name + "_PenanceRelics", pos + _rotated(Vector3(-4.2, 1.5, 5.9), rot_y), rot_y)

func _build_park() -> void:
    _add_box("SmallPark_WetGrass_ClearSightline", Vector3(-21, 0.01, -11), Vector3(31, 0.07, 28), mat_ground, true)
    _add_box("ParkLoop_Path_NorthSouth", Vector3(-21, 0.07, -11), Vector3(3.0, 0.08, 28), mat_sidewalk, true)
    _add_box("ParkLoop_Path_EastWest", Vector3(-21, 0.08, -11), Vector3(31, 0.08, 3.0), mat_sidewalk, true)
    _add_box("Park_Playset_Blockout", Vector3(-28, 1.0, -18), Vector3(4.2, 2.0, 2.8), mat_rusted_metal, true)
    _add_box("Park_SwingBar", Vector3(-13, 2.25, -5), Vector3(5.8, 0.18, 0.18), mat_chain, false)
    _add_chain_pair("Park_SwingChains_A", Vector3(-15, 1.25, -5), 1.9)
    _add_chain_pair("Park_SwingChains_B", Vector3(-11, 1.25, -5), 1.9)
    _add_box("Park_Bench_RottenWood", Vector3(-29, 0.65, -3), Vector3(3.4, 0.38, 0.8), mat_rotten_wood, true, Vector3(0, 0.45, 0))
    _add_tree_cluster("Park_Trees", [Vector3(-34, 0, -20), Vector3(-36, 0, -7), Vector3(-21, 0, -26), Vector3(-9, 0, -21)])
    _add_streetlight("Park_OneWeakLamp", Vector3(-9, 0, -1), 0.22)
    _add_box("Park_StormDrain_EntryLip", Vector3(-34, 0.25, -12), Vector3(3.8, 0.5, 2.0), mat_rusted_metal, true)
    _add_box("Park_StormDrain_BlackOpening", Vector3(-34, 0.7, -13.1), Vector3(3.2, 1.1, 0.18), mat_dark, false)
    _add_box("Park_Lure_WarmPuddleTrail_FromRoad", Vector3(-20, 0.075, 5.0), Vector3(1.1, 0.025, 13.0), mat_entry_spill, false, Vector3(0, 0.1, 0))
    _add_box("Park_Lure_DrainFocus_WetCircle", Vector3(-33.6, 0.08, -11.8), Vector3(6.4, 0.03, 5.2), mat_water, false)
    _add_box("Park_Lure_LeaningLampPointsAtDrain_Pole", Vector3(-31.0, 1.45, -8.8), Vector3(0.16, 2.9, 0.16), mat_rusted_metal, true, Vector3(0.0, 0.0, deg_to_rad(-12.0)))
    _add_box("Park_Lure_LeaningLampPointsAtDrain_Head", Vector3(-32.1, 2.85, -10.4), Vector3(0.85, 0.22, 0.55), mat_rusted_metal, false, Vector3(0.0, -0.55, deg_to_rad(-12.0)))
    var drain_lure_light := SpotLight3D.new()
    drain_lure_light.name = "Park_Lure_DrainFocus_SickAmberSpot"
    drain_lure_light.position = Vector3(-30.9, 3.0, -8.8)
    drain_lure_light.rotation_degrees = Vector3(-62.0, -35.0, 0.0)
    drain_lure_light.light_color = Color(1.0, 0.52, 0.18)
    drain_lure_light.light_energy = 3.0
    drain_lure_light.spot_range = 10.0
    drain_lure_light.spot_angle = 24.0
    drain_lure_light.shadow_enabled = true
    world_root.add_child(drain_lure_light)

func _build_cul_de_sac() -> void:
    _add_box("CulDeSac_ConnectorRoad", Vector3(-68, 0.0, -15), Vector3(28, 0.08, 8), mat_road, true)
    _add_cylinder("CulDeSac_RoadCircle_32m", Vector3(-86, 0.0, -15), 16.0, 0.08, mat_road, true)
    _add_box("CulDeSac_CenterIsland", Vector3(-86, 0.08, -15), Vector3(10.5, 0.12, 10.5), mat_ground, true)
    _add_tree_cluster("CulDeSac_DeadTrees", [Vector3(-88, 0, -18), Vector3(-83, 0, -12), Vector3(-90, 0, -10)])
    _add_streetlight("CulDeSac_FlickerLamp_A", Vector3(-75, 0, -25), 0.18)
    _add_streetlight("CulDeSac_FlickerLamp_B", Vector3(-96, 0, -5), 0.12)
    _add_box("CulDeSac_AbandonedCar", Vector3(-94, 0.7, -21), Vector3(2.1, 1.0, 4.2), mat_rusted_metal, true, Vector3(0, -0.8, 0))

func _build_final_house() -> void:
    _add_box("FinalHouse_Unreachable_RoadStub_Locked", Vector3(0, 0.01, -78), Vector3(8, 0.08, 38), mat_road, true)
    final_house_road = _add_box("FinalHouse_RoadExtension_AppearsLater", Vector3(0, 0.02, -96), Vector3(8, 0.08, 24), mat_road, true)
    final_house_road.visible = false
    _set_mesh_collision_enabled(final_house_road, false)
    final_house_barrier = _add_box("FinalHouse_RustedGate_BlocksEarlyRoute", Vector3(0, 1.5, -76), Vector3(13, 3.0, 0.5), mat_rusted_metal, true)
    _add_box("FinalHouse_SilhouetteMass_VisibleFromLoop", Vector3(0, 4.0, -116), Vector3(18, 8.0, 13), mat_dark, true)
    _add_box("FinalHouse_SteepleLikeChimney", Vector3(4.5, 9.5, -116), Vector3(2.4, 6.0, 2.4), mat_dark, true)
    _add_box("FinalHouse_DoorMaskFacade", Vector3(0, 2.7, -108.85), Vector3(3.2, 5.0, 0.22), mat_rotten_wood, false)
    _add_box("FinalHouse_OnlyLitWindow_Left", Vector3(-5.2, 3.3, -108.75), Vector3(2.1, 1.3, 0.14), mat_window, false)
    _add_box("FinalHouse_OnlyLitWindow_Right", Vector3(5.2, 3.3, -108.75), Vector3(2.1, 1.3, 0.14), mat_window, false)
    _add_chain_fence("FinalHouse_PerimeterFence_Left", Vector3(-10, 0.8, -95), 38, true)
    _add_chain_fence("FinalHouse_PerimeterFence_Right", Vector3(10, 0.8, -95), 38, true)

func _build_first_house_interior() -> void:
    var p := Vector3(24, 0, 36)
    _add_box("FirstHouse_InteriorFloor", p + Vector3(0, 0.08, 0), Vector3(11.3, 0.12, 8.8), mat_concrete, true)
    _add_box("FirstHouse_CeilingLowPressure", p + Vector3(0, 3.58, 0), Vector3(11.6, 0.18, 9.0), mat_dark, false)

    _add_box("FirstHouse_LivingRoom_BlockoutSofa", p + Vector3(-2.2, 0.55, -1.4), Vector3(3.2, 0.8, 1.0), mat_wet_cloth, true)
    _add_box("FirstHouse_Table_Candles", p + Vector3(1.75, 0.55, 0.65), Vector3(1.4, 0.35, 1.0), mat_rotten_wood, true)
    _add_candle_group("FirstHouse_CandleCluster", p + Vector3(1.75, 0.9, 0.65))
    _add_photo_wall("FirstHouse_OldPhotosWall", p + Vector3(-5.55, 2.05, -1.2), 1.5708)

    _add_box("FirstHouse_Hallway_Floor", p + Vector3(0, 0.11, -8.6), Vector3(2.6, 0.12, 10.0), mat_concrete, true)
    _add_box("FirstHouse_Hallway_LeftWall", p + Vector3(-1.45, 1.45, -8.6), Vector3(0.28, 2.9, 10.0), mat_house, true)
    _add_box("FirstHouse_Hallway_RightWall", p + Vector3(1.45, 1.45, -8.6), Vector3(0.28, 2.9, 10.0), mat_house, true)
    stretch_hallway_section = _add_box("FirstHouse_Hallway_StretchableEnd", p + Vector3(0, 1.5, -14.2), Vector3(2.8, 3.0, 2.4), mat_dark, true)
    false_wall_patch = _add_box("FirstHouse_FalseWall_BecomesDoor", p + Vector3(1.31, 1.45, -7.2), Vector3(0.18, 2.9, 1.8), mat_house, false)
    appearing_door = _add_box("FirstHouse_NewDoor_AppearsWhereWallWas", p + Vector3(1.18, 1.4, -7.2), Vector3(0.18, 2.45, 1.2), mat_rotten_wood, false)
    appearing_door.visible = false
    _add_chain_pair("FirstHouse_Hallway_HangingChains", p + Vector3(0, 2.0, -5.2), 1.6)

func _build_church_community_center() -> void:
    var p := Vector3(34, 0, 4)
    _add_box("CommunityChurch_MainHall_14x18m", p + Vector3(0, 3.0, 0), Vector3(14, 6, 18), mat_concrete, true)
    _add_box("CommunityChurch_RoofSlab", p + Vector3(0, 6.4, 0), Vector3(15, 1.0, 19), mat_dark, true)
    _add_box("CommunityChurch_BellTower", p + Vector3(0, 8.5, -7.0), Vector3(4.0, 9.0, 4.0), mat_dark, true)
    _add_cylinder("CommunityChurch_BlockoutBell", p + Vector3(0, 12.8, -7), 1.1, 1.3, mat_rusted_metal, false)
    _add_box("CommunityChurch_Doors", p + Vector3(0, 1.6, 9.15), Vector3(3.2, 3.2, 0.2), mat_rotten_wood, false)
    _add_box("CommunityChurch_BasementDoor", p + Vector3(-6.8, 1.2, -4.0), Vector3(0.2, 2.4, 2.2), mat_rotten_wood, false)
    _add_photo_wall("CommunityChurch_NoticeBoard_Photos", p + Vector3(0, 2.2, 9.3), 0.0)
    _add_candle_group("CommunityChurch_CandlesAtThreshold", p + Vector3(0, 0.55, 7.7))
    _add_streetlight("CommunityChurch_Streetlight", p + Vector3(-9, 0, 9), 0.36)

func _build_storm_drain_tunnels() -> void:
    var y := -4.0
    _add_box("Tunnel_ChasePath_Floor_A", Vector3(-34, y, -24), Vector3(5.0, 0.18, 28), mat_concrete, true)
    _add_box("Tunnel_ChasePath_LeftWall_A", Vector3(-36.6, y + 1.45, -24), Vector3(0.28, 2.9, 28), mat_concrete, true)
    _add_box("Tunnel_ChasePath_RightWall_A", Vector3(-31.4, y + 1.45, -24), Vector3(0.28, 2.9, 28), mat_concrete, true)
    _add_box("Tunnel_ChasePath_Ceiling_A", Vector3(-34, y + 3.0, -24), Vector3(5.0, 0.18, 28), mat_dark, false)

    _add_box("Tunnel_ChasePath_Floor_B", Vector3(-17, y, -38), Vector3(39, 0.18, 5.0), mat_concrete, true)
    _add_box("Tunnel_ChasePath_NorthWall_B", Vector3(-17, y + 1.45, -40.6), Vector3(39, 2.9, 0.28), mat_concrete, true)
    _add_box("Tunnel_ChasePath_SouthWall_B", Vector3(-17, y + 1.45, -35.4), Vector3(39, 2.9, 0.28), mat_concrete, true)
    _add_box("Tunnel_ChasePath_Ceiling_B", Vector3(-17, y + 3.0, -38), Vector3(39, 0.18, 5.0), mat_dark, false)

    _add_box("Tunnel_ChasePath_Floor_C_ToFinal", Vector3(5, y, -63), Vector3(5, 0.18, 45), mat_concrete, true)
    _add_box("Tunnel_ChasePath_LeftWall_C", Vector3(2.4, y + 1.45, -63), Vector3(0.28, 2.9, 45), mat_concrete, true)
    _add_box("Tunnel_ChasePath_RightWall_C", Vector3(7.6, y + 1.45, -63), Vector3(0.28, 2.9, 45), mat_concrete, true)
    _add_box("Tunnel_ChasePath_Ceiling_C", Vector3(5, y + 3.0, -63), Vector3(5, 0.18, 45), mat_dark, false)

    _add_box("Tunnel_WaterChannel", Vector3(-17, y + 0.1, -38), Vector3(36, 0.05, 1.2), mat_water, false)
    _add_box("Tunnel_RustedPipe_A", Vector3(-34, y + 2.3, -24), Vector3(0.45, 0.45, 27), mat_rusted_metal, false)
    _add_box("Tunnel_RustedPipe_B", Vector3(-17, y + 2.2, -38), Vector3(38, 0.4, 0.4), mat_rusted_metal, false)
    _add_candle_group("Tunnel_CandleWarningCluster", Vector3(5, y + 0.5, -82))
    _add_box("Tunnel_ExitLadder_ToFinalHouseRoad", Vector3(5, y + 2.8, -86), Vector3(1.0, 5.5, 0.25), mat_rusted_metal, false)

func _build_penance_silhouette() -> void:
    penance_silhouette = Node3D.new()
    penance_silhouette.name = "Penance_FarLightningSilhouette_Blockout"
    penance_silhouette.position = Vector3(4, 0, -88)
    penance_silhouette.visible = false
    world_root.add_child(penance_silhouette)

    _add_box("Penance_HoodedWetCloth_4mTall", Vector3(0, 2.15, 0), Vector3(1.7, 4.3, 0.85), mat_wet_cloth, false, Vector3.ZERO, penance_silhouette)
    _add_box("Penance_CrushedDoorMask", Vector3(0, 4.25, -0.48), Vector3(1.15, 1.55, 0.18), mat_rotten_wood, false, Vector3(0, 0.08, 0), penance_silhouette)
    _add_chain_pair("Penance_RustedChains", Vector3(0, 2.9, -0.6), 2.2, penance_silhouette)
    _add_candle_group("Penance_CandleRelics", Vector3(0, 1.25, -0.7), penance_silhouette)
    _add_box("Penance_BackDoorPlank", Vector3(0, 2.4, 0.55), Vector3(1.35, 3.1, 0.2), mat_rotten_wood, false, Vector3.ZERO, penance_silhouette)

func _build_sightline_fences_and_props() -> void:
    _add_chain_fence("NorthLoop_SightlineFence_Left", Vector3(-21, 0.8, -67), 30, false)
    _add_chain_fence("NorthLoop_SightlineFence_Right", Vector3(21, 0.8, -67), 30, false)
    _add_streetlight("NorthLoop_Backlight_FinalHouse", Vector3(-12, 0, -62), 0.28)
    _add_streetlight("EastLoop_Backlight_Church", Vector3(46, 0, 19), 0.31)
    _add_streetlight("WestLoop_ParkBacklight", Vector3(-46, 0, -3), 0.24)

    _add_relic_cluster("Roadside_RottenDoorShrine_A", Vector3(12, 0.9, -55), 3.14159)
    _add_relic_cluster("Roadside_RottenDoorShrine_B", Vector3(-52, 0.9, 8), 1.5708)
    _add_relic_cluster("CulDeSac_RottenDoorShrine_C", Vector3(-86, 0.9, -26), 0.0)
    _add_tree_cluster("Loop_BackgroundTrees", [
        Vector3(70, 0, -48), Vector3(70, 0, 27), Vector3(-73, 0, 31),
        Vector3(20, 0, -83), Vector3(-17, 0, -84), Vector3(38, 0, 48)
    ])

func _build_demo_critical_path_props() -> void:
    _build_first_house_readability_pass()
    _build_first_house_penance_reveal()
    _build_demo_clues_and_interactables()
    _build_church_lock_state()
    _build_tunnel_pressure_proxy()
    _build_foster_house_reveal_props()

func _build_first_house_readability_pass() -> void:
    var p := Vector3(24, 0, 36)

    _add_box("FirstHouse_ClearEntry_WetPath_FromRoad", p + Vector3(0, 0.09, 9.2), Vector3(4.2, 0.08, 6.6), mat_sidewalk, true)
    _add_box("FirstHouse_EntryRamp_NoStepSnag", p + Vector3(0, 0.12, 6.0), Vector3(3.8, 0.10, 3.2), mat_sidewalk, true, Vector3(deg_to_rad(-2.5), 0, 0))
    _add_box("FirstHouse_Doorway_WarmLightSpill", p + Vector3(0, 0.125, 4.35), Vector3(2.2, 0.025, 1.2), mat_entry_spill, false)

    var entry_light := OmniLight3D.new()
    entry_light.name = "FirstHouse_RealInteriorPointLight"
    entry_light.position = p + Vector3(0.25, 2.15, 1.35)
    entry_light.light_color = Color(1.0, 0.58, 0.24)
    entry_light.light_energy = 4.6
    entry_light.omni_range = 8.0
    entry_light.shadow_enabled = true
    world_root.add_child(entry_light)

    var doorway_shadow := OmniLight3D.new()
    doorway_shadow.name = "FirstHouse_DimDoorwayTransitionLight"
    doorway_shadow.position = p + Vector3(0, 1.4, 3.95)
    doorway_shadow.light_color = Color(0.55, 0.27, 0.12)
    doorway_shadow.light_energy = 0.35
    doorway_shadow.omni_range = 2.2
    world_root.add_child(doorway_shadow)

    var table_light := SpotLight3D.new()
    table_light.name = "FirstHouse_TablePhotoFocusSpot"
    table_light.position = p + Vector3(1.55, 2.7, 1.15)
    table_light.rotation_degrees = Vector3(-70, 2, 0)
    table_light.light_color = Color(1.0, 0.72, 0.38)
    table_light.light_energy = 2.0
    table_light.spot_range = 5.0
    table_light.spot_angle = 28.0
    table_light.shadow_enabled = true
    world_root.add_child(table_light)

    _add_box("FirstHouse_TableFocus_ChairSilhouette", p + Vector3(3.1, 0.65, 0.8), Vector3(0.7, 1.0, 0.7), mat_rotten_wood, true, Vector3(0, -0.3, 0))
    _add_box("FirstHouse_TableLamp_Base", p + Vector3(1.05, 1.0, 0.88), Vector3(0.18, 0.55, 0.18), mat_rusted_metal, false)
    _add_box("FirstHouse_TableLamp_Shade", p + Vector3(1.05, 1.42, 0.88), Vector3(0.62, 0.38, 0.62), mat_window, false)

func _build_temporary_route_blockers() -> void:
    route_gate_to_park = _add_box("RouteGate_ToPark_BlockedUntilHouse", Vector3(-6, 1.55, 25), Vector3(22, 3.1, 1.0), mat_wet_cloth, true)
    route_gate_to_cul_de_sac = _add_box("RouteGate_ToCulDeSac_BlockedUntilPark", Vector3(-61, 1.55, -15), Vector3(1.0, 3.1, 11), mat_wet_cloth, true)
    route_gate_to_church = _add_box("RouteGate_ToChurch_BlockedUntilCulDeSac", Vector3(45, 1.55, 15), Vector3(1.0, 3.1, 18), mat_wet_cloth, true)
    route_gate_to_basement = _add_box("RouteGate_ToBasement_BlockedUntilChurch", Vector3(27.2, 1.55, 0), Vector3(1.0, 3.1, 5), mat_wet_cloth, true)

func _build_soft_progression_blocks() -> void:
    _add_soft_route_block(
        "before_park",
        "SoftBlock_ToPark_StormSheetUntilPhoto",
        Vector3(-6, 1.25, 26.7),
        Vector3(19.0, 2.5, 0.55)
    )
    _add_soft_route_block(
        "before_cul_de_sac",
        "SoftBlock_ToCulDeSac_FloodedConnectorUntilPark",
        Vector3(-60.2, 1.25, -15),
        Vector3(1.2, 2.5, 24.0)
    )
    _add_soft_route_block(
        "before_church",
        "SoftBlock_EastLoop_FloodedStreetUntilCulDeSac",
        Vector3(39.0, 1.25, 25),
        Vector3(24.0, 2.5, 0.65)
    )
    _add_soft_route_block(
        "before_church",
        "SoftBlock_ToChurch_ClothWallUntilCulDeSac",
        Vector3(44.0, 1.25, 15),
        Vector3(0.65, 2.5, 16.0)
    )
    _add_soft_route_block(
        "before_basement",
        "SoftBlock_ToBasement_ChainedStairUntilChurch",
        Vector3(27.2, 1.25, 0),
        Vector3(0.65, 2.5, 4.4)
    )

    _add_soft_route_block(
        "cul_de_sac_funnel",
        "SoftFunnel_WestLoop_NorthWrongWay",
        Vector3(-52, 1.25, -36),
        Vector3(42.0, 2.5, 20.0)
    )
    _add_soft_route_block(
        "cul_de_sac_funnel",
        "SoftFunnel_WestLoop_SouthWrongWay",
        Vector3(-52, 1.25, 7),
        Vector3(42.0, 2.5, 20.0)
    )
    _add_soft_route_block(
        "cul_de_sac_funnel",
        "SoftFunnel_CulDeSac_NorthLawnNoBypass",
        Vector3(-80, 1.25, -33),
        Vector3(32.0, 2.5, 12.0)
    )
    _add_soft_route_block(
        "cul_de_sac_funnel",
        "SoftFunnel_CulDeSac_SouthLawnNoBypass",
        Vector3(-80, 1.25, 3),
        Vector3(32.0, 2.5, 12.0)
    )
    _add_soft_route_block(
        "church_funnel",
        "SoftFunnel_EastLoop_NorthWrongWay",
        Vector3(52, 1.25, -21),
        Vector3(7.2, 2.5, 18.0)
    )
    _add_soft_route_block(
        "church_funnel",
        "SoftFunnel_EastLoop_SouthWrongWay",
        Vector3(52, 1.25, 31),
        Vector3(7.2, 2.5, 14.0)
    )

func _add_soft_route_block(group_name: String, block_name: String, pos: Vector3, size: Vector3) -> void:
    if not soft_route_blocks.has(group_name):
        soft_route_blocks[group_name] = []

    var block := _add_box(block_name, pos, size, mat_wet_cloth, true)
    soft_route_blocks[group_name].append(block)

    var rail_size := Vector3(size.x, 0.08, 0.08)
    if size.z > size.x:
        rail_size = Vector3(0.08, 0.08, size.z)
    soft_route_blocks[group_name].append(_add_box(block_name + "_SaggingChainTop", pos + Vector3(0, size.y * 0.46, 0), rail_size, mat_chain, false))
    soft_route_blocks[group_name].append(_add_box(block_name + "_WaterAtBase", Vector3(pos.x, 0.055, pos.z), Vector3(max(size.x, 1.8), 0.035, max(size.z, 1.8)), mat_water, false))
    soft_route_blocks[group_name].append(_add_box(block_name + "_CandleMarker", Vector3(pos.x, 0.34, pos.z), Vector3(0.18, 0.42, 0.18), mat_candle, false))

    var marker_light := OmniLight3D.new()
    marker_light.name = block_name + "_CandleMarkerLight"
    marker_light.position = Vector3(pos.x, 0.75, pos.z)
    marker_light.light_color = Color(1.0, 0.42, 0.14)
    marker_light.light_energy = 0.12
    marker_light.omni_range = 2.8
    world_root.add_child(marker_light)
    soft_route_blocks[group_name].append(marker_light)

func _build_first_house_penance_reveal() -> void:
    first_house_penance = Node3D.new()
    first_house_penance.name = "Penance_FirstLitHouse_DoorwaySilhouette"
    first_house_penance.position = Vector3(24.0, 0.0, 37.55)
    first_house_penance.rotation.y = deg_to_rad(180.0)
    first_house_penance.visible = false
    world_root.add_child(first_house_penance)

    _add_box("FirstHousePenance_WetClothBody", Vector3(0, 2.05, 0), Vector3(1.35, 4.1, 0.65), mat_wet_cloth, false, Vector3.ZERO, first_house_penance)
    _add_box("FirstHousePenance_DoorMask_ReadSecond", Vector3(0, 4.05, -0.38), Vector3(0.95, 1.35, 0.16), mat_rotten_wood, false, Vector3(0, 0.1, 0), first_house_penance)
    _add_chain_pair("FirstHousePenance_BarelyVisibleChains", Vector3(0, 2.65, -0.46), 1.7, first_house_penance)

    var backlight := OmniLight3D.new()
    backlight.name = "FirstHouse_Backlight_For_DoorwaySilhouette"
    backlight.position = Vector3(24.0, 2.8, 36.85)
    backlight.light_color = Color(1.0, 0.55, 0.20)
    backlight.light_energy = 1.2
    backlight.omni_range = 6.0
    world_root.add_child(backlight)

func _build_demo_clues_and_interactables() -> void:
    var first_house := Vector3(24, 0, 36)
    _add_box("FirstHouse_Clue_BlankFamilyPhoto_Inspectable", first_house + Vector3(1.75, 1.04, 0.68), Vector3(0.9, 0.055, 0.62), mat_photo, false, Vector3(0, 0.18, 0))
    _add_box("FirstHouse_Photo_ContrastBacking", first_house + Vector3(1.75, 1.015, 0.68), Vector3(1.1, 0.035, 0.78), mat_dark, false, Vector3(0, 0.18, 0))
    _add_interactable_area(
        "Interact_FirstHouse_BlankPhoto",
        first_house + Vector3(1.65, 1.1, 0.65),
        Vector3(2.8, 1.9, 2.6),
        "Inspect",
        "The family photo has one face scraped away. The dust outline is smaller than the others."
    )

    _add_box("Park_Clue_WetChildBlanket", Vector3(-33.4, 0.45, -11.1), Vector3(1.0, 0.08, 0.7), mat_wet_cloth, false, Vector3(0, -0.35, 0))
    _add_box("Park_Clue_RustedRecordTag", Vector3(-33.0, 0.55, -11.55), Vector3(0.35, 0.04, 0.22), mat_rusted_metal, false, Vector3(0, -0.35, 0))
    _add_interactable_area(
        "Interact_Park_DrainEvidence",
        Vector3(-33.5, 0.8, -11.5),
        Vector3(2.2, 1.8, 2.2),
        "Inspect",
        "A soaked blanket is tagged 'FH intake'. The name line is torn away."
    )

    var church := Vector3(34, 0, 4)
    _add_box("Church_Clue_InternalHandlingNotice", church + Vector3(0, 1.35, 7.0), Vector3(1.2, 0.06, 0.8), mat_photo, false)
    _add_interactable_area(
        "Interact_Church_InternalHandlingNotice",
        church + Vector3(0, 1.2, 7.0),
        Vector3(3.0, 2.0, 3.0),
        "Inspect",
        "The notice repeats one phrase: handle this internally."
    )

func _build_church_lock_state() -> void:
    church_door_blocker = _add_box("Church_RustedDoorBlocker_LockedUntilCulDeSac", Vector3(34, 1.55, 13.4), Vector3(4.4, 3.1, 0.5), mat_rusted_metal, true)

func _build_tunnel_pressure_proxy() -> void:
    penance_chase_proxy = Node3D.new()
    penance_chase_proxy.name = "Penance_TunnelPressureProxy"
    penance_chase_proxy.position = Vector3(-34, -4.0, -9.0)
    penance_chase_proxy.visible = false
    world_root.add_child(penance_chase_proxy)

    _add_box("TunnelPenance_WetClothBody", Vector3(0, 2.0, 0), Vector3(1.45, 4.0, 0.8), mat_wet_cloth, false, Vector3.ZERO, penance_chase_proxy)
    _add_box("TunnelPenance_DoorMask", Vector3(0, 4.0, -0.45), Vector3(1.0, 1.45, 0.18), mat_rotten_wood, false, Vector3.ZERO, penance_chase_proxy)
    _add_chain_pair("TunnelPenance_Chains", Vector3(0, 2.6, -0.52), 2.0, penance_chase_proxy)

func _build_foster_house_reveal_props() -> void:
    var monitor_pos := Vector3(5.0, -2.65, -83.5)
    _add_box("TunnelExit_ChurchMonitorStand", monitor_pos + Vector3(0, 0.5, 0), Vector3(1.6, 1.0, 0.25), mat_rusted_metal, true)
    _add_box("TunnelExit_ChurchMonitorScreen_FosterHouseFeed", monitor_pos + Vector3(0, 1.15, -0.16), Vector3(1.35, 0.75, 0.08), mat_window, false)
    _add_interactable_area(
        "Interact_TunnelExit_FosterHouseMonitor",
        monitor_pos + Vector3(0, 1.1, 0),
        Vector3(2.6, 2.0, 2.0),
        "Inspect",
        "The monitor shows the Foster House. Penance stands in the room where the file should be."
    )

    foster_house_reveal_light = OmniLight3D.new()
    foster_house_reveal_light.name = "FosterHouse_RevealWarmSickLight"
    foster_house_reveal_light.position = Vector3(0, 4.0, -110.0)
    foster_house_reveal_light.light_color = Color(1.0, 0.45, 0.18)
    foster_house_reveal_light.light_energy = 0.0
    foster_house_reveal_light.omni_range = 22.0
    world_root.add_child(foster_house_reveal_light)

func _register_event_areas() -> void:
    _add_event_area("Event_FirstHouse_FrontApproach", Vector3(24, 1.2, 43.0), Vector3(8.0, 2.4, 7.0))
    _add_event_area("Event_FirstHouse_Entry", Vector3(24, 1.2, 39.1), Vector3(4.0, 2.4, 3.2))
    _add_event_area("Event_Church_BasementEntrance", Vector3(27.2, 1.2, 0), Vector3(5, 2.4, 5))
    _add_event_area("Event_RoadsLoop_NorthExit_TeleportBeforeUnlock", Vector3(0, 1.2, -79), Vector3(12, 2.4, 5))
    _add_event_area("Event_Lightning_RevealsPenance_LongSightline", Vector3(0, 1.2, -50), Vector3(70, 2.4, 8))
    _add_event_area("Event_Park_LightsFlicker", Vector3(-21, 1.2, -11), Vector3(34, 2.4, 30))
    _add_event_area("Event_FirstHouse_HallwayStretch", Vector3(24, 1.2, 27), Vector3(5, 2.4, 8))
    _add_event_area("Event_FirstHouse_DoorAppearsInWall", Vector3(24, 1.2, 29), Vector3(4, 2.4, 4))
    _add_event_area("Event_Church_Threshold", Vector3(34, 1.2, 14), Vector3(9, 2.4, 5))
    _add_event_area("Event_Tunnel_PressureStarts", Vector3(-34, -2.5, -20), Vector3(5, 3.0, 8))
    _add_event_area("Event_TunnelExit_FinalHouseBecomesReachable", Vector3(5, -2.4, -85), Vector3(5, 4, 8))
    _add_event_area("Event_FosterHouse_FinalApproach", Vector3(0, 1.2, -99), Vector3(12, 2.4, 10))
    _add_event_area("Event_CulDeSac_LightningPenanceAngle", Vector3(-86, 1.2, -15), Vector3(34, 2.4, 34))

func _add_event_area(area_name: String, pos: Vector3, size: Vector3) -> void:
    var area := Area3D.new()
    area.name = area_name
    area.position = pos
    area.monitoring = true
    area.collision_layer = 0
    area.collision_mask = 1

    var shape := CollisionShape3D.new()
    var box := BoxShape3D.new()
    box.size = size
    shape.shape = box
    area.add_child(shape)
    area.body_entered.connect(_on_event_area_body_entered.bind(area_name))
    event_root.add_child(area)

func _on_event_area_body_entered(body: Node3D, event_name: String) -> void:
    if not body.is_in_group("player"):
        return

    match event_name:
        "Event_FirstHouse_FrontApproach":
            _handle_first_house_approached()
        "Event_FirstHouse_Entry":
            _handle_first_house_entered()
        "Event_RoadsLoop_NorthExit_TeleportBeforeUnlock":
            if not final_house_unlocked:
                body.global_position = Vector3(body.global_position.x, body.global_position.y, 18.0)
                _trigger_lightning(true)
        "Event_Lightning_RevealsPenance_LongSightline":
            _fire_once(event_name, func() -> void:
                _trigger_lightning(true)
            )
        "Event_CulDeSac_LightningPenanceAngle":
            if demo_director.try_advance(DemoDirectorScript.PARK_DONE, DemoDirectorScript.CUL_DE_SAC_DONE, "Reached cul-de-sac"):
                _set_phase(DemoPhase.CUL_DE_SAC)
                _open_route_gate(route_gate_to_church)
                _trigger_lightning(true)
                _unlock_church()
        "Event_Park_LightsFlicker":
            if demo_director.try_advance(DemoDirectorScript.HOUSE_DONE, DemoDirectorScript.PARK_DONE, "Reached park"):
                _set_phase(DemoPhase.PARK_LURE)
                _open_route_gate(route_gate_to_cul_de_sac)
                _force_light_flicker()
        "Event_FirstHouse_HallwayStretch":
            if demo_director.first_house_complete:
                _fire_once(event_name, func() -> void:
                    _stretch_first_house_hallway()
                )
        "Event_FirstHouse_DoorAppearsInWall":
            if demo_director.first_house_complete:
                _fire_once(event_name, func() -> void:
                    _reveal_appearing_door()
                )
        "Event_Church_Threshold":
            if demo_director.try_advance(DemoDirectorScript.CUL_DE_SAC_DONE, DemoDirectorScript.CHURCH_DONE, "Reached church"):
                _set_phase(DemoPhase.CHURCH_UNLOCKED)
        "Event_Church_BasementEntrance":
            if demo_director.state == DemoDirectorScript.CHURCH_DONE and church_notice_inspected:
                print("Reached basement entrance")
                if player != null:
                    player.global_position = Vector3(-34, -3.85, -10)
                _set_phase(DemoPhase.TUNNEL_PRESSURE)
            elif demo_director.state == DemoDirectorScript.CHURCH_DONE:
                GameState.show_warning("The basement chain will not move until you inspect the notice.")
                AudioManager.play_ui_warning("basement_notice_required")
        "Event_Tunnel_PressureStarts":
            if church_notice_inspected and demo_director.try_advance(DemoDirectorScript.CHURCH_DONE, DemoDirectorScript.BASEMENT_DONE, "Reached basement"):
                _start_tunnel_pressure()
        "Event_TunnelExit_FinalHouseBecomesReachable":
            if demo_director.state == DemoDirectorScript.BASEMENT_DONE:
                _fire_once(event_name, func() -> void:
                    _unlock_final_house()
                )
        "Event_FosterHouse_FinalApproach":
            if final_house_unlocked and demo_director.try_advance(DemoDirectorScript.BASEMENT_DONE, DemoDirectorScript.DEMO_DONE, "Reached end trigger"):
                _fire_once(event_name, func() -> void:
                    _complete_demo()
                )

func _handle_first_house_approached() -> void:
    if demo_director.state != DemoDirectorScript.START or demo_director.first_house_complete:
        return

    if demo_director.mark_first_house_approached():
        print("Reached first house approach")
        _set_phase(DemoPhase.FIRST_HOUSE)
    if not demo_director.first_house_reveal_done:
        _trigger_first_house_penance_reveal()

func _handle_first_house_entered() -> void:
    if demo_director.state != DemoDirectorScript.START or demo_director.first_house_complete:
        return

    if not demo_director.first_house_approached:
        _handle_first_house_approached()
    if demo_director.mark_first_house_entered():
        print("Entered first house")
        _set_phase(DemoPhase.FIRST_HOUSE_CLUE)

func _fire_once(event_name: String, callback: Callable) -> void:
    if fired_events.has(event_name):
        return
    fired_events[event_name] = true
    callback.call()

func _add_interactable_area(area_name: String, pos: Vector3, size: Vector3, prompt: String, inspect_text: String) -> Area3D:
    var area := Area3D.new()
    area.name = area_name
    area.position = pos
    area.monitoring = true
    area.collision_layer = 0
    area.collision_mask = 1
    area.set_meta("prompt", prompt)
    area.set_meta("inspect_text", inspect_text)

    var shape := CollisionShape3D.new()
    var box := BoxShape3D.new()
    box.size = size
    shape.shape = box
    area.add_child(shape)

    area.body_entered.connect(_on_interactable_body_entered.bind(area))
    area.body_exited.connect(_on_interactable_body_exited.bind(area))
    event_root.add_child(area)
    return area

func _on_interactable_body_entered(body: Node3D, area: Area3D) -> void:
    if not body.is_in_group("player"):
        return
    current_interactable = area
    _refresh_objective_label()

func _on_interactable_body_exited(body: Node3D, area: Area3D) -> void:
    if not body.is_in_group("player"):
        return
    if current_interactable == area:
        current_interactable = null
        _refresh_objective_label()

func _try_interact() -> void:
    if current_interactable == null:
        return

    var area_name := current_interactable.name
    _show_inspection(String(current_interactable.get_meta("inspect_text", "")))
    match area_name:
        "Interact_FirstHouse_BlankPhoto":
            if demo_director.first_house_entered and not demo_director.first_house_complete:
                demo_director.mark_first_house_photo_inspected()
                if demo_director.complete_first_house():
                    print("Reached lit house")
                    AudioManager.play_ritual_stinger("first_house_photo")
                    _set_phase(DemoPhase.PARK_LURE)
                    _open_route_gate(route_gate_to_park)
                    _reveal_appearing_door()
                    _force_light_flicker()
        "Interact_Park_DrainEvidence":
            if demo_director.state == DemoDirectorScript.PARK_DONE:
                _fire_once(area_name, func() -> void:
                    AudioManager.play_ritual_stinger("park_drain")
                    _set_phase(DemoPhase.CUL_DE_SAC)
                    _trigger_lightning(true)
                )
        "Interact_Church_InternalHandlingNotice":
            if demo_director.state == DemoDirectorScript.CHURCH_DONE:
                _fire_once(area_name, func() -> void:
                    church_notice_inspected = true
                    AudioManager.play_ritual_stinger("church_notice")
                    _open_route_gate(route_gate_to_basement)
                    _set_phase(DemoPhase.TUNNEL_PRESSURE)
                    _force_light_flicker()
                    if player != null:
                        player.global_position = Vector3(-34, -3.85, -10)
                )
        "Interact_TunnelExit_FosterHouseMonitor":
            if final_house_unlocked:
                _complete_demo()

    _refresh_objective_label()

func _trigger_first_house_penance_reveal() -> void:
    if not demo_director.mark_first_house_reveal_done():
        return
    if first_house_penance != null:
        first_house_penance.visible = true
    first_house_penance_timer = 3.0
    AudioManager.play_ritual_stinger("first_house_reveal")
    _trigger_lightning(true)
    _set_phase(DemoPhase.FIRST_HOUSE_CLUE)

func _unlock_church() -> void:
    if church_door_blocker != null:
        church_door_blocker.visible = false
        _set_mesh_collision_enabled(church_door_blocker, false)
    _set_phase(DemoPhase.CHURCH_UNLOCKED)
    GameState.show_warning("The church door is open.")
    AudioManager.play_ritual_stinger("church_open")

func _open_route_gate(gate: Node3D) -> void:
    if gate == null:
        return
    gate.visible = false
    _set_mesh_collision_enabled(gate, false)

func _set_soft_route_group_enabled(group_name: String, enabled: bool) -> void:
    if not soft_route_blocks.has(group_name):
        return

    for block in soft_route_blocks[group_name]:
        var block_node := block as Node3D
        if block_node == null:
            continue
        block_node.visible = enabled
        _set_mesh_collision_enabled(block_node, enabled)

func _update_soft_route_blocks() -> void:
    var state := demo_director.state
    _set_soft_route_group_enabled("before_park", state == DemoDirectorScript.START)
    _set_soft_route_group_enabled("before_cul_de_sac", state == DemoDirectorScript.START or state == DemoDirectorScript.HOUSE_DONE)
    _set_soft_route_group_enabled("before_church", state != DemoDirectorScript.CUL_DE_SAC_DONE and state != DemoDirectorScript.CHURCH_DONE and state != DemoDirectorScript.BASEMENT_DONE and state != DemoDirectorScript.DEMO_DONE)
    _set_soft_route_group_enabled("before_basement", state != DemoDirectorScript.BASEMENT_DONE and state != DemoDirectorScript.DEMO_DONE and not church_notice_inspected)
    _set_soft_route_group_enabled("cul_de_sac_funnel", state != DemoDirectorScript.CUL_DE_SAC_DONE and state != DemoDirectorScript.CHURCH_DONE and state != DemoDirectorScript.BASEMENT_DONE and state != DemoDirectorScript.DEMO_DONE)
    _set_soft_route_group_enabled("church_funnel", state != DemoDirectorScript.CHURCH_DONE and state != DemoDirectorScript.BASEMENT_DONE and state != DemoDirectorScript.DEMO_DONE)

func _start_tunnel_pressure() -> void:
    if demo_phase < DemoPhase.TUNNEL_PRESSURE:
        _set_phase(DemoPhase.TUNNEL_PRESSURE)
    tunnel_pressure_active = true
    tunnel_pressure_timer = 16.0
    if penance_chase_proxy != null:
        penance_chase_proxy.global_position = Vector3(-34, -4.0, -10)
        penance_chase_proxy.visible = true
    AudioManager.play_ritual_stinger("tunnel_pressure")
    _trigger_lightning(true)

func _complete_demo() -> void:
    if demo_phase == DemoPhase.DEMO_COMPLETE:
        return
    _set_phase(DemoPhase.DEMO_COMPLETE)
    title_card_timer = 9.0
    if title_card_label != null:
        title_card_label.visible = true
        title_card_label.text = "PENANCE\nThis was only the first descent."
    if penance_silhouette != null:
        penance_silhouette.visible = true
        penance_silhouette.position = Vector3(0, 0, -104)
    if foster_house_reveal_light != null:
        foster_house_reveal_light.light_energy = 3.0
    AudioManager.play_ritual_stinger("demo_complete")
    _trigger_lightning(true)

func _update_flicker_lights(delta: float) -> void:
    for light in flicker_lights:
        if light == null:
            continue
        var base_energy := float(light.get_meta("base_energy", 0.35))
        var phase := float(light.get_meta("phase", 0.0))
        phase += delta * float(light.get_meta("speed", 7.0))
        light.set_meta("phase", phase)
        var pulse := 0.72 + sin(phase) * 0.18 + sin(phase * 2.7) * 0.10
        if randf() < 0.012:
            pulse *= 0.18
        light.light_energy = max(0.02, base_energy * pulse)

func _update_lightning(delta: float) -> void:
    lightning_cooldown = max(0.0, lightning_cooldown - delta)
    thunder_audio_cooldown = max(0.0, thunder_audio_cooldown - delta)
    if lightning_timer > 0.0:
        lightning_timer -= delta
        storm_light.light_energy = 1.8 if lightning_timer > 0.18 else 0.62
        if penance_silhouette != null:
            penance_silhouette.visible = true
    else:
        storm_light.light_energy = 0.45 if debug_visibility_enabled else 0.035
        if penance_silhouette != null and not final_house_unlocked:
            penance_silhouette.visible = false

func _trigger_lightning(force: bool = false) -> void:
    if lightning_cooldown > 0.0 and not force:
        return
    lightning_timer = 0.42
    lightning_cooldown = 5.0
    if penance_silhouette != null:
        penance_silhouette.visible = true
    if thunder_audio_cooldown <= 0.0:
        AudioManager.play_thunder(force)
        thunder_audio_cooldown = 4.0

func _force_light_flicker() -> void:
    for light in flicker_lights:
        light.set_meta("phase", randf() * 20.0)
        light.light_energy *= 0.35

func _stretch_first_house_hallway() -> void:
    if hallway_stretched or stretch_hallway_section == null:
        return
    hallway_stretched = true
    stretch_hallway_section.scale.z = 3.4
    stretch_hallway_section.position.z -= 7.5
    _trigger_lightning(true)

func _reveal_appearing_door() -> void:
    if door_revealed:
        return
    door_revealed = true
    if false_wall_patch != null:
        false_wall_patch.visible = false
    if appearing_door != null:
        appearing_door.visible = true
    _force_light_flicker()
    AudioManager.play_ritual_stinger("appearing_door")

func _unlock_final_house() -> void:
    if final_house_unlocked:
        return
    final_house_unlocked = true
    if final_house_barrier != null:
        final_house_barrier.visible = false
        _set_mesh_collision_enabled(final_house_barrier, false)
    if final_house_road != null:
        final_house_road.visible = true
        _set_mesh_collision_enabled(final_house_road, true)
    if penance_silhouette != null:
        penance_silhouette.visible = true
        penance_silhouette.position = Vector3(0, 0, -104)
    if foster_house_reveal_light != null:
        foster_house_reveal_light.light_energy = 1.4
    if player != null and player.global_position.y < -1.0:
        player.global_position = Vector3(0, 1.1, -70)
    _set_phase(DemoPhase.FOSTER_HOUSE_REVEAL)
    GameState.show_warning("The road has remembered the house.")
    _trigger_lightning(true)

func _update_demo_timers(delta: float) -> void:
    if first_house_penance_timer > 0.0:
        first_house_penance_timer -= delta
        if first_house_penance_timer <= 0.0 and first_house_penance != null:
            first_house_penance.visible = false
            _force_light_flicker()

    if demo_phase == DemoPhase.PARK_LURE:
        park_lure_pulse_timer -= delta
        if park_lure_pulse_timer <= 0.0:
            park_lure_pulse_timer = 4.5
            _pulse_area_lights("Park")

    if title_card_timer > 0.0:
        title_card_timer -= delta
        if title_card_timer <= 0.0 and title_card_label != null:
            title_card_label.text = "DEMO COMPLETE\nPENANCE"

func _show_inspection(text: String) -> void:
    if text == "":
        return

    inspection_timer = 3.2
    if inspection_label != null:
        inspection_label.text = text
        inspection_label.visible = true
    if interact_prompt_label != null:
        interact_prompt_label.visible = false
    if player_camera != null:
        player_camera.fov = max(58.0, default_camera_fov - 14.0)

func _update_inspection(delta: float) -> void:
    if inspection_timer <= 0.0:
        return

    inspection_timer -= delta
    if inspection_timer <= 0.0:
        if inspection_label != null:
            inspection_label.visible = false
        if player_camera != null:
            player_camera.fov = default_camera_fov
        _refresh_objective_label()

func _update_tunnel_pressure(delta: float) -> void:
    if not tunnel_pressure_active:
        return

    tunnel_pressure_timer -= delta
    if penance_chase_proxy != null and player != null:
        var target := player.global_position
        target.y = -4.0
        var to_player := target - penance_chase_proxy.global_position
        if to_player.length() > 0.1:
            penance_chase_proxy.global_position += to_player.normalized() * 2.35 * delta
            penance_chase_proxy.look_at(Vector3(target.x, penance_chase_proxy.global_position.y, target.z), Vector3.UP)

    if tunnel_pressure_timer <= 0.0:
        tunnel_pressure_active = false
        if penance_chase_proxy != null:
            penance_chase_proxy.visible = false

func _pulse_area_lights(name_fragment: String) -> void:
    for light in flicker_lights:
        if light != null and light.name.contains(name_fragment):
            light.light_energy = float(light.get_meta("base_energy", light.light_energy)) * 2.5

func _build_objective_overlay() -> void:
    objective_canvas = CanvasLayer.new()
    objective_canvas.name = "DemoObjectiveOverlay"
    objective_canvas.layer = 10
    add_child(objective_canvas)

    objective_label = Label.new()
    objective_label.name = "ObjectiveLabel"
    objective_label.position = Vector2(28, 24)
    objective_label.size = Vector2(760, 120)
    objective_label.add_theme_font_size_override("font_size", 18)
    objective_label.modulate = Color(0.82, 0.88, 0.90, 0.92)
    objective_canvas.add_child(objective_label)

    interact_prompt_label = Label.new()
    interact_prompt_label.name = "InteractPrompt"
    interact_prompt_label.visible = false
    interact_prompt_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    interact_prompt_label.position = Vector2(0, 0)
    interact_prompt_label.set_anchors_preset(Control.PRESET_CENTER)
    interact_prompt_label.offset_left = -160
    interact_prompt_label.offset_top = 120
    interact_prompt_label.offset_right = 160
    interact_prompt_label.offset_bottom = 170
    interact_prompt_label.add_theme_font_size_override("font_size", 24)
    interact_prompt_label.modulate = Color(1.0, 0.86, 0.56, 1.0)
    objective_canvas.add_child(interact_prompt_label)

    inspection_label = Label.new()
    inspection_label.name = "InspectionText"
    inspection_label.visible = false
    inspection_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    inspection_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
    inspection_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    inspection_label.set_anchors_preset(Control.PRESET_CENTER)
    inspection_label.offset_left = -360
    inspection_label.offset_top = -90
    inspection_label.offset_right = 360
    inspection_label.offset_bottom = 90
    inspection_label.add_theme_font_size_override("font_size", 26)
    inspection_label.modulate = Color(0.95, 0.92, 0.82, 1.0)
    objective_canvas.add_child(inspection_label)

    title_card_label = Label.new()
    title_card_label.name = "TitleCard"
    title_card_label.visible = false
    title_card_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    title_card_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
    title_card_label.set_anchors_preset(Control.PRESET_FULL_RECT)
    title_card_label.add_theme_font_size_override("font_size", 48)
    title_card_label.modulate = Color(0.92, 0.90, 0.84, 1.0)
    objective_canvas.add_child(title_card_label)

    stamina_bar = ProgressBar.new()
    stamina_bar.name = "StaminaBar"
    stamina_bar.min_value = 0.0
    stamina_bar.max_value = 100.0
    stamina_bar.value = 100.0
    stamina_bar.show_percentage = false
    stamina_bar.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
    stamina_bar.offset_left = 28
    stamina_bar.offset_top = -42
    stamina_bar.offset_right = 198
    stamina_bar.offset_bottom = -32
    stamina_bar.modulate = Color(0.82, 0.88, 0.82, 0.78)

    var stamina_bg := StyleBoxFlat.new()
    stamina_bg.bg_color = Color(0.015, 0.018, 0.020, 0.58)
    stamina_bg.border_color = Color(0.18, 0.22, 0.20, 0.70)
    stamina_bg.set_border_width_all(1)
    stamina_bar.add_theme_stylebox_override("background", stamina_bg)

    var stamina_fill := StyleBoxFlat.new()
    stamina_fill.bg_color = Color(0.58, 0.66, 0.58, 0.82)
    stamina_bar.add_theme_stylebox_override("fill", stamina_fill)
    objective_canvas.add_child(stamina_bar)

func _connect_player_ui() -> void:
    if player == null:
        return
    if player.has_signal("stamina_changed"):
        player.connect("stamina_changed", _on_player_stamina_changed)

func _on_player_stamina_changed(current_stamina: float, max_stamina: float) -> void:
    if stamina_bar == null:
        return
    stamina_bar.max_value = max_stamina
    stamina_bar.value = current_stamina
    stamina_bar.modulate.a = 0.88 if current_stamina < max_stamina - 1.0 else 0.42

func _set_phase(next_phase: int) -> void:
    if next_phase < demo_phase and demo_phase != DemoPhase.DEMO_COMPLETE:
        return
    demo_phase = next_phase
    _update_soft_route_blocks()
    _refresh_objective_label()

func _refresh_objective_label() -> void:
    if objective_label == null:
        return

    var text := _phase_objective_text()
    text += "\nSTATE: " + demo_director.state
    if current_interactable != null:
        text += "\nE - " + String(current_interactable.get_meta("prompt", "Inspect"))
    text += "\nShift sprint | Ctrl/C crouch | F3 debug light | F2 overlay | F5 advance"
    objective_label.text = text

    if interact_prompt_label != null:
        interact_prompt_label.visible = current_interactable != null and inspection_timer <= 0.0
        if interact_prompt_label.visible:
            interact_prompt_label.text = "E  " + String(current_interactable.get_meta("prompt", "Inspect"))

func _phase_objective_text() -> String:
    match demo_phase:
        DemoPhase.ARRIVAL:
            return "Arrival Street\nFollow the wet road toward the only warm house light."
        DemoPhase.FIRST_HOUSE:
            return "First Lit House\nApproach the warm window. Something is standing inside."
        DemoPhase.FIRST_HOUSE_CLUE:
            return "First Lit House\nEnter the house and inspect the photo on the table."
        DemoPhase.PARK_LURE:
            return "Park Lure\nFollow the failing park lamp and the drain beside the playset."
        DemoPhase.CUL_DE_SAC:
            return "Cul-de-sac\nThe road is wrong. Follow the bell after the lightning."
        DemoPhase.CHURCH_UNLOCKED:
            return "Church / Community Center\nThe church is open. Find what they handled internally."
        DemoPhase.TUNNEL_PRESSURE:
            return "Storm Drain\nKeep moving through the buried path. Do not wait for the chains."
        DemoPhase.FOSTER_HOUSE_REVEAL:
            return "Foster House\nThe road remembers the house. Approach it."
        DemoPhase.DEMO_COMPLETE:
            return "Demo Complete"
        _:
            return "Penance Demo"

func _debug_advance_phase() -> void:
    match demo_director.state:
        DemoDirectorScript.START:
            demo_director.mark_first_house_approached()
            demo_director.mark_first_house_entered()
            demo_director.mark_first_house_photo_inspected()
            demo_director.complete_first_house()
            _open_route_gate(route_gate_to_park)
            _set_phase(DemoPhase.PARK_LURE)
        DemoDirectorScript.HOUSE_DONE:
            demo_director.advance(DemoDirectorScript.PARK_DONE)
            _set_phase(DemoPhase.PARK_LURE)
        DemoDirectorScript.PARK_DONE:
            demo_director.advance(DemoDirectorScript.CUL_DE_SAC_DONE)
            _set_phase(DemoPhase.CUL_DE_SAC)
            _unlock_church()
        DemoDirectorScript.CUL_DE_SAC_DONE:
            demo_director.advance(DemoDirectorScript.CHURCH_DONE)
            _set_phase(DemoPhase.CHURCH_UNLOCKED)
        DemoDirectorScript.CHURCH_DONE:
            demo_director.advance(DemoDirectorScript.BASEMENT_DONE)
            _set_phase(DemoPhase.TUNNEL_PRESSURE)
        DemoDirectorScript.BASEMENT_DONE:
            _unlock_final_house()
        DemoDirectorScript.DEMO_DONE:
            _complete_demo()

func _add_streetlight(light_name: String, pos: Vector3, energy: float) -> void:
    _add_box(light_name + "_Pole", pos + Vector3(0, 2.0, 0), Vector3(0.18, 4.0, 0.18), mat_rusted_metal, true)
    _add_box(light_name + "_Head", pos + Vector3(0, 4.05, -0.45), Vector3(0.8, 0.22, 0.6), mat_rusted_metal, false)

    var light := OmniLight3D.new()
    light.name = light_name + "_WeakAmberLight"
    light.position = pos + Vector3(0, 3.75, -0.45)
    light.light_color = Color(1.0, 0.58, 0.22)
    light.light_energy = energy
    light.omni_range = 10.5
    light.shadow_enabled = true
    light.set_meta("base_energy", energy)
    light.set_meta("speed", randf_range(5.5, 11.0))
    light.set_meta("phase", randf_range(0.0, 10.0))
    world_root.add_child(light)
    flicker_lights.append(light)

func _scatter_puddles(points: Array[Vector3]) -> void:
    var i := 0
    for point in points:
        _add_box("Puddle_" + str(i), point, Vector3(randf_range(2.2, 4.2), 0.025, randf_range(1.2, 3.2)), mat_water, false, Vector3(0, randf_range(-0.8, 0.8), 0))
        i += 1

func _add_tree_cluster(cluster_name: String, points: Array[Vector3]) -> void:
    var i := 0
    for point in points:
        _add_box(cluster_name + "_Trunk_" + str(i), point + Vector3(0, 2.2, 0), Vector3(0.55, 4.4, 0.55), mat_rotten_wood, true, Vector3(0, randf_range(-0.4, 0.4), 0))
        _add_box(cluster_name + "_CanopyBlock_" + str(i), point + Vector3(0, 5.0, 0), Vector3(3.2, 2.4, 3.2), mat_dark, false, Vector3(0, randf_range(-0.5, 0.5), 0))
        i += 1

func _add_relic_cluster(cluster_name: String, pos: Vector3, rot_y: float) -> void:
    var rot := Vector3(0, rot_y, 0)
    _add_box(cluster_name + "_DoorPlank", pos + _rotated(Vector3(0, 0.8, 0), rot_y), Vector3(1.2, 1.8, 0.16), mat_rotten_wood, false, rot)
    _add_chain_pair(cluster_name + "_Chains", pos + _rotated(Vector3(0, 1.3, -0.15), rot_y), 1.2)
    _add_box(cluster_name + "_OldPhoto", pos + _rotated(Vector3(0.45, 1.35, -0.26), rot_y), Vector3(0.45, 0.55, 0.04), mat_photo, false, rot)
    _add_candle_group(cluster_name + "_Candles", pos + _rotated(Vector3(-0.42, -0.1, -0.26), rot_y))

func _add_candle_group(group_name: String, pos: Vector3, parent: Node3D = null) -> void:
    var target_parent := world_root if parent == null else parent
    for i in range(3):
        var offset := Vector3(float(i - 1) * 0.28, 0, 0)
        _add_box(group_name + "_Candle_" + str(i), pos + offset + Vector3(0, 0.18, 0), Vector3(0.12, 0.36, 0.12), mat_candle, false, Vector3.ZERO, target_parent)

    var light := OmniLight3D.new()
    light.name = group_name + "_TinyLight"
    light.position = pos + Vector3(0, 0.45, 0)
    light.light_color = Color(1.0, 0.48, 0.16)
    light.light_energy = 0.18
    light.omni_range = 3.2
    target_parent.add_child(light)

func _add_photo_wall(wall_name: String, pos: Vector3, rot_y: float) -> void:
    var rot := Vector3(0, rot_y, 0)
    for i in range(5):
        var offset := Vector3(float(i - 2) * 0.55, sin(float(i)) * 0.08, 0)
        _add_box(wall_name + "_Photo_" + str(i), pos + _rotated(offset, rot_y), Vector3(0.35, 0.48, 0.035), mat_photo, false, rot)

func _add_chain_pair(chain_name: String, pos: Vector3, height: float, parent: Node3D = null) -> void:
    var target_parent := world_root if parent == null else parent
    _add_box(chain_name + "_Left", pos + Vector3(-0.32, 0, 0), Vector3(0.08, height, 0.08), mat_chain, false, Vector3.ZERO, target_parent)
    _add_box(chain_name + "_Right", pos + Vector3(0.32, 0, 0), Vector3(0.08, height, 0.08), mat_chain, false, Vector3.ZERO, target_parent)

func _add_chain_fence(fence_name: String, pos: Vector3, length: float, along_z: bool) -> void:
    var post_count := int(length / 4.0) + 1
    for i in range(post_count):
        var t := -length * 0.5 + float(i) * 4.0
        var post_pos := pos + (Vector3(0, 0, t) if along_z else Vector3(t, 0, 0))
        _add_box(fence_name + "_Post_" + str(i), post_pos + Vector3(0, 0.55, 0), Vector3(0.14, 1.1, 0.14), mat_rusted_metal, true)

    var rail_size := Vector3(0.08, 0.08, length) if along_z else Vector3(length, 0.08, 0.08)
    _add_box(fence_name + "_TopRail", pos + Vector3(0, 1.15, 0), rail_size, mat_rusted_metal, false)
    _add_box(fence_name + "_MidRail", pos + Vector3(0, 0.58, 0), rail_size, mat_chain, false)

func _add_box(
    node_name: String,
    pos: Vector3,
    size: Vector3,
    material: Material,
    collision_enabled: bool,
    rotation: Vector3 = Vector3.ZERO,
    parent: Node3D = null
) -> MeshInstance3D:
    var target_parent := world_root if parent == null else parent
    var mesh_instance := MeshInstance3D.new()
    mesh_instance.name = node_name
    mesh_instance.position = pos
    mesh_instance.rotation = rotation

    var mesh := BoxMesh.new()
    mesh.size = size
    mesh_instance.mesh = mesh
    mesh_instance.material_override = material
    target_parent.add_child(mesh_instance)

    if collision_enabled:
        var body := StaticBody3D.new()
        body.name = node_name + "_Collision"
        body.position = pos
        body.rotation = rotation

        var shape := CollisionShape3D.new()
        var box := BoxShape3D.new()
        box.size = size
        shape.shape = box
        body.add_child(shape)
        target_parent.add_child(body)
        mesh_instance.set_meta("collision_node", body.get_path())

    return mesh_instance

func _set_mesh_collision_enabled(mesh_instance: Node3D, enabled: bool) -> void:
    if not mesh_instance.has_meta("collision_node"):
        return

    var body_path: NodePath = mesh_instance.get_meta("collision_node")
    var body := get_node_or_null(body_path) as StaticBody3D
    if body == null:
        return

    body.collision_layer = 1 if enabled else 0
    body.collision_mask = 1 if enabled else 0

func _add_cylinder(
    node_name: String,
    pos: Vector3,
    radius: float,
    height: float,
    material: Material,
    collision_enabled: bool,
    parent: Node3D = null
) -> MeshInstance3D:
    var target_parent := world_root if parent == null else parent
    var mesh_instance := MeshInstance3D.new()
    mesh_instance.name = node_name
    mesh_instance.position = pos

    var mesh := CylinderMesh.new()
    mesh.top_radius = radius
    mesh.bottom_radius = radius
    mesh.height = height
    mesh.radial_segments = 48
    mesh_instance.mesh = mesh
    mesh_instance.material_override = material
    target_parent.add_child(mesh_instance)

    if collision_enabled:
        var body := StaticBody3D.new()
        body.name = node_name + "_Collision"
        body.position = pos

        var shape := CollisionShape3D.new()
        var cylinder := CylinderShape3D.new()
        cylinder.radius = radius
        cylinder.height = height
        shape.shape = cylinder
        body.add_child(shape)
        target_parent.add_child(body)

    return mesh_instance

func _rotated(vector: Vector3, yaw: float) -> Vector3:
    return Basis(Vector3.UP, yaw) * vector

func _ensure_demo_input() -> void:
    _bind_demo_key("toggle_debug_visibility", KEY_F3)
    _bind_demo_key("toggle_objective_overlay", KEY_F2)
    _bind_demo_key("advance_demo_phase", KEY_F5)

func _bind_demo_key(action: String, keycode: Key) -> void:
    if not InputMap.has_action(action):
        InputMap.add_action(action)

    for existing_event in InputMap.action_get_events(action):
        if existing_event is InputEventKey and existing_event.physical_keycode == keycode:
            return

    var ev := InputEventKey.new()
    ev.physical_keycode = keycode
    InputMap.action_add_event(action, ev)
