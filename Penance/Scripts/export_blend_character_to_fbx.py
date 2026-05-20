"""Export a Blender character scene to FBX for Unreal skeletal import.

Run from Blender:
  blender --python export_blend_character_to_fbx.py -- SRC.blend OUT.fbx REPORT.txt
"""

from __future__ import annotations

import sys
import traceback
import os
from pathlib import Path

import bpy


def args_after_separator() -> tuple[Path, Path, Path]:
    if "--" not in sys.argv:
        raise SystemExit("Expected arguments after --: SRC.blend OUT.fbx REPORT.txt")
    args = sys.argv[sys.argv.index("--") + 1 :]
    if len(args) != 3:
        raise SystemExit("Expected arguments after --: SRC.blend OUT.fbx REPORT.txt")
    src = Path(args[0]).expanduser().resolve()
    out = Path(args[1]).expanduser().resolve()
    report = Path(args[2]).expanduser().resolve()
    if not src.exists():
        raise SystemExit(f"Source blend does not exist: {src}")
    out.parent.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    return src, out, report


def visible_export_objects() -> list[bpy.types.Object]:
    objects: list[bpy.types.Object] = []
    for obj in bpy.context.scene.objects:
        if obj.type not in {"ARMATURE", "MESH"}:
            continue
        if obj.hide_get() or obj.hide_viewport:
            continue
        objects.append(obj)
    return objects


def select_for_export(objects: list[bpy.types.Object]) -> None:
    bpy.ops.object.mode_set(mode="OBJECT") if bpy.ops.object.mode_set.poll() else None
    bpy.ops.object.select_all(action="DESELECT")
    active_armature = next((obj for obj in objects if obj.type == "ARMATURE"), None)
    for obj in objects:
        obj.select_set(True)
        if obj.type == "ARMATURE":
            obj.show_in_front = True
    bpy.context.view_layer.objects.active = active_armature or (objects[0] if objects else None)


def write_report(
    path: Path,
    src: Path,
    out: Path,
    objects: list[bpy.types.Object],
    status: str,
    detail: str = "",
) -> None:
    lines = [
        "BLEND_CHARACTER_EXPORT_REPORT",
        f"Source: {src}",
        f"FBX: {out}",
        f"Status: {status}",
        f"Exported object count: {len(objects)}",
    ]
    for obj in objects:
        if obj.type == "ARMATURE":
            lines.append(f"- ARMATURE {obj.name} bones={len(obj.data.bones)}")
            deform_count = sum(1 for bone in obj.data.bones if bone.use_deform)
            lines.append(f"  deform_bones={deform_count}")
        elif obj.type == "MESH":
            modifiers = ",".join(mod.type for mod in obj.modifiers) or "none"
            groups = ",".join(group.name for group in obj.vertex_groups) or "none"
            lines.append(
                f"- MESH {obj.name} verts={len(obj.data.vertices)} "
                f"groups={len(obj.vertex_groups)} modifiers={modifiers}"
            )
            lines.append(f"  vertex_groups={groups}")
    if detail:
        lines.append("Detail:")
        lines.append(detail)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    src, out, report = args_after_separator()
    bpy.ops.wm.open_mainfile(filepath=str(src))
    objects = visible_export_objects()
    select_for_export(objects)
    if not objects:
        write_report(report, src, out, objects, "FAILED", "No visible mesh or armature objects found to export")
        raise SystemExit("No visible mesh or armature objects found to export")

    try:
        override = {
            "selected_objects": objects,
            "selected_editable_objects": objects,
            "active_object": bpy.context.view_layer.objects.active,
        }
        with bpy.context.temp_override(**override):
            bpy.ops.export_scene.fbx(
                filepath=str(out),
                use_selection=True,
                object_types={"ARMATURE", "MESH"},
                apply_unit_scale=True,
                apply_scale_options="FBX_SCALE_ALL",
                bake_space_transform=False,
                add_leaf_bones=False,
                primary_bone_axis="Y",
                secondary_bone_axis="X",
                bake_anim=False,
                path_mode="AUTO",
            )
    except Exception:
        detail = traceback.format_exc()
        write_report(report, src, out, objects, "FAILED", detail)
        raise

    if not out.exists():
        detail = "FBX export operator completed, but the output file does not exist."
        write_report(report, src, out, objects, "FAILED", detail)
        raise SystemExit(detail)

    write_report(report, src, out, objects, "OK")
    print(f"EXPORTED_BLEND_CHARACTER_TO_FBX: {out}")
    sys.stdout.flush()
    os._exit(0)


main()
