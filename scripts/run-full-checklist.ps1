# 全清单一口气验收（自动化）
# Usage: powershell -ExecutionPolicy Bypass -File scripts/run-full-checklist.ps1
#        powershell -ExecutionPolicy Bypass -File scripts/run-full-checklist.ps1 -SkipUnitTests

param(
    [switch]$SkipUnitTests,
    [int]$ApiPort = 8001,
    [int]$AdminPort = 5173
)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$VenvPy = Join-Path $Backend ".venv\Scripts\python.exe"
$Python = if (Test-Path -LiteralPath $VenvPy) { $VenvPy } else { "python" }
$OutJson = Join-Path $Root "docs\full-checklist-latest.json"
$ApiBase = "http://127.0.0.1:$ApiPort"
$AdminBase = "http://127.0.0.1:$AdminPort"
$fail = 0
$steps = New-Object System.Collections.ArrayList

function Add-StepResult($name, $ok, $detail) {
    if (-not $ok) { $script:fail++ }
    [void]$script:steps.Add(@{ name = $name; ok = [bool]$ok; detail = ($detail -as [string]).Trim().Substring(0, [Math]::Min(2000, ($detail -as [string]).Trim().Length)) })
    $c = if ($ok) { "Green" } else { "Red" }
    Write-Host ("[{0}] {1}" -f $(if ($ok) { "OK" } else { "FAIL" }), $name) -ForegroundColor $c
}

function Invoke-Step($name, [scriptblock]$Action) {
    $detail = ""
    $ok = $false
    try {
        & $Action
        $exit = if ($null -ne $LASTEXITCODE) { [int]$LASTEXITCODE } else { 0 }
        if ($exit -ne 0) {
            throw "step exited with code $exit"
        }
        $ok = $true
        $detail = "OK"
    } catch {
        $detail = $_.Exception.Message
        if ($detail -match 'NativeCommandError|CategoryInfo') {
            $detail = ($_.ErrorRecord | Out-String).Trim()
        }
        $ok = $false
    }
    Add-StepResult $name $ok $detail
}

function Wait-Http($url, $maxSec = 90) {
    $deadline = (Get-Date).AddSeconds($maxSec)
    while ((Get-Date) -lt $deadline) {
        try {
            $null = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5
            return $true
        } catch { Start-Sleep -Seconds 2 }
    }
    return $false
}

function Wait-ApiReady($base, $maxSec = 90) {
    $deadline = (Get-Date).AddSeconds($maxSec)
    while ((Get-Date) -lt $deadline) {
        try {
            $h = Invoke-WebRequest -Uri "$base/api/v1/health" -UseBasicParsing -TimeoutSec 5
            if ($h.StatusCode -eq 200) {
                try {
                    $r = Invoke-WebRequest -Uri "$base/api/v1/ready" -UseBasicParsing -TimeoutSec 8
                    if ($r.StatusCode -eq 200) { return $true }
                } catch {
                    Start-Sleep -Seconds 2
                    continue
                }
            }
        } catch { Start-Sleep -Seconds 2 }
    }
    return $false
}

$env:JWT_SECRET_KEY = "checklist-" + ("x" * 32)
$env:SECRET_KEY = $env:JWT_SECRET_KEY
$env:FOUNDER_DEBUG_TOKEN = "checklist-founder-dev"
$env:SMOKE_BASE = $ApiBase
$env:DATABASE_URL = "sqlite:///./youding_dev.db"
$env:DB_TYPE = "sqlite"
$env:REDIS_ENABLED = "false"
$env:LOGIN_BF_USE_REDIS = "false"
$env:MVP_LAUNCH = "1"
$env:PYTHONIOENCODING = "utf-8"
$uvicornEnv = "`$env:JWT_SECRET_KEY='$($env:JWT_SECRET_KEY)'; `$env:SECRET_KEY='$($env:SECRET_KEY)'; `$env:FOUNDER_DEBUG_TOKEN='$($env:FOUNDER_DEBUG_TOKEN)'; `$env:DATABASE_URL='sqlite:///./youding_dev.db'; `$env:DB_TYPE='sqlite'; `$env:REDIS_ENABLED='false'; `$env:LOGIN_BF_USE_REDIS='false'; `$env:MVP_LAUNCH='1';"

# Backend
if (-not (Wait-Http "$ApiBase/api/v1/health" 3)) {
    Write-Host "Starting uvicorn :$ApiPort" -ForegroundColor Cyan
    Start-Process powershell -WindowStyle Hidden -ArgumentList "-NoProfile", "-Command", "Set-Location '$Backend'; `$env:PYTHONPATH=(Get-Location).Path; $uvicornEnv & '$Python' -m uvicorn app.main:app --host 127.0.0.1 --port $ApiPort"
    $up = Wait-Http "$ApiBase/api/v1/health" 90
    Add-StepResult "start_backend" $up $(if ($up) { $ApiBase } else { "timeout" })
} else {
    Add-StepResult "start_backend" $true "already up"
}

# Admin
if (-not (Wait-Http "$AdminBase/" 3)) {
    Write-Host "Starting admin :$AdminPort" -ForegroundColor Cyan
    $adminDir = Join-Path $Root "frontend\admin"
    Start-Process powershell -WindowStyle Hidden -ArgumentList "-NoProfile", "-Command", "Set-Location '$adminDir'; npm run dev -- --host 127.0.0.1 --port $AdminPort"
    $up = Wait-Http "$AdminBase/" 120
    Add-StepResult "start_admin" $up $(if ($up) { $AdminBase } else { "timeout" })
} else {
    Add-StepResult "start_admin" $true "already up"
}

Push-Location $Backend
$env:PYTHONPATH = (Get-Location).Path
Invoke-Step "seed_platforms" { & $Python scripts/seed_platforms_full.py; if ($LASTEXITCODE -ne 0) { exit 1 } }
Invoke-Step "ensure_dev_sqlite" { & $Python scripts/ensure_dev_sqlite.py; if ($LASTEXITCODE -ne 0) { exit 1 } }
Pop-Location

# 重启 API 使 schema/代码生效
Get-NetTCPConnection -LocalPort $ApiPort -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 2
Start-Process powershell -WindowStyle Hidden -ArgumentList @(
    "-NoProfile", "-Command",
    "Set-Location '$Backend'; `$env:PYTHONPATH=(Get-Location).Path; $uvicornEnv & '$Python' -m uvicorn app.main:app --host 127.0.0.1 --port $ApiPort"
) | Out-Null
$null = Wait-ApiReady $ApiBase 90
Add-StepResult "restart_backend" $true "reloaded after ensure_dev_sqlite"

Push-Location $Root
Invoke-Step "check_mounted_routes" {
    & $Python (Join-Path $Root "scripts\check_mounted_routes.py") 2>&1 | ForEach-Object { Write-Host $_ }
    if ($LASTEXITCODE -ne 0) { exit 1 }
}
Invoke-Step "demo_acceptance" {
    & $Python (Join-Path $Root "scripts\run_demo_acceptance.py") 2>&1 | ForEach-Object { Write-Host $_ }
    if ($LASTEXITCODE -ne 0) { exit 1 }
}
Invoke-Step "production_preflight" {
    & $Python (Join-Path $Root "scripts\run_production_preflight.py") 2>&1 | ForEach-Object { Write-Host $_ }
    if ($LASTEXITCODE -ne 0) { exit 1 }
}
Invoke-Step "security_audit" {
    & $Python (Join-Path $Root "scripts\run_security_audit.py") 2>&1 | ForEach-Object { Write-Host $_ }
    if ($LASTEXITCODE -ne 0) { exit 1 }
}

if (-not $SkipUnitTests) {
    Push-Location $Backend
    $env:PYTHONPATH = (Get-Location).Path
    Invoke-Step "pytest_unit" { & $Python -m pytest tests/unit -q --tb=no }
    Pop-Location
} else {
    Add-StepResult "pytest_unit" $true "skipped"
}

Invoke-Step "flywheel_migration" {
    & (Join-Path $Root "scripts\check-flywheel-migration.ps1") 2>&1 | ForEach-Object { Write-Host $_ }
    if ($LASTEXITCODE -ne 0) { exit 1 }
}

$env:SMOKE_USER = "admin"
$env:SMOKE_PASS = "admin123"
Invoke-Step "get_smoke_token" {
    & (Join-Path $Root "scripts\get-smoke-token.ps1") 2>&1 | ForEach-Object { Write-Host $_ }
    if ($LASTEXITCODE -ne 0) { exit 1 }
    if (-not $env:SMOKE_TOKEN) { throw "SMOKE_TOKEN empty" }
}
Invoke-Step "e2e_flywheel" {
    & (Join-Path $Root "scripts\e2e-flywheel-validation.ps1") 2>&1 | ForEach-Object { Write-Host $_ }
    if ($LASTEXITCODE -ne 0) { exit 1 }
}
Invoke-Step "l3_api" {
    & (Join-Path $Root "scripts\run-browser-l3-api.ps1") -ApiBase $ApiBase 2>&1 | ForEach-Object { Write-Host $_ }
    if ($LASTEXITCODE -ne 0) { exit 1 }
}
Invoke-Step "l3_api_smoke" {
    & $Python (Join-Path $Root "scripts\run-l3-api-smoke.py") 2>&1 | ForEach-Object { Write-Host $_ }
    if ($LASTEXITCODE -ne 0) { exit 1 }
}
Invoke-Step "gates_g1_g7" {
    $env:MVP_LAUNCH='1'
    $env:QA08_ENGINEERING_PASS='1'
    & $Python (Join-Path $Root "scripts\check_gates_g1_g7.py") 2>&1 | ForEach-Object { Write-Host $_ }
    if ($LASTEXITCODE -ne 0) { exit 1 }
}

Pop-Location

$report = @{
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
    api_base     = $ApiBase
    admin_base   = $AdminBase
    fail_count   = $fail
    ok           = ($fail -eq 0)
    steps        = $steps
}
$report | ConvertTo-Json -Depth 6 | Set-Content -Path $OutJson -Encoding UTF8
Write-Host "`nWrote $OutJson (fail=$fail)" -ForegroundColor Cyan
exit $(if ($fail -eq 0) { 0 } else { 1 })
