# 消费本租户 queued DeerFlow 任务（副驾轮询 / cron）
param(
    [string]$Base = $(if ($env:SMOKE_BASE) { $env:SMOKE_BASE } else { "http://127.0.0.1:8001" }),
    [int]$Limit = 10
)

$token = $env:SMOKE_TOKEN
if (-not $token) {
    Write-Host "SKIP: set SMOKE_TOKEN (tenant user JWT)" -ForegroundColor Yellow
    exit 0
}

$headers = @{ Authorization = "Bearer $token" }
$uri = "$Base/api/v1/ubrain/jobs/run-pending?limit=$Limit"
$r = Invoke-RestMethod -Uri $uri -Method POST -Headers $headers
Write-Host "processed:" $r.data.processed
$r.data.items | ForEach-Object { Write-Host " -" $_.id $_.status $_.intent }
