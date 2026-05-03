Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Supabase MCP 服务器配置工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check installation
Write-Host "[1/3] 检查安装状态..." -ForegroundColor Yellow
$supabasePath = where.exe mcp-server-supabase 2>$null
if ($supabasePath) {
    Write-Host "OK - mcp-server-supabase 已安装" -ForegroundColor Green
} else {
    Write-Host "ERROR - 未安装，正在安装..." -ForegroundColor Red
    npm install -g @modelcontextprotocol/server-supabase
}

Write-Host ""

# Step 2: Get token
Write-Host "[2/3] 配置 Access Token" -ForegroundColor Yellow
Write-Host "请访问: https://app.supabase.com/account/tokens" -ForegroundColor Cyan
Write-Host ""
$token = Read-Host "请输入 Supabase Access Token"

if ([string]::IsNullOrWhiteSpace($token)) {
    Write-Host "ERROR - Token 不能为空" -ForegroundColor Red
    exit 1
}

# Set environment variable
[System.Environment]::SetEnvironmentVariable('SUPABASE_ACCESS_TOKEN', $token, 'User')
Write-Host "OK - 环境变量已设置" -ForegroundColor Green

Write-Host ""

# Step 3: Update config file
Write-Host "[3/3] 更新配置文件" -ForegroundColor Yellow
$mcpConfigPath = "$env:APPDATA\Lingma\SharedClientCache\mcp.json"

if (Test-Path $mcpConfigPath) {
    Write-Host "配置文件位置: $mcpConfigPath" -ForegroundColor Gray
    
    try {
        $content = Get-Content $mcpConfigPath -Raw -Encoding UTF8
        $config = $content | ConvertFrom-Json
        
        if ($config.mcpServers.supabase) {
            Write-Host "OK - Supabase 配置已存在" -ForegroundColor Green
            
            # Add env if not exists
            if (-not ($config.mcpServers.supabase.PSObject.Properties.Name -contains 'env')) {
                $config.mcpServers.supabase | Add-Member -MemberType NoteProperty -Name 'env' -Value @{}
            }
            
            $config.mcpServers.supabase.env.SUPABASE_ACCESS_TOKEN = $token
            
            # Save back
            $config | ConvertTo-Json -Depth 10 | Set-Content $mcpConfigPath -Encoding UTF8
            Write-Host "OK - 配置文件已更新" -ForegroundColor Green
        } else {
            Write-Host "WARNING - 需要手动添加配置到 mcp.json" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "ERROR - 配置文件处理失败: $_" -ForegroundColor Red
    }
} else {
    Write-Host "ERROR - 配置文件不存在" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "配置完成！请重启 Lingma" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
