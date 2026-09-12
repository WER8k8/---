# QA-01 · S0 三壳冒烟脚本
# 用法: powershell -File scripts/qa-s0-three-shell-smoke.ps1 [-BaseUrl http://127.0.0.1:8001]

param(
    [string]$BaseUrl = "http://127.0.0.1:8001"
)

$ErrorActionPreference = "Stop"
$Bff = "$BaseUrl/api/v1/admin-bff"
$fail = 0

function Assert-Ok($name, $cond) {
    if ($cond) { Write-Host "[PASS] $name" -ForegroundColor Green }
    else { Write-Host "[FAIL] $name" -ForegroundColor Red; $script:fail++ }
}

Write-Host "=== QA-01 S0 BFF Smoke ===" -ForegroundColor Cyan

try {
    $captcha = Invoke-RestMethod -Uri "$Bff/auth/captcha" -Method Get
    Assert-Ok "captcha stub" ($captcha.code -eq 0)
} catch {
    Assert-Ok "captcha reachable" $false
}

try {
    $tenants = Invoke-RestMethod -Uri "$Bff/auth/tenant/search" -Method Get
    Assert-Ok "tenant search" ($tenants.code -eq 0)
} catch {
    Assert-Ok "tenant search" $false
}

try {
    Invoke-RestMethod -Uri "$Bff/menu/routes" -Method Get -ErrorAction Stop
    Assert-Ok "menu routes unauth blocked" $false
} catch {
    $status = $_.Exception.Response.StatusCode.value__
    Assert-Ok "menu routes requires auth" ($status -in 401, 403)
}

Write-Host ""
if ($fail -eq 0) {
    Write-Host "QA-01 BFF smoke: ALL PASS" -ForegroundColor Green
    exit 0
} else {
    Write-Host "QA-01 BFF smoke: $fail FAILED" -ForegroundColor Red
    exit 1
}
