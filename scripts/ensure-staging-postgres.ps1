# 内嵌 Postgres :5433 就绪（Docker 不可用时 staging 共用）
# Usage:
#   . scripts/ensure-staging-postgres.ps1; Ensure-StagingPostgres
#   powershell -File scripts/ensure-staging-postgres.ps1
param([switch]$Quiet)

$script:EnsureStagingPgRoot = if ($PSScriptRoot) { Split-Path -Parent $PSScriptRoot } else { Get-Location }
$script:EnsureStagingPgBin = "C:\Program Files\PostgreSQL\17\bin"
$script:EnsureStagingPgDir = Join-Path $script:EnsureStagingPgRoot "staging-data\postgres"

function Test-StagingPostgresReady {
  try {
    $null = & "$script:EnsureStagingPgBin\psql.exe" -h 127.0.0.1 -p 5433 -U youding -d youding_dev -c "SELECT 1;" 2>&1
    return ($LASTEXITCODE -eq 0)
  } catch { return $false }
}

function Ensure-StagingPostgres {
  if (Test-StagingPostgresReady) {
    if (-not $Quiet) { Write-Host "Postgres ready on :5433" -ForegroundColor DarkGray }
    return
  }
  if (-not (Test-Path "$script:EnsureStagingPgBin\pg_ctl.exe")) {
    throw "Postgres :5433 not ready and binaries missing at $script:EnsureStagingPgBin"
  }
  New-Item -ItemType Directory -Force -Path $script:EnsureStagingPgDir | Out-Null
  if (-not (Test-Path "$script:EnsureStagingPgDir\PG_VERSION")) {
    if (-not $Quiet) { Write-Host "Initializing embedded Postgres" -ForegroundColor Cyan }
    & "$script:EnsureStagingPgBin\initdb.exe" -D $script:EnsureStagingPgDir -U youding -A trust -E UTF8 --locale=C | Out-Null
  }
  $status = & "$script:EnsureStagingPgBin\pg_ctl.exe" status -D $script:EnsureStagingPgDir 2>&1 | Out-String
  if ($status -notmatch "server is running") {
    if (-not $Quiet) { Write-Host "Starting embedded Postgres on :5433" -ForegroundColor Cyan }
    & "$script:EnsureStagingPgBin\pg_ctl.exe" start -D $script:EnsureStagingPgDir -l "$script:EnsureStagingPgDir\server.log" -o "-p 5433" | Out-Null
    Start-Sleep -Seconds 3
  }
  $dbExists = & "$script:EnsureStagingPgBin\psql.exe" -h 127.0.0.1 -p 5433 -U youding -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='youding_dev';" 2>&1
  if ($dbExists -notmatch "1") {
    & "$script:EnsureStagingPgBin\psql.exe" -h 127.0.0.1 -p 5433 -U youding -d postgres -c "CREATE DATABASE youding_dev;" | Out-Null
  }
  if (-not (Test-StagingPostgresReady)) { throw "Embedded Postgres failed readiness on :5433" }
}

if ($MyInvocation.InvocationName -ne '.') {
  Ensure-StagingPostgres
  exit $(if (Test-StagingPostgresReady) { 0 } else { 1 })
}
