from pathlib import Path

import unreal


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEVEL_PATH = "/Game/Maps/Penance_Suburban_Blockout"
REPORT_PATH = PROJECT_ROOT / "Saved" / "PenanceIntegratedAssetInspect.txt"

ASSET_DIRS = [
    "/Game/Map_Assets/Road/gltf/source/scene/StaticMeshes",
    "/Game/PenanceAssets/Enemies/PenanceCarrier/PenanceRoughDraft",
    "/Game/Player",
]


def bounds_text(bounds):
    origin = bounds.origin
    extent = bounds.box_extent
    return (
        f"origin=({origin.x:.1f},{origin.y:.1f},{origin.z:.1f}) "
        f"extent=({extent.x:.1f},{extent.y:.1f},{extent.z:.1f})"
    )


def static_mesh_assets_under(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        return []
    meshes = []
    for asset_path in unreal.EditorAssetLibrary.list_assets(path, recursive=True, include_folder=False):
        asset = unreal.EditorAssetLibrary.load_asset(asset_path)
        if isinstance(asset, unreal.StaticMesh):
            meshes.append(asset)
    return sorted(meshes, key=lambda mesh: mesh.get_path_name())


def main():
    lines = ["PENANCE_INTEGRATED_ASSET_INSPECT"]
    for directory in ASSET_DIRS:
        lines.append(f"Directory: {directory}")
        meshes = static_mesh_assets_under(directory)
        lines.append(f"StaticMesh count: {len(meshes)}")
        for mesh in meshes:
            lines.append(f"- {mesh.get_path_name()} {bounds_text(mesh.get_bounds())}")

    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(LEVEL_PATH)
    actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
    lines.append(f"Level actors: {len(actors)}")
    for actor in actors:
        label = actor.get_actor_label()
        if "Road" in label or "Penance" in label or "Player" in label:
            path = ""
            try:
                mesh = actor.static_mesh_component.static_mesh
                path = mesh.get_path_name() if mesh else ""
            except Exception:
                pass
            lines.append(
                f"Actor {label} folder={actor.get_folder_path()} loc={actor.get_actor_location()} "
                f"scale={actor.get_actor_scale3d()} mesh={path}"
            )

    report = "\n".join(lines) + "\n"
    REPORT_PATH.write_text(report)
    print(report)


if __name__ == "__main__":
    main()
