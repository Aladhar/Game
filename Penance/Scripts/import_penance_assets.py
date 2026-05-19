from pathlib import Path

import unreal


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GODOT_ROOT = PROJECT_ROOT.parent / "they-taught-the-rain-your-name"
UE_ASSET_ROOT = "/Game/PenanceAssets"

ASSET_SPECS = [
    {
        "name": "PenanceCarrier_Current",
        "source": GODOT_ROOT / "assets/models/enemies/penance_carrier/penance_carrier_end_goal_v21_multi_region_reference_baseline.glb",
        "destination": f"{UE_ASSET_ROOT}/Enemies/PenanceCarrier",
    },
    {
        "name": "BellSaint_Current",
        "source": GODOT_ROOT / "assets/models/enemies/bell_saint/bell_saint_v6h_final_form_pass.glb",
        "destination": f"{UE_ASSET_ROOT}/Enemies/BellSaint",
    },
]

TEXTURE_SPECS = [
    {
        "source_dir": GODOT_ROOT / "assets/models/enemies/penance_carrier",
        "pattern": "penance_carrier_v2_textured_*.png",
        "destination": f"{UE_ASSET_ROOT}/Enemies/PenanceCarrier/Textures",
    },
]


def disable_browser_sync():
    # UE 5.7 Interchange overrides AssetImportTask's bSyncToBrowser=false with
    # this CVar. In commandlets there is no Slate application, so browser sync
    # crashes after a successful import.
    unreal.SystemLibrary.execute_console_command(
        None,
        "Interchange.FeatureFlags.Import.SyncToBrowser 0",
    )


def ensure_directory(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def import_file(source_path, destination_path):
    if not source_path.exists():
        raise RuntimeError(f"Missing source asset: {source_path}")

    ensure_directory(destination_path)
    existing_paths = list(
        unreal.EditorAssetLibrary.list_assets(destination_path, recursive=True, include_folder=False)
    )
    source_stem = source_path.stem
    source_folder = f"{destination_path}/{source_stem}"
    if unreal.EditorAssetLibrary.does_directory_exist(source_folder):
        return existing_paths
    if any(source_stem in asset_path for asset_path in existing_paths):
        return existing_paths

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(source_path))
    task.set_editor_property("destination_path", destination_path)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    imported_paths = list(task.get_editor_property("imported_object_paths"))
    if not imported_paths:
        raise RuntimeError(f"Unreal imported no assets from: {source_path}")

    return imported_paths


def make_import_task(source_path, destination_path):
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(source_path))
    task.set_editor_property("destination_path", destination_path)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    return task


def has_imported_asset(source_path, destination_path):
    existing_paths = list(
        unreal.EditorAssetLibrary.list_assets(destination_path, recursive=True, include_folder=False)
    )
    source_stem = source_path.stem
    source_stem_without_resolution = source_stem.removesuffix("_1024").removesuffix("_512")
    source_folder = f"{destination_path}/{source_stem}"
    return (
        unreal.EditorAssetLibrary.does_directory_exist(source_folder)
        or any(source_stem in asset_path for asset_path in existing_paths)
        or any(source_stem_without_resolution in asset_path for asset_path in existing_paths)
    )


def import_named_assets():
    imported = []
    for spec in ASSET_SPECS:
        imported.extend(import_file(spec["source"], spec["destination"]))
    return imported


def import_textures():
    imported = []
    for spec in TEXTURE_SPECS:
        source_dir = spec["source_dir"]
        if not source_dir.exists():
            raise RuntimeError(f"Missing texture source directory: {source_dir}")

        texture_paths = sorted(source_dir.glob(spec["pattern"]))
        if not texture_paths:
            raise RuntimeError(f"No textures matched {spec['pattern']} in {source_dir}")

        ensure_directory(spec["destination"])
        tasks = []
        for texture_path in texture_paths:
            if has_imported_asset(texture_path, spec["destination"]):
                continue
            tasks.append(make_import_task(texture_path, spec["destination"]))

        if tasks:
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)

        imported.extend(
            unreal.EditorAssetLibrary.list_assets(spec["destination"], recursive=True, include_folder=False)
        )
    return imported


def write_report(imported_paths):
    report_path = PROJECT_ROOT / "Saved" / "PenanceAssetImportReport.txt"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["PENANCE_ASSET_IMPORT_REPORT", f"Imported assets: {len(imported_paths)}"]
    lines.extend(sorted(imported_paths))
    report_path.write_text("\n".join(lines) + "\n")


def main():
    disable_browser_sync()
    ensure_directory(UE_ASSET_ROOT)
    imported_paths = []
    imported_paths.extend(import_named_assets())
    imported_paths.extend(import_textures())
    write_report(imported_paths)
    unreal.log(f"Imported Penance assets: {len(imported_paths)}")


if __name__ == "__main__":
    main()
