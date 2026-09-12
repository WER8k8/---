# P13 严验签 + 签名 notify 公网验收（需 ngrok + backend 严验签模式）
# 用法: powershell -ExecutionPolicy Bypass -File scripts/run-p13-strict-notify-check.ps1
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Py = Join-Path $Backend ".venv\Scripts\python.exe"
$BaseUrl = "http://127.0.0.1:8001"
$WebhookSecret = if ($env:PAYMENT_WEBHOOK_SECRET) { $env:PAYMENT_WEBHOOK_SECRET } else { "staging-webhook-local-dev-only-not-prod" }

function Test-HttpUp([string]$Url, [int]$Sec = 5) {
  try { Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $Sec | Out-Null; return $true } catch { return $false }
}

Write-Host "=== P13 strict + signed notify (W42) ===" -ForegroundColor Cyan

if (-not (Test-HttpUp "$BaseUrl/api/v1/health")) {
  Write-Host "Backend not running. Start with strict env first:" -ForegroundColor Red
  Write-Host '  $env:PAYMENT_STRICT_VERIFY="1"; $env:PAYMENT_WEBHOOK_SECRET="staging-webhook-local-dev-only-not-prod"'
  Write-Host "  then scripts/start-dev-admin.ps1 or uvicorn on :8001"
  exit 1
}

$ngrokUrl = $null
try {
  $ngrokUrl = (Invoke-RestMethod "http://127.0.0.1:4040/api/tunnels" -TimeoutSec 3).tunnels |
    Where-Object { $_.proto -eq "https" } | Select-Object -First 1 -ExpandProperty public_url
} catch { }

if (-not $ngrokUrl) {
  Write-Host "ngrok not running. Start: scripts/start-ngrok-tunnel.ps1" -ForegroundColor Red
  exit 1
}

Write-Host "ngrok: $ngrokUrl" -ForegroundColor DarkGray
Write-Host "strict verify + try_signed..." -ForegroundColor Yellow

Push-Location $Backend
$env:PAYMENT_STRICT_VERIFY = "1"
$env:PAYMENT_WEBHOOK_SECRET = $WebhookSecret
$out = & $Py scripts/staging_notify_http_check.py `
  --base-url $BaseUrl `
  --via-public `
  --public-url $ngrokUrl `
  --try-signed 2>&1 | Out-String
Pop-Location

Write-Host $out
try { $json = $out | ConvertFrom-Json } catch { exit 1 }

$reportPath = Join-Path $Root "docs/staging-p13-strict-notify-latest.json"
$json | ConvertTo-Json -Depth 12 | Set-Content -Path $reportPath -Encoding UTF8
Write-Host "Report: $reportPath" -ForegroundColor Cyan

if ($json.ok) {
  Write-Host "P13 strict signed notify: PASS" -ForegroundColor Green
  exit 0
} else {
  Write-Host "P13 strict signed notify: FAIL" -ForegroundColor Red
  exit 1
}
