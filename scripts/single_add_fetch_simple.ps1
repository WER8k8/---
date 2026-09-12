# single_add_fetch_simple.ps1
# 简化版：仅调用 mcp-config-manager 为 fetch 添加占位配置

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

Write-Host "Single MCP Server addition completed (no error check). Please fill env in mcp.json as needed and restart Lingma." -ForegroundColor Yellow