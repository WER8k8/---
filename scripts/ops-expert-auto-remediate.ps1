# Auto-remediate small issues (experts fix without Owner)
param([switch]$Quiet)
$Root = Split-Path -Parent $PSScriptRoot
$Py = Join-Path $Root "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $Py)) { $Py = "python" }
$env:YOUDING_REPO_ROOT = $Root
Push-Location $Root
& $Py (Join-Path $Root "scripts\run_ops_expert_autonomy.py") remediate 2>&1 | Out-Null
$exit = $LASTEXITCODE
Pop-Location
if (-not $Quiet) { Write-Host "auto-remediate exit=$exit" }
exit $exit
