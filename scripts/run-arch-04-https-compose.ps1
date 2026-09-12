# ARCH-04 · HTTPS + compose 实跑记录（staging 自签 + compose config 校验）
# Usage: powershell -ExecutionPolicy Bypass -File scripts/run-arch-04-https-compose.ps1
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Py = Join-Path $Root "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $Py)) { $Py = "python" }
$Report = Join-Path $Root "docs\arch-04-https-compose-latest.json"
$ComposeProd = Join-Path $Root "docker-compose.prod.yml"
$ComposeDev = Join-Path $Root "docker-compose.dev.yml"
$ComposeMirror = Join-Path $Root "docker-compose.cncfstack.yml"

& $Py (Join-Path $Root "scripts\gen-staging-ssl.py")
$sslExit = $LASTEXITCODE
& $Py (Join-Path $Root "scripts\validate-arch-04-nginx-ssl.py")
$nginxExit = $LASTEXITCODE

$configOk = $false
$configError = $null
$dockerOk = $false
try {
  $null = docker info 2>&1
  $dockerOk = ($LASTEXITCODE -eq 0)
} catch { $dockerOk = $false }

if ($dockerOk) {
  Push-Location $Root
  docker compose -f $ComposeProd -f $ComposeMirror config 2>&1 | Out-Null
  $configOk = ($LASTEXITCODE -eq 0)
  if (-not $configOk) { $configError = "docker compose config prod+cncfstack failed" }
  docker compose -f $ComposeDev -f $ComposeMirror config 2>&1 | Out-Null
  if ($LASTEXITCODE -ne 0) { $configOk = $false; $configError = "docker compose config dev+cncfstack failed" }
  Pop-Location
} else {
  $configError = "Docker unavailable; SSL self-sign + file checks only"
}

$nginxConf = Join-Path $Root "docker\nginx\default.conf"
$sslReadme = Join-Path $Root "docker\nginx\ssl\README.md"
$checks = @{
  nginx_conf = Test-Path $nginxConf
  ssl_readme = Test-Path $sslReadme
  compose_prod = Test-Path $ComposeProd
  ssl_fullchain = Test-Path (Join-Path $Root "docker\nginx\ssl\fullchain.pem")
  ssl_privkey = Test-Path (Join-Path $Root "docker\nginx\ssl\privkey.pem")
}

$pass = ($sslExit -eq 0) -and ($nginxExit -eq 0) -and $checks.ssl_fullchain -and $checks.ssl_privkey -and $checks.nginx_conf -and ($configOk -or -not $dockerOk)

$payload = @{
  generated_at = (Get-Date).ToString("o")
  task = "ARCH-04"
  pass = $pass
  docker_ready = $dockerOk
  compose_config_ok = $configOk
  compose_config_error = $configError
  nginx_ssl_check_exit = $nginxExit
  checks = $checks
  domain_staging = "demo.youding.local"
  compose_files = @("docker-compose.prod.yml", "docker-compose.dev.yml", "docker-compose.cncfstack.yml")
}
($payload | ConvertTo-Json -Depth 5) | Set-Content -Path $Report -Encoding UTF8

if ($pass) {
  Write-Host "ARCH-04 HTTPS compose: PASS -> $Report" -ForegroundColor Green
} else {
  Write-Host "ARCH-04 HTTPS compose: FAIL -> $Report" -ForegroundColor Red
}
exit $(if ($pass) { 0 } else { 1 })
