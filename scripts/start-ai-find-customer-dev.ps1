# Start AI_Find_Customer dev stack: upstream mock :8080 + sidecar adapter :8092
# Usage:
#   powershell -File scripts/start-ai-find-customer-dev.ps1
#   powershell -File scripts/start-ai-find-customer-dev.ps1 -Stop
param(
  [switch]$Stop
)

$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path -LiteralPath (Split-Path -Parent $PSScriptRoot)).Path
$MockDir = Join-Path $Root 'deploy\examples\ai-hunter-upstream-mock'
$MockLauncher = Join-Path $Root 'scripts\start-ai-hunter-mock-dev.ps1'
$AdapterLauncher = Join-Path $Root 'scripts\start-ai-find-customer-adapter-dev.ps1'
$DevEnv = Join-Path $Root 'backend\config\dev\.env'
$MockPort = 8080
$AdapterPort = 8092

function Stop-PortListener([int]$Port) {
  Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique |
    ForEach-Object {
      if ($_ -and $_ -ne $PID) {
        Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
      }
    }
}

function Test-HttpOk([string]$Url) {
  try {
    Invoke-RestMethod -Uri $Url -TimeoutSec 4 | Out-Null
    return $true
  } catch { return $false }
}

function Ensure-DevEnvSidecar {
  if (-not (Test-Path -LiteralPath $DevEnv)) {
    Write-Host "WARN missing $DevEnv — copy from .env.example first" -ForegroundColor Yellow
    return
  }
  $text = Get-Content -LiteralPath $DevEnv -Raw -Encoding UTF8
  if ($text -match '(?m)^AI_FIND_CUSTOMER_URL=') {
    return
  }
  $block = @"

# AI_Find_Customer sidecar (auto by start-ai-find-customer-dev.ps1)
AI_FIND_CUSTOMER_URL=http://127.0.0.1:8092
AI_FIND_CUSTOMER_TOKEN=dev-sidecar-token
AI_HUNTER_UPSTREAM_URL=http://127.0.0.1:8080
AI_FIND_CUSTOMER_ALLOW_DEV_STUB=1
"@
  if (-not $text.EndsWith("`n")) { $text += "`r`n" }
  $text += $block
  Set-Content -LiteralPath $DevEnv -Value $text -Encoding UTF8 -NoNewline
  Write-Host "Updated backend/config/dev/.env with AI_FIND_CUSTOMER_*" -ForegroundColor Green
  Write-Host "Restart backend (start-dev-admin.ps1 -ForceRestart) to load new env." -ForegroundColor Yellow
}

if ($Stop) {
  Stop-PortListener $MockPort
  Stop-PortListener $AdapterPort
  Write-Host "Stopped listeners on :$MockPort and :$AdapterPort" -ForegroundColor Green
  exit 0
}

Ensure-DevEnvSidecar

if (-not (Test-HttpOk "http://127.0.0.1:$MockPort/api/v1/health")) {
  Write-Host "Starting AI Hunter upstream mock on :$MockPort" -ForegroundColor Cyan
  Start-Process powershell -WindowStyle Minimized -ArgumentList @(
    '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $MockLauncher,
    '-MockDir', $MockDir, '-Port', $MockPort
  )
  $deadline = (Get-Date).AddSeconds(20)
  while ((Get-Date) -lt $deadline) {
    if (Test-HttpOk "http://127.0.0.1:$MockPort/api/v1/health") { break }
    Start-Sleep -Seconds 1
  }
}

if (-not (Test-HttpOk "http://127.0.0.1:$MockPort/api/v1/health")) {
  Write-Host "FAIL upstream mock did not start on :$MockPort" -ForegroundColor Red
  exit 1
}

if (-not (Test-HttpOk "http://127.0.0.1:$AdapterPort/health")) {
  Write-Host "Starting sidecar adapter on :$AdapterPort" -ForegroundColor Cyan
  Start-Process powershell -WindowStyle Minimized -ArgumentList @(
    '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $AdapterLauncher,
    '-Root', $Root, '-UpstreamUrl', "http://127.0.0.1:$MockPort", '-Port', $AdapterPort
  )
  $deadline = (Get-Date).AddSeconds(25)
  while ((Get-Date) -lt $deadline) {
    if (Test-HttpOk "http://127.0.0.1:$AdapterPort/health") { break }
    Start-Sleep -Seconds 1
  }
}

if (-not (Test-HttpOk "http://127.0.0.1:$AdapterPort/health")) {
  Write-Host "FAIL sidecar adapter did not start on :$AdapterPort" -ForegroundColor Red
  exit 1
}

Write-Host ''
Write-Host "AI Find Customer dev stack OK" -ForegroundColor Green
Write-Host "  upstream mock : http://127.0.0.1:$MockPort/api/v1/health (mode=mock)" -ForegroundColor DarkGray
Write-Host "  sidecar       : http://127.0.0.1:$AdapterPort/health" -ForegroundColor DarkGray
Write-Host "  backend env   : AI_FIND_CUSTOMER_URL=http://127.0.0.1:$AdapterPort" -ForegroundColor DarkGray
Write-Host ''
Write-Host "Verify:" -ForegroundColor Cyan
Write-Host "  python scripts/verify-ai-find-customer-sidecar.py --smoke-find" -ForegroundColor White
