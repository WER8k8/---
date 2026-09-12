# UBX-OPS-01 / P0-02：保温厂演示独立域 HTTPS 彩排
# 用法：
#   $env:DEMO_HTTPS_DOMAIN="www.your-insulation.com"
#   powershell -ExecutionPolicy Bypass -File scripts/pilot-insulation-https-rehearsal.ps1
# 或带 API（需已登录 token）：
#   $env:API_BASE="http://127.0.0.1:8000"
#   $env:AUTH_TOKEN="Bearer ..."

param(
    [string]$Domain = $env:DEMO_HTTPS_DOMAIN
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

if (-not $Domain) {
    Write-Host "请设置 DEMO_HTTPS_DOMAIN，例如：www.example-insulation.com" -ForegroundColor Yellow
    exit 1
}

Write-Host "=== 保温厂 HTTPS 彩排：$Domain ===" -ForegroundColor Cyan

# 1) 直连探针
try {
    $uri = "https://$Domain/"
    $resp = Invoke-WebRequest -Uri $uri -UseBasicParsing -TimeoutSec 15 -MaximumRedirection 5
    Write-Host "[OK] HTTPS 响应码: $($resp.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "[FAIL] HTTPS 访问失败: $_" -ForegroundColor Red
}

# 2) API 探针（可选）
$apiBase = $env:API_BASE
$token = $env:AUTH_TOKEN
if ($apiBase -and $token) {
    $url = "$apiBase/api/v1/domains/pilot/demo-https?domain=$Domain"
    try {
        $r = Invoke-RestMethod -Uri $url -Headers @{ Authorization = $token } -Method Get
        $data = $r.data
        if ($data.ready_for_pilot) {
            Write-Host "[OK] API 彩排：ready_for_pilot=true" -ForegroundColor Green
        } else {
            Write-Host "[WARN] API 彩排：ready_for_pilot=false" -ForegroundColor Yellow
            if ($data.next_steps) { $data.next_steps | ForEach-Object { Write-Host "  - $_" } }
        }
    } catch {
        Write-Host "[WARN] API 调用失败: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "提示: 设置 API_BASE + AUTH_TOKEN 可调用 /api/v1/domains/pilot/demo-https" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "检查清单:" -ForegroundColor Cyan
Write-Host "  1. DNS 已指向租户站/网关"
Write-Host "  2. 管理端「独立域」SSL 已 active 或 pending 可刷新"
Write-Host "  3. 访客提交询盘 → 后台 inquiries 有手机号"
Write-Host "文档: docs/出海计/自有保温厂-30天试点与生存链.md"
