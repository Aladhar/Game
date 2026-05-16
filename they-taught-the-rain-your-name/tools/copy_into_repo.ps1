param(
    [Parameter(Mandatory=$true)]
    [string]$RepoPath
)

$Target = Join-Path $RepoPath "they-taught-the-rain-your-name"
New-Item -ItemType Directory -Force -Path $Target | Out-Null

Get-ChildItem -Path . -Recurse -Force |
    Where-Object { $_.FullName -notmatch "\\.godot\\" } |
    ForEach-Object {
        $Relative = $_.FullName.Substring((Get-Location).Path.Length).TrimStart("\","/")
        $Destination = Join-Path $Target $Relative
        if ($_.PSIsContainer) {
            New-Item -ItemType Directory -Force -Path $Destination | Out-Null
        } else {
            New-Item -ItemType Directory -Force -Path (Split-Path $Destination) | Out-Null
            Copy-Item $_.FullName $Destination -Force
        }
    }

Write-Host "Copied project into: $Target"
