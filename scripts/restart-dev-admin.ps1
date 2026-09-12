# 强制重启开发栈（backend + admin），加载最新代码
param([switch]$Lan)

$Root = Split-Path -Parent $PSScriptRoot
$flags = @('-ForceRestart')
if ($Lan) { $flags += '-Lan' }
powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root 'scripts\launch-dev-admin-safe.ps1') @flags
