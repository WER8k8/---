# ARCH-01 · 省级评测 staging preflight 门禁包装
# Usage: powershell -ExecutionPolicy Bypass -File scripts/run-arch-01-cert-gate.ps1
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Report = Join-Path $Root "docs\arch-01-cert-gate-latest.json"

& (Join-Path $Root "scripts\run-staging-preflight-auto.ps1")
$exitCode = $LASTEXITCODE

$staging = Join-Path $Root "docs\staging-preflight-auto-latest.json"
$preflight = Join-Path $Root "docs\production-preflight-latest.json"
$stagingSummary = $null
$preflightSummary = $null
if (Test-Path $staging) {
  $s = Get-Content $staging -Raw | ConvertFrom-Json
  $stagingSummary = @{
    status = $s.status
    fail_count = $s.fail_count
    finished_at = $s.finished_at
    infra_mode = $s.infra_mode
  }
}
if (Test-Path $preflight) {
  $p = Get-Content $preflight -Raw | ConvertFrom-Json
  $preflightSummary = @{
    ok = $p.ok
    fail = $p.fail
    generated_at = $p.generated_at
  }
}

$payload = @{
  generated_at = (Get-Date).ToString("o")
  task = "ARCH-01"
  pass = ($exitCode -eq 0)
  staging_summary = $stagingSummary
  preflight_summary = $preflightSummary
  staging_report_path = "docs/staging-preflight-auto-latest.json"
  preflight_report_path = "docs/production-preflight-latest.json"
}
($payload | ConvertTo-Json -Depth 6) | Set-Content -Path $Report -Encoding UTF8

if ($exitCode -eq 0) {
  Write-Host "ARCH-01 cert gate: PASS -> $Report" -ForegroundColor Green
} else {
  Write-Host "ARCH-01 cert gate: FAIL -> $Report" -ForegroundColor Red
}
exit $exitCode
