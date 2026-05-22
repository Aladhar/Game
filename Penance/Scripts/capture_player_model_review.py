from __future__ import annotations

import sys
from pathlib import Path

import bpy
from mathutils import Vector


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "Saved" / "PlayerModelReviewScreenshots"


def args_after_separator() -> list[str]:
    if "--" not in sys.argv:
        return []
    return sys.argv[sys.argv.index("--") + 1 :]


def bounds_for_visible_meshes() -> tuple[Vector, Vector]:
    mins = Vector((1e9, 1e9, 1e9))
    maxs = Vector((-1e9, -1e9, -1e9))
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH" or obj.hide_viewport or obj.hide_render:
            continue
        if obj.name.startswith("TEST_") or obj.name.startswith("BACKUP_"):
            continue
        for corner in obj.bound_box:
            co = obj.matrix_world @ Vector(corner)
            mins.x = min(mins.x, co.x)
            mins.y = min(mins.y, co.y)
            mins.z = min(mins.z, co.z)
            maxs.x = max(maxs.x, co.x)
            maxs.y = max(maxs.y, co.y)
            maxs.z = max(maxs.z, co.z)
    return mins, maxs


def setup_scene() -> bpy.types.Camera:
    scene = bpy.context.scene
    scene.render.resolution_x = 1400
    scene.render.resolution_y = 1800
    scene.display.shading.light = "STUDIO"
    scene.view_settings.view_transform = "Filmic"
    scene.view_settings.look = "Medium High Contrast"
    scene.world.color = (0.03, 0.03, 0.035)

    camera_data = bpy.data.cameras.new("TEMP_PlayerReviewCamera")
    camera = bpy.data.objects.new("TEMP_PlayerReviewCamera", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 1.15

    light_data = bpy.data.lights.new("TEMP_PlayerReviewLight", "AREA")
    light = bpy.data.objects.new("TEMP_PlayerReviewLight", light_data)
    scene.collection.objects.link(light)
    light.location = (0.0, -2.4, 2.4)
    light_data.energy = 450.0
    light_data.size = 1.8

    return camera


def point_camera(camera: bpy.types.Object, location: tuple[float, float, float], target: Vector, scale: float) -> None:
    camera.location = location
    direction = target - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    camera.data.ortho_scale = scale


def render_view(name: str, camera: bpy.types.Object, location: tuple[float, float, float], target: Vector, scale: float, output_dir: Path) -> Path:
    point_camera(camera, location, target, scale)
    path = output_dir / f"{name}.png"
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.opengl(write_still=True, view_context=False)
    print(f"SCREENSHOT: {path}")
    return path


def main() -> None:
    args = args_after_separator()
    output_dir = Path(args[0]).expanduser().resolve() if args else OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    mins, maxs = bounds_for_visible_meshes()
    center = (mins + maxs) * 0.5
    camera = setup_scene()

    paths = [
        render_view("front_full", camera, (center.x, center.y - 2.25, center.z + 0.05), center, 1.18, output_dir),
        render_view("three_quarter_full", camera, (center.x + 1.40, center.y - 2.10, center.z + 0.10), center, 1.18, output_dir),
        render_view("hands_closeup", camera, (0.0, -1.05, 0.47), Vector((0.0, -0.035, 0.47)), 0.30, output_dir),
        render_view("jacket_collar_closeup", camera, (0.0, -1.15, 0.70), Vector((0.0, -0.055, 0.68)), 0.45, output_dir),
        render_view("hair_closeup", camera, (0.0, -1.00, 0.91), Vector((0.0, -0.035, 0.91)), 0.30, output_dir),
    ]

    report = output_dir / "review_screenshots.txt"
    report.write_text("\n".join(str(path) for path in paths) + "\n", encoding="utf-8")
    print(f"SCREENSHOT_REPORT: {report}")
    bpy.ops.wm.quit_blender()


if __name__ == "__main__":
    main()
