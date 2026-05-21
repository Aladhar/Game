from pathlib import Path

import unreal


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_FBX = PROJECT_ROOT / "Built" / "FBX" / "SK_Player_FirstPersonBody.fbx"
DESTINATION = "/Game/Player/FirstPerson"
SKELETON_PATH = "/Game/Player/FirstPerson/SK_Player_FirstPersonBody_Skeleton"
FALLBACK_ANIM = "/Game/Player/FirstPerson/AN_Player_Walk_Verify"
REPORT = PROJECT_ROOT / "Saved" / "PlayerLocomotionAssetImportReport.txt"

ANIM_SPECS = [
    ("AN_Player_Idle_FeetTogether", "held at the existing feet-together pose by ABP_Player"),
    ("AN_Player_Idle_Staggered", "optional idle source placeholder"),
    ("AN_Player_StartWalk_Forward", "forward start source"),
    ("AN_Player_Walk_Forward_Loop", "forward loop source"),
    ("AN_Player_Walk_Backward_Loop", "backward loop source"),
    ("AN_Player_StopWalk_Forward", "forward stop source"),
    ("AN_Player_TurnInPlace_Left", "turn-left source, ABP can keep idle if not good"),
    ("AN_Player_TurnInPlace_Right", "turn-right source, ABP can keep idle if not good"),
]


def ensure_dir(path: str) -> None:
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def load_asset(path: str):
    return unreal.EditorAssetLibrary.load_asset(path)


def set_if_present(obj, prop: str, value) -> bool:
    try:
        obj.set_editor_property(prop, value)
        return True
    except Exception:
        return False


def replace_with_anim_duplicate(name: str) -> str:
    target_path = f"{DESTINATION}/{name}"
    source = load_asset(FALLBACK_ANIM)
    if not source:
        return "Missing"

    if load_asset(target_path):
        unreal.EditorAssetLibrary.delete_asset(target_path)
    if not unreal.EditorAssetLibrary.duplicate_asset(FALLBACK_ANIM, target_path):
        return "Missing"
    unreal.EditorAssetLibrary.save_asset(target_path)
    return target_path


def create_abp_shell(lines: list[str], skeleton) -> None:
    target_path = f"{DESTINATION}/ABP_Player"
    if load_asset(target_path):
        lines.append(f"ABP shell exists: {target_path}")
        return

    try:
        factory = unreal.AnimBlueprintFactory()
        set_if_present(factory, "target_skeleton", skeleton)
        parent_class = unreal.load_class(None, "/Script/PenanceDemoUE.ABP_Player")
        if parent_class:
            set_if_present(factory, "parent_class", parent_class)
        asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset("ABP_Player", DESTINATION, unreal.AnimBlueprint, factory)
        if asset:
            unreal.EditorAssetLibrary.save_asset(target_path)
            lines.append(f"Created ABP shell: {target_path}")
        else:
            lines.append("Created ABP shell: failed")
    except Exception as exc:
        lines.append(f"Created ABP shell: failed ({exc})")


def main() -> None:
    unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.SyncToBrowser 0")
    if not SOURCE_FBX.exists():
        raise RuntimeError(f"Missing source FBX: {SOURCE_FBX}")

    ensure_dir(DESTINATION)
    skeleton = load_asset(SKELETON_PATH)
    if not skeleton:
        raise RuntimeError(f"Missing skeleton: {SKELETON_PATH}")

    lines = [
        "PLAYER_LOCOMOTION_ASSET_IMPORT_REPORT",
        f"Source FBX: {SOURCE_FBX}",
        f"Skeleton: {SKELETON_PATH}",
        f"Source animation duplicated: {FALLBACK_ANIM}",
        "Note: Blender 4.5 crashed before Python startup on this Mac, so this pass creates valid named AnimSequence assets from the current fixed Player verify animation. ABP_Player already selects separate forward/backward/start/stop/turn asset slots so improved authored clips can replace these one-for-one.",
        "Assets:",
    ]

    for name, purpose in ANIM_SPECS:
        final_path = replace_with_anim_duplicate(name)
        asset = load_asset(final_path)
        asset_class = asset.get_class().get_name() if asset else "Missing"
        try:
            length = asset.get_editor_property("sequence_length") if asset_class == "AnimSequence" else "n/a"
        except Exception:
            length = "unknown"
        lines.append(f"- {name}: purpose={purpose} path={final_path} class={asset_class} length={length}")

    create_abp_shell(lines, skeleton)

    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    unreal.SystemLibrary.quit_editor()


if __name__ == "__main__":
    main()
