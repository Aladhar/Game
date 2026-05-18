"""
Render quick preview images for the Penance Carrier Blender asset.

Run:
  blender --background --factory-startup --python tools/blender/penance_carrier_render_preview.py -- end_goal
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy


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
PREVIEW_ROOT = ASSET_ROOT / "previews"

BLENDS = {
    "end_goal": ASSET_ROOT / "blender_work/penance_carrier_end_goal_v3.blend",
    "v3": ASSET_ROOT / "blender_work/penance_carrier_end_goal_v3.blend",
    "v4_silhouette": ASSET_ROOT / "blender_work/penance_carrier_end_goal_v4_silhouette.blend",
    "v5_detail": ASSET_ROOT / "blender_work/penance_carrier_end_goal_v5_detail_density.blend",
    "v6_mood": ASSET_ROOT / "blender_work/penance_carrier_end_goal_v6_mood_body.blend",
    "v7_organic": ASSET_ROOT / "blender_work/penance_carrier_end_goal_v7_organic_clutter.blend",
    "v8_balanced": ASSET_ROOT / "blender_work/penance_carrier_end_goal_v8_balanced_end_goal.blend",
    "v9_body_fill": ASSET_ROOT / "blender_work/penance_carrier_end_goal_v9_body_fill.blend",
    "v10_slim": ASSET_ROOT / "blender_work/penance_carrier_end_goal_v10_slim_wrapped_body.blend",
    "v11_source": ASSET_ROOT / "blender_work/penance_carrier_end_goal_v11_safe_sculpt_prep.blend",
    "v11_5_source": ASSET_ROOT / "blender_work/penance_carrier_end_goal_v11_5_clay_quality_sculpt.blend",
    "v11_5_clay": ASSET_ROOT / "blender_work/penance_carrier_end_goal_v11_5_clay_quality_sculpt.blend",
    "v11_6_source": ASSET_ROOT / "blender_work/penance_carrier_end_goal_v11_6_authored_clay_sculpt.blend",
    "v11_6_clay": ASSET_ROOT / "blender_work/penance_carrier_end_goal_v11_6_authored_clay_sculpt.blend",
    "v11_7_source": ASSET_ROOT / "blender_work/penance_carrier_end_goal_v11_7_end_goal_readability.blend",
    "v11_7_clay": ASSET_ROOT / "blender_work/penance_carrier_end_goal_v11_7_end_goal_readability.blend",
    "v11_8_source": ASSET_ROOT / "blender_work/penance_carrier_end_goal_v11_8_head_mask_reference_lock.blend",
    "v11_8_clay": ASSET_ROOT / "blender_work/penance_carrier_end_goal_v11_8_head_mask_reference_lock.blend",
    "v11_9_source": ASSET_ROOT / "blender_work/penance_carrier_end_goal_v11_9_ragged_hood_door_silhouette.blend",
    "v11_9_clay": ASSET_ROOT / "blender_work/penance_carrier_end_goal_v11_9_ragged_hood_door_silhouette.blend",
    "v12_source": ASSET_ROOT / "blender_work/penance_carrier_end_goal_v12_head_readability_checkpoint.blend",
    "v12_clay": ASSET_ROOT / "blender_work/penance_carrier_end_goal_v12_head_readability_checkpoint.blend",
    "v13_source": ASSET_ROOT / "blender_work/penance_carrier_end_goal_v13_hood_door_integration.blend",
    "v13_clay": ASSET_ROOT / "blender_work/penance_carrier_end_goal_v13_hood_door_integration.blend",
    "v14_source": ASSET_ROOT / "blender_work/penance_carrier_end_goal_v14_human_silhouette_lock.blend",
    "v14_clay": ASSET_ROOT / "blender_work/penance_carrier_end_goal_v14_human_silhouette_lock.blend",
    "v15_source": ASSET_ROOT / "blender_work/penance_carrier_end_goal_v15_mask_material_balance.blend",
    "v15_clay": ASSET_ROOT / "blender_work/penance_carrier_end_goal_v15_mask_material_balance.blend",
    "v16_source": ASSET_ROOT / "blender_work/penance_carrier_end_goal_v16_hero_anatomy_weight.blend",
    "v16_clay": ASSET_ROOT / "blender_work/penance_carrier_end_goal_v16_hero_anatomy_weight.blend",
    "v17_source": ASSET_ROOT / "blender_work/penance_carrier_end_goal_v17_proportion_restore.blend",
    "v17_clay": ASSET_ROOT / "blender_work/penance_carrier_end_goal_v17_proportion_restore.blend",
    "v18_source": ASSET_ROOT / "blender_work/penance_carrier_end_goal_v18_clay_authorship.blend",
    "v18_clay": ASSET_ROOT / "blender_work/penance_carrier_end_goal_v18_clay_authorship.blend",
    "v19_source": ASSET_ROOT / "blender_work/penance_carrier_end_goal_v19_front_identity_lock.blend",
    "v19_clay": ASSET_ROOT / "blender_work/penance_carrier_end_goal_v19_front_identity_lock.blend",
    "v20_source": ASSET_ROOT / "blender_work/penance_carrier_end_goal_v20_ragged_hood_integration.blend",
    "v20_clay": ASSET_ROOT / "blender_work/penance_carrier_end_goal_v20_ragged_hood_integration.blend",
    "v21_source": ASSET_ROOT / "blender_work/penance_carrier_end_goal_v21_multi_region_reference_baseline.blend",
    "v21_clay": ASSET_ROOT / "blender_work/penance_carrier_end_goal_v21_multi_region_reference_baseline.blend",
    "v3_head": ASSET_ROOT / "blender_work/penance_carrier_v3_head_readability.blend",
}


def arg_variant() -> str:
    if "--" in sys.argv:
        args = sys.argv[sys.argv.index("--") + 1 :]
        if args:
            return args[0]
    return "end_goal"


def bounds() -> tuple[float, float, float, float, float, float]:
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    xs, ys, zs = [], [], []
    for obj in meshes:
        for corner in obj.bound_box:
            world = obj.matrix_world @ __import__("mathutils").Vector(corner)
            xs.append(world.x)
            ys.append(world.y)
            zs.append(world.z)
    return min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)


def make_clay_material() -> bpy.types.Material:
    mat = bpy.data.materials.new("Preview_flat_gray_clay_quality_check")
    mat.diffuse_color = (0.48, 0.47, 0.44, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.48, 0.47, 0.44, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.78
        bsdf.inputs["Metallic"].default_value = 0.0
    return mat


def setup_render(clay: bool = False) -> None:
    bpy.context.scene.render.engine = "BLENDER_EEVEE_NEXT"
    bpy.context.scene.eevee.taa_render_samples = 32
    bpy.context.scene.render.resolution_x = 1400
    bpy.context.scene.render.resolution_y = 1800
    bpy.context.scene.world.color = (0.018, 0.022, 0.026)

    for obj in list(bpy.context.scene.objects):
        if obj.name.startswith("PC_V4_REF_") or obj.name.startswith("PC_V4_BLOCKOUT_SCALE_"):
            bpy.data.objects.remove(obj, do_unlink=True)
            continue
        if obj.type == "LIGHT":
            bpy.data.objects.remove(obj, do_unlink=True)

    if clay:
        clay_mat = make_clay_material()
        for obj in bpy.context.scene.objects:
            if obj.type == "MESH":
                mat_name = obj.data.materials[0].name.lower() if obj.data.materials else ""
                if "void" in mat_name or "black" in mat_name:
                    continue
                obj.data.materials.clear()
                obj.data.materials.append(clay_mat)

    bpy.ops.object.light_add(type="AREA", location=(-3.8 if clay else 0, -4.5, 5.8))
    key = bpy.context.object
    key.name = "Preview_Key_Light"
    key.data.energy = 1250 if clay else 900
    key.data.size = 4.2 if clay else 5.5

    if clay:
        bpy.ops.object.light_add(type="AREA", location=(3.8, 3.2, 3.5))
        rim = bpy.context.object
        rim.name = "Preview_Strong_Rim_Light"
        rim.data.energy = 850
        rim.data.size = 3.0

    bpy.ops.object.light_add(type="POINT", location=(0.0, -1.2, 2.65))
    face = bpy.context.object
    face.name = "Preview_Face_Candle_Light"
    face.data.energy = 25 if clay else 115
    face.data.color = (0.9, 0.9, 0.86) if clay else (1.0, 0.48, 0.16)


def render_camera(name: str, location: tuple[float, float, float], rotation: tuple[float, float, float], ortho: float, path: Path) -> None:
    cam_data = bpy.data.cameras.new(name)
    cam = bpy.data.objects.new(name, cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = location
    cam.rotation_euler = rotation
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = ortho
    bpy.context.scene.camera = cam
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    variant = arg_variant()
    blend = BLENDS.get(variant)
    if blend is None or not blend.exists():
        raise FileNotFoundError(f"Unknown or missing preview blend for {variant}: {blend}")

    PREVIEW_ROOT.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    setup_render(clay=variant.endswith("_clay"))

    min_x, max_x, min_y, max_y, min_z, max_z = bounds()
    height = max_z - min_z
    center_z = (min_z + max_z) * 0.5

    render_camera(
        f"{variant}_front_camera",
        (0.0, -7.2, center_z + 0.15),
        (math.radians(90), 0, 0),
        height * 1.12,
        PREVIEW_ROOT / f"{variant}_front.png",
    )
    render_camera(
        f"{variant}_three_quarter_camera",
        (3.8, -7.0, center_z + 0.18),
        (math.radians(89), 0, math.radians(28)),
        height * 1.16,
        PREVIEW_ROOT / f"{variant}_three_quarter.png",
    )
    render_camera(
        f"{variant}_back_camera",
        (0.0, 7.2, center_z + 0.15),
        (math.radians(90), 0, math.radians(180)),
        height * 1.12,
        PREVIEW_ROOT / f"{variant}_back.png",
    )
    print("Rendered previews to:", PREVIEW_ROOT)


if __name__ == "__main__":
    main()
