# Write repo root for ASCII launchers (UTF-8, no corruption)
$Root = Split-Path -Parent $PSScriptRoot
$LocalOps = Join-Path $env:LOCALAPPDATA "YouDingOps"
New-Item -ItemType Directory -Force -Path $LocalOps | Out-Null
$RootFile = Join-Path $LocalOps "repo-root.txt"
[System.IO.File]::WriteAllText($RootFile, $Root.TrimEnd('\'), [System.Text.UTF8Encoding]::new($false))
Write-Output $RootFile
