# Worker: uvicorn for AI_Find_Customer backend (Chinese-path safe)
param(
  [Parameter(Mandatory = $true)][string]$BackendDir,
  [Parameter(Mandatory = $true)][int]$Port
)

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $BackendDir
$env:API_HOST = '127.0.0.1'
$env:API_PORT = "$Port"
python -m uvicorn api.app:app --host 127.0.0.1 --port $Port
