# MOD-02 · 企微/抖音 webhook 本机冒烟（需 Postgres :5433）
# Usage: powershell -File scripts/smoke-mod-02-inquiry-webhooks.ps1
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Py = Join-Path $Backend ".venv\Scripts\python.exe"
$Report = Join-Path $Root "docs\mod-02-webhook-smoke-latest.json"
$HostUrl = "http://127.0.0.1:8002"
$Secret = "mod02-smoke-" + ("y" * 24)

. (Join-Path $Root "scripts\ensure-staging-postgres.ps1")
Ensure-StagingPostgres -Quiet

$env:DATABASE_URL = "postgresql://youding:youding@127.0.0.1:5433/youding_dev"
$env:INQUIRY_WEBHOOK_SECRET = $Secret
$env:JWT_SECRET_KEY = $Secret
$env:SECRET_KEY = $Secret
$env:ENVIRONMENT = "development"
$env:REDIS_ENABLED = "false"
$env:PYTHONPATH = $Backend

$proc = Start-Process -FilePath $Py `
  -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8002") `
  -WorkingDirectory $Backend -PassThru -WindowStyle Hidden

$ready = $false
for ($i = 0; $i -lt 30; $i++) {
  try {
    $r = Invoke-WebRequest -Uri "$HostUrl/api/v1/health" -UseBasicParsing -TimeoutSec 2
    if ($r.StatusCode -eq 200) { $ready = $true; break }
  } catch { Start-Sleep -Seconds 2 }
}

$results = @{}
if ($ready) {
  $body = '{"name":"Smoke","phone":"13800138001","message":"MOD-02 smoke"}'
  $hdr = @{ "X-Inquiry-Webhook-Secret" = $Secret; "Content-Type" = "application/json" }
  foreach ($ch in @("wecom", "douyin")) {
    try {
      $res = Invoke-RestMethod -Uri "$HostUrl/api/v1/inquiries/channels/$ch" -Method Post -Headers $hdr -Body $body
      $results[$ch] = ($res.code -eq 0)
    } catch { $results[$ch] = $false }
  }
}
Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue

$pass = $ready -and ($results.wecom -and $results.douyin)
$payload = @{
  generated_at = (Get-Date).ToString("o")
  task = "MOD-02-webhook-smoke"
  pass = $pass
  backend_ready = $ready
  channels = $results
}
($payload | ConvertTo-Json -Depth 4) | Set-Content -Path $Report -Encoding UTF8

if ($pass) {
  Write-Host "MOD-02 webhook smoke: PASS -> $Report" -ForegroundColor Green
  exit 0
}
Write-Host "MOD-02 webhook smoke: FAIL" -ForegroundColor Red
exit 1
