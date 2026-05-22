import bpy
from collections import deque


def bounds(mesh, indices):
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
    neighbors = [[] for _ in mesh.vertices]
    for edge in mesh.edges:
        a, b = edge.vertices
        neighbors[a].append(b)
        neighbors[b].append(a)

    seen = set()
    components = []
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
        components.append(component)

    print(f"MESH {obj.name} components={len(components)}")
    ranked = sorted(components, key=len, reverse=True)
    for index, component in enumerate(ranked[:30], start=1):
        mins, maxs = bounds(mesh, component)
        if maxs[2] > 0.45 and len(component) < 1000:
            continue
        print(f"  #{index}: verts={len(component)} min={mins} max={maxs}")
