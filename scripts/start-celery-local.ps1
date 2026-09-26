# OPS-04: Celery Worker + Beat Daemon Controller for Windows Dev
param(
  [switch]$Daemon,
  [switch]$Stop,
  [switch]$Status,
  [switch]$Beat,
  [switch]$ForceRestart
)

$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path -Parent $ScriptDir
$Backend = Join-Path $Root 'backend'
$LogDir = Join-Path $Backend 'logs'
if (-not (Test-Path -LiteralPath $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }
$WorkerOutLog = Join-Path $LogDir 'celery-worker.log'
$BeatOutLog = Join-Path $LogDir 'celery-beat.log'

function Get-CeleryProcesses {
  Get-Process -Name celery -ErrorAction SilentlyContinue
}

if ($Status) {
  $procs = Get-CeleryProcesses
  if ($procs) {
    Write-Host "Celery is RUNNING with $($procs.Count) process(es):" -ForegroundColor Green
    $procs | Select-Object Id, ProcessName, Responding, WorkingSet64 | Format-Table
  } else {
    Write-Host "Celery is NOT running." -ForegroundColor Yellow
  }
  return
}

if ($Stop -or $ForceRestart) {
  $procs = Get-CeleryProcesses
  if ($procs) {
    Write-Host "Stopping $($procs.Count) Celery process(es)..." -ForegroundColor Yellow
    $procs | ForEach-Object {
      try { Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue } catch {}
    }
    Start-Sleep -Seconds 1
  } else {
    Write-Host "No running Celery processes to stop." -ForegroundColor DarkGray
  }
  if ($Stop -and -not $ForceRestart) { return }
}

# Resolve Celery binary
$CeleryBin = Join-Path $Backend '.venv\Scripts\celery.exe'
if (-not (Test-Path -LiteralPath $CeleryBin)) {
  $cmd = Get-Command celery -ErrorAction SilentlyContinue
  if ($cmd) { $CeleryBin = $cmd.Source }
}
if (-not (Test-Path -LiteralPath $CeleryBin)) {
  Write-Host "ERROR: celery.exe not found in backend\.venv\Scripts or PATH" -ForegroundColor Red
  exit 1
}

# Check Redis port 6379
function Test-Port([int]$port) {
  try {
    $client = New-Object System.Net.Sockets.TcpClient('127.0.0.1', $port)
    $client.Close()
    return $true
  } catch { return $false }
}

if (-not (Test-Port 6379)) {
  Write-Host "WARN: Redis is not listening on 127.0.0.1:6379. Celery cannot connect." -ForegroundColor Yellow
  return
}

$running = Get-CeleryProcesses
if ($running -and -not $ForceRestart) {
  Write-Host "Celery worker already active (PID: $($running[0].Id)). Use -ForceRestart to restart." -ForegroundColor Green
  return
}

Write-Host "Starting Celery worker using $CeleryBin..." -ForegroundColor Cyan

# Prepare environment variables
$DevEnv = Join-Path $Backend 'config\dev\.env'

$startWorkerCmd = @"
Set-Location -LiteralPath '$Backend'
`$env:PYTHONPATH = '$Backend'
if (Test-Path -LiteralPath '$DevEnv') {
  Get-Content -LiteralPath '$DevEnv' -Encoding UTF8 | ForEach-Object {
    `$line = `$_.Trim()
    if (`$line -and `$line[0] -ne '#' -and `$line -match '=') {
      `$parts = `$line -split '=', 2
      `$k = `$parts[0].Trim()
      `$v = `$parts[1].Trim()
      if (`$k) { Set-Item -Path "Env:`$k" -Value `$v }
    }
  }
}
& '$CeleryBin' -A app.tasks.celery_app worker -l info -P solo *> '$WorkerOutLog'
"@

Start-Process powershell -WindowStyle Hidden -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', $startWorkerCmd)

$deadline = (Get-Date).AddSeconds(10)
$workerStarted = $false
while ((Get-Date) -lt $deadline) {
  Start-Sleep -Seconds 1
  $p = Get-CeleryProcesses
  if ($p) {
    $workerStarted = $true
    Write-Host "Celery worker daemon started successfully (PID: $($p[0].Id))" -ForegroundColor Green
    Write-Host "Logs: $WorkerOutLog" -ForegroundColor DarkGray
    break
  }
}

if (-not $workerStarted) {
  Write-Host "WARN: Celery worker did not appear in process list within 10 seconds. Check $WorkerOutLog" -ForegroundColor Yellow
}

if ($Beat) {
  Write-Host "Starting Celery beat daemon..." -ForegroundColor Cyan
  $startBeatCmd = @"
Set-Location -LiteralPath '$Backend'
`$env:PYTHONPATH = '$Backend'
& '$CeleryBin' -A app.tasks.celery_app beat -l info *> '$BeatOutLog'
"@
  Start-Process powershell -WindowStyle Hidden -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', $startBeatCmd)
  Write-Host "Celery beat daemon initiated. Logs: $BeatOutLog" -ForegroundColor Green
}
