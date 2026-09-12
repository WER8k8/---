# 飞书MCP服务配置脚本
Write-Host "======================================"
Write-Host "    飞书MCP服务配置助手"
Write-Host "======================================"
Write-Host ""

# 获取飞书App ID
$FEISHU_APP_ID = Read-Host "请输入飞书APP_ID (格式: cli_xxxxxxxxxxxx)"

# 获取飞书验证令牌
$FEISHU_VERIFICATION_TOKEN = Read-Host "请输入飞书VERIFICATION_TOKEN"

Write-Host ""
Write-Host "正在配置环境变量..."

# 设置FEISHU_APP_ID
echo $FEISHU_APP_ID | npx wrangler secret put FEISHU_APP_ID --env production

# 设置FEISHU_VERIFICATION_TOKEN
echo $FEISHU_VERIFICATION_TOKEN | npx wrangler secret put FEISHU_VERIFICATION_TOKEN --env production

Write-Host ""
Write-Host "正在重新部署服务..."
npx wrangler deploy --env production

Write-Host ""
Write-Host "======================================"
Write-Host "    配置完成！"
Write-Host "======================================"
Write-Host ""
Write-Host "服务地址: https://feishu-mcp-server-prod.lvbowang88.workers.dev"
Write-Host ""
Write-Host "可用工具列表:"
Write-Host "- send_text_message: 发送文本消息给飞书用户"
Write-Host "- send_card_message: 发送卡片消息给飞书用户"
Write-Host "- get_user_info: 获取飞书用户信息"
Write-Host "- get_user_id_by_email: 通过邮箱获取用户ID"
Write-Host "- send_text_by_email: 通过邮箱发送文本消息"
Write-Host "- send_welcome: 发送欢迎卡片"
Write-Host "- send_inquiry_notification: 发送询盘通知"
Write-Host ""
Write-Host "下一步: 更新 .trae/mcp.json 配置文件"
Write-Host "将 URL 设置为: https://feishu-mcp-server-prod.lvbowang88.workers.dev/mcp"