from pathlib import Path

import unreal


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEVEL_PATH = "/Game/Maps/Penance_Suburban_Blockout"
REPORT_PATH = PROJECT_ROOT / "Saved" / "PenancePostStep8AssetsReport.txt"
ROAD_SOURCE = PROJECT_ROOT / "Content" / "Map Assets" / "Road" / "gltf" / "scene.gltf"

CHURCH_ASSET_PREFIX = "/Game/Map_Assets/Church-4a4878e5"
ROAD_ASSET_PREFIX = "/Game/Map_Assets/Road"
ROAD_DESTINATION = "/Game/Map_Assets/Road/gltf/source"

CORE_ROAD_ACTORS = {
    "MainLoop_Road_South",
    "MainLoop_Road_North",
    "MainLoop_Road_West",
    "MainLoop_Road_East",
}

ROAD_REPLACEMENT_TARGETS = {
    "MainLoop_Road_South": ((0.0, 0.0, 22.0), (7.0, 0.08, 78.0)),
    "MainLoop_Road_North": ((0.0, 0.0, -34.0), (7.0, 0.08, 78.0)),
    "MainLoop_Road_West": ((-34.0, 0.0, -6.0), (7.0, 0.08, 56.0)),
    "MainLoop_Road_East": ((34.0, 0.0, -6.0), (7.0, 0.08, 56.0)),
    "ArrivalStreet_Road_80m": ((0.0, 0.0, 58.0), (7.5, 0.08, 80.0)),
    "CulDeSac_ConnectorRoad": ((-42.0, 0.0, -12.0), (7.0, 0.08, 18.0)),
    "CulDeSac_RoadCircle_32m": ((-52.0, 0.0, -12.0), (32.0, 0.08, 32.0)),
    "FinalHouse_Unreachable_RoadStub_Locked": ((0.0, 0.0, -52.0), (7.0, 0.08, 18.0)),
    "FinalHouse_RoadExtension_AppearsLater": ((0.0, 0.0, -64.0), (7.0, 0.08, 20.0)),
    "FirstHouse_ClearEntry_WetPath_FromRoad": ((24.0, 0.12, 42.0), (3.8, 0.10, 3.2)),
    "Park_Lure_WarmPuddleTrail_FromRoad": ((-25.0, 0.05, -9.0), (12.0, 0.03, 2.4)),
}

CHURCH_CENTER = (28.0, 0.0, 1.0)
CHURCH_TARGETS = {
    "Church_VerifiedAssetAnchor": (28.0, 0.03, 1.0),
    "Church_Approach_CrackedPath_TestAsset": (28.0, 0.04, 8.0),
    "Church_Exterior_LeftSightlineBlocker": (18.0, 1.25, 5.0),
    "Church_Exterior_RightSightlineBlocker": (36.5, 1.25, 4.5),
    "Church_Exterior_ForecourtFogBand": (28.0, 0.08, 11.0),
    "Church_Reserve_BoundsMarker": (28.0, 0.08, 1.0),
    "Road_Test_ImportedAsset_SmallPatch": (18.0, 0.05, 18.0),
}


def disable_browser_sync():
    unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.SyncToBrowser 0")


def godot_to_unreal(vec):
    return unreal.Vector(-float(vec[2]) * 100.0, float(vec[0]) * 100.0, float(vec[1]) * 100.0)


def unreal_to_godot(vec):
    return (float(vec.y) / 100.0, float(vec.z) / 100.0, -float(vec.x) / 100.0)


def imported_name(actor):
    for tag in actor.tags:
        value = str(tag)
        if value.startswith("ImportedName_"):
            return value[len("ImportedName_") :]
    label = actor.get_actor_label()
    if label.startswith("Penance_"):
        return label[len("Penance_") :]
    return label


def set_name_tag(actor, name):
    actor.set_actor_label(f"Penance_{name}")
    tags = [tag for tag in actor.tags if not str(tag).startswith("ImportedName_")]
    tags.append(unreal.Name(f"ImportedName_{name}"))
    actor.tags = tags


def set_location(actor, x, y, z):
    actor.modify()
    actor.set_actor_location(godot_to_unreal((x, y, z)), False, True)


def set_scale(actor, sx, sy, sz):
    actor.modify()
    actor.set_actor_scale3d(unreal.Vector(float(sz), float(sx), float(sy)))


def make_material(name, color, roughness=0.9, metallic=0.0, emission=None):
    package_path = "/Game/PenanceImported/Materials"
    asset_path = f"{package_path}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        return unreal.EditorAssetLibrary.load_asset(asset_path)

    unreal.EditorAssetLibrary.make_directory(package_path)
    material_factory = unreal.MaterialFactoryNew()
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name,
        package_path,
        unreal.Material,
        material_factory,
    )
    material.set_editor_property("two_sided", True)
    base_expr = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -500, -120
    )
    base_expr.set_editor_property("constant", unreal.LinearColor(*color))
    unreal.MaterialEditingLibrary.connect_material_property(
        base_expr, "", unreal.MaterialProperty.MP_BASE_COLOR
    )
    rough_expr = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -500, 100
    )
    rough_expr.set_editor_property("r", float(roughness))
    unreal.MaterialEditingLibrary.connect_material_property(
        rough_expr, "", unreal.MaterialProperty.MP_ROUGHNESS
    )
    metal_expr = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -500, 220
    )
    metal_expr.set_editor_property("r", float(metallic))
    unreal.MaterialEditingLibrary.connect_material_property(
        metal_expr, "", unreal.MaterialProperty.MP_METALLIC
    )
    if emission:
        emissive_expr = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionConstant3Vector, -250, -120
        )
        emissive_expr.set_editor_property("constant", unreal.LinearColor(*emission))
        unreal.MaterialEditingLibrary.connect_material_property(
            emissive_expr, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR
        )
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def assign_material(actor, material):
    component = actor.static_mesh_component
    slots = component.get_num_materials()
    for index in range(slots):
        component.set_material(index, material)


def import_source_asset(source_path, destination_path):
    if not source_path.exists():
        raise RuntimeError(f"Missing source asset: {source_path}")
    if not unreal.EditorAssetLibrary.does_directory_exist(destination_path):
        unreal.EditorAssetLibrary.make_directory(destination_path)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(source_path))
    task.set_editor_property("destination_path", destination_path)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", False)
    task.set_editor_property("save", True)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    return list(task.get_editor_property("imported_object_paths"))


def static_mesh_assets_under(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        return []
    result = []
    for asset_path in unreal.EditorAssetLibrary.list_assets(path, recursive=True, include_folder=False):
        asset = unreal.EditorAssetLibrary.load_asset(asset_path)
        if isinstance(asset, unreal.StaticMesh):
            result.append(asset)
    return result


def mesh_footprint_score(mesh):
    bounds = mesh.get_bounds()
    extent = bounds.box_extent
    return float(extent.x) * float(extent.y) + float(extent.x) * float(extent.z)


def ensure_road_mesh_asset():
    meshes = static_mesh_assets_under(ROAD_ASSET_PREFIX)
    if meshes:
        return max(meshes, key=mesh_footprint_score), False
    import_source_asset(ROAD_SOURCE, ROAD_DESTINATION)
    meshes = static_mesh_assets_under(ROAD_ASSET_PREFIX)
    if not meshes:
        raise RuntimeError("Road GLTF import completed but produced no StaticMesh assets")
    return max(meshes, key=mesh_footprint_score), True


def spawn_box(name, target, scale, material, folder, collision=True):
    existing = find_actor_by_name(name)
    if existing:
        actor = existing
    else:
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, godot_to_unreal(target))
        set_name_tag(actor, name)

    cube = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube.Cube")
    actor.modify()
    actor.static_mesh_component.set_static_mesh(cube)
    actor.set_folder_path(folder)
    set_location(actor, *target)
    set_scale(actor, *scale)
    actor.set_actor_enable_collision(bool(collision))
    assign_material(actor, material)
    return actor


def get_all_actors():
    return list(unreal.EditorLevelLibrary.get_all_level_actors())


def find_actor_by_name(name):
    for actor in get_all_actors():
        if imported_name(actor) == name:
            return actor
    return None


def organize_imported_assets():
    changed = 0
    church_actors = []
    road_actors = []
    for actor in get_all_actors():
        name = imported_name(actor)
        label = actor.get_actor_label()
        path = ""
        try:
            mesh = actor.static_mesh_component.static_mesh
            path = mesh.get_path_name() if mesh else ""
        except Exception:
            path = ""

        if name in CORE_ROAD_ACTORS:
            actor.modify()
            actor.set_folder_path("03_Environment/Roads")
            changed += 1
        elif CHURCH_ASSET_PREFIX in path or "Old_Church" in path or label.startswith("SM_Church"):
            actor.modify()
            actor.set_folder_path("03_Environment/ChurchExterior/ImportedChurchTest")
            church_actors.append(actor)
            changed += 1
        elif ROAD_ASSET_PREFIX in path:
            actor.modify()
            actor.set_folder_path("03_Environment/Roads/ImportedRoadTest")
            road_actors.append(actor)
            changed += 1

    return changed, church_actors, road_actors


def create_church_exterior_test_area():
    cracked = make_material(
        "M_Step9_CrackedRoad_Test",
        (0.035, 0.033, 0.03, 1.0),
        roughness=0.96,
    )
    blocker = make_material(
        "M_Step9_ChurchSightlineBlocker_Dark",
        (0.018, 0.017, 0.015, 1.0),
        roughness=0.94,
    )
    fog = make_material(
        "M_Step9_ChurchFogBand",
        (0.12, 0.13, 0.12, 0.55),
        roughness=1.0,
    )
    reserve = make_material(
        "M_Step9_ChurchReserveMarker",
        (0.11, 0.08, 0.045, 0.35),
        roughness=0.9,
    )

    actors = [
        spawn_box(
            "Church_Approach_CrackedPath_TestAsset",
            CHURCH_TARGETS["Church_Approach_CrackedPath_TestAsset"],
            (7.0, 0.04, 14.0),
            cracked,
            "03_Environment/Roads/ImportedRoadTest",
            collision=True,
        ),
        spawn_box(
            "Church_Exterior_LeftSightlineBlocker",
            CHURCH_TARGETS["Church_Exterior_LeftSightlineBlocker"],
            (2.4, 2.5, 10.0),
            blocker,
            "03_Environment/ChurchExterior",
            collision=True,
        ),
        spawn_box(
            "Church_Exterior_RightSightlineBlocker",
            CHURCH_TARGETS["Church_Exterior_RightSightlineBlocker"],
            (2.6, 2.5, 9.0),
            blocker,
            "03_Environment/ChurchExterior",
            collision=True,
        ),
        spawn_box(
            "Church_Exterior_ForecourtFogBand",
            CHURCH_TARGETS["Church_Exterior_ForecourtFogBand"],
            (22.0, 0.05, 3.5),
            fog,
            "03_Environment/ChurchExterior",
            collision=False,
        ),
        spawn_box(
            "Church_Reserve_BoundsMarker",
            CHURCH_TARGETS["Church_Reserve_BoundsMarker"],
            (26.0, 0.02, 22.0),
            reserve,
            "03_Environment/ChurchExterior",
            collision=False,
        ),
    ]
    return actors


def place_road_asset_test():
    mesh, imported = ensure_road_mesh_asset()
    name = "Road_Test_ImportedAsset_SmallPatch"
    actor = find_actor_by_name(name)
    if not actor:
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.StaticMeshActor,
            godot_to_unreal(CHURCH_TARGETS[name]),
        )
        set_name_tag(actor, name)
    actor.modify()
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.set_folder_path("03_Environment/Roads/ImportedRoadTest")
    set_location(actor, *CHURCH_TARGETS[name])
    actor.set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.0))
    actor.set_actor_enable_collision(True)
    return actor, mesh.get_path_name(), imported


def set_mesh_scale_to_godot_size(actor, mesh, width_m, height_m, length_m):
    bounds = mesh.get_bounds()
    extent = bounds.box_extent
    size_x = max(float(extent.x) * 2.0, 1.0)
    size_y = max(float(extent.y) * 2.0, 1.0)
    size_z = max(float(extent.z) * 2.0, 1.0)
    actor.set_actor_scale3d(
        unreal.Vector(
            max(float(length_m) * 100.0 / size_x, 0.01),
            max(float(width_m) * 100.0 / size_y, 0.01),
            max(float(height_m) * 100.0 / size_z, 0.01),
        )
    )


def replace_route_roads():
    mesh, imported = ensure_road_mesh_asset()
    replaced = []
    for name, (target, size) in ROAD_REPLACEMENT_TARGETS.items():
        actor = find_actor_by_name(name)
        if not actor:
            actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
                unreal.StaticMeshActor,
                godot_to_unreal(target),
            )
            set_name_tag(actor, name)
        actor.modify()
        actor.static_mesh_component.set_static_mesh(mesh)
        actor.set_folder_path("03_Environment/Roads")
        set_location(actor, *target)
        set_mesh_scale_to_godot_size(actor, mesh, *size)
        actor.set_actor_enable_collision(True)
        replaced.append(actor)
    return replaced, mesh.get_path_name(), imported


def place_or_verify_church_placeholder(church_actors):
    if church_actors:
        for actor in church_actors:
            actor.modify()
            actor.set_folder_path("03_Environment/ChurchExterior/ImportedChurchTest")
        return church_actors, False

    # Fallback marker only. The real imported church assets stay untouched; this
    # gives the route a verified anchor if no imported church actor is present.
    material = make_material(
        "M_Step9_ChurchVerifiedPlaceholder",
        (0.075, 0.066, 0.055, 1.0),
        roughness=0.92,
    )
    actor = spawn_box(
        "Church_VerifiedAssetAnchor",
        CHURCH_TARGETS["Church_VerifiedAssetAnchor"],
        (11.0, 9.0, 16.0),
        material,
        "03_Environment/ChurchExterior/ImportedChurchTest",
        collision=True,
    )
    return [actor], True


def write_report(
    church_actors,
    road_actors,
    test_actors,
    created_anchor,
    organized_count,
    road_test_actor,
    road_mesh_path,
    road_imported,
    replaced_roads,
):
    lines = [
        "PENANCE_POST_STEP8_ASSETS",
        f"Edited level: {LEVEL_PATH}",
        "Scope: post-Step-8 asset setup plus full route road replacement.",
        f"Imported church actors verified/foldered: {len(church_actors)}",
        f"Imported road actors verified/foldered: {len(road_actors)}",
        f"Fallback church anchor created: {created_anchor}",
        f"Actors organized this run: {organized_count}",
        f"Church test/support actors: {len(test_actors)}",
        f"Road GLTF imported this run: {road_imported}",
        f"Road test actor: {imported_name(road_test_actor)}",
        f"Road replacement mesh: {road_mesh_path}",
        f"Route road actors replaced: {len(replaced_roads)}",
        "Reserved church exterior center: x=28m z=1m",
        "Replaced route roads:",
    ]
    for actor in replaced_roads:
        x, y, z = unreal_to_godot(actor.get_actor_location())
        scale = actor.get_actor_scale3d()
        lines.append(
            f"- {imported_name(actor)} at x={x:.1f} y={y:.1f} z={z:.1f} "
            f"scale=({scale.x:.3f},{scale.y:.3f},{scale.z:.3f})"
        )
    lines.extend([
        "Created/updated test support actors:",
    ])
    for actor in test_actors:
        x, y, z = unreal_to_godot(actor.get_actor_location())
        lines.append(f"- {imported_name(actor)} at x={x:.1f} y={y:.1f} z={z:.1f}")
    REPORT_PATH.write_text("\n".join(lines) + "\n")


def main():
    disable_browser_sync()
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(LEVEL_PATH)
    organized_count, church_actors, road_actors = organize_imported_assets()
    church_actors, created_anchor = place_or_verify_church_placeholder(church_actors)
    test_actors = create_church_exterior_test_area()
    road_test_actor, road_mesh_path, road_imported = place_road_asset_test()
    replaced_roads, road_mesh_path, replacement_imported = replace_route_roads()
    road_imported = road_imported or replacement_imported
    unreal.EditorLoadingAndSavingUtils.save_current_level()
    unreal.EditorAssetLibrary.save_asset(LEVEL_PATH, only_if_is_dirty=False)
    write_report(
        church_actors,
        road_actors,
        test_actors,
        created_anchor,
        organized_count,
        road_test_actor,
        road_mesh_path,
        road_imported,
        replaced_roads,
    )
    unreal.log("Penance post-Step-8 asset setup complete.")


if __name__ == "__main__":
    main()
