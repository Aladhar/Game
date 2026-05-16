"""
Bell Saint v7b Blender Sculpt-Prep Kit — Root Detection Fix

Why this exists:
Blender may run scripts with its working directory set to:
  C:\Program Files\Blender Foundation\Blender 5.1

If that happens, the old script searches for:
  C:\Program Files\Blender Foundation\Blender 5.1\assets\models\...

which is wrong.

This version aggressively finds your Godot project root.

If it still cannot find the project, set USER_PROJECT_ROOT below manually.
Example:
  USER_PROJECT_ROOT = r"C:\Users\Amrit\OneDrive\Documents\GitHub\Game\they-taught-the-rain-your-name"
"""

from __future__ import annotations

import math
import os
from pathlib import Path

import bpy
from mathutils import Vector


# ---------------------------------------------------------------------
# MANUAL OVERRIDE
# ---------------------------------------------------------------------
# If automatic detection fails, paste your exact Godot project folder here.
# It must be the folder that contains project.godot.
#
# Example:
# USER_PROJECT_ROOT = r"C:\Users\Amrit\OneDrive\Documents\GitHub\Game\they-taught-the-rain-your-name"
#
USER_PROJECT_ROOT = r""


# ---------------------------------------------------------------------
# PATH DETECTION
# ---------------------------------------------------------------------

def is_project_root(path: Path) -> bool:
    return path.exists() and (path / "project.godot").exists()


def find_upward(start: Path) -> Path | None:
    try:
        current = start.resolve()
    except Exception:
        current = start

    if current.is_file():
        current = current.parent

    for _ in range(12):
        if is_project_root(current):
            return current
        if current.parent == current:
            break
        current = current.parent
    return None


def get_text_editor_paths() -> list[Path]:
    paths: list[Path] = []
    try:
        for text in bpy.data.texts:
            filepath = getattr(text, "filepath", "")
            if filepath:
                paths.append(Path(filepath))
    except Exception:
        pass
    return paths


def likely_windows_project_paths() -> list[Path]:
    candidates: list[Path] = []
    home = Path.home()

    guesses = [
        home / "Documents" / "GitHub" / "Game" / "they-taught-the-rain-your-name",
        home / "OneDrive" / "Documents" / "GitHub" / "Game" / "they-taught-the-rain-your-name",
        home / "OneDrive" / "Desktop" / "GitHub" / "Game" / "they-taught-the-rain-your-name",
        home / "Desktop" / "GitHub" / "Game" / "they-taught-the-rain-your-name",
        home / "GitHub" / "Game" / "they-taught-the-rain-your-name",
    ]

    for g in guesses:
        candidates.append(g)

    # Also search shallow GitHub locations, but avoid scanning whole drive.
    for base in [
        home / "Documents" / "GitHub",
        home / "OneDrive" / "Documents" / "GitHub",
        home / "Desktop" / "GitHub",
    ]:
        if base.exists():
            try:
                for p in base.glob("*/they-taught-the-rain-your-name"):
                    candidates.append(p)
                for p in base.glob("*/*/they-taught-the-rain-your-name"):
                    candidates.append(p)
            except Exception:
                pass

    return candidates


def find_project_root() -> Path:
    checks: list[Path] = []

    # 1. Manual override.
    if USER_PROJECT_ROOT.strip():
        checks.append(Path(USER_PROJECT_ROOT.strip()))

    # 2. Environment variables.
    for env_name in ["BELL_SAINT_PROJECT_ROOT", "GODOT_PROJECT_ROOT", "RAIN_NAME_PROJECT_ROOT"]:
        value = os.environ.get(env_name, "").strip()
        if value:
            checks.append(Path(value))

    # 3. Current Blender file directory.
    try:
        if bpy.data.filepath:
            checks.append(Path(bpy.data.filepath))
    except Exception:
        pass

    # 4. Script path from Blender Text Editor.
    checks.extend(get_text_editor_paths())

    # 5. __file__, if Blender provides it.
    try:
        checks.append(Path(__file__))
    except Exception:
        pass

    # 6. Current working directory.
    checks.append(Path.cwd())

    # 7. Common project guesses.
    checks.extend(likely_windows_project_paths())

    # First try exact roots, then upward search.
    for c in checks:
        if is_project_root(c):
            return c.resolve()

    for c in checks:
        found = find_upward(c)
        if found:
            return found.resolve()

    attempted = "\n".join([str(c) for c in checks])
    raise FileNotFoundError(
        "Could not find Godot project root containing project.godot.\n\n"
        "Fix options:\n"
        "1. Put this script inside your project at tools/blender/ and open it from there.\n"
        "2. Or set USER_PROJECT_ROOT at the top of this script.\n"
        "3. Or run Blender from the Godot project root:\n"
        "   blender --background --python tools/blender/bell_saint_v7b_sculpt_prep.py\n\n"
        "Attempted paths:\n"
        + attempted
    )


PROJECT_ROOT = find_project_root()

INPUT_GLB = PROJECT_ROOT / "assets/models/enemies/bell_saint/bell_saint_v6_centered_artpass.glb"
WORK_DIR = PROJECT_ROOT / "assets/models/enemies/bell_saint/blender_work"
OUTPUT_BLEND = WORK_DIR / "bell_saint_v7b_sculpt_prep.blend"
OUTPUT_GLB = PROJECT_ROOT / "assets/models/enemies/bell_saint/bell_saint_v7b_sculpt_prep.glb"


# ---------------------------------------------------------------------
# UTILS
# ---------------------------------------------------------------------

def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def ensure_collection(name: str) -> bpy.types.Collection:
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(collection)
    return collection


def move_to_collection(obj: bpy.types.Object, collection_name: str) -> None:
    col = ensure_collection(collection_name)
    for existing in list(obj.users_collection):
        existing.objects.unlink(obj)
    col.objects.link(obj)


def create_mat(name: str, color, roughness: float, metallic: float = 0.0, emission=None, emission_strength: float = 0.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
        if emission is not None:
            if "Emission Color" in bsdf.inputs:
                bsdf.inputs["Emission Color"].default_value = emission
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat


def assign_mat(obj: bpy.types.Object, mat: bpy.types.Material) -> None:
    if obj.type != "MESH":
        return
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def add_modifier(obj: bpy.types.Object, name: str, mod_type: str):
    existing = obj.modifiers.get(name)
    if existing:
        return existing
    return obj.modifiers.new(name, mod_type)


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


def add_weighted_normals(obj: bpy.types.Object) -> None:
    if obj.type != "MESH":
        return
    mod = add_modifier(obj, "AAA_weighted_normals", "WEIGHTED_NORMAL")
    mod.keep_sharp = True
    mod.weight = 50


def add_bevel(obj: bpy.types.Object, width: float, segments: int) -> None:
    if obj.type != "MESH":
        return
    mod = add_modifier(obj, "AAA_soft_bevel_edges", "BEVEL")
    mod.width = width
    mod.segments = segments
    mod.profile = 0.45


def add_noise_displace(obj: bpy.types.Object, name: str, strength: float, size: float) -> None:
    if obj.type != "MESH":
        return
    tex = bpy.data.textures.new(obj.name + "_" + name, type="CLOUDS")
    tex.noise_scale = size
    mod = add_modifier(obj, name, "DISPLACE")
    mod.strength = strength
    mod.texture = tex


def add_subdivision(obj: bpy.types.Object, levels: int = 1) -> None:
    if obj.type != "MESH":
        return
    mod = add_modifier(obj, "SCULPT_PREP_subdivision_preview", "SUBSURF")
    mod.levels = levels
    mod.render_levels = levels


# ---------------------------------------------------------------------
# MATERIALS
# ---------------------------------------------------------------------

MAT_WET_CLOTH = create_mat("AAA_Wet_Black_Cloth_replace_with_4k_PBR", (0.006, 0.008, 0.010, 1), 0.96)
MAT_CLOTH_HI = create_mat("AAA_Charcoal_Cloth_Fold_Highlights", (0.034, 0.038, 0.043, 1), 0.93)
MAT_MUD = create_mat("AAA_Mud_Stained_Cloth_Decals", (0.075, 0.055, 0.036, 1), 0.98)
MAT_BRONZE = create_mat("AAA_Aged_Bronze_Bell_replace_with_4k_PBR", (0.42, 0.26, 0.095, 1), 0.68, 0.60)
MAT_BRONZE_EDGE = create_mat("AAA_Worn_Bronze_Edges", (0.78, 0.56, 0.20, 1), 0.55, 0.70)
MAT_PATINA = create_mat("AAA_BlueGreen_Patina_Decals", (0.06, 0.32, 0.27, 1), 0.86, 0.05)
MAT_RUST = create_mat("AAA_Rust_Drips_Decals", (0.32, 0.10, 0.030, 1), 0.90, 0.12)
MAT_IRON = create_mat("AAA_Black_Rusted_Iron", (0.045, 0.038, 0.034, 1), 0.86, 0.35)
MAT_ROPE = create_mat("AAA_Wet_Rope_Fibers", (0.095, 0.072, 0.047, 1), 0.95)
MAT_WOOD = create_mat("AAA_Splintered_Wet_Wood", (0.065, 0.045, 0.026, 1), 0.95)
MAT_PLATE = create_mat("AAA_Cracked_Pale_Warning_Plate", (0.46, 0.40, 0.30, 1), 0.90)
MAT_VOID = create_mat("AAA_Deep_Black_Void", (0, 0, 0, 1), 1.0)
MAT_GLOW = create_mat("AAA_Dim_Amber_Emission", (1.0, 0.45, 0.10, 1), 0.28, 0.0, (1.0, 0.42, 0.08, 1), 1.2)
MAT_WAX = create_mat("AAA_Dirty_Wax", (0.66, 0.56, 0.38, 1), 0.86)


# ---------------------------------------------------------------------
# MAIN PROCESS
# ---------------------------------------------------------------------

def import_model() -> None:
    if not INPUT_GLB.exists():
        raise FileNotFoundError(
            "Missing input GLB:\n"
            + str(INPUT_GLB)
            + "\n\nMake sure Bell Saint v6 is installed at that exact path."
        )

    bpy.ops.import_scene.gltf(filepath=str(INPUT_GLB))

    mesh_objs = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not mesh_objs:
        raise RuntimeError("No mesh objects were imported from the GLB.")

    # Recenter imported model.
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


def assign_materials_and_collections() -> None:
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue

        n = obj.name.lower()

        if any(k in n for k in ["robe", "cloth", "sleeve", "leg", "foot", "torso", "panel"]):
            assign_mat(obj, MAT_WET_CLOTH)
            move_to_collection(obj, "BS7_01_Body_Cloth_Sculpt")
        if "fold" in n:
            assign_mat(obj, MAT_CLOTH_HI)
            move_to_collection(obj, "BS7_01_Body_Cloth_Sculpt")
        if "mud" in n:
            assign_mat(obj, MAT_MUD)
            move_to_collection(obj, "BS7_04_Decals_Patina_Rust_Wax")
        if any(k in n for k in ["bellhead", "smallbell", "tinybell", "mouth", "crown", "rim"]):
            assign_mat(obj, MAT_BRONZE)
            move_to_collection(obj, "BS7_02_Bell_Head_Metal_Sculpt")
        if any(k in n for k in ["edge", "worn"]):
            assign_mat(obj, MAT_BRONZE_EDGE)
        if "patina" in n:
            assign_mat(obj, MAT_PATINA)
            move_to_collection(obj, "BS7_04_Decals_Patina_Rust_Wax")
        if "rust" in n:
            assign_mat(obj, MAT_RUST)
            move_to_collection(obj, "BS7_04_Decals_Patina_Rust_Wax")
        if any(k in n for k in ["chain", "post", "crossbar", "brace", "iron"]):
            assign_mat(obj, MAT_IRON)
            move_to_collection(obj, "BS7_03_Back_Frame_Chains")
        if any(k in n for k in ["rope", "cord"]):
            assign_mat(obj, MAT_ROPE)
            move_to_collection(obj, "BS7_03_Back_Frame_Chains")
        if "wood" in n:
            assign_mat(obj, MAT_WOOD)
            move_to_collection(obj, "BS7_03_Back_Frame_Chains")
        if "plate" in n:
            assign_mat(obj, MAT_PLATE)
            move_to_collection(obj, "BS7_04_Decals_Patina_Rust_Wax")
        if any(k in n for k in ["void", "cut", "crack"]):
            assign_mat(obj, MAT_VOID)
        if any(k in n for k in ["glow", "amber"]):
            assign_mat(obj, MAT_GLOW)
        if "wax" in n:
            assign_mat(obj, MAT_WAX)
            move_to_collection(obj, "BS7_04_Decals_Patina_Rust_Wax")


def add_sculpt_modifiers() -> None:
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue

        n = obj.name.lower()
        shade_smooth(obj)
        add_weighted_normals(obj)

        if any(k in n for k in ["robe", "cloth", "sleeve", "panel", "fold", "torso"]):
            add_bevel(obj, 0.006, 1)
            add_subdivision(obj, 1)
            add_noise_displace(obj, "SCULPT_PREP_cloth_micro_ripple", 0.006, 0.75)
        elif any(k in n for k in ["bellhead", "rim", "crown", "bell"]):
            add_bevel(obj, 0.012, 2)
            add_noise_displace(obj, "SCULPT_PREP_cast_metal_pitting", 0.0035, 0.42)
        elif any(k in n for k in ["chain", "post", "crossbar", "brace", "iron"]):
            add_bevel(obj, 0.006, 1)
            add_noise_displace(obj, "SCULPT_PREP_rust_noise", 0.0025, 0.35)
        elif any(k in n for k in ["rope", "cord"]):
            add_bevel(obj, 0.004, 1)
            add_noise_displace(obj, "SCULPT_PREP_rope_fiber_noise", 0.002, 0.20)
        else:
            add_bevel(obj, 0.004, 1)


def add_preview_scene() -> None:
    # Guide markers.
    guide_col = ensure_collection("BS7_05_Weakpoints_Guides")

    def marker(name, loc, color):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.055, location=loc)
        obj = bpy.context.object
        obj.name = name
        mat = create_mat(name + "_mat", color, 0.35, 0.0, color, 0.8)
        assign_mat(obj, mat)
        move_to_collection(obj, guide_col.name)

    marker("GUIDE_WeakPoint_BellMouth", (0, 3.48, -0.58), (1, 0.25, 0.08, 1))
    marker("GUIDE_WeakPoint_BackFrame", (0, 3.48, 0.20), (0.25, 0.55, 1, 1))
    marker("GUIDE_WeakPoint_RobeCords", (0, 2.05, -0.43), (1, 0.9, 0.1, 1))

    # Lights/camera.
    bpy.ops.object.light_add(type="AREA", location=(0, 5.2, -5.0))
    key = bpy.context.object
    key.name = "AAA_preview_key_light"
    key.data.energy = 450
    key.data.size = 4.0

    bpy.ops.object.light_add(type="POINT", location=(0, 3.35, -0.75))
    bell = bpy.context.object
    bell.name = "AAA_preview_bell_amber_glow"
    bell.data.energy = 90
    bell.data.color = (1.0, 0.48, 0.12)

    bpy.ops.object.camera_add(location=(0, 2.65, -7.2), rotation=(math.radians(73), 0, 0))
    cam = bpy.context.object
    cam.name = "AAA_preview_camera_front"
    bpy.context.scene.camera = cam


def save_outputs() -> None:
    WORK_DIR.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_BLEND))

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
    print("\n=== Bell Saint v7b Sculpt Prep ===")
    print("Detected project root:", PROJECT_ROOT)
    print("Input GLB:", INPUT_GLB)

    clear_scene()
    import_model()
    assign_materials_and_collections()
    add_sculpt_modifiers()
    add_preview_scene()
    save_outputs()

    print("\nDONE")
    print("Saved blend:", OUTPUT_BLEND)
    print("Exported GLB:", OUTPUT_GLB)


if __name__ == "__main__":
    main()
