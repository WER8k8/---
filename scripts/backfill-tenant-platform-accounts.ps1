# 为历史租户补全 platform_accounts 占位
# 用法: powershell -File scripts/backfill-tenant-platform-accounts.ps1 [-DryRun]

param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not $env:DATABASE_URL) {
    $env:DATABASE_URL = "sqlite:///./youding_dev.db"
    $env:ENVIRONMENT = "development"
    $env:PYTHONPATH = Join-Path $root "backend"
}

$args = @()
if ($DryRun) { $args += "--dry-run" }

python (Join-Path $root "scripts\backfill_tenant_platform_accounts.py") @args
