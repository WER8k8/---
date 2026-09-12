# ============================================================
# 优丁建材 SaaS — 全量测试运行脚本
# 用法:
#   powershell -File scripts/run-tests.ps1                 # 全量测试
#   powershell -File scripts/run-tests.ps1 -Fast            # 快速冒烟（仅 unit）
#   powershell -File scripts/run-tests.ps1 -Coverage        # 全量 + 覆盖率报告
#   powershell -File scripts/run-tests.ps1 -Path tests/unit/test_waf_ua_p3_014.py
# ============================================================

param(
    [switch]$Fast,
    [switch]$Coverage,
    [string]$Path = ""
)

$backendDir = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $backendDir "backend"

Push-Location $backendDir
try {
    $pytestArgs = @("-v", "--tb=short", "--strict-markers", "--no-header", "--color=yes")

    if ($Fast) {
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host " 快速冒烟测试 (unit/ · 排除 integration)" -ForegroundColor Cyan
        Write-Host "========================================" -ForegroundColor Cyan
        $testPath = "tests/unit/"
        $pytestArgs += @("-m", "not integration")
    } elseif ($Path) {
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host " 指定测试: $Path" -ForegroundColor Cyan
        Write-Host "========================================" -ForegroundColor Cyan
        $testPath = $Path
    } else {
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host " 全量测试" -ForegroundColor Cyan
        Write-Host "========================================" -ForegroundColor Cyan
        $testPath = "tests/"
    }

    if ($Coverage -or (-not $Fast -and -not $Path)) {
        $pytestArgs += @("--cov=app", "--cov-report=term-missing", "--cov-report=html:logs/coverage")
    }

    $pytestArgs += $testPath

    Write-Host ""
    Write-Host "Running: pytest $($pytestArgs -join ' ')" -ForegroundColor Gray
    Write-Host ""

    & python -m pytest @pytestArgs

    $exitCode = $LASTEXITCODE
    Write-Host ""
    if ($exitCode -eq 0) {
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "  测试全部通过!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
    } else {
        Write-Host "========================================" -ForegroundColor Red
        Write-Host "  测试失败! (exit=$exitCode)" -ForegroundColor Red
        Write-Host "========================================" -ForegroundColor Red
    }

    if (-not $Fast) {
        $coverageDir = Join-Path $backendDir "logs" "coverage"
        if (Test-Path $coverageDir) {
            Write-Host ""
            Write-Host "Coverage report: $coverageDir/index.html" -ForegroundColor Cyan
        }
    }

    exit $exitCode
} finally {
    Pop-Location
}
