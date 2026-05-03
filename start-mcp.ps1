Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  MCP鏈嶅姟鑷姩瀹夎鍜屽惎鍔ㄥ伐鍏? -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 妫€鏌ode.js
Write-Host "[1/6] 妫€鏌ode.js鐜..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Node.js not found" }
    Write-Host "  OK Node.js宸插畨瑁? $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "  ERROR 鏈娴嬪埌Node.js" -ForegroundColor Red
    exit 1
}

# 2. 鍒涘缓閰嶇疆鏂囦欢
Write-Host "[2/6] 鍒涘缓閰嶇疆鏂囦欢..." -ForegroundColor Yellow
$configPath = "lingma-mcp.config.js"
if (-not (Test-Path $configPath)) {
    $content = "module.exports = {`n"
    $content += "  server: { port: 8787, host: 'localhost', path: '/mcp' },`n"
    $content += "  role: 'lingma-ui-assistant',`n"
    $content += "  transport: 'streamable-http',`n"
    $content += "  timeout: 30000`n"
    $content += "};`n"
    Set-Content -Path $configPath -Value $content -Encoding UTF8
    Write-Host "  OK 閰嶇疆鏂囦欢宸插垱寤? -ForegroundColor Green
} else {
    Write-Host "  OK 閰嶇疆鏂囦欢宸插瓨鍦? -ForegroundColor Green
}

# 3. 妫€鏌ョ鍙?
Write-Host "[3/6] 妫€鏌ョ鍙?787..." -ForegroundColor Yellow
$port = 8787
$connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
if ($connection) {
    Write-Host "  WARNING 绔彛琚崰鐢紝姝ｅ湪鍏抽棴..." -ForegroundColor Yellow
    Stop-Process -Id $connection.OwningProcess -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Write-Host "  OK 宸插叧闂崰鐢ㄨ繘绋? -ForegroundColor Green
} else {
    Write-Host "  OK 绔彛鍙敤" -ForegroundColor Green
}

# 4. 瀹夎MCP Server
Write-Host "[4/6] 妫€鏌CP Server..." -ForegroundColor Yellow
try {
    $result = npm list -g @modelcontextprotocol/server 2>&1 | Out-String
    if ($result -notmatch "@modelcontextprotocol/server") {
        Write-Host "  姝ｅ湪瀹夎MCP Server..." -ForegroundColor Yellow
        npm install -g @modelcontextprotocol/server
        Write-Host "  OK 瀹夎瀹屾垚" -ForegroundColor Green
    } else {
        Write-Host "  OK 宸插畨瑁? -ForegroundColor Green
    }
} catch {
    Write-Host "  INFO 灏嗕娇鐢╪px鏂瑰紡杩愯" -ForegroundColor Yellow
}

# 5. 鍚姩鏈嶅姟
Write-Host "[5/6] 鍚姩MCP鏈嶅姟..." -ForegroundColor Yellow
$logFile = "mcp-server.log"
$process = Start-Process -FilePath "npx" `
    -ArgumentList "@modelcontextprotocol/server", "-c", "lingma-mcp.config.js" `
    -RedirectStandardOutput $logFile `
    -RedirectStandardError $logFile `
    -WindowStyle Normal `
    -PassThru

Write-Host "  OK 杩涚▼宸插惎鍔?(PID: $($process.Id))" -ForegroundColor Green
Write-Host "  绛夊緟鏈嶅姟鍒濆鍖?.." -ForegroundColor Cyan
Start-Sleep -Seconds 5

# 6. 楠岃瘉
Write-Host "[6/6] 楠岃瘉鏈嶅姟鐘舵€?.." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:$port/mcp" -Method GET -TimeoutSec 5 -ErrorAction Stop
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  SUCCESS MCP鏈嶅姟鍚姩鎴愬姛" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  鍦板潃: http://localhost:$port/mcp" -ForegroundColor White
    Write-Host "  Role: lingma-ui-assistant" -ForegroundColor White
    Write-Host "========================================" -ForegroundColor Green
} catch {
    Write-Host "  WARNING 鏈嶅姟鍙兘浠嶅湪鍚姩涓? -ForegroundColor Yellow
    Write-Host "  璇风◢鍚庤闂?http://localhost:$port/mcp" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "鎸夊洖杞﹂敭閫€鍑?.."
Read-Host
