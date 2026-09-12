# LAN dev firewall (auto-elevate)
param([int[]]$Ports = @(5173, 8001))

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
  $self = $MyInvocation.MyCommand.Path
  Write-Host 'Requesting Administrator to open firewall ports...' -ForegroundColor Yellow
  Start-Process powershell -Verb RunAs -ArgumentList @(
    '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$self`""
  ) -Wait
  exit $LASTEXITCODE
}

$ErrorActionPreference = 'Continue'
foreach ($p in $Ports) {
  $name = "YouDing-Dev-LAN-$p"
  $existing = netsh advfirewall firewall show rule name="$name" 2>$null
  if ($LASTEXITCODE -eq 0 -and $existing) {
    Write-Host "exists: $name" -ForegroundColor DarkGray
    continue
  }
  netsh advfirewall firewall add rule name="$name" dir=in action=allow protocol=TCP localport=$p profile=private,domain,public enable=yes | Out-Null
  if ($LASTEXITCODE -eq 0) {
    Write-Host "allowed TCP $p ($name)" -ForegroundColor Green
  } else {
    Write-Host "failed TCP $p" -ForegroundColor Red
    exit 1
  }
}
Write-Host 'firewall done' -ForegroundColor Green
