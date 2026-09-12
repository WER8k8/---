# LAN dev diagnostic
$ErrorActionPreference = 'Continue'
$ApiPort = 8001
$AdminPort = 5173

function Get-LanIp {
  $virtualAlias = '(?i)(vEthernet|WSL|Hyper-V|Default Switch|VMware|VirtualBox)'
  $ips = @()
  Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object { $_.IPAddress -match '^192\.168\.' } |
    ForEach-Object {
      $iface = Get-NetIPInterface -InterfaceIndex $_.InterfaceIndex -ErrorAction SilentlyContinue
      $alias = if ($iface) { [string]$iface.InterfaceAlias } else { '' }
      if ($alias -notmatch $virtualAlias) { $ips += $_.IPAddress }
    }
  if ($ips.Count -eq 0) {
    $text = (ipconfig | Out-String)
    foreach ($m in [regex]::Matches($text, '(?m)IPv4[^\:]*:\s*(192\.168\.\d+\.\d+)')) {
      if ($m.Groups[1].Value -notmatch '^172\.26\.') { $ips += $m.Groups[1].Value }
    }
  }
  return @($ips | Select-Object -Unique)
}

Write-Host ''
Write-Host '========== LAN diagnose ==========' -ForegroundColor Cyan

$lanIps = Get-LanIp
$listen5173 = netstat -ano | findstr "LISTENING" | findstr ":$AdminPort "
$listen8001 = netstat -ano | findstr "LISTENING" | findstr ":$ApiPort "
$bindOk = ($listen5173 -match '0\.0\.0\.0:' + $AdminPort)

Write-Host ''
if ($bindOk) { Write-Host 'OK: frontend listens on 0.0.0.0:'$AdminPort -ForegroundColor Green }
else { Write-Host 'FAIL: run scripts/start-dev-lan.ps1 -ForceRestart' -ForegroundColor Red }

if ($listen8001) { Write-Host 'OK: backend :'$ApiPort -ForegroundColor Green }
else { Write-Host 'FAIL: backend not running' -ForegroundColor Red }

Write-Host ''
if ($lanIps.Count -gt 0) {
  Write-Host 'Use this URL on phone / second laptop (NOT 127.0.0.1 or 172.26.x):' -ForegroundColor Yellow
  foreach ($ip in $lanIps) {
    $url = "http://${ip}:$AdminPort/login"
    Write-Host "  $url" -ForegroundColor Cyan
    try {
      $code = (Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5).StatusCode
      Write-Host "  loopback test -> HTTP $code" -ForegroundColor Green
    } catch {
      Write-Host "  loopback test -> FAIL" -ForegroundColor Red
    }
  }
} else {
  Write-Host 'WARN: no 192.168.x IP found' -ForegroundColor Yellow
}

Write-Host ''
netsh advfirewall firewall show rule name="Vite Dev 5173" >$null 2>&1
if ($LASTEXITCODE -eq 0) { Write-Host 'OK: firewall rule Vite Dev 5173' -ForegroundColor Green }
else { Write-Host 'WARN: run scripts/ensure-dev-lan-firewall.ps1 as Admin' -ForegroundColor Yellow }

Write-Host ''
Write-Host 'If second device still cannot open:' -ForegroundColor Yellow
Write-Host '  - same WiFi/router, not guest network' -ForegroundColor Gray
Write-Host '  - disable router AP isolation' -ForegroundColor Gray
Write-Host '  - login: admin / admin123' -ForegroundColor Gray
Write-Host ''
