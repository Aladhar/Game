"""Open a rigged FBX in Blender for visual inspection.

Usage from Blender:
  blender --python open_rig_in_blender.py -- /absolute/path/to/SK_Player.fbx
"""

import sys
from pathlib import Path

import bpy


def arg_after_separator() -> Path:
    if "--" not in sys.argv:
        raise SystemExit("Expected FBX path after --")
    args = sys.argv[sys.argv.index("--") + 1 :]
    if not args:
        raise SystemExit("Expected FBX path after --")
    fbx_path = Path(args[0]).expanduser().resolve()
    if not fbx_path.exists():
        raise SystemExit(f"FBX does not exist: {fbx_path}")
    return fbx_path


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def import_fbx(fbx_path: Path) -> None:
    bpy.ops.import_scene.fbx(filepath=str(fbx_path))
    bpy.context.scene.name = fbx_path.stem


def prepare_view() -> None:
    for obj in bpy.context.scene.objects:
        obj.select_set(obj.type in {"ARMATURE", "MESH"})
        if obj.type == "ARMATURE":
            bpy.context.view_layer.objects.active = obj
            obj.show_in_front = True

    for area in bpy.context.screen.areas:
        if area.type != "VIEW_3D":
            continue
        region = next((r for r in area.regions if r.type == "WINDOW"), None)
        space = area.spaces.active
        if region and space:
            override = {
                "window": bpy.context.window,
                "screen": bpy.context.screen,
                "area": area,
                "region": region,
                "space_data": space,
                "region_data": space.region_3d,
            }
            with bpy.context.temp_override(**override):
                bpy.ops.view3d.view_axis(type="FRONT", align_active=False)
                bpy.ops.view3d.view_selected(use_all_regions=False)
        break


def main() -> None:
    fbx_path = arg_after_separator()
    clear_scene()
    import_fbx(fbx_path)
    prepare_view()
    print(f"OPENED_RIG_FOR_INSPECTION: {fbx_path}")


main()
