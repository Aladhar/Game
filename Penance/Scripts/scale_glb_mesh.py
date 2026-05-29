from __future__ import annotations

import argparse
import json
import shutil
import struct
from pathlib import Path


JSON_CHUNK = 0x4E4F534A
BIN_CHUNK = 0x004E4942
FLOAT = 5126
VEC3 = "VEC3"


COMPONENT_SIZES = {
    5120: 1,  # BYTE
    5121: 1,  # UNSIGNED_BYTE
    5122: 2,  # SHORT
    5123: 2,  # UNSIGNED_SHORT
    5125: 4,  # UNSIGNED_INT
    5126: 4,  # FLOAT
}

TYPE_COUNTS = {
    "SCALAR": 1,
    "VEC2": 2,
    "VEC3": 3,
    "VEC4": 4,
    "MAT2": 4,
    "MAT3": 9,
    "MAT4": 16,
}


def padded(data: bytes, multiple: int, pad_byte: bytes) -> bytes:
    remainder = len(data) % multiple
    if not remainder:
        return data
    return data + pad_byte * (multiple - remainder)


def read_glb(path: Path) -> tuple[dict, bytearray, list[tuple[int, bytes]]]:
    data = path.read_bytes()
    magic, version, length = struct.unpack_from("<III", data, 0)
    if magic != 0x46546C67 or version != 2 or length != len(data):
        raise RuntimeError(f"{path} is not a valid glTF 2.0 binary file")

    offset = 12
    gltf: dict | None = None
    binary: bytearray | None = None
    extra_chunks: list[tuple[int, bytes]] = []
    while offset < len(data):
        chunk_length, chunk_type = struct.unpack_from("<II", data, offset)
        offset += 8
        chunk = data[offset : offset + chunk_length]
        offset += chunk_length
        if chunk_type == JSON_CHUNK:
            gltf = json.loads(chunk.decode("utf-8").rstrip("\x00 "))
        elif chunk_type == BIN_CHUNK:
            binary = bytearray(chunk)
        else:
            extra_chunks.append((chunk_type, chunk))

    if gltf is None or binary is None:
        raise RuntimeError(f"{path} is missing JSON or BIN chunks")
    return gltf, binary, extra_chunks


def accessor_stride(gltf: dict, accessor_index: int) -> tuple[int, int, int, int]:
    accessor = gltf["accessors"][accessor_index]
    buffer_view = gltf["bufferViews"][accessor["bufferView"]]
    component_size = COMPONENT_SIZES[accessor["componentType"]]
    component_count = TYPE_COUNTS[accessor["type"]]
    element_size = component_size * component_count
    stride = buffer_view.get("byteStride", element_size)
    start = buffer_view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    return start, stride, accessor["count"], element_size


def scale_positions(gltf: dict, binary: bytearray, scale: float) -> int:
    position_accessors: set[int] = set()
    for mesh in gltf.get("meshes", []):
        for primitive in mesh.get("primitives", []):
            position = primitive.get("attributes", {}).get("POSITION")
            if position is not None:
                position_accessors.add(position)

    scaled_vertices = 0
    for accessor_index in sorted(position_accessors):
        accessor = gltf["accessors"][accessor_index]
        if accessor.get("componentType") != FLOAT or accessor.get("type") != VEC3:
            raise RuntimeError(f"POSITION accessor {accessor_index} is not FLOAT VEC3")

        start, stride, count, _element_size = accessor_stride(gltf, accessor_index)
        mins = [float("inf"), float("inf"), float("inf")]
        maxs = [float("-inf"), float("-inf"), float("-inf")]
        for vertex_index in range(count):
            offset = start + vertex_index * stride
            xyz = list(struct.unpack_from("<fff", binary, offset))
            xyz = [value * scale for value in xyz]
            struct.pack_into("<fff", binary, offset, *xyz)
            for axis, value in enumerate(xyz):
                mins[axis] = min(mins[axis], value)
                maxs[axis] = max(maxs[axis], value)
        accessor["min"] = mins
        accessor["max"] = maxs
        scaled_vertices += count

    return scaled_vertices


def write_glb(path: Path, gltf: dict, binary: bytearray, extra_chunks: list[tuple[int, bytes]]) -> None:
    gltf.setdefault("buffers", [{}])[0]["byteLength"] = len(binary)
    json_bytes = padded(json.dumps(gltf, separators=(",", ":")).encode("utf-8"), 4, b" ")
    bin_bytes = padded(bytes(binary), 4, b"\x00")

    chunks = [(JSON_CHUNK, json_bytes), (BIN_CHUNK, bin_bytes), *extra_chunks]
    total_length = 12 + sum(8 + len(chunk) for _chunk_type, chunk in chunks)
    out = bytearray(struct.pack("<III", 0x46546C67, 2, total_length))
    for chunk_type, chunk in chunks:
        out.extend(struct.pack("<II", len(chunk), chunk_type))
        out.extend(chunk)
    path.write_bytes(out)


def main() -> None:
    parser = argparse.ArgumentParser(description="Bake a uniform scale into GLB mesh POSITION data.")
    parser.add_argument("path", type=Path)
    parser.add_argument("--scale", type=float, required=True)
    parser.add_argument("--backup", type=Path)
    args = parser.parse_args()

    if args.scale <= 0.0:
        raise RuntimeError("--scale must be positive")

    source = args.path.resolve()
    if args.backup:
        backup = args.backup.resolve()
        backup.parent.mkdir(parents=True, exist_ok=True)
        if not backup.exists():
            shutil.copy2(source, backup)

    gltf, binary, extra_chunks = read_glb(source)
    vertex_count = scale_positions(gltf, binary, args.scale)
    write_glb(source, gltf, binary, extra_chunks)
    print(f"Scaled {vertex_count} POSITION vertices in {source} by {args.scale:g}")


if __name__ == "__main__":
    main()
