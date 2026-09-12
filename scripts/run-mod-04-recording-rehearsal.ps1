# MOD-04 · 本地录屏彩排（vite preview / 已有 dev 5173）
# Usage: powershell -ExecutionPolicy Bypass -File scripts/run-mod-04-recording-rehearsal.ps1
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$Admin = Join-Path $Root "frontend\admin"
$Py = Join-Path $Root "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $Py)) { $Py = "python" }
$DistIndex = Join-Path $Admin "dist\index.html"
$PreviewPort = 4173

function Test-TcpPort([int]$Port) {
  try {
    $c = New-Object System.Net.Sockets.TcpClient
    $c.Connect("127.0.0.1", $Port)
    $c.Close()
    return $true
  } catch { return $false }
}

function Wait-Port([int]$Port, [int]$Seconds = 45) {
  $deadline = (Get-Date).AddSeconds($Seconds)
  while ((Get-Date) -lt $deadline) {
    if (Test-TcpPort $Port) { return $true }
    Start-Sleep -Seconds 1
  }
  return $false
}

$previewJob = $null
$baseUrl = $null

try {
  if (Test-TcpPort 5173) {
    $baseUrl = "http://127.0.0.1:5173"
    Write-Host "MOD-04 rehearsal: reuse dev :5173" -ForegroundColor Green
  } elseif (Test-TcpPort $PreviewPort) {
    $baseUrl = "http://127.0.0.1:$PreviewPort"
    Write-Host "MOD-04 rehearsal: reuse preview :$PreviewPort" -ForegroundColor Green
  } else {
    if (-not (Test-Path $DistIndex)) {
      Write-Host "=== MOD-04 build dist (vite) ===" -ForegroundColor Cyan
      Push-Location $Admin
      npm run build:cap 2>&1 | Out-Null
      Pop-Location
      if (-not (Test-Path $DistIndex)) {
        Write-Host "MOD-04 rehearsal: dist missing after build" -ForegroundColor Red
        exit 1
      }
    }
    Write-Host "=== MOD-04 vite preview :$PreviewPort ===" -ForegroundColor Cyan
    $npmCmd = (Get-Command npm.cmd -ErrorAction SilentlyContinue).Source
    if (-not $npmCmd) { $npmCmd = "npm.cmd" }
    Push-Location $Admin
    $previewJob = Start-Process -FilePath $npmCmd -ArgumentList @("run", "preview", "--", "--port", "$PreviewPort", "--host", "127.0.0.1") `
      -PassThru -WindowStyle Hidden -WorkingDirectory $Admin
    Pop-Location
    if (-not (Wait-Port $PreviewPort)) {
      Write-Host "MOD-04 rehearsal: preview failed to bind :$PreviewPort" -ForegroundColor Red
      exit 1
    }
    $baseUrl = "http://127.0.0.1:$PreviewPort"
  }

  $env:MOD04_BASE_URL = $baseUrl
  & $Py (Join-Path $Root "scripts\validate-mod-04-recording-rehearsal.py")
  exit $LASTEXITCODE
} finally {
  if ($previewJob -and -not $previewJob.HasExited) {
    Stop-Process -Id $previewJob.Id -Force -ErrorAction SilentlyContinue
  }
}
