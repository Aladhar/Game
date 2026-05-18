"""
Penance Carrier end-goal v3 model pass.

This pass uses Penance_End_Goal.png as the target direction:
- hunched ritual carrier
- house/shrine load with steep roof
- face/door mask void
- many chains, ropes, bells, crosses
- radios, speakers, clocks, cassettes, photos
- candle clusters and wet/rusted/aged material placeholders

Run from the Godot project root:
  blender --background --factory-startup --python tools/blender/penance_carrier_end_goal_v3.py

Input:
  assets/models/enemies/penance_carrier/penance_carrier_blockout_v1.glb

Outputs:
  assets/models/enemies/penance_carrier/blender_work/penance_carrier_end_goal_v3.blend
  assets/models/enemies/penance_carrier/penance_carrier_end_goal_v3.glb
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
INPUT_GLB = ASSET_ROOT / "penance_carrier_blockout_v1.glb"
WORK_DIR = ASSET_ROOT / "blender_work"
OUTPUT_BLEND = WORK_DIR / "penance_carrier_end_goal_v3.blend"
OUTPUT_GLB = ASSET_ROOT / "penance_carrier_end_goal_v3.glb"

COLLECTION_NAME = "PC_EndGoal_V3_detail"

MAT = {}


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def ensure_collection(name: str) -> bpy.types.Collection:
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


def move_to_collection(obj: bpy.types.Object, collection: str = COLLECTION_NAME) -> bpy.types.Object:
    col = ensure_collection(collection)
    for current in list(obj.users_collection):
        current.objects.unlink(obj)
    col.objects.link(obj)
    return obj


def make_mat(
    name: str,
    color: tuple[float, float, float, float],
    roughness: float,
    metallic: float = 0.0,
    emission: tuple[float, float, float, float] | None = None,
    emission_strength: float = 0.0,
) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
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


def create_materials() -> None:
    MAT["soaked_cloth"] = make_mat("PC_V3_soaked_black_cloth", (0.035, 0.034, 0.032, 1), 0.91)
    MAT["wet_wrap"] = make_mat("PC_V3_wet_gray_wraps", (0.125, 0.116, 0.104, 1), 0.88)
    MAT["hood_dark"] = make_mat("PC_V3_head_dark_wet_hood", (0.055, 0.052, 0.048, 1), 0.94)
    MAT["weathered_wood"] = make_mat("PC_V3_split_weathered_wood", (0.145, 0.112, 0.079, 1), 0.91)
    MAT["dead_wood"] = make_mat("PC_V3_blackened_dead_wood", (0.072, 0.061, 0.052, 1), 0.96)
    MAT["pale_splinter"] = make_mat("PC_V3_pale_raw_splinter_edges", (0.46, 0.39, 0.285, 1), 0.87)
    MAT["wood_edge"] = make_mat("PC_V3_raw_splintered_wood_edges", (0.31, 0.245, 0.165, 1), 0.86)
    MAT["rusted_iron"] = make_mat("PC_V3_rusted_iron", (0.135, 0.105, 0.086, 1), 0.82, 0.85)
    MAT["corroded_brass"] = make_mat("PC_V3_corroded_brass", (0.42, 0.285, 0.115, 1), 0.68, 1.0)
    MAT["paper"] = make_mat("PC_V3_old_paper_photos", (0.48, 0.405, 0.285, 1), 0.9)
    MAT["radio"] = make_mat("PC_V3_old_radio_plastic_metal", (0.18, 0.16, 0.14, 1), 0.74, 0.25)
    MAT["glass"] = make_mat("PC_V3_dark_glass_lenses", (0.05, 0.075, 0.078, 0.62), 0.22)
    MAT["void"] = make_mat("PC_V3_mask_void_black", (0.0, 0.0, 0.0, 1), 1.0)
    MAT["wax"] = make_mat("PC_V3_dirty_wax", (0.58, 0.45, 0.29, 1), 0.72)
    MAT["flame"] = make_mat("PC_V3_candle_flame_emissive", (1.0, 0.45, 0.08, 1), 0.25, 0.0, (1.0, 0.36, 0.06, 1), 1.4)
    MAT["rope"] = make_mat("PC_V3_soaked_rope", (0.16, 0.115, 0.075, 1), 0.94)


def assign(obj: bpy.types.Object, mat: bpy.types.Material) -> bpy.types.Object:
    if obj.type == "MESH":
        obj.data.materials.clear()
        obj.data.materials.append(mat)
    return obj


def shade(obj: bpy.types.Object, smooth: bool = True, bevel: float = 0.0, bevel_segments: int = 1) -> bpy.types.Object:
    if obj.type != "MESH":
        return obj
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    if smooth:
        try:
            bpy.ops.object.shade_smooth()
        except Exception:
            pass
    obj.select_set(False)
    if bevel > 0:
        mod = obj.modifiers.new("PC_V3_soft_beveled_edges", "BEVEL")
        mod.width = bevel
        mod.segments = bevel_segments
        mod.profile = 0.45
        normal = obj.modifiers.new("PC_V3_weighted_normals", "WEIGHTED_NORMAL")
        normal.keep_sharp = True
    return obj


def box(
    name: str,
    loc: tuple[float, float, float],
    scale: tuple[float, float, float],
    mat: bpy.types.Material,
    rot: tuple[float, float, float] = (0, 0, 0),
    bevel: float = 0.0,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(obj, mat)
    shade(obj, smooth=False, bevel=bevel, bevel_segments=1)
    return move_to_collection(obj)


def cyl(
    name: str,
    loc: tuple[float, float, float],
    radius: float,
    depth: float,
    mat: bpy.types.Material,
    vertices: int = 24,
    rot: tuple[float, float, float] = (0, 0, 0),
    bevel: float = 0.0,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    assign(obj, mat)
    shade(obj, smooth=True, bevel=bevel, bevel_segments=1)
    return move_to_collection(obj)


def sphere(
    name: str,
    loc: tuple[float, float, float],
    radius: float,
    mat: bpy.types.Material,
    scale: tuple[float, float, float] = (1, 1, 1),
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=radius, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    assign(obj, mat)
    shade(obj, smooth=True)
    return move_to_collection(obj)


def ellipsoid(
    name: str,
    loc: tuple[float, float, float],
    radius: float,
    mat: bpy.types.Material,
    scale: tuple[float, float, float],
) -> bpy.types.Object:
    obj = sphere(name, loc, radius, mat)
    obj.scale = scale
    return obj


def torus(
    name: str,
    loc: tuple[float, float, float],
    major: float,
    minor: float,
    mat: bpy.types.Material,
    rot: tuple[float, float, float] = (0, 0, 0),
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_torus_add(major_segments=24, minor_segments=8, major_radius=major, minor_radius=minor, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    assign(obj, mat)
    shade(obj, smooth=True)
    return move_to_collection(obj)


def oval_disc(
    name: str,
    loc: tuple[float, float, float],
    scale: tuple[float, float, float],
    mat: bpy.types.Material,
) -> bpy.types.Object:
    obj = sphere(name, loc, 1.0, mat)
    obj.scale = scale
    return obj


def import_blockout() -> None:
    if not INPUT_GLB.exists():
        raise FileNotFoundError(f"Missing input GLB: {INPUT_GLB}")
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(INPUT_GLB))
    imported = [obj for obj in bpy.context.scene.objects if obj not in before]
    suppress_clean_shrine = (
        "backshrine",
        "shrineradio",
        "shrinespeaker",
        "shrineclock",
        "shrinecassette",
        "shrinesound",
        "candle",
        "dangling",
        "facefray",
        "hangingcord",
        "sidepanel",
        "mask_mark",
        "blackvoid",
    )
    for obj in imported:
        if any(token in obj.name.lower() for token in suppress_clean_shrine):
            bpy.data.objects.remove(obj, do_unlink=True)

    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            name = obj.name.lower()
            if any(k in name for k in ("body", "arm", "leg", "hand", "foot", "wrap", "veil")):
                assign(obj, MAT["wet_wrap"])
            elif any(k in name for k in ("roof", "frame", "post", "beam", "plank")):
                assign(obj, MAT["dead_wood"])
            elif any(k in name for k in ("bell", "chain", "cross", "radio", "dial")):
                assign(obj, MAT["rusted_iron"])
            elif "void" in name:
                assign(obj, MAT["void"])
            shade(obj, smooth=True, bevel=0.006)
            if "blackvoid_face_slot" in name:
                obj.name = "PC_Blockout_BlackVoid_face_slot_deemphasized"
                obj.scale.x *= 0.55
                obj.scale.z *= 0.55
                obj.location.y += 0.18


def add_roof_shrine() -> None:
    # Back shrine wall and steep roof: the reference reads as a small chapel carried on the back.
    box("PC_V3_shrine_back_wall_dark_gap", (0, 0.38, 2.95), (1.96, 0.16, 1.72), MAT["void"], bevel=0.015)
    box("PC_V3_shrine_front_plank_wall", (0, -0.42, 2.9), (1.84, 0.12, 1.54), MAT["dead_wood"], bevel=0.018)
    box("PC_V3_shrine_left_side_depth", (-1.0, -0.02, 2.85), (0.12, 0.92, 1.48), MAT["dead_wood"], bevel=0.014)
    box("PC_V3_shrine_right_side_depth", (1.0, -0.02, 2.85), (0.12, 0.92, 1.48), MAT["dead_wood"], bevel=0.014)

    for i, x in enumerate([-0.84, -0.56, -0.28, 0.0, 0.28, 0.56, 0.84]):
        z_offset = 0.04 * math.sin(i * 1.7)
        mat = MAT["weathered_wood"] if i % 2 else MAT["dead_wood"]
        box(f"PC_V3_front_vertical_split_plank_{i:02d}", (x, -0.50, 2.85 + z_offset), (0.16, 0.08, 1.62), mat, rot=(0, 0, math.radians(random.uniform(-3, 3))), bevel=0.01)

    for i, x in enumerate([-0.92, -0.74, -0.52, -0.31, -0.08, 0.14, 0.36, 0.61, 0.86]):
        height = random.uniform(0.64, 1.22)
        z = 3.18 - height * 0.45 + random.uniform(-0.04, 0.08)
        box(
            f"PC_V3_front_black_mildew_drip_{i:02d}",
            (x, -0.575, z),
            (random.uniform(0.035, 0.075), 0.026, height),
            MAT["soaked_cloth"],
            rot=(0, 0, math.radians(random.uniform(-4, 4))),
            bevel=0.004,
        )

    # Sloped roof slabs and dozens of broken shingles, closer to the uploaded sheet.
    box("PC_V3_roof_left_heavy_slab", (-0.52, -0.07, 3.88), (1.28, 1.16, 0.13), MAT["dead_wood"], rot=(0, math.radians(-24), 0), bevel=0.018)
    box("PC_V3_roof_right_heavy_slab", (0.52, -0.07, 3.88), (1.28, 1.16, 0.13), MAT["dead_wood"], rot=(0, math.radians(24), 0), bevel=0.018)
    box("PC_V3_roof_ridge_splintered_beam", (0, -0.08, 4.18), (0.18, 1.18, 0.16), MAT["wood_edge"], rot=(0, 0, 0), bevel=0.012)

    shingle_id = 0
    for side, x_center, angle in [("L", -0.53, -24), ("R", 0.53, 24)]:
        for row in range(5):
            for col in range(5):
                x = x_center + (col - 2) * 0.18 * (-1 if side == "L" else 1)
                y = -0.52 + row * 0.22
                z = 3.52 + row * 0.07 + random.uniform(-0.025, 0.025)
                box(
                    f"PC_V3_broken_roof_shingle_{side}_{shingle_id:02d}",
                    (x, y, z),
                    (0.24 + random.uniform(-0.05, 0.05), 0.055, 0.055),
                    MAT["pale_splinter"] if row % 2 else MAT["wood_edge"],
                    rot=(0, math.radians(angle + random.uniform(-4, 4)), math.radians(random.uniform(-5, 5))),
                    bevel=0.006,
                )
                shingle_id += 1

    # Crosses along roofline.
    for i, x in enumerate([-0.88, -0.44, 0, 0.44, 0.88]):
        z = 4.22 + 0.1 * (1 if i == 2 else 0)
        box(f"PC_V3_roof_cross_stem_{i}", (x, -0.10, z), (0.045, 0.045, 0.36), MAT["corroded_brass"], bevel=0.004)
        box(f"PC_V3_roof_cross_bar_{i}", (x, -0.10, z + 0.08), (0.23, 0.045, 0.045), MAT["corroded_brass"], bevel=0.004)


def add_face_mask() -> None:
    # The end-goal head is a hooded mask/door in front of the shrine, not a face on the shrine wall.
    # Push the entire head assembly forward so it is readable even with chains and relics behind it.
    head_y = -1.18
    face_y = -1.30

    oval_disc("PC_V3_CLEAR_HEAD_black_oval_void_depth", (0, face_y - 0.10, 2.98), (0.25, 0.052, 0.37), MAT["void"])
    oval_disc("PC_V3_CLEAR_HEAD_front_vertical_black_oval", (0, face_y - 0.245, 2.98), (0.235, 0.03, 0.34), MAT["void"])
    hood = torus("PC_V3_CLEAR_HEAD_arched_wet_hood_ring", (0, face_y - 0.03, 2.96), 0.37, 0.052, MAT["hood_dark"], rot=(math.radians(90), 0, 0))
    hood.scale.x = 0.72
    hood.scale.y = 0.9
    hood.location.z += 0.05

    box("PC_V3_CLEAR_HEAD_left_hanging_hood_lip", (-0.285, head_y, 2.82), (0.095, 0.14, 0.70), MAT["hood_dark"], rot=(0, 0, math.radians(-7)), bevel=0.016)
    box("PC_V3_CLEAR_HEAD_right_hanging_hood_lip", (0.285, head_y, 2.82), (0.095, 0.14, 0.70), MAT["hood_dark"], rot=(0, 0, math.radians(7)), bevel=0.016)
    box("PC_V3_CLEAR_HEAD_top_hood_bridge", (0, head_y, 3.23), (0.48, 0.15, 0.12), MAT["hood_dark"], bevel=0.016)

    mask_y = face_y - 0.28
    box("PC_V3_CLEAR_HEAD_long_vertical_wooden_mask", (0, mask_y, 2.14), (0.40, 0.105, 1.58), MAT["weathered_wood"], bevel=0.016)
    box("PC_V3_CLEAR_HEAD_left_mask_board_shadow", (-0.13, mask_y - 0.065, 2.13), (0.032, 0.03, 1.47), MAT["dead_wood"], bevel=0.003)
    box("PC_V3_CLEAR_HEAD_right_mask_board_shadow", (0.14, mask_y - 0.065, 2.12), (0.028, 0.03, 1.39), MAT["dead_wood"], bevel=0.003)
    box("PC_V3_CLEAR_HEAD_center_split_in_mask", (0, mask_y - 0.075, 2.14), (0.032, 0.025, 1.42), MAT["pale_splinter"], bevel=0.004)
    box("PC_V3_CLEAR_HEAD_mask_bottom_frayed_black_cloth", (0, face_y - 0.015, 1.47), (0.48, 0.06, 0.24), MAT["soaked_cloth"], bevel=0.01)

    # Shoulders and hunched chest in front of shrine, so the mask reads as the character's head.
    ellipsoid("PC_V3_CLEAR_HEAD_hunched_left_shoulder", (-0.48, -1.04, 2.30), 0.25, MAT["wet_wrap"], (1.0, 0.58, 0.74))
    ellipsoid("PC_V3_CLEAR_HEAD_hunched_right_shoulder", (0.48, -1.04, 2.30), 0.25, MAT["wet_wrap"], (1.0, 0.58, 0.74))
    ellipsoid("PC_V3_CLEAR_HEAD_forward_cloth_chest_mass", (0, -1.02, 2.12), 0.34, MAT["soaked_cloth"], (0.95, 0.58, 1.08))

    for i, z in enumerate([1.76, 1.98, 2.22]):
        box(f"PC_V3_CLEAR_HEAD_door_binding_cross_lash_{i}", (0, mask_y - 0.075, z), (0.43, 0.035, 0.035), MAT["rusted_iron"], rot=(0, 0, math.radians(30 if i % 2 == 0 else -30)), bevel=0.003)
    box("PC_V3_CLEAR_HEAD_ritual_symbol_vertical", (0, mask_y - 0.082, 2.08), (0.032, 0.035, 0.64), MAT["rusted_iron"], bevel=0.003)

    for i, x in enumerate([-0.24, -0.15, -0.06, 0.04, 0.15, 0.25]):
        box(f"PC_V3_CLEAR_HEAD_front_frayed_cloth_strip_{i}", (x, face_y - 0.045, 1.42 - i * 0.018), (0.05, 0.032, random.uniform(0.62, 1.02)), MAT["soaked_cloth"], rot=(0, 0, math.radians(random.uniform(-6, 6))), bevel=0.004)


def add_bell(name: str, loc: tuple[float, float, float], scale: float = 1.0) -> None:
    cyl(f"{name}_body", loc, 0.115 * scale, 0.22 * scale, MAT["corroded_brass"], vertices=28, bevel=0.006)
    torus(f"{name}_lip", (loc[0], loc[1], loc[2] - 0.11 * scale), 0.115 * scale, 0.011 * scale, MAT["corroded_brass"], rot=(0, 0, 0))
    sphere(f"{name}_clapper", (loc[0], loc[1], loc[2] - 0.16 * scale), 0.035 * scale, MAT["rusted_iron"])
    torus(f"{name}_hanger_loop", (loc[0], loc[1], loc[2] + 0.13 * scale), 0.055 * scale, 0.008 * scale, MAT["rusted_iron"], rot=(math.radians(90), 0, 0))


def add_chain(name: str, start: tuple[float, float, float], length: int, dz: float = 0.115, swing: float = 0.0, scale: float = 1.0) -> tuple[float, float, float]:
    x, y, z = start
    for i in range(length):
        x_i = x + math.sin(i * 0.9 + swing) * 0.025
        y_i = y + math.cos(i * 0.7 + swing) * 0.018
        z_i = z - i * dz
        rot = (math.radians(90), 0, math.radians(90 if i % 2 else 0))
        torus(f"{name}_link_{i:02d}", (x_i, y_i, z_i), 0.035 * scale, 0.006 * scale, MAT["rusted_iron"], rot=rot)
    return (x + math.sin(length * 0.9 + swing) * 0.025, y, z - length * dz)


def add_hanging_relics() -> None:
    random.seed(12)
    anchors = [
        (-0.98, -0.64, 3.66), (-0.72, -0.66, 3.82), (-0.46, -0.68, 3.72), (-0.18, -0.70, 3.78),
        (0.18, -0.70, 3.78), (0.46, -0.68, 3.72), (0.72, -0.66, 3.82), (0.98, -0.64, 3.66),
        (-1.08, 0.10, 3.46), (1.08, 0.10, 3.46), (-1.12, 0.38, 3.18), (1.12, 0.38, 3.18),
    ]
    for idx, anchor in enumerate(anchors):
        end = add_chain(f"PC_V3_dangling_chain_{idx:02d}", anchor, random.randint(5, 11), scale=random.uniform(0.8, 1.15), swing=random.random() * 4.0)
        if idx % 3 != 1:
            add_bell(f"PC_V3_hanging_bell_{idx:02d}", (end[0], end[1], end[2] - 0.08), random.uniform(0.65, 1.05))
        else:
            box(f"PC_V3_hanging_key_{idx:02d}_stem", (end[0], end[1], end[2] - 0.08), (0.035, 0.02, 0.24), MAT["corroded_brass"], bevel=0.003)
            torus(f"PC_V3_hanging_key_{idx:02d}_ring", (end[0], end[1], end[2] + 0.07), 0.06, 0.007, MAT["corroded_brass"], rot=(math.radians(90), 0, 0))

    # Large dragged hand bell in the left hand, matching the concept sheet.
    end = add_chain("PC_V3_left_hand_drag_chain", (-0.72, -0.54, 1.72), 9, dz=0.13, swing=0.8, scale=1.1)
    add_bell("PC_V3_large_dragging_hand_bell", (end[0] - 0.08, end[1], end[2] - 0.12), 1.75)

    # Sagging rope curtains under the shrine.
    for i, x in enumerate([-0.82, -0.58, -0.36, -0.12, 0.12, 0.36, 0.58, 0.82]):
        cyl(f"PC_V3_rope_curtain_{i:02d}", (x, -0.69, 2.02 - random.uniform(0, 0.18)), 0.012, random.uniform(0.6, 1.15), MAT["rope"], vertices=8, rot=(0, 0, random.uniform(-0.2, 0.2)))


def add_sound_relics() -> None:
    random.seed(21)
    positions = [
        (-0.70, -0.61, 3.20), (-0.38, -0.62, 3.36), (0.42, -0.62, 3.25), (0.73, -0.61, 3.05),
        (-0.82, -0.62, 2.72), (0.82, -0.62, 2.68), (-0.46, -0.63, 2.46), (0.50, -0.63, 2.48),
    ]
    for i, pos in enumerate(positions):
        w = random.uniform(0.22, 0.34)
        h = random.uniform(0.15, 0.27)
        box(f"PC_V3_old_radio_body_{i:02d}", pos, (w, 0.075, h), MAT["radio"], rot=(0, 0, math.radians(random.uniform(-3, 3))), bevel=0.012)
        cyl(f"PC_V3_radio_speaker_{i:02d}", (pos[0] - w * 0.22, pos[1] - 0.045, pos[2]), min(w, h) * 0.18, 0.018, MAT["rusted_iron"], vertices=20, rot=(math.radians(90), 0, 0))
        cyl(f"PC_V3_radio_dial_{i:02d}", (pos[0] + w * 0.25, pos[1] - 0.047, pos[2] + h * 0.18), min(w, h) * 0.10, 0.018, MAT["corroded_brass"], vertices=18, rot=(math.radians(90), 0, 0))

    for i, pos in enumerate([(-0.18, -0.64, 3.08), (0.17, -0.64, 2.84), (0.02, 0.47, 3.22)]):
        cyl(f"PC_V3_clock_face_{i}", pos, 0.14, 0.035, MAT["paper"], vertices=32, rot=(math.radians(90), 0, 0))
        torus(f"PC_V3_clock_rim_{i}", pos, 0.14, 0.01, MAT["corroded_brass"], rot=(math.radians(90), 0, 0))
        box(f"PC_V3_clock_hand_long_{i}", (pos[0], pos[1] - 0.025, pos[2] + 0.025), (0.012, 0.012, 0.11), MAT["rusted_iron"], rot=(0, 0, math.radians(22 + i * 31)), bevel=0.002)
        box(f"PC_V3_clock_hand_short_{i}", (pos[0] + 0.015, pos[1] - 0.025, pos[2]), (0.012, 0.012, 0.075), MAT["rusted_iron"], rot=(0, 0, math.radians(-48 + i * 17)), bevel=0.002)

    for i, pos in enumerate([(-0.64, 0.48, 2.82), (-0.24, 0.49, 2.55), (0.34, 0.49, 2.74), (0.68, 0.48, 3.02)]):
        box(f"PC_V3_photo_frame_{i}", pos, (0.25, 0.035, 0.32), MAT["weathered_wood"], bevel=0.008)
        box(f"PC_V3_photo_paper_{i}", (pos[0], pos[1] - 0.022, pos[2]), (0.19, 0.012, 0.25), MAT["paper"], bevel=0.003)
        box(f"PC_V3_photo_dark_face_{i}", (pos[0], pos[1] - 0.03, pos[2] + 0.03), (0.07, 0.01, 0.09), MAT["void"], bevel=0.002)


def add_candle_clusters() -> None:
    random.seed(4)
    base_positions = [(-0.72, -0.73, 2.08), (-0.42, -0.74, 2.18), (0.42, -0.74, 2.14), (0.73, -0.73, 2.06), (0.0, -0.75, 3.24)]
    idx = 0
    for base in base_positions:
        for _ in range(3):
            x = base[0] + random.uniform(-0.07, 0.07)
            y = base[1] + random.uniform(-0.015, 0.015)
            z = base[2] + random.uniform(-0.025, 0.055)
            height = random.uniform(0.13, 0.28)
            cyl(f"PC_V3_candle_wax_{idx:02d}", (x, y, z + height * 0.5), 0.026, height, MAT["wax"], vertices=14, bevel=0.003)
            sphere(f"PC_V3_candle_flame_{idx:02d}", (x, y - 0.006, z + height + 0.045), 0.035, MAT["flame"], scale=(0.72, 0.72, 1.55))
            idx += 1


def add_body_overlays() -> None:
    # Wet wraps and torn cloth strips to make the humanoid read less like simple geometry.
    # Long bent arms make the model read as a carrier under a shrine instead of only a shrine prop.
    arm_specs = [
        ("left", -0.66, -1.02, -18, 12),
        ("right", 0.66, -1.02, 18, -12),
    ]
    for side, x, y, upper_rot, fore_rot in arm_specs:
        sign = -1 if side == "left" else 1
        box(f"PC_V3_{side}_wrapped_upper_arm", (x, y, 1.96), (0.16, 0.12, 0.62), MAT["wet_wrap"], rot=(0, 0, math.radians(upper_rot)), bevel=0.025)
        box(f"PC_V3_{side}_wrapped_forearm", (x + sign * 0.08, y - 0.02, 1.52), (0.15, 0.12, 0.58), MAT["wet_wrap"], rot=(0, 0, math.radians(fore_rot)), bevel=0.025)
        ellipsoid(f"PC_V3_{side}_dark_elbow_joint", (x + sign * 0.02, y - 0.01, 1.72), 0.105, MAT["soaked_cloth"], (0.9, 0.72, 0.8))
        ellipsoid(f"PC_V3_{side}_long_wet_hand", (x + sign * 0.14, y - 0.035, 1.20), 0.11, MAT["wet_wrap"], (0.82, 0.52, 1.28))
        for finger in range(4):
            box(
                f"PC_V3_{side}_thin_finger_{finger}",
                (x + sign * (0.10 + finger * 0.025), y - 0.07, 1.04 - finger * 0.012),
                (0.025, 0.025, 0.18),
                MAT["wet_wrap"],
                rot=(0, 0, math.radians(sign * (4 + finger * 3))),
                bevel=0.004,
            )
        for band, z in enumerate([1.42, 1.58, 1.88, 2.04]):
            box(
                f"PC_V3_{side}_arm_ragged_wrap_band_{band}",
                (x + sign * random.uniform(-0.02, 0.08), y - 0.065, z),
                (0.23, 0.035, 0.035),
                MAT["soaked_cloth"],
                rot=(0, 0, math.radians(sign * random.uniform(10, 24))),
                bevel=0.003,
            )

    for i, z in enumerate([0.72, 0.88, 1.04, 1.20]):
        box(f"PC_V3_left_leg_wet_wrap_extra_{i}", (-0.24, -0.16, z), (0.28, 0.055, 0.045), MAT["wet_wrap"], rot=(0, 0, math.radians(12 + i * 9)), bevel=0.006)
        box(f"PC_V3_right_leg_wet_wrap_extra_{i}", (0.24, -0.16, z), (0.28, 0.055, 0.045), MAT["wet_wrap"], rot=(0, 0, math.radians(-12 - i * 9)), bevel=0.006)

    for i, x in enumerate([-0.30, -0.20, -0.11, 0.0, 0.12, 0.22, 0.31]):
        box(f"PC_V3_face_torn_hanging_cloth_{i}", (x, -1.06, 1.84 - i * 0.03), (0.052, 0.032, random.uniform(0.66, 1.08)), MAT["soaked_cloth"], rot=(0, 0, math.radians(random.uniform(-6, 6))), bevel=0.004)

    for i, x in enumerate([-0.9, -0.74, 0.74, 0.9]):
        box(f"PC_V3_side_torn_shroud_{i}", (x, -0.48, 2.28), (0.06, 0.035, random.uniform(0.75, 1.2)), MAT["soaked_cloth"], rot=(0, 0, math.radians(random.uniform(-8, 8))), bevel=0.004)


def add_grotesque_back_shape() -> None:
    random.seed(88)
    # Rear side reads in the end-goal as a filthy shrine with sagging fabric, dark holes, and dragged relics.
    box("PC_V3_BACK_rotten_black_rear_cavity", (0, 0.67, 2.92), (1.48, 0.08, 1.32), MAT["void"], bevel=0.018)
    box("PC_V3_BACK_asymmetric_collapsed_left_eave", (-0.82, 0.70, 3.74), (0.48, 0.11, 0.12), MAT["dead_wood"], rot=(0, 0, math.radians(-12)), bevel=0.012)
    box("PC_V3_BACK_asymmetric_broken_right_eave", (0.88, 0.72, 3.58), (0.42, 0.11, 0.12), MAT["dead_wood"], rot=(0, 0, math.radians(18)), bevel=0.012)

    for i, x in enumerate([-0.82, -0.58, -0.34, -0.10, 0.16, 0.42, 0.70]):
        height = random.uniform(1.05, 1.72)
        z = 2.74 + random.uniform(-0.08, 0.12)
        box(
            f"PC_V3_BACK_sagging_rotten_plank_{i:02d}",
            (x, 0.76, z),
            (random.uniform(0.11, 0.18), 0.075, height),
            MAT["weathered_wood"] if i % 2 else MAT["wood_edge"],
            rot=(0, 0, math.radians(random.uniform(-7, 7))),
            bevel=0.01,
        )

    for i, x in enumerate([-0.66, -0.43, -0.20, 0.05, 0.28, 0.52]):
        box(
            f"PC_V3_BACK_pale_exposed_rotten_rib_{i:02d}",
            (x, 0.915, 2.86 + random.uniform(-0.22, 0.26)),
            (0.34, 0.028, 0.045),
            MAT["pale_splinter"],
            rot=(0, 0, math.radians(random.uniform(-30, 30))),
            bevel=0.004,
        )

    for i, x in enumerate([-0.62, -0.38, -0.16, 0.10, 0.32, 0.56, 0.78]):
        strip_height = random.uniform(0.68, 1.36)
        box(
            f"PC_V3_BACK_wet_hanging_shroud_{i:02d}",
            (x, 0.83, 2.00 - random.uniform(0, 0.12)),
            (random.uniform(0.055, 0.09), 0.04, strip_height),
            MAT["soaked_cloth"],
            rot=(0, 0, math.radians(random.uniform(-8, 8))),
            bevel=0.004,
        )
    for i, x in enumerate([-0.46, -0.18, 0.18, 0.46]):
        ellipsoid(
            f"PC_V3_BACK_tar_sagging_pouch_{i:02d}",
            (x, 0.90, 2.22 + random.uniform(-0.15, 0.1)),
            0.18,
            MAT["soaked_cloth"],
            (0.74, 0.26, random.uniform(1.12, 1.55)),
        )

    for i, (x, z, radius) in enumerate([(-0.48, 3.14, 0.18), (0.06, 3.32, 0.23), (0.54, 2.92, 0.16)]):
        ellipsoid(f"PC_V3_BACK_dark_rotten_hole_{i}", (x, 0.875, z), radius, MAT["void"], (1.0, 0.16, 1.25))
        torus(f"PC_V3_BACK_corroded_hole_rim_{i}", (x, 0.858, z), radius * 1.05, 0.012, MAT["rusted_iron"], rot=(math.radians(90), 0, 0))

    for i, x in enumerate([-0.95, -0.74, -0.51, -0.27, 0.0, 0.28, 0.52, 0.78, 0.98]):
        end = add_chain(f"PC_V3_BACK_sickly_chain_curtain_{i:02d}", (x, 0.88, random.uniform(3.36, 3.78)), random.randint(5, 10), dz=0.12, swing=random.random() * 3.0, scale=random.uniform(0.72, 1.0))
        if i % 2 == 0:
            add_bell(f"PC_V3_BACK_dead_small_bell_{i:02d}", (end[0], end[1], end[2] - 0.08), random.uniform(0.48, 0.82))

    for i in range(26):
        x = random.uniform(-0.92, 0.92)
        z = random.uniform(2.20, 3.82)
        box(
            f"PC_V3_BACK_jagged_rot_splinter_{i:02d}",
            (x, 0.92, z),
            (random.uniform(0.12, 0.34), 0.025, random.uniform(0.018, 0.04)),
            MAT["wood_edge"] if i % 3 else MAT["rusted_iron"],
            rot=(0, 0, math.radians(random.uniform(-48, 48))),
            bevel=0.002,
        )

    # Bulging, uneven wet masses on the side silhouette so the rear does not read as a clean box.
    for i, x in enumerate([-1.08, 1.08, -1.02, 1.02]):
        ellipsoid(
            f"PC_V3_BACK_side_sagging_disgust_mass_{i}",
            (x, 0.42 + random.uniform(-0.05, 0.08), 2.34 + random.uniform(-0.18, 0.25)),
            0.22,
            MAT["soaked_cloth"],
            (0.7, 0.42, 1.25),
        )


def add_corrosion_and_splinters() -> None:
    random.seed(52)
    for i in range(40):
        x = random.uniform(-0.95, 0.95)
        z = random.uniform(2.25, 3.62)
        y = random.choice([-0.705, 0.505])
        mat = MAT["wood_edge"] if i % 3 else MAT["rusted_iron"]
        box(
            f"PC_V3_surface_scratch_splinter_{i:02d}",
            (x, y, z),
            (random.uniform(0.08, 0.22), 0.012, random.uniform(0.012, 0.026)),
            mat,
            rot=(0, 0, math.radians(random.uniform(-32, 32))),
            bevel=0.002,
        )


def add_end_goal_surface_detail() -> None:
    random.seed(144)
    # High-level read from Penance_End_Goal.png: filthy vertical shrine, ritual clutter, black wet void, and rotten back.
    for i in range(34):
        x = random.uniform(-0.86, 0.86)
        z = random.uniform(2.25, 3.55)
        h = random.uniform(0.14, 0.54)
        box(
            f"PC_EndGoal_front_tar_rain_stain_{i:02d}",
            (x, -0.642, z - h * 0.36),
            (random.uniform(0.012, 0.028), 0.012, h),
            MAT["soaked_cloth"],
            rot=(0, 0, math.radians(random.uniform(-2, 2))),
            bevel=0.001,
        )

    for i in range(22):
        x = random.uniform(-0.86, 0.86)
        z = random.uniform(2.15, 3.66)
        box(
            f"PC_EndGoal_front_pale_splinter_gash_{i:02d}",
            (x, -0.665, z),
            (random.uniform(0.11, 0.30), 0.014, random.uniform(0.018, 0.045)),
            MAT["pale_splinter"] if i % 2 else MAT["wood_edge"],
            rot=(0, 0, math.radians(random.uniform(-38, 38))),
            bevel=0.002,
        )

    # Small relics around the shrine face, arranged less evenly than the base prop grid.
    relic_positions = [
        (-0.72, 3.34), (-0.55, 3.02), (-0.38, 3.48), (-0.22, 2.68),
        (0.22, 3.50), (0.42, 2.72), (0.62, 3.18), (0.78, 2.88),
    ]
    for i, (x, z) in enumerate(relic_positions):
        if i % 3 == 0:
            cyl(f"PC_EndGoal_extra_clock_face_{i}", (x, -0.692, z), 0.09, 0.018, MAT["paper"], vertices=28, rot=(math.radians(90), 0, 0))
            torus(f"PC_EndGoal_extra_clock_rim_{i}", (x, -0.707, z), 0.09, 0.008, MAT["corroded_brass"], rot=(math.radians(90), 0, 0))
        elif i % 3 == 1:
            box(f"PC_EndGoal_extra_photo_frame_{i}", (x, -0.692, z), (0.16, 0.024, 0.22), MAT["dead_wood"], rot=(0, 0, math.radians(random.uniform(-6, 6))), bevel=0.004)
            box(f"PC_EndGoal_extra_photo_paper_{i}", (x, -0.711, z), (0.115, 0.01, 0.16), MAT["paper"], bevel=0.002)
            oval_disc(f"PC_EndGoal_extra_photo_face_void_{i}", (x, -0.72, z + 0.012), (0.034, 0.006, 0.048), MAT["void"])
        else:
            box(f"PC_EndGoal_extra_radio_block_{i}", (x, -0.692, z), (0.20, 0.035, 0.14), MAT["radio"], rot=(0, 0, math.radians(random.uniform(-5, 5))), bevel=0.006)
            cyl(f"PC_EndGoal_extra_radio_speaker_{i}", (x - 0.045, -0.718, z), 0.032, 0.012, MAT["rusted_iron"], vertices=18, rot=(math.radians(90), 0, 0))

    # The target head has a tiny pendant/relic in the black mask void.
    add_chain("PC_EndGoal_void_pendant_chain", (0, -1.56, 3.25), 4, dz=0.07, swing=0.3, scale=0.5)
    sphere("PC_EndGoal_void_small_hanging_relic", (0, -1.565, 2.92), 0.045, MAT["corroded_brass"], scale=(0.75, 0.75, 1.35))
    cyl("PC_EndGoal_void_relic_pin", (0, -1.59, 2.83), 0.018, 0.13, MAT["rusted_iron"], vertices=10, bevel=0.002)

    # Rewrap the visible door-mask so it reads like bound, rotten wood instead of a plain board.
    for i, z in enumerate([1.62, 1.84, 2.06, 2.30]):
        box(
            f"PC_EndGoal_mask_dirty_horizontal_binding_{i}",
            (0, -1.66, z),
            (0.42, 0.028, 0.034),
            MAT["rusted_iron"] if i % 2 else MAT["rope"],
            rot=(0, 0, math.radians(random.uniform(-4, 4))),
            bevel=0.002,
        )
    for i, x in enumerate([-0.18, -0.08, 0.04, 0.16]):
        box(
            f"PC_EndGoal_mask_long_black_runoff_{i}",
            (x, -1.675, 2.03),
            (0.022, 0.012, random.uniform(0.78, 1.28)),
            MAT["soaked_cloth"],
            rot=(0, 0, math.radians(random.uniform(-2, 2))),
            bevel=0.001,
        )


def add_guides_and_lighting() -> None:
    bpy.ops.object.light_add(type="AREA", location=(0, -4.0, 5.2))
    key = bpy.context.object
    key.name = "PC_V3_reference_key_light"
    key.data.energy = 760
    key.data.size = 5.0

    bpy.ops.object.light_add(type="POINT", location=(0.0, -0.92, 2.32))
    candle = bpy.context.object
    candle.name = "PC_V3_candle_cluster_preview_light"
    candle.data.energy = 95
    candle.data.color = (1.0, 0.43, 0.14)

    bpy.ops.object.camera_add(location=(3.1, -6.2, 2.65), rotation=(math.radians(68), 0, math.radians(27)))
    bpy.context.scene.camera = bpy.context.object


def set_origin_and_units() -> None:
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        return
    corners = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    min_z = min(c.z for c in corners)
    center_x = (min(c.x for c in corners) + max(c.x for c in corners)) * 0.5
    center_y = (min(c.y for c in corners) + max(c.y for c in corners)) * 0.5
    for obj in bpy.context.scene.objects:
        obj.location.x -= center_x
        obj.location.y -= center_y
        obj.location.z -= min_z


def export_outputs() -> None:
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
    random.seed(1337)
    print("Penance Carrier end-goal v3 pass starting...", flush=True)
    clear_scene()
    create_materials()
    import_blockout()
    add_roof_shrine()
    add_face_mask()
    add_body_overlays()
    add_grotesque_back_shape()
    add_hanging_relics()
    add_sound_relics()
    add_candle_clusters()
    add_corrosion_and_splinters()
    add_end_goal_surface_detail()
    add_guides_and_lighting()
    set_origin_and_units()
    export_outputs()
    print("Saved blend:", OUTPUT_BLEND, flush=True)
    print("Exported GLB:", OUTPUT_GLB, flush=True)


if __name__ == "__main__":
    main()
