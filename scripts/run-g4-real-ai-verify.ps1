# G4 真实 AI Key 验证（演示阶段可跳过 live 外网调用：$env:G4_SKIP_LIVE='1'）
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$DevEnv = Join-Path $Root "backend\config\dev\.env"
if (Test-Path $DevEnv) {
  Get-Content $DevEnv | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
      $k = $matches[1].Trim(); $v = $matches[2].Trim()
      if ($k) { Set-Item -Path Env:$k -Value $v }
    }
  }
}

# 有 Key 时默认走真实 AI（不再 Mock）
$env:MVP_LAUNCH = "0"
if (-not $env:JWT_SECRET_KEY) { $env:JWT_SECRET_KEY = "dev-" + ("x" * 28) }
if (-not $env:SECRET_KEY) { $env:SECRET_KEY = $env:JWT_SECRET_KEY }

Write-Host "=== G4 AI Key Verify (demo skipped, real keys) ===" -ForegroundColor Cyan
python "$Root\scripts\run_g4_live_verify.py"
$code = $LASTEXITCODE

python "$Root\scripts\check_gates_g1_g7.py" 2>&1 | Select-Object -Last 6
exit $code
