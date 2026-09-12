# CODEX 执行规划 — 优丁 Global B2B AI Revenue Engine

> 生成日期：2026-08-28
> 基于三份规划文档 + 项目完成度盘点 + 现场代码核查
> 目标：把"网站开发完成"升级为完整的 B2B AI 获客与成交系统

---

## 一、规划文档源

| 文档 | 版本 | 核心内容 |
|------|------|----------|
| Global B2B AI Revenue Engine — Technical Spec | v1.0 | 24 章完整规格，含领域模型、API、MVP 验收、测试矩阵 |
| Overseas B2B Insulation — Codex Master Technical Spec | v2.0 | 55 章施工图，含 Product Finder 5 步流程、RFQ、Lead Scoring、SEO、GEO、ABM、Outbound |
| 海外工业保温防火建材 — AI B2B 获客与 Revenue Operating System | V3.0 | 46 章系统级规格，十层架构、获客矩阵、Phase 0-7 路线、BoQ AI |

**技术栈差异：** 三份文档写的是 Next.js + NestJS，实际当前代码是 **Nuxt 3 + FastAPI + PostgreSQL/Redis**。验收时按实际技术栈的合理等价物判断。

---

## 二、当前项目状态（已核实）

### 2.1 运行中的服务

| 服务 | 端口 | 源码目录 | 备注 |
|------|------|----------|------|
| 后端 API (FastAPI) | 8000 | worktree: `backend/` | 含 matching 引擎新路由 |
| 前端主站 (Nuxt 3) | 3000 | worktree: `frontend/` | 含 finder 页 |
| 超管后台 (Vite) | 5174 | 主要备份: `frontend/admin/` | |
| seo-admin (Vite) | 5173 | worktree: `seo-admin/` | |
| PostgreSQL | 5433 | Docker (pgvector/pg15) | |
| Redis | 6379 | Docker | |

### 2.2 两份代码副本关系

- **Live worktree:** `上线网站.worktrees/agents-install-vscode-cline-deploy-strix`（当前运行的后端+前端，匹配引擎最新）
- **Git 仓库:** `主要备份/上线网站`（branch `feature/revenue-engine-phase1`，3062 个未提交变更，路由文件更多但更新稍旧）
- **关系：** worktree 原本是 git worktree，但因父仓库被移入"主要备份"目录导致 git 指针断裂。两份副本的 matching 引擎代码已同步。

### 2.3 已实现模块（后端 126+ 路由模块）

✅ **产品系统：** products, product_categories, product_images, product_commerce, product_commercial, product_faqs
✅ **Product Finder 匹配引擎：** `matching.py` + `matching_engine/`（三层匹配：硬过滤→加权评分→证据解释，实测可用）
✅ **内容/CMS：** content, content_master, content_feedback, knowledge, knowledge_graph, knowledge_ingestion
✅ **SEO 基础：** seo_matrix, seo_diagnosis, sitemap, rank_check, baidu_webmaster, schema_markup
✅ **Analytics：** analytics, site_analytics, attribution
✅ **线索/询盘：** inquiries, inquiry_channels, lead_generation, lead_pipeline, lead_search, lead_enrichment, lead_tools, unified_lead, prospect_lead
✅ **用户/认证/租户：** users, auth, tenants, tenant_ai_config, merchant_profile
✅ **全球化/跨境：** globalization, cross_border, international, trade_intel
✅ **AI 助手：** agent_hub, agent_bff, chat_message, chat_session, ubrain* (Commercial OS/Accio/Decision)
✅ **基础知识库：** knowledge, knowledge_ingestion, vector_search, knowledge_graph
✅ **订单/支付：** order, order_item, payment（模型存在，数据待完善）
✅ **企业站点：** about, contact, solutions, products, applications, industry, news, cases

---

## 三、缺口分析（对照文档 Phase 1-2）

### 3.1 Phase 1 核心缺口（成交闭环 MVP）

| 模块 | 文档要求 | 当前状态 | 优先级 |
|------|----------|----------|--------|
| **RFQ 需求单** | 完整提交→持久化→评分→CRM→通知→Task | ❌ 完全缺失 | **P0** |
| **Calculator 计算器** | Thermal / Fire / Quantity 工具型获客 | ❌ 完全缺失 | **P0** |
| **CRM/Opportunity** | Lead → RFQ → Quote → Opportunity → Won | ❌ 完全缺失 | **P0** |
| **超管平台后台** | Dashboard / Products / Leads / RFQs / Quotes | ⚠️ 仅空壳登陆页 | **P1** |
| **Quote 报价** | 可与 RFQ 联动的报价系统 | ⚠️ 模型+基础路由存在，无数据无前端 | **P1** |
| **Company/Account 360** | B2B 买家公司主数据+活动+信号 | ⚠️ 部分存在（tenant/merchant_profile） | **P2** |

### 3.2 Phase 2 缺口（技术转化）

| 模块 | 文档要求 | 当前状态 | 优先级 |
|------|----------|----------|--------|
| **Product Finder 前端 5 步流程** | Application→Substrate→Performance→Environment→Commercial | ✅ 已完成（单页表单） | — |
| **匹配引擎三层算法** | 硬过滤→加权评分→解释 | ✅ 已完成 | — |
| **知识库 RAG** | 文档上传→解析→Embedding→检索→Grounded Answer | ⚠️ 部分（knowledge 路由存在，需补充 RAG 管道） | P2 |
| **AI 技术助手** | 基于批准资料的技术问答 | ⚠️ 部分（chat/agent 路由存在） | P2 |
| **Calculator 系统** | 热工/防火/数量计算器 | ❌ 缺失 | P0（与 Phase 1 合并） |

### 3.3 Phase 3-7 缺口（远期）

| 模块 | 文档要求 | 状态 |
|------|----------|------|
| Visitor/Company Intelligence | 匿名访客→公司识别→富化→Intent | ❌ 缺失 |
| Intent Engine | 信号加权→recency decay→Score→Action | ❌ 缺失 |
| Account Scoring | ICP + Intent + Project + Contact | ❌ 缺失 |
| Project Intelligence | 公开项目/招标抓取→解析→匹配 | ❌ 缺失 |
| Tender Monitoring | 招标采购信号监测 | ❌ 缺失 |
| ABM | Tier A/B/C 目标账户营销 | ❌ 缺失 |
| AI Outbound | Campaign→Sequence→Reply→Stop | ❌ 缺失 |
| GEO Visibility | AI 搜索可见性→Citation→Mention | ⚠️ 部分（geo_engine 存在） |
| AI Sales Agent | 技术问答→销售辅助→任务创建 | ❌ 缺失 |
| Revenue Attribution | First Touch→RFQ→Won ROI | ❌ 缺失 |

---

## 四、执行计划

### 启动单元 1：RFQ 系统（P0）

**目标：** 打通 Finder 匹配 → 提交 RFQ → 持久化 → CRM 线索的核心转化闭环。
**文档来源：** Technical Spec §6, Master Spec §12, V3 OS §21

| 步骤 | 内容 | 产出 |
|------|------|------|
| 1.1 | 创建 RFQ 数据库模型（rfqs, rfq_items, rfq_requirements, rfq_documents） | 4 张表 |
| 1.2 | 创建 RFQ API 路由（POST /rfq, GET /rfq/:id, GET /rfq, PUT /rfq/:id/status） | 4 个端点 |
| 1.3 | 实现 RFQ 校验+去重+产品关联+评分逻辑 | RFQ Score 0-100 |
| 1.4 | 创建 RFQ 前端提交页（继承 Finder 上下文，自动带入匹配产品） | `/request-quote` 页 |
| 1.5 | 创建 RFQ 管理后台（列表/详情/状态管理） | admin RFQ 模块 |
| 1.6 | 接入 Analytics 事件（rfq_start, rfq_submit） | 事件埋点 |
| 1.7 | 创建 RFQ → CRM Task 通知链路 | 销售任务创建 |

### 启动单元 2：Calculator 计算器（P0）

**目标：** 工具型获客入口，与 Finder/RFQ 联动。
**文档来源：** Master Spec §9, V3 OS §8

| 步骤 | 内容 | 产出 |
|------|------|------|
| 2.1 | 创建 Thermal Calculator（面积/厚度/材料→估算） | 后端路由 + 前端页 |
| 2.2 | 创建 Fire Protection Calculator（钢构件/截面系数/耐火→候选厚度） | 后端路由 + 前端页 |
| 2.3 | 创建 Quantity Calculator（面积/厚度/损耗→数量/包装） | 后端路由 + 前端页 |
| 2.4 | 所有计算器接入 Analytics | 事件埋点 |
| 2.5 | 计算器 → RFQ 联动（计算结果自动带入 RFQ） | 转化链路 |

### 启动单元 3：超管平台后台（P1）

**目标：** 从空壳 SaaS 营销页变为可管理 RFQ/Products/Leads 的功能后台。
**文档来源：** Master Spec §33, V3 OS §33

| 步骤 | 内容 | 产出 |
|------|------|------|
| 3.1 | Dashboard（Pipeline 漏斗 / High Intent / RFQs / Tasks） | 管理仪表盘 |
| 3.2 | RFQ 管理（列表/详情/状态流转/评分） | RFQ 管理页 |
| 3.3 | Products 管理（完整度/文档关联） | 产品管理增强 |
| 3.4 | Leads 管理（队列/评分/Next Action） | 线索管理页 |
| 3.5 | Quotes 管理（报价列表/审批/版本） | 报价管理页 |

### 启动单元 4：CRM/Opportunity 模块（P1）

**目标：** Lead → RFQ → Quote → Opportunity → Won 完整销售管道。
**文档来源：** Technical Spec §6, Master Spec §13, 42

| 步骤 | 内容 | 产出 |
|------|------|------|
| 4.1 | 创建 Opportunity 模型（opportunities, opportunity_stages） | 2 张表 |
| 4.2 | 创建 Campaign 模型（campaigns, campaign_steps, campaign_recipients, campaign_events） | 4 张表 |
| 4.3 | 创建 Opportunity API 路由 | CRUD 端点 |
| 4.4 | 前端 Opportunity Board（看板视图） | 销售管道看板 |
| 4.5 | Lead Scoring 配置化（权重/阈值/衰减函数进 DB） | 配置化评分 |
| 4.6 | RFQ → Opportunity 自动流转 | 自动化规则 |

### 后续启动单元（Phase 2-3 预研）

| 单元 | 依赖 | 说明 |
|------|------|------|
| Company/Visitor Intelligence | 需要第三方数据源集成 | Phase 2 |
| Knowledge RAG 管道 | RFQ 闭环后 | Phase 2 |
| AI 技术助手 | RAG 就绪后 | Phase 2 |
| Intent Engine | Analytics 数据积累后 | Phase 3 |
| Project Intelligence | 爬虫基础设施 | Phase 4 |
| ABM | Project 数据就绪 | Phase 4 |
| AI Outbound | Email 基础设施 | Phase 5 |
| GEO Visibility | 内容基础就绪 | Phase 6 |

---

## 五、技术架构要点

### 5.1 路由注册模式

当前后端采用两层路由注册：
1. **手动注册**：`routes/__init__.py` 中显式 `include_router`（matching 等关键路由）
2. **自动发现**：`_auto_discover_routes()` 扫描 `routes/` 目录（新模块自动注册）

新增模块只需在 `routes/` 下创建 `.py` 文件，含 `router = APIRouter()`，即可自动注册。

### 5.2 匹配引擎复用

matching 引擎位于 `backend/app/services/matching_engine/`，包含：
- `schemas.py` — Pydantic 请求/响应模型
- `engine.py` — 纯函数引擎（8 维加权评分 + 硬条件过滤 + 证据生成）

### 5.3 已有询盘模型的复用

现有的 `Inquiry` 模型（`app/models/inquiry.py`）是 RFQ 的最近邻模式，可参考其 UUID 主键、status 状态机、`assigned_to` 分配机制。但 RFQ 需要更丰富的结构化字段，建议新建独立模型而非扩展 Inquiry。

---

## 六、Definition of Done（每个启动单元）

- [ ] 数据库 migration 完整
- [ ] API schema/validation 完整
- [ ] Desktop + mobile 响应式 UI
- [ ] Loading / Empty / Error / Partial 状态完整
- [ ] 权限与审计完整
- [ ] Analytics 事件接入
- [ ] Unit / Integration 测试通过
- [ ] 无假技术数据、假认证、假项目
- [ ] 文档同步
- [ ] 核心流程可从前台跑到 CRM

---

## 七、MVP 验收标准（Technical Spec §21）

1. ✅ 访客可以浏览产品
2. ✅ 可以使用 Product Finder
3. ✅ 推荐结果遵守硬技术条件（不编造数据）
4. ❌ 可以创建 RFQ
5. ❌ RFQ 写入 CRM
6. ❌ Lead 自动评分
7. ❌ 销售收到通知
8. ✅ 产品技术文件可检索
9. ⚠️ AI 技术助手只能基于批准知识库回答（部分）
10. ✅ 页面服务端可渲染
11. ✅ Product 页面具备 SEO Metadata
12. ✅ Sitemap 可用
13. ✅ Analytics Events 正常
14. ✅ Admin 可管理 Products
15. ✅ Admin 可管理 Leads
16. ❌ Admin 可查看 RFQ
17. ✅ 关键操作有 Audit Log

**MVP 完成判定：** 15/17 项通过（第 4、5、6、7、16 项需 RFQ + CRM 实现）

---

## 八、风险与注意事项

1. **技术栈差异：** 文档目标是 Next.js+NestJS，实际是 Nuxt 3+FastAPI。差异本身不构成问题，但验收时需按实际技术栈合理判断。
2. **两份代码副本：** 当前 worktree 和 主要备份 代码不一致（工作树 126 路由 vs 备份 167 路由）。建议在备份 git repo 上创建新分支，将 worktree 匹配引擎代码合并，然后切换回 git repo 作为统一开发目标。
3. **npm 依赖：** 前端为 Nuxt 3，依赖 npm registry。如果沙箱环境网络受限，需提前解决 npm 源问题。
4. **确定性优先：** 所有技术匹配、价格计算、产品 Eligibility 必须使用确定性工程规则，LLM 不得覆盖硬条件。
5. **数据真实性：** 禁止编造认证、测试结果、价格、规格或项目事实。所有外部数据必须保存 source/sourceUrl/retrievedAt/confidence。
