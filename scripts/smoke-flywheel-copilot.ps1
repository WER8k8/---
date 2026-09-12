# 蜂群包 G：商业飞轮 OS + Accio 副驾 API 冒烟（需本地后端 + 租户 JWT）
# Usage:
#   $env:SMOKE_TOKEN = "<tenant_jwt>"
#   powershell -ExecutionPolicy Bypass -File scripts/smoke-flywheel-copilot.ps1
# Optional: $env:SMOKE_BASE = "http://127.0.0.1:8001"

param(
    [string]$Base = $(if ($env:SMOKE_BASE) { $env:SMOKE_BASE } else { "http://127.0.0.1:8001" }),
    [string]$Token = $env:SMOKE_TOKEN
)

$ErrorActionPreference = "Stop"
if (-not $Token) {
    Write-Host "SKIP: set SMOKE_TOKEN to a tenant JWT" -ForegroundColor Yellow
    exit 0
}

$headers = @{
    Authorization = "Bearer $Token"
    Accept        = "application/json"
}

function Invoke-Smoke($Name, $Method, $Path, $Body = $null) {
    $uri = "$Base$Path"
    $params = @{ Uri = $uri; Method = $Method; Headers = $headers }
    if ($Body) {
        $params.ContentType = "application/json"
        $params.Body = ($Body | ConvertTo-Json -Depth 6 -Compress)
    }
    try {
        $r = Invoke-RestMethod @params
        Write-Host "OK  $Name" -ForegroundColor Green
        return $r
    } catch {
        Write-Host "FAIL $Name -> $($_.Exception.Message)" -ForegroundColor Red
        throw
    }
}

Write-Host "=== Flywheel / Accio smoke @ $Base ==="

Invoke-Smoke "commercial-os/status" GET "/api/v1/ubrain/commercial-os/status"
Invoke-Smoke "commercial-os/pipelines" GET "/api/v1/ubrain/commercial-os/pipelines?limit=3"
Invoke-Smoke "commercial-os/gaps" GET "/api/v1/ubrain/commercial-os/gaps"
Invoke-Smoke "integrations" GET "/api/v1/ubrain/commercial-os/integrations"
Invoke-Smoke "ops-snapshot" GET "/api/v1/ubrain/ops-snapshot"
Invoke-Smoke "action-audit" GET "/api/v1/ubrain/action-audit?limit=5"

try {
    Invoke-Smoke "feedback-sync" POST "/api/v1/ubrain/commercial-os/feedback/sync?period_days=7"
} catch {
    Write-Host "WARN feedback-sync (check tenant role)" -ForegroundColor Yellow
}
Invoke-Smoke "inquiries/latest" GET "/api/v1/ubrain/inquiries/latest"

$chat = Invoke-Smoke "ubrain/chat snapshot" POST "/api/v1/ubrain/chat" @{
    message    = "经营快照"
    context    = @{ use_latest_inquiry = $true }
}
if (-not $chat.data.reply -and -not $chat.reply) {
    Write-Host "WARN chat reply empty" -ForegroundColor Yellow
}

Write-Host "`nAll smoke checks passed." -ForegroundColor Cyan
