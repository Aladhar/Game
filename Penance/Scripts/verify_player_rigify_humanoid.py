"""Verify and render the Player.blend Rigify humanoid self-test pose."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector


RIG_NAME = "RIG_Player_Rigify_Humanoid_IK"
MESH_NAME = "Mesh_0"
ACTION_NAME = "AN_Player_Rigify_IK_FK_Deform_SelfTest"


def args_after_separator() -> tuple[Path, Path, Path]:
    if "--" not in sys.argv:
        raise SystemExit("Expected -- SRC.blend REPORT.txt IMAGE_PREFIX")
    args = sys.argv[sys.argv.index("--") + 1 :]
    if len(args) != 3:
        raise SystemExit("Expected -- SRC.blend REPORT.txt IMAGE_PREFIX")
    src = Path(args[0]).expanduser().resolve()
    report = Path(args[1]).expanduser().resolve()
    prefix = Path(args[2]).expanduser().resolve()
    report.parent.mkdir(parents=True, exist_ok=True)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    return src, report, prefix


def bounds(vertices: list[Vector]) -> tuple[Vector, Vector]:
    return (
        Vector((min(v.x for v in vertices), min(v.y for v in vertices), min(v.z for v in vertices))),
        Vector((max(v.x for v in vertices), max(v.y for v in vertices), max(v.z for v in vertices))),
    )


def evaluated_mesh_bounds(mesh: bpy.types.Object, frame: int) -> tuple[Vector, Vector, int]:
    bpy.context.scene.frame_set(frame)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = mesh.evaluated_get(depsgraph)
    temp_mesh = evaluated.to_mesh()
    try:
        verts = [evaluated.matrix_world @ vertex.co for vertex in temp_mesh.vertices]
        minimum, maximum = bounds(verts)
        return minimum, maximum, len(verts)
    finally:
        evaluated.to_mesh_clear()


def prepare_scene(rig: bpy.types.Object, action: bpy.types.Action) -> None:
    rig.animation_data_create()
    rig.animation_data.action = action
    for obj in bpy.data.objects:
        if obj.name.startswith("WGT-") or obj.name.startswith("META_") or obj.name.startswith("SOURCE_"):
            obj.hide_render = True
    bpy.context.scene.render.engine = "BLENDER_WORKBENCH"
    bpy.context.scene.display.shading.light = "STUDIO"
    bpy.context.scene.display.shading.color_type = "MATERIAL"
    bpy.context.scene.render.resolution_x = 1200
    bpy.context.scene.render.resolution_y = 1400


def camera(name: str, location: tuple[float, float, float], rotation: tuple[float, float, float]) -> bpy.types.Object:
    existing = bpy.data.objects.get(name)
    if existing:
        bpy.data.objects.remove(existing, do_unlink=True)
    data = bpy.data.cameras.new(name)
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = rotation
    data.type = "ORTHO"
    data.ortho_scale = 2.25
    return obj


def render(path: Path, frame: int, side: bool) -> None:
    bpy.context.scene.frame_set(frame)
    if side:
        cam = camera("RigifyVerifyCameraSide", (3.2, 0.0, 1.0), (1.5708, 0.0, 1.5708))
    else:
        cam = camera("RigifyVerifyCameraFront", (0.0, -3.2, 1.0), (1.5708, 0.0, 0.0))
    bpy.context.scene.camera = cam
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    src, report, prefix = args_after_separator()
    bpy.ops.wm.open_mainfile(filepath=str(src), load_ui=False)
    rig = bpy.data.objects.get(RIG_NAME)
    mesh = bpy.data.objects.get(MESH_NAME)
    action = bpy.data.actions.get(ACTION_NAME)
    if not rig or rig.type != "ARMATURE":
        raise SystemExit(f"Missing rig: {RIG_NAME}")
    if not mesh or mesh.type != "MESH":
        raise SystemExit(f"Missing mesh: {MESH_NAME}")
    if not action:
        raise SystemExit(f"Missing action: {ACTION_NAME}")

    prepare_scene(rig, action)
    frames = [1, 16, 32, 48]
    lines = [
        "PLAYER_RIGIFY_HUMANOID_VERIFY",
        f"Blend: {src}",
        f"Rig: {rig.name}",
        f"Mesh: {mesh.name}",
        f"Action: {action.name}",
        f"Vertex groups: {len(mesh.vertex_groups)}",
        f"Weighted vertices: {sum(1 for vertex in mesh.data.vertices if vertex.groups)} / {len(mesh.data.vertices)}",
        f"Armature modifiers: {', '.join(mod.name for mod in mesh.modifiers if mod.type == 'ARMATURE')}",
    ]
    for frame in frames:
        minimum, maximum, count = evaluated_mesh_bounds(mesh, frame)
        size = maximum - minimum
        lines.append(
            f"Frame {frame}: verts={count} "
            f"bounds_min=({minimum.x:.4f},{minimum.y:.4f},{minimum.z:.4f}) "
            f"bounds_max=({maximum.x:.4f},{maximum.y:.4f},{maximum.z:.4f}) "
            f"size=({size.x:.4f},{size.y:.4f},{size.z:.4f})"
        )

    render(prefix.with_name(prefix.name + "_front_frame16.png"), 16, side=False)
    render(prefix.with_name(prefix.name + "_side_frame32.png"), 32, side=True)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"PLAYER_RIGIFY_VERIFY_DONE: {report}")
    sys.stdout.flush()
    os._exit(0)


main()
