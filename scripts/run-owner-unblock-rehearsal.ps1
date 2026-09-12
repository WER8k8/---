# Owner 域就绪后 · 一键彩排（不修改生产）
# Usage: powershell -File scripts/run-owner-unblock-rehearsal.ps1
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$Py = Join-Path $Root "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $Py)) { $Py = "python" }

Write-Host "=== Owner unblock rehearsal pack ===" -ForegroundColor Cyan
& $Py (Join-Path $Root "scripts\validate-mod-08-owner-readiness.py")
& $Py (Join-Path $Root "scripts\validate-arch-04-certbot-preflight.py")
powershell -File (Join-Path $Root "scripts\run-mod-04-recording-rehearsal.ps1")
& $Py (Join-Path $Root "scripts\validate-mod-04-https-step.py")

if ($env:MOD04_HTTPS_DOMAIN) {
  Write-Host "MOD04_HTTPS_DOMAIN set — probing HTTPS step 7" -ForegroundColor Green
  & $Py (Join-Path $Root "scripts\validate-mod-04-https-step.py")
} else {
  Write-Host "Tip: set `$env:MOD04_HTTPS_DOMAIN before Certbot 实跑" -ForegroundColor Yellow
}

Write-Host "Done. See docs/r1-owner-handoff-pack.md" -ForegroundColor Green
