import argparse
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def import_glb(path):
    bpy.ops.import_scene.gltf(filepath=str(path))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError(f"No mesh objects imported from {path}")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    mesh = bpy.context.view_layer.objects.active
    mesh.name = path.stem + "_Mesh"
    return mesh


def world_bounds(obj):
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    minimum = Vector((min(v.x for v in corners), min(v.y for v in corners), min(v.z for v in corners)))
    maximum = Vector((max(v.x for v in corners), max(v.y for v in corners), max(v.z for v in corners)))
    return minimum, maximum


def prepare_mesh(mesh):
    bpy.context.view_layer.objects.active = mesh
    mesh.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    minimum, maximum = world_bounds(mesh)
    center = (minimum + maximum) * 0.5
    mesh.location.x -= center.x
    mesh.location.y -= center.y
    mesh.location.z -= minimum.z
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
    return world_bounds(mesh)


def add_bone(edit_bones, name, head, tail, parent=None, connected=False):
    bone = edit_bones.new(name)
    bone.head = Vector(head)
    bone.tail = Vector(tail)
    if parent:
        bone.parent = parent
        bone.use_connect = connected
    return bone


def create_humanoid_armature(mesh, name, tall_scale=1.0):
    minimum, maximum = prepare_mesh(mesh)
    width_x = max(maximum.x - minimum.x, 0.01)
    depth_y = max(maximum.y - minimum.y, 0.01)
    height = max(maximum.z - minimum.z, 0.01)
    radius = max(width_x, depth_y) * 0.5

    bpy.ops.object.armature_add(enter_editmode=True, location=(0.0, 0.0, 0.0))
    armature = bpy.context.object
    armature.name = name + "_Armature"
    armature.data.name = name + "_Skeleton"

    edit_bones = armature.data.edit_bones
    edit_bones.remove(edit_bones[0])

    hip_z = height * 0.46
    spine_z = height * 0.62
    chest_z = height * 0.76
    neck_z = height * 0.86
    head_z = height * 0.98
    shoulder_x = radius * 0.58
    elbow_x = radius * 0.95
    hand_x = radius * 1.20
    hip_x = radius * 0.32
    knee_z = height * 0.24
    foot_z = height * 0.04

    root = add_bone(edit_bones, "root", (0, 0, 0), (0, 0, hip_z))
    pelvis = add_bone(edit_bones, "pelvis", (0, 0, hip_z), (0, 0, spine_z), root, False)
    spine = add_bone(edit_bones, "spine_01", (0, 0, spine_z), (0, 0, chest_z), pelvis, True)
    chest = add_bone(edit_bones, "spine_02", (0, 0, chest_z), (0, 0, neck_z), spine, True)
    neck = add_bone(edit_bones, "neck_01", (0, 0, neck_z), (0, 0, head_z), chest, True)
    add_bone(edit_bones, "head", (0, 0, head_z), (0, 0, height * 1.08), neck, True)

    for side, sign in (("l", -1), ("r", 1)):
        clavicle = add_bone(
            edit_bones,
            f"clavicle_{side}",
            (0, 0, chest_z),
            (sign * shoulder_x, 0, chest_z),
            chest,
            False,
        )
        upper = add_bone(
            edit_bones,
            f"upperarm_{side}",
            (sign * shoulder_x, 0, chest_z),
            (sign * elbow_x, 0, height * 0.58),
            clavicle,
            True,
        )
        lower = add_bone(
            edit_bones,
            f"lowerarm_{side}",
            (sign * elbow_x, 0, height * 0.58),
            (sign * hand_x, 0, height * 0.42),
            upper,
            True,
        )
        add_bone(
            edit_bones,
            f"hand_{side}",
            (sign * hand_x, 0, height * 0.42),
            (sign * hand_x * 1.08, 0, height * 0.34),
            lower,
            True,
        )
        thigh = add_bone(
            edit_bones,
            f"thigh_{side}",
            (sign * hip_x, 0, hip_z),
            (sign * hip_x, 0, knee_z),
            pelvis,
            False,
        )
        calf = add_bone(
            edit_bones,
            f"calf_{side}",
            (sign * hip_x, 0, knee_z),
            (sign * hip_x, 0, foot_z),
            thigh,
            True,
        )
        add_bone(
            edit_bones,
            f"foot_{side}",
            (sign * hip_x, 0, foot_z),
            (sign * hip_x, depth_y * 0.55, foot_z),
            calf,
            True,
        )

    bpy.ops.object.mode_set(mode="OBJECT")
    armature.show_in_front = True
    armature.scale = (tall_scale, tall_scale, tall_scale)
    return armature


def distance_to_segment(point, start, end):
    segment = end - start
    length_squared = segment.length_squared
    if length_squared <= 0.000001:
        return (point - start).length
    t = max(0.0, min(1.0, (point - start).dot(segment) / length_squared))
    closest = start + segment * t
    return (point - closest).length


def create_manual_weights(mesh, armature):
    for group in mesh.vertex_groups:
        mesh.vertex_groups.remove(group)

    bones = [bone for bone in armature.data.bones if bone.name != "root"]
    groups = {bone.name: mesh.vertex_groups.new(name=bone.name) for bone in bones}
    segments = [
        (
            bone.name,
            armature.matrix_world @ bone.head_local,
            armature.matrix_world @ bone.tail_local,
        )
        for bone in bones
    ]

    for vertex in mesh.data.vertices:
        point = mesh.matrix_world @ vertex.co
        distances = []
        for bone_name, start, end in segments:
            distance = distance_to_segment(point, start, end)
            distances.append((distance, bone_name))
        distances.sort(key=lambda item: item[0])
        nearest = distances[:4]
        raw_weights = []
        for distance, bone_name in nearest:
            raw_weights.append((1.0 / max(distance * distance, 0.0001), bone_name))
        total = sum(weight for weight, _bone_name in raw_weights)
        for weight, bone_name in raw_weights:
            groups[bone_name].add([vertex.index], weight / total, "ADD")


def bind_manual_weights(mesh, armature):
    create_manual_weights(mesh, armature)
    modifier = mesh.modifiers.new(name="Armature", type="ARMATURE")
    modifier.object = armature
    mesh.parent = armature


def bind_auto_weights(mesh, armature):
    bpy.ops.object.select_all(action="DESELECT")
    mesh.select_set(True)
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    if not mesh.vertex_groups:
        bind_manual_weights(mesh, armature)


def export_fbx(mesh, armature, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    mesh.select_set(True)
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.export_scene.fbx(
        filepath=str(output),
        use_selection=True,
        object_types={"ARMATURE", "MESH"},
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL",
        bake_space_transform=False,
        add_leaf_bones=False,
        bake_anim=False,
        mesh_smooth_type="FACE",
        use_mesh_modifiers=True,
        path_mode="COPY",
        embed_textures=True,
    )


def run(source, output, name):
    clear_scene()
    mesh = import_glb(source)
    armature = create_humanoid_armature(mesh, name)
    bind_manual_weights(mesh, armature)
    export_fbx(mesh, armature, output)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--name", required=True)
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else sys.argv[1:]
    args = parser.parse_args(argv)
    run(Path(args.source), Path(args.output), args.name)


if __name__ == "__main__":
    main()
