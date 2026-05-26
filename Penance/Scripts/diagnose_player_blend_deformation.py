"""Diagnose Player.blend mesh deformation state."""

from __future__ import annotations

import sys
from pathlib import Path

import bpy
from mathutils import Vector


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BLEND = PROJECT_ROOT / "Content" / "Player" / "Player.blend"
DEFAULT_REPORT = PROJECT_ROOT / "Saved" / "PlayerBlendDeformationDiagnosis.txt"
MESH_NAME = "Mesh_0"


def args_after_separator() -> tuple[Path, Path]:
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    src = Path(args[0]).expanduser().resolve() if args else DEFAULT_BLEND
    report = Path(args[1]).expanduser().resolve() if len(args) > 1 else DEFAULT_REPORT
    report.parent.mkdir(parents=True, exist_ok=True)
    return src, report


def bounds_from_points(points: list[Vector]) -> tuple[Vector, Vector]:
    return (
        Vector((min(v.x for v in points), min(v.y for v in points), min(v.z for v in points))),
        Vector((max(v.x for v in points), max(v.y for v in points), max(v.z for v in points))),
    )


def object_mesh_bounds(obj: bpy.types.Object, evaluated: bool) -> tuple[Vector, Vector]:
    if evaluated:
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = obj.evaluated_get(depsgraph)
        mesh = eval_obj.to_mesh()
        points = [eval_obj.matrix_world @ v.co for v in mesh.vertices]
        eval_obj.to_mesh_clear()
    else:
        points = [obj.matrix_world @ v.co for v in obj.data.vertices]
    return bounds_from_points(points)


def non_identity_pose_count(armature: bpy.types.Object) -> int:
    count = 0
    for bone in armature.pose.bones:
        loc = bone.location.length
        rot = abs(bone.rotation_euler.x) + abs(bone.rotation_euler.y) + abs(bone.rotation_euler.z)
        scale = (Vector(bone.scale) - Vector((1.0, 1.0, 1.0))).length
        if loc > 0.0001 or rot > 0.0001 or scale > 0.0001:
            count += 1
    return count


def main() -> None:
    src, report = args_after_separator()
    bpy.ops.wm.open_mainfile(filepath=str(src), load_ui=False)
    mesh = bpy.data.objects.get(MESH_NAME)
    if not mesh or mesh.type != "MESH":
        raise SystemExit(f"Missing mesh {MESH_NAME}")

    raw_min, raw_max = object_mesh_bounds(mesh, evaluated=False)
    eval_min, eval_max = object_mesh_bounds(mesh, evaluated=True)
    lines = [
        "PLAYER_BLEND_DEFORMATION_DIAGNOSIS",
        f"Blend: {src}",
        f"Mesh: {mesh.name}",
        f"Mesh parent: {mesh.parent.name if mesh.parent else 'none'}",
        f"Mesh hidden: hide_get={mesh.hide_get()} hide_viewport={mesh.hide_viewport} hide_render={mesh.hide_render}",
        f"Raw bounds: min=({raw_min.x:.4f},{raw_min.y:.4f},{raw_min.z:.4f}) max=({raw_max.x:.4f},{raw_max.y:.4f},{raw_max.z:.4f}) size=({raw_max.x - raw_min.x:.4f},{raw_max.y - raw_min.y:.4f},{raw_max.z - raw_min.z:.4f})",
        f"Evaluated bounds: min=({eval_min.x:.4f},{eval_min.y:.4f},{eval_min.z:.4f}) max=({eval_max.x:.4f},{eval_max.y:.4f},{eval_max.z:.4f}) size=({eval_max.x - eval_min.x:.4f},{eval_max.y - eval_min.y:.4f},{eval_max.z - eval_min.z:.4f})",
        "Modifiers:",
    ]
    for modifier in mesh.modifiers:
        target = getattr(modifier, "object", None)
        lines.append(f"- {modifier.name}: type={modifier.type} object={target.name if target else 'none'} show={modifier.show_viewport}")

    lines.append(f"Vertex groups: {len(mesh.vertex_groups)}")
    lines.append("Armatures:")
    for obj in bpy.data.objects:
        if obj.type != "ARMATURE":
            continue
        deform_count = sum(1 for bone in obj.data.bones if bone.use_deform)
        lines.append(
            f"- {obj.name}: hidden={obj.hide_get()}/{obj.hide_viewport} bones={len(obj.data.bones)} "
            f"deform={deform_count} non_identity_pose={non_identity_pose_count(obj)} "
            f"action={obj.animation_data.action.name if obj.animation_data and obj.animation_data.action else 'none'}"
        )

    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


main()
