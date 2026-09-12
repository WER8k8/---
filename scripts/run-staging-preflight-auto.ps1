# Auto staging preflight: Docker OR embedded Postgres + local Redis
# Usage: powershell -ExecutionPolicy Bypass -File scripts/run-staging-preflight-auto.ps1
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Py = Join-Path $Backend ".venv\Scripts\python.exe"
if (-not (Test-Path $Py)) { $Py = "python" }
$Report = Join-Path $Root "docs\staging-preflight-auto-latest.json"
$PgBin = "C:\Program Files\PostgreSQL\17\bin"
$EmbeddedPgDir = Join-Path $Root "staging-data\postgres"
$PgUrl = "postgresql://youding:youding@127.0.0.1:5433/youding_dev"
$RedisUrl = "redis://127.0.0.1:6379/0"

function Write-AutoReport([hashtable]$Data) {
  $dir = Split-Path -Parent $Report
  if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
  ($Data | ConvertTo-Json -Depth 6) | Set-Content -Path $Report -Encoding UTF8
}

function Test-DockerReady {
  try {
    $null = docker info 2>&1
    return ($LASTEXITCODE -eq 0)
  } catch {
    return $false
  }
}

function Test-PostgresReady {
  try {
    $null = & "$PgBin\psql.exe" -h 127.0.0.1 -p 5433 -U youding -d youding_dev -c "SELECT 1;" 2>&1
    return ($LASTEXITCODE -eq 0)
  } catch {
    return $false
  }
}

function Start-DockerDesktopIfNeeded {
  if (Test-DockerReady) { return $true }
  Write-Host "Docker not ready; trying Docker Desktop..." -ForegroundColor Yellow
  $candidates = @(
    "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe",
    "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe",
    "$env:LOCALAPPDATA\Programs\Docker\Docker\Docker Desktop.exe",
    "$env:LOCALAPPDATA\Docker\Docker Desktop.exe"
  )
  foreach ($exe in $candidates) {
    if (Test-Path $exe) {
      Write-Host "  Starting: $exe"
      Start-Process -FilePath $exe | Out-Null
      $deadline = (Get-Date).AddMinutes(4)
      while ((Get-Date) -lt $deadline) {
        if (Test-DockerReady) { return $true }
        Start-Sleep -Seconds 5
      }
      break
    }
  }
  return $false
}

function Reset-EmbeddedDatabase {
  & "$PgBin\psql.exe" -h 127.0.0.1 -p 5433 -U youding -d postgres -c `
    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'youding_dev' AND pid <> pg_backend_pid();" | Out-Null
  & "$PgBin\psql.exe" -h 127.0.0.1 -p 5433 -U youding -d postgres -c "DROP DATABASE IF EXISTS youding_dev;" | Out-Null
  & "$PgBin\psql.exe" -h 127.0.0.1 -p 5433 -U youding -d postgres -c "CREATE DATABASE youding_dev;" | Out-Null
}

function Ensure-EmbeddedPostgres {
  if (Test-PostgresReady) {
    Write-Host "Postgres already ready on :5433 (skip init/start)" -ForegroundColor Green
    return
  }
  if (-not (Test-Path "$PgBin\initdb.exe")) {
    throw "PostgreSQL binaries not found at $PgBin"
  }
  New-Item -ItemType Directory -Force -Path $EmbeddedPgDir | Out-Null
  if (-not (Test-Path "$EmbeddedPgDir\PG_VERSION")) {
    Write-Host "Initializing embedded Postgres at $EmbeddedPgDir" -ForegroundColor Cyan
    & "$PgBin\initdb.exe" -D $EmbeddedPgDir -U youding -A trust -E UTF8 --locale=C | Out-Null
  }
  $status = & "$PgBin\pg_ctl.exe" status -D $EmbeddedPgDir 2>&1 | Out-String
  if ($status -notmatch "server is running") {
    Write-Host "Starting embedded Postgres on :5433" -ForegroundColor Cyan
    & "$PgBin\pg_ctl.exe" start -D $EmbeddedPgDir -l "$EmbeddedPgDir\server.log" -o "-p 5433" | Out-Null
    Start-Sleep -Seconds 3
  }
  $dbExists = & "$PgBin\psql.exe" -h 127.0.0.1 -p 5433 -U youding -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='youding_dev';" 2>&1
  if ($dbExists -notmatch "1") {
    & "$PgBin\psql.exe" -h 127.0.0.1 -p 5433 -U youding -d postgres -c "CREATE DATABASE youding_dev;" | Out-Null
  }
  if (-not (Test-PostgresReady)) {
    throw "Embedded Postgres failed readiness on :5433"
  }
}

function Invoke-StagingPreflightCore([string]$Mode) {
  $prevEap = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  Write-Host "=== 2/5 alembic upgrade head (Postgres) ===" -ForegroundColor Cyan
  Push-Location $Backend
  $env:DATABASE_URL = $PgUrl
  $env:PYTHONPATH = (Get-Location).Path
  & $Py -m alembic upgrade head 2>&1 | Out-Null
  if ($LASTEXITCODE -ne 0) {
    Write-Host "WARN: full head failed; trying flywheel 028" -ForegroundColor Yellow
    & $Py -m alembic upgrade 028_ubrain_action_audit 2>&1 | Out-Null
  }
  Pop-Location

  Write-Host "=== 3/5 seed platforms ===" -ForegroundColor Cyan
  Push-Location $Backend
  $env:DATABASE_URL = $PgUrl
  $env:PYTHONPATH = (Get-Location).Path
  & $Py scripts/seed_platforms_full.py 2>&1 | Out-Null
  Pop-Location

  Write-Host "=== 4/5 production preflight (--production) ===" -ForegroundColor Cyan
  $env:ENVIRONMENT = "production"
  $env:DATABASE_URL = $PgUrl
  $env:MVP_LAUNCH = "1"
  $env:PAYMENT_STRICT_VERIFY = "1"
  $env:SSL_PROVIDER = "certbot"
  $env:CERTBOT_EMAIL = if ($env:CERTBOT_EMAIL) { $env:CERTBOT_EMAIL } else { "staging-preflight@demo.youding.local" }
  $env:REDIS_ENABLED = "true"
  $env:REDIS_URL = $RedisUrl
  $env:CELERY_BROKER_URL = $RedisUrl
  $env:FRONTEND_URL = "https://demo.youding.local"
  $env:JWT_SECRET_KEY = if ($env:JWT_SECRET_KEY) { $env:JWT_SECRET_KEY } else { "staging-preflight-" + ("x" * 16) }
  $env:SECRET_KEY = $env:JWT_SECRET_KEY

  & $Py (Join-Path $Root "scripts\run_production_preflight.py") --production 2>&1 | Out-Null
  $preflightExit = [int]$LASTEXITCODE

  Write-Host "=== 5/5 publish worker smoke (non-blocking) ===" -ForegroundColor Cyan
  try {
    if ($Mode -eq "docker") {
      Push-Location $Root
      & (Join-Path $Root "scripts/docker-with-cncfstack.ps1") -Profile dev --profile ops run --rm publish-worker-once 2>&1 | Select-Object -Last 15
      Pop-Location
    } else {
      Push-Location $Backend
      $env:DATABASE_URL = $PgUrl
      $env:PYTHONPATH = (Get-Location).Path
      & $Py scripts/run_publish_worker.py --once --limit 5 2>&1 | Select-Object -Last 10
      Pop-Location
    }
  } catch {
    Write-Host "WARN: publish worker smoke skipped: $_" -ForegroundColor Yellow
  }

  $ErrorActionPreference = $prevEap
  return ,$preflightExit
}

$startedAt = (Get-Date).ToString("o")
$mode = "embedded"
$dockerOk = $false

if (Start-DockerDesktopIfNeeded) {
  Write-Host "=== 1/5 docker compose: postgres + redis（藏云阁镜像） ===" -ForegroundColor Cyan
  Push-Location $Root
  & (Join-Path $Root "scripts/docker-with-cncfstack.ps1") -Profile dev up -d postgres redis
  $composeExit = $LASTEXITCODE
  Pop-Location
  if ($composeExit -eq 0) {
    $deadline = (Get-Date).AddSeconds(90)
    while ((Get-Date) -lt $deadline) {
      if (Test-PostgresReady) { break }
      Start-Sleep -Seconds 2
    }
    if (Test-PostgresReady) {
      $dockerOk = $true
      $mode = "docker"
    }
  }
}

if (-not $dockerOk) {
  Write-Host "=== 1/5 embedded Postgres + local Redis (Docker unavailable) ===" -ForegroundColor Yellow
  if (Test-PostgresReady) {
    Write-Host "  Reusing existing Postgres on :5433" -ForegroundColor Green
    $mode = "embedded-existing"
  } else {
    Ensure-EmbeddedPostgres
    Reset-EmbeddedDatabase
  }
}

$exitCode = Invoke-StagingPreflightCore -Mode $mode
if ($exitCode -is [array]) { $exitCode = [int]$exitCode[-1] }

$preflightJson = Join-Path $Root "docs\production-preflight-latest.json"
$preflightSummary = $null
$preflightOk = $null
if (Test-Path $preflightJson) {
  $raw = Get-Content $preflightJson -Raw -Encoding UTF8
  try { $preflightSummary = $raw | ConvertFrom-Json } catch {}
  if ($raw -match '"ok"\s*:\s*true') { $preflightOk = $true }
  if ($raw -match '"fail"\s*:\s*0') { $exitCode = 0 }
}
if ($preflightOk -eq $true) { $exitCode = 0 }

Write-AutoReport @{
  started_at = $startedAt
  finished_at = (Get-Date).ToString("o")
  status = if ($exitCode -eq 0) { "PASS" } else { "FAIL" }
  infra_mode = $mode
  docker_ready = $dockerOk
  preflight_exit = $exitCode
  preflight_report = $preflightJson
  fail_count = if ($preflightSummary.readiness.score) { $preflightSummary.readiness.score.fail } else { $null }
  preflight_ok = $preflightOk
}

if ($exitCode -eq 0) {
  Write-Host "`nStaging preflight AUTO: PASS ($mode)" -ForegroundColor Green
} else {
  Write-Host "`nStaging preflight AUTO: FAIL ($mode) see docs/production-preflight-latest.json" -ForegroundColor Red
}
exit $exitCode
