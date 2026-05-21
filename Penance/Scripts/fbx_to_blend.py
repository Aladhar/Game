import bpy
import sys
import argparse
from pathlib import Path


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def enable_fbx_importer():
    try:
        bpy.ops.preferences.addon_enable(module="io_scene_fbx")
    except Exception:
        pass


def set_frame_range_from_actions():
    min_frame = None
    max_frame = None

    for action in bpy.data.actions:
        action.use_fake_user = True  # prevents Blender from deleting the action
        start, end = action.frame_range

        if min_frame is None or start < min_frame:
            min_frame = int(start)
        if max_frame is None or end > max_frame:
            max_frame = int(end)

    if min_frame is not None and max_frame is not None:
        bpy.context.scene.frame_start = min_frame
        bpy.context.scene.frame_end = max_frame
        bpy.context.scene.frame_set(min_frame)


def convert_fbx_to_blend(fbx_path: Path, output_dir: Path):
    clear_scene()
    enable_fbx_importer()

    print(f"Importing: {fbx_path}")

    bpy.ops.import_scene.fbx(
        filepath=str(fbx_path),
        use_anim=True,
        ignore_leaf_bones=True,
        automatic_bone_orientation=False,
        use_custom_normals=True,
    )

    set_frame_range_from_actions()

    output_path = output_dir / f"{fbx_path.stem}.blend"
    print(f"Saving: {output_path}")

    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)

    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    args = parser.parse_args(argv)

    input_path = Path(args.input).expanduser().resolve()
    output_dir = Path(args.output).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if input_path.is_file() and input_path.suffix.lower() == ".fbx":
        fbx_files = [input_path]
    elif input_path.is_dir():
        fbx_files = sorted(input_path.rglob("*.fbx"))
    else:
        raise FileNotFoundError(f"Input must be an FBX file or folder: {input_path}")

    if not fbx_files:
        raise RuntimeError(f"No FBX files found in: {input_path}")

    for fbx in fbx_files:
        convert_fbx_to_blend(fbx, output_dir)

    print("Done.")


if __name__ == "__main__":
    main()