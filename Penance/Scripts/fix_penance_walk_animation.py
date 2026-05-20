"""Fix Penance foot weighting and replace walk with a grounded stalk cycle."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def args_after_separator() -> tuple[Path, Path, Path]:
    if "--" not in sys.argv:
        raise SystemExit("Expected -- SRC.blend OUT.blend REPORT.txt")
    args = sys.argv[sys.argv.index("--") + 1 :]
    if len(args) != 3:
        raise SystemExit("Expected -- SRC.blend OUT.blend REPORT.txt")
    src = Path(args[0]).resolve()
    out = Path(args[1]).resolve()
    report = Path(args[2]).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    return src, out, report


def character_mesh() -> bpy.types.Object:
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and len(obj.data.vertices) > 100]
    return max(meshes, key=lambda obj: len(obj.data.vertices))


def character_armature() -> bpy.types.Object:
    return next(obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE")


def world_vertices(mesh: bpy.types.Object) -> list[Vector]:
    return [mesh.matrix_world @ vertex.co for vertex in mesh.data.vertices]


def bounds(points: list[Vector]) -> tuple[Vector, Vector]:
    return (
        Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points))),
        Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points))),
    )


def select_actual_foot(mesh: bpy.types.Object, armature: bpy.types.Object, side: str) -> list[int]:
    points = world_vertices(mesh)
    min_v, max_v = bounds(points)
    size = max_v - min_v
    bone_name = "foot_l" if side == "left" else "foot_r"
    bone = armature.data.bones[bone_name]
    foot_head = armature.matrix_world @ bone.head_local

    # Penance's mesh is asymmetric and covered in hanging strips; constrain by
    # proximity to the actual foot bone and very low height to avoid robe strips.
    z_min = min_v.z - size.z * 0.02
    z_max = min_v.z + size.z * 0.17
    x_radius = size.x * 0.30
    y_radius = size.y * 0.44
    indices: list[int] = []
    for index, point in enumerate(points):
        if not (z_min <= point.z <= z_max):
            continue
        if abs(point.x - foot_head.x) > x_radius:
            continue
        if abs(point.y - foot_head.y) > y_radius:
            continue
        # Avoid the center robe strips hanging between the legs.
        if side == "left" and point.x > 0.20:
            continue
        if side == "right" and point.x < 0.16:
            continue
        indices.append(index)
    return indices


def remove_from_all_groups(mesh: bpy.types.Object, indices: list[int]) -> None:
    for group in mesh.vertex_groups:
        try:
            group.remove(indices)
        except RuntimeError:
            pass


def assign_to_group(mesh: bpy.types.Object, indices: list[int], name: str) -> None:
    group = mesh.vertex_groups.get(name) or mesh.vertex_groups.new(name=name)
    group.add(indices, 1.0, "REPLACE")


def normalize_all(mesh: bpy.types.Object) -> None:
    bpy.ops.object.mode_set(mode="OBJECT") if bpy.ops.object.mode_set.poll() else None
    bpy.ops.object.select_all(action="DESELECT")
    mesh.select_set(True)
    bpy.context.view_layer.objects.active = mesh
    with bpy.context.temp_override(active_object=mesh, object=mesh, selected_objects=[mesh], selected_editable_objects=[mesh]):
        bpy.ops.object.vertex_group_normalize_all(group_select_mode="ALL", lock_active=False)


def set_pose_mode(armature: bpy.types.Object) -> None:
    bpy.ops.object.mode_set(mode="OBJECT") if bpy.ops.object.mode_set.poll() else None
    bpy.ops.object.select_all(action="DESELECT")
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    with bpy.context.temp_override(active_object=armature, object=armature, selected_objects=[armature], selected_editable_objects=[armature]):
        bpy.ops.object.mode_set(mode="POSE")


def clear_pose(armature: bpy.types.Object) -> None:
    set_pose_mode(armature)
    for bone in armature.pose.bones:
        bone.rotation_mode = "XYZ"
        bone.location = (0.0, 0.0, 0.0)
        bone.rotation_euler = (0.0, 0.0, 0.0)
        bone.scale = (1.0, 1.0, 1.0)


def key(armature: bpy.types.Object, name: str, frame: int, rot=(0.0, 0.0, 0.0), loc=(0.0, 0.0, 0.0)) -> None:
    bone = armature.pose.bones.get(name)
    if not bone:
        return
    bone.rotation_mode = "XYZ"
    bone.rotation_euler = rot
    bone.location = loc
    bone.keyframe_insert("rotation_euler", frame=frame)
    bone.keyframe_insert("location", frame=frame)


def replace_walk(armature: bpy.types.Object) -> str:
    clear_pose(armature)
    for action in list(bpy.data.actions):
        if action.name.startswith("AN_Penance_WalkFix") or action.name.startswith("AN_Penance_HunchedStalk"):
            bpy.data.actions.remove(action)

    action = bpy.data.actions.new("AN_Penance_WalkFix_GroundedStalk_64f")
    armature.animation_data_create()
    armature.animation_data.action = action
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 64

    frames = [
        (1, 0.10, -0.08, -0.04, 0.05, -0.015),
        (17, 0.02, -0.02, 0.02, -0.02, 0.010),
        (33, -0.10, 0.08, 0.04, -0.05, -0.015),
        (49, -0.02, 0.02, -0.02, 0.02, 0.010),
        (64, 0.10, -0.08, -0.04, 0.05, -0.015),
    ]
    for frame, thigh_l, thigh_r, arm_l, arm_r, root_z in frames:
        key(armature, "root", frame, loc=(0.0, 0.0, root_z))
        key(armature, "pelvis", frame, rot=(0.07, 0.0, 0.012 if thigh_l > 0 else -0.012))
        key(armature, "spine_01", frame, rot=(0.17, 0.0, 0.020 if thigh_l > 0 else -0.020))
        key(armature, "spine_02", frame, rot=(0.24, 0.0, 0.018 if thigh_l > 0 else -0.018))
        key(armature, "head", frame, rot=(0.25, 0.0, 0.0))

        key(armature, "thigh_l", frame, rot=(thigh_l, 0.0, 0.0))
        key(armature, "thigh_r", frame, rot=(thigh_r, 0.0, 0.0))
        key(armature, "calf_l", frame, rot=(-0.05 if thigh_l < 0 else 0.02, 0.0, 0.0))
        key(armature, "calf_r", frame, rot=(-0.05 if thigh_r < 0 else 0.02, 0.0, 0.0))
        key(armature, "foot_l", frame, rot=(-0.025 if thigh_l > 0 else 0.018, 0.0, 0.0))
        key(armature, "foot_r", frame, rot=(-0.025 if thigh_r > 0 else 0.018, 0.0, 0.0))

        key(armature, "upperarm_l", frame, rot=(arm_l, 0.0, -0.06))
        key(armature, "upperarm_r", frame, rot=(arm_r, 0.0, 0.06))
        key(armature, "lowerarm_l", frame, rot=(0.10, 0.0, 0.0))
        key(armature, "lowerarm_r", frame, rot=(0.10, 0.0, 0.0))
        key(armature, "bell_l", frame, rot=(0.12 if thigh_l > 0 else -0.12, 0.0, 0.04))

        # Keep the carrier heavy and slow, with secondary strip motion.
        key(armature, "carrier_root", frame, rot=(0.01, 0.0, 0.012 if thigh_l > 0 else -0.012))
        key(armature, "carrier_top", frame, rot=(0.015, 0.0, 0.018 if thigh_l > 0 else -0.018))
        key(armature, "strip_front_l", frame, rot=(-0.05 if thigh_l > 0 else 0.05, 0.0, -0.02))
        key(armature, "strip_front_c", frame, rot=(-0.06 if thigh_l > 0 else 0.06, 0.0, 0.0))
        key(armature, "strip_front_r", frame, rot=(-0.05 if thigh_r > 0 else 0.05, 0.0, 0.02))
        key(armature, "strip_back_l", frame, rot=(0.04 if thigh_l > 0 else -0.04, 0.0, 0.01))
        key(armature, "strip_back_r", frame, rot=(0.04 if thigh_r > 0 else -0.04, 0.0, -0.01))

    action.use_cyclic = True
    return action.name


def evaluated_points(mesh: bpy.types.Object) -> list[Vector]:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = mesh.evaluated_get(depsgraph)
    temp = evaluated.to_mesh()
    try:
        return [evaluated.matrix_world @ vertex.co for vertex in temp.vertices]
    finally:
        evaluated.to_mesh_clear()


def cluster_signature(points: list[Vector], indices: list[int]) -> tuple[float, float]:
    selected = [points[index] for index in indices]
    centroid = sum(selected, Vector((0.0, 0.0, 0.0))) / len(selected)
    radii = [(point - centroid).length for point in selected]
    return max(radii), sum(radii) / len(radii)


def verify(mesh: bpy.types.Object, left: list[int], right: list[int]) -> list[str]:
    frames = [1, 17, 33, 49, 64]
    baseline: dict[str, tuple[float, float]] = {}
    max_drift = {"left": 0.0, "right": 0.0}
    lines = [f"Frames sampled: {frames}"]
    for frame in frames:
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        points = evaluated_points(mesh)
        for side, indices in (("left", left), ("right", right)):
            signature = cluster_signature(points, indices)
            baseline.setdefault(side, signature)
            drift = max(abs(signature[0] - baseline[side][0]), abs(signature[1] - baseline[side][1]))
            max_drift[side] = max(max_drift[side], drift)
            lines.append(f"{side} frame={frame} max_radius={signature[0]:.6f} avg_radius={signature[1]:.6f} drift={drift:.8f}")
    threshold = 0.0005
    lines.append(f"Rigidity threshold: {threshold}")
    lines.append(f"Left max radius drift: {max_drift['left']:.8f}")
    lines.append(f"Right max radius drift: {max_drift['right']:.8f}")
    lines.append(f"Rigid foot verification: {'PASSED' if max(max_drift.values()) <= threshold else 'FAILED'}")
    return lines


def selected_bounds(mesh: bpy.types.Object, indices: list[int]) -> str:
    points = [mesh.matrix_world @ mesh.data.vertices[index].co for index in indices]
    min_v, max_v = bounds(points)
    return f"min=({min_v.x:.5f},{min_v.y:.5f},{min_v.z:.5f}) max=({max_v.x:.5f},{max_v.y:.5f},{max_v.z:.5f})"


def main() -> None:
    src, out, report = args_after_separator()
    bpy.ops.wm.open_mainfile(filepath=str(src))
    mesh = character_mesh()
    armature = character_armature()
    left = select_actual_foot(mesh, armature, "left")
    right = select_actual_foot(mesh, armature, "right")
    if len(left) < 100 or len(right) < 100:
        raise SystemExit(f"Too few foot vertices selected: left={len(left)} right={len(right)}")

    remove_from_all_groups(mesh, left)
    remove_from_all_groups(mesh, right)
    assign_to_group(mesh, left, "foot_l")
    assign_to_group(mesh, right, "foot_r")
    normalize_all(mesh)
    action = replace_walk(armature)
    verification = verify(mesh, left, right)

    lines = [
        "PENANCE_WALK_FIX_REPORT",
        f"Source: {src}",
        f"Saved: {out}",
        f"Action: {action}",
        f"Left actual-foot vertices fixed: {len(left)}",
        f"Right actual-foot vertices fixed: {len(right)}",
        f"Left bounds: {selected_bounds(mesh, left)}",
        f"Right bounds: {selected_bounds(mesh, right)}",
    ]
    lines.extend(verification)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    print(f"FIXED_PENANCE_WALK: {out}")
    os._exit(0)


main()
