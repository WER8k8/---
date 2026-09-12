# P2-09 onboarding E2E recording readiness (automated checks only)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$frontend = Join-Path $repo 'frontend\admin\src\views\client\onboarding.vue'
$router = Join-Path $repo 'frontend\admin\src\router\index.ts'

Write-Host '== Onboarding E2E readiness ==' -ForegroundColor Cyan

$vue = Get-Content -Raw -Encoding UTF8 $frontend
$stepCount = ([regex]::Matches($vue, '<a-step\b')).Count
if ($stepCount -lt 6) {
    throw "onboarding.vue expected >= 6 a-step nodes, found $stepCount"
}
Write-Host "[OK] onboarding wizard has $stepCount steps"

$routerText = Get-Content -Raw -Encoding UTF8 $router
if ($routerText -notmatch "path:\s*'onboarding'") {
    throw 'router missing /client/onboarding route'
}
Write-Host '[OK] /client/onboarding route registered'

Push-Location (Join-Path $repo 'backend')
try {
    $py = Join-Path (Get-Location) '.venv\Scripts\python.exe'
    if (-not (Test-Path $py)) { $py = 'python' }
    & $py -m pytest `
        tests/unit/test_onboarding_chain.py `
        tests/unit/test_onboarding_progress.py `
        tests/unit/test_onboarding_autopilot.py `
        -q --tb=line
    if ($LASTEXITCODE -ne 0) { throw "onboarding pytest failed ($LASTEXITCODE)" }
    Write-Host '[OK] onboarding backend unit tests passed'
}
finally {
    Pop-Location
}

Write-Host ''
Write-Host 'Ready for human E2E screen recording (P2-09).' -ForegroundColor Green
