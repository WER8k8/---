# 局域网联机开发 — 同 WiFi 手机/同事电脑可访问 Admin
param([switch]$ForceRestart)

$ErrorActionPreference = 'Continue'
$env:YOUDING_DEV_BIND_LAN = '1'

$fw = Join-Path $PSScriptRoot 'ensure-dev-lan-firewall.ps1'
if (Test-Path $fw) {
  Write-Host "配置防火墙（若弹出 UAC 请点「是」）..." -ForegroundColor DarkGray
  & powershell -NoProfile -ExecutionPolicy Bypass -File $fw
}

$script = Join-Path $PSScriptRoot 'start-dev-admin.ps1'
$lanArgs = @('-Lan')
if ($ForceRestart) { $lanArgs += '-ForceRestart' }
& powershell -NoProfile -ExecutionPolicy Bypass -File $script @lanArgs
exit $LASTEXITCODE
