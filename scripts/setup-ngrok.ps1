# Configure ngrok authtoken (one-time, local only — never commit)
# Usage:
#   copy .env.ngrok.local.example .env.ngrok.local   # fill token locally
#   powershell -ExecutionPolicy Bypass -File scripts/setup-ngrok.ps1
param(
  [string]$Token = "",
  [switch]$SaveLocal = $true
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $Root ".env.ngrok.local"

function Read-TokenFromEnvFile([string]$Path) {
  if (-not (Test-Path $Path)) { return "" }
  foreach ($line in Get-Content $Path) {
    if ($line -match '^\s*NGROK_AUTHTOKEN\s*=\s*(.+)\s*$') {
      return $matches[1].Trim().Trim('"').Trim("'")
    }
  }
  return ""
}

if (-not $Token) { $Token = $env:NGROK_AUTHTOKEN }
if (-not $Token) { $Token = $env:NGROK_AUTH_TOKEN }
if (-not $Token) { $Token = Read-TokenFromEnvFile $EnvFile }

if (-not $Token) {
  Write-Host "NGROK authtoken not found." -ForegroundColor Red
  Write-Host ""
  Write-Host "Option 1: copy .env.ngrok.local.example to .env.ngrok.local (gitignored)"
  Write-Host "Option 2: set NGROK_AUTHTOKEN in shell, then run this script again"
  Write-Host ""
  Write-Host "Get token: https://dashboard.ngrok.com/get-started/your-authtoken" -ForegroundColor Cyan
  Write-Host "Authtoken is on: Your Authtoken page (get-started), NOT the cr_* ID in the list." -ForegroundColor Yellow
  exit 1
}

# cr_* = credential ID in dashboard list, not the secret token
if ($Token -match '^cr_') {
  Write-Host "This is a credential ID (cr_...), not the authtoken secret." -ForegroundColor Red
  Write-Host "Use: https://dashboard.ngrok.com/get-started/your-authtoken -> Your Authtoken -> Copy"
  exit 1
}

if ($Token.Length -lt 32) {
  Write-Host "Authtoken too short — copy the full string from Your Authtoken page." -ForegroundColor Red
  exit 1
}

Write-Host "=== ngrok authtoken (local only) ===" -ForegroundColor Cyan
ngrok config add-authtoken $Token
if ($LASTEXITCODE -ne 0) {
  Write-Host "ngrok config add-authtoken failed (exit $LASTEXITCODE)" -ForegroundColor Red
  exit $LASTEXITCODE
}

if ($SaveLocal) {
  @(
    "# LOCAL ONLY — listed in .gitignore, never commit or upload"
    "NGROK_AUTHTOKEN=$Token"
  ) | Set-Content -Path $EnvFile -Encoding UTF8
  Write-Host "Saved to .env.ngrok.local (gitignored)" -ForegroundColor DarkGray
}

ngrok config check
if ($LASTEXITCODE -ne 0) {
  Write-Host "ngrok config check failed" -ForegroundColor Red
  exit 1
}

Write-Host ""
Write-Host "Configured. Token stored only on this machine:" -ForegroundColor Green
Write-Host "  - %LOCALAPPDATA%\ngrok\ngrok.yml"
if ($SaveLocal) { Write-Host "  - $EnvFile (gitignored)" }
Write-Host ""
Write-Host "Do NOT paste token in chat, issues, or commit to Git." -ForegroundColor Yellow
Write-Host "Start tunnel: powershell -ExecutionPolicy Bypass -File scripts/start-ngrok-tunnel.ps1"
