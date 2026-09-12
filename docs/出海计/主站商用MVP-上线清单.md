# 主站商用 MVP · 上线清单

> **口径**：核心网站 + 询盘 + SaaS 租户后台 + **流量看板** 可上线；**AI / AccioWork / UBrain 飞轮** 为二期。  
> **不等于**：对外 PM 签字、演示独立域商用（见 [上线评审-严格门禁-2026-05-25.md](./上线评审-严格门禁-2026-05-25.md)）。

---

## 一键门禁（工程师）

```powershell
cd "C:\Users\97907\Desktop\UJ\website CodeBuddy"
copy .env.prod.example .env.prod
# 编辑 .env.prod：DB_*、JWT_SECRET_KEY、SECRET_KEY、DOMAIN、SMTP 等

powershell -File scripts/deploy-mvp-production.ps1
# 生产机 Postgres 已就绪且 DATABASE_URL 指向生产库时，不要 -SkipMigrate
# 启动栈：powershell -File scripts/deploy-mvp-production.ps1 -ComposeUp
```

产出：`docs/production-preflight-latest.json`（`ok: true` 为门禁通过）。

环境变量要点：

| 变量 | MVP 说明 |
|------|----------|
| `MVP_LAUNCH=1` | 无 AI Key 可启动；AI 接口降级 mock |
| `ENVIRONMENT=production` | 必须 |
| `DATABASE_URL` | 必须 PostgreSQL |
| `JWT_SECRET_KEY` / `SECRET_KEY` | ≥32 字符 |
| `PAYMENT_STRICT_VERIFY=1` | 开通收款前必须；MVP 预检可为 warn |
| `SSL_PROVIDER=certbot` | Nginx 终止 SSL 时配置 `CERTBOT_EMAIL` |
| `NUXT_PUBLIC_TENANT_ID` | 单租户固定站可选；多租户用子域名 |

---

## 阶段 A · 基础设施

| # | 动作 | 命令 |
|---|------|------|
| A1 | 复制并填写生产 env | `.env.prod` ← `.env.prod.example` |
| A2 | 迁移 + 平台种子 | `cd backend && python scripts/migrate_production.py --seed-full` |
| A3 | 路由门禁 | `python scripts/check_mounted_routes.py` |
| A4 | MVP 预检 | `PREFLIGHT_ENVIRONMENT=production MVP_LAUNCH=1 python scripts/run_production_preflight.py` |
| A5 | Docker（可选） | `docker compose -f docker-compose.prod.yml --env-file .env.prod up -d` |

迁移链含 **033**（`site_analytics_events` 流量表）。

---

## 阶段 B · 流量看板

| # | 动作 | 验收 |
|---|------|------|
| B1 | 租户站可解析租户 | 子域名 `*.youding-saas.com` 或 `NUXT_PUBLIC_TENANT_ID` |
| B2 | 埋点 | 浏览器 `POST /api/v1/analytics/event` → 200 |
| B3 | 租户后台 | `/client/traffic` 有 PV/点击（有访问后） |
| B4 | 询盘归因 | 提交询盘后在看板「询盘」有记录 |
| B5 | 脚本自检 | `python scripts/verify_traffic_pipeline.py` |

---

## 阶段 C · 生产预检（服务器）

在 **真实 Postgres** 上复跑：

```powershell
$env:DATABASE_URL = "postgresql+psycopg2://..."
$env:ENVIRONMENT = "production"
$env:MVP_LAUNCH = "1"
$env:JWT_SECRET_KEY = "..."   # ≥32
$env:PAYMENT_STRICT_VERIFY = "1"
$env:SSL_PROVIDER = "certbot"
$env:CERTBOT_EMAIL = "ops@example.com"
python scripts/run_production_preflight.py
```

必须通过（`required` 无 `fail`）：

- 数据库连通、非 SQLite  
- JWT 强度  
- 40 平台主数据（`migrate_production --seed-full`）  
- 关键 API 挂载（含 `/api/v1/analytics/*`）  
- 备份目录可写  

可为 **warn**（MVP 允许）：

- AI 未配 Key（`MVP_LAUNCH=1`）  
- UBrain 路径（二期）  
- Redis / FRONTEND_URL 未配（建议仍配）

---

## 阶段 D · 创始人诊断（无需 SSH）

管理端：**超级管理员 → 创始人诊断**（`/admin/founder-diagnostics`）

1. 绑定本人微信 → 复制 `FOUNDER_WECHAT_OPENID` 到服务器 `.env.prod` → 重启后端  
2. 点 **运行诊断** / **国密自检**  

详见 `docs/安全与国密-源码调试说明.md`。

---

## 阶段 E · 人工 L3（30～60 分钟）

参考 [全站验通与安全检查.md](./全站验通与安全检查.md)：

1. HTTPS 首页可开  
2. 管理端登录（租户 / 运营 / 超管）  
3. 提交一条真实格式询盘  
4. **流量看板** 各角色页有数据或空态正确  
5. 超管数据中心 / 聚合无假数据曲线  

---

## 二期（不挡 MVP）

- `AI_DEEPSEEK_API_KEY` 等，去掉 `MVP_LAUNCH` 或设为 `0`  
- AccioWork / SuperAgent 失败单测（13 条）  
- UBrain 飞轮 E2E：`scripts/e2e-flywheel-validation.ps1`  
- PM 书面签字、演示独立域  

---

## 相关文件

| 文件 | 用途 |
|------|------|
| `scripts/deploy-mvp-production.ps1` | 串行门禁 |
| `scripts/migrate_production.py` | Alembic + seed |
| `scripts/run_production_preflight.py` | 预检 JSON |
| `docker-compose.prod.yml` | 生产栈 |
| `.env.prod.example` | 环境模板 |
