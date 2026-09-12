# Feishu MCP Server Auto Deployment Script
# Night Mode - Fully Automated
#
# SECURITY: 所有敏感配置必须通过环境变量提供，禁止硬编码密钥

Write-Host "======================================"
Write-Host "    Feishu MCP Server Auto Deployment"
Write-Host "======================================"
Write-Host ""

# Configuration - 从环境变量读取，禁止硬编码
$FEISHU_APP_ID = $env:FEISHU_APP_ID
$FEISHU_VERIFICATION_TOKEN = $env:FEISHU_VERIFICATION_TOKEN
$FEISHU_APP_SECRET = $env:FEISHU_APP_SECRET

# 验证环境变量是否设置
if (-not $FEISHU_APP_ID) {
    Write-Error "ERROR: FEISHU_APP_ID 环境变量未设置"
    exit 1
}

if (-not $FEISHU_VERIFICATION_TOKEN) {
    Write-Error "ERROR: FEISHU_VERIFICATION_TOKEN 环境变量未设置"
    exit 1
}

if (-not $FEISHU_APP_SECRET) {
    Write-Error "ERROR: FEISHU_APP_SECRET 环境变量未设置"
    exit 1
}

Write-Host "Environment variables verified successfully."
Write-Host "----------------------------------------"

# Set FEISHU_APP_ID
Write-Host "Setting FEISHU_APP_ID..."
echo $FEISHU_APP_ID | npx wrangler secret put FEISHU_APP_ID --env production

# Set FEISHU_VERIFICATION_TOKEN
Write-Host "Setting FEISHU_VERIFICATION_TOKEN..."
echo $FEISHU_VERIFICATION_TOKEN | npx wrangler secret put FEISHU_VERIFICATION_TOKEN --env production

# Set FEISHU_APP_SECRET
Write-Host "Setting FEISHU_APP_SECRET..."
echo $FEISHU_APP_SECRET | npx wrangler secret put FEISHU_APP_SECRET --env production

Write-Host ""
Write-Host "Redeploying service..."
Write-Host "----------------------------------------"
npx wrangler deploy --env production

Write-Host ""
Write-Host "Deployment completed!"
Write-Host "Service URL: https://feishu-mcp-server-prod.lvbowang88.workers.dev"