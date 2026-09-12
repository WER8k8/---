# 飞书MCP Server 一键部署脚本
# 使用前请确保：
# 1. 已安装 Node.js >= 18
# 2. 已安装 wrangler CLI
# 3. 已获取 Cloudflare API Token

param(
    [string]$FEISHU_APP_ID,
    [string]$FEISHU_APP_SECRET,
    [string]$FEISHU_VERIFICATION_TOKEN,
    [string]$CLOUDFLARE_API_TOKEN,
    [string]$CLOUDFLARE_ACCOUNT_ID
)

Write-Host "========================================="
Write-Host "  飞书MCP Server - Cloudflare部署脚本"
Write-Host "========================================="

# 检查参数
if (-not $FEISHU_APP_ID) {
    $FEISHU_APP_ID = Read-Host "请输入飞书 App ID"
}
if (-not $FEISHU_APP_SECRET) {
    $FEISHU_APP_SECRET = Read-Host "请输入飞书 App Secret"
}
if (-not $FEISHU_VERIFICATION_TOKEN) {
    $FEISHU_VERIFICATION_TOKEN = Read-Host "请输入飞书 Verification Token"
}
if (-not $CLOUDFLARE_API_TOKEN) {
    $CLOUDFLARE_API_TOKEN = Read-Host "请输入 Cloudflare API Token"
}
if (-not $CLOUDFLARE_ACCOUNT_ID) {
    $CLOUDFLARE_ACCOUNT_ID = Read-Host "请输入 Cloudflare Account ID"
}

Write-Host ""
Write-Host "[1/5] 配置 Wrangler..."
$env:CLOUDFLARE_API_TOKEN = $CLOUDFLARE_API_TOKEN
$env:CLOUDFLARE_ACCOUNT_ID = $CLOUDFLARE_ACCOUNT_ID

Write-Host "[2/5] 设置环境变量..."
wrangler secret put FEISHU_APP_ID --env production --value $FEISHU_APP_ID
wrangler secret put FEISHU_APP_SECRET --env production --value $FEISHU_APP_SECRET
wrangler secret put FEISHU_VERIFICATION_TOKEN --env production --value $FEISHU_VERIFICATION_TOKEN

Write-Host "[3/5] 创建 R2 Bucket（缓存用）..."
try {
    wrangler r2 bucket create feishu-mcp-cache
} catch {
    Write-Host "R2 Bucket 可能已存在，继续..."
}

Write-Host "[4/5] 构建项目..."
npm run build

Write-Host "[5/5] 部署到 Cloudflare..."
wrangler deploy --env production

Write-Host ""
Write-Host "========================================="
Write-Host "  部署完成！"
Write-Host "========================================="
Write-Host ""
Write-Host "请更新 .trae/mcp.json 文件中的 URL："
Write-Host "https://feishu-mcp-server-prod.your-subdomain.workers.dev/mcp"
