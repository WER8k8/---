# 步骤 6 · 送检彩排自动化门禁（JD-02 + cert:gate + 登录锁）
$ErrorActionPreference = 'Stop'
$Root = Split-Path $PSScriptRoot -Parent

Write-Host '=== Step 6 Demo Gate ==='

& (Join-Path $Root 'scripts\verify-login-entry-lock.ps1')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& (Join-Path $Root 'scripts\verify-shell-nav-program.ps1')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& (Join-Path $Root 'scripts\verify-demo-storyboard.ps1')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Push-Location (Join-Path $Root 'frontend\admin')
Write-Host '[step6] cert:gate...'
npm run cert:gate --silent
if ($LASTEXITCODE -ne 0) { Pop-Location; exit $LASTEXITCODE }
Pop-Location

$noFake = Join-Path $Root 'scripts\validate-no-fake-delivery.py'
if (Test-Path $noFake) {
  Write-Host '[step6] validate-no-fake-delivery...'
  python $noFake
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Host ''
Write-Host '=== Step 6 automation OK ==='
Write-Host 'Owner: scripts/start-dev-admin.ps1 -> docs/design/demo-90s-storyboard-202606.md (录屏 90s)'
Write-Host 'Report: docs/certification-gate-admin-latest.json'
