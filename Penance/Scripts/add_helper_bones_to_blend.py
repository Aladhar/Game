"""Add helper bones to the rough Player/Penance Blender rigs.

Run from Blender:
  blender --python add_helper_bones_to_blend.py -- SRC.blend OUT.blend REPORT.txt
"""

from __future__ import annotations

import sys
import os
from pathlib import Path

import bpy
from mathutils import Vector


def args_after_separator() -> tuple[Path, Path, Path]:
    if "--" not in sys.argv:
        raise SystemExit("Expected arguments after --: SRC.blend OUT.blend REPORT.txt")
    args = sys.argv[sys.argv.index("--") + 1 :]
    if len(args) != 3:
        raise SystemExit("Expected arguments after --: SRC.blend OUT.blend REPORT.txt")
    src = Path(args[0]).expanduser().resolve()
    out = Path(args[1]).expanduser().resolve()
    report = Path(args[2]).expanduser().resolve()
    if not src.exists():
        raise SystemExit(f"Source blend does not exist: {src}")
    out.parent.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    return src, out, report


def first_armature() -> bpy.types.Object:
    armatures = [obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"]
    if not armatures:
        raise SystemExit("No armature found in blend file")
    return armatures[0]


def first_mesh() -> bpy.types.Object | None:
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    return meshes[0] if meshes else None


def midpoint(a: Vector, b: Vector, alpha: float) -> Vector:
    return a.lerp(b, alpha)


def make_bone(
    edit_bones: bpy.types.ArmatureEditBones,
    name: str,
    head: Vector,
    tail: Vector,
    parent_name: str | None,
    deform: bool,
) -> bool:
    if name in edit_bones:
        return False
    bone = edit_bones.new(name)
    bone.head = head
    bone.tail = tail
    bone.use_deform = deform
    if parent_name and parent_name in edit_bones:
        bone.parent = edit_bones[parent_name]
    return True


def add_limb_twist_bone(edit_bones, base_name: str, twist_name: str) -> bool:
    if base_name not in edit_bones:
        return False
    base = edit_bones[base_name]
    head = midpoint(base.head, base.tail, 0.42)
    tail = midpoint(base.head, base.tail, 0.88)
    if (tail - head).length < 0.02:
        tail = base.tail
    return make_bone(edit_bones, twist_name, head, tail, base_name, True)


def add_ik_bone(edit_bones, source_name: str, ik_name: str, offset: Vector) -> bool:
    if source_name not in edit_bones or "root" not in edit_bones:
        return False
    source = edit_bones[source_name]
    head = source.tail + offset
    tail = head + Vector((0.0, 0.0, 0.08))
    return make_bone(edit_bones, ik_name, head, tail, "root", False)


def add_helper_bones(armature: bpy.types.Object) -> list[str]:
    bpy.ops.object.mode_set(mode="OBJECT") if bpy.ops.object.mode_set.poll() else None
    bpy.ops.object.select_all(action="DESELECT")
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    bpy.context.view_layer.update()

    object_context = {
        "active_object": armature,
        "object": armature,
        "selected_objects": [armature],
        "selected_editable_objects": [armature],
    }
    with bpy.context.temp_override(**object_context):
        bpy.ops.object.mode_set(mode="EDIT")

    eb = armature.data.edit_bones
    created: list[str] = []

    twist_specs = [
        ("upperarm_l", "upperarm_twist_l"),
        ("upperarm_r", "upperarm_twist_r"),
        ("lowerarm_l", "lowerarm_twist_l"),
        ("lowerarm_r", "lowerarm_twist_r"),
        ("thigh_l", "thigh_twist_l"),
        ("thigh_r", "thigh_twist_r"),
        ("calf_l", "calf_twist_l"),
        ("calf_r", "calf_twist_r"),
    ]
    for source, helper in twist_specs:
        if add_limb_twist_bone(eb, source, helper):
            created.append(helper)

    ik_specs = [
        ("hand_l", "ik_hand_l", Vector((-0.05, 0.0, 0.0))),
        ("hand_r", "ik_hand_r", Vector((0.05, 0.0, 0.0))),
        ("foot_l", "ik_foot_l", Vector((0.0, 0.08, 0.0))),
        ("foot_r", "ik_foot_r", Vector((0.0, 0.08, 0.0))),
    ]
    for source, helper, offset in ik_specs:
        if add_ik_bone(eb, source, helper, offset):
            created.append(helper)

    if "head" in eb:
        head = eb["head"]
        camera_head = midpoint(head.head, head.tail, 0.2) + Vector((0.0, 0.18, 0.0))
        if make_bone(eb, "camera", camera_head, camera_head + Vector((0.0, 0.12, 0.0)), "head", False):
            created.append("camera")

        jaw_head = midpoint(head.head, head.tail, 0.2) + Vector((0.0, 0.08, -0.02))
        if make_bone(eb, "jaw", jaw_head, jaw_head + Vector((0.0, 0.08, -0.04)), "head", False):
            created.append("jaw")

        for side, x_offset in (("l", -0.035), ("r", 0.035)):
            eye_head = midpoint(head.head, head.tail, 0.45) + Vector((x_offset, 0.09, 0.0))
            name = f"eye_{side}"
            if make_bone(eb, name, eye_head, eye_head + Vector((0.0, 0.05, 0.0)), "head", False):
                created.append(name)

    pelvis_head = eb["pelvis"].head if "pelvis" in eb else Vector((0.0, 0.0, 0.46))
    pelvis_tail = eb["pelvis"].tail if "pelvis" in eb else Vector((0.0, 0.0, 0.56))
    cloth_parent = "pelvis" if "pelvis" in eb else "root"
    cloth_specs = [
        ("cloth_front_l", Vector((-0.055, 0.105, pelvis_tail.z)), Vector((-0.075, 0.135, pelvis_head.z - 0.26))),
        ("cloth_front_r", Vector((0.055, 0.105, pelvis_tail.z)), Vector((0.075, 0.135, pelvis_head.z - 0.26))),
        ("cloth_back_l", Vector((-0.055, -0.105, pelvis_tail.z)), Vector((-0.075, -0.135, pelvis_head.z - 0.26))),
        ("cloth_back_r", Vector((0.055, -0.105, pelvis_tail.z)), Vector((0.075, -0.135, pelvis_head.z - 0.26))),
        ("coat_side_l", Vector((-0.12, 0.0, pelvis_tail.z)), Vector((-0.16, 0.0, pelvis_head.z - 0.22))),
        ("coat_side_r", Vector((0.12, 0.0, pelvis_tail.z)), Vector((0.16, 0.0, pelvis_head.z - 0.22))),
    ]
    for name, head, tail in cloth_specs:
        if make_bone(eb, name, head, tail, cloth_parent, True):
            created.append(name)

    if "hand_r" in eb:
        hand = eb["hand_r"]
        weapon_head = midpoint(hand.head, hand.tail, 0.5) + Vector((0.0, 0.05, 0.0))
        if make_bone(eb, "weapon_r", weapon_head, weapon_head + Vector((0.0, 0.16, 0.0)), "hand_r", False):
            created.append("weapon_r")
    if "hand_l" in eb:
        hand = eb["hand_l"]
        weapon_head = midpoint(hand.head, hand.tail, 0.5) + Vector((0.0, 0.05, 0.0))
        if make_bone(eb, "weapon_l", weapon_head, weapon_head + Vector((0.0, 0.16, 0.0)), "hand_l", False):
            created.append("weapon_l")

    with bpy.context.temp_override(**object_context):
        bpy.ops.object.mode_set(mode="OBJECT")
    return created


def ensure_deform_groups(mesh: bpy.types.Object | None, armature: bpy.types.Object) -> None:
    if not mesh:
        return
    deform_names = [bone.name for bone in armature.data.bones if bone.use_deform]
    existing = {group.name for group in mesh.vertex_groups}
    for name in deform_names:
        if name not in existing:
            mesh.vertex_groups.new(name=name)


def write_report(path: Path, src: Path, out: Path, armature: bpy.types.Object, mesh: bpy.types.Object | None, created: list[str]) -> None:
    deform = [bone.name for bone in armature.data.bones if bone.use_deform]
    non_deform = [bone.name for bone in armature.data.bones if not bone.use_deform]
    lines = [
        "HELPER_BONES_REPORT",
        f"Source: {src}",
        f"Saved: {out}",
        f"Armature: {armature.name}",
        f"Total bones: {len(armature.data.bones)}",
        f"Deform bones: {len(deform)}",
        f"Helper/non-deform bones: {len(non_deform)}",
        f"Created this run: {', '.join(created) if created else 'none'}",
        f"Mesh: {mesh.name if mesh else 'none'}",
        f"Mesh vertex groups: {len(mesh.vertex_groups) if mesh else 0}",
        "Deform bone names:",
        ", ".join(deform),
        "Helper/non-deform bone names:",
        ", ".join(non_deform),
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    src, out, report = args_after_separator()
    bpy.ops.wm.open_mainfile(filepath=str(src))
    armature = first_armature()
    mesh = first_mesh()
    created = add_helper_bones(armature)
    ensure_deform_groups(mesh, armature)
    write_report(report, src, out, armature, mesh, created)
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    print(f"ADDED_HELPER_BONES_AND_SAVED: {out}")
    sys.stdout.flush()
    os._exit(0)


main()
