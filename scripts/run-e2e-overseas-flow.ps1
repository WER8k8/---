# MS-F：一键跑出海 E2E（需 dev 栈已启动）
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
Set-Location (Join-Path $Root 'backend')
& (Join-Path $Root 'backend\.venv\Scripts\python.exe') (Join-Path $Root 'scripts\e2e_cross_border_overseas_flow.py')
exit $LASTEXITCODE
