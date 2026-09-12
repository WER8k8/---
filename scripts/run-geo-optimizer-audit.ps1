# GEO Optimizer 审计包装 — 对齐 geo-optimizer-skill / validate-tenant-geo-audit
param(
  [string]$Tenant = 'dev.local',
  [switch]$SkipProbes
)

$Root = (Resolve-Path -LiteralPath (Split-Path -Parent $PSScriptRoot)).Path
$GeoScript = Join-Path $Root 'scripts\run-tenant-geo-audit.ps1'
$args = @('-Tenant', $Tenant)
if ($SkipProbes) { $args += '-SkipProbes' }

Write-Host '=== GEO Optimizer Audit (wrapper) ===' -ForegroundColor Cyan
powershell -File $GeoScript @args
exit $LASTEXITCODE
