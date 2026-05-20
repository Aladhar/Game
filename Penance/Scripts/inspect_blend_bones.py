"""Report armature bone head/tail coordinates for a Blender file."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import bpy


def main() -> None:
    if "--" not in sys.argv:
        raise SystemExit("Expected -- SRC.blend REPORT.txt")
    args = sys.argv[sys.argv.index("--") + 1 :]
    src = Path(args[0]).resolve()
    report = Path(args[1]).resolve()
    report.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(src))
    armature = next(obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE")
    lines = ["BLEND_BONE_REPORT", f"Blend: {src}", f"Armature: {armature.name}"]
    for bone in armature.data.bones:
        h = armature.matrix_world @ bone.head_local
        t = armature.matrix_world @ bone.tail_local
        lines.append(
            f"{bone.name}: head=({h.x:.5f},{h.y:.5f},{h.z:.5f}) "
            f"tail=({t.x:.5f},{t.y:.5f},{t.z:.5f}) deform={bone.use_deform}"
        )
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"WROTE_BONE_REPORT: {report}")
    os._exit(0)


main()
