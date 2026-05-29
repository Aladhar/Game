"""Build a clean Blender-only player deform rig with IK controls.

The previous Rigify generated control rig is useful as a source of fitted DEF
bone rest positions, but its constraint stack was deforming Mesh_0 at neutral.
This script copies only the fitted deform bones into a clean armature, adds
simple IK/root controls, reconnects Mesh_0 to that clean rig, and authors the
game-scale locomotion actions directly on the clean rig.
"""

from __future__ import annotations

import math
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

import bpy
from mathutils import Vector

from penance_script_safety import filtered_script_args, require_asset_write_permission


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BLEND = PROJECT_ROOT / "Content" / "Player" / "Player.blend"
DEFAULT_REPORT = PROJECT_ROOT / "Saved" / "PlayerCleanDeformIKRigReport.txt"
BACKUP_PATH = PROJECT_ROOT / "Content" / "Player" / "BlenderSource" / "Backups" / "Player_before_clean_deform_ik_rebuild.blend"

MESH_NAME = "Mesh_0"
SOURCE_RIG_NAME = "RIG_Player_Rigify_Humanoid_IK"
CLEAN_RIG_NAME = "ARM_Player_Clean_Deform_IK"
FPS = 30
WALK_SPEED_UU = 250.0
RUN_SPEED_UU = 550.0


@dataclass(frozen=True)
class ActionSpec:
    name: str
    duration: float
    speed_uu: float
    mode: str
    turn_degrees: float = 0.0
    root_motion: bool = True
    looping: bool = True


ACTION_SPECS = [
    ActionSpec("AN_Player_Idle_FeetTogether", 2.0, 0.0, "idle", root_motion=False),
    ActionSpec("AN_Player_Idle_Staggered", 2.0, 0.0, "idle_staggered", root_motion=False),
    ActionSpec("AN_Player_Walk_Forward_Loop", 1.0, WALK_SPEED_UU, "walk"),
    ActionSpec("AN_Player_Walk_Backward_Loop", 1.0, WALK_SPEED_UU, "walk_backward"),
    ActionSpec("AN_Player_TurnInPlace_Left", 0.75, 0.0, "turn", turn_degrees=90.0, looping=False),
    ActionSpec("AN_Player_TurnInPlace_Right", 0.75, 0.0, "turn", turn_degrees=-90.0, looping=False),
    ActionSpec("AN_Player_Walk_Turn_Left_Loop", 1.0, WALK_SPEED_UU, "walk", turn_degrees=35.0),
    ActionSpec("AN_Player_Walk_Turn_Right_Loop", 1.0, WALK_SPEED_UU, "walk", turn_degrees=-35.0),
    ActionSpec("AN_Player_Run_Forward_Loop", 0.8, RUN_SPEED_UU, "run"),
    ActionSpec("AN_Player_Run_Turn_Left_Loop", 0.8, RUN_SPEED_UU, "run", turn_degrees=38.0),
    ActionSpec("AN_Player_Run_Turn_Right_Loop", 0.8, RUN_SPEED_UU, "run", turn_degrees=-38.0),
    ActionSpec("AN_Player_Vault_100cm", 1.15, 0.0, "vault", looping=False),
    ActionSpec("AN_Player_StartWalk_Forward", 0.45, WALK_SPEED_UU, "start_walk", looping=False),
    ActionSpec("AN_Player_StopWalk_Forward", 0.45, WALK_SPEED_UU, "stop_walk", looping=False),
]


def args_after_separator() -> tuple[Path, Path]:
    args = filtered_script_args(sys.argv[sys.argv.index("--") + 1 :]) if "--" in sys.argv else []
    src = Path(args[0]).expanduser().resolve() if args else DEFAULT_BLEND
    report = Path(args[1]).expanduser().resolve() if len(args) > 1 else DEFAULT_REPORT
    if not src.exists():
        raise SystemExit(f"Blend file does not exist: {src}")
    BACKUP_PATH.parent.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    return src, report


def ensure_backup(src: Path) -> str:
    if BACKUP_PATH.exists():
        return f"Backup already exists: {BACKUP_PATH}"
    shutil.copy2(src, BACKUP_PATH)
    return f"Backup created: {BACKUP_PATH}"


def bounds_from_points(points: list[Vector]) -> tuple[Vector, Vector]:
    return (
        Vector((min(v.x for v in points), min(v.y for v in points), min(v.z for v in points))),
        Vector((max(v.x for v in points), max(v.y for v in points), max(v.z for v in points))),
    )


def mesh_bounds(obj: bpy.types.Object, evaluated: bool) -> tuple[Vector, Vector]:
    if evaluated:
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = obj.evaluated_get(depsgraph)
        data = eval_obj.to_mesh()
        points = [eval_obj.matrix_world @ vertex.co for vertex in data.vertices]
        eval_obj.to_mesh_clear()
    else:
        points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    return bounds_from_points(points)


def fmt_bounds(min_v: Vector, max_v: Vector) -> str:
    return (
        f"min=({min_v.x:.4f},{min_v.y:.4f},{min_v.z:.4f}) "
        f"max=({max_v.x:.4f},{max_v.y:.4f},{max_v.z:.4f}) "
        f"size=({max_v.x - min_v.x:.4f},{max_v.y - min_v.y:.4f},{max_v.z - min_v.z:.4f})"
    )


def clear_pose(armature: bpy.types.Object) -> None:
    if armature.animation_data:
        armature.animation_data.action = None
    for bone in armature.pose.bones:
        bone.rotation_mode = "XYZ"
        bone.location = (0.0, 0.0, 0.0)
        bone.rotation_euler = (0.0, 0.0, 0.0)
        bone.scale = (1.0, 1.0, 1.0)


def remove_existing_clean_rig() -> None:
    obj = bpy.data.objects.get(CLEAN_RIG_NAME)
    if obj:
        data = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        if data and data.users == 0:
            bpy.data.armatures.remove(data)


def add_edit_bone(ebones: bpy.types.ArmatureEditBones, name: str, head: Vector, tail: Vector, roll: float = 0.0):
    bone = ebones.new(name)
    bone.head = head
    if (tail - head).length < 0.002:
        tail = head + Vector((0.0, 0.0, 0.02))
    bone.tail = tail
    bone.roll = roll
    return bone


def make_clean_rig(source: bpy.types.Object) -> bpy.types.Object:
    remove_existing_clean_rig()
    armature_data = bpy.data.armatures.new(f"{CLEAN_RIG_NAME}_Data")
    rig = bpy.data.objects.new(CLEAN_RIG_NAME, armature_data)
    bpy.context.collection.objects.link(rig)
    rig.matrix_world = source.matrix_world.copy()
    rig.show_in_front = True
    armature_data.display_type = "BBONE"

    deform_names = [bone.name for bone in source.data.bones if bone.use_deform and bone.name.startswith("DEF-")]
    deform_set = set(deform_names)

    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = armature_data.edit_bones

    for name in deform_names:
        src_bone = source.data.bones[name]
        bone = add_edit_bone(eb, name, src_bone.head_local.copy(), src_bone.tail_local.copy())
        bone.use_deform = True

    root_head = Vector((0.0, 0.0, -0.06))
    root_tail = Vector((0.0, 0.0, 0.18))
    ctrl_root = add_edit_bone(eb, "CTRL_root", root_head, root_tail)
    ctrl_root.use_deform = False

    for name in deform_names:
        src_parent = source.data.bones[name].parent
        parent_name = None
        while src_parent:
            if src_parent.name in deform_set:
                parent_name = src_parent.name
                break
            src_parent = src_parent.parent
        if parent_name:
            eb[name].parent = eb[parent_name]
            eb[name].use_connect = False
        else:
            eb[name].parent = ctrl_root

    for side in ("L", "R"):
        sign = 1.0 if side == "L" else -1.0
        hand = eb.get(f"DEF-hand.{side}")
        foot = eb.get(f"DEF-foot.{side}")
        forearm = eb.get(f"DEF-forearm.{side}")
        shin = eb.get(f"DEF-shin.{side}")
        if hand:
            ctrl = add_edit_bone(eb, f"CTRL_hand_ik.{side}", hand.tail + Vector((0.0, -0.10, 0.0)), hand.tail + Vector((0.0, -0.10, 0.16)))
            ctrl.use_deform = False
            ctrl.parent = ctrl_root
        if forearm:
            pole = add_edit_bone(eb, f"CTRL_elbow_pole.{side}", forearm.head + Vector((0.0, -0.35, 0.0)), forearm.head + Vector((0.0, -0.35, 0.12)))
            pole.use_deform = False
            pole.parent = ctrl_root
        if foot:
            ctrl = add_edit_bone(eb, f"CTRL_foot_ik.{side}", foot.tail + Vector((0.0, -0.10, 0.0)), foot.tail + Vector((0.0, -0.10, 0.16)))
            ctrl.use_deform = False
            ctrl.parent = ctrl_root
        if shin:
            pole = add_edit_bone(eb, f"CTRL_knee_pole.{side}", shin.head + Vector((0.0, -0.40, 0.0)), shin.head + Vector((0.0, -0.40, 0.14)))
            pole.use_deform = False
            pole.parent = ctrl_root

        # A tiny side offset keeps Blender from drawing overlapping control axes.
        for control_name in (f"CTRL_hand_ik.{side}", f"CTRL_elbow_pole.{side}", f"CTRL_foot_ik.{side}", f"CTRL_knee_pole.{side}"):
            control = eb.get(control_name)
            if control:
                control.head.x += sign * 0.015
                control.tail.x += sign * 0.015

    bpy.ops.object.mode_set(mode="POSE")
    for side in ("L", "R"):
        arm_target = rig.pose.bones.get(f"DEF-forearm.{side}.001")
        if arm_target:
            constraint = arm_target.constraints.new(type="IK")
            constraint.name = f"IK_hand_{side}_available"
            constraint.target = rig
            constraint.subtarget = f"CTRL_hand_ik.{side}"
            constraint.pole_target = rig
            constraint.pole_subtarget = f"CTRL_elbow_pole.{side}"
            constraint.chain_count = 4
            constraint.influence = 0.0

        leg_target = rig.pose.bones.get(f"DEF-shin.{side}.001")
        if leg_target:
            constraint = leg_target.constraints.new(type="IK")
            constraint.name = f"IK_foot_{side}_available"
            constraint.target = rig
            constraint.subtarget = f"CTRL_foot_ik.{side}"
            constraint.pole_target = rig
            constraint.pole_subtarget = f"CTRL_knee_pole.{side}"
            constraint.chain_count = 4
            constraint.influence = 0.0

    bpy.ops.object.mode_set(mode="OBJECT")
    clear_pose(rig)
    return rig


def connect_mesh(mesh: bpy.types.Object, rig: bpy.types.Object) -> None:
    mesh.parent = rig
    mesh.matrix_parent_inverse.identity()
    for modifier in list(mesh.modifiers):
        if modifier.type == "ARMATURE":
            mesh.modifiers.remove(modifier)
    modifier = mesh.modifiers.new("CleanDeformIKArmature", "ARMATURE")
    modifier.object = rig
    modifier.use_vertex_groups = True
    modifier.show_viewport = True
    modifier.show_render = True
    mesh.hide_viewport = False
    mesh.hide_render = False
    mesh.hide_set(False)


def pbone(rig: bpy.types.Object, name: str) -> bpy.types.PoseBone | None:
    return rig.pose.bones.get(name)


def key_bone(rig: bpy.types.Object, name: str, frame: int, loc=None, rot=None, scale=None) -> int:
    bone = pbone(rig, name)
    if not bone:
        return 0
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
    return 1


def set_pose_frame(rig: bpy.types.Object, spec: ActionSpec, frame: int, alpha: float) -> int:
    keyed = 0
    cycle = math.sin(alpha * math.tau)
    lift = max(0.0, math.sin(alpha * math.tau))
    opposite_lift = max(0.0, math.sin(alpha * math.tau + math.pi))
    stride = 0.20 if spec.mode.startswith("walk") or spec.mode in {"start_walk", "stop_walk"} else 0.32
    arm_swing = 0.18 if spec.mode.startswith("walk") or spec.mode in {"start_walk", "stop_walk"} else 0.30

    root_y = 0.0
    root_z = 0.0
    if spec.root_motion and spec.speed_uu > 0.0:
        root_y = -((spec.speed_uu / 100.0) * spec.duration) * alpha
    if spec.mode == "vault":
        root_y = -1.05 * alpha
        root_z = 0.50 * math.sin(math.pi * alpha)
    root_turn = math.radians(spec.turn_degrees) * alpha if spec.root_motion else 0.0
    keyed += key_bone(rig, "CTRL_root", frame, loc=(0.0, root_y, root_z), rot=(0.0, 0.0, root_turn))

    if spec.mode == "idle":
        breathe = math.sin(alpha * math.tau) * 0.012
        keyed += key_bone(rig, "DEF-spine.001", frame, rot=(breathe, 0.0, 0.0))
        keyed += key_bone(rig, "DEF-spine.003", frame, rot=(breathe * 0.6, 0.0, 0.0))
        keyed += key_bone(rig, "DEF-spine.006", frame, rot=(-breathe * 0.4, 0.0, 0.0))
        return keyed

    if spec.mode == "idle_staggered":
        breathe = math.sin(alpha * math.tau) * 0.012
        keyed += key_bone(rig, "DEF-spine.001", frame, rot=(breathe, 0.0, 0.0))
        keyed += key_bone(rig, "DEF-thigh.L", frame, rot=(0.025, 0.0, 0.0))
        keyed += key_bone(rig, "DEF-shin.L", frame, rot=(-0.020, 0.0, 0.0))
        return keyed

    if spec.mode == "turn":
        lean = 0.04 if spec.turn_degrees > 0.0 else -0.04
        turn_wave = math.sin(math.pi * alpha)
        keyed += key_bone(rig, "DEF-spine", frame, rot=(0.0, 0.0, lean * turn_wave))
        keyed += key_bone(rig, "DEF-spine.003", frame, rot=(0.0, 0.0, lean * 0.6 * turn_wave))
        keyed += key_bone(rig, "DEF-thigh.L", frame, rot=(0.04 * turn_wave, 0.0, 0.02))
        keyed += key_bone(rig, "DEF-thigh.R", frame, rot=(-0.03 * turn_wave, 0.0, -0.02))
        return keyed

    if spec.mode == "vault":
        tuck = math.sin(math.pi * alpha)
        reach = math.sin(math.pi * min(alpha * 1.25, 1.0))
        keyed += key_bone(rig, "DEF-spine.001", frame, rot=(0.22 * tuck, 0.0, 0.0))
        keyed += key_bone(rig, "DEF-spine.003", frame, rot=(0.16 * tuck, 0.0, 0.0))
        keyed += key_bone(rig, "DEF-upper_arm.L", frame, rot=(-0.55 * reach, 0.0, -0.24))
        keyed += key_bone(rig, "DEF-upper_arm.R", frame, rot=(-0.55 * reach, 0.0, 0.24))
        keyed += key_bone(rig, "DEF-forearm.L", frame, rot=(-0.25 * reach, 0.0, 0.0))
        keyed += key_bone(rig, "DEF-forearm.R", frame, rot=(-0.25 * reach, 0.0, 0.0))
        keyed += key_bone(rig, "DEF-thigh.L", frame, rot=(0.55 * tuck, 0.0, 0.0))
        keyed += key_bone(rig, "DEF-thigh.R", frame, rot=(0.48 * tuck, 0.0, 0.0))
        keyed += key_bone(rig, "DEF-shin.L", frame, rot=(-0.75 * tuck, 0.0, 0.0))
        keyed += key_bone(rig, "DEF-shin.R", frame, rot=(-0.65 * tuck, 0.0, 0.0))
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

    turn_lean = math.radians(spec.turn_degrees) * 0.16
    keyed += key_bone(rig, "DEF-spine", frame, rot=(0.020 * abs(cycle), 0.0, turn_lean + 0.025 * cycle))
    keyed += key_bone(rig, "DEF-spine.002", frame, rot=(-0.015 * abs(cycle), 0.0, -turn_lean * 0.5))
    keyed += key_bone(rig, "DEF-spine.004", frame, rot=(0.015 * abs(cycle), 0.0, -turn_lean * 0.35))
    keyed += key_bone(rig, "DEF-thigh.L", frame, rot=(stride * cycle, 0.0, 0.015))
    keyed += key_bone(rig, "DEF-shin.L", frame, rot=(-0.30 * lift, 0.0, 0.0))
    keyed += key_bone(rig, "DEF-foot.L", frame, rot=(0.10 * cycle - 0.06 * lift, 0.0, 0.0))
    keyed += key_bone(rig, "DEF-thigh.R", frame, rot=(-stride * cycle, 0.0, -0.015))
    keyed += key_bone(rig, "DEF-shin.R", frame, rot=(-0.30 * opposite_lift, 0.0, 0.0))
    keyed += key_bone(rig, "DEF-foot.R", frame, rot=(-0.10 * cycle - 0.06 * opposite_lift, 0.0, 0.0))
    keyed += key_bone(rig, "DEF-upper_arm.L", frame, rot=(-arm_swing * cycle, 0.0, -0.08))
    keyed += key_bone(rig, "DEF-forearm.L", frame, rot=(0.08 + 0.05 * abs(cycle), 0.0, 0.0))
    keyed += key_bone(rig, "DEF-upper_arm.R", frame, rot=(arm_swing * cycle, 0.0, 0.08))
    keyed += key_bone(rig, "DEF-forearm.R", frame, rot=(0.08 + 0.05 * abs(cycle), 0.0, 0.0))
    return keyed


def create_actions(rig: bpy.types.Object) -> list[str]:
    for action in list(bpy.data.actions):
        if action.name.startswith("AN_Player_"):
            bpy.data.actions.remove(action)

    rows: list[str] = []
    rig.animation_data_create()
    bpy.context.scene.render.fps = FPS
    for spec in ACTION_SPECS:
        clear_pose(rig)
        action = bpy.data.actions.new(spec.name)
        rig.animation_data.action = action
        frame_count = max(2, int(round(spec.duration * FPS)) + 1)
        keyed = 0
        for i in range(frame_count):
            frame = i + 1
            alpha = i / (frame_count - 1)
            bpy.context.scene.frame_set(frame)
            keyed += set_pose_frame(rig, spec, frame, alpha)
        action.use_fake_user = True
        action["speed_uu_per_s"] = spec.speed_uu
        action["duration_seconds"] = spec.duration
        action["root_motion_distance_cm"] = spec.speed_uu * spec.duration if spec.speed_uu > 0.0 else (105.0 if spec.mode == "vault" else 0.0)
        action["turn_degrees"] = spec.turn_degrees
        if spec.looping:
            action.use_cyclic = True
        rows.append(
            f"- {spec.name}: frames={frame_count} duration={spec.duration:.2f}s "
            f"speed={spec.speed_uu:.1f}UU/s root={action['root_motion_distance_cm']:.1f}cm "
            f"turn={spec.turn_degrees:.1f} keyed={keyed}"
        )

    rig.animation_data.action = None
    clear_pose(rig)
    bpy.context.scene.frame_set(1)
    return rows


def hide_old_rigify_objects(source: bpy.types.Object) -> int:
    hidden = 0
    for obj in bpy.data.objects:
        if obj == source or obj.name.startswith(("META_Player_Rigify", "RIG_Player_Rigify", "WGT-")):
            obj.hide_viewport = True
            obj.hide_render = True
            try:
                obj.hide_set(True)
            except RuntimeError:
                pass
            hidden += 1
    for collection in bpy.data.collections:
        if collection.name.startswith("WGTS_"):
            collection.hide_viewport = True
            collection.hide_render = True
    return hidden


def weighted_vertex_count(mesh: bpy.types.Object) -> int:
    return sum(1 for vertex in mesh.data.vertices if vertex.groups)


def main() -> None:
    src, report = args_after_separator()
    require_asset_write_permission(f"rebuild and save clean deform IK rig in {src}")
    backup_line = ensure_backup(src)
    bpy.ops.wm.open_mainfile(filepath=str(src), load_ui=False)
    bpy.context.scene.frame_set(1)

    mesh = bpy.data.objects.get(MESH_NAME)
    source = bpy.data.objects.get(SOURCE_RIG_NAME)
    if not mesh or mesh.type != "MESH":
        raise SystemExit(f"Missing mesh: {MESH_NAME}")
    if not source or source.type != "ARMATURE":
        raise SystemExit(f"Missing source fitted rig: {SOURCE_RIG_NAME}")

    clear_pose(source)
    raw_before = mesh_bounds(mesh, False)
    eval_before = mesh_bounds(mesh, True)

    clean = make_clean_rig(source)
    connect_mesh(mesh, clean)
    hidden_old = hide_old_rigify_objects(source)
    action_rows = create_actions(clean)
    bpy.context.view_layer.update()

    raw_after = mesh_bounds(mesh, False)
    eval_after = mesh_bounds(mesh, True)
    deform_count = sum(1 for bone in clean.data.bones if bone.use_deform)
    control_count = sum(1 for bone in clean.data.bones if not bone.use_deform)
    ik_constraints = [
        constraint.name
        for bone in clean.pose.bones
        for constraint in bone.constraints
        if constraint.type == "IK"
    ]

    lines = [
        "PLAYER_CLEAN_DEFORM_IK_RIG_REPORT",
        f"Blend: {src}",
        backup_line,
        f"Mesh: {mesh.name}",
        f"Active clean rig: {clean.name}",
        f"Old Rigify objects hidden: {hidden_old}",
        f"Mesh parent: {mesh.parent.name if mesh.parent else 'none'}",
        "Mesh modifier: "
        + ", ".join(
            f"{m.name}:{m.type}:{getattr(m, 'object', None).name if getattr(m, 'object', None) else 'none'}"
            for m in mesh.modifiers
        ),
        f"Vertex groups: {len(mesh.vertex_groups)}",
        f"Weighted vertices: {weighted_vertex_count(mesh)} / {len(mesh.data.vertices)}",
        f"Clean rig bones: {len(clean.data.bones)}",
        f"Clean deform bones: {deform_count}",
        f"Clean control bones: {control_count}",
        f"IK constraints available default influence 0: {len(ik_constraints)}",
        ", ".join(ik_constraints),
        f"Raw before: {fmt_bounds(*raw_before)}",
        f"Evaluated before: {fmt_bounds(*eval_before)}",
        f"Raw after: {fmt_bounds(*raw_after)}",
        f"Evaluated after: {fmt_bounds(*eval_after)}",
        "Speed calibration:",
        f"- Walk: {WALK_SPEED_UU:.1f} UU/s = {WALK_SPEED_UU / 100.0:.2f} m/s",
        f"- Run: {RUN_SPEED_UU:.1f} UU/s = {RUN_SPEED_UU / 100.0:.2f} m/s",
        "Actions:",
        *action_rows,
    ]
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(src))
    print("\n".join(lines))


main()
