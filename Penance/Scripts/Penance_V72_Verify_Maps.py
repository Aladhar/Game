"""Read-only Unreal Editor validation after applying Penance V7.2 stair fix.

Checks saved map assets and named actors. DOES NOT test actual PIE movement,
collision or the fade; those must be checked manually.
"""
import json
from pathlib import Path
import unreal

INTERIOR = "/Game/Maps/Interiors/House01_Interior"
NEIGHBORHOOD = "/Game/Maps/Neighborhood/Penance_Neighborhood_V7"
PERSISTENT = "/Game/Maps/Penance_Persistent"
TOL = 1.5


def is_near(a, b):
    return abs(a - b) <= TOL


def inspect_map(editor, path):
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        raise RuntimeError("Missing map " + path)
    if not editor.load_level(path):
        raise RuntimeError("Cannot open map " + path)
    result = {}
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        label = str(actor.get_actor_label())
        if label in result:
            raise RuntimeError("Duplicate label " + label + " in " + path)
        result[label] = actor
    return result


def main():
    editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if editor.is_in_play_in_editor():
        raise RuntimeError("Stop Play-in-Editor first")
    issues = []
    interior = inspect_map(editor, INTERIOR)
    stair_names = ["V71_Stair_%02d" % i for i in range(1, 17)]
    for n in stair_names:
        if n not in interior:
            issues.append(n + " missing")
        else:
            p = interior[n].get_actor_location()
            if not is_near(p.y, 430):
                issues.append(n + " not against north wall")
    if "V71_Upper_Floor_East_Landing" not in interior:
        issues.append("Upper landing missing")
    if "V71_House01_Exit_Streaming" not in interior:
        issues.append("Interior exit door missing")
    divider = interior.get("V71_Living_Divider_North")
    closet = interior.get("V71_Foyer_Closet")
    if not divider or not is_near(divider.get_actor_location().y, 240):
        issues.append("Stair divider not shortened/repositioned")
    if not closet or not is_near(closet.get_actor_location().y, -410):
        issues.append("Closet obstructs the stair base or is missing")
    if all(n in interior for n in stair_names) and "V71_Upper_Floor_East_Landing" in interior:
        top = interior[stair_names[-1]]
        landing = interior["V71_Upper_Floor_East_Landing"]
        z1 = top.get_actor_location().z + 50 * top.get_actor_scale3d().z
        z2 = landing.get_actor_location().z + 50 * landing.get_actor_scale3d().z
        if not is_near(z1, z2):
            issues.append("Top stair doesn't match landing elevation")

    # Capture transforms while the interior is loaded. Actor wrappers become
    # invalid after the script switches to the neighborhood and persistent maps.
    stair_centers_y_cm = {
        n: interior[n].get_actor_location().y for n in stair_names if n in interior
    }
    top_stair_surface_z_cm = (
        interior[stair_names[-1]].get_actor_location().z
        + 50 * interior[stair_names[-1]].get_actor_scale3d().z
        if stair_names[-1] in interior else None
    )
    landing_surface_z_cm = (
        interior["V71_Upper_Floor_East_Landing"].get_actor_location().z
        + 50 * interior["V71_Upper_Floor_East_Landing"].get_actor_scale3d().z
        if "V71_Upper_Floor_East_Landing" in interior else None
    )
    divider_loc = interior.get("V71_Living_Divider_North")
    north_divider_location_cm = (
        [divider_loc.get_actor_location().x, divider_loc.get_actor_location().y,
         divider_loc.get_actor_location().z] if divider_loc else None
    )
    closet = interior.get("V71_Foyer_Closet")
    foyer_closet_location_cm = (
        [closet.get_actor_location().x, closet.get_actor_location().y,
         closet.get_actor_location().z] if closet else None
    )

    neighborhood = inspect_map(editor, NEIGHBORHOOD)
    if "V71_House01_Exterior_Streaming" not in neighborhood:
        issues.append("Neighborhood exterior door missing")

    persistent = inspect_map(editor, PERSISTENT)
    player_starts = [a for a in persistent.values() if a.get_class().get_name() == "PlayerStart"]
    progression = [a for a in persistent.values()
                   if a.get_class().get_name() == "PenanceProgressionManager"]
    if len(player_starts) != 1:
        issues.append("Expected 1 PlayerStart; found %d" % len(player_starts))
    if len(progression) != 1:
        issues.append("Expected 1 progression manager; found %d" % len(progression))

    report = {
        "status": "PASS: editor geometry only" if not issues else "FAIL: editor geometry only",
        "interior_stair_count": len([n for n in stair_names if n in interior]),
        "stair_centers_y_cm": stair_centers_y_cm,
        "top_stair_surface_z_cm": top_stair_surface_z_cm,
        "landing_surface_z_cm": landing_surface_z_cm,
        "north_divider_location_cm": north_divider_location_cm,
        "foyer_closet_location_cm": foyer_closet_location_cm,
        "interior_actor_count": len(interior),
        "neighborhood_actor_count": len(neighborhood),
        "persistent_actor_count": len(persistent),
        "issues": issues,
        "remaining_manual_tests": [
            "In Penance_Persistent PIE: E at exterior door enters the loaded interior",
            "Walk up all 16 steps without blocking or head collisions",
            "Walk onto upstairs landing and back down",
            "E at interior exit returns player to original porch",
            "No black screen remains after either fade",
            "No errors about streaming level, skeleton, or player mesh"
        ]
    }
    path = Path(unreal.Paths.project_saved_dir()) / "PenanceV72Verify.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("[Penance V7.2] Verification report: " + str(path))
    if issues:
        raise RuntimeError("Penance V7.2 validation failed: " + "; ".join(issues))
    unreal.log("[Penance V7.2] PASS: static map/stair checks. PIE still required.")


if __name__ == "__main__":
    main()
