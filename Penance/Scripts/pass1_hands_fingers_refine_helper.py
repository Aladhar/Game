from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TARGET_BLEND = PROJECT_ROOT / "Built" / "BlenderWork" / "PlayerModel_Refined_HighQuality_Working copy.blend"
REPORT_PATH = PROJECT_ROOT / "Saved" / "PlayerHandsPass1Report.txt"
SCREENSHOT_DIR = PROJECT_ROOT / "Saved" / "PlayerHandsPass1Screenshots"

ARMATURE_NAME = "SK_Player_Armature"
BODY_NAME = "PlayerRoughDraft_Mesh"
WORK_OBJECT_NAME = "WORK_HandsFingers_Pass1"
OLD_BAD_HAND_OBJECTS = {
    "Player_Refined_IndependentFingers",
    "Player_Refined_FINAL_HandsFingers",
}

FINGERS = ["thumb", "index", "middle", "ring", "pinky"]
PHALANGES = ["01", "02", "03"]


def args_after_separator() -> list[str]:
    if "--" not in sys.argv:
        return []
    return sys.argv[sys.argv.index("--") + 1 :]


def ensure_material(name: str, color: tuple[float, float, float, float], roughness: float) -> bpy.types.Material:
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = color
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = roughness
    return mat


def basis_from_axis(axis: Vector) -> tuple[Vector, Vector, Vector]:
    forward = axis.normalized()
    up_hint = Vector((0.0, 0.0, 1.0))
    if abs(forward.dot(up_hint)) > 0.92:
        up_hint = Vector((0.0, 1.0, 0.0))
    right = forward.cross(up_hint).normalized()
    up = right.cross(forward).normalized()
    return forward, right, up


def create_or_replace_work_object() -> bpy.types.Object:
    old = bpy.data.objects.get(WORK_OBJECT_NAME)
    if old:
        data = old.data
        bpy.data.objects.remove(old, do_unlink=True)
        if data and data.users == 0:
            bpy.data.meshes.remove(data)

    mesh = bpy.data.meshes.new(f"{WORK_OBJECT_NAME}_Mesh")
    obj = bpy.data.objects.new(WORK_OBJECT_NAME, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def hide_old_bad_hand_objects(report: list[str]) -> None:
    for name in sorted(OLD_BAD_HAND_OBJECTS):
        obj = bpy.data.objects.get(name)
        if obj:
            obj.hide_viewport = True
            obj.hide_render = True
            report.append(f"Hidden old placeholder hand object: {name}")


def add_ring(
    verts: list[tuple[float, float, float]],
    weights: list[dict[str, float]],
    center: Vector,
    tangent: Vector,
    radius_x: float,
    radius_y: float,
    sides: int,
    weight_map: dict[str, float],
) -> int:
    _, right, up = basis_from_axis(tangent)
    base = len(verts)
    for side in range(sides):
        angle = math.tau * side / sides
        co = center + right * math.cos(angle) * radius_x + up * math.sin(angle) * radius_y
        verts.append((co.x, co.y, co.z))
        weights.append(dict(weight_map))
    return base


def add_ring_faces(faces: list[tuple[int, ...]], ring_a: int, ring_b: int, sides: int) -> None:
    for side in range(sides):
        faces.append((ring_a + side, ring_a + ((side + 1) % sides), ring_b + ((side + 1) % sides), ring_b + side))


def add_cap(faces: list[tuple[int, ...]], ring: int, sides: int, reverse: bool = False) -> None:
    indices = list(range(ring, ring + sides))
    if reverse:
        indices.reverse()
    faces.append(tuple(indices))


def add_finger(
    verts: list[tuple[float, float, float]],
    faces: list[tuple[int, ...]],
    weights: list[dict[str, float]],
    arm: bpy.types.Object,
    suffix: str,
    finger: str,
    side_sign: float,
) -> tuple[Vector, Vector]:
    bones = [arm.data.bones.get(f"{finger}_{part}_{suffix}") for part in PHALANGES]
    if any(bone is None for bone in bones):
        raise RuntimeError(f"Missing finger bones for {finger}_{suffix}")

    first = bones[0]
    assert first is not None
    base = first.head_local
    points = [base]
    for bone in bones:
        assert bone is not None
        points.append(bone.tail_local)

    # Nudge the visible mesh inward so the finger grows out of the palm instead of hovering under it.
    palm_to_finger = (points[-1] - points[0]).normalized()
    side_pull = Vector((side_sign * 0.002, 0.002, 0.002))
    adjusted = [points[0] - palm_to_finger * 0.006 + side_pull]
    adjusted.extend(point + side_pull for point in points[1:])

    scale_by_finger = {"thumb": 0.90, "index": 0.82, "middle": 0.90, "ring": 0.80, "pinky": 0.64}
    base_radius = 0.0072 * scale_by_finger[finger]
    radii = [
        (base_radius * 1.18, base_radius * 0.92),
        (base_radius * 0.98, base_radius * 0.78),
        (base_radius * 0.78, base_radius * 0.62),
        (base_radius * 0.50, base_radius * 0.42),
    ]
    sides = 10

    ring_indices: list[int] = []
    for index, point in enumerate(adjusted):
        if index == 0:
            tangent = adjusted[1] - point
            weight_map = {f"{finger}_01_{suffix}": 0.82, f"hand_{suffix}": 0.18}
        elif index == len(adjusted) - 1:
            tangent = point - adjusted[index - 1]
            weight_map = {f"{finger}_03_{suffix}": 1.0}
        else:
            tangent = adjusted[min(index + 1, len(adjusted) - 1)] - adjusted[max(index - 1, 0)]
            bone_name = f"{finger}_{min(index, 3):02d}_{suffix}"
            prev_name = f"{finger}_{max(index - 1, 1):02d}_{suffix}"
            weight_map = {bone_name: 0.75, prev_name: 0.25}
        ring_indices.append(add_ring(verts, weights, point, tangent, radii[index][0], radii[index][1], sides, weight_map))

    add_cap(faces, ring_indices[0], sides, reverse=True)
    for a, b in zip(ring_indices, ring_indices[1:]):
        add_ring_faces(faces, a, b, sides)
    add_cap(faces, ring_indices[-1], sides)

    return adjusted[0], adjusted[-1]


def add_palm(
    verts: list[tuple[float, float, float]],
    faces: list[tuple[int, ...]],
    weights: list[dict[str, float]],
    arm: bpy.types.Object,
    suffix: str,
    side_sign: float,
) -> tuple[list[int], Vector]:
    hand = arm.data.bones.get(f"hand_{suffix}")
    lowerarm = arm.data.bones.get(f"lowerarm_{suffix}")
    if not hand or not lowerarm:
        raise RuntimeError(f"Missing hand/lowerarm bones for side {suffix}")

    axis = (hand.tail_local - hand.head_local).normalized()
    center = hand.head_local + axis * 0.030 + Vector((side_sign * 0.004, -0.0015, -0.001))
    _, right, up = basis_from_axis(axis)

    x = right * 0.034
    y = up * 0.022
    z = axis * 0.030
    palm_points = [
        center - x - y - z * 0.60,
        center + x - y - z * 0.60,
        center + x + y - z * 0.40,
        center - x + y - z * 0.40,
        center - x * 0.85 - y * 0.85 + z,
        center + x * 0.85 - y * 0.85 + z,
        center + x * 0.78 + y * 0.88 + z,
        center - x * 0.78 + y * 0.88 + z,
    ]
    base = len(verts)
    for point in palm_points:
        verts.append((point.x, point.y, point.z))
        weights.append({f"hand_{suffix}": 0.88, f"lowerarm_{suffix}": 0.12})

    faces.extend(
        [
            (base, base + 1, base + 2, base + 3),
            (base + 4, base + 7, base + 6, base + 5),
            (base, base + 4, base + 5, base + 1),
            (base + 1, base + 5, base + 6, base + 2),
            (base + 2, base + 6, base + 7, base + 3),
            (base + 3, base + 7, base + 4, base),
        ]
    )
    return list(range(base, base + 8)), center


def add_webbing(
    verts: list[tuple[float, float, float]],
    faces: list[tuple[int, ...]],
    weights: list[dict[str, float]],
    suffix: str,
    finger_bases: dict[str, Vector],
) -> None:
    pairs = [("index", "middle"), ("middle", "ring"), ("ring", "pinky")]
    for left, right in pairs:
        a = finger_bases[left]
        b = finger_bases[right]
        mid = (a + b) * 0.5 + Vector((0.0, 0.004, 0.002))
        base = len(verts)
        verts.extend([(a.x, a.y, a.z), (b.x, b.y, b.z), (mid.x, mid.y, mid.z)])
        weights.extend(
            [
                {f"{left}_01_{suffix}": 0.65, f"hand_{suffix}": 0.35},
                {f"{right}_01_{suffix}": 0.65, f"hand_{suffix}": 0.35},
                {f"hand_{suffix}": 0.55, f"{left}_01_{suffix}": 0.225, f"{right}_01_{suffix}": 0.225},
            ]
        )
        faces.append((base, base + 1, base + 2))


def assign_weights(obj: bpy.types.Object, weights: list[dict[str, float]]) -> None:
    groups: dict[str, bpy.types.VertexGroup] = {}
    for weight_map in weights:
        for group_name in weight_map:
            if group_name not in groups:
                groups[group_name] = obj.vertex_groups.new(name=group_name)
    for vertex_index, weight_map in enumerate(weights):
        total = sum(weight_map.values()) or 1.0
        for group_name, value in weight_map.items():
            groups[group_name].add([vertex_index], value / total, "REPLACE")


def build_hands_mesh(arm: bpy.types.Object, report: list[str]) -> bpy.types.Object:
    obj = create_or_replace_work_object()
    verts: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    weights: list[dict[str, float]] = []

    for suffix, side_sign in (("l", -1.0), ("r", 1.0)):
        add_palm(verts, faces, weights, arm, suffix, side_sign)
        finger_bases: dict[str, Vector] = {}
        for finger in FINGERS:
            base, _tip = add_finger(verts, faces, weights, arm, suffix, finger, side_sign)
            finger_bases[finger] = base
        add_webbing(verts, faces, weights, suffix, finger_bases)

    obj.data.from_pydata(verts, [], faces)
    obj.data.update()
    obj.data.materials.append(ensure_material("MQ_Player_Hands_Pass1_Skin", (0.70, 0.50, 0.40, 1.0), 0.72))
    assign_weights(obj, weights)

    arm_mod = obj.modifiers.new("Armature_Current_Player", "ARMATURE")
    arm_mod.object = arm
    obj.modifiers.new("Live_Smoothing_WeightedNormals", "WEIGHTED_NORMAL")
    obj["Pass"] = "Pass 1 hands/fingers visual replacement; original skinned mesh untouched."
    report.append(f"Created {WORK_OBJECT_NAME}: verts={len(verts)} faces={len(faces)} vertex_groups={len(obj.vertex_groups)}")
    return obj


def create_finger_bend_action(arm: bpy.types.Object, report: list[str]) -> None:
    existing = bpy.data.actions.get("AN_Player_HandsPass1_FingerBend_Test")
    if existing:
        bpy.data.actions.remove(existing)
    if not arm.animation_data:
        arm.animation_data_create()
    prior = arm.animation_data.action
    action = bpy.data.actions.new("AN_Player_HandsPass1_FingerBend_Test")
    action.use_fake_user = True
    arm.animation_data.action = action
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")
    keyed = 0
    for pose_bone in arm.pose.bones:
        if pose_bone.name.startswith(tuple(f"{finger}_" for finger in FINGERS)):
            pose_bone.rotation_mode = "XYZ"
            pose_bone.rotation_euler = (0.0, 0.0, 0.0)
            pose_bone.keyframe_insert(data_path="rotation_euler", frame=1)
            bend = math.radians(18 if "_01_" in pose_bone.name else 32)
            if pose_bone.name.endswith("_r"):
                bend *= -1.0
            pose_bone.rotation_euler[0] = bend
            pose_bone.keyframe_insert(data_path="rotation_euler", frame=18)
            pose_bone.rotation_euler = (0.0, 0.0, 0.0)
            pose_bone.keyframe_insert(data_path="rotation_euler", frame=36)
            keyed += 1
    bpy.ops.object.mode_set(mode="OBJECT")
    arm.animation_data.action = prior
    report.append(f"Pose stress helper action: AN_Player_HandsPass1_FingerBend_Test keyed_bones={keyed}")


def object_bounds(obj: bpy.types.Object) -> tuple[Vector, Vector]:
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return (
        Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners))),
        Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners))),
    )


def capture_screenshots(output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.render.resolution_x = 1400
    scene.render.resolution_y = 1800
    scene.world.color = (0.03, 0.03, 0.035)

    cam_data = bpy.data.cameras.new("TEMP_HandsPass1_Camera")
    cam = bpy.data.objects.new("TEMP_HandsPass1_Camera", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam_data.type = "ORTHO"

    light_data = bpy.data.lights.new("TEMP_HandsPass1_Light", "AREA")
    light = bpy.data.objects.new("TEMP_HandsPass1_Light", light_data)
    scene.collection.objects.link(light)
    light.location = (0.0, -2.3, 2.1)
    light_data.energy = 420.0
    light_data.size = 1.8

    def point(location: tuple[float, float, float], target: Vector, scale: float) -> None:
        cam.location = location
        direction = target - cam.location
        cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        cam.data.ortho_scale = scale

    shots = [
        ("front_full", (0.0, -2.25, 0.50), Vector((0.0, 0.0, 0.50)), 1.18),
        ("three_quarter_full", (1.35, -2.10, 0.53), Vector((0.0, 0.0, 0.50)), 1.18),
        ("hands_front_closeup", (0.0, -0.95, 0.455), Vector((0.0, -0.03, 0.455)), 0.31),
        ("left_hand_closeup", (-0.17, -0.70, 0.465), Vector((-0.17, -0.025, 0.465)), 0.18),
        ("right_hand_closeup", (0.17, -0.70, 0.465), Vector((0.17, -0.025, 0.465)), 0.18),
    ]
    paths: list[Path] = []
    for name, location, target, scale in shots:
        point(location, target, scale)
        path = output_dir / f"{name}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.opengl(write_still=True, view_context=False)
        paths.append(path)
    return paths


def main() -> None:
    args = args_after_separator()
    output_blend = Path(args[0]).expanduser().resolve() if args else TARGET_BLEND
    screenshot_dir = Path(args[1]).expanduser().resolve() if len(args) > 1 else PROJECT_ROOT / "Saved" / "PlayerHandsPass1Screenshots"
    report: list[str] = [
        "PLAYER_HANDS_PASS1_REPORT",
        f"Target: {output_blend}",
    ]

    for action in bpy.data.actions:
        action.use_fake_user = True

    arm = bpy.data.objects.get(ARMATURE_NAME)
    body = bpy.data.objects.get(BODY_NAME)
    if not arm or arm.type != "ARMATURE":
        raise RuntimeError(f"Missing armature {ARMATURE_NAME}")
    if not body or body.type != "MESH":
        raise RuntimeError(f"Missing body mesh {BODY_NAME}")

    hide_old_bad_hand_objects(report)
    hands = build_hands_mesh(arm, report)
    create_finger_bend_action(arm, report)

    body_min, body_max = object_bounds(body)
    hands_min, hands_max = object_bounds(hands)
    report.append(f"Body bounds: min={tuple(round(v, 4) for v in body_min)} max={tuple(round(v, 4) for v in body_max)}")
    report.append(f"Hands bounds: min={tuple(round(v, 4) for v in hands_min)} max={tuple(round(v, 4) for v in hands_max)}")
    report.append("Destructive operations: none on original skinned mesh")
    report.append("Armature changes: none; existing finger bones reused")
    report.append("Modifiers added: Armature_Current_Player, Live_Smoothing_WeightedNormals on WORK_HandsFingers_Pass1")

    screenshot_paths = capture_screenshots(screenshot_dir)
    report.append("Screenshots:")
    report.extend(str(path) for path in screenshot_paths)

    bpy.ops.wm.save_as_mainfile(filepath=str(output_blend))
    REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))
    bpy.ops.wm.quit_blender()


if __name__ == "__main__":
    main()
