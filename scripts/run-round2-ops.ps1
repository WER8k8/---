# 第二轮运营验收
# Usage: powershell -ExecutionPolicy Bypass -File scripts\run-round2-ops.ps1

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$BackupDir = Join-Path $Root "docs\round2-backup"
$py = Join-Path $Backend ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
$ts = Get-Date -Format "yyyyMMdd-HHmmss"

$dbPaths = @(
    (Join-Path $Backend "youding_dev.db"),
    (Join-Path $Root "youding_dev.db")
)
foreach ($f in @(".env")) {
    $src = Join-Path $Backend $f
    if (Test-Path $src) {
        Copy-Item $src (Join-Path $BackupDir "${f}.$ts") -Force
        Write-Host "Backed up $f -> docs\round2-backup\${f}.$ts" -ForegroundColor Green
    } else {
        Write-Host "Skip backup (missing): $f" -ForegroundColor Yellow
    }
}
$dbBacked = $false
foreach ($src in $dbPaths) {
    if ((Test-Path $src) -and (Get-Item $src).Length -gt 0) {
        $name = "youding_dev.db"
        Copy-Item $src (Join-Path $BackupDir "${name}.$ts") -Force
        Write-Host "Backed up $src -> docs\round2-backup\${name}.$ts" -ForegroundColor Green
        $dbBacked = $true
        break
    }
}
if (-not $dbBacked) {
    Write-Host "Skip DB backup: no non-empty youding_dev.db under backend/ or repo root" -ForegroundColor Yellow
}

Write-Host "`n=== Celery (print commands) ===" -ForegroundColor Cyan
powershell -ExecutionPolicy Bypass -File (Join-Path $Root "scripts\start-celery-local.ps1")

Write-Host "`n=== Production preflight (--production) ===" -ForegroundColor Cyan
$env:JWT_SECRET_KEY = "preflight-prod-" + ("x" * 32)
$env:PREFLIGHT_ENVIRONMENT = "production"
& $py (Join-Path $Root "scripts\run_production_preflight.py") --production

Write-Host "`nOps round2 script done. Fill docs\round2-ops-signoff.json" -ForegroundColor Green
