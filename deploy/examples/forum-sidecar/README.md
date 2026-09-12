# 论坛 / 问答 Sidecar — Apache Answer（可选）

与主栈 **分离部署**；产品 API 仍跑 `scripts/start-dev-admin.ps1`。

## 用途

- 租户独立站 **买家问答**（岩棉规格、MOQ、认证长尾 SEO）
- 不做为 Admin 内置模块；避免 PHP/Ruby 论坛进 `backend/`

## 快速启动

```powershell
cd deploy/examples/forum-sidecar
docker compose up -d
```

浏览器打开 http://localhost:9080 ，按向导初始化（开发可用 SQLite）。

## 环境变量（主 API `.env`）

```env
FORUM_SIDECAR_URL=http://127.0.0.1:9080
FORUM_WEBHOOK_SECRET=   # 可选全局密钥；租户也可在 Client 轮换独立密钥
```

## Webhook

Answer 管理后台 → Webhook → `POST /api/v1/forum/webhook`

Headers: `X-Forum-Webhook-Secret`, `X-Tenant-Id`, `Content-Type: application/json`

Body 示例:

```json
{"event":"question.created","title":"Rock wool A1 fire rating thickness?"}
```

## Client

Admin → `/client/forum-qa` 开启嵌入、复制 Webhook 配置。

## 反代

见 `Caddyfile.snippet`（租户子域 `forum.*` → `:9080`）

## 文档

- 选型审计：`docs/open-source-audit/16-forum-community-sidecar.md`
- 源码深读：`powershell -File scripts/clone-forum-ref-repos.ps1` → `_ref/answer`（不进 git）
