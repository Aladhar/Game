from pathlib import Path

import unreal

from penance_script_safety import require_asset_write_permission


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_FBX = PROJECT_ROOT / "Built" / "FBX" / "SK_Player_FirstPersonBody.fbx"
DESTINATION = "/Game/Player/FirstPerson"
REPORT = PROJECT_ROOT / "Saved" / "PlayerFirstPersonBodyImportReport.txt"


def ensure_dir(path: str) -> None:
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def class_name(path: str) -> str:
    asset = unreal.EditorAssetLibrary.load_asset(path)
    return asset.get_class().get_name() if asset else "Missing"


def import_body() -> list[str]:
    if not SOURCE_FBX.exists():
        raise RuntimeError(f"Missing FBX: {SOURCE_FBX}")
    ensure_dir(DESTINATION)

    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_as_skeletal", True)
    options.set_editor_property("import_animations", True)
    options.set_editor_property("import_materials", False)
    options.set_editor_property("import_textures", False)
    options.set_editor_property("create_physics_asset", False)
    options.set_editor_property("skeleton", None)

    skeletal_data = options.get_editor_property("skeletal_mesh_import_data")
    if skeletal_data:
        skeletal_data.set_editor_property("convert_scene", True)
        skeletal_data.set_editor_property("convert_scene_unit", True)
        skeletal_data.set_editor_property("import_uniform_scale", 1.0)
        skeletal_data.set_editor_property("update_skeleton_reference_pose", True)
        skeletal_data.set_editor_property("use_t0_as_ref_pose", True)

    anim_data = options.get_editor_property("anim_sequence_import_data")
    if anim_data:
        anim_data.set_editor_property("import_custom_attribute", True)
        anim_data.set_editor_property("convert_scene", True)
        anim_data.set_editor_property("convert_scene_unit", True)

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(SOURCE_FBX))
    task.set_editor_property("destination_path", DESTINATION)
    task.set_editor_property("destination_name", "SK_Player_FirstPersonBody")
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    task.set_editor_property("options", options)

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    return list(task.get_editor_property("imported_object_paths"))


def main() -> None:
    require_asset_write_permission(f"import first-person body assets into {DESTINATION}")
    unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.SyncToBrowser 0")
    imported = import_body()
    assets = unreal.EditorAssetLibrary.list_assets(DESTINATION, recursive=True, include_folder=False)
    lines = [
        "PLAYER_FIRST_PERSON_BODY_IMPORT_REPORT",
        f"Source FBX: {SOURCE_FBX}",
        f"Imported count: {len(imported)}",
    ]
    for path in sorted(imported):
        lines.append(f"Imported: {class_name(path)} {path}")
    lines.append("Destination assets:")
    for path in sorted(assets):
        lines.append(f"- {class_name(path)} {path}")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    unreal.SystemLibrary.quit_editor()


if __name__ == "__main__":
    main()
