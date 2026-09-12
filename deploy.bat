@echo off
echo ========================================
echo   SEO 矩阵系统 - 一键部署脚本 (Windows)
echo ========================================
echo.

REM 检查 Docker 是否安装
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] Docker 未安装，请先安装 Docker Desktop
    pause
    exit /b 1
)
echo [成功] Docker 已安装

REM 进入后端目录
cd /d "%~dp0seo-backend"

echo.
echo [步骤 1/5] 检查环境配置...
if not exist ".env" (
    echo [提示] .env 文件不存在，从 .env.example 复制
    copy .env.example .env
) else (
    echo [成功] .env 文件已存在
)

echo.
echo [步骤 2/5] 构建并启动服务...
docker-compose up -d --build
if %errorlevel% neq 0 (
    echo [错误] 服务启动失败
    pause
    exit /b 1
)

echo.
echo [步骤 3/5] 等待服务就绪...
timeout /t 30 /nobreak >nul

echo.
echo [步骤 4/5] 初始化数据库...
docker exec seo-backend node src/scripts/initData.js
docker exec seo-backend node src/scripts/createAdmin.js

echo.
echo [步骤 5/5] 显示服务状态...
docker-compose ps

echo.
echo ========================================
echo   部署完成！
echo ========================================
echo.
echo   访问地址：
echo   - 前端管理后台: http://localhost:5173
echo   - 后端 API:        http://localhost:3000
echo.
echo   默认管理员账号：
echo   - 用户名: admin
echo   - 密码: Trae@2024
echo.
echo   常用命令：
echo   - 查看日志: docker-compose logs -f
echo   - 停止服务: docker-compose down
echo   - 启动服务: docker-compose up -d
echo.
pause
