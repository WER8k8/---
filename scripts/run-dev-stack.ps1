# 启动本地 Postgres+Redis（T-ENV-04 / T-OPS-REDIS，藏云阁镜像加速）
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
& (Join-Path $Root "scripts/docker-with-cncfstack.ps1") -Profile dev up -d
Write-Host "Postgres: postgresql://youding:youding@127.0.0.1:5433/youding_dev"
Write-Host "Redis: redis://127.0.0.1:6379/0"
