# AI Find Customer sidecar adapter — safe launcher
param(
  [Parameter(Mandatory = $true)][string]$Root,
  [Parameter(Mandatory = $true)][string]$UpstreamUrl,
  [int]$Port = 8092,
  [string]$Token = 'dev-sidecar-token'
)

$ErrorActionPreference = 'Stop'
$env:AI_HUNTER_UPSTREAM_URL = $UpstreamUrl
$env:AI_FIND_CUSTOMER_TOKEN = $Token
$Adapter = Join-Path $Root 'scripts\ai-find-customer-sidecar-adapter.py'
& python $Adapter --port $Port
