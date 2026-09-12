# Provincial software evaluation gate (repo-level)
# Usage: powershell -ExecutionPolicy Bypass -File scripts/run-provincial-cert-gate.ps1

param(
    [switch]$SkipBackendUnit,
    [switch]$SkipMountedRoutes
)

$ErrorActionPreference = 'Continue'
$Root = Split-Path -Parent $PSScriptRoot
$Admin = Join-Path $Root 'frontend\admin'
$Backend = Join-Path $Root 'backend'
$OutJson = Join-Path $Root 'docs\provincial-cert-gate-latest.json'
$fail = 0
$steps = @()

function Add-Step($name, $ok, $detail) {
    if (-not $ok) { $script:fail++ }
    $d = ($detail -as [string]).Trim()
    if ($d.Length -gt 500) { $d = $d.Substring(0, 500) }
    $script:steps += @{ name = $name; ok = [bool]$ok; detail = $d }
    $tag = if ($ok) { 'OK' } else { 'FAIL' }
    $color = if ($ok) { 'Green' } else { 'Red' }
    Write-Host "[$tag] $name" -ForegroundColor $color
}

Write-Host '=== Provincial cert gate scan ===' -ForegroundColor Cyan
Write-Host "Root: $Root"

Push-Location $Admin
$adminOut = npm run cert:gate 2>&1 | Out-String
$adminOk = $LASTEXITCODE -eq 0
Pop-Location
$adminDetail = if ($adminOut -match '"ready":\s*true') { 'ready=true' } else { $adminOut }
Add-Step 'admin-cert-gate' $adminOk $adminDetail

Push-Location $Admin
npm run build 2>&1 | Out-Null
$buildOk = $LASTEXITCODE -eq 0
Pop-Location
Add-Step 'admin-build' $buildOk $(if ($buildOk) { 'vue-tsc + vite build OK' } else { 'build failed' })

if (-not $SkipMountedRoutes) {
    Push-Location $Root
    $mr = python scripts/check_mounted_routes.py 2>&1 | Out-String
    $mrOk = $LASTEXITCODE -eq 0
    Pop-Location
    Add-Step 'mounted-routes' $mrOk $mr
}

if (-not $SkipBackendUnit) {
    Push-Location $Backend
    $ut = python -m pytest tests/unit -q --tb=no 2>&1 | Out-String
    $utOk = $LASTEXITCODE -eq 0
    Pop-Location
    $summary = if ($ut -match '(\d+ passed)') { $Matches[0] } else { $ut }
    Add-Step 'backend-unit' $utOk $summary
}

$report = @{
    generatedAt = (Get-Date).ToString('o')
    target      = 'Provincial software evaluation'
    repoRoot    = $Root
    ready       = ($fail -eq 0)
    failCount   = $fail
    steps       = $steps
    docs        = @(
        'docs/省级软件评测-达标总清单.md',
        'docs/送检功能清单-v1.md',
        'docs/certification-gate-admin-latest.json',
        'docs/申报材料/GB25000.51-合规审查报告-2026-05-31.md'
    )
}

$report | ConvertTo-Json -Depth 6 | Set-Content -Path $OutJson -Encoding UTF8
Write-Host ''
Write-Host "Report: $OutJson" -ForegroundColor Cyan
if ($fail -eq 0) {
    Write-Host 'Overall: READY (engineering gate)' -ForegroundColor Green
} else {
    Write-Host "Overall: BLOCKED ($fail failures)" -ForegroundColor Red
}

exit $fail
