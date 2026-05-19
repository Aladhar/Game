from pathlib import Path

import unreal


PROJECT_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PREFIXES = [
    "/Game/PenanceAssets/Enemies/PenanceCarrier",
    "/Game/PenanceAssets/Enemies/BellSaint",
]

REQUIRED_DIRECTORIES = [
    "/Game/PenanceAssets/Enemies/PenanceCarrier/penance_carrier_end_goal_v21_multi_region_reference_baseline",
    "/Game/PenanceAssets/Enemies/BellSaint/bell_saint_v6h_final_form_pass",
]

REQUIRED_ASSET_NAME_PARTS = [
    "penance_carrier_v2_textured_penance_carrier_body_cloth_basecolor",
    "penance_carrier_v2_textured_penance_carrier_house_wood_basecolor",
    "penance_carrier_v2_textured_penance_carrier_wax_candle_emissive",
]


def list_assets():
    assets = []
    for prefix in REQUIRED_PREFIXES:
        if not unreal.EditorAssetLibrary.does_directory_exist(prefix):
            raise RuntimeError(f"Missing Unreal asset directory: {prefix}")
        assets.extend(unreal.EditorAssetLibrary.list_assets(prefix, recursive=True, include_folder=False))
    return assets


def write_report(assets):
    report_path = PROJECT_ROOT / "Saved" / "PenanceAssetVerify.txt"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["PENANCE_ASSET_VERIFY", f"Assets found: {len(assets)}"]
    lines.extend(sorted(assets))
    report_path.write_text("\n".join(lines) + "\n")


def main():
    assets = list_assets()
    for directory in REQUIRED_DIRECTORIES:
        if not unreal.EditorAssetLibrary.does_directory_exist(directory):
            raise RuntimeError(f"Missing imported Unreal asset directory: {directory}")

    for name_part in REQUIRED_ASSET_NAME_PARTS:
        if not any(name_part in asset_path for asset_path in assets):
            raise RuntimeError(f"Missing imported Unreal asset containing: {name_part}")

    write_report(assets)
    unreal.log(f"Verified Penance assets: {len(assets)}")


if __name__ == "__main__":
    main()
