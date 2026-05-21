from pathlib import Path

import unreal


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ANIM = "/Game/Player/FirstPerson/SK_Player_FirstPersonBody_Anim"
VERIFY_ANIM = "/Game/Player/FirstPerson/AN_Player_Walk_Verify"
PREVIEW_MAP = "/Game/Maps/Player_WalkAnimation_Verify"
REPORT = PROJECT_ROOT / "Saved" / "PlayerWalkAnimationPreviewSetupReport.txt"


def load_asset(path: str):
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if not asset:
        raise RuntimeError(f"Missing asset: {path}")
    return asset


def ensure_verify_animation():
    anim = unreal.EditorAssetLibrary.load_asset(VERIFY_ANIM)
    if anim:
        return anim

    if not unreal.EditorAssetLibrary.does_asset_exist(SOURCE_ANIM):
        raise RuntimeError(f"Missing source animation: {SOURCE_ANIM}")

    anim = unreal.EditorAssetLibrary.duplicate_asset(SOURCE_ANIM, VERIFY_ANIM)
    if not anim:
        raise RuntimeError(f"Failed to duplicate {SOURCE_ANIM} to {VERIFY_ANIM}")

    unreal.EditorAssetLibrary.save_asset(VERIFY_ANIM)
    return anim


def setup_map(anim) -> None:
    if not unreal.EditorLevelLibrary.new_level(PREVIEW_MAP):
        raise RuntimeError(f"Failed to create level: {PREVIEW_MAP}")

    preview_class = unreal.load_class(None, "/Script/PenanceDemoUE.PenancePlayerWalkPreviewActor")
    if not preview_class:
        raise RuntimeError("PenancePlayerWalkPreviewActor class is unavailable. Build the editor target first.")

    unreal.EditorLoadingAndSavingUtils.save_current_level()


def main() -> None:
    unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.SyncToBrowser 0")

    mesh = load_asset("/Game/Player/FirstPerson/SK_Player_FirstPersonBody")
    anim = ensure_verify_animation()
    setup_map(anim)

    lines = [
        "PLAYER_WALK_ANIMATION_PREVIEW_SETUP_REPORT",
        f"Preview map: {PREVIEW_MAP}",
        f"Preview actor class: /Script/PenanceDemoUE.PenancePlayerWalkPreviewActor",
        f"Skeletal mesh: {mesh.get_path_name()}",
        f"Animation source: {SOURCE_ANIM}",
        f"Playable animation asset: {anim.get_path_name()}",
        f"Open this map and press Play: {PREVIEW_MAP}",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    unreal.SystemLibrary.quit_editor()


if __name__ == "__main__":
    main()
