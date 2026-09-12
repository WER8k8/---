# 获取 E2E / 飞轮冒烟用 JWT（写入 $env:SMOKE_TOKEN）
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts/get-smoke-token.ps1
# Env:
#   SMOKE_BASE  (default http://127.0.0.1:8001)
#   SMOKE_USER  (default admin)
#   SMOKE_PASS  (default admin123)

param(
    [string]$Base = $(if ($env:SMOKE_BASE) { $env:SMOKE_BASE } else { "http://127.0.0.1:8001" }),
    [string]$User = $(if ($env:SMOKE_USER) { $env:SMOKE_USER } else { "admin" }),
    [string]$Pass = $(if ($env:SMOKE_PASS) { $env:SMOKE_PASS } else { "admin123" })
)

$ErrorActionPreference = "Stop"
$body = @{
    username_or_email = $User
    password          = $Pass
} | ConvertTo-Json -Compress

try {
    $r = Invoke-RestMethod -Uri "$Base/api/v1/auth/login" -Method POST -ContentType "application/json" -Body $body
} catch {
    Write-Host "LOGIN FAIL: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Ensure backend is running at $Base and user exists." -ForegroundColor Yellow
    exit 1
}

$token = $null
if ($r.data -and $r.data.access_token) { $token = $r.data.access_token }
elseif ($r.access_token) { $token = $r.access_token }

if (-not $token) {
    Write-Host "LOGIN: no access_token in response" -ForegroundColor Red
    $r | ConvertTo-Json -Depth 5
    exit 1
}

$env:SMOKE_TOKEN = $token
Write-Host "SMOKE_TOKEN set (length $($token.Length))" -ForegroundColor Green
Write-Host "Run: powershell -File scripts/e2e-flywheel-validation.ps1"
