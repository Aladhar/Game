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
FIXED_PROP_FOLDER = "PenanceImported/FixedSceneProps"
PENANCE_CARRIER_MESH_ROOT = (
    "/Game/PenanceAssets/Enemies/PenanceCarrier/"
    "penance_carrier_end_goal_v21_multi_region_reference_baseline/StaticMeshes"
)

PLACEHOLDER_MESH_NAMES_TO_REPLACE = {
    "FirstHouse_LivingRoom_BlockoutSofa",
    "FirstHouse_Table_Candles",
    "FirstHouse_TableFocus_ChairSilhouette",
    "FirstHouse_TableLamp_Base",
    "FirstHouse_TableLamp_Shade",
    "FirstHouse_Clue_BlankFamilyPhoto_Inspectable",
    "FirstHouse_Photo_ContrastBacking",
    "Penance_HoodedWetCloth_4mTall",
    "Penance_CrushedDoorMask",
    "Penance_BackDoorPlank",
    "FirstHousePenance_WetClothBody",
    "FirstHousePenance_DoorMask_ReadSecond",
    "TunnelPenance_WetClothBody",
    "TunnelPenance_DoorMask",
}

PLACEHOLDER_MESH_PREFIXES_TO_REPLACE = (
    "Penance_RustedChains_",
    "Penance_CandleRelics_",
    "FirstHousePenance_BarelyVisibleChains_",
    "TunnelPenance_Chains_",
)


def sanitize_name(value):
    value = re.sub(r"[^A-Za-z0-9_]+", "_", str(value))
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "Unnamed"


def godot_to_unreal_location(vec):
    return unreal.Vector(-float(vec["z"]) * 100.0, float(vec["x"]) * 100.0, float(vec["y"]) * 100.0)


def godot_to_unreal_rotation(rot):
    # Good enough for the blockout import: preserves yaw and rough lean on simple primitives.
    return unreal.Rotator(float(rot["z"]), -float(rot["y"]), -float(rot["x"]))


def godot_vec(x, y, z):
    return {"x": x, "y": y, "z": z}


def rotated_godot_offset(offset, yaw_degrees):
    yaw = math.radians(yaw_degrees)
    x = float(offset["x"])
    z = float(offset["z"])
    return {
        "x": x * math.cos(yaw) + z * math.sin(yaw),
        "y": float(offset["y"]),
        "z": -x * math.sin(yaw) + z * math.cos(yaw),
    }


def add_godot_vec(a, b):
    return {
        "x": float(a["x"]) + float(b["x"]),
        "y": float(a["y"]) + float(b["y"]),
        "z": float(a["z"]) + float(b["z"]),
    }


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


def is_replaced_placeholder(item):
    name = item.get("name", "")
    return name in PLACEHOLDER_MESH_NAMES_TO_REPLACE or any(
        name.startswith(prefix) for prefix in PLACEHOLDER_MESH_PREFIXES_TO_REPLACE
    )


def spawn_meshes(data, material_cache):
    cube_mesh = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube.Cube")
    cylinder_mesh = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cylinder.Cylinder")
    if not cube_mesh or not cylinder_mesh:
        raise RuntimeError("Could not load Unreal basic shape meshes.")

    for item in data.get("meshes", []):
        if is_replaced_placeholder(item):
            continue

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


def fixed_material(material_cache, name, color, roughness=0.85, metallic=0.0, emission=None, emission_energy=0.0):
    return create_or_get_material(
        {
            "name": name,
            "albedo": {"r": color[0], "g": color[1], "b": color[2], "a": color[3] if len(color) > 3 else 1.0},
            "roughness": roughness,
            "metallic": metallic,
            "emission_enabled": emission is not None,
            "emission": {
                "r": emission[0] if emission else 0.0,
                "g": emission[1] if emission else 0.0,
                "b": emission[2] if emission else 0.0,
                "a": emission[3] if emission and len(emission) > 3 else 1.0,
            },
            "emission_energy": emission_energy,
        },
        material_cache,
    )


def spawn_fixed_box(cube_mesh, material_cache, name, origin, offset, size, material_name, yaw=0.0, collision=False, folder=FIXED_PROP_FOLDER):
    material = fixed_material_for_name(material_cache, material_name)
    offset_rotated = rotated_godot_offset(offset, yaw)
    position = add_godot_vec(origin, offset_rotated)
    scale = unreal.Vector(float(size["z"]), float(size["x"]), float(size["y"]))
    actor = spawn_static_mesh_actor(
        cube_mesh,
        name,
        godot_to_unreal_location(position),
        godot_to_unreal_rotation(godot_vec(0.0, yaw, 0.0)),
        scale,
        material,
        folder,
        collision,
    )
    return actor


def spawn_fixed_cylinder(cylinder_mesh, material_cache, name, origin, offset, radius, height, material_name, yaw=0.0, collision=False, folder=FIXED_PROP_FOLDER):
    material = fixed_material_for_name(material_cache, material_name)
    offset_rotated = rotated_godot_offset(offset, yaw)
    position = add_godot_vec(origin, offset_rotated)
    actor = spawn_static_mesh_actor(
        cylinder_mesh,
        name,
        godot_to_unreal_location(position),
        godot_to_unreal_rotation(godot_vec(0.0, yaw, 0.0)),
        unreal.Vector(radius * 2.0, radius * 2.0, height),
        material,
        folder,
        collision,
    )
    return actor


def fixed_material_for_name(material_cache, material_name):
    if material_name == "wet_cloth":
        return fixed_material(material_cache, "Fixed_Wet_Rotten_Cloth", (0.035, 0.045, 0.05, 1.0), 0.97)
    if material_name == "rotten_wood":
        return fixed_material(material_cache, "Fixed_Rotten_Furniture_Wood", (0.13, 0.08, 0.045, 1.0), 0.94)
    if material_name == "dark":
        return fixed_material(material_cache, "Fixed_Deep_Black_Gap", (0.004, 0.005, 0.006, 1.0), 0.96)
    if material_name == "paper":
        return fixed_material(material_cache, "Fixed_Yellowed_Photo_Paper", (0.44, 0.36, 0.24, 1.0), 0.88)
    if material_name == "metal":
        return fixed_material(material_cache, "Fixed_Rusted_Metal", (0.19, 0.075, 0.03, 1.0), 0.84, 0.35)
    if material_name == "warm":
        return fixed_material(
            material_cache,
            "Fixed_Warm_Lamp_Glow",
            (0.5, 0.35, 0.16, 1.0),
            0.45,
            0.0,
            (1.0, 0.55, 0.18, 1.0),
            0.8,
        )
    return fixed_material(material_cache, "Fixed_Neutral_Prop", (0.45, 0.45, 0.45, 1.0), 0.8)


def find_mesh_entry(data, name):
    for item in data.get("meshes", []):
        if item.get("name") == name:
            return item
    return None


def spawn_fixed_couch(cube_mesh, material_cache, data):
    source = find_mesh_entry(data, "FirstHouse_LivingRoom_BlockoutSofa")
    origin = source["position"] if source else godot_vec(21.8, 0.55, 34.6)
    floor_origin = godot_vec(origin["x"], 0.0, origin["z"])
    yaw = source["rotation_degrees"]["y"] if source else 0.0

    spawn_fixed_box(cube_mesh, material_cache, "FirstHouse_Couch_SaggingSeat", floor_origin, godot_vec(0, 0.48, 0), godot_vec(3.25, 0.42, 1.05), "wet_cloth", yaw, True)
    spawn_fixed_box(cube_mesh, material_cache, "FirstHouse_Couch_TallBack", floor_origin, godot_vec(0, 0.98, 0.46), godot_vec(3.35, 1.35, 0.28), "wet_cloth", yaw, True)
    spawn_fixed_box(cube_mesh, material_cache, "FirstHouse_Couch_LeftArm", floor_origin, godot_vec(-1.82, 0.78, 0.02), godot_vec(0.32, 0.96, 1.2), "wet_cloth", yaw, True)
    spawn_fixed_box(cube_mesh, material_cache, "FirstHouse_Couch_RightArm", floor_origin, godot_vec(1.82, 0.72, 0.0), godot_vec(0.32, 0.86, 1.12), "wet_cloth", yaw, True)
    spawn_fixed_box(cube_mesh, material_cache, "FirstHouse_Couch_LeftSplitCushion", floor_origin, godot_vec(-0.65, 0.76, -0.1), godot_vec(1.15, 0.10, 0.88), "wet_cloth", yaw)
    spawn_fixed_box(cube_mesh, material_cache, "FirstHouse_Couch_RightSplitCushion", floor_origin, godot_vec(0.64, 0.73, -0.08), godot_vec(1.15, 0.10, 0.82), "wet_cloth", yaw)
    spawn_fixed_box(cube_mesh, material_cache, "FirstHouse_Couch_LeftFrontWoodFoot", floor_origin, godot_vec(-1.25, 0.18, -0.42), godot_vec(0.16, 0.34, 0.16), "rotten_wood", yaw)
    spawn_fixed_box(cube_mesh, material_cache, "FirstHouse_Couch_RightFrontWoodFoot", floor_origin, godot_vec(1.25, 0.18, -0.42), godot_vec(0.16, 0.34, 0.16), "rotten_wood", yaw)


def spawn_fixed_table(cube_mesh, material_cache, data):
    source = find_mesh_entry(data, "FirstHouse_Table_Candles")
    origin = source["position"] if source else godot_vec(25.75, 0.55, 36.65)
    floor_origin = godot_vec(origin["x"], 0.0, origin["z"])
    yaw = source["rotation_degrees"]["y"] if source else 0.0

    spawn_fixed_box(cube_mesh, material_cache, "FirstHouse_Table_ThickTop", floor_origin, godot_vec(0, 0.78, 0), godot_vec(1.55, 0.18, 1.08), "rotten_wood", yaw, True)
    spawn_fixed_box(cube_mesh, material_cache, "FirstHouse_Table_LowerShelf", floor_origin, godot_vec(0, 0.42, 0), godot_vec(1.36, 0.10, 0.9), "rotten_wood", yaw)
    for x in (-0.62, 0.62):
        for z in (-0.42, 0.42):
            spawn_fixed_box(cube_mesh, material_cache, f"FirstHouse_Table_Leg_{x}_{z}", floor_origin, godot_vec(x, 0.38, z), godot_vec(0.16, 0.72, 0.16), "rotten_wood", yaw, True)
    spawn_fixed_box(cube_mesh, material_cache, "FirstHouse_Table_DarkDrawerFace", floor_origin, godot_vec(0, 0.66, -0.56), godot_vec(1.08, 0.26, 0.045), "dark", yaw)


def spawn_fixed_chair(cube_mesh, material_cache, name, origin, yaw):
    spawn_fixed_box(cube_mesh, material_cache, name + "_Seat", origin, godot_vec(0, 0.52, 0), godot_vec(0.78, 0.16, 0.74), "rotten_wood", yaw, True)
    spawn_fixed_box(cube_mesh, material_cache, name + "_BackPanel", origin, godot_vec(0, 1.15, 0.34), godot_vec(0.82, 1.25, 0.12), "rotten_wood", yaw, True)
    spawn_fixed_box(cube_mesh, material_cache, name + "_TopRail", origin, godot_vec(0, 1.72, 0.28), godot_vec(0.96, 0.16, 0.16), "rotten_wood", yaw)
    for x in (-0.3, 0.3):
        for z in (-0.26, 0.26):
            spawn_fixed_box(cube_mesh, material_cache, f"{name}_Leg_{x}_{z}", origin, godot_vec(x, 0.26, z), godot_vec(0.11, 0.52, 0.11), "rotten_wood", yaw, True)
    spawn_fixed_box(cube_mesh, material_cache, name + "_BrokenCrossBrace", origin, godot_vec(0, 0.38, -0.34), godot_vec(0.72, 0.08, 0.08), "rotten_wood", yaw)


def spawn_fixed_first_house_small_props(cube_mesh, material_cache, data):
    chair = find_mesh_entry(data, "FirstHouse_TableFocus_ChairSilhouette")
    chair_pos = chair["position"] if chair else godot_vec(27.1, 0.65, 36.8)
    chair_yaw = chair["rotation_degrees"]["y"] if chair else -17.2
    spawn_fixed_chair(cube_mesh, material_cache, "FirstHouse_RightDiningChair", godot_vec(chair_pos["x"], 0.0, chair_pos["z"]), chair_yaw)
    spawn_fixed_chair(cube_mesh, material_cache, "FirstHouse_PulledOutDiningChair", godot_vec(25.25, 0.0, 37.92), 172.0)

    lamp_origin = godot_vec(25.05, 0.0, 36.88)
    spawn_fixed_box(cube_mesh, material_cache, "FirstHouse_TableLamp_MetalBase", lamp_origin, godot_vec(0, 0.93, 0), godot_vec(0.42, 0.08, 0.42), "metal")
    spawn_fixed_box(cube_mesh, material_cache, "FirstHouse_TableLamp_ThinStem", lamp_origin, godot_vec(0, 1.2, 0), godot_vec(0.12, 0.55, 0.12), "metal")
    spawn_fixed_box(cube_mesh, material_cache, "FirstHouse_TableLamp_TornWarmShade", lamp_origin, godot_vec(0, 1.52, 0), godot_vec(0.72, 0.34, 0.72), "warm")
    spawn_fixed_box(cube_mesh, material_cache, "FirstHouse_TableLamp_MissingShadePanel", lamp_origin, godot_vec(0, 1.51, -0.38), godot_vec(0.42, 0.24, 0.04), "dark")

    photo = find_mesh_entry(data, "FirstHouse_Clue_BlankFamilyPhoto_Inspectable")
    photo_pos = photo["position"] if photo else godot_vec(25.75, 1.04, 36.68)
    photo_yaw = photo["rotation_degrees"]["y"] if photo else 10.3
    photo_origin = godot_vec(photo_pos["x"], 0.0, photo_pos["z"])
    spawn_fixed_box(cube_mesh, material_cache, "FirstHouse_BlankFamilyPhoto_DarkBacking", photo_origin, godot_vec(0, 1.005, 0), godot_vec(1.12, 0.035, 0.78), "dark", photo_yaw)
    spawn_fixed_box(cube_mesh, material_cache, "FirstHouse_BlankFamilyPhoto_Paper", photo_origin, godot_vec(0, 1.045, 0), godot_vec(0.92, 0.045, 0.62), "paper", photo_yaw)
    spawn_fixed_box(cube_mesh, material_cache, "FirstHouse_BlankFamilyPhoto_ScrapedFaceVoid", photo_origin, godot_vec(0.22, 1.076, -0.04), godot_vec(0.18, 0.018, 0.24), "dark", photo_yaw)
    spawn_fixed_box(cube_mesh, material_cache, "FirstHouse_BlankFamilyPhoto_FrameTop", photo_origin, godot_vec(0, 1.09, 0.35), godot_vec(1.04, 0.035, 0.05), "rotten_wood", photo_yaw)
    spawn_fixed_box(cube_mesh, material_cache, "FirstHouse_BlankFamilyPhoto_FrameBottom", photo_origin, godot_vec(0, 1.09, -0.35), godot_vec(1.04, 0.035, 0.05), "rotten_wood", photo_yaw)

    note_origin = godot_vec(26.14, 0.0, 36.18)
    note_yaw = -25.0
    spawn_fixed_box(cube_mesh, material_cache, "FirstHouse_Table_HandwrittenNote_Paper", note_origin, godot_vec(0, 1.02, 0), godot_vec(0.62, 0.025, 0.46), "paper", note_yaw)
    spawn_fixed_box(cube_mesh, material_cache, "FirstHouse_Table_HandwrittenNote_FoldedCorner", note_origin, godot_vec(0.24, 1.045, 0.16), godot_vec(0.16, 0.022, 0.13), "rotten_wood", note_yaw)
    for index in range(4):
        spawn_fixed_box(
            cube_mesh,
            material_cache,
            f"FirstHouse_Table_HandwrittenNote_InkLine_{index}",
            note_origin,
            godot_vec(-0.04, 1.056 + index * 0.002, -0.14 + index * 0.085),
            godot_vec(0.42 - index * 0.045, 0.012, 0.018),
            "dark",
            note_yaw,
        )


def spawn_penance_static_meshes(base_name, base_position, yaw, scale, hidden):
    asset_paths = list(unreal.EditorAssetLibrary.list_assets(PENANCE_CARRIER_MESH_ROOT, recursive=True, include_folder=False))
    static_mesh_paths = [path for path in asset_paths if "/StaticMeshes/" in path]
    if not static_mesh_paths:
        return 0

    count = 0
    for asset_path in static_mesh_paths:
        mesh = unreal.EditorAssetLibrary.load_asset(asset_path)
        if not isinstance(mesh, unreal.StaticMesh):
            continue
        actor = spawn_static_mesh_actor(
            mesh,
            f"{base_name}_{asset_path.rsplit('/', 1)[-1]}",
            godot_to_unreal_location(base_position),
            godot_to_unreal_rotation(godot_vec(0.0, yaw, 0.0)),
            unreal.Vector(scale, scale, scale),
            None,
            f"{FIXED_PROP_FOLDER}/PenanceCarrier",
            False,
        )
        actor.set_is_temporarily_hidden_in_editor(hidden)
        count += 1
    return count


def spawn_penance_proxy(cube_mesh, cylinder_mesh, material_cache, base_name, origin, yaw, scale=1.0, hidden=False):
    folder = f"{FIXED_PROP_FOLDER}/PenanceProxy"
    parts = [
        ("HunchedWetClothTorso", godot_vec(0, 2.05 * scale, 0), godot_vec(1.25 * scale, 3.45 * scale, 0.7 * scale), "wet_cloth"),
        ("LeftShoulderRag", godot_vec(-0.58 * scale, 3.25 * scale, -0.02 * scale), godot_vec(0.62 * scale, 1.35 * scale, 0.48 * scale), "wet_cloth"),
        ("RightShoulderRag", godot_vec(0.58 * scale, 3.1 * scale, -0.02 * scale), godot_vec(0.58 * scale, 1.55 * scale, 0.52 * scale), "wet_cloth"),
        ("CrushedDoorMaskCenter", godot_vec(0, 4.08 * scale, -0.47 * scale), godot_vec(0.96 * scale, 1.32 * scale, 0.13 * scale), "rotten_wood"),
        ("BlackFaceGap", godot_vec(0.03 * scale, 4.08 * scale, -0.61 * scale), godot_vec(0.42 * scale, 0.62 * scale, 0.04 * scale), "dark"),
        ("BackShrineDoor", godot_vec(0, 2.75 * scale, 0.58 * scale), godot_vec(1.28 * scale, 2.8 * scale, 0.16 * scale), "rotten_wood"),
        ("DraggingLeftLeg", godot_vec(-0.34 * scale, 0.75 * scale, 0.02 * scale), godot_vec(0.34 * scale, 1.45 * scale, 0.38 * scale), "wet_cloth"),
        ("DraggingRightLeg", godot_vec(0.34 * scale, 0.68 * scale, 0.04 * scale), godot_vec(0.32 * scale, 1.28 * scale, 0.34 * scale), "wet_cloth"),
    ]
    for suffix, offset, size, material_name in parts:
        actor = spawn_fixed_box(cube_mesh, material_cache, f"{base_name}_{suffix}", origin, offset, size, material_name, yaw, False, folder)
        actor.set_is_temporarily_hidden_in_editor(hidden)
    for x in (-0.32, 0.32):
        actor = spawn_fixed_box(cube_mesh, material_cache, f"{base_name}_FrontRustedChain_{x}", origin, godot_vec(x * scale, 2.65 * scale, -0.58 * scale), godot_vec(0.08 * scale, 2.0 * scale, 0.08 * scale), "metal", yaw, False, folder)
        actor.set_is_temporarily_hidden_in_editor(hidden)
    bell = spawn_fixed_cylinder(cylinder_mesh, material_cache, f"{base_name}_DeadBell", origin, godot_vec(-0.68 * scale, 1.0 * scale, -0.52 * scale), 0.18 * scale, 0.34 * scale, "metal", yaw, False, folder)
    bell.set_is_temporarily_hidden_in_editor(hidden)


def spawn_fixed_penance_appearances(cube_mesh, cylinder_mesh, material_cache):
    appearances = [
        ("Penance_FarLightning_AuthoredCarrier", godot_vec(4.0, 0.0, -88.0), 0.0, 1.0, False),
        ("Penance_FirstHouseDoorway_AuthoredCarrier", godot_vec(24.0, 0.0, 37.55), 180.0, 0.88, False),
        ("Penance_TunnelPressure_AuthoredCarrier", godot_vec(-34.0, -4.0, -9.0), 0.0, 0.92, False),
    ]
    for base_name, position, yaw, scale, hidden in appearances:
        spawned = spawn_penance_static_meshes(base_name, position, yaw, scale, hidden)
        if spawned == 0:
            spawn_penance_proxy(cube_mesh, cylinder_mesh, material_cache, base_name + "_Proxy", position, yaw, scale, hidden)
        else:
            spawn_penance_proxy(cube_mesh, cylinder_mesh, material_cache, base_name + "_ReadableProxy", position, yaw, scale, hidden)


def spawn_fixed_scene_props(data, material_cache):
    cube_mesh = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube.Cube")
    cylinder_mesh = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cylinder.Cylinder")
    if not cube_mesh or not cylinder_mesh:
        raise RuntimeError("Could not load Unreal basic shape meshes for fixed props.")

    spawn_fixed_couch(cube_mesh, material_cache, data)
    spawn_fixed_table(cube_mesh, material_cache, data)
    spawn_fixed_first_house_small_props(cube_mesh, material_cache, data)
    spawn_fixed_penance_appearances(cube_mesh, cylinder_mesh, material_cache)


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
    spawn_fixed_scene_props(data, material_cache)
    spawn_area_markers(data, material_cache)
    spawn_lights(data)
    spawn_player_start(data)
    add_import_note(data)

    unreal.EditorLevelLibrary.save_current_level()
    unreal.log(f"Imported Penance blockout: {len(data.get('meshes', []))} meshes, {len(data.get('areas', []))} areas, {len(data.get('lights', []))} lights")


if __name__ == "__main__":
    main()
