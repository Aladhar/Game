#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SRC="$ROOT/assets/models/enemies/penance_carrier/Penance_End_Goal.png"
CROP_DIR="$ROOT/assets/models/enemies/penance_carrier/reference_crops"
SWATCH_DIR="$ROOT/assets/textures/enemies/penance_carrier/end_goal_swatches"

mkdir -p "$CROP_DIR" "$SWATCH_DIR"

crop_upscale() {
  local name="$1"
  local out_dir="$2"
  local x="$3"
  local y="$4"
  local w="$5"
  local h="$6"
  local out_w="$7"
  local out_h="$8"
  local tmp
  tmp="$(mktemp "/private/tmp/${name}.XXXXXX.png")"

  # sips uses crop offset as y, x. We crop first, then upscale to a stable
  # reference size so Blender planes and material tools use clean inputs.
  sips --cropToHeightWidth "$h" "$w" --cropOffset "$y" "$x" "$SRC" --out "$tmp" >/dev/null
  sips --resampleHeightWidth "$out_h" "$out_w" "$tmp" --out "$out_dir/${name}.png" >/dev/null
  rm -f "$tmp"
}

# Orthographic references from the top-right sheet area.
crop_upscale "front_ortho_x4" "$CROP_DIR" 675 32 235 535 940 2140
crop_upscale "side_ortho_x4" "$CROP_DIR" 900 32 245 535 980 2140
crop_upscale "back_ortho_x4" "$CROP_DIR" 1138 32 335 535 1340 2140

# Detail crops used for face, shrine clutter, and kitbash prop modeling.
crop_upscale "detail_shrine_x4" "$CROP_DIR" 675 565 330 340 1320 1360
crop_upscale "detail_face_mask_x4" "$CROP_DIR" 1005 565 220 340 880 1360
crop_upscale "detail_sound_relics_x4" "$CROP_DIR" 1225 565 260 340 1040 1360
crop_upscale "hero_full_left_panel_x2" "$CROP_DIR" 0 0 670 1055 1340 2110
crop_upscale "material_strip_x4" "$CROP_DIR" 680 910 800 125 3200 500

# Bottom-row material swatches. The sheet labels are preserved in the filenames.
crop_upscale "soaked_cloth_8k_seed" "$SWATCH_DIR" 690 930 78 74 1024 1024
crop_upscale "aged_leather_8k_seed" "$SWATCH_DIR" 785 930 78 74 1024 1024
crop_upscale "rusted_iron_8k_seed" "$SWATCH_DIR" 880 930 78 74 1024 1024
crop_upscale "weathered_wood_8k_seed" "$SWATCH_DIR" 975 930 78 74 1024 1024
crop_upscale "wax_candle_8k_seed" "$SWATCH_DIR" 1070 930 78 74 1024 1024
crop_upscale "old_paper_photos_8k_seed" "$SWATCH_DIR" 1165 930 78 74 1024 1024
crop_upscale "corroded_brass_8k_seed" "$SWATCH_DIR" 1260 930 78 74 1024 1024
crop_upscale "glass_lens_8k_seed" "$SWATCH_DIR" 1360 930 78 74 1024 1024

cat <<EOF
Extracted end-goal references:
  $CROP_DIR
  $SWATCH_DIR
EOF
