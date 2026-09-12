# 飞书MCP Server - Cloudflare Workers 部署指南

## 前置条件

1. 已安装 Node.js >= 18
2. 已安装 Cloudflare Wrangler CLI
3. 已创建飞书应用并获取以下凭证：
   - App ID
   - App Secret
   - Verification Token

## 安装 Wrangler

```bash
npm install -g wrangler
```

## 登录 Cloudflare

```bash
wrangler login
```

## 配置环境变量

编辑 `wrangler.toml` 文件，填入您的飞书凭证：

```toml
[vars]
FEISHU_APP_ID = "cli_xxxxxxxxxxxx"
FEISHU_APP_SECRET = "your-feishu-app-secret"
FEISHU_VERIFICATION_TOKEN = "your-verification-token"
FEISHU_API_BASE_URL = "https://open.feishu.cn/open-apis"
```

或者使用 Cloudflare Secrets（推荐）：

```bash
wrangler secret put FEISHU_APP_ID
wrangler secret put FEISHU_APP_SECRET
wrangler secret put FEISHU_VERIFICATION_TOKEN
```

## 创建 R2 Bucket（可选）

如果需要缓存功能：

```bash
wrangler r2 bucket create feishu-mcp-cache
```

## 开发模式

```bash
npm install
npm run dev
```

## 部署到 Cloudflare

```bash
npm run deploy
```

## 验证部署

```bash
# 健康检查
curl https://feishu-mcp-server.your-domain.workers.dev/health

# 测试发送消息
curl -X POST https://feishu-mcp-server.your-domain.workers.dev/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "id": "1",
    "method": "send_text_message",
    "params": {
      "open_id": "ou_xxxxxxxxxxxx",
      "text": "测试消息"
    }
  }'
```

## MCP API 接口

### 基础路径

```
POST /mcp
```

### 请求格式

```json
{
  "id": "请求ID",
  "method": "工具名称",
  "params": {
    "参数名": "参数值"
  }
}
```

### 响应格式

```json
{
  "id": "请求ID",
  "result": {
    "返回数据"
  },
  "error": {
    "code": 错误码,
    "message": "错误信息"
  }
}
```

## 可用工具列表

| 工具名称 | 描述 | 参数 |
|----------|------|------|
| `list_tools` | 获取所有可用工具列表 | 无 |
| `send_text_message` | 发送文本消息 | open_id, text |
| `send_card_message` | 发送卡片消息 | open_id, card |
| `get_user_info` | 获取用户信息 | open_id |
| `get_user_id_by_email` | 通过邮箱获取用户ID | email |
| `send_text_by_email` | 通过邮箱发送文本消息 | email, text |
| `send_welcome` | 发送欢迎卡片 | open_id, user_name(可选) |
| `send_inquiry_notification` | 发送询盘通知卡片 | open_id, inquiry |

## 配置到 Trae

更新 `.trae/mcp.json` 文件，将 `url` 替换为您的 Workers 部署地址：

```json
{
  "mcps": [
    {
      "name": "feishu-mcp",
      "description": "飞书机器人MCP服务",
      "url": "https://feishu-mcp-server.your-domain.workers.dev/mcp",
      "api_key": "",
      "headers": {}
    }
  ]
}
```

## 飞书应用配置

在飞书开放平台配置您的应用：

1. **凭证与基础信息** → 获取 App ID 和 App Secret
2. **事件与回调** → 配置事件回调URL（如果需要接收消息）
3. **权限管理** → 添加以下权限：
   - `im:message`（发送消息）
   - `im:resource`（获取资源）
4. **安全设置** → 设置 Verification Token
5. **发布应用** → 创建版本并发布到企业内

## 注意事项

1. 飞书应用需要发布到企业内才能正常使用
2. Token会自动缓存，有效期2小时
3. 部署后 Workers 会自动处理 HTTPS
4. Cloudflare Workers 提供全球边缘部署，延迟更低
