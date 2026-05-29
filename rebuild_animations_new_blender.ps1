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
$LogDir = "Penance\Saved\BuildLogs"
$PlayerOut = Join-Path $OutBlendDir "Player_adaptive_ANIM_REBUILT.blend"
$PenanceOut = Join-Path $OutBlendDir "Penance_adaptive_ANIM_REBUILT.blend"

$RequiredFiles = @($Script, $PlayerSource, $PenanceSource)
foreach ($Path in $RequiredFiles) {
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Required file not found: $Path"
    }
}
if (-not (Test-Path -LiteralPath $BlenderExe)) {
    throw "Blender executable not found: $BlenderExe"
}

Write-Host "Using Blender:"
& $BlenderExe --version
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if ($DryRun) {
    Write-Host "DRY RUN: would create $OutBlendDir and $LogDir"
    Write-Host "DRY RUN: would copy $PlayerSource -> $PlayerOut"
    Write-Host "DRY RUN: would copy $PenanceSource -> $PenanceOut"
    Write-Host "DRY RUN: would rebuild animation controls with $Script"
    exit 0
}

New-Item -ItemType Directory -Force -Path $OutBlendDir, $LogDir | Out-Null
Copy-Item -LiteralPath $PlayerSource -Destination $PlayerOut -Force
Copy-Item -LiteralPath $PenanceSource -Destination $PenanceOut -Force

$env:PENANCE_ALLOW_ASSET_WRITE = "1"

Write-Host "Rebuilding Player animation + adaptive controls..."
& $BlenderExe --background --python $Script -- player $PlayerOut $PlayerReport 2>&1 |
    Tee-Object -FilePath (Join-Path $LogDir "player_anim_rebuild.log")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Rebuilding Penance animation + adaptive controls..."
& $BlenderExe --background --python $Script -- penance $PenanceOut $PenanceReport 2>&1 |
    Tee-Object -FilePath (Join-Path $LogDir "penance_anim_rebuild.log")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "DONE."
Write-Host "Rebuilt Blender files:"
Write-Host "  $PlayerOut"
Write-Host "  $PenanceOut"
