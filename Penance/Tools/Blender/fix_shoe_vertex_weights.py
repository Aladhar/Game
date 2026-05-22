import bpy
import os
from collections import deque


MAX_SHOE_Z = 0.32
MIN_SHOE_Z = 0.04
MIN_COMPONENT_VERTS = 75


def get_or_create_group(obj, name):
    group = obj.vertex_groups.get(name)
    if group is None:
        group = obj.vertex_groups.new(name=name)
    return group


def connected_components(mesh):
    neighbors = [[] for _ in mesh.vertices]
    for edge in mesh.edges:
        a, b = edge.vertices
        neighbors[a].append(b)
        neighbors[b].append(a)

    seen = set()
    for vertex in mesh.vertices:
        if vertex.index in seen:
            continue
        queue = deque([vertex.index])
        seen.add(vertex.index)
        component = []
        while queue:
            current = queue.popleft()
            component.append(current)
            for nxt in neighbors[current]:
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        yield component


def component_bounds(mesh, component):
    mins = [float("inf"), float("inf"), float("inf")]
    maxs = [float("-inf"), float("-inf"), float("-inf")]
    total_x = 0.0
    for index in component:
        co = mesh.vertices[index].co
        total_x += co.x
        mins[0] = min(mins[0], co.x)
        mins[1] = min(mins[1], co.y)
        mins[2] = min(mins[2], co.z)
        maxs[0] = max(maxs[0], co.x)
        maxs[1] = max(maxs[1], co.y)
        maxs[2] = max(maxs[2], co.z)
    return mins, maxs, total_x / len(component)


def is_shoe_component(mesh, component):
    if len(component) < MIN_COMPONENT_VERTS:
        return False
    mins, maxs, center_x = component_bounds(mesh, component)
    if mins[2] > MIN_SHOE_Z:
        return False
    if maxs[2] > MAX_SHOE_Z:
        return False
    if abs(center_x) < 0.01:
        return False
    return True


def clear_vertex_groups(obj, vertex_indices):
    for group in obj.vertex_groups:
        group.remove(vertex_indices)


def normalize_all_vertex_weights(obj):
    for vertex in obj.data.vertices:
        total_weight = sum(item.weight for item in vertex.groups)
        if total_weight <= 0:
            continue
        for item in vertex.groups:
            item.weight = item.weight / total_weight


def fix_mesh(obj):
    mesh = obj.data
    left_group = get_or_create_group(obj, "foot_l")
    right_group = get_or_create_group(obj, "foot_r")

    left_vertices = []
    right_vertices = []

    for component in connected_components(mesh):
        if not is_shoe_component(mesh, component):
            continue
        _mins, _maxs, center_x = component_bounds(mesh, component)
        if center_x < 0:
            left_vertices.extend(component)
        else:
            right_vertices.extend(component)

    left_vertices = sorted(set(left_vertices))
    right_vertices = sorted(set(right_vertices))

    clear_vertex_groups(obj, left_vertices)
    clear_vertex_groups(obj, right_vertices)
    if left_vertices:
        left_group.add(left_vertices, 1.0, "REPLACE")
    if right_vertices:
        right_group.add(right_vertices, 1.0, "REPLACE")

    normalize_all_vertex_weights(obj)

    return len(left_vertices), len(right_vertices)


totals = []
for obj in [item for item in bpy.data.objects if item.type == "MESH"]:
    left_count, right_count = fix_mesh(obj)
    totals.append((obj.name, left_count, right_count))
    print(
        f"FIXED {obj.name}: left_shoe_vertices={left_count} "
        f"right_shoe_vertices={right_count}"
    )

if not any(left or right for _name, left, right in totals):
    raise RuntimeError("No shoe vertices matched the expected low foot components")

bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print(f"SAVED {os.path.basename(bpy.data.filepath)}")
