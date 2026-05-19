from pathlib import Path

import unreal


LEVEL_PATH = "/Game/Maps/Penance_Suburban_Blockout"


def main():
    level_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    level_subsystem.load_level(LEVEL_PATH)

    actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
    imported = [actor for actor in actors if actor.get_actor_label().startswith("Penance_")]
    lights = [actor for actor in imported if "Lights" in str(actor.get_folder_path())]
    markers = [actor for actor in imported if "EventAndInteractableMarkers" in str(actor.get_folder_path())]
    mesh_actor_classes = {"StaticMeshActor", "PenanceHingedDoor", "PenancePickupItem"}
    geometry = [
        actor
        for actor in imported
        if actor.get_class().get_name() in mesh_actor_classes
        and "PenanceImported/" in str(actor.get_folder_path())
        and "Lights" not in str(actor.get_folder_path())
        and "EventAndInteractableMarkers" not in str(actor.get_folder_path())
    ]
    hinged_doors = [actor for actor in imported if actor.get_class().get_name() == "PenanceHingedDoor"]
    pickups = [actor for actor in imported if actor.get_class().get_name() == "PenancePickupItem"]
    progression_managers = [actor for actor in imported if actor.get_class().get_name() == "PenanceProgressionManager"]
    progression_triggers = [actor for actor in imported if actor.get_class().get_name() == "PenanceProgressionTrigger"]

    report = "\n".join(
        [
            "PENANCE_IMPORT_VERIFY",
            f"Imported actors: {len(imported)}",
            f"Geometry actors: {len(geometry)}",
            f"Marker actors: {len(markers)}",
            f"Light actors: {len(lights)}",
            f"Hinged door actors: {len(hinged_doors)}",
            f"Pickup actors: {len(pickups)}",
            f"Progression managers: {len(progression_managers)}",
            f"Progression triggers: {len(progression_triggers)}",
        ]
    )
    unreal.log(report)
    Path(unreal.Paths.project_saved_dir()).joinpath("PenanceImportVerify.txt").write_text(report)

    if len(geometry) < 700:
        raise RuntimeError("Expected at least 700 imported geometry actors.")
    if len(markers) < 15:
        raise RuntimeError("Expected at least 15 event/interactable markers.")
    if len(lights) < 40:
        raise RuntimeError("Expected at least 40 imported lights.")
    if len(progression_managers) != 1:
        raise RuntimeError("Expected exactly one progression manager.")
    if len(progression_triggers) != 17:
        raise RuntimeError("Expected exactly 17 progression triggers.")


if __name__ == "__main__":
    main()
