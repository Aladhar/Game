from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = PROJECT_ROOT / "Saved" / "PlayerHandsPass1OverlayReport.txt"
ARMATURE_NAME = "SK_Player_Armature"
BODY_NAME = "PlayerRoughDraft_Mesh"
WORK_OBJECT_NAME = "WORK_HandsFingers_Pass1C_Overlay"

HIDE_FAILED_HANDS = {
    "Player_Refined_IndependentFingers",
    "Player_Refined_FINAL_HandsFingers",
    "WORK_HandsFingers_Pass1",
    "WORK_HandsFingers_Pass1B_Compact",
}

FINGERS = ["thumb", "index", "middle", "ring", "pinky"]


def args_after_separator() -> list[str]:
    if "--" not in sys.argv:
        return []
    return sys.argv[sys.argv.index("--") + 1 :]


def material() -> bpy.types.Material:
    mat = bpy.data.materials.get("MQ_Player_Hands_Pass1C_PlayerGrey") or bpy.data.materials.new("MQ_Player_Hands_Pass1C_PlayerGrey")
    mat.use_nodes = True
    mat.diffuse_color = (0.70, 0.69, 0.65, 1.0)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.70, 0.69, 0.65, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.82
    return mat


def basis(axis: Vector) -> tuple[Vector, Vector, Vector]:
    fwd = axis.normalized()
    up_hint = Vector((0.0, 0.0, 1.0))
    if abs(fwd.dot(up_hint)) > 0.9:
        up_hint = Vector((0.0, 1.0, 0.0))
    right = fwd.cross(up_hint).normalized()
    up = right.cross(fwd).normalized()
    return fwd, right, up


def add_ring(
    verts: list[tuple[float, float, float]],
    weights: list[dict[str, float]],
    center: Vector,
    axis: Vector,
    right: Vector,
    up: Vector,
    rx: float,
    ry: float,
    group_weights: dict[str, float],
    sides: int = 10,
) -> int:
    base = len(verts)
    for side in range(sides):
        angle = math.tau * side / sides
        co = center + right * math.cos(angle) * rx + up * math.sin(angle) * ry
        verts.append((co.x, co.y, co.z))
        weights.append(dict(group_weights))
    return base


def connect_rings(faces: list[tuple[int, ...]], a: int, b: int, sides: int = 10) -> None:
    for side in range(sides):
        faces.append((a + side, a + ((side + 1) % sides), b + ((side + 1) % sides), b + side))


def add_capsule_finger(
    verts: list[tuple[float, float, float]],
    faces: list[tuple[int, ...]],
    weights: list[dict[str, float]],
    base: Vector,
    direction: Vector,
    right: Vector,
    up: Vector,
    length: float,
    radius: float,
    suffix: str,
    finger: str,
) -> tuple[Vector, Vector]:
    sides = 10
    points = [
        base,
        base + direction * (length * 0.34),
        base + direction * (length * 0.68),
        base + direction * length,
    ]
    radii = [(radius * 1.16, radius * 0.92), (radius, radius * 0.78), (radius * 0.76, radius * 0.58), (radius * 0.42, radius * 0.36)]
    bone_names = [f"{finger}_01_{suffix}", f"{finger}_01_{suffix}", f"{finger}_02_{suffix}", f"{finger}_03_{suffix}"]
    rings = []
    for idx, point in enumerate(points):
        blend = {bone_names[idx]: 0.82, f"hand_{suffix}": 0.18} if idx == 0 else {bone_names[idx]: 1.0}
        rings.append(add_ring(verts, weights, point, direction, right, up, radii[idx][0], radii[idx][1], blend, sides))
    faces.append(tuple(reversed(range(rings[0], rings[0] + sides))))
    for a, b in zip(rings, rings[1:]):
        connect_rings(faces, a, b, sides)
    faces.append(tuple(range(rings[-1], rings[-1] + sides)))
    return points[0], points[-1]


def add_tapered_prism(
    verts: list[tuple[float, float, float]],
    faces: list[tuple[int, ...]],
    weights: list[dict[str, float]],
    points: list[Vector],
    direction: Vector,
    right: Vector,
    up: Vector,
    widths: list[float],
    depths: list[float],
    group_weights: list[dict[str, float]],
) -> list[int]:
    """Create a low-profile rounded-box form that reads more like a stylized finger than a rod."""
    ring_bases: list[int] = []
    for point, width, depth, wg in zip(points, widths, depths, group_weights):
        base = len(verts)
        corners = [
            point + right * -width + up * -depth,
            point + right * width + up * -depth,
            point + right * width + up * depth,
            point + right * -width + up * depth,
        ]
        for co in corners:
            verts.append((co.x, co.y, co.z))
            weights.append(dict(wg))
        ring_bases.append(base)
    faces.append(tuple(reversed(range(ring_bases[0], ring_bases[0] + 4))))
    for a, b in zip(ring_bases, ring_bases[1:]):
        faces.extend(
            [
                (a, a + 1, b + 1, b),
                (a + 1, a + 2, b + 2, b + 1),
                (a + 2, a + 3, b + 3, b + 2),
                (a + 3, a, b, b + 3),
            ]
        )
    faces.append(tuple(range(ring_bases[-1], ring_bases[-1] + 4)))
    return ring_bases


def add_overlay_finger(
    verts: list[tuple[float, float, float]],
    faces: list[tuple[int, ...]],
    weights: list[dict[str, float]],
    base: Vector,
    direction: Vector,
    right: Vector,
    up: Vector,
    length: float,
    half_width: float,
    half_depth: float,
    suffix: str,
    finger: str,
) -> tuple[Vector, Vector]:
    points = [
        base,
        base + direction * (length * 0.36),
        base + direction * (length * 0.70),
        base + direction * length,
    ]
    widths = [half_width * 1.18, half_width, half_width * 0.74, half_width * 0.44]
    depths = [half_depth * 1.12, half_depth, half_depth * 0.78, half_depth * 0.52]
    groups = [
        {f"hand_{suffix}": 0.46, f"{finger}_01_{suffix}": 0.54},
        {f"{finger}_01_{suffix}": 1.0},
        {f"{finger}_02_{suffix}": 1.0},
        {f"{finger}_03_{suffix}": 1.0},
    ]
    add_tapered_prism(verts, faces, weights, points, direction, right, up, widths, depths, groups)
    return points[0], points[-1]


def add_knuckle_pad(
    verts: list[tuple[float, float, float]],
    faces: list[tuple[int, ...]],
    weights: list[dict[str, float]],
    center: Vector,
    direction: Vector,
    right: Vector,
    up: Vector,
    suffix: str,
) -> None:
    ring0 = add_ring(verts, weights, center - direction * 0.003, direction, right, up, 0.019, 0.0048, {f"hand_{suffix}": 1.0}, sides=8)
    ring1 = add_ring(verts, weights, center + direction * 0.006, direction, right, up, 0.017, 0.0060, {f"hand_{suffix}": 1.0}, sides=8)
    connect_rings(faces, ring0, ring1, sides=8)


def add_palm_shell(
    verts: list[tuple[float, float, float]],
    faces: list[tuple[int, ...]],
    weights: list[dict[str, float]],
    wrist: Vector,
    palm_end: Vector,
    axis: Vector,
    right: Vector,
    up: Vector,
    suffix: str,
) -> None:
    sides = 12
    centers = [wrist, wrist + axis * 0.023, palm_end]
    dims = [(0.025, 0.019), (0.035, 0.024), (0.031, 0.020)]
    rings = []
    for idx, center in enumerate(centers):
        wg = {f"hand_{suffix}": 0.78, f"lowerarm_{suffix}": 0.22} if idx == 0 else {f"hand_{suffix}": 1.0}
        rings.append(add_ring(verts, weights, center, axis, right, up, dims[idx][0], dims[idx][1], wg, sides))
    faces.append(tuple(reversed(range(rings[0], rings[0] + sides))))
    for a, b in zip(rings, rings[1:]):
        connect_rings(faces, a, b, sides)
    faces.append(tuple(range(rings[-1], rings[-1] + sides)))


def add_webbing(
    verts: list[tuple[float, float, float]],
    faces: list[tuple[int, ...]],
    weights: list[dict[str, float]],
    bases: list[Vector],
    suffix: str,
) -> None:
    for index in range(len(bases) - 1):
        a = bases[index]
        b = bases[index + 1]
        mid = (a + b) * 0.5 + Vector((0.0, 0.006, 0.002))
        base = len(verts)
        verts.extend([(a.x, a.y, a.z), (b.x, b.y, b.z), (mid.x, mid.y, mid.z)])
        weights.extend([{f"hand_{suffix}": 1.0}, {f"hand_{suffix}": 1.0}, {f"hand_{suffix}": 1.0}])
        faces.append((base, base + 1, base + 2))


def assign_weights(obj: bpy.types.Object, weights: list[dict[str, float]]) -> None:
    groups: dict[str, bpy.types.VertexGroup] = {}
    for mapping in weights:
        for name in mapping:
            if name not in groups:
                groups[name] = obj.vertex_groups.new(name=name)
    for idx, mapping in enumerate(weights):
        total = sum(mapping.values()) or 1.0
        for name, value in mapping.items():
            groups[name].add([idx], value / total, "REPLACE")


def build_overlay_hands(arm: bpy.types.Object, report: list[str]) -> bpy.types.Object:
    old = bpy.data.objects.get(WORK_OBJECT_NAME)
    if old:
        data = old.data
        bpy.data.objects.remove(old, do_unlink=True)
        if data and data.users == 0:
            bpy.data.meshes.remove(data)

    for name in sorted(HIDE_FAILED_HANDS):
        obj = bpy.data.objects.get(name)
        if obj:
            obj.hide_viewport = True
            obj.hide_render = True
            report.append(f"Hidden failed/old hand object: {name}")

    verts: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    weights: list[dict[str, float]] = []
    for suffix, side_sign in (("l", -1.0), ("r", 1.0)):
        hand = arm.data.bones.get(f"hand_{suffix}")
        if not hand:
            raise RuntimeError(f"Missing hand_{suffix}")
        axis = (hand.tail_local - hand.head_local).normalized()
        _fwd, right, up = basis(axis)
        # The first two attempts sat behind the visible hand. Nudge this pass toward
        # the camera-facing side of the current model and keep it short/connected.
        front_offset = Vector((0.0, -0.040, 0.0))
        wrist = hand.head_local + axis * 0.006 + front_offset
        palm_end = hand.head_local + axis * 0.043 + front_offset
        add_palm_shell(verts, faces, weights, wrist, palm_end, axis, right, up, suffix)
        add_knuckle_pad(verts, faces, weights, palm_end + axis * 0.002, axis, right, up, suffix)

        offsets = {
            "index": -0.015,
            "middle": -0.004,
            "ring": 0.007,
            "pinky": 0.017,
        }
        lengths = {"index": 0.034, "middle": 0.038, "ring": 0.034, "pinky": 0.027}
        widths = {"index": 0.0078, "middle": 0.0082, "ring": 0.0073, "pinky": 0.0058}
        depths = {"index": 0.0056, "middle": 0.0059, "ring": 0.0053, "pinky": 0.0045}
        bases = []
        for finger in ["index", "middle", "ring", "pinky"]:
            start = palm_end + right * offsets[finger] + up * -0.001
            direction = (axis + right * (offsets[finger] * 0.42)).normalized()
            base, _tip = add_overlay_finger(
                verts,
                faces,
                weights,
                start,
                direction,
                right,
                up,
                lengths[finger],
                widths[finger],
                depths[finger],
                suffix,
                finger,
            )
            bases.append(base)
        thumb_start = hand.head_local + axis * 0.026 + front_offset + right * (0.026 * side_sign) + up * -0.002
        thumb_dir = (axis * 0.44 + right * (0.58 * side_sign) + up * -0.05).normalized()
        add_overlay_finger(verts, faces, weights, thumb_start, thumb_dir, right, up, 0.026, 0.0073, 0.0054, suffix, "thumb")
        add_webbing(verts, faces, weights, bases, suffix)

    mesh = bpy.data.meshes.new(f"{WORK_OBJECT_NAME}_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(WORK_OBJECT_NAME, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(material())
    assign_weights(obj, weights)
    mod = obj.modifiers.new("Armature_Current_Player", "ARMATURE")
    mod.object = arm
    bevel = obj.modifiers.new("Live_Small_Bevel_For_Soft_Hand_Edges", "BEVEL")
    bevel.width = 0.0022
    bevel.segments = 2
    bevel.affect = "EDGES"
    obj.modifiers.new("Live_Hand_Smoothing_WeightedNormals", "WEIGHTED_NORMAL")
    report.append(f"Created {WORK_OBJECT_NAME}: verts={len(verts)} faces={len(faces)} groups={len(obj.vertex_groups)}")
    return obj


def capture(output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.render.resolution_x = 1400
    scene.render.resolution_y = 1800
    try:
        scene.render.engine = "BLENDER_WORKBENCH"
    except TypeError:
        pass
    scene.world.color = (0.03, 0.03, 0.035)
    cam_data = bpy.data.cameras.new("TEMP_HandsPass1C_Camera")
    cam = bpy.data.objects.new("TEMP_HandsPass1C_Camera", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam_data.type = "ORTHO"
    light_data = bpy.data.lights.new("TEMP_HandsPass1C_Light", "AREA")
    light = bpy.data.objects.new("TEMP_HandsPass1C_Light", light_data)
    scene.collection.objects.link(light)
    light.location = (0.0, -2.4, 2.1)
    light_data.energy = 420
    light_data.size = 1.8

    def point(loc, target, scale):
        cam.location = loc
        direction = target - cam.location
        cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        cam.data.ortho_scale = scale

    shots = [
        ("front_full", (0.0, -2.25, 0.50), Vector((0.0, 0.0, 0.50)), 1.18),
        ("three_quarter_full", (1.35, -2.10, 0.53), Vector((0.0, 0.0, 0.50)), 1.18),
        ("left_hand_closeup", (-0.17, -0.64, 0.465), Vector((-0.17, -0.025, 0.465)), 0.18),
        ("right_hand_closeup", (0.17, -0.64, 0.465), Vector((0.17, -0.025, 0.465)), 0.18),
        ("hands_front_closeup", (0.0, -0.92, 0.455), Vector((0.0, -0.025, 0.455)), 0.34),
    ]
    paths = []
    for name, loc, target, scale in shots:
        point(loc, target, scale)
        path = output_dir / f"{name}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        paths.append(path)
    return paths


def main() -> None:
    args = args_after_separator()
    output_blend = Path(args[0]).expanduser().resolve()
    screenshot_dir = Path(args[1]).expanduser().resolve()
    report = ["PLAYER_HANDS_PASS1C_OVERLAY_REPORT", f"Target: {output_blend}"]
    for action in bpy.data.actions:
        action.use_fake_user = True
    arm = bpy.data.objects.get(ARMATURE_NAME)
    if not arm:
        raise RuntimeError("Missing current armature")
    obj = build_overlay_hands(arm, report)
    paths = capture(screenshot_dir)
    report.append("Screenshots:")
    report.extend(str(path) for path in paths)
    report.append("Destructive operations: none on original mesh")
    report.append("Armature changes: none")
    report.append("Weights: WORK_HandsFingers_Pass1C_Overlay weighted to hand/lowerarm/finger groups")
    bpy.ops.wm.save_as_mainfile(filepath=str(output_blend))
    REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))
    bpy.ops.wm.quit_blender()


if __name__ == "__main__":
    main()
