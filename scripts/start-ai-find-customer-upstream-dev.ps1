# Start real AI_Find_Customer upstream (xiongQvQ/AI_Find_Customer backend)
# Usage:
#   powershell -File scripts/start-ai-find-customer-upstream-dev.ps1
#   powershell -File scripts/start-ai-find-customer-upstream-dev.ps1 -UpstreamRoot D:\refs\AI_Find_Customer
param(
  [string]$UpstreamRoot = '',
  [int]$Port = 8080,
  [switch]$Stop
)

$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path -LiteralPath (Split-Path -Parent $PSScriptRoot)).Path
if (-not $UpstreamRoot) {
  $UpstreamRoot = Join-Path $Root 'deploy\upstreams\AI_Find_Customer'
}
$BackendDir = Join-Path $UpstreamRoot 'backend'

function Stop-PortListener([int]$PortNum) {
  Get-NetTCPConnection -LocalPort $PortNum -State Listen -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique |
    ForEach-Object {
      if ($_ -and $_ -ne $PID) {
        Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
      }
    }
}

function Test-HttpOk([string]$Url) {
  try { Invoke-RestMethod -Uri $Url -TimeoutSec 5 | Out-Null; return $true } catch { return $false }
}

if ($Stop) {
  Stop-PortListener $Port
  Write-Host "Stopped listener on :$Port" -ForegroundColor Green
  exit 0
}

if (-not (Test-Path -LiteralPath (Join-Path $BackendDir 'api\app.py'))) {
  Write-Host "FAIL missing upstream backend at $BackendDir" -ForegroundColor Red
  Write-Host "Run: powershell -File scripts/clone-b2b-upstreams.ps1" -ForegroundColor Yellow
  Write-Host "Or:  -UpstreamRoot <path-to-AI_Find_Customer>" -ForegroundColor Yellow
  exit 1
}

$EnvFile = Join-Path $BackendDir '.env'
$EnvExample = Join-Path $BackendDir '.env.example'
if (-not (Test-Path -LiteralPath $EnvFile)) {
  if (Test-Path -LiteralPath $EnvExample) {
    Copy-Item -LiteralPath $EnvExample -Destination $EnvFile
    Write-Host "Copied backend/.env.example -> .env — fill MINIMAX/TAVILY/SERPER keys before hunts" -ForegroundColor Yellow
  } else {
    Write-Host "WARN missing $EnvFile — upstream health may fail" -ForegroundColor Yellow
  }
}

if (Test-HttpOk "http://127.0.0.1:$Port/api/v1/health") {
  Write-Host "Upstream already listening on :$Port" -ForegroundColor Green
  exit 0
}

Write-Host "Starting AI_Find_Customer upstream on :$Port" -ForegroundColor Cyan
Write-Host "  dir: $BackendDir" -ForegroundColor DarkGray

$launcher = Join-Path $Root 'scripts\start-ai-find-customer-upstream-worker.ps1'
Start-Process powershell -WindowStyle Normal -ArgumentList @(
  '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $launcher,
  '-BackendDir', $BackendDir, '-Port', $Port
)

$deadline = (Get-Date).AddSeconds(90)
while ((Get-Date) -lt $deadline) {
  if (Test-HttpOk "http://127.0.0.1:$Port/api/v1/health") {
    Write-Host "OK upstream http://127.0.0.1:$Port/api/v1/health" -ForegroundColor Green
    exit 0
  }
  Start-Sleep -Seconds 2
}

Write-Host "FAIL upstream did not become healthy on :$Port" -ForegroundColor Red
Write-Host "Check upstream window for pip/uvicorn errors; fill backend/.env API keys." -ForegroundColor Yellow
exit 1
