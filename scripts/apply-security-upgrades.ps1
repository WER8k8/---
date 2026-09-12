# P0 安全依赖升级后验收
# Usage: powershell -ExecutionPolicy Bypass -File scripts/apply-security-upgrades.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"

Write-Host "=== Install upgraded requirements ===" -ForegroundColor Cyan
Push-Location $Backend
$env:PYTHONPATH = (Get-Location).Path
python -m pip install --upgrade pip
python -m pip uninstall -y langchain 2>$null
python -m pip install -r requirements.txt
Pop-Location

Write-Host "`n=== pip-audit ===" -ForegroundColor Cyan
python -m pip install pip-audit -q 2>$null
python (Join-Path $Root "scripts\run_security_audit.py")

Write-Host "`n=== Quick unit smoke ===" -ForegroundColor Cyan
Push-Location $Backend
$env:ENVIRONMENT = "testing"
python -m pytest tests/unit/test_auth.py tests/unit/test_flywheel_d2_d6_api.py tests/unit/test_audit_user_resolution.py -q --tb=short
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Pop-Location

Write-Host "`nOK: security upgrade path finished. See docs/security-audit-latest.md" -ForegroundColor Green
