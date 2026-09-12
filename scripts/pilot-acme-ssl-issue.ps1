# P0-01：生产 ACME / certbot SSL 签发彩排
# 环境变量示例见 docs/Sprint-O-商用收尾.md

param(
    [string]$ApiBase = $(if ($env:API_BASE) { $env:API_BASE } else { "http://127.0.0.1:8001" }),
    [string]$TenantId = $env:PILOT_TENANT_ID,
    [string]$Domain = $env:DEMO_HTTPS_DOMAIN,
    [string]$Token = $env:AUTH_TOKEN
)

if (-not $TenantId -or -not $Domain -or -not $Token) {
    Write-Host "需要: PILOT_TENANT_ID, DEMO_HTTPS_DOMAIN, AUTH_TOKEN (Bearer ...)" -ForegroundColor Yellow
    exit 1
}

$headers = @{ Authorization = $Token; "Content-Type" = "application/json" }

Write-Host "SSL_PROVIDER=$($env:SSL_PROVIDER) ACME_WEBHOOK_URL=$($env:ACME_WEBHOOK_URL)" -ForegroundColor Cyan

# 触发签发
$issueUrl = "$ApiBase/api/v1/domain/tenants/$TenantId/domains/$Domain/ssl"
try {
    $r = Invoke-RestMethod -Uri $issueUrl -Method Post -Headers $headers
    Write-Host "[issue] $($r.message)" -ForegroundColor Green
    Write-Host ($r.data | ConvertTo-Json -Compress)
} catch {
    Write-Host "[FAIL] issue: $_" -ForegroundColor Red
    exit 1
}

Start-Sleep -Seconds 2

# 刷新 pending（P0-01 轮询）
$refreshUrl = "$ApiBase/api/v1/domain/tenants/$TenantId/domains/$Domain/ssl/refresh"
try {
    $r2 = Invoke-RestMethod -Uri $refreshUrl -Method Post -Headers $headers
    Write-Host "[refresh] ssl_status=$($r2.data.ssl_status)" -ForegroundColor Green
} catch {
    Write-Host "[WARN] refresh: $_" -ForegroundColor Yellow
}

Write-Host "生产配置: SSL_PROVIDER=acme|certbot, ACME_WEBHOOK_URL 或 CERTBOT_EMAIL+CERTBOT_WEBROOT" -ForegroundColor DarkGray
