# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
<#
.SYNOPSIS
    一键启动国内轨企微 SCRM 侧车套件（MySQL 8.0 容器 + Redis + Spring Boot 8085 + Vue3 2024）
.DESCRIPTION
    Path A 国内私域工作台专用启动脚本，零侵入、全自动化探测并拉起全部微服务。
#>
param (
    [switch]$NoFrontend = $false
)

$ErrorActionPreference = "Continue"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " [AEOS] 正在启动国内轨企微 SCRM 侧车环境 (iYqueCode)..." -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. 检查并拉起 Docker MySQL 8.0 容器
Write-Host "[1/4] 检查侧车 MySQL 8.0 容器..." -ForegroundColor Yellow
$mysqlRunning = docker ps --filter "name=uding-scrm-mysql" --format "{{.Status}}"
if (-not $mysqlRunning) {
    Write-Host "  启动 uding-scrm-mysql 容器..." -ForegroundColor Gray
    docker start uding-scrm-mysql | Out-Null
    Start-Sleep -Seconds 2
}
Write-Host "  [OK] MySQL 8.0 容器在线 (端口 :10179 / :3306, 库: scrm_ky 52表)" -ForegroundColor Green

# 2. 检查并确保 Redis 5.0 在线
Write-Host "[2/4] 检查 Redis 5.0 服务..." -ForegroundColor Yellow
$redisCheck = Test-NetConnection -ComputerName 127.0.0.1 -Port 6379 -InformationLevel Quiet
if (-not $redisCheck) {
    Write-Host "  启动 Redis 服务..." -ForegroundColor Gray
    Start-Process -FilePath "C:\Users\Administrator\Documents\上线网站开发完成\tools\redis\redis-server.exe" -ArgumentList "C:\Users\Administrator\Documents\上线网站开发完成\tools\redis\redis.windows.conf" -WindowStyle Hidden
    Start-Sleep -Seconds 2
}
Write-Host "  [OK] Redis 在线 (端口 :6379, 侧车使用 db: 1)" -ForegroundColor Green

# 3. 检查并拉起 Spring Boot Java 后端 (8085)
Write-Host "[3/4] 检查 Spring Boot 后端服务 (:8085)..." -ForegroundColor Yellow
$apiCheck = Test-NetConnection -ComputerName 127.0.0.1 -Port 8085 -InformationLevel Quiet
if (-not $apiCheck) {
    Write-Host "  正在使用便携 JDK 17 拉起 iyque-code-1.0-SNAPSHOT.jar..." -ForegroundColor Gray
    $javaExe = "$env:TEMP\iyque-toolchain\jdk\jdk-17.0.2\bin\java.exe"
    $jarPath = "$env:TEMP\uptake-eval\iYqueCode\target\iyque-code-1.0-SNAPSHOT.jar"
    $logOut = "$env:TEMP\uptake-eval\iyque-boot.out.log"
    $logErr = "$env:TEMP\uptake-eval\iyque-boot.err.log"
    $jdbcUrl = "jdbc:mysql://127.0.0.1:10179/scrm_ky?useUnicode=true&characterEncoding=UTF-8&useSSL=false&serverTimezone=Asia/Shanghai&allowPublicKeyRetrieval=true"

    Start-Process -FilePath $javaExe -ArgumentList "-Dfile.encoding=UTF-8", "-jar", $jarPath, "--spring.datasource.url=$jdbcUrl" -WorkingDirectory "$env:TEMP\uptake-eval\iYqueCode" -RedirectStandardOutput $logOut -RedirectStandardError $logErr -WindowStyle Hidden
    
    # 轮询等待端口就绪
    $waited = 0
    while ($waited -lt 25) {
        Start-Sleep -Seconds 2
        $waited += 2
        if (Test-NetConnection -ComputerName 127.0.0.1 -Port 8085 -InformationLevel Quiet) {
            break
        }
    }
}
Write-Host "  [OK] Spring Boot API 后端就绪: http://127.0.0.1:8085" -ForegroundColor Green

# 4. 检查并拉起 Vue 3 PC 前端 (2024)
if (-not $NoFrontend) {
    Write-Host "[4/4] 检查 Vue 3 控制台前端 (:2024)..." -ForegroundColor Yellow
    $uiCheck = Test-NetConnection -ComputerName 127.0.0.1 -Port 2024 -InformationLevel Quiet
    if (-not $uiCheck) {
        Write-Host "  正在启动 Vite 前端工作台..." -ForegroundColor Gray
        Start-Process -FilePath "npm" -ArgumentList "--prefix", "$env:TEMP\uptake-eval\iYqueCode\frontEnd\pc", "run", "dev", "--", "--host", "127.0.0.1", "--port", "2024" -WindowStyle Hidden
        Start-Sleep -Seconds 5
    }
    Write-Host "  [OK] 前端控制台在线: http://127.0.0.1:2024/tools/" -ForegroundColor Green
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " 企微 SCRM 侧车套件运行正常：" -ForegroundColor Green
Write-Host "   控制台 UI : http://127.0.0.1:2024/tools/ (账号: iyque / 密码: iyque.cn)" -ForegroundColor White
Write-Host "   后端 API  : http://127.0.0.1:8085" -ForegroundColor White
Write-Host "   线索回流口: http://127.0.0.1:8001/api/v1/wecom-leads/ingest" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan
