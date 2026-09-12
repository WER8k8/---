# D2-D6 + T2 automated validation
# Usage: powershell -ExecutionPolicy Bypass -File scripts/e2e-flywheel-validation.ps1

param(
    [string]$Base = $(if ($env:SMOKE_BASE) { $env:SMOKE_BASE } else { "http://127.0.0.1:8001" })
)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$VenvPy = Join-Path $Backend ".venv\Scripts\python.exe"
$Python = if (Test-Path -LiteralPath $VenvPy) { $VenvPy } else { "python" }
$fail = 0

function Step($Name, [scriptblock]$Block) {
    Write-Host "`n=== $Name ===" -ForegroundColor Cyan
    try {
        & $Block
        Write-Host "PASS $Name" -ForegroundColor Green
    } catch {
        Write-Host "FAIL $Name -> $($_.Exception.Message)" -ForegroundColor Red
        $script:fail++
    }
}

Step "D1 migration check" {
    & (Join-Path $Root "scripts\check-flywheel-migration.ps1")
}

Step "T2 public inquiry valid phone" {
    $body = @{
        name    = "E2E"
        phone   = "13800138000"
        message = "E2E inquiry"
        product = "demo"
    } | ConvertTo-Json -Compress
    $r = Invoke-RestMethod -Uri "$Base/api/v1/inquiries/public" -Method POST -ContentType "application/json" -Body $body
    if ($null -eq $r.data -and $null -eq $r.id) { throw "unexpected response" }
}

Step "T2 public inquiry invalid phone 422" {
    $body = @{ name = "E2E"; phone = "123"; message = "test" } | ConvertTo-Json -Compress
    try {
        Invoke-RestMethod -Uri "$Base/api/v1/inquiries/public" -Method POST -ContentType "application/json" -Body $body
        throw "expected 422"
    } catch {
        if ($_.Exception.Response.StatusCode.value__ -ne 422) { throw }
    }
}

if ($env:SMOKE_TOKEN) {
    Step "D2-D6 API smoke" {
        $env:SMOKE_BASE = $Base
        & (Join-Path $Root "scripts\smoke-flywheel-copilot.ps1")
    }
    Step "D2-D6 pytest" {
        Push-Location (Join-Path $Root "backend")
        & $Python -m pytest tests/unit/test_flywheel_d2_d6_api.py tests/unit/test_swarm_round7_deerflow_sidecar.py tests/unit/test_swarm_round8_graphrag_stub.py -q --tb=line
        if ($LASTEXITCODE -ne 0) { throw "pytest failed" }
        Pop-Location
    }
} else {
    Write-Host "`nSKIP D2-D6: SMOKE_TOKEN not set" -ForegroundColor Yellow
}

if ($fail -gt 0) {
    Write-Host "`n$fail step(s) failed." -ForegroundColor Red
    exit 1
}
Write-Host "`nAutomated steps OK." -ForegroundColor Cyan
exit 0
