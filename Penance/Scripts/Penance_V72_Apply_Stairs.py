"""Penance V7.2 House 01 stair correction. Run inside UE 5.7 Editor.

Only edits the V7.1-generated House01_Interior map. Backs up that map,
refuses to overwrite unexpectedly edited layouts, and leaves streaming actors,
player start and progression untouched. Does not run PIE or touch C++.
"""
import json
from pathlib import Path
import unreal

LEVEL = "/Game/Maps/Interiors/House01_Interior"
BACKUP = "/Game/Maps/Interiors/House01_Interior_V71_BeforeStairFix"
TOL = 1.5
TARGET_Y = 430.0
STAIRS = ["V71_Stair_%02d" % n for n in range(1, 17)]
REQUIRED = STAIRS + [
    "V71_Living_Divider_North", "V71_Foyer_Closet", "V71_Side_North",
    "V71_Upper_Floor_East_Landing", "V71_House01_Exit_Streaming",
]


def near(a, b):
    return abs(a - b) <= TOL


def loc(a):
    p = a.get_actor_location()
    return p.x, p.y, p.z


def fail(msg):
    raise RuntimeError("[Penance V7.2] " + msg)


def all_actors():
    result = {}
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        name = str(actor.get_actor_label())
        if name in result:
            fail("Duplicate actor label: " + name)
        result[name] = actor
    return result


def stair_state(actors):
    ys = [loc(actors[name])[1] for name in STAIRS]
    if all(near(v, TARGET_Y) for v in ys):
        return "moved"
    if all(near(v, 265.0) for v in ys):
        return "original"
    fail("Stairs are not in the original or corrected position. "
         "No edits made. Y centers: " + str(ys))


def check_dimensions(actors):
    # Same dimensions and anchors as the known V7.1 builder. Do not force
    # transforms into customized interiors.
    north = actors["V71_Side_North"]
    upper = actors["V71_Upper_Floor_East_Landing"]
    if not (near(loc(north)[1], 510.0) and near(loc(upper)[0], 370.0)):
        fail("Different wall/landing anchors; no edits made")
    ns = north.get_actor_scale3d()
    if not (near(ns.y * 100.0, 24.0) and near(ns.z * 100.0, 300.0)):
        fail("North wall dimensions changed; no edits made")
    for n in range(16):
        a = actors[STAIRS[n]]
        x, _, z = loc(a)
        s = a.get_actor_scale3d()
        if not (near(x, -350.0 + n*32.0)
                and near(z, 19.0*(n+1)/2.0)
                and near(s.x * 100.0, 32.0)
                and near(s.y * 100.0, 135.0)
                and near(s.z * 100.0, 19.0*(n+1))):
            fail("Stair %02d was resized or repositioned; no edits made" % (n+1))


def target_partitions(actors):
    divider = actors["V71_Living_Divider_North"]
    closet = actors["V71_Foyer_Closet"]
    d = loc(divider)
    c = loc(closet)
    ds = divider.get_actor_scale3d()
    if (near(d[0], -50) and near(d[1], 240) and near(d[2], 150)
            and near(ds.y * 100, 200)
            and near(c[0], -430) and near(c[1], -410) and near(c[2], 110)):
        return "moved"
    if (near(d[0], -50) and near(d[1], 320) and near(d[2], 150)
            and near(ds.y * 100, 360)
            and near(c[0], -400) and near(c[1], 415) and near(c[2], 110)):
        return "original"
    fail("Stair divider or closet has been customized; no edits made")


def main():
    editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assets = unreal.EditorAssetLibrary
    if editor.is_in_play_in_editor():
        fail("Stop Play-in-Editor first")
    if not assets.does_asset_exist(LEVEL):
        fail("Map not found: " + LEVEL)

    # Back up the existing level first, even if it has been modified.
    if not assets.does_asset_exist(BACKUP):
        if not assets.duplicate_asset(LEVEL, BACKUP):
            fail("Couldn't create the backup; nothing changed. "
                 "Duplicate House01_Interior in the Content Browser first.")
        unreal.log("[Penance V7.2] Created backup: " + BACKUP)
    else:
        unreal.log("[Penance V7.2] Keeping existing backup: " + BACKUP)
    # duplicate_asset can leave the duplicate dirty in the transient editor
    # session; persist it before touching the original map.
    if not assets.save_asset(BACKUP, only_if_is_dirty=False):
        fail("Couldn't save the interior backup; original map was not edited")

    if not editor.load_level(LEVEL):
        fail("Couldn't open interior level")
    actors = all_actors()
    missing = [name for name in REQUIRED if name not in actors]
    if missing:
        fail("Actors missing: " + ", ".join(missing) + "; no edits made")
    check_dimensions(actors)
    stair_status = stair_state(actors)
    partition_status = target_partitions(actors)
    if stair_status != partition_status:
        fail("Stairs and partitions are in different edit states; no edits made")

    if stair_status == "original":
        # Explicitly mark edited actors so SaveCurrentLevel writes their
        # transforms into the .umap rather than returning success on a clean
        # package with only transient in-memory changes.
        for actor in (actors["V71_Living_Divider_North"],
                      actors["V71_Foyer_Closet"]):
            actor.modify()
        for name in STAIRS:
            actors[name].modify()
        actors["V71_Living_Divider_North"].set_actor_location(
            unreal.Vector(-50, 240, 150), False, True)
        actors["V71_Living_Divider_North"].set_actor_scale3d(
            unreal.Vector(0.24, 2.0, 3.0))
        actors["V71_Foyer_Closet"].set_actor_location(
            unreal.Vector(-430, -410, 110), False, True)
        for name in STAIRS:
            x, _, z = loc(actors[name])
            actors[name].set_actor_location(unreal.Vector(x, TARGET_Y, z), False, True)

    # Editor geometry checks (NOT a substitute for physically walking in PIE).
    if stair_state(actors) != "moved" or target_partitions(actors) != "moved":
        fail("Post-edit verification failed. Check without saving")
    if len(STAIRS) != 16 or not near(19.0*16, 304.0):
        fail("Unexpected stair geometry")
    last = actors[STAIRS[-1]]
    last_top = loc(last)[2] + 0.5 * last.get_actor_scale3d().z * 100
    landing = actors["V71_Upper_Floor_East_Landing"]
    landing_top = loc(landing)[2] + 0.5 * landing.get_actor_scale3d().z * 100
    if not near(last_top, landing_top):
        fail("Stair top and upstairs landing do not match")

    if not unreal.EditorLoadingAndSavingUtils.save_current_level():
        fail("Couldn't save interior map; backup still exists")
    if not assets.save_asset(LEVEL, only_if_is_dirty=False):
        fail("Couldn't persist the edited interior asset; backup still exists")
    result = {
        "status": "saved; runtime test still required",
        "map": LEVEL,
        "backup": BACKUP,
        "already_applied": stair_status == "moved",
        "stairs": 16,
        "stair_center_y_cm": TARGET_Y,
        "stair_width_cm": 135,
        "north_wall_inside_y_cm": 498,
        "stair_wall_side_clearance_at_center_cm": 33,
        "stair_top_z_cm": last_top,
        "upper_landing_top_z_cm": landing_top,
        "player_capsule_diameter_from_v71_cpp_cm": 70,
        "note": "Editor geometry only; must test collision, door E interaction and fades in PIE"
    }
    path = Path(unreal.Paths.project_saved_dir()) / "PenanceV72StairsReport.json"
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    unreal.log("[Penance V7.2] Stair fix saved. " + str(path))


if __name__ == "__main__":
    main()
