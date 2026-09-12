# Daily standup + notify Owner (big items only highlighted)
param(
    [switch]$Quiet,
    [switch]$NoNotify
)
$Root = Split-Path -Parent $PSScriptRoot
$Py = Join-Path $Root "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $Py)) { $Py = "python" }
$env:YOUDING_REPO_ROOT = $Root
$args = @("standup")
if ($NoNotify) { $args += "--no-notify" }
Push-Location $Root
$output = & $Py (Join-Path $Root "scripts\run_ops_expert_autonomy.py") @args 2>&1
$exit = $LASTEXITCODE
Pop-Location
if (-not $Quiet) {
    Write-Host $output
    Write-Host "standup: docs/ops/expert-standup-latest.md"
}
exit $exit
