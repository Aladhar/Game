import json
from pathlib import Path

import unreal

from penance_script_safety import require_asset_write_permission


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEVEL_PATH = "/Game/Maps/Penance_Suburban_Blockout"
BACKUP_LEVEL_PATH = "/Game/Maps/Penance_Suburban_Blockout_Step8_Backup"
REPORT_PATH = PROJECT_ROOT / "Saved" / "PenanceStep8LayoutReport.txt"
EXPORT_PATH = PROJECT_ROOT / "Content" / "PenanceBlockoutExport.json"


def godot_to_unreal(vec):
    return unreal.Vector(-float(vec[2]) * 100.0, float(vec[0]) * 100.0, float(vec[1]) * 100.0)


def unreal_to_godot(vec):
    return [float(vec.y) / 100.0, float(vec.z) / 100.0, -float(vec.x) / 100.0]


def sanitize_name(value):
    return str(value).replace(" ", "_")


def actor_class_name(actor):
    return actor.get_class().get_name()


def imported_name(actor):
    for tag in actor.tags:
        value = str(tag)
        if value.startswith("ImportedName_"):
            return value[len("ImportedName_") :]
    label = actor.get_actor_label()
    if label.startswith("Penance_"):
        return label[len("Penance_") :]
    return label


def duplicate_backup_once():
    if unreal.EditorAssetLibrary.does_asset_exist(BACKUP_LEVEL_PATH):
        return False
    if not unreal.EditorAssetLibrary.does_asset_exist(LEVEL_PATH):
        raise RuntimeError(f"Missing level: {LEVEL_PATH}")
    if not unreal.EditorAssetLibrary.duplicate_asset(LEVEL_PATH, BACKUP_LEVEL_PATH):
        raise RuntimeError(f"Failed to create backup level: {BACKUP_LEVEL_PATH}")
    unreal.EditorAssetLibrary.save_asset(BACKUP_LEVEL_PATH)
    return True


def load_level():
    subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    subsystem.load_level(LEVEL_PATH)


def load_baseline_positions():
    with EXPORT_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    positions = {}
    for item in data.get("meshes", []):
        position = item.get("position")
        name = item.get("name")
        if name and position:
            positions[name] = (
                float(position["x"]),
                float(position["y"]),
                float(position["z"]),
            )

    for item in data.get("lights", []):
        position = item.get("position")
        name = item.get("name")
        if name and position:
            positions[name] = (
                float(position["x"]),
                float(position["y"]),
                float(position["z"]),
            )

    player = data.get("player_start", {})
    player_position = player.get("position")
    if player_position:
        positions["PlayerStart_FromGodot"] = (
            float(player_position["x"]),
            float(player_position["y"]),
            float(player_position["z"]),
        )

    return positions


def set_location_godot(actor, x, y, z):
    actor.modify()
    actor.set_actor_location(godot_to_unreal((x, y, z)), False, True)


def set_box_scale(actor, size_x, size_y, size_z):
    actor.modify()
    actor.set_actor_scale3d(unreal.Vector(float(size_z), float(size_x), float(size_y)))


def set_cylinder_scale(actor, radius, height):
    actor.modify()
    actor.set_actor_scale3d(unreal.Vector(float(radius) * 2.0, float(radius) * 2.0, float(height)))


def set_folder(actor, folder):
    actor.modify()
    actor.set_folder_path(folder)


def assign_folder(actor, name):
    cls = actor_class_name(actor)
    if cls == "PlayerStart":
        set_folder(actor, "01_Player")
        return
    if cls in {"PenanceProgressionManager", "PenanceProgressionTrigger", "PenancePickupItem"}:
        set_folder(actor, "02_GameplayFlow")
        return
    if "Light" in cls or "Light" in name:
        set_folder(actor, "04_Lighting")
        return
    if "Audio" in cls or "Sound" in cls or "Audio" in name or "Sound" in name:
        set_folder(actor, "05_Audio")
        return
    if "Penance" in name or "Chase" in name:
        set_folder(actor, "07_Encounters")
        return
    if (
        "RouteGate" in name
        or "SoftBlock" in name
        or "SoftFunnel" in name
        or "Fence" in name
        or "Blocker" in name
    ):
        set_folder(actor, "09_Blockers_Gates")
        return
    if "Road" in name or "Sidewalk" in name or "Ground" in name or "Puddle" in name or "Path" in name:
        set_folder(actor, "03_Environment/Roads")
        return
    if name.startswith("Park_"):
        set_folder(actor, "03_Environment/Park")
        return
    if name.startswith("Church_") or "Church" in name:
        set_folder(actor, "03_Environment/ChurchExterior")
        return
    if name.startswith("House_") or name.startswith("FirstHouse") or name.startswith("FinalHouse"):
        set_folder(actor, "03_Environment/Neighborhood")
        return
    if cls == "TextRenderActor":
        set_folder(actor, "10_Debug")
        return
    set_folder(actor, "00_Persistent")


ROAD_TARGETS = {
    "NeighborhoodGround_150m_x_180m": ((0.0, -0.08, -8.0), ("box", 105.0, 0.12, 145.0)),
    "MainLoop_Road_South": ((0.0, 0.0, 22.0), ("box", 78.0, 0.08, 7.0)),
    "MainLoop_Road_North": ((0.0, 0.0, -34.0), ("box", 78.0, 0.08, 7.0)),
    "MainLoop_Road_West": ((-34.0, 0.0, -6.0), ("box", 7.0, 0.08, 56.0)),
    "MainLoop_Road_East": ((34.0, 0.0, -6.0), ("box", 7.0, 0.08, 56.0)),
    "CulDeSac_ConnectorRoad": ((-42.0, 0.0, -12.0), ("box", 18.0, 0.08, 7.0)),
    "CulDeSac_RoadCircle_32m": ((-52.0, 0.0, -12.0), ("cylinder", 12.0, 0.08)),
    "ParkLoop_Path_NorthSouth": ((-22.0, 0.07, -6.0), ("box", 3.0, 0.08, 20.0)),
    "ParkLoop_Path_EastWest": ((-22.0, 0.08, -6.0), ("box", 22.0, 0.08, 3.0)),
    "FinalHouse_Unreachable_RoadStub_Locked": ((0.0, 0.0, -52.0), ("box", 18.0, 0.08, 7.0)),
    "FinalHouse_RoadExtension_AppearsLater": ((0.0, 0.0, -64.0), ("box", 20.0, 0.08, 7.0)),
}

EXACT_TARGETS = {
    "PlayerStart_FromGodot": (0.0, 1.0918, 58.0),
    "Event_FirstHouse_FrontApproach": (18.0, 1.2, 37.0),
    "Event_FirstHouse_Entry": (18.0, 1.2, 33.1),
    "Event_FirstHouse_HallwayStretch": (18.0, 1.2, 21.0),
    "Event_FirstHouse_DoorAppearsInWall": (18.0, 1.2, 23.0),
    "Interact_FirstHouse_BlankPhoto": (19.65, 1.1, 30.65),
    "Event_Park_LightsFlicker": (-22.0, 1.2, -6.0),
    "Interact_Park_DrainEvidence": (-27.5, 0.8, -5.5),
    "Event_CulDeSac_LightningPenanceAngle": (-52.0, 1.2, -12.0),
    "Event_Lightning_RevealsPenance_LongSightline": (-2.0, 1.2, -36.0),
    "Event_RoadsLoop_NorthExit_TeleportBeforeUnlock": (0.0, 1.2, -52.0),
    "Event_Church_Threshold": (28.0, 1.2, 8.0),
    "Interact_Church_InternalHandlingNotice": (28.0, 1.2, 5.0),
    "Event_Church_BasementEntrance": (22.0, 1.2, -2.0),
    "Event_Tunnel_PressureStarts": (-28.0, -2.5, -16.0),
    "Event_TunnelExit_FinalHouseBecomesReachable": (4.0, -2.4, -62.0),
    "Interact_TunnelExit_FosterHouseMonitor": (4.0, -1.6, -60.5),
    "Event_FosterHouse_FinalApproach": (0.0, 1.2, -72.0),
    "RouteGate_ToPark_BlockedUntilHouse": (-3.0, 1.5, 22.0),
    "RouteGate_ToCulDeSac_BlockedUntilPark": (-38.0, 1.5, -12.0),
    "RouteGate_ToChurch_BlockedUntilCulDeSac": (31.0, 1.5, 8.0),
    "RouteGate_ToBasement_BlockedUntilChurch": (22.0, 1.5, -2.0),
    "Church_RustedDoorBlocker_LockedUntilCulDeSac": (28.0, 1.5, 7.4),
    "SoftBlock_ToPark_StormSheetUntilPhoto": (-3.0, 1.3, 22.8),
    "SoftBlock_ToPark_StormSheetUntilPhoto_SaggingChainTop": (-3.0, 2.4, 22.8),
    "SoftBlock_ToPark_StormSheetUntilPhoto_WaterAtBase": (-3.0, 0.1, 22.8),
    "SoftBlock_ToPark_StormSheetUntilPhoto_CandleMarker": (-3.0, 0.3, 22.8),
    "SoftBlock_ToPark_StormSheetUntilPhoto_CandleMarkerLight": (-3.0, 0.8, 22.8),
    "SoftBlock_ToCulDeSac_FloodedConnectorUntilPark": (-38.0, 1.3, -12.0),
    "SoftBlock_ToCulDeSac_FloodedConnectorUntilPark_SaggingChainTop": (-38.0, 2.4, -12.0),
    "SoftBlock_ToCulDeSac_FloodedConnectorUntilPark_WaterAtBase": (-38.0, 0.1, -12.0),
    "SoftBlock_ToCulDeSac_FloodedConnectorUntilPark_CandleMarker": (-38.0, 0.3, -12.0),
    "SoftBlock_ToCulDeSac_FloodedConnectorUntilPark_CandleMarkerLight": (-38.0, 0.8, -12.0),
    "SoftBlock_EastLoop_FloodedStreetUntilCulDeSac": (28.0, 1.3, 22.0),
    "SoftBlock_EastLoop_FloodedStreetUntilCulDeSac_SaggingChainTop": (28.0, 2.4, 22.0),
    "SoftBlock_EastLoop_FloodedStreetUntilCulDeSac_WaterAtBase": (28.0, 0.1, 22.0),
    "SoftBlock_EastLoop_FloodedStreetUntilCulDeSac_CandleMarker": (28.0, 0.3, 22.0),
    "SoftBlock_EastLoop_FloodedStreetUntilCulDeSac_CandleMarkerLight": (28.0, 0.8, 22.0),
    "SoftBlock_ToChurch_ClothWallUntilCulDeSac": (31.0, 1.3, 8.0),
    "SoftBlock_ToChurch_ClothWallUntilCulDeSac_SaggingChainTop": (31.0, 2.4, 8.0),
    "SoftBlock_ToChurch_ClothWallUntilCulDeSac_WaterAtBase": (31.0, 0.1, 8.0),
    "SoftBlock_ToChurch_ClothWallUntilCulDeSac_CandleMarker": (31.0, 0.3, 8.0),
    "SoftBlock_ToChurch_ClothWallUntilCulDeSac_CandleMarkerLight": (31.0, 0.8, 8.0),
    "SoftBlock_ToBasement_ChainedStairUntilChurch": (22.0, 1.3, -2.0),
    "SoftBlock_ToBasement_ChainedStairUntilChurch_SaggingChainTop": (22.0, 2.4, -2.0),
    "SoftBlock_ToBasement_ChainedStairUntilChurch_WaterAtBase": (22.0, 0.1, -2.0),
    "SoftBlock_ToBasement_ChainedStairUntilChurch_CandleMarker": (22.0, 0.3, -2.0),
    "SoftBlock_ToBasement_ChainedStairUntilChurch_CandleMarkerLight": (22.0, 0.8, -2.0),
    "SoftFunnel_WestLoop_NorthWrongWay": (-34.0, 1.3, -28.0),
    "SoftFunnel_WestLoop_NorthWrongWay_SaggingChainTop": (-34.0, 2.4, -28.0),
    "SoftFunnel_WestLoop_NorthWrongWay_WaterAtBase": (-34.0, 0.1, -28.0),
    "SoftFunnel_WestLoop_NorthWrongWay_CandleMarker": (-34.0, 0.3, -28.0),
    "SoftFunnel_WestLoop_NorthWrongWay_CandleMarkerLight": (-34.0, 0.8, -28.0),
    "SoftFunnel_WestLoop_SouthWrongWay": (-34.0, 1.3, 10.0),
    "SoftFunnel_WestLoop_SouthWrongWay_SaggingChainTop": (-34.0, 2.4, 10.0),
    "SoftFunnel_WestLoop_SouthWrongWay_WaterAtBase": (-34.0, 0.1, 10.0),
    "SoftFunnel_WestLoop_SouthWrongWay_CandleMarker": (-34.0, 0.3, 10.0),
    "SoftFunnel_WestLoop_SouthWrongWay_CandleMarkerLight": (-34.0, 0.8, 10.0),
    "SoftFunnel_CulDeSac_NorthLawnNoBypass": (-50.0, 1.3, -24.0),
    "SoftFunnel_CulDeSac_NorthLawnNoBypass_SaggingChainTop": (-50.0, 2.4, -24.0),
    "SoftFunnel_CulDeSac_NorthLawnNoBypass_WaterAtBase": (-50.0, 0.1, -24.0),
    "SoftFunnel_CulDeSac_NorthLawnNoBypass_CandleMarker": (-50.0, 0.3, -24.0),
    "SoftFunnel_CulDeSac_NorthLawnNoBypass_CandleMarkerLight": (-50.0, 0.8, -24.0),
    "SoftFunnel_CulDeSac_SouthLawnNoBypass": (-50.0, 1.3, 0.0),
    "SoftFunnel_CulDeSac_SouthLawnNoBypass_SaggingChainTop": (-50.0, 2.4, 0.0),
    "SoftFunnel_CulDeSac_SouthLawnNoBypass_WaterAtBase": (-50.0, 0.1, 0.0),
    "SoftFunnel_CulDeSac_SouthLawnNoBypass_CandleMarker": (-50.0, 0.3, 0.0),
    "SoftFunnel_CulDeSac_SouthLawnNoBypass_CandleMarkerLight": (-50.0, 0.8, 0.0),
    "SoftFunnel_EastLoop_NorthWrongWay": (34.0, 1.3, -18.0),
    "SoftFunnel_EastLoop_NorthWrongWay_SaggingChainTop": (34.0, 2.4, -18.0),
    "SoftFunnel_EastLoop_NorthWrongWay_WaterAtBase": (34.0, 0.1, -18.0),
    "SoftFunnel_EastLoop_NorthWrongWay_CandleMarker": (34.0, 0.3, -18.0),
    "SoftFunnel_EastLoop_NorthWrongWay_CandleMarkerLight": (34.0, 0.8, -18.0),
    "SoftFunnel_EastLoop_SouthWrongWay": (34.0, 1.3, 25.0),
    "SoftFunnel_EastLoop_SouthWrongWay_SaggingChainTop": (34.0, 2.4, 25.0),
    "SoftFunnel_EastLoop_SouthWrongWay_WaterAtBase": (34.0, 0.1, 25.0),
    "SoftFunnel_EastLoop_SouthWrongWay_CandleMarker": (34.0, 0.3, 25.0),
    "SoftFunnel_EastLoop_SouthWrongWay_CandleMarkerLight": (34.0, 0.8, 25.0),
}

PREFIX_DELTAS = [
    ("House_01_", (-6.0, -6.0)),
    ("FirstHouse", (-6.0, -6.0)),
    ("House_02_", (10.0, -6.0)),
    ("House_03_", (-22.0, 3.0)),
    ("House_04_", (-22.0, 10.0)),
    ("House_05_", (-9.0, 26.0)),
    ("House_06_", (2.0, 26.0)),
    ("House_07_", (11.0, 27.0)),
    ("House_08_", (23.0, 8.0)),
    ("House_09_", (23.0, -4.0)),
    ("House_10_", (5.0, 1.0)),
    ("Park_", (6.0, 6.0)),
    ("CulDeSac_", (34.0, 3.0)),
    ("Roadside_RottenDoorShrine_A", (10.0, -6.0)),
    ("Roadside_RottenDoorShrine_B", (23.0, -4.0)),
    ("Church_", (-6.0, -6.0)),
    ("FinalHouse_", (0.0, 40.0)),
    ("Penance_", (0.0, 23.0)),
]


def apply_layout():
    baseline_positions = load_baseline_positions()
    actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
    moved = []
    scaled = []
    foldered = 0
    skipped_prefix_moves = []

    for actor in actors:
        name = imported_name(actor)
        assign_folder(actor, name)
        foldered += 1

        if name in ROAD_TARGETS:
            target, scale_spec = ROAD_TARGETS[name]
            set_location_godot(actor, *target)
            if scale_spec[0] == "box":
                _shape, sx, sy, sz = scale_spec
                set_box_scale(actor, sx, sy, sz)
            else:
                _shape, radius, height = scale_spec
                set_cylinder_scale(actor, radius, height)
            moved.append(name)
            scaled.append(name)
            continue

        if name in EXACT_TARGETS:
            set_location_godot(actor, *EXACT_TARGETS[name])
            moved.append(name)
            continue

        for prefix, delta in PREFIX_DELTAS:
            if name.startswith(prefix):
                baseline = baseline_positions.get(name)
                if baseline:
                    x, y, z = baseline
                    set_location_godot(actor, x + delta[0], y, z + delta[1])
                    moved.append(name)
                else:
                    skipped_prefix_moves.append(name)
                break

    unreal.EditorLoadingAndSavingUtils.save_current_level()
    unreal.EditorAssetLibrary.save_asset(LEVEL_PATH, only_if_is_dirty=False)
    return {
        "actors": len(actors),
        "moved": len(moved),
        "scaled": len(scaled),
        "foldered": foldered,
        "moved_names": moved,
        "scaled_names": scaled,
        "skipped_prefix_moves": skipped_prefix_moves,
    }


def write_report(backup_created, stats):
    lines = [
        "PENANCE_STEP8_LAYOUT_REFINEMENT",
        f"Edited level: {LEVEL_PATH}",
        f"Backup level: {BACKUP_LEVEL_PATH}",
        f"Backup created this run: {backup_created}",
        "Scope: layout, spacing, scale, navigation only; no church/road/GLB replacements.",
        "Design changes:",
        "- Reduced neighborhood ground from roughly 150x180m to 105x145m while keeping edge margin for start/final approach.",
        "- Tightened main road loop from roughly 104x80m to 68x56m.",
        "- Pulled first house/player approach closer together.",
        "- Pulled park, cul-de-sac, church approach, final-house/Penance route inward.",
        "- Kept church area as placeholder with reserved exterior space.",
        "- Reorganized actors into Step 8 outliner folders.",
        f"Actors scanned: {stats['actors']}",
        f"Actors moved: {stats['moved']}",
        f"Actors scaled: {stats['scaled']}",
        f"Actors foldered: {stats['foldered']}",
        "Scaled actors:",
        *stats["scaled_names"],
    ]
    if stats["skipped_prefix_moves"]:
        sample = stats["skipped_prefix_moves"][:25]
        lines.extend(
            [
                f"Prefix-move actors left in place because they were not in PenanceBlockoutExport.json: {len(stats['skipped_prefix_moves'])}",
                "Skipped prefix-move sample:",
                *sample,
            ]
        )
    REPORT_PATH.write_text("\n".join(lines) + "\n")


def main():
    require_asset_write_permission(f"refine and save Step 8 layout in {LEVEL_PATH}")
    backup_created = duplicate_backup_once()
    load_level()
    stats = apply_layout()
    write_report(backup_created, stats)
    unreal.log("Penance Step 8 layout refinement complete.")
    unreal.log(f"Edited level: {LEVEL_PATH}")
    unreal.log(f"Backup level: {BACKUP_LEVEL_PATH}")


if __name__ == "__main__":
    main()
