from pathlib import Path

import unreal

from penance_script_safety import require_asset_write_permission


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = PROJECT_ROOT / "Saved" / "PenanceRiggedCharacterImportReport.txt"

SPECS = [
    {
        "name": "SK_Player",
        "source": PROJECT_ROOT / "Content" / "Player" / "BlenderSource" / "SK_Player_FromBlend.fbx",
        "destination": "/Game/Player/Skeletal",
    },
    {
        "name": "SK_Penance",
        "source": PROJECT_ROOT / "Content" / "PenanceAssets" / "Enemies" / "PenanceCarrier" / "BlenderSource" / "SK_Penance_FromBlend.fbx",
        "destination": "/Game/PenanceAssets/Enemies/PenanceCarrier/Skeletal",
    },
]


def disable_browser_sync():
    unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.SyncToBrowser 0")


def ensure_directory(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def make_fbx_options():
    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_as_skeletal", True)
    options.set_editor_property("import_animations", False)
    options.set_editor_property("import_materials", False)
    options.set_editor_property("import_textures", False)
    options.set_editor_property("create_physics_asset", True)
    options.set_editor_property("skeleton", None)

    skeletal_data = options.get_editor_property("skeletal_mesh_import_data")
    if skeletal_data:
        skeletal_data.set_editor_property("convert_scene", True)
        skeletal_data.set_editor_property("convert_scene_unit", True)
        skeletal_data.set_editor_property("import_uniform_scale", 1.0)
        skeletal_data.set_editor_property("update_skeleton_reference_pose", True)
        skeletal_data.set_editor_property("use_t0_as_ref_pose", True)

    return options


def import_spec(spec):
    source = spec["source"]
    if not source.exists():
        raise RuntimeError(f"Missing rigged FBX: {source}")

    ensure_directory(spec["destination"])
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(source))
    task.set_editor_property("destination_path", spec["destination"])
    task.set_editor_property("destination_name", spec["name"])
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    task.set_editor_property("options", make_fbx_options())

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    imported = list(task.get_editor_property("imported_object_paths"))
    if not imported:
        raise RuntimeError(f"Unreal imported no assets from: {source}")
    return imported


def class_name(asset_path):
    asset = unreal.EditorAssetLibrary.load_asset(asset_path)
    return asset.get_class().get_name() if asset else "Missing"


def main():
    require_asset_write_permission("import rigged character FBX files into Unreal content")
    disable_browser_sync()
    imported_paths = []
    for spec in SPECS:
        imported_paths.extend(import_spec(spec))

    all_paths = []
    for spec in SPECS:
        all_paths.extend(
            unreal.EditorAssetLibrary.list_assets(spec["destination"], recursive=True, include_folder=False)
        )

    lines = ["PENANCE_RIGGED_CHARACTER_IMPORT_REPORT"]
    lines.append(f"Imported path count: {len(imported_paths)}")
    for path in sorted(imported_paths):
        lines.append(f"Imported: {class_name(path)} {path}")
    lines.append("Destination assets:")
    for path in sorted(all_paths):
        lines.append(f"- {class_name(path)} {path}")

    REPORT_PATH.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
