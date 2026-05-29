"""Scale Player.blend to demo character size and add game-speed locomotion actions.

Target game scale:
- Unreal uses centimeters.
- 1 Blender unit is treated as 1 meter for FBX export.
- Demo standing player target is 165 cm, so the mesh/rig should be 1.65 BU tall.

Run from Blender:
  blender --background --python scale_player_and_add_game_locomotion.py -- SRC.blend REPORT.txt
"""

from __future__ import annotations

import math
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

import bpy
from mathutils import Matrix, Vector


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BLEND = PROJECT_ROOT / "Content" / "Player" / "Player.blend"
DEFAULT_REPORT = PROJECT_ROOT / "Saved" / "PlayerGameScaleLocomotionReport.txt"
BACKUP_PATH = PROJECT_ROOT / "Content" / "Player" / "BlenderSource" / "Backups" / "Player_before_game_scale_locomotion.blend"

RIG_NAME = "RIG_Player_Rigify_Humanoid_IK"
MESH_NAME = "Mesh_0"
TARGET_HEIGHT_M = 1.65
FPS = 30
WALK_SPEED_UU = 250.0
RUN_SPEED_UU = 550.0


@dataclass(frozen=True)
class ActionSpec:
    name: str
    duration: float
    speed_uu: float
    turn_degrees: float = 0.0
    mode: str = "walk"
    root_motion: bool = True
    looping: bool = True


ACTION_SPECS = [
    ActionSpec("AN_Player_Idle_FeetTogether", 2.0, 0.0, mode="idle", root_motion=False, looping=True),
    ActionSpec("AN_Player_Idle_Staggered", 2.0, 0.0, mode="idle_staggered", root_motion=False, looping=True),
    ActionSpec("AN_Player_Walk_Forward_Loop", 1.0, WALK_SPEED_UU, mode="walk", looping=True),
    ActionSpec("AN_Player_Walk_Backward_Loop", 1.0, WALK_SPEED_UU, mode="walk_backward", looping=True),
    ActionSpec("AN_Player_TurnInPlace_Left", 0.75, 0.0, turn_degrees=90.0, mode="turn", root_motion=True, looping=False),
    ActionSpec("AN_Player_TurnInPlace_Right", 0.75, 0.0, turn_degrees=-90.0, mode="turn", root_motion=True, looping=False),
    ActionSpec("AN_Player_Walk_Turn_Left_Loop", 1.0, WALK_SPEED_UU, turn_degrees=35.0, mode="walk", looping=True),
    ActionSpec("AN_Player_Walk_Turn_Right_Loop", 1.0, WALK_SPEED_UU, turn_degrees=-35.0, mode="walk", looping=True),
    ActionSpec("AN_Player_Run_Forward_Loop", 0.8, RUN_SPEED_UU, mode="run", looping=True),
    ActionSpec("AN_Player_Run_Turn_Left_Loop", 0.8, RUN_SPEED_UU, turn_degrees=38.0, mode="run", looping=True),
    ActionSpec("AN_Player_Run_Turn_Right_Loop", 0.8, RUN_SPEED_UU, turn_degrees=-38.0, mode="run", looping=True),
    ActionSpec("AN_Player_Vault_100cm", 1.15, 0.0, mode="vault", root_motion=True, looping=False),
    ActionSpec("AN_Player_StartWalk_Forward", 0.45, WALK_SPEED_UU, mode="start_walk", looping=False),
    ActionSpec("AN_Player_StopWalk_Forward", 0.45, WALK_SPEED_UU, mode="stop_walk", looping=False),
]


def args_after_separator() -> tuple[Path, Path]:
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    src = Path(args[0]).expanduser().resolve() if args else DEFAULT_BLEND
    report = Path(args[1]).expanduser().resolve() if len(args) > 1 else DEFAULT_REPORT
    if not src.exists():
        raise SystemExit(f"Blend file does not exist: {src}")
    report.parent.mkdir(parents=True, exist_ok=True)
    BACKUP_PATH.parent.mkdir(parents=True, exist_ok=True)
    return src, report


def ensure_backup(src: Path) -> str:
    if BACKUP_PATH.exists():
        return f"Backup already exists: {BACKUP_PATH}"
    shutil.copy2(src, BACKUP_PATH)
    return f"Backup created: {BACKUP_PATH}"


def world_bounds(obj: bpy.types.Object) -> tuple[Vector, Vector]:
    verts = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    return (
        Vector((min(v.x for v in verts), min(v.y for v in verts), min(v.z for v in verts))),
        Vector((max(v.x for v in verts), max(v.y for v in verts), max(v.z for v in verts))),
    )


def scale_armature_data(armature: bpy.types.Object, factor: float) -> None:
    bpy.ops.object.mode_set(mode="OBJECT") if bpy.ops.object.mode_set.poll() else None
    was_hidden_viewport = armature.hide_viewport
    was_hidden_render = armature.hide_render
    was_hidden_layer = armature.hide_get()
    armature.hide_viewport = False
    armature.hide_set(False)
    bpy.ops.object.select_all(action="DESELECT")
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    with bpy.context.temp_override(active_object=armature, object=armature, selected_objects=[armature], selected_editable_objects=[armature]):
        bpy.ops.object.mode_set(mode="EDIT")
        for bone in armature.data.edit_bones:
            bone.head *= factor
            bone.tail *= factor
            bone.roll = bone.roll
        bpy.ops.object.mode_set(mode="OBJECT")
    armature.hide_viewport = was_hidden_viewport
    armature.hide_render = was_hidden_render
    armature.hide_set(was_hidden_layer)


def scale_widget_objects(factor: float) -> int:
    count = 0
    for obj in bpy.data.objects:
        if not obj.name.startswith("WGT-"):
            continue
        obj.location *= factor
        obj.scale *= factor
        obj.hide_viewport = True
        obj.hide_render = True
        try:
            obj.hide_set(True)
        except RuntimeError:
            pass
        count += 1
    for collection in bpy.data.collections:
        if collection.name.startswith("WGTS_"):
            collection.hide_viewport = True
            collection.hide_render = True
    return count


def scale_mesh_vertices(mesh: bpy.types.Object, factor: float) -> None:
    for vertex in mesh.data.vertices:
        vertex.co *= factor
    mesh.data.update()


def scale_existing_actions(factor: float) -> int:
    scaled_curves = 0
    for action in bpy.data.actions:
        for curve in action.fcurves:
            if curve.data_path.endswith("location"):
                for key in curve.keyframe_points:
                    key.co_ui.y *= factor
                    key.handle_left.y *= factor
                    key.handle_right.y *= factor
                scaled_curves += 1
    return scaled_curves


def ensure_game_scale(mesh: bpy.types.Object, rig: bpy.types.Object) -> tuple[float, float, float, int, int]:
    mesh.hide_viewport = False
    mesh.hide_render = False
    mesh.hide_set(False)
    rig.hide_viewport = False
    rig.hide_render = False
    rig.hide_set(False)

    min_v, max_v = world_bounds(mesh)
    old_height = max_v.z - min_v.z
    if old_height <= 0.001:
        raise RuntimeError("Mesh height is invalid")
    factor = TARGET_HEIGHT_M / old_height
    if abs(factor - 1.0) < 0.0005:
        return old_height, old_height, 1.0, 0, 0

    # Mesh and armatures are identity-space after the Rigify pass. Scale their
    # data, not object transforms, so Unreal imports at real size without a
    # component scale workaround.
    scale_mesh_vertices(mesh, factor)
    armature_count = 0
    for obj in bpy.data.objects:
        if obj.type == "ARMATURE":
            scale_armature_data(obj, factor)
            armature_count += 1

    widget_count = scale_widget_objects(factor)
    scale_existing_actions(factor)

    min_after, max_after = world_bounds(mesh)
    return old_height, max_after.z - min_after.z, factor, armature_count, widget_count


def pose_bone(rig: bpy.types.Object, name: str) -> bpy.types.PoseBone | None:
    return rig.pose.bones.get(name)


def clear_pose(rig: bpy.types.Object) -> None:
    bpy.ops.object.mode_set(mode="OBJECT") if bpy.ops.object.mode_set.poll() else None
    bpy.ops.object.select_all(action="DESELECT")
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    with bpy.context.temp_override(active_object=rig, object=rig, selected_objects=[rig], selected_editable_objects=[rig]):
        bpy.ops.object.mode_set(mode="POSE")
    for bone in rig.pose.bones:
        bone.rotation_mode = "XYZ"
        bone.location = (0.0, 0.0, 0.0)
        bone.rotation_euler = (0.0, 0.0, 0.0)
        bone.scale = (1.0, 1.0, 1.0)


def key_transform(rig: bpy.types.Object, name: str, frame: int, loc=None, rot=None, scale=None) -> bool:
    bone = pose_bone(rig, name)
    if not bone:
        return False
    bone.rotation_mode = "XYZ"
    if loc is not None:
        bone.location = loc
    if rot is not None:
        bone.rotation_euler = rot
    if scale is not None:
        bone.scale = scale
    bone.keyframe_insert("location", frame=frame)
    bone.keyframe_insert("rotation_euler", frame=frame)
    bone.keyframe_insert("scale", frame=frame)
    return True


def set_frame_pose(rig: bpy.types.Object, spec: ActionSpec, frame: int, alpha: float) -> int:
    keyed = 0
    cycle = math.sin(alpha * math.tau)
    lift = max(0.0, math.sin(alpha * math.tau))
    opposite_lift = max(0.0, math.sin(alpha * math.tau + math.pi))
    stride = 0.22 if spec.mode.startswith("walk") or spec.mode in {"start_walk", "stop_walk"} else 0.34
    arm_swing = 0.22 if spec.mode.startswith("walk") or spec.mode in {"start_walk", "stop_walk"} else 0.38

    root_y = 0.0
    if spec.root_motion and spec.speed_uu > 0.0:
        distance_m = spec.speed_uu / 100.0 * spec.duration
        root_y = -distance_m * alpha
    root_z = 0.0
    if spec.mode == "vault":
        root_y = -1.05 * alpha
        root_z = 0.55 * math.sin(math.pi * alpha)

    root_turn = math.radians(spec.turn_degrees) * alpha if spec.root_motion else 0.0
    keyed += key_transform(rig, "root", frame, loc=(0.0, root_y, root_z), rot=(0.0, 0.0, root_turn))

    if spec.mode == "idle":
        breathe = math.sin(alpha * math.tau) * 0.018
        keyed += key_transform(rig, "torso", frame, rot=(breathe, 0.0, 0.0))
        keyed += key_transform(rig, "chest", frame, rot=(breathe * 0.6, 0.0, 0.0))
        keyed += key_transform(rig, "head", frame, rot=(-breathe * 0.4, 0.0, 0.0))
        return keyed

    if spec.mode == "idle_staggered":
        breathe = math.sin(alpha * math.tau) * 0.018
        keyed += key_transform(rig, "torso", frame, rot=(breathe, 0.0, 0.0))
        keyed += key_transform(rig, "thigh_fk.L", frame, rot=(0.035, 0.0, 0.0))
        keyed += key_transform(rig, "shin_fk.L", frame, rot=(-0.025, 0.0, 0.0))
        keyed += key_transform(rig, "foot_fk.L", frame, rot=(0.015, 0.0, 0.0))
        return keyed

    if spec.mode == "turn":
        lean = 0.05 if spec.turn_degrees > 0.0 else -0.05
        keyed += key_transform(rig, "hips", frame, rot=(0.0, 0.0, lean * math.sin(math.pi * alpha)))
        keyed += key_transform(rig, "chest", frame, rot=(0.0, 0.0, lean * 0.6 * math.sin(math.pi * alpha)))
        keyed += key_transform(rig, "thigh_fk.L", frame, rot=(0.06 * math.sin(math.pi * alpha), 0.0, 0.03))
        keyed += key_transform(rig, "thigh_fk.R", frame, rot=(-0.04 * math.sin(math.pi * alpha), 0.0, -0.03))
        return keyed

    if spec.mode == "vault":
        reach = math.sin(math.pi * min(alpha * 1.25, 1.0))
        tuck = math.sin(math.pi * alpha)
        keyed += key_transform(rig, "torso", frame, rot=(0.35 * tuck, 0.0, 0.0))
        keyed += key_transform(rig, "chest", frame, rot=(0.22 * tuck, 0.0, 0.0))
        keyed += key_transform(rig, "upper_arm_fk.L", frame, rot=(-0.95 * reach, 0.0, -0.35))
        keyed += key_transform(rig, "upper_arm_fk.R", frame, rot=(-0.95 * reach, 0.0, 0.35))
        keyed += key_transform(rig, "forearm_fk.L", frame, rot=(-0.35 * reach, 0.0, 0.0))
        keyed += key_transform(rig, "forearm_fk.R", frame, rot=(-0.35 * reach, 0.0, 0.0))
        keyed += key_transform(rig, "thigh_fk.L", frame, rot=(0.85 * tuck, 0.0, 0.0))
        keyed += key_transform(rig, "thigh_fk.R", frame, rot=(0.65 * tuck, 0.0, 0.0))
        keyed += key_transform(rig, "shin_fk.L", frame, rot=(-1.05 * tuck, 0.0, 0.0))
        keyed += key_transform(rig, "shin_fk.R", frame, rot=(-0.85 * tuck, 0.0, 0.0))
        return keyed

    if spec.mode == "start_walk":
        ramp = alpha
        cycle *= ramp
        lift *= ramp
        opposite_lift *= ramp
    elif spec.mode == "stop_walk":
        ramp = 1.0 - alpha
        cycle *= ramp
        lift *= ramp
        opposite_lift *= ramp

    if spec.mode == "walk_backward":
        stride *= -0.65

    turn_lean = math.radians(spec.turn_degrees) * 0.20
    keyed += key_transform(rig, "hips", frame, rot=(0.035 * abs(cycle), 0.0, turn_lean + 0.035 * cycle))
    keyed += key_transform(rig, "torso", frame, rot=(-0.025 * abs(cycle), 0.0, -turn_lean * 0.5))
    keyed += key_transform(rig, "chest", frame, rot=(0.025 * abs(cycle), 0.0, -turn_lean * 0.35))
    keyed += key_transform(rig, "head", frame, rot=(-0.015 * abs(cycle), 0.0, 0.0))
    keyed += key_transform(rig, "thigh_fk.L", frame, rot=(stride * cycle, 0.0, 0.02))
    keyed += key_transform(rig, "shin_fk.L", frame, rot=(-0.42 * lift, 0.0, 0.0))
    keyed += key_transform(rig, "foot_fk.L", frame, rot=(0.14 * cycle - 0.08 * lift, 0.0, 0.0))
    keyed += key_transform(rig, "toe_fk.L", frame, rot=(-0.10 * lift, 0.0, 0.0))
    keyed += key_transform(rig, "thigh_fk.R", frame, rot=(-stride * cycle, 0.0, -0.02))
    keyed += key_transform(rig, "shin_fk.R", frame, rot=(-0.42 * opposite_lift, 0.0, 0.0))
    keyed += key_transform(rig, "foot_fk.R", frame, rot=(-0.14 * cycle - 0.08 * opposite_lift, 0.0, 0.0))
    keyed += key_transform(rig, "toe_fk.R", frame, rot=(-0.10 * opposite_lift, 0.0, 0.0))
    keyed += key_transform(rig, "upper_arm_fk.L", frame, rot=(-arm_swing * cycle, 0.0, -0.10))
    keyed += key_transform(rig, "forearm_fk.L", frame, rot=(0.12 + 0.08 * abs(cycle), 0.0, 0.0))
    keyed += key_transform(rig, "upper_arm_fk.R", frame, rot=(arm_swing * cycle, 0.0, 0.10))
    keyed += key_transform(rig, "forearm_fk.R", frame, rot=(0.12 + 0.08 * abs(cycle), 0.0, 0.0))
    return keyed


def create_action(rig: bpy.types.Object, spec: ActionSpec) -> tuple[str, int, int, float]:
    old = bpy.data.actions.get(spec.name)
    if old:
        bpy.data.actions.remove(old)
    clear_pose(rig)
    action = bpy.data.actions.new(spec.name)
    rig.animation_data_create()
    rig.animation_data.action = action
    frames = max(2, int(round(spec.duration * FPS)) + 1)
    keyed = 0
    for index in range(frames):
        frame = index + 1
        alpha = index / (frames - 1)
        bpy.context.scene.frame_set(frame)
        keyed += set_frame_pose(rig, spec, frame, alpha)
    action.use_fake_user = True
    action["speed_uu_per_s"] = spec.speed_uu
    action["duration_seconds"] = spec.duration
    action["root_motion_distance_cm"] = spec.speed_uu * spec.duration if spec.speed_uu > 0.0 else (105.0 if spec.mode == "vault" else 0.0)
    action["turn_degrees"] = spec.turn_degrees
    action["game_scale_height_cm"] = TARGET_HEIGHT_M * 100.0
    if spec.looping:
        action.use_cyclic = True
    return action.name, frames, keyed, float(action["root_motion_distance_cm"])


def hide_export_noise(mesh: bpy.types.Object, rig: bpy.types.Object) -> None:
    for obj in bpy.data.objects:
        if obj.name.startswith("WGT-"):
            obj.hide_viewport = True
            obj.hide_render = True
            try:
                obj.hide_set(True)
            except RuntimeError:
                pass
        elif obj.type == "ARMATURE" and obj.name not in {RIG_NAME}:
            obj.hide_viewport = True
            obj.hide_render = True
            try:
                obj.hide_set(True)
            except RuntimeError:
                pass
    mesh.hide_viewport = False
    mesh.hide_render = False
    mesh.hide_set(False)
    rig.hide_viewport = False
    rig.hide_render = False
    rig.hide_set(False)


def leave_file_in_neutral_pose(rig: bpy.types.Object) -> None:
    if rig.animation_data:
        rig.animation_data.action = None
    bpy.context.scene.frame_set(1)
    clear_pose(rig)


def main() -> None:
    src, report = args_after_separator()
    backup_line = ensure_backup(src)
    bpy.ops.wm.open_mainfile(filepath=str(src), load_ui=False)
    bpy.context.scene.render.fps = FPS

    mesh = bpy.data.objects.get(MESH_NAME)
    rig = bpy.data.objects.get(RIG_NAME)
    if not mesh or mesh.type != "MESH":
        raise SystemExit(f"Missing mesh: {MESH_NAME}")
    if not rig or rig.type != "ARMATURE":
        raise SystemExit(f"Missing rig: {RIG_NAME}")

    old_height, new_height, scale_factor, armature_count, widget_count = ensure_game_scale(mesh, rig)
    action_rows = [create_action(rig, spec) for spec in ACTION_SPECS]
    hide_export_noise(mesh, rig)
    leave_file_in_neutral_pose(rig)

    min_v, max_v = world_bounds(mesh)
    deform_points = [
        rig.matrix_world @ bone.head_local
        for bone in rig.data.bones
        if bone.use_deform
    ] + [
        rig.matrix_world @ bone.tail_local
        for bone in rig.data.bones
        if bone.use_deform
    ]
    deform_min = Vector((min(v.x for v in deform_points), min(v.y for v in deform_points), min(v.z for v in deform_points)))
    deform_max = Vector((max(v.x for v in deform_points), max(v.y for v in deform_points), max(v.z for v in deform_points)))
    modifier_summary = ", ".join(
        f"{mod.name}:{mod.type}:{mod.object.name if getattr(mod, 'object', None) else 'none'}"
        for mod in mesh.modifiers
    )

    lines = [
        "PLAYER_GAME_SCALE_LOCOMOTION_REPORT",
        f"Blend: {src}",
        backup_line,
        "Scale target: 165 cm demo player standing height",
        f"Old mesh height BU/m: {old_height:.4f}",
        f"New mesh height BU/m: {new_height:.4f}",
        f"Scale factor applied: {scale_factor:.6f}",
        f"Armatures scaled: {armature_count}",
        f"Rigify widgets hidden/scaled: {widget_count}",
        f"Mesh visible: hide_get={mesh.hide_get()} hide_viewport={mesh.hide_viewport} hide_render={mesh.hide_render}",
        f"Mesh parent: {mesh.parent.name if mesh.parent else 'none'}",
        f"Mesh modifiers: {modifier_summary}",
        f"Mesh bounds: min=({min_v.x:.4f},{min_v.y:.4f},{min_v.z:.4f}) max=({max_v.x:.4f},{max_v.y:.4f},{max_v.z:.4f})",
        f"Deform bone bounds: min=({deform_min.x:.4f},{deform_min.y:.4f},{deform_min.z:.4f}) max=({deform_max.x:.4f},{deform_max.y:.4f},{deform_max.z:.4f})",
        "Speed calibration:",
        f"- Walk: {WALK_SPEED_UU:.1f} UU/s = {WALK_SPEED_UU / 100.0:.2f} m/s",
        f"- Run: {RUN_SPEED_UU:.1f} UU/s = {RUN_SPEED_UU / 100.0:.2f} m/s",
        "Actions:",
    ]
    for name, frames, keyed, root_cm in action_rows:
        action = bpy.data.actions[name]
        lines.append(
            f"- {name}: frames={frames} duration={action['duration_seconds']:.3f}s "
            f"speed={action['speed_uu_per_s']:.1f}UU/s root_motion={root_cm:.1f}cm "
            f"turn={action['turn_degrees']:.1f}deg keyed={keyed}"
        )

    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(src))
    print(f"PLAYER_GAME_SCALE_LOCOMOTION_DONE: {src}")
    print(f"REPORT: {report}")
    sys.stdout.flush()
    os._exit(0)


main()
