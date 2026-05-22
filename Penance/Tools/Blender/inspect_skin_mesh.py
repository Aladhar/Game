import bpy
from collections import defaultdict


def bounds_for_vertices(mesh, indices):
    mins = [float("inf"), float("inf"), float("inf")]
    maxs = [float("-inf"), float("-inf"), float("-inf")]
    for index in indices:
        co = mesh.vertices[index].co
        mins[0] = min(mins[0], co.x)
        mins[1] = min(mins[1], co.y)
        mins[2] = min(mins[2], co.z)
        maxs[0] = max(maxs[0], co.x)
        maxs[1] = max(maxs[1], co.y)
        maxs[2] = max(maxs[2], co.z)
    return [round(v, 4) for v in mins], [round(v, 4) for v in maxs]


for obj in [item for item in bpy.data.objects if item.type == "MESH"]:
    mesh = obj.data
    print(f"MESH {obj.name} verts={len(mesh.vertices)} polys={len(mesh.polygons)}")
    print("VERTEX_GROUPS", [group.name for group in obj.vertex_groups])
    material_names = [
        material.name if material else "<none>" for material in mesh.materials
    ]
    print("MATERIALS", material_names)

    material_vertices = defaultdict(set)
    material_polys = defaultdict(int)
    for polygon in mesh.polygons:
        material_name = (
            material_names[polygon.material_index]
            if polygon.material_index < len(material_names)
            else "<bad>"
        )
        material_polys[material_name] += 1
        material_vertices[material_name].update(polygon.vertices)

    print("MATERIAL_STATS")
    for material_name in sorted(material_vertices):
        mins, maxs = bounds_for_vertices(mesh, material_vertices[material_name])
        print(
            f"  {material_name}: polys={material_polys[material_name]} "
            f"verts={len(material_vertices[material_name])} min={mins} max={maxs}"
        )

    print("GROUP_STATS")
    for group in obj.vertex_groups:
        indices = []
        for vertex in mesh.vertices:
            if any(weight.group == group.index for weight in vertex.groups):
                indices.append(vertex.index)
        if not indices:
            continue
        mins, maxs = bounds_for_vertices(mesh, indices)
        print(f"  {group.name}: verts={len(indices)} min={mins} max={maxs}")
