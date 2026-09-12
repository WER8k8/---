# Tenant Nuxt site preview — safe launcher for Chinese workspace paths

param(

  [Parameter(Mandatory = $true)][string]$FrontendDir,

  [Parameter(Mandatory = $true)][int]$Port,

  [string]$NuxtHost = '127.0.0.1'

)



$ErrorActionPreference = 'Stop'

Set-Location -LiteralPath $FrontendDir

$lockRoot = Join-Path $FrontendDir '.nuxt'
if (Test-Path -LiteralPath $lockRoot) {
  foreach ($sub in @('dev', 'dist', 'cache')) {
    $p = Join-Path $lockRoot $sub
    if (Test-Path -LiteralPath $p) {
      Remove-Item -LiteralPath $p -Recurse -Force -ErrorAction SilentlyContinue
    }
  }
  foreach ($lockFile in @('nuxt.lock', 'nitro.lock')) {
    $lf = Join-Path $lockRoot $lockFile
    if (Test-Path -LiteralPath $lf) {
      Remove-Item -LiteralPath $lf -Force -ErrorAction SilentlyContinue
    }
  }
  Get-ChildItem -Path $lockRoot -Recurse -Filter '*.lock' -ErrorAction SilentlyContinue |
    ForEach-Object { Remove-Item -LiteralPath $_.FullName -Force -ErrorAction SilentlyContinue }
}

$env:NUXT_IGNORE_LOCK = '1'

$env:NUXT_HOST = $NuxtHost

$env:NUXT_PORT = "$Port"

$env:API_HOST = 'http://127.0.0.1:8001'

$env:NUXT_PUBLIC_API_BASE = '/api/v1'

npm run dev -- --host $NuxtHost --port $Port

