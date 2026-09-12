# Sync UBrain sales feedback into research memory (Windows Task Scheduler friendly)
# Requires: UBRAIN_API_TOKEN = Bearer JWT for a tenant-bound user
# Optional: UBRAIN_API_BASE = https://your-api.example.com

param(
    [int]$PeriodDays = 7
)

$Base = if ($env:UBRAIN_API_BASE) { $env:UBRAIN_API_BASE.TrimEnd('/') } else { "http://127.0.0.1:8001" }
$Token = $env:UBRAIN_API_TOKEN
if (-not $Token) {
    Write-Error "Set UBRAIN_API_TOKEN to a valid Bearer JWT"
    exit 1
}

$Uri = "$Base/api/v1/ubrain/commercial-os/feedback/sync?period_days=$PeriodDays"
$Headers = @{ Authorization = "Bearer $Token" }

try {
    $resp = Invoke-RestMethod -Method Post -Uri $Uri -Headers $Headers -ContentType "application/json"
    $data = $resp.data
    if (-not $data) { $data = $resp }
    Write-Host "feedback sync ok snapshot=$($data.snapshot_id)"
    if ($data.deerflow_next_prompt) {
        Write-Host $data.deerflow_next_prompt
    }
    exit 0
} catch {
    Write-Error $_
    exit 2
}
