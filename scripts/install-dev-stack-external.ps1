#Requires -Version 5.1
<#
.SYNOPSIS
  Install Cursor/ECC dev tools outside repo; junction-link .cursor.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts/install-dev-stack-external.ps1
  powershell -ExecutionPolicy Bypass -File scripts/install-dev-stack-external.ps1 -InstallEcc
#>
[CmdletBinding()]
param(
    [switch]$InstallEcc,
    [switch]$SkipCodegraph
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
$ConfigPath = Join-Path $RepoRoot '.project\dev-stack.config.json'

if (-not (Test-Path $ConfigPath)) {
    throw "Missing config: $ConfigPath"
}

$config = Get-Content $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
$DevStackRoot = $config.dev_stack_root
$CursorExternal = $config.paths.cursor
$EccSource = $config.ecc_source

function Test-IsJunction([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return $false }
    $item = Get-Item -LiteralPath $Path -Force
    return ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0
}

function Ensure-Dir([string]$Path) {
    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Force -Path $Path | Out-Null
    }
}

Write-Host ''
Write-Host '================================================================' -ForegroundColor Cyan
Write-Host '  Dev-stack external install (isolated from product source)' -ForegroundColor Cyan
Write-Host '================================================================' -ForegroundColor Cyan
Write-Host "  Repo:      $RepoRoot"
Write-Host "  Dev-stack: $DevStackRoot"
Write-Host ''

Ensure-Dir $DevStackRoot
Ensure-Dir $CursorExternal
Ensure-Dir (Join-Path $DevStackRoot 'workflows')

$RepoCursor = Join-Path $RepoRoot '.cursor'
if ((Test-Path -LiteralPath $RepoCursor) -and -not (Test-IsJunction $RepoCursor)) {
    Write-Host '[1/5] Move .cursor to external dev-stack...' -ForegroundColor Yellow
    $extCursorParent = Split-Path -Parent $CursorExternal
    Ensure-Dir $extCursorParent
    if (Test-Path -LiteralPath $CursorExternal) {
        Write-Host '  External .cursor exists; merge children...' -ForegroundColor Gray
        Get-ChildItem -LiteralPath $RepoCursor -Force | ForEach-Object {
            $dest = Join-Path $CursorExternal $_.Name
            if (-not (Test-Path -LiteralPath $dest)) {
                Move-Item -LiteralPath $_.FullName -Destination $CursorExternal -Force
            }
        }
        Remove-Item -LiteralPath $RepoCursor -Recurse -Force
    } else {
        Move-Item -LiteralPath $RepoCursor -Destination $CursorExternal -Force
    }
    Write-Host '  OK: migrated' -ForegroundColor Green
} else {
    Write-Host '[1/5] .cursor already junction or missing; skip migrate' -ForegroundColor Gray
}

Write-Host '[2/5] Create .cursor junction...' -ForegroundColor Yellow
Ensure-Dir $CursorExternal
if (Test-Path -LiteralPath $RepoCursor) {
    if (-not (Test-IsJunction $RepoCursor)) {
        throw ".cursor exists but is not a junction: $RepoCursor"
    }
} else {
    $null = cmd /c "mklink /J `"$RepoCursor`" `"$CursorExternal`""
    if (-not (Test-Path -LiteralPath $RepoCursor)) {
        throw "Junction failed: $RepoCursor -> $CursorExternal"
    }
}
Write-Host "  OK: $RepoCursor -> $CursorExternal" -ForegroundColor Green

Write-Host '[3/5] Sync .project/rules to external .cursor/rules ...' -ForegroundColor Yellow
$ProjectRules = Join-Path $RepoRoot '.project\rules'
$ExternalRules = Join-Path $CursorExternal 'rules'
Ensure-Dir $ExternalRules
if (Test-Path $ProjectRules) {
    Get-ChildItem $ProjectRules -Filter '*.mdc' | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $ExternalRules $_.Name) -Force
    }
}
Write-Host '  OK: rules synced' -ForegroundColor Green

$RepoEccManifest = Join-Path $RepoRoot 'ecc-install.json'
$ExtEccManifest = Join-Path $DevStackRoot 'ecc-install.json'
if (Test-Path -LiteralPath $RepoEccManifest) {
    Move-Item -LiteralPath $RepoEccManifest -Destination $ExtEccManifest -Force -ErrorAction SilentlyContinue
}

if ($InstallEcc) {
    Write-Host '[4/5] Install ECC to external .cursor ...' -ForegroundColor Yellow
    $Installer = Join-Path $EccSource 'scripts\install-apply.js'
    if (-not (Test-Path $Installer)) {
        throw "ECC installer missing: $Installer"
    }
    Push-Location $RepoRoot
    try {
        & node $Installer --target cursor --profile developer
        if ($LASTEXITCODE -ne 0) { throw "ECC install exit $LASTEXITCODE" }
    } finally {
        Pop-Location
    }
    Copy-Item -LiteralPath $ConfigPath -Destination (Join-Path $DevStackRoot 'dev-stack.config.json') -Force
    @{ installed_at = (Get-Date -Format 'o'); source = $EccSource; profile = 'developer' } |
        ConvertTo-Json | Set-Content $ExtEccManifest -Encoding UTF8
    Write-Host '  OK: ECC installed (external manifest)' -ForegroundColor Green
} else {
    Write-Host '[4/5] Skip ECC (use -InstallEcc to install)' -ForegroundColor Gray
}

if (-not $SkipCodegraph) {
    Write-Host '[5/5] CodeGraph local index (gitignored)...' -ForegroundColor Yellow
    $cg = Get-Command codegraph -ErrorAction SilentlyContinue
    if ($cg) {
        Push-Location $RepoRoot
        try {
            if (-not (Test-Path '.codegraph')) {
                & codegraph init -i 2>&1 | Out-Host
            } else {
                & codegraph sync 2>&1 | Out-Host
            }
        } finally {
            Pop-Location
        }
        Write-Host '  OK: .codegraph/ local only (gitignored)' -ForegroundColor Green
    } else {
        Write-Host '  WARN: codegraph CLI not installed' -ForegroundColor Yellow
    }
} else {
    Write-Host '[5/5] Skip CodeGraph' -ForegroundColor Gray
}

Write-Host ''
Write-Host '================================================================' -ForegroundColor Green
Write-Host '  Dev tools isolated from product source.' -ForegroundColor Green
Write-Host '  Verify: scripts/verify-dev-isolation.ps1' -ForegroundColor Green
Write-Host '  Docs:   docs/DEV-TOOLS-ISOLATION.md' -ForegroundColor Green
Write-Host '================================================================' -ForegroundColor Green
Write-Host ''
