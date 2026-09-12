# WhatsFinds AI 完整体验分析与 YouDing 优化吸收清单

> 基于官网 https://whatsfinds.com/ 与系统内部结构探索（账号：lvbowang88@gmail.com / 未授权）
> 探索时间：2026-07-20

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

| 环节 | WhatsFinds 做法 | YouDing 吸收建议 |
|------|----------------|------------------|
| **意图拆解** | 产品词→市场→客户类型→自动组合语法 | 在 `auto_discovery.py` / `search_strategy.py` 加入 `IntentPlanner` Agent |
| **Key隔离** | 每用户自带 Serper Key，额度透明 | 新增 `user_serper_key` 字段，搜索服务读取用户级配置 |
| **平台过滤** | 自动过滤低价值平台、零售、重复域名 | 复用 `seo_diagnosis.py` 的 `domain_quality_scorer` |
| **证据保留** | 每条线索保留原始搜索语法+快照+来源页 | 在 `ProspectLead` 模型加 `evidence_chain` JSON 字段 |
| **去重策略** | 域名级去重 + 公司名模糊匹配 | 复用 `lead_enrichment.py` 的 `dedupe_by_domain_and_name` |

### 2.3 画像 Agent 设计细节

| 字段 | 数据来源 | 评分权重 | YouDing 对应能力 |
|------|----------|----------|------------------|
| **官网摘要** | 爬取首页/About/Products | 25% | `site_content_array_i18n` 已有多语言内容 |
| **联系人提取** | 官网Contact/Team页 + LinkedIn公开 | 20% | 需新增 `contact_extractor` 服务 |
| **邮箱可信度** | 格式验证 + MX记录 + 历史送达 | 25% | 复用 `email_validator` + 新增 `mx_checker` |
| **匹配度评分** | 产品词覆盖 + 行业关键词 + 地理 | 30% | 直接用 `unified_geo_score_service` 逻辑 |

> **关键洞察**：WhatsFinds 的画像评分 = **GEO评分的简化版**。你的 13 战术、22 源雷达、Schema 结构化数据，完全可以生成比他们更精准的画像。

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

### 2.5 追踪 Agent 设计细节

| 能力 | 实现方式 | YouDing 现状 | 补齐建议 |
|------|----------|--------------|----------|
| **打开追踪** | 1px 像素 + 唯一 ID | 无 | 新增 `tracking_pixel` 服务 + `email_open_event` 模型 |
| **点击追踪** | 重定向链接 + UTM | 无 | 复用 `attribution_service` 逻辑 |
| **回复抓取** | IMAP 轮询 + Webhook | 企微推送已有 | 新增 `email_reply_webhook` 解析线程 |
| **意向分类** | LLM 分类：询价/拒绝/要求资料/其他 | 无 | 复用 `inquiry_channels.py` 的分类逻辑 |
| **复盘报表** | 按模版/客户类型/发送时间聚合 | 归因报表已有 | 新增 `email_campaign_analytics` 视图 |

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

**可直接迁移到 YouDing**：
1. **多标签页任务栏** — 你的 `frontend/admin/src/composables/useAdminWorkspace.ts` 已有雏形，补齐“可关闭/状态保持”
2. **面包屑+下拉模块** — 替代当前平铺导航，支持模块间快速跳转
3. **暗色模式切换** — 官网有 `◐` 图标，你的 `@nuxtjs/color-mode` 已移除，可按需加回

### 3.3 关键页面交互细节（从 DOM 推断）

| 页面 | 核心交互 | 技术实现提示 |
|------|----------|--------------|
| **潜在客户搜索** | 表单分步：产品词→市场→类型→语法预览→跑任务 | `vue-form-wizard` 或自研 Stepper + `reactive` 表单状态 |
| **搜索任务列表** | 卡片式：状态/进度/结果数/操作(查看/导出/删) | `ElCard` + `ElProgress` + `slot` 操作列 |
| **客户画像详情** | 左侧证据链(可展开) + 右侧评分雷达图 + 底部联系人 | `ElTimeline`(证据) + `ECharts`(雷达) + `ElDescriptions` |
| **AI写邮件** | 左侧画像摘要 + 右侧编辑器(变量插入/预览/发送) | `Monaco Editor` 或 `Tiptap` + 变量选择器组件 |
| **发送任务** | 列表：模版/收件数/发送态/打开率/点击率/操作 | `ElTable` + 自定义 `rate` 列渲染进度条 |

---

## 四、排班/工作台布局设计

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
| **画像审核台** | 证据链+评分+一键进客户池 | 无 | `ProspectLead` 详情页加"同步为客户/商机"按钮 |
| **写信工作台** | 画像注入→模版选择→变量填充→预览→发送/存草稿 | `ai_generate` 仅生成文本 | 新建 `/workspace/outreach` 集成 `OutreachEditor` |
| **追踪复盘台** | 像素回调→实时看板→回复分类→复盘建议 | 无 | 接入 `email_tracking` 服务 |

---

## 五、交互体验亮点清单（可直接抄作业）

| # | 交互细节 | WhatsFinds 做法 | YouDing 落地路径 |
|---|----------|----------------|------------------|
| 1 | **搜索语法实时预览** | 输入产品词/市场/类型 → 即时生成 `site:xxx "keyword" -exclude` | `SearchSyntaxPreview` 组件，`watch` 表单字段防抖生成 |
| 2 | **Key/模型/邮箱 配置即测** | 设置页填完 → 点"测试连接" → 绿/红标记保存 | `AiProviderConfig` + `TestConnectionAction` 复用现有 `ai_engine.py` |
| 3 | **证据可点击溯源** | 画像页每条证据旁有链接图标 → 新窗口打开原文 | `EvidenceChain` 组件，`evidence.source_url` 渲染为外链 |
| 4 | **评分维度可视化** | 雷达图：匹配度/邮箱可信/公开证据/联系人完整度 | `ECharts` 雷达图 + `ScoreBreakdown` Tooltip |
| 5 | **变量插入器** | 写信编辑器 `@` 唤起变量面板（公司名/联系人/产品/证据编号） | `VariablePicker` 组件，注入 `Tiptap`/`Monaco` |
| 6 | **A/B 版本并行编辑** | 同一任务生成 2-3 版本，Tab 切换对比 | `EmailVersionTabs` 组件，共享变量上下文 |
| 7 | **发送前预览渲染** | 实时渲染 HTML 邮件样式，移动端/桌面端切换 | `EmailPreviewModal` + `iframe` 沙箱渲染 |
| 8 | **追踪像素一键植入** | 模版保存时自动注入 `{{tracking_pixel}}` | `TemplateProcessor` 中间件自动注入 |
| 9 | **回复自动关联线索** | IMAP 拉取 → 线程解析 → 匹配 `message_id` → 写回 `ProspectLead` | `EmailReplyProcessor` 定时任务 + `inquiry_channels` 复用 |
| 10 | **配置级数据隔离** | 切换账号 → 所有 Key/模型/邮箱/任务/数据瞬间切换 | 你的 `tenant` 架构已支持，缺**前端账号切换器** |

---

## 六、授权/计费/设备绑定模型（可借鉴）

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

**YouDing 可吸收**：
- **设备指纹绑定** — 防止账号共享，`device_fingerprint` 模型
- **授权码格式** — `TL1.{random}.{random}` 易于人工核销
- **订单状态机** — 待支付/待确认/已激活/已过期/已退款

---

## 七、技术架构关键点（从官网推断）

### 7.1 核心设计原则
| 原则 | 体现 | YouDing 对齐度 |
|------|------|----------------|
| **用户自带核心资产** | Key/模型/邮箱全由用户配置 | ✅ 你的 `AI_DEEPSEEK_API_KEY` 等环境变量已支持，缺**用户级覆盖** |
| **服务端状态持久化** | 线索/任务/配置/发信记录云端保存 | ✅ PostgreSQL + Redis 已满足 |
| **账号级隔离** | 登录即恢复自己的工作台 | ✅ 多租户 `tenant_id` 隔离，缺**前端工作台状态恢复** |
| **Agent 编排而非单体** | 搜客/画像/写信/跟进 四 Agent 解耦 | 🔄 你的 `hermes` 调度器可托管，需拆分为 4 个 Agent 服务 |

### 7.2 推测技术栈
- **前端**：Vue 3 + Vite + Pinia + Element Plus（导航/表单/表格风格吻合）
- **后端**：FastAPI / Node.js（WebSocket 推送实时进度）
- **任务队列**：Celery / BullMQ（搜客/画像/发信异步任务）
- **爬虫**：Playwright / Puppeteer（官网摘要/联系人提取）
- **邮件**：SMTP/IMAP 库 + 追踪像素服务
- **部署**：Docker Compose 单机/集群，用户自建或 SaaS

---

## 八、YouDing 优化吸收清单（按优先级）

### 🔴 P0 —— 本周可落地，立竿见影

| 编号 | 优化项 | WhatsFinds 来源 | YouDing 落地文件/路由 | 预估工时 |
|------|--------|----------------|----------------------|----------|
| **P0-1** | **搜索语法实时预览组件** | 官网"BUYER SIGNALS"区 | 新建 `frontend/components/whatsfinds/SearchSyntaxPreview.vue` → 接入 `auto_discovery` 页面 | 2d |
| **P0-2** | **用户级 API Key/模型/邮箱配置页** | "YOUR STACK, YOUR DATA" | 新建 `/admin/ai-provider-config` + `AiProviderConfig` 模型(tenant隔离) | 3d |
| **P0-3** | **证据链可视化组件** | 画像页"官网证据/邮箱可信度/联系人/匹配度" | `frontend/components/whatsfinds/EvidenceChain.vue` → 接入 `ProspectLead` 详情 | 2d |
| **P0-4** | **评分雷达图组件** | 画像页四维雷达 | `frontend/components/whatsfinds/ScoreRadar.vue` (ECharts) | 1d |
| **P0-5** | **多标签页任务栏增强** | 顶部"已打开页面"可关闭/保持 | 完善 `useAdminWorkspace.ts` + `AppTabs.vue` | 2d |

### 🟠 P1 —— 两周内完成，补齐执行层短板

| 编号 | 优化项 | WhatsFinds 来源 | YouDing 落地路径 |
|------|--------|----------------|------------------|
| **P1-1** | **搜客执行台单页聚合** | 01搜客→02画像→03写信→04追踪线性流 | 新建 `/workspace/prospecting` 路由，聚合 `auto_discovery`/`lead_enrichment`/`ai_generate`/`email_tracking` |
| **P1-2** | **AI写信工作台(变量注入+预览+A/B)** | 写信Agent+变量插入器+预览 | 新建 `OutreachEditor.vue` (Tiptap+VariablePicker) + `/workspace/outreach` |
| **P1-3** | **邮件追踪像素服务** | 打开/点击追踪+回复抓取 | 新建 `email_tracking` 服务 + `tracking_pixel` 路由 + `email_open_event`/`email_click_event` 模型 |
| **P1-4** | **画像评分维度拆解** | 匹配度/邮箱可信/证据/联系人 | 复用 `unified_geo_score_service` 拆解为 4 子分 + `ScoreRadar` 展示 |
| **P1-5** | **设备指纹+授权码体系** | TL-设备ID + TL1.授权码 | 新增 `device_fingerprint`/`license_code`/`license_order` 模型 + `/system/license` 页 |

### 🟢 P2 —— 月度规划，构建护城河

| 编号 | 优化项 | 战略价值 |
|------|--------|----------|
| **P2-1** | **Agent 化重构 Hermes** | 将 `hermes/daily_autonomous_cycle.py` 拆分为 `SearchAgent`/`ProfileAgent`/`WriteAgent`/`TrackAgent`，统一 `AgentProtocol` 接口，支持用户自带模型 |
| **P2-2** | **跨租户"种子源共享"开关** | 你的 GEO/SEO 高质量线索 → 可选共享给同行业租户作为"高信度种子"，形成网络效应 |
| **P2-3** | **私有化部署包** | 打包 `docker-compose.whatsfinds.yml`，支持客户自建 Key/模型/邮箱/数据完全隔离 |
| **P2-4** | **WhatsApp/LinkedIn 触达插件** | 补齐 WhatsFinds 仅邮件的短板，复用你的 `wecom_push_service` 架构 |

---

## 九、代码结构参考（WhatsFinds 风格映射到 YouDing）

```text
# 前端新增 (frontend/components/whatsfinds/)
├── SearchSyntaxPreview.vue      # 搜索语法实时预览
├── EvidenceChain.vue            # 证据链时间轴(可展开/外链)
├── ScoreRadar.vue               # 画像评分雷达图
├── VariablePicker.vue           # 写信变量插入器(@唤起)
├── OutreachEditor.vue           # AI写信工作台(Tiptap+预览+A/B)
├── EmailVersionTabs.vue         # 邮件版本对比Tab
├── EmailPreviewModal.vue        # 发送前渲染预览(移动端/桌面端)
├── TrackingPixelGenerator.vue   # 像素生成/嵌入预览
├── DeviceFingerprintBanner.vue  # 未授权顶栏提示
└── LicenseActivationForm.vue    # 授权码激活表单

# 后端新增 (backend/app/)
├── models/
│   ├── ai_provider_config.py        # 用户级 Key/模型/邮箱配置
│   ├── prospect_lead.py             # 潜在客户线索(含 evidence_chain)
│   ├── email_tracking_event.py      # 打开/点击/回复事件
│   ├── license_code.py              # 授权码/设备绑定/订单
│   └── device_fingerprint.py        # 设备指纹
├── services/
│   ├── search_agent.py              # 搜客 Agent(意图拆解+Serper调用+去重)
│   ├── profile_agent.py             # 画像 Agent(爬取+提取+评分)
│   ├── write_agent.py               # 写信 Agent(模版库+变量注入+模型调用)
│   ├── track_agent.py               # 追踪 Agent(像素回调+IMAP轮询+分类)
│   ├── email_tracking_service.py    # 像素路由/事件持久化/回调处理
│   ├── license_service.py           # 激活/续费/设备绑定/订单状态机
│   └── variable_resolver.py         # 写信变量解析(画像/企业优势/历史模版)
├── api/v1/routes/
│   ├── workspace_prospecting.py     # /workspace/prospecting 聚合入口
│   ├── workspace_outreach.py        # /workspace/outreach 写信台
│   ├── email_tracking.py            # /tracking/pixel /tracking/click
│   ├── ai_provider_config.py        # /admin/ai-provider-config
│   └── license.py                   # /system/license
└── agents/
    └── agent_protocol.py            # Agent 统一接口定义
```

---

## 十、一句话总结

> **WhatsFinds 的核心洞察是：外贸团队不需要"更多数据"，而需要"把自己的 Key/模型/邮箱/数据跑通在一个工作台里"。**
>
> YouDing 已在 **GEO/SEO 技术栈、询盘归因自动化、跨租户行业学习** 上建立护城河；WhatsFinds 在 **用户自主权、Agent 化执行层、邮件全链路追踪** 上走得更远。
>
> **融合策略**：
> - **YouDing 提供"高质量种子源+策略大脑+多租户隔离"** → 作为 WhatsFinds 这类执行层的**上游能力平台**
> - **吸收 WhatsFinds 的"工作台交互+Agent编排+用户自带资产"模式** → 补齐 YouDing 执行层"最后一公里"体验
> - **联合产出"GEO驱动的AI外贸工作台"** → 既有技术深度(你)，又有执行闭环(他)，形成**平台+工作台**双引擎护城河

---

> 文档基于 2026-07-20 官网公开信息 + 系统结构推断生成，WhatsFinds 产品可能快速迭代，建议每季度复盘一次差距。