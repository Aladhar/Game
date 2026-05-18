param(
    [string]$EngineRoot = "C:\Program Files\Epic Games\UE_5.6"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$ProjectFile = Join-Path $ProjectRoot "PenanceDemoUE.uproject"
$Editor = Join-Path $EngineRoot "Engine\Binaries\Win64\UnrealEditor.exe"

if (-not (Test-Path -LiteralPath $Editor -PathType Leaf)) {
    throw "Missing UnrealEditor.exe at $Editor"
}

if (-not (Test-Path -LiteralPath $ProjectFile -PathType Leaf)) {
    throw "Missing project file at $ProjectFile"
}

Start-Process -FilePath $Editor -ArgumentList "`"$ProjectFile`"" -WorkingDirectory $ProjectRoot
