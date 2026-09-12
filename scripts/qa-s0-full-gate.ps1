# QA-S0 · 全 Gate 编排（BFF 冒烟 + 可选截图）

param(
    [string]$BackendUrl = "http://127.0.0.1:8001",
    [string]$FrontendUrl = "http://127.0.0.1:5173",
    [switch]$CaptureScreenshots,
    [switch]$StartBackend,
    [switch]$StartFrontend
)

$ErrorActionPreference = "Stop"
$repo = Split-Path $PSScriptRoot -Parent
$backend = Join-Path $repo "backend"
$admin = Join-Path $repo "frontend\admin"
$fail = 0

function Test-Port($port) {
    return [bool](Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
}

function Start-BackendIfNeeded {
    if (Test-Port 8001) { Write-Host "[skip] backend :8001 already up" -ForegroundColor DarkGray; return }
    if (-not $StartBackend) {
        Write-Host "[warn] backend :8001 not listening — use -StartBackend or start manually" -ForegroundColor Yellow
        return
    }
    Write-Host "[start] backend :8001 …" -ForegroundColor Cyan
    $env:PYTHONPATH = $backend
    $env:DATABASE_URL = "sqlite:///./youding_dev.db"
    $env:REDIS_ENABLED = "false"
    $env:MVP_LAUNCH = "1"
    if (-not $env:JWT_SECRET_KEY) { $env:JWT_SECRET_KEY = "dev-" + ("x" * 28) }
    Start-Process -FilePath "$backend\.venv\Scripts\python.exe" `
        -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8001" `
        -WorkingDirectory $backend -WindowStyle Hidden
    Start-Sleep -Seconds 5
}

function Start-FrontendIfNeeded {
    if (Test-Port 5173) { Write-Host "[skip] frontend :5173 already up" -ForegroundColor DarkGray; return }
    if (-not $StartFrontend) {
        Write-Host "[warn] frontend :5173 not listening — use -StartFrontend for screenshots" -ForegroundColor Yellow
        return
    }
    Write-Host "[start] frontend :5173 …" -ForegroundColor Cyan
    Start-Process -FilePath "npm" -ArgumentList "run", "dev" -WorkingDirectory $admin -WindowStyle Hidden
    Start-Sleep -Seconds 8
}

Write-Host "=== QA-S0 Full Gate ===" -ForegroundColor Cyan

Start-BackendIfNeeded
Start-FrontendIfNeeded

$env:PYTHONPATH = $backend
Push-Location $repo
try {
    python scripts/qa-three-shell-e2e.py
    if ($LASTEXITCODE -ne 0) { $fail++ }

    python scripts/qa-bff-three-role-smoke.py
    if ($LASTEXITCODE -ne 0) { $fail++ }

    Push-Location $backend
    python -m pytest tests/unit/test_admin_bff_w1.py tests/unit/test_admin_bff_three_shell.py tests/unit/test_plan_gate_service.py -q --tb=no
    if ($LASTEXITCODE -ne 0) { $fail++ }
    Pop-Location

    Push-Location $admin
    npm run cert:gate 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { $fail++ }
    Pop-Location

    if ($CaptureScreenshots) {
        if (-not (Test-Port 5173)) {
            Write-Host "[FAIL] screenshots need frontend :5173" -ForegroundColor Red
            $fail++
        } else {
            node scripts/capture-cert-screenshots.mjs --base $FrontendUrl --api $BackendUrl
            if ($LASTEXITCODE -ne 0) { $fail++ }
        }
    }
} finally {
    Pop-Location
}

Write-Host ""
if ($fail -eq 0) {
    Write-Host "QA-S0 Full Gate: ALL PASS" -ForegroundColor Green
    exit 0
} else {
    Write-Host "QA-S0 Full Gate: $fail stage(s) FAILED" -ForegroundColor Red
    exit 1
}
