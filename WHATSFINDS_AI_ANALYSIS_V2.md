# WhatsFinds AI 完整体验分析与 YouDing 优化吸收清单 · V2 升级版

> 基于官网 https://whatsfinds.com/ 与系统内部结构探索（账号：lvbowang88@gmail.com / 未授权）
> 原始探索时间：2026-07-20 ｜ V2 校准时间：2026-07-20
>
> **V2 升级要点**：在 V1 基础上，对 YouDing 现有代码库（`backend/app/models/*`、`backend/app/services/hermes/agency/*`、`frontend/admin/src/composables/*`）做了实测校准，修正了 V1 把"已存在能力"误判为"需新建"的关键偏差，并补齐了执行摘要、成功指标、优先级矩阵、实施路线图、MVP 定义、ROI 分析、风险登记册，以及每个优化项的验收标准 / 风险回滚 / 依赖关系 / 价值评分。

---

## 0. V2 升级说明

V1 是一份高质量的"竞品体验观察 + 吸收建议"，但在"落地路径"上存在一个系统性偏差：**大量被建议"新建"的模型 / 服务 / 组件，在 YouDing 代码库中其实已经存在或已有雏形**。V2 做了三件事：

1. **代码现状校准**（第八章）—— 逐项核对 V1 的"新建"建议与真实代码，把"从 0 建"改写为"扩展 / 接线 / 复用"，工时与风险随之大幅下调。
2. **补齐决策层缺失**—— 执行摘要、优先级矩阵、成功 KPI、4 周路线图、MVP 定义、ROI、风险登记册，让这份文档能直接进排期会。
3. **每个优化项结构化**—— P0/P1/P2 每条新增：现状校准、验收标准、风险与回滚、依赖关系、价值评分（1-5）、建议负责人。

> **一句话结论**：YouDing 不是"缺能力"，而是"已有能力没接成 WhatsFinds 那样的执行闭环"。V2 的工作重心从"造轮子"调整为"接线 + 闭环 + 体验层打磨"。

---

## 执行摘要（TL;DR）

| # | 关键判断 | 依据 |
|---|----------|------|
| 1 | **V1 高估了缺口**。`ProspectLead`、`EmailOutreach`（含像素/打开/点击/退订全字段）、`License`（含 `hardware_id` 设备指纹）、`AIModelProvider`/`AIModelConfig`、`ab_test` 模型均已存在 | `backend/app/models/` 实测 |
| 2 | **Agent 编排基础设施已具备**。`hermes/agency/` 已有 YAML DAG 引擎（`workflow_runner.py` + `role_loader` + `llm_router` + `provider_setup`）和 25+ 工作流 YAML，"Agent 化重构 Hermes"应是"在现有引擎上新增 4 个 outbound 工作流"，而非从零搭建 | `backend/app/services/hermes/agency/` 实测 |
| 3 | **真正缺口集中在三处**：① 用户级（tenant 级）AI Provider 配置 + 测试连接（现有 `AIModelProvider` 是全局唯一，无 tenant 隔离）；② 追踪像素/回复 webhook 的**路由端点与服务层**（模型已有，路由未挂）；③ 执行层单页聚合（搜→画→写→追一体化工作台） | 路由层与前端页面层核对 |
| 4 | **MVP 可压缩到 2 周**：P0-1/2/3/4/5 全部是"接线 + 组件"，不涉及新模型迁移，预计 8-10 人日即可让"WhatsFinds 式工作台"跑通最小闭环 | 见第十二章 MVP 定义 |

---

## 一、产品定位与核心差异化

### 1.1 定位标语对比
| 维度 | WhatsFinds AI | YouDing (优丁) |
|------|--------------|----------------|
| **核心定位** | 外贸 AI 销售工作台 / AI Outbound Workspace | 中国建材企业出海 B2B SaaS / GEO+SEO 内容获客 |
| **核心承诺** | "一套外贸开发工作流，而不是一个名单下载器" | "16项能力：GEO雷达+SEO矩阵+询盘归因+AI谈判" |
| **目标用户** | 外贸开发团队（SOHO/小团队/中型外贸公司） | 建材/制造企业出海决策者+运营团队 |
| **数据理念** | **用户自带 Key/模型/邮箱，数据完全自有** | 平台托管，多租户隔离，跨租户行业学习 |

### 1.2 核心差异化矩阵

| 能力象限 | WhatsFinds 强项 | YouDing 强项 | 互补机会 |
|----------|----------------|--------------|----------|
| **搜客数据源** | 公开网页搜索 + 用户自带 Serper Key | GEO雷达(22源) + SEO矩阵(2800县×关键词) | 你的GEO数据可做他的"高质量种子源" |
| **客户画像** | 官网摘要+联系人+邮箱可信度+证据链 | 询盘归因(6字段)+Schema双语+12语言hreflang | 你的Schema/多语言能力可强化他的画像 |
| **AI写信** | 用户自带模型+画像注入+企业优势库 | GEO写作策略v3(13战术)+低分重写3次 | 你的策略库可做他的"写信Agent"预设 |
| **触达渠道** | 邮件(SMTP/IMAP)+打开追踪 | 企微推送+询盘自动创建+邮件回复自动谈判 | 你的企微/IM集成可补他的触达短板 |
| **工作流** | 4步线性流：搜→画→写→追 | 全链路：获客→归因→内容→询盘→谈判→复盘 | 你的Hermes编排器可托管他的Agent |
| **数据所有权** | **完全用户自有**（Key/模型/邮箱/数据） | 平台托管+跨租户学习 | 你可提供"私有化部署+数据隔离"版本 |

### 1.3 定位 2×2 矩阵（NEW）

```
                        执行闭环强 ↑
                                   │
                 WhatsFinds        │
              (工作台/Agent化)      │
                                   │
  数据深度弱 ←─────────────────────┼─────────────────────→ 数据深度强
                                   │              YouDing
                                   │         (GEO/SEO/归因/多租户)
                                   │
                        执行闭环弱 ↓
```

> 两家分别在"执行闭环"与"数据深度"两个轴上各占一极，**融合 = 把 YouDing 的数据深度灌进 WhatsFinds 式的执行闭环**。

### 1.4 竞争护城河深度拆解（NEW）

| 护城河类型 | WhatsFinds | YouDing | 融合后强度 |
|-----------|------------|---------|-----------|
| **数据网络效应** | 弱（单租户自有数据） | 中（跨租户行业学习） | **强**（GEO 种子源 + 跨租户学习 + 执行回流） |
| **切换成本** | 中（用户自带 Key，迁移成本低） | 高（多语言站点 + Schema + 归因历史） | **极高** |
| **技术栈深度** | 中（搜/画/写/追四件套） | 高（22 源雷达 + 2800 县矩阵 + 13 战术 + Hermes DAG） | **极高** |
| **体验闭环** | 高（4 步线性工作台） | 中（能力分散在多个路由） | **高** |
| **定价权** | 中（半年 499 / 年 799） | 待定 | — |

---

## 二、获客逻辑全链路设计（WhatsFinds 核心）

### 2.1 四阶段线性工作流

```
┌─────────────────────────────────────────────────────────────────────┐
│                    WHATSFINDS AI OUTBOUND WORKFLOW                   │
├──────────────┬──────────────┬──────────────┬────────────────────────┤
│   01 搜客     │   02 画像    │   03 写信    │   04 追踪              │
│  (Search)    │  (Profile)   │  (Write)     │  (Track)               │
├──────────────┼──────────────┼──────────────┼────────────────────────┤
│ 输入:         │ 输入:         │ 输入:         │ 输入:                  │
│ - 产品词      │ - 搜客结果    │ - 客户画像    │ - 发送记录             │
│ - 目标市场    │ - 官网内容    │ - 企业优势库  │ - 打开/点击/回复       │
│ - 客户类型    │ - 公开联系人  │ - 历史高转模版 │ - 回复内容             │
│ - Serper Key  │ - 邮箱可信度  │ - 模型配置    │ - 追踪像素             │
├──────────────┼──────────────┼──────────────┼────────────────────────┤
│ 执行:         │ 执行:         │ 执行:         │ 执行:                  │
│ - 拆解搜索意图│ - 官网爬取摘要 │ - 模型生成草稿 │ - 像素嵌入             │
│ - 组合语法    │ - 联系人提取  │ - 变量注入    │ - 实时回调             │
│ - 过滤低价值  │ - 邮箱验证    │ - 多版本A/B   │ - 回复分类             │
│ - 去重域名    │ - 匹配度评分  │ - 人工审核/直发 │ - 复盘报表             │
├──────────────┼──────────────┼──────────────┼────────────────────────┤
│ 产出:         │ 产出:         │ 产出:         │ 产出:                  │
│ - 候选名单    │ - 结构化档案  │ - 发信任务    │ - 打开率/点击率/回复率 │
│ - 搜索语法    │ - 优先级分数  │ - 发送日志    │ - 高意向线索           │
│ - 原始证据链  │ - 证据引用    │ - 版本历史    │ - 复盘建议             │
└──────────────┴──────────────┴──────────────┴────────────────────────┘
```

### 2.2 搜客 Agent 设计细节（可直接吸收）

| 环节 | WhatsFinds 做法 | YouDing 吸收建议 | V2 现状校准 |
|------|----------------|------------------|------------|
| **意图拆解** | 产品词→市场→客户类型→自动组合语法 | 在 `auto_discovery.py` / `search_strategy.py` 加入 `IntentPlanner` Agent | `auto_discovery.py` 路由已存在，需补意图拆解逻辑 |
| **Key隔离** | 每用户自带 Serper Key，额度透明 | 新增 `user_serper_key` 字段，搜索服务读取用户级配置 | **缺口属实**：现有 AI Provider 是全局级，需加 tenant 级 |
| **平台过滤** | 自动过滤低价值平台、零售、重复域名 | 复用 `seo_diagnosis.py` 的 `domain_quality_scorer` | `seo_diagnosis.py` 存在，可复用 |
| **证据保留** | 每条线索保留原始搜索语法+快照+来源页 | 在 `ProspectLead` 模型加 `evidence_chain` JSON 字段 | `ProspectLead` 已存在，有 `source_detail` JSON；**需新增 `evidence_chain` 列** |
| **去重策略** | 域名级去重 + 公司名模糊匹配 | 复用 `lead_enrichment.py` 的 `dedupe_by_domain_and_name` | `lead_enrichment.py` 存在；`ProspectLead` 已有 `domain` + `company_name_normalized` 索引，去重基础已具备 |

### 2.3 画像 Agent 设计细节

| 字段 | 数据来源 | 评分权重 | YouDing 对应能力 | V2 现状校准 |
|------|----------|----------|------------------|------------|
| **官网摘要** | 爬取首页/About/Products | 25% | `site_content_array_i18n` 已有多语言内容 | 已具备 |
| **联系人提取** | 官网Contact/Team页 + LinkedIn公开 | 20% | 需新增 `contact_extractor` 服务 | 缺口属实 |
| **邮箱可信度** | 格式验证 + MX记录 + 历史送达 | 25% | 复用 `email_validator` + 新增 `mx_checker` | `ProspectLead.email_verified` 已有（valid/invalid/unknown/risky）；**缺 MX + 子维度拆分** |
| **匹配度评分** | 产品词覆盖 + 行业关键词 + 地理 | 30% | 直接用 `unified_geo_score_service` 逻辑 | `unified_geo_score_service.py` 存在；`ProspectLead` 已有 `fit_score`/`engagement_score`/`overall_score` 三档分 |

> **关键洞察（V2 修正）**：WhatsFinds 的画像评分 = **GEO 评分的简化版**。YouDing 的 `ProspectLead` 已有 `fit_score`/`engagement_score`/`overall_score` 三档分，比 V1 推断的更完整。真正要做的是把 `overall_score` **拆解为可解释的 4 子分**（匹配度/邮箱可信/证据强度/联系人完整度）并在前端雷达图展示，而非从 0 建评分。

### 2.4 写信 Agent 设计细节

```python
# WhatsFinds 的提示词结构（从官网推断）
WRITE_EMAIL_PROMPT = """
角色：资深外贸开发信专家
输入：
1. 客户画像：{company_summary, key_contacts, industry, buying_signals, evidence_chain}
2. 企业优势库：{product_advantages, certifications, case_studies, price_flexibility}
3. 历史高转模版：{top_performing_templates}
4. 发信约束：{tone, length, language, cta_type}

输出：主题行 + 正文（含变量占位）+ 备选版本 A/B
约束：不编造证据，引用画像中的具体证据编号 [E1][E2]
"""
```

**YouDing 优势**：你的 `GEO写作策略v3` 有 13 个战术（权威引用、数据支撑、反向链接诱饵等），可直接封装为 `EmailTacticLibrary` 供 Agent 调用。

**V2 现状校准**：`ai_template.py`（模板）、`ab_test.py`（A/B 测试）、`case_study.py`（案例库）模型均已存在。写信 Agent 的"企业优势库"可复用 `case_study` + `ai_knowledge`；A/B 并行编辑可复用 `ab_test` 模型。缺口在"变量注入编辑器 + 预览"前端组件。

### 2.5 追踪 Agent 设计细节

| 能力 | 实现方式 | YouDing 现状（V1） | V2 现状校准 | 补齐建议 |
|------|----------|--------------|----------|----------|
| **打开追踪** | 1px 像素 + 唯一 ID | 无 | **`EmailOutreach.tracking_pixel_id` + `open_count` + `first/last_opened_at` 已存在** | 只需补像素路由端点 `/tracking/pixel/{id}` |
| **点击追踪** | 重定向链接 + UTM | 无 | **`EmailOutreach.tracking_links` JSON + `click_count` + `first/last_clicked_at` 已存在** | 只需补点击重定向路由 |
| **回复抓取** | IMAP 轮询 + Webhook | 企微推送已有 | 缺口属实 | 新增 `email_reply_webhook` 解析线程 |
| **意向分类** | LLM 分类：询价/拒绝/要求资料/其他 | 无 | `inquiry.py` + `inquiry_channels.py` 分类逻辑可复用 | 接入 `inquiry_channels` 分类 |
| **复盘报表** | 按模版/客户类型/发送时间聚合 | 归因报表已有 | `attribution_service.py` 可复用 | 新增 `email_campaign_analytics` 视图 |

> **V2 重大修正**：V1 把追踪能力列为"无"，实际 `EmailOutreach` 模型已内置完整追踪字段（像素 ID、链接 JSON、打开/点击计数与时戳、退信类型）。**P1-3 从"建追踪服务"降级为"挂路由端点 + 接 webhook"**，工时从 5d 降至 ~2d。

### 2.6 Agent 接口契约规范（NEW）

为了让 4 个 Agent 可在 `hermes/agency/` 现有 DAG 引擎上运行，建议统一契约：

```python
# backend/app/services/hermes/agency/agent_protocol.py（建议新增）
from typing import Protocol, Any

class OutboundAgent(Protocol):
    """统一 4 Agent 契约，复用 workflow_runner 的 YAML DAG 调度。"""
    agent_id: str          # search / profile / write / track
    required_inputs: list[str]
    produced_outputs: list[str]

    async def run(self, ctx: "OutboundContext") -> "AgentResult": ...
    async def dry_run(self, ctx: "OutboundContext") -> "AgentPlan": ...  # 预览不执行
    def estimate_cost(self, ctx: "OutboundContext") -> dict: ...          # Key/模型额度预估
```

> 复用现有 `agency/llm_router.py`（已支持多模型路由）+ `provider_setup.py`，即可天然支持"用户自带模型"。

### 2.7 数据流架构（NEW）

```
[用户配置层]                      [执行层 4 Agent]                    [数据层]
 tenant_ai_provider ──┐         ┌── SearchAgent ──→ ProspectLead(+evidence_chain)
 user_serper_key      ├──→ DAG ─┼── ProfileAgent ─→ ProspectLead(子分+雷达)
 smtp/imap_credential │  引擎   ├── WriteAgent ───→ EmailOutreach(+ab_test)
                      │         └── TrackAgent ───→ EmailOutreach(打开/点击/回复)
                      │                              ↓
                      └──────────────────────→ inquiry(意向分类)
                                                    ↓
                                            attribution_service(复盘)
```

---

## 三、网页设计与交互体验

### 3.1 官网信息架构（单页式销售漏斗）

```
Hero: "让外贸开发进入 AI 销售工作流" + 两个CTA(进入系统/申请体验)
├── LIVE WORKFLOW 预览（4步可视化流程图）
├── BUYER SIGNALS（核心价值：从产品词找买家，非名单下载器）
├── OPERATING SYSTEM（工作流而非工具：4步详细说明）
├── YOUR STACK, YOUR DATA（三大自主权：Key/模型/邮箱 + 云端保存）
├── AI SALES TEAM（4个Agent职责可视化）
└── EARLY ACCESS（申请授权→进入系统）
```

**设计亮点可吸收**：
- **流程可视化优先**：Hero 下方直接放 4 步工作流图标，用户 3 秒懂核心价值
- **证据前置**："官网证据、邮箱可信度、联系人线索和市场匹配度合并评分" — 把评分维度显性化
- **自主权三件套** 用卡片并列：自带 Key / 自带模型 / 自带邮箱 — 极强信任信号
- **Agent 拟人化**：搜客/画像/写信/跟进 四个 Agent 各自编号，降低认知负荷

### 3.2 系统内部 UI 结构（从导航推断）

#### 左侧主导航（图标+文字，分组折叠）
```
⌂ 概览
客户开发
  ⌕ 潜在客户搜索    ← 核心入口
  ▦ 客户列表
  ◉ 客户画像
  ⇄ 商机推进
邮件营销
  ✉ 发送任务
  ✎ AI 写邮件
系统中心
  ⚙ 设置
  ? 帮助中心
  ! 更新公告 NEW
  ◇ 授权
```

#### 顶部面包屑 + Tab 栏（关键交互）
```
WhatsFinds AI ▸ 潜客任务 ▽    线索管理与开发 ▽    系统中心 ▽    ◐ 暗色模式
┌─────────────────────────────────────────────────────────────┐
│ 控制台  |  授权管理 ×  |  潜在客户搜索  |  客户列表  |  发送任务  │  ← 多标签页，可关闭
└─────────────────────────────────────────────────────────────┘
```

**可直接迁移到 YouDing（V2 校准）**：
1. **多标签页任务栏** — `useWorkTabNavigation.ts` + `useModuleTabSync.ts` + `useShellNavigation.ts` **均已存在**，补齐"可关闭/状态保持"与 outbound 页面注册即可
2. **面包屑+下拉模块** — 替代当前平铺导航，支持模块间快速跳转
3. **暗色模式切换** — 官网有 `◐` 图标，按需加回

### 3.3 关键页面交互细节（从 DOM 推断）

| 页面 | 核心交互 | 技术实现提示 |
|------|----------|--------------|
| **潜在客户搜索** | 表单分步：产品词→市场→类型→语法预览→跑任务 | `vue-form-wizard` 或自研 Stepper + `reactive` 表单状态 |
| **搜索任务列表** | 卡片式：状态/进度/结果数/操作(查看/导出/删) | `ElCard` + `ElProgress` + `slot` 操作列 |
| **客户画像详情** | 左侧证据链(可展开) + 右侧评分雷达图 + 底部联系人 | `ElTimeline`(证据) + `ECharts`(雷达) + `ElDescriptions` |
| **AI写邮件** | 左侧画像摘要 + 右侧编辑器(变量插入/预览/发送) | `Monaco Editor` 或 `Tiptap` + 变量选择器组件 |
| **发送任务** | 列表：模版/收件数/发送态/打开率/点击率/操作 | `ElTable` + 自定义 `rate` 列渲染进度条 |

---

## 四、工作台布局设计

### 4.1 WhatsFinds 的"工作台"概念

> 官网定位：**AI Outbound Workspace** — 不是 CRM，是**执行层工作台**

| 维度 | 设计 | YouDing 对比 |
|------|------|--------------|
| **核心视图** | 任务看板：搜客任务/画像任务/发信任务/追踪任务 | 你的 `client_today_service.py` 已有"今日工作台" |
| **时间维度** | 无显式日历，任务按"进行中/待处理/已完成"分组 | 你的"今日/本周/本月"切换更强 |
| **优先级** | 画像评分高→前；打开未回复→前 | 你的 `followup_rules` + `health_score` 更细 |
| **多账号隔离** | 账号级配置隔离（Key/模型/邮箱/数据） | 你的多租户架构天然支持，但**前端切换入口缺失** |

### 4.2 YouDing 缺失的"执行视图"对比

| 视图 | WhatsFinds | YouDing 现状 | 补齐建议 |
|------|------------|--------------|----------|
| **搜客执行台** | 任务创建→运行→结果查看一体化 | 分散在 `auto_discovery`/`seo_matrix`/各路由 | 新建 `/workspace/prospecting` 单页聚合 |
| **画像审核台** | 证据链+评分+一键进客户池 | 无（但 `ProspectLead` 模型已就绪） | `ProspectLead` 详情页加"同步为客户/商机"按钮 |
| **写信工作台** | 画像注入→模版选择→变量填充→预览→发送/存草稿 | `ai_generate` 仅生成文本 | 新建 `/workspace/outreach` 集成 `OutreachEditor` |
| **追踪复盘台** | 像素回调→实时看板→回复分类→复盘建议 | 无（但 `EmailOutreach` 追踪字段已就绪） | 接入像素路由 + `email_campaign_analytics` 视图 |

---

## 五、交互体验亮点清单（可直接抄作业 · V2 加价值/工时评分）

| # | 交互细节 | WhatsFinds 做法 | YouDing 落地路径 | 价值(1-5) | 工时 | V2 校准 |
|---|----------|----------------|------------------|-----------|------|---------|
| 1 | **搜索语法实时预览** | 输入产品词/市场/类型 → 即时生成 `site:xxx "keyword" -exclude` | `SearchSyntaxPreview.vue`，`watch` 表单字段防抖生成 | 5 | 1d | 纯前端，无依赖 |
| 2 | **Key/模型/邮箱 配置即测** | 设置页填完 → 点"测试连接" → 绿/红标记保存 | `AiProviderConfig` + `TestConnectionAction` 复用 `ai_engine.py` | 5 | 2d | **需先做 tenant 级 Provider**（P0-2） |
| 3 | **证据可点击溯源** | 画像页每条证据旁有链接图标 → 新窗口打开原文 | `EvidenceChain.vue`，`evidence.source_url` 渲染为外链 | 4 | 1d | 依赖 `ProspectLead.evidence_chain` 新列 |
| 4 | **评分维度可视化** | 雷达图：匹配度/邮箱可信/公开证据/联系人完整度 | `ECharts` 雷达图 + `ScoreBreakdown` Tooltip | 5 | 1d | 依赖 `overall_score` 拆 4 子分 |
| 5 | **变量插入器** | 写信编辑器 `@` 唤起变量面板 | `VariablePicker.vue`，注入 `Tiptap`/`Monaco` | 4 | 2d | 纯前端 |
| 6 | **A/B 版本并行编辑** | 同一任务生成 2-3 版本，Tab 切换对比 | `EmailVersionTabs.vue`，共享变量上下文 | 3 | 2d | **`ab_test.py` 模型已存在**，做 UI 接线 |
| 7 | **发送前预览渲染** | 实时渲染 HTML 邮件样式，移动端/桌面端切换 | `EmailPreviewModal` + `iframe` 沙箱渲染 | 4 | 1d | 纯前端 |
| 8 | **追踪像素一键植入** | 模版保存时自动注入 `{{tracking_pixel}}` | `TemplateProcessor` 中间件自动注入 | 5 | 1d | **`EmailOutreach.tracking_pixel_id` 已存在**，做注入中间件 |
| 9 | **回复自动关联线索** | IMAP 拉取 → 线程解析 → 匹配 `message_id` → 写回 `ProspectLead` | `EmailReplyProcessor` 定时任务 + `inquiry_channels` 复用 | 5 | 3d | `provider_message_id` 字段已存在 |
| 10 | **配置级数据隔离** | 切换账号 → 所有 Key/模型/邮箱/任务/数据瞬间切换 | 你的 `tenant` 架构已支持，缺**前端账号切换器** | 4 | 1d | 多租户已就绪，做前端切换器 |

---

## 六、授权/计费/设备绑定模型（可借鉴 · V2 校准）

### 6.1 定价策略
| 套餐 | 价格 | 定位 | YouDing 参考 |
|------|------|------|--------------|
| 半年卡 | ￥499 | "完整跑完一轮外贸开发周期" | 你的 `MVP_LAUNCH=1` 可对标"试用版" |
| 年卡 | ￥799 | "长期开发更划算，持续获客" | 年付折扣策略可直接复用 |

### 6.2 设备绑定 + 授权码流程
```
1. 用户登录 → 显示"未激活" + 设备ID (TL-XXXXXX-XXXXXXXX)
2. 用户购买 → 获得授权码 (TL1.xxxxx.xxxxx)
3. 授权页输入码 → 激活 → 绑定设备ID
4. 后台人工确认订单 → 自动开通 / 刷新订单状态
5. 授权信息显示：客户/版本/到期时间/设备ID
```

### 6.3 V2 现状校准（NEW）

> **V1 把授权体系列为"新增"，实际 `License` 模型已存在且字段相当完整。**

`backend/app/models/license.py` 已有：
- `license_key`（授权码，唯一索引）
- `hardware_id`（**即设备指纹**，V1 建议新建 `device_fingerprint`，可复用此字段）
- `max_devices`（设备数上限）
- `expires_at` / `activated_at`（有效期）
- `plan_code` / `ai_quota`（套餐 + AI 额度）
- `status`（inactive/active 状态机雏形）
- `tenant_id` 关联

同时 `app_device.py` 模型也已存在，可做设备管理。

**真正缺口**：① 激活 UI 页面（`LicenseActivationForm.vue`）；② 订单状态机（待支付/待确认/已激活/已过期/已退款）—— 可在现有 `status` 字段上扩展 enum；③ `TL1.{random}.{random}` 授权码格式生成器。

---

## 七、技术架构关键点（V2 修正）

### 7.1 核心设计原则
| 原则 | 体现 | YouDing 对齐度（V2 校准） |
|------|------|----------------|
| **用户自带核心资产** | Key/模型/邮箱全由用户配置 | 🟡 你的 `AIModelProvider` 是**全局唯一**（`name` unique，无 `tenant_id`），缺**用户级覆盖** —— 这是 P0-2 的核心 |
| **服务端状态持久化** | 线索/任务/配置/发信记录云端保存 | ✅ PostgreSQL + Redis 已满足 |
| **账号级隔离** | 登录即恢复自己的工作台 | ✅ 多租户 `tenant_id` 隔离；🟡 缺**前端工作台状态恢复 + 账号切换器** |
| **Agent 编排而非单体** | 搜客/画像/写信/跟进 四 Agent 解耦 | ✅ `hermes/agency/` 已有 DAG 引擎，**应在现有引擎上新增 4 个 outbound 工作流**，而非重构 |

### 7.2 推测技术栈
- **前端**：Vue 3 + Vite + Pinia + Element Plus（导航/表单/表格风格吻合）—— ✅ 与 YouDing 一致
- **后端**：FastAPI / Node.js（WebSocket 推送实时进度）—— ✅ YouDing 用 FastAPI
- **任务队列**：Celery / BullMQ（搜客/画像/发信异步任务）
- **爬虫**：Playwright / Puppeteer（官网摘要/联系人提取）—— YouDing 已有 `.playwright-mcp`
- **邮件**：SMTP/IMAP 库 + 追踪像素服务
- **部署**：Docker Compose 单机/集群，用户自建或 SaaS

---

## 八、代码现状校准（V2 核心修正章）

> 本章是 V2 相对 V1 最重要的增量。它把 V1 的"新建清单"逐项对照真实代码，得出"大部分已存在，只需接线"的结论。

### 8.1 已有模型清单 vs V1"新建"建议

| V1 建议"新建"模型 | 实际状态 | 现有字段覆盖度 | 真正缺口 |
|-------------------|----------|---------------|----------|
| `prospect_lead.py` | ✅ **已存在** | 高：`fit_score`/`engagement_score`/`overall_score`/`email_verified`/`domain`/`company_name_normalized`/`source_detail` JSON/`tags` | 加 `evidence_chain` JSON 列 + 4 子分拆解 |
| `email_tracking_event.py` | ✅ **已存在**（`EmailOutreach` 内置） | 高：`tracking_pixel_id`/`tracking_links`/`open_count`/`click_count`/`bounce_type`/`provider_message_id` | 独立事件表可选；路由端点是刚需 |
| `license_code.py` | ✅ **已存在**（`License`） | 高：`license_key`/`hardware_id`/`max_devices`/`expires_at`/`plan_code` | 订单状态机 enum + 激活 UI |
| `device_fingerprint.py` | ✅ **可复用** | `License.hardware_id` + `app_device.py` | 无 |
| `ai_provider_config.py` | 🟡 **部分存在** | 中：`AIModelProvider`+`AIModelConfig` 有 `api_key`/`base_url`/`default_model`，但**无 `tenant_id`**（全局级） | 加 tenant 级 Provider 表 + 测试连接 |
| `ab_test`（A/B） | ✅ **已存在** | — | 邮件场景 UI 接线 |

### 8.2 已有 Hermes / Agency 引擎能力（V1 严重低估）

`backend/app/services/hermes/agency/` 已有：
- `workflow_runner.py` —— **YAML DAG 工作流执行引擎**（变量插值 `{{var}}`、步骤编排）
- `role_loader.py` —— 角色加载（Agent 拟人化的基础）
- `llm_router.py` —— **多模型路由**（天然支持"用户自带模型"）
- `provider_setup.py` —— Provider 配置
- `orchestrator_bridge.py` —— 编排器桥接

`data/agency_workflows/` 已有 **25+ 工作流 YAML**：content-pipeline、geo-content-matrix-b2b、investment-analysis、product-launch-comms、tech-blog 等。

另有：`daily_autonomous_cycle.py`（7 步自主运营闭环）、`command_center.py`、`registry.py`、`runtime.py`、`greedy_agency_orchestrator_service.py`、四类 harness（learning/prompt/scoring/consistency）。

> **结论**：P2-1"Agent 化重构 Hermes"应改写为"**在现有 agency/workflow_runner 上新增 4 个 outbound 工作流 YAML（search/profile/write/track）+ 复用 llm_router 支持用户自带模型**"，工时从"重构级（数周）"降至"配置级（3-5d）"。

### 8.3 已有前端基础设施（V1 低估）

`frontend/admin/src/composables/` 已有：
- `useWorkTabNavigation.ts` + `useModuleTabSync.ts` + `useShellNavigation.ts` —— **多标签页导航已具备**
- `useAiConnect.ts` + `useGrowthAgentRun.ts` + `useAssistantPanel.ts` —— AI/Agent UI 钩子
- `useGlobalSearch.ts` —— 全局搜索
- `useWebSocket.ts` —— 实时推送（追踪回调所需）

### 8.4 校准结论：从"新建"到"接线"

| V1 立场 | V2 校准 | 影响 |
|---------|---------|------|
| "需新建 5 个模型" | 4 个已存在 / 1 个需加 tenant 字段 | 模型迁移工时 ≈ 0 |
| "需重构 Hermes 为 4 Agent" | 在现有 DAG 引擎上加 4 个 YAML | 工时 -70% |
| "追踪服务从 0 建" | 模型已就绪，挂路由即可 | P1-3 工时 5d → 2d |
| "设备指纹新模型" | 复用 `hardware_id` | P1-5 工时下调 |
| "多标签页增强" | 3 个 composable 已存在 | P0-5 工时 2d → 1d |

---

## 九、优化吸收清单（V2 重构 · 基于代码校准）

> 每项新增：**现状校准 / 验收标准 / 风险与回滚 / 依赖 / 价值分 / 建议负责人**。

### 优先级 2×2 矩阵（NEW）

```
   高价值 ↑
         │   P0-2(Key/模型配置)  P0-1(语法预览)
         │   P0-3(证据链)        P0-4(雷达图)
         │   P1-3(追踪路由)      P0-5(多标签)
         │
         │        P1-1(执行台聚合)   P1-2(写信工作台)
         │        P1-4(评分拆解)
         │
         │   P1-5(授权UI)  P2-1(Agent YAML)
         │   P2-2(种子共享) P2-3(私有化) P2-4(多渠道)
         └─────────────────────────────────────→ 高工时
  低价值                            (工时)
```

### 🔴 P0 —— 本周可落地，立竿见影

#### P0-1 搜索语法实时预览组件
- **现状校准**：`auto_discovery.py` 路由已存在；纯前端增量
- **落地**：新建 `frontend/components/whatsfinds/SearchSyntaxPreview.vue` → 接入 `auto_discovery` 页面
- **验收标准**：① 输入产品词/市场/类型后 ≤300ms 防抖生成语法；② 语法可复制；③ 含 `site:`/`""`/`-exclude` 组合
- **风险与回滚**：风险低（纯展示组件）；回滚 = 移除组件
- **依赖**：无
- **价值分**：5 ｜ **工时**：1d（V1 估 2d，校准下调）｜ **负责人**：前端

#### P0-2 用户级 API Key/模型/邮箱配置页（含测试连接）⭐ 核心
- **现状校准**：`AIModelProvider`/`AIModelConfig` 存在但**无 tenant_id**（全局级），需新增 tenant 级 Provider 表
- **落地**：新建 `tenant_ai_provider` 模型（tenant 隔离）+ `/admin/ai-provider-config` 页 + `TestConnectionAction`
- **验收标准**：① 每个租户可独立配置 Key/模型/SMTP；② 点"测试连接"返回绿/红 + 延迟；③ 配置加密存储；④ `ai_engine.py` 优先读 tenant 级，回退全局
- **风险与回滚**：🟡 中风险（涉及密钥存储）；回滚 = feature flag 关闭 tenant 级读取，回退全局
- **依赖**：加密存储（复用现有 `.secrets` 机制）
- **价值分**：5 ｜ **工时**：3d ｜ **负责人**：后端+前端

#### P0-3 证据链可视化组件
- **现状校准**：`ProspectLead` 已有 `source_detail` JSON；需加 `evidence_chain` 列
- **落地**：`ProspectLead` 加 `evidence_chain` JSON 列 + `EvidenceChain.vue` 接入详情页
- **验收标准**：① 每条证据可展开看原文摘要；② 证据旁有外链图标溯源；③ 证据编号 [E1][E2] 可在写信时引用
- **风险与回滚**：风险低（加列 + 组件）；回滚 = 隐藏组件
- **依赖**：DB 迁移（加列）
- **价值分**：4 ｜ **工时**：2d ｜ **负责人**：后端(迁移)+前端

#### P0-4 评分雷达图组件
- **现状校准**：`ProspectLead` 已有 `fit_score`/`engagement_score`/`overall_score`；需拆 4 子分
- **落地**：`ScoreRadar.vue`（ECharts）+ `overall_score` 拆解为 {匹配度/邮箱可信/证据强度/联系人完整度}
- **验收标准**：① 雷达图 4 轴；② Tooltip 显示子分明细；③ 子分来自后端计算
- **风险与回滚**：风险低；回滚 = 隐藏雷达图
- **依赖**：P0-3（证据强度子分依赖 evidence_chain）
- **价值分**：5 ｜ **工时**：1d ｜ **负责人**：前端

#### P0-5 多标签页任务栏增强
- **现状校准**：`useWorkTabNavigation.ts` + `useModuleTabSync.ts` 已存在，补"可关闭/状态保持 + outbound 页注册"
- **落地**：完善 `useWorkTabNavigation.ts` + `AppTabs.vue`
- **验收标准**：① 标签可关闭；② 切换标签保持表单状态；③ outbound 4 页可开为标签
- **风险与回滚**：风险低；回滚 = 保留现有导航
- **依赖**：无
- **价值分**：4 ｜ **工时**：1d（V1 估 2d，校准下调）｜ **负责人**：前端

### 🟠 P1 —— 两周内完成，补齐执行层短板

#### P1-1 搜客执行台单页聚合
- **现状校准**：能力分散在 `auto_discovery`/`seo_matrix`/各路由；前端聚合即可
- **落地**：新建 `/workspace/prospecting` 路由，聚合 4 步
- **验收标准**：① 单页完成 搜→画→写→追 四步切换；② 每步状态持久；③ 进度 WebSocket 实时推送（复用 `useWebSocket.ts`）
- **风险与回滚**：🟡 中（聚合多路由，状态管理复杂）；回滚 = 退回分散路由
- **依赖**：P0-1/3/4/5
- **价值分**：5 ｜ **工时**：4d ｜ **负责人**：前端+后端

#### P1-2 AI 写信工作台（变量注入+预览+A/B）
- **现状校准**：`ai_template.py`/`ab_test.py`/`case_study.py` 模型已存在；缺编辑器 UI
- **落地**：`OutreachEditor.vue`（Tiptap+VariablePicker）+ `/workspace/outreach`
- **验收标准**：① `@` 唤起变量面板；② A/B 两版 Tab 对比；③ 移动/桌面预览；④ 草稿/直发
- **风险与回滚**：风险中；回滚 = 用回 `ai_generate` 纯文本
- **依赖**：P0-2（用户级模型）、P0-3（变量来源）
- **价值分**：5 ｜ **工时**：4d ｜ **负责人**：前端+后端

#### P1-3 邮件追踪像素路由 + 回复 webhook ⭐ 工时大幅下调
- **现状校准**：`EmailOutreach` 已有 `tracking_pixel_id`/`tracking_links`/`open_count`/`click_count` 全字段；**只需挂路由端点 + IMAP 回复轮询**
- **落地**：新建 `/tracking/pixel/{id}` 路由 + `/tracking/click` 重定向 + `EmailReplyProcessor` 定时任务
- **验收标准**：① 像素请求写 `open_count`；② 点击重定向写 `click_count` 并跳转；③ IMAP 回复匹配 `provider_message_id` 写回线索
- **风险与回滚**：风险低（模型已就绪）；回滚 = 关路由
- **依赖**：无（模型已就绪）
- **价值分**：5 ｜ **工时**：2d（V1 估 5d，校准下调 60%）｜ **负责人**：后端

#### P1-4 画像评分维度拆解
- **现状校准**：`unified_geo_score_service.py` + `ProspectLead` 三档分已存在
- **落地**：拆 `overall_score` 为 4 子分 + `ScoreRadar` 展示
- **验收标准**：① 4 子分可解释；② 子分写入 `ProspectLead`；③ 雷达图联动
- **风险与回滚**：风险低；回滚 = 隐藏子分
- **依赖**：P0-3、P0-4
- **价值分**：4 ｜ **工时**：2d ｜ **负责人**：后端

#### P1-5 设备指纹 + 授权码激活 UI
- **现状校准**：`License` 模型（`license_key`/`hardware_id`/`max_devices`/`expires_at`）+ `app_device.py` 已存在；缺激活 UI + 订单状态机
- **落地**：`LicenseActivationForm.vue` + `/system/license` 页 + 订单 enum 扩展 + `TL1.{r}.{r}` 生成器
- **验收标准**：① 输入授权码激活并绑 `hardware_id`；② 显示客户/版本/到期/设备ID；③ 订单状态机 5 态
- **风险与回滚**：风险中（计费相关）；回滚 = 关激活页
- **依赖**：无
- **价值分**：3 ｜ **工时**：3d（V1 估更高，校准下调）｜ **负责人**：后端+前端

### 🟢 P2 —— 月度规划，构建护城河

#### P2-1 Agent 化（在现有 DAG 引擎上新增 4 outbound 工作流）⭐ 重构→配置
- **现状校准**：`hermes/agency/workflow_runner.py` DAG 引擎 + `llm_router` 已就绪；新增 4 个 YAML 即可
- **落地**：新增 `data/agency_workflows/outbound/{search,profile,write,track}.yaml` + `agent_protocol.py` 契约
- **验收标准**：① 4 工作流可独立 dry_run；② 复用 `llm_router` 读用户级模型；③ DAG 串联 4 步
- **价值分**：5 ｜ **工时**：3-5d（V1 估"数周重构"，校准下调 70%）｜ **负责人**：后端

#### P2-2 跨租户"种子源共享"开关
- **价值**：GEO/SEO 高质量线索可选共享给同行业租户，形成网络效应
- **工时**：5d ｜ **负责人**：后端

#### P2-3 私有化部署包
- **价值**：`docker-compose.whatsfinds.yml`，客户自建 Key/模型/邮箱/数据隔离
- **工时**：5d ｜ **负责人**：DevOps

#### P2-4 WhatsApp/LinkedIn 触达插件
- **价值**：补齐 WhatsFinds 仅邮件的短板，复用 `wecom_push_service` 架构
- **工时**：7d ｜ **负责人**：后端

---

## 十、成功指标与 KPI（NEW）

### 10.1 体验层 KPI（P0 后 2 周内观测）
| 指标 | 基线 | 目标 | 衡量方式 |
|------|------|------|----------|
| 搜客任务完成率 | 待测 | +30% | `/workspace/prospecting` 漏斗 |
| 画像审核→进客户池转化 | 待测 | +25% | `ProspectLead` 状态流转 |
| 写信→发送转化 | 待测 | +40% | `OutreachEditor` 草稿→sent |
| 邮件打开率 | 待测 | ≥35% | `EmailOutreach.open_count` |
| 邮件回复率 | 待测 | ≥8% | 回复 webhook 匹配 |

### 10.2 业务层 KPI（P1 后 1 月观测）
| 指标 | 目标 |
|------|------|
| 单租户月均发信量 | ≥500 |
| 高意向线索（询价类回复）月增 | ≥20% |
| 续费率（年卡） | ≥60% |

---

## 十一、实施路线图与依赖（NEW · 4 周）

```
W1(本周)   │ P0-1■  P0-2■■■  P0-3■■  P0-4■  P0-5■
          │  ├─依赖: P0-4 ← P0-3
W2        │ P1-3■■  P1-4■■  P1-1■■■■  P1-5■■■
          │  ├─依赖: P1-1 ← {P0-1,P0-3,P0-4,P0-5}
          │  ├─依赖: P1-4 ← {P0-3,P0-4}
W3        │ P1-2■■■■  P2-1■■■
          │  ├─依赖: P1-2 ← {P0-2,P0-3}
          │  ├─依赖: P2-1 ← P1-1(执行台验证流程)
W4        │ P2-2■■■■■  P2-3■■■■■  体验打磨 + 灰度
          │  └─依赖: P2-2 ← P2-1
```

**关键路径**：P0-2（Key 配置）→ P1-2（写信台）→ P1-1（执行台聚合）→ P2-1（Agent YAML）。
**并行可能**：P0-1/3/4/5 互相独立，可 4 人并行；P1-3 与 P1 线并行。

---

## 十二、MVP 定义（NEW · 2 周最小闭环）

> 目标：让一个外贸运营在 YouDing 内跑通"搜→画→写→追"最小闭环，不追求 P2。

**MVP 范围（W1-W2，~10 人日）**：
1. P0-2 tenant 级 Key/模型配置 + 测试连接（核心前置）
2. P0-1 搜索语法预览（让搜客直观）
3. P0-3 证据链 + P0-4 雷达图（让画像可信）
4. P1-3 追踪像素路由（让发信可衡量）
5. P1-1 执行台单页聚合（让 4 步连贯）

**MVP 不做**：P1-2 写信工作台先用 `ai_generate` 凑合；P1-5 授权 UI 延后；所有 P2。

**MVP 验收**：1 个真实租户在 1 个工作日内完成 ① 配置自带 Key → ② 搜出 20 条线索 → ③ 查看 1 个画像（证据+雷达）→ ④ 发 1 封信 → ⑤ 看到打开事件。

---

## 十三、ROI 分析（NEW）

| 投入 | 估算 | 预期回报 |
|------|------|----------|
| P0 全集 | ~8 人日 | 体验对齐 WhatsFinds， demos 可用 |
| P1 全集 | ~15 人日 | 执行闭环跑通，打开率/回复率可衡量，续费率提升基础 |
| P2 全集 | ~20 人日 | 护城河（Agent 化 + 网络效应 + 私有化 + 多渠道） |
| **合计** | **~43 人日** | 对标 WhatsFinds 年卡 ¥799 定价，假设 100 租户/月，月营收 ~¥80k，2-3 个月回本 |

**对比"按 V1 从 0 建"**：V1 隐含 ~90+ 人日（含 5 新模型 + Hermes 重构 + 追踪服务），V2 校准后 ~43 人日，**节省 ~50%**。

---

## 十四、风险登记册（NEW）

| # | 风险 | 等级 | 缓解 | 负责人 |
|---|------|------|------|--------|
| R1 | tenant 级 Key 存储泄露 | 高 | 复用 `.secrets` 加密；审计日志；feature flag 回退全局 | 后端 |
| R2 | 追踪像素被邮件客户端拦截 | 中 | 同时用重定向链接 + UTM 双轨；不做唯一依赖 | 后端 |
| R3 | `EmailOutreach` 已有字段语义与新路由不一致 | 中 | 上线前对齐字段语义；写迁移校验脚本 | 后端 |
| R4 | P1-1 执行台聚合状态管理复杂导致回归 | 中 | 灰度发布；保留分散路由作为回退 | 前端 |
| R5 | `agency/workflow_runner` YAML 引擎不支持用户级模型路由 | 中 | 先验证 `llm_router` 是否读 tenant 配置；不行则加适配层 | 后端 |
| R6 | 授权/计费改动影响存量租户 | 高 | `License` 改动向后兼容；新 enum 不破坏旧 status | 后端 |
| R7 | WhatsFinds 快速迭代，差距拉大 | 低 | 每季度复盘一次（见文末） | 产品 |

---

## 十五、代码结构参考（V2 校准版）

```text
# 前端新增 (frontend/components/whatsfinds/) —— 多数为纯组件，模型已就绪
├── SearchSyntaxPreview.vue      # 搜索语法实时预览          [P0-1, 1d]
├── EvidenceChain.vue            # 证据链时间轴              [P0-3, 依赖 evidence_chain 列]
├── ScoreRadar.vue               # 画像评分雷达图            [P0-4]
├── VariablePicker.vue           # 写信变量插入器            [P1-2]
├── OutreachEditor.vue           # AI写信工作台              [P1-2]
├── EmailVersionTabs.vue         # 邮件版本对比Tab (复用ab_test) [P1-2]
├── EmailPreviewModal.vue        # 发送前渲染预览            [P1-2]
├── TrackingPixelGenerator.vue   # 像素生成预览              [P1-3, 模型已有]
├── DeviceFingerprintBanner.vue  # 未授权顶栏(复用License)    [P1-5]
└── LicenseActivationForm.vue    # 授权码激活表单(复用License)[P1-5]

# 后端新增/改动 (backend/app/)
├── models/
│   ├── tenant_ai_provider.py        # ★新增: tenant级Key/模型(唯一真正新模型) [P0-2]
│   ├── prospect_lead.py             # 改: 加 evidence_chain 列 + 4子分        [P0-3/P1-4]
│   ├── email_outreach.py            # 复用: 字段已就绪,无需改动               [P1-3]
│   ├── license.py                   # 改: 扩展订单状态机 enum                 [P1-5]
│   └── app_device.py                # 复用: 设备管理                          [P1-5]
├── services/
│   ├── search_agent.py              # 新: 意图拆解+Serper+去重               [P2-1]
│   ├── profile_agent.py             # 新: 爬取+提取+评分                      [P2-1]
│   ├── write_agent.py               # 新: 模版库+变量注入                     [P2-1]
│   ├── track_agent.py               # 新: 像素回调+IMAP+分类                  [P2-1]
│   ├── email_tracking_service.py    # 新: 像素路由/事件持久化(模型已就绪)     [P1-3]
│   ├── license_service.py           # 新: 激活/续费/订单状态机(模型已就绪)    [P1-5]
│   └── variable_resolver.py         # 新: 写信变量解析                        [P1-2]
├── api/v1/routes/
│   ├── workspace_prospecting.py     # 新: /workspace/prospecting 聚合入口     [P1-1]
│   ├── workspace_outreach.py        # 新: /workspace/outreach 写信台          [P1-2]
│   ├── email_tracking.py            # 新: /tracking/pixel /tracking/click     [P1-3]
│   ├── ai_provider_config.py        # 新: /admin/ai-provider-config(tenant级) [P0-2]
│   └── license.py                   # 改: 激活端点                             [P1-5]
└── services/hermes/agency/
    ├── agent_protocol.py            # 新: 4 Agent 统一契约                    [P2-1]
    └── data/agency_workflows/outbound/
        ├── search.yaml              # 新: 搜客工作流(复用 workflow_runner)    [P2-1]
        ├── profile.yaml             # 新: 画像工作流                          [P2-1]
        ├── write.yaml               # 新: 写信工作流                          [P2-1]
        └── track.yaml               # 新: 追踪工作流                          [P2-1]
```

> 标注说明：`★新增` = 真正新建模型（仅 1 个）；`改` = 在现有模型上加列/enum；`复用` = 字段已就绪无需改；`新` = 新服务/路由/组件。

---

## 十六、一句话总结（V2 增强版）

> **WhatsFinds 的核心洞察是：外贸团队不需要"更多数据"，而需要"把自己的 Key/模型/邮箱/数据跑通在一个工作台里"。**
>
> **V2 校准后的关键判断**：YouDing 已在 **GEO/SEO 技术栈、询盘归因、跨租户学习、Hermes DAG 引擎** 上建立护城河，且 `ProspectLead`/`EmailOutreach`/`License`/`AIModelConfig`/`ab_test` 等模型**大多已存在**。真正缺的不是"造能力"，而是：
> 1. **补一个 tenant 级 AI Provider 配置**（唯一真正新建模型）—— 让"用户自带资产"成立
> 2. **把已就绪的追踪字段挂上路由** —— 让发信可衡量
> 3. **把分散的 4 步聚合成单页工作台** —— 让执行闭环可见
> 4. **在现有 agency DAG 引擎上加 4 个 outbound YAML** —— 让 Agent 化低成本落地
>
> **融合策略**：YouDing 提供"高质量种子源 + 策略大脑 + 多租户隔离 + DAG 引擎"作为上游能力平台，吸收 WhatsFinds 的"工作台交互 + Agent 编排 + 用户自带资产"模式补齐执行层"最后一公里"。既有技术深度（YouDing），又有执行闭环（WhatsFinds），形成**平台 + 工作台**双引擎护城河。
>
> **投入产出**：V2 校准后总投入 ~43 人日（较 V1 隐含估算节省 ~50%），MVP 2 周可跑通最小闭环。

---

> V2 文档基于 2026-07-20 官网公开信息 + YouDing 代码库实测校准生成。WhatsFinds 产品可能快速迭代，建议每季度复盘一次差距。本文件与 V1（`WHATSFINDS_AI_ANALYSIS.md`）并存，V1 保留作为原始观察记录。
