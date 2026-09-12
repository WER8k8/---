# 启动 SAU Sidecar（开发）
param(
    [int]$Port = 9910,
    [string]$Host = "127.0.0.1"
)
$root = Split-Path -Parent $PSScriptRoot
$adapter = Join-Path $root "scripts\sau-sidecar-adapter.py"
if (-not (Test-Path $adapter)) {
    Write-Error "missing $adapter"
    exit 1
}
if (-not $env:SAU_HOME) {
    $env:SAU_HOME = Join-Path $env:USERPROFILE ".sau-home"
}
Write-Host "SAU sidecar http://${Host}:${Port} SAU_HOME=$env:SAU_HOME"
python $adapter --host $Host --port $Port
