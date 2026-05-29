Write-Host "Checking Penance environment..."

$errors = 0

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Git not found"
    $errors++
}

if (-not (Get-Command git-lfs -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Git LFS not found"
    $errors++
}

$Blender = $env:BLENDER_EXE
if (-not $Blender) {
    $Blender = "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"
}

if (-not (Test-Path $Blender)) {
    Write-Host "ERROR: Blender not found at $Blender"
    $errors++
} else {
    Write-Host "Blender found: $Blender"
}

if (-not (Test-Path "Penance")) {
    Write-Host "ERROR: Penance folder not found"
    $errors++
}

if ($errors -eq 0) {
    Write-Host "Environment check passed."
} else {
    Write-Host "Environment check failed with $errors error(s)."
    exit 1
}
