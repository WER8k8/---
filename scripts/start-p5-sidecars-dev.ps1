# Start P5 B2B sidecars: P4 stack + IMAP read-only inquiry (:8097)
# Usage: powershell -File scripts/start-p5-sidecars-dev.ps1

$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path -LiteralPath (Split-Path -Parent $PSScriptRoot)).Path
$SidecarLauncher = Join-Path $Root 'scripts\start-sidecar-py-dev.ps1'

& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root 'scripts\start-p4-sidecars-dev.ps1')
if ($LASTEXITCODE -ne 0) { exit 1 }

$ImapPort = 8097
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

Ensure-EnvBlock 'IMAP_INQUIRY_URL=' @"

# IMAP read-only inquiry (auto start-p5-sidecars-dev.ps1)
IMAP_INQUIRY_URL=http://127.0.0.1:8097
IMAP_INQUIRY_TOKEN=dev-sidecar-token
IMAP_INQUIRY_ALLOW_DEV_STUB=1
"@

$ImapDir = Join-Path $Root 'deploy\examples\imap-inquiry-sidecar'
if (-not (Test-HttpOk "http://127.0.0.1:$ImapPort/health")) {
  Write-Host "Starting IMAP inquiry sidecar on :$ImapPort" -ForegroundColor Cyan
  Start-Process powershell -WindowStyle Minimized -ArgumentList @(
    '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $SidecarLauncher,
    '-SidecarDir', $ImapDir, '-PortEnv', 'IMAP_INQUIRY_PORT', '-Port', $ImapPort,
    '-TokenEnv', 'IMAP_INQUIRY_TOKEN', '-Token', 'dev-sidecar-token',
    '-ExtraEnv', 'IMAP_INQUIRY_ALLOW_DEV_STUB=1'
  )
  Start-Sleep -Seconds 3
}

Write-Host ''
Write-Host 'P5 sidecars ready (read-only IMAP stub)' -ForegroundColor Green
Write-Host "  imap inquiry     : http://127.0.0.1:$ImapPort/health"
Write-Host '  Restart backend to load IMAP_INQUIRY_URL' -ForegroundColor Yellow
Write-Host ''
Write-Host 'Verify:' -ForegroundColor Cyan
Write-Host '  cd backend; .\.venv\Scripts\python.exe ..\scripts\verify-imap-inquiry-sidecar.py --smoke'
Write-Host '  cd backend; .\.venv\Scripts\python.exe -m pytest tests/unit/test_p5_sidecars.py -q'
