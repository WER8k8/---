# AI Global Growth OS — 完整开发计划 V2.0（现状盘点版）

> 盘点日期：2026-08-30
> 依据：① 对真实代码库（`主要备份\上线网站`）的目录/文件/关键词证据探查；② 6 份需求与架构文档（AI Native出海B2B获客系统架构设计、AI 企业私有智能中心、CODEX TASK-001~013 规格书第一/二部、ECC to Experience Engine 完整架构、新建 DOCX 讨论文档）；③ 项目内既有状态文档（项目完成度盘点 08-29/30、服务状态 08-30、交接文档、匹配引擎交付状态）。
> 需求基线：TASK-001 ~ TASK-031 共 31 个模块 + 架构文档补充项（AI Advisor、Programmatic SEO、统一 Revenue Engine、Policy Engine 等）。

---

## 一、现状总览

### 1.1 代码库与环境事实

| 项 | 现状 | 备注 |
|---|---|---|
| 真实代码库 | `主要备份\上线网站`（后端+前端+admin） | ⚠️ 工作目录下的 `上线网站` 是空壳，`上线网站.worktrees` 是历史副本；**存在多份副本不一致，需 Sprint 0 统一** |
| 后端 | FastAPI，约 100+ 路由文件、300+ 服务文件、120+ 模型文件 | openapi 路径 1616 条（幽灵路由已清零） |
| 数据库迁移 | alembic 001~083 共 80+ 个迁移文件 | 实际运行版本停在 **080**；081/082/083 已写好待执行 |
| 表规模 | PostgreSQL 224 张表（Docker :5433）；SQLite 模式经 create_all 达 271 张 | 两套数据库并存，需统一 |
| 前端主站 | 官网页面齐全（产品/案例/行业/新闻/计算器/找产品/询价/采购），移动端 22 页 | ⚠️ 主站构建形态存在疑点：一处记录 Nuxt 生产构建成功，当前副本 `nuxt.config.ts` 已归档、根 package.json 指向 admin 依赖——**需实机确认** |
| 超管后台 | 独立应用（Vue3+Vite+Ant Design Vue），46 个模块目录 | 历史审计记录 400+ .vue 页（P0=0），当前副本统计约 100+ 视图，副本差异需统一确认 |
| 服务运行 | 后端 :8000、前端 :3000、Admin :5174、PG :5433、Redis :6379、n8n :5678 | 另有 SQLite 零依赖降级模式 |
| AI 模型 | **仍为 mock 模式**（MVP_LAUNCH=1，5 家 provider Key 全空） | 接入真实 AI 是激活全部 AI 功能的总开关 |
| 缺陷审计 | 累计修复 40/122 项，其中 18 项 P0/P1 支付/安全 Bug 已全部修复 | 剩余 82 项多为中低优先级 |

### 1.2 完成度总评

```
第一阶段 底座工程（TASK-001~013）：  约 75%
第二阶段 智能能力层（TASK-014~018）：约 50%
第三阶段 商业执行层（TASK-019~023）：约 60%
第四阶段 业务闭环层（TASK-024~031）：约 65%

总体代码完成度：约 65%
商业闭环（产品→匹配→询价→报价→成交→计费）：主干已通，差"智能化"和"自动化"两端
```

---

## 二、已完成 / 未完成清单（逐 TASK 对照）

图例：✅ 基本完成（可直接用）｜🟡 部分完成（有骨架/部分功能，差关键件）｜❌ 未开始或仅有概念

### 第一阶段：底座工程

| TASK | 模块 | 状态 | 代码证据 | 缺口（还要做什么） |
|---|---|---|---|---|
| 001 | 项目初始化 | ✅ | FastAPI 主应用、Dockerfile、docker-compose（含多套生产编排）、Makefile | 无 |
| 002 | 多租户 | 🟡 | tenants 表、tenant_id 贯穿业务表、`069_rls_tenant_isolation_pilot`（仅试点）、BUG-10 RLS 注入已修 | RLS 从试点推到全量核心表；跨租户隔离测试套件 |
| 003 | 私有数据空间 | ✅ | files.py、多存储后端（MinIO/R2/七牛）、uploads 目录规范 | 对象存储按租户前缀隔离的抽查测试 |
| 004 | 事件总线 | 🟡 | `core/event_bus.py`、events 包、event_bridge | 确认 Redis Streams 语义；事件契约（EventEnvelope）标准化 |
| 005 | Outbox 模式 | ❌ | 未发现独立 outbox 表/发布 Worker | 建 outbox_events 表 + 轮询发布 + 重试，保证"写库即发事件"最终一致 |
| 006 | 认证 | ✅ | auth.py（27KB）、oauth 登录、JWT、MFA 状态、统一后台登录 | 无重大缺口 |
| 007 | RBAC | 🟡 | roles/permissions、license 模块、合规扫描 | 权限矩阵收口：`resource.action` 全端点覆盖核查 |
| 008 | Task Schema | 🟡 | tasks/platform_job/deerflow_job/heal_job、paperclip 编排 | 统一任务主表：预算、DAG（parent_task_id）、幂等键 |
| 009 | Task 状态机 | 🟡 | 订单状态机已修（BUG-21）、任务基础流转 | 非法转移拦截、超时/重试/断点恢复（checkpoint/resume） |
| 010 | Harness Adapter | 🟡 | 自研 harness 服务簇（consistency/prompt/learning/scoring harness）、talking_stick | 按规格收敛为统一 `HarnessRuntime` Protocol + Mock 契约测试 |
| 011 | Hermes 调度 | 🟡 | `services/hermes/` 70+ 文件（command_center、runtime、daily_autonomous_cycle 等） | 功能多但耦合深；需冻结对外接口（Plan 版本化、Dispatch 可测试） |
| 012 | Model Gateway | ✅ | ai_engine、5 家 provider、ai_model_capability、provider_health、fallback | 接入真实 Key 后的熔断/成本记录验证 |
| 013 | Trace | 🟡 | trace_id 中间件、`072_agent_observability`、`074_step_cost_attribution` | trace_spans 全链路落库 + Token 成本按任务归集 |

### 第二阶段：智能能力层

| TASK | 模块 | 状态 | 代码证据 | 缺口 |
|---|---|---|---|---|
| 014 | ECC 经验中心 | 🟡 | ecc_integration 路由、ecc_expert_panel、site_builder_ecc_pipeline、`020_add_pgvector`、vector_search_service、rag 目录 | **pgvector 全链路未打通**：ecc_knowledge/ecc_sop 标准表、Embedding 入库、检索+Rerank、经验评估入库流程 |
| 015 | Skill 系统 | 🟡 | a2a_skill_marketplace_service（19KB）、foreign_trade_skills、hermes install_service | Skill 结构化（manifest+prompt+输入输出 schema）、版本化、热更新、执行接口统一 |
| 016 | MCP 连接层 | ❌ | 无标准 MCP Router/manifest 实现（仅根目录 .mcp.json 开发配置） | mcp_servers 表 + manifest 标准 + Router + 权限控制 |
| 017 | Plugin 系统 | 🟡 | hermes_plugin_installs 表（039）、install_service | Plugin Manager：注册/沙箱/生命周期/独立升级 |
| 018 | Agent 智能员工 | ✅ | agent_hub/agent_portal/agent_tree、agent_loop 目录、agent_observability、多角色 Agent | Agent 预算与执行次数上限的策略化（接 Policy） |

### 第三阶段：商业执行层

| TASK | 模块 | 状态 | 代码证据 | 缺口 |
|---|---|---|---|---|
| 019 | DeerFlow 深度执行 | 🟡 | deerflow_job 模型（024）、deerflow_ops_service、paperclip 编排 | Planner/Executor/Reviewer 三角色 + 完整状态机（CREATED→…→DONE）+ 断点恢复 |
| 020 | n8n 自动化 | 🟡 | n8n 实例已部署（:5678）、email_webhook/worldfirst_webhook 等回调存在 | 事件总线 → n8n 标准对接；"新 Lead→CRM→邮件→跟进"等场景工作流落地 |
| 021 | Browser Runtime | ✅ | egress 体系（路由 30KB）、browser_profile（030）、供应商（047）、JIT（042）、代理（043） | 租户级 Profile 隔离抽查；平台 ToS 合规白名单 |
| 022 | AI 建站 | 🟡 | site_build_workflow、site_builder_ecc_pipeline、site_patrol、site_audit、site_content_i18n（12 语言） | **"产品图片+一句话 → 10 分钟生成官网"端到端流程未打通/未验证** |
| 023 | SEO/GEO/AEO | ✅ | seo/geo/aeo 目录、EEAT、seo_matrix、schema_markup、关键词排名、百度站长、edge_cdn | 程序化 SEO 页面（国家×产品×场景）批量生成与质量门槛 |

### 第四阶段：业务闭环层

| TASK | 模块 | 状态 | 代码证据 | 缺口 |
|---|---|---|---|---|
| 024 | 内容生产 | ✅ | content（26KB）、content_master、media_factory、content_feedback_loop、content_scorer | 一个产品 → 20+ 内容资产的原子化流水线验证 |
| 025 | 全球分发 | 🟡 | publishers、publish_workers、publish_task、aitoearn、cross_platform_dashboard | 统一 DistributionChannel 接口（validate/publish/status/analytics）+ 5 渠道实测 |
| 026 | Lead 获客 | ✅ | lead_generation（20KB）、lead_pipeline、lead_search、lead_tools、prospect_lead、lead_score、intent_engine | Lead 评分权重用真实成交数据校准 |
| 027 | CRM | ✅ | crm_pipeline（19KB）、company/Account360、customer_operations（52KB）、emotion_crm、inquiries（29KB）、opportunities | 无重大缺口 |
| 028 | AI 销售 | 🟡 | nurture_cycle、social_nurture、outreach、email_queue/email_tracking、sales_task、ubrain | 开发信个性化 + 回复分析 + 合规（退订/限流）闭环实测 |
| 029 | Revenue 计费 | 🟡 | 080/081 revenue engine、082 wallet、083 token bonus、payment_pkg、finance、invoices、coupons、license；18 项支付 P0/P1 Bug 已修 | **七种模式统一计量**（Metering→Pricing→Billing→Invoice）；083 迁移未执行 |
| 030 | Experience Engine | 🟡 | attribution_service（22KB）、`075_intent_spec_learning_loop`、ai_learning_service、content_feedback_loop | 完整"行为→结果→经验"沉淀链路：成功/失败路径记录 + 经验入库评估 |
| 031 | Evolution Engine | ❌ | ai_learning 路由/服务、learning_harness、flywheel_workflow、continuous_iteration（零散要素） | **Draft→Evaluation→Canary→Approved→Production 安全进化流水线整体缺失** |

### 计划外但架构文档要求的缺口

| 缺口 | 说明 | 优先级 |
|---|---|---|
| **AI Advisor 前台超级入口** | 前端无独立 advisor/chat 页（仅 IM 浮窗）；架构文档定义其为"网站超级入口"：自然语言需求→识别→匹配→方案→询价 | P0 |
| Policy Engine（AgentShield） | Agent 工具调用的统一授权/配额/审批层；目前散落在各服务 | P1 |
| Credential Vault | 渠道 OAuth 凭证加密托管、短期凭证下发；Agent 不得接触原始密钥 | P1 |
| Evidence Engine | Agent 执行结果的证据链（截图/URL/时间戳/验证状态），"不信 Agent 自述" | P1 |
| Revenue Agent / 商业 KPI 看板 | 后台"AI Revenue OS"大盘（MRR/ARR/七管道收入/Agent ROI） | P2 |
| Skill Marketplace 商品化 | marketplace 服务已有骨架，缺定价/订购/结算接入 | P2 |

---

## 三、已知技术债与风险

| # | 问题 | 影响 | 处置 |
|---|---|---|---|
| 1 | 多份代码副本并存且不一致（主备份 / worktrees / 空壳 / fix-backup 多轮） | 容易改错库、进度误判 | Sprint 0 冻结唯一主干，其余归档 |
| 2 | SQLite 与 PostgreSQL 双轨、alembic 停在 080 | 迁移链断裂、生产不可靠 | 统一到 PG 并补跑 081~083 |
| 3 | 前端主站构建形态存疑（Nuxt vs Vite SPA） | 部署方式不确定 | Sprint 0 实机验证并记录结论 |
| 4 | AI 全 mock（Key 未配置） | 所有 AI 功能演示为假数据 | 配置至少 1 家真实 Key，MVP_LAUNCH=0 灰度 |
| 5 | Redis 降级模式下 Celery 不可用 | 异步任务受限 | 生产环境强制起 Redis |
| 6 | 剩余 82 项审计缺陷未修 | 多为中低危 | 纳入常规迭代消化 |
| 7 | metrics 端点需认证 | 监控采集不便 | 为采集器单独豁免或加内网地址白名单 |
| 8 | `config/prod/.env` 已有模板但生产容器未实测 | 上生产有隐患 | 随生产部署阶段验证 |

---

## 四、开发计划

### 总路线（约 8~10 周到达商业化可用，之后持续迭代）

```
Sprint 0（稳定统一，约1周）
  → 阶段A：商业闭环补强（P0，约2.5周）
    → 阶段B：智能架构补全（P1，约3周）
      → 阶段C：进化与生产化（P2，约2.5周）
        → 阶段D：平台化扩展（长期）
```

---

### Sprint 0：稳定与统一（第 1 周）

目标：消除多副本混乱，把环境固定到"单一真相"，为后续开发铺平。

| # | 任务 | 交付物 | 验收标准 | 预估 |
|---|---|---|---|---|
| 0.1 | 冻结唯一代码主干 | 主干指定为 `主要备份\上线网站`（或经 git 对比后合并 worktrees 的更新），其余目录改名归档并写 `代码库位置.md` | 全团队只在主干提交；归档目录只读 | 0.5 天 |
| 0.2 | 数据库统一到 PostgreSQL | Docker PG :5433 为唯一开发库；执行 alembic 081/082/083 | `alembic current` = 083；wallet/token bonus 表可查；SQLite 仅作离线降级保留 | 1 天 |
| 0.3 | 前端构建形态确认 | 实测主站 `npm run build` + 产物启动，记录结论（Nuxt SSR 或 Vite SPA） | 首页/计算器/询价页生产模式下 200 且首屏 <1s | 1 天 |
| 0.4 | 接入真实 AI（灰度） | 配置 1~2 家 provider Key；`MVP_LAUNCH=0` 仅在开发环境 | 匹配引擎/内容生成返回真实模型结果；mock 开关可随时回退 | 0.5 天 |
| 0.5 | 服务一键启动脚本收口 | 统一 `启动开发环境` 脚本（PG+Redis+后端+前端+admin+n8n） | 冷启动一条命令全绿，健康检查全通过 | 0.5 天 |
| 0.6 | 建立回归基线 | 关键链路自动化冒烟脚本（匹配→询价→报价→商机→计费） | 每次合并前跑通 | 1 天 |

### 阶段 A：商业闭环补强（第 2~4 周，P0）

目标：把"客户感知最强、直接决定转化和收入"的缺口补齐。

| # | 任务 | 对应缺口 | 交付物与验收标准 | 预估 |
|---|---|---|---|---|
| A1 | **AI Advisor 超级入口**（前台） | 计划外缺口 | 新建 `/advisor` 页：自然语言输入 → 意图识别（国家/建筑类型/面积/材料/时间）→ 调用匹配引擎+计算器 → 输出结构化方案（产品+厚度+防火等级+估算成本）→ 一键转询价。验收：输入"20,000 m² steel warehouse in Saudi Arabia, rock wool" 返回完整方案并可提交 | 4~5 天 |
| A2 | **一键建站端到端** | TASK-022 | 打通"产品图片+一句话 → Vision 提取 → 品牌/结构/文案 → 多语言官网预览 → 发布"全流程；验收：10 分钟内生成含首页/产品/案例/博客/询价页的可访问站点（真实 AI，可人工审核后发布） | 5~7 天 |
| A3 | **Outbox 事件一致性** | TASK-005 | outbox_events 表 + 发布 Worker + 重试/死信；验收：业务写库后事件 5s 内发布，宕机重启后不丢不重（幂等键） | 2~3 天 |
| A4 | **DeerFlow 完整状态机** | TASK-019 | deerflow_tasks 状态机（CREATED→PLANNING→EXECUTING→REVIEW→WAIT_HUMAN→DONE/FAILED）+ Planner/Executor/Reviewer 三角色 + 断点恢复；验收：杀掉进程后任务可从断点续跑 | 4~5 天 |
| A5 | **n8n 场景工作流** | TASK-020 | 事件总线 ↔ n8n Webhook 标准对接；落地 3 条工作流：新 Lead→评分→通知销售；新内容→审核→分发；每日市场新闻→AI 摘要→入库。验收：事件触发后自动完成且可查运行记录 | 3~4 天 |
| A6 | **ECC 向量检索链路** | TASK-014 | ecc_knowledge/ecc_sop 表 + Embedding 入库 + pgvector 检索 + Rerank + `POST /api/ecc/search`；验收：输入任务描述返回相关经验与 SOP，Top5 命中率人工抽检 ≥70% | 3~5 天 |
| A7 | 迁移 083 + Revenue 表对齐 | TASK-029 | 083 执行、purchased_token_bonus 生效、钱包/台账抽查 | 已含在 0.2，此处做计费链路回归 | 0.5 天 |

**阶段 A 里程碑验收**：客户从 Advisor 输入需求 → 拿到方案 → 提交询价 → 自动评分入 CRM → 触发销售跟进工作流，全程真实 AI、可追踪。

### 阶段 B：智能架构补全（第 5~7 周，P1）

目标：补齐"可插拔、可治理"的架构件，让 Agent 体系安全可扩展。

| # | 任务 | 对应缺口 | 验收标准 | 预估 |
|---|---|---|---|---|
| B1 | 标准 MCP Router | TASK-016 | mcp_servers 表 + manifest 标准 + 统一调用入口 + 工具权限；验收：Agent 经 Router 调用至少 2 个外部工具（搜索/CRM），无直连 | 3~4 天 |
| B2 | Plugin Manager | TASK-017 | 插件注册/校验/加载/监控/升级生命周期 + 沙箱运行；验收：动态安装/卸载插件不影响主服务 | 4~5 天 |
| B3 | Skill 版本化与热更新 | TASK-015 | Skill 结构规范（manifest+prompt+schema）+ 版本管理 + 灰度发布；验收：新版本 Skill 可 5%→100% 灰度，可一键回滚 | 3~4 天 |
| B4 | Task 统一状态机与断点恢复 | TASK-008/009 | 任务主表统一（预算/幂等键/父子任务）+ 非法转移拦截 + checkpoint；验收：非法转移返回 TASK_INVALID_STATE，长任务可恢复 | 3~4 天 |
| B5 | Experience Engine 完整链路 | TASK-030 | 行为/结果/Trace 三层数据归集 → 经验提炼 → 评估后入库（不直接学习原始数据）；验收：一次成交/失败案例自动沉淀为可检索经验条目 | 4~5 天 |
| B6 | Policy Engine + Credential Vault | 计划外 | Agent 工具调用统一走授权→策略→配额；渠道凭证加密托管、短期下发；验收：Agent 无法越权调用未授权工具、无法读取其他租户凭证 | 4~5 天 |
| B7 | Trace 全链路 + 成本归集 | TASK-013 | trace_spans 落库、每任务 Token 成本准确；验收：任一任务可回放完整 span 树与费用 | 2~3 天 |

### 阶段 C：进化与生产化（第 8~10 周，P2）

| # | 任务 | 对应缺口 | 验收标准 | 预估 |
|---|---|---|---|---|
| C1 | **Evolution Engine MVP** | TASK-031 | Draft→Evaluation→Canary→Approved→Production 流水线：系统从经验中生成 Skill/策略改进草稿，自动评估后灰度；验收：至少一次"改进草稿→评估→5% 灰度→全量"完整闭环，且人工可否决 | 5~7 天 |
| C2 | Evidence Engine | 计划外 | Agent 执行结果强制附证据（截图/URL/状态/时间）+ 验证器；验收：发布类任务无证据不能标记成功 | 3~4 天 |
| C3 | RLS 全量 + 隔离测试套件 | TASK-002 | 核心业务表全量启用 RLS；验收：Tenant A/B 交叉访问全部 DENY（API/DB/存储/缓存/事件五层） | 3~4 天 |
| C4 | 生产部署 | 运维 | 生产 docker-compose 实测（PG 高可用/Redis/备份/监控）、`config/prod/.env` 实装、灰度发布演练 | 3~4 天 |
| C5 | 可观测性与告警 | 运维 | metrics 采集打通（采集器豁免）、核心指标看板（任务成功率/降级率/成本）、告警规则 | 2~3 天 |
| C6 | 剩余审计缺陷消化 | 技术债 | 82 项按优先级分批清零（高危优先） | 贯穿 |
| C7 | 演示用真实业务数据 | 运营 | 产品/案例/认证等真实资料入库（**严禁编造**）；验收：演示链路全真实数据 | 2 天 |

### 阶段 D：平台化扩展（长期，商业化验证后）

| 方向 | 内容 |
|---|---|
| 七种收入统一计量 | Metering→Pricing→Billing 全打通，七管道收入在 Revenue OS 大盘分列 |
| Skill Marketplace 商品化 | 技能定价/订购/结算/分成 |
| 多租户官网平台化 | 从"建材单站"复制为"企业各自独立官网"的 SaaS 形态 |
| 行业模板复制 | 建材 → 机械设备 → 工业品，行业专家库（ECC）模板化 |
| Agent KPI 与 Revenue-per-Agent | 每个 Agent 的成本/成功率/归因收入核算 |

---

## 五、开发规范（承接 Codex 规格书硬性规则）

1. 任何第三方 AI Runtime 必须 Adapter 化，业务层不直接依赖具体实现；
2. 所有业务数据带 tenant_id，数据库层 RLS 双保险；
3. 所有 Agent 任务可追踪（Trace），所有模型调用记成本；
4. 长任务必须可恢复（断点+重试+死信）；
5. 所有 Tool 有权限、所有 Agent 有执行次数与预算上限；
6. Skill 必须版本化；经验入库必须经评估；
7. AI 不得直接修改生产核心配置；单组件故障不得拖垮全系统；
8. **红线：绝不编造业务/测试/认证数据；编辑前备份；只改主干工作区。**

每个任务交付必须附：Implemented / Files changed / Migrations / API changes / Tests / Security checks / Known issues / Rollback plan / PASS-FAIL。

---

## 六、最终验收标准

**核心链路**：创建租户 → 上传产品 → 创建 AI 任务 → 调度执行 → 生成 Trace → 结果落库 → 任务完成。

**商业闭环**：自然语言 + 产品图片 → AI 建站 → 内容/视频 → SEO/GEO/AEO → 多平台分发 → 获客 → Lead 评分 → CRM → 开发信 → 报价 → 成交 → 数据沉淀 → AI 进化。

**安全验收**：跨租户访问在 API/Repository/数据库 RLS/对象存储/缓存/事件/Trace/运行时八层全部 DENY。

---

## 附录：代码库位置与启动

```
真实代码主干：主要备份\上线网站
  后端   backend/            （FastAPI，alembic 迁移 001~083）
  前端   frontend/           （主站）
  超管   frontend/admin/     （Vue3+Vite，46 模块）

启动（PostgreSQL 模式）：
  .\启动开发环境-正确版.bat   （或 start-all-services-fixed.ps1）
  后端 :8000 / 前端 :3000 / Admin :5174 / PG :5433 / Redis :6379 / n8n :5678

待办提醒：迁移 083 需在 Docker 运行时执行；生产部署前补 config/prod/.env 实测。
```
