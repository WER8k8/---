# Start P2 B2B sidecars: AI Find Customer + Domain Email + MediaCrawler
# Usage: powershell -File scripts/start-p2-sidecars-dev.ps1

$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path -LiteralPath (Split-Path -Parent $PSScriptRoot)).Path
$SidecarLauncher = Join-Path $Root 'scripts\start-sidecar-py-dev.ps1'

& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root 'scripts\start-ai-find-customer-dev.ps1')
if ($LASTEXITCODE -ne 0) { exit 1 }

$EmailPort = 8093
$MediaPort = 8094
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

Ensure-EnvBlock 'DOMAIN_EMAIL_EXTRACTOR_URL=' @"

# Domain email extractor (auto start-p2-sidecars-dev.ps1)
DOMAIN_EMAIL_EXTRACTOR_URL=http://127.0.0.1:8093
DOMAIN_EMAIL_EXTRACTOR_TOKEN=dev-sidecar-token
DOMAIN_EMAIL_EXTRACTOR_ALLOW_DEV_STUB=1
"@

Ensure-EnvBlock 'MEDIA_CRAWLER_URL=' @"

# MediaCrawler sidecar (auto start-p2-sidecars-dev.ps1)
MEDIA_CRAWLER_URL=http://127.0.0.1:8094
MEDIA_CRAWLER_TOKEN=dev-sidecar-token
MEDIA_CRAWLER_ALLOW_DEV_STUB=1
ECOMMERCE_SOCIAL_SPIDERS_ENABLED=1
ECOMMERCE_SPIDER_ENABLE_MEDIA_FACEBOOK=1
"@

$EmailDir = Join-Path $Root 'deploy\examples\domain-email-extractor-sidecar'
if (-not (Test-HttpOk "http://127.0.0.1:$EmailPort/health")) {
  Write-Host "Starting domain email extractor on :$EmailPort" -ForegroundColor Cyan
  Start-Process powershell -WindowStyle Minimized -ArgumentList @(
    '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $SidecarLauncher,
    '-SidecarDir', $EmailDir, '-PortEnv', 'DOMAIN_EMAIL_EXTRACTOR_PORT', '-Port', $EmailPort,
    '-TokenEnv', 'DOMAIN_EMAIL_EXTRACTOR_TOKEN', '-Token', 'dev-sidecar-token'
  )
  Start-Sleep -Seconds 3
}

$MediaDir = Join-Path $Root 'deploy\examples\media-crawler-sidecar'
if (-not (Test-HttpOk "http://127.0.0.1:$MediaPort/health")) {
  Write-Host "Starting MediaCrawler sidecar on :$MediaPort" -ForegroundColor Cyan
  Start-Process powershell -WindowStyle Minimized -ArgumentList @(
    '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $SidecarLauncher,
    '-SidecarDir', $MediaDir, '-PortEnv', 'MEDIA_CRAWLER_PORT', '-Port', $MediaPort,
    '-TokenEnv', 'MEDIA_CRAWLER_TOKEN', '-Token', 'dev-sidecar-token'
  )
  Start-Sleep -Seconds 3
}

Write-Host ''
Write-Host 'P2 sidecars ready (dev stub mode)' -ForegroundColor Green
Write-Host "  email extractor : http://127.0.0.1:$EmailPort/health"
Write-Host "  media crawler   : http://127.0.0.1:$MediaPort/health"
Write-Host '  Restart backend to load new .env keys' -ForegroundColor Yellow
Write-Host ''
Write-Host 'Verify:' -ForegroundColor Cyan
Write-Host '  cd backend; .\.venv\Scripts\python.exe ..\scripts\verify-domain-email-extractor-sidecar.py --smoke'
Write-Host '  cd backend; .\.venv\Scripts\python.exe ..\scripts\verify-media-crawler-sidecar.py'
