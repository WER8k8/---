# 专家团 P0 #1/#3：预发 Postgres + Redis + migrate + 生产 preflight
# 用法: powershell -ExecutionPolicy Bypass -File scripts/run-staging-preflight.ps1
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Py = Join-Path $Backend ".venv\Scripts\python.exe"
if (-not (Test-Path $Py)) { $Py = "python" }

function Test-HttpUp([string]$Url, [int]$Sec = 3) {
  try { Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $Sec | Out-Null; return $true } catch { return $false }
}

Write-Host "=== 1/5 docker compose: postgres + redis（藏云阁镜像） ===" -ForegroundColor Cyan
Push-Location $Root
& (Join-Path $Root "scripts/docker-with-cncfstack.ps1") -Profile dev up -d postgres redis
Pop-Location

$deadline = (Get-Date).AddSeconds(90)
while ((Get-Date) -lt $deadline) {
  if ((Test-HttpUp "http://127.0.0.1:5433" 2) -or (docker exec youding-dev-postgres pg_isready -U youding -d youding_dev 2>$null)) { break }
  Start-Sleep -Seconds 2
}

$pgUrl = "postgresql://youding:youding@127.0.0.1:5433/youding_dev"
$redisUrl = "redis://127.0.0.1:6379/0"

Write-Host "=== 2/5 alembic upgrade head (Postgres) ===" -ForegroundColor Cyan
Push-Location $Backend
$env:DATABASE_URL = $pgUrl
$env:PYTHONPATH = (Get-Location).Path
& $Py -m alembic upgrade head
if ($LASTEXITCODE -ne 0) {
  Write-Host "WARN: full head failed; trying flywheel 028" -ForegroundColor Yellow
  & $Py -m alembic upgrade 028_ubrain_action_audit
}
Pop-Location

Write-Host "=== 3/5 seed platforms ===" -ForegroundColor Cyan
Push-Location $Backend
$env:DATABASE_URL = $pgUrl
$env:PYTHONPATH = (Get-Location).Path
& $Py scripts/seed_platforms_full.py
Pop-Location

Write-Host "=== 4/5 production preflight (--production) ===" -ForegroundColor Cyan
$env:ENVIRONMENT = "production"
$env:DATABASE_URL = $pgUrl
$env:MVP_LAUNCH = "1"
$env:PAYMENT_STRICT_VERIFY = "1"
$env:SSL_PROVIDER = "certbot"
$env:CERTBOT_EMAIL = if ($env:CERTBOT_EMAIL) { $env:CERTBOT_EMAIL } else { "staging-preflight@demo.youding.local" }
$env:REDIS_ENABLED = "true"
$env:REDIS_URL = $redisUrl
$env:CELERY_BROKER_URL = $redisUrl
$env:FRONTEND_URL = "https://demo.youding.local"
$env:JWT_SECRET_KEY = if ($env:JWT_SECRET_KEY) { $env:JWT_SECRET_KEY } else { "staging-preflight-" + ("x" * 16) }
$env:SECRET_KEY = $env:JWT_SECRET_KEY

& $Py (Join-Path $Root "scripts\run_production_preflight.py") --production
$preflightExit = $LASTEXITCODE

Write-Host "=== 5/5 optional Celery worker smoke (profile ops) ===" -ForegroundColor Cyan
Push-Location $Root
& (Join-Path $Root "scripts/docker-with-cncfstack.ps1") -Profile dev --profile ops run --rm publish-worker-once 2>&1 | Select-Object -Last 15
Pop-Location

if ($preflightExit -eq 0) {
  Write-Host "`nStaging preflight: PASS" -ForegroundColor Green
} else {
  Write-Host "`nStaging preflight: FAIL (see docs/production-preflight-latest.json)" -ForegroundColor Red
}
exit $preflightExit
