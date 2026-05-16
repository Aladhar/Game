# Bell Saint v7d Visual Cleanup
#
# Run this AFTER v7c, or on an open v7c Blender scene.
#
# Purpose:
# - remove visible colored guide markers
# - make patina subtle instead of bright teal
# - make bronze darker/less toy-like
# - make robe darker
# - keep sculpt-prep modifiers
# - export a cleaner GLB for Godot
#
# If you run this from PowerShell, it will try to open:
# assets/models/enemies/bell_saint/blender_work/bell_saint_v7c_sculpt_prep.blend
#
# Output:
# assets/models/enemies/bell_saint/blender_work/bell_saint_v7d_visual_cleanup.blend
# assets/models/enemies/bell_saint/bell_saint_v7d_visual_cleanup.glb

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
INPUT_BLEND = PROJECT_ROOT / "assets/models/enemies/bell_saint/blender_work/bell_saint_v7c_sculpt_prep.blend"
OUTPUT_BLEND = PROJECT_ROOT / "assets/models/enemies/bell_saint/blender_work/bell_saint_v7d_visual_cleanup.blend"
OUTPUT_GLB = PROJECT_ROOT / "assets/models/enemies/bell_saint/bell_saint_v7d_visual_cleanup.glb"


def load_v7c_if_needed() -> None:
    # If scene already has Bell Saint objects, do not reopen.
    has_bell = any(obj.name.startswith("BS6_") for obj in bpy.context.scene.objects)
    if has_bell:
        print("Using currently open scene.")
        return

    if not INPUT_BLEND.exists():
        raise FileNotFoundError(
            "Could not find v7c blend file:\n"
            + str(INPUT_BLEND)
            + "\n\nRun bell_saint_v7c_sculpt_prep.py first."
        )

    bpy.ops.wm.open_mainfile(filepath=str(INPUT_BLEND))


def set_principled(mat_name: str, color, roughness=0.9, metallic=0.0, emission=None, emission_strength=0.0):
    mat = bpy.data.materials.get(mat_name)
    if mat is None:
        mat = bpy.data.materials.new(mat_name)

    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
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

    return mat


def assign_material(obj, mat):
    if obj.type != "MESH":
        return
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def create_cleanup_materials():
    mats = {}

    mats["cloth"] = set_principled(
        "V7D_wet_black_robes_dark_not_flat",
        (0.003, 0.004, 0.005, 1),
        roughness=0.98,
        metallic=0.0,
    )

    mats["cloth_hi"] = set_principled(
        "V7D_subtle_charcoal_cloth_folds",
        (0.018, 0.021, 0.024, 1),
        roughness=0.96,
        metallic=0.0,
    )

    mats["mud"] = set_principled(
        "V7D_dark_mud_stains",
        (0.045, 0.033, 0.022, 1),
        roughness=0.99,
        metallic=0.0,
    )

    mats["bronze"] = set_principled(
        "V7D_dark_aged_bronze",
        (0.26, 0.17, 0.065, 1),
        roughness=0.78,
        metallic=0.48,
    )

    mats["bronze_edge"] = set_principled(
        "V7D_dull_worn_bronze_edges",
        (0.50, 0.34, 0.12, 1),
        roughness=0.68,
        metallic=0.55,
    )

    mats["patina"] = set_principled(
        "V7D_subtle_old_patina_not_teal",
        (0.035, 0.115, 0.090, 1),
        roughness=0.93,
        metallic=0.05,
    )

    mats["rust"] = set_principled(
        "V7D_dark_rust_streaks",
        (0.15, 0.045, 0.018, 1),
        roughness=0.95,
        metallic=0.08,
    )

    mats["iron"] = set_principled(
        "V7D_black_rusted_iron",
        (0.030, 0.027, 0.025, 1),
        roughness=0.90,
        metallic=0.35,
    )

    mats["rope"] = set_principled(
        "V7D_wet_rope_dark",
        (0.050, 0.038, 0.026, 1),
        roughness=0.97,
        metallic=0.0,
    )

    mats["wood"] = set_principled(
        "V7D_wet_splintered_wood_dark",
        (0.040, 0.027, 0.018, 1),
        roughness=0.97,
        metallic=0.0,
    )

    mats["plate"] = set_principled(
        "V7D_dirty_warning_plate",
        (0.27, 0.235, 0.180, 1),
        roughness=0.94,
        metallic=0.0,
    )

    mats["void"] = set_principled(
        "V7D_deep_black_void",
        (0.0, 0.0, 0.0, 1),
        roughness=1.0,
        metallic=0.0,
    )

    mats["wax"] = set_principled(
        "V7D_dirty_unlit_wax",
        (0.42, 0.34, 0.22, 1),
        roughness=0.90,
        metallic=0.0,
    )

    mats["glow"] = set_principled(
        "V7D_subtle_warm_glow",
        (1.0, 0.42, 0.10, 1),
        roughness=0.40,
        metallic=0.0,
        emission=(1.0, 0.30, 0.06, 1),
        emission_strength=0.35,
    )

    mats["red"] = set_principled(
        "V7D_dried_dark_red_paint",
        (0.13, 0.006, 0.004, 1),
        roughness=0.90,
        metallic=0.0,
    )

    return mats


def remove_or_hide_guides() -> None:
    # Delete visible colored guide spheres. These were for sculpt reference only.
    for obj in list(bpy.context.scene.objects):
        lower = obj.name.lower()
        if lower.startswith("guide_") or "weakpoint" in lower or lower.startswith("label_"):
            bpy.data.objects.remove(obj, do_unlink=True)

    # Hide guide collection if it exists.
    col = bpy.data.collections.get("BS7_05_Weakpoints_Guides")
    if col:
        col.hide_viewport = True
        col.hide_render = True


def cleanup_material_assignments() -> None:
    mats = create_cleanup_materials()

    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue

        n = obj.name.lower()

        if any(k in n for k in ["robe", "cloth", "sleeve", "leg", "foot", "torso", "panel"]):
            assign_material(obj, mats["cloth"])

        if "fold" in n:
            assign_material(obj, mats["cloth_hi"])

        if "mud" in n:
            assign_material(obj, mats["mud"])

        if any(k in n for k in ["bellhead", "smallbell", "tinybell", "mouth", "crown", "rim"]):
            assign_material(obj, mats["bronze"])

        if any(k in n for k in ["edge", "worn"]):
            assign_material(obj, mats["bronze_edge"])

        if "patina" in n:
            assign_material(obj, mats["patina"])

        if "rust" in n:
            assign_material(obj, mats["rust"])

        if any(k in n for k in ["chain", "post", "crossbar", "brace", "iron"]):
            assign_material(obj, mats["iron"])

        if any(k in n for k in ["rope", "cord"]):
            assign_material(obj, mats["rope"])

        if "wood" in n:
            assign_material(obj, mats["wood"])

        if "plate" in n:
            assign_material(obj, mats["plate"])

        if any(k in n for k in ["void", "cut", "crack"]):
            assign_material(obj, mats["void"])

        if any(k in n for k in ["glow", "amber"]):
            assign_material(obj, mats["glow"])

        if "wax" in n:
            assign_material(obj, mats["wax"])

        if "redwarning" in n or "paint" in n:
            assign_material(obj, mats["red"])


def reduce_visual_noise() -> None:
    # Some decal objects are too loud. Make patina/rust patches smaller by scaling slightly.
    for obj in bpy.context.scene.objects:
        n = obj.name.lower()

        if "patina" in n:
            obj.scale *= 0.72

        if "bellrimchip" in n:
            obj.scale *= 0.82

        if "amberglow" in n:
            obj.scale *= 0.55

        if "waxstub" in n:
            obj.scale *= 0.80


def tune_lights() -> None:
    for obj in bpy.context.scene.objects:
        if obj.type == "LIGHT":
            lower = obj.name.lower()

            if "bell" in lower or "amber" in lower:
                obj.data.energy = 35
                obj.data.color = (1.0, 0.35, 0.08)

            if "key" in lower:
                obj.data.energy = 300


def export_clean_glb() -> None:
    OUTPUT_BLEND.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_BLEND))

    bpy.ops.object.select_all(action="DESELECT")

    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            lower = obj.name.lower()
            if lower.startswith("guide_") or "weakpoint" in lower or lower.startswith("label_"):
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
    print("=== Bell Saint v7d Visual Cleanup ===")
    print("Project root:", PROJECT_ROOT)

    load_v7c_if_needed()
    remove_or_hide_guides()
    cleanup_material_assignments()
    reduce_visual_noise()
    tune_lights()
    export_clean_glb()

    print("Done.")
    print("Saved blend:", OUTPUT_BLEND)
    print("Exported GLB:", OUTPUT_GLB)


if __name__ == "__main__":
    main()
