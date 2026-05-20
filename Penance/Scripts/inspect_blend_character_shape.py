"""Generate simple shape reports and viewport renders for a Blender character."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def args_after_separator() -> tuple[Path, Path, Path]:
    if "--" not in sys.argv:
        raise SystemExit("Expected arguments after --: SRC.blend REPORT.txt IMAGE_PREFIX")
    args = sys.argv[sys.argv.index("--") + 1 :]
    if len(args) != 3:
        raise SystemExit("Expected arguments after --: SRC.blend REPORT.txt IMAGE_PREFIX")
    src = Path(args[0]).expanduser().resolve()
    report = Path(args[1]).expanduser().resolve()
    prefix = Path(args[2]).expanduser().resolve()
    if not src.exists():
        raise SystemExit(f"Source blend does not exist: {src}")
    report.parent.mkdir(parents=True, exist_ok=True)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    return src, report, prefix


def mesh_objects() -> list[bpy.types.Object]:
    return [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]


def armature_objects() -> list[bpy.types.Object]:
    return [obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"]


def mesh_world_vertices(mesh: bpy.types.Object) -> list[Vector]:
    return [mesh.matrix_world @ vertex.co for vertex in mesh.data.vertices]


def bounds(vertices: list[Vector]) -> tuple[Vector, Vector]:
    minimum = Vector((min(v.x for v in vertices), min(v.y for v in vertices), min(v.z for v in vertices)))
    maximum = Vector((max(v.x for v in vertices), max(v.y for v in vertices), max(v.z for v in vertices)))
    return minimum, maximum


def slice_widths(vertices: list[Vector], minimum: Vector, maximum: Vector) -> list[str]:
    lines: list[str] = []
    height = max(maximum.z - minimum.z, 0.001)
    for pct in (0.05, 0.12, 0.20, 0.32, 0.45, 0.58, 0.72, 0.86, 0.95):
        z = minimum.z + height * pct
        band = height * 0.025
        slice_vertices = [v for v in vertices if abs(v.z - z) <= band]
        if not slice_vertices:
            lines.append(f"z_pct={pct:.2f} vertices=0")
            continue
        min_v, max_v = bounds(slice_vertices)
        lines.append(
            f"z_pct={pct:.2f} vertices={len(slice_vertices)} "
            f"width_x={max_v.x - min_v.x:.4f} depth_y={max_v.y - min_v.y:.4f} "
            f"x=({min_v.x:.4f},{max_v.x:.4f}) y=({min_v.y:.4f},{max_v.y:.4f})"
        )
    return lines


def write_report(path: Path, src: Path) -> None:
    lines = [f"BLEND_CHARACTER_SHAPE_REPORT", f"Source: {src}"]
    arms = armature_objects()
    for armature in arms:
        deform = [bone.name for bone in armature.data.bones if bone.use_deform]
        helpers = [bone.name for bone in armature.data.bones if not bone.use_deform]
        lines.extend(
            [
                f"Armature: {armature.name}",
                f"Total bones: {len(armature.data.bones)}",
                f"Deform bones: {len(deform)}",
                f"Helper/non-deform bones: {len(helpers)}",
                f"Helper names: {', '.join(helpers) if helpers else 'none'}",
            ]
        )
    for mesh in mesh_objects():
        vertices = mesh_world_vertices(mesh)
        min_v, max_v = bounds(vertices)
        size = max_v - min_v
        group_names = [group.name for group in mesh.vertex_groups]
        lines.extend(
            [
                f"Mesh: {mesh.name}",
                f"Vertices: {len(vertices)}",
                f"Bounds min=({min_v.x:.4f},{min_v.y:.4f},{min_v.z:.4f}) max=({max_v.x:.4f},{max_v.y:.4f},{max_v.z:.4f})",
                f"Size x={size.x:.4f} y={size.y:.4f} z={size.z:.4f}",
                f"Vertex groups: {len(group_names)}",
                f"Vertex group names: {', '.join(group_names)}",
                "Cross sections:",
            ]
        )
        lines.extend(slice_widths(vertices, min_v, max_v))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def prepare_camera(location: tuple[float, float, float], rotation: tuple[float, float, float]) -> None:
    camera_data = bpy.data.cameras.new("InspectionCamera")
    camera = bpy.data.objects.new("InspectionCamera", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = location
    camera.rotation_euler = rotation
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 1.25
    bpy.context.scene.camera = camera


def render_image(path: Path, front: bool) -> None:
    if front:
        prepare_camera((0.0, -2.2, 0.52), (1.5708, 0.0, 0.0))
    else:
        prepare_camera((2.2, 0.0, 0.52), (1.5708, 0.0, 1.5708))
    bpy.context.scene.render.engine = "BLENDER_WORKBENCH"
    bpy.context.scene.display.shading.light = "STUDIO"
    bpy.context.scene.render.resolution_x = 1000
    bpy.context.scene.render.resolution_y = 1200
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    src, report, prefix = args_after_separator()
    bpy.ops.wm.open_mainfile(filepath=str(src))
    write_report(report, src)
    render_image(prefix.with_name(prefix.name + "_front.png"), True)
    render_image(prefix.with_name(prefix.name + "_side.png"), False)
    print(f"WROTE_SHAPE_REPORT: {report}")
    os._exit(0)


main()
