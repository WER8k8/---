# 每周 SEO/GEO 闭环 — 对标 Claude SEO Stack（周一挖词由 Deerflow 扩展；此处周四技术审计）
# Usage: powershell -File scripts/run-weekly-seo-geo-loop.ps1
# 已接入: scripts/ops-weekly-hardening.ps1

param(
  [string]$RepoRoot = (Split-Path -Parent $PSScriptRoot),
  [string]$Tenant = 'dev.local'
)

$ErrorActionPreference = 'Continue'
$Py = Join-Path $RepoRoot 'backend\.venv\Scripts\python.exe'
if (-not (Test-Path $Py)) { $Py = 'python' }
$ReportDir = Join-Path $RepoRoot 'docs\ops'
$Report = Join-Path $ReportDir 'weekly-seo-geo-loop-latest.json'
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null

$steps = New-Object System.Collections.Generic.List[object]
$day = (Get-Date).DayOfWeek.ToString()

function Run-Step($Name, $ScriptBlock) {
  Write-Host "=== $Name ===" -ForegroundColor Cyan
  $exit = 0
  try { & $ScriptBlock } catch { $exit = 1; Write-Host $_.Exception.Message -ForegroundColor Red }
  if ($null -ne $LASTEXITCODE -and $LASTEXITCODE -ne 0) { $exit = $LASTEXITCODE }
  $ok = ($exit -eq 0)
  $steps.Add([ordered]@{ step = $Name; ok = $ok; exit = $exit }) | Out-Null
  if ($ok) { Write-Host "$Name PASS" -ForegroundColor Green } else { Write-Host "$Name FAIL" -ForegroundColor Red }
}

Write-Host "=== 优丁 · 每周 SEO/GEO 闭环 ($day) ===" -ForegroundColor Cyan

Run-Step 'tenant-seo-audit' {
  powershell -File (Join-Path $RepoRoot 'scripts\run-tenant-seo-audit.ps1') -Tenant $Tenant
}
Run-Step 'tenant-geo-audit' {
  powershell -File (Join-Path $RepoRoot 'scripts\run-tenant-geo-audit.ps1') -Tenant $Tenant
}
if ($day -eq 'Monday') {
  Run-Step 'seo-keyword-discover' {
    & $Py (Join-Path $RepoRoot 'scripts\run-seo-keyword-discover.py') --tenant $Tenant
  }
}
Run-Step 'gap-closure-smoke' {
  & $Py (Join-Path $RepoRoot 'scripts\smoke-gap-closure-dev.py')
}
Run-Step 'cert-gate' {
  Push-Location (Join-Path $RepoRoot 'frontend\admin')
  npm run cert:gate 2>&1 | Out-Host
  Pop-Location
}

$fail = @($steps | Where-Object { -not $_.ok }).Count
$payload = @{
  generated_at = (Get-Date).ToUniversalTime().ToString('o')
  task         = 'weekly-seo-geo-loop'
  weekday      = $day
  ok           = ($fail -eq 0)
  fail_count   = $fail
  steps        = @($steps | ForEach-Object { @{ step = $_.step; ok = $_.ok; exit = $_.exit } })
  reports      = @(
    'docs/tenant-seo-audit-latest.json'
    'docs/tenant-geo-audit-latest.json'
    'docs/gap-closure-smoke-latest.json'
    'docs/certification-gate-admin-latest.json'
  )
}
($payload | ConvertTo-Json -Depth 5) | Set-Content -Path $Report -Encoding UTF8

if ($fail -eq 0) {
  Write-Host "每周 SEO/GEO: 全部通过 -> $Report" -ForegroundColor Green
  exit 0
}
Write-Host "每周 SEO/GEO: $fail 步失败 -> $Report" -ForegroundColor Red
exit 1
