# MOD-06 · 出海计 App 构建链预检（web build + 可选 cap sync）
# Usage: powershell -File scripts/run-mod-06-cap-sync-prep.ps1
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Admin = Join-Path $Root "frontend\admin"
$Report = Join-Path $Root "docs\mod-06-cap-sync-prep-latest.json"
$Py = Join-Path $Root "backend\.venv\Scripts\python.exe"

Write-Host "=== MOD-06 npm run build:cap ===" -ForegroundColor Cyan
Push-Location $Admin
$prevEap = $ErrorActionPreference
$ErrorActionPreference = "Continue"
npm run build:cap 2>&1 | Out-Null
$buildExit = $LASTEXITCODE
$ErrorActionPreference = $prevEap
$distOk = Test-Path (Join-Path $Admin "dist\index.html")
$capCore = Test-Path (Join-Path $Admin "node_modules\@capacitor\core")
$capSyncExit = $null
if ($capCore -and $buildExit -eq 0) {
  Write-Host "=== MOD-06 cap sync ===" -ForegroundColor Cyan
  $ErrorActionPreference = "Continue"
  npm run cap:sync 2>&1 | Out-Null
  $capSyncExit = $LASTEXITCODE
  $ErrorActionPreference = $prevEap
}
Pop-Location

& $Py (Join-Path $Root "scripts\validate-mod-06-chuhaiji-app.py") 2>&1 | Out-Null
$validateExit = $LASTEXITCODE

$pass = ($buildExit -eq 0) -and $distOk -and ($validateExit -eq 0) -and (($null -eq $capSyncExit) -or ($capSyncExit -eq 0))

$payload = @{
  generated_at = (Get-Date).ToString("o")
  task = "MOD-06-cap-sync-prep"
  pass = $pass
  npm_build_exit = $buildExit
  dist_index_html = $distOk
  capacitor_installed = $capCore
  cap_sync_exit = $capSyncExit
  validate_mod06_exit = $validateExit
  note = $(if (-not $capCore) { "Install @capacitor/* then rerun for cap sync" } else { "cap sync attempted" })
}
($payload | ConvertTo-Json -Depth 4) | Set-Content -Path $Report -Encoding UTF8

if ($pass) {
  Write-Host "MOD-06 cap sync prep: PASS -> $Report" -ForegroundColor Green
  exit 0
}
Write-Host "MOD-06 cap sync prep: FAIL -> $Report" -ForegroundColor Red
exit 1
