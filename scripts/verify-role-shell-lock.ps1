#Requires -Version 5.1
<#
.SYNOPSIS
  校验 ROLE-SHELL-LOCK-01：租户 / 超管 / 代理 登录后壳隔离

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts/verify-role-shell-lock.ps1
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
$LockFile = Join-Path $RepoRoot '.project\role-shell-lock.json'
$AdminDir = Join-Path $RepoRoot 'frontend\admin'
$CheckScript = Join-Path $AdminDir 'scripts\check-role-shell-lock.mjs'

if (-not (Test-Path $LockFile)) {
    Write-Error "Missing contract: .project/role-shell-lock.json"
    exit 1
}

Write-Host "ROLE-SHELL-LOCK-01 contract: $LockFile" -ForegroundColor Cyan
Write-Host "Charter: docs/product/ROLE-SHELL-LOCK-CHARTER.md" -ForegroundColor Cyan

Push-Location $AdminDir
try {
    node $CheckScript
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    Pop-Location
}

Write-Host "OK: role shell lock verified" -ForegroundColor Green
