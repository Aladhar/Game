"""Export the game-scale Rigify player mesh/rig and all actions to FBX."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import bpy


RIG_NAME = "RIG_Player_Rigify_Humanoid_IK"
MESH_NAME = "Mesh_0"


def args_after_separator() -> tuple[Path, Path, Path]:
    if "--" not in sys.argv:
        raise SystemExit("Expected -- SRC.blend OUT.fbx REPORT.txt")
    args = sys.argv[sys.argv.index("--") + 1 :]
    if len(args) != 3:
        raise SystemExit("Expected -- SRC.blend OUT.fbx REPORT.txt")
    src = Path(args[0]).expanduser().resolve()
    out = Path(args[1]).expanduser().resolve()
    report = Path(args[2]).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    return src, out, report


def main() -> None:
    src, out, report = args_after_separator()
    bpy.ops.wm.open_mainfile(filepath=str(src), load_ui=False)
    rig = bpy.data.objects.get(RIG_NAME)
    mesh = bpy.data.objects.get(MESH_NAME)
    if not rig or rig.type != "ARMATURE":
        raise SystemExit(f"Missing rig: {RIG_NAME}")
    if not mesh or mesh.type != "MESH":
        raise SystemExit(f"Missing mesh: {MESH_NAME}")

    for obj in bpy.data.objects:
        obj.select_set(False)
        if obj.name.startswith("WGT-") or (obj.type == "ARMATURE" and obj.name != RIG_NAME) or (obj.type == "MESH" and obj.name != MESH_NAME):
            obj.hide_viewport = True
            obj.hide_render = True

    mesh.hide_viewport = False
    mesh.hide_render = False
    mesh.hide_set(False)
    rig.hide_viewport = False
    rig.hide_render = False
    rig.hide_set(False)
    mesh.select_set(True)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig

    bpy.ops.export_scene.fbx(
        filepath=str(out),
        use_selection=True,
        object_types={"ARMATURE", "MESH"},
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL",
        bake_space_transform=False,
        add_leaf_bones=False,
        primary_bone_axis="Y",
        secondary_bone_axis="X",
        bake_anim=True,
        bake_anim_use_all_actions=True,
        bake_anim_use_nla_strips=False,
        bake_anim_force_startend_keying=True,
        path_mode="AUTO",
    )

    actions = [action for action in bpy.data.actions if action.name.startswith("AN_Player_")]
    lines = [
        "PLAYER_GAME_SCALE_FBX_EXPORT_REPORT",
        f"Blend: {src}",
        f"FBX: {out}",
        f"Mesh: {mesh.name} vertices={len(mesh.data.vertices)} groups={len(mesh.vertex_groups)}",
        f"Rig: {rig.name} bones={len(rig.data.bones)} deform={sum(1 for bone in rig.data.bones if bone.use_deform)}",
        f"Actions exported: {len(actions)}",
    ]
    for action in sorted(actions, key=lambda item: item.name):
        lines.append(
            f"- {action.name}: speed={action.get('speed_uu_per_s', 'n/a')} "
            f"duration={action.get('duration_seconds', 'n/a')} "
            f"root_cm={action.get('root_motion_distance_cm', 'n/a')} "
            f"turn={action.get('turn_degrees', 'n/a')}"
        )
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"EXPORTED_PLAYER_GAME_SCALE_FBX: {out}")
    sys.stdout.flush()
    os._exit(0)


main()
