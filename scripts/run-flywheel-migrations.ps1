# D1：商业飞轮相关迁移一键 upgrade head
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Push-Location (Join-Path $Root "backend")

# 飞轮 P0 仅需 025–028；全量 head 请在 PostgreSQL 上执行（029+ 含 pgvector 等）
$Target = $(if ($env:ALEMBIC_TARGET) { $env:ALEMBIC_TARGET } else { "028_ubrain_action_audit" })
Write-Host "=== alembic upgrade $Target (flywheel 025-028) ===" -ForegroundColor Cyan
python -m alembic upgrade $Target
if ($LASTEXITCODE -ne 0) { Pop-Location; exit $LASTEXITCODE }

Pop-Location
Write-Host "`n=== verify ===" -ForegroundColor Cyan
& (Join-Path $Root "scripts\check-flywheel-migration.ps1")
