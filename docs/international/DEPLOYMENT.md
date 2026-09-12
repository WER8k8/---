# 优丁建材国际订单采集系统 — 部署文档

## 1. 架构概述

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Cloudflare Workers (海外边缘节点)               │
│                                                                     │
│  ┌─────────────┐  ┌──────────────────┐  ┌────────────────────────┐ │
│  │ 调度 Worker  │→│ 爬虫 Worker       │→│ NLP 提取 Worker        │ │
│  │ (Cron 触发)  │  │ (Puppeteer/HTTP) │  │ (AES-256 加密输出)     │ │
│  └─────────────┘  └──────────────────┘  └───────────┬────────────┘ │
│                                                      │              │
└──────────────────────────────────────────────────────┼──────────────┘
                                                       │ HTTPS (TLS 1.3)
                                                       │
┌──────────────────────────────────────────────────────┼──────────────┐
│                    阿里云轻量服务器 (国内节点)           │              │
│                                                      ▼              │
│  ┌──────────────────┐  ┌────────────────┐  ┌──────────────────────┐│
│  │ Nginx (SSL 终端)  │→│ Webhook 接收    │→│ PostgreSQL 15+       ││
│  │                  │  │ (Node.js 18+)   │  │ (数据存储)            ││
│  └──────────────────┘  └────────────────┘  └──────────────────────┘│
│                                               ↑                    │
│  ┌────────────────────────────────────────────┘                    │
│  │ Admin 管理后台 (Vue + Node.js)                                  │
│  └─────────────────────────────────────────────────────────────────┘
```

**数据流说明：**
1. Cron 定时器触发调度 Worker，按目标列表分发爬虫任务
2. 爬虫 Worker 通过 HTTP 请求或 Puppeteer 无头浏览器采集目标网站页面
3. NLP 提取 Worker 解析页面内容，抽取订单信息（产品名、数量、价格、联系方式等）
4. 提取结果经 AES-256-GCM 加密后，通过 HTTPS POST 至阿里云 Webhook 端点
5. 阿里云 Nginx 终结 SSL，反向代理至 Node.js Webhook 服务
6. Webhook 服务解密、校验、入库至 PostgreSQL
7. Admin 后台提供数据查询、导出、系统管理功能

---

## 2. 环境要求

| 组件 | 最低版本 | 说明 |
|------|----------|------|
| Node.js | 18+ | Workers 本地开发 & 后端运行时 |
| npm / yarn | 9+ | 包管理 |
| Python | 3.11+ | NLP 辅助工具（可选） |
| PostgreSQL | 15+ | 主数据库 |
| Nginx | 1.24+ | 反向代理 & SSL 终端 |
| Wrangler | 3.x | Cloudflare Workers CLI |

---

## 3. Cloudflare Workers 部署

### 3.1 安装 Wrangler

```bash
# 全局安装 wrangler
npm install -g wrangler

# 验证安装
wrangler --version
# 应输出: ⛅ wrangler 3.x.x
```

### 3.2 登录 Cloudflare

```bash
wrangler login
# 浏览器会自动打开，授权后终端显示成功信息
```

### 3.3 配置环境变量

创建或编辑 `wrangler.toml`：

```toml
name = "order-crawler"
main = "src/index.js"
compatibility_date = "2025-04-01"

# 环境变量
[vars]
WEBHOOK_URL = "https://your-aliyun-server.com/api/webhook"
ENCRYPTION_KEY = ""  # 通过 wrangler secret 设置
CRAWL_TIMEOUT_MS = "30000"
MAX_RETRIES = "3"
TARGET_LANGUAGES = "en,ar,fr,es,pt,ru,de,tr,id,th,vi,ms,sw,ko,ja,hi,bn,ur,fa"

# Cron 触发器（每 30 分钟执行一次）
[triggers]
crons = ["*/30 * * * *"]

# KV 命名空间（用于任务去重和状态跟踪）
[[kv_namespaces]]
binding = "TASK_STATE"
id = "your-kv-namespace-id"
```

设置敏感变量（不要写在配置文件中）：

```bash
# 设置 AES-256 加密密钥（32 字节，Base64 编码）
wrangler secret put ENCRYPTION_KEY
# 输入: your-base64-encoded-32-byte-key

# 设置 Webhook 签名密钥
wrangler secret put WEBHOOK_SECRET
# 输入: your-webhook-hmac-secret
```

### 3.4 本地开发

```bash
# 克隆项目
git clone <your-repo-url>
cd order-crawler

# 安装依赖
npm install

# 本地测试（需安装 Node.js 18+）
wrangler dev --port 8787

# 在另一个终端测试
curl http://localhost:8787/__scheduled?cron=*/30+*+*+*+*
```

### 3.5 部署

```bash
# 发布到生产环境
wrangler deploy

# 发布到预览环境
wrangler deploy --env preview

# 查看部署状态
wrangler tail
```

---

## 4. 阿里云后端部署

### 4.1 服务器初始化

```bash
# 使用 SSH 登录服务器
ssh root@your-aliyun-server-ip

# 系统更新
apt update && apt upgrade -y

# 安装 Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# 安装 PostgreSQL 15+
apt install -y postgresql-15 postgresql-contrib-15

# 安装 Nginx
apt install -y nginx

# 安装 certbot（SSL 证书）
apt install -y certbot python3-certbot-nginx

# 安装依赖工具
apt install -y git curl wget unzip
```

### 4.2 数据库初始化

```bash
# 启动 PostgreSQL
systemctl start postgresql
systemctl enable postgresql

# 创建数据库和用户
sudo -u postgres psql <<EOF
CREATE USER order_admin WITH PASSWORD 'your-strong-password';
CREATE DATABASE order_db OWNER order_admin;
GRANT ALL PRIVILEGES ON DATABASE order_db TO order_admin;
EOF
```

### 4.3 部署后端应用

```bash
# 创建项目目录
mkdir -p /opt/order-system
cd /opt/order-system

# 克隆代码
git clone <your-repo-url> .

# 安装依赖
npm install --production
npm install pm2 -g

# 配置环境变量
cat > .env <<EOF
PORT=3000
NODE_ENV=production
DB_HOST=localhost
DB_PORT=5432
DB_NAME=order_db
DB_USER=order_admin
DB_PASSWORD=your-strong-password
ENCRYPTION_KEY=your-base64-encoded-32-byte-key
WEBHOOK_SECRET=your-webhook-hmac-secret
LOG_LEVEL=info
EOF

# 数据库迁移
npx knex migrate:latest
npx knex seed:run  # 可选：填充测试数据

# 启动服务（使用 pm2）
pm2 start src/index.js --name order-webhook
pm2 save
pm2 startup  # 设置开机自启
```

### 4.4 Nginx 配置

创建 `/etc/nginx/sites-available/order-system`：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL 证书（使用 certbot 后自动填充）
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers on;

    # 请求大小限制（最大订单数据）
    client_max_body_size 10m;

    # Webhook 端点
    location /api/webhook {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 30s;
    }

    # Admin 管理后台
    location /admin {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
    }

    # 静态资源缓存
    location /static {
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
}
```

启用站点并申请 SSL：

```bash
# 启用配置
ln -s /etc/nginx/sites-available/order-system /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx

# 申请 SSL 证书
certbot --nginx -d your-domain.com --non-interactive --agree-tos -m admin@your-domain.com

# 配置自动续期
certbot renew --dry-run
```

### 4.5 安全组配置

在阿里云控制台 → 安全组规则，添加以下入站规则：

| 端口 | 协议 | 源 | 说明 |
|------|------|-----|------|
| 22 | TCP | 公司固定 IP 或 VPN | SSH |
| 80 | TCP | 0.0.0.0/0 | HTTP 重定向 |
| 443 | TCP | 0.0.0.0/0 | HTTPS |
| 5432 | TCP | 127.0.0.1 | PostgreSQL（禁止公网开放） |

### 4.6 防火墙配置（UFW）

```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow from <company-ip> to any port 22 proto tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
```

---

## 5. 部署验证步骤

### 5.1 健康检查

```bash
# 检查后端服务
curl -s https://your-domain.com/health | jq .
# 预期输出: {"status":"ok","uptime":12345,"db":"connected"}

# 检查 Webhook 端点可达性
curl -s -o /dev/null -w "%{http_code}" -X POST https://your-domain.com/api/webhook
# 预期输出: 401（未授权，说明端点在线且认证正常）
```

### 5.2 Workers 端到端测试

```bash
# 手动触发爬虫（使用 wrangler）
wrangler tail &
wrangler trigger scheduled --name order-crawler

# 或者直接调用 Worker HTTP 端点
curl -X POST "https://order-crawler.your-subdomain.workers.dev/__scheduled" \
  -H "Content-Type: application/json" \
  -d '{"cron":"*/30 * * * *"}'
```

### 5.3 验证数据入库

```bash
# 登录数据库检查
sudo -u postgres psql -d order_db -c "SELECT COUNT(*) FROM orders;"
sudo -u postgres psql -d order_db -c "SELECT id, source, status, created_at FROM orders ORDER BY created_at DESC LIMIT 10;"
```

### 5.4 模拟 webhook 推送测试

```bash
# 使用测试脚本模拟 Webhook 推送
ENCRYPTION_KEY="your-key" node scripts/test_webhook.js

# 或者手动 curl
curl -X POST https://your-domain.com/api/webhook \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: $(./scripts/sign.sh '{"test":true}')" \
  -d '{"encrypted_data":"...", "iv":"...", "source":"test"}'
```

---

## 6. 回滚方案

### 6.1 Workers 回滚

```bash
# 查看历史版本
wrangler versions list

# 查看版本详情
wrangler versions show <version-id>

# 回滚到指定版本
wrangler rollback --version <version-id>

# 或回滚到上一个版本
wrangler rollback
```

### 6.2 后端回滚

```bash
# pm2 版本回退
cd /opt/order-system

# 查看发布记录
git log --oneline -10

# 回退到指定版本
git checkout <previous-release-tag>

# 重新安装依赖（如有变更）
npm install --production

# 回滚数据库（如有迁移）
npx knex migrate:down

# 重启服务
pm2 restart order-webhook
```

### 6.3 数据库回滚

```bash
# 查看迁移历史
npx knex migrate:list

# 回退最后一批迁移
npx knex migrate:down

# 回退到指定批次
npx knex migrate:down <batch-number>

# 从备份恢复（见 MAINTENANCE.md 备份章节）
pg_restore -U order_admin -d order_db /backups/order_db_2025-01-01.dump
```

### 6.4 域名回滚（DNS）

如升级涉及域名变更，在 Cloudflare Dashboard 中：

1. DNS → Records → 修改 A 记录指向旧服务器 IP
2. 等待 TTL 过期（通常 300 秒）
3. 验证服务恢复

---

## 7. 附录：目录结构

```
/opt/order-system/
├── src/
│   ├── index.js              # 入口文件
│   ├── webhook/              # Webhook 接收
│   ├── decrypt/              # 解密模块
│   ├── db/                   # 数据库操作
│   ├── admin/                # 管理后台 API
│   └── middleware/            # 认证/日志中间件
├── migrations/               # 数据库迁移
├── seeds/                    # 测试数据
├── scripts/                  # 运维脚本
├── .env                      # 环境变量
├── package.json
└── knexfile.js               # Knex 配置
```

---

> **部署完成后请立即执行 COMPLIANCE.md 中的合规检查清单，确保跨境数据传输合规。**
