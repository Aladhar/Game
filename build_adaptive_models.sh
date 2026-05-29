#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

BLENDER="${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}"
export PENANCE_ALLOW_ASSET_WRITE=1

SCRIPT="Penance/Scripts/adapt_model_controls_and_walk.py"

PLAYER_SRC="Penance/Content/Player/BlenderSource/Player_adaptive.blend"
PLAYER_REPORT="Penance/Saved/PlayerShapeReport.txt"

PENANCE_SRC="Penance/Content/PenanceAssets/Enemies/PenanceCarrier/BlenderSource/Penance_adaptive.blend"
PENANCE_REPORT="Penance/Saved/PenanceShapeReport.txt"

OUT_BLEND_DIR="Penance/Built/Blender"
OUT_FBX_DIR="Penance/Built/FBX"
LOG_DIR="Penance/Saved/BuildLogs"

mkdir -p "$OUT_BLEND_DIR"
mkdir -p "$OUT_FBX_DIR"
mkdir -p "$LOG_DIR"

PLAYER_OUT="$OUT_BLEND_DIR/Player_adaptive_BUILT.blend"
PENANCE_OUT="$OUT_BLEND_DIR/Penance_adaptive_BUILT.blend"

echo "Copying source blend files..."
cp "$PLAYER_SRC" "$PLAYER_OUT"
cp "$PENANCE_SRC" "$PENANCE_OUT"

echo "Creating FBX export helper..."
cat > "$LOG_DIR/export_all_meshes_armatures.py" <<'PY'
import bpy
import os

out = os.environ.get("FBX_OUT")
if not out:
    raise RuntimeError("FBX_OUT environment variable missing")

# Fix old Blender render-engine name if needed.
for scene in bpy.data.scenes:
    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except Exception:
        pass

bpy.ops.object.select_all(action="DESELECT")

selected = []
for obj in bpy.context.scene.objects:
    if obj.type in {"MESH", "ARMATURE"}:
        obj.select_set(True)
        selected.append(obj.name)

armatures = [obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"]
if armatures:
    bpy.context.view_layer.objects.active = armatures[0]

print("Selected for FBX export:", selected)

bpy.ops.export_scene.fbx(
    filepath=out,
    use_selection=True,
    object_types={"ARMATURE", "MESH"},
    apply_unit_scale=True,
    bake_space_transform=False,
    add_leaf_bones=False,
    bake_anim=True,
    bake_anim_use_all_actions=True,
    bake_anim_use_nla_strips=False,
)

print("EXPORTED FBX:", out)
PY

echo "Building Player adaptive blend..."
"$BLENDER" --background \
  --python "$SCRIPT" \
  -- player "$PLAYER_OUT" "$PLAYER_REPORT" \
  2>&1 | tee "$LOG_DIR/player_build.log"

echo "Exporting Player FBX..."
FBX_OUT="$(pwd)/$OUT_FBX_DIR/SK_Player_Adaptive_BUILT.fbx" \
"$BLENDER" --background "$PLAYER_OUT" \
  --python "$LOG_DIR/export_all_meshes_armatures.py" \
  2>&1 | tee "$LOG_DIR/player_export.log"

echo "Building Penance adaptive blend..."
"$BLENDER" --background \
  --python "$SCRIPT" \
  -- penance "$PENANCE_OUT" "$PENANCE_REPORT" \
  2>&1 | tee "$LOG_DIR/penance_build.log"

echo "Exporting Penance FBX..."
FBX_OUT="$(pwd)/$OUT_FBX_DIR/SK_Penance_Adaptive_BUILT.fbx" \
"$BLENDER" --background "$PENANCE_OUT" \
  --python "$LOG_DIR/export_all_meshes_armatures.py" \
  2>&1 | tee "$LOG_DIR/penance_export.log"

echo ""
echo "DONE."
echo "Built blend files:"
echo "  $PLAYER_OUT"
echo "  $PENANCE_OUT"
echo ""
echo "Built FBX files:"
echo "  $OUT_FBX_DIR/SK_Player_Adaptive_BUILT.fbx"
echo "  $OUT_FBX_DIR/SK_Penance_Adaptive_BUILT.fbx"
echo ""
echo "Logs:"
echo "  $LOG_DIR/player_build.log"
echo "  $LOG_DIR/player_export.log"
echo "  $LOG_DIR/penance_build.log"
echo "  $LOG_DIR/penance_export.log"
