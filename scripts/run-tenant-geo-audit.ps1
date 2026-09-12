# 租户预览站 GEO/AEO 审计
param(
  [string]$Tenant = 'dev.local',
  [string]$NuxtBase = 'http://127.0.0.1:3000',
  [string]$ApiBase = 'http://127.0.0.1:8001',
  [switch]$SkipProbes
)

$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path -LiteralPath (Split-Path -Parent $PSScriptRoot)).Path
$Py = Join-Path $Root 'backend\.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Py)) { $Py = 'python' }

$args = @(
  (Join-Path $Root 'scripts\validate-tenant-geo-audit.py'),
  '--nuxt-base', $NuxtBase,
  '--api-base', $ApiBase,
  '--tenant', $Tenant
)
if ($SkipProbes -or $env:YOUDING_GEO_AUDIT_SKIP_PROBES -eq '1') { $args += '--skip-probes' }

Write-Host '=== Tenant GEO Audit ===' -ForegroundColor Cyan

try {
  Invoke-WebRequest -Uri "$NuxtBase/tenant?__tenant=$Tenant&lpro=1" -TimeoutSec 120 -UseBasicParsing | Out-Null
} catch {
  Write-Host "WARN nuxt warmup: $($_.Exception.Message)" -ForegroundColor Yellow
}

& $Py @args
exit $LASTEXITCODE
