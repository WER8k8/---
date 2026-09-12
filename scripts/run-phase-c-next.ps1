# Phase C 一键顺序执行（研发侧）
# Usage: powershell -ExecutionPolicy Bypass -File scripts/run-phase-c-next.ps1
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Py = Join-Path $Root "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $Py)) { $Py = "python" }

Write-Host "=== 1/4 hierarchy + aggregation acceptance ===" -ForegroundColor Cyan
& $Py (Join-Path $Root "scripts\run-hierarchy-browser-acceptance.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "=== 2/4 staging preflight auto ===" -ForegroundColor Cyan
& (Join-Path $Root "scripts\run-staging-preflight-auto.ps1")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "=== 3/4 reliability smoke (~5 min) ===" -ForegroundColor Cyan
& $Py (Join-Path $Root "scripts\run-reliability-smoke.py")

Write-Host "=== 4/4 locust light (50 users, 30s) ===" -ForegroundColor Cyan
Push-Location $Root
& $Py (Join-Path $Root "scripts\load_test.py") --url "http://127.0.0.1:8001" --users 50 --duration 30s --qps 200
Pop-Location

Write-Host "`nPhase C engineering batch done. See docs/phase-c-progress-latest.json" -ForegroundColor Green
