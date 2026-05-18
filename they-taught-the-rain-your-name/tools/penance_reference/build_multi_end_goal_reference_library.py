#!/usr/bin/env python3
"""
Build an organized multi-sheet Penance Carrier reference library.

Input:
  assets/models/enemies/penance_carrier/End_Goal/*.png

Output:
  assets/models/enemies/penance_carrier/reference_crops/end_goal_multi_region/

The source sheets include repeated duplicates. This script keeps one canonical
copy for each useful labeled region and crops/upscales them into folders named
for the modeling area they drive: orthographic, hero_views, face_mask,
shrine_roof, back_structure, chains_bells, limbs_feet, materials, and full_sheets.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter


ROOT = Path(__file__).resolve().parents[2]
ASSET_ROOT = ROOT / "assets/models/enemies/penance_carrier"
SOURCE_DIR = ASSET_ROOT / "End_Goal"
OUT_ROOT = ASSET_ROOT / "reference_crops/end_goal_multi_region"


@dataclass(frozen=True)
class CropSpec:
    source: str
    category: str
    name: str
    box: tuple[int, int, int, int]
    out_size: tuple[int, int]
    notes: str


SOURCES = {
    "master_sheet": "Penance_End_Goal.png",
    "front_ortho": "ChatGPT Image May 17, 2026 at 01_23_29 PM (1).png",
    "back_ortho": "Penance .png",
    "left_side": "ChatGPT Image May 17, 2026 at 01_23_30 PM (3).png",
    "right_side": "ChatGPT Image May 17, 2026 at 01_23_30 PM (4).png",
    "front_right": "ChatGPT Image May 17, 2026 at 01_23_31 PM (5).png",
    "rear_left": "ChatGPT Image May 17, 2026 at 01_20_36 PM (6).png",
}


CROPS: list[CropSpec] = [
    # Full orthographic and hero sheets.
    CropSpec("front_ortho", "orthographic/front", "front_orthographic_full_body_x4", (285, 25, 560, 1030), (2240, 4120), "Primary front silhouette: head/mask, shoulders, arms, legs, bell."),
    CropSpec("back_ortho", "orthographic/back", "back_orthographic_full_body_x4", (325, 25, 520, 1030), (2080, 4120), "Primary back silhouette and rear hanging mass."),
    CropSpec("left_side", "orthographic/left_side", "left_side_full_body_x4", (260, 35, 475, 1015), (1900, 4060), "Left side depth, hunched posture, mask projection, foot profile."),
    CropSpec("right_side", "orthographic/right_side", "right_side_full_body_x4", (250, 35, 620, 1015), (2480, 4060), "Right side depth, shrine overhang, hand bell position."),
    CropSpec("front_right", "hero_views/front_right", "front_right_three_quarter_full_x3", (245, 40, 590, 1015), (1770, 3045), "Front-right hero read with mask and arms."),
    CropSpec("rear_left", "hero_views/rear_left", "rear_left_three_quarter_full_x3", (205, 35, 520, 1015), (1560, 3045), "Rear-left hero read with back shrine and dangling relics."),
    CropSpec("master_sheet", "overview", "legacy_master_overview_full", (0, 0, 1491, 1055), (1491, 1055), "Original all-in-one target sheet for broad mood comparison."),

    # Front sheet details.
    CropSpec("front_ortho", "face_mask", "front_face_door_mask_detail_x4", (890, 35, 245, 375), (980, 1500), "Front face/door mask, black opening, hood rim, wooden planks."),
    CropSpec("front_ortho", "shrine_front", "front_chest_shrine_harness_x4", (1145, 35, 275, 375), (1100, 1500), "Chest/shrine harness load above shoulders."),
    CropSpec("front_ortho", "hands_bell", "front_hand_bell_chain_detail_x4", (890, 425, 245, 320), (980, 1280), "Left hand, chain grip, hero bell."),
    CropSpec("front_ortho", "shrine_front", "front_relic_cluster_detail_x4", (1145, 425, 275, 320), (1100, 1280), "Front radios, photos, bells, candles, and relic placement."),
    CropSpec("front_ortho", "limbs_feet", "front_foot_wrapping_toes_x4", (890, 760, 245, 275), (980, 1100), "Front foot toes, leather/cloth wrapping, wet ground contact."),
    CropSpec("front_ortho", "chains_bells", "front_bell_chain_variants_x4", (1145, 760, 275, 275), (1100, 1100), "Bell and chain silhouette variants."),

    # Back sheet details.
    CropSpec("back_ortho", "shrine_roof", "back_roof_upper_shrine_detail_x4", (845, 35, 285, 380), (1140, 1520), "Rear roof ridge, crosses, chain density."),
    CropSpec("back_ortho", "back_structure", "back_shrine_rear_attachments_x4", (1140, 35, 285, 380), (1140, 1520), "Rear radios, portraits, speaker clusters, candles."),
    CropSpec("back_ortho", "chains_bells", "back_chain_relic_clusters_x4", (845, 430, 580, 220), (2320, 880), "Rear chain and bell cluster rhythm."),
    CropSpec("back_ortho", "back_structure", "lower_back_drapery_structure_x4", (845, 665, 580, 365), (2320, 1460), "Lower rear drapery, rotten hanging mass, leg separation."),

    # Left-side details.
    CropSpec("left_side", "side_transition", "left_shoulder_back_transition_x4", (775, 82, 335, 365), (1340, 1460), "Left shoulder compressed under shrine load."),
    CropSpec("left_side", "face_mask", "left_mask_head_side_detail_x4", (1122, 82, 290, 365), (1160, 1460), "Mask/head side projection and rag falloff."),
    CropSpec("left_side", "limbs_feet", "left_arm_wrapping_hand_detail_x4", (775, 475, 245, 300), (980, 1200), "Left arm wrap, knuckles, hanging relics."),
    CropSpec("left_side", "chains_bells", "left_chain_bell_arrangement_x4", (1030, 475, 355, 300), (1420, 1200), "Left side chain and bell drape lengths."),
    CropSpec("left_side", "limbs_feet", "left_leg_foot_profile_x4", (775, 810, 370, 220), (1480, 880), "Left foot side profile and splayed toes."),

    # Right-side details.
    CropSpec("right_side", "side_transition", "right_shoulder_shrine_transition_x4", (910, 70, 280, 450), (1120, 1800), "Right shoulder/shrine transition and side mass."),
    CropSpec("right_side", "face_mask", "right_mask_side_profile_x4", (1190, 70, 245, 450), (980, 1800), "Right mask side profile and vertical wood falloff."),
    CropSpec("right_side", "limbs_feet", "right_arm_wrapping_relics_x4", (910, 550, 245, 225), (980, 900), "Right arm wrapping and nearby bells."),
    CropSpec("right_side", "limbs_feet", "right_foot_side_profile_x4", (1190, 550, 245, 225), (980, 900), "Right foot side profile, toes, wrapped ankle."),
    CropSpec("right_side", "overview", "right_side_scale_guide_x4", (910, 810, 500, 240), (2000, 960), "Scale guide and full side mini read."),

    # Front-right detail sheet.
    CropSpec("front_right", "face_mask", "front_right_face_mask_detail_x4", (840, 45, 300, 390), (1200, 1560), "Front-right face/mask detail and hood material layering."),
    CropSpec("front_right", "face_mask", "front_right_face_opening_x4", (1160, 45, 260, 390), (1040, 1560), "Deep black face opening, hanging inner relic, mask planks."),
    CropSpec("front_right", "shrine_front", "front_right_chest_harness_relics_x4", (840, 470, 300, 240), (1200, 960), "Chest harness and relic anchors over shoulders."),
    CropSpec("front_right", "chains_bells", "front_right_dangling_bell_chains_x4", (1160, 470, 260, 240), (1040, 960), "Dangling bell chains near right/front side."),
    CropSpec("front_right", "shrine_front", "front_right_shrine_corner_x4", (840, 750, 580, 280), (2320, 1120), "Front-right shrine corner density and roof-to-wall transition."),

    # Rear-left detail sheet.
    CropSpec("rear_left", "shrine_roof", "rear_left_roof_ridge_crosses_x4", (735, 35, 345, 330), (1380, 1320), "Roof ridge, shingles, crosses, hanging chains."),
    CropSpec("rear_left", "back_structure", "rear_left_structure_overview_x4", (1090, 35, 330, 330), (1320, 1320), "Rear structure overview and side attachments."),
    CropSpec("rear_left", "chains_bells", "rear_chain_clusters_x4", (735, 380, 345, 285), (1380, 1140), "Rear chain clusters and bell depth."),
    CropSpec("rear_left", "shrine_side", "side_relic_bundles_x4", (1090, 380, 330, 285), (1320, 1140), "Side relic bundles, radios, portraits, candle glow."),
    CropSpec("rear_left", "limbs_feet", "rear_leg_foot_wrapping_x4", (735, 700, 345, 210), (1380, 840), "Rear leg/foot wrap texture and silhouette."),
    CropSpec("rear_left", "chains_bells", "lower_rear_hanging_bells_relics_x4", (1090, 700, 330, 210), (1320, 840), "Lower rear bells and dangling relic endings."),
    CropSpec("rear_left", "materials", "rear_left_material_strip_x4", (735, 940, 680, 95), (2720, 380), "Material swatches from rear-left sheet."),
]


def safe_name(name: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in name)


def load_source(key: str) -> Image.Image:
    path = SOURCE_DIR / SOURCES[key]
    if not path.exists():
        raise FileNotFoundError(path)
    return Image.open(path).convert("RGB")


def enhance(img: Image.Image) -> Image.Image:
    img = ImageEnhance.Contrast(img).enhance(1.04)
    img = ImageEnhance.Sharpness(img).enhance(1.18)
    return img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=85, threshold=3))


def crop_and_save(spec: CropSpec) -> dict[str, object]:
    src = load_source(spec.source)
    x, y, w, h = spec.box
    cropped = src.crop((x, y, x + w, y + h))
    cropped = cropped.resize(spec.out_size, Image.Resampling.LANCZOS)
    cropped = enhance(cropped)
    out_dir = OUT_ROOT / spec.category
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{spec.name}.png"
    cropped.save(out, optimize=True)
    entry = asdict(spec)
    entry["output"] = str(out.relative_to(ROOT))
    entry["source_path"] = str((SOURCE_DIR / SOURCES[spec.source]).relative_to(ROOT))
    return entry


def copy_full_sheets() -> list[dict[str, str]]:
    out_dir = OUT_ROOT / "full_sheets"
    out_dir.mkdir(parents=True, exist_ok=True)
    copied: list[dict[str, str]] = []
    for key, filename in SOURCES.items():
        src = SOURCE_DIR / filename
        out = out_dir / f"{key}_{safe_name(filename)}"
        shutil.copy2(src, out)
        copied.append({"key": key, "source": str(src.relative_to(ROOT)), "output": str(out.relative_to(ROOT))})
    return copied


def write_index(entries: list[dict[str, object]], full_sheets: list[dict[str, str]]) -> None:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    data = {
        "purpose": "Multi-sheet Penance Carrier reference baseline organized by modeling region.",
        "source_folder": str(SOURCE_DIR.relative_to(ROOT)),
        "notes": [
            "Use orthographic/front as the main front silhouette target.",
            "Use orthographic/back plus back_structure for disgusting rear mass and drapery.",
            "Use left_side/right_side crops for depth and mask projection.",
            "Use face_mask, chains_bells, shrine_front, shrine_roof, and limbs_feet as detail targets.",
            "Duplicate source sheets are intentionally collapsed to canonical sources.",
        ],
        "full_sheets": full_sheets,
        "crops": entries,
    }
    (OUT_ROOT / "index.json").write_text(json.dumps(data, indent=2), encoding="utf-8")

    lines = [
        "# Penance Carrier Multi-Region End Goal Reference",
        "",
        "This folder is generated from `assets/models/enemies/penance_carrier/End_Goal`.",
        "It replaces the older single-sheet-only reference baseline for new Penance Carrier V passes.",
        "",
        "## Region Folders",
        "",
    ]
    for category in sorted({entry["category"] for entry in entries}):
        lines.append(f"- `{category}`")
    lines += ["", "## Key Modeling Targets", ""]
    lines += [
        "- Front silhouette: `orthographic/front/front_orthographic_full_body_x4.png`",
        "- Back silhouette: `orthographic/back/back_orthographic_full_body_x4.png`",
        "- Side depth: `orthographic/left_side/left_side_full_body_x4.png` and `orthographic/right_side/right_side_full_body_x4.png`",
        "- Face and mask: `face_mask/*`",
        "- Shrine/clutter: `shrine_front/*`, `shrine_roof/*`, `shrine_side/*`, `back_structure/*`",
        "- Chains/bells: `chains_bells/*`",
        "- Feet/limbs: `limbs_feet/*`",
    ]
    (OUT_ROOT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    if not SOURCE_DIR.exists():
        raise FileNotFoundError(SOURCE_DIR)
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    entries = [crop_and_save(spec) for spec in CROPS]
    full_sheets = copy_full_sheets()
    write_index(entries, full_sheets)
    print(f"Wrote {len(entries)} organized region crops to {OUT_ROOT}")
    print(f"Wrote {len(full_sheets)} canonical full sheets to {OUT_ROOT / 'full_sheets'}")


if __name__ == "__main__":
    main()
