# Dev completion sweep — unit tests + cert gate + staging preflight smoke
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "=== Dev Completion Sweep ===" -ForegroundColor Cyan

$results = @()

function Add-Result($name, $ok, $detail) {
    $script:results += [pscustomobject]@{ step = $name; ok = $ok; detail = $detail }
}

Push-Location "$Root\backend"
python -m alembic upgrade head 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) { Add-Result "alembic_head" $true "ok" } else { Add-Result "alembic_head" $false "exit $LASTEXITCODE" }

$pytest = python -m pytest tests/unit/test_referral_redeem.py tests/unit/test_trade_intel_m2.py tests/unit/test_agent_tree_crud.py -q --tb=no 2>&1
if ($LASTEXITCODE -eq 0) { Add-Result "unit_smoke" $true ($pytest | Select-Object -Last 1) } else { Add-Result "unit_smoke" $false ($pytest | Select-Object -Last 3) }
Pop-Location

Push-Location "$Root\frontend\admin"
$gate = npm run cert:gate 2>&1 | Out-String
if ($LASTEXITCODE -eq 0) { Add-Result "cert_gate" $true "ready" } else { Add-Result "cert_gate" $false "fail" }
Pop-Location

if (Test-Path "$Root\scripts\run-phase-c-next.ps1") {
    & "$Root\scripts\run-phase-c-next.ps1" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { Add-Result "phase_c" $true "ok" } else { Add-Result "phase_c" $false "exit $LASTEXITCODE" }
}

python "$Root\scripts\module_progress.py" 2>&1 | Out-Null

$fail = @($results | Where-Object { -not $_.ok }).Count
Write-Host ""
$results | Format-Table -AutoSize
Write-Host "FAIL: $fail / $($results.Count)" -ForegroundColor $(if ($fail -eq 0) { "Green" } else { "Yellow" })

$report = @{
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
    steps        = $results
    fail_count   = $fail
    engineering_code_complete = ($fail -eq 0)
    pm_still_required = @(
        "12 模块截图 docs/送检截图/"
        "l3-signoff.json pm_signed"
        "HTTPS 演示独立域"
        "G4 真实 AI Key 生产实跑"
        "Locust 1000 + 72h（staging 服务器）"
    )
}
$out = Join-Path $Root "docs\engineering-complete-latest.json"
$report | ConvertTo-Json -Depth 5 | Set-Content -Path $out -Encoding UTF8
Write-Host "Report: $out"
exit $fail
