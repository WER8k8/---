# CONSOLE-REGRESSION-LOCK-01 — 控制台红错硬锁校验
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
Set-Location (Join-Path $repo 'frontend\admin')
node scripts/check-console-regression-lock.mjs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host 'console-regression-lock: ok'
