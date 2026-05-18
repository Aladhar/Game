"""
Penance Carrier v2 Blender Sculpt-Prep Kit

Run from the Godot project root:
  blender --background --python tools/blender/penance_carrier_v2_sculpt_prep.py

Input:
  assets/models/enemies/penance_carrier/penance_carrier_blockout_v1.glb

Outputs:
  assets/models/enemies/penance_carrier/blender_work/penance_carrier_v2_sculpt_prep.blend
  assets/models/enemies/penance_carrier/penance_carrier_v2_sculpt_prep.glb

This is a production-prep pass. It creates a clean Blender working file with
organized collections, AAA-oriented placeholder materials, sculpt modifiers,
guide markers, review lighting, and a Godot-ready GLB export.
"""

from __future__ import annotations

import math
from pathlib import Path

import bpy
from mathutils import Vector


def find_project_root() -> Path:
    try:
        script_path = Path(__file__).resolve()
    except NameError:
        script_path = Path.cwd().resolve()

    current = script_path.parent
    for _ in range(8):
        if (current / "project.godot").exists():
            return current
        current = current.parent

    return Path.cwd().resolve()


PROJECT_ROOT = find_project_root()
ASSET_ROOT = PROJECT_ROOT / "assets/models/enemies/penance_carrier"
INPUT_GLB = ASSET_ROOT / "penance_carrier_blockout_v1.glb"
WORK_DIR = ASSET_ROOT / "blender_work"
OUTPUT_BLEND = WORK_DIR / "penance_carrier_v2_sculpt_prep.blend"
OUTPUT_GLB = ASSET_ROOT / "penance_carrier_v2_sculpt_prep.glb"


MATERIAL_SPECS = {
    "PC_V2_soaked_cloth": ((0.055, 0.052, 0.048, 1.0), 0.86, 0.0),
    "PC_V2_aged_leather": ((0.22, 0.145, 0.08, 1.0), 0.72, 0.0),
    "PC_V2_weathered_wood": ((0.33, 0.26, 0.19, 1.0), 0.82, 0.0),
    "PC_V2_rusted_iron": ((0.26, 0.21, 0.18, 1.0), 0.76, 0.82),
    "PC_V2_corroded_brass": ((0.54, 0.38, 0.18, 1.0), 0.58, 1.0),
    "PC_V2_wax_candle": ((0.76, 0.62, 0.43, 1.0), 0.66, 0.0),
    "PC_V2_old_paper_photo": ((0.49, 0.40, 0.29, 1.0), 0.88, 0.0),
    "PC_V2_glass_lens": ((0.09, 0.12, 0.13, 0.45), 0.18, 0.0),
    "PC_V2_rope": ((0.18, 0.135, 0.085, 1.0), 0.9, 0.0),
    "PC_V2_black_void": ((0.006, 0.005, 0.004, 1.0), 0.98, 0.0),
}


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    for datablock in (
        bpy.data.meshes,
        bpy.data.materials,
        bpy.data.textures,
        bpy.data.images,
        bpy.data.collections,
    ):
        for item in list(datablock):
            if item.users == 0:
                datablock.remove(item)


def ensure_collection(name: str) -> bpy.types.Collection:
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
    return collection


def move_to_collection(obj: bpy.types.Object, collection_name: str) -> None:
    collection = ensure_collection(collection_name)
    for existing in list(obj.users_collection):
        existing.objects.unlink(obj)
    collection.objects.link(obj)


def create_materials() -> dict[str, bpy.types.Material]:
    materials: dict[str, bpy.types.Material] = {}
    for name, (base_color, roughness, metallic) in MATERIAL_SPECS.items():
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = base_color
            bsdf.inputs["Roughness"].default_value = roughness
            bsdf.inputs["Metallic"].default_value = metallic
            if name == "PC_V2_glass_lens":
                bsdf.inputs["Alpha"].default_value = 0.45
                mat.blend_method = "BLEND"
                if hasattr(mat, "use_screen_refraction"):
                    mat.use_screen_refraction = True
            if name == "PC_V2_wax_candle":
                if "Emission Color" in bsdf.inputs:
                    bsdf.inputs["Emission Color"].default_value = (1.0, 0.56, 0.22, 1.0)
                if "Emission Strength" in bsdf.inputs:
                    bsdf.inputs["Emission Strength"].default_value = 0.18
        materials[name] = mat
    return materials


def object_name(obj: bpy.types.Object) -> str:
    return f"{obj.name} {getattr(obj.data, 'name', '')}".lower()


def has_any(obj: bpy.types.Object, words: tuple[str, ...]) -> bool:
    name = object_name(obj)
    return any(word in name for word in words)


def choose_material(obj: bpy.types.Object, materials: dict[str, bpy.types.Material]) -> bpy.types.Material:
    if has_any(obj, ("cloth", "robe", "veil", "rag", "wrap", "bandage", "body", "leg", "arm")):
        return materials["PC_V2_soaked_cloth"]
    if has_any(obj, ("leather", "strap", "belt")):
        return materials["PC_V2_aged_leather"]
    if has_any(obj, ("wood", "plank", "shrine", "house", "roof", "door")):
        return materials["PC_V2_weathered_wood"]
    if has_any(obj, ("chain", "iron", "rust", "nail", "hook", "wire")):
        return materials["PC_V2_rusted_iron"]
    if has_any(obj, ("bell", "brass", "clock", "key", "relic", "speaker", "radio")):
        return materials["PC_V2_corroded_brass"]
    if has_any(obj, ("candle", "wax", "flame")):
        return materials["PC_V2_wax_candle"]
    if has_any(obj, ("paper", "photo", "cassette", "label")):
        return materials["PC_V2_old_paper_photo"]
    if has_any(obj, ("glass", "lens")):
        return materials["PC_V2_glass_lens"]
    if has_any(obj, ("rope", "cord", "twine")):
        return materials["PC_V2_rope"]
    if has_any(obj, ("mask", "face", "void", "hole")):
        return materials["PC_V2_black_void"]
    return materials["PC_V2_weathered_wood"]


def choose_collection(obj: bpy.types.Object) -> str:
    if has_any(obj, ("body", "arm", "leg", "foot", "hand", "cloth", "robe", "veil", "mask")):
        return "PC_V2_01_body_cloth_mask"
    if has_any(obj, ("house", "shrine", "roof", "wood", "plank", "door")):
        return "PC_V2_02_back_shrine"
    if has_any(obj, ("bell", "chain", "rope", "cord", "hook", "key")):
        return "PC_V2_03_hanging_relics"
    if has_any(obj, ("radio", "speaker", "clock", "cassette", "photo", "paper", "lens")):
        return "PC_V2_04_sound_relics"
    if has_any(obj, ("candle", "wax", "flame", "light")):
        return "PC_V2_05_candles_lights"
    return "PC_V2_99_uncategorized"


def add_modifier_if_missing(obj: bpy.types.Object, name: str, mod_type: str):
    for mod in obj.modifiers:
        if mod.name == name:
            return mod
    return obj.modifiers.new(name=name, type=mod_type)


def shade_smooth(obj: bpy.types.Object) -> None:
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    try:
        bpy.ops.object.shade_smooth()
    except Exception:
        pass
    obj.select_set(False)


def add_weighted_normals(obj: bpy.types.Object) -> None:
    mod = add_modifier_if_missing(obj, "V2_weighted_normals", "WEIGHTED_NORMAL")
    mod.keep_sharp = True
    mod.weight = 55


def add_bevel(obj: bpy.types.Object, amount: float, segments: int) -> None:
    mod = add_modifier_if_missing(obj, "V2_soft_bevel_edges", "BEVEL")
    mod.width = amount
    mod.segments = segments
    mod.profile = 0.45


def add_noise_displacement(obj: bpy.types.Object, name: str, strength: float, size: float) -> None:
    tex = bpy.data.textures.new(f"{obj.name}_{name}_noise", type="VORONOI")
    tex.noise_scale = size
    if hasattr(tex, "intensity"):
        tex.intensity = 0.34

    mod = add_modifier_if_missing(obj, name, "DISPLACE")
    mod.strength = strength
    mod.texture = tex


def prep_mesh_objects(materials: dict[str, bpy.types.Material]) -> None:
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue

        obj.data.materials.clear()
        obj.data.materials.append(choose_material(obj, materials))
        move_to_collection(obj, choose_collection(obj))
        shade_smooth(obj)
        add_weighted_normals(obj)

        if has_any(obj, ("wood", "plank", "shrine", "house", "roof", "radio", "clock", "speaker", "bell")):
            add_bevel(obj, 0.012, 2)
        if has_any(obj, ("cloth", "robe", "veil", "rag", "wrap", "bandage")):
            add_noise_displacement(obj, "V2_cloth_micro_warp", 0.006, 1.25)
        if has_any(obj, ("wood", "plank", "roof", "door")):
            add_noise_displacement(obj, "V2_wood_grain_breakup", 0.004, 0.75)
        if has_any(obj, ("bell", "chain", "iron", "brass", "radio", "speaker", "clock")):
            add_noise_displacement(obj, "V2_corrosion_breakup", 0.0035, 0.42)


def import_model() -> None:
    if not INPUT_GLB.exists():
        raise FileNotFoundError(f"Missing input GLB: {INPUT_GLB}")
    bpy.ops.import_scene.gltf(filepath=str(INPUT_GLB))


def recenter_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        return

    world_corners = [
        obj.matrix_world @ Vector(corner)
        for obj in meshes
        for corner in obj.bound_box
    ]

    min_x = min(corner.x for corner in world_corners)
    max_x = max(corner.x for corner in world_corners)
    min_y = min(corner.y for corner in world_corners)
    max_y = max(corner.y for corner in world_corners)
    min_z = min(corner.z for corner in world_corners)

    center_x = (min_x + max_x) * 0.5
    center_y = (min_y + max_y) * 0.5
    for obj in meshes:
        obj.location.x -= center_x
        obj.location.y -= center_y
        obj.location.z -= min_z


def add_guide_marker(name: str, location: tuple[float, float, float], color: tuple[float, float, float, float]) -> None:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.055, location=location)
    marker = bpy.context.object
    marker.name = name
    mat = bpy.data.materials.new(f"{name}_mat")
    mat.diffuse_color = color
    marker.data.materials.append(mat)
    move_to_collection(marker, "PC_V2_90_sculpt_guides")


def add_text_label(name: str, text: str, location: tuple[float, float, float]) -> None:
    bpy.ops.object.text_add(location=location, rotation=(math.radians(72), 0.0, 0.0))
    label = bpy.context.object
    label.name = name
    label.data.body = text
    label.data.align_x = "CENTER"
    label.data.size = 0.13
    move_to_collection(label, "PC_V2_90_sculpt_guides")


def add_sculpt_guides() -> None:
    add_guide_marker("GUIDE_mask_void_target", (0.0, -0.72, 2.72), (0.02, 0.02, 0.02, 1.0))
    add_guide_marker("GUIDE_main_bell_weight", (-0.95, -0.3, 0.62), (0.8, 0.52, 0.18, 1.0))
    add_guide_marker("GUIDE_radio_weak_point", (-0.62, -0.56, 3.16), (0.34, 0.52, 0.78, 1.0))
    add_guide_marker("GUIDE_candle_cluster", (0.22, -0.64, 3.2), (1.0, 0.45, 0.14, 1.0))
    add_text_label("LABEL_V2_texture_budget", "LOD0: 8K hero maps; ship with 4K/2K fallback", (0.0, -1.35, 3.9))
    add_text_label("LABEL_V2_manual_sculpt", "manual sculpt: cloth folds, cracked planks, bell dents, rope tension", (0.0, -1.35, 3.65))


def add_review_lighting() -> None:
    bpy.ops.object.light_add(type="AREA", location=(0.0, -4.5, 5.0))
    key = bpy.context.object
    key.name = "PC_V2_review_key_light"
    key.data.energy = 650
    key.data.size = 5.0

    bpy.ops.object.light_add(type="POINT", location=(-1.0, -0.9, 2.85))
    candle = bpy.context.object
    candle.name = "PC_V2_candle_glow_reference"
    candle.data.energy = 65
    candle.data.color = (1.0, 0.48, 0.18)

    bpy.ops.object.camera_add(location=(3.2, -6.0, 2.8), rotation=(math.radians(67), 0.0, math.radians(28)))
    bpy.context.scene.camera = bpy.context.object


def set_units_and_origin() -> None:
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0
    empty = bpy.data.objects.new("PC_V2_export_root_origin_grounded", None)
    bpy.context.scene.collection.objects.link(empty)


def export_glb() -> None:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_BLEND))
    bpy.ops.export_scene.gltf(
        filepath=str(OUTPUT_GLB),
        export_format="GLB",
        export_apply=True,
        export_yup=True,
        export_materials="EXPORT",
    )


def main() -> None:
    print("Penance Carrier v2 sculpt-prep starting...")
    clear_scene()
    import_model()
    recenter_scene()
    materials = create_materials()
    prep_mesh_objects(materials)
    add_sculpt_guides()
    add_review_lighting()
    set_units_and_origin()
    export_glb()
    print("Saved blend:", OUTPUT_BLEND)
    print("Exported GLB:", OUTPUT_GLB)
    print("Next: manual sculpt, UV unwrap, bake normal/AO/curvature, then texture in ArmorPaint or Material Maker.")


if __name__ == "__main__":
    main()
