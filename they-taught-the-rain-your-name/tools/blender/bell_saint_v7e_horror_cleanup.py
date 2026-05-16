# Bell Saint v7e Horror Cleanup
#
# Run this after v7d, or on the open v7d Blender scene.
#
# Main goal:
# Make the model read as horror instead of toy-like.
#
# Changes:
# - hide/remove bright teal patina chunks
# - remove red warning paint color
# - darken bell bronze
# - reduce shiny gold rim
# - make face plate dirty bone/wood
# - darken robe and folds
# - export cleaner horror GLB

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
OUTPUT_BLEND = PROJECT_ROOT / "assets/models/enemies/bell_saint/blender_work/bell_saint_v7e_horror_cleanup.blend"
OUTPUT_GLB = PROJECT_ROOT / "assets/models/enemies/bell_saint/bell_saint_v7e_horror_cleanup.glb"


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
        "Run v7c first, then v7d, then v7e.\n\n"
        f"Missing:\n{INPUT_BLEND}\n{FALLBACK_BLEND}"
    )


def mat(name: str, color, roughness=0.9, metallic=0.0, emission=None, emission_strength=0.0):
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


def assign(obj, material) -> None:
    if obj.type != "MESH":
        return
    obj.data.materials.clear()
    obj.data.materials.append(material)


M_ROBE = mat("V7E_near_black_wet_robe", (0.0015, 0.002, 0.0025, 1), 0.985, 0.0)
M_FOLD = mat("V7E_subtle_charcoal_folds", (0.010, 0.012, 0.014, 1), 0.975, 0.0)
M_MUD = mat("V7E_dried_dark_mud", (0.032, 0.024, 0.015, 1), 0.99, 0.0)
M_BRONZE = mat("V7E_old_dead_bronze", (0.155, 0.095, 0.038, 1), 0.84, 0.46)
M_BRONZE_EDGE = mat("V7E_dull_scraped_bronze", (0.31, 0.21, 0.075, 1), 0.78, 0.50)
M_PATINA = mat("V7E_nearly_black_patina_stains", (0.010, 0.045, 0.038, 1), 0.96, 0.0)
M_RUST = mat("V7E_dark_brown_rust", (0.060, 0.020, 0.010, 1), 0.98, 0.0)
M_IRON = mat("V7E_black_iron", (0.018, 0.016, 0.015, 1), 0.92, 0.33)
M_ROPE = mat("V7E_black_wet_rope", (0.025, 0.019, 0.013, 1), 0.98, 0.0)
M_WOOD = mat("V7E_rotten_wet_wood", (0.030, 0.020, 0.012, 1), 0.99, 0.0)
M_PLATE = mat("V7E_dirty_bone_wood_plate", (0.24, 0.205, 0.150, 1), 0.96, 0.0)
M_VOID = mat("V7E_total_black_void", (0, 0, 0, 1), 1.0, 0.0)
M_WAX = mat("V7E_old_dark_wax", (0.28, 0.22, 0.135, 1), 0.94, 0.0)
M_GLOW = mat("V7E_tiny_warm_candle_glow", (1.0, 0.36, 0.08, 1), 0.5, 0.0, (1.0, 0.22, 0.03, 1), 0.18)


def remove_toy_colors() -> None:
    # Hide visual sticker pieces that currently look like colored toy decals.
    for obj in bpy.context.scene.objects:
        n = obj.name.lower()

        # The teal patina patches are too loud. Hide for now instead of deleting.
        if "patina" in n:
            obj.hide_viewport = True
            obj.hide_render = True

        # Red paint face looks toy-like. Hide it.
        if "redwarning" in n or "red_warning" in n or "paint" in n:
            obj.hide_viewport = True
            obj.hide_render = True

        # Guide markers should never show in model.
        if n.startswith("guide_") or "weakpoint" in n or n.startswith("label_"):
            obj.hide_viewport = True
            obj.hide_render = True


def assign_horror_materials() -> None:
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue

        n = obj.name.lower()

        if any(k in n for k in ["robe", "cloth", "sleeve", "leg", "foot", "torso", "panel"]):
            assign(obj, M_ROBE)

        if "fold" in n:
            assign(obj, M_FOLD)

        if "mud" in n:
            assign(obj, M_MUD)

        if any(k in n for k in ["bellhead", "smallbell", "tinybell", "mouth", "crown", "rim"]):
            assign(obj, M_BRONZE)

        if any(k in n for k in ["edge", "worn"]):
            assign(obj, M_BRONZE_EDGE)

        if "patina" in n:
            assign(obj, M_PATINA)

        if "rust" in n:
            assign(obj, M_RUST)

        if any(k in n for k in ["chain", "post", "crossbar", "brace", "iron"]):
            assign(obj, M_IRON)

        if any(k in n for k in ["rope", "cord"]):
            assign(obj, M_ROPE)

        if "wood" in n:
            assign(obj, M_WOOD)

        if "plate" in n:
            assign(obj, M_PLATE)

        if any(k in n for k in ["void", "cut", "crack"]):
            assign(obj, M_VOID)

        if any(k in n for k in ["wax"]):
            assign(obj, M_WAX)

        if any(k in n for k in ["glow", "amber"]):
            assign(obj, M_GLOW)


def improve_scale_balance() -> None:
    for obj in bpy.context.scene.objects:
        n = obj.name.lower()

        # Make glow dots less visible.
        if "amberglow" in n or "glow" in n:
            obj.scale *= 0.40

        # Make worn rim less thick.
        if "brightwornrim" in n or "wornrim" in n or "belledge" in n:
            obj.scale *= 0.72

        # Dark chip geometry should be smaller.
        if "chip" in n:
            obj.scale *= 0.75

        # Keep front cords from looking like random noodles.
        if "frontcord" in n:
            obj.scale.x *= 0.75
            obj.scale.z *= 0.75


def add_horror_shadow_plate() -> None:
    # Add a subtle dark hood/inner shadow under the bell mouth so the face reads creepier.
    import math

    mesh_name = "V7E_added_black_inner_hood"
    if bpy.data.objects.get(mesh_name):
        return

    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 3.28, -0.43))
    obj = bpy.context.object
    obj.name = mesh_name
    obj.dimensions = (0.34, 0.13, 0.045)
    obj.rotation_euler[0] = math.radians(-3)
    assign(obj, M_VOID)


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
    print("=== Bell Saint v7e Horror Cleanup ===")
    print("Project root:", PROJECT_ROOT)

    load_source_scene()
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
