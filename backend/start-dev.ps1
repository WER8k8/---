<#
.SYNOPSIS
启动优丁平台开发环境

.DESCRIPTION
使用开发环境配置启动后端服务，默认端口8080

.EXAMPLE
.\start-dev.ps1

.EXAMPLE
.\start-dev.ps1 -Port 8080
#>

param(
    [int]$Port = 8080
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "优丁平台 - 开发环境启动脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

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

Write-Host "`n🚀 启动开发环境服务..." -ForegroundColor Green
Write-Host "   环境: Development" -ForegroundColor Yellow
Write-Host "   端口: $Port" -ForegroundColor Yellow
Write-Host "   配置: config/dev/.env" -ForegroundColor Yellow
Write-Host ""

python run.py --env dev --port $Port