# single_add_fetch.ps1
# 为 MCP Server "fetch" 添加占位配置

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$manager = Join-Path $scriptDir 'mcp-config-manager.ps1'

$serverName = 'fetch'
$config = @{
    command = 'npx'
    args    = @('-y',"@modelcontextprotocol/server-$serverName")
    env     = @{}
} | ConvertTo-Json -Compress

Write-Host "[+] 添加 MCP Server: $serverName" -ForegroundColor Cyan
& $manager -Action Add -ServerName $serverName -Config $config
if ($LASTEXITCODE -ne 0) {
    Write-Host "   -> 添加 $serverName 失败，请检查日志" -ForegroundColor Red
} else {
    Write-Host "   -> 添加 $serverName 成功" -ForegroundColor Green
}

Write-Host "单个 MCP Server 添加完成。请根据实际需求在 mcp.json 中补全 env 配置后重新启动 Lingma。" -ForegroundColor Yellow