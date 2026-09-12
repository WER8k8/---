<#
.SYNOPSIS
启动优丁平台测试环境

.DESCRIPTION
使用测试环境配置启动后端服务，默认端口8081

.EXAMPLE
.\start-test.ps1

.EXAMPLE
.\start-test.ps1 -Port 8081
#>

param(
    [int]$Port = 8081
)

Write-Host "========================================" -ForegroundColor Yellow
Write-Host "优丁平台 - 测试环境启动脚本" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "❌ 未找到Python，请确保Python已安装并添加到PATH"
    exit 1
}

$venvPath = ".venv"
if (-not (Test-Path $venvPath)) {
    Write-Warning "⚠️ 未找到虚拟环境，将使用系统Python"
} else {
    Write-Host "✅ 使用虚拟环境: $venvPath" -ForegroundColor Green
}

Write-Host "`n🚀 启动测试环境服务..." -ForegroundColor Green
Write-Host "   环境: Testing" -ForegroundColor Yellow
Write-Host "   端口: $Port" -ForegroundColor Yellow
Write-Host "   配置: config/test/.env" -ForegroundColor Yellow
Write-Host ""

python run.py --env test --port $Port