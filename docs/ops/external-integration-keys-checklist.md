# 外部能力凭证申请清单（Wave1 运营真源）

> 用途：主理人按表申请/填 Key；**未填时系统必须诚实 failed/not_configured，禁止假成功**。  
> 配置位置：开发仓库 `backend/.env` 与 `config/dev/.env` **成对改**（见仓库 AGENTS ENV-LOCK）。  
> 改完后重启后端（`scripts/start-dev-admin.ps1 -ForceRestart`），勿手敲裸 uvicorn。

---

## 1. 第三方登录 OAuth（唯一登录 `/login`）

| 能力 | 环境变量 | 申请入口（示意） | 未配置时行为 | 申请后验收 |
|------|----------|------------------|--------------|------------|
| QQ 互联 | `QQ_APP_ID` `QQ_APP_KEY` | https://connect.qq.com → 创建应用 → 回调 `OAUTH_REDIRECT_URI` | providers.qq=false；登录页 QQ 置灰「暂未开通」 | `GET /api/v1/auth/oauth/providers` 中 `qq:true`；authorize URL 指向 graph.qq.com（非 dev:） |
| 微信开放平台 | `WECHAT_OPEN_APP_ID` `WECHAT_OPEN_APP_SECRET` | https://open.weixin.qq.com → 网站应用 | providers.wechat=false | 同上 wechat:true |
| 飞书 | `FEISHU_APP_ID` `FEISHU_APP_SECRET` | https://open.feishu.cn → 企业自建应用 | providers.feishu=false | feishu:true |
| 钉钉 | `DINGTALK_APP_ID` `DINGTALK_APP_SECRET` | https://open-dev.dingtalk.com | providers.dingtalk=false | dingtalk:true |
| 回调地址 | `OAUTH_REDIRECT_URI` | 默认 `http://localhost:5173/login/oauth-callback`；生产改成正式域 | 回调不匹配会报 100010 | 第三方后台白名单一致 |
| 开发模拟 | `OAUTH_DEV_BYPASS` | 仅本地；**生产必须 false** | true 时可点模拟登录 | 生产响应不得出现 dev bypass 提示 |

**硬锁**：登录页只能是 `frontend/admin/src/views/login/index.vue` 路由 `/login`，禁止第二套登录。

---

## 2. 静态 IP 槽位 · 服务商采购（三轨计费第三轨）

| 能力 | 环境变量 | 说明 | 未配置时行为 | 申请后验收 |
|------|----------|------|--------------|------------|
| IPRoyal 长期 ISP | `IPROYAL_API_TOKEN`（必填）`IPROYAL_PLAN_ID` `IPROYAL_PRODUCT_ID` `IPROYAL_BATCH_SIZE` `IPROYAL_POOL_LOW_WATERMARK` `IPROYAL_AUTO_RENEW_DAYS` | https://iproyal.com → Reseller API | `active_provider=manual`；无自动下单；手工录入仍可用 | `/api/v1/egress/suppliers` 中 iproyal `has_token/ready=true`；`pool/replenish` 可下单 |
| ASocks 按量住宅 | `ASOCKS_API_KEY` 或 `ASOCKS_LIST_URL` | https://asocks.com | 不能 JIT 采购 | EGRESS_PROVIDER=asocks 时 request-slot 可开出 host |
| 启用供应商 | 供应商管理 UI 或 `egress/suppliers` activate | adapter: manual / iproyal / asocks | 激活 iproyal 无 token → 明确报错 | activate 成功且 endpoints 出现 provider=iproyal |
| QC 开关 | `EGRESS_QC_ENABLED` | 开通后探活 | false 则跳过 QC | 按运维策略 |

**当前实测**：`GET /api/v1/egress/suppliers` → `active_provider=manual`，属诚实手工模式，不是故障。

---

## 3. 海关数据（受限）

| 能力 | 环境变量 | 说明 | 未配置时行为 | 申请后验收 |
|------|----------|------|--------------|------------|
| 海关买家反查 Sidecar | `CUSTOMS_DATA_SPIDER_URL` `CUSTOMS_DATA_SPIDER_TOKEN` | 外部 CustomsDataSpider 服务；合规 restricted | `customs_data_spider.configured=false` `fallback=not_configured`；UI 不展示假买家 | `GET /api/v1/foreign-trade/integrations/sidecars/status` 中 healthy=true；buyer-research 返回 evidence_url |
| 出海参谋统计 | （内置矩阵） | `/trade-intel/customs-*` 为公开统计/规则试点 | 有数据也须 disclaimer，**不代表实时报关** | 对外话术不写「已接海关实时」 |

---

## 4. 其它 Sidecar / 集成（低优先）

| 能力 | 环境变量 | 未配置行为 |
|------|----------|------------|
| Headless 探索引擎 | （见 sidecars status url 字段） | `fallback=dev_stub` |
| 用户行为分析 | 同上 | dev_stub |
| LinkedIn 决策人 | 外部数据源 Token | 路由在；无源则诚实 failed |
| GoodJob 桥 | `GOODJOB_BASE_URL`（本地已有 5188/4188） | 未配 → goodjob_bridge_disabled |
| TradeAI | `TRADEAI_BASE_URL` + 进程 :8010 | 未起 → 执行器 honest failed；login 保持 410 |

---

## 5. 填完 Key 后建议命令

```powershell
powershell -File scripts/start-dev-admin.ps1 -ForceRestart
# OAuth
# GET /api/v1/auth/oauth/providers  → 对应 provider:true
# Egress
# GET /api/v1/egress/suppliers      → has_token:true
# 海关
# GET /api/v1/foreign-trade/integrations/sidecars/status
powershell -File scripts/verify-login-entry-lock.ps1
```

## 6. Wave2（有 Key 后）

1. OAuth 真登录 E2E（QQ/微信任选一端先通）  
2. IPRoyal 或 ASocks 自动开通一条槽位 → 绑定租户  
3. Customs sidecar 一单 buyer-research（须 evidence_url）  
4. 全程不打开附属独立登录；优丁唯一 `/login`
