"""Test bind options for Player.blend without saving."""

from __future__ import annotations

import sys
from pathlib import Path

import bpy
from mathutils import Vector


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BLEND = PROJECT_ROOT / "Content" / "Player" / "Player.blend"
MESH_NAME = "Mesh_0"
RIG_NAME = "RIG_Player_Rigify_Humanoid_IK"


def bounds(obj: bpy.types.Object, evaluated: bool) -> tuple[Vector, Vector]:
    if evaluated:
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = obj.evaluated_get(depsgraph)
        data = eval_obj.to_mesh()
        pts = [eval_obj.matrix_world @ v.co for v in data.vertices]
        eval_obj.to_mesh_clear()
    else:
        pts = [obj.matrix_world @ v.co for v in obj.data.vertices]
    return (
        Vector((min(v.x for v in pts), min(v.y for v in pts), min(v.z for v in pts))),
        Vector((max(v.x for v in pts), max(v.y for v in pts), max(v.z for v in pts))),
    )


def fmt(label: str, min_v: Vector, max_v: Vector) -> str:
    return f"{label}: min=({min_v.x:.4f},{min_v.y:.4f},{min_v.z:.4f}) max=({max_v.x:.4f},{max_v.y:.4f},{max_v.z:.4f}) size=({max_v.x-min_v.x:.4f},{max_v.y-min_v.y:.4f},{max_v.z-min_v.z:.4f})"


def clear_pose(rig: bpy.types.Object) -> None:
    if rig.animation_data:
        rig.animation_data.action = None
    for bone in rig.pose.bones:
        bone.location = (0.0, 0.0, 0.0)
        bone.rotation_euler = (0.0, 0.0, 0.0)
        bone.scale = (1.0, 1.0, 1.0)


def main() -> None:
    src = Path(sys.argv[sys.argv.index("--") + 1]).resolve() if "--" in sys.argv else DEFAULT_BLEND
    bpy.ops.wm.open_mainfile(filepath=str(src), load_ui=False)
    mesh = bpy.data.objects[MESH_NAME]
    rig = bpy.data.objects[RIG_NAME]
    clear_pose(rig)
    bpy.context.view_layer.update()
    raw = bounds(mesh, False)
    ev = bounds(mesh, True)
    print(fmt("current raw", *raw))
    print(fmt("current eval", *ev))

    mesh.parent = None
    mesh.matrix_parent_inverse.identity()
    bpy.context.view_layer.update()
    print(fmt("parent none raw", *bounds(mesh, False)))
    print(fmt("parent none eval", *bounds(mesh, True)))

    for modifier in mesh.modifiers:
        if modifier.type == "ARMATURE":
            modifier.show_viewport = False
    bpy.context.view_layer.update()
    print(fmt("modifier disabled raw", *bounds(mesh, False)))
    print(fmt("modifier disabled eval", *bounds(mesh, True)))


main()
