from math import sqrt
from pathlib import Path

import unreal


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEVEL_PATH = "/Game/Maps/Penance_Suburban_Blockout"
BACKUP_LEVEL_PATH = "/Game/Maps/Penance_Suburban_Blockout_Step8_Backup"
REPORT_PATH = PROJECT_ROOT / "Saved" / "PenanceStep8LayoutVerify.txt"


EXPECTED_POSITIONS = {
    "PlayerStart_FromGodot": (0.0, 1.0918, 58.0),
    "Event_FirstHouse_FrontApproach": (18.0, 1.2, 37.0),
    "RouteGate_ToPark_BlockedUntilHouse": (-3.0, 1.5, 22.0),
    "Event_Park_LightsFlicker": (-22.0, 1.2, -6.0),
    "Event_CulDeSac_LightningPenanceAngle": (-52.0, 1.2, -12.0),
    "Event_Church_Threshold": (28.0, 1.2, 8.0),
    "Event_TunnelExit_FinalHouseBecomesReachable": (4.0, -2.4, -62.0),
    "Event_FosterHouse_FinalApproach": (0.0, 1.2, -72.0),
}

EXPECTED_SCALES = {
    "NeighborhoodGround_150m_x_180m": (145.0, 105.0, 0.12),
    "MainLoop_Road_South": (7.0, 78.0, 0.08),
    "MainLoop_Road_North": (7.0, 78.0, 0.08),
    "MainLoop_Road_West": (56.0, 7.0, 0.08),
    "MainLoop_Road_East": (56.0, 7.0, 0.08),
}

EXPECTED_FOLDERS = {
    "PlayerStart_FromGodot": "01_Player",
    "Event_FirstHouse_FrontApproach": "02_GameplayFlow",
    "Event_Park_LightsFlicker": "02_GameplayFlow",
    "MainLoop_Road_South": "03_Environment/Roads",
    "CommunityChurch_MainHall_14x18m": "03_Environment/ChurchExterior",
    "RouteGate_ToChurch_BlockedUntilCulDeSac": "09_Blockers_Gates",
}

ROUTE_POINTS = [
    ("start_to_first_house", "PlayerStart_FromGodot", "Event_FirstHouse_FrontApproach", 35.0),
    ("first_house_gate_to_park", "RouteGate_ToPark_BlockedUntilHouse", "Event_Park_LightsFlicker", 40.0),
    ("park_to_cul_de_sac", "Event_Park_LightsFlicker", "Event_CulDeSac_LightningPenanceAngle", 40.0),
    ("cul_de_sac_to_church", "Event_CulDeSac_LightningPenanceAngle", "Event_Church_Threshold", 90.0),
    ("church_to_final_route", "Event_Church_Threshold", "Event_FosterHouse_FinalApproach", 90.0),
]


def godot_location(actor):
    location = actor.get_actor_location()
    return (float(location.y) / 100.0, float(location.z) / 100.0, -float(location.x) / 100.0)


def imported_name(actor):
    for tag in actor.tags:
        value = str(tag)
        if value.startswith("ImportedName_"):
            return value[len("ImportedName_") :]
    label = actor.get_actor_label()
    if label.startswith("Penance_"):
        return label[len("Penance_") :]
    return label


def distance_2d(a, b):
    return sqrt((a[0] - b[0]) ** 2 + (a[2] - b[2]) ** 2)


def actor_scale_tuple(actor):
    scale = actor.get_actor_scale3d()
    return (float(scale.x), float(scale.y), float(scale.z))


def main():
    failures = []
    if not unreal.EditorAssetLibrary.does_asset_exist(BACKUP_LEVEL_PATH):
        failures.append(f"Missing backup level: {BACKUP_LEVEL_PATH}")

    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(LEVEL_PATH)
    actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
    named = {}
    folder_counts = {}
    for actor in actors:
        name = imported_name(actor)
        if name:
            named.setdefault(name, []).append(actor)
        folder = str(actor.get_folder_path())
        folder_counts[folder] = folder_counts.get(folder, 0) + 1

    actual_positions = {}
    for name, expected in EXPECTED_POSITIONS.items():
        matches = named.get(name, [])
        if not matches:
            failures.append(f"Missing layout actor: {name}")
            continue
        actual = godot_location(matches[0])
        actual_positions[name] = actual
        if distance_2d(actual, expected) > 0.75 or abs(actual[1] - expected[1]) > 0.25:
            failures.append(f"{name} expected {expected}, got {tuple(round(v, 3) for v in actual)}")

    for name, expected in EXPECTED_SCALES.items():
        matches = named.get(name, [])
        if not matches:
            failures.append(f"Missing scaled actor: {name}")
            continue
        actual = actor_scale_tuple(matches[0])
        if any(abs(actual[i] - expected[i]) > 0.05 for i in range(3)):
            failures.append(f"{name} scale expected {expected}, got {tuple(round(v, 3) for v in actual)}")

    for name, expected in EXPECTED_FOLDERS.items():
        matches = named.get(name, [])
        if not matches:
            failures.append(f"Missing folder actor: {name}")
            continue
        actual = str(matches[0].get_folder_path())
        if actual != expected:
            failures.append(f"{name} folder expected {expected}, got {actual}")

    ground = named.get("NeighborhoodGround_150m_x_180m", [None])[0]
    if ground:
        gx, _gy, gz = godot_location(ground)
        sx = actor_scale_tuple(ground)[1]
        sz = actor_scale_tuple(ground)[0]
        min_x, max_x = gx - sx / 2.0, gx + sx / 2.0
        min_z, max_z = gz - sz / 2.0, gz + sz / 2.0
        for name, actual in actual_positions.items():
            if not (min_x <= actual[0] <= max_x and min_z <= actual[2] <= max_z):
                failures.append(f"{name} is outside ground bounds")

    route_lines = []
    for label, start_name, end_name, max_distance in ROUTE_POINTS:
        if start_name in actual_positions and end_name in actual_positions:
            distance = distance_2d(actual_positions[start_name], actual_positions[end_name])
            route_lines.append(f"{label}: {distance:.1f}m")
            if distance > max_distance:
                failures.append(f"{label} too long: {distance:.1f}m > {max_distance:.1f}m")

    report_lines = [
        "PENANCE_STEP8_LAYOUT_VERIFY",
        f"Edited level: {LEVEL_PATH}",
        f"Backup exists: {unreal.EditorAssetLibrary.does_asset_exist(BACKUP_LEVEL_PATH)}",
        f"Actors scanned: {len(actors)}",
        f"Position checks: {len(EXPECTED_POSITIONS)}",
        f"Scale checks: {len(EXPECTED_SCALES)}",
        f"Folder checks: {len(EXPECTED_FOLDERS)}",
        "Route distances:",
        *route_lines,
        "Folder counts:",
    ]
    for folder in sorted(folder_counts):
        report_lines.append(f"{folder}: {folder_counts[folder]}")
    report_lines.append(f"Failures: {len(failures)}")
    if failures:
        report_lines.append("FAILURES:")
        report_lines.extend(failures)

    report = "\n".join(report_lines) + "\n"
    REPORT_PATH.write_text(report)
    print(report)

    if failures:
        raise RuntimeError("Penance Step 8 layout verification failed")


if __name__ == "__main__":
    main()
