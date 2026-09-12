# MOD-06 · 尝试 bundleRelease 产出 AAB（需 JDK + Android SDK）
# Usage: powershell -ExecutionPolicy Bypass -File scripts/run-mod-06-aab-build.ps1
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$Android = Join-Path $Root "frontend\admin\android"
$Report = Join-Path $Root "docs\mod-06-aab-build-latest.json"
$Py = Join-Path $Root "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $Py)) { $Py = "python" }

$javaOk = $false
try {
  $null = & java -version 2>&1
  $javaOk = ($LASTEXITCODE -eq 0)
} catch { $javaOk = $false }

$payload = @{
  generated_at = (Get-Date).ToString("o")
  task = "MOD-06-aab-build"
  java_available = $javaOk
  gradlew_exit = $null
  aab_path = $null
  pass = $false
}

if (-not $javaOk) {
  $payload.note = "JDK 未检测到；跳过 bundleRelease"
  ($payload | ConvertTo-Json -Depth 4) | Set-Content -Path $Report -Encoding UTF8
  Write-Host "MOD-06 AAB build: SKIP (no JDK) -> $Report" -ForegroundColor Yellow
  exit 0
}

Push-Location $Android
& .\gradlew.bat bundleRelease 2>&1 | Out-Null
$payload.gradlew_exit = $LASTEXITCODE
Pop-Location

$aab = Get-ChildItem -Path (Join-Path $Android "app\build\outputs\bundle\release") -Filter "*.aab" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($aab) {
  $payload.aab_path = $aab.FullName
  $payload.pass = ($payload.gradlew_exit -eq 0)
}

($payload | ConvertTo-Json -Depth 4) | Set-Content -Path $Report -Encoding UTF8
& $Py (Join-Path $Root "scripts\validate-mod-06-android-aab.py") | Out-Null

if ($payload.pass) {
  Write-Host "MOD-06 AAB build: PASS -> $($payload.aab_path)" -ForegroundColor Green
  exit 0
}
Write-Host "MOD-06 AAB build: FAIL/SKIP -> $Report" -ForegroundColor Yellow
exit 0
