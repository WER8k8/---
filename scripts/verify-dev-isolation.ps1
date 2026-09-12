#Requires -Version 5.1
<#
.SYNOPSIS
  Verify dev workspace: production config + dev-tools isolation from product source.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts/verify-dev-isolation.ps1
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Continue'

$RepoRoot = Split-Path -Parent $PSScriptRoot
$issues = @()
$warnings = @()

function Test-EnvFile([string]$Path) {
    if (-not (Test-Path $Path)) { return $null }
    $map = @{}
    Get-Content $Path -Encoding UTF8 | ForEach-Object {
        $line = $_.Trim()
        if ($line -match '^\s*#' -or $line -eq '') { return }
        if ($line -match '^([^=]+)=(.*)$') {
            $map[$Matches[1].Trim()] = $Matches[2].Trim()
        }
    }
    return $map
}

function Test-IsJunction([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return $false }
    try {
        $item = Get-Item -LiteralPath $Path -Force
        return ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0
    } catch {
        return $false
    }
}

function Test-GitTracks([string]$Pattern) {
    Push-Location $RepoRoot
    try {
        $tracked = git ls-files $Pattern 2>$null
        return @($tracked | Where-Object { $_ -and $_.Trim() -ne '' })
    } finally {
        Pop-Location
    }
}

# --- 生产 env 隔离 ---
$prodFiles = @(
    (Join-Path $RepoRoot 'backend\.env.production'),
    (Join-Path $RepoRoot '.env.production'),
    (Join-Path $RepoRoot '.env.prod')
)
foreach ($pf in $prodFiles) {
    if (Test-Path $pf) {
        $warnings += "Production env file present locally (keep on server only): $pf"
    }
}

$rootEnv = Join-Path $RepoRoot '.env'
$envMap = Test-EnvFile $rootEnv
if ($envMap) {
    if ($envMap['ENVIRONMENT'] -eq 'production') {
        $issues += 'Root .env has ENVIRONMENT=production; use development locally'
    }
    $db = $envMap['DATABASE_URL']
    if ($db -and $db -notmatch 'sqlite' -and $db -match 'prod|production|5432') {
        $warnings += "Root .env DATABASE_URL looks like production: $db"
    }
}

$cfgProd = Join-Path $RepoRoot 'backend\config\prod\.env'
if (Test-Path $cfgProd) {
    $pm = Test-EnvFile $cfgProd
    if ($pm -and $pm['ENVIRONMENT'] -eq 'production' -and $pm['DATABASE_URL'] -and $pm['DATABASE_URL'] -notmatch 'DB_|password@|example') {
        $warnings += 'backend/config/prod/.env may contain real production DATABASE_URL'
    }
}

$devDb = Join-Path $RepoRoot 'backend\youding_dev.db'
if (-not (Test-Path $devDb)) {
    $warnings += 'Missing backend/youding_dev.db; run scripts/ensure_dev_sqlite.py'
}

$deployTpl = Join-Path $RepoRoot 'deploy\production\env.template'
if (-not (Test-Path $deployTpl)) {
    $warnings += 'Missing deploy/production/env.template'
}

# --- 开发工具 vs 产品源码隔离 ---
$configPath = Join-Path $RepoRoot '.project\dev-stack.config.json'
if (-not (Test-Path $configPath)) {
    $issues += 'Missing .project/dev-stack.config.json (dev-tools isolation config)'
} else {
    $config = Get-Content $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $devStackRoot = $config.dev_stack_root
    $externalCursor = $config.paths.cursor

    if (-not (Test-Path $devStackRoot)) {
        $warnings += "Dev stack not initialized: $devStackRoot — run scripts/install-dev-stack-external.ps1"
    }

    $repoCursor = Join-Path $RepoRoot '.cursor'
    if (Test-Path -LiteralPath $repoCursor) {
        if (Test-IsJunction $repoCursor) {
            Write-Host "[OK]    .cursor is a junction (dev-tools externalized)" -ForegroundColor DarkGreen
        } else {
            $issues += '.cursor is a real directory inside repo — run scripts/install-dev-stack-external.ps1 to migrate'
        }
    } else {
        $warnings += '.cursor missing — run scripts/install-dev-stack-external.ps1 for Cursor/ECC'
    }

    if ((Test-Path -LiteralPath $externalCursor) -and -not (Test-IsJunction $repoCursor)) {
        $warnings += "External .cursor exists but repo junction missing: $externalCursor"
    }
}

$neverCommit = @('.cursor', '.codegraph', 'ecc-install.json')
foreach ($nc in $neverCommit) {
    $tracked = @(Test-GitTracks $nc)
    foreach ($t in $tracked) {
        $issues += "Dev tool tracked by git (must not commit): $t"
    }
}

$trackedEcc = @(Test-GitTracks 'ecc-install.json')
if ($trackedEcc.Count -gt 0) {
    $issues += 'ecc-install.json is git-tracked — move to dev-stack external'
}

$isoDoc = Join-Path $RepoRoot 'docs\DEV-TOOLS-ISOLATION.md'
if (-not (Test-Path $isoDoc)) {
    $warnings += 'Missing docs/DEV-TOOLS-ISOLATION.md'
}

$projectRule = Join-Path $RepoRoot '.project\rules\00-workspace-isolation.mdc'
if (-not (Test-Path $projectRule)) {
    $issues += 'Missing .project/rules/00-workspace-isolation.mdc'
}

# --- 输出 ---
Write-Host ''
Write-Host '=== Dev / Prod / Dev-Tools isolation check ===' -ForegroundColor Cyan
Write-Host "Repo: $RepoRoot"
Write-Host ''

if ($issues.Count -eq 0 -and $warnings.Count -eq 0) {
    Write-Host 'OK: no isolation issues found.' -ForegroundColor Green
    exit 0
}

foreach ($i in $issues) {
    Write-Host "[ERROR] $i" -ForegroundColor Red
}
foreach ($w in $warnings) {
    Write-Host "[WARN]  $w" -ForegroundColor Yellow
}

Write-Host ''
Write-Host 'See: docs/WORKSPACE-ISOLATION.md + docs/DEV-TOOLS-ISOLATION.md' -ForegroundColor Gray

if ($issues.Count -gt 0) {
    exit 1
}
exit 0
