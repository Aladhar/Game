"""
Penance Carrier V9 body-fill pass.

This pass builds on the V5 detail-density pass and corrects:
- darker wet mood materials
- clearer hooded void and vertical door-mask head
- stronger wrapped human body read
- less toy-like shrine surface

It keeps:
- wrapped human anatomy detail
- dense shrine kitbash proxies
- chain/bell/rope curtains
- rotten back mass and sagging shrouds

It uses:
- Penance_End_Goal.png-derived front/side/back reference crops
- penance_carrier_blockout_v1.glb as the only imported base model

Outputs:
  assets/models/enemies/penance_carrier/blender_work/penance_carrier_end_goal_v9_body_fill.blend
  assets/models/enemies/penance_carrier/penance_carrier_end_goal_v9_body_fill.glb
"""

from __future__ import annotations

import math
import random
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
REF_ROOT = ASSET_ROOT / "reference_crops"
INPUT_GLB = ASSET_ROOT / "penance_carrier_blockout_v1.glb"
WORK_DIR = ASSET_ROOT / "blender_work"
OUTPUT_BLEND = WORK_DIR / "penance_carrier_end_goal_v9_body_fill.blend"
OUTPUT_GLB = ASSET_ROOT / "penance_carrier_end_goal_v9_body_fill.glb"

MAT: dict[str, bpy.types.Material] = {}


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def make_mat(name: str, color: tuple[float, float, float, float], roughness: float, metallic: float = 0.0) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
    return mat


def make_image_mat(name: str, image_path: Path, alpha: float = 0.42) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.blend_method = "BLEND"
    mat.show_transparent_back = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(image_path))
    if bsdf:
        mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Alpha"].default_value = alpha
        bsdf.inputs["Roughness"].default_value = 1.0
    return mat


def create_materials() -> None:
    MAT["cloth"] = make_mat("PC_V8_wet_black_wrapped_cloth", (0.040, 0.038, 0.034, 1), 0.96)
    MAT["wrap_highlight"] = make_mat("PC_V8_damp_gray_wrap_highlights", (0.145, 0.137, 0.122, 1), 0.94)
    MAT["wood"] = make_mat("PC_V8_rotten_dark_weathered_wood", (0.092, 0.067, 0.045, 1), 0.95)
    MAT["raw_wood"] = make_mat("PC_V8_old_pale_but_dirty_door_wood", (0.255, 0.215, 0.155, 1), 0.92)
    MAT["metal"] = make_mat("PC_V6_rusted_dark_iron", (0.085, 0.070, 0.058, 1), 0.86, 0.8)
    MAT["brass"] = make_mat("PC_V6_dull_corroded_brass", (0.36, 0.235, 0.09, 1), 0.74, 1.0)
    MAT["void"] = make_mat("PC_V6_black_mask_void", (0.0, 0.0, 0.0, 1), 1.0)
    MAT["paper"] = make_mat("PC_V8_stained_old_paper", (0.31, 0.265, 0.19, 1), 0.95)
    MAT["wax"] = make_mat("PC_V8_dirty_dead_wax", (0.34, 0.285, 0.20, 1), 0.86)
    MAT["guide"] = make_mat("PC_V6_silhouette_measure_guides", (0.0, 0.75, 1.0, 0.38), 1.0)


def ensure_collection(name: str) -> bpy.types.Collection:
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


def move_to(obj: bpy.types.Object, collection: str) -> bpy.types.Object:
    col = ensure_collection(collection)
    for current in list(obj.users_collection):
        current.objects.unlink(obj)
    col.objects.link(obj)
    return obj


def assign(obj: bpy.types.Object, mat: bpy.types.Material) -> bpy.types.Object:
    if obj.type == "MESH":
        obj.data.materials.clear()
        obj.data.materials.append(mat)
    return obj


def shade(obj: bpy.types.Object, bevel: float = 0.0) -> bpy.types.Object:
    if obj.type != "MESH":
        return obj
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    try:
        bpy.ops.object.shade_smooth()
    except Exception:
        pass
    obj.select_set(False)
    if bevel > 0:
        mod = obj.modifiers.new("PC_V4_bevel_for_readability", "BEVEL")
        mod.width = bevel
        mod.segments = 1
        mod.profile = 0.45
        obj.modifiers.new("PC_V4_weighted_normals", "WEIGHTED_NORMAL")
    return obj


def box(name: str, loc: tuple[float, float, float], scale: tuple[float, float, float], mat: bpy.types.Material, rot=(0, 0, 0), collection="PC_V4_silhouette") -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(obj, mat)
    shade(obj, 0.01)
    return move_to(obj, collection)


def cyl(name: str, loc: tuple[float, float, float], radius: float, depth: float, mat: bpy.types.Material, vertices=24, rot=(0, 0, 0), collection="PC_V4_silhouette") -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    assign(obj, mat)
    shade(obj, 0.004)
    return move_to(obj, collection)


def sphere(name: str, loc: tuple[float, float, float], radius: float, mat: bpy.types.Material, scale=(1, 1, 1), collection="PC_V4_silhouette") -> bpy.types.Object:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=radius, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    assign(obj, mat)
    shade(obj)
    return move_to(obj, collection)


def torus(name: str, loc: tuple[float, float, float], major: float, minor: float, mat: bpy.types.Material, rot=(0, 0, 0), collection="PC_V4_silhouette") -> bpy.types.Object:
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=32, minor_segments=8, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    assign(obj, mat)
    shade(obj)
    return move_to(obj, collection)


def chain_links(name: str, start: tuple[float, float, float], count: int, dz: float, mat: bpy.types.Material, scale: float = 1.0, swing: float = 0.0) -> tuple[float, float, float]:
    x, y, z = start
    for i in range(count):
        x_i = x + math.sin(i * 0.9 + swing) * 0.025
        y_i = y + math.cos(i * 0.55 + swing) * 0.015
        z_i = z - i * dz
        torus(
            f"{name}_link_{i:02d}",
            (x_i, y_i, z_i),
            0.030 * scale,
            0.0055 * scale,
            mat,
            rot=(math.radians(90), 0, math.radians(90 if i % 2 else 0)),
            collection="PC_V5_detail_density",
        )
    return (x + math.sin(count * 0.9 + swing) * 0.025, y, z - count * dz)


def bell_proxy(name: str, loc: tuple[float, float, float], scale: float = 1.0) -> None:
    cyl(f"{name}_body", loc, 0.085 * scale, 0.16 * scale, MAT["brass"], vertices=24, collection="PC_V5_detail_density")
    torus(f"{name}_rim", (loc[0], loc[1], loc[2] - 0.08 * scale), 0.085 * scale, 0.008 * scale, MAT["brass"], collection="PC_V5_detail_density")
    sphere(f"{name}_clapper", (loc[0], loc[1], loc[2] - 0.13 * scale), 0.025 * scale, MAT["metal"], collection="PC_V5_detail_density")


def radio_proxy(name: str, loc: tuple[float, float, float], scale: float = 1.0, rot_z: float = 0.0) -> None:
    box(f"{name}_body", loc, (0.22 * scale, 0.045, 0.15 * scale), MAT["metal"], rot=(0, 0, rot_z), collection="PC_V5_detail_density")
    cyl(f"{name}_speaker", (loc[0] - 0.045 * scale, loc[1] - 0.032, loc[2]), 0.034 * scale, 0.012, MAT["void"], vertices=18, rot=(math.radians(90), 0, 0), collection="PC_V5_detail_density")
    cyl(f"{name}_dial", (loc[0] + 0.060 * scale, loc[1] - 0.034, loc[2] + 0.035 * scale), 0.016 * scale, 0.012, MAT["brass"], vertices=14, rot=(math.radians(90), 0, 0), collection="PC_V5_detail_density")


def candle_proxy(name: str, loc: tuple[float, float, float], height: float = 0.18) -> None:
    cyl(f"{name}_wax", (loc[0], loc[1], loc[2] + height * 0.5), 0.023, height, MAT["wax"], vertices=14, collection="PC_V5_detail_density")
    sphere(f"{name}_flame", (loc[0], loc[1] - 0.008, loc[2] + height + 0.045), 0.030, MAT["brass"], scale=(0.6, 0.6, 1.35), collection="PC_V5_detail_density")


def add_reference_plane(name: str, image_name: str, loc: tuple[float, float, float], size: tuple[float, float], rot=(0, 0, 0)) -> None:
    path = REF_ROOT / image_name
    mat = make_image_mat(f"PC_V4_REF_{name}", path)
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = f"PC_V4_REF_{name}"
    obj.dimensions = (size[0], size[1], 1)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(obj, mat)
    move_to(obj, "PC_V4_reference_planes")


def add_reference_planes() -> None:
    # Height is normalized to 4.2m, matching the target's roughly 3.4m creature plus roof relics.
    add_reference_plane("front_ortho", "enhanced/front_ortho_clean_x4.png", (0, -2.55, 2.1), (1.85, 4.2), (math.radians(90), 0, 0))
    add_reference_plane("back_ortho", "enhanced/back_ortho_clean_x4.png", (0, 2.55, 2.1), (2.25, 4.2), (math.radians(90), 0, math.radians(180)))
    add_reference_plane("side_ortho", "enhanced/side_ortho_clean_x4.png", (2.25, 0, 2.1), (1.85, 4.2), (math.radians(90), 0, math.radians(90)))


def import_blockout_for_scale() -> None:
    if not INPUT_GLB.exists():
        raise FileNotFoundError(INPUT_GLB)
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(INPUT_GLB))
    for obj in [obj for obj in bpy.context.scene.objects if obj not in before]:
        obj.name = f"PC_V4_BLOCKOUT_SCALE_{obj.name}"
        obj.hide_render = True
        if obj.type == "MESH":
            name = obj.name.lower()
            if any(k in name for k in ("body", "arm", "leg", "hand", "foot", "wrap", "mask")):
                assign(obj, MAT["cloth"])
            elif any(k in name for k in ("bell", "chain", "cross", "radio", "dial")):
                assign(obj, MAT["metal"])
            else:
                assign(obj, MAT["wood"])
            obj.display_type = "TEXTURED"
            shade(obj, 0.004)
            move_to(obj, "PC_V4_imported_blockout_scale_reference")


def add_v4_primary_silhouette() -> None:
    # Shrine: wider and more triangular than V3, with rear depth enforced by the side crop.
    box("PC_V4_shrine_front_rotten_wall", (0, -0.42, 2.98), (1.82, 0.12, 1.45), MAT["wood"])
    box("PC_V4_shrine_rear_rotten_wall", (0, 0.54, 2.95), (1.92, 0.12, 1.55), MAT["wood"])
    box("PC_V4_shrine_left_side_wall", (-0.98, 0.06, 2.92), (0.12, 1.06, 1.52), MAT["wood"])
    box("PC_V4_shrine_right_side_wall", (0.98, 0.06, 2.92), (0.12, 1.06, 1.52), MAT["wood"])
    box("PC_V4_roof_left_steep_slab", (-0.54, 0.02, 3.78), (1.30, 1.20, 0.12), MAT["wood"], rot=(0, math.radians(-25), 0))
    box("PC_V4_roof_right_steep_slab", (0.54, 0.02, 3.78), (1.30, 1.20, 0.12), MAT["wood"], rot=(0, math.radians(25), 0))
    box("PC_V4_roof_ridge_heavy_rot", (0, 0.02, 4.07), (0.16, 1.22, 0.15), MAT["raw_wood"])

    # Hunched human mass and readable door-mask head.
    sphere("PC_V4_hunched_upper_back_mass", (0, -0.18, 2.18), 0.42, MAT["cloth"], scale=(0.95, 0.72, 0.86))
    sphere("PC_V4_left_shoulder_under_mask", (-0.43, -0.72, 2.20), 0.22, MAT["cloth"], scale=(1.0, 0.58, 0.72))
    sphere("PC_V4_right_shoulder_under_mask", (0.43, -0.72, 2.20), 0.22, MAT["cloth"], scale=(1.0, 0.58, 0.72))
    hood = torus("PC_V6_head_narrow_hood_oval_ring", (0, -1.02, 2.87), 0.30, 0.040, MAT["cloth"], rot=(math.radians(90), 0, 0))
    hood.scale.x = 0.74
    hood.scale.z = 1.18
    sphere("PC_V6_head_vertical_black_void", (0, -1.09, 2.90), 0.23, MAT["void"], scale=(0.62, 0.065, 1.30))
    box("PC_V6_long_door_mask_front", (0, -1.24, 2.02), (0.34, 0.075, 1.54), MAT["wood"])
    box("PC_V6_door_mask_left_pale_plank", (-0.105, -1.285, 2.02), (0.040, 0.020, 1.44), MAT["raw_wood"])
    box("PC_V6_door_mask_center_split", (0, -1.292, 2.05), (0.030, 0.018, 1.38), MAT["raw_wood"])
    box("PC_V6_door_mask_right_shadow_plank", (0.115, -1.286, 2.02), (0.034, 0.020, 1.36), MAT["metal"])

    # Bent arms and legs positioned from the orthographic front/side proportions.
    for side, sign in [("left", -1), ("right", 1)]:
        box(f"PC_V4_{side}_long_upper_arm_wrapped", (sign * 0.61, -0.54, 1.82), (0.16, 0.12, 0.62), MAT["cloth"], rot=(0, 0, math.radians(sign * -15)))
        box(f"PC_V4_{side}_long_forearm_wrapped", (sign * 0.68, -0.58, 1.36), (0.15, 0.11, 0.58), MAT["cloth"], rot=(0, 0, math.radians(sign * 9)))
        sphere(f"PC_V4_{side}_large_hanging_hand", (sign * 0.72, -0.62, 1.02), 0.11, MAT["cloth"], scale=(0.75, 0.48, 1.24))
        box(f"PC_V6_{side}_wrapped_thigh", (sign * 0.25, -0.10, 1.10), (0.18, 0.16, 0.78), MAT["cloth"], rot=(0, 0, math.radians(sign * 5)))
        box(f"PC_V6_{side}_wrapped_shin", (sign * 0.31, -0.08, 0.48), (0.145, 0.13, 0.75), MAT["cloth"], rot=(0, 0, math.radians(sign * -5)))
        sphere(f"PC_V6_{side}_splayed_bare_foot_block", (sign * 0.34, -0.30, 0.08), 0.12, MAT["wrap_highlight"], scale=(1.75, 0.72, 0.40))

    # Disgusting rear silhouette: not just clutter, but sagging black mass and broken openings.
    box("PC_V4_back_black_rotten_hollow", (0, 0.74, 2.72), (1.28, 0.08, 1.12), MAT["void"])
    for i, x in enumerate([-0.58, -0.36, -0.16, 0.08, 0.31, 0.55]):
        box(f"PC_V4_back_sagging_shroud_{i:02d}", (x, 0.86, 2.02), (0.08, 0.04, 1.05 - i * 0.045), MAT["cloth"], rot=(0, 0, math.radians((i - 2) * 4)))
    for i, (x, z) in enumerate([(-0.46, 3.12), (0.0, 3.28), (0.48, 2.95)]):
        sphere(f"PC_V4_back_rotten_dark_hole_{i}", (x, 0.89, z), 0.16, MAT["void"], scale=(1.1, 0.18, 1.25))


def add_v4_relic_density_guides() -> None:
    # A controlled layout grid that later Geometry Nodes/scattering can replace with hero props.
    for i, x in enumerate([-0.82, -0.58, -0.34, -0.10, 0.14, 0.38, 0.62, 0.86]):
        z = 3.48 + 0.12 * math.sin(i)
        cyl(f"PC_V4_chain_anchor_front_{i:02d}", (x, -0.78, z), 0.035, 0.02, MAT["metal"], vertices=16, rot=(math.radians(90), 0, 0))
        cyl(f"PC_V4_chain_guide_drop_front_{i:02d}", (x, -0.79, z - 0.38), 0.008, 0.76, MAT["metal"], vertices=8)
        if i % 2 == 0:
            cyl(f"PC_V4_bell_proxy_front_{i:02d}", (x, -0.80, z - 0.76), 0.075, 0.13, MAT["brass"], vertices=20)

    for i, x in enumerate([-0.70, -0.42, -0.15, 0.18, 0.48, 0.74]):
        box(f"PC_V4_radio_clock_photo_proxy_{i:02d}", (x, -0.72, 3.04 + 0.25 * math.sin(i * 1.5)), (0.22, 0.04, 0.16), MAT["paper" if i % 3 == 0 else "metal"], rot=(0, 0, math.radians((i - 2) * 5)))

    for i, x in enumerate([-0.72, -0.44, 0.42, 0.72]):
        cyl(f"PC_V4_candle_proxy_{i:02d}", (x, -0.78, 2.30), 0.026, 0.22, MAT["wax"], vertices=14)


def add_v5_wrapped_human_detail() -> None:
    random.seed(505)
    # Dense wrap bands make the human portion read closer to the target instead of blocky limbs.
    for side, sign in [("left", -1), ("right", 1)]:
        for i, z in enumerate([0.38, 0.50, 0.62, 0.78, 0.94, 1.10]):
            box(
                f"PC_V5_{side}_leg_wrap_band_{i:02d}",
                (sign * (0.27 + random.uniform(-0.025, 0.025)), -0.34, z),
                (0.24, 0.035, 0.034),
                MAT["wrap_highlight"] if i % 4 == 0 else MAT["cloth"],
                rot=(0, 0, math.radians(sign * random.uniform(12, 26))),
                collection="PC_V5_detail_density",
            )
        for i, z in enumerate([1.22, 1.40, 1.56, 1.74, 1.92]):
            box(
                f"PC_V5_{side}_arm_wrap_band_{i:02d}",
                (sign * (0.62 + random.uniform(-0.035, 0.035)), -0.78, z),
                (0.22, 0.032, 0.032),
                MAT["cloth"],
                rot=(0, 0, math.radians(sign * random.uniform(-28, -12))),
                collection="PC_V5_detail_density",
            )
        for finger in range(4):
            box(
                f"PC_V5_{side}_long_finger_{finger}",
                (sign * (0.70 + finger * 0.025), -0.72, 0.86 - finger * 0.012),
                (0.022, 0.030, 0.16),
                MAT["cloth"],
                rot=(0, 0, math.radians(sign * (3 + finger * 4))),
                collection="PC_V5_detail_density",
            )

    for i, x in enumerate([-0.19, -0.11, -0.04, 0.04, 0.12, 0.20]):
        box(
            f"PC_V5_head_mask_hanging_fray_{i:02d}",
            (x, -1.31, 1.36 - i * 0.014),
            (0.045, 0.026, random.uniform(0.52, 0.92)),
            MAT["cloth"],
            rot=(0, 0, math.radians(random.uniform(-4, 4))),
            collection="PC_V5_detail_density",
        )


def add_v5_shrine_density() -> None:
    random.seed(606)
    # Broken shingles and crosses along the roofline.
    idx = 0
    for side, sign, angle in [("left", -1, -24), ("right", 1, 24)]:
        for row in range(4):
            for col in range(5):
                x = sign * (0.22 + col * 0.145)
                y = -0.62 + row * 0.16
                z = 3.53 + row * 0.075 + random.uniform(-0.02, 0.02)
                box(
                    f"PC_V5_roof_broken_shingle_{side}_{idx:02d}",
                    (x, y, z),
                    (random.uniform(0.15, 0.28), 0.035, 0.035),
                    MAT["raw_wood"] if idx % 3 else MAT["wood"],
                    rot=(0, math.radians(angle), math.radians(random.uniform(-12, 12))),
                    collection="PC_V5_detail_density",
                )
                idx += 1

    for i, x in enumerate([-0.88, -0.50, 0.0, 0.50, 0.88]):
        box(f"PC_V5_roof_cross_stem_{i}", (x, -0.42, 4.16 + (0.10 if i == 2 else 0.0)), (0.035, 0.035, 0.34), MAT["brass"], collection="PC_V5_detail_density")
        box(f"PC_V5_roof_cross_bar_{i}", (x, -0.42, 4.24 + (0.10 if i == 2 else 0.0)), (0.18, 0.035, 0.035), MAT["brass"], collection="PC_V5_detail_density")

    # Front shrine objects.
    relics = [
        (-0.68, 3.26, "radio"), (-0.44, 3.44, "clock"), (-0.18, 3.12, "photo"),
        (0.16, 3.42, "radio"), (0.44, 3.18, "clock"), (0.70, 3.35, "photo"),
        (-0.72, 2.78, "photo"), (-0.42, 2.58, "radio"), (0.44, 2.62, "radio"), (0.72, 2.80, "photo"),
    ]
    for i, (x, z, kind) in enumerate(relics):
        if kind == "radio":
            radio_proxy(f"PC_V5_front_relic_radio_{i:02d}", (x, -0.82, z), random.uniform(0.8, 1.15), math.radians(random.uniform(-4, 4)))
        elif kind == "clock":
            cyl(f"PC_V5_front_relic_clock_face_{i:02d}", (x, -0.84, z), 0.075, 0.018, MAT["paper"], vertices=28, rot=(math.radians(90), 0, 0), collection="PC_V5_detail_density")
            torus(f"PC_V5_front_relic_clock_rim_{i:02d}", (x, -0.85, z), 0.075, 0.007, MAT["brass"], rot=(math.radians(90), 0, 0), collection="PC_V5_detail_density")
        else:
            box(f"PC_V5_front_relic_photo_frame_{i:02d}", (x, -0.82, z), (0.14, 0.026, 0.19), MAT["wood"], rot=(0, 0, math.radians(random.uniform(-5, 5))), collection="PC_V5_detail_density")
            box(f"PC_V5_front_relic_photo_void_{i:02d}", (x, -0.84, z), (0.06, 0.012, 0.08), MAT["void"], collection="PC_V5_detail_density")

    for i, x in enumerate([-0.86, -0.63, -0.40, -0.17, 0.17, 0.40, 0.63, 0.86]):
        end = chain_links(f"PC_V5_front_chain_curtain_{i:02d}", (x, -0.88, 3.62 + random.uniform(-0.08, 0.10)), random.randint(6, 11), 0.105, MAT["metal"], random.uniform(0.72, 1.05), random.random() * 4)
        if i % 2 == 0:
            bell_proxy(f"PC_V5_front_hanging_bell_{i:02d}", (end[0], end[1], end[2] - 0.08), random.uniform(0.7, 1.1))

    for i, (x, z) in enumerate([(-0.76, 2.62), (-0.52, 2.76), (0.52, 2.72), (0.76, 2.58), (0.0, 3.24)]):
        candle_proxy(f"PC_V5_candle_cluster_{i:02d}", (x, -0.88, z), random.uniform(0.14, 0.26))


def add_v5_back_disgust_detail() -> None:
    random.seed(707)
    for i, x in enumerate([-0.72, -0.50, -0.30, -0.10, 0.14, 0.36, 0.58, 0.80]):
        box(
            f"PC_V5_back_rotten_vertical_plank_{i:02d}",
            (x, 0.93, 2.78 + random.uniform(-0.10, 0.12)),
            (random.uniform(0.08, 0.14), 0.055, random.uniform(0.92, 1.48)),
            MAT["wood"] if i % 2 else MAT["raw_wood"],
            rot=(0, 0, math.radians(random.uniform(-6, 6))),
            collection="PC_V5_detail_density",
        )
    for i, x in enumerate([-0.60, -0.36, -0.12, 0.12, 0.36, 0.60]):
        box(
            f"PC_V5_back_tar_shroud_{i:02d}",
            (x, 1.00, 2.12),
            (random.uniform(0.06, 0.10), 0.035, random.uniform(0.72, 1.22)),
            MAT["cloth"],
            rot=(0, 0, math.radians(random.uniform(-8, 8))),
            collection="PC_V5_detail_density",
        )
    for i, x in enumerate([-0.76, -0.48, -0.22, 0.02, 0.26, 0.52, 0.78]):
        end = chain_links(f"PC_V5_back_chain_curtain_{i:02d}", (x, 1.02, 3.50 + random.uniform(-0.06, 0.10)), random.randint(6, 12), 0.105, MAT["metal"], random.uniform(0.65, 0.95), random.random() * 5)
        if i % 3 != 1:
            bell_proxy(f"PC_V5_back_dead_bell_{i:02d}", (end[0], end[1], end[2] - 0.06), random.uniform(0.55, 0.9))
    for i, (x, z) in enumerate([(-0.46, 3.10), (0.02, 3.28), (0.46, 2.92), (-0.18, 2.62)]):
        sphere(f"PC_V5_back_black_rot_opening_{i:02d}", (x, 1.035, z), 0.15, MAT["void"], scale=(1.0, 0.12, 1.25), collection="PC_V5_detail_density")
        torus(f"PC_V5_back_rot_opening_rim_{i:02d}", (x, 1.02, z), 0.15, 0.008, MAT["metal"], rot=(math.radians(90), 0, 0), collection="PC_V5_detail_density")


def add_v8_balanced_end_goal_correction() -> None:
    random.seed(909)
    # Make the shrine face broken and dense without turning into a flat toy wall.
    for i, x in enumerate([-0.84, -0.68, -0.51, -0.34, -0.18, -0.02, 0.15, 0.33, 0.52, 0.71, 0.87]):
        z = 3.04 + random.uniform(-0.05, 0.08)
        box(
            f"PC_V8_front_weathered_plank_{i:02d}",
            (x, -0.965, z),
            (random.uniform(0.045, 0.085), 0.024, random.uniform(0.92, 1.42)),
            MAT["raw_wood"] if i % 4 == 1 else MAT["wood"],
            rot=(0, 0, math.radians(random.uniform(-3.5, 3.5))),
            collection="PC_V8_balanced_end_goal",
        )
    for i, (x, z) in enumerate([(-0.57, 3.26), (-0.28, 3.52), (0.26, 3.32), (0.61, 3.03), (0.02, 2.72)]):
        box(
            f"PC_V8_small_shadow_gap_{i:02d}",
            (x, -0.982, z),
            (random.uniform(0.10, 0.18), 0.014, random.uniform(0.12, 0.25)),
            MAT["void"],
            rot=(0, 0, math.radians(random.uniform(-8, 8))),
            collection="PC_V8_balanced_end_goal",
        )

    # Head/hood: clear black void under a wet cloth arch, with a dirty vertical door-mask below.
    hood = bpy.data.objects.get("PC_V6_head_narrow_hood_oval_ring")
    if hood:
        assign(hood, MAT["cloth"])
        hood.scale.x *= 0.62
        hood.scale.z *= 1.24
    for i, (x, z, h, rz) in enumerate([(-0.22, 2.65, 0.64, -9), (-0.15, 2.40, 0.52, -4), (0.15, 2.40, 0.52, 4), (0.22, 2.65, 0.64, 9)]):
        box(
            f"PC_V8_wet_hood_lip_{i:02d}",
            (x, -1.345, z),
            (0.062, 0.036, h),
            MAT["cloth"],
            rot=(0, 0, math.radians(rz)),
            collection="PC_V8_balanced_end_goal",
        )
    sphere("PC_V8_head_black_inner_void", (0, -1.372, 2.78), 0.24, MAT["void"], scale=(0.48, 0.05, 1.38), collection="PC_V8_balanced_end_goal")

    for i, (x, h) in enumerate([(-0.145, 1.36), (-0.073, 1.52), (0.0, 1.58), (0.074, 1.46), (0.144, 1.30)]):
        box(
            f"PC_V8_face_door_rotten_strip_{i:02d}",
            (x, -1.405, 1.80),
            (0.038, 0.024, h),
            MAT["raw_wood"] if i != 2 else MAT["wood"],
            rot=(0, 0, math.radians(random.uniform(-2.4, 2.4))),
            collection="PC_V8_balanced_end_goal",
        )
    for i, z in enumerate([2.28, 1.98, 1.68, 1.40]):
        box(
            f"PC_V8_face_mask_stitch_{i:02d}",
            (0, -1.425, z),
            (0.23 - i * 0.022, 0.014, 0.020),
            MAT["metal"],
            rot=(0, 0, math.radians(13 if i % 2 else -13)),
            collection="PC_V8_balanced_end_goal",
        )

    # Layer organic bandages over the blockout limbs instead of leaving rectangular legs.
    for side, sign in [("left", -1), ("right", 1)]:
        for i, z in enumerate([0.34, 0.47, 0.60, 0.75, 0.91, 1.08]):
            box(
                f"PC_V8_{side}_shin_bandage_{i:02d}",
                (sign * (0.31 + random.uniform(-0.026, 0.026)), -0.40, z),
                (0.235, 0.030, 0.030),
                MAT["wrap_highlight"] if i % 3 == 0 else MAT["cloth"],
                rot=(0, 0, math.radians(sign * random.uniform(16, 30))),
                collection="PC_V8_balanced_end_goal",
            )
        for i, z in enumerate([1.25, 1.42, 1.60, 1.78, 1.96]):
            box(
                f"PC_V8_{side}_arm_bandage_{i:02d}",
                (sign * (0.64 + random.uniform(-0.035, 0.035)), -0.82, z),
                (0.220, 0.028, 0.028),
                MAT["wrap_highlight"] if i % 4 == 0 else MAT["cloth"],
                rot=(0, 0, math.radians(sign * random.uniform(-32, -15))),
                collection="PC_V8_balanced_end_goal",
            )

    # More hanging silhouette in the spirit of the target, but controlled so the head stays identifiable.
    for i, x in enumerate([-0.95, -0.80, -0.64, -0.48, -0.31, -0.17, 0.17, 0.32, 0.49, 0.66, 0.83, 0.97]):
        z0 = random.uniform(3.38, 3.80)
        end = chain_links(f"PC_V8_front_chain_curtain_{i:02d}", (x, -1.03, z0), random.randint(7, 13), 0.095, MAT["metal"], random.uniform(0.58, 0.86), random.random() * 5)
        if i in [0, 3, 8, 11]:
            bell_proxy(f"PC_V8_front_hanging_bell_{i:02d}", (end[0], end[1] - 0.02, end[2] - 0.08), random.uniform(0.60, 0.92))
        elif i in [1, 5, 9]:
            box(f"PC_V8_front_hanging_key_{i:02d}", (end[0], end[1] - 0.02, end[2] - 0.12), (0.022, 0.014, 0.18), MAT["brass"], collection="PC_V8_balanced_end_goal")
            torus(f"PC_V8_front_hanging_key_ring_{i:02d}", (end[0], end[1] - 0.02, end[2] + 0.005), 0.033, 0.004, MAT["brass"], rot=(math.radians(90), 0, 0), collection="PC_V8_balanced_end_goal")
        else:
            box(f"PC_V8_front_dark_tassel_{i:02d}", (end[0], end[1] - 0.01, end[2] - 0.20), (0.040, 0.020, random.uniform(0.28, 0.55)), MAT["cloth"], rot=(0, 0, math.radians(random.uniform(-5, 5))), collection="PC_V8_balanced_end_goal")

    # Back: rotten ribbing plus holes, brighter than V6 so it does not collapse to unreadable black.
    for i, x in enumerate([-0.76, -0.58, -0.40, -0.23, -0.06, 0.12, 0.30, 0.50, 0.70]):
        box(
            f"PC_V8_back_rotten_rib_{i:02d}",
            (x, 1.075, 2.55 + random.uniform(-0.08, 0.12)),
            (random.uniform(0.052, 0.090), 0.038, random.uniform(0.96, 1.58)),
            MAT["raw_wood"] if i % 3 == 0 else MAT["cloth"],
            rot=(0, 0, math.radians(random.uniform(-7, 7))),
            collection="PC_V8_balanced_end_goal",
        )
    for i, (x, z) in enumerate([(-0.48, 3.18), (-0.18, 2.82), (0.18, 3.28), (0.48, 2.78)]):
        sphere(f"PC_V8_back_small_rot_void_{i:02d}", (x, 1.110, z), 0.12, MAT["void"], scale=(1.05, 0.075, 1.35), collection="PC_V8_balanced_end_goal")


def add_v9_body_fill_correction() -> None:
    random.seed(1009)
    # Nested body shapes: dark inner bulk, damp cloth outer lobes, then thin wrap cuts on top.
    # This removes the visible empty lanes between V8's rectangular strips while keeping the body readable.
    sphere("PC_V9_inner_hunched_torso_core", (0.0, -0.62, 1.76), 0.46, MAT["cloth"], scale=(0.82, 0.44, 1.72), collection="PC_V9_body_fill")
    sphere("PC_V9_upper_chest_under_mask_fill", (0.0, -0.76, 2.18), 0.34, MAT["cloth"], scale=(0.78, 0.36, 0.86), collection="PC_V9_body_fill")
    sphere("PC_V9_lower_belly_sagging_fill", (0.0, -0.52, 1.18), 0.34, MAT["cloth"], scale=(0.74, 0.40, 0.86), collection="PC_V9_body_fill")
    sphere("PC_V9_left_hip_cloth_fill", (-0.25, -0.48, 1.12), 0.25, MAT["cloth"], scale=(0.78, 0.34, 0.92), collection="PC_V9_body_fill")
    sphere("PC_V9_right_hip_cloth_fill", (0.25, -0.48, 1.12), 0.25, MAT["cloth"], scale=(0.78, 0.34, 0.92), collection="PC_V9_body_fill")

    # Shape-in-shape mask layering: black void inside hood, dirty door slats over the body, thin stitch lines over slats.
    sphere("PC_V9_head_void_deepest_inner_shape", (0, -1.438, 2.80), 0.205, MAT["void"], scale=(0.46, 0.040, 1.42), collection="PC_V9_body_fill")
    for i, (x, height, z) in enumerate([(-0.16, 1.44, 1.77), (-0.08, 1.60, 1.82), (0.0, 1.70, 1.86), (0.08, 1.55, 1.80), (0.16, 1.38, 1.75)]):
        box(
            f"PC_V9_front_mask_nested_plank_{i:02d}",
            (x, -1.455, z),
            (0.046, 0.020, height),
            MAT["raw_wood"] if i in [1, 2, 3] else MAT["wood"],
            rot=(0, 0, math.radians(random.uniform(-2.0, 2.0))),
            collection="PC_V9_body_fill",
        )
    for i, z in enumerate([2.24, 2.02, 1.78, 1.54, 1.31]):
        box(
            f"PC_V9_mask_tight_stitch_{i:02d}",
            (0, -1.475, z),
            (0.20 - i * 0.018, 0.012, 0.018),
            MAT["metal"],
            rot=(0, 0, math.radians(-14 if i % 2 == 0 else 14)),
            collection="PC_V9_body_fill",
        )

    # Continuous limbs under the bandage strips, so arms/legs no longer look like floating ladders.
    for side, sign in [("left", -1), ("right", 1)]:
        sphere(f"PC_V9_{side}_upper_arm_filled_muscle", (sign * 0.58, -0.70, 1.77), 0.16, MAT["cloth"], scale=(0.72, 0.36, 1.72), collection="PC_V9_body_fill")
        sphere(f"PC_V9_{side}_forearm_filled_muscle", (sign * 0.67, -0.72, 1.28), 0.14, MAT["cloth"], scale=(0.64, 0.34, 1.52), collection="PC_V9_body_fill")
        sphere(f"PC_V9_{side}_thigh_filled_column", (sign * 0.25, -0.36, 0.93), 0.16, MAT["cloth"], scale=(0.62, 0.35, 1.82), collection="PC_V9_body_fill")
        sphere(f"PC_V9_{side}_shin_filled_column", (sign * 0.31, -0.34, 0.38), 0.135, MAT["cloth"], scale=(0.58, 0.32, 1.72), collection="PC_V9_body_fill")
        sphere(f"PC_V9_{side}_ankle_to_foot_fill", (sign * 0.33, -0.31, 0.08), 0.105, MAT["wrap_highlight"], scale=(1.55, 0.52, 0.34), collection="PC_V9_body_fill")

        for i, z in enumerate([0.30, 0.42, 0.55, 0.69, 0.84, 1.00, 1.16]):
            box(
                f"PC_V9_{side}_leg_gap_cover_wrap_{i:02d}",
                (sign * (0.29 + random.uniform(-0.020, 0.020)), -0.54, z),
                (0.245, 0.026, 0.026),
                MAT["wrap_highlight"] if i % 3 == 1 else MAT["cloth"],
                rot=(0, 0, math.radians(sign * random.uniform(18, 34))),
                collection="PC_V9_body_fill",
            )
        for i, z in enumerate([1.20, 1.36, 1.54, 1.72, 1.90, 2.05]):
            box(
                f"PC_V9_{side}_arm_gap_cover_wrap_{i:02d}",
                (sign * (0.64 + random.uniform(-0.028, 0.028)), -0.92, z),
                (0.225, 0.024, 0.024),
                MAT["wrap_highlight"] if i % 4 == 2 else MAT["cloth"],
                rot=(0, 0, math.radians(sign * random.uniform(-34, -16))),
                collection="PC_V9_body_fill",
            )

    # Fill between front mask slats and torso with dark dangling cloth so no empty vertical slots remain.
    for i, x in enumerate([-0.205, -0.125, -0.045, 0.045, 0.125, 0.205]):
        box(
            f"PC_V9_mask_to_torso_dark_undercloth_{i:02d}",
            (x, -1.000, 1.36 - abs(x) * 0.45),
            (0.050, 0.070, random.uniform(0.82, 1.22)),
            MAT["cloth"],
            rot=(0, 0, math.radians(random.uniform(-3, 3))),
            collection="PC_V9_body_fill",
        )


def add_lighting_and_cameras() -> None:
    bpy.ops.object.light_add(type="AREA", location=(0, -4.0, 5.3))
    key = bpy.context.object
    key.name = "PC_V4_Key_Rainy_Studio_Light"
    key.data.energy = 700
    key.data.size = 4.8

    bpy.ops.object.camera_add(location=(3.2, -6.4, 2.55), rotation=(math.radians(69), 0, math.radians(27)))
    bpy.context.scene.camera = bpy.context.object


def set_origin_and_units() -> None:
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and not obj.name.startswith("PC_V4_REF_")]
    corners = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    min_z = min(c.z for c in corners)
    center_x = (min(c.x for c in corners) + max(c.x for c in corners)) * 0.5
    center_y = (min(c.y for c in corners) + max(c.y for c in corners)) * 0.5
    for obj in meshes:
        obj.location.x -= center_x
        obj.location.y -= center_y
        obj.location.z -= min_z


def export_outputs() -> None:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_BLEND))

    for obj in bpy.context.scene.objects:
        obj.select_set(False)
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH" and not obj.name.startswith("PC_V4_REF_") and not obj.name.startswith("PC_V4_BLOCKOUT_SCALE_"):
            obj.select_set(True)

    bpy.ops.export_scene.gltf(
        filepath=str(OUTPUT_GLB),
        export_format="GLB",
        export_apply=True,
        use_selection=True,
        export_yup=True,
        export_materials="EXPORT",
    )


def main() -> None:
    print("Penance Carrier V9 body-fill pass starting...", flush=True)
    random.seed(1909)
    clear_scene()
    create_materials()
    add_reference_planes()
    import_blockout_for_scale()
    add_v4_primary_silhouette()
    add_v4_relic_density_guides()
    add_v5_wrapped_human_detail()
    add_v5_shrine_density()
    add_v5_back_disgust_detail()
    add_v8_balanced_end_goal_correction()
    add_v9_body_fill_correction()
    add_lighting_and_cameras()
    set_origin_and_units()
    export_outputs()
    print("Saved blend:", OUTPUT_BLEND, flush=True)
    print("Exported GLB:", OUTPUT_GLB, flush=True)


if __name__ == "__main__":
    main()
