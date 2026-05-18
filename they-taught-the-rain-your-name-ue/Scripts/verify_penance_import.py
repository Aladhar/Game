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
    geometry = [actor for actor in imported if "Geometry" in str(actor.get_folder_path())]

    report = "\n".join(
        [
            "PENANCE_IMPORT_VERIFY",
            f"Imported actors: {len(imported)}",
            f"Geometry actors: {len(geometry)}",
            f"Marker actors: {len(markers)}",
            f"Light actors: {len(lights)}",
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


if __name__ == "__main__":
    main()
