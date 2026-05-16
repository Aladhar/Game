extends Node3D

const PenanceCarrierScene := preload("res://scenes/enemies/penance_carrier.tscn")
const BellSaintScene := preload("res://scenes/enemies/bell_saint.tscn")
const RainHunterScene := preload("res://scenes/enemies/rain_hunter.tscn")
const LanternBrideScene := preload("res://scenes/enemies/lantern_bride.tscn")
const ClubManScene := preload("res://scenes/enemies/club_man.tscn")
const CrookedScarecrowScene := preload("res://scenes/enemies/crooked_scarecrow.tscn")

var mat_road: StandardMaterial3D
var mat_ground: StandardMaterial3D
var mat_metal: StandardMaterial3D
var mat_wood: StandardMaterial3D
var mat_light: StandardMaterial3D
var mat_dark: StandardMaterial3D

func _ready() -> void:
    _make_materials()
    _build_town()
    SceneBus.enemy_stage_changed.connect(_on_enemy_stage_changed)

func _make_materials() -> void:
    mat_road = _mat(Color(0.015, 0.017, 0.02), 0.35, 0.15)
    mat_ground = _mat(Color(0.015, 0.028, 0.018), 0.9, 0.0)
    mat_metal = _mat(Color(0.055, 0.06, 0.065), 0.65, 0.3)
    mat_wood = _mat(Color(0.095, 0.065, 0.045), 0.85, 0.0)
    mat_dark = _mat(Color(0.006, 0.007, 0.009), 0.95, 0.0)
    mat_light = StandardMaterial3D.new()
    mat_light.albedo_color = Color(0.9, 0.62, 0.25)
    mat_light.emission_enabled = true
    mat_light.emission = Color(0.9, 0.55, 0.22)
    mat_light.emission_energy_multiplier = 1.8

func _mat(color: Color, roughness: float, metallic: float) -> StandardMaterial3D:
    var m := StandardMaterial3D.new()
    m.albedo_color = color
    m.roughness = roughness
    m.metallic = metallic
    return m

func _build_town() -> void:
    _box("WetRoad", Vector3(0, -0.05, -20), Vector3(14, 0.1, 110), mat_road)
    _box("LeftGround", Vector3(-18, -0.1, -20), Vector3(22, 0.1, 115), mat_ground)
    _box("RightGround", Vector3(18, -0.1, -20), Vector3(22, 0.1, 115), mat_ground)

    _build_entrance_sign(Vector3(0, 1.2, 18))
    _build_diner(Vector3(-12, 0, -8))
    _build_church(Vector3(14, 0, -26))
    _build_mill(Vector3(-14, 0, -48))
    _build_field(Vector3(18, 0, -58))
    _build_broadcast_tower(Vector3(0, 0, -75))
    _place_enemy_stages()

func _box(name: String, pos: Vector3, size: Vector3, material: Material) -> MeshInstance3D:
    var mesh_instance := MeshInstance3D.new()
    mesh_instance.name = name
    mesh_instance.position = pos
    var mesh := BoxMesh.new()
    mesh.size = size
    mesh_instance.mesh = mesh
    mesh_instance.material_override = material
    add_child(mesh_instance)

    var body := StaticBody3D.new()
    body.name = name + "_Collision"
    body.position = pos
    var shape := CollisionShape3D.new()
    var box := BoxShape3D.new()
    box.size = size
    shape.shape = box
    body.add_child(shape)
    add_child(body)

    return mesh_instance

func _build_entrance_sign(pos: Vector3) -> void:
    _box("GreyhollowSignPost", pos + Vector3(0, 0.8, 0), Vector3(0.18, 1.6, 0.18), mat_wood)
    var sign := _box("GreyhollowSign", pos + Vector3(0, 1.8, 0), Vector3(5.0, 1.0, 0.12), mat_wood)
    sign.name = "GREYHOLLOW_POPULATION_1107"

func _build_diner(pos: Vector3) -> void:
    _box("DinerBlockout", pos + Vector3(0, 1.5, 0), Vector3(8, 3, 7), mat_metal)
    _box("DinerWarmWindow", pos + Vector3(0, 2.2, -3.55), Vector3(3.5, 0.9, 0.08), mat_light)

func _build_church(pos: Vector3) -> void:
    _box("DrownedChurch", pos + Vector3(0, 2, 0), Vector3(7, 4, 9), mat_dark)
    _box("BellTower", pos + Vector3(0, 5.0, -2.5), Vector3(2.1, 6, 2.1), mat_dark)
    _box("ChurchBellMarker", pos + Vector3(0, 7.7, -2.6), Vector3(1.1, 0.8, 1.1), mat_metal)

func _build_mill(pos: Vector3) -> void:
    _box("FeedMill", pos + Vector3(0, 2, 0), Vector3(9, 4, 8), mat_metal)
    _box("MillPipe", pos + Vector3(0, 4.4, -4.5), Vector3(8, 0.35, 0.35), mat_metal)

func _build_field(pos: Vector3) -> void:
    for i in range(5):
        _box("ScarecrowPost_%d" % i, pos + Vector3(i * 2.5 - 5, 1.3, 0), Vector3(0.16, 2.6, 0.16), mat_wood)
        _box("ScarecrowArm_%d" % i, pos + Vector3(i * 2.5 - 5, 2.2, 0), Vector3(1.4, 0.12, 0.12), mat_wood)

func _build_broadcast_tower(pos: Vector3) -> void:
    _box("BroadcastTowerBase", pos + Vector3(0, 1, 0), Vector3(4, 2, 4), mat_metal)
    _box("BroadcastMast", pos + Vector3(0, 8, 0), Vector3(0.35, 14, 0.35), mat_metal)
    _box("WarningConsole", pos + Vector3(0, 1.2, -3), Vector3(2, 1.2, 1), mat_light)

func _place_enemy_stages() -> void:
    var bell := BellSaintScene.instantiate()
    bell.position = Vector3(14, 0, -19)
    add_child(bell)

    var hunter := RainHunterScene.instantiate()
    hunter.position = Vector3(-6, 0, -34)
    add_child(hunter)

    var bride := LanternBrideScene.instantiate()
    bride.position = Vector3(8, 0, -10)
    add_child(bride)

    var club := ClubManScene.instantiate()
    club.position = Vector3(-14, 0, -42)
    add_child(club)

    var scarecrow := CrookedScarecrowScene.instantiate()
    scarecrow.position = Vector3(18, 0, -58)
    add_child(scarecrow)

    var carrier := PenanceCarrierScene.instantiate()
    carrier.name = "PenanceCarrier"
    carrier.position = Vector3(0, 0, -88)
    carrier.visible = false
    add_child(carrier)

func _on_enemy_stage_changed(enemy_name: String, stage: int) -> void:
    if enemy_name == "PenanceCarrier" and stage >= 1:
        var carrier := get_node_or_null("PenanceCarrier")
        if carrier != null:
            carrier.visible = true
