# 使用藏云阁镜像加速启动 Docker Compose
# 文档: https://cncfstack.com/p/assets/docs/cncfstack/image/
param(
  [ValidateSet('dev', 'prod')]
  [string]$Profile = 'dev',
  [string]$EnvFile = '',
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$ComposeArgs
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Mirror = Join-Path $Root 'docker-compose.cncfstack.yml'

if (-not (Test-Path $Mirror)) {
  throw "缺少 $Mirror"
}

$Base = if ($Profile -eq 'prod') {
  Join-Path $Root 'docker-compose.prod.yml'
} else {
  Join-Path $Root 'docker-compose.dev.yml'
}

if (-not (Test-Path $Base)) {
  throw "缺少 $Base"
}

$cmd = @('compose', '-f', $Base, '-f', $Mirror)
if ($EnvFile -and (Test-Path (Join-Path $Root $EnvFile))) {
  $cmd += @('--env-file', $EnvFile)
}
$cmd += $ComposeArgs

Write-Host "藏云阁镜像加速: docker $($cmd -join ' ')" -ForegroundColor Cyan
Push-Location $Root
try {
  & docker @cmd
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
  Pop-Location
}
