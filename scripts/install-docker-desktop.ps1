# Install Docker Desktop (requires one-time Administrator UAC approval)
# Usage: powershell -ExecutionPolicy Bypass -File scripts/install-docker-desktop.ps1
$ErrorActionPreference = "Stop"

function Test-DockerDaemon {
  try {
    $null = docker info 2>&1
    return ($LASTEXITCODE -eq 0)
  } catch {
    return $false
  }
}

if (Test-DockerDaemon) {
  Write-Host "Docker daemon already running." -ForegroundColor Green
  exit 0
}

Write-Host "Installing Docker Desktop via winget (UAC prompt expected once)..." -ForegroundColor Cyan
$proc = Start-Process -FilePath "winget" -ArgumentList @(
  "install", "Docker.DockerDesktop",
  "--accept-package-agreements", "--accept-source-agreements", "--silent"
) -Wait -PassThru -NoNewWindow

if ($proc.ExitCode -ne 0) {
  Write-Host "winget install exit code: $($proc.ExitCode)" -ForegroundColor Yellow
  Write-Host "If UAC was denied, right-click PowerShell -> Run as administrator, then rerun this script." -ForegroundColor Yellow
}

$paths = @(
  "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe",
  "$env:LOCALAPPDATA\Programs\Docker\Docker\Docker Desktop.exe"
)
foreach ($exe in $paths) {
  if (Test-Path $exe) {
    Write-Host "Starting Docker Desktop: $exe"
    Start-Process -FilePath $exe | Out-Null
    break
  }
}

$deadline = (Get-Date).AddMinutes(5)
while ((Get-Date) -lt $deadline) {
  if (Test-DockerDaemon) {
    Write-Host "Docker daemon is ready." -ForegroundColor Green
    exit 0
  }
  Start-Sleep -Seconds 5
  Write-Host "Waiting for Docker daemon..."
}

Write-Host "Docker Desktop installed or started, but daemon not ready yet. Reboot may be required." -ForegroundColor Yellow
exit 1
