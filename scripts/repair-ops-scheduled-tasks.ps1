# Repair YouDing scheduled tasks (requires admin once)
# Usage: powershell -ExecutionPolicy Bypass -File scripts/repair-ops-scheduled-tasks.ps1

param(
    [switch]$SkipTest
)

$ErrorActionPreference = "Stop"

function Test-Admin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $p = New-Object Security.Principal.WindowsPrincipal($id)
    return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Admin)) {
    Write-Host "Re-launching with Administrator..." -ForegroundColor Yellow
    $argList = "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    if ($SkipTest) { $argList += " -SkipTest" }
    Start-Process -FilePath "powershell.exe" -Verb RunAs -ArgumentList $argList -Wait
    exit $LASTEXITCODE
}

$Root = Split-Path -Parent $PSScriptRoot
$InstallScript = Join-Path $Root "scripts\install-ops-autopilot.ps1"
$LocalOps = Join-Path $env:LOCALAPPDATA "YouDingOps"
$Log = Join-Path $LocalOps "repair-scheduled-tasks.log"

New-Item -ItemType Directory -Force -Path $LocalOps | Out-Null
function Log($m) { "$(Get-Date -Format o) $m" | Add-Content -Path $Log -Encoding UTF8; Write-Host $m }

Log "=== repair start (admin) ==="

$names = @(
    "Ops-DailyHealth-Logon",
    "Ops-DailyHealth-Periodic",
    "Ops-ExpertDailyRoster",
    "Ops-WeeklyHardening"
)
foreach ($n in $names) {
    $full = "\YouDing\$n"
    $existing = Get-ScheduledTask -TaskPath "\YouDing\" -TaskName $n -ErrorAction SilentlyContinue
    if ($existing) {
        try {
            Unregister-ScheduledTask -TaskName $n -TaskPath "\YouDing\" -Confirm:$false
            Log "removed old task: $full"
        } catch {
            Log "WARN remove $full : $($_.Exception.Message)"
        }
    }
}

& powershell -NoProfile -ExecutionPolicy Bypass -File $InstallScript
if ($LASTEXITCODE -ne 0) {
    Log "install script exit $LASTEXITCODE"
}

Get-ScheduledTask -TaskPath "\YouDing\" | ForEach-Object {
    $info = Get-ScheduledTaskInfo $_
    Log ("task {0} state={1} last={2} next={3}" -f $_.TaskName, $_.State, $info.LastTaskResult, $info.NextRunTime)
}

if ($SkipTest) {
    Log "skip test"
    exit 0
}

Log "trigger Ops-ExpertDailyRoster..."
Start-ScheduledTask -TaskPath "\YouDing\" -TaskName "Ops-ExpertDailyRoster"

$deadline = (Get-Date).AddMinutes(3)
$lastResult = $null
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 10
    $info = Get-ScheduledTaskInfo -TaskPath "\YouDing\" -TaskName "Ops-ExpertDailyRoster"
    $state = (Get-ScheduledTask -TaskPath "\YouDing\" -TaskName "Ops-ExpertDailyRoster").State
    Log ("poll state=$state lastResult=$($info.LastTaskResult)")
    if ($state -eq "Ready" -and $info.LastRunTime -gt (Get-Date).AddMinutes(-5)) {
        $lastResult = $info.LastTaskResult
        if ($lastResult -eq 0) { break }
        if ($lastResult -ne 267009) { break }
    }
}

$expertLog = Join-Path $LocalOps "launch-expert-daily.log"
if (Test-Path $expertLog) {
    Log "--- launch-expert-daily.log tail ---"
    Get-Content $expertLog -Tail 8 | ForEach-Object { Log $_ }
}

if ($null -eq $lastResult) {
    Log "FAIL: task did not finish in 3 minutes"
    exit 1
}
if ($lastResult -eq 0) {
    Log "OK: scheduled task LastTaskResult=0"
    exit 0
}

Log "FAIL: scheduled task LastTaskResult=$lastResult"
exit 1
