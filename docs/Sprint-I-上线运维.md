# Sprint I · 上线运维

> **目标**：生产预检、就绪探针、备份运维 API、上线检查清单。

## 交付

| ID | 内容 |
|----|------|
| I-01 | `production_readiness_service` — JWT/DB/物流/平台/备份目录/Redis |
| I-02 | `GET /api/v1/ops/readiness`（超管）+ `GET /ops/readiness/public` |
| I-03 | `POST /ops/backup/run` + `GET /ops/backup/status` |
| I-04 | `GET /health/ready` 增强（DB + 配置，503 未就绪） |
| I-05 | `scripts/run_production_preflight.py` |

## 一键预检

```powershell
# 本地（默认 development，SQLite 可 warn 通过）
python scripts/run_production_preflight.py

# 模拟生产门禁（须 PostgreSQL + seed + 关闭 OAUTH_DEV_BYPASS）
$env:PREFLIGHT_ENVIRONMENT="production"
python scripts/run_production_preflight.py
```

产出：`docs/production-preflight-latest.json`

## Kubernetes 探针建议

| 探针 | 路径 | 说明 |
|------|------|------|
| liveness | `GET /health` | 进程存活 |
| readiness | `GET /health/ready` | DB + 必填配置，失败返回 HTTP 503 |

## 生产 Cron 建议

```cron
# 每日 03:00 备份（应用内 AutoBackup 已注册，亦可手动）
0 3 * * * curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" https://api.example.com/api/v1/ops/backup/run

# 每小时就绪巡检（可选）
0 * * * * curl -s https://api.example.com/api/v1/ops/readiness/public
```

## PostgreSQL 备份

应用内 `run_manual_backup` 对 SQLite 复制文件；**生产 PostgreSQL** 请使用：

```bash
pg_dump -Fc "$DATABASE_URL" -f backups/pg_$(date +%Y%m%d).dump
```

## Nginx / SSL（运维手册摘要）

1. 租户 CNAME → `saas.youding.com`
2. `POST /api/v1/tenants/{id}/domains/{domain}/ssl` 提交申请
3. 生产配置 `SSL_PROVIDER=http` + `ACME_WEBHOOK_URL` 对接 certbot 服务  
   或运维侧 `certbot --nginx -d www.tenant.com`

## 上线前 Checklist

- [ ] `ENVIRONMENT=production`
- [ ] `JWT_SECRET_KEY` ≥ 32 字符
- [ ] `OAUTH_DEV_BYPASS=false`
- [ ] `DATABASE_URL` 为 PostgreSQL
- [ ] `python scripts/migrate_production.py --seed-full`
- [ ] `python scripts/run_production_preflight.py` → ok=true
- [ ] `python scripts/run_demo_acceptance.py`（演示环境）
