import argparse
import sys
from pathlib import Path

import bpy


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def world_bounds(obj):
    corners = [obj.matrix_world @ obj.data.vertices[i].co for i in range(len(obj.data.vertices))]
    return (
        (min(v.x for v in corners), min(v.y for v in corners), min(v.z for v in corners)),
        (max(v.x for v in corners), max(v.y for v in corners), max(v.z for v in corners)),
    )


def inspect(path):
    clear_scene()
    bpy.ops.import_scene.fbx(filepath=str(path))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    armatures = [obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"]
    lines = [f"FBX_RIG_INSPECT {path}"]
    lines.append(f"Meshes: {len(meshes)}")
    for mesh in meshes:
        minimum, maximum = world_bounds(mesh)
        lines.append(
            f"Mesh {mesh.name}: min=({minimum[0]:.3f},{minimum[1]:.3f},{minimum[2]:.3f}) "
            f"max=({maximum[0]:.3f},{maximum[1]:.3f},{maximum[2]:.3f}) "
            f"verts={len(mesh.data.vertices)} groups={len(mesh.vertex_groups)}"
        )
        group_names = [group.name for group in mesh.vertex_groups]
        lines.append("Vertex groups: " + ", ".join(group_names))

    lines.append(f"Armatures: {len(armatures)}")
    for armature in armatures:
        lines.append(f"Armature {armature.name}: bones={len(armature.data.bones)}")
        for bone in armature.data.bones:
            head = armature.matrix_world @ bone.head_local
            tail = armature.matrix_world @ bone.tail_local
            parent = bone.parent.name if bone.parent else "None"
            lines.append(
                f"Bone {bone.name}: head=({head.x:.3f},{head.y:.3f},{head.z:.3f}) "
                f"tail=({tail.x:.3f},{tail.y:.3f},{tail.z:.3f}) parent={parent}"
            )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fbx", required=True)
    parser.add_argument("--report", required=True)
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else sys.argv[1:]
    args = parser.parse_args(argv)
    report = inspect(Path(args.fbx))
    Path(args.report).write_text(report + "\n")
    print(report)


if __name__ == "__main__":
    main()
