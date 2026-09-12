<#
.SYNOPSIS
启动优丁平台生产环境

.DESCRIPTION
使用生产环境配置启动后端服务，默认端口8000

.NOTES
生产环境需要提前配置环境变量或config/prod/.env文件
敏感配置应通过环境变量注入，不应硬编码在配置文件中

.EXAMPLE
.\start-prod.ps1

.EXAMPLE
.\start-prod.ps1 -Port 80
#>

param(
    [int]$Port = 8000
)

Write-Host "========================================" -ForegroundColor Red
Write-Host "优丁平台 - 生产环境启动脚本" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Red

Write-Warning "⚠️  注意：这是生产环境启动脚本"
Write-Warning "⚠️  请确保已正确配置所有敏感信息"
Write-Warning "⚠️  生产环境不应在开发机器上运行"

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

Write-Host "`n🚀 启动生产环境服务..." -ForegroundColor Green
Write-Host "   环境: Production" -ForegroundColor Red
Write-Host "   端口: $Port" -ForegroundColor Yellow
Write-Host "   配置: config/prod/.env" -ForegroundColor Yellow
Write-Host ""

python run.py --env prod --port $Port