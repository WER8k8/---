#Requires -Version 5.1
<#
.SYNOPSIS
  安装 ECC 1.10.0 到外部 dev-stack（不污染产品源码树）。

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts/install-ecc-workspace.ps1
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
$ExternalInstaller = Join-Path $RepoRoot 'scripts\install-dev-stack-external.ps1'

if (-not (Test-Path $ExternalInstaller)) {
    throw "Missing: $ExternalInstaller"
}

& $ExternalInstaller -InstallEcc
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host 'ECC 已通过外部 dev-stack 安装。' -ForegroundColor Green
Write-Host '重启 Cursor 使规则生效。' -ForegroundColor Green
