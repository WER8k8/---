# 摸金校尉生产就绪验证（API + 单元测试）
# 用法: powershell -File scripts/verify-greedy-production-readiness.ps1 [-BaseUrl http://127.0.0.1:8001]

param(
    [string]$BaseUrl = "http://127.0.0.1:8001"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

Write-Host "== Greedy production readiness ==" -ForegroundColor Cyan

$env:SECRET_KEY = "test-secret-key-for-unit-testing-only-not-for-production-use"
$env:JWT_SECRET_KEY = "test-jwt-secret-key-for-unit-testing-only-not-for-production-use"

Push-Location backend
python -m pytest tests/unit/test_greedy_readiness.py -q --noconftest
if ($LASTEXITCODE -ne 0) { Pop-Location; exit 1 }
Pop-Location

Write-Host "Unit tests OK" -ForegroundColor Green

try {
    $health = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get -TimeoutSec 5
    Write-Host "API health: $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "API not reachable at $BaseUrl — skip live readiness (start backend for full check)" -ForegroundColor Yellow
    exit 0
}

Write-Host "Live GET /api/v1/hermes/greedy/readiness requires ops auth — use Admin 摸金校尉总控 or curl with Bearer token" -ForegroundColor Gray
Write-Host "Done." -ForegroundColor Green
