# Generic Python sidecar launcher — safe for Chinese workspace paths
param(
  [Parameter(Mandatory = $true)][string]$SidecarDir,
  [Parameter(Mandatory = $true)][string]$PortEnv,
  [Parameter(Mandatory = $true)][int]$Port,
  [string]$TokenEnv = '',
  [string]$Token = 'dev-sidecar-token',
  [string[]]$ExtraEnv = @()
)

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $SidecarDir
Set-Item -Path "env:$PortEnv" -Value "$Port"
if ($TokenEnv) {
  Set-Item -Path "env:$TokenEnv" -Value $Token
}
foreach ($pair in $ExtraEnv) {
  $name, $value = $pair -split '=', 2
  if ($name) {
    Set-Item -Path "env:$name" -Value $value
  }
}
python main.py
