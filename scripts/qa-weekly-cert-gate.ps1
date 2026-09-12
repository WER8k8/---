# QA-02 · 每周 cert:gate 回归脚本

param(
    [string]$RepoRoot = (Split-Path $PSScriptRoot -Parent)
)

$ErrorActionPreference = "Stop"
$admin = Join-Path $RepoRoot "frontend\admin"
$out = Join-Path $RepoRoot "docs\qa\cert-gate-weekly-latest.json"
$fail = 0

Write-Host "=== QA-02 Weekly cert:gate ===" -ForegroundColor Cyan

Push-Location $admin
npm run cert:gate 2>&1 | Out-Host
if ($LASTEXITCODE -ne 0) { $fail++ }
Pop-Location

$env:PYTHONPATH = Join-Path $RepoRoot "backend"
Push-Location $RepoRoot
python scripts/qa-three-shell-e2e.py
if ($LASTEXITCODE -ne 0) { $fail++ }
python scripts/qa-bff-three-role-smoke.py
if ($LASTEXITCODE -ne 0) { $fail++ }
Pop-Location

$report = @{
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
    cert_gate_ok = ($fail -eq 0)
    fail_count = $fail
}
$dir = Split-Path $out -Parent
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
$report | ConvertTo-Json -Depth 4 | Set-Content -Path $out -Encoding UTF8

if ($fail -eq 0) {
    Write-Host "QA-02 weekly: PASS -> $out" -ForegroundColor Green
    exit 0
}
Write-Host "QA-02 weekly: $fail FAILED" -ForegroundColor Red
exit 1
