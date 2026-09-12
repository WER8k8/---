# QA-04 · Locust 正式 72h（HTTPS 域就绪后执行）
# Usage:
#   $env:LOCUST_HOST = "https://demo.youding.com"
#   powershell -ExecutionPolicy Bypass -File scripts/qa-locust-72h-production.ps1
param(
  [string]$HostUrl = $env:LOCUST_HOST,
  [int]$Users = 50,
  [int]$SpawnRate = 5,
  [string]$RunTime = "72h"
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Py = Join-Path $Backend ".venv\Scripts\python.exe"
$ReportDir = Join-Path $Root "docs\qa-locust"
$Report = Join-Path $ReportDir "locust-72h-latest.json"
$CsvPrefix = Join-Path $ReportDir "run-72h"

if (-not $HostUrl) {
  Write-Host "QA-04 72h: set LOCUST_HOST (HTTPS API base, e.g. https://demo.youding.com)" -ForegroundColor Red
  exit 1
}
if ($HostUrl -notmatch "^https://") {
  Write-Host "QA-04 72h: LOCUST_HOST must be HTTPS (ARCH-04/MOD-01 prerequisite)" -ForegroundColor Red
  exit 1
}

Write-Host "=== QA-04 Locust 72h on $HostUrl ===" -ForegroundColor Cyan
Push-Location $Backend
$prevEap = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& $Py -m locust -f locustfile.py --host=$HostUrl --headless `
  -u $Users -r $SpawnRate --run-time $RunTime --csv $CsvPrefix 2>&1 | Tee-Object -Variable locustLog
$locustExit = $LASTEXITCODE
$ErrorActionPreference = $prevEap
Pop-Location

$payload = @{
  generated_at = (Get-Date).ToString("o")
  task = "QA-04-72h-production"
  host = $HostUrl
  duration = $RunTime
  users = $Users
  spawn_rate = $SpawnRate
  locust_exit = $locustExit
  pass = ($locustExit -eq 0)
  csv_prefix = "docs/qa-locust/run-72h"
  schedule = "docs/qa-locust/QA-04-72h-schedule.md"
}
($payload | ConvertTo-Json -Depth 4) | Set-Content -Path $Report -Encoding UTF8

if ($locustExit -eq 0) {
  Write-Host "QA-04 72h production: PASS -> $Report" -ForegroundColor Green
  exit 0
}
Write-Host "QA-04 72h production: FAIL (exit $locustExit)" -ForegroundColor Red
exit 1
