# 运维每日健康检查 — 不用懂代码，双击或计划任务跑即可
# 用法: powershell -File scripts/ops-daily-health.ps1
#       powershell -File scripts/ops-daily-health.ps1 -AutoStart

param(
    [switch]$AutoStart,
    [string]$BaseUrl = "http://127.0.0.1:8001",
    [string]$AdminUrl = "http://127.0.0.1:5173"
)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$ReportDir = Join-Path $Root "docs\ops"
$Report = Join-Path $ReportDir "daily-health-latest.json"
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null

function Test-Endpoint($Name, $Url, $MaxMs = 3000) {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec ([math]::Ceiling($MaxMs / 1000))
        $sw.Stop()
        return @{
            name = $Name
            ok = ($r.StatusCode -ge 200 -and $r.StatusCode -lt 400)
            status = $r.StatusCode
            ms = [int]$sw.ElapsedMilliseconds
        }
    } catch {
        $sw.Stop()
        return @{
            name = $Name
            ok = $false
            status = 0
            ms = [int]$sw.ElapsedMilliseconds
            error = $_.Exception.Message
        }
    }
}

Write-Host "=== 优丁 · 每日健康检查 ===" -ForegroundColor Cyan
$checks = @()

$checks += Test-Endpoint "backend_health" "$BaseUrl/api/v1/health"
$checks += Test-Endpoint "backend_ready" "$BaseUrl/api/v1/health/ready" 5000
$checks += Test-Endpoint "admin_login" "$AdminUrl/login"
$checks += Test-Endpoint "ops_readiness_public" "$BaseUrl/api/v1/ops/readiness/public" 5000

$backendDown = -not ($checks | Where-Object { $_.name -eq "backend_health" -and $_.ok })
$adminDown = -not ($checks | Where-Object { $_.name -eq "admin_login" -and $_.ok })

if ($AutoStart -and ($backendDown -or $adminDown)) {
    Write-Host "服务未就绪，尝试自动拉起 launch-dev-admin-safe.ps1 ..." -ForegroundColor Yellow
    $safeLauncher = Join-Path $Root 'scripts\launch-dev-admin-safe.ps1'
    Start-Process powershell -ArgumentList '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $safeLauncher -WindowStyle Minimized
    $deadline = (Get-Date).AddSeconds(150)
    $checks = @()
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 5
        $checks = @()
        $checks += Test-Endpoint "backend_health" "$BaseUrl/api/v1/health" 8000
        if (-not ($checks[-1].ok)) { continue }
        $checks += Test-Endpoint "backend_ready" "$BaseUrl/api/v1/health/ready" 10000
        $checks += Test-Endpoint "admin_login" "$AdminUrl/login" 15000
        $checks += Test-Endpoint "ops_readiness_public" "$BaseUrl/api/v1/ops/readiness/public" 10000
        if (($checks | Where-Object { -not $_.ok }).Count -eq 0) { break }
    }
}

$fail = @($checks | Where-Object { -not $_.ok }).Count
foreach ($c in $checks) {
    $color = if ($c.ok) { "Green" } else { "Red" }
    $extra = if ($c.error) { " — $($c.error)" } else { "" }
    Write-Host ("  [{0}] {1} {2}ms{3}" -f $(if ($c.ok) { "OK" } else { "FAIL" }), $c.name, $c.ms, $extra) -ForegroundColor $color
}

$payload = @{
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
    task = "ops-daily-health"
    run_kind = "health_only"
    ok = ($fail -eq 0)
    fail_count = $fail
    checks = $checks
    hint = if ($fail -gt 0) { "运行: powershell -File scripts/start-dev-admin.ps1" } else { "全部正常" }
}
($payload | ConvertTo-Json -Depth 5) | Set-Content -Path $Report -Encoding UTF8

if ($fail -eq 0) {
    Write-Host "每日健康: 全部通过 -> $Report" -ForegroundColor Green
    exit 0
}
Write-Host "每日健康: $fail 项失败 -> $Report" -ForegroundColor Red
Write-Host "修复: powershell -File scripts/start-dev-admin.ps1" -ForegroundColor Yellow
exit 1
