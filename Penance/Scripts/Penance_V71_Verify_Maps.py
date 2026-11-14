"""Read-only editor inspection of the V7.1 generated map assets (not a PIE test)."""
import unreal
from pathlib import Path
import json

maps = [
    "/Game/Maps/Penance_Persistent",
    "/Game/Maps/Neighborhood/Penance_Neighborhood_V7",
    "/Game/Maps/Interiors/House01_Interior",
]
editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if editor.is_in_play_in_editor():
    raise RuntimeError("Stop Play-in-Editor before verifying maps")

results = {}
for path in maps:
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        raise RuntimeError("Missing map: " + path)
    if not editor.load_level(path):
        raise RuntimeError("Failed loading map: " + path)
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    labels = [str(a.get_actor_label()) for a in actors]
    results[path] = {
        "actor_count_visible_in_editor": len(labels),
        "doors": [s for s in labels if s.startswith("V71_House01_") and "Streaming" in s],
        "player_start_count": sum(a.get_class().get_name() == "PlayerStart" for a in actors),
        "progression_manager_count": sum(a.get_class().get_name() == "PenanceProgressionManager" for a in actors),
    }

editor.load_level(maps[0])
output = Path(unreal.Paths.project_saved_dir()) / "PenanceV71MapVerify.json"
output.write_text(json.dumps(results, indent=2))
print("[Penance V7.1] Editor map checks: " + str(output))
print(json.dumps(results, indent=2))
