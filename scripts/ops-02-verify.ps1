# OPS-02：生产 Hermes / n8n 实机验收脚本
param(
    [string]$BaseUrl = "http://127.0.0.1:8001",
    [string]$Token = $env:ADMIN_BEARER_TOKEN,
    [string]$N8nSecret = $env:N8N_WEBHOOK_SECRET
)

$ErrorActionPreference = "Stop"
$headers = @{ "Content-Type" = "application/json" }
if ($Token) { $headers["Authorization"] = "Bearer $Token" }

Write-Host "=== 1. n8n webhook health ==="
Invoke-RestMethod -Uri "$BaseUrl/api/v1/ubrain/commercial-os/webhook/health" -Method Get | ConvertTo-Json

Write-Host "=== 2. Hermes ops run (需 super_admin token) ==="
if (-not $Token) {
    Write-Warning "跳过 ops/run：请设置 ADMIN_BEARER_TOKEN"
} else {
    try {
        $r = Invoke-RestMethod -Uri "$BaseUrl/api/v1/hermes/ops/run" -Method Post -Headers $headers
        $r | ConvertTo-Json -Depth 4
    } catch {
        Write-Warning $_.Exception.Message
    }
}

Write-Host "=== 3. Command center snapshot ==="
if ($Token) {
    $cc = Invoke-RestMethod -Uri "$BaseUrl/api/v1/hermes/ops/command-center" -Method Get -Headers $headers
    Write-Host "overall:" $cc.data.overall_status
    Write-Host "deerflow queued:" $cc.data.deerflow.queue.counts.queued
}

Write-Host "=== 4. n8n sample payload (optional) ==="
if ($N8nSecret) {
    & "$PSScriptRoot\test-n8n-webhook.ps1" -BaseUrl $BaseUrl -Secret $N8nSecret -Event health
}

Write-Host "Done. 生产请确认 FEISHU_WEBHOOK_URL 收到卡片。"
