# Expert daily roster - each lane runs once per day, archives for evolution/research
# Usage: powershell -File scripts/ops-expert-daily-run.ps1
#        powershell -File scripts/ops-expert-daily-run.ps1 -Lane sre

param(
    [string]$Lane = "",
    [switch]$Quiet
)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$RosterPath = Join-Path $Root ".project\expert-daily-roster.json"
$ArchiveDir = Join-Path $Root "docs\ops\daily-runs"
$HistoryPath = Join-Path $Root "docs\ops\expert-daily-history.jsonl"
$SummaryPath = Join-Path $Root "docs\ops\expert-daily-latest.json"

if (-not (Test-Path $RosterPath)) { throw "missing roster: $RosterPath" }
New-Item -ItemType Directory -Force -Path $ArchiveDir | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path $HistoryPath -Parent) | Out-Null

$Roster = Get-Content $RosterPath -Raw -Encoding UTF8 | ConvertFrom-Json
$Py = Join-Path $Root "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $Py)) { $Py = "python" }

$dayKey = (Get-Date).ToString("yyyy-MM-dd")
$startedAt = (Get-Date).ToUniversalTime().ToString("o")
$results = New-Object System.Collections.Generic.List[object]

function Write-Roster($Msg, $Color) {
    if (-not $Quiet) { Write-Host $Msg -ForegroundColor $Color }
}

function Invoke-LaneStep {
    param($LaneDef)
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $exit = 0
    $detail = ""
    try {
        switch ($LaneDef.kind) {
            "powershell" {
                $scriptPath = Join-Path $Root ($LaneDef.script -replace "/", "\")
                $argList = @()
                if ($LaneDef.args) { $argList = @($LaneDef.args) }
                if ($LaneDef.id -eq 'tenant_geo_audit') {
                    $env:YOUDING_GEO_AUDIT_SKIP_PROBES = '1'
                }
                if ($argList -contains "-AutoStart") {
                    & $scriptPath -AutoStart 2>&1 | Out-String | ForEach-Object { $detail = $_ }
                } elseif ($argList.Count -gt 0) {
                    & $scriptPath @argList 2>&1 | Out-String | ForEach-Object { $detail = $_ }
                } else {
                    & $scriptPath 2>&1 | Out-String | ForEach-Object { $detail = $_ }
                }
                if ($null -ne $LASTEXITCODE) { $exit = $LASTEXITCODE }
            }
            "python" {
                $scriptPath = Join-Path $Root ($LaneDef.script -replace "/", "\")
                Push-Location $Root
                $env:PYTHONPATH = Join-Path $Root "backend"
                & $Py $scriptPath 2>&1 | Out-String | ForEach-Object { $detail = $_ }
                Pop-Location
                if ($null -ne $LASTEXITCODE) { $exit = $LASTEXITCODE }
            }
            "npm" {
                $cwd = Join-Path $Root ($LaneDef.cwd -replace "/", "\")
                Push-Location $cwd
                npm run $LaneDef.script 2>&1 | Out-String | ForEach-Object { $detail = $_ }
                Pop-Location
                if ($null -ne $LASTEXITCODE) { $exit = $LASTEXITCODE }
            }
            "pytest" {
                $env:SECRET_KEY = "test-secret-key-for-unit-testing-only-not-for-production-use"
                $env:JWT_SECRET_KEY = "test-jwt-secret-key-for-unit-testing-only-not-for-production-use"
                Push-Location (Join-Path $Root "backend")
                & $Py -m pytest ($LaneDef.script -replace "/", "\") -q 2>&1 | Out-String | ForEach-Object { $detail = $_ }
                Pop-Location
                if ($null -ne $LASTEXITCODE) { $exit = $LASTEXITCODE }
            }
            default {
                $exit = 1
                $detail = "unknown kind $($LaneDef.kind)"
            }
        }
    } catch {
        $exit = 1
        $detail = $_.Exception.Message
    }
    $sw.Stop()
    $reportData = $null
    if ($LaneDef.report) {
        $rp = Join-Path $Root ($LaneDef.report -replace "/", "\")
        if (Test-Path $rp) {
            try { $reportData = Get-Content $rp -Raw -Encoding UTF8 | ConvertFrom-Json } catch {}
        }
    }
    return [ordered]@{
        id = $LaneDef.id
        expert = $LaneDef.expert
        focus = $LaneDef.focus
        ok = ($exit -eq 0)
        exit = $exit
        duration_ms = [int]$sw.ElapsedMilliseconds
        report_path = $LaneDef.report
        report_snapshot = $reportData
        detail_tail = if ($detail.Length -gt 400) { $detail.Substring($detail.Length - 400) } else { $detail }
    }
}

Write-Roster "=== Expert daily roster $dayKey ===" "Cyan"

$lanes = @($Roster.lanes)
if ($Lane) {
    $lanes = @($lanes | Where-Object { $_.id -eq $Lane })
    if ($lanes.Count -eq 0) { throw "unknown lane: $Lane" }
}

foreach ($laneDef in $lanes) {
    Write-Roster "--- [$($laneDef.expert)] $($laneDef.id): $($laneDef.focus) ---" "Cyan"
    $row = Invoke-LaneStep -LaneDef $laneDef
    $results.Add($row) | Out-Null
    $color = if ($row.ok) { "Green" } else { "Red" }
    Write-Roster ("  -> {0} ({1}ms)" -f $(if ($row.ok) { "PASS" } else { "FAIL" }), $row.duration_ms) $color
}

$fail = @($results | Where-Object { -not $_.ok }).Count
$passCount = @($results | Where-Object { $_.ok }).Count
$laneRows = @()
foreach ($r in $results) { $laneRows += $r }

$payload = @{
    day = $dayKey
    run_kind = "full_roster"
    started_at = $startedAt
    finished_at = (Get-Date).ToUniversalTime().ToString("o")
    ok = ($fail -eq 0)
    fail_count = $fail
    pass_count = $passCount
    lane_count = $laneRows.Count
    lanes = $laneRows
    evolution_hint = "急诊复盘: docs/ops/daily-runs/$dayKey.json + expert-daily-history.jsonl"
}

$archiveFile = Join-Path $ArchiveDir "$dayKey.json"
($payload | ConvertTo-Json -Depth 8) | Set-Content -Path $archiveFile -Encoding UTF8
($payload | ConvertTo-Json -Depth 8 -Compress) | Add-Content -Path $HistoryPath -Encoding UTF8
($payload | ConvertTo-Json -Depth 6) | Set-Content -Path $SummaryPath -Encoding UTF8

Write-Roster "Archive: $archiveFile" "Gray"
Write-Roster "History: $HistoryPath" "Gray"

# Phase 2-4: 自动修补 -> 站会 -> 通知 Owner（勤劳人格，无需 Owner 开口）
$RemediateScript = Join-Path $Root "scripts\ops-expert-auto-remediate.ps1"
$StandupScript = Join-Path $Root "scripts\ops-expert-daily-standup.ps1"
if (Test-Path $RemediateScript) {
    Write-Roster "--- auto-remediate (small fixes) ---" "Cyan"
    & $RemediateScript -Quiet | Out-Null
}
if (Test-Path $StandupScript) {
    Write-Roster "--- daily standup + notify owner ---" "Cyan"
    & $StandupScript -Quiet | Out-Null
}

$Py = Join-Path $Root "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $Py)) { $Py = "python" }
$Honesty = Join-Path $Root "scripts\validate-ops-honesty.py"
if (Test-Path $Honesty) {
    $env:YOUDING_REPO_ROOT = $Root
    & $Py $Honesty 2>&1 | Out-Null
}

if ($fail -eq 0) {
    Write-Roster "Expert daily: ALL PASS ($($results.Count) lanes)" "Green"
    exit 0
}
Write-Roster "Expert daily: $fail lane(s) FAIL - next session agents fix P0 first" "Red"
exit 1
