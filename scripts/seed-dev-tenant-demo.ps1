# 创建本地租户演示账号 tenant_demo / TenantDemo@2026!
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location (Join-Path $Root "backend")
$env:PYTHONPATH = (Get-Location).Path
$env:DATABASE_URL = "sqlite:///./youding_dev.db"
$env:ENVIRONMENT = "development"
.\.venv\Scripts\python.exe (Join-Path $Root "scripts\seed_dev_tenant_demo.py")
