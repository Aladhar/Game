"""Adapt helper controls to the actual model silhouette and add walk actions."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector


PLAYER_REMOVE = {
    "cloth_front_l",
    "cloth_front_r",
    "cloth_back_l",
    "cloth_back_r",
    "coat_side_l",
    "coat_side_r",
}

PENANCE_REMOVE = {
    "camera",
    "jaw",
    "eye_l",
    "eye_r",
    "weapon_l",
    "weapon_r",
}


def args_after_separator() -> tuple[str, Path, Path]:
    if "--" not in sys.argv:
        raise SystemExit("Expected arguments after --: player|penance SRC.blend REPORT.txt")
    args = sys.argv[sys.argv.index("--") + 1 :]
    if len(args) != 3:
        raise SystemExit("Expected arguments after --: player|penance SRC.blend REPORT.txt")
    kind = args[0].lower()
    if kind not in {"player", "penance"}:
        raise SystemExit("First argument must be player or penance")
    src = Path(args[1]).expanduser().resolve()
    report = Path(args[2]).expanduser().resolve()
    if not src.exists():
        raise SystemExit(f"Blend does not exist: {src}")
    report.parent.mkdir(parents=True, exist_ok=True)
    return kind, src, report


def first_armature() -> bpy.types.Object:
    armatures = [obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"]
    if not armatures:
        raise SystemExit("No armature found")
    return armatures[0]


def first_mesh() -> bpy.types.Object | None:
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    return meshes[0] if meshes else None


def set_edit_mode(armature: bpy.types.Object) -> None:
    bpy.ops.object.mode_set(mode="OBJECT") if bpy.ops.object.mode_set.poll() else None
    bpy.ops.object.select_all(action="DESELECT")
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    bpy.context.view_layer.update()
    with bpy.context.temp_override(
        active_object=armature,
        object=armature,
        selected_objects=[armature],
        selected_editable_objects=[armature],
    ):
        bpy.ops.object.mode_set(mode="EDIT")


def set_pose_mode(armature: bpy.types.Object) -> None:
    bpy.ops.object.mode_set(mode="OBJECT") if bpy.ops.object.mode_set.poll() else None
    bpy.ops.object.select_all(action="DESELECT")
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    bpy.context.view_layer.update()
    with bpy.context.temp_override(
        active_object=armature,
        object=armature,
        selected_objects=[armature],
        selected_editable_objects=[armature],
    ):
        bpy.ops.object.mode_set(mode="POSE")


def remove_bones_and_groups(armature: bpy.types.Object, mesh: bpy.types.Object | None, names: set[str]) -> list[str]:
    removed: list[str] = []
    set_edit_mode(armature)
    for name in sorted(names):
        bone = armature.data.edit_bones.get(name)
        if bone:
            armature.data.edit_bones.remove(bone)
            removed.append(name)
    bpy.ops.object.mode_set(mode="OBJECT")
    if mesh:
        for name in sorted(names):
            group = mesh.vertex_groups.get(name)
            if group:
                mesh.vertex_groups.remove(group)
    return removed


def make_bone(edit_bones, name: str, head: Vector, tail: Vector, parent_name: str | None, deform: bool) -> bool:
    if name in edit_bones:
        edit_bones[name].use_deform = deform
        return False
    bone = edit_bones.new(name)
    bone.head = head
    bone.tail = tail
    bone.use_deform = deform
    if parent_name and parent_name in edit_bones:
        bone.parent = edit_bones[parent_name]
    return True


def add_player_controls(armature: bpy.types.Object) -> list[str]:
    set_edit_mode(armature)
    eb = armature.data.edit_bones
    created: list[str] = []
    specs = [
        ("jacket_front_l", Vector((-0.055, -0.095, 0.62)), Vector((-0.075, -0.105, 0.38)), "spine_01", True),
        ("jacket_front_r", Vector((0.055, -0.095, 0.62)), Vector((0.075, -0.105, 0.38)), "spine_01", True),
        ("jacket_hem_l", Vector((-0.095, -0.040, 0.44)), Vector((-0.125, -0.045, 0.34)), "pelvis", True),
        ("jacket_hem_r", Vector((0.095, -0.040, 0.44)), Vector((0.125, -0.045, 0.34)), "pelvis", True),
        ("hood_collar_l", Vector((-0.060, -0.020, 0.78)), Vector((-0.135, -0.005, 0.72)), "neck_01", True),
        ("hood_collar_r", Vector((0.060, -0.020, 0.78)), Vector((0.135, -0.005, 0.72)), "neck_01", True),
        ("hair_front_l", Vector((-0.035, -0.085, 0.96)), Vector((-0.060, -0.095, 0.87)), "head", True),
        ("hair_front_r", Vector((0.035, -0.085, 0.96)), Vector((0.060, -0.095, 0.87)), "head", True),
        ("look_at", Vector((0.0, -0.28, 0.92)), Vector((0.0, -0.36, 0.92)), "head", False),
        ("camera", Vector((0.0, -0.18, 0.90)), Vector((0.0, -0.28, 0.90)), "head", False),
    ]
    for spec in specs:
        if make_bone(eb, *spec):
            created.append(spec[0])
    bpy.ops.object.mode_set(mode="OBJECT")
    return created


def add_penance_controls(armature: bpy.types.Object) -> list[str]:
    set_edit_mode(armature)
    eb = armature.data.edit_bones
    created: list[str] = []
    specs = [
        ("hunch_spine_upper", Vector((0.16, -0.04, 0.78)), Vector((0.13, -0.08, 0.62)), "spine_02", True),
        ("hunch_spine_lower", Vector((0.14, -0.03, 0.62)), Vector((0.10, -0.07, 0.45)), "spine_01", True),
        ("carrier_root", Vector((0.16, 0.03, 0.55)), Vector((0.16, 0.03, 0.68)), "spine_02", True),
        ("carrier_top", Vector((0.16, 0.02, 0.86)), Vector((0.16, 0.02, 1.02)), "carrier_root", True),
        ("carrier_side_l", Vector((-0.02, 0.02, 0.78)), Vector((-0.04, 0.02, 0.30)), "carrier_root", True),
        ("carrier_side_r", Vector((0.34, 0.02, 0.78)), Vector((0.36, 0.02, 0.30)), "carrier_root", True),
        ("strip_front_l", Vector((0.05, -0.20, 0.64)), Vector((0.04, -0.24, 0.08)), "carrier_root", True),
        ("strip_front_c", Vector((0.16, -0.23, 0.68)), Vector((0.16, -0.27, 0.02)), "carrier_root", True),
        ("strip_front_r", Vector((0.28, -0.20, 0.64)), Vector((0.30, -0.24, 0.08)), "carrier_root", True),
        ("strip_back_l", Vector((0.05, 0.13, 0.68)), Vector((0.04, 0.16, 0.02)), "carrier_root", True),
        ("strip_back_r", Vector((0.28, 0.13, 0.68)), Vector((0.30, 0.16, 0.02)), "carrier_root", True),
        ("bell_l", Vector((-0.02, -0.08, 0.28)), Vector((-0.07, -0.12, 0.08)), "hand_l", True),
    ]
    for spec in specs:
        if make_bone(eb, *spec):
            created.append(spec[0])
    bpy.ops.object.mode_set(mode="OBJECT")
    return created


def sync_deform_groups(mesh: bpy.types.Object | None, armature: bpy.types.Object) -> None:
    if not mesh:
        return
    deform_names = {bone.name for bone in armature.data.bones if bone.use_deform}
    for group in list(mesh.vertex_groups):
        if group.name not in deform_names and group.name not in {"pelvis", "root"}:
            continue
    existing = {group.name for group in mesh.vertex_groups}
    for name in sorted(deform_names):
        if name not in existing:
            mesh.vertex_groups.new(name=name)


def clear_pose(armature: bpy.types.Object) -> None:
    set_pose_mode(armature)
    for bone in armature.pose.bones:
        bone.rotation_mode = "XYZ"
        bone.location = (0.0, 0.0, 0.0)
        bone.rotation_euler = (0.0, 0.0, 0.0)
        bone.scale = (1.0, 1.0, 1.0)


def key_bone(armature: bpy.types.Object, name: str, frame: int, rot=(0.0, 0.0, 0.0), loc=(0.0, 0.0, 0.0)) -> None:
    bone = armature.pose.bones.get(name)
    if not bone:
        return
    bone.rotation_mode = "XYZ"
    bone.rotation_euler = rot
    bone.location = loc
    bone.keyframe_insert("rotation_euler", frame=frame)
    bone.keyframe_insert("location", frame=frame)


def add_player_walk(armature: bpy.types.Object) -> str:
    clear_pose(armature)
    action = bpy.data.actions.new("AN_Player_CautiousWalk_32f")
    armature.animation_data_create()
    armature.animation_data.action = action
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 32
    frames = [
        (1, 0.26, -0.22, -0.18, 0.18, -0.10),
        (9, 0.00, 0.00, 0.00, 0.00, 0.02),
        (17, -0.26, 0.22, 0.18, -0.18, -0.10),
        (25, 0.00, 0.00, 0.00, 0.00, 0.02),
        (32, 0.26, -0.22, -0.18, 0.18, -0.10),
    ]
    for frame, leg_l, leg_r, arm_l, arm_r, root_z in frames:
        key_bone(armature, "root", frame, loc=(0.0, 0.0, root_z))
        key_bone(armature, "pelvis", frame, rot=(0.0, 0.04 if leg_l > 0 else -0.04, 0.0))
        key_bone(armature, "spine_01", frame, rot=(0.03, 0.0, 0.02 if leg_l > 0 else -0.02))
        key_bone(armature, "thigh_l", frame, rot=(leg_l, 0.0, 0.0))
        key_bone(armature, "thigh_r", frame, rot=(leg_r, 0.0, 0.0))
        key_bone(armature, "calf_l", frame, rot=(-0.18 if leg_l < 0 else 0.08, 0.0, 0.0))
        key_bone(armature, "calf_r", frame, rot=(-0.18 if leg_r < 0 else 0.08, 0.0, 0.0))
        key_bone(armature, "foot_l", frame, rot=(-0.10 if leg_l > 0 else 0.08, 0.0, 0.0))
        key_bone(armature, "foot_r", frame, rot=(-0.10 if leg_r > 0 else 0.08, 0.0, 0.0))
        key_bone(armature, "upperarm_l", frame, rot=(arm_l, 0.0, 0.0))
        key_bone(armature, "upperarm_r", frame, rot=(arm_r, 0.0, 0.0))
        key_bone(armature, "lowerarm_l", frame, rot=(0.08, 0.0, 0.0))
        key_bone(armature, "lowerarm_r", frame, rot=(0.08, 0.0, 0.0))
        key_bone(armature, "head", frame, rot=(0.02, 0.0, 0.0))
        key_bone(armature, "jacket_front_l", frame, rot=(0.04 if leg_l > 0 else -0.02, 0.0, 0.0))
        key_bone(armature, "jacket_front_r", frame, rot=(0.04 if leg_r > 0 else -0.02, 0.0, 0.0))
    action.use_cyclic = True
    return action.name


def add_penance_walk(armature: bpy.types.Object) -> str:
    clear_pose(armature)
    action = bpy.data.actions.new("AN_Penance_HunchedStalk_48f")
    armature.animation_data_create()
    armature.animation_data.action = action
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 48
    frames = [
        (1, 0.18, -0.16, 0.10, -0.08, -0.04),
        (13, 0.04, -0.03, -0.04, 0.03, 0.03),
        (25, -0.18, 0.16, -0.10, 0.08, -0.04),
        (37, -0.03, 0.04, 0.04, -0.03, 0.03),
        (48, 0.18, -0.16, 0.10, -0.08, -0.04),
    ]
    for frame, leg_l, leg_r, arm_l, arm_r, root_z in frames:
        key_bone(armature, "root", frame, loc=(0.0, 0.0, root_z))
        key_bone(armature, "pelvis", frame, rot=(0.10, 0.0, 0.02 if leg_l > 0 else -0.02))
        key_bone(armature, "spine_01", frame, rot=(0.22, 0.0, 0.04 if leg_l > 0 else -0.04))
        key_bone(armature, "spine_02", frame, rot=(0.28, 0.0, 0.03 if leg_l > 0 else -0.03))
        key_bone(armature, "head", frame, rot=(0.30, 0.0, 0.0))
        key_bone(armature, "thigh_l", frame, rot=(leg_l, 0.0, 0.0))
        key_bone(armature, "thigh_r", frame, rot=(leg_r, 0.0, 0.0))
        key_bone(armature, "calf_l", frame, rot=(-0.10 if leg_l < 0 else 0.04, 0.0, 0.0))
        key_bone(armature, "calf_r", frame, rot=(-0.10 if leg_r < 0 else 0.04, 0.0, 0.0))
        key_bone(armature, "upperarm_l", frame, rot=(arm_l, 0.0, -0.08))
        key_bone(armature, "upperarm_r", frame, rot=(arm_r, 0.0, 0.08))
        key_bone(armature, "lowerarm_l", frame, rot=(0.18, 0.0, 0.0))
        key_bone(armature, "lowerarm_r", frame, rot=(0.16, 0.0, 0.0))
        key_bone(armature, "bell_l", frame, rot=(0.18 if leg_l > 0 else -0.18, 0.0, 0.06))
        key_bone(armature, "strip_front_c", frame, rot=(-0.08 if leg_l > 0 else 0.08, 0.0, 0.0))
        key_bone(armature, "strip_front_l", frame, rot=(-0.06 if leg_l > 0 else 0.06, 0.0, -0.03))
        key_bone(armature, "strip_front_r", frame, rot=(-0.06 if leg_r > 0 else 0.06, 0.0, 0.03))
        key_bone(armature, "carrier_top", frame, rot=(0.02, 0.0, 0.03 if leg_l > 0 else -0.03))
    action.use_cyclic = True
    return action.name


def write_report(
    path: Path,
    kind: str,
    src: Path,
    armature: bpy.types.Object,
    mesh: bpy.types.Object | None,
    removed: list[str],
    created: list[str],
    action_name: str,
) -> None:
    deform = [bone.name for bone in armature.data.bones if bone.use_deform]
    helpers = [bone.name for bone in armature.data.bones if not bone.use_deform]
    lines = [
        "MODEL_ADAPTED_CONTROLS_AND_WALK_REPORT",
        f"Kind: {kind}",
        f"Blend: {src}",
        f"Armature: {armature.name}",
        f"Total bones: {len(armature.data.bones)}",
        f"Deform bones: {len(deform)}",
        f"Helper/non-deform bones: {len(helpers)}",
        f"Removed controls: {', '.join(removed) if removed else 'none'}",
        f"Created controls: {', '.join(created) if created else 'none'}",
        f"Walk action: {action_name}",
        f"Mesh: {mesh.name if mesh else 'none'}",
        f"Vertex groups: {len(mesh.vertex_groups) if mesh else 0}",
        "Deform bone names:",
        ", ".join(deform),
        "Helper/non-deform bone names:",
        ", ".join(helpers),
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    kind, src, report = args_after_separator()
    bpy.ops.wm.open_mainfile(filepath=str(src))
    for scene in bpy.data.scenes:
        try:
            scene.render.engine = "BLENDER_WORKBENCH"
        except Exception:
            pass
    armature = first_armature()
    mesh = first_mesh()
    if kind == "player":
        removed = remove_bones_and_groups(armature, mesh, PLAYER_REMOVE)
        created = add_player_controls(armature)
        sync_deform_groups(mesh, armature)
        action_name = add_player_walk(armature)
    else:
        removed = remove_bones_and_groups(armature, mesh, PENANCE_REMOVE)
        created = add_penance_controls(armature)
        sync_deform_groups(mesh, armature)
        action_name = add_penance_walk(armature)
    bpy.ops.object.mode_set(mode="OBJECT") if bpy.ops.object.mode_set.poll() else None
    write_report(report, kind, src, armature, mesh, removed, created, action_name)
    bpy.ops.wm.save_as_mainfile(filepath=str(src))
    print(f"ADAPTED_MODEL_CONTROLS_AND_WALK: {src}")
    os._exit(0)


main()
