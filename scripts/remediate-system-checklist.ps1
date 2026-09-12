# 系统问题清单一键修复（开发环境）
# Usage: powershell -File scripts/remediate-system-checklist.ps1
# 修复：Sidecar 栈、开发栈重启、假交付扫描、gap smoke、SEO/GEO、专家站会

param(
  [switch]$SkipExpertDaily
)

$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path -LiteralPath (Split-Path -Parent $PSScriptRoot)).Path
$Py = Join-Path $Root 'backend\.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Py)) { $Py = 'python' }

$results = @()

function Add-Result([string]$Name, [bool]$Ok, [string]$Detail = '') {
  $script:results += [PSCustomObject]@{ name = $Name; ok = $Ok; detail = $Detail }
}

Write-Host '=== 系统清单修复 ===' -ForegroundColor Cyan

# 1) 开发栈 + Sidecar
$start = Join-Path $Root 'scripts\start-dev-admin.ps1'
& powershell -NoProfile -ExecutionPolicy Bypass -File $start -ForceRestart -WithSidecars
Add-Result 'dev_stack_with_sidecars' ($LASTEXITCODE -eq 0)

# 2) 假交付扫描
& $Py (Join-Path $Root 'scripts\validate-no-fake-delivery.py') | Out-Null
Add-Result 'no_fake_delivery' ($LASTEXITCODE -eq 0)

# 3) B2B Sidecar 探针
& $Py (Join-Path $Root 'scripts\verify-b2b-sidecars-all.py') | Out-Null
Add-Result 'b2b_sidecars' ($LASTEXITCODE -eq 0)

# 4) Gap 闭环冒烟
& $Py (Join-Path $Root 'scripts\smoke-gap-closure-dev.py') | Out-Null
Add-Result 'gap_closure_smoke' ($LASTEXITCODE -eq 0)

# 5) 租户 SEO / GEO
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root 'scripts\run-tenant-seo-audit.ps1') | Out-Null
Add-Result 'tenant_seo_audit' ($LASTEXITCODE -eq 0)
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root 'scripts\run-tenant-geo-audit.ps1') | Out-Null
Add-Result 'tenant_geo_audit' ($LASTEXITCODE -eq 0)

# 6) 专家每日全量（可选，较慢）
if (-not $SkipExpertDaily) {
  & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root 'scripts\ops-expert-daily-run.ps1') -Quiet | Out-Null
  Add-Result 'expert_daily_roster' ($LASTEXITCODE -eq 0)
}

$fail = @($results | Where-Object { -not $_.ok })
Write-Host ''
Write-Host "完成: $($results.Count - $fail.Count)/$($results.Count)" -ForegroundColor $(if ($fail.Count -eq 0) { 'Green' } else { 'Yellow' })
foreach ($r in $results) {
  $mark = if ($r.ok) { 'OK' } else { 'FAIL' }
  Write-Host "  [$mark] $($r.name)"
}

if ($fail.Count -gt 0) {
  Write-Host ''
  Write-Host 'Owner-only (cannot auto-fix): HTTPS domain, DNS, Certbot, BJ-01 signoff, PM marketing review, E2E recording' -ForegroundColor DarkYellow
  exit 1
}
exit 0
