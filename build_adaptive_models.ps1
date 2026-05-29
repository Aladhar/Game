param(
    [string]$BlenderExe = $env:BLENDER_EXE,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot

if (-not $BlenderExe) {
    $BlenderExe = "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"
}

$Script = "Penance\Scripts\adapt_model_controls_and_walk.py"
$PlayerSource = "Penance\Content\Player\BlenderSource\Player_adaptive.blend"
$PlayerReport = "Penance\Saved\PlayerShapeReport.txt"
$PenanceSource = "Penance\Content\PenanceAssets\Enemies\PenanceCarrier\BlenderSource\Penance_adaptive.blend"
$PenanceReport = "Penance\Saved\PenanceShapeReport.txt"
$OutBlendDir = "Penance\Built\Blender"
$OutFbxDir = "Penance\Built\FBX"
$LogDir = "Penance\Saved\BuildLogs"
$PlayerOut = Join-Path $OutBlendDir "Player_adaptive_BUILT.blend"
$PenanceOut = Join-Path $OutBlendDir "Penance_adaptive_BUILT.blend"
$ExportHelper = Join-Path $LogDir "export_all_meshes_armatures.py"

$RequiredFiles = @($Script, $PlayerSource, $PenanceSource)
foreach ($Path in $RequiredFiles) {
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Required file not found: $Path"
    }
}
if (-not (Test-Path -LiteralPath $BlenderExe)) {
    throw "Blender executable not found: $BlenderExe"
}

if ($DryRun) {
    Write-Host "DRY RUN: would create $OutBlendDir, $OutFbxDir, and $LogDir"
    Write-Host "DRY RUN: would copy $PlayerSource -> $PlayerOut"
    Write-Host "DRY RUN: would copy $PenanceSource -> $PenanceOut"
    Write-Host "DRY RUN: would run Blender build/export steps with $BlenderExe"
    exit 0
}

New-Item -ItemType Directory -Force -Path $OutBlendDir, $OutFbxDir, $LogDir | Out-Null

Copy-Item -LiteralPath $PlayerSource -Destination $PlayerOut -Force
Copy-Item -LiteralPath $PenanceSource -Destination $PenanceOut -Force

@'
import bpy
import os

out = os.environ.get("FBX_OUT")
if not out:
    raise RuntimeError("FBX_OUT environment variable missing")

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
'@ | Set-Content -LiteralPath $ExportHelper -Encoding UTF8

$env:PENANCE_ALLOW_ASSET_WRITE = "1"

Write-Host "Building Player adaptive blend..."
& $BlenderExe --background --python $Script -- player $PlayerOut $PlayerReport 2>&1 |
    Tee-Object -FilePath (Join-Path $LogDir "player_build.log")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Exporting Player FBX..."
$env:FBX_OUT = [System.IO.Path]::GetFullPath((Join-Path $OutFbxDir "SK_Player_Adaptive_BUILT.fbx"))
& $BlenderExe --background $PlayerOut --python $ExportHelper 2>&1 |
    Tee-Object -FilePath (Join-Path $LogDir "player_export.log")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Building Penance adaptive blend..."
& $BlenderExe --background --python $Script -- penance $PenanceOut $PenanceReport 2>&1 |
    Tee-Object -FilePath (Join-Path $LogDir "penance_build.log")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Exporting Penance FBX..."
$env:FBX_OUT = [System.IO.Path]::GetFullPath((Join-Path $OutFbxDir "SK_Penance_Adaptive_BUILT.fbx"))
& $BlenderExe --background $PenanceOut --python $ExportHelper 2>&1 |
    Tee-Object -FilePath (Join-Path $LogDir "penance_export.log")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "DONE."
