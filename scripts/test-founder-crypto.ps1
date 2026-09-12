# 国密自检 + 创始人 API 连通性（需后端已启动、超管 JWT）
param(
    [string]$BaseUrl = "http://127.0.0.1:8001/api/v1",
    [string]$Jwt = $env:SMOKE_JWT,
    [string]$FounderToken = $env:FOUNDER_DEBUG_TOKEN
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "==> gmssl 本地 roundtrip" -ForegroundColor Cyan
Push-Location (Join-Path $Root "backend")
$env:PYTHONPATH = (Get-Location).Path
python -c @"
from app.core.gm_crypto import self_test, gmssl_available
from app.core.config import settings
key = getattr(settings, 'GM_SM4_KEY', '') or settings.SECRET_KEY
r = self_test(key)
print('gmssl_installed:', r.get('gmssl_installed'))
print('sm4_roundtrip_ok:', r.get('sm4_roundtrip_ok'))
if r.get('error'):
    print('hint:', r['error'])
"@
Pop-Location

if (-not $Jwt -or -not $FounderToken) {
    Write-Host "`n跳过 HTTP 测试：请设置环境变量 SMOKE_JWT 与 FOUNDER_DEBUG_TOKEN" -ForegroundColor Yellow
    Write-Host "  powershell -File scripts/get-smoke-token.ps1"
    exit 0
}

Write-Host "`n==> GET founder-ops/crypto/self-test" -ForegroundColor Cyan
$headers = @{
    Authorization       = "Bearer $Jwt"
    "X-Founder-Debug-Token" = $FounderToken
}
try {
    $r = Invoke-RestMethod -Uri "$BaseUrl/founder-ops/crypto/self-test" -Headers $headers
    $r | ConvertTo-Json -Depth 6
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
