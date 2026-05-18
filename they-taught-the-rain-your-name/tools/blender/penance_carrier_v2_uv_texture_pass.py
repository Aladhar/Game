"""
Penance Carrier v2 UV + procedural texture pass.

Run from the Godot project root:
  blender --background --factory-startup --python tools/blender/penance_carrier_v2_uv_texture_pass.py

Input:
  assets/models/enemies/penance_carrier/blender_work/penance_carrier_v2_sculpt_prep.blend

Outputs:
  assets/models/enemies/penance_carrier/blender_work/penance_carrier_v2_textured.blend
  assets/models/enemies/penance_carrier/penance_carrier_v2_textured.glb
  assets/textures/enemies/penance_carrier/generated/*.png

This is an automated production pass, not a replacement for human sculpting or
hand-painted hero textures. It creates usable UVs and authored placeholder PBR
maps so the asset can be validated in Godot before the final art pass.
"""

from __future__ import annotations

import math
import struct
import zlib
from pathlib import Path

import bpy


def find_project_root() -> Path:
    try:
        script_path = Path(__file__).resolve()
    except NameError:
        script_path = Path.cwd().resolve()

    current = script_path.parent
    for _ in range(8):
        if (current / "project.godot").exists():
            return current
        current = current.parent

    return Path.cwd().resolve()


PROJECT_ROOT = find_project_root()
ASSET_ROOT = PROJECT_ROOT / "assets/models/enemies/penance_carrier"
TEXTURE_ROOT = PROJECT_ROOT / "assets/textures/enemies/penance_carrier/generated"
INPUT_BLEND = ASSET_ROOT / "blender_work/penance_carrier_v2_sculpt_prep.blend"
OUTPUT_BLEND = ASSET_ROOT / "blender_work/penance_carrier_v2_textured.blend"
OUTPUT_GLB = ASSET_ROOT / "penance_carrier_v2_textured.glb"


TEXTURE_SETS = {
    "PC_V2_soaked_cloth": {
        "prefix": "penance_carrier_body_cloth",
        "size": 1024,
        "base": (22, 22, 21),
        "accent": (82, 78, 70),
        "roughness": 226,
        "metallic": 0,
    },
    "PC_V2_weathered_wood": {
        "prefix": "penance_carrier_house_wood",
        "size": 1024,
        "base": (82, 61, 43),
        "accent": (150, 124, 92),
        "roughness": 212,
        "metallic": 0,
    },
    "PC_V2_rusted_iron": {
        "prefix": "penance_carrier_metal_relics",
        "size": 1024,
        "base": (76, 63, 55),
        "accent": (158, 83, 44),
        "roughness": 196,
        "metallic": 210,
    },
    "PC_V2_corroded_brass": {
        "prefix": "penance_carrier_brass_relics",
        "size": 1024,
        "base": (133, 96, 45),
        "accent": (78, 124, 98),
        "roughness": 168,
        "metallic": 225,
    },
    "PC_V2_old_paper_photo": {
        "prefix": "penance_carrier_paper_decals",
        "size": 512,
        "base": (125, 103, 75),
        "accent": (205, 184, 138),
        "roughness": 232,
        "metallic": 0,
    },
    "PC_V2_glass_lens": {
        "prefix": "penance_carrier_glass_lens",
        "size": 512,
        "base": (28, 38, 40),
        "accent": (118, 150, 152),
        "roughness": 70,
        "metallic": 0,
    },
    "PC_V2_wax_candle": {
        "prefix": "penance_carrier_wax_candle",
        "size": 512,
        "base": (194, 160, 109),
        "accent": (255, 168, 72),
        "roughness": 152,
        "metallic": 0,
        "emissive": (255, 118, 36),
    },
    "PC_V2_rope": {
        "prefix": "penance_carrier_rope",
        "size": 512,
        "base": (59, 44, 29),
        "accent": (130, 101, 66),
        "roughness": 235,
        "metallic": 0,
    },
    "PC_V2_aged_leather": {
        "prefix": "penance_carrier_aged_leather",
        "size": 512,
        "base": (64, 37, 20),
        "accent": (139, 80, 38),
        "roughness": 190,
        "metallic": 0,
    },
    "PC_V2_black_void": {
        "prefix": "penance_carrier_mask_void",
        "size": 512,
        "base": (2, 2, 2),
        "accent": (22, 18, 14),
        "roughness": 250,
        "metallic": 0,
    },
}


def png_chunk(kind: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + kind
        + data
        + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    )


def write_png_rgb(path: Path, width: int, height: int, row_fn) -> None:
    compressor = zlib.compressobj(level=6)
    compressed_parts: list[bytes] = []

    for y in range(height):
        row = bytearray(1 + width * 3)
        offset = 1
        for x in range(width):
            r, g, b = row_fn(x, y, width, height)
            row[offset] = max(0, min(255, int(r)))
            row[offset + 1] = max(0, min(255, int(g)))
            row[offset + 2] = max(0, min(255, int(b)))
            offset += 3
        compressed_parts.append(compressor.compress(bytes(row)))

    compressed_parts.append(compressor.flush())
    raw = b"".join(compressed_parts)
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", header) + png_chunk(b"IDAT", raw) + png_chunk(b"IEND", b""))


def hash_noise(x: int, y: int, seed: int) -> float:
    n = x * 374761393 + y * 668265263 + seed * 1442695041
    n = (n ^ (n >> 13)) * 1274126177
    n = n ^ (n >> 16)
    return (n & 0xFFFFFFFF) / 0xFFFFFFFF


def smooth_noise(x: float, y: float, seed: int) -> float:
    xi = math.floor(x)
    yi = math.floor(y)
    xf = x - xi
    yf = y - yi
    u = xf * xf * (3.0 - 2.0 * xf)
    v = yf * yf * (3.0 - 2.0 * yf)
    a = hash_noise(xi, yi, seed)
    b = hash_noise(xi + 1, yi, seed)
    c = hash_noise(xi, yi + 1, seed)
    d = hash_noise(xi + 1, yi + 1, seed)
    return (a * (1.0 - u) + b * u) * (1.0 - v) + (c * (1.0 - u) + d * u) * v


def fbm(u: float, v: float, seed: int) -> float:
    total = 0.0
    amplitude = 0.55
    frequency = 3.0
    normalizer = 0.0
    for octave in range(5):
        total += smooth_noise(u * frequency, v * frequency, seed + octave * 17) * amplitude
        normalizer += amplitude
        amplitude *= 0.52
        frequency *= 2.15
    return total / normalizer


def height_value(x: int, y: int, width: int, height: int, seed: int, material_kind: str) -> float:
    u = x / max(1, width - 1)
    v = y / max(1, height - 1)
    n = fbm(u, v, seed)
    if "wood" in material_kind:
        grain = abs(math.sin((u * 28.0 + n * 5.0) * math.pi))
        return n * 0.45 + grain * 0.55
    if "cloth" in material_kind or "rope" in material_kind:
        weave = (abs(math.sin(u * 180.0)) + abs(math.sin(v * 150.0))) * 0.25
        return n * 0.6 + weave * 0.4
    if "metal" in material_kind or "brass" in material_kind:
        pits = 1.0 if hash_noise(x // 8, y // 8, seed + 99) > 0.82 else 0.0
        return n * 0.75 + pits * 0.25
    return n


def make_texture_set(material_name: str, spec: dict) -> dict[str, Path]:
    prefix = spec["prefix"]
    size = int(spec["size"])
    base = spec["base"]
    accent = spec["accent"]
    seed = sum(ord(c) for c in prefix)
    TEXTURE_ROOT.mkdir(parents=True, exist_ok=True)

    paths = {
        "basecolor": TEXTURE_ROOT / f"{prefix}_basecolor_{size}.png",
        "normal": TEXTURE_ROOT / f"{prefix}_normal_{size}.png",
        "roughness": TEXTURE_ROOT / f"{prefix}_roughness_{size}.png",
        "ao": TEXTURE_ROOT / f"{prefix}_ao_{size}.png",
        "metallic": TEXTURE_ROOT / f"{prefix}_metallic_{size}.png",
    }
    if "emissive" in spec:
        paths["emissive"] = TEXTURE_ROOT / f"{prefix}_emissive_{size}.png"

    def basecolor_row(x, y, w, h):
        n = height_value(x, y, w, h, seed, material_name)
        stain = hash_noise(x // 48, y // 48, seed + 31)
        mix = max(0.0, min(1.0, n * 0.82 + stain * 0.18))
        edge_dirt = 0.82 + 0.18 * smooth_noise(x / 96.0, y / 96.0, seed + 44)
        return tuple((base[i] * (1.0 - mix) + accent[i] * mix) * edge_dirt for i in range(3))

    def normal_row(x, y, w, h):
        h_l = height_value(max(0, x - 1), y, w, h, seed, material_name)
        h_r = height_value(min(w - 1, x + 1), y, w, h, seed, material_name)
        h_d = height_value(x, max(0, y - 1), w, h, seed, material_name)
        h_u = height_value(x, min(h - 1, y + 1), w, h, seed, material_name)
        sx = (h_l - h_r) * 3.0
        sy = (h_d - h_u) * 3.0
        nz = 1.0
        length = math.sqrt(sx * sx + sy * sy + nz * nz)
        return ((sx / length * 0.5 + 0.5) * 255, (sy / length * 0.5 + 0.5) * 255, (nz / length * 0.5 + 0.5) * 255)

    def roughness_row(x, y, w, h):
        n = height_value(x, y, w, h, seed + 7, material_name)
        r = spec["roughness"] + (n - 0.5) * 42
        return (r, r, r)

    def ao_row(x, y, w, h):
        n = height_value(x, y, w, h, seed + 11, material_name)
        ao = 160 + n * 78
        return (ao, ao, ao)

    def metallic_row(x, y, w, h):
        m = spec["metallic"]
        return (m, m, m)

    write_png_rgb(paths["basecolor"], size, size, basecolor_row)
    write_png_rgb(paths["normal"], size, size, normal_row)
    write_png_rgb(paths["roughness"], size, size, roughness_row)
    write_png_rgb(paths["ao"], size, size, ao_row)
    write_png_rgb(paths["metallic"], size, size, metallic_row)

    if "emissive" in paths:
        emissive = spec["emissive"]

        def emissive_row(x, y, w, h):
            flame = max(0.0, 1.0 - abs((x / w) - 0.5) * 3.0) * max(0.0, 1.0 - abs((y / h) - 0.42) * 3.6)
            n = smooth_noise(x / 24.0, y / 24.0, seed + 55)
            strength = max(0.0, min(1.0, flame * 0.85 + n * 0.15))
            return tuple(c * strength for c in emissive)

        write_png_rgb(paths["emissive"], size, size, emissive_row)

    return paths


def smart_uv_unwrap() -> None:
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        if not obj.data.uv_layers:
            obj.data.uv_layers.new(name="UVMap")
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        try:
            bpy.ops.uv.cube_project(cube_size=4.0, correct_aspect=True, clip_to_bounds=False, scale_to_bounds=True)
        except Exception as exc:
            print(f"UV unwrap skipped for {obj.name}: {exc}", flush=True)
        bpy.ops.object.mode_set(mode="OBJECT")


def clear_nodes(material: bpy.types.Material) -> bpy.types.Node:
    material.use_nodes = True
    nodes = material.node_tree.nodes
    for node in list(nodes):
        nodes.remove(node)
    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    bsdf.location = (260, 0)
    out = nodes.new(type="ShaderNodeOutputMaterial")
    out.location = (560, 0)
    material.node_tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return bsdf


def add_image_node(material: bpy.types.Material, path: Path, colorspace: str, location: tuple[int, int]):
    image = bpy.data.images.load(str(path), check_existing=True)
    image.colorspace_settings.name = colorspace
    node = material.node_tree.nodes.new(type="ShaderNodeTexImage")
    node.image = image
    node.location = location
    return node


def bind_textures_to_materials(all_paths: dict[str, dict[str, Path]]) -> None:
    for material_name, paths in all_paths.items():
        mat = bpy.data.materials.get(material_name)
        if mat is None:
            continue

        bsdf = clear_nodes(mat)
        links = mat.node_tree.links

        base = add_image_node(mat, paths["basecolor"], "sRGB", (-620, 180))
        rough = add_image_node(mat, paths["roughness"], "Non-Color", (-620, -80))
        metal = add_image_node(mat, paths["metallic"], "Non-Color", (-620, -300))
        normal_tex = add_image_node(mat, paths["normal"], "Non-Color", (-860, -520))
        normal_map = mat.node_tree.nodes.new(type="ShaderNodeNormalMap")
        normal_map.location = (-360, -500)
        normal_map.inputs["Strength"].default_value = 0.55

        links.new(base.outputs["Color"], bsdf.inputs["Base Color"])
        links.new(rough.outputs["Color"], bsdf.inputs["Roughness"])
        links.new(metal.outputs["Color"], bsdf.inputs["Metallic"])
        links.new(normal_tex.outputs["Color"], normal_map.inputs["Color"])
        links.new(normal_map.outputs["Normal"], bsdf.inputs["Normal"])

        if "emissive" in paths:
            emissive = add_image_node(mat, paths["emissive"], "sRGB", (-620, -720))
            if "Emission Color" in bsdf.inputs:
                links.new(emissive.outputs["Color"], bsdf.inputs["Emission Color"])
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = 0.7


def export_outputs() -> None:
    OUTPUT_BLEND.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_BLEND))
    bpy.ops.export_scene.gltf(
        filepath=str(OUTPUT_GLB),
        export_format="GLB",
        export_apply=True,
        export_yup=True,
        export_materials="EXPORT",
    )


def main() -> None:
    if not INPUT_BLEND.exists():
        raise FileNotFoundError(f"Missing sculpt-prep blend: {INPUT_BLEND}")

    print("Penance Carrier v2 UV + texture pass starting...", flush=True)
    bpy.ops.wm.open_mainfile(filepath=str(INPUT_BLEND))
    smart_uv_unwrap()

    all_paths = {}
    for material_name, spec in TEXTURE_SETS.items():
        print("Generating texture set:", spec["prefix"], flush=True)
        all_paths[material_name] = make_texture_set(material_name, spec)

    bind_textures_to_materials(all_paths)
    export_outputs()
    print("Saved textured blend:", OUTPUT_BLEND, flush=True)
    print("Exported textured GLB:", OUTPUT_GLB, flush=True)


if __name__ == "__main__":
    main()
