#!/bin/zsh
set -euo pipefail

cd "/Users/amritladhar/Documents/GitHub/Game"

BLENDER="/Applications/Blender.app/Contents/MacOS/Blender"

SCRIPT="Penance/Scripts/adapt_model_controls_and_walk.py"

PLAYER_SRC="Penance/Content/Player/BlenderSource/Player_adaptive.blend"
PLAYER_REPORT="Penance/Saved/PlayerShapeReport.txt"

PENANCE_SRC="Penance/Content/PenanceAssets/Enemies/PenanceCarrier/BlenderSource/Penance_adaptive.blend"
PENANCE_REPORT="Penance/Saved/PenanceShapeReport.txt"

OUT_BLEND_DIR="Penance/Built/Blender"
LOG_DIR="Penance/Saved/BuildLogs"

mkdir -p "$OUT_BLEND_DIR"
mkdir -p "$LOG_DIR"

PLAYER_OUT="$OUT_BLEND_DIR/Player_adaptive_ANIM_REBUILT.blend"
PENANCE_OUT="$OUT_BLEND_DIR/Penance_adaptive_ANIM_REBUILT.blend"

echo "Using Blender:"
"$BLENDER" --version

echo ""
echo "Copying source .blend files..."
cp "$PLAYER_SRC" "$PLAYER_OUT"
cp "$PENANCE_SRC" "$PENANCE_OUT"

echo ""
echo "Rebuilding Player animation + adaptive controls..."
"$BLENDER" --background \
  --python "$SCRIPT" \
  -- player "$PLAYER_OUT" "$PLAYER_REPORT" \
  2>&1 | tee "$LOG_DIR/player_anim_rebuild.log"

echo ""
echo "Rebuilding Penance animation + adaptive controls..."
"$BLENDER" --background \
  --python "$SCRIPT" \
  -- penance "$PENANCE_OUT" "$PENANCE_REPORT" \
  2>&1 | tee "$LOG_DIR/penance_anim_rebuild.log"

echo ""
echo "DONE."
echo "Open these rebuilt Blender files:"
echo "  $PLAYER_OUT"
echo "  $PENANCE_OUT"
echo ""
echo "Logs:"
echo "  $LOG_DIR/player_anim_rebuild.log"
echo "  $LOG_DIR/penance_anim_rebuild.log"
