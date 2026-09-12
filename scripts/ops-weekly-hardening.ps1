# 运维每周加固 — 安全扫描 + 假交付 + 前端门禁（专家「自己找事干」汇总）
# 用法: powershell -File scripts/ops-weekly-hardening.ps1
# 建议: Windows 计划任务 · 每周五 18:00

param(
    [string]$RepoRoot = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = "Continue"
$Py = Join-Path $RepoRoot "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $Py)) { $Py = "python" }
$ReportDir = Join-Path $RepoRoot "docs\ops"
$Report = Join-Path $ReportDir "weekly-hardening-latest.json"
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null

$steps = New-Object System.Collections.Generic.List[object]

function Run-Step($Name, $ScriptBlock) {
    Write-Host "=== $Name ===" -ForegroundColor Cyan
    $exit = 0
    try { & $ScriptBlock } catch { $exit = 1; Write-Host $_.Exception.Message -ForegroundColor Red }
    if ($null -ne $LASTEXITCODE -and $LASTEXITCODE -ne 0) { $exit = $LASTEXITCODE }
    $ok = ($exit -eq 0)
    $steps.Add([ordered]@{ step = $Name; ok = $ok; exit = $exit }) | Out-Null
    if ($ok) { Write-Host "$Name PASS" -ForegroundColor Green } else { Write-Host "$Name FAIL" -ForegroundColor Red }
}

Write-Host "=== 优丁 · 每周运维加固（ECC 专家例行） ===" -ForegroundColor Cyan

Run-Step "daily-health" { powershell -File (Join-Path $RepoRoot "scripts\ops-daily-health.ps1") }
Run-Step "no-fake-delivery" { & $Py (Join-Path $RepoRoot "scripts\validate-no-fake-delivery.py") }
Run-Step "security-audit" {
    $sec = Join-Path $RepoRoot "scripts\run-security-audit.ps1"
    if (Test-Path $sec) { powershell -File $sec } else { Write-Host "skip: no run-security-audit.ps1" }
}
Run-Step "mounted-routes" { & $Py (Join-Path $RepoRoot "scripts\check_mounted_routes.py") }
Run-Step "production-preflight" { & $Py (Join-Path $RepoRoot "scripts\run_production_preflight.py") }
Run-Step "cert-gate" {
    Push-Location (Join-Path $RepoRoot "frontend\admin")
    npm run cert:gate 2>&1 | Out-Host
    Pop-Location
}
Run-Step "international-webhook-test" {
    $env:SECRET_KEY = "test-secret-key-for-unit-testing-only-not-for-production-use"
    $env:JWT_SECRET_KEY = "test-jwt-secret-key-for-unit-testing-only-not-for-production-use"
    Push-Location (Join-Path $RepoRoot "backend")
    & $Py -m pytest tests/unit/test_international_crawl_webhook.py -q
    Pop-Location
}
Run-Step "weekly-seo-geo-loop" {
    powershell -File (Join-Path $RepoRoot "scripts\run-weekly-seo-geo-loop.ps1")
}

$fail = @($steps | Where-Object { -not $_.ok }).Count
$payload = @{
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
    task = "ops-weekly-hardening"
    ok = ($fail -eq 0)
    fail_count = $fail
    steps = @($steps | ForEach-Object { @{ step = $_.step; ok = $_.ok; exit = $_.exit } })
}
($payload | ConvertTo-Json -Depth 5) | Set-Content -Path $Report -Encoding UTF8

if ($fail -eq 0) {
    Write-Host "每周加固: 全部通过 -> $Report" -ForegroundColor Green
    exit 0
}
Write-Host "每周加固: $fail 步失败 -> $Report（把报告发给 Cursor 让专家修）" -ForegroundColor Red
exit 1
