# Safe launcher for Chinese-path workspaces — ops/SRE 自动拉起用
# Usage: powershell -File scripts/launch-dev-admin-safe.ps1

$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Launcher = Join-Path $ScriptDir 'start-dev-admin.ps1'
if (-not (Test-Path -LiteralPath $Launcher)) {
  Write-Error "Missing start-dev-admin.ps1 at $Launcher"
}
& powershell -NoProfile -ExecutionPolicy Bypass -File $Launcher @args
exit $LASTEXITCODE
