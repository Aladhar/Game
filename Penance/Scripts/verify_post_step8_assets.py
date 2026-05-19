from pathlib import Path

import unreal


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEVEL_PATH = "/Game/Maps/Penance_Suburban_Blockout"
REPORT_PATH = PROJECT_ROOT / "Saved" / "PenancePostStep8AssetsVerify.txt"

REQUIRED_ASSET_DIRS = [
    "/Game/Map_Assets/Church-4a4878e5",
    "/Game/Map_Assets/Road",
]

REQUIRED_ACTORS = {
    "Church_Approach_CrackedPath_TestAsset": "03_Environment/Roads/ImportedRoadTest",
    "Church_Exterior_LeftSightlineBlocker": "03_Environment/ChurchExterior",
    "Church_Exterior_RightSightlineBlocker": "03_Environment/ChurchExterior",
    "Church_Exterior_ForecourtFogBand": "03_Environment/ChurchExterior",
    "Church_Reserve_BoundsMarker": "03_Environment/ChurchExterior",
    "Road_Test_ImportedAsset_SmallPatch": "03_Environment/Roads/ImportedRoadTest",
}


def imported_name(actor):
    for tag in actor.tags:
        value = str(tag)
        if value.startswith("ImportedName_"):
            return value[len("ImportedName_") :]
    label = actor.get_actor_label()
    if label.startswith("Penance_"):
        return label[len("Penance_") :]
    return label


def godot_location(actor):
    location = actor.get_actor_location()
    return (float(location.y) / 100.0, float(location.z) / 100.0, -float(location.x) / 100.0)


def main():
    failures = []
    for directory in REQUIRED_ASSET_DIRS:
        if not unreal.EditorAssetLibrary.does_directory_exist(directory):
            failures.append(f"Missing imported asset directory: {directory}")

    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(LEVEL_PATH)
    actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
    named = {imported_name(actor): actor for actor in actors if imported_name(actor)}

    imported_church_actors = []
    imported_road_actors = []
    for actor in actors:
        path = ""
        try:
            mesh = actor.static_mesh_component.static_mesh
            path = mesh.get_path_name() if mesh else ""
        except Exception:
            pass
        if "/Game/Map_Assets/Church-4a4878e5" in path:
            imported_church_actors.append(actor)
        if "/Game/Map_Assets/Road" in path:
            imported_road_actors.append(actor)

    if not imported_church_actors and "Church_VerifiedAssetAnchor" not in named:
        failures.append("No imported church actor or fallback church anchor in level")
    if not imported_road_actors:
        failures.append("No imported road static mesh actor in level")

    for name, folder in REQUIRED_ACTORS.items():
        actor = named.get(name)
        if not actor:
            failures.append(f"Missing post-Step-8 actor: {name}")
            continue
        actual_folder = str(actor.get_folder_path())
        if actual_folder != folder:
            failures.append(f"{name} folder expected {folder}, got {actual_folder}")

    route_actor = named.get("Event_Church_Threshold")
    path_actor = named.get("Church_Approach_CrackedPath_TestAsset")
    if route_actor and path_actor:
        rx, _ry, rz = godot_location(route_actor)
        px, _py, pz = godot_location(path_actor)
        if abs(rx - px) > 4.0 or abs(rz - pz) > 4.0:
            failures.append("Church test road is not aligned with church threshold trigger")

    report_lines = [
        "PENANCE_POST_STEP8_ASSETS_VERIFY",
        f"Edited level: {LEVEL_PATH}",
        f"Imported church actors in level: {len(imported_church_actors)}",
        f"Imported road actors in level: {len(imported_road_actors)}",
        f"Required support actors: {len(REQUIRED_ACTORS)}",
        f"Failures: {len(failures)}",
    ]
    if failures:
        report_lines.append("FAILURES:")
        report_lines.extend(failures)
    REPORT_PATH.write_text("\n".join(report_lines) + "\n")
    print("\n".join(report_lines))

    if failures:
        raise RuntimeError("Post-Step-8 asset verification failed")


if __name__ == "__main__":
    main()
