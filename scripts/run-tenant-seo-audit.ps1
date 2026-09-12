# 租户预览站 SEO 审计 — 一键（需 Nuxt :3000 + API :8001）
# Usage: powershell -File scripts/run-tenant-seo-audit.ps1

param(
  [string]$Tenant = 'dev.local',
  [string]$NuxtBase = 'http://127.0.0.1:3000',
  [string]$ApiBase = 'http://127.0.0.1:8001'
)

$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path -LiteralPath (Split-Path -Parent $PSScriptRoot)).Path
$Py = Join-Path $Root 'backend\.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Py)) { $Py = 'python' }

Write-Host '=== Tenant SEO Audit ===' -ForegroundColor Cyan
Write-Host "Nuxt: $NuxtBase  API: $ApiBase  tenant: $Tenant"

# 冷启动预热（Nuxt 首次 SSR 可能 >30s）
try {
  Invoke-WebRequest -Uri "$NuxtBase/tenant?__tenant=$Tenant&lpro=1" -TimeoutSec 120 -UseBasicParsing | Out-Null
} catch {
  Write-Host "WARN nuxt warmup: $($_.Exception.Message)" -ForegroundColor Yellow
}

& $Py (Join-Path $Root 'scripts\validate-tenant-seo-audit.py') `
  --nuxt-base $NuxtBase `
  --api-base $ApiBase `
  --tenant $Tenant

exit $LASTEXITCODE
