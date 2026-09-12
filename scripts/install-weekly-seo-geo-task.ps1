# 注册 Windows 计划任务：每周 SEO/GEO 闭环 + 周一挖词
# Usage: powershell -ExecutionPolicy Bypass -File scripts/install-weekly-seo-geo-task.ps1

param(
  [string]$RepoRoot = (Split-Path -Parent $PSScriptRoot),
  [string]$TaskName = 'YouDing-Weekly-SEO-GEO',
  [string]$KeywordTaskName = 'YouDing-Monday-SEO-Keywords'
)

$ErrorActionPreference = 'Stop'
$WeeklyScript = Join-Path $RepoRoot 'scripts\run-weekly-seo-geo-loop.ps1'
$KeywordScript = Join-Path $RepoRoot 'scripts\run-seo-keyword-discover.py'
$Py = Join-Path $RepoRoot 'backend\.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Py)) { $Py = 'python' }

if (-not (Test-Path -LiteralPath $WeeklyScript)) {
  Write-Error "Missing $WeeklyScript"
}

$weeklyAction = New-ScheduledTaskAction -Execute 'powershell.exe' `
  -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$WeeklyScript`"" `
  -WorkingDirectory $RepoRoot

$weeklyTrigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Thursday -At '18:00'

Register-ScheduledTask -TaskName $TaskName -Action $weeklyAction -Trigger $weeklyTrigger `
  -Description '优丁每周 SEO/GEO 审计闭环' -Force | Out-Null

$keywordAction = New-ScheduledTaskAction -Execute $Py `
  -Argument "`"$KeywordScript`"" `
  -WorkingDirectory $RepoRoot

$keywordTrigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At '09:00'

Register-ScheduledTask -TaskName $KeywordTaskName -Action $keywordAction -Trigger $keywordTrigger `
  -Description '优丁周一 SEO 挖词' -Force | Out-Null

Write-Host "Registered: $TaskName (Thu 18:00)" -ForegroundColor Green
Write-Host "Registered: $KeywordTaskName (Mon 09:00)" -ForegroundColor Green
