# 外贸 B2B 生态 — 服务器部署清单

> 与源码同仓交付 · 数据：`backend/app/data/foreign_trade_ecosystem_catalog.json`  
> API：`GET /api/v1/foreign-trade/ecosystem/*`

## 1. 随镜像必达（bundled）

无需额外容器，构建 `backend` + `frontend/admin` 即包含：

| 能力 | 代码/数据 |
|------|-----------|
| 开发信质量包 | `outreach_deliverability_service.py` |
| Accio 销售 | `accio_sales_service.py` |
| DeerFlow 研究（Lite + 旁路） | `deerflow_*` · 见 [DEERFLOW-SIDECAR-DEPLOY.md](./DEERFLOW-SIDECAR-DEPLOY.md) |
| Hermes 迭代闭环 | `hermes_continuous_iteration_service.py` |
| 矩阵/建站/广告 gap | `matrix_publish_service` · commercial-os |
| 专家角色库 | `b2b_trade_experts.json` |
| **生态目录** | `foreign_trade_ecosystem_catalog.json` |

部署后验证：

```bash
curl -s "$API/api/v1/foreign-trade/ecosystem/overview" -H "Authorization: Bearer $TOKEN" | jq .
curl -s "$API/api/v1/super-agent/skills?include_gaps=true" -H "Authorization: Bearer $TOKEN" | jq '.data.total'
```

## 2. 生产 `.env` 建议（外贸相关）

在 `deploy/production/env.template` 基础上：

```env
# 研究员 + 运维闭环
HERMES_OPS_AUTOPILOT_ENABLED=true
HERMES_CONTINUOUS_ITERATION_ENABLED=true
DEERFLOW_SCHEDULER_ENABLED=true
DEERFLOW_TENANT_CELERY_ENABLED=true

# 可选旁路
DEERFLOW_SIDECAR_URL=
DEERFLOW_SIDECAR_SECRET=
AI_FIND_CUSTOMER_URL=
AI_FIND_CUSTOMER_TOKEN=
HEADLESS_PROBE_SIDECAR_URL=
HEADLESS_PROBE_SIDECAR_TOKEN=
HEADLESS_PROBE_ALLOW_STUB=0
ECOMMERCE_CRAWLERS_URL=
ECOMMERCE_CRAWLERS_TOKEN=
USER_ACTION_ANALYTICS_URL=
USER_ACTION_ANALYTICS_TOKEN=
USER_ACTION_ANALYTICS_ALLOW_STUB=0

# n8n 回调（销售蜂群 / 飞书 / 发布完成）
N8N_WEBHOOK_SECRET=

# Agency LLM（可选 compose）
HERMES_AGENCY_LLM_ENABLED=false
```

## 3. 可选 Sidecar（compose_optional）

| 组件 | 路径 | 用途 |
|------|------|------|
| AI Hunter 找客 | [AI-FIND-CUSTOMER-SIDECAR-DEPLOY.md](./AI-FIND-CUSTOMER-SIDECAR-DEPLOY.md) | Sidecar HTTP，主站 Accio 优先调用 |
| Headless 探针 | [HEADLESS-PROBE-SIDECAR-DEPLOY.md](./HEADLESS-PROBE-SIDECAR-DEPLOY.md) | Playwright Worker，增长工具 batch |
| ECommerce 爬虫 | [ECOMMERCE-CRAWLERS-SIDECAR-DEPLOY.md](./ECOMMERCE-CRAWLERS-SIDECAR-DEPLOY.md) | 百度/企查查/招聘等 Python 爬虫网关 |
| Spark 行为分析 | [USER-ACTION-ANALYTICS-SIDECAR-DEPLOY.md](./USER-ACTION-ANALYTICS-SIDECAR-DEPLOY.md) | 页面转化 / Session / 热门商品 |
| n8n 工作流 | `deploy/examples/n8n/` | DeerFlow 完成、发布 done、反馈闭环 |
| Agency Ollama | `deploy/production/agency-llm-compose.yml` | Hermes ECC LLM 本地 |
| SEO 矩阵库 | `deploy/docs/SEO-MATRIX-DATABASE-DEPLOY.md` | 独立 Postgres |

**不默认 fork** 进主仓：ERPNext、UZonMail — 通过 `agent-hub` MCP 登记或运维自建。AI_Find_Customer / Headless 见上表 Sidecar 文档。

## 4. P0 短板与补齐路线

| GW ID | 短板 | 内置状态 | 推荐补齐 |
|-------|------|----------|----------|
| GW-P-TR-01 | UTM 全链路 | gap | inquiry 字段 + leadscloud/inquiry 参考 |
| GW-G-CC-02 | 1→N 内容变体 | gap | content_master 串联 |
| GW-L-DC-01 | MEDDPICC | gap | b2b-sdr BANT 对标 |
| GW-G-AEO-01 | AEO 事实审计 | gap | brand_audit job |
| GW-G-SM-04 | 账号健康告警 | gap | binding 定时 + 飞书 |

完整技能表：`GET /api/v1/foreign-trade/ecosystem/skills?status=gap`

## 5. GitHub 外贸搜索（591 条）用法

- 不将 spam 仓库 vendoring 进主仓  
- 策展列表在 catalog → `github_curated`  
- 桌面扩展库（可选 sync）：`出海计/docs/外贸知识库/`  
- 补抓脚本（运维机）：`出海计/scripts/fetch-github-foreign-trade.ps1`

## 6. 部署顺序（摘要）

1. `git pull` + `npm run build` + uvicorn/gunicorn  
2. `alembic upgrade head`  
3. 填写 `.env`（上表）  
4. 可选：`docker compose -f deploy/production/agency-llm-compose.yml up -d`  
5. 导入 n8n workflow JSON（examples/n8n）  
6. 验证 ecosystem overview + cert:gate  

## 7. Out-of-Scope（刻意不做）

- 购买实名海关/企业库 API  
- 自动 SMTP 群发（仅草稿 + deliverability）  
- VPN/翻墙类 GitHub 项目  
- 侵权电子书打包进镜像  
