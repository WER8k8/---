# One-shot gap-closure dev stack: sidecars + backend/admin + smoke
# Usage: powershell -File scripts/run-gap-closure-dev.ps1

param(
  [switch]$SkipStart,
  [switch]$ForceRestart
)

$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path -LiteralPath (Split-Path -Parent $PSScriptRoot)).Path
$Py = Join-Path $Root 'backend\.venv\Scripts\python.exe'

Write-Host '=== Gap closure dev stack ===' -ForegroundColor Cyan

if (-not $SkipStart) {
  & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root 'scripts\start-p6-sidecars-dev.ps1')
  if ($LASTEXITCODE -ne 0) { exit 1 }

  $launchArgs = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $Root 'scripts\launch-dev-admin-safe.ps1'))
  if ($ForceRestart) { $launchArgs += '-ForceRestart' }
  Start-Process powershell -WindowStyle Minimized -ArgumentList $launchArgs

  $deadline = (Get-Date).AddSeconds(120)
  $ready = $false
  while ((Get-Date) -lt $deadline) {
    try {
      Invoke-RestMethod -Uri 'http://127.0.0.1:8001/api/v1/health' -TimeoutSec 5 | Out-Null
      $ready = $true
      break
    } catch { Start-Sleep -Seconds 3 }
  }
  if (-not $ready) {
    Write-Host 'WARN backend not ready within 120s — smoke may fail' -ForegroundColor Yellow
  }
}

& $Py (Join-Path $Root 'scripts\smoke-gap-closure-dev.py')
exit $LASTEXITCODE
