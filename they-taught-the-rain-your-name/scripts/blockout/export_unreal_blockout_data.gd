extends SceneTree

const SCENE_PATH := "res://scenes/blockout/suburban_horror_blockout.tscn"
const UE_PROJECT_DIR := "they-taught-the-rain-your-name-ue"
const OUTPUT_RELATIVE_PATH := "Content/PenanceBlockoutExport.json"

var scene: Node

func _init() -> void:
    call_deferred("_run")

func _run() -> void:
    scene = load(SCENE_PATH).instantiate()
    root.add_child(scene)
    await process_frame

    var export_data := {
        "source": SCENE_PATH,
        "unit_scale": "1 Godot unit = 1 meter; Unreal output uses centimeters",
        "coordinate_mapping": "UE_X = -Godot_Z, UE_Y = Godot_X, UE_Z = Godot_Y",
        "meshes": [],
        "areas": [],
        "lights": [],
        "player_start": {},
    }

    _collect_nodes(scene, export_data)

    var godot_root := ProjectSettings.globalize_path("res://").rstrip("/")
    var ue_root := godot_root.get_base_dir().path_join(UE_PROJECT_DIR)
    var output_path := ue_root.path_join(OUTPUT_RELATIVE_PATH)
    DirAccess.make_dir_recursive_absolute(output_path.get_base_dir())

    var file := FileAccess.open(output_path, FileAccess.WRITE)
    if file == null:
        push_error("Could not write Unreal blockout export: " + output_path)
        quit(1)
        return

    file.store_string(JSON.stringify(export_data, "\t"))
    file.close()

    print("UNREAL BLOCKOUT EXPORT WRITTEN: " + output_path)
    print("Meshes: " + str(export_data["meshes"].size()))
    print("Areas: " + str(export_data["areas"].size()))
    print("Lights: " + str(export_data["lights"].size()))
    quit(0)

func _collect_nodes(node: Node, export_data: Dictionary) -> void:
    if node is MeshInstance3D:
        var mesh_entry := _mesh_entry(node as MeshInstance3D)
        if not mesh_entry.is_empty():
            export_data["meshes"].append(mesh_entry)
    elif node is Area3D:
        var area_entry := _area_entry(node as Area3D)
        if not area_entry.is_empty():
            export_data["areas"].append(area_entry)
    elif node is Light3D:
        export_data["lights"].append(_light_entry(node as Light3D))

    if node.name == "Player" and node is Node3D:
        var player := node as Node3D
        export_data["player_start"] = {
            "name": player.name,
            "position": _v3(player.global_position),
            "rotation_degrees": _v3(player.global_rotation_degrees),
        }

    for child in node.get_children():
        _collect_nodes(child, export_data)

func _mesh_entry(mesh_instance: MeshInstance3D) -> Dictionary:
    var mesh := mesh_instance.mesh
    var shape_type := ""
    var shape := {}

    if mesh is BoxMesh:
        shape_type = "box"
        shape = {"size": _v3((mesh as BoxMesh).size)}
    elif mesh is CylinderMesh:
        var cylinder := mesh as CylinderMesh
        shape_type = "cylinder"
        shape = {
            "radius": cylinder.top_radius,
            "height": cylinder.height,
        }
    else:
        return {}

    return {
        "name": mesh_instance.name,
        "path": str(mesh_instance.get_path()),
        "type": shape_type,
        "position": _v3(mesh_instance.global_position),
        "rotation_degrees": _v3(mesh_instance.global_rotation_degrees),
        "visible": mesh_instance.visible,
        "collision": mesh_instance.has_meta("collision_node"),
        "shape": shape,
        "material": _material_entry(mesh_instance.material_override),
    }

func _area_entry(area: Area3D) -> Dictionary:
    var shape_size := Vector3.ZERO
    for child in area.get_children():
        if child is CollisionShape3D and (child as CollisionShape3D).shape is BoxShape3D:
            shape_size = ((child as CollisionShape3D).shape as BoxShape3D).size
            break

    if shape_size == Vector3.ZERO:
        return {}

    return {
        "name": area.name,
        "path": str(area.get_path()),
        "position": _v3(area.global_position),
        "rotation_degrees": _v3(area.global_rotation_degrees),
        "size": _v3(shape_size),
        "prompt": str(area.get_meta("prompt", "")),
        "inspect_text": str(area.get_meta("inspect_text", "")),
    }

func _light_entry(light: Light3D) -> Dictionary:
    var entry := {
        "name": light.name,
        "path": str(light.get_path()),
        "position": _v3(light.global_position),
        "rotation_degrees": _v3(light.global_rotation_degrees),
        "color": _color(light.light_color),
        "energy": light.light_energy,
        "visible": light.visible,
        "type": "light",
    }

    if light is DirectionalLight3D:
        entry["type"] = "directional"
    elif light is OmniLight3D:
        entry["type"] = "point"
        entry["range"] = (light as OmniLight3D).omni_range
    elif light is SpotLight3D:
        entry["type"] = "spot"
        entry["range"] = (light as SpotLight3D).spot_range
        entry["angle"] = (light as SpotLight3D).spot_angle

    return entry

func _material_entry(material: Material) -> Dictionary:
    if material == null or not material is StandardMaterial3D:
        return {
            "name": "Default_Blockout",
            "albedo": {"r": 0.5, "g": 0.5, "b": 0.5, "a": 1.0},
            "emission_enabled": false,
            "emission": {"r": 0.0, "g": 0.0, "b": 0.0, "a": 1.0},
            "emission_energy": 0.0,
            "roughness": 0.7,
            "metallic": 0.0,
        }

    var standard := material as StandardMaterial3D
    return {
        "name": _material_name_from_color(standard),
        "albedo": _color(standard.albedo_color),
        "emission_enabled": standard.emission_enabled,
        "emission": _color(standard.emission),
        "emission_energy": standard.emission_energy_multiplier,
        "roughness": standard.roughness,
        "metallic": standard.metallic,
    }

func _material_name_from_color(material: StandardMaterial3D) -> String:
    if material.emission_enabled and material.emission_energy_multiplier > 0.8:
        return "Candle_Emissive"
    if material.emission_enabled:
        return "Warm_Window_Or_Spill"
    var color := material.albedo_color
    if color.r < 0.02 and color.g < 0.02 and color.b < 0.025:
        return "Near_Black_Wet_Dark"
    if color.r > 0.30 and color.g > 0.25 and color.b > 0.18:
        return "Old_Photo_Paper"
    if color.r > 0.16 and color.g < 0.13 and color.b < 0.08:
        return "Rusted_Metal"
    if color.r > 0.10 and color.g < 0.12 and color.b < 0.09:
        return "Rotten_Wood"
    if color.b > color.r and color.g > color.r:
        return "Wet_Water_Or_Cloth"
    return "Graybox_Blockout"

func _v3(value: Vector3) -> Dictionary:
    return {"x": value.x, "y": value.y, "z": value.z}

func _color(value: Color) -> Dictionary:
    return {"r": value.r, "g": value.g, "b": value.b, "a": value.a}
