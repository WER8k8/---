# AI Hunter upstream mock — safe launcher for Chinese workspace paths
param(
  [Parameter(Mandatory = $true)][string]$MockDir,
  [int]$Port = 8080
)

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $MockDir
$env:AI_HUNTER_MOCK_PORT = "$Port"
python main.py
