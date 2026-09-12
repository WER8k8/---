# P13 商业闭环 — 本机可自动化实机验收（ngrok/沙箱密钥为可选门禁）
# 用法: powershell -ExecutionPolicy Bypass -File scripts/run-p13-staging-acceptance.ps1
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Py = Join-Path $Backend ".venv\Scripts\python.exe"
if (-not (Test-Path $Py)) { $Py = "python" }
$BaseUrl = "http://127.0.0.1:8001"
$ReportPath = Join-Path $Root "docs\staging-p13-acceptance-latest.json"
$Ts = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

function Test-HttpUp([string]$Url, [int]$Sec = 5) {
  try { Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $Sec | Out-Null; return $true } catch { return $false }
}

$report = [ordered]@{
  generated_at = $Ts
  base_url = $BaseUrl
  steps = @()
  ok = $true
}

function Add-Step([string]$Name, [bool]$Ok, $Detail) {
  $script:report.steps += @{ name = $Name; ok = $Ok; detail = $Detail }
  if (-not $Ok) { $script:report.ok = $false }
}

Write-Host "=== P13 staging acceptance ===" -ForegroundColor Cyan

if (-not (Test-HttpUp "$BaseUrl/api/v1/health")) {
  Add-Step "backend_health" $false "Backend not reachable at $BaseUrl — run scripts/start-dev-admin.ps1"
  $report | ConvertTo-Json -Depth 8 | Set-Content -Path $ReportPath -Encoding UTF8
  Write-Host "FAIL: backend down" -ForegroundColor Red
  exit 1
}
Add-Step "backend_health" $true @{ status = 200 }

Push-Location $Backend
$env:ENVIRONMENT = "testing"
$env:SECRET_KEY = "test-secret-key-for-unit-testing-only-not-for-production-use"
$env:JWT_SECRET_KEY = "test-jwt-secret-key-for-unit-testing-only-not-for-production-use"
$env:PAYMENT_STRICT_VERIFY = "0"

Write-Host "--- pytest P13 ---" -ForegroundColor Yellow
& $Py -m pytest tests/unit/test_commercial_loop_p13.py -q
$pytestOk = ($LASTEXITCODE -eq 0)
Add-Step "pytest_p13" $pytestOk @{ exit_code = $LASTEXITCODE }

Write-Host "--- staging self-check (HTTP) ---" -ForegroundColor Yellow
$selfOut = & $Py scripts/staging_payment_self_check.py --http --base-url $BaseUrl 2>&1 | Out-String
try { $selfJson = $selfOut | ConvertFrom-Json } catch { $selfJson = @{ ok = $false; raw = $selfOut } }
Add-Step "staging_self_check" ([bool]$selfJson.ok) $selfJson

Write-Host "--- local notify (relaxed) ---" -ForegroundColor Yellow
$notifyOut = & $Py scripts/staging_notify_http_check.py --base-url $BaseUrl 2>&1 | Out-String
try { $notifyJson = $notifyOut | ConvertFrom-Json } catch { $notifyJson = @{ ok = $false; raw = $notifyOut } }
Add-Step "local_notify_relaxed" ([bool]$notifyJson.ok) $notifyJson

Write-Host "--- audit CSV export ---" -ForegroundColor Yellow
$exportPy = @"
import httpx, json, sys
base = '$BaseUrl'
c = httpx.Client(timeout=30, follow_redirects=True)
login = c.post(f'{base}/api/v1/auth/login', json={'username_or_email':'admin','password':'admin123'})
body = login.json()
if body.get('code') != 0:
    print(json.dumps({'ok': False, 'error': 'login failed'})); sys.exit(0)
token = body['data']['access_token']
h = {'Authorization': f'Bearer {token}'}
c.post(f'{base}/api/v1/payment/ops/staging/self-check', headers=h)
ex = c.get(f'{base}/api/v1/payment/ops/audit/export', headers=h)
ok = ex.status_code == 200 and 'text/csv' in ex.headers.get('content-type', '')
print(json.dumps({'ok': ok, 'status': ex.status_code, 'content_type': ex.headers.get('content-type',''), 'head': ex.text[:120]}, ensure_ascii=False))
"@
$exportOut = & $Py -c $exportPy 2>&1 | Out-String
try { $exportJson = $exportOut | ConvertFrom-Json } catch { $exportJson = @{ ok = $false; raw = $exportOut } }
Add-Step "audit_csv_export" ([bool]$exportJson.ok) $exportJson

Write-Host "--- ngrok public notify (optional) ---" -ForegroundColor Yellow
$ngrokUrl = $null
try {
  $tunnels = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -TimeoutSec 3
  $ngrokUrl = ($tunnels.tunnels | Where-Object { $_.proto -eq 'https' } | Select-Object -First 1).public_url
} catch { }

if (-not $ngrokUrl) {
  $setupScript = Join-Path $Root "scripts\setup-ngrok.ps1"
  $tunnelScript = Join-Path $Root "scripts\start-ngrok-tunnel.ps1"
  $envFile = Join-Path $Root ".env.ngrok.local"
  $hasToken = (Test-Path $envFile) -or $env:NGROK_AUTHTOKEN -or $env:NGROK_AUTH_TOKEN
  if ($hasToken) {
    Write-Host "ngrok not running; attempting start..." -ForegroundColor Yellow
    & powershell -ExecutionPolicy Bypass -File $tunnelScript -SetupIfMissing 2>&1 | Out-Null
    Start-Sleep -Seconds 3
    try {
      $tunnels = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -TimeoutSec 3
      $ngrokUrl = ($tunnels.tunnels | Where-Object { $_.proto -eq 'https' } | Select-Object -First 1).public_url
    } catch { }
  }
}

if ($ngrokUrl) {
  $pubOut = & $Py scripts/staging_notify_http_check.py --base-url $BaseUrl --via-public --public-url $ngrokUrl 2>&1 | Out-String
  try { $pubJson = $pubOut | ConvertFrom-Json } catch { $pubJson = @{ ok = $false; raw = $pubOut } }
  Add-Step "public_notify_ngrok" ([bool]$pubJson.ok) $pubJson
} else {
  Add-Step "public_notify_ngrok" $true @{
    skipped = $true
    reason = "ngrok not running or authtoken missing"
    hint = "copy .env.ngrok.local.example -> .env.ngrok.local, fill NGROK_AUTHTOKEN, then scripts/setup-ngrok.ps1 && scripts/start-ngrok-tunnel.ps1"
  }
}

Pop-Location

$report | ConvertTo-Json -Depth 10 | Set-Content -Path $ReportPath -Encoding UTF8
Write-Host ""
Write-Host "Report: $ReportPath" -ForegroundColor Cyan
if ($report.ok) {
  Write-Host "P13 staging acceptance: PASS (local gates)" -ForegroundColor Green
  exit 0
} else {
  Write-Host "P13 staging acceptance: FAIL" -ForegroundColor Red
  exit 1
}
