# ECommerceCrawlers Sidecar 部署

> 上游：[DropsDevopsOrg/ECommerceCrawlers](https://github.com/DropsDevopsOrg/ECommerceCrawlers)  
> **不整仓 fork 进 `backend/`** — 独立 Python Worker + 合规门禁。

## 合规分级（2026-06 升级）

| 级别 | 说明 | 启用条件 |
|------|------|----------|
| `allowed_sidecar` | 百度收录、招聘、博客园等 | `purpose` + Sidecar 在线 |
| `human_review` | 企查查、点评等 | `purpose`；结果须人工核实 |
| `restricted` | 淘宝/闲鱼/FOFA/头条等 | 上列 + `ECOMMERCE_SPIDER_ENABLE_<ID>` + `tenant_consent` + `compliance_acknowledged` |
| `social_restricted` | 微信/微博/知乎 | 上列 + `ECOMMERCE_SOCIAL_SPIDERS_ENABLED=1`；**禁** `bulk_outreach` / 账号池 |
| `platform_blocked` | 蜘蛛泛目录等黑帽 SEO | **永久禁用**，主站 403 |

原 `forbidden` 社媒 spider 已改为 `social_restricted`：合规可调用，但须三重门禁 + Sidecar 隔离。

## 环境变量

```env
# 主站 backend/.env
ECOMMERCE_CRAWLERS_URL=https://your-spider-worker
ECOMMERCE_CRAWLERS_TOKEN=shared-secret
ECOMMERCE_SOCIAL_SPIDERS_ENABLED=0
ECOMMERCE_SPIDER_ENABLE_TAOBAO=0
ECOMMERCE_SPIDER_ENABLE_WECHAT=0
# 或运维一次性：ECOMMERCE_SPIDERS_ENABLE_ALL=1（不推荐生产默认开）

# Sidecar 容器
ECOMMERCE_CRAWLERS_REPO=/opt/ECommerceCrawlers
ECOMMERCE_CRAWLERS_TOKEN=shared-secret
```

## Sidecar 快速启动

```bash
git clone https://github.com/DropsDevopsOrg/ECommerceCrawlers.git /opt/ECommerceCrawlers
cd deploy/examples/ecommerce-crawlers-sidecar
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8092
```

## HTTP 契约

### `POST /v1/run-spider`

```json
{
  "spider_id": "baidu_keyword",
  "repo_path": "OthertCrawler/0x10baidu",
  "params": { "keyword": "保温建材" },
  "purpose": "SEO 收录监测",
  "compliance": "allowed_sidecar",
  "tenant_id": "optional-uuid"
}
```

响应须含 **`items` 或 `evidence_url`**，否则主站返回 `SPIDER_NO_EVIDENCE`（非假成功）。

## 主站 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/foreign-trade/integrations/ecommerce-crawlers/registry` | 全量 spider + 合规说明 |
| POST | `/api/v1/foreign-trade/integrations/ecommerce-crawlers/run` | 触发（tenant_admin+ 或超管） |
| GET | `/api/v1/foreign-trade/integrations/sidecars/status` | 含 `ecommerce_crawlers` |

### Run 请求体（restricted / social 必填）

```json
{
  "spider_id": "wechat",
  "params": { "keyword": "行业关键词" },
  "purpose": "公开公众号文章行业监测",
  "tenant_consent": true,
  "compliance_acknowledged": true
}
```

## 已登记 spider（节选）

- SEO：`baidu_keyword`
- OSINT：`qichacha`, `fofa`
- 竞品：`taobao`, `xianyu`, `zhaopin`
- 社媒：`wechat`, `weibo`, `zhihu`（social_restricted）
- 禁用：`spider_flood_dir`（platform_blocked）

完整列表见 registry API。

## 验收

```powershell
# registry
curl http://127.0.0.1:8001/api/v1/foreign-trade/integrations/ecommerce-crawlers/registry -H "Authorization: Bearer <token>"

# allowed（未配 Sidecar → 503）
curl -X POST http://127.0.0.1:8001/api/v1/foreign-trade/integrations/ecommerce-crawlers/run `
  -H "Authorization: Bearer <admin>" -H "Content-Type: application/json" `
  -d '{"spider_id":"baidu_keyword","params":{"keyword":"test"},"purpose":"seo_probe"}'

# social 无门禁 → 403 SOCIAL_SPIDERS_NOT_ENABLED
curl -X POST ... -d '{"spider_id":"wechat","purpose":"公开文章监测测试用途"}'

# 黑帽 → 403 SPIDER_PLATFORM_BLOCKED
curl -X POST ... -d '{"spider_id":"spider_flood_dir","purpose":"x"}'
```

## Out-of-Scope

- 主站内置账号池 / SMTP / 自动群发
- 无 Sidecar 时写入「已收录/已核实」终态
- 泛目录等 platform_blocked spider
