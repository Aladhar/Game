"""Audit key Player.blend bone placement against Mesh_0 geometry."""

from __future__ import annotations

import sys
from pathlib import Path

import bpy
from mathutils import Vector


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BLEND = PROJECT_ROOT / "Content" / "Player" / "Player.blend"
DEFAULT_REPORT = PROJECT_ROOT / "Saved" / "PlayerBonePlacementAudit.txt"
MESH_NAME = "Mesh_0"
RIG_NAME = "ARM_Player_Clean_Deform_IK"


KEY_BONES = [
    "CTRL_root",
    "DEF-spine",
    "DEF-spine.001",
    "DEF-spine.002",
    "DEF-spine.003",
    "DEF-spine.004",
    "DEF-spine.005",
    "DEF-spine.006",
    "DEF-thigh.L",
    "DEF-thigh.L.001",
    "DEF-shin.L",
    "DEF-shin.L.001",
    "DEF-foot.L",
    "DEF-toe.L",
    "DEF-thigh.R",
    "DEF-thigh.R.001",
    "DEF-shin.R",
    "DEF-shin.R.001",
    "DEF-foot.R",
    "DEF-toe.R",
    "DEF-upper_arm.L",
    "DEF-upper_arm.L.001",
    "DEF-forearm.L",
    "DEF-forearm.L.001",
    "DEF-hand.L",
    "DEF-upper_arm.R",
    "DEF-upper_arm.R.001",
    "DEF-forearm.R",
    "DEF-forearm.R.001",
    "DEF-hand.R",
]


def args_after_separator() -> tuple[Path, Path]:
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    src = Path(args[0]).expanduser().resolve() if args else DEFAULT_BLEND
    report = Path(args[1]).expanduser().resolve() if len(args) > 1 else DEFAULT_REPORT
    report.parent.mkdir(parents=True, exist_ok=True)
    return src, report


def fmt(v: Vector) -> str:
    return f"({v.x:.4f},{v.y:.4f},{v.z:.4f})"


def slice_stats(mesh: bpy.types.Object, z_min: float, z_max: float, side: str | None = None) -> str:
    verts = []
    for vertex in mesh.data.vertices:
        p = mesh.matrix_world @ vertex.co
        if not (z_min <= p.z <= z_max):
            continue
        if side == "L" and p.x <= 0.0:
            continue
        if side == "R" and p.x >= 0.0:
            continue
        verts.append(p)
    if not verts:
        return "none"
    mn = Vector((min(v.x for v in verts), min(v.y for v in verts), min(v.z for v in verts)))
    mx = Vector((max(v.x for v in verts), max(v.y for v in verts), max(v.z for v in verts)))
    center = sum(verts, Vector((0.0, 0.0, 0.0))) / len(verts)
    return f"count={len(verts)} center={fmt(center)} min={fmt(mn)} max={fmt(mx)}"


def main() -> None:
    src, report = args_after_separator()
    bpy.ops.wm.open_mainfile(filepath=str(src), load_ui=False)
    mesh = bpy.data.objects.get(MESH_NAME)
    rig = bpy.data.objects.get(RIG_NAME)
    if not mesh or mesh.type != "MESH":
        raise SystemExit(f"Missing mesh {MESH_NAME}")
    if not rig or rig.type != "ARMATURE":
        raise SystemExit(f"Missing rig {RIG_NAME}")

    lines = [
        "PLAYER_BONE_PLACEMENT_AUDIT",
        f"Blend: {src}",
        f"Mesh: {mesh.name}",
        f"Rig: {rig.name}",
        "Mesh z-slices:",
    ]
    for z0, z1, label in [
        (0.00, 0.12, "feet"),
        (0.12, 0.38, "lower legs"),
        (0.38, 0.78, "upper legs"),
        (0.78, 1.05, "hips/pelvis"),
        (1.05, 1.32, "torso"),
        (1.32, 1.50, "shoulders/upper arms"),
        (1.50, 1.65, "neck/head"),
    ]:
        lines.append(f"- {label} z={z0:.2f}-{z1:.2f}: {slice_stats(mesh, z0, z1)}")
    lines.append("Side arm slices:")
    for side in ("L", "R"):
        for z0, z1, label in [(1.28, 1.45, "shoulder"), (1.08, 1.30, "elbow/forearm"), (0.82, 1.08, "wrist/hand")]:
            lines.append(f"- {side} {label}: {slice_stats(mesh, z0, z1, side)}")

    lines.append("Key bone positions:")
    for name in KEY_BONES:
        bone = rig.data.bones.get(name)
        if not bone:
            lines.append(f"- {name}: missing")
            continue
        head = rig.matrix_world @ bone.head_local
        tail = rig.matrix_world @ bone.tail_local
        lines.append(f"- {name}: head={fmt(head)} tail={fmt(tail)} length={(tail - head).length:.4f}")

    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


main()
