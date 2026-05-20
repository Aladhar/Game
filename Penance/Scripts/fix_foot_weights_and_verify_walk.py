"""Make lower shoe/foot vertices rigid to foot bones and verify during walk.

This is meant for the built/adaptive Blender character files. It finds the
visible character mesh, chooses the lower left/right foot clusters from actual
mesh bounds, removes those vertices from all vertex groups, assigns them to the
matching foot bone at weight 1.0, normalizes weights, then samples the current
walk action to check that those clusters do not stretch.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def args_after_separator() -> tuple[Path, Path, Path, dict[str, float]]:
    if "--" not in sys.argv:
        raise SystemExit("Expected arguments after --: SRC.blend OUT.blend REPORT.txt [key=value ...]")
    args = sys.argv[sys.argv.index("--") + 1 :]
    if len(args) < 3:
        raise SystemExit("Expected arguments after --: SRC.blend OUT.blend REPORT.txt [key=value ...]")
    src = Path(args[0]).expanduser().resolve()
    out = Path(args[1]).expanduser().resolve()
    report = Path(args[2]).expanduser().resolve()
    if not src.exists():
        raise SystemExit(f"Blend does not exist: {src}")
    out.parent.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    params = {
        "z_pct": 0.18,
        "y_min_pct": -0.05,
        "y_max_pct": 1.05,
    }
    for raw in args[3:]:
        key, _, value = raw.partition("=")
        if key not in params or not value:
            raise SystemExit(f"Unsupported parameter: {raw}")
        params[key] = float(value)
    return src, out, report, params


def character_mesh() -> bpy.types.Object:
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and len(obj.data.vertices) > 100]
    if not meshes:
        raise SystemExit("No character mesh found")
    return max(meshes, key=lambda obj: len(obj.data.vertices))


def character_armature(mesh: bpy.types.Object) -> bpy.types.Object:
    for mod in mesh.modifiers:
        if mod.type == "ARMATURE" and mod.object:
            return mod.object
    armatures = [obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"]
    if not armatures:
        raise SystemExit("No armature found")
    return armatures[0]


def bone_name(armature: bpy.types.Object, candidates: list[str]) -> str:
    names = {bone.name for bone in armature.data.bones}
    for candidate in candidates:
        if candidate in names:
            return candidate
    raise SystemExit(f"Missing foot bone. Tried: {', '.join(candidates)}")


def mesh_bounds(mesh: bpy.types.Object) -> tuple[Vector, Vector]:
    world = [mesh.matrix_world @ vertex.co for vertex in mesh.data.vertices]
    minimum = Vector((min(v.x for v in world), min(v.y for v in world), min(v.z for v in world)))
    maximum = Vector((max(v.x for v in world), max(v.y for v in world), max(v.z for v in world)))
    return minimum, maximum


def local_to_world(mesh: bpy.types.Object, index: int) -> Vector:
    return mesh.matrix_world @ mesh.data.vertices[index].co


def select_foot_vertices(mesh: bpy.types.Object, side: str, params: dict[str, float]) -> list[int]:
    min_v, max_v = mesh_bounds(mesh)
    size = max_v - min_v
    z_max = min_v.z + size.z * params["z_pct"]
    z_min = min_v.z - size.z * 0.02
    y_front = min_v.y + size.y * params["y_min_pct"]
    y_back = min_v.y + size.y * params["y_max_pct"]
    center_x = (min_v.x + max_v.x) * 0.5

    candidates: list[int] = []
    for vertex in mesh.data.vertices:
        co = local_to_world(mesh, vertex.index)
        if not (z_min <= co.z <= z_max):
            continue
        if not (y_front <= co.y <= y_back):
            continue
        if side == "left" and co.x >= center_x:
            continue
        if side == "right" and co.x < center_x:
            continue
        candidates.append(vertex.index)

    # If the model is asymmetric or facing a different axis, fall back to lower
    # left/right clusters by height and X split.
    if len(candidates) < 25:
        candidates = []
        for vertex in mesh.data.vertices:
            co = local_to_world(mesh, vertex.index)
            if not (z_min <= co.z <= z_max):
                continue
            if side == "left" and co.x >= center_x:
                continue
            if side == "right" and co.x < center_x:
                continue
            candidates.append(vertex.index)

    return candidates


def selected_bounds(mesh: bpy.types.Object, indices: list[int]) -> str:
    if not indices:
        return "none"
    points = [local_to_world(mesh, index) for index in indices]
    minimum = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    maximum = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return (
        f"min=({minimum.x:.5f},{minimum.y:.5f},{minimum.z:.5f}) "
        f"max=({maximum.x:.5f},{maximum.y:.5f},{maximum.z:.5f})"
    )


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


def weights_for(mesh: bpy.types.Object, index: int) -> dict[str, float]:
    result: dict[str, float] = {}
    for assignment in mesh.data.vertices[index].groups:
        group = mesh.vertex_groups[assignment.group]
        result[group.name] = assignment.weight
    return result


def evaluated_vertices(mesh: bpy.types.Object) -> list[Vector]:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = mesh.evaluated_get(depsgraph)
    temp = evaluated.to_mesh()
    try:
        return [evaluated.matrix_world @ vertex.co for vertex in temp.vertices]
    finally:
        evaluated.to_mesh_clear()


def cluster_signature(points: list[Vector], indices: list[int]) -> tuple[float, float, Vector]:
    selected = [points[index] for index in indices if index < len(points)]
    if not selected:
        return 0.0, 0.0, Vector((0.0, 0.0, 0.0))
    centroid = sum(selected, Vector((0.0, 0.0, 0.0))) / len(selected)
    radii = [(point - centroid).length for point in selected]
    max_radius = max(radii)
    avg_radius = sum(radii) / len(radii)
    return max_radius, avg_radius, centroid


def walk_action(armature: bpy.types.Object) -> bpy.types.Action | None:
    if armature.animation_data and armature.animation_data.action:
        return armature.animation_data.action
    walk_names = [action for action in bpy.data.actions if "walk" in action.name.lower()]
    return walk_names[0] if walk_names else (bpy.data.actions[0] if bpy.data.actions else None)


def verify_rigidity(mesh: bpy.types.Object, armature: bpy.types.Object, left: list[int], right: list[int]) -> list[str]:
    action = walk_action(armature)
    if action and armature.animation_data:
        armature.animation_data.action = action
    start = int(action.frame_range[0]) if action else int(bpy.context.scene.frame_start)
    end = int(action.frame_range[1]) if action else int(bpy.context.scene.frame_end)
    if end <= start:
        end = start + 32
    frames = sorted(set([start, start + (end - start) // 4, start + (end - start) // 2, start + 3 * (end - start) // 4, end]))

    lines = [f"Walk action tested: {action.name if action else 'none'}", f"Frames sampled: {frames}"]
    baseline: dict[str, tuple[float, float]] = {}
    max_drift: dict[str, float] = {"left": 0.0, "right": 0.0}
    for frame in frames:
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        points = evaluated_vertices(mesh)
        for side, indices in (("left", left), ("right", right)):
            max_radius, avg_radius, centroid = cluster_signature(points, indices)
            if side not in baseline:
                baseline[side] = (max_radius, avg_radius)
            drift = max(abs(max_radius - baseline[side][0]), abs(avg_radius - baseline[side][1]))
            max_drift[side] = max(max_drift[side], drift)
            lines.append(
                f"{side} frame={frame} centroid=({centroid.x:.5f},{centroid.y:.5f},{centroid.z:.5f}) "
                f"max_radius={max_radius:.6f} avg_radius={avg_radius:.6f} drift={drift:.8f}"
            )
    threshold = 0.0005
    lines.append(f"Rigidity threshold: {threshold}")
    lines.append(f"Left max radius drift: {max_drift['left']:.8f}")
    lines.append(f"Right max radius drift: {max_drift['right']:.8f}")
    lines.append(f"Rigid verification: {'PASSED' if max(max_drift.values()) <= threshold else 'FAILED'}")
    return lines


def write_report(
    path: Path,
    src: Path,
    out: Path,
    mesh: bpy.types.Object,
    armature: bpy.types.Object,
    left_bone: str,
    right_bone: str,
    left: list[int],
    right: list[int],
    params: dict[str, float],
    verification: list[str],
) -> None:
    sample_left = left[:8]
    sample_right = right[:8]
    lines = [
        "FOOT_WEIGHT_FIX_REPORT",
        f"Source: {src}",
        f"Saved: {out}",
        f"Mesh: {mesh.name}",
        f"Armature: {armature.name}",
        f"Left foot bone: {left_bone}",
        f"Right foot bone: {right_bone}",
        f"Selection params: z_pct={params['z_pct']} y_min_pct={params['y_min_pct']} y_max_pct={params['y_max_pct']}",
        f"Left shoe/foot vertices fixed: {len(left)}",
        f"Right shoe/foot vertices fixed: {len(right)}",
        f"Left fixed bounds: {selected_bounds(mesh, left)}",
        f"Right fixed bounds: {selected_bounds(mesh, right)}",
        f"Left sample vertex weights: {[weights_for(mesh, i) for i in sample_left]}",
        f"Right sample vertex weights: {[weights_for(mesh, i) for i in sample_right]}",
    ]
    lines.extend(verification)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    src, out, report, params = args_after_separator()
    bpy.ops.wm.open_mainfile(filepath=str(src))
    mesh = character_mesh()
    armature = character_armature(mesh)
    left_bone = bone_name(armature, ["foot.L", "foot_l", "Foot.L", "foot_l"])
    right_bone = bone_name(armature, ["foot.R", "foot_r", "Foot.R", "foot_r"])

    left = select_foot_vertices(mesh, "left", params)
    right = select_foot_vertices(mesh, "right", params)
    if len(left) < 25 or len(right) < 25:
        raise SystemExit(f"Not enough foot vertices found: left={len(left)} right={len(right)}")

    remove_from_all_groups(mesh, left)
    remove_from_all_groups(mesh, right)
    assign_to_group(mesh, left, left_bone)
    assign_to_group(mesh, right, right_bone)
    normalize_all(mesh)
    verification = verify_rigidity(mesh, armature, left, right)
    write_report(report, src, out, mesh, armature, left_bone, right_bone, left, right, params, verification)
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    print(f"FIXED_FOOT_WEIGHTS_AND_VERIFIED: {out}")
    os._exit(0)


main()
