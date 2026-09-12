# Admin Vite launcher — avoids -Command quoting issues on Chinese workspace paths
param(
  [Parameter(Mandatory = $true)][string]$AdminDir,
  [Parameter(Mandatory = $true)][int]$AdminPort,
  [string]$ViteHost = '127.0.0.1',
  [string]$LanHost = ''
)

$ErrorActionPreference = 'Stop'
if ($LanHost) { $env:YOUDING_DEV_LAN_HOST = $LanHost }
Set-Location -LiteralPath $AdminDir
npm run dev -- --host $ViteHost --port $AdminPort --strictPort
