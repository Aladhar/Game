from pathlib import Path

import unreal


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = PROJECT_ROOT / "Saved" / "PenanceUnrealAssetClassInspect.txt"

ROOTS = [
    "/Game/PenanceAssets/Enemies/PenanceCarrier",
    "/Game/Player",
    "/Game/Animations/Player",
    "/Game/Animations/Enemies",
    "/Game/Map_Assets/Road",
]


def class_name(asset):
    try:
        return asset.get_class().get_name()
    except Exception:
        return type(asset).__name__


def main():
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    lines = ["PENANCE_UNREAL_ASSET_CLASS_INSPECT"]
    class_counts = {}
    for root in ROOTS:
        lines.append(f"Root: {root}")
        if not unreal.EditorAssetLibrary.does_directory_exist(root):
            lines.append("- MISSING")
            continue
        paths = sorted(unreal.EditorAssetLibrary.list_assets(root, recursive=True, include_folder=False))
        lines.append(f"- assets: {len(paths)}")
        for path in paths:
            asset = unreal.EditorAssetLibrary.load_asset(path)
            if not asset:
                data = registry.get_asset_by_object_path(path)
                cls = str(data.asset_class_path.asset_name) if data else "Unknown"
            else:
                cls = class_name(asset)
            class_counts[cls] = class_counts.get(cls, 0) + 1
            lines.append(f"  {cls}: {path}")

    lines.append("Class counts:")
    for cls, count in sorted(class_counts.items()):
        lines.append(f"- {cls}: {count}")

    report = "\n".join(lines) + "\n"
    REPORT_PATH.write_text(report)
    print(report)


if __name__ == "__main__":
    main()
