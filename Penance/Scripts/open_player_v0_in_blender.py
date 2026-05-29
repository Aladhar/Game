from __future__ import annotations

from pathlib import Path

import bpy


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PLAYER_GLB = PROJECT_ROOT / "Content" / "Player" / "PlayerV0.glb"


def main() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    bpy.ops.import_scene.gltf(filepath=str(PLAYER_GLB))

    for obj in bpy.context.scene.objects:
        obj.select_set(obj.type == "MESH")
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if meshes:
        bpy.context.view_layer.objects.active = meshes[0]

    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0


main()
