# install_all_mcp_onebyone.ps1
# 逐个调用 mcp-config-manager.ps1 添加 MCP Server，避免循环语法错误。

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$manager = Join-Path $scriptDir 'mcp-config-manager.ps1'

function Add-Server($name) {
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

Add-Server 'fetch'
Add-Server 'chrome-devtools'
Add-Server 'bing-cn'
Add-Server '12306-mcp'
Add-Server 'jina-ai-mcp-tools'
Add-Server 'deepwiki'
Add-Server 'zhipu-web-search'
Add-Server 'dingtalk'
Add-Server 'supabase'
Add-Server 'antvis'
Add-Server 'agentbay'
Add-Server 'mobvoi'
Add-Server 'gezhe'
Add-Server 'douyin-mcp-server'
Add-Server 'bazi-mcp'
Add-Server 'allvoicelab'
Add-Server 'amap-maps'
Add-Server 'baidu-maps'
Add-Server 'alipay-subscription'
Add-Server 'unionpay-mcp'
Add-Server 'memos'
Add-Server 'weread'
Add-Server 'openmemory'

Write-Host "全部 MCP Server 添加完成。请根据实际需求在 mcp.json 中补全 env 配置后重新启动 Lingma。" -ForegroundColor Yellow