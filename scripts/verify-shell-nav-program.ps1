# 导航壳层项目门禁 — 对齐 .project/shell-nav-program.json
$ErrorActionPreference = 'Stop'
$Root = Split-Path $PSScriptRoot -Parent

Push-Location (Join-Path $Root 'frontend\admin')

Write-Host '[shell-nav] vitest shellNavKernel...'
npx vitest run tests/unit/shellNavKernel.test.ts
if ($LASTEXITCODE -ne 0) { Pop-Location; exit $LASTEXITCODE }

Write-Host '[shell-nav] check-nav-routes...'
node scripts/check-nav-routes.mjs
if ($LASTEXITCODE -ne 0) { Pop-Location; exit $LASTEXITCODE }

Pop-Location
Write-Host '[shell-nav] OK'
