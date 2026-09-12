# INT-02：探测 n8n webhook 健康与示例回调（本地开发默认 :8001）
param(
    [string]$BaseUrl = "http://127.0.0.1:8001",
    [string]$Secret = $env:N8N_WEBHOOK_SECRET,
    [ValidateSet("health", "feedback", "deerflow_done")]
    [string]$Event = "health",
    [string]$PayloadFile = ""
)

$ErrorActionPreference = "Stop"
$webhookPath = "/api/v1/ubrain/commercial-os/webhook"

if ($Event -eq "health") {
    $uri = "$BaseUrl$webhookPath/health"
    Write-Host "GET $uri"
    $resp = Invoke-RestMethod -Uri $uri -Method Get
    $resp | ConvertTo-Json -Depth 6
    exit 0
}

if (-not $PayloadFile) {
    $examples = Join-Path $PSScriptRoot "..\deploy\examples\n8n"
    $PayloadFile = if ($Event -eq "feedback") {
        Join-Path $examples "n8n-feedback.json"
    } else {
        Join-Path $examples "n8n-deerflow-done.json"
    }
}

if (-not (Test-Path $PayloadFile)) {
    throw "Payload not found: $PayloadFile"
}

$body = Get-Content -Raw -Path $PayloadFile
$headers = @{ "Content-Type" = "application/json" }
if ($Secret) {
    $headers["X-N8N-Webhook-Secret"] = $Secret
}

$uri = "$BaseUrl$webhookPath"
Write-Host "POST $uri (event=$Event)"
try {
    $resp = Invoke-RestMethod -Uri $uri -Method Post -Headers $headers -Body $body
    $resp | ConvertTo-Json -Depth 8
} catch {
    Write-Host $_.Exception.Message
    if ($_.ErrorDetails.Message) { Write-Host $_.ErrorDetails.Message }
    exit 1
}
