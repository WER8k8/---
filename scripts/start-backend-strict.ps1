# 严验签 backend（:8001）— P13 staging 实机验收用
# 用法: powershell -ExecutionPolicy Bypass -File scripts/start-backend-strict.ps1
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Py = Join-Path $Backend ".venv\Scripts\python.exe"
$Port = 8001

function Test-HttpUp([string]$Url, [int]$Sec = 3) {
  try { Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $Sec | Out-Null; return $true } catch { return $false }
}

$listeners = @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique)
foreach ($procId in $listeners) {
  Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Seconds 2

$cmd = @"
Set-Location '$Backend'
`$env:PYTHONPATH = (Get-Location).Path
`$env:DATABASE_URL = 'sqlite:///./youding_dev.db'
`$env:REDIS_ENABLED = 'false'
`$env:LOGIN_BF_USE_REDIS = 'false'
`$env:MVP_LAUNCH = '1'
`$env:ENVIRONMENT = 'development'
`$env:PAYMENT_STRICT_VERIFY = '1'
`$env:PAYMENT_WEBHOOK_SECRET = 'staging-webhook-local-dev-only-not-prod'
if (-not `$env:JWT_SECRET_KEY) { `$env:JWT_SECRET_KEY = 'dev-' + ('x' * 28) }
`$env:SECRET_KEY = `$env:JWT_SECRET_KEY
& '$Py' -m uvicorn app.main:app --host 127.0.0.1 --port $Port
"@

Write-Host "Starting strict backend on :$Port ..." -ForegroundColor Cyan
Start-Process powershell -WindowStyle Normal -ArgumentList "-NoProfile", "-Command", $cmd

$deadline = (Get-Date).AddSeconds(45)
while ((Get-Date) -lt $deadline) {
  if (Test-HttpUp "http://127.0.0.1:$Port/api/v1/health") { break }
  Start-Sleep -Seconds 2
}

if (-not (Test-HttpUp "http://127.0.0.1:$Port/api/v1/health")) {
  Write-Host "Backend failed to start on :$Port" -ForegroundColor Red
  exit 1
}

Write-Host "Backend strict mode: http://127.0.0.1:$Port/docs" -ForegroundColor Green
Write-Host "Verify: scripts/run-p13-strict-notify-check.ps1"
