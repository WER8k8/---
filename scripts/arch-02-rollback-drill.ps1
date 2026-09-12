# ARCH-02 · 双 Admin 回滚演练脚本

param(
    [string]$RepoRoot = (Split-Path $PSScriptRoot -Parent)
)

$ErrorActionPreference = "Continue"
$admin = Join-Path $RepoRoot "frontend\admin"
$fail = 0

Write-Host "=== ARCH-02 Rollback Drill ===" -ForegroundColor Cyan

# 1. 送检路由静态检查
Push-Location $admin
npm run cert:nav 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Host "[FAIL] cert:nav"; $fail++ } else { Write-Host "[PASS] cert:nav" }

# 2. BFF 冒烟（现网仍可用 legacy auth）
Pop-Location
$env:PYTHONPATH = Join-Path $RepoRoot "backend"
python (Join-Path $RepoRoot "scripts\qa-three-shell-e2e.py")
if ($LASTEXITCODE -ne 0) { $fail++ }

# 3. 截图 manifest 存在性（送检可演示）
$manifest = Join-Path $RepoRoot "docs\cert-screenshots\manifest.json"
if (-not (Test-Path $manifest)) {
    Write-Host "[WARN] cert manifest missing — run cert:screenshots"
} else {
    Write-Host "[PASS] cert manifest exists"
}

Write-Host ""
Write-Host "Manual: Nginx 指回 frontend/admin dist · 记录 ecc-delivery-tracker" -ForegroundColor Yellow
if ($fail -eq 0) {
    Write-Host "ARCH-02 drill (automated): PASS" -ForegroundColor Green
    exit 0
}
Write-Host "ARCH-02 drill: $fail automated check(s) FAILED" -ForegroundColor Red
exit 1
