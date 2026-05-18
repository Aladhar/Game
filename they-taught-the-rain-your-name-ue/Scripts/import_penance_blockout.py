import json
import math
import re
from pathlib import Path

import unreal


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPORT_PATH = PROJECT_ROOT / "Content" / "PenanceBlockoutExport.json"
LEVEL_PATH = "/Game/Maps/Penance_Suburban_Blockout"
IMPORT_ROOT = "/Game/PenanceImported"
MATERIAL_ROOT = f"{IMPORT_ROOT}/Materials"


def sanitize_name(value):
    value = re.sub(r"[^A-Za-z0-9_]+", "_", str(value))
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "Unnamed"


def godot_to_unreal_location(vec):
    return unreal.Vector(-float(vec["z"]) * 100.0, float(vec["x"]) * 100.0, float(vec["y"]) * 100.0)


def godot_to_unreal_rotation(rot):
    # Good enough for the blockout import: preserves yaw and rough lean on simple primitives.
    return unreal.Rotator(float(rot["z"]), -float(rot["y"]), -float(rot["x"]))


def godot_color_to_linear(color):
    return unreal.LinearColor(
        float(color.get("r", 0.5)),
        float(color.get("g", 0.5)),
        float(color.get("b", 0.5)),
        float(color.get("a", 1.0)),
    )


def godot_color_to_unreal_color(color):
    return unreal.Color(
        int(max(0.0, min(1.0, float(color.get("r", 0.5)))) * 255.0),
        int(max(0.0, min(1.0, float(color.get("g", 0.5)))) * 255.0),
        int(max(0.0, min(1.0, float(color.get("b", 0.5)))) * 255.0),
        int(max(0.0, min(1.0, float(color.get("a", 1.0)))) * 255.0),
    )


def ensure_directory(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def load_json():
    if not EXPORT_PATH.exists():
        raise RuntimeError(f"Missing export JSON: {EXPORT_PATH}")
    return json.loads(EXPORT_PATH.read_text())


def create_or_get_material(material_data, cache):
    name = sanitize_name(material_data.get("name", "Blockout"))
    color = material_data.get("albedo", {})
    key = (
        name,
        round(float(color.get("r", 0.5)), 3),
        round(float(color.get("g", 0.5)), 3),
        round(float(color.get("b", 0.5)), 3),
        bool(material_data.get("emission_enabled", False)),
    )
    if key in cache:
        return cache[key]

    ensure_directory(MATERIAL_ROOT)
    asset_name = sanitize_name(f"M_{name}_{len(cache):03d}")
    asset_path = f"{MATERIAL_ROOT}/{asset_name}"

    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        existing = unreal.EditorAssetLibrary.load_asset(asset_path)
        if existing:
            cache[key] = existing
            return existing

    tools = unreal.AssetToolsHelpers.get_asset_tools()
    material = tools.create_asset(asset_name, MATERIAL_ROOT, unreal.Material, unreal.MaterialFactoryNew())
    material.set_editor_property("two_sided", True)

    base_expr = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -500, -120
    )
    base_expr.set_editor_property("constant", godot_color_to_linear(color))
    unreal.MaterialEditingLibrary.connect_material_property(
        base_expr, "", unreal.MaterialProperty.MP_BASE_COLOR
    )

    rough_expr = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -500, 100
    )
    rough_expr.set_editor_property("r", float(material_data.get("roughness", 0.75)))
    unreal.MaterialEditingLibrary.connect_material_property(
        rough_expr, "", unreal.MaterialProperty.MP_ROUGHNESS
    )

    metal_expr = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -500, 220
    )
    metal_expr.set_editor_property("r", float(material_data.get("metallic", 0.0)))
    unreal.MaterialEditingLibrary.connect_material_property(
        metal_expr, "", unreal.MaterialProperty.MP_METALLIC
    )

    if material_data.get("emission_enabled", False):
        emissive_expr = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionConstant3Vector, -250, -120
        )
        emissive_expr.set_editor_property("constant", godot_color_to_linear(material_data.get("emission", color)))
        unreal.MaterialEditingLibrary.connect_material_property(
            emissive_expr, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR
        )

    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    cache[key] = material
    return material


def clear_imported_actors():
    actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
    for actor in actors:
        if actor.get_actor_label().startswith("Penance_"):
            unreal.EditorLevelLibrary.destroy_actor(actor)


def set_label_and_folder(actor, label, folder):
    actor.set_actor_label(f"Penance_{sanitize_name(label)}")
    actor.set_folder_path(folder)


def spawn_static_mesh_actor(mesh_asset, name, location, rotation, scale, material, folder, collision):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, location, rotation)
    set_label_and_folder(actor, name, folder)
    actor.set_actor_scale3d(scale)
    component = actor.static_mesh_component
    component.set_static_mesh(mesh_asset)
    if material:
        component.set_material(0, material)
    actor.set_actor_enable_collision(collision)
    if hasattr(component, "set_collision_enabled"):
        component.set_collision_enabled(
            unreal.CollisionEnabled.QUERY_AND_PHYSICS if collision else unreal.CollisionEnabled.NO_COLLISION
        )
    return actor


def spawn_meshes(data, material_cache):
    cube_mesh = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube.Cube")
    cylinder_mesh = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cylinder.Cylinder")
    if not cube_mesh or not cylinder_mesh:
        raise RuntimeError("Could not load Unreal basic shape meshes.")

    for item in data.get("meshes", []):
        material = create_or_get_material(item.get("material", {}), material_cache)
        location = godot_to_unreal_location(item["position"])
        rotation = godot_to_unreal_rotation(item["rotation_degrees"])
        collision = bool(item.get("collision", False))

        if item["type"] == "box":
            size = item["shape"]["size"]
            scale = unreal.Vector(float(size["z"]), float(size["x"]), float(size["y"]))
            mesh = cube_mesh
        elif item["type"] == "cylinder":
            radius = float(item["shape"]["radius"])
            height = float(item["shape"]["height"])
            scale = unreal.Vector(radius * 2.0, radius * 2.0, height)
            mesh = cylinder_mesh
        else:
            continue

        folder = "PenanceImported/Geometry/HiddenAtStart" if not item.get("visible", True) else "PenanceImported/Geometry"
        actor = spawn_static_mesh_actor(mesh, item["name"], location, rotation, scale, material, folder, collision)
        actor.set_is_temporarily_hidden_in_editor(not item.get("visible", True))


def spawn_area_markers(data, material_cache):
    trigger_material = create_or_get_material(
        {
            "name": "Trigger_Marker",
            "albedo": {"r": 0.1, "g": 0.35, "b": 0.95, "a": 0.30},
            "roughness": 0.4,
            "metallic": 0.0,
            "emission_enabled": True,
            "emission": {"r": 0.1, "g": 0.35, "b": 0.95, "a": 1.0},
        },
        material_cache,
    )
    cube_mesh = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube.Cube")

    for area in data.get("areas", []):
        size = area["size"]
        actor = spawn_static_mesh_actor(
            cube_mesh,
            area["name"],
            godot_to_unreal_location(area["position"]),
            godot_to_unreal_rotation(area["rotation_degrees"]),
            unreal.Vector(float(size["z"]), float(size["x"]), float(size["y"])),
            trigger_material,
            "PenanceImported/EventAndInteractableMarkers",
            False,
        )
        actor.set_editor_property("is_spatially_loaded", True)
        if area.get("prompt"):
            actor.tags = [unreal.Name("Interactable"), unreal.Name(sanitize_name(area["prompt"]))]
        else:
            actor.tags = [unreal.Name("ScriptedEvent")]


def spawn_lights(data):
    for light in data.get("lights", []):
        location = godot_to_unreal_location(light["position"])
        rotation = godot_to_unreal_rotation(light["rotation_degrees"])
        light_type = light.get("type", "point")
        if light_type == "directional":
            actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.DirectionalLight, location, rotation)
            component = actor.get_component_by_class(unreal.DirectionalLightComponent)
        elif light_type == "spot":
            actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SpotLight, location, rotation)
            component = actor.get_component_by_class(unreal.SpotLightComponent)
            component.set_editor_property("attenuation_radius", float(light.get("range", 12.0)) * 100.0)
            component.set_editor_property("outer_cone_angle", float(light.get("angle", 45.0)))
        else:
            actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PointLight, location, rotation)
            component = actor.get_component_by_class(unreal.PointLightComponent)
            component.set_editor_property("attenuation_radius", float(light.get("range", 12.0)) * 100.0)

        set_label_and_folder(actor, light["name"], "PenanceImported/Lights")
        component.set_editor_property("light_color", godot_color_to_unreal_color(light.get("color", {})))
        component.set_editor_property("intensity", max(10.0, float(light.get("energy", 1.0)) * 950.0))
        actor.set_is_temporarily_hidden_in_editor(not light.get("visible", True))


def spawn_player_start(data):
    player = data.get("player_start") or {}
    if not player:
        return
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.PlayerStart,
        godot_to_unreal_location(player["position"]),
        godot_to_unreal_rotation(player["rotation_degrees"]),
    )
    set_label_and_folder(actor, "PlayerStart_FromGodot", "PenanceImported/Gameplay")


def add_import_note(data):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.TextRenderActor, unreal.Vector(0, 0, 260), unreal.Rotator(0, 180, 0))
    set_label_and_folder(actor, "ImportNotes", "PenanceImported/Notes")
    component = actor.get_component_by_class(unreal.TextRenderComponent)
    component.set_editor_property("text", "Penance Godot blockout import\nGeometry/lights/event markers only\nRebuild gameplay logic natively in Unreal")
    component.set_editor_property("world_size", 80.0)


def new_or_open_level():
    level_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(LEVEL_PATH):
        level_subsystem.load_level(LEVEL_PATH)
    else:
        level_subsystem.new_level(LEVEL_PATH)


def main():
    data = load_json()
    ensure_directory(IMPORT_ROOT)
    ensure_directory("/Game/Maps")
    new_or_open_level()
    clear_imported_actors()

    material_cache = {}
    spawn_meshes(data, material_cache)
    spawn_area_markers(data, material_cache)
    spawn_lights(data)
    spawn_player_start(data)
    add_import_note(data)

    unreal.EditorLevelLibrary.save_current_level()
    unreal.log(f"Imported Penance blockout: {len(data.get('meshes', []))} meshes, {len(data.get('areas', []))} areas, {len(data.get('lights', []))} lights")


if __name__ == "__main__":
    main()
