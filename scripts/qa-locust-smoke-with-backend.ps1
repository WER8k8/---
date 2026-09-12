# QA-04 · 启动 backend + Locust 冒烟（ARCH-01 通过后可用）
# Usage: powershell -ExecutionPolicy Bypass -File scripts/qa-locust-smoke-with-backend.ps1
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Py = Join-Path $Backend ".venv\Scripts\python.exe"
$secret = "qa-locust-smoke-" + ("x" * 32)

$env:DATABASE_URL = "postgresql://youding:youding@127.0.0.1:5433/youding_dev"
$env:JWT_SECRET_KEY = $secret
$env:SECRET_KEY = $secret
$env:ENVIRONMENT = "development"
$env:REDIS_ENABLED = "false"
$env:PYTHONPATH = $Backend

Write-Host "=== alembic upgrade (QA-04 prep) ===" -ForegroundColor Cyan
Push-Location $Backend
$prevEap = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& $Py -m alembic upgrade head 2>&1 | Out-Null
$alembicExit = $LASTEXITCODE
if ($alembicExit -ne 0) {
  & $Py -m alembic upgrade 028_ubrain_action_audit 2>&1 | Out-Null
}
$ErrorActionPreference = $prevEap
Pop-Location

$proc = Start-Process -FilePath $Py `
  -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8001") `
  -WorkingDirectory $Backend `
  -PassThru `
  -WindowStyle Hidden

$ready = $false
for ($i = 0; $i -lt 60; $i++) {
  try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:8001/api/v1/health" -UseBasicParsing -TimeoutSec 2
    if ($r.StatusCode -eq 200) { $ready = $true; break }
  } catch { Start-Sleep -Seconds 2 }
}

if (-not $ready) {
  Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
  Write-Host "QA-04: backend failed to start on :8001" -ForegroundColor Red
  exit 1
}

& (Join-Path $Root "scripts\qa-locust-smoke.ps1")
$smokeExit = $LASTEXITCODE
Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
exit $smokeExit
