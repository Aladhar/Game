from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ARMATURE_NAME = "SK_Player_Armature"
FINGERS = ("thumb", "index", "middle", "ring", "pinky")


def args_after_separator() -> list[str]:
    if "--" not in sys.argv:
        return []
    return sys.argv[sys.argv.index("--") + 1 :]


def bend_fingers(arm: bpy.types.Object) -> list[str]:
    report: list[str] = []
    arm.data.pose_position = "POSE"
    for suffix in ("l", "r"):
        for finger in FINGERS:
            for idx, amount in ((1, 0.44), (2, 0.34), (3, 0.24)):
                name = f"{finger}_{idx:02d}_{suffix}"
                pose_bone = arm.pose.bones.get(name)
                if not pose_bone:
                    report.append(f"Missing pose bone: {name}")
                    continue
                pose_bone.rotation_mode = "XYZ"
                pose_bone.rotation_euler[1] = amount
                pose_bone.rotation_euler[2] = amount * 0.22
                report.append(f"Bent {name}: y={amount:.2f} rad z={amount * 0.22:.2f} rad")
    bpy.context.view_layer.update()
    return report


def render(output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.render.resolution_x = 1400
    scene.render.resolution_y = 1800
    try:
        scene.render.engine = "BLENDER_WORKBENCH"
    except TypeError:
        pass
    scene.world.color = (0.03, 0.03, 0.035)

    cam_data = bpy.data.cameras.new("TEMP_HandsPoseStress_Camera")
    cam = bpy.data.objects.new("TEMP_HandsPoseStress_Camera", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam_data.type = "ORTHO"

    light_data = bpy.data.lights.new("TEMP_HandsPoseStress_Light", "AREA")
    light = bpy.data.objects.new("TEMP_HandsPoseStress_Light", light_data)
    scene.collection.objects.link(light)
    light.location = (0.0, -2.4, 2.1)
    light_data.energy = 420
    light_data.size = 1.8

    def point(loc: tuple[float, float, float], target: Vector, scale: float) -> None:
        cam.location = loc
        direction = target - cam.location
        cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        cam.data.ortho_scale = scale

    shots = [
        ("pose_bend_left", (-0.17, -0.64, 0.465), Vector((-0.17, -0.025, 0.465)), 0.18),
        ("pose_bend_right", (0.17, -0.64, 0.465), Vector((0.17, -0.025, 0.465)), 0.18),
    ]
    paths: list[Path] = []
    for name, loc, target, scale in shots:
        point(loc, target, scale)
        path = output_dir / f"{name}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        paths.append(path)
    return paths


def main() -> None:
    args = args_after_separator()
    output_dir = Path(args[0]).expanduser().resolve()
    report_path = Path(args[1]).expanduser().resolve()
    arm = bpy.data.objects.get(ARMATURE_NAME)
    if not arm:
        raise RuntimeError(f"Missing {ARMATURE_NAME}")
    report = ["PLAYER_HANDS_PASS1C_POSE_STRESS_RENDER", *bend_fingers(arm)]
    paths = render(output_dir)
    report.append("Screenshots:")
    report.extend(str(path) for path in paths)
    report.append("Saved blend: no")
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))
    bpy.ops.wm.quit_blender()


if __name__ == "__main__":
    main()
