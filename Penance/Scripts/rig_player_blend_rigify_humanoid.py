"""Fit a Rigify humanoid IK rig to Penance/Content/Player/Player.blend.

This is intentionally targeted at the current Player.blend:
- one visible player mesh named Mesh_0
- one source Mixamo-style armature named Armature

Run from Blender:
  blender --background --python Penance/Scripts/rig_player_blend_rigify_humanoid.py -- SRC.blend REPORT.txt
"""

from __future__ import annotations

import math
import os
import shutil
import sys
from pathlib import Path

import addon_utils
import bpy
from mathutils import Matrix, Vector


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BLEND = PROJECT_ROOT / "Content" / "Player" / "Player.blend"
DEFAULT_REPORT = PROJECT_ROOT / "Saved" / "PlayerRigifyHumanoidReport.txt"
BACKUP_PATH = PROJECT_ROOT / "Content" / "Player" / "BlenderSource" / "Backups" / "Player_before_rigify_humanoid_ik.blend"

SOURCE_ARMATURE_NAME = "Armature"
SOURCE_ARMATURE_HIDDEN_NAME = "SOURCE_Mixamo_TPose_Armature_HIDDEN"
MESH_NAME = "Mesh_0"
META_NAME = "META_Player_Rigify_Humanoid_Fitted"
RIG_NAME = "RIG_Player_Rigify_Humanoid_IK"
SELF_TEST_ACTION = "AN_Player_Rigify_IK_FK_Deform_SelfTest"

MIXAMO_PREFIX = "mixamorig5:"


def args_after_separator() -> tuple[Path, Path]:
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    src = Path(args[0]).expanduser().resolve() if args else DEFAULT_BLEND
    report = Path(args[1]).expanduser().resolve() if len(args) > 1 else DEFAULT_REPORT
    if not src.exists():
        raise SystemExit(f"Blend file does not exist: {src}")
    report.parent.mkdir(parents=True, exist_ok=True)
    BACKUP_PATH.parent.mkdir(parents=True, exist_ok=True)
    return src, report


def ensure_backup(src: Path) -> str:
    if BACKUP_PATH.exists():
        return f"Backup already exists: {BACKUP_PATH}"
    shutil.copy2(src, BACKUP_PATH)
    return f"Backup created: {BACKUP_PATH}"


def object_by_name(name: str, obj_type: str) -> bpy.types.Object:
    obj = bpy.data.objects.get(name)
    if not obj or obj.type != obj_type:
        raise SystemExit(f"Expected {obj_type} object named {name}")
    return obj


def source_armature() -> bpy.types.Object:
    for name in (SOURCE_ARMATURE_NAME, SOURCE_ARMATURE_HIDDEN_NAME):
        obj = bpy.data.objects.get(name)
        if obj and obj.type == "ARMATURE":
            obj.hide_viewport = False
            return obj
    raise SystemExit(f"Expected source armature named {SOURCE_ARMATURE_NAME} or {SOURCE_ARMATURE_HIDDEN_NAME}")


def world_bone_points(armature: bpy.types.Object) -> dict[str, tuple[Vector, Vector]]:
    return {
        bone.name: (
            armature.matrix_world @ bone.head_local,
            armature.matrix_world @ bone.tail_local,
        )
        for bone in armature.data.bones
    }


def mixamo_name(short_name: str) -> str:
    return f"{MIXAMO_PREFIX}{short_name}"


def center_between(points: dict[str, tuple[Vector, Vector]], names: list[str], end: str = "head") -> Vector:
    values: list[Vector] = []
    index = 0 if end == "head" else 1
    for name in names:
        if name in points:
            values.append(points[name][index])
    if not values:
        return Vector((0.0, 0.08, 1.0))
    total = Vector((0.0, 0.0, 0.0))
    for value in values:
        total += value
    return total / len(values)


def rotate_y_around(point: Vector, pivot: Vector, angle: float) -> Vector:
    return pivot + Matrix.Rotation(angle, 4, "Y") @ (point - pivot)


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    if edge0 == edge1:
        return 1.0 if x >= edge1 else 0.0
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def arm_a_pose_transform(point: Vector, side: str, shoulder: Vector, angle_degrees: float = 38.0) -> Vector:
    sign = 1.0 if side == "L" else -1.0
    angle = math.radians(angle_degrees) * sign
    return rotate_y_around(point, shoulder, angle)


def convert_mesh_to_relaxed_a_pose(mesh: bpy.types.Object, points: dict[str, tuple[Vector, Vector]]) -> int:
    """Bend the existing horizontal arm mesh down to match the fitted A-pose rig.

    The bind mesh needs to follow the bind armature. This keeps the torso mostly
    untouched and smoothly blends the shoulder/sleeve area into each arm.
    """

    left_shoulder = points[mixamo_name("LeftArm")][0]
    right_shoulder = points[mixamo_name("RightArm")][0]
    changed = 0
    for vertex in mesh.data.vertices:
        p = vertex.co.copy()
        side: str | None = None
        if p.x > 0.115 and 1.34 <= p.z <= 1.78:
            side = "L"
            shoulder = left_shoulder
            outward = p.x
        elif p.x < -0.115 and 1.34 <= p.z <= 1.78:
            side = "R"
            shoulder = right_shoulder
            outward = -p.x
        else:
            continue

        # Full effect past the upper arm, soft blend through shoulder and sleeve.
        x_factor = smoothstep(0.115, 0.265, outward)
        z_factor = smoothstep(1.34, 1.46, p.z) * (1.0 - smoothstep(1.74, 1.80, p.z))
        factor = x_factor * z_factor
        if factor <= 0.0:
            continue

        target = arm_a_pose_transform(p, side, shoulder)
        vertex.co = p.lerp(target, factor)
        changed += 1

    mesh.data.update()
    return changed


def apply_mesh_world_transform(mesh: bpy.types.Object) -> None:
    bpy.ops.object.mode_set(mode="OBJECT") if bpy.ops.object.mode_set.poll() else None
    world = mesh.matrix_world.copy()
    for vertex in mesh.data.vertices:
        vertex.co = world @ vertex.co
    mesh.matrix_world = Matrix.Identity(4)
    mesh.data.update()
    mesh.hide_viewport = False
    mesh.hide_render = False
    mesh.hide_set(False)


def remove_prior_generated_rigs() -> int:
    removed = 0
    for obj in list(bpy.data.objects):
        if obj.name.startswith(
            (
                META_NAME,
                RIG_NAME,
                "RIG_Player_Rigify_Humanoid_Fitted",
                "WGT-RIG_Player_Rigify",
                "WGT-rig",
                "rig",
                "metarig",
            )
        ):
            data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if data and data.users == 0 and isinstance(data, bpy.types.Armature):
                bpy.data.armatures.remove(data)
            elif data and data.users == 0 and isinstance(data, bpy.types.Mesh):
                bpy.data.meshes.remove(data)
            removed += 1
    for collection in list(bpy.data.collections):
        if collection.name.startswith(("WGTS_", "Widgets")) and not collection.objects:
            bpy.data.collections.remove(collection)
    for text in list(bpy.data.texts):
        if text.name.startswith(("RIG_Player_Rigify_Humanoid_Fitted_ui", f"{RIG_NAME}_ui")):
            bpy.data.texts.remove(text)
    action = bpy.data.actions.get(SELF_TEST_ACTION)
    if action:
        bpy.data.actions.remove(action)
    return removed


def set_bone(eb: bpy.types.ArmatureEditBones, name: str, head: Vector, tail: Vector) -> None:
    if name not in eb:
        return
    bone = eb[name]
    if (tail - head).length < 0.002:
        tail = head + Vector((0.0, 0.0, 0.02))
    bone.head = head
    bone.tail = tail


def set_connected_chain(eb: bpy.types.ArmatureEditBones, names: list[str], points: list[Vector]) -> None:
    for index, name in enumerate(names):
        set_bone(eb, name, points[index], points[index + 1])


def transformed_mixamo_bone(
    points: dict[str, tuple[Vector, Vector]],
    short_name: str,
    side: str | None = None,
) -> tuple[Vector, Vector]:
    head, tail = points[mixamo_name(short_name)]
    if side:
        shoulder = points[mixamo_name("LeftArm" if side == "L" else "RightArm")][0]
        head = arm_a_pose_transform(head, side, shoulder)
        tail = arm_a_pose_transform(tail, side, shoulder)
    return head, tail


def fit_rigify_metarig(points: dict[str, tuple[Vector, Vector]]) -> bpy.types.Object:
    addon_utils.enable("rigify", default_set=True)
    bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
    bpy.ops.object.armature_human_metarig_add()
    meta = bpy.context.object
    meta.name = META_NAME
    meta.data.name = f"{META_NAME}_Data"
    meta.location = (0.0, 0.0, 0.0)
    meta.rotation_euler = (0.0, 0.0, 0.0)
    meta.scale = (1.0, 1.0, 1.0)
    bpy.context.view_layer.update()
    meta.show_in_front = True
    meta.data.display_type = "BBONE"

    body_center = center_between(points, [mixamo_name("Hips"), mixamo_name("Spine")], "head")
    default_head_top_z = 1.98
    target_head_top_z = points[mixamo_name("HeadTop_End")][1].z
    scale = target_head_top_z / default_head_top_z
    offset = Vector((body_center.x, body_center.y - 0.01, 0.0))

    bpy.ops.object.mode_set(mode="EDIT")
    eb = meta.data.edit_bones

    for bone in eb:
        bone.head = bone.head * scale + offset
        bone.tail = bone.tail * scale + offset

    hip = center_between(points, [mixamo_name("Hips")], "head")
    spine_tail = points[mixamo_name("Spine")][1]
    spine1_tail = points[mixamo_name("Spine1")][1]
    neck_head = points[mixamo_name("Neck")][0]
    neck_tail = points[mixamo_name("Neck")][1]
    head_head = points[mixamo_name("Head")][0]
    head_top = points[mixamo_name("HeadTop_End")][1]

    # Rigify spine rigs require a perfectly connected chain. The source Mixamo
    # skeleton has small gaps, so use player-derived landmarks but snap each
    # segment endpoint to the next segment start.
    spine_points = [
        hip + Vector((0.0, 0.0, -0.04)),
        points[mixamo_name("Hips")][1],
        spine_tail,
        spine1_tail,
        neck_head,
        neck_tail,
        head_head,
        head_top,
    ]
    set_connected_chain(
        eb,
        ["spine", "spine.001", "spine.002", "spine.003", "spine.004", "spine.005", "spine.006"],
        spine_points,
    )

    for side, prefix in (("L", "Left"), ("R", "Right")):
        suffix = ".L" if side == "L" else ".R"
        shoulder = transformed_mixamo_bone(points, f"{prefix}Shoulder", side)
        upper = transformed_mixamo_bone(points, f"{prefix}Arm", side)
        fore = transformed_mixamo_bone(points, f"{prefix}ForeArm", side)
        hand = transformed_mixamo_bone(points, f"{prefix}Hand", side)
        elbow_soft = upper[1] + Vector((0.0, -0.045, 0.0))
        set_bone(eb, f"shoulder{suffix}", shoulder[0], shoulder[1])
        set_connected_chain(eb, [f"upper_arm{suffix}", f"forearm{suffix}", f"hand{suffix}"], [upper[0], elbow_soft, fore[1], hand[1]])

        fingers = {
            "thumb": "Thumb",
            "f_index": "Index",
            "f_middle": "Middle",
            "f_ring": "Ring",
            "f_pinky": "Pinky",
        }
        for rigify_prefix, mixamo_finger in fingers.items():
            for index in (1, 2, 3):
                source = f"{prefix}Hand{mixamo_finger}{index}"
                chain_points: list[Vector] = []
                for chain_index in (1, 2, 3, 4):
                    chain_source = f"{prefix}Hand{mixamo_finger}{chain_index}"
                    if mixamo_name(chain_source) not in points:
                        continue
                    chain_head, chain_tail = transformed_mixamo_bone(points, chain_source, side)
                    if not chain_points:
                        chain_points.append(chain_head)
                    if chain_index <= 3:
                        chain_points.append(chain_tail)
                    elif len(chain_points) == 3:
                        chain_points.append(chain_tail)
                if len(chain_points) >= 4:
                    set_connected_chain(
                        eb,
                        [f"{rigify_prefix}.01{suffix}", f"{rigify_prefix}.02{suffix}", f"{rigify_prefix}.03{suffix}"],
                        chain_points[:4],
                    )
                break

        palm_sources = ["Index1", "Middle1", "Ring1", "Pinky1"]
        for palm_index, source_suffix in enumerate(palm_sources, start=1):
            finger_head = transformed_mixamo_bone(points, f"{prefix}Hand{source_suffix}", side)[0]
            hand_tail = hand[1]
            set_bone(eb, f"palm.{palm_index:02d}{suffix}", hand_tail, finger_head)

        leg_prefix = prefix
        thigh = transformed_mixamo_bone(points, f"{leg_prefix}UpLeg")
        shin = transformed_mixamo_bone(points, f"{leg_prefix}Leg")
        foot = transformed_mixamo_bone(points, f"{leg_prefix}Foot")
        toe = transformed_mixamo_bone(points, f"{leg_prefix}ToeBase")
        knee_soft = thigh[1] + Vector((0.0, -0.035, 0.0))
        set_connected_chain(eb, [f"thigh{suffix}", f"shin{suffix}", f"foot{suffix}", f"toe{suffix}"], [thigh[0], knee_soft, shin[1], foot[1], toe[1]])

        heel_head = foot[1] + Vector((0.0, 0.035, 0.0))
        heel_tail = heel_head + Vector((0.0, 0.045, 0.0))
        set_bone(eb, f"heel.02{suffix}", heel_head, heel_tail)

    # Keep optional torso helpers inside the torso volume.
    chest_anchor = spine_points[3]
    set_bone(eb, "breast.L", chest_anchor + Vector((0.055, -0.035, -0.03)), chest_anchor + Vector((0.105, -0.065, -0.05)))
    set_bone(eb, "breast.R", chest_anchor + Vector((-0.055, -0.035, -0.03)), chest_anchor + Vector((-0.105, -0.065, -0.05)))
    set_bone(eb, "pelvis.L", hip + Vector((0.045, 0.0, -0.02)), hip + Vector((0.12, 0.0, -0.055)))
    set_bone(eb, "pelvis.R", hip + Vector((-0.045, 0.0, -0.02)), hip + Vector((-0.12, 0.0, -0.055)))

    bpy.ops.object.mode_set(mode="OBJECT")
    return meta


def generate_rig(meta: bpy.types.Object) -> bpy.types.Object:
    bpy.ops.object.select_all(action="DESELECT")
    meta.select_set(True)
    bpy.context.view_layer.objects.active = meta
    bpy.ops.object.mode_set(mode="POSE")
    before = {obj.name for obj in bpy.data.objects if obj.type == "ARMATURE"}
    bpy.ops.pose.rigify_generate()
    bpy.ops.object.mode_set(mode="OBJECT")
    candidates = [obj for obj in bpy.data.objects if obj.type == "ARMATURE" and obj.name not in before]
    if not candidates:
        candidates = [obj for obj in bpy.data.objects if obj.type == "ARMATURE" and obj.name.startswith("rig")]
    if not candidates:
        raise RuntimeError("Rigify did not create a generated rig")
    rig = candidates[-1]
    rig.name = RIG_NAME
    rig.data.name = f"{RIG_NAME}_Data"
    rig.show_in_front = True
    rig.data.display_type = "BBONE"
    return rig


def bind_mesh_with_auto_weights(mesh: bpy.types.Object, rig: bpy.types.Object) -> str:
    bpy.ops.object.mode_set(mode="OBJECT") if bpy.ops.object.mode_set.poll() else None
    mesh.parent = None
    for modifier in list(mesh.modifiers):
        if modifier.type == "ARMATURE":
            mesh.modifiers.remove(modifier)
    for group in list(mesh.vertex_groups):
        mesh.vertex_groups.remove(group)

    bpy.ops.object.select_all(action="DESELECT")
    mesh.select_set(True)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    try:
        with bpy.context.temp_override(
            active_object=rig,
            object=rig,
            selected_objects=[mesh, rig],
            selected_editable_objects=[mesh, rig],
        ):
            op_result = bpy.ops.object.parent_set(type="ARMATURE_AUTO")
        has_armature_modifier = any(modifier.type == "ARMATURE" and modifier.object == rig for modifier in mesh.modifiers)
        if op_result == {"CANCELLED"} or not mesh.vertex_groups or not has_armature_modifier:
            raise RuntimeError(f"parent_set returned {op_result}, groups={len(mesh.vertex_groups)}, armature_modifier={has_armature_modifier}")
        result = "Automatic weights succeeded"
    except Exception as exc:
        # Fallback keeps the file animatable if Blender's bone heat solver fails.
        mesh.parent = rig
        modifier = mesh.modifiers.new("RigifyHumanoidArmature", "ARMATURE")
        modifier.object = rig
        create_nearest_bone_fallback_weights(mesh, rig)
        result = f"Automatic weights failed; used nearest-deform-bone fallback: {exc}"

    for modifier in mesh.modifiers:
        if modifier.type == "ARMATURE":
            modifier.name = "RigifyHumanoidArmature"
            modifier.object = rig
            modifier.use_vertex_groups = True
    mesh.hide_viewport = False
    mesh.hide_render = False
    mesh.hide_set(False)
    return result


def distance_to_segment(point: Vector, a: Vector, b: Vector) -> float:
    axis = b - a
    length_sq = axis.length_squared
    if length_sq <= 1e-8:
        return (point - a).length
    t = max(0.0, min(1.0, (point - a).dot(axis) / length_sq))
    closest = a + axis * t
    return (point - closest).length


def create_nearest_bone_fallback_weights(mesh: bpy.types.Object, rig: bpy.types.Object) -> None:
    deform_bones = [bone for bone in rig.data.bones if bone.use_deform and bone.name.startswith("DEF-")]
    groups = {bone.name: mesh.vertex_groups.new(name=bone.name) for bone in deform_bones}
    segments = [
        (
            bone.name,
            rig.matrix_world @ bone.head_local,
            rig.matrix_world @ bone.tail_local,
        )
        for bone in deform_bones
    ]
    for vertex in mesh.data.vertices:
        p = mesh.matrix_world @ vertex.co
        nearest = sorted(
            ((name, distance_to_segment(p, head, tail)) for name, head, tail in segments),
            key=lambda item: item[1],
        )[:3]
        weighted = [(name, 1.0 / max(distance, 0.002) ** 2) for name, distance in nearest]
        total = sum(weight for _name, weight in weighted)
        for name, weight in weighted:
            groups[name].add([vertex.index], weight / total, "ADD")


def hide_source_armature(source: bpy.types.Object) -> None:
    source.name = "SOURCE_Mixamo_TPose_Armature_HIDDEN"
    source.data.name = "SOURCE_Mixamo_TPose_Armature_Data_HIDDEN"
    source.hide_viewport = True
    source.hide_render = True


def make_self_test_action(rig: bpy.types.Object) -> tuple[str, int]:
    action = bpy.data.actions.new(SELF_TEST_ACTION)
    rig.animation_data_create()
    rig.animation_data.action = action
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 48

    controls = [
        "torso",
        "chest",
        "head",
        "upper_arm_fk.L",
        "forearm_fk.L",
        "hand_fk.L",
        "upper_arm_fk.R",
        "forearm_fk.R",
        "hand_fk.R",
        "hand_ik.L",
        "hand_ik.R",
        "foot_ik.L",
        "foot_ik.R",
    ]
    keyed = 0
    for frame, side in ((1, 0.0), (16, 1.0), (32, -1.0), (48, 0.0)):
        bpy.context.scene.frame_set(frame)
        for name in controls:
            bone = rig.pose.bones.get(name)
            if not bone:
                continue
            bone.rotation_mode = "XYZ"
            bone.location = (0.0, 0.0, 0.0)
            bone.rotation_euler = (0.0, 0.0, 0.0)
            if name == "chest":
                bone.rotation_euler = (0.04 * side, 0.0, 0.05 * side)
            elif name == "head":
                bone.rotation_euler = (-0.04 * side, 0.0, -0.04 * side)
            elif "upper_arm_fk.L" == name:
                bone.rotation_euler = (0.0, 0.0, -0.35 * side)
            elif "upper_arm_fk.R" == name:
                bone.rotation_euler = (0.0, 0.0, 0.35 * side)
            elif name.startswith("forearm_fk"):
                bone.rotation_euler = (0.0, 0.0, 0.20 * side)
            elif name == "hand_ik.L":
                bone.location = (0.0, -0.02 * side, 0.05 * side)
            elif name == "hand_ik.R":
                bone.location = (0.0, 0.02 * side, -0.05 * side)
            elif name == "foot_ik.L":
                bone.location = (0.0, -0.02 * side, 0.02 * side)
            elif name == "foot_ik.R":
                bone.location = (0.0, 0.02 * side, -0.02 * side)
            bone.keyframe_insert("location", frame=frame)
            bone.keyframe_insert("rotation_euler", frame=frame)
            keyed += 1
    return action.name, keyed


def weighted_vertex_count(mesh: bpy.types.Object) -> int:
    return sum(1 for vertex in mesh.data.vertices if vertex.groups)


def generate_report(
    path: Path,
    src: Path,
    backup_line: str,
    removed_generated: int,
    mesh_vertices_a_posed: int,
    source: bpy.types.Object,
    meta: bpy.types.Object,
    rig: bpy.types.Object,
    mesh: bpy.types.Object,
    bind_result: str,
    action_name: str,
    keyed: int,
) -> None:
    deform = [bone.name for bone in rig.data.bones if bone.use_deform]
    helpers = [bone.name for bone in rig.data.bones if not bone.use_deform]
    ik_controls = [name for name in rig.pose.bones.keys() if "ik" in name.lower()]
    fk_controls = [name for name in rig.pose.bones.keys() if "fk" in name.lower()]
    twist_deforms = [
        name
        for name in deform
        if any(part in name.lower() for part in ("upper_arm", "forearm", "thigh", "shin"))
        and any(ch.isdigit() for ch in name)
    ]
    modifiers = [f"{mod.name}:{mod.type}:{getattr(mod, 'object', None).name if getattr(mod, 'object', None) else 'none'}" for mod in mesh.modifiers]
    lines = [
        "PLAYER_RIGIFY_HUMANOID_IK_REPORT",
        f"Blend: {src}",
        backup_line,
        f"Removed prior generated rigs: {removed_generated}",
        f"Source armature hidden backup in file: {source.name}",
        f"Metarig: {meta.name}",
        f"Generated rig: {rig.name}",
        f"Mesh: {mesh.name}",
        f"Mesh vertices converted to relaxed A-pose: {mesh_vertices_a_posed}",
        f"Bind result: {bind_result}",
        f"Mesh parent: {mesh.parent.name if mesh.parent else 'none'}",
        f"Mesh modifiers: {', '.join(modifiers) if modifiers else 'none'}",
        f"Vertex groups: {len(mesh.vertex_groups)}",
        f"Weighted vertices: {weighted_vertex_count(mesh)} / {len(mesh.data.vertices)}",
        f"Generated rig bones: {len(rig.data.bones)}",
        f"Generated deform bones: {len(deform)}",
        f"Generated helper/control bones: {len(helpers)}",
        f"IK controls found: {len(ik_controls)}",
        ", ".join(sorted(ik_controls)[:80]),
        f"FK controls found: {len(fk_controls)}",
        ", ".join(sorted(fk_controls)[:80]),
        f"Twist/segment deform bones found: {len(twist_deforms)}",
        ", ".join(sorted(twist_deforms)[:80]),
        f"Self-test action: {action_name}",
        f"Self-test keyed transforms: {keyed}",
        "Notes:",
        "- Rigify full human metarig was fitted to the player proportions and generated into an IK/FK control rig.",
        "- Mesh was bound to the generated Rigify rig; the original Mixamo armature remains hidden as an in-file reference.",
        "- The bind mesh arms were moved from horizontal T-pose into a relaxed A-pose to reduce shoulder/armpit distortion.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    src, report = args_after_separator()
    backup_line = ensure_backup(src)
    bpy.ops.wm.open_mainfile(filepath=str(src), load_ui=False)

    source = source_armature()
    mesh = object_by_name(MESH_NAME, "MESH")
    points = world_bone_points(source)

    removed_generated = remove_prior_generated_rigs()
    apply_mesh_world_transform(mesh)
    mesh_vertices_a_posed = convert_mesh_to_relaxed_a_pose(mesh, points)

    meta = fit_rigify_metarig(points)
    rig = generate_rig(meta)
    bind_result = bind_mesh_with_auto_weights(mesh, rig)
    hide_source_armature(source)
    meta.hide_viewport = True
    meta.hide_render = True

    action_name, keyed = make_self_test_action(rig)
    generate_report(
        report,
        src,
        backup_line,
        removed_generated,
        mesh_vertices_a_posed,
        source,
        meta,
        rig,
        mesh,
        bind_result,
        action_name,
        keyed,
    )

    bpy.ops.wm.save_as_mainfile(filepath=str(src))
    print(f"PLAYER_RIGIFY_HUMANOID_IK_DONE: {src}")
    print(f"REPORT: {report}")
    sys.stdout.flush()
    os._exit(0)


main()
