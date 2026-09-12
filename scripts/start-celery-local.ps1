# OPS-04：本地启动 Celery worker + beat（需 Redis）
# Usage: 开两个终端分别运行 worker / beat，或本脚本仅打印命令

$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"

Write-Host "Celery 本地（需 Redis 6379 与 backend/.env CELERY_BROKER_URL）" -ForegroundColor Cyan
Write-Host ""
Write-Host "终端 1 — worker:"
Write-Host "  cd `"$Backend`""
Write-Host "  `$env:PYTHONPATH = (Get-Location).Path"
Write-Host "  celery -A app.tasks.celery_app worker -l info -P solo"
Write-Host ""
Write-Host "终端 2 — beat:"
Write-Host "  cd `"$Backend`""
Write-Host "  `$env:PYTHONPATH = (Get-Location).Path"
Write-Host "  celery -A app.tasks.celery_app beat -l info"
Write-Host ""
Write-Host "已注册 beat：SEO 每日/每周 + GEO 技术雷达/竞品/Rank Guard"
