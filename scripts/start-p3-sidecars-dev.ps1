# Start P3 B2B sidecars: P2 stack + LinkedIn decision-maker (:8095)
# Usage: powershell -File scripts/start-p3-sidecars-dev.ps1

$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path -LiteralPath (Split-Path -Parent $PSScriptRoot)).Path
$SidecarLauncher = Join-Path $Root 'scripts\start-sidecar-py-dev.ps1'

& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root 'scripts\start-p2-sidecars-dev.ps1')
if ($LASTEXITCODE -ne 0) { exit 1 }

$LinkedInPort = 8095
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

Ensure-EnvBlock 'LINKEDIN_DECISION_MAKER_URL=' @"

# LinkedIn decision maker (auto start-p3-sidecars-dev.ps1)
LINKEDIN_DECISION_MAKER_URL=http://127.0.0.1:8095
LINKEDIN_DECISION_MAKER_TOKEN=dev-sidecar-token
LINKEDIN_DECISION_MAKER_ALLOW_DEV_STUB=1
"@

$LiDir = Join-Path $Root 'deploy\examples\linkedin-scraper-sidecar'
if (-not (Test-HttpOk "http://127.0.0.1:$LinkedInPort/health")) {
  Write-Host "Starting LinkedIn decision-maker sidecar on :$LinkedInPort" -ForegroundColor Cyan
  Start-Process powershell -WindowStyle Minimized -ArgumentList @(
    '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $SidecarLauncher,
    '-SidecarDir', $LiDir, '-PortEnv', 'LINKEDIN_DECISION_MAKER_PORT', '-Port', $LinkedInPort,
    '-TokenEnv', 'LINKEDIN_DECISION_MAKER_TOKEN', '-Token', 'dev-sidecar-token',
    '-ExtraEnv', 'LINKEDIN_DECISION_MAKER_ALLOW_DEV_STUB=1'
  )
  Start-Sleep -Seconds 3
}

Write-Host ''
Write-Host 'P3 sidecars ready (dev stub mode)' -ForegroundColor Green
Write-Host "  linkedin DM      : http://127.0.0.1:$LinkedInPort/health"
Write-Host '  Restart backend to load LINKEDIN_DECISION_MAKER_URL' -ForegroundColor Yellow
Write-Host ''
Write-Host 'Verify:' -ForegroundColor Cyan
Write-Host '  cd backend; .\.venv\Scripts\python.exe ..\scripts\verify-linkedin-decision-maker-sidecar.py --smoke'
Write-Host '  cd backend; .\.venv\Scripts\python.exe ..\scripts\verify-customs-buyer-brief.py'
