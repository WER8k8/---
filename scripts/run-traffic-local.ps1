# 本地流量看板联调（SQLite，无需 Postgres）
# 用法：在仓库根目录  powershell -File scripts/run-traffic-local.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$dbFile = Join-Path $Backend "youding_traffic_verify.db"

$env:PYTHONPATH = $Backend
$env:DATABASE_URL = "sqlite:///$($dbFile -replace '\\','/')"
$env:ENVIRONMENT = "development"
$env:REDIS_ENABLED = "false"
if (-not $env:SECRET_KEY) { $env:SECRET_KEY = "dev-local-secret-key-32chars-minimum!!" }
if (-not $env:JWT_SECRET_KEY) { $env:JWT_SECRET_KEY = "dev-local-jwt-secret-key-32chars-min!!" }

Write-Host "==> 验证流量链路"
python (Join-Path $Root "scripts\verify_traffic_pipeline.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "==> 启动 API http://127.0.0.1:8765 (Ctrl+C 停止)"
Set-Location $Backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8765 --reload
