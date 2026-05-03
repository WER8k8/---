# ============================================
# 优丁建材 - Windows一键部署脚本
# 使用方法：在PowerShell中运行 .\deploy.ps1
# ============================================

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "优丁建材官网 - 自动化部署脚本 (Windows)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 检查必要工具
function Check-Dependencies {
    Write-Host "`n🔍 检查依赖工具..." -ForegroundColor Yellow
    
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Host "❌ Docker未安装，请先安装Docker Desktop" -ForegroundColor Red
        Write-Host "📌 下载地址：https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host "✅ Docker已安装: $(docker --version)" -ForegroundColor Green
    Write-Host "✅ 依赖检查通过" -ForegroundColor Green
}

# 配置环境
function Setup-Environment {
    Write-Host "`n📝 配置环境..." -ForegroundColor Yellow
    
    if (-not (Test-Path ".env.prod")) {
        Write-Host "⚠️ 未找到.env.prod文件" -ForegroundColor Yellow
        Write-Host "📋 正在从模板创建.env.prod..." -ForegroundColor Yellow
        Copy-Item ".env.prod.example" ".env.prod"
        
        Write-Host "`n❌ 请先编辑.env.prod文件，填入真实配置后再运行部署" -ForegroundColor Red
        Write-Host "📌 必填配置项：" -ForegroundColor Yellow
        Write-Host "   - DOMAIN (域名)" -ForegroundColor White
        Write-Host "   - DB_PASSWORD (数据库密码)" -ForegroundColor White
        Write-Host "   - JWT_SECRET_KEY (JWT密钥)" -ForegroundColor White
        Write-Host "   - AI_NVIDIA_API_KEY (英伟达API密钥)" -ForegroundColor White
        Write-Host "   - SMTP_SERVER, SMTP_USERNAME, SMTP_PASSWORD (邮件服务)" -ForegroundColor White
        Write-Host "`n💡 编辑命令：notepad .env.prod" -ForegroundColor Yellow
        exit 1
    }
    
    # 加载环境变量
    Get-Content ".env.prod" | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
    
    $envDomain = [Environment]::GetEnvironmentVariable("DOMAIN", "Process")
    $envDbPassword = [Environment]::GetEnvironmentVariable("DB_PASSWORD", "Process")
    $envJwtKey = [Environment]::GetEnvironmentVariable("JWT_SECRET_KEY", "Process")
    
    # 验证必填配置
    if ([string]::IsNullOrEmpty($envDomain) -or $envDomain -eq "www.youdingjiancai.com") {
        Write-Host "❌ 请修改.env.prod中的DOMAIN为实际域名" -ForegroundColor Red
        exit 1
    }
    
    if ([string]::IsNullOrEmpty($envDbPassword) -or $envDbPassword -eq "your-secure-db-password-change-me") {
        Write-Host "❌ 请修改.env.prod中的DB_PASSWORD为强密码" -ForegroundColor Red
        exit 1
    }
    
    if ([string]::IsNullOrEmpty($envJwtKey) -or $envJwtKey -eq "your-jwt-secret-key-here-change-me") {
        Write-Host "❌ 请修改.env.prod中的JWT_SECRET_KEY" -ForegroundColor Red
        Write-Host "💡 生成命令：python -c 'import secrets; print(secrets.token_hex(32))'" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host "✅ 环境配置检查通过" -ForegroundColor Green
}

# 构建镜像
function Build-Images {
    Write-Host "`n🔨 构建Docker镜像..." -ForegroundColor Yellow
    
    docker compose -f docker-compose.prod.yml build --no-cache
    
    Write-Host "✅ 镜像构建完成" -ForegroundColor Green
}

# 启动服务
function Start-Services {
    Write-Host "`n🚀 启动服务..." -ForegroundColor Yellow
    
    docker compose -f docker-compose.prod.yml up -d
    
    Write-Host "✅ 服务已启动" -ForegroundColor Green
}

# 等待服务就绪
function Wait-ForServices {
    Write-Host "`n⏳ 等待服务就绪..." -ForegroundColor Yellow
    
    # 等待PostgreSQL
    Write-Host "  等待数据库启动..." -ForegroundColor White
    $maxAttempts = 30
    $attempt = 0
    while ($attempt -lt $maxAttempts) {
        $attempt++
        $result = docker compose -f docker-compose.prod.yml exec -T postgres pg_isready -U $env:DB_USER 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ 数据库已就绪" -ForegroundColor Green
            break
        }
        if ($attempt -eq $maxAttempts) {
            Write-Host "  ❌ 数据库启动超时" -ForegroundColor Red
            exit 1
        }
        Start-Sleep -Seconds 2
    }
    
    # 等待后端API
    Write-Host "  等待后端API启动..." -ForegroundColor White
    $attempt = 0
    while ($attempt -lt $maxAttempts) {
        $attempt++
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" -TimeoutSec 2 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-Host "  ✅ 后端API已就绪" -ForegroundColor Green
                break
            }
        } catch {
            # 忽略错误，继续重试
        }
        if ($attempt -eq $maxAttempts) {
            Write-Host "  ⚠️ 后端API启动超时（可能正常，请手动检查）" -ForegroundColor Yellow
            break
        }
        Start-Sleep -Seconds 2
    }
}

# 运行数据库迁移
function Run-Migrations {
    Write-Host "`n🗄️ 运行数据库迁移..." -ForegroundColor Yellow
    
    docker compose -f docker-compose.prod.yml exec -T backend alembic upgrade head
    
    Write-Host "✅ 数据库迁移完成" -ForegroundColor Green
}

# 检查服务状态
function Check-Status {
    Write-Host "`n📊 服务状态：" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    
    docker compose -f docker-compose.prod.yml ps
    
    $envDomain = [Environment]::GetEnvironmentVariable("DOMAIN", "Process")
    
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "🌐 访问地址：" -ForegroundColor Green
    Write-Host "   前端：https://$envDomain" -ForegroundColor White
    Write-Host "   后端API：https://$envDomain/api/v1" -ForegroundColor White
    Write-Host "   API文档：https://$envDomain/api/docs" -ForegroundColor White
    Write-Host "   管理后台：https://$envDomain/admin" -ForegroundColor White
    Write-Host "`n📋 常用命令：" -ForegroundColor Yellow
    Write-Host "   查看日志：docker compose -f docker-compose.prod.yml logs -f" -ForegroundColor White
    Write-Host "   停止服务：docker compose -f docker-compose.prod.yml down" -ForegroundColor White
    Write-Host "   重启服务：docker compose -f docker-compose.prod.yml restart" -ForegroundColor White
    Write-Host "   更新部署：.\deploy.ps1" -ForegroundColor White
    Write-Host "========================================" -ForegroundColor Cyan
}

# 主流程
function Main {
    Check-Dependencies
    Setup-Environment
    Build-Images
    Start-Services
    Wait-ForServices
    Run-Migrations
    Check-Status
    
    Write-Host "`n🎉 部署完成！" -ForegroundColor Green
}

Main
