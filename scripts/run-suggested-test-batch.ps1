# 建议测试批次：G4 + 飞轮/UBrain 实机 + Phase C（演示跳过）
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Py = Join-Path $Backend ".venv\Scripts\python.exe"
if (-not (Test-Path $Py)) { $Py = "python" }
$DevEnv = Join-Path $Backend "config\dev\.env"

function Test-PortUp([int]$Port) {
  try {
    Invoke-WebRequest -Uri "http://127.0.0.1:$Port/docs" -UseBasicParsing -TimeoutSec 3 | Out-Null
    return $true
  } catch { return $false }
}

function Start-BackendRealAi {
  Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
  Start-Sleep -Seconds 2
  $cmd = @"
Set-Location '$Backend'
`$env:PYTHONPATH = (Get-Location).Path
`$env:DATABASE_URL = 'sqlite:///./youding_dev.db'
`$env:REDIS_ENABLED = 'false'
`$env:LOGIN_BF_USE_REDIS = 'false'
if (Test-Path '$DevEnv') {
  Get-Content '$DevEnv' | ForEach-Object {
    if (`$_ -match '^\s*([^#][^=]+)=(.*)$') {
      `$k = `$matches[1].Trim(); `$v = `$matches[2].Trim()
      if (`$k) { Set-Item -Path Env:`$k -Value `$v }
    }
  }
}
`$env:MVP_LAUNCH = '0'
if (-not `$env:JWT_SECRET_KEY) { `$env:JWT_SECRET_KEY = 'dev-' + ('x' * 28) }
if (-not `$env:SECRET_KEY) { `$env:SECRET_KEY = `$env:JWT_SECRET_KEY }
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001
"@
  Start-Process powershell -WindowStyle Minimized -ArgumentList "-NoProfile", "-Command", $cmd
  $deadline = (Get-Date).AddSeconds(45)
  while ((Get-Date) -lt $deadline) {
    if (Test-PortUp 8001) { return $true }
    Start-Sleep -Seconds 2
  }
  return $false
}

$results = @()
function Add-R([string]$Step, [bool]$Ok, [string]$Detail) {
  $script:results += [pscustomobject]@{ step = $Step; ok = $Ok; detail = $Detail }
  $color = if ($Ok) { "Green" } else { "Red" }
  Write-Host ("[{0}] {1} — {2}" -f ($(if ($Ok) { "PASS" } else { "FAIL" })), $Step, $Detail) -ForegroundColor $color
}

Write-Host "=== 建议测试批次（演示跳过）===" -ForegroundColor Cyan

if (-not (Test-PortUp 8001)) {
  Write-Host "Starting backend with real AI (MVP_LAUNCH=0)..." -ForegroundColor Yellow
  if (-not (Start-BackendRealAi)) { Add-R "backend_up" $false "8001 timeout"; exit 1 }
}
Add-R "backend_up" (Test-PortUp 8001) ":8001"

Write-Host "`n--- G4 真实 AI Key ---" -ForegroundColor Cyan
& (Join-Path $Root "scripts\run-g4-real-ai-verify.ps1") 2>&1 | Out-Null
Add-R "g4_verify" ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"

Write-Host "`n--- 飞轮 D2-D6 单测 ---" -ForegroundColor Cyan
Push-Location $Backend
& $Py -m pytest tests/unit/test_flywheel_d2_d6_http.py tests/unit/test_flywheel_d2_d6_api.py -q --tb=no 2>&1 | Tee-Object -Variable flyOut | Out-Null
$flyOk = ($LASTEXITCODE -eq 0)
Add-R "flywheel_unit" $flyOk ($flyOut | Select-Object -Last 1)
Pop-Location

Write-Host "`n--- UBrain + 飞轮实机 smoke ---" -ForegroundColor Cyan
& $Py (Join-Path $Root "scripts\run-ubrain-flywheel-live-smoke.py")
Add-R "ubrain_flywheel_live" ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"

Write-Host "`n--- 层级/数据中心验收 ---" -ForegroundColor Cyan
& $Py (Join-Path $Root "scripts\run-hierarchy-browser-acceptance.py")
Add-R "hierarchy_acceptance" ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"

Write-Host "`n--- 可靠性 smoke（12 轮 × 5s ≈ 1 分钟）---" -ForegroundColor Cyan
$env:RELIABILITY_ROUNDS = "12"
& $Py (Join-Path $Root "scripts\run-reliability-smoke.py")
Add-R "reliability_1min" ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"

Write-Host "`n--- 轻量压测 30 用户 20s ---" -ForegroundColor Cyan
Push-Location $Root
& $Py (Join-Path $Root "scripts\load_test.py") --url "http://127.0.0.1:8001" --users 30 --duration 20s --qps 100 2>&1 | Out-Null
Add-R "locust_light" ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"
Pop-Location

$fail = @($results | Where-Object { -not $_.ok }).Count
Write-Host "`n=== 汇总: $($results.Count - $fail)/$($results.Count) PASS, FAIL=$fail ===" -ForegroundColor $(if ($fail -eq 0) { "Green" } else { "Yellow" })

$report = @{
  generated_at = (Get-Date).ToUniversalTime().ToString("o")
  demo_skipped = $true
  steps        = $results
  fail_count   = $fail
  artifacts    = @(
    "docs/g4-ai-key-verify-latest.json"
    "docs/ubrain-flywheel-live-smoke-latest.json"
    "docs/hierarchy-browser-acceptance-latest.json"
    "docs/申报材料/reliability-smoke-latest.json"
  )
}
$out = Join-Path $Root "docs\suggested-test-batch-latest.json"
$report | ConvertTo-Json -Depth 6 | Set-Content -Path $out -Encoding UTF8
Write-Host "Report: $out"
exit $fail
