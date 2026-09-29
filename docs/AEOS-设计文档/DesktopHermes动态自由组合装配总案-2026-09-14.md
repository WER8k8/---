# Desktop Hermes 动态自由组合与全域零件装配总案（最高架构设计法典）

> **文档性质**：优丁 YouDing B2B 外贸 Agent OS 最高施工与装配蓝图（终极交接版）  
> **制定时间**：2026-09-14 ｜ **执笔**：谷歌首席架构师 × 系统工程组  
> **适用对象**：全 IDE 通行（Claude 3.5 Sonnet / Codex / Cursor / Qoder / Windsurf / 人工研发团队）  
> **核心使命**：彻底终结“文档考古学”与“机械填坑”，给出最清晰的**全系统原子零件清单**，建立**“外层 Desktop Hermes（动态组合+意图分析+Skill插件）➔ 内层 Hermes 调度核心 ➔ 动态可变编排路线”**的世界级先进微内核架构，指导后续所有开发无缝实现与落地。

---

## 目录
- [0. 最高工程总则：必须搞清的“两大铁律”](#0-最高工程总则必须搞清的两大铁律)
  - [0.1 铁律一：摸透“代码库里有什么”（真实家底底盘）](#01-铁律一摸透代码库里有什么真实家底底盘)
  - [0.2 铁律二：每次写代码必须“先探后写”（Probe Before Write 操作法典）](#02-铁律二每次写代码必须先探后写probe-before-write-操作法典)
  - [0.3 先验探针工具箱（动代码前必须跑的 5 大命令）](#03-先验探针工具箱动代码前必须跑的-5-大命令)
  - [0.4 “先探后写”决策树与四步工法（探 ➔ 账 ➔ 定 ➔ 简）](#04-先探后写决策树与四步工法探--账--定--简)
  - [0.5 架构北极星：从“静态死流程”到“动态微内核”](#05-架构北极星从静态死流程到动态微内核)
- [1. 全域物理零件大底盘清单（系统的真实家底）](#1-全域物理零件大底盘清单系统的真实家底)
  - [1.1 执行层：24 个物理执行器（Executors）](#11-执行层24-个物理执行器executors)
  - [1.2 插件层：76 个业务 Skills 插件包](#12-插件层76-个业务-skills-插件包)
  - [1.3 专家层：319 个 AgencyZH 行业专家画像](#13-专家层319-个-agencyzh-行业专家画像)
  - [1.4 规约层：898 个 ECC 工业级 SOP 规范](#14-规约层898-个-ecc-工业级-sop-规范)
  - [1.5 渠道层：50 个海内外社媒/电商出站渠道](#15-渠道层50-个海内外社媒电商出站渠道)
  - [1.6 数据层：234 张 PostgreSQL 数据库表](#16-数据层234-张-postgresql-数据库表)
  - [1.7 展现层：双前端去向裁定（谷歌 SEO 唯一母体）](#17-展现层双前端去向裁定谷歌-seo-唯一母体)
  - [1.8 路由与服务层：150+ 路由模块与 677 个 Service 资产](#18-路由与服务层150-路由模块与-677-个-service-资产)
- [2. 三层解耦架构与动态自由组合机制](#2-三层解耦架构与动态自由组合机制)
  - [2.1 第一层：外层 Desktop Hermes（交互、意图解构与插件中枢）](#21-第一层外层-desktop-hermes交互意图解构与插件中枢)
  - [2.2 第二层：内层调度爱马仕 Hermes（状态机微内核）](#22-第二层内层调度爱马仕-hermes状态机微内核)
  - [2.3 第三层：可插拔执行路线（四大经典超级航道）](#23-第三层可插拔执行路线四大经典超级航道)
- [3. 给后续编程 IDE 的分步落地实操工法](#3-给后续编程-ide-的分步落地实操工法)
  - [3.1 第一步：底座门禁红线锁定（不可后退）](#31-第一步底座门禁红线锁定不可后退)
  - [3.2 第二步：动态 TaskGraph 合成器实现（替换写死模板）](#32-第二步动态-taskgraph-合成器实现替换写死模板)
  - [3.3 第三步：外部子系统真物理通信连通](#33-第三步外部子系统真物理通信连通)
  - [3.4 第四步：数据库 207 张空表“业务注水工程”](#34-第四步数据库-207-张空表业务注水工程)
  - [3.5 第五步：Nuxt 3 谷歌 SEO 终极视觉收敛](#35-第五步nuxt-3-谷歌-seo-终极视觉收敛)
- [4. 不可破坏的五大硬锁与架构契约](#4-不可破坏的五大硬锁与架构契约)

---

## 0. 最高工程总则：必须搞清的“两大铁律”

> **【致后续所有接手 IDE（Claude / Codex / Cursor / Windsurf / Qoder 等）】**：  
> 本项目不是一张白纸，而是一个已有 **45,350 个文件、234 张数据表、150+ 路由模块、677 个服务文件** 的工业级复杂外贸操作系统。  
> 过去很多 IDE 接手后，盲人摸象、凭空脑补、凭空手写，最终堆积了 **12 个割裂的编排引擎、49 个孤儿页面、11 个孤儿组件、207 张空表**。每一个技术债务的根源，都是因为**“不知道代码库里有什么，动代码前从来不探，直接盲写新文件”**。  
> **因此，本项目确立不可撼动的最高工程公理：两大铁律！**

---

### 0.1 铁律一：摸透“代码库里有什么”（真实家底底盘）

**在动任何一行代码之前，必须彻底看清代码库现存的真实资产，严禁凭空捏造、严禁重复造轮子！**

代码库里已经具备了全链路的原子零件（详见第 1 章）：
1. **执行层（24 个物理执行器）**：物理位于 `backend/app/services/hermes/executors/`，覆盖深研、建站、核价、单证、社媒、WhatsApp、出站、物流等 **52 项核心能力**；
2. **插件层（76 个业务 Skills）**：物理位于 `skills/`，含 22 参数建材精算、外贸开发信、海关数据、谈判博弈等完整 Prompt 与规约；
3. **专家层（319 个行业专家画像）**：物理位于 `_external/agency-agents-zh/`，具备细分外贸角色的系统级 Prompt 与行为规范；
4. **规约层（898 个工业级 SOP）**：物理位于 `_external/ecc/`，覆盖信用证、拼箱核算、PI 标准条款等 30 年外贸行业标准化操作规程；
5. **渠道层（50 个出站渠道矩阵）**：8 个真实通道（LIVE）+ 42 个接桩通道（STUB）；
6. **数据层（234 张 PostgreSQL 数据表）**：原生 PG 15.8 @5433 上完备的企业级领域模型（建站、订单、询盘、核价、海运、HS 编码、外贸履约、社媒养号等）；
7. **展现层（双前端架构）**：Nuxt 3（SSR 直出 + 12 语种 i18n + Schema 结构化数据，面向 Google SEO 唯一母体）+ Vite SPA 暖白高品质运行版；
8. **路由与服务层**：FastAPI 150+ 路由模块、677 个核心 Service、统一任务桥接器 `hermes_task_bridge.py`。

---

### 0.2 铁律二：每次写代码必须“先探后写”（Probe Before Write 操作法典）

**严禁任何 IDE “接到需求直接敲新代码”！每次写代码必须先探明存量，再根据实际探测结果编写极简代码。**

#### 0.2.1 为什么必须“先探后写”？
- **现实情况**：需求中的 95% 以上的能力，代码库里都已经存在对应的 Service、Model 或 Executor，只是缺少胶水连通或缺少参数传递。
- **违规后果**：如果不探测就盲写，就会新建第 2 个相同功能的 Service、新建第 2 个登录页、新建第 2 套数据表，把系统搞成割裂的千层饼。
- **法典要求**：**“一行代码能解决的事，绝不用第 2 行”**。先用探针探测到存量零件的位置，直接在既有零件上扩展、注入或微调，坚决不另起炉灶。

---

### 0.3 先验探针工具箱（动代码前必须执行的命令）

任何 IDE 在着手编写代码前，必须按顺序运行以下探针命令，获取第一手客观事实：

```bash
# -------------------------------------------------------------
# 探针 1：探物理运行环境与服务活体（绝不凭记忆猜测端口）
# -------------------------------------------------------------
python tools/probe.py
# 👉 必验：PG@5433 (真库)、Redis@6379 (真缓存)、8001 (FastAPI后端)、5173 (Admin后台)、3000 (官网)

# -------------------------------------------------------------
# 探针 2：探存量能力与路由（查当前系统已经能做什么，是否已串联）
# -------------------------------------------------------------
python tools/capability_ledger.py
# 👉 必验：150 路由模块 / 677 服务文件的串联状态，查看目标功能是否已有路由或已有 Service

# -------------------------------------------------------------
# 探针 3：探执行器白名单与调度契约（查 24 个执行器声明的能力）
# -------------------------------------------------------------
python tools/verify_executors.py
# 👉 必验：24/24 PASS，确认目标能力应该落在哪一个物理执行器中，绝不重复创建执行器

# -------------------------------------------------------------
# 探针 4：探数据库真实表结构与数据密度（绝不拍脑袋建新表）
# -------------------------------------------------------------
python tools/db_probe.py --tables          # 查库里 234 张表全貌，找现成表
python tools/db_probe.py --density         # 查哪些表有数据，哪些是 0 行空表
python tools/db_probe.py --drift           # 查 SQLAlchemy 模型与数据库表是否存在漂移

# -------------------------------------------------------------
# 探针 5：探系统架构红线与冒烟门禁（改动后必跑）
# -------------------------------------------------------------
python tools/smoke_orchestration.py        # 编排静态冒烟测试（防环、白名单）
cd 上线网站.worktrees/agents-install-vscode-cline-deploy-strix/backend
python scripts/orchestration_selfcheck.py  # 19 项架构全景门禁（100% 全绿才可交付）
```

---

### 0.4 “先探后写”四步工作法（Probe-Assess-Locate-WriteMinimal）

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 步骤 1：探存量与活体 (Probe)                                                │
│  · 跑 tools/probe.py 确认物理服务状态                                       │
│  · 跑 tools/capability_ledger.py 搜索需求关键词（如 "whatsapp", "pi", "boq"）│
│  · 跑 tools/db_probe.py 检查是否有现成数据表支撑                            │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ 得到事实清单：已有模块 A、缺少参数 B
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 步骤 2：对账本与定落点 (Assess & Locate)                                    │
│  · 判断：该能力属于哪一层？(Desktop外层 / Hermes内层 / 24执行器之一)        │
│  · 决策：禁止新建独立控制器/服务！只能在既有执行器/既有路由/既有模型上扩展   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ 确定最小改动文件与接口
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 步骤 3：极简编写与代码复用 (Write Minimal)                                   │
│  · 奉行“一行代码原则”：复用 99% 的既有基础设施，仅编写 1% 的胶水或业务分支  │
│  · 保持五大硬锁：单登录/四壳隔离/薄荷绿单真源/八大子系统/PG@5433           │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ 代码改动落盘
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 步骤 4：闭环门禁自检 (Verify & Gate Check)                                   │
│  · 必须跑：verify_executors.py + smoke_orchestration.py + selfcheck.py     │
│  · 只要有 1 项报错，严禁交付，必须当场闭环修复                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 0.5 架构北极星：从“静态死流程”到“动态微内核”

#### 0.5.1 核心公式
$$\mathbf{Desktop\ Hermes\ 外层\ (意图解构\ +\ Skill插件热插拔)\ \xrightarrow{\ 动态自由编译\ }\ 内层调度\ Hermes\ (DAG微内核)\ \xrightarrow{\ 受控总线\ }\ 【按需定制的任意可变路线】}$$

#### 0.5.2 核心思想转变
- **以往致命缺陷**：过去的 IDE 把系统看成几张写死的固定流程图（如“建站图”、“开发信图”）。客户一旦提出复合需求，系统立刻陷入死胡同；且产生大量未被调用的“代码孤岛”。
- **世界级解法**：
  1. **系统所有能力彻底原子化**：每一个能力（Scrape、BOQ Calc、PI Generate、WhatsApp Send、SEO Audit）都是一个标准可调用的“执行插座”；
  2. **意图动态组装**：外层通过自然语言意图，动态匹配 76 个 Skill，并实时编译出专属的 DAG 任务图；
  3. **内层受控调度**：内层 Hermes 充当高可靠操作系统内核，只负责防环、流转数据、安全审批、Saga 事务补偿与精准扣费。

---

## 1. 全域物理零件大底盘清单（系统的真实家底）

全系统源码 45,350 个文件，包含以下不可遗漏的核心零件：

### 1.1 执行层：24 个物理执行器（Executors）
物理位于 `backend/app/services/hermes/executors/`，全部已在 `__init__.py` 注册，是执行能力的物理终点：

| 执行器标识 | 声明能力 (Capabilities) | 承载物理业务 |
|---|---|---|
| `deerflow` | `research.deep_run`, `seo.optimize` | DeerFlow 9 意图深研与 EEAT 高质量文章引擎 |
| `trade_ai_agent` | `prospect.scrape`, `outreach.whatsapp`, `inbox.classify` | `_external/trade-ai-agent` 全网社媒雷达与 WhatsApp 矩阵 |
| `goodjob_crm` | `document.generate_pi`, `document.generate_trade_docs`, `crm.sync_stage` | `_external/goodjob-crm` 22参数核价、PI/CI/箱单套打与7步履约 |
| `site_builder` | `site.generate`, `site.build` | 智能建站与可视化组件装配 |
| `content` | `content.create` | 内容中台多语言文章与页面生成 |
| `publish` | `publish.multi`, `publish.single` | 全域分发总调度（8 真实发布器 + 42 平台桩） |
| `nurture` | `nurture.create`, `nurture.advance` | 社交媒体账号养号防封与轨迹记录 |
| `egress` | `egress.assign`, `egress.provision` | 多租户出站静态住宅 IP 与指纹环境分配 |
| `order` | `order.create`, `order.fulfill` | 真实跨境订单生成与状态推进 |
| `inquiry` | `inquiry.capture` | 全渠道询盘统一入库与捕获 |
| `billing` | `billing.meter` | 三轨商业计费（SaaS + Token + 静态IP槽位） |
| `accio` | `outreach.letter`, `prospect.enrich` | 买家画像丰富与高转化英文开发信生成 |
| `lead` | `lead.search`, `lead.score` | Geo 经纬度地理拓客与线索价值评分 |
| `seo` | `seo.rank` | 关键词排名监测与独立站 SEO 诊断 |
| `media` | `media.render` | 多媒体海报与短视频工厂渲染 |
| `browser` | `browser.scrape` | 真实浏览器无头抓取与合规取证 |
| `logistics` | `logistics.track` | 国际海运提单/集装箱物流轨迹追踪 |
| `ubrain` | `ubrain.chat` | 知识图谱向量检索与行业问答 |
| `wangcai` | `wangcai.ask` | 海关数据与外贸蓝海市场推理分析 |
| `forum` | `forum.post` | 海外行业垂直论坛（Reddit/Quora等）互动获客 |
| `engagement` | `engagement.send` | 私域会话即时发送与自动跟进 |
| `ai_engine` | `ai.chat`, `ai.reason` | 大模型直出与复杂商业逻辑多步推理 |
| `research` | `research.brief` | 行业与竞品情报快速简报生成 |

---

### 1.2 插件层：76 个业务 Skills 插件包
物理位于 `<worktree>/skills/`，通过 `backend/app/services/registry/skill_pack_loader.py` 动态扫描加载。每个技能包含独立的 `SKILL.md`，具备领域 Prompt 与规约：
- **市场研究类**：`customer-research`, `competitor-analysis`, `market-entry`, `prospecting`
- **出海营销类**：`cold-email`, `ai-seo`, `programmatic-seo`, `ads`, `marketing-loops`
- **外贸商务类**：`boq-calculator`（22参数建材精算）, `customs-lookup`, `sales-enablement`, `negotiation`
- **全自动插件热插拔**：用户或开发者只要在 `skills/` 下放入新的文件夹和 `SKILL.md`，系统无需重启即可动态热识别。

---

### 1.3 专家层：319 个 AgencyZH 行业专家画像
物理位于 `_external/agency-agents-zh/`：
- 涵盖外贸细分垂直角色的系统级 Prompt 与行为模式（阿语商务谈判专家、俄语报关精算师、欧美大型建材超市采购选品官、Google 独立站 SEO 架构师等）。
- 通过 `TaskNode.persona_ref` 传递并在执行器内部动态激活。

---

### 1.4 规约层：898 个 ECC 工业级 SOP 规范
物理位于 `_external/ecc/`：
- 沉淀了 30 年外贸行业标准化操作规程（信用证审核要点、国际海运集装箱拼箱计算公式、形式发票国际商会标准条款、反倾销税避税排查等）。
- 通过 `TaskNode.sop_ref` 注入大模型上下文，约束生成结果的专业度。

---

### 1.5 渠道层：50 个海内外社媒/电商出站渠道
记录于 `backend/app/services/platform_catalog.py` 与 `publish_workers/tier_router.py`：
- **8 个真发通道（LIVE）**：微信公众号、知乎、头条、YouTube (OAuth)、LinkedIn、Facebook、Instagram、X (Twitter)。
- **42 个待接桩平台（STUB）**：Reddit、WhatsApp、TikTok、Pinterest、Threads、Medium、Telegram、LINE，以及阿里巴巴国际站、Made-in-China、Amazon Seller、eBay 等。

---

### 1.6 数据层：234 张 PostgreSQL 数据库表
物理运行于原生 PostgreSQL 15.8 @5433（数据库 `youding_dev`，单 head 112）：
- **当前现状**：仅 27 张表有数据（8.5%），高达 **207 张表处于 0 行数据的空表孤岛状态**。
- **关键死表**：`customs_declarations`（报关单）、`hs_code_mappings`（海关编码）、`exchange_rate_logs`（汇率对冲）、`tenant_white_label_domains`（白标域名）、`social_account_nurture_traces`（养号轨迹）等，需要通过种子注水工程激活。

---

### 1.7 展现层：双前端去向裁定（谷歌 SEO 唯一母体）
- **核心判定结论**：**Nuxt 3（SSR 服务端直出 + 12 语种国际化 + JSON-LD Schema）是面向谷歌 SEO 的绝对唯一工业母体**。纯客户端 Vite SPA（首屏空 HTML）做海外独立站无法支撑快速收录。
- **视觉收敛方案**：以 worktree `frontend/`（Nuxt 3）为基准，将 `主要备份` Vite 运行版中的优质“暖米白 `#f5f4f0` + 砖橙 CTA”样式及组件代码回合入 Nuxt 3，兼顾顶尖的谷歌 SEO 表现与高品质企业站视觉。

---

### 1.8 路由与服务层：150+ 路由模块与 677 个 Service 资产
物理位于 `backend/app/api/v1/routes/` 与 `backend/app/services/`：
- **API 路由全景**：150 个路由模块，覆盖 `/api/v1/*` 下 1000+ API 端点（租户管理、站点生成、内容中台、多渠道分发、询盘处理、出站 IP 分配等）；
- **服务层资产**：677 个核心 Service 文件，封装了从 SEO 诊断、海运费精算、邮件发送、WhatsApp 对接、汇率获取到 PDF 生成的所有底层业务逻辑；
- **任务桥接中枢**：`backend/app/services/tasks/hermes_task_bridge.py` 充当 FastAPI 路由与 Hermes 调度器之间的标准粘合层；
- **先探铁律约束**：开发任何新接口前，必须先在 `routes/` 和 `services/` 中检索，禁止在没有检查既有路由的情况下新建平行路由模块！

---

## 2. 三层解耦架构与动态自由组合机制

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. 外层：Desktop Hermes (本地极速桌面端 / ACP stdio / 交互中枢)              │
│    ├─ 自然语言输入 ➔ 意图解构器 (提取行业、地区、产品规格、交付目标)         │
│    └─ Skill 插件动态选拔器 (从 76+ Skills 插件池中召回最匹配的领域包)       │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │ 输出定制化意图事件 IntentEvent
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. 内层：爱马仕 Hermes 调度核心 (微内核状态机 / DAG Governor)                │
│    ├─ 动态 TaskGraph 编译器 (将意图+Skill转化为可执行 DAG，自动推导依赖)     │
│    ├─ 数据总线 (JsonPath input_from：跨节点参数穿透 $.n1.output ➔ $.n2.input)│
│    ├─ 安全审批闸门 (wait_human：真实触达/扣费前挂起等待桌面端人工确认)      │
│    └─ 可靠性与计费 (Saga 逆向事务补偿 + Token Wallet 实时算力拦截)           │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │ 受控并发/串行派发任务
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 3. 编排执行路线 (Pluggable Pipelines · 自由插拔、按需定制)                   │
│    ├─ [路线 A：DeerFlow 深研内容]  ➔ 9 意图研报 ➔ 12 语种 EEAT ➔ Google 霸屏 │
│    ├─ [路线 B：TradeAI 全域拓客]   ➔ 社媒地图雷达 ➔ 买家清洗 ➔ WhatsApp 触达 │
│    ├─ [路线 C：GoodJob 履约单证]   ➔ 22参数核价 ➔ PI 形式发票套打 ➔ 箱单CI   │
│    └─ [路线 D：任意自由组合超导网] ➔ 根据业务意图，横跨上述系统自由组合      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.1 第一层：外层 Desktop Hermes（交互、意图解构与插件中枢）
- **通信中枢**：基于 `tools/youding_acp.py`（Agent Client Protocol），支持 JSON-RPC over stdio 与本地客户端通信。
- **意图解构器 (`IntentParser`)**：
  接收用户随意输入的自然语言需求，解析为标准化意图元组：
  ```json
  {
    "scene_type": "b2b_trade_lead_and_quote",
    "target_product": "rockwool_sandwich_panel",
    "target_country": "Saudi Arabia",
    "constraints": {"quantity": 5000, "unit": "sqm", "incoterms": "CIF Jeddah"},
    "required_actions": ["market_research", "lead_hunting", "boq_pricing", "pi_generation", "whatsapp_outreach"]
  }
  ```
- **Skill 插件动态选拔**：
  根据 `required_actions`，从 76 个 Skill 中动态选出最契合的技能（如 `customer-research`、`boq-calculator`、`cold-email`），提取其内部的指令规约作为 Prompt 上下文。

---

### 2.2 第二层：内层调度爱马仕 Hermes（状态机微内核）
- **动态 TaskGraph 编译**：
  根据外层解构出的动作序列，**在运行时动态实例化 `TaskGraph` 对象**，而非走死板写死的硬编码模板：
  - 自动注入上游到下游的依赖关系：`depends_on=["n1"]`；
  - 自动绑定数据流动总线：`input_from={"buyer_phone": "n1.output.whatsapp_number"}`；
  - 自动绑定行业角色与 SOP：`persona_ref="role:arabic_trade_officer"`, `sop_ref="ecc://pi_terms"`。
- **微内核核心治理**：
  1. **拓扑防环**：Kahn 算法实时检测，一旦检测到循环依赖立即报错；
  2. **并发与预算**：`max_parallel` 限制最大并发数，`budget_cap` 控制单个图的最大 Token 消耗；
  3. **审批门挂起**：涉及真发消息、真扣费的高危节点，状态变为 `wait_human`，推送给外层桌面端，等待用户点击“批准”后方可续跑；
  4. **Saga 事务补偿**：如果“PI 单证生成”失败，自动逆向触发“删除已建草稿”、“释放预扣信用额度”。

---

### 2.3 第三层：可插拔执行路线（四大经典超级航道）

#### 航道 A：DeerFlow 深度研报与全球独立站霸屏
- **触发意图**：产品上架、市场洞察、Google SEO 自然引流。
- **零件装配**：
  $$\mathbf{产品数据 \xrightarrow{} DeerFlow(9意图研报) \xrightarrow{} Content(12语种EEAT文章) \xrightarrow{} Nuxt3(SSR直出) \xrightarrow{} Publish(IndexNow毫秒推送)}$$

#### 航道 B：TradeAI 全域潜客雷达与 WhatsApp 私域破冰
- **触发意图**：寻找精准采购商、社媒主动获客、WhatsApp 批量触达。
- **零件装配**：
  $$\mathbf{关键词/地区 \xrightarrow{} TradeAI(地图/社媒抓取) \xrightarrow{} Lead(价值评分) \xrightarrow{} WhatsApp\ Bridge(真发触达) \xrightarrow{} TradeAI(收件箱意图分类)}$$

#### 航道 C：GoodJob 建材 22 参数工业核价与 7 步单证履约
- **触发意图**：买家询盘报价、海运排柜算价、生成正规 PI/CI/装箱单。
- **零件装配**：
  $$\mathbf{询盘捕获 \xrightarrow{} BOQ(22参数核价精算) \xrightarrow{} GoodJob(PI一键套打) \xrightarrow{} Billing(定金核销) \xrightarrow{} GoodJob(CI/箱单套打) \xrightarrow{} 物流追踪}$$

#### 航道 D：全流程自由复合超导网络（按需混合）
- **触发意图**：全自动端到端出海闭环。
- **零件装配**：
  $$\mathbf{DeerFlow(中东市场背调) \xrightarrow{} TradeAI(捕获利雅得买家) \xrightarrow{} BOQ(算好运费单价) \xrightarrow{} GoodJob(套打出英文PI) \xrightarrow{} WhatsApp(带单证触达)}$$

---

## 3. 给后续编程 IDE 的分步落地实操工法

后续任何接手的 IDE（Claude / Codex / Cursor 等），请直接按照以下五步进行代码落地，**无需推翻重来**：

### 3.1 第一步：底座门禁红线锁定（不可后退）
任何代码改动前后，必须保证以下三大门禁 100% 全绿：
```bash
# 1. 验证 24 个执行器全部合规且能力无冲突
python tools/verify_executors.py
# 2. 验证编排静态冒烟测试 100% PASS
python tools/smoke_orchestration.py
# 3. 验证架构全景 19 项门禁全绿
cd 上线网站.worktrees/agents-install-vscode-cline-deploy-strix/backend
python scripts/orchestration_selfcheck.py
```

---

### 3.2 第二步：动态 TaskGraph 合成器实现（替换写死模板）
- **核心文件**：`backend/app/services/hermes/planner_service.py`
- **实施要点**：
  1. 重构 `decompose()` 方法中的 `L2_llm` 与复合分支；
  2. 接入 `skill_pack_loader.py` 的技能检索接口：当用户提出非标准模板的需求时，根据用户关键词从 76 个 Skill 中动态检索候选技能；
  3. 将选中的技能规约、24 个执行器的输入输出契约组装为 System Prompt，要求 ModelGateway 产出标准的 `TaskGraph` JSON；
  4. 保证每个动态节点中，`depends_on` 依赖正确，`input_from` 的 JsonPath 穿透格式符合规范（如 `"email": "n1.output.email"`）；
  5. 必须跑过 `validate_graph(graph)` 的三道安全阀检验（执行器白名单、能力白名单、拓扑防环）。

---

### 3.3 第三步：外部子系统真物理通信连通
- **核心文件**：
  - `backend/app/services/hermes/executors/trade_ai_agent_executor.py`
  - `backend/app/services/hermes/executors/goodjob_crm_executor.py`
  - `backend/app/services/adapters/tradeai/`
  - `backend/app/services/goodjob/trade_document_bridge.py`
- **实施要点**：
  1. 在 `config/dev/.env` 中配置实际运行端口：
     - `TRADEAI_BASE_URL=http://127.0.0.1:8010`
     - `GOODJOB_BASE_URL=http://127.0.0.1:5188`
  2. 实现端到端真调用：当执行器被调度时，通过 `httpx.AsyncClient` 发送真实 HTTP 请求，将返回的线索数组或生成的 PDF 存盘路径回写到 `AiTask.output_json` 中；
  3. 若服务未启动或缺少凭据，**严禁伪造假数据（假邮箱/假状态）**，必须诚实返回 `status: failed` 并给出清晰排错日志（满足“交付求真”契约）。

---

### 3.4 第四步：数据库 207 张空表“业务注水工程”
- **核心文件**：`backend/seed.py` 与 `tools/seed_dev_users.py`
- **实施要点**：
  1. 为当前处于 0 行数据的 207 张关键外贸业务表注入真实测试种子：
     - 注入 100 条海运 HS 编码与关税映射数据（`hs_code_mappings`）；
     - 注入 20 款建材核心规格与 22 参数配载字典（`product_boq_profiles`）；
     - 注入多币种汇率快照（`exchange_rate_logs`）；
     - 注入外贸形式发票模板样式数据；
  2. 运行 `python tools/db_probe.py --density`，将有业务数据的表从 27 张提升至 60 张以上，确保全链任务图执行时不再因空表而产生逻辑断流。

---

### 3.5 第五步：Nuxt 3 谷歌 SEO 终极视觉收敛
- **核心目录**：`上线网站.worktrees/agents-install-vscode-cline-deploy-strix/frontend/`
- **实施要点**：
  1. **坚定保留 Nuxt 3 母体**：确保 `@nuxtjs/i18n` 12 语种矩阵、Nitro SSR 服务端直出、JSON-LD 结构化数据完好无损；
  2. **样式吸收**：从 `主要备份/上线网站/frontend` 中提取暖米白（`#f5f4f0`）底色、深黑主字（`#1c1917`）与砖橙 CTA（`#9a3412`）的设计令牌，替换 Nuxt 3 旧版的薄荷绿；
  3. **孤儿页面收口**：将 `pages/mobile/*` 等 21 个孤立移动端页面正式纳入主路由或封装为响应式视图，消除 49 个孤儿页面的技术债务。

---

## 4. 不可破坏的五大硬锁与架构契约

后续任何 IDE 在修改代码或编写新功能时，**严禁触犯以下硬锁**，否则属于高优先级违规：

1. **LOGIN-LOCK-01 唯一登录锁**：
   全站唯一登录路由必须是 `/login`，唯一登录组件必须是 `frontend/admin/src/views/login/index.vue`。禁止创建第二套登录入口或添加 `?portal=` 多门户分支。
2. **ROLE-SHELL-LOCK-01 角色壳隔离锁**：
   超管路由必须在 `/admin`，租户端在 `/client/*`，代理端在 `/agent/*`。严禁混合角色壳目录。
3. **DESIGN-TOKEN-LOCK-01 主色单真源锁**：
   管理后台与平台主色单真源为薄荷绿 `#4a9b8c`，官网对外视觉按暖米白与砖橙分层，禁止任意硬编码杂色，禁止恢复暗色模式。
4. **SYSTEM-LOCK-02 八大子系统法定不可裁减锁**：
   系统必须完整保留：① DeepSeek Harness ② Hermes 调度核心 ③ Site/Calc/BOQ ④ DeerFlow ⑤ Trade AI Agent ⑥ GoodJob CRM ⑦ 350+ 智能资产 ⑧ Browser Runtime/n8n。严禁在任何架构设计中遗漏或将任何子系统归入退役。
5. **ENV-LOCK-01 原生运行环境锁**：
   后端唯一真实数据源为原生 PostgreSQL 15.8 @5433（单 head 112）与 Redis 5.0 @6379，禁止回退到空 SQLite 掩盖迁移问题。

---

*（本法典由 Antigravity 谷歌首席架构师团队制定并封存，已实时同步至本地知识库，为优丁系统最高执行纲领）*
