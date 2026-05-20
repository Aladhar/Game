"""Render full-body front/side walk frames from a Blender character file."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def args_after_separator() -> tuple[Path, Path, str]:
    if "--" not in sys.argv:
        raise SystemExit("Expected -- SRC.blend OUTPUT_DIR frame_csv")
    args = sys.argv[sys.argv.index("--") + 1 :]
    if len(args) != 3:
        raise SystemExit("Expected -- SRC.blend OUTPUT_DIR frame_csv")
    src = Path(args[0]).resolve()
    out = Path(args[1]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    return src, out, args[2]


def mesh_bounds() -> tuple[Vector, Vector]:
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and len(obj.data.vertices) > 100]
    mesh = max(meshes, key=lambda obj: len(obj.data.vertices))
    points = [mesh.matrix_world @ vertex.co for vertex in mesh.data.vertices]
    return (
        Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points))),
        Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points))),
    )


def camera(name: str, location, rotation, scale: float):
    data = bpy.data.cameras.new(name)
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = rotation
    data.type = "ORTHO"
    data.ortho_scale = scale
    return obj


def render(path: Path, cam, frame: int) -> None:
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    bpy.context.scene.camera = cam
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    src, out, frame_csv = args_after_separator()
    bpy.ops.wm.open_mainfile(filepath=str(src))
    min_v, max_v = mesh_bounds()
    center = (min_v + max_v) * 0.5
    height = max_v.z - min_v.z
    width = max(max_v.x - min_v.x, max_v.y - min_v.y)
    scale = max(height * 1.18, width * 1.35)

    bpy.context.scene.render.engine = "BLENDER_WORKBENCH"
    bpy.context.scene.display.shading.light = "STUDIO"
    bpy.context.scene.render.resolution_x = 1100
    bpy.context.scene.render.resolution_y = 1300

    front = camera("WalkFront", (center.x, min_v.y - 2.4, center.z), (1.5708, 0.0, 0.0), scale)
    side = camera("WalkSide", (max_v.x + 2.4, center.y, center.z), (1.5708, 0.0, 1.5708), scale)
    frames = [int(part) for part in frame_csv.split(",") if part.strip()]
    for frame in frames:
        render(out / f"front_f{frame:02d}.png", front, frame)
        render(out / f"side_f{frame:02d}.png", side, frame)
    print(f"RENDERED_FULLBODY_WALK: {out}")
    os._exit(0)


main()
