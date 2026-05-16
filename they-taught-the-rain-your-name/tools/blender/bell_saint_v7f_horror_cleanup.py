# Bell Saint v7f Horror Cleanup - Material Lifetime Fix
#
# Fixes the v7e error:
# ReferenceError: StructRNA of type Material has been removed
#
# Cause:
# v7e created materials, then opened a .blend file, which invalidated the material references.
#
# Fix:
# v7f loads the .blend FIRST, then creates materials, then assigns them.

from __future__ import annotations

import os
from pathlib import Path
import bpy


USER_PROJECT_ROOT = r""


def is_project_root(path: Path) -> bool:
    return path.exists() and (path / "project.godot").exists()


def find_upward(start: Path) -> Path | None:
    current = start.resolve()
    if current.is_file():
        current = current.parent

    for _ in range(12):
        if is_project_root(current):
            return current
        if current.parent == current:
            break
        current = current.parent

    return None


def find_project_root() -> Path:
    checks = []

    if USER_PROJECT_ROOT.strip():
        checks.append(Path(USER_PROJECT_ROOT.strip()))

    for env_name in ["BELL_SAINT_PROJECT_ROOT", "GODOT_PROJECT_ROOT", "RAIN_NAME_PROJECT_ROOT"]:
        value = os.environ.get(env_name, "").strip()
        if value:
            checks.append(Path(value))

    try:
        if bpy.data.filepath:
            checks.append(Path(bpy.data.filepath))
    except Exception:
        pass

    try:
        checks.append(Path(__file__))
    except Exception:
        pass

    checks.append(Path.cwd())

    home = Path.home()
    checks.extend([
        home / "OneDrive" / "Documents" / "GitHub" / "Game" / "they-taught-the-rain-your-name",
        home / "Documents" / "GitHub" / "Game" / "they-taught-the-rain-your-name",
        home / "Desktop" / "GitHub" / "Game" / "they-taught-the-rain-your-name",
    ])

    for item in checks:
        if is_project_root(item):
            return item.resolve()

    for item in checks:
        found = find_upward(item)
        if found:
            return found.resolve()

    raise FileNotFoundError("Could not find Godot project root. Set USER_PROJECT_ROOT at top of script.")


PROJECT_ROOT = find_project_root()
INPUT_BLEND = PROJECT_ROOT / "assets/models/enemies/bell_saint/blender_work/bell_saint_v7d_visual_cleanup.blend"
FALLBACK_BLEND = PROJECT_ROOT / "assets/models/enemies/bell_saint/blender_work/bell_saint_v7c_sculpt_prep.blend"
OUTPUT_BLEND = PROJECT_ROOT / "assets/models/enemies/bell_saint/blender_work/bell_saint_v7f_horror_cleanup.blend"
OUTPUT_GLB = PROJECT_ROOT / "assets/models/enemies/bell_saint/bell_saint_v7f_horror_cleanup.glb"

MATS = {}


def load_source_scene() -> None:
    has_bell = any(obj.name.startswith("BS6_") for obj in bpy.context.scene.objects)
    if has_bell:
        print("Using currently open scene.")
        return

    if INPUT_BLEND.exists():
        bpy.ops.wm.open_mainfile(filepath=str(INPUT_BLEND))
        return

    if FALLBACK_BLEND.exists():
        bpy.ops.wm.open_mainfile(filepath=str(FALLBACK_BLEND))
        return

    raise FileNotFoundError(
        "Could not find v7d or v7c blend file.\n"
        "Run v7c first, then v7d if available, then v7f.\n\n"
        f"Missing:\n{INPUT_BLEND}\n{FALLBACK_BLEND}"
    )


def make_mat(name: str, color, roughness=0.9, metallic=0.0, emission=None, emission_strength=0.0):
    material = bpy.data.materials.get(name)
    if material is None:
        material = bpy.data.materials.new(name)

    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")

    if bsdf:
        if "Base Color" in bsdf.inputs:
            bsdf.inputs["Base Color"].default_value = color
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = roughness
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = metallic

        if emission is not None:
            if "Emission Color" in bsdf.inputs:
                bsdf.inputs["Emission Color"].default_value = emission
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = emission_strength

    return material


def create_materials_after_blend_load() -> None:
    # IMPORTANT: called only after load_source_scene().
    MATS.clear()

    MATS["robe"] = make_mat("V7F_near_black_wet_robe", (0.0015, 0.002, 0.0025, 1), 0.985, 0.0)
    MATS["fold"] = make_mat("V7F_subtle_charcoal_folds", (0.010, 0.012, 0.014, 1), 0.975, 0.0)
    MATS["mud"] = make_mat("V7F_dried_dark_mud", (0.032, 0.024, 0.015, 1), 0.99, 0.0)
    MATS["bronze"] = make_mat("V7F_old_dead_bronze", (0.155, 0.095, 0.038, 1), 0.84, 0.46)
    MATS["bronze_edge"] = make_mat("V7F_dull_scraped_bronze", (0.31, 0.21, 0.075, 1), 0.78, 0.50)
    MATS["patina"] = make_mat("V7F_nearly_black_patina_stains", (0.010, 0.045, 0.038, 1), 0.96, 0.0)
    MATS["rust"] = make_mat("V7F_dark_brown_rust", (0.060, 0.020, 0.010, 1), 0.98, 0.0)
    MATS["iron"] = make_mat("V7F_black_iron", (0.018, 0.016, 0.015, 1), 0.92, 0.33)
    MATS["rope"] = make_mat("V7F_black_wet_rope", (0.025, 0.019, 0.013, 1), 0.98, 0.0)
    MATS["wood"] = make_mat("V7F_rotten_wet_wood", (0.030, 0.020, 0.012, 1), 0.99, 0.0)
    MATS["plate"] = make_mat("V7F_dirty_bone_wood_plate", (0.24, 0.205, 0.150, 1), 0.96, 0.0)
    MATS["void"] = make_mat("V7F_total_black_void", (0, 0, 0, 1), 1.0, 0.0)
    MATS["wax"] = make_mat("V7F_old_dark_wax", (0.28, 0.22, 0.135, 1), 0.94, 0.0)
    MATS["glow"] = make_mat(
        "V7F_tiny_warm_candle_glow",
        (1.0, 0.36, 0.08, 1),
        0.5,
        0.0,
        (1.0, 0.22, 0.03, 1),
        0.18,
    )


def assign(obj, material) -> None:
    if obj.type != "MESH":
        return
    obj.data.materials.clear()
    obj.data.materials.append(material)


def remove_toy_colors() -> None:
    for obj in bpy.context.scene.objects:
        n = obj.name.lower()

        if "patina" in n:
            obj.hide_viewport = True
            obj.hide_render = True

        if "redwarning" in n or "red_warning" in n or "paint" in n:
            obj.hide_viewport = True
            obj.hide_render = True

        if n.startswith("guide_") or "weakpoint" in n or n.startswith("label_"):
            obj.hide_viewport = True
            obj.hide_render = True


def assign_horror_materials() -> None:
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue

        n = obj.name.lower()

        if any(k in n for k in ["robe", "cloth", "sleeve", "leg", "foot", "torso", "panel"]):
            assign(obj, MATS["robe"])

        if "fold" in n:
            assign(obj, MATS["fold"])

        if "mud" in n:
            assign(obj, MATS["mud"])

        if any(k in n for k in ["bellhead", "smallbell", "tinybell", "mouth", "crown", "rim"]):
            assign(obj, MATS["bronze"])

        if any(k in n for k in ["edge", "worn"]):
            assign(obj, MATS["bronze_edge"])

        if "patina" in n:
            assign(obj, MATS["patina"])

        if "rust" in n:
            assign(obj, MATS["rust"])

        if any(k in n for k in ["chain", "post", "crossbar", "brace", "iron"]):
            assign(obj, MATS["iron"])

        if any(k in n for k in ["rope", "cord"]):
            assign(obj, MATS["rope"])

        if "wood" in n:
            assign(obj, MATS["wood"])

        if "plate" in n:
            assign(obj, MATS["plate"])

        if any(k in n for k in ["void", "cut", "crack"]):
            assign(obj, MATS["void"])

        if any(k in n for k in ["wax"]):
            assign(obj, MATS["wax"])

        if any(k in n for k in ["glow", "amber"]):
            assign(obj, MATS["glow"])


def improve_scale_balance() -> None:
    for obj in bpy.context.scene.objects:
        n = obj.name.lower()

        if "amberglow" in n or "glow" in n:
            obj.scale *= 0.40

        if "brightwornrim" in n or "wornrim" in n or "belledge" in n:
            obj.scale *= 0.72

        if "chip" in n:
            obj.scale *= 0.75

        if "frontcord" in n:
            obj.scale.x *= 0.75
            obj.scale.z *= 0.75


def add_horror_shadow_plate() -> None:
    import math

    mesh_name = "V7F_added_black_inner_hood"
    if bpy.data.objects.get(mesh_name):
        return

    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 3.28, -0.43))
    obj = bpy.context.object
    obj.name = mesh_name
    obj.dimensions = (0.34, 0.13, 0.045)
    obj.rotation_euler[0] = math.radians(-3)
    assign(obj, MATS["void"])


def tune_preview_lights() -> None:
    for obj in bpy.context.scene.objects:
        if obj.type != "LIGHT":
            continue

        n = obj.name.lower()

        if "amber" in n or "bell" in n:
            obj.data.energy = 18
            obj.data.color = (1.0, 0.24, 0.05)

        if "key" in n:
            obj.data.energy = 180


def export() -> None:
    OUTPUT_BLEND.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_BLEND))

    bpy.ops.object.select_all(action="DESELECT")

    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue

        if obj.hide_render:
            continue

        n = obj.name.lower()
        if n.startswith("guide_") or "weakpoint" in n or n.startswith("label_"):
            continue

        obj.select_set(True)

    bpy.ops.export_scene.gltf(
        filepath=str(OUTPUT_GLB),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_materials="EXPORT",
    )


def main() -> None:
    print("=== Bell Saint v7f Horror Cleanup ===")
    print("Project root:", PROJECT_ROOT)

    load_source_scene()
    create_materials_after_blend_load()
    remove_toy_colors()
    assign_horror_materials()
    improve_scale_balance()
    add_horror_shadow_plate()
    tune_preview_lights()
    export()

    print("Done.")
    print("Saved blend:", OUTPUT_BLEND)
    print("Exported GLB:", OUTPUT_GLB)


if __name__ == "__main__":
    main()
