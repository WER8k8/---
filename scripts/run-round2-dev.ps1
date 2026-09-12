# 第二轮研发验收（使用 backend\.venv）
# Usage: powershell -ExecutionPolicy Bypass -File scripts\run-round2-dev.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$VenvPy = Join-Path $Backend ".venv\Scripts\python.exe"
$VenvPip = Join-Path $Backend ".venv\Scripts\pip.exe"

if (-not (Test-Path $VenvPy)) {
    Write-Host "Creating backend\.venv ..." -ForegroundColor Cyan
    python -m venv (Join-Path $Backend ".venv")
}

$env:PYTHONPATH = $Backend
$env:DATABASE_URL = "sqlite:///./youding_dev.db"
$env:JWT_SECRET_KEY = "checklist-" + ("x" * 32)
$env:FOUNDER_DEBUG_TOKEN = "checklist-founder-dev"
$env:SMOKE_BASE = "http://127.0.0.1:8001"

Write-Host "=== pip install requirements ===" -ForegroundColor Cyan
& $VenvPy -m pip install --upgrade pip -q
& $VenvPy -m pip uninstall -y langchain 2>$null | Out-Null
& $VenvPy -m pip install -r (Join-Path $Backend "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "pip install requirements failed" }

Write-Host "`n=== apply-security (audit + smoke) ===" -ForegroundColor Cyan
& $VenvPy -m pip install pip-audit -q 2>$null
& $VenvPy (Join-Path $Root "scripts\run_security_audit.py")

Push-Location $Backend
$env:ENVIRONMENT = "testing"
& $VenvPy -m pytest tests/unit/test_auth.py tests/unit/test_flywheel_d2_d6_api.py tests/unit/test_audit_user_resolution.py -q --tb=short
if ($LASTEXITCODE -ne 0) { Pop-Location; exit $LASTEXITCODE }

& $VenvPy scripts\ensure_dev_sqlite.py
& $VenvPy scripts\seed_platforms_full.py
Pop-Location

Write-Host "`n=== demo + preflight (dev) ===" -ForegroundColor Cyan
& $VenvPy (Join-Path $Root "scripts\check_mounted_routes.py")
& $VenvPy (Join-Path $Root "scripts\run_demo_acceptance.py")
& $VenvPy (Join-Path $Root "scripts\run_production_preflight.py")

Write-Host "`n=== full-checklist ===" -ForegroundColor Cyan
# 子进程用系统 python 起 uvicorn；清单内 pytest 仍走 backend 目录
$env:Path = "$(Split-Path $VenvPy);$env:Path"
powershell -ExecutionPolicy Bypass -File (Join-Path $Root "scripts\run-full-checklist.ps1") -SkipUnitTests

Write-Host "`nOK: round2 dev automation finished" -ForegroundColor Green
