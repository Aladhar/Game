from pathlib import Path

import unreal


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_GLB = PROJECT_ROOT / "Content/PenanceAssets/Enemies/PenanceCarrier/PenanceRoughDraft.glb"
DESTINATION_PATH = "/Game/PenanceAssets/Enemies/PenanceCarrier/PenanceRoughDraft"
LEVEL_PATH = "/Game/Maps/PenanceRoughDraft_Render"
REPORT_PATH = PROJECT_ROOT / "Saved" / "PenanceRoughDraftRender.txt"
SCREENSHOT_PATH = PROJECT_ROOT / "Saved" / "Screenshots" / "PenanceRoughDraft_Render.png"


def disable_browser_sync():
    unreal.SystemLibrary.execute_console_command(
        None,
        "Interchange.FeatureFlags.Import.SyncToBrowser 0",
    )


def ensure_directory(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def import_roughdraft():
    if not SOURCE_GLB.exists():
        raise RuntimeError(f"Missing source GLB: {SOURCE_GLB}")

    ensure_directory(DESTINATION_PATH)
    existing = unreal.EditorAssetLibrary.list_assets(
        DESTINATION_PATH,
        recursive=True,
        include_folder=False,
    )
    if any(asset_path.endswith(".PenanceRoughDraft") for asset_path in existing):
        return list(existing)

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(SOURCE_GLB))
    task.set_editor_property("destination_path", DESTINATION_PATH)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    imported = list(task.get_editor_property("imported_object_paths"))
    if not imported:
        raise RuntimeError(f"Unreal imported no assets from: {SOURCE_GLB}")
    return imported


def get_static_meshes():
    mesh_paths = []
    for asset_path in unreal.EditorAssetLibrary.list_assets(
        DESTINATION_PATH,
        recursive=True,
        include_folder=False,
    ):
        asset = unreal.EditorAssetLibrary.load_asset(asset_path)
        if isinstance(asset, unreal.StaticMesh):
            mesh_paths.append(asset_path)
    if not mesh_paths:
        raise RuntimeError(f"No StaticMesh assets found under: {DESTINATION_PATH}")
    return sorted(mesh_paths)


def spawn_static_mesh(mesh_path):
    mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor,
        unreal.Vector(0.0, 0.0, 0.0),
        unreal.Rotator(0.0, 0.0, 0.0),
    )
    actor.set_actor_label("PenanceRoughDraft_RenderMesh")
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.static_mesh_component.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
    return actor


def actor_bounds(actor):
    origin, extent = actor.get_actor_bounds(False)
    return origin, extent


def setup_render_level(mesh_paths):
    if unreal.EditorAssetLibrary.does_asset_exist(LEVEL_PATH):
        unreal.EditorLoadingAndSavingUtils.load_map(LEVEL_PATH)
        for actor in unreal.EditorLevelLibrary.get_all_level_actors():
            unreal.EditorLevelLibrary.destroy_actor(actor)
    else:
        unreal.EditorLevelLibrary.new_level(LEVEL_PATH)

    mesh_actors = [spawn_static_mesh(path) for path in mesh_paths]
    origins = []
    extents = []
    for actor in mesh_actors:
        origin, extent = actor_bounds(actor)
        origins.append(origin)
        extents.append(extent)

    min_x = min(origin.x - extent.x for origin, extent in zip(origins, extents))
    max_x = max(origin.x + extent.x for origin, extent in zip(origins, extents))
    min_y = min(origin.y - extent.y for origin, extent in zip(origins, extents))
    max_y = max(origin.y + extent.y for origin, extent in zip(origins, extents))
    min_z = min(origin.z - extent.z for origin, extent in zip(origins, extents))
    max_z = max(origin.z + extent.z for origin, extent in zip(origins, extents))

    center = unreal.Vector(
        (min_x + max_x) * 0.5,
        (min_y + max_y) * 0.5,
        (min_z + max_z) * 0.5,
    )
    size = max(max_x - min_x, max_y - min_y, max_z - min_z, 100.0)

    for actor in mesh_actors:
        actor.add_actor_world_offset(unreal.Vector(-center.x, -center.y, -min_z), False, False)

    camera_distance = size * 1.8
    camera_height = max(size * 0.42, 120.0)
    camera = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.CineCameraActor,
        unreal.Vector(-camera_distance, -camera_distance * 0.75, camera_height),
        unreal.Rotator(-8.0, 38.0, 0.0),
    )
    camera.set_actor_label("PenanceRoughDraft_RenderCamera")
    camera_component = camera.get_cine_camera_component()
    camera_component.set_editor_property("current_focal_length", 38.0)
    camera_component.set_editor_property("current_aperture", 5.6)

    sun = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.DirectionalLight,
        unreal.Vector(-220.0, -180.0, 420.0),
        unreal.Rotator(-42.0, -28.0, 8.0),
    )
    sun.set_actor_label("PenanceRoughDraft_KeyLight")
    sun.light_component.set_editor_property("intensity", 4.5)

    fill = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.PointLight,
        unreal.Vector(260.0, -360.0, 220.0),
        unreal.Rotator(0.0, 0.0, 0.0),
    )
    fill.set_actor_label("PenanceRoughDraft_FillLight")
    fill.light_component.set_editor_property("intensity", 800.0)
    fill.light_component.set_editor_property("attenuation_radius", size * 3.0)

    floor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor,
        unreal.Vector(0.0, 0.0, -1.0),
        unreal.Rotator(0.0, 0.0, 0.0),
    )
    floor.set_actor_label("PenanceRoughDraft_RenderFloor")
    floor.static_mesh_component.set_static_mesh(
        unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Plane")
    )
    floor.set_actor_scale3d(unreal.Vector(size / 80.0, size / 80.0, 1.0))

    world = unreal.EditorLevelLibrary.get_editor_world()
    world.get_world_settings().set_editor_property("default_game_mode", None)
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(
        camera.get_actor_location(),
        camera.get_actor_rotation(),
    )
    unreal.EditorLoadingAndSavingUtils.save_current_level()
    return camera, size


def request_screenshot(camera):
    # Python commandlets run under NullRHI, so they can import/build the level
    # but cannot produce a real rendered viewport image. A screenshot can be
    # requested by running this script in the full editor instead of commandlet.
    return None

    SCREENSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    unreal.EditorLevelLibrary.editor_set_game_view(True)
    unreal.AutomationLibrary.take_high_res_screenshot(
        1280,
        1280,
        str(SCREENSHOT_PATH),
        camera=camera,
        mask_enabled=False,
        capture_hdr=False,
    )
    return SCREENSHOT_PATH


def write_report(imported_paths, mesh_paths, screenshot_path):
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "PENANCE_ROUGHDRAFT_RENDER",
        f"Source GLB: {SOURCE_GLB}",
        f"Import destination: {DESTINATION_PATH}",
        f"Preview level: {LEVEL_PATH}",
        f"Screenshot requested: {screenshot_path or 'skipped: commandlet uses NullRHI'}",
        f"Imported paths: {len(imported_paths)}",
        *sorted(imported_paths),
        f"Static meshes: {len(mesh_paths)}",
        *mesh_paths,
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n")


def main():
    disable_browser_sync()
    imported_paths = import_roughdraft()
    mesh_paths = get_static_meshes()
    camera, _size = setup_render_level(mesh_paths)
    screenshot_path = request_screenshot(camera)
    write_report(imported_paths, mesh_paths, screenshot_path)
    unreal.log(f"Prepared Penance rough draft render level: {LEVEL_PATH}")
    unreal.log(f"Requested screenshot: {screenshot_path}")


if __name__ == "__main__":
    main()
