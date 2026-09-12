# Sprint H · 商用上线

> **目标**：40 平台主数据、真实物流对接能力、SSL 申请状态机、生产迁移脚本。

## 交付一览

| ID | 内容 | 验证 |
|----|------|------|
| H-01 | 国内 20 + 海外 20 平台 seed | `python backend/scripts/seed_platforms_full.py` |
| H-02 | 快递100 物流适配（可降级 demo） | `.env` 见下 |
| H-03 | SSL 状态机（mock / HTTP 委托） | `POST .../domains/{domain}/ssl` |
| H-04 | `migrate_production.py` | `alembic upgrade` + seed |
| H-05 | 单元测试 | `pytest tests/unit/test_sprint_h_services.py` |

## 环境变量

```env
# 物流
LOGISTICS_PROVIDER=demo          # 或 kuaidi100
KUAIDI100_CUSTOMER=
KUAIDI100_API_KEY=
LOGISTICS_FALLBACK_DEMO=true

# SSL
SSL_PROVIDER=mock                # 或 http + ACME_WEBHOOK_URL
ACME_WEBHOOK_URL=
```

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/platforms/catalog` | 40 平台目录与就绪状态 |
| GET | `/api/v1/platforms/pilot` | 5+5 试点 |
| GET | `/api/v1/tenants/{id}/domains/ssl` | 租户域名 SSL 状态 |
| POST | `/api/v1/tenants/{id}/domains/{domain}/ssl` | 触发 SSL 申请 |

## 生产部署

```powershell
cd backend
$env:DATABASE_URL="postgresql+psycopg2://user:pass@host:5432/db"
python scripts/migrate_production.py --seed-full
```

## 说明

- **快递100**：配置密钥后 `LOGISTICS_PROVIDER=kuaidi100`；失败时默认降级沙箱（可关 `LOGISTICS_FALLBACK_DEMO=false`）。
- **SSL**：`mock` 模式约 5 秒后 `pending→active`；生产可接 `ACME_WEBHOOK_URL` 由外部 certbot/acme.sh 服务回调。
- **40 平台名单**：见 `backend/app/services/platform_catalog.py`，PM 可在该文件调整后重新 seed。
