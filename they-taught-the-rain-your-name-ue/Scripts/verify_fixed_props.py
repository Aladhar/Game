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

REQUIRED_HINGED_DOOR_LABEL_PARTS = [
    "House_01_FirstEnterable_OpenDoor_ParkedLeft",
    "FirstHouse_NewDoor_AppearsWhereWallWas",
    "CommunityChurch_Doors",
    "CommunityChurch_BasementDoor",
    "FinalHouse_DoorMaskFacade",
]

REQUIRED_PICKUP_LABEL_PARTS = [
    "Pickup_BlankFamilyPhoto",
    "Pickup_HandwrittenNote",
    "Pickup_WetChildBlanket",
    "Pickup_RustedRecordTag",
    "Pickup_InternalHandlingNotice",
]

PENANCE_CHARACTER_LABEL_PARTS = [
    "Penance_FarLightning_AuthoredCarrier",
    "Penance_FirstHouseDoorway_AuthoredCarrier",
    "Penance_TunnelPressure_AuthoredCarrier",
    "ReadableProxy",
]


def labels_containing(labels, needle):
    return [label for label in labels if needle in label]


def folder_path(actor):
    try:
        return str(actor.get_folder_path())
    except Exception:
        return ""


def class_name(actor):
    try:
        return actor.get_class().get_name()
    except Exception:
        return ""


def main():
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(LEVEL_PATH)
    actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
    labels = sorted(actor.get_actor_label() for actor in actors)

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
    missing_hinged_doors = [
        needle
        for needle in REQUIRED_HINGED_DOOR_LABEL_PARTS
        if not any(needle in actor.get_actor_label() and class_name(actor) == "PenanceHingedDoor" for actor in actors)
    ]
    missing_pickups = [
        needle
        for needle in REQUIRED_PICKUP_LABEL_PARTS
        if not any(needle in actor.get_actor_label() and class_name(actor) == "PenancePickupItem" for actor in actors)
    ]
    bad_penance_folders = [
        actor.get_actor_label()
        for actor in actors
        if any(needle in actor.get_actor_label() for needle in PENANCE_CHARACTER_LABEL_PARTS)
        and "PenanceImported/Penance" not in folder_path(actor)
    ]
    bad_door_folders = [
        actor.get_actor_label()
        for actor in actors
        if class_name(actor) == "PenanceHingedDoor" and "PenanceImported/Doors/Hinged" not in folder_path(actor)
    ]

    fixed_count = len([label for label in labels if "FixedSceneProps" in label or "FirstHouse_Couch_" in label])
    hinged_door_count = len([actor for actor in actors if class_name(actor) == "PenanceHingedDoor"])
    pickup_count = len([actor for actor in actors if class_name(actor) == "PenancePickupItem"])
    report_lines = [
        "PENANCE_FIXED_PROP_VERIFY",
        f"Actor labels scanned: {len(labels)}",
        f"Required fixed label checks: {len(REQUIRED_FIXED_LABEL_PARTS)}",
        f"Missing fixed labels: {len(missing)}",
        f"Required hinged door checks: {len(REQUIRED_HINGED_DOOR_LABEL_PARTS)}",
        f"Missing hinged doors: {len(missing_hinged_doors)}",
        f"Required pickup checks: {len(REQUIRED_PICKUP_LABEL_PARTS)}",
        f"Missing pickups: {len(missing_pickups)}",
        f"Stale placeholder labels: {sum(len(value) for value in stale.values())}",
        f"Approx fixed prop label count: {fixed_count}",
        f"Hinged door actor count: {hinged_door_count}",
        f"Pickup actor count: {pickup_count}",
        f"Bad Penance folders: {len(bad_penance_folders)}",
        f"Bad hinged door folders: {len(bad_door_folders)}",
    ]

    if missing:
        report_lines.append("MISSING:")
        report_lines.extend(missing)
    if missing_hinged_doors:
        report_lines.append("MISSING_HINGED_DOORS:")
        report_lines.extend(missing_hinged_doors)
    if missing_pickups:
        report_lines.append("MISSING_PICKUPS:")
        report_lines.extend(missing_pickups)
    if bad_penance_folders:
        report_lines.append("BAD_PENANCE_FOLDERS:")
        report_lines.extend(bad_penance_folders[:20])
    if bad_door_folders:
        report_lines.append("BAD_DOOR_FOLDERS:")
        report_lines.extend(bad_door_folders[:20])
    if stale:
        report_lines.append("STALE:")
        for needle, matches in stale.items():
            report_lines.append(f"{needle}: {len(matches)}")

    report = "\n".join(report_lines) + "\n"
    report_path = PROJECT_ROOT / "Saved" / "PenanceFixedPropVerify.txt"
    report_path.write_text(report)
    print(report)

    if missing or missing_hinged_doors or missing_pickups or bad_penance_folders or bad_door_folders or stale:
        raise RuntimeError("Fixed prop verification failed")


if __name__ == "__main__":
    main()
