# JD-02 · 90 秒送检分镜路由门禁（只读检查，不启动浏览器）
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host '[demo-storyboard] check-nav-routes...'
node frontend/admin/scripts/check-nav-routes.mjs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$required = @(
  '/login',
  '/admin/dashboard',
  '/inquiries',
  '/admin/tenants',
  '/client/dashboard'
)

Write-Host '[demo-storyboard] verify LOCKED §10 paths in router meta...'
$routerFile = Join-Path $root 'frontend/admin/src/router/index.ts'
if (-not (Test-Path $routerFile)) {
  Write-Error "router not found: $routerFile"
}

$routerText = Get-Content -Raw -Path $routerFile
$missing = @()
foreach ($p in $required) {
  $escaped = [regex]::Escape($p)
  if ($routerText -notmatch $escaped) {
    $missing += $p
  }
}

if ($missing.Count -gt 0) {
  Write-Host 'MISSING paths in router:' ($missing -join ', ')
  exit 1
}

Write-Host '[demo-storyboard] OK — routes present for Owner walkthrough'
Write-Host '  Next: scripts/start-dev-admin.ps1 → follow docs/design/demo-90s-storyboard-202606.md'
