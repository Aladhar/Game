"""Rebuild Player.blend with an anatomical game deform rig for Mesh_0.

This is Blender-only. The goal is not merely "no neutral explosion"; the active
armature should place deform joints where a humanoid model should bend, and the
mesh should be weighted to those bones so animation deformation is intentional.
"""

from __future__ import annotations

import math
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

import bpy
from mathutils import Vector


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BLEND = PROJECT_ROOT / "Content" / "Player" / "Player.blend"
DEFAULT_REPORT = PROJECT_ROOT / "Saved" / "PlayerAnatomicalGameRigReport.txt"
BACKUP_PATH = PROJECT_ROOT / "Content" / "Player" / "BlenderSource" / "Backups" / "Player_before_anatomical_game_rig.blend"

MESH_NAME = "Mesh_0"
SOURCE_FINGER_RIG_NAME = "RIG_Player_Rigify_Humanoid_IK"
RIG_NAME = "ARM_Player_Anatomical_Game_Rig"
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
    looping: bool = True


ACTION_SPECS = [
    ActionSpec("AN_Player_Idle_FeetTogether", 2.0, 0.0, "idle"),
    ActionSpec("AN_Player_Idle_Staggered", 2.0, 0.0, "idle_staggered"),
    ActionSpec("AN_Player_Walk_Forward_Loop", 1.0, WALK_SPEED_UU, "walk"),
    ActionSpec("AN_Player_Walk_Backward_Loop", 1.0, WALK_SPEED_UU, "walk_backward"),
    ActionSpec("AN_Player_TurnInPlace_Left", 0.75, 0.0, "turn_left", 90.0, False),
    ActionSpec("AN_Player_TurnInPlace_Right", 0.75, 0.0, "turn_right", -90.0, False),
    ActionSpec("AN_Player_Walk_Turn_Left_Loop", 1.0, WALK_SPEED_UU, "walk", 35.0),
    ActionSpec("AN_Player_Walk_Turn_Right_Loop", 1.0, WALK_SPEED_UU, "walk", -35.0),
    ActionSpec("AN_Player_Run_Forward_Loop", 0.8, RUN_SPEED_UU, "run"),
    ActionSpec("AN_Player_Run_Turn_Left_Loop", 0.8, RUN_SPEED_UU, "run", 38.0),
    ActionSpec("AN_Player_Run_Turn_Right_Loop", 0.8, RUN_SPEED_UU, "run", -38.0),
    ActionSpec("AN_Player_Vault_100cm", 1.15, 0.0, "vault", 0.0, False),
    ActionSpec("AN_Player_StartWalk_Forward", 0.45, WALK_SPEED_UU, "start_walk", 0.0, False),
    ActionSpec("AN_Player_StopWalk_Forward", 0.45, WALK_SPEED_UU, "stop_walk", 0.0, False),
]


def args_after_separator() -> tuple[Path, Path]:
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
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


def remove_existing_rig() -> None:
    obj = bpy.data.objects.get(RIG_NAME)
    if obj:
        data = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        if data and data.users == 0:
            bpy.data.armatures.remove(data)


def add_bone(
    eb: bpy.types.ArmatureEditBones,
    name: str,
    head: tuple[float, float, float] | Vector,
    tail: tuple[float, float, float] | Vector,
    parent: str | None = None,
    deform: bool = True,
):
    bone = eb.new(name)
    bone.head = Vector(head)
    bone.tail = Vector(tail)
    if (bone.tail - bone.head).length < 0.002:
        bone.tail = bone.head + Vector((0.0, 0.0, 0.02))
    bone.use_deform = deform
    if parent and parent in eb:
        bone.parent = eb[parent]
        bone.use_connect = False
    return bone


def copy_finger_bones(eb: bpy.types.ArmatureEditBones, source: bpy.types.Object | None, side: str) -> int:
    if not source:
        return 0
    parent = f"hand.{side}"
    copied = 0
    prefixes = ["DEF-thumb", "DEF-f_index", "DEF-f_middle", "DEF-f_ring", "DEF-f_pinky"]
    for src_bone in source.data.bones:
        if not src_bone.use_deform or not src_bone.name.endswith(f".{side}"):
            continue
        if not any(src_bone.name.startswith(prefix) for prefix in prefixes):
            continue
        bone = add_bone(eb, src_bone.name, src_bone.head_local, src_bone.tail_local, parent, True)
        src_parent = src_bone.parent
        if src_parent and src_parent.name in eb:
            bone.parent = eb[src_parent.name]
        copied += 1
    return copied


def create_anatomical_rig(source_finger_rig: bpy.types.Object | None) -> tuple[bpy.types.Object, int]:
    remove_existing_rig()
    arm_data = bpy.data.armatures.new(f"{RIG_NAME}_Data")
    rig = bpy.data.objects.new(RIG_NAME, arm_data)
    bpy.context.collection.objects.link(rig)
    rig.show_in_front = True
    arm_data.display_type = "BBONE"

    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm_data.edit_bones

    # Root is a horizontal control so keyed local Y translation moves the whole
    # rig across the ground plane instead of along the character height.
    add_bone(eb, "root", (0.0, 0.0, 0.0), (0.0, -0.25, 0.0), deform=False)
    add_bone(eb, "pelvis", (0.0, 0.064, 0.82), (0.0, 0.064, 0.92), "root")
    add_bone(eb, "spine_01", (0.0, 0.066, 0.92), (0.0, 0.073, 1.07), "pelvis")
    add_bone(eb, "spine_02", (0.0, 0.073, 1.07), (0.0, 0.076, 1.22), "spine_01")
    add_bone(eb, "chest", (0.0, 0.076, 1.22), (0.0, 0.074, 1.36), "spine_02")
    add_bone(eb, "neck", (0.0, 0.070, 1.36), (0.0, 0.060, 1.49), "chest")
    add_bone(eb, "head", (0.0, 0.060, 1.49), (0.0, 0.045, 1.63), "neck")

    for side, sign in (("L", 1.0), ("R", -1.0)):
        add_bone(eb, f"clavicle.{side}", (0.030 * sign, 0.074, 1.335), (0.135 * sign, 0.084, 1.318), "chest")
        add_bone(eb, f"upper_arm.{side}", (0.135 * sign, 0.084, 1.318), (0.230 * sign, 0.080, 1.120), f"clavicle.{side}")
        add_bone(eb, f"upper_arm_twist.{side}", (0.230 * sign, 0.080, 1.120), (0.300 * sign, 0.080, 0.980), f"upper_arm.{side}")
        add_bone(eb, f"forearm.{side}", (0.300 * sign, 0.080, 0.980), (0.390 * sign, 0.095, 0.875), f"upper_arm_twist.{side}")
        add_bone(eb, f"forearm_twist.{side}", (0.390 * sign, 0.095, 0.875), (0.470 * sign, 0.112, 0.910), f"forearm.{side}")
        add_bone(eb, f"hand.{side}", (0.470 * sign, 0.112, 0.910), (0.545 * sign, 0.128, 0.995), f"forearm_twist.{side}")

        add_bone(eb, f"thigh.{side}", (0.075 * sign, 0.065, 0.86), (0.082 * sign, 0.050, 0.58), "pelvis")
        add_bone(eb, f"thigh_twist.{side}", (0.082 * sign, 0.050, 0.58), (0.086 * sign, 0.040, 0.39), f"thigh.{side}")
        add_bone(eb, f"calf.{side}", (0.086 * sign, 0.040, 0.39), (0.090 * sign, 0.060, 0.18), f"thigh_twist.{side}")
        add_bone(eb, f"calf_twist.{side}", (0.090 * sign, 0.060, 0.18), (0.095 * sign, 0.070, 0.075), f"calf.{side}")
        add_bone(eb, f"foot.{side}", (0.095 * sign, 0.070, 0.075), (0.108 * sign, -0.010, 0.030), f"calf_twist.{side}")
        add_bone(eb, f"toe.{side}", (0.108 * sign, -0.010, 0.030), (0.135 * sign, -0.085, 0.030), f"foot.{side}")

        add_bone(eb, f"CTRL_hand_ik.{side}", (0.545 * sign, -0.020, 0.995), (0.545 * sign, -0.020, 1.140), "root", False)
        add_bone(eb, f"CTRL_elbow_pole.{side}", (0.300 * sign, -0.280, 1.000), (0.300 * sign, -0.280, 1.120), "root", False)
        add_bone(eb, f"CTRL_foot_ik.{side}", (0.110 * sign, -0.085, 0.030), (0.110 * sign, -0.085, 0.180), "root", False)
        add_bone(eb, f"CTRL_knee_pole.{side}", (0.088 * sign, -0.330, 0.390), (0.088 * sign, -0.330, 0.520), "root", False)

    copied_fingers = copy_finger_bones(eb, source_finger_rig, "L") + copy_finger_bones(eb, source_finger_rig, "R")

    bpy.ops.object.mode_set(mode="POSE")
    for side in ("L", "R"):
        for target_name, ik_name, pole_name, chain_count in [
            (f"forearm_twist.{side}", f"CTRL_hand_ik.{side}", f"CTRL_elbow_pole.{side}", 4),
            (f"calf_twist.{side}", f"CTRL_foot_ik.{side}", f"CTRL_knee_pole.{side}", 4),
        ]:
            target = rig.pose.bones.get(target_name)
            if not target:
                continue
            constraint = target.constraints.new(type="IK")
            constraint.name = f"IK_available_{target_name}"
            constraint.target = rig
            constraint.subtarget = ik_name
            constraint.pole_target = rig
            constraint.pole_subtarget = pole_name
            constraint.chain_count = chain_count
            constraint.influence = 0.0

    bpy.ops.object.mode_set(mode="OBJECT")
    clear_pose(rig)
    return rig, copied_fingers


def clear_pose(rig: bpy.types.Object) -> None:
    if rig.animation_data:
        rig.animation_data.action = None
    for bone in rig.pose.bones:
        bone.rotation_mode = "XYZ"
        bone.location = (0.0, 0.0, 0.0)
        bone.rotation_euler = (0.0, 0.0, 0.0)
        bone.scale = (1.0, 1.0, 1.0)


def distance_to_segment(point: Vector, a: Vector, b: Vector) -> float:
    axis = b - a
    length_sq = axis.length_squared
    if length_sq <= 1e-8:
        return (point - a).length
    t = max(0.0, min(1.0, (point - a).dot(axis) / length_sq))
    return (point - (a + axis * t)).length


def deform_segments(rig: bpy.types.Object) -> list[tuple[str, Vector, Vector]]:
    result = []
    for bone in rig.data.bones:
        if not bone.use_deform:
            continue
        result.append((bone.name, rig.matrix_world @ bone.head_local, rig.matrix_world @ bone.tail_local))
    return result


def side_from_vertex(point: Vector) -> str | None:
    if point.x > 0.012:
        return "L"
    if point.x < -0.012:
        return "R"
    return None


def is_bone_candidate(name: str, point: Vector) -> bool:
    side = side_from_vertex(point)
    if name.endswith(".L") and side == "R":
        return False
    if name.endswith(".R") and side == "L":
        return False
    if name.startswith(("upper_arm", "forearm", "hand", "clavicle", "DEF-thumb", "DEF-f_")):
        return point.z >= 0.72 and abs(point.x) >= 0.07
    if name.startswith(("thigh", "calf", "foot", "toe")):
        return point.z <= 0.92 and abs(point.x) <= 0.28
    if name in {"pelvis", "spine_01", "spine_02", "chest", "neck", "head"}:
        return abs(point.x) <= 0.30 or point.z >= 1.25
    return True


def replace_weights(mesh: bpy.types.Object, rig: bpy.types.Object) -> tuple[int, int]:
    for modifier in list(mesh.modifiers):
        if modifier.type == "ARMATURE":
            mesh.modifiers.remove(modifier)
    for group in list(mesh.vertex_groups):
        mesh.vertex_groups.remove(group)

    groups = {bone.name: mesh.vertex_groups.new(name=bone.name) for bone in rig.data.bones if bone.use_deform}
    segments = deform_segments(rig)
    weighted = 0
    max_influences = 0

    for vertex in mesh.data.vertices:
        point = mesh.matrix_world @ vertex.co
        distances = [
            (name, distance_to_segment(point, head, tail))
            for name, head, tail in segments
            if is_bone_candidate(name, point)
        ]
        if not distances:
            distances = [(name, distance_to_segment(point, head, tail)) for name, head, tail in segments]
        nearest = sorted(distances, key=lambda item: item[1])[:4]
        weighted_values = [(name, 1.0 / max(distance, 0.012) ** 3) for name, distance in nearest]
        total = sum(weight for _name, weight in weighted_values)
        influences = 0
        for name, weight in weighted_values:
            normalized = weight / total
            if normalized < 0.015:
                continue
            groups[name].add([vertex.index], normalized, "ADD")
            influences += 1
        weighted += 1 if influences else 0
        max_influences = max(max_influences, influences)

    mesh.parent = rig
    mesh.matrix_parent_inverse.identity()
    modifier = mesh.modifiers.new("AnatomicalGameArmature", "ARMATURE")
    modifier.object = rig
    modifier.use_vertex_groups = True
    modifier.show_viewport = True
    modifier.show_render = True
    return weighted, max_influences


def hide_old_rigs(active: bpy.types.Object) -> int:
    hidden = 0
    for obj in bpy.data.objects:
        if obj == active or obj.type != "ARMATURE":
            continue
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


def key_bone(rig: bpy.types.Object, name: str, frame: int, loc=None, rot=None, scale=None) -> int:
    bone = rig.pose.bones.get(name)
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
    stride = 0.18 if spec.mode.startswith("walk") or spec.mode in {"start_walk", "stop_walk"} else 0.28
    arm_swing = 0.16 if spec.mode.startswith("walk") or spec.mode in {"start_walk", "stop_walk"} else 0.26

    root_y = 0.0
    root_z = 0.0
    if spec.speed_uu > 0.0:
        root_y = -((spec.speed_uu / 100.0) * spec.duration) * alpha
    if spec.mode == "vault":
        root_y = -1.05 * alpha
        root_z = 0.42 * math.sin(math.pi * alpha)
    keyed += key_bone(rig, "root", frame, loc=(0.0, root_y, root_z), rot=(0.0, 0.0, math.radians(spec.turn_degrees) * alpha))

    if spec.mode == "idle":
        breathe = math.sin(alpha * math.tau) * 0.010
        keyed += key_bone(rig, "spine_01", frame, rot=(breathe, 0.0, 0.0))
        keyed += key_bone(rig, "chest", frame, rot=(breathe * 0.5, 0.0, 0.0))
        return keyed
    if spec.mode == "idle_staggered":
        breathe = math.sin(alpha * math.tau) * 0.010
        keyed += key_bone(rig, "spine_01", frame, rot=(breathe, 0.0, 0.0))
        keyed += key_bone(rig, "thigh.L", frame, rot=(0.020, 0.0, 0.0))
        keyed += key_bone(rig, "calf.L", frame, rot=(-0.018, 0.0, 0.0))
        return keyed
    if spec.mode.startswith("turn"):
        wave = math.sin(math.pi * alpha)
        lean = 0.035 if spec.turn_degrees > 0.0 else -0.035
        keyed += key_bone(rig, "pelvis", frame, rot=(0.0, 0.0, lean * wave))
        keyed += key_bone(rig, "chest", frame, rot=(0.0, 0.0, lean * 0.5 * wave))
        keyed += key_bone(rig, "thigh.L", frame, rot=(0.035 * wave, 0.0, 0.012))
        keyed += key_bone(rig, "thigh.R", frame, rot=(-0.028 * wave, 0.0, -0.012))
        return keyed
    if spec.mode == "vault":
        tuck = math.sin(math.pi * alpha)
        reach = math.sin(math.pi * min(alpha * 1.2, 1.0))
        keyed += key_bone(rig, "spine_01", frame, rot=(0.18 * tuck, 0.0, 0.0))
        keyed += key_bone(rig, "chest", frame, rot=(0.12 * tuck, 0.0, 0.0))
        keyed += key_bone(rig, "upper_arm.L", frame, rot=(-0.45 * reach, 0.0, -0.18))
        keyed += key_bone(rig, "upper_arm.R", frame, rot=(-0.45 * reach, 0.0, 0.18))
        keyed += key_bone(rig, "forearm.L", frame, rot=(-0.18 * reach, 0.0, 0.0))
        keyed += key_bone(rig, "forearm.R", frame, rot=(-0.18 * reach, 0.0, 0.0))
        keyed += key_bone(rig, "thigh.L", frame, rot=(0.48 * tuck, 0.0, 0.0))
        keyed += key_bone(rig, "thigh.R", frame, rot=(0.42 * tuck, 0.0, 0.0))
        keyed += key_bone(rig, "calf.L", frame, rot=(-0.62 * tuck, 0.0, 0.0))
        keyed += key_bone(rig, "calf.R", frame, rot=(-0.56 * tuck, 0.0, 0.0))
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

    lean = math.radians(spec.turn_degrees) * 0.12
    keyed += key_bone(rig, "pelvis", frame, rot=(0.015 * abs(cycle), 0.0, lean + 0.018 * cycle))
    keyed += key_bone(rig, "spine_02", frame, rot=(-0.010 * abs(cycle), 0.0, -lean * 0.5))
    keyed += key_bone(rig, "chest", frame, rot=(0.010 * abs(cycle), 0.0, -lean * 0.35))
    keyed += key_bone(rig, "thigh.L", frame, rot=(stride * cycle, 0.0, 0.010))
    keyed += key_bone(rig, "calf.L", frame, rot=(-0.24 * lift, 0.0, 0.0))
    keyed += key_bone(rig, "foot.L", frame, rot=(0.08 * cycle - 0.04 * lift, 0.0, 0.0))
    keyed += key_bone(rig, "thigh.R", frame, rot=(-stride * cycle, 0.0, -0.010))
    keyed += key_bone(rig, "calf.R", frame, rot=(-0.24 * opposite_lift, 0.0, 0.0))
    keyed += key_bone(rig, "foot.R", frame, rot=(-0.08 * cycle - 0.04 * opposite_lift, 0.0, 0.0))
    keyed += key_bone(rig, "upper_arm.L", frame, rot=(-arm_swing * cycle, 0.0, -0.055))
    keyed += key_bone(rig, "forearm.L", frame, rot=(0.06 + 0.04 * abs(cycle), 0.0, 0.0))
    keyed += key_bone(rig, "upper_arm.R", frame, rot=(arm_swing * cycle, 0.0, 0.055))
    keyed += key_bone(rig, "forearm.R", frame, rot=(0.06 + 0.04 * abs(cycle), 0.0, 0.0))
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
        frames = max(2, int(round(spec.duration * FPS)) + 1)
        keyed = 0
        for i in range(frames):
            frame = i + 1
            alpha = i / (frames - 1)
            bpy.context.scene.frame_set(frame)
            keyed += set_pose_frame(rig, spec, frame, alpha)
        action.use_fake_user = True
        action["speed_uu_per_s"] = spec.speed_uu
        action["duration_seconds"] = spec.duration
        action["root_motion_distance_cm"] = spec.speed_uu * spec.duration if spec.speed_uu else (105.0 if spec.mode == "vault" else 0.0)
        action["turn_degrees"] = spec.turn_degrees
        if spec.looping:
            action.use_cyclic = True
        rows.append(f"- {spec.name}: frames={frames} speed={spec.speed_uu:.1f}UU/s root={action['root_motion_distance_cm']:.1f}cm turn={spec.turn_degrees:.1f} keyed={keyed}")
    rig.animation_data.action = None
    clear_pose(rig)
    bpy.context.scene.frame_set(1)
    return rows


def bone_line(rig: bpy.types.Object, name: str) -> str:
    bone = rig.data.bones.get(name)
    if not bone:
        return f"- {name}: missing"
    head = rig.matrix_world @ bone.head_local
    tail = rig.matrix_world @ bone.tail_local
    return f"- {name}: head=({head.x:.4f},{head.y:.4f},{head.z:.4f}) tail=({tail.x:.4f},{tail.y:.4f},{tail.z:.4f}) length={(tail - head).length:.4f}"


def main() -> None:
    src, report = args_after_separator()
    backup_line = ensure_backup(src)
    bpy.ops.wm.open_mainfile(filepath=str(src), load_ui=False)
    bpy.context.scene.frame_set(1)

    mesh = bpy.data.objects.get(MESH_NAME)
    if not mesh or mesh.type != "MESH":
        raise SystemExit(f"Missing mesh: {MESH_NAME}")
    source_finger_rig = bpy.data.objects.get(SOURCE_FINGER_RIG_NAME)

    raw_before = mesh_bounds(mesh, False)
    eval_before = mesh_bounds(mesh, True)
    rig, copied_fingers = create_anatomical_rig(source_finger_rig if source_finger_rig and source_finger_rig.type == "ARMATURE" else None)
    weighted, max_influences = replace_weights(mesh, rig)
    hidden_old = hide_old_rigs(rig)
    mesh.hide_viewport = False
    mesh.hide_render = False
    mesh.hide_set(False)
    rig.hide_viewport = False
    rig.hide_render = False
    rig.hide_set(False)
    action_rows = create_actions(rig)
    bpy.context.view_layer.update()

    raw_after = mesh_bounds(mesh, False)
    eval_after = mesh_bounds(mesh, True)
    deform_count = sum(1 for bone in rig.data.bones if bone.use_deform)
    control_count = sum(1 for bone in rig.data.bones if not bone.use_deform)
    ik_count = sum(1 for bone in rig.pose.bones for c in bone.constraints if c.type == "IK")
    key_bones = [
        "pelvis", "spine_01", "spine_02", "chest", "neck", "head",
        "clavicle.L", "upper_arm.L", "upper_arm_twist.L", "forearm.L", "forearm_twist.L", "hand.L",
        "clavicle.R", "upper_arm.R", "upper_arm_twist.R", "forearm.R", "forearm_twist.R", "hand.R",
        "thigh.L", "thigh_twist.L", "calf.L", "calf_twist.L", "foot.L", "toe.L",
        "thigh.R", "thigh_twist.R", "calf.R", "calf_twist.R", "foot.R", "toe.R",
    ]

    lines = [
        "PLAYER_ANATOMICAL_GAME_RIG_REPORT",
        f"Blend: {src}",
        backup_line,
        f"Active rig: {rig.name}",
        f"Mesh: {mesh.name}",
        f"Mesh parent: {mesh.parent.name if mesh.parent else 'none'}",
        f"Armature modifier: {next((m.object.name for m in mesh.modifiers if m.type == 'ARMATURE' and m.object), 'none')}",
        f"Old armatures hidden: {hidden_old}",
        f"Deform bones: {deform_count}",
        f"Control bones: {control_count}",
        f"Copied finger deform bones from fitted source: {copied_fingers}",
        f"IK constraints available default influence 0: {ik_count}",
        f"Weighted vertices: {weighted} / {len(mesh.data.vertices)}",
        f"Max influences per generated vertex: {max_influences}",
        f"Raw before: {fmt_bounds(*raw_before)}",
        f"Evaluated before: {fmt_bounds(*eval_before)}",
        f"Raw after: {fmt_bounds(*raw_after)}",
        f"Evaluated after: {fmt_bounds(*eval_after)}",
        "Key anatomical bone placement:",
        *[bone_line(rig, name) for name in key_bones],
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
