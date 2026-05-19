from pathlib import Path

import unreal


LEVEL_PATH = "/Game/Maps/Penance_Suburban_Blockout"
PROJECT_ROOT = Path(__file__).resolve().parents[1]

REPLACED_PLACEHOLDER_LABEL_PARTS = [
    "FirstHouse_LivingRoom_BlockoutSofa",
    "FirstHouse_Table_Candles",
    "FirstHouse_TableFocus_ChairSilhouette",
    "FirstHouse_TableLamp_Base",
    "FirstHouse_TableLamp_Shade",
    "FirstHouse_Clue_BlankFamilyPhoto_Inspectable",
    "FirstHouse_Photo_ContrastBacking",
    "Penance_HoodedWetCloth_4mTall",
    "Penance_CrushedDoorMask",
    "Penance_BackDoorPlank",
    "FirstHousePenance_WetClothBody",
    "FirstHousePenance_DoorMask_ReadSecond",
    "TunnelPenance_WetClothBody",
    "TunnelPenance_DoorMask",
]

REQUIRED_FIXED_LABEL_PARTS = [
    "FirstHouse_Couch_SaggingSeat",
    "FirstHouse_Table_ThickTop",
    "FirstHouse_RightDiningChair_Seat",
    "FirstHouse_PulledOutDiningChair_Seat",
    "FirstHouse_TableLamp_TornWarmShade",
    "FirstHouse_BlankFamilyPhoto_ScrapedFaceVoid",
    "FirstHouse_Table_HandwrittenNote_Paper",
    "Penance_FirstHouseDoorway_AuthoredCarrier",
    "Penance_TunnelPressure_AuthoredCarrier",
    "Penance_FarLightning_AuthoredCarrier",
]


def labels_containing(labels, needle):
    return [label for label in labels if needle in label]


def main():
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(LEVEL_PATH)
    labels = sorted(actor.get_actor_label() for actor in unreal.EditorLevelLibrary.get_all_level_actors())

    stale = {
        needle: labels_containing(labels, needle)
        for needle in REPLACED_PLACEHOLDER_LABEL_PARTS
        if labels_containing(labels, needle)
    }
    missing = [
        needle
        for needle in REQUIRED_FIXED_LABEL_PARTS
        if not labels_containing(labels, needle)
    ]

    fixed_count = len([label for label in labels if "FixedSceneProps" in label or "FirstHouse_Couch_" in label])
    report_lines = [
        "PENANCE_FIXED_PROP_VERIFY",
        f"Actor labels scanned: {len(labels)}",
        f"Required fixed label checks: {len(REQUIRED_FIXED_LABEL_PARTS)}",
        f"Missing fixed labels: {len(missing)}",
        f"Stale placeholder labels: {sum(len(value) for value in stale.values())}",
        f"Approx fixed prop label count: {fixed_count}",
    ]

    if missing:
        report_lines.append("MISSING:")
        report_lines.extend(missing)
    if stale:
        report_lines.append("STALE:")
        for needle, matches in stale.items():
            report_lines.append(f"{needle}: {len(matches)}")

    report = "\n".join(report_lines) + "\n"
    report_path = PROJECT_ROOT / "Saved" / "PenanceFixedPropVerify.txt"
    report_path.write_text(report)
    print(report)

    if missing or stale:
        raise RuntimeError("Fixed prop verification failed")


if __name__ == "__main__":
    main()
