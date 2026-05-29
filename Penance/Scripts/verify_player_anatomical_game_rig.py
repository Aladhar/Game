"""Verify Player.blend's anatomical rig and Mesh_0 deformation samples."""

from __future__ import annotations

import sys
from pathlib import Path

import bpy
from mathutils import Vector


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BLEND = PROJECT_ROOT / "Content" / "Player" / "Player.blend"
DEFAULT_REPORT = PROJECT_ROOT / "Saved" / "PlayerAnatomicalGameRigVerification.txt"
MESH_NAME = "Mesh_0"
RIG_NAME = "ARM_Player_Anatomical_Game_Rig"


def args_after_separator() -> tuple[Path, Path]:
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    src = Path(args[0]).expanduser().resolve() if args else DEFAULT_BLEND
    report = Path(args[1]).expanduser().resolve() if len(args) > 1 else DEFAULT_REPORT
    report.parent.mkdir(parents=True, exist_ok=True)
    return src, report


def bounds(obj: bpy.types.Object, evaluated: bool) -> tuple[Vector, Vector]:
    if evaluated:
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = obj.evaluated_get(depsgraph)
        data = eval_obj.to_mesh()
        points = [eval_obj.matrix_world @ vertex.co for vertex in data.vertices]
        eval_obj.to_mesh_clear()
    else:
        points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    return (
        Vector((min(v.x for v in points), min(v.y for v in points), min(v.z for v in points))),
        Vector((max(v.x for v in points), max(v.y for v in points), max(v.z for v in points))),
    )


def fmt(min_v: Vector, max_v: Vector) -> str:
    s = max_v - min_v
    return f"min=({min_v.x:.4f},{min_v.y:.4f},{min_v.z:.4f}) max=({max_v.x:.4f},{max_v.y:.4f},{max_v.z:.4f}) size=({s.x:.4f},{s.y:.4f},{s.z:.4f})"


def clear_pose(rig: bpy.types.Object) -> None:
    if rig.animation_data:
        rig.animation_data.action = None
    for bone in rig.pose.bones:
        bone.rotation_mode = "XYZ"
        bone.location = (0.0, 0.0, 0.0)
        bone.rotation_euler = (0.0, 0.0, 0.0)
        bone.scale = (1.0, 1.0, 1.0)


def weighted_vertex_count(mesh: bpy.types.Object) -> int:
    return sum(1 for vertex in mesh.data.vertices if vertex.groups)


def max_vertex_influences(mesh: bpy.types.Object) -> int:
    return max((len(vertex.groups) for vertex in mesh.data.vertices), default=0)


def main() -> None:
    src, report = args_after_separator()
    bpy.ops.wm.open_mainfile(filepath=str(src), load_ui=False)
    mesh = bpy.data.objects.get(MESH_NAME)
    rig = bpy.data.objects.get(RIG_NAME)
    if not mesh or mesh.type != "MESH":
        raise SystemExit(f"Missing mesh: {MESH_NAME}")
    if not rig or rig.type != "ARMATURE":
        raise SystemExit(f"Missing rig: {RIG_NAME}")

    clear_pose(rig)
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    raw_min, raw_max = bounds(mesh, False)
    neutral_min, neutral_max = bounds(mesh, True)
    raw_size = raw_max - raw_min
    neutral_delta = ((neutral_max - neutral_min) - raw_size).length

    lines = [
        "PLAYER_ANATOMICAL_GAME_RIG_VERIFICATION",
        f"Blend: {src}",
        f"Mesh: {mesh.name}",
        f"Rig: {rig.name}",
        f"Mesh parent: {mesh.parent.name if mesh.parent else 'none'}",
        f"Armature modifier target: {next((m.object.name for m in mesh.modifiers if m.type == 'ARMATURE' and m.object), 'none')}",
        f"Weighted vertices: {weighted_vertex_count(mesh)} / {len(mesh.data.vertices)}",
        f"Max stored influences per vertex: {max_vertex_influences(mesh)}",
        f"Neutral raw: {fmt(raw_min, raw_max)}",
        f"Neutral evaluated: {fmt(neutral_min, neutral_max)}",
        f"Neutral size delta length: {neutral_delta:.8f}",
        "Sampled action deformation sizes:",
    ]

    worst_size_delta = neutral_delta
    worst_action = "neutral"
    actions = sorted([action for action in bpy.data.actions if action.name.startswith("AN_Player_")], key=lambda action: action.name)
    for action in actions:
        rig.animation_data_create()
        rig.animation_data.action = action
        start, end = action.frame_range
        sample_frames = sorted({int(start), int((start + end) / 2), int(end)})
        max_size = Vector((0.0, 0.0, 0.0))
        min_z = 9999.0
        for frame in sample_frames:
            bpy.context.scene.frame_set(frame)
            bpy.context.view_layer.update()
            mn, mx = bounds(mesh, True)
            s = mx - mn
            max_size.x = max(max_size.x, s.x)
            max_size.y = max(max_size.y, s.y)
            max_size.z = max(max_size.z, s.z)
            min_z = min(min_z, mn.z)
        delta = (max_size - raw_size).length
        if delta > worst_size_delta:
            worst_size_delta = delta
            worst_action = action.name
        lines.append(
            f"- {action.name}: frames={sample_frames} max_size=({max_size.x:.4f},{max_size.y:.4f},{max_size.z:.4f}) "
            f"size_delta={delta:.4f} min_z={min_z:.4f}"
        )

    clear_pose(rig)
    bpy.context.scene.frame_set(1)
    lines.append(f"Worst sampled size delta: {worst_size_delta:.4f} action={worst_action}")
    lines.append("Result: PASS" if neutral_delta < 0.001 and weighted_vertex_count(mesh) == len(mesh.data.vertices) else "Result: FAIL")
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


main()
