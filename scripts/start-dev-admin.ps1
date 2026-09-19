# Start local dev: backend :8001 + admin Vite (5173, or 5174+ if busy)
# 3000 官网 = 主要备份 Vite 暖白版（见 官网启动强制索引-必读.md）；Nuxt 租户预览改走 3002
# Usage:
#   powershell -File scripts/start-dev-admin.ps1
#   powershell -File scripts/start-dev-admin.ps1 -Lan
#   powershell -File scripts/start-dev-admin.ps1 -ForceRestart
param(
  [switch]$Lan,
  [switch]$ForceRestart,
  [switch]$WithSidecars
)

if (-not $Lan -and $env:YOUDING_DEV_BIND_LAN -eq '1') { $Lan = $true }

$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path -LiteralPath (Split-Path -Parent $PSScriptRoot)).Path
$Backend = Join-Path $Root 'backend'
$AdminDir = Join-Path $Root 'frontend\admin'
$TenantDir = Join-Path $Root 'frontend'
$AdminViteScript = Join-Path $Root 'scripts\start-admin-vite-dev.ps1'
$TenantNuxtScript = Join-Path $Root 'scripts\start-tenant-nuxt-dev.ps1'
$Bootstrap = Join-Path $Root 'scripts\dev-backend-bootstrap.ps1'
# 官网运行真相源（强制索引）：工作区 主要备份 Vite，而非 worktree Nuxt
$OfficialSiteDir = Join-Path (Split-Path -Parent $Root) '主要备份\上线网站\frontend'
$ApiPort = 8001
$AdminPort = 5173
$TenantPort = 3000
$NuxtPreviewPort = 3002

function Test-HttpUp([string]$Url, [int]$Sec = 3) {
  try {
    Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $Sec | Out-Null
    return $true
  } catch { return $false }
}

function Test-TenantNuxt([int]$Port) {
  try {
    $html = (Invoke-WebRequest -Uri "http://127.0.0.1:$Port/tenant?__tenant=dev.local" -UseBasicParsing -TimeoutSec 5).Content
    return ($html.Length -gt 200)
  } catch { return $false }
}

function Test-AdminVite([int]$Port) {
  try {
    $html = (Invoke-WebRequest -Uri "http://127.0.0.1:$Port/" -UseBasicParsing -TimeoutSec 3).Content
    return ($html -match '@vite/client' -or $html -match 'src/main\.ts')
  } catch { return $false }
}

function Pick-AdminPort {
  param([int[]]$Candidates = @(5173, 5174, 5175))
  foreach ($p in $Candidates) {
    if (-not (Test-HttpUp "http://127.0.0.1:$p/" 2)) { return $p }
    if (Test-AdminVite $p) { return $p }
  }
  return $Candidates[-1]
}

$AdminPort = Pick-AdminPort

function Get-LanIPv4List {
  $virtualAlias = '(?i)(vEthernet|WSL|Hyper-V|Default Switch|VMware|VirtualBox|Loopback|Teredo|isatap|Npcap|Tailscale)'
  $rows = @()
  try {
    Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
      Where-Object {
        $_.IPAddress -notmatch '^127\.' -and
        $_.PrefixOrigin -ne 'WellKnown' -and
        ($_.IPAddress -match '^192\.168\.' -or $_.IPAddress -match '^10\.' -or $_.IPAddress -match '^172\.(1[6-9]|2[0-9]|3[0-1])\.')
      } |
      ForEach-Object {
        $iface = Get-NetIPInterface -InterfaceIndex $_.InterfaceIndex -ErrorAction SilentlyContinue
        $alias = if ($iface) { [string]$iface.InterfaceAlias } else { '' }
        if ($alias -match $virtualAlias) { return }
        $score = if ($_.IPAddress -match '^192\.168\.') { 100 } elseif ($_.IPAddress -match '^10\.') { 80 } else { 50 }
        $rows += [PSCustomObject]@{ IP = $_.IPAddress; Alias = $alias; Score = $score }
      }
  } catch {
    Write-Host "LAN IP detect failed: $($_.Exception.Message)" -ForegroundColor DarkYellow
  }
  if ($rows.Count -eq 0) {
    $text = (ipconfig | Out-String)
    foreach ($m in [regex]::Matches($text, '(?m)^\s*IPv4[^\:]*:\s*(192\.168\.\d{1,3}\.\d{1,3})')) {
      $rows += [PSCustomObject]@{ IP = $m.Groups[1].Value; Alias = 'ipconfig'; Score = 100 }
    }
  }
  return ,@($rows | Sort-Object -Property Score -Descending | Select-Object -ExpandProperty IP -Unique)
}

$BindHost = if ($Lan) { '0.0.0.0' } else { '127.0.0.1' }
$ViteHost = if ($Lan) { '0.0.0.0' } else { '127.0.0.1' }
$LanIpList = if ($Lan) { @(Get-LanIPv4List) } else { @() }
$LanIp = if ($LanIpList.Count -gt 0) { [string]$LanIpList[0] } else { $null }

$DevEnvFile = Join-Path $Backend 'config\dev\.env'
$corsOrigins = ''
$publicApiBase = "http://127.0.0.1:$ApiPort"
$frontendUrl = ''

if ($Lan -and $LanIpList.Count -gt 0) {
  $lanOriginList = ($LanIpList | ForEach-Object { "http://${_}:$AdminPort" }) -join ','
  $corsOrigins = "http://127.0.0.1:$AdminPort,http://localhost:$AdminPort,$lanOriginList"
}
if ($Lan -and $LanIp) {
  $publicApiBase = "http://${LanIp}:$ApiPort"
  $frontendUrl = "http://${LanIp}:$AdminPort"
}

function Test-LoginProxy([string]$BaseUrl, [int]$Retries = 8) {
  $loginJson = (@{ username_or_email = 'admin'; password = 'admin123' } | ConvertTo-Json -Compress)
  $devUa = @{ 'User-Agent' = 'YouDingSaaS-Internal/1.0' }
  for ($i = 1; $i -le $Retries; $i++) {
    try {
      Invoke-RestMethod -Uri "$BaseUrl/api/v1/auth/login" -Method POST -ContentType 'application/json; charset=utf-8' -Body $loginJson -Headers $devUa | Out-Null
      return $true
    } catch {}
    Start-Sleep -Seconds 2
  }
  return $false
}

function Test-EgressSuppliersRoute([int]$Port) {
  try {
    $spec = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/openapi.json" -TimeoutSec 8
    return [bool]($spec.paths.PSObject.Properties.Name -contains '/api/v1/egress/suppliers')
  } catch { return $false }
}

function Stop-PortListener([int]$Port) {
  Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique |
    ForEach-Object {
      $procId = $_
      if (-not $procId -or $procId -eq $PID) { return }
      Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
      Start-Sleep -Milliseconds 400
    }
}

function Clear-NuxtDevLock([string]$FrontendRoot) {
  $lockRoot = Join-Path $FrontendRoot '.nuxt'
  if (-not (Test-Path -LiteralPath $lockRoot)) { return }
  foreach ($sub in @('dev', 'dist', 'cache')) {
    $p = Join-Path $lockRoot $sub
    if (Test-Path -LiteralPath $p) {
      Remove-Item -LiteralPath $p -Recurse -Force -ErrorAction SilentlyContinue
    }
  }
  foreach ($lockFile in @('nuxt.lock', 'nitro.lock')) {
    $lf = Join-Path $lockRoot $lockFile
    if (Test-Path -LiteralPath $lf) {
      Remove-Item -LiteralPath $lf -Force -ErrorAction SilentlyContinue
    }
  }
  Get-ChildItem -Path $lockRoot -Recurse -Filter '*.lock' -ErrorAction SilentlyContinue |
    ForEach-Object { Remove-Item -LiteralPath $_.FullName -Force -ErrorAction SilentlyContinue }
}

function Test-TenantNuxtReady([int]$Port, [int]$MaxWaitSec = 180) {
  $deadline = (Get-Date).AddSeconds($MaxWaitSec)
  while ((Get-Date) -lt $deadline) {
    if (Test-TenantNuxt $Port) { return $true }
    Start-Sleep -Seconds 3
  }
  return $false
}

if ($ForceRestart) {
  Write-Host "Force restart: stopping :$ApiPort, :$AdminPort, :$TenantPort, :$NuxtPreviewPort" -ForegroundColor Yellow
  Stop-PortListener $ApiPort
  Stop-PortListener $AdminPort
  Stop-PortListener $TenantPort
  Stop-PortListener $NuxtPreviewPort
  Clear-NuxtDevLock $TenantDir
  Start-Sleep -Seconds 2
}

function Ensure-DevEnvKey([string]$Key, [string]$Value) {
  if (-not (Test-Path -LiteralPath $DevEnvFile)) { return }
  $text = Get-Content -LiteralPath $DevEnvFile -Raw -Encoding UTF8
  $pattern = "(?m)^$([regex]::Escape($Key))=.*$"
  if ($text -match $pattern) {
    $text = [regex]::Replace($text, $pattern, "$Key=$Value")
  } else {
    if (-not $text.EndsWith("`n")) { $text += "`r`n" }
    $text += "$Key=$Value`r`n"
  }
  Set-Content -LiteralPath $DevEnvFile -Value $text -Encoding UTF8 -NoNewline
}

if ($WithSidecars) {
  Write-Host 'Starting B2B sidecars (P6 stack)...' -ForegroundColor Cyan
  Ensure-DevEnvKey 'AI_FIND_CUSTOMER_ALLOW_DEV_STUB' '1'
  $p6 = Join-Path $Root 'scripts\start-p6-sidecars-dev.ps1'
  if (Test-Path -LiteralPath $p6) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $p6
    if ($LASTEXITCODE -ne 0) {
      Write-Host 'WARN sidecars partial — continuing dev stack' -ForegroundColor Yellow
    }
  }
}

$needBackend = $ForceRestart -or $WithSidecars -or (-not (Test-HttpUp "http://127.0.0.1:$ApiPort/docs"))
if (-not $needBackend) {
  try {
    $spec = Invoke-RestMethod -Uri "http://127.0.0.1:$ApiPort/openapi.json" -TimeoutSec 8
    $paths = @($spec.paths.PSObject.Properties.Name)
    if ($paths -notcontains '/api/v1/egress/suppliers') {
      Stop-PortListener $ApiPort
      Start-Sleep -Seconds 2
      $needBackend = $true
    }
  } catch {
    Stop-PortListener $ApiPort
    Start-Sleep -Seconds 2
    $needBackend = $true
  }
}
if (-not $needBackend -and -not (Test-EgressSuppliersRoute $ApiPort)) {
  Stop-PortListener $ApiPort
  Start-Sleep -Seconds 2
  $needBackend = $true
}

if ($needBackend) {
  Write-Host "Starting backend on :$ApiPort" -ForegroundColor Cyan
  $bootArgs = @(
    '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $Bootstrap,
    '-BackendDir', $Backend,
    '-DevEnvFile', $DevEnvFile,
    '-BindHost', $BindHost,
    '-ApiPort', $ApiPort,
    '-AdminPort', $AdminPort
  )
  if ($corsOrigins) { $bootArgs += @('-CorsOrigins', $corsOrigins) }
  if ($publicApiBase) { $bootArgs += @('-PublicApiBase', $publicApiBase) }
  if ($frontendUrl) { $bootArgs += @('-FrontendUrl', $frontendUrl) }
  Start-Process powershell -WindowStyle Normal -ArgumentList $bootArgs
  $deadline = (Get-Date).AddSeconds(60)
  while ((Get-Date) -lt $deadline) {
    if (Test-HttpUp "http://127.0.0.1:$ApiPort/docs") { break }
    Start-Sleep -Seconds 2
  }
}

if (-not (Test-AdminVite $AdminPort) -or $ForceRestart) {
  Write-Host "Starting admin Vite on :$AdminPort (--host $ViteHost)" -ForegroundColor Cyan
  $viteArgs = @(
    '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $AdminViteScript,
    '-AdminDir', $AdminDir, '-AdminPort', $AdminPort, '-ViteHost', $ViteHost
  )
  if ($Lan -and $LanIp) { $viteArgs += @('-LanHost', $LanIp) }
  Start-Process powershell -WindowStyle Normal -ArgumentList $viteArgs
  $deadline = (Get-Date).AddSeconds(90)
  while ((Get-Date) -lt $deadline) {
    if (Test-AdminVite $AdminPort) { break }
    Start-Sleep -Seconds 2
  }
}

# 3000 = 主要备份 Vite 官网（暖米白+砖橙，强制索引真源）
if (-not (Test-HttpUp "http://127.0.0.1:$TenantPort/" 3) -or $ForceRestart) {
  if ($ForceRestart) { Stop-PortListener $TenantPort; Start-Sleep -Seconds 1 }
  if (Test-Path -LiteralPath (Join-Path $OfficialSiteDir 'package.json')) {
    $officialLog = Join-Path $OfficialSiteDir 'vite-3000.log'
    Write-Host "Starting official site Vite on :$TenantPort ($OfficialSiteDir)" -ForegroundColor Cyan
    Start-Process powershell -WindowStyle Hidden -ArgumentList @(
      '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command',
      "Set-Location -LiteralPath '$OfficialSiteDir'; `$env:API_HOST='http://127.0.0.1:$ApiPort'; npx vite --port $TenantPort --host $ViteHost *> '$officialLog'"
    )
    $deadline = (Get-Date).AddSeconds(60)
    while ((Get-Date) -lt $deadline) {
      if (Test-HttpUp "http://127.0.0.1:$TenantPort/" 3) { break }
      Start-Sleep -Seconds 2
    }
    Write-Host "Official site : http://127.0.0.1:$TenantPort/  (Vite 暖白，勿与后台薄荷混谈)" -ForegroundColor Green
  } else {
    Write-Host "WARN official site dir missing: $OfficialSiteDir" -ForegroundColor Yellow
  }
}

# 3002 = worktree Nuxt 租户站预览（?__tenant=dev.local），不占 3000
if (-not (Test-HttpUp "http://127.0.0.1:$NuxtPreviewPort/" 3) -or $ForceRestart) {
  if ($ForceRestart) { Stop-PortListener $NuxtPreviewPort; Clear-NuxtDevLock $TenantDir; Start-Sleep -Seconds 1 }
  if (Test-Path -LiteralPath (Join-Path $TenantDir 'package.json')) {
    $nuxtBind = if ($Lan -and $LanIp) { '0.0.0.0' } else { '127.0.0.1' }
    Write-Host "Starting tenant Nuxt preview on :$NuxtPreviewPort (host=$nuxtBind)" -ForegroundColor Cyan
    Start-Process powershell -WindowStyle Hidden -ArgumentList @(
      '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command',
      "`$env:API_HOST='http://127.0.0.1:$ApiPort'; & powershell -NoProfile -ExecutionPolicy Bypass -File '$TenantNuxtScript' -FrontendDir '$TenantDir' -Port $NuxtPreviewPort -NuxtHost '$nuxtBind'"
    )
    Write-Host "Tenant preview : http://127.0.0.1:$NuxtPreviewPort/tenant?__tenant=dev.local&lpro=1" -ForegroundColor Green
  }
}

# 附属二 GoodJob CRM 服务自动化启动检查（:5188 / :4188）
$GoodJobDir = Join-Path (Split-Path -Parent $Root) '_external\goodjob-crm'
if (Test-Path -LiteralPath $GoodJobDir) {
  $gjWebPort = 5188
  $gjApiPort = 4188
  function Test-PortOpen([int]$port) {
    try {
      $client = New-Object System.Net.Sockets.TcpClient('127.0.0.1', $port)
      $client.Close()
      return $true
    } catch { return $false }
  }
  if (-not (Test-PortOpen $gjApiPort)) {
    Write-Host "Starting GoodJob CRM backend on :$gjApiPort" -ForegroundColor Cyan
    $gjBackendDir = Join-Path $GoodJobDir 'backend'
    Start-Process powershell -WindowStyle Hidden -ArgumentList @(
      '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command',
      "cd '$gjBackendDir'; npx tsx src/server.ts"
    )
  }
  if (-not (Test-PortOpen $gjWebPort)) {
    Write-Host "Starting GoodJob CRM frontend on :$gjWebPort" -ForegroundColor Cyan
    $gjFrontendDir = Join-Path $GoodJobDir 'frontend'
    Start-Process powershell -WindowStyle Hidden -ArgumentList @(
      '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command',
      "cd '$gjFrontendDir'; npx vite --host 127.0.0.1 --port $gjWebPort"
    )
  }
}

Write-Host ''
Write-Host "Backend : http://127.0.0.1:$ApiPort/docs" -ForegroundColor Green
Write-Host "Login   : http://127.0.0.1:$AdminPort/login  (LOGIN-LOCK-01)" -ForegroundColor Green
Write-Host "Admin   : http://127.0.0.1:$AdminPort/admin" -ForegroundColor Green
if ($Lan -and $LanIp) {
  Write-Host "LAN     : http://${LanIp}:$AdminPort/login" -ForegroundColor Cyan
  Write-Host "Tip     : same WiFi; allow TCP $AdminPort in firewall" -ForegroundColor DarkGray
}
Write-Host "admin   : admin / admin123  -> /admin" -ForegroundColor Yellow
Write-Host "tenant  : tenant / tenant123 -> /client/today  (dev.local)" -ForegroundColor Yellow
Write-Host "inquiry : /client/inquiries -> language bridge (summary + EN draft)" -ForegroundColor DarkGray
Write-Host "goodjob : /client/annex/goodjob -> GoodJob CRM 附属执行台 (:5188)" -ForegroundColor Cyan
Write-Host "agent   : agent / agent123 -> /agent/performance" -ForegroundColor Yellow
Write-Host "ref     : .project/dev-login-accounts.json" -ForegroundColor DarkGray
Write-Host ''

if (Test-LoginProxy "http://127.0.0.1:$AdminPort") {
  Write-Host 'Login proxy (127.0.0.1): OK' -ForegroundColor Green
} else {
  Write-Host 'Login proxy (127.0.0.1): FAIL' -ForegroundColor Red
  exit 1
}
if ($Lan -and $LanIp) {
  if (Test-LoginProxy "http://${LanIp}:$AdminPort") {
    Write-Host "Login proxy ($LanIp): OK" -ForegroundColor Green
  } else {
    Write-Host "Login proxy ($LanIp): FAIL - check firewall TCP $AdminPort" -ForegroundColor Yellow
  }
}

$verify = Join-Path $Root 'scripts\verify-dev-admin-stack.ps1'
if (Test-Path -LiteralPath $verify) {
  & powershell -NoProfile -ExecutionPolicy Bypass -File $verify -ApiPort $ApiPort -AdminPort $AdminPort
  if ($LASTEXITCODE -ne 0) { exit 1 }
}
