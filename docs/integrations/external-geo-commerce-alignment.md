# 外部 GEO / 商务方案 · 与本仓库合拍对照表

> **签发**：PM-07 / 文档 Lane H  
> **日期**：2026-07-04  
> **用途**：评估 Medusa / Saleor / Spree、GEO Optimizer、Edge Middleware、Claude SEO Stack 时，**查部门归属、已有代码、短板、可借鉴项**；**不**作为换栈依据。  
> **诚实门禁**：数字可信度以 [`docs/admin-seo-geo-data-trust-map.md`](../admin-seo-geo-data-trust-map.md) 为准；禁止假交付见 `01-no-fake-delivery-hardgate.mdc`。

---

## 一、总原则（30 秒读完）

| 外部方案 | 与本项目关系 | 结论 |
|----------|--------------|------|
| Medusa / Saleor / Spree | 通用 Headless **商城** | **不学栈、不换核**；只借鉴多语言/多币种/URL 元数据 **模式** |
| GEO Optimizer Skill | AI 就绪度审计 + llms.txt | **最合拍**；作 CLI/MCP **外挂**，接入现有 SEO/GEO 脚本链 |
| Edge GEO Middleware | AI 爬虫分流 + 语义载荷 | **理念合拍**；在 **Nuxt Nitro** 实现，**不**迁 Next.js |
| Claude SEO/GEO Stack | 每周自动化工作流 | **编排合拍**；并入 **Ops 专家自治 + cert/smoke**，不整包迁入 |

**产品定位不变**：FastAPI 多租户外贸 SaaS · 询盘转化 · Nuxt L-Pro 租户站 — 不是 DTC 购物车中台。

---

## 二、最合拍部门（主责矩阵）

| 外部能力域 | 主责部门 / Lane | 协责 | 对应任务域 |
|------------|-----------------|------|------------|
| 租户站 SEO（title/meta/canonical/hreflang） | **前端 FE** · 租户 Nuxt | QA | 租户预览、L-Pro |
| 站点体检 / 技术 SEO | **后端 BE** + **MKT** Admin | QA | `/seo/site-audit` |
| GEO 模型探测 / 提及率 | **MKT** + **BE** | SaaS 验收 | `/admin/geo-engine` |
| llms.txt / AEO | **BE** SEO API + **FE** 静态发布 | MKT | `/seo/llms-txt` |
| 租户级 SEO/GEO 门禁脚本 | **QA** Lane F | BE/FE | `scripts/validate-tenant-*` |
| AI 爬虫 middleware | **ARCH** Lane A + **FE** Nuxt | BE | Nitro `server/` |
| 每周 SEO 闭环编排 | **PM** Lane H + Ops | MKT/QA | `docs/ops/*`、smoke |
| 多币种/购物车（若未来要做） | **ARCH** + **BE** sidecar | — | **非 R1**；仅模式参考 Medusa |

---

## 三、已有代码（本仓库 · 可直接续写）

### 3.1 SEO / 技术审计

| 能力 | 路径 | 说明 |
|------|------|------|
| 公网站点体检 API | `backend/app/api/v1/seo/site_audit.py` | Admin `/seo/site-audit` |
| 审计引擎 | `backend/app/services/site_audit.py` | 真抓 URL，禁内网 |
| Admin 页面 | `frontend/admin/src/views/seo/site-audit.vue` | 路由 `seo/site-audit` |
| **租户预览 SEO 审计** | `scripts/validate-tenant-seo-audit.py` | 本地 Nuxt + visitor-context |
| 一键运行 | `scripts/run-tenant-seo-audit.ps1` | 报告 `docs/tenant-seo-audit-latest.json` |
| dev 冒烟接入 | `scripts/smoke-gap-closure-dev.py` | gap-closure 链 |
| 租户 SEO Head | `frontend/composables/useTenantLProSeoHead.ts` | SSR title/meta/hreflang |
| 租户媒体 URL | `frontend/composables/useTenantMediaUrl.ts` | `/uploads` 代理 |
| Nuxt 代理 | `frontend/nuxt.config.ts` | `/api`、`/uploads` → `:8001` |
| 协作入口 | `AGENTS.md` § 租户预览 SEO 审计 | Cursor 可触发 |

### 3.2 GEO / AEO

| 能力 | 路径 | 说明 |
|------|------|------|
| 多模型 GEO 探测 | `backend/app/services/geo_engine_service.py` | DeepSeek/OpenAI/Gemini/Claude… |
| GEO 优化器（内容分） | `backend/app/geo_engine/geo_optimizer.py` | 可见性 0–100 启发式 |
| 引擎注册表 | `backend/app/services/geo/multi_engine_rank_registry.py` | Perplexity/Copilot 等「探索中」 |
| Admin GEO 台 | `frontend/admin/src/views/admin/geo-engine/index.vue` | 路由 `geo-engine` |
| llms.txt 生成 API | `backend/app/api/v1/seo/llms_txt.py` | POST `/generate` |
| DB 驱动 llms | `backend/app/api/v1/seo/llms_txt_generator.py` | GET `/llms.txt` |
| Admin llms 页 | `frontend/admin/src/views/seo/llms-txt.vue` | 路由 `seo/llms-txt` |
| 预生成脚本 | `scripts/pregenerate_llms_txt.py` | 写入 `frontend/public/llms.txt` |
| 数据可信度 | `docs/admin-seo-geo-data-trust-map.md` | 老板/验收必读 |
| GEO 战略备忘 | `docs/geo/GEO-GLOBAL-STRATEGY.md` | 全球模型清单（偏策略） |

### 3.3 租户站 / 外贸转化

| 能力 | 路径 | 说明 |
|------|------|------|
| 租户 bootstrap | `frontend/composables/useTenantSiteBootstrap.ts` | SSR API 绝对 URL |
| 语言 / 联系渠道 | `frontend/composables/useVisitorLocale.ts` | EN 隐藏微信/QQ |
| visitor-context API | `backend/app/api/v1/routes/public_visitor_context.py` | 气泡与渠道 |
| L-Pro 页面壳 | `frontend/components/tenant/premium/*` | 产品/首页/联系 |
| dev 种子与占位图 | `backend/scripts/ensure_dev_sqlite.py` | `uploads/dev/product-*.jpg` |

### 3.4 门禁 / 自动化（对标 Claude SEO Stack 的「周四审计」）

| 能力 | 路径 | 说明 |
|------|------|------|
| Admin cert:gate | `frontend/admin/scripts/run-certification-gate.mjs` | 含 `audit-page-stubs` |
| Ops 诚实门禁 | `scripts/validate-ops-honesty.py` | P0 假交付 |
| 专家站会 | `docs/ops/expert-standup-latest.json` | 9 Lane full_roster |

---

## 四、短板（2026-07-04 更新 · 已闭环 vs 仍待 Owner）

### ✅ 已闭环（GEO-T01～T05 / OPS-T01～T03）

| 项 | 落点 |
|----|------|
| 租户 llms.txt / llms-full | Nuxt 路由 + `public_tenant_geo` API |
| JSON-LD + AI 爬虫语义块 | `useTenantGeoJsonLd` + `ai-crawler` middleware |
| 统一 GEO 分 `unified-geo-v1` | `unified_geo_score_service` + Admin/租户看板 |
| Perplexity/Copilot 探针 | `ai_search_probe_service`（无 Key 则 honest not_configured） |
| 每周 SEO/GEO 闭环 | `run-weekly-seo-geo-loop.ps1` + cert:gate 租户审计 |
| 周一挖词 | `run-seo-keyword-discover.py` |
| 生产 llms 反代 | `deploy/nginx-prod.conf` |

### P1 — 仍待 Owner / 外部配置

| 短板 | 现状 | 下一步 |
|------|------|--------|
| **Perplexity/Bing Key** | 探针已接，未配置则不计分 | Owner 填 Key 后 overall 含 AI Search 分量 |
| **AI 引文追踪实盘** | `honest_stub` | 接 DeerFlow/Headless 后替换 citations |
| **公网 site-audit** | 本地租户审计已绿 | 上线域名后跑 Admin `/seo/site-audit` |

### P2 — 产品未立项（Out-of-Scope）

| 短板 | 说明 |
|------|------|
| Headless 商城 | B2B 询盘够用；DTC 需 sidecar 评估 |
| 关键词排名 mock 降级 | trust-map 已标 ⚠️；勿对外报排名 |
| geo-optimizer-skill MCP | 可选 dev sidecar；`run-geo-optimizer-audit.ps1` 已包装本地审计 |

### 不换栈（明确 Out-of-Scope）

- 用 Medusa / Saleor / Spree **替换** FastAPI 主后端或 Nuxt 租户前端  
- 为 GEO 单独 **迁移 Next.js 16 Edge**（保持 Nuxt 3 + Nitro）

---

## 五、要借鉴的部分（外部 → 本仓库落点）

### 5.1 GEO Optimizer Skill（Auriti-Labs/geo-optimizer-skill）— **优先**

| 借鉴项 | 落点部门 | 建议实现 |
|--------|----------|----------|
| 0–100 AI 可见性评分 | QA + BE | `scripts/validate-tenant-geo-audit.py` 消费 CLI/MCP JSON |
| 47 种 GEO 改法 / 段落级建议 | MKT + BE | 扩展 `geo_optimizer.py` 或 Admin 建议卡片数据源 |
| llms.txt + llms-full.txt 自动生成 | BE + FE | 租户域 API + Nuxt 路由 `/llms.txt`（按 `__tenant`） |
| MCP 服务端 | ARCH + PM | 可选 dev-stack sidecar；**不**进生产主路径除非有 Key |

### 5.2 Edge GEO Middleware（Next.js 思路 → Nuxt 实现）

| 借鉴项 | 落点部门 | 建议实现 |
|--------|----------|----------|
| UA 识别 GPTBot / ClaudeBot / PerplexityBot | FE + ARCH | `frontend/server/middleware/ai-crawler.ts` |
| 语义载荷 / Knowledge Graph 片段 | BE + FE | SSR 注入 JSON-LD `Product`/`Organization`/`FAQPage` |
| 双轨交付（人看 HTML / AI 看结构化） | FE Nuxt | routeRules + middleware 分支 |

### 5.3 Claude Code AI SEO & GEO Stack（工作流）

| 借鉴项 | 落点部门 | 建议实现 |
|--------|----------|----------|
| 周一挖词缺口 | MKT + BE | Deerflow / SEO 关键词 API 已有，加 cron 报告 |
| 周二内容生成 | MKT | `/publish/unified` GEO 发布台（**人审**） |
| 周三内链 | FE + PAGE | site-editor-lab / 模板内链规则 |
| 周四技术审计 | QA | `run-tenant-seo-audit.ps1` + `cert:gate` + gap-closure |
| MCP + GSC/GA4 | ARCH | 已有 gsc-ads webhook 验证脚本，扩展即可 |

### 5.4 Medusa / Saleor / Spree（仅模式，不引代码）

| 借鉴项 | 何时需要 | 本仓库对应 |
|--------|----------|------------|
| 多语言 / 多币种展示 | 已有 visitor-context + i18n | 继续 L-Pro / Admin 配置 |
| Headless + SSR SEO | 已是 Nuxt SSR | `useTenantLProSeoHead` |
| 清晰 SEO URL | 已有 slug 路由 | `tenantProductDetailPath` |
| 购物车 / 支付 / 订单中台 | **产品未立项** | 未来 sidecar，Lane ARCH 评估 |

---

## 六、推荐落地顺序（可进 PM 看板）

| 序 | 任务草案 ID | 内容 | 主责 | 状态 |
|----|-------------|------|------|------|
| 1 | **GEO-T01** | 租户 `/llms.txt` API + Nuxt 静态路由 | BE + FE | ✅ 2026-07-04 |
| 2 | **GEO-T02** | `validate-tenant-geo-audit.py`（JSON-LD、llms、AI 可读正文） | QA + BE | ✅ 2026-07-04 |
| 3 | **GEO-T03** | Nuxt AI 爬虫 middleware + JSON-LD 注入 | FE + ARCH | ✅ 2026-07-04 |
| 4 | **GEO-T04** | Perplexity/Copilot 探针（`ai_search_probe_service`） | BE | ✅ 2026-07-04 |
| 5 | **OPS-T01** | 每周 smoke：`run-weekly-seo-geo-loop.ps1` | PM + QA | ✅ 2026-07-04 |
| 6 | **GEO-T05** | 统一 GEO 分 + 租户/Admin 看板 | BE + FE | ✅ 2026-07-04 |
| 7 | **OPS-T02** | 周一挖词 `run-seo-keyword-discover.py` | MKT + BE | ✅ 2026-07-04 |
| 8 | **OPS-T03** | cert:gate 接入 tenant SEO/GEO 审计 | QA | ✅ 2026-07-04 |

---

## 七、快速索引

| 文档 | 用途 |
|------|------|
| [`docs/admin-seo-geo-data-trust-map.md`](../admin-seo-geo-data-trust-map.md) | 哪些数字能信 |
| [`docs/pm-swarm-parallel-charter.md`](../pm-swarm-parallel-charter.md) | Lane 边界 |
| [`AGENTS.md`](../../AGENTS.md) | 租户 SEO 审计入口 |
| [`docs/tenant-seo-audit-latest.json`](../tenant-seo-audit-latest.json) | 最近一次租户 SEO 报告 |

---

**Out-of-Scope**：本文不评价 GitHub 星标涨跌；不承诺接入第三方商业 API 费用；Medusa/Saleor/Spree 源码 **不** clone 进本仓库 `backend/` / `frontend/`。
