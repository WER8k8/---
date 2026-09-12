# T-PREFLIGHT：生产形态预检（本地模拟 production 环境变量）
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Py = Join-Path $Root "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $Py)) { $Py = "python" }

$env:ENVIRONMENT = "production"
$env:MVP_LAUNCH = if ($env:MVP_LAUNCH) { $env:MVP_LAUNCH } else { "0" }
if (-not $env:JWT_SECRET_KEY) { $env:JWT_SECRET_KEY = "preflight-" + ("x" * 32) }
if (-not $env:SECRET_KEY) { $env:SECRET_KEY = $env:JWT_SECRET_KEY }
if (-not $env:DATABASE_URL) {
  Write-Host "提示: 未设 DATABASE_URL，将按 SQLite 检查（生产应 postgresql://）"
}

& $Py (Join-Path $Root "scripts\run_production_preflight.py") --production
exit $LASTEXITCODE
