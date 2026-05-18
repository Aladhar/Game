"""
Penance Carrier V4 silhouette-lock pass.

This is the first careful production pass after reference extraction. It uses:
- Penance_End_Goal.png-derived front/side/back reference crops
- penance_carrier_blockout_v1.glb as the only imported base model

Outputs:
  assets/models/enemies/penance_carrier/blender_work/penance_carrier_end_goal_v4_silhouette.blend
  assets/models/enemies/penance_carrier/penance_carrier_end_goal_v4_silhouette.glb
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
REF_ROOT = ASSET_ROOT / "reference_crops"
INPUT_GLB = ASSET_ROOT / "penance_carrier_blockout_v1.glb"
WORK_DIR = ASSET_ROOT / "blender_work"
OUTPUT_BLEND = WORK_DIR / "penance_carrier_end_goal_v4_silhouette.blend"
OUTPUT_GLB = ASSET_ROOT / "penance_carrier_end_goal_v4_silhouette.glb"

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
    MAT["cloth"] = make_mat("PC_V4_soaked_wrapped_cloth", (0.075, 0.073, 0.066, 1), 0.92)
    MAT["wood"] = make_mat("PC_V4_rotten_weathered_wood", (0.18, 0.135, 0.09, 1), 0.9)
    MAT["raw_wood"] = make_mat("PC_V4_pale_broken_splinter", (0.47, 0.40, 0.29, 1), 0.86)
    MAT["metal"] = make_mat("PC_V4_rusted_iron", (0.13, 0.105, 0.085, 1), 0.82, 0.8)
    MAT["brass"] = make_mat("PC_V4_corroded_brass", (0.42, 0.285, 0.12, 1), 0.7, 1.0)
    MAT["void"] = make_mat("PC_V4_black_mask_void", (0.0, 0.0, 0.0, 1), 1.0)
    MAT["paper"] = make_mat("PC_V4_old_paper", (0.50, 0.43, 0.31, 1), 0.9)
    MAT["wax"] = make_mat("PC_V4_dirty_wax", (0.62, 0.50, 0.33, 1), 0.75)
    MAT["guide"] = make_mat("PC_V4_silhouette_measure_guides", (0.0, 0.75, 1.0, 0.38), 1.0)


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
    torus("PC_V4_head_hood_oval_ring", (0, -0.98, 2.82), 0.34, 0.045, MAT["cloth"], rot=(math.radians(90), 0, 0))
    sphere("PC_V4_head_black_void", (0, -1.04, 2.84), 0.25, MAT["void"], scale=(0.78, 0.08, 1.18))
    box("PC_V4_long_door_mask_front", (0, -1.13, 2.05), (0.40, 0.08, 1.48), MAT["wood"])
    box("PC_V4_door_mask_center_split", (0, -1.18, 2.05), (0.035, 0.02, 1.36), MAT["raw_wood"])

    # Bent arms and legs positioned from the orthographic front/side proportions.
    for side, sign in [("left", -1), ("right", 1)]:
        box(f"PC_V4_{side}_long_upper_arm_wrapped", (sign * 0.61, -0.54, 1.82), (0.16, 0.12, 0.62), MAT["cloth"], rot=(0, 0, math.radians(sign * -15)))
        box(f"PC_V4_{side}_long_forearm_wrapped", (sign * 0.68, -0.58, 1.36), (0.15, 0.11, 0.58), MAT["cloth"], rot=(0, 0, math.radians(sign * 9)))
        sphere(f"PC_V4_{side}_large_hanging_hand", (sign * 0.72, -0.62, 1.02), 0.11, MAT["cloth"], scale=(0.75, 0.48, 1.24))
        box(f"PC_V4_{side}_wrapped_thigh", (sign * 0.23, -0.10, 1.12), (0.20, 0.18, 0.80), MAT["cloth"], rot=(0, 0, math.radians(sign * 4)))
        box(f"PC_V4_{side}_wrapped_shin", (sign * 0.28, -0.08, 0.48), (0.17, 0.15, 0.75), MAT["cloth"], rot=(0, 0, math.radians(sign * -4)))
        sphere(f"PC_V4_{side}_splayed_bare_foot_block", (sign * 0.32, -0.27, 0.08), 0.14, MAT["cloth"], scale=(1.55, 0.72, 0.42))

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
    print("Penance Carrier V4 silhouette-lock pass starting...", flush=True)
    clear_scene()
    create_materials()
    add_reference_planes()
    import_blockout_for_scale()
    add_v4_primary_silhouette()
    add_v4_relic_density_guides()
    add_lighting_and_cameras()
    set_origin_and_units()
    export_outputs()
    print("Saved blend:", OUTPUT_BLEND, flush=True)
    print("Exported GLB:", OUTPUT_GLB, flush=True)


if __name__ == "__main__":
    main()
