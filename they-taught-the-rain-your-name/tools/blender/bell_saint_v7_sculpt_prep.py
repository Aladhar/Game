"""
Bell Saint v7 Blender Sculpt-Prep Kit

Run this inside Blender.

Expected input:
  assets/models/enemies/bell_saint/bell_saint_v6_centered_artpass.glb

Output:
  assets/models/enemies/bell_saint/blender_work/bell_saint_v7_sculpt_prep.blend
  assets/models/enemies/bell_saint/bell_saint_v7_sculpt_prep.glb

What this does:
- imports the v6 Bell Saint GLB
- recenters and normalizes object origins
- sorts objects into collections
- creates cleaner AAA-oriented material placeholders
- adds bevel modifiers to hard-surface objects
- adds weighted normals
- adds sculpt/displacement modifiers to cloth and bell pieces
- adds visual guide empties for weak points
- adds basic lights/camera for review
- exports a Godot-ready GLB

This is a sculpt-prep pass, not the final AAA sculpt.
After running it, manually sculpt cloth folds/dents in Blender, then retopo/UV/bake.
"""

from __future__ import annotations

import math
from pathlib import Path

import bpy
from mathutils import Vector


# -----------------------------
# PATH SETUP
# -----------------------------

def find_project_root() -> Path:
    """Find the Godot project root by walking upward from this script."""
    try:
        script_path = Path(__file__).resolve()
    except NameError:
        script_path = Path.cwd().resolve()

    current = script_path.parent
    for _ in range(8):
        if (current / "project.godot").exists():
            return current
        current = current.parent

    # Fallback: assume script was launched from project root.
    return Path.cwd().resolve()


PROJECT_ROOT = find_project_root()

INPUT_GLB = PROJECT_ROOT / "assets/models/enemies/bell_saint/bell_saint_v6_centered_artpass.glb"
WORK_DIR = PROJECT_ROOT / "assets/models/enemies/bell_saint/blender_work"
OUTPUT_BLEND = WORK_DIR / "bell_saint_v7_sculpt_prep.blend"
OUTPUT_GLB = PROJECT_ROOT / "assets/models/enemies/bell_saint/bell_saint_v7_sculpt_prep.glb"


# -----------------------------
# CLEANUP / HELPERS
# -----------------------------

def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    # Clean orphaned data to avoid material buildup.
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
    if name in bpy.data.collections:
        return bpy.data.collections[name]

    collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(collection)
    return collection


def move_to_collection(obj: bpy.types.Object, collection_name: str) -> None:
    collection = ensure_collection(collection_name)

    for col in list(obj.users_collection):
        col.objects.unlink(obj)

    collection.objects.link(obj)


def create_mat(
    name: str,
    base_color: tuple[float, float, float, float],
    roughness: float,
    metallic: float = 0.0,
    emission: tuple[float, float, float, float] | None = None,
    emission_strength: float = 0.0,
) -> bpy.types.Material:
    if name in bpy.data.materials:
        return bpy.data.materials[name]

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True

    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = base_color
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic

        if emission is not None:
            # Blender 4.x inputs
            if "Emission Color" in bsdf.inputs:
                bsdf.inputs["Emission Color"].default_value = emission
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = emission_strength

    return mat


def assign_material_by_name(obj: bpy.types.Object, material: bpy.types.Material) -> None:
    if obj.type != "MESH":
        return

    obj.data.materials.clear()
    obj.data.materials.append(material)


def add_modifier_if_missing(obj: bpy.types.Object, name: str, mod_type: str):
    for mod in obj.modifiers:
        if mod.name == name:
            return mod
    return obj.modifiers.new(name=name, type=mod_type)


def add_weighted_normals(obj: bpy.types.Object) -> None:
    if obj.type != "MESH":
        return

    mod = add_modifier_if_missing(obj, "AAA_weighted_normals", "WEIGHTED_NORMAL")
    mod.keep_sharp = True
    mod.weight = 50


def add_bevel(obj: bpy.types.Object, amount: float, segments: int) -> None:
    if obj.type != "MESH":
        return

    mod = add_modifier_if_missing(obj, "AAA_soft_bevel_edges", "BEVEL")
    mod.width = amount
    mod.segments = segments
    mod.affect = "EDGES"
    mod.profile = 0.45


def add_displace_noise(obj: bpy.types.Object, name: str, strength: float, size: float, material_sensitive=False) -> None:
    if obj.type != "MESH":
        return

    tex_name = f"{obj.name}_{name}_noise"
    tex = bpy.data.textures.new(tex_name, type="VORONOI" if material_sensitive else "CLOUDS")
    tex.noise_scale = size
    if hasattr(tex, "intensity"):
        tex.intensity = 0.35

    mod = add_modifier_if_missing(obj, name, "DISPLACE")
    mod.strength = strength
    mod.texture = tex


def add_subdivision(obj: bpy.types.Object, levels: int, render_levels: int) -> None:
    if obj.type != "MESH":
        return

    mod = add_modifier_if_missing(obj, "SCULPT_PREP_subdivision_preview", "SUBSURF")
    mod.levels = levels
    mod.render_levels = render_levels


def shade_smooth(obj: bpy.types.Object) -> None:
    if obj.type != "MESH":
        return

    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    try:
        bpy.ops.object.shade_smooth()
    except Exception:
        pass
    obj.select_set(False)


def name_contains(obj: bpy.types.Object, keywords: list[str]) -> bool:
    lower = obj.name.lower()
    return any(k.lower() in lower for k in keywords)


# -----------------------------
# IMPORT
# -----------------------------

def import_v6_model() -> None:
    if not INPUT_GLB.exists():
        raise FileNotFoundError(
            f"Missing input GLB:\n{INPUT_GLB}\n\n"
            "Make sure Bell Saint v6 is installed before running this script."
        )

    bpy.ops.import_scene.gltf(filepath=str(INPUT_GLB))

    # Center all imported root objects around origin on X/Z, keep feet near ground.
    mesh_objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if not mesh_objs:
        raise RuntimeError("No mesh objects imported from GLB.")

    # Set origins to geometry and apply transforms where safe.
    bpy.ops.object.select_all(action="DESELECT")
    for obj in mesh_objs:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = mesh_objs[0]
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")

    # Compute combined bounds.
    min_v = Vector((9999, 9999, 9999))
    max_v = Vector((-9999, -9999, -9999))

    for obj in mesh_objs:
        for corner in obj.bound_box:
            w = obj.matrix_world @ Vector(corner)
            min_v.x = min(min_v.x, w.x)
            min_v.y = min(min_v.y, w.y)
            min_v.z = min(min_v.z, w.z)
            max_v.x = max(max_v.x, w.x)
            max_v.y = max(max_v.y, w.y)
            max_v.z = max(max_v.z, w.z)

    center_x = (min_v.x + max_v.x) * 0.5
    center_z = (min_v.z + max_v.z) * 0.5
    ground_y = min_v.y

    for obj in mesh_objs:
        obj.location.x -= center_x
        obj.location.z -= center_z
        obj.location.y -= ground_y


# -----------------------------
# ART DIRECTION MATERIALS
# -----------------------------

MAT_WET_CLOTH = create_mat("AAA_Wet_Black_Cloth__replace_with_4k_PBR", (0.006, 0.008, 0.010, 1), 0.96, 0.0)
MAT_CLOTH_HI = create_mat("AAA_Charcoal_Cloth_Fold_Highlights__replace_with_4k_PBR", (0.034, 0.038, 0.043, 1), 0.93, 0.0)
MAT_MUD = create_mat("AAA_Mud_Stained_Cloth_Decals__replace_with_2k_PBR", (0.075, 0.055, 0.036, 1), 0.98, 0.0)
MAT_BRONZE = create_mat("AAA_Aged_Bronze_Bell__replace_with_4k_PBR", (0.42, 0.26, 0.095, 1), 0.68, 0.60)
MAT_BRONZE_EDGE = create_mat("AAA_Worn_Bronze_Edges__replace_with_2k_PBR", (0.78, 0.56, 0.20, 1), 0.55, 0.70)
MAT_PATINA = create_mat("AAA_BlueGreen_Patina_Decals__replace_with_2k_PBR", (0.06, 0.32, 0.27, 1), 0.86, 0.05)
MAT_RUST = create_mat("AAA_Rust_Drips_Decals__replace_with_2k_PBR", (0.32, 0.10, 0.030, 1), 0.90, 0.12)
MAT_IRON = create_mat("AAA_Black_Rusted_Iron__replace_with_2k_PBR", (0.045, 0.038, 0.034, 1), 0.86, 0.35)
MAT_ROPE = create_mat("AAA_Wet_Rope_Fibers__replace_with_2k_PBR", (0.095, 0.072, 0.047, 1), 0.95, 0.0)
MAT_WOOD = create_mat("AAA_Splintered_Wet_Wood__replace_with_2k_PBR", (0.065, 0.045, 0.026, 1), 0.95, 0.0)
MAT_PLATE = create_mat("AAA_Cracked_Pale_Warning_Plate__replace_with_2k_PBR", (0.46, 0.40, 0.30, 1), 0.90, 0.0)
MAT_VOID = create_mat("AAA_Deep_Black_Void", (0, 0, 0, 1), 1.0, 0.0)
MAT_GLOW = create_mat("AAA_Dim_Amber_Emission", (1.0, 0.45, 0.10, 1), 0.28, 0.0, (1.0, 0.42, 0.08, 1), 1.2)
MAT_WAX = create_mat("AAA_Dirty_Wax__replace_with_2k_PBR", (0.66, 0.56, 0.38, 1), 0.86, 0.0)


def assign_art_materials() -> None:
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue

        n = obj.name.lower()

        if any(k in n for k in ["bellhead", "smallbell", "tinybell", "bronze", "rim"]):
            assign_material_by_name(obj, MAT_BRONZE)
        if any(k in n for k in ["edge", "wornrim", "bright"]):
            assign_material_by_name(obj, MAT_BRONZE_EDGE)
        if "patina" in n:
            assign_material_by_name(obj, MAT_PATINA)
        if "rust" in n:
            assign_material_by_name(obj, MAT_RUST)
        if any(k in n for k in ["iron", "chain", "post", "crossbar", "brace"]):
            assign_material_by_name(obj, MAT_IRON)
        if "rope" in n or "cord" in n:
            assign_material_by_name(obj, MAT_ROPE)
        if "wood" in n:
            assign_material_by_name(obj, MAT_WOOD)
        if "plate" in n:
            assign_material_by_name(obj, MAT_PLATE)
        if any(k in n for k in ["void", "cut", "crack"]):
            assign_material_by_name(obj, MAT_VOID)
        if any(k in n for k in ["glow", "amber"]):
            assign_material_by_name(obj, MAT_GLOW)
        if "wax" in n:
            assign_material_by_name(obj, MAT_WAX)
        if "mud" in n:
            assign_material_by_name(obj, MAT_MUD)
        if any(k in n for k in ["robe", "cloth", "sleeve", "panel", "fold", "leg", "foot", "torso"]):
            if "fold" in n:
                assign_material_by_name(obj, MAT_CLOTH_HI)
            else:
                assign_material_by_name(obj, MAT_WET_CLOTH)


# -----------------------------
# COLLECTION ORGANIZATION
# -----------------------------

def organize_collections() -> None:
    collections = [
        "BS7_01_Body_Cloth_Sculpt",
        "BS7_02_Bell_Head_Metal_Sculpt",
        "BS7_03_Back_Frame_Chains",
        "BS7_04_Decals_Patina_Rust_Wax",
        "BS7_05_Weakpoints_Guides",
    ]

    for col in collections:
        ensure_collection(col)

    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue

        n = obj.name.lower()

        if any(k in n for k in ["robe", "cloth", "sleeve", "leg", "foot", "torso", "fold", "panel"]):
            move_to_collection(obj, "BS7_01_Body_Cloth_Sculpt")
        elif any(k in n for k in ["bellhead", "mouth", "crown", "rim", "smallbell", "tinybell"]):
            move_to_collection(obj, "BS7_02_Bell_Head_Metal_Sculpt")
        elif any(k in n for k in ["chain", "post", "crossbar", "brace", "cord"]):
            move_to_collection(obj, "BS7_03_Back_Frame_Chains")
        elif any(k in n for k in ["patina", "rust", "wax", "mud", "plate", "paint", "crack", "chip"]):
            move_to_collection(obj, "BS7_04_Decals_Patina_Rust_Wax")
        else:
            move_to_collection(obj, "BS7_04_Decals_Patina_Rust_Wax")


# -----------------------------
# MODIFIERS / SCULPT PREP
# -----------------------------

def apply_sculpt_prep_modifiers() -> None:
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue

        n = obj.name.lower()

        shade_smooth(obj)
        add_weighted_normals(obj)

        if any(k in n for k in ["robe", "cloth", "sleeve", "panel", "fold", "torso"]):
            add_bevel(obj, 0.006, 1)
            add_subdivision(obj, levels=1, render_levels=1)
            add_displace_noise(obj, "SCULPT_PREP_cloth_micro_ripple", strength=0.006, size=0.75)

        elif any(k in n for k in ["bellhead", "rim", "crown", "bell"]):
            add_bevel(obj, 0.012, 2)
            add_displace_noise(obj, "SCULPT_PREP_cast_metal_pitting", strength=0.0035, size=0.42, material_sensitive=True)

        elif any(k in n for k in ["chain", "iron", "post", "crossbar", "brace"]):
            add_bevel(obj, 0.006, 1)
            add_displace_noise(obj, "SCULPT_PREP_rust_noise", strength=0.0025, size=0.35, material_sensitive=True)

        elif any(k in n for k in ["rope", "cord"]):
            add_bevel(obj, 0.004, 1)
            add_displace_noise(obj, "SCULPT_PREP_rope_fiber_noise", strength=0.002, size=0.20)

        else:
            add_bevel(obj, 0.004, 1)


# -----------------------------
# GUIDE MARKERS / LIGHTS / CAMERA
# -----------------------------

def add_marker(name: str, location: tuple[float, float, float], color: tuple[float, float, float, float]) -> None:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.055, location=location)
    obj = bpy.context.object
    obj.name = name

    mat = create_mat(name + "_mat", color, 0.35, 0.0, color, 0.8)
    assign_material_by_name(obj, mat)
    move_to_collection(obj, "BS7_05_Weakpoints_Guides")


def add_text_label(name: str, text: str, location: tuple[float, float, float], size: float = 0.12) -> None:
    font_curve = bpy.data.curves.new(name, type="FONT")
    font_curve.body = text
    font_curve.align_x = "CENTER"
    font_curve.size = size

    obj = bpy.data.objects.new(name, font_curve)
    obj.location = location
    obj.rotation_euler[0] = math.radians(70)
    bpy.context.scene.collection.objects.link(obj)
    move_to_collection(obj, "BS7_05_Weakpoints_Guides")


def setup_guides_lighting_camera() -> None:
    add_marker("GUIDE_WeakPoint_BellMouth", (0, 3.48, -0.58), (1, 0.25, 0.08, 1))
    add_marker("GUIDE_WeakPoint_BackFrame", (0, 3.48, 0.20), (0.25, 0.55, 1, 1))
    add_marker("GUIDE_WeakPoint_RobeCords", (0, 2.05, -0.43), (1, 0.9, 0.1, 1))

    add_text_label("LABEL_BellMouth", "weak point: bell mouth", (0, 3.72, -0.82))
    add_text_label("LABEL_ClothSculpt", "sculpt cloth folds here", (0, 1.45, -0.78))
    add_text_label("LABEL_MetalSculpt", "sculpt dents / patina / chips", (0, 4.05, -0.72))

    # Lights
    bpy.ops.object.light_add(type="AREA", location=(0, 5.2, -5.0))
    key = bpy.context.object
    key.name = "AAA_preview_key_light"
    key.data.energy = 450
    key.data.size = 4.0

    bpy.ops.object.light_add(type="POINT", location=(0, 3.35, -0.75))
    bell_glow = bpy.context.object
    bell_glow.name = "AAA_preview_bell_amber_glow"
    bell_glow.data.energy = 80
    bell_glow.data.color = (1.0, 0.48, 0.12)

    # Camera
    bpy.ops.object.camera_add(location=(0, 2.65, -7.2), rotation=(math.radians(73), 0, 0))
    cam = bpy.context.object
    bpy.context.scene.camera = cam
    cam.name = "AAA_preview_camera_front"

    # Set view unit-ish clipping.
    bpy.context.scene.render.resolution_x = 1200
    bpy.context.scene.render.resolution_y = 1600


# -----------------------------
# EXPORT
# -----------------------------

def set_origins_and_save() -> None:
    WORK_DIR.mkdir(parents=True, exist_ok=True)

    # Select mesh objects for export.
    bpy.ops.object.select_all(action="DESELECT")
    for obj in bpy.context.scene.objects:
        if obj.type in {"MESH", "EMPTY", "LIGHT"} and not obj.name.startswith("GUIDE_"):
            obj.select_set(True)

    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_BLEND))

    # Export selected meshes. Ignore labels and guide markers.
    bpy.ops.object.select_all(action="DESELECT")
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH" and not obj.name.startswith("GUIDE_"):
            obj.select_set(True)

    bpy.ops.export_scene.gltf(
        filepath=str(OUTPUT_GLB),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_materials="EXPORT",
    )


def main() -> None:
    print("Bell Saint v7 sculpt-prep starting...")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Input: {INPUT_GLB}")

    clear_scene()
    import_v6_model()
    assign_art_materials()
    organize_collections()
    apply_sculpt_prep_modifiers()
    setup_guides_lighting_camera()
    set_origins_and_save()

    print("Done.")
    print(f"Saved blend: {OUTPUT_BLEND}")
    print(f"Exported GLB: {OUTPUT_GLB}")


if __name__ == "__main__":
    main()
