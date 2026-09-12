#Requires -Version 5.1
<#
.SYNOPSIS
  校验 LOGIN-LOCK-01：管理端仅 /login 超管入口（跨 IDE 硬锁）

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts/verify-login-entry-lock.ps1
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
$LockFile = Join-Path $RepoRoot '.project\login-entry-lock.json'
$AdminDir = Join-Path $RepoRoot 'frontend\admin'
$CheckScript = Join-Path $AdminDir 'scripts\check-login-entry-lock.mjs'

if (-not (Test-Path $LockFile)) {
    Write-Error "Missing contract: .project/login-entry-lock.json"
    exit 1
}

Write-Host "LOGIN-LOCK-01 contract: $LockFile" -ForegroundColor Cyan
Write-Host "Charter: docs/product/LOGIN-SINGLE-ENTRY-CHARTER.md" -ForegroundColor Cyan

Push-Location $AdminDir
try {
    node $CheckScript
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    Pop-Location
}

Write-Host "OK: login entry lock verified" -ForegroundColor Green
