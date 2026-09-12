# install_all_mcp_final.ps1
# 全自动安装所有MCP Server

# 设置路径
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$manager = Join-Path $scriptDir 'mcp-config-manager.ps1'

# MCP服务器列表
$servers = @(
    'fetch',
    'chrome-devtools',
    'bing-cn',
    '12306-mcp',
    'jina-ai-mcp-tools',
    'deepwiki',
    'zhipu-web-search',
    'dingtalk',
    'supabase',
    'antvis',
    'agentbay',
    'mobvoi',
    'gezhe',
    'douyin-mcp-server',
    'bazi-mcp',
    'allvoicelab',
    'amap-maps',
    'baidu-maps',
    'alipay-subscription',
    'unionpay-mcp',
    'memos',
    'weread',
    'openmemory'
)

# 主安装函数
function Install-McpServer {
    param($name)
    
    try {
        Write-Host "[+] 正在安装 MCP Server: $name" -ForegroundColor Cyan
        
        $config = @{
            command = 'npx'
            args    = @('-y', "@modelcontextprotocol/server-$name")
            env     = @{}
        } | ConvertTo-Json -Compress
        
        & $manager -Action Add -ServerName $name -Config $config -ErrorAction Stop
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   -> 安装成功" -ForegroundColor Green
            return $true
        } else {
            Write-Host "   -> 安装失败 (退出码: $LASTEXITCODE)" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "   -> 安装错误: $_" -ForegroundColor Red
        return $false
    }
}

# 执行安装
$successCount = 0
foreach ($server in $servers) {
    if (Install-McpServer $server) {
        $successCount++
    }
    Start-Sleep -Milliseconds 200  # 避免请求过快
}

# 结果汇总
Write-Host "\n[完成] 成功安装 $successCount/$($servers.Count) 个MCP Server" -ForegroundColor Yellow
Write-Host "请手动配置mcp.json中的环境变量后重启Lingma" -ForegroundColor Yellow