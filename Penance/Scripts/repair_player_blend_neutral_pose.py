"""Repair Player.blend so it opens with the mesh/armature aligned.

This does not touch Unreal assets. It clears saved pose/action state from the
armatures, keeps the authored actions in the file, and saves the visible player
in a neutral bind-compatible pose.
"""

from __future__ import annotations

import sys
from pathlib import Path

import bpy
from mathutils import Vector

from penance_script_safety import filtered_script_args, require_asset_write_permission


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BLEND = PROJECT_ROOT / "Content" / "Player" / "Player.blend"
DEFAULT_REPORT = PROJECT_ROOT / "Saved" / "PlayerBlendNeutralPoseRepairReport.txt"
MESH_NAME = "Mesh_0"
RIG_NAME = "RIG_Player_Rigify_Humanoid_IK"


def args_after_separator() -> tuple[Path, Path]:
    args = filtered_script_args(sys.argv[sys.argv.index("--") + 1 :]) if "--" in sys.argv else []
    src = Path(args[0]).expanduser().resolve() if args else DEFAULT_BLEND
    report = Path(args[1]).expanduser().resolve() if len(args) > 1 else DEFAULT_REPORT
    if not src.exists():
        raise SystemExit(f"Blend file does not exist: {src}")
    report.parent.mkdir(parents=True, exist_ok=True)
    return src, report


def bounds_from_points(points: list[Vector]) -> tuple[Vector, Vector]:
    return (
        Vector((min(v.x for v in points), min(v.y for v in points), min(v.z for v in points))),
        Vector((max(v.x for v in points), max(v.y for v in points), max(v.z for v in points))),
    )


def mesh_bounds(obj: bpy.types.Object, evaluated: bool) -> tuple[Vector, Vector]:
    if evaluated:
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = obj.evaluated_get(depsgraph)
        data = eval_obj.to_mesh()
        points = [eval_obj.matrix_world @ vertex.co for vertex in data.vertices]
        eval_obj.to_mesh_clear()
    else:
        points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    return bounds_from_points(points)


def clear_armature_pose(armature: bpy.types.Object) -> int:
    if armature.animation_data:
        armature.animation_data.action = None
    armature.data.pose_position = "POSE"
    changed = 0
    for bone in armature.pose.bones:
        bone.rotation_mode = "XYZ"
        if bone.location.length > 0.0:
            changed += 1
        bone.location = (0.0, 0.0, 0.0)
        if abs(bone.rotation_euler.x) + abs(bone.rotation_euler.y) + abs(bone.rotation_euler.z) > 0.0:
            changed += 1
        bone.rotation_euler = (0.0, 0.0, 0.0)
        if (Vector(bone.scale) - Vector((1.0, 1.0, 1.0))).length > 0.0:
            changed += 1
        bone.scale = (1.0, 1.0, 1.0)
    return changed


def main() -> None:
    src, report = args_after_separator()
    require_asset_write_permission(f"repair and save neutral pose in {src}")
    bpy.ops.wm.open_mainfile(filepath=str(src), load_ui=False)
    bpy.context.scene.frame_set(1)

    mesh = bpy.data.objects.get(MESH_NAME)
    rig = bpy.data.objects.get(RIG_NAME)
    if not mesh or mesh.type != "MESH":
        raise SystemExit(f"Missing mesh: {MESH_NAME}")
    if not rig or rig.type != "ARMATURE":
        raise SystemExit(f"Missing rig: {RIG_NAME}")

    raw_before_min, raw_before_max = mesh_bounds(mesh, evaluated=False)
    eval_before_min, eval_before_max = mesh_bounds(mesh, evaluated=True)

    changed_pose_channels = 0
    cleared_armatures: list[str] = []
    for obj in bpy.data.objects:
        if obj.type != "ARMATURE":
            continue
        changed_pose_channels += clear_armature_pose(obj)
        cleared_armatures.append(obj.name)

    mesh.hide_viewport = False
    mesh.hide_render = False
    mesh.hide_set(False)
    rig.hide_viewport = False
    rig.hide_render = False
    rig.hide_set(False)

    for modifier in mesh.modifiers:
        if modifier.type == "ARMATURE":
            modifier.object = rig
            modifier.show_viewport = True
            modifier.show_render = True

    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()

    raw_after_min, raw_after_max = mesh_bounds(mesh, evaluated=False)
    eval_after_min, eval_after_max = mesh_bounds(mesh, evaluated=True)
    actions = sorted(action.name for action in bpy.data.actions if action.name.startswith("AN_Player_"))

    def fmt(min_v: Vector, max_v: Vector) -> str:
        return (
            f"min=({min_v.x:.4f},{min_v.y:.4f},{min_v.z:.4f}) "
            f"max=({max_v.x:.4f},{max_v.y:.4f},{max_v.z:.4f}) "
            f"size=({max_v.x - min_v.x:.4f},{max_v.y - min_v.y:.4f},{max_v.z - min_v.z:.4f})"
        )

    lines = [
        "PLAYER_BLEND_NEUTRAL_POSE_REPAIR_REPORT",
        f"Blend: {src}",
        f"Mesh: {mesh.name}",
        f"Rig: {rig.name}",
        f"Cleared armatures: {', '.join(cleared_armatures)}",
        f"Changed pose channels: {changed_pose_channels}",
        f"Mesh parent: {mesh.parent.name if mesh.parent else 'none'}",
        f"Mesh visible: hide_get={mesh.hide_get()} hide_viewport={mesh.hide_viewport} hide_render={mesh.hide_render}",
        f"Rig active action after repair: {rig.animation_data.action.name if rig.animation_data and rig.animation_data.action else 'none'}",
        f"Raw before: {fmt(raw_before_min, raw_before_max)}",
        f"Evaluated before: {fmt(eval_before_min, eval_before_max)}",
        f"Raw after: {fmt(raw_after_min, raw_after_max)}",
        f"Evaluated after: {fmt(eval_after_min, eval_after_max)}",
        f"Actions preserved: {len(actions)}",
        ", ".join(actions),
    ]

    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(src))
    print("\n".join(lines))


main()
