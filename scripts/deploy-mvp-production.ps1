# 主站商用 MVP — 生产部署门禁（阶段 A～C）
# 用法:
#   cd "website CodeBuddy"
#   copy .env.prod.example .env.prod   # 填好密钥后
#   powershell -File scripts/deploy-mvp-production.ps1
#   powershell -File scripts/deploy-mvp-production.ps1 -SkipMigrate
#   powershell -File scripts/deploy-mvp-production.ps1 -ComposeUp

param(
    [switch]$SkipMigrate,
    [switch]$ComposeUp,
    [string]$EnvFile = ".env.prod"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Write-Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }

if (-not (Test-Path $EnvFile)) {
    Write-Host "缺少 $EnvFile，请从 .env.prod.example 复制并填写。" -ForegroundColor Red
    exit 1
}

# 加载 .env.prod 到当前进程（简单 KEY=VALUE）
Get-Content $EnvFile | ForEach-Object {
    if ($_ -match '^\s*#' -or $_ -match '^\s*$') { return }
    if ($_ -match '^\s*([^#=]+)=(.*)$') {
        $k = $matches[1].Trim()
        $v = $matches[2].Trim().Trim('"')
        [Environment]::SetEnvironmentVariable($k, $v, "Process")
    }
}

$env:PYTHONPATH = Join-Path $Root "backend"
$env:ENVIRONMENT = if ($env:ENVIRONMENT) { $env:ENVIRONMENT } else { "production" }
$env:MVP_LAUNCH = if ($env:MVP_LAUNCH) { $env:MVP_LAUNCH } else { "1" }
$env:PREFLIGHT_ENVIRONMENT = "production"
$env:PREFLIGHT_MVP_LAUNCH = "1"

if (-not $env:JWT_SECRET_KEY -or $env:JWT_SECRET_KEY.Length -lt 32) {
    Write-Host "JWT_SECRET_KEY 未设置或长度 < 32" -ForegroundColor Red
    exit 1
}

Write-Step "A1 路由挂载检查"
python scripts/check_mounted_routes.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if (-not $SkipMigrate) {
    Write-Step "A2 生产库迁移 + 40 平台种子"
    Push-Location (Join-Path $Root "backend")
    try {
        python scripts/migrate_production.py --seed-full
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    } finally {
        Pop-Location
    }
}

Write-Step "A3 流量管线自检（SQLite 模拟，仅逻辑）"
python scripts/verify_traffic_pipeline.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "流量自检失败（若仅本机无 Postgres 可忽略，生产库上再跑）" -ForegroundColor Yellow
}

Write-Step "C 生产预检（MVP 模式）"
python scripts/run_production_preflight.py
$preflight = $LASTEXITCODE

if ($ComposeUp) {
    Write-Step "Docker Compose 启动（藏云阁镜像加速）"
    & (Join-Path $Root "scripts/docker-with-cncfstack.ps1") -Profile prod -EnvFile $EnvFile up -d
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Write-Host "等待 backend 健康检查..." -ForegroundColor Gray
    Start-Sleep -Seconds 15
    & (Join-Path $Root "scripts/docker-with-cncfstack.ps1") -Profile prod -EnvFile $EnvFile ps
}

Write-Step "完成"
Write-Host "预检报告: docs/production-preflight-latest.json"
if ($preflight -ne 0) {
    Write-Host "预检未全绿：请打开 JSON 查看 required fail 项（生产机需 Postgres 连通）。" -ForegroundColor Yellow
    exit $preflight
}
Write-Host "MVP 门禁通过（本机路由层）。生产机请再跑一遍并做 L3 人工验通。" -ForegroundColor Green
exit 0
