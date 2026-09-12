# T5：发布 Worker cron 友好脚本（需超管 OPS_CRON_TOKEN）
param(
    [string]$BaseUrl = $(if ($env:SMOKE_BASE) { $env:SMOKE_BASE } else { "http://127.0.0.1:8001" }),
    [int]$RunLimit = 20,
    [int]$RetryLimit = 50,
    [switch]$RetryOnly
)

$token = $env:OPS_CRON_TOKEN
if (-not $token) {
    Write-Host "SKIP: set OPS_CRON_TOKEN (super_admin JWT)" -ForegroundColor Yellow
    exit 0
}

$headers = @{ Authorization = "Bearer $token" }

if (-not $RetryOnly) {
    $runUri = "$BaseUrl/api/v1/ops/publish-worker/run?limit=$RunLimit"
    $run = Invoke-RestMethod -Uri $runUri -Method POST -Headers $headers
    Write-Host "RUN:" ($run.data | ConvertTo-Json -Compress)
}

$retryUri = "$BaseUrl/api/v1/ops/publish-worker/retry-failed?limit=$RetryLimit"
$retry = Invoke-RestMethod -Uri $retryUri -Method POST -Headers $headers
Write-Host "RETRY requeued:" $retry.data.requeued

$status = Invoke-RestMethod -Uri "$BaseUrl/api/v1/ops/publish-worker/status" -Headers $headers
Write-Host "QUEUE:" ($status.data | ConvertTo-Json -Compress)
