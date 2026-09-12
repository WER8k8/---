# MOD-06 · 安装 Capacitor 并 cap sync
# Usage: powershell -File scripts/install-mod-06-capacitor.ps1
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Admin = Join-Path $Root "frontend\admin"
$Report = Join-Path $Root "docs\mod-06-capacitor-install-latest.json"

Write-Host "=== MOD-06 npm install @capacitor/* ===" -ForegroundColor Cyan
Push-Location $Admin
$prevEap = $ErrorActionPreference
$ErrorActionPreference = "Continue"
npm install @capacitor/core @capacitor/cli @capacitor/android @capacitor/ios --save-dev --legacy-peer-deps 2>&1 | Out-Null
$installExit = $LASTEXITCODE
npm run build:cap 2>&1 | Out-Null
$buildExit = $LASTEXITCODE
npx cap sync 2>&1 | Out-Null
$syncExit = $LASTEXITCODE
if (-not (Test-Path $androidDir)) {
  npx cap add android 2>&1 | Out-Null
  if ($LASTEXITCODE -ne 0) { $syncExit = $LASTEXITCODE }
  npx cap sync 2>&1 | Out-Null
  if ($LASTEXITCODE -ne 0) { $syncExit = $LASTEXITCODE }
}
$ErrorActionPreference = $prevEap
Pop-Location

$androidDir = Join-Path $Admin "android"
$iosDir = Join-Path $Admin "ios"
$pass = ($installExit -eq 0) -and ($buildExit -eq 0) -and ($syncExit -eq 0) -and (Test-Path $androidDir)

$payload = @{
  generated_at = (Get-Date).ToString("o")
  task = "MOD-06-capacitor-install"
  pass = $pass
  npm_install_exit = $installExit
  build_cap_exit = $buildExit
  cap_sync_exit = $syncExit
  android_dir = (Test-Path $androidDir)
  ios_dir = (Test-Path $iosDir)
}
($payload | ConvertTo-Json -Depth 4) | Set-Content -Path $Report -Encoding UTF8

if ($pass) {
  Write-Host "MOD-06 capacitor install: PASS -> $Report" -ForegroundColor Green
  exit 0
}
Write-Host "MOD-06 capacitor install: FAIL -> $Report" -ForegroundColor Red
exit 1
