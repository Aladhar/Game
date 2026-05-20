"""Report bounds and membership for important Blender vertex groups."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def args_after_separator() -> tuple[Path, Path]:
    if "--" not in sys.argv:
        raise SystemExit("Expected arguments after --: SRC.blend REPORT.txt")
    args = sys.argv[sys.argv.index("--") + 1 :]
    if len(args) != 2:
        raise SystemExit("Expected arguments after --: SRC.blend REPORT.txt")
    src = Path(args[0]).expanduser().resolve()
    report = Path(args[1]).expanduser().resolve()
    report.parent.mkdir(parents=True, exist_ok=True)
    return src, report


def character_mesh() -> bpy.types.Object:
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and len(obj.data.vertices) > 100]
    if not meshes:
        raise SystemExit("No character mesh found")
    return max(meshes, key=lambda obj: len(obj.data.vertices))


def group_indices(mesh: bpy.types.Object, group_name: str, min_weight: float = 0.01) -> list[int]:
    group = mesh.vertex_groups.get(group_name)
    if not group:
        return []
    indices: list[int] = []
    for vertex in mesh.data.vertices:
        for assignment in vertex.groups:
            if assignment.group == group.index and assignment.weight >= min_weight:
                indices.append(vertex.index)
                break
    return indices


def world_bounds(mesh: bpy.types.Object, indices: list[int]) -> str:
    if not indices:
        return "none"
    points = [mesh.matrix_world @ mesh.data.vertices[index].co for index in indices]
    min_v = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    max_v = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return f"min=({min_v.x:.5f},{min_v.y:.5f},{min_v.z:.5f}) max=({max_v.x:.5f},{max_v.y:.5f},{max_v.z:.5f})"


def main() -> None:
    src, report = args_after_separator()
    bpy.ops.wm.open_mainfile(filepath=str(src))
    mesh = character_mesh()
    groups = [
        "foot_l",
        "foot_r",
        "calf_l",
        "calf_r",
        "thigh_l",
        "thigh_r",
        "strip_front_l",
        "strip_front_c",
        "strip_front_r",
        "strip_back_l",
        "strip_back_r",
        "carrier_root",
        "bell_l",
    ]
    lines = ["VERTEX_GROUP_INSPECTION", f"Blend: {src}", f"Mesh: {mesh.name}"]
    for group_name in groups:
        indices = group_indices(mesh, group_name)
        lines.append(f"{group_name}: count={len(indices)} {world_bounds(mesh, indices)}")
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"WROTE_VERTEX_GROUP_REPORT: {report}")
    os._exit(0)


main()
