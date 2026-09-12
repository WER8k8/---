# Ops autopilot - ASCII launchers in %LOCALAPPDATA% (fix task 267011 on Unicode paths)

param(
    [switch]$Quiet
)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$DailyScript = Join-Path $Root "scripts\ops-daily-health.ps1"
$ExpertDailyScript = Join-Path $Root "scripts\ops-expert-daily-run.ps1"
$WeeklyScript = Join-Path $Root "scripts\ops-weekly-hardening.ps1"
$Marker = Join-Path $Root ".project\ops-autopilot-installed.json"
$LocalOps = Join-Path $env:LOCALAPPDATA "YouDingOps"
$RootFile = Join-Path $LocalOps "repo-root.txt"
$LaunchHealth = Join-Path $LocalOps "launch-daily-health.ps1"
$LaunchExpert = Join-Path $LocalOps "launch-expert-daily.ps1"

if (-not (Test-Path $DailyScript)) { throw "missing $DailyScript" }

function Write-Ops($Msg, $Color) {
    if (-not $Quiet) { Write-Host $Msg -ForegroundColor $Color }
}

New-Item -ItemType Directory -Force -Path $LocalOps | Out-Null
[System.IO.File]::WriteAllText($RootFile, $Root.TrimEnd('\'), [System.Text.UTF8Encoding]::new($false))

$healthLauncher = @"
`$ErrorActionPreference = 'Stop'
`$Log = Join-Path `$env:LOCALAPPDATA 'YouDingOps\launch-daily-health.log'
function Log(`$m){ "`$(Get-Date -Format o) `$m" | Add-Content -Path `$Log -Encoding UTF8 }
try {
  Log 'start'
  `$env:CI = 'true'
  `$env:npm_config_yes = 'true'
  `$RootFile = Join-Path `$env:LOCALAPPDATA 'YouDingOps\repo-root.txt'
  `$Root = [System.IO.File]::ReadAllText(`$RootFile).Trim()
  Set-Location -LiteralPath `$Root
  & (Join-Path `$Root 'scripts\ops-daily-health.ps1') -AutoStart
  `$code = if (`$null -ne `$LASTEXITCODE) { `$LASTEXITCODE } else { 0 }
  Log "exit `$code"
  exit `$code
} catch {
  Log "error `$(`$_.Exception.Message)"
  exit 1
}
"@
Set-Content -Path $LaunchHealth -Value $healthLauncher -Encoding UTF8

$expertLauncher = @"
`$ErrorActionPreference = 'Stop'
`$Log = Join-Path `$env:LOCALAPPDATA 'YouDingOps\launch-expert-daily.log'
function Log(`$m){ "`$(Get-Date -Format o) `$m" | Add-Content -Path `$Log -Encoding UTF8 }
try {
  Log 'start'
  `$env:CI = 'true'
  `$env:npm_config_yes = 'true'
  `$RootFile = Join-Path `$env:LOCALAPPDATA 'YouDingOps\repo-root.txt'
  `$Root = [System.IO.File]::ReadAllText(`$RootFile).Trim()
  Set-Location -LiteralPath `$Root
  & (Join-Path `$Root 'scripts\ops-expert-daily-run.ps1') -Quiet
  `$code = if (`$null -ne `$LASTEXITCODE) { `$LASTEXITCODE } else { 0 }
  Log "exit `$code"
  exit `$code
} catch {
  Log "error `$(`$_.Exception.Message)"
  exit 1
}
"@
Set-Content -Path $LaunchExpert -Value $expertLauncher -Encoding UTF8

function Register-YouDingTask {
    param(
        [string]$Name,
        [string]$LauncherPath,
        [string]$Description,
        [string]$Schedule
    )
    $taskName = "YouDing\$Name"
    try {
        $action = New-ScheduledTaskAction `
            -Execute "powershell.exe" `
            -Argument "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$LauncherPath`"" `
            -WorkingDirectory $LocalOps
        $settings = New-ScheduledTaskSettingsSet `
            -AllowStartIfOnBatteries `
            -DontStopIfGoingOnBatteries `
            -StartWhenAvailable `
            -ExecutionTimeLimit (New-TimeSpan -Hours 3) `
            -MultipleInstances IgnoreNew
        $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

        if ($Schedule -eq "logon") { $trigger = New-ScheduledTaskTrigger -AtLogOn }
        elseif ($Schedule -eq "daily") { $trigger = New-ScheduledTaskTrigger -Daily -At "08:00" }
        elseif ($Schedule -eq "weekly") { $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Friday -At "18:00" }
        else { throw "unknown schedule $Schedule" }

        Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description $Description -Force | Out-Null
        Write-Ops "registered: $taskName ($Schedule) via $LauncherPath" "Green"
        return $true
    } catch {
        Write-Ops "task skip $taskName : $($_.Exception.Message)" "Yellow"
        return $false
    }
}

Write-Ops "=== YouDing ops autopilot install (honest) ===" "Cyan"

$ok1 = Register-YouDingTask -Name "Ops-DailyHealth-Logon" -LauncherPath $LaunchHealth -Description "YouDing health only on logon" -Schedule "logon"

$weeklyLauncherPath = Join-Path $LocalOps "launch-weekly.ps1"
$weeklyLauncher = @"
`$ErrorActionPreference = 'Stop'
`$RootFile = Join-Path `$env:LOCALAPPDATA 'YouDingOps\repo-root.txt'
`$Root = [System.IO.File]::ReadAllText(`$RootFile).Trim()
Set-Location -LiteralPath `$Root
& (Join-Path `$Root 'scripts\ops-weekly-hardening.ps1')
exit `$LASTEXITCODE
"@
Set-Content -Path $weeklyLauncherPath -Value $weeklyLauncher -Encoding UTF8

$okExpert = Register-YouDingTask -Name "Ops-ExpertDailyRoster" -LauncherPath $LaunchExpert -Description "YouDing full 7-lane roster 08:00" -Schedule "daily"
$ok3 = Register-YouDingTask -Name "Ops-WeeklyHardening" -Description "YouDing weekly hardening" -LauncherPath $weeklyLauncherPath -Schedule "weekly"

$payload = @{
    installed_at = (Get-Date).ToUniversalTime().ToString("o")
    repo_root_file = $RootFile
    launchers = @{
        health = $LaunchHealth
        expert = $LaunchExpert
    }
    tasks = @(
        $(if ($ok1) { "YouDing\Ops-DailyHealth-Logon" }),
        $(if ($okExpert) { "YouDing\Ops-ExpertDailyRoster" }),
        $(if ($ok3) { "YouDing\Ops-WeeklyHardening" })
    ) | Where-Object { $_ }
    honesty_gate = "scripts/validate-ops-honesty.py"
}
$projectDir = Split-Path $Marker -Parent
New-Item -ItemType Directory -Force -Path $projectDir | Out-Null
($payload | ConvertTo-Json -Depth 5) | Set-Content -Path $Marker -Encoding UTF8

Write-Ops "Ops autopilot: $Marker" "Green"
& powershell -NoProfile -ExecutionPolicy Bypass -File $LaunchHealth | Out-Null
Write-Ops "Health launcher smoke done." "Green"
