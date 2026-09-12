# install_all_mcp.ps1
# 脚本使用 mcp-config-manager.ps1 为列表中的 MCP Server 添加配置。

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$manager = Join-Path $scriptDir 'mcp-config-manager.ps1'

$servers = @('fetch','chrome-devtools','bing-cn','12306-mcp','jina-ai-mcp-tools','deepwiki','zhipu-web-search','dingtalk','supabase','antvis','agentbay','mobvoi','gezhe','douyin-mcp-server','bazi-mcp','allvoicelab','amap-maps','baidu-maps','alipay-subscription','unionpay-mcp','memos','weread','openmemory')

foreach ($name in $servers) {
    Write-Host "[+] 添加 MCP Server: $name" -ForegroundColor Cyan
    $config = @{
        command = 'npx'
        args    = @('-y',"@modelcontextprotocol/server-$name")
        env     = @{}
    } | ConvertTo-Json -Compress
    & $manager -Action Add -ServerName $name -Config $config
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   -> 添加 $name 失败，请检查日志" -ForegroundColor Red
    } else {
        Write-Host "   -> 添加 $name 成功" -ForegroundColor Green
    }
    Write-Host ""
}

Write-Host "全部 MCP Server 添加完成。请根据实际需求在 mcp.json 中补全 env 配置后重新启动 Lingma。" -ForegroundColor Yellow