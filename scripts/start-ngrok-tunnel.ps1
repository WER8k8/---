# Start ngrok tunnel to local API (default :8001)
# Usage: powershell -ExecutionPolicy Bypass -File scripts/start-ngrok-tunnel.ps1
param(
  [int]$ApiPort = 8001,
  [switch]$SetupIfMissing
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

function Get-NgrokPublicUrl {
  try {
    $tunnels = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -TimeoutSec 3
    return ($tunnels.tunnels | Where-Object { $_.proto -eq "https" } | Select-Object -First 1).public_url
  } catch {
    return $null
  }
}

function Test-NgrokConfigured {
  ngrok config check 2>&1 | Out-Null
  return ($LASTEXITCODE -eq 0)
}

$existing = Get-NgrokPublicUrl
if ($existing) {
  Write-Host "ngrok already running: $existing" -ForegroundColor Green
  Write-Host "alipay notify: $existing/api/v1/payment/notify/alipay"
  Write-Host "wechat notify: $existing/api/v1/payment/notify/wechat"
  exit 0
}

if (-not (Test-NgrokConfigured)) {
  if ($SetupIfMissing) {
    & (Join-Path $Root "scripts\setup-ngrok.ps1")
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
  } else {
    Write-Host "ngrok not configured. Run scripts/setup-ngrok.ps1 first." -ForegroundColor Red
    exit 1
  }
}

Write-Host "Starting ngrok http $ApiPort ..." -ForegroundColor Cyan
Start-Process ngrok -ArgumentList "http", "$ApiPort", "--log=stdout" -WindowStyle Normal | Out-Null

$deadline = (Get-Date).AddSeconds(20)
$publicUrl = $null
while ((Get-Date) -lt $deadline) {
  $publicUrl = Get-NgrokPublicUrl
  if ($publicUrl) { break }
  Start-Sleep -Seconds 1
}

if (-not $publicUrl) {
  Write-Host "ngrok start timeout - check ngrok window for authtoken errors" -ForegroundColor Red
  exit 1
}

Write-Host ""
Write-Host "Public URL: $publicUrl" -ForegroundColor Green
Write-Host "Local API:  http://127.0.0.1:$ApiPort"
Write-Host ""
Write-Host "Verify:"
Write-Host "  cd backend"
Write-Host "  python scripts/staging_notify_http_check.py --base-url http://127.0.0.1:$ApiPort --via-public --discover-ngrok"
