# DF-09：DeerFlow 租户队列 Celery Worker（生产）
# 在 backend 目录执行；需 Redis + 已配置 CELERY_BROKER_URL

param(
    [string]$Queue = "deerflow",
    [int]$Concurrency = 2
)

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path (Split-Path -Parent $here) "backend"
Set-Location $backend

$env:PYTHONPATH = "."
Write-Host "Starting Celery worker queue=$Queue concurrency=$Concurrency" -ForegroundColor Cyan
celery -A app.tasks.celery_app:celery_app worker -Q $Queue -c $Concurrency -l info
