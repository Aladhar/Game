"""Penance V7.1 - run in Unreal Editor 5.7 after compiling PenanceStreamingDoor.

Creates three real .umap assets in the active project. Non-destructive: abort if any
requested map already exists. All maps are non-World-Partition graybox test maps.
"""
from pathlib import Path
import json
import unreal

PERSISTENT = "/Game/Maps/Penance_Persistent"
NEIGHBORHOOD = "/Game/Maps/Neighborhood/Penance_Neighborhood_V7"
INTERIOR = "/Game/Maps/Interiors/House01_Interior"
ALL_MAPS = (PERSISTENT, NEIGHBORHOOD, INTERIOR)

api = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
asset = unreal.EditorAssetLibrary
cube = asset.load_asset("/Engine/BasicShapes/Cube")


def die(message):
    raise RuntimeError("[Penance V7.1] " + message)


def save():
    if not unreal.EditorLoadingAndSavingUtils.save_current_level():
        die("Unable to save current level")


def new_map(package_path):
    print("[Penance V7.1] Creating " + package_path)
    if not api.new_level(package_path, is_partitioned_world=False):
        die("Could not create " + package_path)


def box(name, center, size, collide=True):
    """center and size in centimeters; no fake collision across doorway gaps."""
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor,
                       unreal.Vector(*center), unreal.Rotator(0, 0, 0))
    actor.set_actor_label("V71_" + name)
    actor.static_mesh_component.set_static_mesh(cube)
    actor.set_actor_scale3d(unreal.Vector(size[0]/100, size[1]/100, size[2]/100))
    actor.set_actor_enable_collision(collide)
    component = actor.static_mesh_component
    component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS
                                    if collide else unreal.CollisionEnabled.NO_COLLISION)
    return actor


def door(name, center, exterior):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.PenanceStreamingDoor, unreal.Vector(*center), unreal.Rotator(0, 0, 0))
    if not actor: die("Failed to create streaming doorway: " + name)
    actor.set_actor_label("V71_" + name)
    actor.set_editor_property("exterior_entrance", exterior)
    return actor


def create_interior():
    new_map(INTERIOR)
    box("House01_Floor", (0, 0, -12), (1240, 1040, 24))
    # Front wall: break around 130 cm doorway at Y = 0.
    box("Front_Wall_Left", (-600, -300, 150), (24, 440, 300))
    box("Front_Wall_Right", (-600, 300, 150), (24, 440, 300))
    box("Front_Door_Header", (-600, 0, 265), (24, 130, 70))
    box("Back_Wall", (600, 0, 150), (24, 1040, 300))
    box("Side_South", (0, -510, 150), (1240, 24, 300))
    box("Side_North", (0, 510, 150), (1240, 24, 300))
    # Hall/living division, with 120 cm wide gap. Rooms are simple grayboxes.
    box("Living_Divider_South", (-50, -320, 150), (24, 360, 300))
    box("Living_Divider_North", (-50, 320, 150), (24, 360, 300))
    box("Kitchen_Divider", (300, -170, 150), (24, 680, 300))
    box("Kitchen_Counter", (465, -340, 46), (260, 65, 92))
    box("Kitchen_Island", (280, -260, 42), (190, 85, 84))
    box("Living_Couch", (-290, -310, 40), (190, 75, 80))
    box("Living_Table", (-150, -270, 34), (90, 70, 68))
    box("Foyer_Closet", (-400, 415, 110), (130, 90, 220))
    # Physically climbable stairs: 16 treads from Z=0 up to Z=304 cm.
    for i in range(16):
        rise = 19 * (i+1)
        box("Stair_%02d" % (i+1), (-350 + i*32, 265, rise/2), (32, 135, rise))
    # Upper floor has an actual staircase opening over the stair run.
    box("Upper_Floor_South", (0, -220, 292), (1240, 600, 24))
    box("Upper_Floor_East_Landing", (370, 290, 292), (460, 440, 24))
    box("Upper_Floor_West", (-515, 290, 292), (170, 440, 24))
    box("Upper_Hall_Wall", (240, -140, 445), (24, 680, 280))
    box("Upper_Bedroom_Divider", (-180, -320, 445), (24, 360, 280))
    box("Upper_Back_Wall", (600, 0, 445), (24, 1040, 280))
    box("Upper_Front_Left", (-600, -300, 445), (24, 440, 280))
    box("Upper_Front_Right", (-600, 300, 445), (24, 440, 280))
    box("Upper_North_Wall", (0, 510, 445), (1240, 24, 280))
    box("Upper_South_Wall", (0, -510, 445), (1240, 24, 280))
    # The exit door is inside the streamed level, but only calls the persistent exterior door.
    door("House01_Exit_Streaming", (-600, 0, 107), False)
    light = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.PointLight, unreal.Vector(0, 0, 240), unreal.Rotator(0,0,0))
    light.set_actor_label("V71_Interior_FillLight")
    save()


def create_neighborhood():
    new_map(NEIGHBORHOOD)
    # A SMALL FUNCTIONAL STREAMING TEST SITE - not the full previously proposed town.
    box("Ground", (150, 0, -18), (5500, 5300, 36))
    box("Road", (-1400, 0, 4), (1700, 620, 8))
    box("Sidewalk", (-1100, -400, 9), (2200, 150, 18))
    box("Walkway", (-520, 0, 9), (380, 200, 18))
    # House 1 outer walls: 130 cm wide opening at X=-400, facing the road.
    box("House01_LeftFront", (-400, -340, 155), (25, 490, 310))
    box("House01_RightFront", (-400, 340, 155), (25, 490, 310))
    box("House01_FrontHeader", (-400, 0, 265), (25, 190, 90))
    box("House01_BackWall", (950, 0, 155), (25, 1160, 310))
    box("House01_LeftWall", (275, -575, 155), (1350, 25, 310))
    box("House01_RightWall", (275, 575, 155), (1350, 25, 310))
    # Two-story upper mass with a pitched roof placeholder. Exterior only.
    box("House01_UpperFloor", (275, 0, 309), (1350, 1160, 18))
    box("House01_SecondStory", (275, 0, 438), (1230, 1060, 240))
    box("House01_RoofPlaceholder", (275, 0, 581), (1470, 1290, 40))
    # Neighbor landmarks so the persistent map can later be replaced with final V7.
    for i, (x, y, size) in enumerate([(-1200,-1550,(950,1050)),(650,-1900,(1000,1050)),(-1350,1450,(850,950)),(750,1650,(1050,900))]):
        w,d=size
        box("AbandonedNeighbor%02d_Body"%(i+1), (x,y,160), (w,d,320))
        box("AbandonedNeighbor%02d_Roof"%(i+1), (x,y,348), (w+90,d+90,55))
    door("House01_Exterior_Streaming", (-400, 0, 107), True)
    save()


def create_persistent():
    new_map(PERSISTENT)
    start = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.PlayerStart, unreal.Vector(-1600, 0, 104), unreal.Rotator(0,0,0))
    start.set_actor_label("V71_Persistent_PlayerStart")
    manager = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.PenanceProgressionManager, unreal.Vector(-1000,-700,200), unreal.Rotator(0,0,0))
    manager.set_actor_label("V71_Persistent_ProgressionManager")
    sun = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.DirectionalLight, unreal.Vector(0,0,1500), unreal.Rotator(-45,45,0))
    sun.set_actor_label("V71_Debug_DirectionalLight")
    # Add neighborhood as ALWAYS LOADED. Interior is NOT added here; its C++ door streams it.
    world = unreal.EditorLevelLibrary.get_editor_world()
    if not hasattr(unreal, "EditorLevelUtils"):
        die("EditorLevelUtils unavailable; enable Editor Scripting Utilities plugin")
    added = unreal.EditorLevelUtils.add_level_to_world(world, NEIGHBORHOOD,
                                                       unreal.LevelStreamingAlwaysLoaded)
    if not added: die("Could not attach the neighborhood to persistent world")
    if not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True):
        die("Could not save persistent map and its streamed-level reference")
    if not api.load_level(PERSISTENT): die("Cannot reopen persistent world")
    save()


def main():
    if api.is_in_play_in_editor(): die("Stop Play-in-Editor before building")
    if not hasattr(unreal, "PenanceStreamingDoor"):
        die("PenanceStreamingDoor C++ class missing. Build new C++ code and reopen Editor.")
    if not hasattr(unreal, "PenanceProgressionManager"):
        die("Your existing PenanceProgressionManager C++ class is missing.")
    if not cube: die("Unreal's built-in Cube mesh could not be loaded")
    occupied = [p for p in ALL_MAPS if asset.does_asset_exist(p)]
    if occupied: die("Will not overwrite existing maps: " + ", ".join(occupied))
    for folder in ("/Game/Maps", "/Game/Maps/Neighborhood", "/Game/Maps/Interiors"):
        asset.make_directory(folder)
    create_interior()
    create_neighborhood()
    create_persistent()
    report = {"status": "editor script completed", "maps": list(ALL_MAPS),
              "interior_offset_cm": [200000,0,0],
              "note": "Verify E transitions, fades, and collision in PIE; no gameplay test performed by this script"}
    report_path = Path(unreal.Paths.project_saved_dir()) / "PenanceV71BuildReport.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("[Penance V7.1] Generated maps and saved report: " + str(report_path))


if __name__ == "__main__":
    main()
