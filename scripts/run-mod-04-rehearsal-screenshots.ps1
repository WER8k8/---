# MOD-04 · 七步录屏彩排截图（依赖 vite preview）
# Usage: powershell -File scripts/run-mod-04-rehearsal-screenshots.ps1
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$Py = Join-Path $Root "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $Py)) { $Py = "python" }

powershell -File (Join-Path $Root "scripts\run-mod-04-recording-rehearsal.ps1") | Out-Null
if ($env:MOD04_BASE_URL) {
  $base = $env:MOD04_BASE_URL
} else {
  $base = "http://127.0.0.1:4173"
}
$env:MOD04_BASE_URL = $base

Push-Location (Join-Path $Root "frontend\admin")
node scripts/mod-04-rehearsal-screenshots.mjs
$nodeExit = $LASTEXITCODE
Pop-Location

& $Py (Join-Path $Root "scripts\validate-mod-04-rehearsal-screenshots.py")
exit $(if ($LASTEXITCODE -eq 0 -and $nodeExit -eq 0) { 0 } else { 1 })
