param(
    [string]$UnrealRoot = $env:UE_5_7_ROOT,
    [string]$BlenderExe = $env:BLENDER_EXE,
    [switch]$SkipVersionLaunch
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RequiredUnrealVersion = [version]"5.7.4"
$RequiredBlenderMajorMinor = "5.1"
$MinimumWindows11Build = 22000
$errors = New-Object System.Collections.Generic.List[string]
$warnings = New-Object System.Collections.Generic.List[string]

function Add-ErrorMessage {
    param([string]$Message)
    $errors.Add($Message)
    Write-Host "ERROR: $Message" -ForegroundColor Red
}

function Add-WarningMessage {
    param([string]$Message)
    $warnings.Add($Message)
    Write-Host "WARN: $Message" -ForegroundColor Yellow
}

function Test-CommandAvailable {
    param([string]$Name)
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $command) {
        Add-ErrorMessage "$Name not found on PATH"
        return $null
    }
    Write-Host "$Name found: $($command.Source)"
    return $command
}

function Resolve-UnrealRoot {
    param([string]$ConfiguredRoot)
    if ($ConfiguredRoot) {
        return $ConfiguredRoot
    }

    $defaultRoot = "C:\Program Files\Epic Games\UE_5.7"
    if (Test-Path -LiteralPath $defaultRoot) {
        return $defaultRoot
    }

    return $null
}

function Test-UnrealVersion {
    param([string]$Root)
    if (-not $Root) {
        Add-ErrorMessage "Unreal Engine root not configured. Set UE_5_7_ROOT to the UE 5.7.4 install path."
        return
    }
    if (-not (Test-Path -LiteralPath $Root)) {
        Add-ErrorMessage "Unreal Engine root does not exist: $Root"
        return
    }

    $buildVersionPath = Join-Path $Root "Engine\Build\Build.version"
    if (-not (Test-Path -LiteralPath $buildVersionPath)) {
        Add-WarningMessage "Could not find Build.version under Unreal root: $buildVersionPath"
        return
    }

    $buildVersion = Get-Content -LiteralPath $buildVersionPath -Raw | ConvertFrom-Json
    $actual = [version]"$($buildVersion.MajorVersion).$($buildVersion.MinorVersion).$($buildVersion.PatchVersion)"
    if ($actual -ne $RequiredUnrealVersion) {
        Add-ErrorMessage "Unreal Engine version is $actual, expected $RequiredUnrealVersion"
        return
    }
    Write-Host "Unreal Engine version OK: $actual"
}

function Test-UnrealWindowsTools {
    param([string]$Root)
    if (-not $Root -or -not (Test-Path -LiteralPath $Root)) {
        return
    }

    $requiredToolPaths = @(
        "Engine\Binaries\Win64\UnrealEditor-Cmd.exe",
        "Engine\Binaries\DotNET\UnrealBuildTool\UnrealBuildTool.dll",
        "Engine\Build\BatchFiles\Build.bat",
        "Engine\Build\BatchFiles\RunUAT.bat"
    )

    foreach ($relativePath in $requiredToolPaths) {
        $toolPath = Join-Path $Root $relativePath
        if (Test-Path -LiteralPath $toolPath) {
            Write-Host "Unreal Windows tool found: $relativePath"
        } else {
            Add-ErrorMessage "Missing Unreal Windows tool: $toolPath"
        }
    }
}

function Test-BlenderVersion {
    param([string]$ConfiguredExe)
    $exe = $ConfiguredExe
    if (-not $exe) {
        $exe = "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"
    }
    if (-not (Test-Path -LiteralPath $exe)) {
        Add-ErrorMessage "Blender not found at $exe. Set BLENDER_EXE to the Blender 5.1 executable."
        return
    }

    Write-Host "Blender found: $exe"
    if ($SkipVersionLaunch) {
        Add-WarningMessage "Skipped Blender version launch check."
        return
    }

    $versionOutputLines = & $exe --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Add-ErrorMessage "Blender --version failed with exit code $LASTEXITCODE"
        return
    }
    $versionOutput = $versionOutputLines | Select-Object -First 1
    if ($versionOutput -notmatch "Blender\s+$RequiredBlenderMajorMinor(\.|\\s)") {
        Add-ErrorMessage "Blender version output was '$versionOutput', expected Blender $RequiredBlenderMajorMinor.x"
        return
    }
    Write-Host "Blender version OK: $versionOutput"
}

function Test-VisualStudio2022 {
    $vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
    if (-not (Test-Path -LiteralPath $vswhere)) {
        Add-ErrorMessage "vswhere.exe not found. Install Visual Studio 2022 with C++ game development workloads."
        return
    }

    $installPath = & $vswhere -latest -products * -version "[17.0,18.0)" -requires Microsoft.VisualStudio.Workload.NativeGame -property installationPath
    if ($LASTEXITCODE -ne 0 -or -not $installPath) {
        Add-ErrorMessage "Visual Studio 2022 Native Game workload not found."
        return
    }
    Write-Host "Visual Studio 2022 Native Game workload found: $installPath"
}

Write-Host "Checking Penance Windows-first environment..."

$osVersion = [Environment]::OSVersion.Version
if ($osVersion.Build -lt $MinimumWindows11Build) {
    Add-ErrorMessage "Windows build $($osVersion.Build) detected, expected Windows 11 build $MinimumWindows11Build or newer."
} else {
    Write-Host "Windows build OK: $($osVersion.Build)"
}

Test-CommandAvailable "git" | Out-Null
Test-CommandAvailable "git-lfs" | Out-Null

if (-not (Test-Path -LiteralPath "Penance\PenanceDemoUE.uproject")) {
    Add-ErrorMessage "Penance\PenanceDemoUE.uproject not found. Run this script from the repository root."
} else {
    $project = Get-Content -LiteralPath "Penance\PenanceDemoUE.uproject" -Raw | ConvertFrom-Json
    if ($project.EngineAssociation -ne "5.7") {
        Add-ErrorMessage "PenanceDemoUE.uproject EngineAssociation is '$($project.EngineAssociation)', expected '5.7'."
    } else {
        Write-Host "Project EngineAssociation OK: $($project.EngineAssociation)"
    }
}

$resolvedUnrealRoot = Resolve-UnrealRoot $UnrealRoot
Test-UnrealVersion $resolvedUnrealRoot
Test-UnrealWindowsTools $resolvedUnrealRoot
Test-BlenderVersion $BlenderExe
Test-VisualStudio2022

if ($errors.Count -eq 0) {
    Write-Host "Environment check passed with $($warnings.Count) warning(s)." -ForegroundColor Green
    exit 0
}

Write-Host "Environment check failed with $($errors.Count) error(s) and $($warnings.Count) warning(s)." -ForegroundColor Red
exit 1
