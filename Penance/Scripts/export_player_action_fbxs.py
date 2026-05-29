"""Export each Player.blend AN_Player_* action as an individual FBX."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import bpy


RIG_NAME = "RIG_Player_Rigify_Humanoid_IK"
MESH_NAME = "Mesh_0"


def args_after_separator() -> tuple[Path, Path, Path]:
    if "--" not in sys.argv:
        raise SystemExit("Expected -- SRC.blend OUT_DIR REPORT.txt")
    args = sys.argv[sys.argv.index("--") + 1 :]
    if len(args) != 3:
        raise SystemExit("Expected -- SRC.blend OUT_DIR REPORT.txt")
    src = Path(args[0]).expanduser().resolve()
    out_dir = Path(args[1]).expanduser().resolve()
    report = Path(args[2]).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    return src, out_dir, report


def main() -> None:
    src, out_dir, report = args_after_separator()
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
    rig.animation_data_create()

    actions = sorted([action for action in bpy.data.actions if action.name.startswith("AN_Player_")], key=lambda item: item.name)
    lines = [
        "PLAYER_ACTION_FBX_EXPORT_REPORT",
        f"Blend: {src}",
        f"Output directory: {out_dir}",
        f"Action count: {len(actions)}",
    ]
    for action in actions:
        rig.animation_data.action = action
        start, end = action.frame_range
        bpy.context.scene.frame_start = int(start)
        bpy.context.scene.frame_end = int(end)
        out = out_dir / f"{action.name}.fbx"
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
            bake_anim_use_all_actions=False,
            bake_anim_use_nla_strips=False,
            bake_anim_force_startend_keying=True,
            path_mode="AUTO",
        )
        lines.append(
            f"- {action.name}: fbx={out} frames={int(end - start + 1)} "
            f"speed={action.get('speed_uu_per_s', 'n/a')} root_cm={action.get('root_motion_distance_cm', 'n/a')}"
        )

    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"EXPORTED_PLAYER_ACTION_FBXS: {out_dir}")
    sys.stdout.flush()
    os._exit(0)


main()
