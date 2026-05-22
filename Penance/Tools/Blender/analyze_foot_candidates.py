import bpy
from collections import Counter, deque


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


def component_groups(obj, component):
    names = {group.index: group.name for group in obj.vertex_groups}
    counts = Counter()
    for index in component:
        for item in obj.data.vertices[index].groups:
            counts[names[item.group]] += 1
    return counts.most_common(8)


for obj in [item for item in bpy.data.objects if item.type == "MESH"]:
    mesh = obj.data
    neighbors = [[] for _ in mesh.vertices]
    for edge in mesh.edges:
        a, b = edge.vertices
        neighbors[a].append(b)
        neighbors[b].append(a)

    seen = set()
    candidates = []
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

        mins, maxs = bounds(mesh, component)
        if len(component) >= 100 and mins[2] <= 0.08 and maxs[2] <= 0.55:
            candidates.append((len(component), mins, maxs, component))

    print(f"MESH {obj.name} foot_candidates={len(candidates)}")
    for rank, (size, mins, maxs, component) in enumerate(
        sorted(candidates, reverse=True), start=1
    ):
        print(
            f"  #{rank}: verts={size} min={mins} max={maxs} "
            f"groups={component_groups(obj, component)}"
        )
