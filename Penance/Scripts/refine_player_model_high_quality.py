from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_BLEND = PROJECT_ROOT / "Built" / "BlenderWork" / "PlayerAnim_Working_Copy_For_You_To_Work_On.blend"
IDLE_BLEND = PROJECT_ROOT / "Built" / "BlenderWork" / "Idle.blend"
OUTPUT_BLEND = PROJECT_ROOT / "Built" / "BlenderWork" / "PlayerModel_Refined_HighQuality_Working.blend"
OUTPUT_FBX = PROJECT_ROOT / "Built" / "FBX" / "SK_Player_FirstPersonBody_Refined.fbx"
REPORT_PATH = PROJECT_ROOT / "Saved" / "PlayerModelRefinedHighQualityReport.txt"

ARMATURE_NAME = "SK_Player_Armature"
MESH_NAME = "PlayerRoughDraft_Mesh"

FINGER_CHAINS = ["thumb", "index", "middle", "ring", "pinky"]
PHALANGES = ["01", "02", "03"]
GENERATED_OBJECT_PREFIXES = (
    "Player_Refined_",
)
GENERATED_ACTIONS = {
    "AN_Player_FingerBend_SelfTest",
}


def args_after_separator() -> list[str]:
    if "--" not in sys.argv:
        return []
    return sys.argv[sys.argv.index("--") + 1 :]


def parse_args() -> tuple[Path, Path, Path | None, Path]:
    args = args_after_separator()
    source = SOURCE_BLEND
    output = OUTPUT_BLEND
    fbx: Path | None = None
    report = REPORT_PATH

    i = 0
    while i < len(args):
        key = args[i]
        if key == "--source":
            source = Path(args[i + 1]).expanduser().resolve()
            i += 2
        elif key == "--output":
            output = Path(args[i + 1]).expanduser().resolve()
            i += 2
        elif key == "--fbx":
            fbx = Path(args[i + 1]).expanduser().resolve()
            i += 2
        elif key == "--report":
            report = Path(args[i + 1]).expanduser().resolve()
            i += 2
        else:
            raise RuntimeError(f"Unknown argument: {key}")

    return source, output, fbx, report


def ensure_material(name: str, color: tuple[float, float, float, float], roughness: float = 0.8) -> bpy.types.Material:
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        try:
            bsdf.inputs["Base Color"].default_value = color
            bsdf.inputs["Roughness"].default_value = roughness
        except Exception:
            pass
    mat.diffuse_color = color
    return mat


def collection(name: str) -> bpy.types.Collection:
    col = bpy.data.collections.get(name)
    if not col:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


def move_object_to_collection(obj: bpy.types.Object, col: bpy.types.Collection) -> None:
    for existing in list(obj.users_collection):
        existing.objects.unlink(obj)
    col.objects.link(obj)


def duplicate_backups(arm: bpy.types.Object, mesh: bpy.types.Object) -> None:
    backup_col = collection("BACKUP_ORIGINAL_PLAYER_MODEL_DO_NOT_EXPORT")
    backup_col.hide_viewport = True
    backup_col.hide_render = True

    if not bpy.data.objects.get("BACKUP_ORIGINAL_SK_Player_Armature"):
        arm_backup = arm.copy()
        arm_backup.data = arm.data.copy()
        arm_backup.name = "BACKUP_ORIGINAL_SK_Player_Armature"
        arm_backup.data.name = "BACKUP_ORIGINAL_SK_Player_Armature_Data"
        backup_col.objects.link(arm_backup)
        arm_backup.hide_viewport = True
        arm_backup.hide_render = True

    if not bpy.data.objects.get("BACKUP_ORIGINAL_PlayerRoughDraft_Mesh"):
        mesh_backup = mesh.copy()
        mesh_backup.data = mesh.data.copy()
        mesh_backup.name = "BACKUP_ORIGINAL_PlayerRoughDraft_Mesh"
        mesh_backup.data.name = "BACKUP_ORIGINAL_PlayerRoughDraft_Mesh_Data"
        backup_col.objects.link(mesh_backup)
        mesh_backup.hide_viewport = True
        mesh_backup.hide_render = True


def append_idle_reference(report: list[str]) -> None:
    existing_ref = bpy.data.objects.get("REFERENCE_Armature_FingerBones")
    if existing_ref:
        report.append(f"Idle reference append: reused {existing_ref.name}")
        return

    if not IDLE_BLEND.exists():
        report.append(f"Idle reference append: missing {IDLE_BLEND}")
        return

    ref_col = collection("REFERENCE_IDLE_FINGER_ARMATURE_HIDDEN")
    ref_col.hide_viewport = True
    ref_col.hide_render = True
    with bpy.data.libraries.load(str(IDLE_BLEND), link=False) as (data_from, data_to):
        armature_objects = [name for name in data_from.objects if "armature" in name.lower()]
        data_to.objects = armature_objects[:1]

    appended = [obj for obj in data_to.objects if obj]
    for obj in appended:
        obj.name = f"REFERENCE_{obj.name}_FingerBones"
        move_object_to_collection(obj, ref_col)
        obj.hide_viewport = True
        obj.hide_render = True

    if appended and appended[0].type == "ARMATURE":
        finger_bones = [bone.name for bone in appended[0].data.bones if "hand" in bone.name.lower() and any(name in bone.name.lower() for name in FINGER_CHAINS)]
        report.append(f"Idle reference append: appended {appended[0].name} with {len(finger_bones)} finger bones")
    else:
        report.append("Idle reference append: no armature object appended")


def remove_prior_generated_assets(report: list[str]) -> None:
    removed_objects = 0
    for obj in list(bpy.data.objects):
        if any(obj.name.startswith(prefix) for prefix in GENERATED_OBJECT_PREFIXES):
            data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if data and data.users == 0:
                if isinstance(data, bpy.types.Mesh):
                    bpy.data.meshes.remove(data)
            removed_objects += 1

    removed_actions = 0
    for action_name in GENERATED_ACTIONS:
        action = bpy.data.actions.get(action_name)
        if action:
            bpy.data.actions.remove(action)
            removed_actions += 1

    if removed_objects or removed_actions:
        report.append(f"Removed prior generated refinement assets: objects={removed_objects} actions={removed_actions}")


def basis_from_axis(axis: Vector) -> tuple[Vector, Vector, Vector]:
    forward = axis.normalized()
    up_hint = Vector((0.0, 0.0, 1.0))
    if abs(forward.dot(up_hint)) > 0.92:
        up_hint = Vector((0.0, 1.0, 0.0))
    right = forward.cross(up_hint).normalized()
    up = right.cross(forward).normalized()
    return forward, right, up


def add_finger_bones(arm: bpy.types.Object, report: list[str]) -> list[str]:
    added: list[str] = []
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")

    for suffix, side_sign in (("l", -1.0), ("r", 1.0)):
        hand = arm.data.edit_bones.get(f"hand_{suffix}")
        if not hand:
            report.append(f"Finger bones {suffix}: missing hand_{suffix}")
            continue

        palm_axis = (hand.tail - hand.head).normalized()
        side_axis = Vector((side_sign, 0.0, 0.0))
        spread_axis = Vector((side_sign, 0.0, 0.12)).normalized()
        base_center = hand.tail - palm_axis * 0.006
        finger_offsets = {
            "thumb": (-0.034, -0.008, -0.006),
            "index": (-0.015, -0.001, 0.003),
            "middle": (0.000, 0.000, 0.006),
            "ring": (0.015, -0.001, 0.003),
            "pinky": (0.030, -0.004, -0.003),
        }
        lengths = {
            "thumb": (0.017, 0.015, 0.012),
            "index": (0.018, 0.017, 0.014),
            "middle": (0.020, 0.018, 0.015),
            "ring": (0.018, 0.016, 0.013),
            "pinky": (0.015, 0.013, 0.011),
        }

        previous_by_name: dict[str, bpy.types.EditBone] = {}
        for finger in FINGER_CHAINS:
            if finger == "thumb":
                direction = (palm_axis * 0.62 + side_axis * 0.58 + Vector((0.0, -0.08, 0.0))).normalized()
            else:
                spread = finger_offsets[finger][0]
                direction = (palm_axis + spread_axis * spread * 1.8 + Vector((0.0, -0.04, 0.0))).normalized()

            base = base_center + side_axis * finger_offsets[finger][0] + Vector((0.0, finger_offsets[finger][1], finger_offsets[finger][2]))
            start = base
            parent = hand
            for idx, phalanx in enumerate(PHALANGES):
                bone_name = f"{finger}_{phalanx}_{suffix}"
                bone = arm.data.edit_bones.get(bone_name)
                if not bone:
                    bone = arm.data.edit_bones.new(bone_name)
                    added.append(bone_name)
                length = lengths[finger][idx]
                bone.head = start
                bone.tail = start + direction * length
                bone.parent = parent
                bone.use_connect = idx > 0
                bone.use_deform = True
                bone.roll = hand.roll
                start = bone.tail
                parent = bone
                previous_by_name[bone_name] = bone

    bpy.ops.object.mode_set(mode="OBJECT")
    report.append(f"Finger bones added/verified: {len(added)} new bones")
    return added


def create_cylinder_segment(
    verts: list[tuple[float, float, float]],
    faces: list[tuple[int, ...]],
    assignments: list[str],
    start: Vector,
    end: Vector,
    radius_start: float,
    radius_end: float,
    sides: int,
    bone_name: str,
) -> None:
    axis = end - start
    forward, right, up = basis_from_axis(axis)
    base_index = len(verts)
    rings = [(start, radius_start), ((start + end) * 0.5, (radius_start + radius_end) * 0.52), (end, radius_end)]
    for center, radius in rings:
        for side in range(sides):
            angle = math.tau * side / sides
            co = center + right * math.cos(angle) * radius + up * math.sin(angle) * radius
            verts.append((co.x, co.y, co.z))
            assignments.append(bone_name)

    for ring in range(len(rings) - 1):
        ring_a = base_index + ring * sides
        ring_b = base_index + (ring + 1) * sides
        for side in range(sides):
            faces.append((ring_a + side, ring_a + ((side + 1) % sides), ring_b + ((side + 1) % sides), ring_b + side))
    faces.append(tuple(base_index + side for side in reversed(range(sides))))
    last = base_index + (len(rings) - 1) * sides
    faces.append(tuple(last + side for side in range(sides)))


def create_ellipsoid(
    verts: list[tuple[float, float, float]],
    faces: list[tuple[int, ...]],
    assignments: list[str],
    center: Vector,
    radius: Vector,
    group: str,
    rings: int = 5,
    sides: int = 10,
) -> None:
    base = len(verts)
    for ring in range(rings + 1):
        phi = -math.pi * 0.5 + math.pi * ring / rings
        z = math.sin(phi)
        ring_radius = math.cos(phi)
        for side in range(sides):
            theta = math.tau * side / sides
            co = Vector(
                (
                    center.x + math.cos(theta) * ring_radius * radius.x,
                    center.y + math.sin(theta) * ring_radius * radius.y,
                    center.z + z * radius.z,
                )
            )
            verts.append((co.x, co.y, co.z))
            assignments.append(group)

    for ring in range(rings):
        ring_a = base + ring * sides
        ring_b = base + (ring + 1) * sides
        for side in range(sides):
            faces.append((ring_a + side, ring_a + ((side + 1) % sides), ring_b + ((side + 1) % sides), ring_b + side))


def create_hair_clump(
    verts: list[tuple[float, float, float]],
    faces: list[tuple[int, ...]],
    assignments: list[str],
    points: list[Vector],
    radius: float,
    group: str,
    sides: int = 9,
) -> None:
    base = len(verts)
    for index, point in enumerate(points):
        if index == 0:
            tangent = points[1] - point
        elif index == len(points) - 1:
            tangent = point - points[index - 1]
        else:
            tangent = points[index + 1] - points[index - 1]
        _, right, up = basis_from_axis(tangent)
        taper = 1.0 - (index / max(1, len(points) - 1)) * 0.82
        oval_y = radius * taper * 0.70
        oval_z = radius * taper * 1.18
        for side in range(sides):
            angle = math.tau * side / sides
            co = point + right * math.cos(angle) * oval_y + up * math.sin(angle) * oval_z
            verts.append((co.x, co.y, co.z))
            assignments.append(group)

    for index in range(len(points) - 1):
        ring_a = base + index * sides
        ring_b = base + (index + 1) * sides
        for side in range(sides):
            faces.append((ring_a + side, ring_a + ((side + 1) % sides), ring_b + ((side + 1) % sides), ring_b + side))
    faces.append(tuple(base + side for side in reversed(range(sides))))
    last = base + (len(points) - 1) * sides
    faces.append(tuple(last + side for side in range(sides)))


def create_curved_panel(
    verts: list[tuple[float, float, float]],
    faces: list[tuple[int, ...]],
    assignments: list[str],
    x0: float,
    x1: float,
    z0: float,
    z1: float,
    y_front: float,
    thickness: float,
    group: str,
    x_segments: int = 3,
    z_segments: int = 7,
    asym: float = 0.0,
) -> None:
    base = len(verts)
    for layer in range(2):
        for iz in range(z_segments + 1):
            z_t = iz / z_segments
            z = z0 + (z1 - z0) * z_t
            for ix in range(x_segments + 1):
                x_t = ix / x_segments
                x = x0 + (x1 - x0) * x_t
                center_x = (x0 + x1) * 0.5
                curve = -0.010 * (1.0 - abs((x - center_x) / max(abs(x1 - x0) * 0.5, 0.001)) ** 2)
                fold = math.sin(z_t * math.pi * 2.2 + asym) * 0.0035
                edge_lift = 0.004 * abs(x_t - 0.5)
                y = y_front + curve + fold + edge_lift + (thickness if layer == 1 else 0.0)
                verts.append((x, y, z))
                assignments.append(group)

    cols = x_segments + 1
    layer_size = (x_segments + 1) * (z_segments + 1)
    for layer in range(2):
        offset = base + layer * layer_size
        for iz in range(z_segments):
            for ix in range(x_segments):
                a = offset + iz * cols + ix
                b = a + 1
                c = a + cols + 1
                d = a + cols
                faces.append((a, b, c, d) if layer == 0 else (a, d, c, b))

    # Edge thickness.
    for iz in range(z_segments):
        for ix in (0, x_segments):
            a = base + iz * cols + ix
            b = base + (iz + 1) * cols + ix
            c = base + layer_size + (iz + 1) * cols + ix
            d = base + layer_size + iz * cols + ix
            faces.append((a, b, c, d))
    for ix in range(x_segments):
        for iz in (0, z_segments):
            a = base + iz * cols + ix
            b = base + iz * cols + ix + 1
            c = base + layer_size + iz * cols + ix + 1
            d = base + layer_size + iz * cols + ix
            faces.append((a, b, c, d))


def create_refined_finger_mesh(arm: bpy.types.Object, material: bpy.types.Material, report: list[str]) -> bpy.types.Object:
    verts: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    assignments: list[str] = []

    for suffix, side_sign in (("l", -1.0), ("r", 1.0)):
        hand = arm.data.bones.get(f"hand_{suffix}")
        if hand:
            hand_axis = (hand.tail_local - hand.head_local).normalized()
            palm_center = hand.head_local + hand_axis * 0.030 + Vector((side_sign * 0.002, -0.003, -0.003))
            create_ellipsoid(verts, faces, assignments, palm_center, Vector((0.030, 0.018, 0.024)), f"hand_{suffix}", rings=6, sides=12)

        for finger in FINGER_CHAINS:
            for phalanx in PHALANGES:
                bone_name = f"{finger}_{phalanx}_{suffix}"
                bone = arm.data.bones.get(bone_name)
                if not bone:
                    continue
                finger_scale = {"thumb": 0.82, "index": 0.78, "middle": 0.86, "ring": 0.76, "pinky": 0.60}[finger]
                phalanx_scale = {"01": 1.0, "02": 0.82, "03": 0.62}[phalanx]
                radius = 0.0052 * finger_scale * phalanx_scale
                create_cylinder_segment(
                    verts,
                    faces,
                    assignments,
                    bone.head_local,
                    bone.tail_local,
                    radius,
                    radius * 0.78,
                    8,
                    bone_name,
                )
                if phalanx == "01":
                    create_ellipsoid(
                        verts,
                        faces,
                        assignments,
                        bone.head_local,
                        Vector((radius * 1.65, radius * 1.18, radius * 1.35)),
                        bone_name,
                        rings=4,
                        sides=8,
                    )
                if phalanx == "03":
                    create_ellipsoid(
                        verts,
                        faces,
                        assignments,
                        bone.tail_local,
                        Vector((radius * 1.05, radius * 0.92, radius * 0.82)),
                        bone_name,
                        rings=4,
                        sides=8,
                    )

    mesh = bpy.data.meshes.new("Player_Refined_IndependentFingers_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("Player_Refined_IndependentFingers", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(material)

    groups: dict[str, bpy.types.VertexGroup] = {}
    for bone_name in sorted(set(assignments)):
        groups[bone_name] = obj.vertex_groups.new(name=bone_name)
    for index, bone_name in enumerate(assignments):
        groups[bone_name].add([index], 1.0, "REPLACE")

    mod = obj.modifiers.new("Armature_SK_Player", "ARMATURE")
    mod.object = arm
    bevel = obj.modifiers.new("Soft_Hand_Finger_Surface", "WEIGHTED_NORMAL")
    try:
        bevel.keep_sharp = True
    except Exception:
        pass
    report.append(f"Finger/hand geometry: verts={len(verts)} faces={len(faces)} weighted_segments={len(groups)}")
    return obj


def create_box(
    verts: list[tuple[float, float, float]],
    faces: list[tuple[int, ...]],
    assignments: list[str],
    min_corner: tuple[float, float, float],
    max_corner: tuple[float, float, float],
    group: str,
) -> None:
    x0, y0, z0 = min_corner
    x1, y1, z1 = max_corner
    base = len(verts)
    verts.extend(
        [
            (x0, y0, z0),
            (x1, y0, z0),
            (x1, y1, z0),
            (x0, y1, z0),
            (x0, y0, z1),
            (x1, y0, z1),
            (x1, y1, z1),
            (x0, y1, z1),
        ]
    )
    faces.extend(
        [
            (base, base + 1, base + 2, base + 3),
            (base + 4, base + 7, base + 6, base + 5),
            (base, base + 4, base + 5, base + 1),
            (base + 1, base + 5, base + 6, base + 2),
            (base + 2, base + 6, base + 7, base + 3),
            (base + 3, base + 7, base + 4, base),
        ]
    )
    assignments.extend([group] * 8)


def create_tube_between(
    verts: list[tuple[float, float, float]],
    faces: list[tuple[int, ...]],
    assignments: list[str],
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    radius: float,
    group: str,
) -> None:
    create_cylinder_segment(verts, faces, assignments, Vector(start), Vector(end), radius, radius * 0.9, 6, group)


def create_jacket_detail_mesh(arm: bpy.types.Object, material: bpy.types.Material, report: list[str]) -> bpy.types.Object:
    verts: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    assignments: list[str] = []

    # Curved layered panels, center overlap, hem, collar, and cuffs.
    create_curved_panel(verts, faces, assignments, -0.108, -0.012, 0.505, 0.787, -0.083, 0.013, "jacket_front_l", asym=0.4)
    create_curved_panel(verts, faces, assignments, 0.012, 0.108, 0.500, 0.782, -0.084, 0.013, "jacket_front_r", asym=1.3)
    create_curved_panel(verts, faces, assignments, -0.017, 0.002, 0.505, 0.790, -0.096, 0.018, "jacket_front_l", x_segments=1, z_segments=7, asym=0.8)
    create_curved_panel(verts, faces, assignments, -0.001, 0.019, 0.500, 0.784, -0.098, 0.018, "jacket_front_r", x_segments=1, z_segments=7, asym=1.7)
    create_curved_panel(verts, faces, assignments, -0.114, -0.002, 0.478, 0.515, -0.091, 0.014, "jacket_hem_l", x_segments=4, z_segments=1, asym=2.1)
    create_curved_panel(verts, faces, assignments, 0.002, 0.116, 0.476, 0.512, -0.093, 0.014, "jacket_hem_r", x_segments=4, z_segments=1, asym=2.9)
    create_curved_panel(verts, faces, assignments, -0.130, -0.028, 0.764, 0.846, -0.067, 0.018, "hood_collar_l", x_segments=3, z_segments=2, asym=0.5)
    create_curved_panel(verts, faces, assignments, 0.028, 0.132, 0.758, 0.842, -0.069, 0.018, "hood_collar_r", x_segments=3, z_segments=2, asym=1.1)

    for suffix in ("l", "r"):
        hand = arm.data.bones.get(f"hand_{suffix}")
        if hand:
            start = Vector(hand.head_local) - (Vector(hand.tail_local) - Vector(hand.head_local)).normalized() * 0.010
            end = Vector(hand.head_local) + (Vector(hand.tail_local) - Vector(hand.head_local)).normalized() * 0.010
            create_cylinder_segment(verts, faces, assignments, start, end, 0.021, 0.023, 10, f"lowerarm_{suffix}")

    # Raised folds and seam strips.
    for x, group, wobble in [(-0.075, "jacket_front_l", -0.005), (-0.043, "jacket_front_l", 0.004), (0.045, "jacket_front_r", -0.003), (0.078, "jacket_front_r", 0.006)]:
        create_tube_between(verts, faces, assignments, (x, -0.101, 0.525), (x + wobble, -0.099, 0.758), 0.0032, group)
    create_tube_between(verts, faces, assignments, (-0.103, -0.101, 0.640), (-0.118, -0.090, 0.525), 0.0028, "jacket_front_l")
    create_tube_between(verts, faces, assignments, (0.101, -0.102, 0.635), (0.118, -0.090, 0.520), 0.0028, "jacket_front_r")
    create_tube_between(verts, faces, assignments, (-0.118, -0.092, 0.805), (-0.050, -0.096, 0.845), 0.0030, "hood_collar_l")
    create_tube_between(verts, faces, assignments, (0.050, -0.097, 0.842), (0.120, -0.092, 0.803), 0.0030, "hood_collar_r")

    mesh = bpy.data.meshes.new("Player_Refined_Jacket3D_Details_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("Player_Refined_Jacket3D_Details", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(material)

    groups: dict[str, bpy.types.VertexGroup] = {}
    for group_name in sorted(set(assignments)):
        groups[group_name] = obj.vertex_groups.new(name=group_name)
    for index, group_name in enumerate(assignments):
        groups[group_name].add([index], 1.0, "REPLACE")

    mod = obj.modifiers.new("Armature_SK_Player", "ARMATURE")
    mod.object = arm
    normal = obj.modifiers.new("Cloth_Detail_WeightedNormals", "WEIGHTED_NORMAL")
    try:
        normal.keep_sharp = True
    except Exception:
        pass
    report.append(f"Jacket/collar details: verts={len(verts)} faces={len(faces)} weighted_groups={len(groups)}")
    return obj


def create_hair_clump_mesh(arm: bpy.types.Object, material: bpy.types.Material, report: list[str]) -> bpy.types.Object:
    verts: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    assignments: list[str] = []

    clumps = [
        ([(-0.052, -0.070, 0.972), (-0.065, -0.094, 0.930), (-0.076, -0.106, 0.875)], 0.020, "hair_front_l"),
        ([(-0.034, -0.084, 0.986), (-0.040, -0.113, 0.925), (-0.048, -0.124, 0.858)], 0.017, "hair_front_l"),
        ([(-0.012, -0.094, 0.982), (-0.018, -0.126, 0.925), (-0.020, -0.134, 0.872)], 0.015, "head"),
        ([(0.012, -0.094, 0.982), (0.020, -0.126, 0.925), (0.024, -0.134, 0.872)], 0.015, "head"),
        ([(0.034, -0.084, 0.986), (0.043, -0.113, 0.925), (0.052, -0.124, 0.858)], 0.017, "hair_front_r"),
        ([(0.054, -0.070, 0.972), (0.068, -0.094, 0.930), (0.080, -0.106, 0.875)], 0.020, "hair_front_r"),
        ([(-0.073, -0.030, 0.948), (-0.094, -0.052, 0.902), (-0.101, -0.068, 0.848)], 0.016, "hair_front_l"),
        ([(0.073, -0.030, 0.948), (0.097, -0.052, 0.902), (0.104, -0.068, 0.848)], 0.016, "hair_front_r"),
        ([(-0.052, 0.022, 0.955), (-0.072, 0.018, 0.900), (-0.074, 0.005, 0.840)], 0.014, "head"),
        ([(0.052, 0.022, 0.955), (0.074, 0.018, 0.900), (0.077, 0.005, 0.840)], 0.014, "head"),
        ([(-0.018, 0.038, 0.972), (-0.024, 0.045, 0.918), (-0.026, 0.036, 0.858)], 0.013, "head"),
        ([(0.020, 0.038, 0.972), (0.028, 0.045, 0.918), (0.030, 0.036, 0.858)], 0.013, "head"),
    ]
    for points, radius, group in clumps:
        create_hair_clump(verts, faces, assignments, [Vector(point) for point in points], radius, group, sides=9)

    mesh = bpy.data.meshes.new("Player_Refined_LayeredHairClumps_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("Player_Refined_LayeredHairClumps", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(material)

    groups: dict[str, bpy.types.VertexGroup] = {}
    for group_name in sorted(set(assignments)):
        groups[group_name] = obj.vertex_groups.new(name=group_name)
    for index, group_name in enumerate(assignments):
        groups[group_name].add([index], 1.0, "REPLACE")

    mod = obj.modifiers.new("Armature_SK_Player", "ARMATURE")
    mod.object = arm
    normal = obj.modifiers.new("Hair_Clump_WeightedNormals", "WEIGHTED_NORMAL")
    report.append(f"Hair clumps: verts={len(verts)} faces={len(faces)} weighted_groups={len(groups)}")
    return obj


def add_missing_vertex_groups(mesh_obj: bpy.types.Object, arm: bpy.types.Object) -> None:
    for bone in arm.data.bones:
        if bone.use_deform and not mesh_obj.vertex_groups.get(bone.name):
            mesh_obj.vertex_groups.new(name=bone.name)


def rigidify_shoe_weights(mesh_obj: bpy.types.Object, report: list[str]) -> None:
    mesh = mesh_obj.data
    deform_group_names = {group.name for group in mesh_obj.vertex_groups}
    changed = {"l": 0, "r": 0}
    for suffix, sign in (("l", -1.0), ("r", 1.0)):
        foot_group = mesh_obj.vertex_groups.get(f"foot_{suffix}")
        if not foot_group:
            continue
        for vert in mesh.vertices:
            co = vert.co
            if co.z > 0.118:
                continue
            if sign < 0.0 and co.x > -0.045:
                continue
            if sign > 0.0 and co.x < 0.045:
                continue
            if not (-0.125 <= co.y <= 0.085):
                continue

            existing = [mesh_obj.vertex_groups[item.group] for item in vert.groups if mesh_obj.vertex_groups[item.group].name in deform_group_names]
            for group in existing:
                try:
                    group.remove([vert.index])
                except RuntimeError:
                    pass
            foot_group.add([vert.index], 1.0, "REPLACE")
            changed[suffix] += 1
    report.append(f"Shoe rigid weights: left_vertices={changed['l']} right_vertices={changed['r']}")


def create_finger_bend_selftest_action(arm: bpy.types.Object, report: list[str]) -> None:
    if not arm.animation_data:
        arm.animation_data_create()
    previous_action = arm.animation_data.action
    action = bpy.data.actions.new("AN_Player_FingerBend_SelfTest")
    action.use_fake_user = True
    arm.animation_data.action = action
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")

    finger_pose_bones = []
    for pose_bone in arm.pose.bones:
        if any(pose_bone.name.startswith(f"{finger}_") for finger in FINGER_CHAINS):
            finger_pose_bones.append(pose_bone)
        pose_bone.rotation_mode = "XYZ"
        pose_bone.rotation_euler = (0.0, 0.0, 0.0)

    for pose_bone in finger_pose_bones:
        pose_bone.keyframe_insert(data_path="rotation_euler", frame=1)

    keyed = 0
    for suffix, bend_sign in (("l", 1.0), ("r", -1.0)):
        for finger in FINGER_CHAINS:
            for phalanx in ("01", "02", "03"):
                bone = arm.pose.bones.get(f"{finger}_{phalanx}_{suffix}")
                if not bone:
                    continue
                bone.rotation_mode = "XYZ"
                bone.rotation_euler[0] = bend_sign * math.radians(22 if phalanx == "01" else 34)
                bone.keyframe_insert(data_path="rotation_euler", frame=18)
                keyed += 1

    for pose_bone in finger_pose_bones:
        pose_bone.rotation_euler = (0.0, 0.0, 0.0)
        pose_bone.keyframe_insert(data_path="rotation_euler", frame=36)

    bpy.ops.object.mode_set(mode="OBJECT")
    arm.animation_data.action = previous_action
    report.append(f"Finger bend self-test action: keyed_finger_bones={keyed}")


def shade_and_tag(obj: bpy.types.Object) -> None:
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    try:
        bpy.ops.object.shade_smooth()
    except Exception:
        pass
    obj.select_set(False)
    obj["PenanceRefinedPlayerModel"] = True


def export_refined_fbx(arm: bpy.types.Object, objects: list[bpy.types.Object], output_fbx: Path, report: list[str]) -> None:
    output_fbx.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = arm
    try:
        bpy.ops.export_scene.fbx(
            filepath=str(output_fbx),
            use_selection=True,
            object_types={"ARMATURE", "MESH"},
            add_leaf_bones=False,
            bake_anim=True,
            use_mesh_modifiers=True,
            mesh_smooth_type="FACE",
            primary_bone_axis="Y",
            secondary_bone_axis="X",
        )
        report.append(f"FBX export: {output_fbx}")
    except Exception as exc:
        report.append(f"FBX export failed: {exc}")


def main() -> None:
    source, output, fbx, report_path = parse_args()
    if not source.exists():
        raise RuntimeError(f"Missing source blend: {source}")

    report: list[str] = [
        "PLAYER_MODEL_REFINED_HIGH_QUALITY_REPORT",
        f"Source: {source}",
        f"Output: {output}",
        f"Idle reference: {IDLE_BLEND}",
    ]

    # Keep every pre-existing action alive.
    for action in bpy.data.actions:
        action.use_fake_user = True

    arm = bpy.data.objects.get(ARMATURE_NAME)
    mesh = bpy.data.objects.get(MESH_NAME)
    if not arm or arm.type != "ARMATURE":
        raise RuntimeError(f"Missing armature: {ARMATURE_NAME}")
    if not mesh or mesh.type != "MESH":
        raise RuntimeError(f"Missing mesh: {MESH_NAME}")

    duplicate_backups(arm, mesh)
    append_idle_reference(report)

    skin_mat = ensure_material("MQ_Player_Skin_Refined", (0.72, 0.50, 0.39, 1.0), 0.72)
    jacket_mat = ensure_material("MQ_Player_Jacket_Cloth_Refined", (0.045, 0.052, 0.060, 1.0), 0.91)
    hair_mat = ensure_material("MQ_Player_Hair_Clumps_Refined", (0.060, 0.043, 0.034, 1.0), 0.86)

    add_finger_bones(arm, report)
    add_missing_vertex_groups(mesh, arm)
    rigidify_shoe_weights(mesh, report)

    refined_objects = [
        mesh,
        create_refined_finger_mesh(arm, skin_mat, report),
        create_jacket_detail_mesh(arm, jacket_mat, report),
        create_hair_clump_mesh(arm, hair_mat, report),
    ]
    for obj in refined_objects:
        shade_and_tag(obj)

    create_finger_bend_selftest_action(arm, report)

    arm["PenanceSkeletonCompatibility"] = "Existing bone names preserved; finger chains added under hand_l/hand_r; no rest pose applied."
    mesh["PenanceShoeWeights"] = "Shoe-region vertices below z=0.118 locked to foot_l/foot_r."

    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    report.append("Saved refined blend: yes")

    if fbx:
        export_refined_fbx(arm, refined_objects, fbx, report)
    else:
        report.append("FBX export: skipped")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))
    bpy.ops.wm.quit_blender()


if __name__ == "__main__":
    main()
