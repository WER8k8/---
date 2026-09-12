# O-4: Wire real B2B upstream (AI_Find_Customer) — clone → upstream → adapter → backend env
# Usage:
#   powershell -File scripts/run-o4-b2b-upstream-wire.ps1
#   powershell -File scripts/run-o4-b2b-upstream-wire.ps1 -UpstreamRoot D:\refs\AI_Find_Customer -SkipClone
#   powershell -File scripts/run-o4-b2b-upstream-wire.ps1 -WireOnly   # env only, no process start

param(
  [string]$UpstreamRoot = '',
  [int]$UpstreamPort = 8080,
  [int]$SidecarPort = 8092,
  [switch]$SkipClone,
  [switch]$SkipRestart,
  [switch]$WireOnly
)

$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path -LiteralPath (Split-Path -Parent $PSScriptRoot)).Path
$Py = Join-Path $Root 'backend\.venv\Scripts\python.exe'

function Test-HttpOk([string]$Url) {
  try { Invoke-RestMethod -Uri $Url -TimeoutSec 5 | Out-Null; return $true } catch { return $false }
}

Write-Host '=== O-4 B2B real upstream wire (AI_Find_Customer) ===' -ForegroundColor Cyan

if (-not $SkipClone) {
  & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root 'scripts\clone-b2b-upstreams.ps1') -Shallow
  if ($LASTEXITCODE -ne 0) {
    Write-Host 'WARN clone step failed (network?) — use -SkipClone -UpstreamRoot <path> if you cloned manually' -ForegroundColor Yellow
  }
}

if (-not $UpstreamRoot) {
  $UpstreamRoot = Join-Path $Root 'deploy\upstreams\AI_Find_Customer'
}

$upstreamBackend = Join-Path $UpstreamRoot 'backend\api\app.py'
if (-not (Test-Path -LiteralPath $upstreamBackend)) {
  Write-Host '' 
  Write-Host 'BLOCKED: AI_Find_Customer not present at:' -ForegroundColor Red
  Write-Host "  $UpstreamRoot" -ForegroundColor Red
  Write-Host '' 
  Write-Host 'Owner steps (VPS or machine with GitHub):' -ForegroundColor Yellow
  Write-Host '  1. git clone --depth 1 https://github.com/xiongQvQ/AI_Find_Customer.git deploy/upstreams/AI_Find_Customer'
  Write-Host '  2. cd deploy/upstreams/AI_Find_Customer/backend && copy .env.example .env'
  Write-Host '  3. Fill MINIMAX_API_KEY + TAVILY_API_KEY + SERPER_API_KEY in backend/.env'
  Write-Host '  4. Re-run: powershell -File scripts/run-o4-b2b-upstream-wire.ps1 -SkipClone'
  exit 2
}

if (-not $WireOnly) {
  & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root 'scripts\start-ai-find-customer-upstream-dev.ps1') `
    -UpstreamRoot $UpstreamRoot -Port $UpstreamPort
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

  & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root 'scripts\start-ai-find-customer-dev.ps1') -Stop 2>$null | Out-Null

  $adapterLauncher = Join-Path $Root 'scripts\start-ai-find-customer-adapter-dev.ps1'
  if (-not (Test-HttpOk "http://127.0.0.1:$SidecarPort/health")) {
    Write-Host "Starting sidecar adapter :$SidecarPort -> upstream :$UpstreamPort" -ForegroundColor Cyan
    Start-Process powershell -WindowStyle Minimized -ArgumentList @(
      '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $adapterLauncher,
      '-Root', $Root, '-UpstreamUrl', "http://127.0.0.1:$UpstreamPort", '-Port', $SidecarPort
    )
    $deadline = (Get-Date).AddSeconds(30)
    while ((Get-Date) -lt $deadline) {
      if (Test-HttpOk "http://127.0.0.1:$SidecarPort/health") { break }
      Start-Sleep -Seconds 1
    }
  }
}

& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root 'scripts\connect-b2b-upstream.ps1') `
  -Name AI_Find_Customer -UpstreamUrl "http://127.0.0.1:$UpstreamPort"

if (-not $SkipRestart) {
  Start-Process powershell -WindowStyle Minimized -ArgumentList @(
    '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
    (Join-Path $Root 'scripts\launch-dev-admin-safe.ps1'), '-ForceRestart'
  )
  $deadline = (Get-Date).AddSeconds(120)
  while ((Get-Date) -lt $deadline) {
    if (Test-HttpOk 'http://127.0.0.1:8001/api/v1/health') { break }
    Start-Sleep -Seconds 3
  }
}

& $Py (Join-Path $Root 'scripts\validate-o4-b2b-upstream-wire.py')
exit $LASTEXITCODE
