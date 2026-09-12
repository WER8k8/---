# QA-04 · Locust 冒烟（非 72h 长跑，归档报告骨架）
# Usage: powershell -ExecutionPolicy Bypass -File scripts/qa-locust-smoke.ps1
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Py = Join-Path $Backend ".venv\Scripts\python.exe"
if (-not (Test-Path $Py)) { $Py = "python" }
$ReportDir = Join-Path $Root "docs\qa-locust"
$Report = Join-Path $ReportDir "locust-smoke-latest.json"
$HostUrl = if ($env:LOCUST_HOST) { $env:LOCUST_HOST } else { "http://127.0.0.1:8001" }

# 健康检查（不阻断；写入报告）
$healthOk = $false
try {
  $resp = Invoke-WebRequest -Uri "$HostUrl/api/v1/health" -UseBasicParsing -TimeoutSec 5
  $healthOk = ($resp.StatusCode -eq 200)
} catch {
  $healthOk = $false
}

New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null

Push-Location $Backend
$prevEap = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& $Py -m locust -f locustfile.py --host=$HostUrl --headless -u 5 -r 1 --run-time 20s --csv "$ReportDir\smoke" 2>&1 | Out-Null
$locustExit = $LASTEXITCODE
$ErrorActionPreference = $prevEap
Pop-Location

$statsPath = Join-Path $ReportDir "smoke_stats.csv"
$summary = @{
  generated_at = (Get-Date).ToString("o")
  task = "QA-04-smoke"
  host = $HostUrl
  duration = "20s"
  users = 5
  backend_health = $healthOk
  locust_exit = $locustExit
  stats_csv = $(if (Test-Path $statsPath) { $true } else { $false })
  smoke_pass = ($locustExit -eq 0) -and $healthOk
  note = "72h run scheduled at CERT stage; this script is weekly smoke only"
}
($summary | ConvertTo-Json -Depth 4) | Set-Content -Path $Report -Encoding UTF8

if ($summary.smoke_pass) {
  Write-Host ('QA-04 Locust smoke: PASS -> ' + $Report) -ForegroundColor Green
} else {
  Write-Host ('QA-04 Locust smoke: FAIL (check backend at ' + $HostUrl + ')') -ForegroundColor Yellow
}
exit $(if ($summary.smoke_pass) { 0 } else { 1 })
