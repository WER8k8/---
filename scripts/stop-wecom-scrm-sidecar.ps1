# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
<#
.SYNOPSIS
    一键停止国内轨企微 SCRM 侧车套件（Spring Boot 8085 + Vite 2024 前端 + 可选 MySQL 容器）
#>
param (
    [switch]$StopDatabase = $false
)

Write-Host "正在停止企微 SCRM 侧车进程..." -ForegroundColor Yellow

# 停止 Java 进程 (iyque-code)
$javaProc = Get-CimInstance Win32_Process -Filter "CommandLine LIKE '%iyque-code%'"
if ($javaProc) {
    $javaProc | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    Write-Host "  [OK] Java 后端 (:8085) 已停止" -ForegroundColor Green
} else {
    Write-Host "  [-] Java 后端未在运行" -ForegroundColor Gray
}

# 停止 Vite 前端 (端口 2024)
$port2024 = Get-NetTCPConnection -LocalPort 2024 -ErrorAction SilentlyContinue
if ($port2024) {
    $port2024 | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object {
        Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
    }
    Write-Host "  [OK] 前端 Vite (:2024) 已停止" -ForegroundColor Green
} else {
    Write-Host "  [-] 前端 Vite 未在运行" -ForegroundColor Gray
}

# 可选停止 MySQL 容器
if ($StopDatabase) {
    docker stop uding-scrm-mysql | Out-Null
    Write-Host "  [OK] MySQL 8.0 容器已停止" -ForegroundColor Green
} else {
    Write-Host "  [i] MySQL 8.0 容器保持运行（传入 -StopDatabase 可停止）" -ForegroundColor Cyan
}

Write-Host "企微 SCRM 侧车停止完毕。" -ForegroundColor Cyan
