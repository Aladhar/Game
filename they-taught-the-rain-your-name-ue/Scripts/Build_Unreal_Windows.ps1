param(
    [string]$EngineRoot = "C:\Program Files\Epic Games\UE_5.6",
    [string]$Configuration = "Development",
    [switch]$SkipImport,
    [switch]$SkipPackage
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$ProjectFile = Join-Path $ProjectRoot "PenanceDemoUE.uproject"
$EditorCmd = Join-Path $EngineRoot "Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
$RunUAT = Join-Path $EngineRoot "Engine\Build\BatchFiles\RunUAT.bat"
$ImportScript = Join-Path $ProjectRoot "Scripts\import_penance_blockout.py"
$VerifyScript = Join-Path $ProjectRoot "Scripts\verify_penance_import.py"
$ArchiveDir = Join-Path $ProjectRoot "Builds\Win64"

function Assert-FileExists {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Missing file: $Path"
    }
}

function Assert-DirectoryExists {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
        throw "Missing directory: $Path"
    }
}

function Assert-WithinProject {
    param([string]$Path)
    $resolvedProject = [System.IO.Path]::GetFullPath($ProjectRoot.Path).TrimEnd('\') + '\'
    $resolvedTarget = [System.IO.Path]::GetFullPath($Path)
    if (-not $resolvedTarget.StartsWith($resolvedProject, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to touch path outside project: $resolvedTarget"
    }
}

function Remove-GeneratedImportContent {
    $targets = @(
        (Join-Path $ProjectRoot "Content\Maps\Penance_Suburban_Blockout.umap"),
        (Join-Path $ProjectRoot "Content\PenanceImported")
    )

    foreach ($target in $targets) {
        Assert-WithinProject $target
        if (Test-Path -LiteralPath $target) {
            Write-Host "Removing generated import content: $target"
            Remove-Item -LiteralPath $target -Recurse -Force
        }
    }
}

Assert-DirectoryExists $EngineRoot
Assert-FileExists $EditorCmd
Assert-FileExists $RunUAT
Assert-FileExists $ProjectFile
Assert-FileExists $ImportScript
Assert-FileExists $VerifyScript

if (-not $SkipImport) {
    Remove-GeneratedImportContent

    & $EditorCmd $ProjectFile -run=pythonscript "-script=$ImportScript" -unattended -nop4 -NullRHI -NoSplash -DDC-ForceMemoryCache
    if ($LASTEXITCODE -ne 0) {
        throw "Unreal import failed with exit code $LASTEXITCODE"
    }

    & $EditorCmd $ProjectFile -run=pythonscript "-script=$VerifyScript" -unattended -nop4 -NullRHI -NoSplash -DDC-ForceMemoryCache
    if ($LASTEXITCODE -ne 0) {
        throw "Unreal verification failed with exit code $LASTEXITCODE"
    }
}

if (-not $SkipPackage) {
    Assert-WithinProject $ArchiveDir
    New-Item -ItemType Directory -Force -Path $ArchiveDir | Out-Null

    & $RunUAT BuildCookRun "-project=$ProjectFile" -noP4 -platform=Win64 "-clientconfig=$Configuration" -build -cook -stage -pak -archive "-archivedirectory=$ArchiveDir" -utf8output
    if ($LASTEXITCODE -ne 0) {
        throw "Win64 package failed with exit code $LASTEXITCODE"
    }
}

Write-Host "Unreal rebuild complete."
