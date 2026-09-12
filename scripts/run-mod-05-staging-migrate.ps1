# MOD-05 · staging Postgres 执行 025/026 迁移并校验
# Usage: powershell -ExecutionPolicy Bypass -File scripts/run-mod-05-staging-migrate.ps1
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Py = Join-Path $Backend ".venv\Scripts\python.exe"
$Report = Join-Path $Root "docs\mod-05-staging-migrate-latest.json"

. (Join-Path $Root "scripts\ensure-staging-postgres.ps1")

$env:DATABASE_URL = "postgresql://youding:youding@127.0.0.1:5433/youding_dev"
$env:PYTHONPATH = $Backend

Ensure-StagingPostgres

Write-Host "=== MOD-05 alembic upgrade head ===" -ForegroundColor Cyan
Push-Location $Backend
$prevEap = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& $Py -m alembic upgrade head 2>&1 | Out-Null
$upgradeExit = $LASTEXITCODE
Pop-Location

& $Py (Join-Path $Root "scripts\validate-mod-05-staging-tables.py") 2>&1 | Out-Null
$tablesExit = $LASTEXITCODE
& $Py (Join-Path $Root "scripts\validate-mod-05-migrations.py") 2>&1 | Out-Null
$validateExit = $LASTEXITCODE
$ErrorActionPreference = $prevEap

$pass = ($tablesExit -eq 0) -and ($validateExit -eq 0) -and (($upgradeExit -eq 0) -or ($tablesExit -eq 0))

$payload = @{
  generated_at = (Get-Date).ToString("o")
  task = "MOD-05-staging-migrate"
  pass = $pass
  alembic_upgrade_exit = $upgradeExit
  staging_tables_exit = $tablesExit
  validate_mod05_exit = $validateExit
  database_url = "postgresql://youding:***@127.0.0.1:5433/youding_dev"
}
($payload | ConvertTo-Json -Depth 4) | Set-Content -Path $Report -Encoding UTF8

if ($pass) {
  Write-Host "MOD-05 staging migrate: PASS -> $Report" -ForegroundColor Green
  exit 0
}
Write-Host "MOD-05 staging migrate: FAIL -> $Report" -ForegroundColor Red
exit 1
