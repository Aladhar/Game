"""Export all mesh and armature objects in a .blend to FBX."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import bpy


def args_after_separator() -> tuple[Path, Path]:
    if "--" not in sys.argv:
        raise SystemExit("Expected -- SRC.blend OUT.fbx")
    args = sys.argv[sys.argv.index("--") + 1 :]
    if len(args) != 2:
        raise SystemExit("Expected -- SRC.blend OUT.fbx")
    src = Path(args[0]).resolve()
    out = Path(args[1]).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    return src, out


def main() -> None:
    src, out = args_after_separator()
    bpy.ops.wm.open_mainfile(filepath=str(src))
    objects = [obj for obj in bpy.context.scene.objects if obj.type in {"MESH", "ARMATURE"}]
    if not objects:
        raise SystemExit("No mesh or armature objects found")
    active = next((obj for obj in objects if obj.type == "ARMATURE"), objects[0])
    for obj in bpy.context.scene.objects:
        obj.select_set(False)
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = active
    with bpy.context.temp_override(
        active_object=active,
        object=active,
        selected_objects=objects,
        selected_editable_objects=objects,
    ):
        bpy.ops.export_scene.fbx(
            filepath=str(out),
            use_selection=True,
            object_types={"ARMATURE", "MESH"},
            apply_unit_scale=True,
            bake_space_transform=False,
            add_leaf_bones=False,
            bake_anim=True,
            bake_anim_use_all_actions=True,
            bake_anim_use_nla_strips=False,
        )
    print(f"EXPORTED_BLEND_FBX: {out}")
    os._exit(0)


main()
