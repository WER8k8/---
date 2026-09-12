# Start P6 B2B sidecars: P5 stack + LibreTranslate (:8098)
# Usage: powershell -File scripts/start-p6-sidecars-dev.ps1

$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path -LiteralPath (Split-Path -Parent $PSScriptRoot)).Path
$SidecarLauncher = Join-Path $Root 'scripts\start-sidecar-py-dev.ps1'

& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root 'scripts\start-p5-sidecars-dev.ps1')
if ($LASTEXITCODE -ne 0) { exit 1 }

$LtPort = 8098
$DevEnv = Join-Path $Root 'backend\config\dev\.env'

function Test-HttpOk([string]$Url) {
  try { Invoke-RestMethod -Uri $Url -TimeoutSec 4 | Out-Null; return $true } catch { return $false }
}

function Ensure-EnvBlock([string]$Marker, [string]$Block) {
  if (-not (Test-Path -LiteralPath $DevEnv)) { return }
  $text = Get-Content -LiteralPath $DevEnv -Raw -Encoding UTF8
  if ($text -match [regex]::Escape($Marker)) { return }
  if (-not $text.EndsWith("`n")) { $text += "`r`n" }
  $text += $Block
  Set-Content -LiteralPath $DevEnv -Value $text -Encoding UTF8 -NoNewline
}

Ensure-EnvBlock 'LIBRETRANSLATE_URL=' @"

# LibreTranslate sidecar (auto start-p6-sidecars-dev.ps1)
LIBRETRANSLATE_URL=http://127.0.0.1:8098
LIBRETRANSLATE_TOKEN=dev-sidecar-token
LIBRETRANSLATE_ALLOW_DEV_STUB=1
"@

$LtDir = Join-Path $Root 'deploy\examples\libretranslate-sidecar'
if (-not (Test-HttpOk "http://127.0.0.1:$LtPort/health")) {
  Write-Host "Starting LibreTranslate sidecar on :$LtPort" -ForegroundColor Cyan
  Start-Process powershell -WindowStyle Minimized -ArgumentList @(
    '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $SidecarLauncher,
    '-SidecarDir', $LtDir, '-PortEnv', 'LIBRETRANSLATE_PORT', '-Port', $LtPort,
    '-TokenEnv', 'LIBRETRANSLATE_TOKEN', '-Token', 'dev-sidecar-token',
    '-ExtraEnv', 'LIBRETRANSLATE_ALLOW_DEV_STUB=1'
  )
  Start-Sleep -Seconds 2
}

Write-Host ''
Write-Host 'P6 sidecars ready (LibreTranslate stub)' -ForegroundColor Green
Write-Host "  libretranslate   : http://127.0.0.1:$LtPort/health"
Write-Host '  Restart backend to load LIBRETRANSLATE_URL' -ForegroundColor Yellow
Write-Host ''
Write-Host 'Verify:' -ForegroundColor Cyan
Write-Host '  cd backend; .\.venv\Scripts\python.exe ..\scripts\verify-b2b-sidecars-all.py'
