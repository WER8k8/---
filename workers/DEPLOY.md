# Workers 部署指南

## 前置条件

1. 安装 Node.js 18+
2. 安装 wrangler CLI:
   ```bash
   npm install -g wrangler
   ```
3. 登录 Cloudflare:
   ```bash
   wrangler login
   ```

## 本地开发

```bash
# 安装依赖
cd workers
npm install

# 本地运行（开发服务器）
npm run dev

# 本地运行 + 连接远程 KV/D1
npm run dev -- --remote

# 本地运行 + 自定义端口
npm run dev -- --port 8788
```

## 本地测试（不依赖 Worker runtime）

```bash
# 快速测试（爬取 example.com）
node test/test.js

# 测试指定 URL
URL=https://httpbin.org/html node test/test.js

# 测试指定地区
REGION=jp node test/test.js

# 开启调试输出
DEBUG=1 node test/test.js

# 完整传输测试（需配置 Webhook）
WEBHOOK_URL=https://your-webhook.com/api \
ENCRYPTION_KEY=0001... \
HMAC_KEY=dead... \
node test/test.js
```

## 部署步骤

1. 配置 wrangler.toml 中的 account_id 和 route:
   ```bash
   # 查看账户 ID
   wrangler whoami
   ```
   将 account_id 填入 wrangler.toml。

2. 创建 KV 命名空间（如未创建）:
   ```bash
   wrangler kv:namespace create CRAWLER_CACHE
   ```
   将返回的 id 填入 wrangler.toml 的 `kv_namespaces` 中。

3. 创建 D1 数据库（如未创建）:
   ```bash
   wrangler d1 create crawler-db
   ```
   将返回的 database_id 填入 wrangler.toml 的 `d1_databases` 中。

4. 设置生产环境变量:
   ```bash
   wrangler secret put WEBHOOK_URL
   wrangler secret put ENCRYPTION_KEY
   wrangler secret put HMAC_KEY
   wrangler secret put PROXY_ENDPOINT
   ```

5. 部署:
   ```bash
   npm run deploy
   ```

## 查看日志

```bash
# 实时日志
npm run tail

# 指定环境
npm run tail -- --env production
```

## 环境管理

项目仅使用 `production` 环境。如需多环境，在 wrangler.toml 中添加 `[env.staging]` 配置段。

```bash
# 部署到特定环境
wrangler deploy --env staging

# 查看特定环境的日志
wrangler tail --env staging
```

## 回滚

```bash
# 查看历史版本
wrangler versions list

# 回滚到指定版本
wrangler rollback <version-id>
```

## 架构概览

```
[外部 HTTP 请求]
     │ POST /api/international/crawl
     ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  crawler.ts │ ──▶ │ extractor.ts │ ──▶ │ transmitter.ts  │
│  网页爬取    │     │  信息提取     │     │  加密传输        │
└─────────────┘     └──────────────┘     └─────────────────┘
     │                     │                      │
     ▼                     ▼                      ▼
  KV (缓存)            D1 (结构化)          Webhook (外部)
```
