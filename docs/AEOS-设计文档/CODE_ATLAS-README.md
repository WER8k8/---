# CODE ATLAS 索引 · 优丁全库代码地图

> 自动生成 + 人工摘要。目标：知道**每个模块管什么、和谁连带**。
> 生成日期：2026-09-14 · 扫描根：`上线网站.worktrees/agents-install-vscode-cline-deploy-strix`

## 文档

| 文件 | 内容 | 体量 |
|------|------|------|
| `CODE_ATLAS-backend-app.md` | 后端 1241 文件逐文件：路径/行数/说明/类函数/app 内依赖 | ~350KB |
| `code-atlas-backend-app.json` | 同上机器可读 | |
| `CODE_MAP-services-by-package.md` | services 按包功能地图 + core/models/api/tasks 抽样 | ~137KB |
| `CODE_ATLAS-relations-frontend.md` | 依赖枢纽、包级热点、admin 前端 566 文件按角色壳 | |
| `code-atlas-frontend-admin.json` | 前端文件机读 | |

## 架构连带（一图读懂）

```
                    ┌─────────────────────────────────────┐
                    │  main.py (lifespan 注册中间件/路由)  │
                    └─────────────────┬───────────────────┘
                                      │
     ┌────────────────────────────────┼────────────────────────────────┐
     ▼                                ▼                                ▼
 api/v1/*                      tasks/Celery                    APScheduler
 (157 routes + 子包)           (13 模块多队列)                 (ops/rank/geo…)
     │                                │                                │
     │ 645→core  404→models           │ 26→core                        │
     │ 104→hermes 89→ubrain           │ 12→deerflow                    │
     ▼                                ▼                                ▼
 ┌──────────────────────────────── services (739 py) ────────────────────────────────┐
 │  hermes(105) DAG/编排/专家     ubrain(83) 获客/外联/记忆      foreign_trade(44)     │
 │  cross_border(32) 翻译/配音    talking_stick(19)              geo(15)+geo_engine    │
 │  publish_workers+platforms     wangcai(8) 租户助手            deerflow(7)           │
 │  paperclip/browser_runtime     扁平根 270：订单/支付/AI引擎/SEO/代理/发布…          │
 └────────────────────────────────────────┬──────────────────────────────────────────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    ▼                     ▼                     ▼
              core (68)              models (94)            db/session
           config/security         ~229 表 ORM              get_db()
           jwt_cookie/tenant       user/tenant/content      RLS 可选
           response/cache          inquiry/payment/order
                    │
                    ▼
         PostgreSQL@5433 · Redis@6379 · n8n@5678 · MinIO/Qdrant
```

## 被依赖最多的枢纽（改这里要全站回归）

1. `core.database` (258) · `core.config` (235) · `models.user` (222)
2. `core.response` (198) · `core.security` (190) · `models.tenant` (159)
3. `db.session` (134) · `models.content` (92) · `core.cache` (84)

## services 包职责速查

| 包 | 作用 |
|----|------|
| **hermes** | 内部编排中枢：DAG、专家执行器、命令中心、运维自动驾驶、品牌守卫 |
| **ubrain** | 获客大脑：潜客、邮件外联、矩阵发布、租户记忆、Accio 销售 |
| **foreign_trade** | 外贸 OSINT/ICP/询盘/单证相关服务 |
| **cross_border** | 跨境语言桥：ASR/TTS/配音/翻译/出口报价 |
| **geo + geo_engine** | GEO 内容与排名监控 |
| **wangcai** | 租户前台智能助手（意图/知识/记忆/LLM 路由） |
| **deerflow** | 研报规划-执行-评审状态机 |
| **publish_workers / platforms / egress** | 发布 worker、平台能力、出站 IP/指纹 |
| **browser_runtime / n8n** | 无头浏览器取证、n8n 出站 |
| **paperclip** | 审批/编排类（orchestrator 被 api 高频引用） |
| **goodjob / deepseek_harness** | CRM 桥接 / 外层推理沙箱适配 |
| **扁平根 270** | 按前缀分主题：ai_ / client_ / order_ / payment_ / seo_ / agent_ … |

## API 面

- 入口：`/api/v1/*` 自动发现（`routes/auto_discovery.py`）
- BFF：`/api/v1/admin-bff/*` Cookie 鉴权
- 超管：`/api/v1/super-admin/*`
- 公开：`public_*` 路由（租户站、wangcai、forum）
- 业务热点路由：`hermes.py` `ubrain*.py` `unified_publish.py` `inquiries.py` `payment*.py` `crm_pipeline.py` `foreign_trade*.py`

## 前端 admin

- 566 vue/ts；壳：`views/login` · `views/client` · `views/admin` · `views/agent` · `views/partner` · `views/tenants`
- API 双轨：`utils/api.ts` Bearer + `api/admin-bff.ts` Cookie
- 设计真源：`stores/uiPreferences.ts` 薄荷 `#4a9b8c`

## 怎么用这套地图

1. 改功能前先查 `CODE_MAP-services-by-package.md` 有没有同职责包（防重复造轮子）
2. 改某文件依赖/被谁用 → 查 `CODE_ATLAS-backend-app.md` 对应行的「依赖(app)」
3. 动 core/database/security/models.user → 按枢纽列表全站回归
4. 前端页面属于哪个壳、调哪个 API → 查 `CODE_ATLAS-relations-frontend.md` §4
