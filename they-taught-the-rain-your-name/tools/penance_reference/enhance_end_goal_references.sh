#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SRC="$ROOT/assets/models/enemies/penance_carrier/Penance_End_Goal.png"
CROP_DIR="$ROOT/assets/models/enemies/penance_carrier/reference_crops"
SWATCH_DIR="$ROOT/assets/textures/enemies/penance_carrier/end_goal_swatches"
FFMPEG="${FFMPEG:-/opt/homebrew/bin/ffmpeg}"

if [[ ! -x "$FFMPEG" ]]; then
  echo "Missing ffmpeg at $FFMPEG" >&2
  exit 1
fi

mkdir -p "$CROP_DIR/enhanced" "$SWATCH_DIR/enhanced"

enhance_crop() {
  local name="$1"
  local out_dir="$2"
  local x="$3"
  local y="$4"
  local w="$5"
  local h="$6"
  local out_w="$7"
  local out_h="$8"
  local denoise="$9"

  "$FFMPEG" -hide_banner -loglevel error -y \
    -i "$SRC" \
    -vf "crop=${w}:${h}:${x}:${y},scale=${out_w}:${out_h}:flags=lanczos${denoise},unsharp=5:5:0.55:3:3:0.18" \
    "$out_dir/${name}.png"
}

# Cleaned orthographic references. These preserve silhouette and reduce blocky pixels.
enhance_crop "front_ortho_clean_x4" "$CROP_DIR/enhanced" 675 32 235 535 940 2140 ",hqdn3d=1.2:1.0:2.0:2.0"
enhance_crop "side_ortho_clean_x4" "$CROP_DIR/enhanced" 900 32 245 535 980 2140 ",hqdn3d=1.2:1.0:2.0:2.0"
enhance_crop "back_ortho_clean_x4" "$CROP_DIR/enhanced" 1138 32 335 535 1340 2140 ",hqdn3d=1.2:1.0:2.0:2.0"

# Detail crops for close lookdev and kitbash modeling.
enhance_crop "detail_shrine_clean_x4" "$CROP_DIR/enhanced" 675 565 330 340 1320 1360 ",hqdn3d=1.0:0.9:1.8:1.8"
enhance_crop "detail_face_mask_clean_x4" "$CROP_DIR/enhanced" 1005 565 220 340 880 1360 ",hqdn3d=1.0:0.9:1.8:1.8"
enhance_crop "detail_sound_relics_clean_x4" "$CROP_DIR/enhanced" 1225 565 260 340 1040 1360 ",hqdn3d=1.0:0.9:1.8:1.8"
enhance_crop "hero_full_left_panel_clean_x2" "$CROP_DIR/enhanced" 0 0 670 1055 1340 2110 ",hqdn3d=1.0:0.9:1.8:1.8"
enhance_crop "material_strip_clean_x4" "$CROP_DIR/enhanced" 680 910 800 125 3200 500 ",hqdn3d=0.8:0.7:1.3:1.3"

# Larger material seeds. These are not final textures; they are cleaned references
# for ArmorPaint/Material Maker/procedural PBR generation.
enhance_crop "soaked_cloth_clean_2k_seed" "$SWATCH_DIR/enhanced" 690 930 78 74 2048 2048 ",hqdn3d=0.7:0.7:1.2:1.2"
enhance_crop "aged_leather_clean_2k_seed" "$SWATCH_DIR/enhanced" 785 930 78 74 2048 2048 ",hqdn3d=0.7:0.7:1.2:1.2"
enhance_crop "rusted_iron_clean_2k_seed" "$SWATCH_DIR/enhanced" 880 930 78 74 2048 2048 ",hqdn3d=0.7:0.7:1.2:1.2"
enhance_crop "weathered_wood_clean_2k_seed" "$SWATCH_DIR/enhanced" 975 930 78 74 2048 2048 ",hqdn3d=0.7:0.7:1.2:1.2"
enhance_crop "wax_candle_clean_2k_seed" "$SWATCH_DIR/enhanced" 1070 930 78 74 2048 2048 ",hqdn3d=0.7:0.7:1.2:1.2"
enhance_crop "old_paper_photos_clean_2k_seed" "$SWATCH_DIR/enhanced" 1165 930 78 74 2048 2048 ",hqdn3d=0.7:0.7:1.2:1.2"
enhance_crop "corroded_brass_clean_2k_seed" "$SWATCH_DIR/enhanced" 1260 930 78 74 2048 2048 ",hqdn3d=0.7:0.7:1.2:1.2"
enhance_crop "glass_lens_clean_2k_seed" "$SWATCH_DIR/enhanced" 1360 930 78 74 2048 2048 ",hqdn3d=0.7:0.7:1.2:1.2"

cat <<EOF
Enhanced end-goal references:
  $CROP_DIR/enhanced
  $SWATCH_DIR/enhanced
EOF
