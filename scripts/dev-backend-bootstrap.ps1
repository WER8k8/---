# Backend bootstrap for start-dev-admin.ps1 (UTF-8, invoked via -File)
param(
  [Parameter(Mandatory = $true)][string]$BackendDir,
  [Parameter(Mandatory = $true)][string]$DevEnvFile,
  [Parameter(Mandatory = $true)][string]$BindHost,
  [Parameter(Mandatory = $true)][int]$ApiPort,
  [Parameter(Mandatory = $true)][int]$AdminPort,
  [string]$CorsOrigins = '',
  [string]$PublicApiBase = '',
  [string]$FrontendUrl = ''
)

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $BackendDir
$env:PYTHONPATH = (Get-Location).Path
$env:TZ = 'Asia/Shanghai'

if (Test-Path -LiteralPath $DevEnvFile) {
  Get-Content -LiteralPath $DevEnvFile -Encoding UTF8 | ForEach-Object {
    $line = $_.Trim()
    if ($line -and $line[0] -ne '#' -and $line -match '=') {
      $parts = $line -split '=', 2
      $k = $parts[0].Trim()
      $v = $parts[1].Trim()
      if ($k) { Set-Item -Path "Env:$k" -Value $v }
    }
  }
}

$env:ENVIRONMENT = 'development'

$wingetLinks = Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Links'
if (Test-Path $wingetLinks) { $env:Path = "$wingetLinks;$env:Path" }

try {
  $ff = & where.exe ffmpeg 2>$null | Select-Object -First 1
  if ($ff) {
    $ff = $ff.Trim()
    $item = Get-Item -LiteralPath $ff -ErrorAction SilentlyContinue
    if ($item -and $item.LinkType -eq 'SymbolicLink' -and $item.Target) {
      $env:FFMPEG_PATH = ($item.Target | Select-Object -First 1)
    } else {
      $env:FFMPEG_PATH = $ff
    }
  }
} catch {}

if (-not $env:HF_ENDPOINT) { $env:HF_ENDPOINT = 'https://hf-mirror.com' }

$hasKey = $false
foreach ($k in @('AI_NVIDIA_API_KEY', 'AI_DEEPSEEK_API_KEY', 'AI_OPENAI_API_KEY', 'AI_ANTHROPIC_API_KEY', 'AI_GEMINI_API_KEY')) {
  $v = [Environment]::GetEnvironmentVariable($k)
  if ($v -and $v -notmatch 'your_|here|change-me') { $hasKey = $true; break }
}
if ($hasKey) { $env:MVP_LAUNCH = '0' } else { $env:MVP_LAUNCH = '1' }
if (-not $env:JWT_SECRET_KEY -or $env:JWT_SECRET_KEY -eq '') { $env:JWT_SECRET_KEY = 'dev-' + ('x' * 28) }
if (-not $env:SECRET_KEY -or $env:SECRET_KEY -eq '') { $env:SECRET_KEY = $env:JWT_SECRET_KEY }
if (-not $env:FRONTEND_URL) { $env:FRONTEND_URL = "http://127.0.0.1:$AdminPort" }
if (-not $env:DB_TYPE) {
  $env:DB_TYPE = 'sqlite'
}

if (Test-Path -LiteralPath $DevEnvFile) {
  Get-Content -LiteralPath $DevEnvFile -Encoding UTF8 | ForEach-Object {
    $line = $_.Trim()
    if ($line -and $line[0] -ne '#' -and $line -match '^DB_TYPE\s*=') {
      $parts = $line -split '=', 2
      if ($parts.Count -ge 2) { $env:DB_TYPE = $parts[1].Trim() }
    }
  }
}

if (-not $env:DOUYIN_COMMENT_INBOX_DIR) {
  $inbox = Join-Path (Get-Location) 'fixtures\dev\douyin_comment_inbox'
  if (Test-Path $inbox) { $env:DOUYIN_COMMENT_INBOX_DIR = $inbox }
}

if ($CorsOrigins) { $env:CORS_ORIGINS = $CorsOrigins }
if ($PublicApiBase) { $env:PUBLIC_API_BASE = $PublicApiBase }
if ($FrontendUrl) { $env:FRONTEND_URL = $FrontendUrl }

.\.venv\Scripts\python.exe -m alembic upgrade heads
if ($LASTEXITCODE -ne 0) { throw 'alembic upgrade failed' }

$env:PYTHONPATH = (Get-Location).Path
if ($env:DB_TYPE -eq 'sqlite') {
  .\.venv\Scripts\python.exe scripts/ensure_dev_sqlite.py
  if ($LASTEXITCODE -ne 0) { throw 'ensure_dev_sqlite failed' }
}
elseif ($env:DB_TYPE -eq 'postgresql') {
  # ENV-LOCK-01：PG 为唯一真源。ensure_dev_sqlite.py 会把 DATABASE_URL 解析成
  # 本地 SQLite 文件并往里补账号，在 PG 环境下执行等于偷偷造第二套数据源，
  # 因此这里显式跳过；PG 侧的开发数据由 alembic + seed_dev_tenant_demo.py 负责。
  Write-Host '[bootstrap] DB_TYPE=postgresql -> skip ensure_dev_sqlite.py (ENV-LOCK-01)'
}
else { throw ("Unsupported DB_TYPE='" + $env:DB_TYPE + "'") }

.\.venv\Scripts\python.exe ..\scripts\seed_dev_tenant_demo.py
if ($LASTEXITCODE -ne 0) { throw 'seed_dev_tenant_demo failed' }

if ($env:DB_TYPE -eq 'sqlite') {
  .\.venv\Scripts\python.exe scripts/repair_dev_inquiry_columns.py
}

.\.venv\Scripts\python.exe -m uvicorn app.main:app --host $BindHost --port $ApiPort
