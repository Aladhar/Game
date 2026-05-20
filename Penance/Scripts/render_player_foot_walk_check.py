"""Render lower-body walk frames for visual shoe deformation checks."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def args_after_separator() -> tuple[Path, Path]:
    if "--" not in sys.argv:
        raise SystemExit("Expected arguments after --: SRC.blend OUTPUT_DIR")
    args = sys.argv[sys.argv.index("--") + 1 :]
    if len(args) != 2:
        raise SystemExit("Expected arguments after --: SRC.blend OUTPUT_DIR")
    src = Path(args[0]).expanduser().resolve()
    out = Path(args[1]).expanduser().resolve()
    if not src.exists():
        raise SystemExit(f"Blend does not exist: {src}")
    out.mkdir(parents=True, exist_ok=True)
    return src, out


def mesh_bounds() -> tuple[Vector, Vector]:
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and len(obj.data.vertices) > 100]
    mesh = max(meshes, key=lambda obj: len(obj.data.vertices))
    points = [mesh.matrix_world @ vertex.co for vertex in mesh.data.vertices]
    minimum = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    maximum = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return minimum, maximum


def setup_camera(name: str, location: tuple[float, float, float], rotation: tuple[float, float, float], scale: float) -> bpy.types.Object:
    camera_data = bpy.data.cameras.new(name)
    camera = bpy.data.objects.new(name, camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = location
    camera.rotation_euler = rotation
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = scale
    return camera


def render(path: Path, camera: bpy.types.Object, frame: int) -> None:
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    bpy.context.scene.camera = camera
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    src, out = args_after_separator()
    bpy.ops.wm.open_mainfile(filepath=str(src))
    minimum, maximum = mesh_bounds()
    center_x = (minimum.x + maximum.x) * 0.5
    center_y = (minimum.y + maximum.y) * 0.5
    # Focus on lower legs/shoes, with enough space to see cuff distortion.
    center_z = minimum.z + (maximum.z - minimum.z) * 0.18

    bpy.context.scene.render.engine = "BLENDER_WORKBENCH"
    bpy.context.scene.display.shading.light = "STUDIO"
    bpy.context.scene.display.shading.color_type = "MATERIAL"
    bpy.context.scene.render.resolution_x = 900
    bpy.context.scene.render.resolution_y = 900

    front = setup_camera(
        "FootCheckFront",
        (center_x, minimum.y - 1.35, center_z),
        (1.5708, 0.0, 0.0),
        0.44,
    )
    side = setup_camera(
        "FootCheckSide",
        (maximum.x + 1.35, center_y, center_z),
        (1.5708, 0.0, 1.5708),
        0.44,
    )

    for frame in (1, 8, 16, 24, 32):
        render(out / f"front_f{frame:02d}.png", front, frame)
        render(out / f"side_f{frame:02d}.png", side, frame)
    print(f"RENDERED_FOOT_WALK_CHECK: {out}")
    os._exit(0)


main()
