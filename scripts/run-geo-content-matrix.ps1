#Requires -Version 5.1
<#
.SYNOPSIS
  本地 GEO 内容矩阵：产品 API（DeerFlow）或可选 agency-orchestrator 对照。

.EXAMPLE
  powershell -File scripts/run-geo-content-matrix.ps1 -Message "岩棉 GEO 内容矩阵" -Platforms "LinkedIn,百家号,抖音"
  powershell -File scripts/run-geo-content-matrix.ps1 -UseAgencyOrchestrator -Domain "岩棉出口" -Keywords "rock wool,A1"
#>
[CmdletBinding()]
param(
    [string]$Message = "岩棉保温棉 GEO 内容矩阵 关键词 rock wool, fire rating, B2B export",
    [string]$Platforms = "LinkedIn,百家号,抖音,小红书",
    [string]$Domain = "",
    [string]$Keywords = "",
    [switch]$UseAgencyOrchestrator,
    [switch]$Sync,
    [string]$ApiBase = "http://127.0.0.1:8001",
    [string]$Token = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$platformList = @($Platforms -split '[,，、|]' | ForEach-Object { $_.Trim() } | Where-Object { $_ })

if ($UseAgencyOrchestrator) {
    if (-not (Get-Command ao -ErrorAction SilentlyContinue)) {
        Write-Host 'Installing agency-orchestrator globally...' -ForegroundColor Yellow
        npm install -g agency-orchestrator
    }
    $domainArg = if ($Domain) { $Domain } else { "建材 B2B 出口" }
    $kwArg = if ($Keywords) { $Keywords } else { "rock wool insulation, fire rating" }
    Write-Host "Running ao seo-content-matrix (local planning layer)..." -ForegroundColor Cyan
    ao run workflows/marketing/seo-content-matrix.yaml `
        --input "domain=$domainArg" `
        --input "target_keywords=$kwArg" `
        --input "article_count=1" `
        --watch
    Write-Host ''
    Write-Host 'ao 产出在 ao-output/；请人审后导入统一发布母版，或通过副驾触发 geo_content_matrix 写入 CMS。' -ForegroundColor Green
    exit 0
}

Write-Host 'Product path: UBrain geo_content_matrix (DeerFlow → content_masters)' -ForegroundColor Cyan
Write-Host "  Message:   $Message"
Write-Host "  Platforms: $($platformList -join ', ')"
Write-Host ''

if (-not $Token) {
    Write-Host '未提供 -Token：请在租户副驾对话中说：' -ForegroundColor Yellow
    Write-Host "  $Message"
    Write-Host '或在 Admin 登录后带 Bearer Token 调用 ubrain/chat。'
    Write-Host ''
    Write-Host '本地无 Token 时可直接跑 pytest：' -ForegroundColor Gray
    Write-Host '  cd backend; python -m pytest tests/unit/test_geo_content_matrix.py -q'
    exit 0
}

$body = @{
    message = $Message
    context = @{
        async     = -not $Sync
        platforms = $platformList
    }
} | ConvertTo-Json -Depth 5 -Compress

if ($Domain) { $bodyObj = $body | ConvertFrom-Json; $bodyObj.context.domain = $Domain; $body = $bodyObj | ConvertTo-Json -Depth 5 -Compress }
if ($Keywords) { $bodyObj = $body | ConvertFrom-Json; $bodyObj.context.target_keywords = $Keywords; $body = $bodyObj | ConvertTo-Json -Depth 5 -Compress }

$headers = @{
    Authorization = "Bearer $Token"
    'Content-Type' = 'application/json'
}

try {
    $resp = Invoke-RestMethod -Uri "$ApiBase/api/v1/ubrain/chat" -Method Post -Headers $headers -Body $body
    $resp | ConvertTo-Json -Depth 8
} catch {
    Write-Error $_
    exit 1
}
