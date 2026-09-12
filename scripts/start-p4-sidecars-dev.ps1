# Start P4 B2B sidecars: P3 stack + CustomsDataSpider (:8096)
# Usage: powershell -File scripts/start-p4-sidecars-dev.ps1

$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path -LiteralPath (Split-Path -Parent $PSScriptRoot)).Path
$SidecarLauncher = Join-Path $Root 'scripts\start-sidecar-py-dev.ps1'

& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root 'scripts\start-p3-sidecars-dev.ps1')
if ($LASTEXITCODE -ne 0) { exit 1 }

$CustomsPort = 8096
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

Ensure-EnvBlock 'CUSTOMS_DATA_SPIDER_URL=' @"

# CustomsDataSpider sidecar (auto start-p4-sidecars-dev.ps1)
CUSTOMS_DATA_SPIDER_URL=http://127.0.0.1:8096
CUSTOMS_DATA_SPIDER_TOKEN=dev-sidecar-token
CUSTOMS_DATA_SPIDER_ALLOW_DEV_STUB=1
"@

$CustomsDir = Join-Path $Root 'deploy\examples\customs-data-spider-sidecar'
if (-not (Test-HttpOk "http://127.0.0.1:$CustomsPort/health")) {
  Write-Host "Starting CustomsDataSpider sidecar on :$CustomsPort" -ForegroundColor Cyan
  Start-Process powershell -WindowStyle Minimized -ArgumentList @(
    '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $SidecarLauncher,
    '-SidecarDir', $CustomsDir, '-PortEnv', 'CUSTOMS_DATA_SPIDER_PORT', '-Port', $CustomsPort,
    '-TokenEnv', 'CUSTOMS_DATA_SPIDER_TOKEN', '-Token', 'dev-sidecar-token',
    '-ExtraEnv', 'CUSTOMS_DATA_SPIDER_ALLOW_DEV_STUB=1'
  )
  Start-Sleep -Seconds 3
}

Write-Host ''
Write-Host 'P4 sidecars ready (dev stub mode)' -ForegroundColor Green
Write-Host "  customs spider   : http://127.0.0.1:$CustomsPort/health"
Write-Host '  Restart backend to load CUSTOMS_DATA_SPIDER_URL' -ForegroundColor Yellow
Write-Host ''
Write-Host 'Verify:' -ForegroundColor Cyan
Write-Host '  cd backend; .\.venv\Scripts\python.exe ..\scripts\verify-customs-data-spider-sidecar.py --smoke'
Write-Host '  cd backend; .\.venv\Scripts\python.exe ..\scripts\verify-customs-buyer-brief.py'
