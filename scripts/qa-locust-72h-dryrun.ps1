# QA-04 · Locust 72h 干跑（2min 验证流水线，非生产 72h）
# Usage: powershell -ExecutionPolicy Bypass -File scripts/qa-locust-72h-dryrun.ps1
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Py = Join-Path $Backend ".venv\Scripts\python.exe"
$ReportDir = Join-Path $Root "docs\qa-locust"
$Report = Join-Path $ReportDir "locust-72h-dryrun-latest.json"
$HostUrl = "http://127.0.0.1:8001"

$secret = "qa-locust-dryrun-" + ("x" * 32)
$env:DATABASE_URL = "postgresql://youding:youding@127.0.0.1:5433/youding_dev"
$env:JWT_SECRET_KEY = $secret
$env:SECRET_KEY = $secret
$env:ENVIRONMENT = "development"
$env:REDIS_ENABLED = "false"
$env:PYTHONPATH = $Backend

Write-Host "=== alembic upgrade (QA-04 dryrun) ===" -ForegroundColor Cyan
Push-Location $Backend
$prevEap = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& $Py -m alembic upgrade head 2>&1 | Out-Null
$ErrorActionPreference = $prevEap
Pop-Location

$proc = Start-Process -FilePath $Py `
  -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8001") `
  -WorkingDirectory $Backend -PassThru -WindowStyle Hidden

$ready = $false
for ($i = 0; $i -lt 45; $i++) {
  try {
    $r = Invoke-WebRequest -Uri "$HostUrl/api/v1/health" -UseBasicParsing -TimeoutSec 2
    if ($r.StatusCode -eq 200) { $ready = $true; break }
  } catch { Start-Sleep -Seconds 2 }
}
if (-not $ready) {
  Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
  Write-Host "QA-04 dryrun: backend not ready" -ForegroundColor Red
  exit 1
}

Push-Location $Backend
$ErrorActionPreference = "Continue"
& $Py -m locust -f locustfile.py --host=$HostUrl --headless -u 10 -r 2 --run-time 2m --csv "$ReportDir\dryrun-72h" 2>&1 | Out-Null
$locustExit = $LASTEXITCODE
$ErrorActionPreference = $prevEap
Pop-Location
Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue

$payload = @{
  generated_at = (Get-Date).ToString("o")
  task = "QA-04-72h-dryrun"
  duration = "2m"
  users = 10
  locust_exit = $locustExit
  smoke_pass = ($locustExit -eq 0)
  note = "Production 72h uses docs/qa-locust/QA-04-72h-schedule.md on HTTPS domain"
}
($payload | ConvertTo-Json -Depth 4) | Set-Content -Path $Report -Encoding UTF8

if ($locustExit -eq 0) {
  Write-Host "QA-04 72h dryrun: PASS -> $Report" -ForegroundColor Green
  exit 0
}
Write-Host "QA-04 72h dryrun: FAIL" -ForegroundColor Red
exit 1
