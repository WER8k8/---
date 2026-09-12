# Talking-Stick 安全扫描脚本
# 用法: powershell -ExecutionPolicy Bypass -File scripts/run-talking-stick-scan.ps1 -TargetPath <目标路径>

param(
    [Parameter(Mandatory=$true)]
    [string]$TargetPath,
    
    [string]$ApiUrl = "http://127.0.0.1:8001",
    
    [switch]$WaitForResult,
    
    [int]$TimeoutSeconds = 300
)

$ErrorActionPreference = "Stop"

# 检查目标路径是否存在
if (-not (Test-Path $TargetPath)) {
    Write-Error "目标路径不存在: $TargetPath"
    exit 1
}

# 获取API URL
$ApiBase = "$ApiUrl/api/v1/talking-stick"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Talking-Stick 安全扫描" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "目标路径: $TargetPath" -ForegroundColor Yellow
Write-Host "API地址: $ApiBase" -ForegroundColor Yellow
Write-Host ""

# 提交扫描任务
Write-Host "提交扫描任务..." -ForegroundColor Green

$scanRequest = @{
    target_path = $TargetPath
    options = @{
        scan_type = "full"
        include_dependencies = $true
    }
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$ApiBase/scan" -Method Post -Body $scanRequest -ContentType "application/json"
    $taskId = $response.task_id
    
    Write-Host "任务已提交，任务ID: $taskId" -ForegroundColor Green
    Write-Host ""
    
    if (-not $WaitForResult) {
        Write-Host "任务已提交，可通过以下命令查询状态:" -ForegroundColor Yellow
        Write-Host "  GET $ApiBase/scan/$taskId/status" -ForegroundColor White
        Write-Host ""
        Write-Host "获取结果:" -ForegroundColor Yellow
        Write-Host "  GET $ApiBase/scan/$taskId/result" -ForegroundColor White
        exit 0
    }
    
    # 等待结果
    Write-Host "等待扫描完成..." -ForegroundColor Yellow
    
    $startTime = Get-Date
    $timeout = New-TimeSpan -Seconds $TimeoutSeconds
    
    while ($true) {
        $status = Invoke-RestMethod -Uri "$ApiBase/scan/$taskId/status" -Method Get
        
        $elapsed = (Get-Date) - $startTime
        if ($elapsed -gt $timeout) {
            Write-Error "扫描超时（超过 $TimeoutSeconds 秒）"
            exit 1
        }
        
        switch ($status.status) {
            "completed" {
                Write-Host "扫描完成！" -ForegroundColor Green
                Write-Host ""
                
                # 获取结果
                $result = Invoke-RestMethod -Uri "$ApiBase/scan/$taskId/result" -Method Get
                
                # 显示摘要
                Write-Host "========================================" -ForegroundColor Cyan
                Write-Host "扫描结果摘要" -ForegroundColor Cyan
                Write-Host "========================================" -ForegroundColor Cyan
                
                $summary = $result.summary
                Write-Host "总文件数: $($summary.total_files)" -ForegroundColor White
                Write-Host "风险文件: $($summary.risk_files)" -ForegroundColor Yellow
                Write-Host "发现漏洞: $($summary.total_vulnerabilities)" -ForegroundColor Red
                Write-Host ""
                
                Write-Host "漏洞严重程度分布:" -ForegroundColor Yellow
                Write-Host "  严重: $($summary.critical_count)" -ForegroundColor Red
                Write-Host "  高危: $($summary.high_count)" -ForegroundColor DarkRed
                Write-Host "  中危: $($summary.medium_count)" -ForegroundColor Yellow
                Write-Host "  低危: $($summary.low_count)" -ForegroundColor Green
                Write-Host ""
                
                # 显示报告路径
                if ($result.report_paths) {
                    Write-Host "报告已生成:" -ForegroundColor Green
                    foreach ($format in $result.report_paths.Keys) {
                        Write-Host "  $format`: $($result.report_paths[$format])" -ForegroundColor White
                    }
                }
                
                exit 0
            }
            "failed" {
                Write-Error "扫描失败: $($status.error)"
                exit 1
            }
            "cancelled" {
                Write-Host "扫描已取消" -ForegroundColor Yellow
                exit 0
            }
            default {
                Write-Host "." -NoNewline
                Start-Sleep -Seconds 2
            }
        }
    }
    
} catch {
    Write-Error "API请求失败: $_"
    exit 1
}