#Requires -Version 5.1
# Sync dev docs from 上线网站 (dev source) to desktop 出海计 KB
# powershell -ExecutionPolicy Bypass -File scripts/sync-to-chuhaiji-kb.ps1

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot
$KbName   = -join ([char]0x51FA, [char]0x6D77, [char]0x8BA1)
$KbRoot   = Join-Path (Join-Path $env:USERPROFILE 'Desktop') $KbName
$LogFile  = Join-Path $KbRoot 'records\sync-log.txt'

if (-not (Test-Path $RepoRoot)) {
    Write-Error "Dev repo not found: $RepoRoot"
}

foreach ($sub in @('docs', 'records', 'scripts')) {
    $p = Join-Path $KbRoot $sub
    if (-not (Test-Path $p)) { New-Item -ItemType Directory -Force -Path $p | Out-Null }
}

$srcDocs = Join-Path $RepoRoot 'docs'
$dstDocs = Join-Path $KbRoot 'docs'
if (Test-Path $srcDocs) {
    Copy-Item -Path (Join-Path $srcDocs '*') -Destination $dstDocs -Recurse -Force
}

foreach ($f in @('README.md', 'AGENTS.md', 'CLAUDE.md')) {
    $src = Join-Path $RepoRoot $f
    if (Test-Path $src) {
        $name = if ($f -eq 'README.md') { 'README-repo-root.md' } else { $f }
        Copy-Item -Path $src -Destination (Join-Path $dstDocs $name) -Force
    }
}

# 真相源说明（每次同步刷新）
$sourceDoc = Join-Path $RepoRoot 'docs\SOURCE-REPO.md'
if (Test-Path $sourceDoc) {
    Copy-Item -Path $sourceDoc -Destination (Join-Path $dstDocs 'SOURCE-REPO.md') -Force
}

$ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$count = (Get-ChildItem -Path $dstDocs -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count
$line = "[$ts] sync ok | docs files ~ $count | from $RepoRoot (dev source, not CodeBuddy)"
Add-Content -Path $LogFile -Value $line -Encoding UTF8
Write-Host $line
Write-Host "KB: $KbRoot"
