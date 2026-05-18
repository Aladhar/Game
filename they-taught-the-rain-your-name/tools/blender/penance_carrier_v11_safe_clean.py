"""
Penance Carrier V11 safe sculpt-prep pass.

This pass branches from the safer V8 balanced pass and adds:
- cleaner export/shading hygiene
- weighted normals and controlled triangulation
- procedural sculpt-prep surface variation for cloth, wood, metal, and wax
- restrained nested surface detail without changing the safe V8 silhouette

This is not a finished hand sculpt. It creates a safer high-detail/procedural
source direction that can later be baked down to LOD meshes.

It keeps:
- darker wet mood materials
- clearer hooded void and vertical door-mask head
- stronger wrapped human body read
- less toy-like shrine surface
- wrapped human anatomy detail
- dense shrine kitbash proxies
- chain/bell/rope curtains
- rotten back mass and sagging shrouds

It uses:
- End_Goal multi-sheet, region-organized reference crops
- penance_carrier_blockout_v1.glb as the only imported base model

Outputs:
  assets/models/enemies/penance_carrier/blender_work/penance_carrier_end_goal_v11_safe_sculpt_prep.blend
  assets/models/enemies/penance_carrier/penance_carrier_end_goal_v11_safe_sculpt_prep.glb
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
REF_ROOT = ASSET_ROOT / "reference_crops/end_goal_multi_region"
INPUT_GLB = ASSET_ROOT / "penance_carrier_blockout_v1.glb"
WORK_DIR = ASSET_ROOT / "blender_work"
OUTPUT_BLEND = WORK_DIR / "penance_carrier_end_goal_v22_multi_region_shape_correction.blend"
OUTPUT_GLB = ASSET_ROOT / "penance_carrier_end_goal_v22_multi_region_shape_correction.glb"

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
    MAT["wrap_highlight"] = make_mat("PC_V11_damp_dirty_wrap_highlights", (0.090, 0.085, 0.076, 1), 0.96)
    MAT["wood"] = make_mat("PC_V8_rotten_dark_weathered_wood", (0.092, 0.067, 0.045, 1), 0.95)
    MAT["raw_wood"] = make_mat("PC_V11_old_dirty_door_wood_muted", (0.190, 0.158, 0.112, 1), 0.94)
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


def ellipsoid(
    name: str,
    loc: tuple[float, float, float],
    radius: float,
    mat: bpy.types.Material,
    scale=(1, 1, 1),
    rot=(0, 0, 0),
    collection="PC_V11_organic_rebuild",
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=radius, location=loc, rotation=rot)
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


def ragged_panel(
    name: str,
    y: float,
    z_min: float,
    z_max: float,
    width_bottom: float,
    width_top: float,
    mat: bpy.types.Material,
    x_center: float = 0.0,
    cols: int = 7,
    rows: int = 18,
    collection: str = "PC_V11_ragged_sculpt_panels",
) -> bpy.types.Object:
    verts: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int, int]] = []
    phase = random.uniform(0, math.tau)
    for r in range(rows + 1):
        t = r / rows
        z = z_min + (z_max - z_min) * t
        width = width_bottom + (width_top - width_bottom) * t
        edge_jitter = 0.018 * math.sin(t * math.tau * 2.3 + phase)
        for c in range(cols + 1):
            u = c / cols
            edge_bias = abs(u - 0.5) * 2
            x = x_center + (u - 0.5) * (width + edge_jitter * edge_bias)
            x += math.sin(t * 7.0 + c * 1.7 + phase) * 0.012
            yy = y + math.sin(t * 9.0 + c * 0.8 + phase) * 0.010
            if r == 0 and c in [1, 3, 6]:
                z -= random.uniform(0.04, 0.16)
            verts.append((x, yy, z))
    for r in range(rows):
        for c in range(cols):
            a = r * (cols + 1) + c
            faces.append((a, a + 1, a + cols + 2, a + cols + 1))

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    assign(obj, mat)
    shade(obj)
    solid = obj.modifiers.new("PC_V11_panel_thickness", "SOLIDIFY")
    solid.thickness = 0.018
    tex = bpy.data.textures.new(f"{name}_controlled_warp_noise", type="CLOUDS")
    tex.noise_scale = 0.42
    tex.noise_depth = 4
    disp = obj.modifiers.new("PC_V11_controlled_panel_warp", "DISPLACE")
    disp.strength = 0.012
    disp.texture = tex
    return move_to(obj, collection)


def wrapped_limb_mesh(
    name: str,
    loc: tuple[float, float, float],
    height: float,
    radius_x: float,
    radius_y: float,
    mat: bpy.types.Material,
    rot=(0, 0, 0),
    rings: int = 18,
    sides: int = 12,
    collection: str = "PC_V11_clay_sculpt_upgrade",
) -> bpy.types.Object:
    verts: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int, int]] = []
    phase = random.uniform(0, math.tau)
    for r in range(rings + 1):
        t = r / rings
        z = (t - 0.5) * height
        taper = 0.72 + 0.24 * math.sin(t * math.pi)
        sag = 1.0 + 0.12 * math.sin(t * math.tau * 1.4 + phase)
        crease = 1.0 - 0.10 * max(0.0, math.sin(t * math.tau * 5.0 + phase))
        cx = math.sin(t * math.tau * 1.7 + phase) * radius_x * 0.12
        cy = math.cos(t * math.tau * 1.2 + phase) * radius_y * 0.10
        for s in range(sides):
            a = s / sides * math.tau
            rib = 1.0 + 0.08 * math.sin(s * 2.0 + r * 0.75 + phase)
            x = cx + math.cos(a) * radius_x * taper * sag * rib
            y = cy + math.sin(a) * radius_y * taper * crease * rib
            verts.append((x, y, z))
    for r in range(rings):
        for s in range(sides):
            a = r * sides + s
            faces.append((a, r * sides + (s + 1) % sides, (r + 1) * sides + (s + 1) % sides, (r + 1) * sides + s))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = loc
    obj.rotation_euler = rot
    bpy.context.scene.collection.objects.link(obj)
    assign(obj, mat)
    shade(obj)
    tex = bpy.data.textures.new(f"{name}_lumpy_clay_noise", type="VORONOI")
    tex.noise_scale = 0.58
    tex.intensity = 0.22
    disp = obj.modifiers.new("PC_V11_lumpy_sculpt_displace", "DISPLACE")
    disp.strength = 0.010
    disp.texture = tex
    return move_to(obj, collection)


def chipped_board_mesh(
    name: str,
    loc: tuple[float, float, float],
    height: float,
    width: float,
    mat: bpy.types.Material,
    rot=(0, 0, 0),
    rows: int = 14,
    collection: str = "PC_V11_clay_sculpt_upgrade",
) -> bpy.types.Object:
    verts: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int, int]] = []
    phase = random.uniform(0, math.tau)
    for r in range(rows + 1):
        t = r / rows
        z = (t - 0.5) * height
        left_chip = math.sin(t * 11.0 + phase) * 0.018 - random.uniform(0, 0.010)
        right_chip = math.cos(t * 9.0 + phase) * 0.018 + random.uniform(0, 0.010)
        if r in [0, rows]:
            left_chip -= random.uniform(0.00, 0.04)
            right_chip += random.uniform(0.00, 0.04)
        verts.extend([
            (-width * 0.5 + left_chip, -0.010, z),
            (width * 0.5 + right_chip, -0.010, z),
            (width * 0.5 + right_chip * 0.6, 0.010, z),
            (-width * 0.5 + left_chip * 0.6, 0.010, z),
        ])
    for r in range(rows):
        a = r * 4
        b = (r + 1) * 4
        faces.extend([(a, b, b + 1, a + 1), (a + 1, b + 1, b + 2, a + 2), (a + 2, b + 2, b + 3, a + 3), (a + 3, b + 3, b, a)])
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = loc
    obj.rotation_euler = rot
    bpy.context.scene.collection.objects.link(obj)
    assign(obj, mat)
    shade(obj, 0.002)
    return move_to(obj, collection)


def sculpted_bell(
    name: str,
    loc: tuple[float, float, float],
    scale: float,
    collection: str = "PC_V11_clay_sculpt_upgrade",
) -> None:
    verts: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int, int]] = []
    rings = 8
    sides = 24
    phase = random.uniform(0, math.tau)
    for r in range(rings + 1):
        t = r / rings
        z = (0.5 - t) * 0.28 * scale
        base_radius = (0.040 + 0.095 * (t ** 1.55)) * scale
        if r == rings:
            base_radius *= 1.18
        for s in range(sides):
            a = s / sides * math.tau
            dent = 1.0 + 0.045 * math.sin(s * 3.0 + r * 0.9 + phase)
            verts.append((math.cos(a) * base_radius * dent, math.sin(a) * base_radius * dent, z))
    for r in range(rings):
        for s in range(sides):
            a = r * sides + s
            faces.append((a, r * sides + (s + 1) % sides, (r + 1) * sides + (s + 1) % sides, (r + 1) * sides + s))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(f"{name}_flared_dented_shell", mesh)
    obj.location = loc
    bpy.context.scene.collection.objects.link(obj)
    assign(obj, MAT["brass"])
    shade(obj)
    move_to(obj, collection)
    torus(f"{name}_uneven_lip", (loc[0], loc[1], loc[2] - 0.14 * scale), 0.112 * scale, 0.010 * scale, MAT["brass"], collection=collection)
    sphere(f"{name}_heavy_clapper", (loc[0], loc[1], loc[2] - 0.20 * scale), 0.030 * scale, MAT["metal"], collection=collection)


def sculpted_chain_link(
    name: str,
    loc: tuple[float, float, float],
    sx: float,
    sz: float,
    mat: bpy.types.Material,
    rot=(0, 0, 0),
    sides: int = 18,
    collection: str = "PC_V11_6_authored_clay_sculpt",
) -> bpy.types.Object:
    verts: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int, int]] = []
    tube = 0.007
    phase = random.uniform(0, math.tau)
    for i in range(sides):
        a = i / sides * math.tau
        oval_x = math.cos(a) * sx * (1.0 + 0.10 * math.sin(a * 3.0 + phase))
        oval_z = math.sin(a) * sz * (1.0 + 0.08 * math.cos(a * 2.0 + phase))
        pinch = 1.0 - 0.20 * max(0.0, math.sin(a * 2.0 + phase))
        for j in range(6):
            b = j / 6 * math.tau
            verts.append((oval_x + math.cos(b) * tube * pinch, math.sin(b) * tube * 0.72, oval_z + math.sin(b) * tube))
    for i in range(sides):
        ni = (i + 1) % sides
        for j in range(6):
            nj = (j + 1) % 6
            faces.append((i * 6 + j, ni * 6 + j, ni * 6 + nj, i * 6 + nj))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = loc
    obj.rotation_euler = rot
    bpy.context.scene.collection.objects.link(obj)
    assign(obj, mat)
    shade(obj)
    return move_to(obj, collection)


def sculpted_finger(
    name: str,
    loc: tuple[float, float, float],
    length: float,
    radius: float,
    mat: bpy.types.Material,
    rot=(0, 0, 0),
    collection: str = "PC_V11_6_authored_clay_sculpt",
) -> bpy.types.Object:
    return wrapped_limb_mesh(
        name,
        loc,
        length,
        radius,
        radius * 0.62,
        mat,
        rot=rot,
        rings=8,
        sides=8,
        collection=collection,
    )


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


def bell_proxy_at_collection(name: str, loc: tuple[float, float, float], scale: float = 1.0, collection: str = "PC_V11_ragged_sculpt_panels") -> None:
    cyl(f"{name}_body", loc, 0.085 * scale, 0.16 * scale, MAT["brass"], vertices=28, collection=collection)
    torus(f"{name}_rim", (loc[0], loc[1], loc[2] - 0.08 * scale), 0.085 * scale, 0.008 * scale, MAT["brass"], collection=collection)
    sphere(f"{name}_clapper", (loc[0], loc[1], loc[2] - 0.13 * scale), 0.025 * scale, MAT["metal"], collection=collection)


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
    # Height is normalized to 4.2m, matching the target's roughly 3.4m carrier
    # plus roof crosses/relics. These planes now use the organized multi-sheet
    # End_Goal crop library instead of the older single reference sheet.
    add_reference_plane(
        "front_ortho_multi_region",
        "orthographic/front/front_orthographic_full_body_x4.png",
        (0, -2.82, 2.1),
        (1.86, 4.2),
        (math.radians(90), 0, 0),
    )
    add_reference_plane(
        "back_ortho_multi_region",
        "orthographic/back/back_orthographic_full_body_x4.png",
        (0, 2.82, 2.1),
        (2.05, 4.2),
        (math.radians(90), 0, math.radians(180)),
    )
    add_reference_plane(
        "left_side_multi_region",
        "orthographic/left_side/left_side_full_body_x4.png",
        (2.35, 0, 2.1),
        (1.70, 4.2),
        (math.radians(90), 0, math.radians(90)),
    )
    add_reference_plane(
        "right_side_multi_region",
        "orthographic/right_side/right_side_full_body_x4.png",
        (-2.35, 0, 2.1),
        (2.06, 4.2),
        (math.radians(90), 0, math.radians(-90)),
    )


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


def add_v11_primary_form_correction() -> None:
    random.seed(2011)

    # Pull the earlier rectangular blockout limbs behind the new organic overlay.
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        lname = obj.name.lower()
        if any(k in lname for k in ["long_upper_arm_wrapped", "long_forearm_wrapped", "wrapped_thigh", "wrapped_shin"]):
            obj.location.y += 0.18
            obj.scale.x *= 0.56
            obj.scale.y *= 0.62
        elif "splayed_bare_foot_block" in lname:
            obj.scale.x *= 0.80
            obj.scale.z *= 0.68

    # Primary form: gravity asymmetry and load tension before any small detail.
    primary_offsets = {
        "PC_V4_hunched_upper_back_mass": ((-0.035, -0.030, -0.035), (1.02, 1.00, 0.96)),
        "PC_V4_left_shoulder_under_mask": ((-0.040, -0.020, -0.070), (1.06, 1.00, 0.92)),
        "PC_V4_right_shoulder_under_mask": ((0.020, -0.015, 0.025), (0.94, 1.00, 1.04)),
        "PC_V6_left_wrapped_thigh": ((-0.035, -0.025, -0.020), (0.92, 1.00, 1.03)),
        "PC_V6_right_wrapped_thigh": ((0.026, -0.005, 0.030), (0.86, 1.00, 0.98)),
        "PC_V6_left_wrapped_shin": ((-0.030, -0.018, -0.030), (0.88, 1.00, 1.02)),
        "PC_V6_right_wrapped_shin": ((0.018, 0.000, 0.018), (0.84, 1.00, 0.98)),
    }
    for name, (offset, scale) in primary_offsets.items():
        obj = bpy.data.objects.get(name)
        if obj:
            obj.location.x += offset[0]
            obj.location.y += offset[1]
            obj.location.z += offset[2]
            obj.scale.x *= scale[0]
            obj.scale.y *= scale[1]
            obj.scale.z *= scale[2]

    # Board warping and non-uniform shrine load: never perfectly centered.
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        name = obj.name
        if "roof_left" in name:
            obj.rotation_euler.z += math.radians(-1.4)
            obj.location.x -= 0.012
            obj.location.z -= 0.012
        elif "roof_right" in name:
            obj.rotation_euler.z += math.radians(0.7)
            obj.location.x += 0.006
            obj.location.z += 0.006
        elif "front_weathered_plank" in name or "rotten_vertical_board" in name:
            obj.rotation_euler.z += math.radians(random.uniform(-2.2, 2.2))
            obj.location.z += random.uniform(-0.035, 0.025)
            obj.scale.x *= random.uniform(0.86, 1.14)
        elif "front_relic" in name or "radio" in name.lower() or "clock" in name.lower():
            obj.rotation_euler.z += math.radians(random.uniform(-2.6, 2.6))
            obj.location.z -= random.uniform(0.000, 0.030)

    # Chain tension points: anchors sag from weight and bells tilt instead of hanging perfectly.
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        lname = obj.name.lower()
        if "chain" in lname and "link" in lname:
            obj.location.x += math.sin(obj.location.z * 3.1) * 0.010
            obj.location.z -= max(0.0, 3.2 - obj.location.z) * 0.004
        elif "bell" in lname:
            obj.rotation_euler.x += math.radians(random.uniform(-5, 5))
            obj.rotation_euler.z += math.radians(random.uniform(-6, 6))
            obj.location.z -= random.uniform(0.004, 0.020)


def add_v11_organic_end_goal_rebuild() -> None:
    random.seed(2211)

    # The target reads as a crushed human under a shrine, not a shrine on sticks.
    # Build uneven shoulder, rib, belly, arm, and leg masses over the safe V8 core.
    ellipsoid("PC_V11_crushed_left_shoulder_meat", (-0.42, -1.02, 2.16), 0.24, MAT["cloth"], scale=(1.45, 0.52, 0.82), rot=(0, 0, math.radians(-12)))
    ellipsoid("PC_V11_crushed_right_shoulder_meat", (0.35, -1.02, 2.08), 0.22, MAT["cloth"], scale=(1.15, 0.50, 0.92), rot=(0, 0, math.radians(9)))
    ellipsoid("PC_V11_sunken_chest_under_mask", (-0.03, -1.06, 1.83), 0.30, MAT["cloth"], scale=(0.78, 0.42, 1.22), rot=(0, 0, math.radians(-4)))
    ellipsoid("PC_V11_low_hanging_abdomen_mass", (0.08, -0.96, 1.34), 0.25, MAT["cloth"], scale=(0.86, 0.46, 1.02), rot=(0, 0, math.radians(7)))

    for i, (x, z, sx, sz, rz) in enumerate([
        (-0.19, 2.42, 0.70, 1.20, -10),
        (-0.13, 2.18, 0.56, 1.10, -4),
        (0.10, 2.06, 0.52, 1.02, 6),
        (0.16, 1.78, 0.46, 0.94, 14),
        (-0.04, 1.52, 0.40, 0.82, -7),
    ]):
        ellipsoid(
            f"PC_V11_hanging_mask_cloth_lobe_{i:02d}",
            (x, -1.39, z),
            0.12,
            MAT["cloth"],
            scale=(sx, 0.18, sz),
            rot=(0, 0, math.radians(rz)),
        )

    # Clearer head: a cloth hood rim, an unmistakable black face hole, and nested door boards.
    ellipsoid("PC_V11_head_hood_left_fold", (-0.18, -1.43, 2.85), 0.15, MAT["cloth"], scale=(0.55, 0.20, 1.72), rot=(0, 0, math.radians(-18)))
    ellipsoid("PC_V11_head_hood_right_fold", (0.18, -1.43, 2.82), 0.14, MAT["cloth"], scale=(0.48, 0.20, 1.62), rot=(0, 0, math.radians(14)))
    ellipsoid("PC_V11_head_hood_top_sag", (0.00, -1.44, 3.07), 0.15, MAT["cloth"], scale=(1.45, 0.18, 0.42), rot=(0, 0, math.radians(-3)))
    ellipsoid("PC_V11_face_absolute_black_socket", (0.00, -1.515, 2.82), 0.19, MAT["void"], scale=(0.64, 0.06, 1.42))
    for i, (x, z, h, rz) in enumerate([(-0.11, 2.18, 0.95, -2), (-0.04, 2.05, 1.12, 1), (0.05, 2.00, 1.04, -1), (0.13, 2.12, 0.86, 3)]):
        box(
            f"PC_V11_face_nested_rotten_board_{i:02d}",
            (x, -1.545, z),
            (0.047, 0.020, h),
            MAT["raw_wood"] if i in [0, 2] else MAT["wood"],
            rot=(0, 0, math.radians(rz)),
            collection="PC_V11_organic_rebuild",
        )

    # Limbs: overlapping ellipsoids create lumpy wrapped anatomy before bands and folds.
    for side, sign in [("left", -1), ("right", 1)]:
        arm_x = sign * 0.58
        ellipsoid(f"PC_V11_{side}_upper_arm_organic_sleeve", (arm_x, -1.02, 1.78), 0.17, MAT["cloth"], scale=(0.42, 0.34, 1.92), rot=(0, math.radians(sign * 8), math.radians(sign * -12)))
        ellipsoid(f"PC_V11_{side}_forearm_organic_sleeve", (sign * 0.67, -1.03, 1.28), 0.15, MAT["cloth"], scale=(0.38, 0.32, 1.74), rot=(0, math.radians(sign * -5), math.radians(sign * 7)))
        ellipsoid(f"PC_V11_{side}_wrist_sack", (sign * 0.70, -1.04, 0.94), 0.09, MAT["cloth"], scale=(0.62, 0.36, 0.76), rot=(0, 0, math.radians(sign * 8)))
        for finger in range(5):
            box(
                f"PC_V11_{side}_dirty_long_finger_{finger:02d}",
                (sign * (0.66 + finger * 0.026), -1.075, 0.83 - finger * 0.012),
                (0.020, 0.020, 0.18 + 0.018 * (finger % 2)),
                MAT["cloth"],
                rot=(0, 0, math.radians(sign * (8 + finger * 5))),
                collection="PC_V11_organic_rebuild",
            )

        leg_x = sign * (0.27 if side == "left" else 0.31)
        ellipsoid(
            f"PC_V11_{side}_leg_continuous_under_wrap_mass",
            (leg_x + sign * 0.012, -0.82, 0.72),
            0.15,
            MAT["cloth"],
            scale=(0.46, 0.30, 2.70),
            rot=(0, math.radians(sign * 4), math.radians(sign * -4)),
        )
        for i, z in enumerate([1.02, 0.78, 0.54, 0.32]):
            ellipsoid(
                f"PC_V11_{side}_leg_lumpy_wrapped_volume_{i:02d}",
                (leg_x + sign * random.uniform(-0.018, 0.030), -0.78, z),
                0.13,
                MAT["cloth"],
                scale=(0.38 + random.uniform(-0.04, 0.05), 0.28, 1.30 + random.uniform(-0.10, 0.18)),
                rot=(0, math.radians(sign * random.uniform(-7, 7)), math.radians(sign * random.uniform(-5, 9))),
            )
        ellipsoid(f"PC_V11_{side}_bare_foot_ugly_splayed_mass", (sign * 0.35, -1.00, 0.07), 0.12, MAT["wrap_highlight"], scale=(1.62, 0.62, 0.34), rot=(0, 0, math.radians(sign * -4)))
        for toe in range(5):
            ellipsoid(
                f"PC_V11_{side}_bare_toe_{toe:02d}",
                (sign * (0.24 + toe * 0.055), -1.10, 0.12 + random.uniform(-0.010, 0.010)),
                0.025,
                MAT["cloth"],
                scale=(0.88, 0.62, 0.46),
                rot=(0, 0, math.radians(sign * random.uniform(-8, 8))),
            )

    # Break the shrine into shapes within shapes: overlay uneven boards, holes, and sagging junk.
    for i, x in enumerate([-0.88, -0.74, -0.59, -0.43, -0.27, -0.10, 0.07, 0.24, 0.43, 0.62, 0.81]):
        zc = 3.02 + random.uniform(-0.10, 0.11)
        box(
            f"PC_V11_front_uneven_outer_plank_{i:02d}",
            (x, -1.080 - random.uniform(0, 0.020), zc),
            (random.uniform(0.036, 0.074), 0.030, random.uniform(0.72, 1.30)),
            MAT["raw_wood"] if i in [1, 8] else MAT["wood"],
            rot=(0, 0, math.radians(random.uniform(-6, 6))),
            collection="PC_V11_organic_rebuild",
        )
        if i % 2 == 0:
            box(
                f"PC_V11_front_black_gap_behind_plank_{i:02d}",
                (x + random.uniform(-0.030, 0.030), -1.112, zc + random.uniform(-0.22, 0.22)),
                (random.uniform(0.035, 0.070), 0.010, random.uniform(0.22, 0.46)),
                MAT["void"],
                rot=(0, 0, math.radians(random.uniform(-8, 8))),
                collection="PC_V11_organic_rebuild",
            )

    for i, (x, y, z, sx, rz) in enumerate([
        (-0.76, -0.78, 3.70, 0.44, -19), (-0.46, -0.68, 3.82, 0.35, -12),
        (-0.18, -0.52, 3.92, 0.28, -7), (0.22, -0.60, 3.88, 0.34, 8),
        (0.56, -0.72, 3.76, 0.48, 14), (0.82, -0.83, 3.60, 0.32, 23),
    ]):
        box(
            f"PC_V11_roof_splintered_weighted_board_{i:02d}",
            (x, y, z),
            (sx, 0.035, random.uniform(0.040, 0.070)),
            MAT["raw_wood"] if i % 2 else MAT["wood"],
            rot=(math.radians(random.uniform(-2, 2)), math.radians(random.uniform(-20, 20)), math.radians(rz)),
            collection="PC_V11_organic_rebuild",
        )

    # Back: larger hanging, rotten silhouette with uneven guts/rags so the rear is disgusting, not plain.
    ellipsoid("PC_V11_back_swollen_rotten_under_mass", (-0.05, 1.12, 2.12), 0.42, MAT["cloth"], scale=(1.22, 0.34, 1.44), rot=(0, 0, math.radians(-5)))
    for i, x in enumerate([-0.66, -0.49, -0.33, -0.18, 0.02, 0.20, 0.39, 0.58, 0.76]):
        h = random.uniform(0.72, 1.46)
        box(
            f"PC_V11_back_torn_viscous_hanging_rag_{i:02d}",
            (x, 1.205, 2.25 - h * 0.20 + random.uniform(-0.08, 0.08)),
            (random.uniform(0.045, 0.090), 0.030, h),
            MAT["cloth"] if i % 3 else MAT["void"],
            rot=(0, 0, math.radians(random.uniform(-10, 10))),
            collection="PC_V11_organic_rebuild",
        )
    for i, (x, z, r) in enumerate([(-0.42, 2.92, 0.16), (-0.06, 3.17, 0.19), (0.34, 2.78, 0.15), (0.18, 2.34, 0.13)]):
        ellipsoid(
            f"PC_V11_back_deep_rotted_hole_{i:02d}",
            (x, 1.245, z),
            r,
            MAT["void"],
            scale=(1.25, 0.10, 1.55),
            rot=(0, 0, math.radians(random.uniform(-9, 9))),
        )


def add_v11_surface_sculpt_prep() -> None:
    random.seed(2111)

    # Cloth direction, sag, fold stacking, and compression dents over the safe V8 body.
    for i, (x, z, width, angle) in enumerate([
        (-0.18, 2.26, 0.30, -18), (-0.12, 2.06, 0.34, 14), (0.08, 1.88, 0.32, -12),
        (0.16, 1.68, 0.28, 18), (-0.08, 1.48, 0.26, -16), (0.02, 1.28, 0.24, 10),
    ]):
        box(
            f"PC_V11_chest_stacked_wet_cloth_fold_{i:02d}",
            (x, -1.135, z),
            (width, 0.020, 0.026),
            MAT["wrap_highlight"] if i in [1, 4] else MAT["cloth"],
            rot=(0, 0, math.radians(angle)),
            collection="PC_V11_sculpt_prep_surface",
        )

    for side, sign in [("left", -1), ("right", 1)]:
        for i, z in enumerate([0.42, 0.58, 0.76, 0.94, 1.12]):
            box(
                f"PC_V11_{side}_leg_compression_fold_{i:02d}",
                (sign * (0.30 + random.uniform(-0.018, 0.018)), -0.575, z),
                (0.24, 0.020, 0.022),
                MAT["wrap_highlight"] if i % 2 else MAT["cloth"],
                rot=(0, 0, math.radians(sign * random.uniform(20, 34))),
                collection="PC_V11_sculpt_prep_surface",
            )
        for i, z in enumerate([1.26, 1.44, 1.62, 1.82, 2.02]):
            box(
                f"PC_V11_{side}_arm_sagging_wrap_fold_{i:02d}",
                (sign * (0.64 + random.uniform(-0.026, 0.026)), -0.965, z),
                (0.21, 0.020, 0.022),
                MAT["wrap_highlight"] if i in [1, 3] else MAT["cloth"],
                rot=(0, 0, math.radians(sign * random.uniform(-34, -16))),
                collection="PC_V11_sculpt_prep_surface",
            )

    # Extra asymmetry: small sunken cloth dents and torn darker valleys.
    for i, (x, z, sx, sz) in enumerate([(-0.22, 1.96, 0.055, 0.20), (0.18, 1.72, 0.048, 0.24), (-0.05, 1.18, 0.044, 0.18), (0.24, 0.82, 0.036, 0.16)]):
        sphere(
            f"PC_V11_cloth_compression_dent_shadow_{i:02d}",
            (x, -1.155, z),
            0.060,
            MAT["void"],
            scale=(sx / 0.060, 0.040, sz / 0.060),
            collection="PC_V11_sculpt_prep_surface",
        )

    # Wood grain flow and chipped planks on the shrine and door-mask.
    for i, x in enumerate([-0.78, -0.62, -0.46, -0.30, -0.14, 0.02, 0.18, 0.36, 0.54, 0.72]):
        for j in range(2):
            box(
                f"PC_V11_front_plank_vertical_grain_{i:02d}_{j}",
                (x + random.uniform(-0.018, 0.018), -1.002, 2.58 + j * 0.46 + random.uniform(-0.05, 0.05)),
                (0.012, 0.012, random.uniform(0.25, 0.46)),
                MAT["wood"] if j == 0 else MAT["raw_wood"],
                rot=(0, 0, math.radians(random.uniform(-2, 2))),
                collection="PC_V11_sculpt_prep_surface",
            )

    for i, (x, z) in enumerate([(-0.10, 2.18), (0.06, 1.98), (-0.13, 1.70), (0.12, 1.46)]):
        box(
            f"PC_V11_mask_splinter_crack_{i:02d}",
            (x, -1.492, z),
            (0.018, 0.010, random.uniform(0.30, 0.48)),
            MAT["void"],
            rot=(0, 0, math.radians(random.uniform(-5, 5))),
            collection="PC_V11_sculpt_prep_surface",
        )

    # Hammer dents and corrosion layering on metal/brass relics.
    relic_positions = [(-0.70, 2.78), (-0.42, 2.58), (0.44, 2.62), (0.72, 2.80), (-0.68, 3.26), (0.16, 3.42)]
    for i, (x, z) in enumerate(relic_positions):
        cyl(
            f"PC_V11_relic_hammer_dent_dark_{i:02d}",
            (x + random.uniform(-0.045, 0.045), -0.872, z + random.uniform(-0.040, 0.040)),
            random.uniform(0.016, 0.030),
            0.007,
            MAT["void"],
            vertices=12,
            rot=(math.radians(90), 0, 0),
            collection="PC_V11_sculpt_prep_surface",
        )
        if i % 2 == 0:
            cyl(
                f"PC_V11_relic_corrosion_ring_{i:02d}",
                (x + random.uniform(-0.050, 0.050), -0.878, z + random.uniform(-0.045, 0.045)),
                random.uniform(0.022, 0.038),
                0.006,
                MAT["brass"],
                vertices=14,
                rot=(math.radians(90), 0, 0),
                collection="PC_V11_sculpt_prep_surface",
            )

    # Melt flow on wax: small vertical drips below the candle bodies.
    for i, (x, z) in enumerate([(-0.76, 2.62), (-0.52, 2.76), (0.52, 2.72), (0.76, 2.58), (0.0, 3.24)]):
        for j in range(2):
            cyl(
                f"PC_V11_wax_melt_drip_{i:02d}_{j}",
                (x + random.uniform(-0.018, 0.018), -0.900, z + 0.045 - j * 0.075),
                random.uniform(0.006, 0.010),
                random.uniform(0.10, 0.18),
                MAT["wax"],
                vertices=8,
                collection="PC_V11_sculpt_prep_surface",
            )

    # Fine noisy displacement on curved cloth/metal/wax primitives to create real surface variation.
    for obj in list(bpy.context.scene.objects):
        if obj.type != "MESH" or obj.name.startswith("PC_V4_REF_") or obj.name.startswith("PC_V4_BLOCKOUT_SCALE_"):
            continue
        mat_name = obj.data.materials[0].name.lower() if obj.data.materials else ""
        if any(k in mat_name for k in ["cloth", "wrap"]):
            tex = bpy.data.textures.new(f"{obj.name}_v11_cloth_noise", type="VORONOI")
            tex.noise_scale = 0.72
            tex.intensity = 0.28
            mod = obj.modifiers.new("PC_V11_subtle_cloth_surface_noise", "DISPLACE")
            mod.strength = 0.006
            mod.texture = tex
        elif "wood" in mat_name:
            tex = bpy.data.textures.new(f"{obj.name}_v11_wood_noise", type="WOOD")
            tex.noise_scale = 0.92
            tex.turbulence = 8.0
            mod = obj.modifiers.new("PC_V11_subtle_wood_grain_displace", "DISPLACE")
            mod.strength = 0.0035
            mod.texture = tex
        elif any(k in mat_name for k in ["iron", "brass", "metal"]):
            tex = bpy.data.textures.new(f"{obj.name}_v11_metal_pitting", type="VORONOI")
            tex.noise_scale = 0.36
            mod = obj.modifiers.new("PC_V11_metal_pitting_micro_displace", "DISPLACE")
            mod.strength = 0.0025
            mod.texture = tex


def add_v11_identity_detail_correction() -> None:
    random.seed(2311)

    # A continuous ragged door-mask surface fixes the current "many sticks" read.
    ragged_panel("PC_V11_black_inner_hanging_cloth_behind_mask", -1.535, 0.98, 2.96, 0.44, 0.58, MAT["cloth"], cols=5, rows=18)
    ragged_panel("PC_V11_warped_central_door_mask_panel", -1.575, 0.86, 2.42, 0.27, 0.36, MAT["raw_wood"], cols=6, rows=20)
    ragged_panel("PC_V11_left_torn_front_cloak_sheet", -1.30, 0.76, 2.22, 0.18, 0.30, MAT["cloth"], x_center=-0.28, cols=4, rows=14)
    ragged_panel("PC_V11_right_torn_front_cloak_sheet", -1.29, 0.82, 2.12, 0.15, 0.25, MAT["cloth"], x_center=0.25, cols=4, rows=13)

    for i, (x, z, w, rz) in enumerate([
        (-0.10, 2.34, 0.28, -17), (0.08, 2.08, 0.26, 14), (-0.08, 1.78, 0.25, -12),
        (0.08, 1.50, 0.23, 18), (-0.05, 1.18, 0.20, -8),
    ]):
        box(
            f"PC_V11_mask_cross_tension_lash_{i:02d}",
            (x, -1.610, z),
            (w, 0.014, 0.018),
            MAT["metal"] if i % 2 else MAT["cloth"],
            rot=(0, 0, math.radians(rz)),
            collection="PC_V11_ragged_sculpt_panels",
        )

    ellipsoid(
        "PC_V11_corrected_visible_black_head_void",
        (0.0, -1.635, 2.72),
        0.18,
        MAT["void"],
        scale=(0.58, 0.055, 1.28),
        collection="PC_V11_ragged_sculpt_panels",
    )
    ellipsoid(
        "PC_V11_corrected_wet_hood_brow",
        (-0.02, -1.645, 2.96),
        0.16,
        MAT["cloth"],
        scale=(1.55, 0.13, 0.32),
        rot=(0, 0, math.radians(-2)),
        collection="PC_V11_ragged_sculpt_panels",
    )
    for i, x in enumerate([-0.115, -0.045, 0.030, 0.105]):
        box(
            f"PC_V11_door_panel_vertical_split_{i:02d}",
            (x, -1.625, 1.56 + random.uniform(-0.04, 0.04)),
            (0.014, 0.010, random.uniform(1.02, 1.34)),
            MAT["wood"] if i % 2 else MAT["void"],
            rot=(0, 0, math.radians(random.uniform(-2, 2))),
            collection="PC_V11_ragged_sculpt_panels",
        )
    for i, (x, z, h, rz) in enumerate([(-0.09, 2.16, 0.30, -4), (0.08, 1.88, 0.36, 6), (-0.05, 1.34, 0.28, -8), (0.11, 1.02, 0.22, 5)]):
        box(
            f"PC_V11_door_panel_dark_crack_{i:02d}",
            (x, -1.632, z),
            (0.020, 0.010, h),
            MAT["void"],
            rot=(0, 0, math.radians(rz)),
            collection="PC_V11_ragged_sculpt_panels",
        )

    # Break smooth shoulders, arms, and legs with non-even wrap rhythm.
    wrap_targets = [
        (-0.44, -1.255, 1.53, 0.48, -16), (-0.34, -1.260, 1.67, 0.40, 11),
        (0.37, -1.255, 1.48, 0.44, 15), (0.28, -1.260, 1.66, 0.35, -9),
        (-0.68, -1.090, 1.22, 0.25, 24), (0.67, -1.090, 1.18, 0.23, -22),
        (-0.31, -0.930, 0.78, 0.22, 18), (-0.30, -0.930, 0.50, 0.20, -14),
        (0.33, -0.930, 0.82, 0.22, -17), (0.32, -0.930, 0.50, 0.20, 15),
    ]
    for i, (x, y, z, w, rz) in enumerate(wrap_targets):
        box(
            f"PC_V11_anatomy_breakup_wrap_band_{i:02d}",
            (x, y, z),
            (w, 0.018, 0.024),
            MAT["wrap_highlight"] if i in [1, 6, 8] else MAT["cloth"],
            rot=(0, 0, math.radians(rz)),
            collection="PC_V11_ragged_sculpt_panels",
        )

    # The reference has a strong left-hand bell/chain read. Add it as a silhouette anchor.
    end = chain_links("PC_V11_left_hand_hero_bell_chain", (-0.79, -1.14, 1.10), 9, 0.105, MAT["metal"], 1.10, 1.7)
    bell_proxy_at_collection("PC_V11_left_hand_large_penitence_bell", (end[0] - 0.03, end[1] - 0.02, end[2] - 0.10), 1.35)

    # Side and back rot should hang in sheets, not just rectangles.
    ragged_panel("PC_V11_back_rotten_skin_sheet_left", 1.265, 1.18, 3.00, 0.32, 0.48, MAT["cloth"], x_center=-0.36, cols=5, rows=17)
    ragged_panel("PC_V11_back_rotten_skin_sheet_right", 1.270, 1.05, 2.78, 0.24, 0.40, MAT["cloth"], x_center=0.34, cols=5, rows=15)


def add_v11_5_clay_quality_sculpt_pass() -> None:
    random.seed(2415)

    # Replace the obvious old hero-bell proxy with an authored dented form.
    for obj in list(bpy.context.scene.objects):
        if obj.name.startswith("PC_V11_left_hand_large_penitence_bell"):
            bpy.data.objects.remove(obj, do_unlink=True)
    sculpted_bell("PC_V11_5_left_hand_sculpted_penitence_bell", (-0.82, -1.16, 0.56), 0.78)

    # The current body still has too many smooth ovals. Overlay twisted, lumpy wrapped forms
    # with non-identical cross sections so the clay read carries authored compression.
    wrapped_limb_mesh(
        "PC_V11_5_left_arm_pinched_wrapped_sculpt",
        (-0.62, -1.105, 1.46),
        1.12,
        0.090,
        0.062,
        MAT["cloth"],
        rot=(math.radians(-5), math.radians(-8), math.radians(-11)),
        rings=22,
    )
    wrapped_limb_mesh(
        "PC_V11_5_right_arm_pinched_wrapped_sculpt",
        (0.62, -1.105, 1.42),
        1.02,
        0.082,
        0.056,
        MAT["cloth"],
        rot=(math.radians(3), math.radians(7), math.radians(9)),
        rings=20,
    )
    wrapped_limb_mesh(
        "PC_V11_5_left_leg_compressed_wrapped_sculpt",
        (-0.31, -0.96, 0.62),
        1.34,
        0.078,
        0.054,
        MAT["cloth"],
        rot=(math.radians(1), math.radians(-4), math.radians(-2)),
        rings=24,
    )
    wrapped_limb_mesh(
        "PC_V11_5_right_leg_compressed_wrapped_sculpt",
        (0.32, -0.96, 0.58),
        1.22,
        0.073,
        0.052,
        MAT["cloth"],
        rot=(math.radians(-1), math.radians(5), math.radians(3)),
        rings=22,
    )
    wrapped_limb_mesh(
        "PC_V11_5_twisted_hanging_torso_cloth_core",
        (-0.02, -1.22, 1.58),
        1.70,
        0.135,
        0.060,
        MAT["cloth"],
        rot=(math.radians(2), math.radians(-3), math.radians(2)),
        rings=26,
        sides=14,
    )

    # Fold hierarchy: long gravity folds first, then uneven compression bands.
    for i, (x, z0, h, rz, depth) in enumerate([
        (-0.16, 1.34, 0.74, -5, 0.024),
        (-0.05, 1.18, 0.92, 2, 0.018),
        (0.10, 1.22, 0.78, 7, 0.022),
        (0.21, 1.12, 0.58, 12, 0.016),
        (-0.29, 1.08, 0.50, -13, 0.014),
    ]):
        chipped_board_mesh(
            f"PC_V11_5_long_cloth_valley_fold_{i:02d}",
            (x, -1.355 - depth, z0 + h * 0.5),
            h,
            random.uniform(0.016, 0.030),
            MAT["cloth"] if i != 1 else MAT["wrap_highlight"],
            rot=(0, 0, math.radians(rz)),
            rows=12,
        )
    for i, (x, y, z, w, rz) in enumerate([
        (-0.37, -1.195, 1.78, 0.36, -18),
        (-0.29, -1.205, 1.55, 0.32, 12),
        (0.35, -1.190, 1.68, 0.34, 16),
        (0.24, -1.205, 1.45, 0.28, -11),
        (-0.29, -1.035, 0.88, 0.26, 20),
        (-0.32, -1.025, 0.59, 0.22, -17),
        (0.33, -1.030, 0.82, 0.25, -20),
        (0.31, -1.025, 0.52, 0.21, 14),
    ]):
        box(
            f"PC_V11_5_nonuniform_compression_wrap_{i:02d}",
            (x, y, z),
            (w, 0.017, random.uniform(0.018, 0.032)),
            MAT["wrap_highlight"] if i in [1, 5] else MAT["cloth"],
            rot=(0, 0, math.radians(rz)),
            collection="PC_V11_clay_sculpt_upgrade",
        )

    # Front shrine planks: authored bowing/chipping overlays, not perfectly straight rods.
    for i, (x, z, h, w, rz) in enumerate([
        (-0.82, 3.02, 1.22, 0.058, -5),
        (-0.63, 3.12, 1.42, 0.044, 3),
        (-0.45, 2.88, 1.04, 0.052, -8),
        (-0.23, 3.20, 1.30, 0.040, 5),
        (0.02, 3.03, 1.18, 0.048, -2),
        (0.28, 3.16, 1.36, 0.054, 7),
        (0.52, 2.96, 1.10, 0.046, -4),
        (0.78, 3.08, 1.28, 0.060, 6),
    ]):
        chipped_board_mesh(
            f"PC_V11_5_authored_front_chipped_plank_{i:02d}",
            (x, -1.145 - random.uniform(0, 0.018), z),
            h,
            w,
            MAT["wood"] if i not in [1, 6] else MAT["raw_wood"],
            rot=(0, 0, math.radians(rz + random.uniform(-1.5, 1.5))),
            rows=16,
        )
        if i in [0, 3, 7]:
            box(
                f"PC_V11_5_deep_corner_crush_shadow_{i:02d}",
                (x + random.uniform(-0.025, 0.025), -1.168, z + random.uniform(-0.28, 0.32)),
                (random.uniform(0.030, 0.050), 0.010, random.uniform(0.12, 0.24)),
                MAT["void"],
                rot=(0, 0, math.radians(random.uniform(-10, 10))),
                collection="PC_V11_clay_sculpt_upgrade",
            )

    # Roof and side silhouette get hand-broken edge history.
    for i, (x, y, z, h, w, rz) in enumerate([
        (-0.78, -0.62, 3.82, 0.52, 0.070, -58),
        (-0.50, -0.52, 3.92, 0.42, 0.052, -47),
        (-0.18, -0.48, 4.00, 0.34, 0.046, -36),
        (0.20, -0.52, 3.96, 0.36, 0.050, 38),
        (0.56, -0.60, 3.84, 0.48, 0.064, 51),
        (0.85, -0.72, 3.70, 0.40, 0.055, 61),
    ]):
        chipped_board_mesh(
            f"PC_V11_5_roof_hand_broken_warped_board_{i:02d}",
            (x, y, z),
            h,
            w,
            MAT["wood"] if i % 2 else MAT["raw_wood"],
            rot=(math.radians(random.uniform(-2, 2)), math.radians(random.uniform(-16, 16)), math.radians(rz)),
            rows=10,
        )

    # Relic clay read: imperfect clocks/speakers and oval-damaged loops.
    for i, (x, z, sx, sy) in enumerate([
        (-0.55, 3.24, 1.18, 0.82),
        (0.42, 3.18, 0.86, 1.10),
        (0.66, 2.82, 1.08, 0.92),
    ]):
        ring = torus(
            f"PC_V11_5_oval_damaged_clock_rim_{i:02d}",
            (x, -1.176, z),
            0.070,
            0.006,
            MAT["metal"],
            rot=(math.radians(90), 0, math.radians(random.uniform(-6, 6))),
            collection="PC_V11_clay_sculpt_upgrade",
        )
        ring.scale.x *= sx
        ring.scale.y *= sy
        cyl(
            f"PC_V11_5_sunken_relic_face_{i:02d}",
            (x, -1.182, z),
            0.052,
            0.007,
            MAT["void"] if i == 1 else MAT["paper"],
            vertices=17,
            rot=(math.radians(90), 0, 0),
            collection="PC_V11_clay_sculpt_upgrade",
        )

    # Back shape: torn sheets with different depths so it reads disgusting in profile and back.
    for i, (x, y, z0, z1, wb, wt) in enumerate([
        (-0.60, 1.335, 1.22, 2.72, 0.08, 0.20),
        (-0.42, 1.355, 1.02, 2.46, 0.06, 0.16),
        (-0.16, 1.345, 1.15, 2.78, 0.10, 0.22),
        (0.08, 1.365, 0.92, 2.42, 0.06, 0.15),
        (0.34, 1.340, 1.18, 2.66, 0.07, 0.18),
        (0.58, 1.360, 1.05, 2.34, 0.05, 0.14),
    ]):
        ragged_panel(
            f"PC_V11_5_back_layered_rotten_sheet_{i:02d}",
            y,
            z0,
            z1,
            wb,
            wt,
            MAT["cloth"] if i != 2 else MAT["void"],
            x_center=x,
            cols=4,
            rows=15,
            collection="PC_V11_clay_sculpt_upgrade",
        )

    # The large right side wall still reads too untouched in clay. Add shallow history
    # without destroying the house silhouette.
    for i, (x, z, h, w, rz) in enumerate([
        (0.91, 2.82, 1.12, 0.040, -2),
        (1.00, 2.64, 0.84, 0.032, 3),
        (0.86, 3.22, 0.62, 0.026, -5),
        (1.04, 3.04, 0.72, 0.030, 6),
    ]):
        chipped_board_mesh(
            f"PC_V11_5_side_wall_subtle_chipped_history_{i:02d}",
            (x, 0.18, z),
            h,
            w,
            MAT["wood"],
            rot=(0, math.radians(90), math.radians(rz)),
            rows=10,
        )


def add_v11_6_end_goal_clay_refinement() -> None:
    random.seed(2616)

    # End-goal correction: the target's human is a hunched, crushed figure. Hide the
    # remaining smooth proxy ovals behind layered compression, not more generic noise.
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        lname = obj.name.lower()
        if any(k in lname for k in ["shoulder_meat", "low_hanging_abdomen", "left_shoulder_under_mask", "right_shoulder_under_mask"]):
            obj.scale.x *= 0.82
            obj.scale.z *= 0.88
            obj.location.y += 0.030
        elif "leg_lumpy_wrapped_volume" in lname:
            obj.scale.x *= 0.72
            obj.scale.z *= 0.90

    for i, (x, z, h, w, rz) in enumerate([
        (-0.34, 1.42, 0.74, 0.055, -9),
        (-0.21, 1.30, 1.02, 0.044, 5),
        (-0.08, 1.22, 1.24, 0.050, -2),
        (0.08, 1.28, 1.08, 0.045, 7),
        (0.22, 1.38, 0.82, 0.052, 13),
    ]):
        ragged_panel(
            f"PC_V11_6_front_weighted_torn_body_layer_{i:02d}",
            -1.445 - i * 0.004,
            z,
            z + h,
            w * 0.65,
            w,
            MAT["cloth"] if i != 2 else MAT["void"],
            x_center=x,
            cols=3,
            rows=13,
            collection="PC_V11_6_authored_clay_sculpt",
        )
        box(
            f"PC_V11_6_body_layer_anchor_fold_{i:02d}",
            (x + random.uniform(-0.020, 0.020), -1.475, z + h * random.uniform(0.40, 0.72)),
            (random.uniform(0.16, 0.28), 0.012, 0.018),
            MAT["cloth"],
            rot=(0, 0, math.radians(rz + random.uniform(-4, 4))),
            collection="PC_V11_6_authored_clay_sculpt",
        )

    # Head/mask: bring it closer to the reference's black hood and narrow hanging
    # door-plank face instead of a broad smooth plaque.
    ellipsoid(
        "PC_V11_6_deeper_hood_cavity_shadow",
        (0.0, -1.690, 2.80),
        0.19,
        MAT["void"],
        scale=(0.54, 0.045, 1.42),
        collection="PC_V11_6_authored_clay_sculpt",
    )
    for i, (x, h, z, rz) in enumerate([(-0.105, 1.20, 1.64, -2), (-0.032, 1.36, 1.58, 1), (0.044, 1.24, 1.62, -1), (0.118, 0.98, 1.70, 3)]):
        chipped_board_mesh(
            f"PC_V11_6_narrow_rotted_face_plank_{i:02d}",
            (x, -1.690, z),
            h,
            0.040,
            MAT["raw_wood"] if i in [0, 2] else MAT["wood"],
            rot=(0, 0, math.radians(rz)),
            rows=12,
            collection="PC_V11_6_authored_clay_sculpt",
        )
    for i, (x, z, rz) in enumerate([(-0.07, 2.16, -18), (0.07, 1.88, 14), (-0.03, 1.48, -12)]):
        box(
            f"PC_V11_6_face_lashed_crossbar_{i:02d}",
            (x, -1.715, z),
            (0.23 - i * 0.035, 0.012, 0.020),
            MAT["metal"],
            rot=(0, 0, math.radians(rz)),
            collection="PC_V11_6_authored_clay_sculpt",
        )

    # Replace visible perfect loop chains in the left hero silhouette with imperfect
    # hand-authored links. The target's bell chain is a major read.
    for obj in list(bpy.context.scene.objects):
        if obj.name.startswith("PC_V11_left_hand_hero_bell_chain_link"):
            bpy.data.objects.remove(obj, do_unlink=True)
    for i in range(9):
        sculpted_chain_link(
            f"PC_V11_6_left_hand_imperfect_chain_link_{i:02d}",
            (-0.82 + math.sin(i * 0.9) * 0.022, -1.175, 1.06 - i * 0.082),
            random.uniform(0.020, 0.032),
            random.uniform(0.036, 0.052),
            MAT["metal"],
            rot=(math.radians(90 + random.uniform(-8, 8)), math.radians(random.uniform(-5, 5)), math.radians((90 if i % 2 else 0) + random.uniform(-12, 12))),
        )

    # Hands and feet should not read as pads. Add long, uneven fingers/toes like the
    # orthographic reference.
    for side, sign in [("left", -1), ("right", 1)]:
        for i in range(5):
            sculpted_finger(
                f"PC_V11_6_{side}_knuckled_hanging_finger_{i:02d}",
                (sign * (0.70 + i * 0.022), -1.155, 0.82 - i * 0.018),
                random.uniform(0.14, 0.21),
                random.uniform(0.010, 0.015),
                MAT["cloth"],
                rot=(math.radians(random.uniform(-2, 2)), math.radians(sign * random.uniform(0, 8)), math.radians(sign * (8 + i * 5))),
            )
        for i in range(5):
            sculpted_finger(
                f"PC_V11_6_{side}_bare_splayed_toe_{i:02d}",
                (sign * (0.25 + i * 0.047), -1.135, 0.085 + random.uniform(-0.006, 0.010)),
                random.uniform(0.070, 0.105),
                random.uniform(0.010, 0.014),
                MAT["wrap_highlight"],
                rot=(math.radians(86), math.radians(sign * random.uniform(-5, 6)), math.radians(sign * random.uniform(-10, 12))),
            )

    # Break remaining flat back sheets into overlapping, thin layers. This should keep
    # the disgusting rear mass while avoiding broad generated curtains.
    for i, (x, z0, z1, wb, wt) in enumerate([
        (-0.68, 1.10, 2.55, 0.035, 0.11),
        (-0.51, 0.96, 2.30, 0.030, 0.09),
        (-0.24, 1.20, 2.72, 0.042, 0.13),
        (0.02, 0.90, 2.46, 0.030, 0.10),
        (0.23, 1.08, 2.68, 0.040, 0.12),
        (0.49, 0.98, 2.34, 0.026, 0.08),
        (0.70, 1.24, 2.62, 0.034, 0.10),
    ]):
        ragged_panel(
            f"PC_V11_6_back_thin_torn_rag_layer_{i:02d}",
            1.405 + random.uniform(-0.012, 0.014),
            z0,
            z1,
            wb,
            wt,
            MAT["cloth"] if i % 3 else MAT["void"],
            x_center=x,
            cols=3,
            rows=12,
            collection="PC_V11_6_authored_clay_sculpt",
        )

    # Shrine prop imperfection: non-perfect speaker/clock rims layered over the front.
    for i, (x, z) in enumerate([(-0.68, 3.26), (-0.42, 2.60), (0.22, 3.38), (0.58, 2.86)]):
        sculpted_chain_link(
            f"PC_V11_6_damaged_relic_outer_rim_{i:02d}",
            (x, -1.205, z),
            random.uniform(0.052, 0.076),
            random.uniform(0.044, 0.068),
            MAT["metal"],
            rot=(math.radians(90), 0, math.radians(random.uniform(-9, 9))),
            sides=20,
        )
        cyl(
            f"PC_V11_6_relic_deep_face_shadow_{i:02d}",
            (x + random.uniform(-0.010, 0.012), -1.214, z + random.uniform(-0.010, 0.012)),
            random.uniform(0.026, 0.044),
            0.006,
            MAT["void"],
            vertices=13,
            rot=(math.radians(90), 0, 0),
            collection="PC_V11_6_authored_clay_sculpt",
        )


def remove_objects_by_prefix(prefixes: tuple[str, ...]) -> None:
    for obj in list(bpy.context.scene.objects):
        if obj.name.startswith(prefixes):
            bpy.data.objects.remove(obj, do_unlink=True)


def add_v11_7_end_goal_readability_correction() -> None:
    random.seed(2717)

    # V11.6 gained useful authored detail, but the clay render drifted away from
    # the end-goal hierarchy. Pull it back toward: shrine silhouette, hood void,
    # long door-mask, crushed shoulders, hanging arms, then relic density.
    remove_objects_by_prefix((
        "PC_V11_5_long_cloth_valley_fold_",
        "PC_V11_5_side_wall_subtle_chipped_history_",
        "PC_V11_6_front_weighted_torn_body_layer_",
        "PC_V11_6_body_layer_anchor_fold_",
        "PC_V11_6_deeper_hood_cavity_shadow",
        "PC_V11_6_narrow_rotted_face_plank_",
        "PC_V11_6_face_lashed_crossbar_",
        "PC_V11_6_damaged_relic_outer_rim_",
        "PC_V11_6_relic_deep_face_shadow_",
    ))

    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        lname = obj.name.lower()
        if any(k in lname for k in [
            "head_black_inner_void",
            "head_vertical_black_void",
            "face_absolute_black_socket",
            "corrected_visible_black_head_void",
        ]):
            obj.scale.x *= 0.58
            obj.scale.z *= 0.84
            obj.location.z -= 0.020
        elif "hanging_mask_cloth_lobe" in lname:
            obj.scale.x *= 0.62
            obj.location.y += 0.030
        elif "authored_front_chipped_plank_03" in lname or "authored_front_chipped_plank_04" in lname:
            obj.scale.z *= 0.56
            obj.location.z += 0.36
        elif "twisted_hanging_torso_cloth_core" in lname:
            obj.scale.x *= 0.62
            obj.scale.y *= 0.82
            obj.location.y += 0.075
        elif "upper_arm_organic_sleeve" in lname or "forearm_organic_sleeve" in lname:
            obj.scale.x *= 0.78
            obj.scale.y *= 0.86

    # A single readable black hood socket replaces the competing oval shadows.
    ellipsoid(
        "PC_V11_7_single_narrow_hood_void_end_goal",
        (0.0, -1.735, 2.77),
        0.20,
        MAT["void"],
        scale=(0.34, 0.042, 1.18),
        collection="PC_V11_7_end_goal_readability",
    )
    ellipsoid(
        "PC_V11_7_left_sagging_hood_lip",
        (-0.105, -1.710, 2.86),
        0.145,
        MAT["cloth"],
        scale=(0.48, 0.13, 1.22),
        rot=(0, 0, math.radians(-15)),
        collection="PC_V11_7_end_goal_readability",
    )
    ellipsoid(
        "PC_V11_7_right_sagging_hood_lip",
        (0.115, -1.710, 2.83),
        0.135,
        MAT["cloth"],
        scale=(0.43, 0.13, 1.08),
        rot=(0, 0, math.radians(12)),
        collection="PC_V11_7_end_goal_readability",
    )
    ellipsoid(
        "PC_V11_7_compressed_wet_hood_brow",
        (-0.015, -1.725, 3.02),
        0.145,
        MAT["cloth"],
        scale=(1.34, 0.12, 0.28),
        rot=(0, 0, math.radians(-4)),
        collection="PC_V11_7_end_goal_readability",
    )

    # The end-goal face reads as a long nailed door plank hanging from the hood.
    ragged_panel(
        "PC_V11_7_long_rotted_door_mask_slab",
        -1.748,
        0.78,
        2.42,
        0.25,
        0.36,
        MAT["raw_wood"],
        x_center=-0.010,
        cols=6,
        rows=24,
        collection="PC_V11_7_end_goal_readability",
    )
    for i, (x, h, z, w, rz) in enumerate([
        (-0.125, 1.46, 1.58, 0.030, -2),
        (-0.055, 1.58, 1.52, 0.026, 1),
        (0.018, 1.50, 1.55, 0.032, -1),
        (0.092, 1.36, 1.62, 0.028, 3),
    ]):
        chipped_board_mesh(
            f"PC_V11_7_individual_face_plank_{i:02d}",
            (x, -1.782, z),
            h,
            w,
            MAT["raw_wood"] if i != 1 else MAT["wood"],
            rot=(0, 0, math.radians(rz)),
            rows=16,
            collection="PC_V11_7_end_goal_readability",
        )
    for i, (x, z, width, rz) in enumerate([(-0.02, 2.03, 0.24, -18), (0.02, 1.66, 0.19, 12), (-0.01, 1.27, 0.16, -10)]):
        box(
            f"PC_V11_7_face_lash_with_clear_spacing_{i:02d}",
            (x, -1.804, z),
            (width, 0.010, 0.018),
            MAT["metal"] if i != 1 else MAT["cloth"],
            rot=(0, 0, math.radians(rz)),
            collection="PC_V11_7_end_goal_readability",
        )
    for i, (x, z, h) in enumerate([(-0.092, 1.92, 0.30), (0.045, 1.38, 0.38), (0.115, 1.02, 0.26)]):
        box(
            f"PC_V11_7_door_mask_deep_split_{i:02d}",
            (x, -1.812, z),
            (0.012, 0.008, h),
            MAT["void"],
            rot=(0, 0, math.radians(random.uniform(-4, 5))),
            collection="PC_V11_7_end_goal_readability",
        )

    # Restore the target's asymmetric crushed human read: one heavy left arm with
    # a bell, one tighter right arm, and wrapped legs that do not look like poles.
    wrapped_limb_mesh(
        "PC_V11_7_left_arm_heavy_bowed_sleeve_end_goal",
        (-0.60, -1.36, 1.44),
        1.10,
        0.070,
        0.046,
        MAT["cloth"],
        rot=(math.radians(-7), math.radians(-18), math.radians(-22)),
        rings=24,
        sides=12,
        collection="PC_V11_7_end_goal_readability",
    )
    wrapped_limb_mesh(
        "PC_V11_7_left_forearm_pull_to_bell",
        (-0.76, -1.30, 0.98),
        0.74,
        0.055,
        0.038,
        MAT["cloth"],
        rot=(math.radians(-5), math.radians(-12), math.radians(-8)),
        rings=18,
        sides=10,
        collection="PC_V11_7_end_goal_readability",
    )
    wrapped_limb_mesh(
        "PC_V11_7_right_arm_tighter_hanging_sleeve",
        (0.56, -1.32, 1.32),
        0.96,
        0.058,
        0.040,
        MAT["cloth"],
        rot=(math.radians(2), math.radians(11), math.radians(11)),
        rings=20,
        sides=10,
        collection="PC_V11_7_end_goal_readability",
    )
    for side, sign in [("left", -1), ("right", 1)]:
        for i in range(4):
            sculpted_finger(
                f"PC_V11_7_{side}_long_uneven_visible_finger_{i:02d}",
                (sign * (0.70 + i * 0.018), -1.385, 0.73 - i * 0.018),
                random.uniform(0.13, 0.19),
                random.uniform(0.008, 0.012),
                MAT["cloth"],
                rot=(math.radians(random.uniform(-4, 3)), math.radians(sign * random.uniform(1, 10)), math.radians(sign * (8 + i * 6))),
                collection="PC_V11_7_end_goal_readability",
            )

    # Keep relic density, but make a few larger end-goal props carry the read.
    for i, (x, z, sx, sz) in enumerate([
        (-0.62, 3.10, 0.070, 0.056),
        (-0.30, 2.78, 0.052, 0.070),
        (0.28, 3.18, 0.078, 0.060),
        (0.58, 2.78, 0.060, 0.050),
    ]):
        sculpted_chain_link(
            f"PC_V11_7_imperfect_front_clock_speaker_rim_{i:02d}",
            (x, -1.240, z),
            sx,
            sz,
            MAT["metal"],
            rot=(math.radians(90), 0, math.radians(random.uniform(-8, 8))),
            sides=22,
            collection="PC_V11_7_end_goal_readability",
        )
        cyl(
            f"PC_V11_7_relic_inset_dark_center_{i:02d}",
            (x + random.uniform(-0.008, 0.008), -1.250, z + random.uniform(-0.008, 0.008)),
            min(sx, sz) * 0.50,
            0.006,
            MAT["void"] if i in [1, 3] else MAT["paper"],
            vertices=15,
            rot=(math.radians(90), 0, 0),
            collection="PC_V11_7_end_goal_readability",
        )

    # Break the back into disgusting interior gaps and hanging skin without making
    # the entire back a flat curtain.
    for i, (x, z0, z1, wb, wt) in enumerate([
        (-0.42, 1.04, 2.52, 0.030, 0.12),
        (-0.15, 0.88, 2.36, 0.026, 0.10),
        (0.16, 1.10, 2.62, 0.034, 0.13),
        (0.43, 0.96, 2.28, 0.024, 0.09),
    ]):
        ragged_panel(
            f"PC_V11_7_back_rotten_interior_tongue_{i:02d}",
            1.470 + random.uniform(-0.015, 0.012),
            z0,
            z1,
            wb,
            wt,
            MAT["void"] if i == 1 else MAT["cloth"],
            x_center=x,
            cols=3,
            rows=14,
            collection="PC_V11_7_end_goal_readability",
        )

    # The target has a strong left-side bell silhouette. Reassert that anchor after
    # the cleanup so the hand/bell relationship is legible from a distance.
    sculpted_bell("PC_V11_7_left_hand_end_goal_bell_reasserted", (-0.88, -1.33, 0.48), 0.82, collection="PC_V11_7_end_goal_readability")


def sculpted_hood_arch_mesh(
    name: str,
    loc: tuple[float, float, float],
    width: float,
    height: float,
    tube_x: float,
    tube_y: float,
    mat: bpy.types.Material,
    collection: str = "PC_V11_8_head_mask_reference_lock",
) -> bpy.types.Object:
    verts: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int, int]] = []
    segments = 28
    sides = 8
    phase = random.uniform(0, math.tau)
    for i in range(segments + 1):
        t = i / segments
        angle = math.radians(205 - 230 * t)
        cx = math.cos(angle) * width * 0.5
        cz = math.sin(angle) * height * 0.5
        wobble = 1.0 + 0.06 * math.sin(i * 1.7 + phase)
        for s in range(sides):
            a = s / sides * math.tau
            x = cx + math.cos(a) * tube_x * wobble
            y = math.sin(a) * tube_y * (1.0 + 0.08 * math.sin(i + s + phase))
            z = cz + math.sin(a) * tube_x * 0.75
            verts.append((x, y, z))
    for i in range(segments):
        for s in range(sides):
            faces.append((
                i * sides + s,
                (i + 1) * sides + s,
                (i + 1) * sides + (s + 1) % sides,
                i * sides + (s + 1) % sides,
            ))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = loc
    bpy.context.scene.collection.objects.link(obj)
    assign(obj, mat)
    shade(obj)
    return move_to(obj, collection)


def add_v11_8_head_mask_reference_lock() -> None:
    random.seed(2818)

    # The previous passes left several overlapping hood sockets. Remove them and
    # rebuild one target-like head: narrow black opening inside a wet arched hood,
    # attached directly to the long door-mask plank.
    remove_objects_by_prefix((
        "PC_BlackVoid_face_slot",
        "PC_HangingFaceMask_long_wood",
        "PC_V6_head_vertical_black_void",
        "PC_V6_long_door_mask_front",
        "PC_V6_door_mask_",
        "PC_V8_head_black_inner_void",
        "PC_V8_wet_hood_lip_",
        "PC_V8_face_door_rotten_strip_",
        "PC_V8_face_mask_stitch_",
        "PC_V11_hanging_mask_cloth_lobe_",
        "PC_V11_head_hood_",
        "PC_V11_face_absolute_black_socket",
        "PC_V11_face_nested_rotten_board_",
        "PC_V11_black_inner_hanging_cloth_behind_mask",
        "PC_V11_warped_central_door_mask_panel",
        "PC_V11_mask_cross_tension_lash_",
        "PC_V11_corrected_visible_black_head_void",
        "PC_V11_corrected_wet_hood_brow",
        "PC_V11_door_panel_vertical_split_",
        "PC_V11_door_panel_dark_crack_",
        "PC_V11_7_single_narrow_hood_void_end_goal",
        "PC_V11_7_left_sagging_hood_lip",
        "PC_V11_7_right_sagging_hood_lip",
        "PC_V11_7_compressed_wet_hood_brow",
        "PC_V11_7_long_rotted_door_mask_slab",
        "PC_V11_7_individual_face_plank_",
        "PC_V11_7_face_lash_with_clear_spacing_",
        "PC_V11_7_door_mask_deep_split_",
    ))

    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        lname = obj.name.lower()
        if "crushed_left_shoulder_meat" in lname:
            obj.scale.x *= 0.82
            obj.location.x -= 0.035
            obj.location.z -= 0.020
        elif "crushed_right_shoulder_meat" in lname:
            obj.scale.x *= 0.76
            obj.location.x += 0.030
            obj.location.z -= 0.040
        elif "sunken_chest_under_mask" in lname or "low_hanging_abdomen" in lname:
            obj.scale.x *= 0.70
            obj.location.y += 0.060
        elif "authored_front_chipped_plank_02" in lname or "authored_front_chipped_plank_05" in lname:
            obj.scale.z *= 0.72
            obj.location.z += 0.18

    sculpted_hood_arch_mesh(
        "PC_V11_8_wrapped_arched_hood_exact_target_read",
        (0.0, -1.820, 2.68),
        0.48,
        0.62,
        0.043,
        0.020,
        MAT["cloth"],
    )
    ellipsoid(
        "PC_V11_8_single_black_face_hole_inside_arch",
        (0.0, -1.846, 2.67),
        0.155,
        MAT["void"],
        scale=(0.42, 0.040, 1.16),
        collection="PC_V11_8_head_mask_reference_lock",
    )
    ellipsoid(
        "PC_V11_8_small_hanging_inner_clapper_shape",
        (0.0, -1.870, 2.64),
        0.042,
        MAT["brass"],
        scale=(0.55, 0.40, 1.35),
        collection="PC_V11_8_head_mask_reference_lock",
    )

    ragged_panel(
        "PC_V11_8_dark_cloth_backing_tied_to_door_mask",
        -1.820,
        0.92,
        2.55,
        0.30,
        0.42,
        MAT["void"],
        cols=5,
        rows=20,
        collection="PC_V11_8_head_mask_reference_lock",
    )
    ragged_panel(
        "PC_V11_8_center_rotted_hanging_face_door",
        -1.852,
        0.80,
        2.38,
        0.26,
        0.34,
        MAT["raw_wood"],
        cols=6,
        rows=24,
        collection="PC_V11_8_head_mask_reference_lock",
    )
    for i, (x, z, h, w, rz) in enumerate([
        (-0.122, 1.58, 1.44, 0.030, -3),
        (-0.052, 1.56, 1.54, 0.025, 1),
        (0.012, 1.54, 1.50, 0.032, -1),
        (0.078, 1.58, 1.38, 0.026, 4),
        (0.135, 1.62, 1.18, 0.021, 2),
    ]):
        chipped_board_mesh(
            f"PC_V11_8_door_mask_separate_warped_plank_{i:02d}",
            (x, -1.884, z),
            h,
            w,
            MAT["raw_wood"] if i in [0, 2, 4] else MAT["wood"],
            rot=(0, 0, math.radians(rz)),
            rows=16,
            collection="PC_V11_8_head_mask_reference_lock",
        )
    for i, (x, z, width, rz) in enumerate([(0.005, 2.15, 0.22, -15), (-0.012, 1.78, 0.19, 13), (0.008, 1.36, 0.16, -11)]):
        box(
            f"PC_V11_8_mask_lash_not_evenly_spaced_{i:02d}",
            (x, -1.902, z),
            (width, 0.010, 0.017),
            MAT["metal"] if i != 1 else MAT["cloth"],
            rot=(0, 0, math.radians(rz)),
            collection="PC_V11_8_head_mask_reference_lock",
        )
    for i, (x, z, h) in enumerate([(-0.085, 1.98, 0.22), (0.040, 1.54, 0.34), (0.108, 1.12, 0.24)]):
        box(
            f"PC_V11_8_door_crack_deep_black_{i:02d}",
            (x, -1.912, z),
            (0.010, 0.008, h),
            MAT["void"],
            rot=(0, 0, math.radians(random.uniform(-5, 5))),
            collection="PC_V11_8_head_mask_reference_lock",
        )


def add_v11_9_ragged_hood_door_silhouette() -> None:
    random.seed(2919)

    # V11.8 made the head readable but too icon-like. Replace the clean U ring
    # with an uneven wet hood wrapped onto the door slab, matching the reference
    # where the head is a dark opening buried in cloth/wood, not a perfect symbol.
    remove_objects_by_prefix((
        "PC_V11_8_wrapped_arched_hood_exact_target_read",
        "PC_V11_8_single_black_face_hole_inside_arch",
        "PC_V11_8_small_hanging_inner_clapper_shape",
        "PC_V11_8_dark_cloth_backing_tied_to_door_mask",
        "PC_V11_8_center_rotted_hanging_face_door",
        "PC_V11_8_door_mask_separate_warped_plank_",
        "PC_V11_8_mask_lash_not_evenly_spaced_",
        "PC_V11_8_door_crack_deep_black_",
    ))

    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        lname = obj.name.lower()
        if "twisted_hanging_torso_cloth_core" in lname:
            obj.scale.x *= 0.54
            obj.scale.z *= 0.86
            obj.location.y += 0.090
        elif "left_torn_front_cloak_sheet" in lname:
            obj.scale.x *= 0.78
            obj.location.x -= 0.065
        elif "right_torn_front_cloak_sheet" in lname:
            obj.scale.x *= 0.74
            obj.location.x += 0.070

    # Long central face slab: this is the target's clearest human/head cue.
    ragged_panel(
        "PC_V11_9_one_piece_long_door_face_slab",
        -1.890,
        0.76,
        2.56,
        0.25,
        0.38,
        MAT["raw_wood"],
        cols=7,
        rows=26,
        collection="PC_V11_9_ragged_hood_door_silhouette",
    )
    for i, (x, z, h, w, rz) in enumerate([
        (-0.135, 1.58, 1.52, 0.027, -2),
        (-0.065, 1.55, 1.66, 0.022, 1),
        (0.004, 1.56, 1.62, 0.028, -1),
        (0.072, 1.59, 1.48, 0.024, 3),
        (0.132, 1.62, 1.28, 0.020, -4),
    ]):
        chipped_board_mesh(
            f"PC_V11_9_visible_splintered_face_board_{i:02d}",
            (x, -1.923, z),
            h,
            w,
            MAT["raw_wood"] if i != 3 else MAT["wood"],
            rot=(0, 0, math.radians(rz)),
            rows=16,
            collection="PC_V11_9_ragged_hood_door_silhouette",
        )

    # Hood is built from sagging cloth lobes with a small black opening, avoiding
    # the perfect circular arch that broke the clay read.
    ellipsoid(
        "PC_V11_9_small_black_hood_opening",
        (0.0, -1.948, 2.63),
        0.150,
        MAT["void"],
        scale=(0.40, 0.040, 1.05),
        collection="PC_V11_9_ragged_hood_door_silhouette",
    )
    for i, (x, z, sx, sz, rz) in enumerate([
        (-0.175, 2.62, 0.42, 1.28, -15),
        (-0.085, 2.80, 0.48, 0.54, -5),
        (0.050, 2.82, 0.58, 0.44, 4),
        (0.175, 2.60, 0.38, 1.16, 13),
    ]):
        ellipsoid(
            f"PC_V11_9_sagging_hood_cloth_mass_{i:02d}",
            (x, -1.932, z),
            0.125,
            MAT["cloth"],
            scale=(sx, 0.12, sz),
            rot=(0, 0, math.radians(rz)),
            collection="PC_V11_9_ragged_hood_door_silhouette",
        )
    for i, (x, z, h, rz) in enumerate([(-0.205, 2.38, 0.44, -9), (0.196, 2.36, 0.42, 8)]):
        chipped_board_mesh(
            f"PC_V11_9_hood_side_crushed_edge_{i:02d}",
            (x, -1.950, z),
            h,
            0.034,
            MAT["cloth"],
            rot=(0, 0, math.radians(rz)),
            rows=9,
            collection="PC_V11_9_ragged_hood_door_silhouette",
        )

    for i, (x, z, width, rz) in enumerate([(-0.004, 2.14, 0.22, -16), (0.020, 1.76, 0.18, 12), (-0.010, 1.32, 0.15, -10)]):
        box(
            f"PC_V11_9_door_lash_scar_{i:02d}",
            (x, -1.945, z),
            (width, 0.010, 0.016),
            MAT["metal"] if i != 1 else MAT["cloth"],
            rot=(0, 0, math.radians(rz)),
            collection="PC_V11_9_ragged_hood_door_silhouette",
        )
    for i, (x, z, h) in enumerate([(-0.088, 1.94, 0.26), (0.030, 1.47, 0.36), (0.112, 1.02, 0.24)]):
        box(
            f"PC_V11_9_door_dark_splinter_gap_{i:02d}",
            (x, -1.956, z),
            (0.010, 0.008, h),
            MAT["void"],
            rot=(0, 0, math.radians(random.uniform(-4, 5))),
            collection="PC_V11_9_ragged_hood_door_silhouette",
        )


def add_v12_head_readability_checkpoint() -> None:
    random.seed(3012)

    # The rounded hood lobes made V11.9 read too face-like and clean. Replace
    # them with flatter torn hood panels so the head becomes a dark, buried slot
    # attached to the long wooden mask, closer to Penance_End_Goal.
    remove_objects_by_prefix((
        "PC_V11_9_small_black_hood_opening",
        "PC_V11_9_sagging_hood_cloth_mass_",
        "PC_V11_9_hood_side_crushed_edge_",
    ))

    ragged_panel(
        "PC_V12_left_flat_torn_hood_side",
        -1.955,
        2.24,
        2.86,
        0.055,
        0.120,
        MAT["cloth"],
        x_center=-0.175,
        cols=3,
        rows=10,
        collection="PC_V12_head_readability_checkpoint",
    )
    ragged_panel(
        "PC_V12_right_flat_torn_hood_side",
        -1.957,
        2.20,
        2.82,
        0.045,
        0.105,
        MAT["cloth"],
        x_center=0.165,
        cols=3,
        rows=10,
        collection="PC_V12_head_readability_checkpoint",
    )
    box(
        "PC_V12_compressed_uneven_hood_brow",
        (-0.012, -1.972, 2.82),
        (0.345, 0.018, 0.045),
        MAT["cloth"],
        rot=(0, 0, math.radians(-4)),
        collection="PC_V12_head_readability_checkpoint",
    )
    box(
        "PC_V12_lower_wet_hood_fold_shadow",
        (0.012, -1.976, 2.44),
        (0.275, 0.014, 0.040),
        MAT["cloth"],
        rot=(0, 0, math.radians(5)),
        collection="PC_V12_head_readability_checkpoint",
    )
    ellipsoid(
        "PC_V12_single_readable_black_head_slot",
        (0.0, -1.988, 2.61),
        0.138,
        MAT["void"],
        scale=(0.36, 0.036, 0.96),
        collection="PC_V12_head_readability_checkpoint",
    )
    ellipsoid(
        "PC_V12_tiny_hanging_glint_inside_slot",
        (-0.004, -2.006, 2.56),
        0.028,
        MAT["brass"],
        scale=(0.58, 0.40, 1.20),
        collection="PC_V12_head_readability_checkpoint",
    )

    for i, (x, z, h, rz) in enumerate([(-0.170, 2.36, 0.30, -8), (0.155, 2.32, 0.28, 7), (-0.058, 2.18, 0.22, 3), (0.062, 2.08, 0.18, -5)]):
        box(
            f"PC_V12_short_hood_to_door_overlap_strip_{i:02d}",
            (x, -1.990, z),
            (0.025, 0.010, h),
            MAT["cloth"] if i < 2 else MAT["wood"],
            rot=(0, 0, math.radians(rz)),
            collection="PC_V12_head_readability_checkpoint",
        )


def add_v13_hood_door_integration() -> None:
    random.seed(3113)

    # V12 made the head legible but still too box-framed. This pass removes the
    # remaining symbolic head construction and rebuilds the target read: wet hood
    # collapsed around a black opening, with the long rotten door-mask continuing
    # down from it as one vertical object.
    remove_objects_by_prefix((
        "PC_V11_9_one_piece_long_door_face_slab",
        "PC_V11_9_visible_splintered_face_board_",
        "PC_V11_9_door_lash_scar_",
        "PC_V11_9_door_dark_splinter_gap_",
        "PC_V12_left_flat_torn_hood_side",
        "PC_V12_right_flat_torn_hood_side",
        "PC_V12_compressed_uneven_hood_brow",
        "PC_V12_lower_wet_hood_fold_shadow",
        "PC_V12_single_readable_black_head_slot",
        "PC_V12_tiny_hanging_glint_inside_slot",
        "PC_V12_short_hood_to_door_overlap_strip_",
    ))

    # Quiet a few big smooth primitive leftovers around the face so the new hood
    # is not fighting oval masses in the clay read.
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        lname = obj.name.lower()
        if "crushed_left_shoulder_meat" in lname:
            obj.scale.x *= 0.72
            obj.scale.z *= 0.78
            obj.location.x -= 0.050
            obj.location.y += 0.030
        elif "crushed_right_shoulder_meat" in lname:
            obj.scale.x *= 0.70
            obj.scale.z *= 0.74
            obj.location.x += 0.050
            obj.location.y += 0.034
        elif "low_hanging_abdomen" in lname or "sunken_chest_under_mask" in lname:
            obj.scale.x *= 0.68
            obj.location.y += 0.050
        elif "left_arm_heavy_bowed_sleeve" in lname:
            obj.scale.x *= 0.82
            obj.location.x -= 0.035
        elif "right_arm_tighter_hanging_sleeve" in lname:
            obj.scale.x *= 0.80
            obj.location.x += 0.040

    # One continuous mask backer, then individual warped boards over it.
    ragged_panel(
        "PC_V13_deep_black_cloth_inside_hood_and_door",
        -1.965,
        0.88,
        2.74,
        0.28,
        0.46,
        MAT["void"],
        cols=5,
        rows=22,
        collection="PC_V13_hood_door_integration",
    )
    ragged_panel(
        "PC_V13_long_target_door_mask_unbroken_slab",
        -1.990,
        0.74,
        2.48,
        0.25,
        0.36,
        MAT["raw_wood"],
        cols=7,
        rows=28,
        collection="PC_V13_hood_door_integration",
    )
    for i, (x, z, h, w, rz) in enumerate([
        (-0.132, 1.56, 1.56, 0.024, -2),
        (-0.068, 1.54, 1.68, 0.021, 1),
        (-0.008, 1.55, 1.64, 0.025, -1),
        (0.058, 1.57, 1.52, 0.023, 2),
        (0.122, 1.60, 1.32, 0.020, -3),
    ]):
        chipped_board_mesh(
            f"PC_V13_splintered_vertical_face_board_{i:02d}",
            (x, -2.022, z),
            h,
            w,
            MAT["raw_wood"] if i != 1 else MAT["wood"],
            rot=(0, 0, math.radians(rz)),
            rows=18,
            collection="PC_V13_hood_door_integration",
        )

    # Irregular hood: no perfect U, no square top rail. Built from sagged panels
    # and small overlap strips with different depths.
    ragged_panel(
        "PC_V13_left_heavy_wet_hood_flap",
        -2.012,
        2.18,
        2.92,
        0.045,
        0.145,
        MAT["cloth"],
        x_center=-0.178,
        cols=4,
        rows=13,
        collection="PC_V13_hood_door_integration",
    )
    ragged_panel(
        "PC_V13_right_heavy_wet_hood_flap",
        -2.014,
        2.15,
        2.86,
        0.040,
        0.125,
        MAT["cloth"],
        x_center=0.154,
        cols=4,
        rows=12,
        collection="PC_V13_hood_door_integration",
    )
    for i, (x, z, w, h, rz, mat_key) in enumerate([
        (-0.095, 2.88, 0.160, 0.030, -11, "cloth"),
        (0.050, 2.84, 0.185, 0.026, 7, "cloth"),
        (-0.018, 2.42, 0.210, 0.024, 4, "cloth"),
        (-0.150, 2.35, 0.028, 0.310, -8, "cloth"),
        (0.142, 2.31, 0.026, 0.280, 7, "cloth"),
    ]):
        box(
            f"PC_V13_uneven_hood_overlap_piece_{i:02d}",
            (x, -2.032 - i * 0.002, z),
            (w, 0.012, h),
            MAT[mat_key],
            rot=(0, 0, math.radians(rz)),
            collection="PC_V13_hood_door_integration",
        )

    ellipsoid(
        "PC_V13_narrow_buried_black_head_socket",
        (-0.006, -2.046, 2.63),
        0.128,
        MAT["void"],
        scale=(0.34, 0.034, 1.08),
        collection="PC_V13_hood_door_integration",
    )
    ellipsoid(
        "PC_V13_tiny_low_hanging_relic_inside_socket",
        (-0.002, -2.068, 2.58),
        0.024,
        MAT["brass"],
        scale=(0.55, 0.38, 1.35),
        collection="PC_V13_hood_door_integration",
    )

    for i, (x, z, width, rz) in enumerate([(-0.006, 2.10, 0.215, -17), (0.018, 1.74, 0.178, 13), (-0.020, 1.31, 0.148, -10)]):
        box(
            f"PC_V13_mask_lash_embedded_in_wood_{i:02d}",
            (x, -2.046, z),
            (width, 0.010, 0.015),
            MAT["metal"] if i != 1 else MAT["cloth"],
            rot=(0, 0, math.radians(rz)),
            collection="PC_V13_hood_door_integration",
        )
    for i, (x, z, h) in enumerate([(-0.092, 1.94, 0.27), (0.032, 1.50, 0.35), (0.106, 1.08, 0.22)]):
        box(
            f"PC_V13_door_deep_vertical_crack_{i:02d}",
            (x, -2.058, z),
            (0.009, 0.008, h),
            MAT["void"],
            rot=(0, 0, math.radians(random.uniform(-5, 5))),
            collection="PC_V13_hood_door_integration",
        )


def add_v14_human_silhouette_lock() -> None:
    random.seed(3214)

    # The reference reads from distance as: shrine, clear hooded head, long door
    # mask, crushed shoulders, arms. Clear the central front clutter that was
    # burying that hierarchy, then place a stronger authored human read forward.
    for obj in list(bpy.context.scene.objects):
        if obj.type != "MESH" or obj.name.startswith(("PC_V13_", "PC_V14_")):
            continue
        lx, ly, lz = obj.location.x, obj.location.y, obj.location.z
        lname = obj.name.lower()
        is_central = -0.32 <= lx <= 0.32 and ly < -0.86 and 0.95 <= lz <= 3.30
        is_noise = any(k in lname for k in [
            "plank", "strip", "fray", "cord", "chain", "rim", "relic", "radio",
            "clock", "speaker", "cassette", "candle", "stitch", "lash", "gap",
        ])
        if is_central and is_noise:
            bpy.data.objects.remove(obj, do_unlink=True)

    remove_objects_by_prefix((
        "PC_V13_deep_black_cloth_inside_hood_and_door",
        "PC_V13_long_target_door_mask_unbroken_slab",
        "PC_V13_splintered_vertical_face_board_",
        "PC_V13_left_heavy_wet_hood_flap",
        "PC_V13_right_heavy_wet_hood_flap",
        "PC_V13_uneven_hood_overlap_piece_",
        "PC_V13_narrow_buried_black_head_socket",
        "PC_V13_tiny_low_hanging_relic_inside_socket",
        "PC_V13_mask_lash_embedded_in_wood_",
        "PC_V13_door_deep_vertical_crack_",
    ))

    ragged_panel(
        "PC_V14_deep_hood_void_backer",
        -2.120,
        1.02,
        2.92,
        0.34,
        0.54,
        MAT["void"],
        cols=5,
        rows=22,
        collection="PC_V14_human_silhouette_lock",
    )
    ragged_panel(
        "PC_V14_large_rotten_door_mask_primary",
        -2.155,
        0.74,
        2.48,
        0.33,
        0.43,
        MAT["raw_wood"],
        cols=7,
        rows=28,
        collection="PC_V14_human_silhouette_lock",
    )
    for i, (x, h, z, w, rz) in enumerate([
        (-0.155, 1.54, 1.58, 0.032, -2),
        (-0.078, 1.70, 1.52, 0.026, 1),
        (0.000, 1.66, 1.55, 0.034, -1),
        (0.082, 1.50, 1.60, 0.028, 3),
        (0.155, 1.28, 1.66, 0.023, -3),
    ]):
        chipped_board_mesh(
            f"PC_V14_bold_face_board_{i:02d}",
            (x, -2.190, z),
            h,
            w,
            MAT["raw_wood"] if i != 2 else MAT["wood"],
            rot=(0, 0, math.radians(rz)),
            rows=18,
            collection="PC_V14_human_silhouette_lock",
        )

    # Bigger, reference-like hood opening. It is narrow and vertical but surrounded
    # by torn cloth instead of a square frame.
    ellipsoid(
        "PC_V14_clearest_black_head_socket",
        (0.0, -2.218, 2.66),
        0.160,
        MAT["void"],
        scale=(0.44, 0.035, 1.20),
        collection="PC_V14_human_silhouette_lock",
    )
    ragged_panel(
        "PC_V14_left_wrapped_hood_cheek_flap",
        -2.207,
        2.22,
        2.96,
        0.050,
        0.165,
        MAT["cloth"],
        x_center=-0.205,
        cols=4,
        rows=14,
        collection="PC_V14_human_silhouette_lock",
    )
    ragged_panel(
        "PC_V14_right_wrapped_hood_cheek_flap",
        -2.210,
        2.18,
        2.88,
        0.046,
        0.145,
        MAT["cloth"],
        x_center=0.190,
        cols=4,
        rows=13,
        collection="PC_V14_human_silhouette_lock",
    )
    for i, (x, z, w, rz) in enumerate([(-0.085, 2.92, 0.19, -12), (0.070, 2.86, 0.22, 8), (-0.005, 2.41, 0.25, 4)]):
        box(
            f"PC_V14_torn_hood_brow_not_bar_{i:02d}",
            (x, -2.232, z),
            (w, 0.010, 0.026),
            MAT["cloth"],
            rot=(0, 0, math.radians(rz)),
            collection="PC_V14_human_silhouette_lock",
        )

    # Shoulders and upper arms need to frame the door-mask like the reference.
    wrapped_limb_mesh(
        "PC_V14_left_compressed_shoulder_under_hood",
        (-0.365, -2.065, 2.08),
        0.55,
        0.105,
        0.050,
        MAT["cloth"],
        rot=(math.radians(0), math.radians(-8), math.radians(-63)),
        rings=16,
        sides=12,
        collection="PC_V14_human_silhouette_lock",
    )
    wrapped_limb_mesh(
        "PC_V14_right_compressed_shoulder_under_hood",
        (0.340, -2.060, 2.02),
        0.46,
        0.095,
        0.046,
        MAT["cloth"],
        rot=(math.radians(0), math.radians(7), math.radians(58)),
        rings=14,
        sides=12,
        collection="PC_V14_human_silhouette_lock",
    )
    for i, (x, z, width, rz) in enumerate([(-0.010, 2.12, 0.25, -16), (0.016, 1.72, 0.20, 12), (-0.018, 1.31, 0.16, -10)]):
        box(
            f"PC_V14_mask_lash_clear_but_irregular_{i:02d}",
            (x, -2.236, z),
            (width, 0.010, 0.015),
            MAT["metal"] if i != 1 else MAT["cloth"],
            rot=(0, 0, math.radians(rz)),
            collection="PC_V14_human_silhouette_lock",
        )
    for i, (x, z, h) in enumerate([(-0.104, 1.90, 0.28), (0.038, 1.48, 0.34), (0.118, 1.05, 0.23)]):
        box(
            f"PC_V14_door_deep_splinter_void_{i:02d}",
            (x, -2.246, z),
            (0.010, 0.008, h),
            MAT["void"],
            rot=(0, 0, math.radians(random.uniform(-5, 5))),
            collection="PC_V14_human_silhouette_lock",
        )


def add_v15_mask_material_balance() -> None:
    random.seed(3315)

    # V14 proved the silhouette direction, but the mask became a black rectangle.
    # Reduce void material to the actual hood opening and splinter gaps; let the
    # door read as rotten wood again, like the target face/mask callout.
    remove_objects_by_prefix((
        "PC_V14_deep_hood_void_backer",
        "PC_V14_large_rotten_door_mask_primary",
        "PC_V14_bold_face_board_",
        "PC_V14_clearest_black_head_socket",
        "PC_V14_left_wrapped_hood_cheek_flap",
        "PC_V14_right_wrapped_hood_cheek_flap",
        "PC_V14_torn_hood_brow_not_bar_",
        "PC_V14_mask_lash_clear_but_irregular_",
        "PC_V14_door_deep_splinter_void_",
    ))

    ragged_panel(
        "PC_V15_rotten_wood_door_mask_broad_read",
        -2.170,
        0.72,
        2.45,
        0.34,
        0.42,
        MAT["raw_wood"],
        cols=8,
        rows=30,
        collection="PC_V15_mask_material_balance",
    )
    for i, (x, h, z, w, rz) in enumerate([
        (-0.150, 1.48, 1.58, 0.030, -2),
        (-0.075, 1.66, 1.52, 0.024, 1),
        (-0.006, 1.62, 1.55, 0.032, -1),
        (0.070, 1.48, 1.60, 0.026, 3),
        (0.145, 1.26, 1.66, 0.022, -3),
    ]):
        chipped_board_mesh(
            f"PC_V15_visible_rotted_face_plank_{i:02d}",
            (x, -2.205, z),
            h,
            w,
            MAT["raw_wood"] if i != 2 else MAT["wood"],
            rot=(0, 0, math.radians(rz)),
            rows=18,
            collection="PC_V15_mask_material_balance",
        )

    # Hood cloth is dark and wet, but not a black box.
    ragged_panel(
        "PC_V15_left_wet_hood_wrapped_edge",
        -2.205,
        2.18,
        2.90,
        0.045,
        0.145,
        MAT["cloth"],
        x_center=-0.190,
        cols=4,
        rows=14,
        collection="PC_V15_mask_material_balance",
    )
    ragged_panel(
        "PC_V15_right_wet_hood_wrapped_edge",
        -2.208,
        2.15,
        2.84,
        0.040,
        0.125,
        MAT["cloth"],
        x_center=0.175,
        cols=4,
        rows=13,
        collection="PC_V15_mask_material_balance",
    )
    for i, (x, z, w, rz) in enumerate([(-0.085, 2.86, 0.170, -10), (0.060, 2.82, 0.200, 7), (-0.005, 2.39, 0.225, 3)]):
        box(
            f"PC_V15_crushed_hood_lip_fragment_{i:02d}",
            (x, -2.232, z),
            (w, 0.010, 0.024),
            MAT["cloth"],
            rot=(0, 0, math.radians(rz)),
            collection="PC_V15_mask_material_balance",
        )

    ellipsoid(
        "PC_V15_actual_narrow_black_head_opening",
        (-0.006, -2.238, 2.62),
        0.145,
        MAT["void"],
        scale=(0.36, 0.030, 1.10),
        collection="PC_V15_mask_material_balance",
    )
    ellipsoid(
        "PC_V15_small_relic_glint_inside_head_opening",
        (-0.002, -2.258, 2.56),
        0.024,
        MAT["brass"],
        scale=(0.55, 0.35, 1.20),
        collection="PC_V15_mask_material_balance",
    )
    for i, (x, z, width, rz) in enumerate([(-0.010, 2.11, 0.235, -16), (0.018, 1.72, 0.190, 12), (-0.018, 1.30, 0.155, -10)]):
        box(
            f"PC_V15_mask_lash_embedded_not_bar_{i:02d}",
            (x, -2.242, z),
            (width, 0.010, 0.014),
            MAT["metal"] if i != 1 else MAT["cloth"],
            rot=(0, 0, math.radians(rz)),
            collection="PC_V15_mask_material_balance",
        )
    for i, (x, z, h) in enumerate([(-0.100, 1.92, 0.27), (0.036, 1.48, 0.34), (0.114, 1.05, 0.23), (-0.018, 0.92, 0.18)]):
        box(
            f"PC_V15_thin_door_splinter_shadow_{i:02d}",
            (x, -2.252, z),
            (0.009, 0.007, h),
            MAT["void"],
            rot=(0, 0, math.radians(random.uniform(-5, 5))),
            collection="PC_V15_mask_material_balance",
        )


def add_v16_hero_anatomy_weight() -> None:
    random.seed(3416)

    # Remove front-center prop loops that read like a second face and compete with
    # the target's hood socket. The shrine can be dense, but the mask corridor
    # must stay readable.
    for obj in list(bpy.context.scene.objects):
        if obj.type != "MESH":
            continue
        lname = obj.name.lower()
        lx, ly, lz = obj.location.x, obj.location.y, obj.location.z
        central_face_noise = -0.42 <= lx <= 0.42 and ly < -0.78 and 2.20 <= lz <= 3.10
        relic_or_ring = any(k in lname for k in ["clock", "speaker", "rim", "relic", "torus", "ring", "radio", "cassette"])
        if central_face_noise and relic_or_ring:
            bpy.data.objects.remove(obj, do_unlink=True)

    # Pull back old arm/panel shapes that were reading like vertical boards.
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        lname = obj.name.lower()
        if "left_arm_heavy_bowed_sleeve" in lname or "right_arm_tighter_hanging_sleeve" in lname:
            obj.scale.x *= 0.62
            obj.location.y += 0.060
        elif "left_compressed_shoulder_under_hood" in lname:
            obj.scale.x *= 0.82
            obj.location.x -= 0.035
        elif "right_compressed_shoulder_under_hood" in lname:
            obj.scale.x *= 0.82
            obj.location.x += 0.030

    # Rebuild the target's human read: hunched shoulders, asymmetric arms, and a
    # left hand pulling a large bell chain. These shapes are forward of the shrine.
    wrapped_limb_mesh(
        "PC_V16_left_upper_arm_sagging_from_shoulder",
        (-0.52, -2.225, 1.72),
        0.92,
        0.070,
        0.044,
        MAT["cloth"],
        rot=(math.radians(-4), math.radians(-13), math.radians(-21)),
        rings=22,
        sides=12,
        collection="PC_V16_hero_anatomy_weight",
    )
    wrapped_limb_mesh(
        "PC_V16_left_forearm_droop_to_bell_chain",
        (-0.72, -2.245, 1.08),
        0.76,
        0.052,
        0.034,
        MAT["cloth"],
        rot=(math.radians(-2), math.radians(-8), math.radians(-8)),
        rings=18,
        sides=10,
        collection="PC_V16_hero_anatomy_weight",
    )
    wrapped_limb_mesh(
        "PC_V16_right_arm_crushed_close_to_body",
        (0.54, -2.215, 1.52),
        0.98,
        0.060,
        0.038,
        MAT["cloth"],
        rot=(math.radians(2), math.radians(10), math.radians(10)),
        rings=20,
        sides=10,
        collection="PC_V16_hero_anatomy_weight",
    )

    for i, (x, z, w, rz) in enumerate([
        (-0.44, 2.06, 0.30, -22),
        (-0.36, 1.82, 0.25, 16),
        (0.38, 1.98, 0.26, 20),
        (0.30, 1.70, 0.22, -15),
    ]):
        box(
            f"PC_V16_shoulder_compression_wrap_{i:02d}",
            (x, -2.275, z),
            (w, 0.012, 0.022),
            MAT["wrap_highlight"] if i in [1, 3] else MAT["cloth"],
            rot=(0, 0, math.radians(rz)),
            collection="PC_V16_hero_anatomy_weight",
        )

    for i in range(4):
        sculpted_finger(
            f"PC_V16_left_visible_bell_grip_finger_{i:02d}",
            (-0.735 - i * 0.018, -2.278, 0.705 - i * 0.016),
            random.uniform(0.12, 0.18),
            random.uniform(0.008, 0.012),
            MAT["cloth"],
            rot=(math.radians(random.uniform(-3, 3)), math.radians(-8), math.radians(-(8 + i * 6))),
            collection="PC_V16_hero_anatomy_weight",
        )

    # More convincing hero chain: oval imperfect links descending to a larger bell
    # just outside the left leg, matching the big front illustration read.
    remove_objects_by_prefix(("PC_V11_7_left_hand_end_goal_bell_reasserted", "PC_V11_5_left_hand_sculpted_penitence_bell"))
    for i in range(8):
        sculpted_chain_link(
            f"PC_V16_left_hand_weighted_chain_link_{i:02d}",
            (-0.815 + math.sin(i * 0.8) * 0.018, -2.285, 0.94 - i * 0.082),
            random.uniform(0.018, 0.028),
            random.uniform(0.036, 0.050),
            MAT["metal"],
            rot=(math.radians(90 + random.uniform(-8, 8)), math.radians(random.uniform(-4, 5)), math.radians((90 if i % 2 else 0) + random.uniform(-12, 12))),
            collection="PC_V16_hero_anatomy_weight",
        )
    sculpted_bell("PC_V16_large_left_penitence_bell_final_silhouette", (-0.885, -2.300, 0.28), 0.92, collection="PC_V16_hero_anatomy_weight")

    # Slightly thicken and vary the legs without making them blocky.
    for side, sign in [("left", -1), ("right", 1)]:
        wrapped_limb_mesh(
            f"PC_V16_{side}_leg_wrapped_anatomy_overlay",
            (sign * 0.295, -2.070, 0.58),
            1.20 if side == "left" else 1.12,
            0.060 if side == "left" else 0.054,
            0.036,
            MAT["cloth"],
            rot=(math.radians(1), math.radians(sign * 5), math.radians(sign * random.uniform(1, 4))),
            rings=22,
            sides=10,
            collection="PC_V16_hero_anatomy_weight",
        )


def add_v17_proportion_restore() -> None:
    random.seed(3517)

    # V16 improved anatomy but pushed some silhouette anchors too far. Rebalance:
    # bell closer to the hand, legs less stretched, and hood/door proportion more
    # like the reference sheet.
    remove_objects_by_prefix((
        "PC_V16_left_hand_weighted_chain_link_",
        "PC_V16_large_left_penitence_bell_final_silhouette",
    ))

    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        lname = obj.name.lower()
        if "pc_v16_left_leg_wrapped_anatomy_overlay" in lname:
            obj.scale.z *= 0.78
            obj.location.z += 0.11
            obj.location.y += 0.025
        elif "pc_v16_right_leg_wrapped_anatomy_overlay" in lname:
            obj.scale.z *= 0.80
            obj.location.z += 0.10
            obj.location.y += 0.025
        elif "left_forearm_droop_to_bell_chain" in lname:
            obj.scale.z *= 0.82
            obj.location.z += 0.08
            obj.location.x += 0.035
        elif "left_upper_arm_sagging_from_shoulder" in lname:
            obj.scale.z *= 0.92
            obj.location.x += 0.025
        elif "right_arm_crushed_close_to_body" in lname:
            obj.scale.z *= 0.90
            obj.location.x -= 0.025

    # Strengthen the actual hood read without turning it into a clean ring.
    ragged_panel(
        "PC_V17_dark_hood_socket_backing",
        -2.292,
        2.33,
        2.88,
        0.16,
        0.29,
        MAT["void"],
        cols=4,
        rows=12,
        collection="PC_V17_proportion_restore",
    )
    ellipsoid(
        "PC_V17_black_opening_readable_from_distance",
        (-0.006, -2.325, 2.63),
        0.148,
        MAT["void"],
        scale=(0.40, 0.030, 1.12),
        collection="PC_V17_proportion_restore",
    )
    for i, (x, z, w, rz) in enumerate([(-0.095, 2.86, 0.18, -11), (0.070, 2.82, 0.20, 7), (-0.014, 2.38, 0.23, 4)]):
        box(
            f"PC_V17_wet_hood_lip_broken_{i:02d}",
            (x, -2.340, z),
            (w, 0.010, 0.022),
            MAT["cloth"],
            rot=(0, 0, math.radians(rz)),
            collection="PC_V17_proportion_restore",
        )
    for i, (x, z, h) in enumerate([(-0.172, 2.50, 0.40), (0.160, 2.45, 0.36)]):
        chipped_board_mesh(
            f"PC_V17_hood_side_torn_vertical_edge_{i:02d}",
            (x, -2.348, z),
            h,
            0.028,
            MAT["cloth"],
            rot=(0, 0, math.radians(-8 if i == 0 else 7)),
            rows=9,
            collection="PC_V17_proportion_restore",
        )

    # Re-place the left bell closer to the hand. It should be a hero silhouette,
    # but not disconnected from the body.
    for i in range(7):
        sculpted_chain_link(
            f"PC_V17_left_hand_chain_link_tighter_{i:02d}",
            (-0.760 + math.sin(i * 0.8) * 0.015, -2.300, 0.92 - i * 0.070),
            random.uniform(0.017, 0.026),
            random.uniform(0.034, 0.046),
            MAT["metal"],
            rot=(math.radians(90 + random.uniform(-8, 8)), math.radians(random.uniform(-3, 4)), math.radians((90 if i % 2 else 0) + random.uniform(-10, 10))),
            collection="PC_V17_proportion_restore",
        )
    sculpted_bell("PC_V17_left_hand_bell_closer_to_reference", (-0.810, -2.305, 0.36), 0.70, collection="PC_V17_proportion_restore")

    # Add a few torso compression folds tying shoulders to door-mask.
    for i, (x, z, h, rz) in enumerate([(-0.235, 1.78, 0.56, -7), (0.215, 1.72, 0.50, 6), (-0.120, 1.46, 0.44, 4), (0.105, 1.40, 0.40, -5)]):
        chipped_board_mesh(
            f"PC_V17_torso_torn_gravity_fold_{i:02d}",
            (x, -2.260, z),
            h,
            0.024,
            MAT["cloth"],
            rot=(0, 0, math.radians(rz)),
            rows=10,
            collection="PC_V17_proportion_restore",
        )


def add_v18_clay_authorship() -> None:
    random.seed(3618)

    # V18 is a clay-read pass against Penance_End_Goal.png. Remove the pieces
    # that were technically useful but read as clean bars or a black rectangle.
    remove_objects_by_prefix((
        "PC_V15_mask_lash_embedded_not_bar_",
        "PC_V17_dark_hood_socket_backing",
        "PC_V17_black_opening_readable_from_distance",
        "PC_V17_wet_hood_lip_broken_",
        "PC_V17_hood_side_torn_vertical_edge_",
    ))

    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        lname = obj.name.lower()
        if "pc_v15_rotten_wood_door_mask_broad_read" in lname:
            obj.scale.x *= 0.92
            obj.scale.z *= 1.03
            obj.location.z -= 0.015
            obj.location.y += 0.030
        elif "pc_v15_visible_rotted_face_plank_" in lname:
            obj.location.y += 0.032
            obj.scale.x *= random.uniform(0.86, 1.08)
            obj.rotation_euler.z += math.radians(random.uniform(-2.0, 2.0))
        elif "pc_v16_left_upper_arm_sagging_from_shoulder" in lname:
            obj.location.x -= 0.045
            obj.location.z -= 0.030
            obj.scale.x *= 1.08
        elif "pc_v16_right_arm_crushed_close_to_body" in lname:
            obj.location.x += 0.030
            obj.scale.x *= 0.92

    # Rebuild the hood as cloth over a narrow vertical void: ragged, not a ring.
    ellipsoid(
        "PC_V18_deep_narrow_head_void_not_panel",
        (-0.004, -2.372, 2.60),
        0.128,
        MAT["void"],
        scale=(0.34, 0.026, 1.22),
        collection="PC_V18_clay_authorship",
    )
    for i, (x, z0, z1, wb, wt) in enumerate([
        (-0.205, 2.20, 2.93, 0.040, 0.155),
        (0.184, 2.16, 2.86, 0.036, 0.132),
        (-0.070, 2.78, 2.99, 0.120, 0.220),
        (0.065, 2.72, 2.93, 0.105, 0.195),
    ]):
        ragged_panel(
            f"PC_V18_wet_hood_ragged_overhang_{i:02d}",
            -2.362 - i * 0.004,
            z0,
            z1,
            wb,
            wt,
            MAT["cloth"],
            x_center=x,
            cols=4 if i < 2 else 5,
            rows=14 if i < 2 else 8,
            collection="PC_V18_clay_authorship",
        )
    for i, (x, z, h, w, rz) in enumerate([
        (-0.155, 2.48, 0.48, 0.026, -8),
        (0.138, 2.42, 0.42, 0.022, 7),
        (-0.048, 2.28, 0.34, 0.018, 4),
        (0.062, 2.20, 0.30, 0.016, -5),
    ]):
        chipped_board_mesh(
            f"PC_V18_hood_edge_frayed_vertical_splinter_{i:02d}",
            (x, -2.388, z),
            h,
            w,
            MAT["cloth"] if i < 2 else MAT["wrap_highlight"],
            rot=(0, 0, math.radians(rz)),
            rows=9,
            collection="PC_V18_clay_authorship",
        )

    # Put authored, non-horizontal marks back onto the wooden face plank. These
    # are short cuts/nails/splinters, not graphic stripes.
    for i, (x, z, h, w, rz, mat_key) in enumerate([
        (-0.040, 2.04, 0.28, 0.012, -18, "metal"),
        (0.060, 1.78, 0.23, 0.010, 16, "cloth"),
        (-0.082, 1.44, 0.31, 0.010, 9, "metal"),
        (0.090, 1.16, 0.24, 0.009, -12, "wood"),
        (0.000, 0.91, 0.20, 0.009, 4, "void"),
    ]):
        chipped_board_mesh(
            f"PC_V18_mask_irregular_embedded_cut_{i:02d}",
            (x, -2.402, z),
            h,
            w,
            MAT[mat_key],
            rot=(0, 0, math.radians(rz)),
            rows=6,
            collection="PC_V18_clay_authorship",
        )
    for i, (x, z, sx, sz) in enumerate([
        (-0.143, 2.16, 0.012, 0.090),
        (0.127, 1.86, 0.010, 0.070),
        (-0.022, 1.20, 0.009, 0.105),
    ]):
        ellipsoid(
            f"PC_V18_door_crack_shadow_not_symmetrical_{i:02d}",
            (x, -2.410, z),
            0.085,
            MAT["void"],
            scale=(sx, 0.018, sz),
            collection="PC_V18_clay_authorship",
        )

    # Close the proxy gaps around the human core with sagging, asymmetrical cloth
    # forms that radiate from the hood/shoulder weight.
    for i, (x, z0, z1, wb, wt) in enumerate([
        (-0.355, 1.06, 2.02, 0.095, 0.175),
        (0.318, 0.98, 1.94, 0.080, 0.145),
        (-0.170, 0.82, 1.64, 0.060, 0.115),
        (0.138, 0.76, 1.54, 0.052, 0.100),
    ]):
        ragged_panel(
            f"PC_V18_body_gap_closing_weighted_cloth_{i:02d}",
            -2.318 - i * 0.006,
            z0,
            z1,
            wb,
            wt,
            MAT["cloth"] if i < 2 else MAT["wrap_highlight"],
            x_center=x,
            cols=4,
            rows=16,
            collection="PC_V18_clay_authorship",
        )
    for i, (x, z, w, rz) in enumerate([
        (-0.300, 1.93, 0.34, -24),
        (-0.260, 1.65, 0.26, 17),
        (0.288, 1.86, 0.30, 22),
        (0.214, 1.55, 0.23, -16),
        (-0.090, 1.28, 0.20, 11),
        (0.070, 1.12, 0.18, -9),
    ]):
        box(
            f"PC_V18_authored_cloth_tension_fold_{i:02d}",
            (x, -2.430, z),
            (w, 0.011, 0.018),
            MAT["wrap_highlight"] if i in [1, 4] else MAT["cloth"],
            rot=(0, 0, math.radians(rz)),
            collection="PC_V18_clay_authorship",
        )

    # Feet must read humanoid from the front: splayed toes and uneven weight.
    for side, sign in [("left", -1), ("right", 1)]:
        ellipsoid(
            f"PC_V18_{side}_flattened_wrapped_foot_mass",
            (sign * 0.318, -2.248, 0.095),
            0.110,
            MAT["cloth"],
            scale=(1.38, 0.46, 0.34),
            rot=(0, 0, math.radians(sign * 4)),
            collection="PC_V18_clay_authorship",
        )
        for toe in range(5):
            toe_x = sign * (0.240 + toe * 0.030)
            if side == "right":
                toe_x = sign * (0.245 + toe * 0.026)
            sculpted_finger(
                f"PC_V18_{side}_splayed_wrapped_toe_{toe:02d}",
                (toe_x, -2.330 - toe * 0.006, 0.068 + random.uniform(-0.008, 0.008)),
                random.uniform(0.115, 0.165),
                random.uniform(0.010, 0.015),
                MAT["cloth"],
                rot=(math.radians(88 + random.uniform(-4, 4)), math.radians(sign * (80 + toe * 2)), math.radians(sign * random.uniform(0, 10))),
                collection="PC_V18_clay_authorship",
            )

    # Deliberate shrine relic anchors, placed outside the face corridor so the
    # head stays obvious while the shrine still feels dense and heavy.
    for i, (x, z, s) in enumerate([(-0.55, 2.86, 0.74), (0.54, 2.62, 0.62), (-0.44, 3.24, 0.55)]):
        box(
            f"PC_V18_large_front_sound_relic_body_{i:02d}",
            (x, -2.365, z),
            (0.21 * s, 0.040, 0.145 * s),
            MAT["metal"],
            rot=(0, 0, math.radians(random.uniform(-5, 5))),
            collection="PC_V18_clay_authorship",
        )
        cyl(
            f"PC_V18_large_front_sound_relic_speaker_{i:02d}",
            (x - 0.036 * s, -2.394, z),
            0.035 * s,
            0.010,
            MAT["void"],
            vertices=18,
            rot=(math.radians(90), 0, 0),
            collection="PC_V18_clay_authorship",
        )
        cyl(
            f"PC_V18_large_front_sound_relic_brass_dial_{i:02d}",
            (x + 0.052 * s, -2.396, z + 0.032 * s),
            0.016 * s,
            0.010,
            MAT["brass"],
            vertices=14,
            rot=(math.radians(90), 0, 0),
            collection="PC_V18_clay_authorship",
        )
    for i, (x, z, scale) in enumerate([(-0.66, 2.34, 0.48), (0.62, 2.10, 0.40), (0.70, 3.10, 0.36)]):
        sculpted_bell(f"PC_V18_side_hanging_asymmetric_bell_{i:02d}", (x, -2.390, z), scale, collection="PC_V18_clay_authorship")

    # More disgusting back shape: hollow rot, sagging tongues, and uneven interior
    # depth without hiding the two-leg silhouette.
    for i, (x, z0, z1, wb, wt) in enumerate([
        (-0.42, 0.55, 2.70, 0.080, 0.190),
        (-0.18, 0.42, 2.58, 0.070, 0.150),
        (0.08, 0.60, 2.78, 0.064, 0.168),
        (0.34, 0.50, 2.48, 0.090, 0.155),
    ]):
        ragged_panel(
            f"PC_V18_back_rotten_hanging_tongue_{i:02d}",
            2.355 + i * 0.018,
            z0,
            z1,
            wb,
            wt,
            MAT["cloth"] if i != 1 else MAT["wood"],
            x_center=x,
            cols=4,
            rows=20,
            collection="PC_V18_back_disgust_shape",
        )
    for i, (x, z, sx, sz) in enumerate([(-0.26, 2.10, 0.030, 0.19), (0.22, 1.72, 0.026, 0.16), (0.02, 2.54, 0.020, 0.13)]):
        ellipsoid(
            f"PC_V18_back_rotten_hollow_shadow_{i:02d}",
            (x, 2.405, z),
            0.120,
            MAT["void"],
            scale=(sx, 0.020, sz),
            collection="PC_V18_back_disgust_shape",
        )


def add_v19_front_identity_lock() -> None:
    random.seed(3719)

    # The V18 front still read as a shrine slab first and a character second.
    # Clear the central face corridor, then place a dominant hood/door/head mass
    # in front of the shrine so the silhouette matches the target's priority.
    protected = ("mask", "hood", "door", "head", "shoulder", "arm", "leg", "foot", "toe", "body")
    clutter = ("chain", "bell", "ring", "clock", "speaker", "radio", "relic", "tassel", "cord", "fray", "strip", "rim")
    for obj in list(bpy.context.scene.objects):
        if obj.type != "MESH":
            continue
        lname = obj.name.lower()
        central_front = -0.34 <= obj.location.x <= 0.34 and obj.location.y < -0.70 and 0.92 <= obj.location.z <= 3.18
        if central_front and any(k in lname for k in clutter) and not any(k in lname for k in protected):
            bpy.data.objects.remove(obj, do_unlink=True)

    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        lname = obj.name.lower()
        # Push old graph-like front detail back so it becomes background texture.
        if obj.location.y < -0.72 and 0.85 <= obj.location.z <= 3.25 and -0.45 <= obj.location.x <= 0.45:
            if any(k in lname for k in ("front_chain", "front_hanging", "small_shadow_gap", "front_relic", "radio_clock")):
                obj.location.y += 0.22
                obj.scale.x *= 0.78
                obj.scale.z *= 0.86
        if "pc_v4_shrine_front_rotten_wall" in lname:
            obj.location.y += 0.10
            obj.scale.x *= 0.96
        elif "pc_v8_front_weathered_plank" in lname and -0.36 <= obj.location.x <= 0.36:
            obj.location.y += 0.18
            obj.scale.z *= 0.72

    # Large hood arch around the void. It is intentionally forward of all shrine
    # detail and broken up with ragged cloth chunks so it is readable in clay.
    hood = torus(
        "PC_V19_primary_hood_arch_clear_head_read",
        (0.0, -2.720, 2.55),
        0.315,
        0.054,
        MAT["cloth"],
        rot=(math.radians(90), 0, 0),
        collection="PC_V19_front_identity_lock",
    )
    hood.scale.x = 0.74
    hood.scale.z = 1.20
    ellipsoid(
        "PC_V19_primary_black_head_void_clear",
        (-0.004, -2.780, 2.56),
        0.155,
        MAT["void"],
        scale=(0.42, 0.030, 1.26),
        collection="PC_V19_front_identity_lock",
    )
    ellipsoid(
        "PC_V19_small_hanging_relic_inside_void",
        (0.000, -2.810, 2.47),
        0.027,
        MAT["brass"],
        scale=(0.62, 0.36, 1.45),
        collection="PC_V19_front_identity_lock",
    )
    for i, (x, z, sx, sz, rz) in enumerate([
        (-0.190, 2.68, 0.18, 0.34, -9),
        (0.172, 2.62, 0.16, 0.31, 7),
        (-0.070, 2.86, 0.20, 0.14, -14),
        (0.070, 2.82, 0.22, 0.13, 11),
    ]):
        ellipsoid(
            f"PC_V19_lumpy_wet_hood_cloth_mass_{i:02d}",
            (x, -2.765 - i * 0.010, z),
            0.145,
            MAT["cloth"],
            scale=(sx, 0.030, sz),
            rot=(0, 0, math.radians(rz)),
            collection="PC_V19_front_identity_lock",
        )
    for i, (x, z0, z1, wb, wt) in enumerate([
        (-0.265, 2.05, 2.78, 0.040, 0.120),
        (0.238, 1.98, 2.70, 0.034, 0.108),
        (-0.165, 1.72, 2.42, 0.030, 0.070),
        (0.156, 1.66, 2.34, 0.028, 0.066),
    ]):
        ragged_panel(
            f"PC_V19_hood_side_rag_integrated_to_door_{i:02d}",
            -2.790 - i * 0.006,
            z0,
            z1,
            wb,
            wt,
            MAT["cloth"] if i < 2 else MAT["wrap_highlight"],
            x_center=x,
            cols=4,
            rows=16,
            collection="PC_V19_front_identity_lock",
        )

    # The target has a wooden door-like face/mask. Make it wider, lower, and
    # visibly built from uneven planks instead of a thin center strip.
    ragged_panel(
        "PC_V19_broad_rotten_door_mask_target_read",
        -2.835,
        0.62,
        2.38,
        0.315,
        0.455,
        MAT["raw_wood"],
        cols=9,
        rows=34,
        collection="PC_V19_front_identity_lock",
    )
    for i, (x, h, z, w, rz) in enumerate([
        (-0.160, 1.55, 1.50, 0.036, -3),
        (-0.082, 1.70, 1.49, 0.030, 1),
        (-0.010, 1.66, 1.52, 0.038, -1),
        (0.072, 1.52, 1.55, 0.030, 3),
        (0.154, 1.34, 1.62, 0.026, -4),
    ]):
        chipped_board_mesh(
            f"PC_V19_door_mask_authored_plank_{i:02d}",
            (x, -2.865, z),
            h,
            w,
            MAT["raw_wood"] if i != 2 else MAT["wood"],
            rot=(0, 0, math.radians(rz)),
            rows=22,
            collection="PC_V19_front_identity_lock",
        )
    for i, (x, z, h, rz) in enumerate([
        (-0.060, 2.03, 0.30, -17),
        (0.062, 1.74, 0.23, 14),
        (-0.095, 1.36, 0.30, 8),
        (0.082, 1.07, 0.22, -12),
    ]):
        chipped_board_mesh(
            f"PC_V19_door_mask_broken_lash_not_bar_{i:02d}",
            (x, -2.895, z),
            h,
            0.011,
            MAT["metal"] if i in [0, 2] else MAT["cloth"],
            rot=(0, 0, math.radians(rz)),
            rows=6,
            collection="PC_V19_front_identity_lock",
        )

    # Forward shoulders and arms: heavier, more anatomical, and not hidden behind
    # hanging strips. The left side pulls to the bell like the reference.
    wrapped_limb_mesh(
        "PC_V19_left_hunched_shoulder_pressing_door",
        (-0.405, -2.705, 2.02),
        0.62,
        0.115,
        0.060,
        MAT["cloth"],
        rot=(math.radians(-2), math.radians(-12), math.radians(-66)),
        rings=18,
        sides=14,
        collection="PC_V19_front_identity_lock",
    )
    wrapped_limb_mesh(
        "PC_V19_right_hunched_shoulder_pressing_door",
        (0.365, -2.700, 1.94),
        0.55,
        0.102,
        0.052,
        MAT["cloth"],
        rot=(math.radians(1), math.radians(9), math.radians(58)),
        rings=16,
        sides=14,
        collection="PC_V19_front_identity_lock",
    )
    wrapped_limb_mesh(
        "PC_V19_left_hero_arm_heavy_reaching_bell",
        (-0.650, -2.760, 1.26),
        1.20,
        0.075,
        0.045,
        MAT["cloth"],
        rot=(math.radians(-3), math.radians(-10), math.radians(-15)),
        rings=26,
        sides=12,
        collection="PC_V19_front_identity_lock",
    )
    wrapped_limb_mesh(
        "PC_V19_right_arm_tucked_rotten_sleeve",
        (0.555, -2.735, 1.28),
        1.04,
        0.064,
        0.040,
        MAT["cloth"],
        rot=(math.radians(2), math.radians(12), math.radians(10)),
        rings=22,
        sides=12,
        collection="PC_V19_front_identity_lock",
    )
    for i, (x, z, w, rz) in enumerate([
        (-0.330, 1.92, 0.34, -24),
        (-0.282, 1.64, 0.26, 18),
        (0.315, 1.82, 0.30, 22),
        (0.238, 1.50, 0.23, -17),
    ]):
        box(
            f"PC_V19_shoulder_to_mask_compression_fold_{i:02d}",
            (x, -2.900, z),
            (w, 0.012, 0.020),
            MAT["wrap_highlight"] if i in [1, 3] else MAT["cloth"],
            rot=(0, 0, math.radians(rz)),
            collection="PC_V19_front_identity_lock",
        )

    # Reassert one readable left bell chain in front, close to the hand.
    for i in range(8):
        sculpted_chain_link(
            f"PC_V19_left_hand_readable_chain_link_{i:02d}",
            (-0.782 + math.sin(i * 0.75) * 0.016, -2.900, 0.98 - i * 0.078),
            random.uniform(0.018, 0.028),
            random.uniform(0.036, 0.052),
            MAT["metal"],
            rot=(math.radians(90 + random.uniform(-8, 8)), math.radians(random.uniform(-4, 4)), math.radians((90 if i % 2 else 0) + random.uniform(-12, 12))),
            collection="PC_V19_front_identity_lock",
        )
    sculpted_bell("PC_V19_left_hero_penitence_bell_closer_target", (-0.842, -2.910, 0.31), 0.78, collection="PC_V19_front_identity_lock")


def add_v20_ragged_hood_integration() -> None:
    random.seed(3820)

    # V19 solved head readability but the smooth oval hood looked too generated.
    # Replace the clean tube/ring with layered cloth chunks and crushed brow mass.
    remove_objects_by_prefix((
        "PC_V19_primary_hood_arch_clear_head_read",
        "PC_V19_primary_black_head_void_clear",
        "PC_V19_lumpy_wet_hood_cloth_mass_",
        "PC_V19_small_hanging_relic_inside_void",
    ))

    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        lname = obj.name.lower()
        if "pc_v19_broad_rotten_door_mask_target_read" in lname:
            obj.location.z += 0.040
            obj.location.y -= 0.020
            obj.scale.x *= 0.96
        elif "pc_v19_door_mask_authored_plank_" in lname:
            obj.location.z += random.uniform(0.020, 0.055)
            obj.location.y -= 0.020
            obj.rotation_euler.z += math.radians(random.uniform(-1.5, 1.5))
        elif "pc_v19_hood_side_rag_integrated_to_door_" in lname:
            obj.location.y -= 0.018
            obj.scale.x *= random.uniform(0.92, 1.08)

    # Deep void remains, but its edge is ragged and partially occluded.
    ellipsoid(
        "PC_V20_deep_vertical_head_void_ragged_edge",
        (-0.006, -2.925, 2.54),
        0.145,
        MAT["void"],
        scale=(0.34, 0.024, 1.18),
        collection="PC_V20_ragged_hood_integration",
    )
    for i, (x, z, sx, sz, rz) in enumerate([
        (-0.155, 2.69, 0.34, 0.135, -13),
        (0.120, 2.66, 0.32, 0.125, 9),
        (-0.035, 2.78, 0.42, 0.110, 3),
        (-0.205, 2.48, 0.135, 0.420, -8),
        (0.190, 2.42, 0.120, 0.390, 7),
        (-0.118, 2.24, 0.085, 0.260, 5),
        (0.095, 2.18, 0.075, 0.230, -6),
    ]):
        ellipsoid(
            f"PC_V20_crushed_layered_hood_mass_{i:02d}",
            (x, -2.948 - i * 0.004, z),
            0.160,
            MAT["cloth"] if i not in [2, 6] else MAT["wrap_highlight"],
            scale=(sx, 0.030, sz),
            rot=(0, 0, math.radians(rz)),
            collection="PC_V20_ragged_hood_integration",
        )
    for i, (x, z0, z1, wb, wt) in enumerate([
        (-0.232, 2.05, 2.74, 0.030, 0.085),
        (0.210, 1.98, 2.65, 0.027, 0.076),
        (-0.060, 2.17, 2.82, 0.024, 0.060),
        (0.050, 2.05, 2.70, 0.022, 0.055),
    ]):
        ragged_panel(
            f"PC_V20_hood_frayed_overlap_over_void_{i:02d}",
            -2.970 - i * 0.004,
            z0,
            z1,
            wb,
            wt,
            MAT["cloth"],
            x_center=x,
            cols=3,
            rows=14,
            collection="PC_V20_ragged_hood_integration",
        )
    for i, (x, z, h, w, rz) in enumerate([
        (-0.125, 2.78, 0.22, 0.024, -18),
        (0.055, 2.73, 0.24, 0.020, 15),
        (-0.205, 2.43, 0.34, 0.018, -8),
        (0.182, 2.36, 0.30, 0.016, 7),
    ]):
        chipped_board_mesh(
            f"PC_V20_hood_cracked_edge_sculpt_mark_{i:02d}",
            (x, -2.992, z),
            h,
            w,
            MAT["cloth"] if i < 2 else MAT["wrap_highlight"],
            rot=(0, 0, math.radians(rz)),
            rows=7,
            collection="PC_V20_ragged_hood_integration",
        )

    # Add asymmetric face-door details that follow the target's X/stitch language
    # without becoming clean graphic bars.
    for i, (x, z, h, rz, mat_key) in enumerate([
        (-0.050, 1.93, 0.31, -22, "metal"),
        (0.070, 1.72, 0.28, 19, "cloth"),
        (-0.060, 1.44, 0.30, 16, "metal"),
        (0.055, 1.22, 0.25, -18, "wood"),
        (-0.030, 0.98, 0.22, -9, "void"),
    ]):
        chipped_board_mesh(
            f"PC_V20_door_authored_penitent_mark_{i:02d}",
            (x, -3.010, z),
            h,
            0.010,
            MAT[mat_key],
            rot=(0, 0, math.radians(rz)),
            rows=6,
            collection="PC_V20_ragged_hood_integration",
        )
    for i, (x, z, w, rz) in enumerate([
        (-0.365, 1.98, 0.40, -26),
        (-0.318, 1.71, 0.30, 19),
        (0.335, 1.90, 0.35, 24),
        (0.260, 1.58, 0.27, -18),
        (-0.150, 2.18, 0.22, -8),
        (0.128, 2.10, 0.20, 7),
    ]):
        box(
            f"PC_V20_loaded_cloth_fold_into_mask_{i:02d}",
            (x, -3.020, z),
            (w, 0.010, 0.017),
            MAT["wrap_highlight"] if i in [1, 3, 5] else MAT["cloth"],
            rot=(0, 0, math.radians(rz)),
            collection="PC_V20_ragged_hood_integration",
        )

    # Toe/foot correction in the front silhouette. The previous feet were too
    # disk-like; this adds explicit toe groups under the wrap mass.
    for side, sign in [("left", -1), ("right", 1)]:
        for toe in range(5):
            sculpted_finger(
                f"PC_V20_{side}_visible_uneven_front_toe_{toe:02d}",
                (sign * (0.242 + toe * 0.030), -2.975 - toe * 0.004, 0.072),
                random.uniform(0.105, 0.155),
                random.uniform(0.009, 0.013),
                MAT["wrap_highlight"] if toe in [0, 4] else MAT["cloth"],
                rot=(math.radians(88 + random.uniform(-3, 3)), math.radians(sign * (82 + toe * 2)), math.radians(sign * random.uniform(0, 8))),
                collection="PC_V20_ragged_hood_integration",
            )


def add_v21_multi_region_reference_baseline() -> None:
    random.seed(3921)

    # V21 responds to the organized End_Goal folder: front orthographic owns the
    # silhouette, side sheets own depth, back sheet owns the rotten rear mass,
    # and the detail panels own face, foot, shrine, and chain language.
    remove_objects_by_prefix((
        "PC_V19_left_hand_readable_chain_link_",
        "PC_V19_left_hero_penitence_bell_closer_target",
    ))

    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        lname = obj.name.lower()
        if "pc_v4_shrine_front_rotten_wall" in lname:
            obj.scale.x *= 0.92
            obj.location.y += 0.10
        elif "pc_v4_shrine_left_side_wall" in lname or "pc_v4_shrine_right_side_wall" in lname:
            obj.scale.y *= 1.12
        elif "pc_v4_roof_left_steep_slab" in lname:
            obj.rotation_euler.y += math.radians(-2.0)
            obj.location.z += 0.035
        elif "pc_v4_roof_right_steep_slab" in lname:
            obj.rotation_euler.y += math.radians(2.0)
            obj.location.z += 0.035
        elif "pc_v16_left_leg_wrapped_anatomy_overlay" in lname:
            obj.location.x -= 0.030
            obj.scale.x *= 1.06
        elif "pc_v16_right_leg_wrapped_anatomy_overlay" in lname:
            obj.location.x += 0.030
            obj.scale.x *= 1.06

    # Front door-mask based on the new front orthographic crop: long, broad,
    # plank-built, with clear black head opening and symbol language.
    ragged_panel(
        "PC_V21_front_ortho_long_door_mask_primary",
        -3.090,
        0.52,
        2.48,
        0.34,
        0.48,
        MAT["raw_wood"],
        cols=10,
        rows=40,
        collection="PC_V21_multi_region_reference_baseline",
    )
    for i, (x, h, z, w, rz) in enumerate([
        (-0.172, 1.76, 1.44, 0.034, -3),
        (-0.088, 1.92, 1.42, 0.030, 2),
        (-0.006, 1.98, 1.44, 0.038, -1),
        (0.082, 1.82, 1.47, 0.032, 3),
        (0.166, 1.58, 1.55, 0.026, -4),
    ]):
        chipped_board_mesh(
            f"PC_V21_front_mask_plank_authoring_{i:02d}",
            (x, -3.125, z),
            h,
            w,
            MAT["raw_wood"] if i != 2 else MAT["wood"],
            rot=(0, 0, math.radians(rz)),
            rows=24,
            collection="PC_V21_multi_region_reference_baseline",
        )
    ellipsoid(
        "PC_V21_black_void_locked_from_face_detail_crop",
        (-0.004, -3.155, 2.43),
        0.145,
        MAT["void"],
        scale=(0.40, 0.024, 1.10),
        collection="PC_V21_multi_region_reference_baseline",
    )
    ellipsoid(
        "PC_V21_inner_hanging_bulb_relic_in_void",
        (0.000, -3.185, 2.48),
        0.030,
        MAT["brass"],
        scale=(0.62, 0.32, 1.60),
        collection="PC_V21_multi_region_reference_baseline",
    )
    for i, (x, z, h, rz, mat_key) in enumerate([
        (-0.052, 1.88, 0.34, -24, "metal"),
        (0.062, 1.66, 0.29, 22, "metal"),
        (-0.054, 1.36, 0.31, 18, "cloth"),
        (0.060, 1.12, 0.27, -20, "cloth"),
        (0.000, 0.88, 0.24, 0, "void"),
    ]):
        chipped_board_mesh(
            f"PC_V21_mask_symbol_lashed_cut_{i:02d}",
            (x, -3.190, z),
            h,
            0.010,
            MAT[mat_key],
            rot=(0, 0, math.radians(rz)),
            rows=6,
            collection="PC_V21_multi_region_reference_baseline",
        )

    # The face crop shows a layered hood made of strapped arcs. Use broken
    # overlapping cloth volumes instead of a single tube.
    for i, (x, z, sx, sz, rz, mat_key) in enumerate([
        (-0.165, 2.64, 0.36, 0.12, -14, "cloth"),
        (0.150, 2.61, 0.34, 0.11, 10, "cloth"),
        (-0.030, 2.76, 0.44, 0.10, 2, "wrap_highlight"),
        (-0.232, 2.40, 0.13, 0.42, -8, "cloth"),
        (0.220, 2.34, 0.12, 0.38, 7, "cloth"),
    ]):
        ellipsoid(
            f"PC_V21_face_crop_layered_hood_piece_{i:02d}",
            (x, -3.175 - i * 0.005, z),
            0.160,
            MAT[mat_key],
            scale=(sx, 0.027, sz),
            rot=(0, 0, math.radians(rz)),
            collection="PC_V21_multi_region_reference_baseline",
        )
    for i, (x, z0, z1, wb, wt) in enumerate([
        (-0.250, 1.92, 2.62, 0.034, 0.094),
        (0.235, 1.84, 2.55, 0.030, 0.085),
        (-0.085, 2.10, 2.78, 0.022, 0.060),
        (0.075, 2.02, 2.68, 0.020, 0.055),
    ]):
        ragged_panel(
            f"PC_V21_face_crop_frayed_hood_drop_{i:02d}",
            -3.205 - i * 0.004,
            z0,
            z1,
            wb,
            wt,
            MAT["cloth"],
            x_center=x,
            cols=3,
            rows=14,
            collection="PC_V21_multi_region_reference_baseline",
        )

    # Side sheets show the carrier leaning forward under load. Add side-depth
    # shoulder/back transitions that make the body less flat in profile.
    wrapped_limb_mesh(
        "PC_V21_left_side_shoulder_back_transition_mass",
        (-0.455, -2.880, 2.08),
        0.72,
        0.126,
        0.072,
        MAT["cloth"],
        rot=(math.radians(-4), math.radians(-18), math.radians(-64)),
        rings=20,
        sides=14,
        collection="PC_V21_multi_region_reference_baseline",
    )
    wrapped_limb_mesh(
        "PC_V21_right_side_shoulder_back_transition_mass",
        (0.430, -2.865, 2.00),
        0.66,
        0.116,
        0.066,
        MAT["cloth"],
        rot=(math.radians(3), math.radians(16), math.radians(58)),
        rings=18,
        sides=14,
        collection="PC_V21_multi_region_reference_baseline",
    )
    for i, (x, z, w, rz) in enumerate([
        (-0.375, 1.95, 0.42, -27),
        (-0.320, 1.69, 0.31, 20),
        (0.355, 1.88, 0.37, 25),
        (0.280, 1.58, 0.29, -19),
        (-0.170, 2.18, 0.25, -9),
        (0.145, 2.08, 0.23, 8),
    ]):
        box(
            f"PC_V21_shoulder_harness_loaded_fold_{i:02d}",
            (x, -3.225, z),
            (w, 0.011, 0.018),
            MAT["wrap_highlight"] if i in [1, 3, 5] else MAT["cloth"],
            rot=(0, 0, math.radians(rz)),
            collection="PC_V21_multi_region_reference_baseline",
        )

    # Use the new foot/detail crops to make toes readable instead of disk feet.
    for side, sign in [("left", -1), ("right", 1)]:
        ellipsoid(
            f"PC_V21_{side}_front_foot_weight_mass",
            (sign * 0.330, -2.980, 0.090),
            0.115,
            MAT["cloth"],
            scale=(1.56, 0.48, 0.36),
            rot=(0, 0, math.radians(sign * 3)),
            collection="PC_V21_multi_region_reference_baseline",
        )
        for toe in range(5):
            sculpted_finger(
                f"PC_V21_{side}_orthographic_toe_read_{toe:02d}",
                (sign * (0.242 + toe * 0.032), -3.075 - toe * 0.006, 0.068 + random.uniform(-0.006, 0.006)),
                random.uniform(0.112, 0.170),
                random.uniform(0.010, 0.014),
                MAT["wrap_highlight"] if toe in [0, 4] else MAT["cloth"],
                rot=(math.radians(88 + random.uniform(-3, 3)), math.radians(sign * (82 + toe * 2)), math.radians(sign * random.uniform(0, 8))),
                collection="PC_V21_multi_region_reference_baseline",
            )

    # Chains/bells are organized as hero elements now: one large left bell, plus
    # side curtain chains with varied lengths. Keep them out of the face corridor.
    for i in range(9):
        sculpted_chain_link(
            f"PC_V21_left_hero_bell_chain_link_{i:02d}",
            (-0.790 + math.sin(i * 0.75) * 0.018, -3.135, 0.98 - i * 0.082),
            random.uniform(0.019, 0.030),
            random.uniform(0.038, 0.055),
            MAT["metal"],
            rot=(math.radians(90 + random.uniform(-8, 8)), math.radians(random.uniform(-4, 4)), math.radians((90 if i % 2 else 0) + random.uniform(-12, 12))),
            collection="PC_V21_multi_region_reference_baseline",
        )
    sculpted_bell("PC_V21_left_hero_penitence_bell_from_front_crop", (-0.848, -3.150, 0.27), 0.86, collection="PC_V21_multi_region_reference_baseline")

    for i, (x, z, count, scale) in enumerate([
        (-0.88, 3.24, 9, 0.72),
        (-0.66, 3.38, 11, 0.62),
        (0.66, 3.32, 10, 0.64),
        (0.88, 3.18, 8, 0.70),
    ]):
        for link in range(count):
            sculpted_chain_link(
                f"PC_V21_side_curtain_chain_{i:02d}_{link:02d}",
                (x + math.sin(link * 0.65 + i) * 0.020, -2.960, z - link * 0.110),
                0.014 * scale,
                0.034 * scale,
                MAT["metal"],
                rot=(math.radians(90), 0, math.radians(90 if link % 2 else 0)),
                collection="PC_V21_multi_region_reference_baseline",
            )
        if i in [0, 3]:
            sculpted_bell(f"PC_V21_side_reference_hanging_bell_{i:02d}", (x, -2.975, z - count * 0.110 - 0.08), 0.48, collection="PC_V21_multi_region_reference_baseline")

    # Back structure: add rear drapery tongues and rot hollows based on the new
    # back/lower-back detail sheets, preserving leg separation.
    for i, (x, z0, z1, wb, wt, mat_key) in enumerate([
        (-0.46, 0.56, 2.76, 0.070, 0.180, "cloth"),
        (-0.22, 0.42, 2.60, 0.064, 0.150, "wood"),
        (0.02, 0.50, 2.82, 0.058, 0.166, "cloth"),
        (0.28, 0.46, 2.52, 0.078, 0.140, "cloth"),
        (0.50, 0.72, 2.38, 0.052, 0.100, "wood"),
    ]):
        ragged_panel(
            f"PC_V21_back_drapery_reference_tongue_{i:02d}",
            2.525 + i * 0.014,
            z0,
            z1,
            wb,
            wt,
            MAT[mat_key],
            x_center=x,
            cols=4,
            rows=22,
            collection="PC_V21_back_reference_shape",
        )
    for i, (x, z, sx, sz) in enumerate([(-0.24, 2.12, 0.028, 0.18), (0.19, 1.74, 0.025, 0.16), (0.02, 2.56, 0.020, 0.13)]):
        ellipsoid(
            f"PC_V21_back_rot_hollow_from_rear_sheet_{i:02d}",
            (x, 2.575, z),
            0.120,
            MAT["void"],
            scale=(sx, 0.020, sz),
            collection="PC_V21_back_reference_shape",
        )


def clean_topology_and_shading() -> None:
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH" or obj.name.startswith("PC_V4_REF_") or obj.name.startswith("PC_V4_BLOCKOUT_SCALE_"):
            continue
        mesh = obj.data
        mesh.validate(clean_customdata=True)
        mesh.update()
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        try:
            bpy.ops.object.shade_smooth()
        except Exception:
            pass
        obj.select_set(False)

        if not any(mod.type == "WEIGHTED_NORMAL" for mod in obj.modifiers):
            mod = obj.modifiers.new("PC_V11_weighted_normals_export_safe", "WEIGHTED_NORMAL")
            mod.keep_sharp = True
            mod.weight = 50
        if not any(mod.type == "TRIANGULATE" for mod in obj.modifiers):
            tri = obj.modifiers.new("PC_V11_controlled_triangulation", "TRIANGULATE")
            tri.quad_method = "BEAUTY"
            tri.ngon_method = "BEAUTY"


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
    print("Penance Carrier V21 multi-region reference baseline pass starting...", flush=True)
    random.seed(2111)
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
    add_v11_primary_form_correction()
    add_v11_organic_end_goal_rebuild()
    add_v11_surface_sculpt_prep()
    add_v11_identity_detail_correction()
    add_v11_5_clay_quality_sculpt_pass()
    add_v11_6_end_goal_clay_refinement()
    add_v11_7_end_goal_readability_correction()
    add_v11_8_head_mask_reference_lock()
    add_v11_9_ragged_hood_door_silhouette()
    add_v12_head_readability_checkpoint()
    add_v13_hood_door_integration()
    add_v14_human_silhouette_lock()
    add_v15_mask_material_balance()
    add_v16_hero_anatomy_weight()
    add_v17_proportion_restore()
    add_v18_clay_authorship()
    add_v19_front_identity_lock()
    add_v20_ragged_hood_integration()
    add_v21_multi_region_reference_baseline()
    clean_topology_and_shading()
    add_lighting_and_cameras()
    set_origin_and_units()
    export_outputs()
    print("Saved blend:", OUTPUT_BLEND, flush=True)
    print("Exported GLB:", OUTPUT_GLB, flush=True)


if __name__ == "__main__":
    main()
