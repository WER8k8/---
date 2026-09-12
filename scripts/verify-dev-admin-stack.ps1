# 本地 Admin 开发栈探活 — start-dev-admin 收尾 / 会话内自检
# 用法: powershell -File scripts/verify-dev-admin-stack.ps1
param(
  [int]$ApiPort = 8001,
  [int]$AdminPort = 5173,
  [int]$MaxHealthMs = 800
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$failures = @()

function Add-Fail([string]$Msg) { $script:failures += $Msg }

function Measure-HttpMs([string]$Url, [int]$Sec = 8) {
  $sw = [System.Diagnostics.Stopwatch]::StartNew()
  try {
    $null = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $Sec
    $sw.Stop()
    return @{ ok = $true; ms = [int]$sw.ElapsedMilliseconds }
  } catch {
    $sw.Stop()
    return @{ ok = $false; ms = [int]$sw.ElapsedMilliseconds; err = $_.Exception.Message }
  }
}

function Measure-HttpMsWarm([string]$Url, [int]$Attempts = 3, [int]$PauseMs = 1500) {
  $best = @{ ok = $false; ms = 999999; err = 'unreachable' }
  for ($i = 0; $i -lt $Attempts; $i++) {
    $r = Measure-HttpMs $Url
    if ($r.ok -and $r.ms -lt $best.ms) { $best = $r }
    if ($r.ok -and $r.ms -le $MaxHealthMs) { return $r }
    if ($i -lt ($Attempts - 1)) { Start-Sleep -Milliseconds $PauseMs }
  }
  return $best
}

$health = Measure-HttpMsWarm "http://127.0.0.1:$ApiPort/api/v1/health"
if (-not $health.ok) {
  Add-Fail "API :$ApiPort 不可达 — 请运行 scripts/start-dev-admin.ps1"
} elseif ($health.ms -gt $MaxHealthMs) {
  Add-Fail "API /health 过慢 ($($health.ms)ms > ${MaxHealthMs}ms)，可能 Redis/进程阻塞 — 建议 -ForceRestart"
}

$ready = Measure-HttpMsWarm "http://127.0.0.1:$ApiPort/api/v1/health/ready" 2 2000
if (-not $ready.ok) {
  Add-Fail "API /health/ready 失败"
} elseif ($ready.ms -gt ($MaxHealthMs * 3)) {
  Add-Fail "API /health/ready 过慢 ($($ready.ms)ms)，检查 REDIS_ENABLED 与就绪探针"
}

$admin = Measure-HttpMs "http://127.0.0.1:$AdminPort/login" 10
if (-not $admin.ok) {
  Add-Fail "Admin :$AdminPort 不可达"
}

$loginBody = '{"username_or_email":"admin","password":"admin123"}'
try {
  $sw = [System.Diagnostics.Stopwatch]::StartNew()
  $null = Invoke-RestMethod -Uri "http://127.0.0.1:$ApiPort/api/v1/auth/login" -Method Post -Body $loginBody -ContentType 'application/json' -TimeoutSec 15
  $sw.Stop()
  if ($sw.ElapsedMilliseconds -gt 3000) {
    Add-Fail "登录接口过慢 ($($sw.ElapsedMilliseconds)ms)"
  }
} catch {
  Add-Fail "登录接口失败: $($_.Exception.Message)"
}

# Vue 路由组件不得是整页 HTML（今日 AiConfig 类事故）
$badVue = Get-ChildItem -Path (Join-Path $Root 'frontend\admin\src\views') -Recurse -Filter '*.vue' -ErrorAction SilentlyContinue |
  Where-Object {
    $head = Get-Content -LiteralPath $_.FullName -TotalCount 3 -ErrorAction SilentlyContinue
    $head -match '<!DOCTYPE|<html'
  }
if ($badVue) {
  foreach ($f in $badVue) {
    Add-Fail "损坏的 Vue 页面: $($f.FullName.Replace($Root + '\', ''))"
  }
}

if ($failures.Count -eq 0) {
  Write-Host "dev-admin-stack: OK (health $($health.ms)ms, ready $($ready.ms)ms)" -ForegroundColor Green
  exit 0
}

Write-Host "dev-admin-stack: FAIL" -ForegroundColor Red
foreach ($f in $failures) { Write-Host "  - $f" -ForegroundColor Yellow }
exit 1
