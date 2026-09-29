# 功能地图 · backend/app 按包（自动生成）

总 py 文件 1241 · services 739

## 0. services 包一览

| 包 | 文件数 | 职责推断（取包内代表文件 docstring） |
|----|------:|--------------------------------------|
| `(flat)` | 271 | Publish Service - handles content publis; -*- coding: utf-8 -*-; -*- coding: utf-8 -*- |
| `hermes` | 105 | 专家巡检注册表 — 基于 ECC (Everything Claude Code; 专家执行注册表 — 让专家真正执行专职工作。 基于 ECC (Everythin; 摸金校尉 · 挣钱大赛 + 专家记忆 — 持续盈利者不下线，越赛越有 exper |
| `ubrain` | 83 | UBrain v1 — 意图识别 + 工具调用（走现有 API 数据或 M0 规; 开发信质量评估 + A/B 测试 + 获客流程标准化 — FIX-58 & FI; WhatsApp Business Cloud API 正式接入 — FIX-5 |
| `foreign_trade` | 44 | 形式发票 PI / 商业发票 CI / 装箱单 PL / 原产地证 CO / 分; PI / 报价单导出 — DOCX（OOXML）与可打印 HTML。; 外贸标杆能力 — 智能体编排门面（UBrain / Hermes / DeerF |
| `cross_border` | 32 | 出海视音频数字人工厂 — 听写 / 多语种翻译 / 原声克隆 / 嘴型对齐 / ; 视频/音频 → 中文听写（Whisper 多后端 + 讯飞 LFASR 直传，长; 开源视频本地化上游注册表 — 对标 Vozo / 山海智影；智能优先级见 OPT |
| `talking_stick` | 19 | Talking-Stick 验证Agent 负责复现漏洞、构造POC、剔除误报，; Talking-Stick 规则引擎 负责应用检测规则并识别漏洞; Talking-Stick 报告生成器 负责生成多格式的安全审计报告 |
| `geo` | 15 | GEO 技术雷达 v2 — 定时抓取 GEO/SEO 最新论文、论坛、白帽技术、; GEO 写作策略 v3 — Princeton 引用战术 + arXiv 202; 全球出海国家与港口矩阵着陆页引擎 (Programmatic Geo-Matri |
| `registry` | 11 | Skill 注册表服务（轮17-1/17-2）。 替代 SkillRegistr; 技能包扫描解析器 —— 把磁盘上的 SKILL.md 技能包变成编排可消费的索引; MCP 注册表服务（轮17-3；轮19 扩展 connector-manifes |
| `platforms` | 9 | 微博发布适配器 — 真实对接微博开放平台 API。 支持: - OAuth 2.; 百度百家号发布适配器 — 真实对接百家号开放平台 API。 支持: - OAut; 今日头条发布适配器 — 真实对接头条号开放平台 API。 支持: - OAuth |
| `publish_workers` | 9 | social-auto-upload CLI Worker — 抖音/快手/B站; SAU HTTP Sidecar 客户端 — 远程 Worker 机执行 Pla; 发布分层路由 — 集 SAU / biliup / xhs-mcp / 原生 / |
| `seo` | 9 | 产品 AI SEO 内容与差异化（千人千面）生成服务。 依托 Google EE; SEO 收录复检 — 供 API 与 Celery 共用。; 搜索引擎收录探测 — Baidu site: 查询（失败可降级 HTTP 探活） |
| `wangcai` | 8 | WangcaiRouter 总编排（实施指南 §0.1 链路；阶段 1 收口，不; 旺财 N1 意图识别层（实施指南 §1，总纲 §7A 阶段 1）。 设计（指南 ; 旺财 N3/N7 持久化接线（迁移 094：wangcai_sessions + |
| `browser_runtime` | 7 | Browser Runtime 真实执行器（轮25-C，Playwright 真; Browser Runtime Policy 闸门（总纲 §4.7 + 既有 P; 证据回传模型（总纲 §4.7 P5：合规执行须留证）。 每次 Browser R |
| `deerflow` | 7 | DeerFlow 子任务执行器。 负责执行规划器生成的子任务，每个子任务有独立的; DeerFlow 任务规划器。 将复杂任务拆解为可独立执行的子任务，生成执行计划; DeerFlow 断点管理器。 负责保存和恢复任务的执行状态（checkpoin |
| `moss_vl` | 7 | MOSS-VL 官方仓库追踪、双缓冲热更新与版本回滚管理器。 工业级模型版本生命; MOSS-VL-Realtime 官方实时流式会话 API。 100% 对齐官方; MOSS-VL 官方开源仓库自动化同步与环境检测工具。 |
| `paperclip` | 7 | Paperclip 核心编排服务。 管理公司、Agent、目标、任务的全生命周期; Paperclip 心跳调度引擎。 以 daemon 线程定时扫描所有 hear; Paperclip 租户业务上下文 — 聚合产品/视频/询盘/行业数据供 220 |
| `pipeline` | 7 | Pipeline S3 接线（总纲 §6.4 / V1.7 待办）：存量质量件注; 清洗关卡 CleanseGate（总纲 §6.4-1）。 职责：发布物进入复核前; 四链路业务侧关卡接入（总纲 §6.4/§6.6：文章/视频/邮件/多平台分发）。 |
| `crawlers` | 6 | ECommerceCrawlers 爬虫配方注册表 — 映射 GitHub 子项; ECommerceCrawlers 智能层 — 大白话状态、自动补全合规字段、一; ECommerceCrawlers 合规门禁 — 无 Sidecar / 无授权 |
| `tasks` | 6 | ai_tasks → Hermes 编排桥（打通中央断点；总纲 §4.6 / 轮; 统一任务控制面服务（总纲 §4.6-1/§4.6-2 / §8 082；轮23 ; Paperclip → ai_tasks 影子双写桥（总纲 §4.6-1 收编过 |
| `agent_loop` | 5 | 增长工具 Agent 工作流 — 热词 → 成稿 → 质检 → 引流监测快照。; Agent run 持久化与查询。; Agent run 状态存储（内存 + 可选 Redis）。 BUG-15 修复 |
| `ai` | 5 | AI数据洞察服务 - 基于真实LLM调用 功能： - 异常检测（基于统计规则 +; AI推荐系统服务 - 基于真实协同过滤算法与LLM解释生成 功能： - 协同过滤; AI引擎 v2 - 基于真实LLM调用的完整实现 功能： 1. AI内容生成（真 |
| `analytics` | 5 | UserActionAnalyzePlatform 智能层 — 中文状态与一键分; UserActionAnalyzePlatform Sidecar HTTP 客; UserActionAnalyzePlatform 合规门禁。 |
| `egress` | 5 | 出口 IP — manual 运营录入 / mock 演示 / asocks J; IPRoyal Reseller API 客户端 — 静态住宅IP自动采购。; IPRoyal 缓冲池适配器 — 从预购池中分配IP，非实时下单。 |
| `evolution` | 5 | 核心进化引擎 — 编排完整闭环。 流程： 数据收集 → 经验沉淀 → Skill; 灰度发布 — Draft → Evaluation → Canary → App; Skill/SOP 版本管理 — 语义化版本 + 状态机。 管理 Skill 和 |
| `feishu` | 5 | -*- coding: utf-8 -*-; -*- coding: utf-8 -*-; -*- coding: utf-8 -*- |
| `model_gateway` | 5 | 成本记账（总纲 §4.6）：每次 LLM 调用写 model_call_ledg; 能力路由：required_capabilities + 四维信号 → ai_e; Model Gateway 门面（总纲 §4.6）。 复用既有 get_ai_e |
| `n8n` | 4 | n8n 工作流注册表。 管理 n8n 工作流的注册、查询、启用/禁用，存储 wo; n8n 工作流触发器。 向 n8n 发送 Webhook 请求触发工作流，支持：; n8n Webhook 接收服务。 接收 n8n 工作流的回调请求，提供： -  |
| `payment_pkg` | 4 | 通用支付服务（对接订单模型） 本模块只负责支付订单管理、渠道下单、回调处理与入账; 微信支付服务（Native 扫码支付 + 回调验签 + 退款） 本模块只负责微信; 支付回调验签严格模式 — 单一权威判定。 全仓所有验签 / 严验相关逻辑都必须通 |
| `trace` | 4 | 统一 Trace 服务 — 链式追踪的写入/读取与记分卡聚合（总纲 §4.6-7; 终态钩子 — 任务终态接线至经验飞轮（总纲 §4.6-7 / §6.6 P3）。; Canary 发布门禁（总纲 §1.3 第4条 / §6.6 P3 / E14） |
| `deepseek_harness` | 3 | DeepSeek Harness 客户端（懒加载官方 SDK，绝不污染导入期）。; DeepSeek Harness 接入配置（纯标准库，无重依赖，保证本包可随时安; DeepSeek Harness 外层智能体运行时接入包。 把开源 "一切皆插件 |
| `goodjob` | 3 | trade-documents 桥 · 单证生成委派 GoodJob（批次 B）; customer_pool 投影同步 · UJ 真相 → GoodJob 工作副; GoodJob 附属桥服务（批次 B：customer_pool 投影 + 单证 |
| `matching_engine` | 3 | Product Finder 匹配引擎（纯函数，不依赖 FastAPI / SQ; Product Finder 匹配引擎 — 请求 / 响应 Pydantic 模; Product Finder 匹配引擎包。 暴露 ``MatchingEngin |
| `site_builder` | 3 | 一键建站核心编排器。 串联 Vision 分析、结构生成、多语言内容、SEO 优; 一键建站各步骤 Prompt 模板。 每个步骤有独立的 system / use; 一键建站编排服务 — 端到端站点生成流水线。 |
| `vault` | 3 | 凭证库服务（总纲 §3.1/§8 迁移 087；轮20）。 统一密钥入库：sto; 凭证库加密层（总纲 §3.1/§8 迁移 087；轮20）。 - 默认后端 ae; 凭证库包（总纲 §8 迁移 087；轮20）。 |
| `adapters` | 2 | Trade AI Agent 适配器（总纲 §5.2：代码级嫁接，MIT）。 来; Adapter 层（Execution Plane 平级适配器集合，总纲 §3. |
| `annex` | 2 | 附属统一登录票据服务 · UJ 为唯一身份源. 设计出处：uj-annex-in; 附属统一身份域：UJ 为唯一身份源（annex_ticket 短时票据，§9.3 |
| `billing` | 2 | 统一计量埋点与账单对账（总纲 §4.6-8 / §6.6 P4 / §7.6） ; 订阅到期倒计时 · 纯函数服务（零迁移、零外部依赖）. 数据源均为既有字段：te |
| `calculators` | 2 | 工程计算器引擎 — 纯函数，无 Web 依赖，可单元测试。 包含： - ther; Calculator 包 — 工程计算器（Thermal / Fire Prot |
| `orchestrator` | 2 | 商业闭环编排器。 从产品输入到成交的完整链路: 自然语言+产品图片 → AI建站; 商业闭环编排器 — 串联从产品输入到成交的完整链路。 |
| `policy` | 2 | Policy Engine：统一策略裁决（总纲 §3.1/§7.2/§6.6 P; Policy Engine 包（总纲 §3.1/§6.6 P2；轮20）。 |
| `facade` | 1 | 大模型网关防腐层 (Anti-Corruption Layer) - 改造 10 |
| `marketing` | 1 | Google Merchant Center (GMC) 官方规范商品 XML/ |
| `media` | 1 | VID-11：多平台标题/描述长度适配。 |

## (扁平根目录 services/*.py) · 271 文件

| 主题前缀 | 文件数 | 代表文件 |
|----------|------:|----------|
| _other | 123 | `__init__.py`, `_scan_long.py`, `acme_service.py`, `acquisition_outreach_service.py` |
| media | 14 | `media_cleanup_scheduler.py`, `media_cloud_upload_service.py`, `media_cuplayer_service.py`, `media_factory_service.py` |
| tenant | 13 | `tenant_aitoearn_slot_service.py`, `tenant_lifecycle_service.py`, `tenant_llms_txt_service.py`, `tenant_onboarding_service.py` |
| ai | 12 | `ai_config_service.py`, `ai_engine.py`, `ai_invocation_service.py`, `ai_key_probe.py` |
| platform | 9 | `platform_account_service.py`, `platform_alignment_service.py`, `platform_catalog.py`, `platform_compliance_checker.py` |
| site | 9 | `site_ai_service.py`, `site_audit.py`, `site_content_array_i18n.py`, `site_content_bridge.py` |
| trade | 9 | `trade_intel_commercial_service.py`, `trade_intel_comtrade_client.py`, `trade_intel_customs_service.py`, `trade_intel_data.py` |
| geo | 7 | `geo_agents.py`, `geo_alert_service.py`, `geo_engine_service.py`, `geo_lead_service.py` |
| content | 6 | `content_adapter.py`, `content_feedback_loop.py`, `content_master_publish_service.py`, `content_optimizer.py` |
| publish | 6 | `publish_capability_registry.py`, `publish_dispatch_service.py`, `publish_queue_service.py`, `publish_readiness_service.py` |
| agent | 5 | `agent_aggregation_service.py`, `agent_commission_service.py`, `agent_hub_service.py`, `agent_node_write_service.py` |
| payment | 5 | `payment_balance_service.py`, `payment_compensation_service.py`, `payment_ops_audit_service.py`, `payment_ops_service.py` |
| aitoearn | 4 | `aitoearn_engage_send_service.py`, `aitoearn_hub_service.py`, `aitoearn_local_proxy.py`, `aitoearn_publish_adapter.py` |
| email | 4 | `email_dns_auth_service.py`, `email_recovery_service.py`, `email_service.py`, `email_tracking_service.py` |
| inquiry | 4 | `inquiry_assignment_audit_service.py`, `inquiry_lead_assignment_service.py`, `inquiry_push_service.py`, `inquiry_weekly_service.py` |
| ops | 4 | `ops_autopilot_scheduler.py`, `ops_backup_service.py`, `ops_expert_autonomy_service.py`, `ops_readiness_alert_service.py` |
| video | 4 | `video_bind_hub_service.py`, `video_publish_orchestrator.py`, `video_publish_router.py`, `video_seo_geo_aao_optimizer.py` |
| client | 3 | `client_bff_service.py`, `client_today_service.py`, `client_today_three_service.py` |
| product | 3 | `product_content_ai_service.py`, `product_image_storage_service.py`, `product_service.py` |
| order | 2 | `order_addon_service.py`, `order_payment_sync_service.py` |
| sales | 2 | `sales_channel_rehearsal_service.py`, `sales_push_service.py` |
| seo | 2 | `seo_analyzer.py`, `seo_report_service.py` |
| unified | 2 | `unified_admin_login.py`, `unified_geo_score_service.py` |
| user | 2 | `user_service.py`, `user_wallet_service.py` |
| wangcai | 2 | `wangcai_reply_locale.py`, `wangcai_trade_service.py` |
| alert | 1 | `alert_service.py` |
| attribution | 1 | `attribution_service.py` |
| backup | 1 | `backup_service.py` |
| cache | 1 | `cache_service.py` |
| commission | 1 | `commission_rule_service.py` |
| compliance | 1 | `compliance_scanner.py` |
| cross | 1 | `cross_platform_dashboard_service.py` |
| foreign | 1 | `foreign_trade_ecosystem_service.py` |
| lead | 1 | `lead_enrichment.py` |
| rfq | 1 | `rfq_service.py` |
| ssl | 1 | `ssl_certificate_service.py` |
| super | 1 | `super_admin_path_audit.py` |
| token | 1 | `token_service.py` |
| whatsapp | 1 | `whatsapp_bridge.py` |
| workflow | 1 | `workflow_canvas_service.py` |

## services/hermes · 105 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `__init__.py` | 4 | Hermes — 内部插件平台（对外品牌：旺财插件市场）。 |  |
| `__init__.py` | 16 | Hermes 内嵌 agency-orchestrator 专家角色库。 |  |
| `__init__.py` | 45 | Hermes Executor Plugins Package. Automatically imports and registers built-in executors. |  |
| `a2a_skill_marketplace_service.py` | 594 | Hermes A2A 技能市场 — Brief→ECC→部门路由 沉底为可调用 Agent 技能。 合规：只读探测 + 虚拟积分结算预览；禁止真 SMTP/群发/未授权爬取。 财迷 | load_a2a_registry, list_a2a_agents, get_agent, list_a2a_skills, crystallize_a2a_skill, lis |
| `accio_executor.py` | 167 | Accio Executor Plugin for Hermes — 销售飞轮（接真实服务）。 承载实现（已存在，本插件只做契约适配，**不再返回硬编码假数据**）： servic | AccioExecutor |
| `ai_engine_executor.py` | 92 | AI Engine Executor Plugin for Hermes Orchestration. 把既有 AI 能力层（DeepSeek Harness / ubrain / | AiEngineExecutor |
| `alert_dispatcher.py` | 379 | Hermes 运维告警 — 飞书 Webhook（巡站 / 技术雷达 / 异常）。 | should_send_alert, mark_alert_sent, send_feishu_card, send_wechat_markdown, dispatch_ops_a |
| `anysearch_probe_service.py` | 168 | AnySearch 外网探测 — Hermes 研究员 hourly / 批量脚本共用。 | parse_anysearch_output, run_anysearch, topic_search_query, synthesize_finding_extension, e |
| `base.py` | 124 | Base Executor Contract for Hermes Orchestration. 三份契约之一（见 docs/架构设计-智能编排内核-任务图驱动-2026-09-0 | ExecutorContext, BaseExecutor, ExecutorRegistry |
| `billing_executor.py` | 108 | Billing Executor Plugin for Hermes Orchestration. 把既有 billing services（meter_event / subsc | BillingExecutor |
| `brand_audit_service.py` | 199 | COMP-02 品牌抽检：扫描租户/落地页可见文案是否泄露禁词。 | audit_brand_leaks |
| `brand_guard.py` | 97 | 对外文案脱敏：禁止第三方 Agent 产品商标进入用户可见字段。 | sanitize_public_copy, sanitize_public_data |
| `browser_companion.py` | 84 | 浏览器伴侣插件 — 本地 Chrome/Edge 扩展，不进服务端执行。 | is_browser_companion, list_browser_companions, browser_companion_hint |
| `browser_executor.py` | 109 | Browser Executor Plugin for Hermes Orchestration. 把既有 browser_runtime（取证/爬取）包成 ExecutorReg | BrowserExecutor |
| `command_center.py` | 464 | L0 超管司令部 — 聚合 Hermes / DeerFlow / SEO / 视频 Worker 态势（只读）。 |  |
| `command_center_cache.py` | 265 | 司令部快照缓存 — Redis + Stale-While-Revalidate + 云端后台预热。 生产路径目标：用户打开司令部 <1s（命中 Redis 预热缓存），后台异步刷 | CommandCenterPrewarmScheduler, warm_command_center_snapshot, invalidate_command_center_cac |
| `companion_launch.py` | 148 | 优丁平台专属 · 浏览器伴侣唤起（内容仅来自本平台任务，不可独立外发）。 | CompanionLaunchError, build_video_companion_payload, build_article_companion_payload, comp |
| `consistency_harness_service.py` | 323 | 一致性控制服务 (Consistency Harness) 确保AI生成内容与品牌风格、产品参数、技术规范的一致性。 支持：品牌声音一致性、产品信息一致性、技术参数校验、跨平台内容 | ConsistencyHarnessService |
| `content_executor.py` | 130 | Content Executor Plugin — 内容页创建与发布。 承载实现（已存在）： services/content_service.ContentPageService | ContentExecutor |
| `content_knowledge_graph_service.py` | 441 | 内容知识图谱服务 (Content Knowledge Graph) 构建产品、行业、技术参数之间的知识关联网络。 支持：产品分类体系、技术参数关联、行业标准映射、内容推荐。 | ContentKnowledgeGraphService |
| `daily_autonomous_cycle.py` | 641 | 每日自主运营闭环 — 串联所有步骤。 运行顺序： 1. 技术雷达扫描 → 更新策略 (⑤) 2. GEO 探测 → 品牌曝光检测 3. SEO 内容生成 → GEO 评分 → 不合 | StepResult, DailyAutonomousCycleScheduler, run_daily_autonomous_cycle |
| `daily_rank_ops.py` | 312 | Hermes 每日排名攻坚 — 多引擎 probe + 战术雷达 + ECC 评审 + 回归告警。 | run_hermes_daily_rank_cycle_async, run_hermes_daily_rank_cycle, load_rank_ops_snapshot |
| `deerflow_executor.py` | 134 | DeerFlow Executor Plugin for Hermes Orchestration. | DeerflowExecutor |
| `deerflow_ops_service.py` | 96 | DeerFlow 超管运维：全平台队列分页 + SLO 指标。 | list_ops_jobs, deerflow_slo_snapshot |
| `ecc_expert_panel.py` | 382 | Hermes ECC 专家人格评审 — 对齐 docs/技术栈-智能体-MCP-调度表，只读测试、不装依赖。 | EccExpert, review_candidate, review_all, panel_meta |
| `egress_executor.py` | 115 | Egress Executor Plugin — 静态 IP 槽位分配 + 指纹环境。 对应业务链第 7 环「分配」：给租户的社媒账号分配**独立静态 IP** 与**指纹环境** | EgressExecutor |
| `engagement_executor.py` | 121 | Engagement Executor Plugin for Hermes Orchestration. 把既有 aitoearn_engage_send_service（社媒互动 | EngagementExecutor |
| `experience_engine.py` | 124 | 经验沉淀自进化引擎（Experience Engine）。 反哺外层 DSH 和内层 Hermes：从每次执行中提取经验，统计成功率与耗时， 生成改进建议，辅助后续任务校验与意图识 | ExperienceRecord, ExperienceEngine, get_engine |
| `expert_execution_registry.py` | 1327 | 专家执行注册表 — 让专家真正执行专职工作。 基于 ECC (Everything Claude Code) 技能体系，为每个专家角色定义实际执行操作： - SEO专家：执行关键词 | execute_seo_specialist, execute_content_creator, execute_growth_hacker, execute_security_e |
| `expert_inspection_registry.py` | 1543 | 专家巡检注册表 — 基于 ECC (Everything Claude Code) 真实技能体系实现专家功能。 ECC 包含：36个专用子智能体、271+个技能模块、92+个命令  | inspect_seo_specialist, inspect_content_creator, inspect_growth_hacker, inspect_cross_bord |
| `flywheel_workflow.py` | 308 | Hermes 卖货飞轮闭环 — 研究 → 找客 → 编排（内部调度，对外脱敏）。 | run_closed_loop_flywheel, public_flywheel_status |
| `forum_executor.py` | 113 | Forum Executor Plugin for Hermes Orchestration. 把既有 forum_webhook_service / forum_sidecar_ | ForumExecutor |
| `github_ecosystem_scout_service.py` | 523 | GitHub 生态侦察 — 代用户翻找开源项目，映射系统短板，推送 PM Inbox（不自动安装）。 研究员/ECC 职责：按 catalog 缺口 + 关键词搜索 GitHub， | search_github_repositories, run_github_ecosystem_scout, save_scout_snapshot, load_scout_sn |
| `goodjob_crm_executor.py` | 358 | GoodJob CRM Executor — 接真实 HTTP 桥（不再返回硬编码假单证）。 ⚠️ 本文件此前是**危险 mock**：硬编码了假的卖家抬头、**假银行账号与假 S | GoodJobCrmExecutor |
| `greedy_agency_orchestrator_service.py` | 399 | Hermes 财迷疯 × agency-agents-zh — 专家库编排（SaaS 内嵌 220+ 角色）。 | load_greedy_agency_config, greedy_agency_status, plan_greedy_orchestration, run_greedy_orc |
| `greedy_avatar_constitution.py` | 183 | 财迷疯分身宪法（摸金校尉）— 与 SaaS Hermes 维护宪法隔离。 SaaS Hermes：巡站维护，只读 + 建议（maintenance_constitution）。 财 | GreedyAvatarViolation, load_greedy_charter, is_greedy_action_forbidden, assert_greedy_acti |
| `greedy_contest_memory_service.py` | 1014 | 摸金校尉 · 挣钱大赛 + 专家记忆 — 持续盈利者不下线，越赛越有 experience。 | load_contest_config, get_arena_state, tick_endurance_arena, get_endurance_status, get_role |
| `greedy_cumulative_personality_service.py` | 368 | 全球累计（周/月/年）+ 摸金打江山人格（羞耻感·奋发图强·比上次更强）。 | period_keys, evaluate_personality, get_cumulative_stats, record_cumulative_settlement, app |
| `greedy_endurance_scheduler.py` | 132 | 7×24 持久耐力赛调度 — 每小时检查 30 天擂台是否满期并轮转。 | GreedyEnduranceScheduler |
| `greedy_hub_service.py` | 92 | 摸金校尉总控 Hub — 一次拉取累计/大赛/耐力/闭环/队列/生存脉搏。 | greedy_hub_snapshot |
| `greedy_production_readiness_service.py` | 326 | 摸金校尉 · 生产就绪检查 + 平台自营租户 bootstrap。 | ensure_greedy_publish_tenant, resolve_bootstrap_tenant_id_from_store, bootstrap_publish_pl |
| `greedy_project_board_service.py` | 501 | 挣钱项目看板 — 从大赛轮次、专家归因收入、L4 审核历史聚合，禁止写死假数。 | get_project_earnings_board |
| `greedy_publish_queue_service.py` | 265 | L4 发布队列人工审核 — 通过/驳回 + 审核历史。 | get_publish_review_history, review_publish_queue_item |
| `greedy_revenue_loop_scheduler.py` | 187 | 摸金校尉 · 搞钱闭环日调度 — 与 SaaS Hermes 巡站调度隔离。 | GreedyRevenueLoopScheduler |
| `greedy_revenue_loop_service.py` | 361 | 财迷疯 · 摸金校尉 — 搞钱商业闭环（调研→编排→生产→发出→卖出跟踪→收款 KPI）。 仅 platform_survival scope；不触 SaaS 租户主流程。宪法：g | run_greedy_revenue_loop_async, run_greedy_revenue_loop, get_greedy_publish_queue, greedy_r |
| `greedy_survival_digest_scheduler.py` | 152 | 摸金校尉 · Survival 周报调度 — 每周一推送飞书（全球累计 + 人格 + 大赛）。 | GreedySurvivalDigestScheduler |
| `greedy_survival_digest_service.py` | 164 | 摸金校尉 · Survival 周报 — 飞书推送（全球累计 + 人格 + 大赛 Top5）。 | build_survival_digest_markdown, send_survival_digest_feishu, is_weekly_digest_due |
| `greedy_survival_publish_service.py` | 198 | 摸金校尉 L4 审核通过 → ContentMaster + PublishTask 真发。 | channels_to_platform_names, resolve_greedy_publish_tenant_id, create_survival_content_mast |
| `harness_gateway.py` | 123 | DeepSeek Harness Gateway —— 最外层意图入口（接真实拆解器）。 ⚠️ 本文件此前是**桩**：`intent` 硬编码为 `"inferred_from_ | HarnessGateway, process_inbound_webhook |
| `hermes_ai_lanes_service.py` | 61 | RADAR-07 / AI-03：Hermes ops vs 租户 customer AI 场景分流快照。 | build_ai_lane_snapshot |
| `hermes_continuous_iteration_service.py` | 433 | Hermes 持续迭代闭环 — 宪法 + DeerFlow + 研究员 + 营销/各部门 + ECC。 L1 只读采集 → L2 ResearchBrief → L3 ECC 评审 | brief_to_ecc_candidate, route_departments, run_continuous_iteration_cycle, load_iteration_ |
| `hermes_mcp_server.py` | 78 | Hermes MCP Server. Exposes the internal TaskGraph (Plan-as-Data) generation and dispatch a | GeneratePlanToolInput, HermesMCPServer |
| `hermes_rank_first_constitution.py` | 54 | Hermes 存在第一准则 — 排名效果优先于一切运维动作。 流量入口分散（百度 / 豆包 / 360 / 无头浏览器 / 各厂大模型），机制各异且蒸馏频繁； Hermes 驱动  | rank_first_payload |
| `inquiry_executor.py` | 112 | Inquiry Capture Executor Plugin for Hermes Orchestration. 把既有 `InquiriesUnifiedService.cre | InquiryExecutor |
| `install_service.py` | 153 | 租户 Hermes 插件安装 / 启用。 | list_tenant_installs, is_plugin_enabled, install_plugin, set_plugin_enabled, ensure_defaul |
| `lead_executor.py` | 199 | Lead Search Executor Plugin for Hermes Orchestration. 把既有 `GeoLeadService.search_leads`（ge | LeadExecutor |
| `learning_harness_service.py` | 394 | 学习更新服务 (Learning Harness) 增强AI系统的自我学习和进化能力，支持： - 用户反馈学习 - 内容质量反馈 - 市场趋势学习 - 模型性能监控与优化 - 知识 | LearningHarnessService |
| `llm_router.py` | 642 | agency-orchestrator 10 provider / 7 免 Key — Hermes LLM 路由（对齐 ao factory）。 | AgencyLlmConfig, probe_provider, list_providers, provider_catalog_meta, resolve_provider_c |
| `logistics_executor.py` | 101 | Logistics Tracking Executor Plugin for Hermes Orchestration. 把既有 `fetch_tracking_payload`  | LogisticsExecutor |
| `maintenance_constitution.py` | 124 | Hermes 巡站维护宪法 — 底层写死：只维护、不破坏。 任何维护动作须经 assert_maintenance_action 校验；禁止类动作在编译期常量中冻结。 | HermesMaintenanceViolation, is_action_forbidden, assert_maintenance_action, constitution_p |
| `marketing_anysearch_workflow_service.py` | 392 | Hermes 营销 Lane — AnySearch 数字产品/智能体变现深度拆解与工作流编排。 | load_monetize_workflow, decompose_hits, run_monetize_round, aggregate_workflow_blueprint,  |
| `media_executor.py` | 173 | Media Executor Plugin for Hermes Orchestration. 把既有 Media Factory / Video Edit services 包成 | MediaExecutor |
| `node_terminal_hooks.py` | 225 | 节点终态钩子链（H.7：D 类机制层 Evolution / Pipeline 变钩子，不做独立引擎）。 接线纪律（与 n8n 出站通知同规格）： - 钩子 best-effort | NodeTerminalHookReport, fire_node_terminal_hooks |
| `nurture_executor.py` | 137 | Nurture Executor Plugin — 多平台账号养护（养号）。 业务链第 7 环：分发出去的账号需要「养」——按各平台的养护规则推进周期， 避免新号被判定为营销号而限 | NurtureExecutor |
| `ops_access.py` | 29 | Hermes 运维 API 访问门控 — L0 超管专用，租户不可见。 | is_ops_admin, ops_admin_forbidden_message |
| `ops_autopilot.py` | 196 | Hermes 运维自动驾驶 — 巡站 + 技术雷达 + 自愈 + 飞书通知。 | run_tech_radar_cycle, run_full_ops_cycle, load_ops_snapshot |
| `orchestrator_bridge.py` | 388 | Hermes × agency-orchestrator — 专家角色库编排桥接。 | agency_catalog, run_hermes_agency_workflow, run_geo_matrix_via_agency, run_geo_matrix_via_ |
| `order_executor.py` | 141 | Order Executor Plugin for Hermes Orchestration. 把既有 order services（order_addon_service / o | OrderExecutor |
| `outreach_scenario.py` | 56 | B2B Outreach and Lead Gen Scenario Template. Defines the TaskGraph for finding leads, prof | build_outreach_graph |
| `planner_service.py` | 437 | Hermes 拆解器（Planner）—— 意图 → 任务图。 这是整条编排链的「大脑」入口：把一句自然语言需求拆成可执行的 TaskGraph。 补齐的是设计文档 `docs/架 | known_capabilities, validate_graph, decompose |
| `platform_survival_service.py` | 367 | Hermes 平台生存基金 — 财迷疯真钱账本（仅超管收款，与租户账单隔离）。 | load_survival_charter, record_survival_settlement, record_worldfirst_inbound, worldfirst_s |
| `product_executor.py` | 151 | Product Create Executor Plugin for Hermes Orchestration. 把既有 `ProductService.create_produc | ProductExecutor |
| `prompt_harness_service.py` | 503 | 统一 Prompt 构建管理服务 (Prompt Harness) 统一管理各服务的 Prompt 模板，支持模板版本管理、动态参数注入、Prompt 优化。 解决当前 Promp | PromptHarnessService |
| `provider_setup.py` | 243 | Hermes agency LLM — 服务器/bootstrap 安装计划（非交互部分可脚本化）。 | build_setup_plan, run_automated_bootstrap |
| `publish_executor.py` | 292 | Publish Executor Plugin — 多平台内容分发。 ⚠️ 重要：本插件**刻意不使用** `PublishDispatchService.distribute`  | PublishExecutor |
| `publish_history_aggregate.py` | 84 | 超管统一发布历史：SEO 图文 + 视频矩阵。 | list_unified_publish_history |
| `registry.py` | 128 | Hermes 插件注册表 — 对内完整目录，对外经 marketplace 脱敏。 | load_catalog, list_plugins, get_plugin, catalog_meta, public_market_item, internal_plugin_ |
| `research_brief_service.py` | 453 | 外贸研究员 — 只读信号 → ResearchBrief JSON（违宪动作禁止自动执行）。 | hourly_topic, collect_signals, compose_research_brief, save_brief_snapshot, append_brief_i |
| `research_executor.py` | 176 | Research Executor Plugin for Hermes Orchestration. 把既有 hermes/research_brief_service + for | ResearchExecutor |
| `role_economics_service.py` | 272 | 211 专家变现契约 — 每位角色须有赚钱路径，否则不得摸金上场。 | load_role_economics_registry, resolve_role_economics, list_publish_sku_catalog, build_l4_p |
| `role_loader.py` | 153 | agency-orchestrator 角色库加载 — 产品内嵌 agency-agents 中文专家人格。 | resolve_roles_dir, load_role, list_roles, roles_meta, resolve_persona_ref |
| `runtime.py` | 516 | Hermes 插件运行时 — 统一执行入口。 | HermesPluginError, execute_plugin |
| `safe_remediation.py` | 149 | Hermes 安全自愈 — 仅白名单动作，违宪即拒绝。 | run_safe_remediation, execute_human_instruction |
| `scoring_harness_service.py` | 365 | 评分分发服务 (Scoring Harness) 扩展现有评分能力，支持多维度评分、评分规则管理、评分分发策略。 | ScoringHarnessService |
| `seo_executor.py` | 236 | SEO Executor Plugin for Hermes Orchestration. 把既有 SEO 服务（rank tracking / inclusion check / | SeoExecutor |
| `site_build_scenario.py` | 54 | Site Build and Distribution Scenario Template. Defines the standard TaskGraph for taking p | build_site_generation_graph |
| `site_build_workflow.py` | 208 | Hermes 智能建站工作流 — ECC 专家流水线 + 设计技能约束。 | design_skills_summary, run_ai_site_builder_v1 |
| `site_builder_ecc_pipeline.py` | 304 | Hermes 建站 ECC 专家流水线 — 美工/文案/视觉营销/美学 UI，非裸 LLM。 | load_site_builder_pipeline, compile_expert_brief, apply_copy_expert_pass, apply_visual_mar |
| `site_builder_executor.py` | 165 | Site Builder Executor Plugin for Hermes Orchestration. 把已有的建站实现（`hermes_task_bridge._run_s | SiteBuilderExecutor |
| `site_cta_audit.py` | 46 | 生成站双 CTA + 24h 询盘承诺抽检（western-inquiry-conversion）。 | audit_site_western_cta |
| `site_design_guard.py` | 140 | 租户建站设计 manifest 与设计门禁（供 Hermes 流水线复用，避免循环 import）。 | load_design_manifest, apply_design_guard, apply_google_ecosystem_guard |
| `site_patrol_scheduler.py` | 196 | Hermes 7×24 巡站调度 — 只读维护，间隔可配置。 | HermesSitePatrolScheduler, run_site_patrol_manual |
| `site_patrol_service.py` | 609 | Hermes 7×24 巡站维护 — 只读探测 + 建议，不执行破坏性操作。 | run_site_patrol, patrol_status |
| `site_patrol_store.py` | 134 | Hermes 巡站快照持久化（仅单键 SystemSetting）。 | load_patrol_snapshot, save_patrol_snapshot, append_patrol_trend, load_patrol_trend |
| `sop_resolver.py` | 98 | ECC SOP Resolver: resolve `sop_ref` URIs to skill content. The sop_ref format is `ecc://<s | resolve_sop_ref |
| `task_control_supervisor.py` | 443 | Hermes Task Control Supervisor. Responsible for executing the TaskGraph DAG by mapping Tas | parse_graph_to_tasks, advance_plan, compensate_plan |
| `tech_radar_markdown_export.py` | 52 | RADAR-08：技术雷达 Markdown 日报导出。 | export_tech_radar_markdown |
| `tech_validation.py` | 126 | Hermes 对抓取技术候选做安全验证（不安装、不改依赖）。 | validate_candidate, validate_all |
| `trade_ai_agent_executor.py` | 189 | Trade AI Agent Executor — 接真实适配器（不再返回假数据）。 ⚠️ 本文件此前是**纯 mock**：伪造格式类似 `buyerN@<keyword>-in | TradeAiAgentExecutor |
| `ubrain_executor.py` | 88 | UBrain Executor Plugin for Hermes Orchestration. 把既有 `ubrain_orchestrator.chat` 包成 Executo | UbrainExecutor |
| `video_matrix_workflow.py` | 303 | Hermes 视频矩阵真发编排 — 预检 → 分发 → 验真汇总。 | run_video_matrix_v1 |
| `wangcai_executor.py` | 116 | Wangcai Executor Plugin for Hermes Orchestration. 把既有旺财统一入口 `ask_wangcai_for_tenant`（公开站海关 | WangcaiExecutor |
| `workflow_runner.py` | 383 | agency-orchestrator YAML 工作流执行 — Hermes 驱动的 Python DAG 引擎。 | resolve_workflows_dir, list_workflow_files, workflow_id_from_path, load_workflow_yaml, lis |
| `worldfirst_webhook_service.py` | 234 | 万里汇 WorldFirst Webhook → 财迷疯 survival 台账（摸金校尉 L6 自动收款）。 | verify_worldfirst_webhook, parse_worldfirst_webhook_payload, handle_worldfirst_webhook, we |
| `write_boundary_audit_service.py` | 129 | ARCH-03：Hermes 写库边界静态审计（只读扫描）。 | audit_write_boundaries |

## services/ubrain · 83 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `__init__.py` | 6 | -*- coding: utf-8 -*- |  |
| `accio_gap_constants.py` | 45 | Accio gap 技能 ID（避免 catalog ↔ handlers 循环导入）。 |  |
| `accio_gap_handlers.py` | 317 | Accio 对标 gap 技能 — 预览载荷 + 带 DB 上下文真执行。 | is_gap_mvp_skill, is_gap_execute_skill, execute_gap_mvp, execute_gap_mvp_async |
| `accio_sales_service.py` | 784 | AccioWork 卖货核心：找客、开发信、谈单草稿（画像级 + 人审发送）。 | find_buyer_prospects, build_outreach_letters, outreach_letter_pack, negotiation_draft, lis |
| `accio_skill_catalog.py` | 119 | AccioWork 39+ 技能包对标目录（本系统实现状态）。 | load_skill_catalog, iter_skills, get_skill, list_gap_skills, list_partial_mvp_skills, cata |
| `action_audit_service.py` | 244 | Accio A5：UBrain / 对外动作审计（不含真实 SMTP 外发本身）。 | log_action, serialize_audit, log_flywheel_action, list_action_audits, summarize_action_aud |
| `ai_email_generator.py` | 387 | AI 开发信生成 — FIX-48 基于客户画像自动生成个性化开发信： - 模板变量替换 - AI 内容生成（基于 LLM） - A/B 测试变体生成 - 质量评估 | EmailTemplate, AIEmailGenerator |
| `ai_find_customer_sidecar.py` | 440 | AI Hunter 找客旁路 — 对接 xiongQvQ/AI_Find_Customer 式 Sidecar HTTP API。 主站不内置深度爬虫；Sidecar 返回须带 e | sidecar_base_url, sidecar_token, allow_dev_stub, ai_find_customer_sidecar_status, fetch_si |
| `brand_guard_bff.py` | 23 | UB-06：飞轮 BFF 层统一脱敏序列化。 | public_serialize_job |
| `channel_status.py` | 115 | FIX-5: Prospect channel availability service. Centralizes API-availability checks for all  | ChannelInfo, get_channel_status, get_all_channel_statuses |
| `chat_context_service.py` | 137 | UBrain 对话上下文：经营快照 + 记忆，供 general LLM 与智能路由使用。 | refine_intent, is_strategic_question, build_situational_context |
| `chat_task_service.py` | 79 | UBrain chat -> unified ai_task entry. | UBrainChatTaskError, run_chat_task |
| `code_quality_service.py` | 412 | 代码质量服务 — FIX-70~73 FIX-70: 前端代码质量（ESLint + Prettier + Vitest 配置生成与合规检查） FIX-71: 全栈严格类型化（Ty | FrontendConfigGenerator, TypeComplianceReport, TypeComplianceTracker, CodeReviewResult |
| `commercial_os_bridge.py` | 754 | DeerFlow + AccioWork 商业 OS 飞轮 — 记忆 / 编排 / 反馈（可接 Mem0、n8n）。 | count_auto_outbound_enqueues, extract_insight_from_deerflow, retrieve_insights_for_accio,  |
| `content_draft_service.py` | 100 | UBrain-X：将 lead_content_pack 选题写入 ContentMaster 草稿（人审后发布）。 | write_lead_content_drafts |
| `dedup_engine.py` | 308 | 线索去重引擎 —— 统一模型的核心组件 去重策略（优先级降序）： 1. 邮箱精确匹配（最强信号） 2. LinkedIn URL 精确匹配 3. 域名 + 公司名模糊匹配（Jaro | DedupEngine, find_duplicate, merge_lead_data, save_or_merge_lead |
| `deerflow_brief_templates_service.py` | 143 | DeerFlow 租户 Research Brief 预制模板（Hermes×AnySearch 研究沉淀）。 | list_brief_templates, get_brief_template, match_brief_template, apply_brief_template |
| `deerflow_job_service.py` | 578 | DeerFlow 任务队列：入队、执行、轮询（Phase 1 进程内执行，可接 cron）。 | serialize_job, serialize_job_with_steps, enqueue_job, run_subtask_intent, run_job, run_pen |
| `deerflow_research_service.py` | 343 | DeerFlow 风格深度研究 — Planner / Researcher / Reviewer / Writer → Research Brief。 | build_research_brief, run_market_research_v2 |
| `deerflow_scheduled_service.py` | 424 | DeerFlow 定时更新 — 套餐门控入队 + 分 lane 队列消费。 | run_deerflow_pending_only, run_scheduled_deerflow_update, load_deerflow_schedule_snapshot, |
| `deerflow_scheduler.py` | 181 | DeerFlow 定时调度 — 每日市场研究 + 与 Hermes 运维循环联动。 | DeerflowScheduler |
| `deerflow_sidecar.py` | 273 | 官方 DeerFlow 2.0 旁路：可选 HTTP 研究服务，失败则回退本机 Lite。 DeerFlow 2.0 是字节跳动开源的超级智能体框架，基于 LangGraph +  | sidecar_base_url, deerflow_version, is_deerflow_v2, deerflow_gateway_url, deerflow_langgra |
| `deerflow_tenant_quota.py` | 166 | DeerFlow 租户套餐/配额 — 定时市场研究仅对符合条件的租户。 | monthly_limit, increment_monthly_count, check_tenant_schedule_eligibility, resolve_eligibl |
| `domain_email_extractor_sidecar.py` | 208 | 官网域名邮箱 enrichment Sidecar — AI Hunter 后处理，须 source_url。 | sidecar_base_url, sidecar_token, domain_email_extractor_sidecar_status, domain_from_url, f |
| `drip_sequence_service.py` | 413 | 邮件序列 Drip Campaign — FIX-44 自动跟进邮件序列管理： - 预置序列模板（3封/5封/7封） - 自定义序列 - 触发条件（打开/点击/未回复/时间） -  | SequenceTrigger, SequenceStep, DripSequence, DripSequenceService |
| `email_outreach_service.py` | 479 | 邮件外联服务 —— 状态机 + 幂等 + 追踪 核心功能： 1. 幂等发送：同一 idempotency_key 只发送一次 2. 状态机管理：严格的 draft → queued | EmailOutreachService, create_email, list_pending_review_outreach, approve_outreach_email,  |
| `email_quality_service.py` | 1115 | 开发信质量评估 + A/B 测试 + 获客流程标准化 — FIX-58 & FIX-59 FIX-58: 开发信质量评估 + A/B 测试 1. 多维度质量评分（主题行/正文/CT | EmailQualityDimension, QualityDimensionScore, EmailQualityReport, EmailQualityEvaluator |
| `email_queue_service.py` | 1001 | 邮件发送队列 + 数据飞轮 + 安全加密 + AI 安全 — FIX-62 ~ FIX-65 FIX-62: 邮件发送队列（高吞吐 + 高送达率） FIX-63: 数据飞轮（越用越 | EmailQueueStatus, EmailQueueItem, EmailSendQueue, DataFlywheelStage |
| `email_send_service.py` | 194 | 零成本邮件发送服务 支持两种发送方式（零成本策略）： 1. Resend API — 免费额度 3000 封/月，配置了 RESEND_API_KEY 时优先使用 2. SMTP  | EmailSendResult, EmailMessage, EmailSendService, email_service_available, send_email |
| `email_tracking_service.py` | 236 | 邮件追踪服务 — FIX-47 提供邮件打开/点击/回复追踪功能： - 追踪像素（1x1 透明图片） - 链接重写（点击追踪） - 回复检测 - 追踪数据聚合 | EmailTrackingService |
| `email_verification_service.py` | 222 | 零成本邮箱验证服务 — 无需付费 API 验证策略（从快到慢，从省钱到精准）： 1. 格式校验（正则）— 0 成本，毫秒级 2. 域名 MX 记录检查 — 0 成本，10-50ms | EmailVerificationResult, EmailVerificationService, verify_email |
| `embedding_service.py` | 261 | Embedding Service - 文本向量生成服务 支持多种模型源： - NVIDIA NIM (nv-embed-v1) - OpenAI (text-embedding- | EmbeddingService, get_embedding_service |
| `export_feasibility_reply.py` | 314 | 出口可行性回复：避免重复提问时机械复读同一模板。 | build_export_feasibility_reply, memory_patch_after_export |
| `flywheel_integrations.py` | 181 | P2 外挂槽位：Mem0 双写、PostHog 埋点、n8n 状态（未配置则 no-op）。 | graphrag_integration_status, tavily_integration_status, flywheel_integrations_status, sync |
| `follow_up_engine.py` | 771 | 智能 Follow-up 策略引擎 — FIX-57 基于客户行为的多渠道智能跟进系统： 1. 时机优化：基于打开/点击时间的数据驱动最佳跟随时机 2. 内容自适应：根据前一次交互 | FollowUpStage, FollowUpChannel, FollowUpTrigger, FollowUpOutcome |
| `general_smart_reply.py` | 572 | 无 LLM 时的卖货助手智能回复：并列多种策略，结合经营快照给出可执行建议。 | parse_business_metrics, build_strategy_options, format_strategy_reply, expand_strategy_cho |
| `geo_content_matrix_service.py` | 734 | GEO/SEO 内容矩阵 — 借鉴 agency-orchestrator seo-content-matrix + content-pipeline DAG。 上游：关键词 →  | run_geo_content_matrix_job |
| `gmssl_crypto_service.py` | 484 | 国密算法服务 — FIX-13: GmSSL 认证库替换 支持国密标准算法： - SM4: 对称加密（替代 AES） - SM2: 非对称加密/签名（替代 RSA/ECDSA） - | SM3, SM4, GmSSLCryptoResult, GmSSLCryptoService |
| `google_prospect_service.py` | 527 | Google 搜索客户开发服务 — 通过 Google 搜索引擎地毯式开发海外客户。 Google 是全球最大的搜索引擎，每天处理数十亿次搜索请求， 是外贸企业主动开发客户的重要渠 | fetch_google_prospects, find_google_prospects |
| `hunter_service.py` | 1072 | Hunter.io / Apollo.io 付费 API 集成 — FIX-53 提供： 1. 域名搜索（按域名查找公司邮箱） 2. 邮箱验证（批量验证邮箱有效性） 3. 邮箱查找 | EmailConfidence, VerificationStatus, ApolloPersonSeniority, HunterEmail |
| `imap_inquiry_sidecar.py` | 152 | 只读 IMAP 询盘收取 Sidecar — mymailclaw 对标，禁止 SMTP 自动发信。 | sidecar_base_url, sidecar_token, imap_inquiry_sidecar_status, poll_imap_inbox |
| `inquiry_context_service.py` | 328 | Accio A2/A3/A4：租户真实询盘上下文 → 草稿、评分与经营快照。 | get_latest_inquiry, resolve_inquiry, build_inquiry_reply_draft, tenant_ops_snapshot |
| `inquiry_discovery_service.py` | 68 | Discovery 教练 — 新询盘结构化追问（MOQ / 目的港 / 规格）。 | build_discovery_questions, format_discovery_note, attach_discovery_to_message |
| `inquiry_intel_service.py` | 75 | 询盘智能 enrichment — 意向分 + Discovery 追问（列表/详情共用）。 | strip_discovery_block, discovery_questions_for_inquiry, enrich_inquiry_intel |
| `inquiry_scoring_service.py` | 81 | 询盘意向评分 — 副驾 inquiry_score 与公开询盘创建共用。 | score_inquiry_lead |
| `knowledge_graph_service.py` | 744 | Knowledge Graph Service - Neo4j 知识图谱服务 提供基于 Neo4j 的实体图谱构建、查询、最短路径、语义搜索能力。 降级策略：Neo4j 不可用时降 | KnowledgeGraphService, get_knowledge_graph_service |
| `lead_csv_service.py` | 270 | 获客CSV导入导出 — FIX-38 支持： - CSV 文件上传导入线索 - 线索列表导出为 CSV - 批量导入验证 + 去重 | LeadCSVService, LeadCSVValidator |
| `lead_processing_pipeline.py` | 431 | 线索处理 Pipeline（责任链模式） — FIX-35 处理流程： Raw Lead → 标准化 → 去重 → 验证 → 评分 → 丰富 → 入库 每个处理器（Handler） | PipelineStatus, LeadContext, LeadHandler, NormalizeHandler |
| `lead_scoring_engine.py` | 296 | 线索评分引擎 v2 — FIX-36 多维加权评分模型，从以下维度评估线索质量： 1. 邮箱质量（30%）：是否验证通过、域名类型 2. 公司信息完整度（20%）：公司名、网站、行 | LeadGrade, LeadScoringEngine, score_lead |
| `lead_search_engine.py` | 270 | 线索搜索引擎 — FIX-61 倒排索引 + 向量搜索混合引擎： 1. 倒排索引：快速关键词搜索 + 精确匹配 2. 向量搜索（Qdrant）：语义相似度搜索 3. 混合搜索：倒排 | SearchHit, InvertedIndex, LeadSearchEngine |
| `lead_search_task.py` | 223 | 获客搜索异步任务 —— 后台执行 + 进度推送 实现方式（渐进式）： - Phase 1: asyncio 后台任务 + 内存状态存储（当前） - Phase 2: Celery  | TaskStatus, LeadSearchTask, create_task, get_task, update_task, cleanup_old_tasks, execute |
| `linkedin_decision_maker_sidecar.py` | 152 | LinkedIn 决策人 enrichment Sidecar — P3 restricted，须 evidence_url + 人工核实。 | sidecar_base_url, sidecar_token, linkedin_decision_maker_sidecar_status, fetch_decision_ma |
| `linkedin_prospect_service.py` | 301 | LinkedIn 外贸客户开发服务 — 从 LinkedIn 挖掘 B2B 决策人。 LinkedIn 是全球最大的职场社交平台，拥有超过 8 亿用户， 是外贸企业寻找采购经理、供 | fetch_linkedin_prospects, find_linkedin_prospects |
| `linkedin_sales_navigator_service.py` | 1019 | LinkedIn Sales Navigator API 正式接入 — FIX-55 LinkedIn Sales Navigator API (v2) 集成： 1. 人员搜索（按 | LinkedInSeniority, LinkedInCompanySize, LinkedInIndustry, LinkedInPerson |
| `llm_assist_reply.py` | 194 | 预制模板 + 大模型 API 辅助润色 — 财旺通用对话层。 | format_recent_turns, assist_template_reply, resolve_template_for_message, reply_with_templ |
| `matrix_publish_bootstrap.py` | 166 | 矩阵发布零配置引导 — 自动补平台、占位账号、内容母版草稿。 | ensure_platforms_for_names, ensure_placeholder_accounts, ensure_matrix_content_draft, boot |
| `matrix_publish_service.py` | 301 | 矩阵发布 — 计划预览、PublishTask 创建、视频真发统一入口。 | default_platform_names, resolve_platform_ids, build_matrix_publish_plan, execute_matrix_pu |
| `mem0_batch_sync_service.py` | 68 | INT-03：Mem0 洞察批量双写（超管触发 · 未配置则 no-op）。 | sync_recent_insights_to_mem0, integrations_health_snapshot |
| `orchestrator.py` | 1786 | UBrain v1 — 意图识别 + 工具调用（走现有 API 数据或 M0 规则）。 | UBrainOrchestrator |
| `outreach_deliverability_service.py` | 415 | 开发信可达性 — 质量评分、垃圾箱风险、发送窗口（研究员×PM 契约）。 | country_timezone, suggest_send_window, follow_up_schedule, check_recipient_email, scan_spa |
| `p2_enhancement_service.py` | 729 | P2 增强服务 — 完成剩余 19 项 获客 P2: - #26: LinkedIn + WhatsApp 渠道完善（渠道聚合器） - #27: 数据飞轮第五阶段（预测性获客） - | ChannelAggregatorService, PredictiveAcquisitionEngine, MCPAcquisitionToolkit, DatabasePart |
| `paid_ads_creative_service.py` | 115 | 付费广告创意 — 结构化变体 + 可选 AI 增强。 | generate_paid_ads_creative |
| `performance_optimization_service.py` | 501 | 性能优化服务 — FIX-66~69 FIX-66: 异步化 + 消息驱动（EventBus 增强 + 异步任务编排） FIX-67: Cloudflare CDN + 边缘缓存  | MessagePriority, AsyncMessage, AsyncMessageBus, CDNCacheConfig |
| `pro_research_terms_service.py` | 59 | COMP-03：Pro 定时市场研究服务条款（租户可见 · 已脱敏）。 | build_pro_research_terms |
| `product_commercial_service.py` | 547 | 产品商业化服务 — FIX-74~81 FIX-74: 代理体系落地运营（代理注册 + 佣金结算 + 层级管理） FIX-75: 模板市场（邮件模板 + 落地页模板 + 行业模板） | AgentTier, AgentSystemService, TemplateMarketplaceService, IndustrySolutionService |
| `prospect_export_service.py` | 103 | 采购商候选导出 — CSV（人工核实后跟进）。 | export_prospects_csv, mark_prospect_contacted |
| `prospect_research_engine.py` | 829 | RAG 客户洞察 + 定制化开发信 — FIX-56 基于检索增强生成（RAG）的客户研究 + 个性化开发信引擎： 1. 客户情报收集：网站抓取 + 新闻 + 行业报告 + 社交媒 | CompanyGrowthSignal, InsightCategory, EmailTone, CompanyInsight |
| `quality_gate_service.py` | 82 | DF-13：研究质量门 — 低分自动重跑（限频）。 | maybe_enqueue_quality_rerun |
| `quora_prospect_service.py` | 269 | Quora 外贸客户开发服务 — 从 Quora 问答平台挖掘采购需求。 Quora 是全球最大的问答平台，拥有大量行业专家和采购决策者， 是外贸企业发现市场需求、建立专业形象的重 | fetch_quora_prospects, find_quora_prospects |
| `reddit_prospect_service.py` | 257 | Reddit 外贸客户开发服务 — 从 Reddit 社区挖掘潜在采购商线索。 Reddit 是全球最大的兴趣社区平台，拥有大量行业细分社区（subreddit）， 是外贸企业发现 | fetch_reddit_prospects, find_reddit_prospects |
| `reply_templates.py` | 175 | 财旺/UBrain 预制回复模板 — 事实与指令骨架；口语润色由 LLM assist 完成。 | capability_template, capability_plain_reply, greeting_plain_reply, greeting_template, poli |
| `search_strategy_builder.py` | 634 | AI 辅助搜索策略构建器 — FIX-60 智能搜索策略引擎： 1. 行业搜索模板库（自动匹配行业最佳搜索词） 2. 布尔搜索构建器（AND/OR/NOT 语法） 3. 多平台搜索 | SearchPlatform, SearchIntent, SearchQuery, SearchStrategy |
| `skill_audit_service.py` | 259 | 技能安全审核服务 — 参考 CocoLoop BSS安全扫描体系。 CocoLoop 采用全链路安全审核： - BSS安全扫描检测恶意代码、权限泄露、非法调用 - 风险等级划分为  | analyze_skill_risk, scan_skill_code, get_skill_catalog_with_security, search_skills, get_f |
| `super_agent_bridge.py` | 635 | AccioWork 原生桥 — 无 ai_engine 包时使用 UBrain 卖货服务。 | NativeAccioWorkEngine, get_native_acciowork_engine |
| `team_rbac_service.py` | 85 | 租户团队 RBAC 快照 — 角色权限矩阵（ROLE_PERMISSIONS + 超管 DB 角色）。 | build_team_rbac_snapshot |
| `tenant_memory_service.py` | 199 | 租户副驾记忆 — Accio「越用越智能」底座。 | resolve_company_name, get_memory, merge_memory, record_tool_use |
| `tiktok_prospect_service.py` | 253 | TikTok 外贸客户开发服务 — 从 TikTok 短视频挖掘采购需求。 TikTok 是全球最火的短视频平台，拥有超过 15 亿用户， 越来越多的海外采购商通过短视频寻找供应商 | fetch_tiktok_prospects, find_tiktok_prospects |
| `ubrain_decision_tracker.py` | 330 | UBrain AI Agent 决策追踪服务 提供决策记录、执行追踪、反馈收集与性能归因的完整闭环。 数据同时写入 PostgreSQL（业务表）与 SiteAnalyticsEv | UBrainDecisionTracker |
| `vector_search_service.py` | 681 | Vector Search Service - Qdrant 向量检索服务 提供基于 Qdrant 的高性能向量搜索能力。 降级策略：Qdrant 不可用时降级到 PostgreS | VectorSearchService, get_vector_search_service |
| `website_email_scraper.py` | 249 | 零成本网站邮箱抓取服务 — 从目标公司网站提取邮箱 策略： 1. 抓取首页 + Contact + About 页面 2. 用正则提取所有邮箱 3. 过滤掉 info@ / sup | ScrapedEmail, WebsiteEmailResult, WebsiteEmailScraper, scrape_website_emails |
| `whatsapp_business_service.py` | 1097 | WhatsApp Business Cloud API 正式接入 — FIX-54 Meta WhatsApp Cloud API v17.0+ 集成： 1. 发送文本消息（模板/ | WhatsAppMessageType, WhatsAppMessageStatus, WhatsAppTemplateCategory, WhatsAppTemplateStat |
| `whatsapp_prospect_service.py` | 709 | WhatsApp 外贸客户开发服务 — 参考 whatsfinds.com 获客模式。 WhatsApp 全球月活用户超20亿，在中东、南美、东南亚等市场的商务沟通渗透率超85%。 | fetch_whatsapp_prospects, find_whatsapp_prospects, generate_whatsapp_message, verify_whats |
| `zero_trust_service.py` | 322 | 零信任安全架构服务 — FIX-14 核心原则： 1. 永不信任，始终验证（Never Trust, Always Verify） 2. 最小权限访问（Least Privileg | TrustLevel, RiskLevel, DeviceContext, AccessContext |

## services/foreign_trade · 44 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `__init__.py` | 8 | 外贸 AI 技能引擎 — 统一入口。 |  |
| `__init__.py` | 37 | OSINT 六层背调 — 改编自 chefroger/smart-trade-ai (MIT)，见 THIRD_PARTY_ATTRIBUTION.md。 |  |
| `aeo_fact_audit_service.py` | 118 | GW-G-AEO-01 — 站点/母版文案 vs 禁泄露品牌词 + 租户事实一致性。 | audit_tenant_content_masters, run_aeo_fact_audit |
| `approval_flow.py` | 193 | 多级审批流 -- sales_rep -> sales_manager -> director，支持超阈值逐级上报。 | ApprovalStatus, ApprovalLevel, ApprovalRecord, ApprovalRequest, register_audit_hook, fire_ |
| `benchmark_catalog_service.py` | 59 | 标杆来源取长补短 — 供研究员 / Admin / ecosystem API 引用。 | list_benchmark_sources, build_benchmark_matrix, adopt_playbook_hints |
| `cold_email_skill.py` | 56 | 开发信生成技能 — 对应 cold-email SKILL.md。 |  |
| `competitor_profile_skill.py` | 58 | 竞品画像技能 — 对应 competitor-profiling SKILL.md。 |  |
| `constants.py` | 106 | Trade AI Assistant — OSINT 模块：常量和共享工具。 包含个人邮箱域名黑名单、免费建站平台列表、制裁名单来源、 HTTP 工具函数等各子模块共享的数据。 | set_sanctions_cache_dir, get_sanctions_cache_dir, http_get |
| `content_one_to_many_service.py` | 169 | GW-G-CC-02 — 1 长文 → 多平台变体 + 开发信摘要。 | variant_body_for_platform, build_outreach_snippet, expand_one_to_many |
| `copywriting_skill.py` | 59 | 营销文案技能 — 对应 copywriting SKILL.md。 |  |
| `customer_research_skill.py` | 58 | 客户调研技能 — 对应 customer-research SKILL.md。 |  |
| `customs_buyer_brief_service.py` | 85 | 海关/买家情报 brief — 公开统计 + playbook，禁止无来源 buyer 列表落库。 | build_customs_buyer_brief |
| `customs_data_spider_sidecar.py` | 178 | CustomsDataSpider Sidecar — 海关买家 research brief，须 evidence_url + 人工核实。 | sidecar_base_url, sidecar_token, customs_data_spider_sidecar_status, fetch_customs_buyer_r |
| `email_verify.py` | 298 | Trade AI Assistant — OSINT Layer 3: 企业邮箱验证。 判断邮箱是企业邮箱 (@公司域名) 还是个人邮箱 (@gmail/@qq等)， 并通过 DN | verify_corporate_email |
| `foreign_trade_agent_service.py` | 434 | 外贸标杆能力 — 智能体编排门面（UBrain / Hermes / DeerFlow 统一入口）。 | agent_envelope, extract_osint_target, extract_website_url, resolve_tenant_website_url, run |
| `geo_visibility_dashboard_service.py` | 118 | GW-G-GEO-DASH — GEO/AEO 客户可见性看板（对标迈富时效果报告）。 | build_geo_visibility_dashboard |
| `gsc_ads_attribution_webhook_service.py` | 208 | GW-P-GSC-02 — Google Search Console / Google Ads 归因 webhook 回环。 | verify_gsc_ads_signature, gsc_ads_webhook_status, ingest_gsc_ads_webhook, gsc_ads_attribut |
| `inquiry_ai_classifier.py` | 259 | 询盘 AI 智能分级 —— §7 缺口补齐。 在既有 MEDDPICC 规则评分（inquiry_meddpicc_service）之上，做三级评分 + 自动标签 + 可选 AI  | Classification, classify_inquiry, persist_classification, get_classification |
| `inquiry_meddpicc_service.py` | 150 | GW-L-DC-01 — 询盘 MEDDPICC 字段提取与评分。 | extract_meddpicc_from_text, load_meddpicc, save_meddpicc, score_inquiry_meddpicc |
| `inquiry_pipeline_service.py` | 172 | GW-L-PL-01 — 询盘管道阶段 MQL→SQL→报价→PI→定金。 | get_pipeline_stage, pipeline_stage_meta, set_pipeline_stage, pipeline_summary, enrich_inqu |
| `integrations_sidecars_status_service.py` | 73 | 并行聚合 B2B / GEO 旁路就绪态（避免 /integrations/sidecars/status 串行超时）。 | build_integrations_sidecars_status |
| `linkedin_verify.py` | 68 | Trade AI Assistant — OSINT Layer 6: LinkedIn 公司页验证。 LinkedIn 是外贸获客的核心渠道。我们不使用容易被反爬屏蔽的 Goog | linkedin_company_verify |
| `market_insight_skill.py` | 87 | 市场洞察技能 — 对标阿里国际 Accio Work 的"生成市场洞察"能力。 背景（2026-09-14 竞品雷达）：Accio Work 是构建在 Qwen 上的 AI 原生应 |  |
| `matrix_oauth_publish_gate_service.py` | 140 | GW-S-MAT-01 — 矩阵真发 OAuth 绑定 SLA 门禁。 | check_platform_oauth_gate, matrix_oauth_gate_report, assert_matrix_oauth_before_publish |
| `negotiation_rules.py` | 164 | 阶梯让步配置引擎 —— 将 round_1/round_2/round_3 硬编码逻辑抽成可配置规则。 | ConcessionResult, NegotiationRules, apply_concession |
| `orchestrator.py` | 279 | Trade AI Assistant — OSINT 编排器：完整尽职调查流程。 osint_full_check() 是 OSINT 模块的统一入口，接收邮箱/域名/公司名， 自 | osint_full_check |
| `osint_service.py` | 29 | OSINT 背调 API 封装。 | run_osint_check |
| `platform_health_alert_service.py` | 101 | GW-G-SM-04 — 平台账号 login_status 超时告警。 | scan_offline_accounts, run_platform_health_alert_cycle |
| `prospect_cleaner_service.py` | 112 | 潜客数据清洗 — 改编自 EricHong123/Eric_Frank DataCleanerSkill（核心逻辑，无 pandas）。 | clean_prospect_records |
| `prospect_skill.py` | 48 | 智能搜客技能 — 对应 prospecting SKILL.md。 |  |
| `publish_preflight_checklist_service.py` | 164 | GW-G-CC-04 — 发布前人审清单（数字/认证/MOQ）。 | load_preflight_checklist, apply_preflight_checklist, scan_content_risks, validate_prefligh |
| `sales_enablement_skill.py` | 58 | 销售赋能技能 — 对应 sales-enablement SKILL.md。 |  |
| `sanctions.py` | 356 | Trade AI Assistant — OSINT Layer 4: 制裁名单筛查。 筛查 OFAC / UN / EU 制裁名单，支持精确匹配和模糊匹配。 CSV 数据下载后持 | check_sanctions |
| `scoring.py` | 134 | Trade AI Assistant — OSINT 模块：风险评分与建议生成。 根据各层检测结果计算综合风险评分（0-100），并生成针对性的行动建议。 | compute_risk_score, generate_recommendations |
| `seo_audit_skill.py` | 60 | SEO 审计技能 — 对应 seo-audit SKILL.md。 |  |
| `skill_registry.py` | 121 | 外贸 AI 技能注册表 — 动态发现、注册、调用技能。 | SkillResult, SkillMeta, SkillRegistry |
| `strategy_templates.py` | 168 | 议价策略模板 —— 按 Incoterms 提供差异化报价参数与折扣策略。 | StrategyParams, get_strategy, list_strategies |
| `supplier_compare_skill.py` | 100 | 供应商/同行比较排序卡 — 对标阿里国际 Accio Work 的"比价与供应商比较"能力链。 背景（TODO.md §11）：Accio Work 的多 agent 分工里有"找 |  |
| `tech_stack.py` | 162 | Trade AI Assistant — OSINT Layer 5: 技术栈检测（BuiltWith-style）。 通过 HTTP 响应头和 HTML 内容正则匹配，检测网站使 | detect_tech_stack |
| `trade_document_export_service.py` | 446 | PI / 报价单导出 — DOCX（OOXML）与可打印 HTML。 | build_proforma_docx, build_proforma_print_html, build_proforma_pdf, build_trade_document_h |
| `trade_document_service.py` | 683 | 形式发票 PI / 商业发票 CI / 装箱单 PL / 原产地证 CO / 分批装运拆单 / 单据冲红全家桶。 30年外贸专家团队标准： - PI: 形式发票（订单确认、首付30 | build_proforma_invoice, build_commercial_invoice, build_packing_list, build_certificate_of |
| `utm_attribution_service.py` | 279 | GW-P-TR-01 — UTM 全链路：矩阵 publish_task → 独立域 → 询盘。 | parse_utm_from_url, serialize_utm, deserialize_utm, stamp_publish_task_utm, build_default_ |
| `website_icp_service.py` | 142 | 官网 ICP 画像 — 改编自 qingchuh/sale_agent_factory WebAnalyzer（MIT）。 | analyze_website_icp |
| `whois.py` | 307 | Trade AI Assistant — OSINT Layer 2: WHOIS 域名查询。 通过 socket 直接发送 IANA WHOIS 协议请求，无需第三方库。 支持  | domain_whois |

## services/cross_border · 32 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `__init__.py` | 4 | 跨境语言桥 — 询盘翻译、中文片出海、出口报价（W1–W3）。 |  |
| `audio_asr_service.py` | 540 | 视频/音频 → 中文听写（Whisper 多后端 + 讯飞 LFASR 直传，长媒体分片扇出扇入）。 | extract_audio_wav, transcribe_wav_file, transcribe_zh_from_media |
| `audio_chunk_service.py` | 196 | 长媒体听写分片：ffmpeg 切段、并行转写、扇入合并。 | probe_media_duration_sec, split_wav_chunks, merge_chunk_transcripts, transcribe_chunks_par |
| `cross_border_job_service.py` | 373 | 中文片出海异步任务：入队、调度、查询（复用 media_render_tasks）。 | create_cross_border_job, dispatch_cross_border_job, get_cross_border_job, serialize_cross_ |
| `cross_border_sse.py` | 47 | 跨境任务 SSE 事件流。 | stream_cross_border_job_events |
| `cross_border_worker.py` | 199 | 中文片出海 Worker：听写 / 出海（Celery 或后台线程调用）。 | run_cross_border_job |
| `export_quote_service.py` | 148 | FOB/MOQ 出口报价一页 — 绑定产品库（W3 / XF-D2）。 | build_export_quote_onepager |
| `forum_language_bridge_service.py` | 127 | 论坛语言桥 — 英文问→中文摘要；老板中文答→英文发布草稿（FORUM-05）。 | summarize_forum_question_zh, draft_forum_answer_en |
| `gemini_audio_asr_service.py` | 245 | Gemini 音频听写兜底（多模态 generateContent，非专用 ASR）。 使用已有 AI_GEMINI_API_KEY；小文件 inline base64，大文件走  | is_gemini_asr_configured, parse_gemini_transcript_response, transcribe_with_gemini_audio |
| `glossary_helper.py` | 41 | 建材术语库片段 — 供 LLM 翻译/回复时引用。 | build_glossary_prompt_block |
| `imap_inquiry_ingest_service.py` | 142 | 只读 IMAP 询盘入库 — 去重 + 诚实门禁（禁止假询盘、禁止自动回复）。 | poll_and_ingest_imap_inquiries |
| `industry_belt_product_import_service.py` | 236 | 产业带 AI 调研 → 产品库候选（须人工勾选导入，默认未上架）。 | load_survey_payload, list_product_candidates, import_product_candidates |
| `inquiry_bridge_service.py` | 228 | 询盘语言桥 — 外文询盘→中文摘要；老板中文→英文回复草稿（W2 / XF-C1/C2）。 | summarize_inquiry_zh, draft_reply_en, inquiry_bridge_status |
| `krillinai_sidecar_adapter.py` | 87 | KrillinAI sidecar/CLI 适配器 — 仅在上游就绪时调用，禁止假成功。 | krillinai_probe, run_krillinai_localization |
| `libretranslate_sidecar.py` | 128 | LibreTranslate 旁路 — 跨境文案机翻（须标注 machine_translated）。 | sidecar_base_url, sidecar_token, libretranslate_sidecar_status, translate_text |
| `lipsync_service.py` | 129 | 神经元级高保真口型对齐服务（Neural Lip-Syncing Service）。 实现“嘴随声动、声画合一”： 1. 分析原视频中出镜说话人的人脸区域与嘴唇关键点； 2. 结合 | apply_sidecar_lipsync, apply_ffmpeg_smart_mux, apply_video_lipsync |
| `media_studio_capability_registry.py` | 233 | 全媒体工作室能力注册表 — ASR / 剪辑适配器 / TTS，供前端枢纽页与运维探测。 | list_asr_capabilities, list_editor_adapters, list_localization_providers, build_media_stud |
| `media_studio_project_service.py` | 104 | 全媒体工作室项目持久化 — SRT/segments 存于 media_task edit_config。 | get_studio_project, save_studio_project |
| `opensource_localization_registry.py` | 531 | 开源视频本地化上游注册表 — 对标 Vozo / 山海智影；智能优先级见 OPTIMAL_PICK_ORDER。 | is_krillinai_configured, is_linly_dubbing_configured, is_youdub_webui_configured, is_video |
| `opensource_localization_service.py` | 489 | 开源精品轨执行器 — 统一 sidecar 契约或 KrillinAI CLI；未配置则明确失败。 | run_opensource_premium_job |
| `premium_video_dub_service.py` | 191 | 精品出海轨编排 — 开源 sidecar / Vozo / 回退禁止假成功。 | run_premium_overseas_job |
| `seo_belt_service.py` | 77 | 大城+河间 SEO/GEO 词库 — Client 预览与入库（W3）。 | preview_belt_keywords, seed_keywords_for_tenant |
| `sidecar_health.py` | 63 | Sidecar 健康探测 — mock/reference 不得计为已配置。 | probe_sidecar_health, is_verified_sidecar_url |
| `tts_service.py` | 379 | 英文 TTS — edge-tts（无需 API Key）。 | list_english_voices, voice_id_to_gender, resolve_dub_voice, synthesize_english_mp3, srt_ti |
| `video_dub_service.py` | 630 | 出海视音频数字人工厂 — 听写 / 多语种翻译 / 原声克隆 / 嘴型对齐 / 矩阵分发。 支持中出海 12 语种（英、阿、西、俄、葡、法、德、日、韩、越、印尼、泰）： 1. 工业 | transcribe_video_task, run_video_dub_job, ingest_client_video |
| `voice_cloning_service.py` | 190 | 零样本高保真声音克隆服务（Zero-Shot Cross-Lingual Voice Cloning）。 支持中出海多语种（英、阿、西、俄、葡等 12 语种）声线克隆： 1. 从原 | extract_reference_audio, synthesize_with_sidecar_cloning, synthesize_with_commercial_api,  |
| `voice_gender_infer.py` | 133 | 从原片音轨粗估解说者性别（基频启发式），用于英文 TTS 音色匹配。 | infer_voice_gender_from_media |
| `vozo_localization_service.py` | 188 | Vozo Enterprise 精品轨 — 有 Key 才调用；无 Key / 失败禁止假成功。 | is_vozo_configured, run_vozo_premium_job |
| `whisper_model_pool.py` | 47 | Whisper 模型单例预热（Worker 启动后复用）。 | get_faster_whisper_model, warm_whisper_model, whisper_warmed |
| `xfyun_ifasr_llm_service.py` | 344 | 讯飞「录音文件转写大模型」WebAPI（Ifasr LLM）。 文档：https://www.xfyun.cn/doc/spark/asr_llm/Ifasr_llm.html 接 | build_ifasr_llm_signature, parse_ifasr_llm_order_result, transcribe_with_ifasr_llm |
| `xfyun_lfasr_service.py` | 364 | 讯飞语音转写（LFASR / raasr）— 云端听写兜底。 文档：https://www.xfyun.cn/doc/asr/lfasr/API.html 与星火 LLM（AI_X | _SliceIdGenerator, use_ifasr_llm_api, is_xfyun_lfasr_configured, prefer_xfyun_lfasr_direct |
| `youding_self_hosted_provider.py` | 80 | 优丁内置真实出海链 — 无 sidecar、无 mock，走 video_dub_service 全链路。 | is_youding_self_hosted_configured, youding_self_hosted_provider_row |

## services/talking_stick · 19 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `__init__.py` | 28 | Talking-Stick 漏洞挖掘系统 基于talking-stick模式的多Agent协作漏洞挖掘系统 |  |
| `__init__.py` | 14 | Talking-Stick Agent模块 包含侦察Agent、审计Agent和验证Agent |  |
| `__init__.py` | 17 | Talking-Stick 数据模型模块 包含扫描结果、漏洞和修复方案的数据模型 |  |
| `__init__.py` | 13 | Talking-Stick 工具模块 包含文件扫描、依赖解析和规则引擎等工具 |  |
| `audit_agent.py` | 212 | Talking-Stick 审计Agent 负责精读风险代码，寻找已知漏洞（OWASP Top10、命令注入、XSS、SSRF、权限缺陷） | AuditAgent |
| `base_agent.py` | 91 | Talking-Stick Agent 基类 所有Agent的基类，提供通用功能 | BaseAgent |
| `config.py` | 125 | Talking-Stick 配置管理模块 负责加载和管理配置文件 | ModelConfig, FileLockConfig, OutputConfig, TalkingStickConfig |
| `dependency_parser.py` | 168 | Talking-Stick 依赖解析工具 负责解析和分析项目依赖 | DependencyFile, DependencyParser |
| `file_lock.py` | 156 | Talking-Stick 文件锁机制 确保同一时间只有一个Agent可以访问代码仓库 | LockInfo, FileLock |
| `file_scanner.py` | 171 | Talking-Stick 文件扫描工具 负责遍历目录和识别风险文件 | FileInfo, FileScanner |
| `fix.py` | 128 | Talking-Stick 修复方案数据模型 | POC, FixSuggestion, VerificationResult, VerificationOutput |
| `recon_agent.py` | 231 | Talking-Stick 侦察Agent 负责遍历目录、收集源码、依赖清单，初步标记风险文件 | ReconAgent |
| `report_generator.py` | 260 | Talking-Stick 报告生成器 负责生成多格式的安全审计报告 | ReportGenerator |
| `rule_engine.py` | 319 | Talking-Stick 规则引擎 负责应用检测规则并识别漏洞 | DetectionRule, RuleEngine |
| `scan_result.py` | 128 | Talking-Stick 扫描结果数据模型 | RiskFile, DependencyInfo, ScanSummary, ScanResult |
| `scheduler.py` | 222 | Talking-Stick 调度器 负责协调三个Agent的工作，管理任务队列 | Scheduler |
| `task_queue.py` | 139 | Talking-Stick 任务队列 负责管理扫描任务的排队和执行 | TaskStatus, Task, TaskQueue |
| `verify_agent.py` | 577 | Talking-Stick 验证Agent 负责复现漏洞、构造POC、剔除误报，输出修复方案 | VerifyAgent |
| `vulnerability.py` | 87 | Talking-Stick 漏洞数据模型 | Vulnerability, AuditResult |

## services/geo · 15 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `content_kernel.py` | 217 | 内容事实内核（Fact Kernel）— 全平台分发的单一事实真源。 设计定位（对应 AGENTS.md「一核多形」缺口）： - 一份结构化事实内核只生产一次，质量最高；各平台只是 | PlatformGroup, Evidence, TradeTerms, FactKernel |
| `content_kernel_bridge.py` | 137 | 内核接线层 — 把「母版 + 产品快照」落成事实内核，供发布台/Worker 按形态投影。 对应缺口 #8（接线）：unified_publish 发布任务执行前调用 `build | build_kernel_from_master, kernel_from_master, persist_kernel, invalidate_kernel, touch_ker |
| `geo_matrix_landing_service.py` | 319 | 全球出海国家与港口矩阵着陆页引擎 (Programmatic Geo-Matrix Landing Engine)。 基于外贸 30 年实战经验与 Google EEAT 算法规范 | GeoMatrixLandingService |
| `geo_writing_policy.py` | 385 | GEO 写作策略 v3 — Princeton 引用战术 + arXiv 2026 最新研究 + 去 AI 味。 战术版本随 tech-radar 外网检索更新；见 TACTICS | ContentQualityScore, build_geo_write_instructions, build_humanize_rewrite_instructions, bu |
| `headless_rank_probe_service.py` | 291 | Headless 排名探针 — 外置 Sidecar（Playwright/Browser Use）或显式 dev stub。 未配置 Sidecar 时返回 skipped/50 | sidecar_base_url, sidecar_token, headless_probe_sidecar_status, probe_single_engine, run_h |
| `multi_engine_rank_registry.py` | 186 | 多流量入口排名注册表 — 百度 / 豆包 / 360 / 大模型 / 出海搜索 分轨探测。 各入口 ranking 机制不同，不可共用一套 SEO 规则；本模块定义探针映射与蒸馏风 | TrafficEngine, engine_stat_keys, all_traffic_engines, probe_ready_engines, exploration_eng |
| `platform_content_router.py` | 155 | 平台形态路由 — 把事实内核分发到四类平台形态。 对应缺口第 2、3 条：ContentMaster 只发「同一篇长文」，本模块按 平台形态（A 搜索 / B 社媒 / C B2B | render_search, render_social, render_b2b, render_knowledge, route |
| `platform_discovery_service.py` | 103 | 平台发现与扩展 — 对照 catalog / live 适配器，持续拉高 GEO 覆盖面。 | catalog_platform_names, live_adapter_names, exploration_gap_report, propose_platform_regis |
| `platform_rank_registry.py` | 162 | 平台 × GEO 排名权重注册表 — 排名优先准则下的发布顺序。 平台越多、且覆盖 AI/搜索训练源，GEO 引用面越广；本模块为「先上高权重、再扩探索」提供排序。 | PlatformRankProfile, all_platform_rank_profiles, publish_order_for_ranking, revenue_loop_k |
| `product_feed.py` | 152 | B2B 商品 feed 生成器 — 从事实内核产出结构化商品 feed。 对应缺口第 4 条：垂直 B2B（Alibaba/GlobalSources/Made-in-China/ | build_feed_record, build_product_feed, to_generic_xml_item |
| `public_tech_reference_service.py` | 134 | 公开技术资料引用 — 国标/专利摘要等脱敏改写，供 GEO 内容注入可验证参数。 仅处理用户粘贴或已授权的公开文本；去掉申请人、完整专利号、联系方式，保留技术事实。 | desensitize_public_technical_text, extract_geo_technical_facts, build_technical_reference_ |
| `ranking_loop_service.py` | 303 | 获客排名闭环 — GSC/百度真值回收接入 headless 排名探针。 补齐蓝图 P2：GSC 回收从「只读面板」升级为「判定器」—— - GSC performance 真值  | collect_gsc_evidence, collect_baidu_evidence, probe_google_engines, summarize_ranks, build |
| `tavily_search.py` | 110 | Tavily 外网 AI/SEO 新闻搜索（RADAR-09）。 | tavily_configured, fetch_tavily_search, fetch_tavily_radar_items |
| `tech_radar_fetch.py` | 746 | GEO 技术雷达 v2 — 定时抓取 GEO/SEO 最新论文、论坛、白帽技术、开源工具。 抓取源分类： 1. 学术论文 — arXiv GEO/LLM-SEO 相关论文 2. 行 | RadarSource, RadarItem, fetch_tech_radar, fetch_latest_geo_techniques, update_tactics_from |
| `tech_radar_reports_service.py` | 56 | RADAR-06/08：技术雷达 Markdown 日报索引。 | list_tech_radar_reports |

## services/registry · 11 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `__init__.py` | 57 | 能力注册表服务包（轮17）。 统一入口导出各服务工厂，供 API 路由/编排层调用。 覆盖 083 迁移 8 张表（skills/skill_versions/mcp_server |  |
| `common.py` | 52 | 注册表公共工具：JSON 安全解析、状态校验、唯一性帮助。 | parse_json, into_json, valid_name, ensure_in, commit_or_rollback |
| `data_source_service.py` | 148 | 数据源合规评审服务（轮17-6）。 §5.2.4：数据源接入前必须登记四元元数据（name/data_class/license_basis/ tos_verified）并经评审； | DataSourceNotFoundError, DataSourceConflictError, DataSourceService, build_data_source_ser |
| `matrix.py` | 125 | Skill 运行态 × 发布态 映射矩阵（轮17-5）。 Trade AI BaseSkill 使用运行态（SKILL_STATUS，5 态：pending/running/suc | RunStatus, PublishStatus, can_start, action_on_running, publish_transition |
| `mcp_service.py` | 367 | MCP 注册表服务（轮17-3；轮19 扩展 connector-manifest 字段）。 替代 agent_hub_service 的进程内 _custom_mcp_serve | McpNotFoundError, McpConflictError, McpService, build_mcp_service |
| `permissions.py` | 115 | Permissions 权限矩阵（轮17-8）。 能力资源访问权限精确到五级：read / write / execute / delete / publish。 - 默认 NO  | Permission, granted, build_granted, can, describe |
| `plugin_service.py` | 175 | Plugin 注册表服务（轮17-4）。 plugins/plugin_versions 表持久化。Plugin 带 manifest（JSON 容器），版本化发布。 与 Skil | PluginNotFoundError, PluginConflictError, PluginService, build_plugin_service |
| `skill_base.py` | 235 | Skill 运行时基类（移植自 Trade AI Agent `app/core/skill_base.py`，MIT，保留出处）。 改造点（合并红线 §融合裁决）： - 去掉原  | SkillStatus, BaseSkill, SkillRegistry, register_skill |
| `skill_pack_loader.py` | 370 | 技能包扫描解析器 —— 把磁盘上的 SKILL.md 技能包变成编排可消费的索引。 背景（本文件存在的理由）： 项目内有大量**真实技能资产**躺在磁盘上，但后端代码此前**从不读 | SkillPackEntry, resolve_skill_pack_dirs, discover_skill_packs, load_skill_body, score_skil |
| `skill_service.py` | 577 | Skill 注册表服务（轮17-1/17-2）。 替代 SkillRegistry 的内存 list（Trade AI skill_base.py 的 register/get/l | SkillNotFoundError, SkillConflictError, IllegalTransitionError, SkillService, build_skill_ |
| `tenant_toggle.py` | 89 | 租户能力开关（轮17-7）。 tenant_capability_toggles：按租户 × 能力类型 × 能力实例 显式启用/停用。 默认 enabled=False，必须显式启 | TenantToggleService, build_tenant_toggle_service |

## services/platforms · 9 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `__init__.py` | 20 | -*- coding: utf-8 -*- |  |
| `b2b_global.py` | 320 | 海外 B2B 拓客适配器 — Alibaba 国际站 / Made-in-China / GlobalSources。 对应缺口 #1（海外 B2B 空白）。遵守 publish_ | B2BGlobalPublisher, B2BPublisherAdapter, AlibabaPublisherAdapter, MadeInChinaPublisherAdap |
| `baijiahao.py` | 401 | 百度百家号发布适配器 — 真实对接百家号开放平台 API。 支持: - OAuth 2.0 授权流程 - 图文文章发布 - 发布状态查询 - 数据回采（阅读量/评论数/推荐量） - | BaijiahaoPublisher, BaijiahaoPublisherAdapter |
| `csdn.py` | 299 | CSDN 发布适配器 — 真实对接 CSDN 博客 API。 支持: - Cookie 模拟登录 - Markdown 文章发布 - 分类/标签设置 - 发布状态查询 - 数据回采 | CSDNPublisher, CSDNPublisherAdapter |
| `toutiao.py` | 396 | 今日头条发布适配器 — 真实对接头条号开放平台 API。 支持: - OAuth 2.0 授权流程 - 图文文章发布 - 微头条发布 - 发布状态查询 - 数据回采 - 指数退避重 | ToutiaoPublisher, ToutiaoPublisherAdapter |
| `wechat.py` | 296 | 微信公众号发布适配器 —— 真实对接微信公众平台 API | WeChatPublisher, WeChatPublisherAdapter |
| `weibo.py` | 452 | 微博发布适配器 — 真实对接微博开放平台 API。 支持: - OAuth 2.0 授权流程 - 短微博/长微博（头条文章）发布 - 图片上传 - 发布状态查询 - 数据回采（转发 | WeiboPublisher, WeiboPublisherAdapter |
| `xiaohongshu.py` | 374 | 小红书发布适配器 — 真实对接小红书创作者平台 API。 支持: - Cookie 模拟登录 - 图文/视频笔记发布 - 图片上传 - 话题标签 - 数据回采（点赞/收藏/评论）  | XiaohongshuPublisher, XiaohongshuPublisherAdapter |
| `zhihu.py` | 326 | 知乎发布适配器 — 真实对接知乎专栏 API。 支持: - Cookie 模拟登录 - 专栏文章发布（Markdown / HTML） - 发布状态查询 - 数据回采（点赞/评论/ | ZhihuPublisher, ZhihuPublisherAdapter |

## services/publish_workers · 9 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `__init__.py` | 13 | 多平台视频发布 Worker — SAU / biliup / 小红书 MCP / AiToEarn 分层。 |  |
| `biliup_worker.py` | 114 | biliup CLI Worker — B站专用，可解析 BV 回执。 | biliup_cli_path, biliup_enabled, publish_via_biliup |
| `dual_line.py` | 121 | 双线发布 — 主路（SAU/专用 Worker）+ 备路（AiToEarn）同时部署，主败备上。 | primary_line_ready, fallback_line_ready, dual_line_status, dual_line_block_reason, annotat |
| `media_fetch.py` | 100 | 将云视频 URL 拉到 Worker 本地路径（SAU / xhs-mcp 需要本地文件）。 | download_video_to_temp, download_image_to_temp |
| `sau_sidecar.py` | 177 | SAU HTTP Sidecar 客户端 — 远程 Worker 机执行 Playwright 上传。 | sau_sidecar_enabled, sau_sidecar_base, sau_sidecar_health, submit_sau_publish_job, poll_sa |
| `sau_worker.py` | 405 | social-auto-upload CLI Worker — 抖音/快手/B站/小红书/视频号。 | sau_cli_path, sau_enabled, sau_account_name, sau_bind_hint, format_sau_schedule, sau_check |
| `tier_router.py` | 146 | 发布分层路由 — 集 SAU / biliup / xhs-mcp / 原生 / AiToEarn。 | platform_tier_chain, any_publish_worker_ready, preflight_workers, preflight_workers_async, |
| `verify.py` | 84 | 发布后验真 — 无 platform URL/ID 一律不算成功。 | extract_post_url_from_text, extract_bvid_from_text, verify_publish_outcome |
| `xhs_mcp_worker.py` | 117 | xiaohongshu-mcp HTTP Worker — 小红书视频真发。 | xhs_mcp_enabled, publish_via_xhs_mcp |

## services/seo · 9 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `inclusion_check_service.py` | 191 | SEO 收录复检 — 供 API 与 Celery 共用。 | inclusion_probe_status, recheck_inclusion_batch |
| `inclusion_probe.py` | 147 | 搜索引擎收录探测 — Baidu site: 查询（失败可降级 HTTP 探活）。 | probe_url_inclusion |
| `inclusion_probe_cache.py` | 73 | 收录探测 probe_mode 侧车缓存（无 schema 迁移）。 | set_probe_mode, get_probe_mode |
| `indexnow_service.py` | 74 | IndexNow 开放极速收录协议服务。 支持向微软 Bing、Yandex 及各主流搜索引擎联盟实时推送新增/变更 URL， 打破传统蜘蛛轮巡等待周期，实现发布后 24 小时内闪 | IndexNowService |
| `product_seo_generator.py` | 256 | 产品 AI SEO 内容与差异化（千人千面）生成服务。 依托 Google EEAT (经验/专业/权威/信任) 与 Information Gain 算法专利规范， 为每个租户的 | ProductSeoGenerator |
| `rank_scheduler_ops.py` | 125 | Hermes ops：Rank Scheduler 状态与 keywords 表同步。 | sync_keywords_from_db, recent_rankings, build_rank_scheduler_ops_snapshot, run_rank_check_ |
| `seo_matrix_db_health.py` | 85 | SEO-09：独立 SEO 矩阵库连通性探针（司令部健康）。 | seo_matrix_db_health |
| `seo_research_hints_service.py` | 122 | SEO-10：矩阵词/收录关键词 → DeerFlow research_hints。 | collect_seo_hints, sync_seo_research_hints, sync_all_active_tenants |
| `seo_utm_service.py` | 40 | SEO-11：矩阵发布 URL 追加 UTM 便于 PostHog/流量归因。 | append_publish_utm |

## services/wangcai · 8 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `__init__.py` | 10 | 旺财租户前台智能助手链路增强（总纲 §7A / 实施指南 N1-N8）。 阶段 1（知识接通，不依赖 LLM 可上线）： - N1 意图识别层：intent.py（≈12 意图注册 |  |
| `intent.py` | 248 | 旺财 N1 意图识别层（实施指南 §1，总纲 §7A 阶段 1）。 设计（指南 1.4）： - IntentRegistry 注册表式：新增意图不改核心代码（对齐 Skill 版本 | IntentResult, IntentDef, register_intent, detect_intent, list_intents |
| `knowledge.py` | 208 | 旺财 N2 知识检索层（实施指南 §2，阶段一：SQL 关键词起步）。 设计（指南 2.4）： - KnowledgeRetriever.search(tenant_hint, q | KnowledgeHit, RetrievalResult, KnowledgeRetriever, tokenize, score_text, rank_hits, miss_r |
| `llm.py` | 216 | 旺财 N4 LLM 调用层（实施指南 §4，总纲 §7A 阶段 2）。 纪律（实施指南 4.1/4.6）： - 只经 `get_ai_engine()` 单例（Model Gate | DraftAnswer, WangcaiLLM, build_prompt |
| `memory.py` | 180 | 旺财 N3 上下文记忆层（实施指南 §3）。 设计（指南 3.4）： - SessionStore：get_or_create(visitor_ref, tenant_id) /  | Turn, SessionRecord, ContextWindow, SessionStore, build_context, resolve_coreference_hint |
| `persistence.py` | 236 | 旺财 N3/N7 持久化接线（迁移 094：wangcai_sessions + wangcai_qa_log，轮14）。 设计纪律（对齐总纲 §7A.3 / 实施指南 3.4、4 | DbSessionStore, qa_persist_enabled |
| `router.py` | 423 | WangcaiRouter 总编排（实施指南 §0.1 链路；阶段 1 收口，不依赖 LLM 可上线）。 流程（指南 0.1）： N1 意图 → 新意图：N3 上下文 → N2 知 | WangcaiRouter, llm_enabled, try_llm_reply, build_db_retriever, get_router |
| `wangcai_task_service.py` | 91 | Wangcai ask -> unified ai_task entry (H.5: 旺财接入 Hermes 任务面). 公开旺财端点保持响应契约不变，但执行改走与 UBrain（ | WangcaiChatTaskError, run_wangcai_task |

## services/browser_runtime · 7 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `__init__.py` | 19 | Browser Runtime（P5）— Playwright + CDP 浏览器执行层（总纲 §4.7）。 本轮 25-B 仅落地骨架（runtime 核心 + 租户 Profi |  |
| `evidence.py` | 311 | 证据回传模型（总纲 §4.7 P5：合规执行须留证）。 每次 Browser Runtime 实际执行（无论成功失败）必须产出 EvidenceRecord （结构化、append | EvidenceRecord, persist_evidence |
| `exceptions.py` | 24 | Browser Runtime 异常体系。 | BrowserRuntimeError, BrowserRuntimeDisabled, BrowserRuntimeUnavailable, BrowserRuntimePoli |
| `executor.py` | 857 | Browser Runtime 真实执行器（轮25-C，Playwright 真接入）。 按 evidence.py 的 EvidenceRecord 6 态契约，落地 navig | run_real_execution |
| `policy.py` | 390 | Browser Runtime Policy 闸门（总纲 §4.7 + 既有 Policy Engine 复用）。 本轮 25-B 提供轻量内置闸门（域名/动作/输入模式三层最小集 | PolicyVerdict, check_action, check_url, check_input, check_all, check_click_target, check_ |
| `profile.py` | 157 | 租户 Profile 隔离（总纲 §4.7：每租户独立 Profile 防跨租户泄漏）。 红线 1：Profile 路径不可越界（任何 resolve 调用必须落在 config  | ProfilePath, is_runtime_enabled, is_tenant_allowed, ensure_tenant_allowed, resolve_profile |
| `runtime.py` | 230 | Browser Runtime 核心（总纲 §4.7 P5：Playwright + CDP）。 本轮 25-B 仅落地**接口契约 + 降级语义**，真实 Playwright  | status, execute |

## services/deerflow · 7 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `__init__.py` | 32 | DeerFlow 执行引擎 — 状态机驱动的任务编排。 提供复杂任务的规划、执行、审核、断点恢复能力。 状态流转：CREATED -> PLANNING -> EXECUTING  |  |
| `checkpoint.py` | 374 | DeerFlow 断点管理器。 负责保存和恢复任务的执行状态（checkpoint）。 Checkpoint 数据保存到 DeerFlowJob.payload_json 的 JS | Checkpoint, CheckpointSnapshot, CheckpointManager |
| `executor.py` | 1187 | DeerFlow 子任务执行器。 负责执行规划器生成的子任务，每个子任务有独立的 Trace span。 支持独立的重试策略和超时控制。 | SubTaskResult, SubTaskExecutor, SubTaskExecutionError |
| `kernel_bridge.py` | 88 | DeerFlow 内核桥接 — 内容产出时抽取事实层为 FactKernel。 对应缺口 #8：DeerFlow 出 9 意图内容时，把「事实层」抽成内核 JSON， 供统一发布台 | extract_kernel_from_subtask, project_deerflow_output |
| `planner.py` | 391 | DeerFlow 任务规划器。 将复杂任务拆解为可独立执行的子任务，生成执行计划。 规划结果保存到 DeerFlowJob 的 checkpoint 中。 | SubTask, ExecutionPlan, TaskPlanner |
| `reviewer.py` | 312 | DeerFlow 结果审核器。 对执行结果进行审核，决定是否需要人工确认或打回重做。 支持基于规则的自动审核和基于质量评分的智能审核。 | ReviewDecision, ReviewResult, ReviewRule, ResultReviewer |
| `state_machine.py` | 368 | DeerFlow 执行引擎状态机核心。 定义任务生命周期状态、转移规则和转移逻辑。 使用数据库事务保证状态转移的一致性。 状态流转图： CREATED -> PLANNING -> | DeerFlowStatus, TransitionResult, DeerFlowStateMachine, DeerFlowStateMachineError |

## services/moss_vl · 7 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `__init__.py` | 23 | OpenMOSS / MOSS-VL 完整多模态开源引擎包。 提供离线视频全景推理、Real-Time 流式会话、XRoPE 时空三维位置编码、 官方权重/量化加载器以及仓库同步工 |  |
| `hot_reload_manager.py` | 289 | MOSS-VL 官方仓库追踪、双缓冲热更新与版本回滚管理器。 工业级模型版本生命周期治理体系： 1. 实时追踪复旦 OpenMOSS 官方仓库（GitHub / ModelScop | MossVersionSnapshot, MossRuntimeInstance, MossHotReloadManager |
| `model_loader.py` | 83 | MOSS-VL 官方模型权重加载器与量化支持。 原生支持从 Hugging Face 或阿里魔搭（ModelScope）加载： - `OpenMOSS-Team/MOSS-VL`  | MossVLModelLoader |
| `offline_inference.py` | 114 | MOSS-VL 官方离线视频全景推理引擎。 对齐官方 `inference/run_inference.py` 架构： 支持完整长视频全景抽帧、多分辨率 Token 视觉编码、密集 | DenseEventAnnotation, OfflineInferenceEngine |
| `realtime_session.py` | 130 | MOSS-VL-Realtime 官方实时流式会话 API。 100% 对齐官方 Hugging Face `OpenMOSS-Team/MOSS-VL-Realtime` 接口： | StreamFrame, StreamMessage, MossRealtimeSession, create_realtime_session |
| `repo_syncer.py` | 119 | MOSS-VL 官方开源仓库自动化同步与环境检测工具。 | MossRepoSyncer |
| `xrope_spatial_temporal.py` | 67 | XRoPE (Cross-attention Rotary Position Embedding) 时空三维统一位置编码器。 基于复旦大学 MOSS-VL 核心技术报告 (arXi | SpatiotemporalCoordinate, XRoPEEmbedding |

## services/paperclip · 7 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `__init__.py` | 3 | -*- coding: utf-8 -*- |  |
| `approval_gate.py` | 351 | Paperclip 审批门服务。 管理 Agent 雇佣、任务执行等关键操作的审批流程。 | create_approval, approve, reject, get_pending_approvals, auto_expire, execute_hire_agent |
| `budget_guard.py` | 237 | Paperclip 预算控制服务。 管理 Agent 月度积分预算：余额检查、消费扣费、月初重置、预警。 | check_budget, consume_credits, reset_monthly_budgets, get_budget_status, budget_overview,  |
| `goal_chain.py` | 335 | Paperclip 目标对齐链服务。 构建使命 → 项目 → 目标 → 任务的完整链路，支持进度冒泡更新。 | build_goal_chain, get_agent_context, update_progress, get_goal_tree, create_goal, list_com |
| `heartbeat_engine.py` | 500 | Paperclip 心跳调度引擎。 以 daemon 线程定时扫描所有 heartbeat_enabled=True 且到期的 Agent， 执行心跳：检查预算 → 查询 pend | PaperclipHeartbeatEngine, list_company_heartbeats, trigger_manual_heartbeat, engine_status |
| `orchestrator.py` | 999 | Paperclip 核心编排服务。 管理公司、Agent、目标、任务的全生命周期。 融合 Hermes + DeerFlow 架构，为 Agent 提供心跳驱动的自动执行能力。 | create_company, hire_agent, fire_agent, assign_goal, create_task, delegate_task |
| `tenant_context.py` | 365 | Paperclip 租户业务上下文 — 聚合产品/视频/询盘/行业数据供 220 个 Agent 使用。 每个租户的 220 个 Agent 都通过此模块获取完整的业务上下文， 确 | build_tenant_business_context, build_agent_mission_prompt |

## services/pipeline · 7 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `__init__.py` | 9 | 四链路强制流水线（总纲 §6：双关卡与四链路加固）。 S1 框架核心（§6.6）：状态机 / 关卡骨架 / 幂等与 lease 语义。 本包为纯逻辑层，不依赖 ORM/路由；DB  |  |
| `__init__.py` | 4 | 双关卡（总纲 §6.4-1/2）：清洗关（CleanseGate）与复核关（ReviewGate）。 |  |
| `chains.py` | 159 | 四链路业务侧关卡接入（总纲 §6.4/§6.6：文章/视频/邮件/多平台分发）。 设计语义（对齐 §6.4 与 §6.6 风险规避）： - **硬拦截仅发生在清洗关**（品牌风险/ | ChainGateReport, gates_enabled, gate_content, outreach_hold_decision |
| `cleanse.py` | 165 | 清洗关卡 CleanseGate（总纲 §6.4-1）。 职责：发布物进入复核前的强制清洗检查；**未过不得进复核**（红线）。 聚合策略（§6.4-1）：结构化问题清单（code | CleanseIssue, CleanseReport, CleanseGate, register_checker |
| `review.py` | 135 | 复核关卡 ReviewGate（总纲 §6.4-2）。 职责：清洗通过后的第二道关。自动复核（打分≥阈值→自动通过）+ 低分/高风险→人工复核；复核三态：通过 / 驳回 / 修改重 | ReviewVerdict, ReviewGate, register_scorer |
| `state_machine.py` | 106 | 流水线状态机（总纲 §6.5：11 态）。 主链：generated→cleansing→cleansed→reviewing→approved→distributing→veri | InvalidTransition, can_transition, apply_transition, main_path |
| `wiring.py` | 174 | Pipeline S3 接线（总纲 §6.4 / V1.7 待办）：存量质量件注册入双关卡。 接线清单（全部惰性导入 + 故障隔离；组件不可用 → 跳过该检查器，关卡逻辑不变）：  | brand_guard_checker, compliance_checker, build_cleanse_gate, content_scorer_scorer, eeat_s |

## services/crawlers · 6 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `__init__.py` | 4 | Crawler sidecar integrations. |  |
| `ecommerce_crawlers_compliance.py` | 241 | ECommerceCrawlers 合规门禁 — 无 Sidecar / 无授权 / 无 evidence 一律拒绝。 | ComplianceDecision, assert_spider_compliance, validate_spider_result |
| `ecommerce_crawlers_registry.py` | 427 | ECommerceCrawlers 爬虫配方注册表 — 映射 GitHub 子项目到本系统能力。 来源：https://github.com/DropsDevopsOrg/ECom | SpiderRecipe, recipe_by_id, recipes_for_lane, callable_recipes, registry_payload |
| `ecommerce_crawlers_sidecar.py` | 212 | ECommerceCrawlers Sidecar — 外置 Python 爬虫 Worker HTTP 网关。 | sidecar_base_url, sidecar_token, ecommerce_crawlers_sidecar_status, run_spider, enrich_osi |
| `ecommerce_crawlers_smart.py` | 361 | ECommerceCrawlers 智能层 — 大白话状态、自动补全合规字段、一键探测。 | build_panel, resolve_spider_id, apply_run_defaults, quick_run, enrich_result_zh, domestic_ |
| `media_crawler_sidecar.py` | 145 | MediaCrawler Sidecar — NanmiCoder/MediaCrawler HTTP gateway (social_restricted). | sidecar_base_url, sidecar_token, media_crawler_sidecar_status, run_media_spider |

## services/tasks · 6 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `__init__.py` | 3 | -*- coding: utf-8 -*- |  |
| `deerflow_bridge.py` | 158 | DeerFlow → ai_tasks 影子双写桥（总纲 §4.6-1 收编过渡；轮24-A 首批调用方）。 总纲裁决：ai_tasks 是任务真相源，DeerflowJob/Pa | DeerflowTaskBridge, idempotency_key_for |
| `hermes_task_bridge.py` | 698 | ai_tasks → Hermes 编排桥（打通中央断点；总纲 §4.6 / 轮24 后续）。 背景：ai_tasks 是一张"被动影子表"——状态机/checkpoint 真实， | HermesNodeExecutionError, dispatch_ai_task |
| `paperclip_approval_bridge.py` | 180 | Paperclip 审批闸口与 Hermes 等人任务桥。 Hermes 的 `wait_human` 节点原本只能靠任务控制面手动放行；这里把它同步成 Paperclip 审批记 | create_task_approval, resume_approved_task, cancel_rejected_task |
| `paperclip_bridge.py` | 192 | Paperclip → ai_tasks 影子双写桥（总纲 §4.6-1 收编过渡第 2 迭代；轮24-B）。 与 deerflow_bridge 同构：把 PaperclipTa | PaperclipTaskBridge, idempotency_key_for, resolve_tenant_id |
| `task_control.py` | 586 | 统一任务控制面服务（总纲 §4.6-1/§4.6-2 / §8 082；轮23 任务端接线）。 把 ai_tasks → task_traces → terminal_hook(e | TaskControlError, TaskNotFound, InvalidTaskTransition, QuotaGateDenied, can_transition, si |

## services/agent_loop · 5 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `__init__.py` | 12 | Agent 任务循环 — bounded 工作流（非开放域 Autonomous Agent）。 |  |
| `growth_workflow.py` | 611 | 增长工具 Agent 工作流 — 热词 → 成稿 → 质检 → 引流监测快照。 | _GrowthRunExecutor, create_growth_run, get_growth_run, execute_growth_run |
| `run_repository.py` | 173 | Agent run 持久化与查询。 | calc_run_progress, upsert_run, sync_run, load_run_from_db, get_run, list_runs |
| `session_store.py` | 95 | Agent run 状态存储（内存 + 可选 Redis）。 BUG-15 修复：添加持久化保障和异常处理。 Redis 不可用时仍保持内存存储，但添加明确警告日志。 | new_run_id, save_run, load_run, patch_run, patch_task |
| `workflow_presets.py` | 61 | 增长跑盘预设模板。 | list_presets, preset_by_id |

## services/ai · 5 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `ai_engine_v2.py` | 405 | AI引擎 v2 - 基于真实LLM调用的完整实现 功能： 1. AI内容生成（真实LLM调用，通过AIEngine单例） 2. 多LLM调度（DeepSeek/OpenAI/Gem | LLMProvider, OpenAIProvider, GeminiProvider, ClaudeProvider, generate_content, chat |
| `analytics_insight_service.py` | 573 | AI数据洞察服务 - 基于真实LLM调用 功能： - 异常检测（基于统计规则 + AI解释） - 趋势预测（AI分析数据趋势） - 智能洞察生成（调用LLM分析数据） - 自动可视 | InsightRequest, Insight, InsightResult, generate_insights, recommend_visualization |
| `hallucination_detector.py` | 161 | 幻觉检测器：纯规则引擎，无网络依赖。 检测维度： 1. 关键词一致性 —— response 中的专有名词/数字能否在 prompt 中找到依据 2. 自我矛盾检测 —— 同一实体 | fact_check |
| `recommendation_service.py` | 458 | AI推荐系统服务 - 基于真实协同过滤算法与LLM解释生成 功能： - 协同过滤（基于用户相似度和物品相似度） - 内容推荐（TF-IDF相似度） - 混合推荐（协同过滤 + 内容 | RecommendationRequest, RecommendedItem, RecommendationResult, generate_recommendations, bu |
| `security_scan_service.py` | 358 | AI安全扫描服务 - 基于真实LLM调用 功能： - 代码安全扫描（调用LLM分析代码安全性） - OWASP Top 10漏洞检测 - 依赖漏洞扫描 - 配置安全审计 - 结构化 | SecurityScanRequest, SecurityIssue, SecurityScanResult, scan_code_security, scan_dependenc |

## services/analytics · 5 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `__init__.py` | 3 | -*- coding: utf-8 -*- |  |
| `user_action_analytics_compliance.py` | 191 | UserActionAnalyzePlatform 合规门禁。 | ComplianceDecision, assert_module_compliance, validate_analytics_result |
| `user_action_analytics_registry.py` | 145 | UserActionAnalyzePlatform 模块注册 — Spark 电商行为分析 → 本系统 Lane。 来源：https://github.com/oeljeklaus | AnalyticsModule, module_by_id, callable_modules, registry_payload |
| `user_action_analytics_sidecar.py` | 199 | UserActionAnalyzePlatform Sidecar HTTP 客户端。 | sidecar_base_url, sidecar_token, user_action_analytics_sidecar_status, run_analytics_modul |
| `user_action_analytics_smart.py` | 207 | UserActionAnalyzePlatform 智能层 — 中文状态与一键分析。 | build_panel_slice, conversion_summary_for_growth, resolve_module_id, apply_run_defaults, q |

## services/egress · 5 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `__init__.py` | 16 | 出口 IP 上游采购适配器。 |  |
| `demo_guard.py` | 71 | 清除历史演示 IP 槽位（禁止假数据进入平台池统计）。 | is_demo_egress_endpoint, purge_demo_egress_endpoints |
| `iproyal_client.py` | 271 | IPRoyal Reseller API 客户端 — 静态住宅IP自动采购。 | IPRoyalAPIError, IPRoyalOrderResult, IPRoyalClient |
| `iproyal_provisioner.py` | 107 | IPRoyal 缓冲池适配器 — 从预购池中分配IP，非实时下单。 | PoolExhaustedError, IPRoyalProvisioner |
| `provisioner.py` | 561 | 出口 IP — manual 运营录入 / mock 演示 / asocks JIT 采购 / iproyal 长期养号。 | EgressProvisionerError, PurchasedProxy, EgressProvisioner, MockProvisioner, active_egress_ |

## services/evolution · 5 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `__init__.py` | 26 | AI 进化引擎 — 闭环自进化系统。 流程： 数据收集 → 经验沉淀 → Skill优化 → SOP优化 → 灰度发布 → 效果验证 模块： - engine: 核心进化引擎，编排 |  |
| `canary.py` | 455 | 灰度发布 — Draft → Evaluation → Canary → Approved → Production。 支持按租户/百分比分流，所有进化操作需人工审批才能进入 Pr | CanaryRelease |
| `engine.py` | 629 | 核心进化引擎 — 编排完整闭环。 流程： 数据收集 → 经验沉淀 → Skill优化 → SOP优化 → 灰度发布 → 效果验证 每个阶段通过流水线编排，支持单步执行和全闭环运行。 | EvolutionEngine |
| `experience_store.py` | 383 | 经验存储 — 经验沉淀阶段。 从任务执行记录中提取可复用模式，存入 PostgreSQL JSONB 经验库。 支持经验检索、置信度更新、合并相似经验。 | ExperienceStore |
| `version_control.py` | 425 | Skill/SOP 版本管理 — 语义化版本 + 状态机。 管理 Skill 和 SOP 的版本生命周期： draft → evaluation → canary → approv | VersionControl |

## services/feishu · 5 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `__init__.py` | 19 | -*- coding: utf-8 -*- |  |
| `cards.py` | 246 | -*- coding: utf-8 -*- | FeishuCardBuilder |
| `client.py` | 490 | -*- coding: utf-8 -*- | FeishuClient |
| `handlers.py` | 541 | -*- coding: utf-8 -*- | FeishuMessageHandler |
| `report.py` | 262 | -*- coding: utf-8 -*- | FeishuReportService |

## services/model_gateway · 5 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `__init__.py` | 58 | Model Gateway — 轮16 重构（总纲 §4.6）。 能力标签路由 + 成本记账门面。复用既有 get_ai_engine() 单例，不重建已存在模块。 业务只传 re | is_gateway_enabled |
| `capability.py` | 60 | 能力标签（总纲 §4.6）：reasoning/coding/vision/writing/translation/structured_output/cheap/fast。 业务 | normalize |
| `gateway.py` | 157 | Model Gateway 门面（总纲 §4.6）。 复用既有 get_ai_engine() 单例，不重建已存在模块；新增能力标签路由 + 成本记账。 业务只传 required | ModelGateway, get_model_gateway |
| `ledger.py` | 187 | 成本记账（总纲 §4.6）：每次 LLM 调用写 model_call_ledger，可汇总至 token_ledger。 设计原则： - 复用既有数据库 SessionLocal | CostLedger, aggregate_to_token_ledger |
| `router.py` | 159 | 能力路由：required_capabilities + 四维信号 → ai_engine 场景 tier。 评分维度（总纲 038 并入 Model Router）：Qualit | ModelRouter, resolve_tier |

## services/n8n · 4 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `__init__.py` | 28 | n8n 集成服务模块。 提供 n8n 工作流触发、Webhook 接收、工作流注册三大能力： - webhook.py : 接收 n8n 回调（HMAC-SHA256 签名验证 + |  |
| `trigger.py` | 293 | n8n 工作流触发器。 向 n8n 发送 Webhook 请求触发工作流，支持： - Celery 异步执行 - 失败重试 3 次，指数退避（1s → 2s → 4s） - 触发日 | N8nTriggerService, trigger_n8n_workflow |
| `webhook.py` | 290 | n8n Webhook 接收服务。 接收 n8n 工作流的回调请求，提供： - HMAC-SHA256 签名验证 - JSON 数据解析 - 事件类型路由分发 - 触发后续业务流程 | N8nWebhookService, verify_webhook_signature |
| `workflow_registry.py` | 322 | n8n 工作流注册表。 管理 n8n 工作流的注册、查询、启用/禁用，存储 workflow_id、endpoint、auth_config。 支持内存缓存 + 数据库持久化（通过 | WorkflowRecord, WorkflowRegistry, get_workflow_registry, ensure_builtin_workflows |

## services/payment_pkg · 4 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `__init__.py` | 19 | 支付服务子包（单一职责拆分） - wechat_pay: 微信支付 Native / 验签 / 退款底层能力 - payment_service_impl: 支付订单管理、渠道下单 |  |
| `payment_service_impl.py` | 788 | 通用支付服务（对接订单模型） 本模块只负责支付订单管理、渠道下单、回调处理与入账，迁移自原 app.services.payment_service 的 PaymentServic | PaymentService |
| `verify_flags.py` | 24 | 支付回调验签严格模式 — 单一权威判定。 全仓所有验签 / 严验相关逻辑都必须通过本函数取数，禁止各模块自行用 ``os.getenv("PAYMENT_STRICT_VERIFY | is_payment_strict |
| `wechat_pay.py` | 238 | 微信支付服务（Native 扫码支付 + 回调验签 + 退款） 本模块只负责微信支付相关能力，迁移自原 app.services.payment_service 的 WeChatP | WeChatPayService |

## services/trace · 4 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `__init__.py` | 26 | 统一 Trace / 经验飞轮接线（总纲 §4.6-7 / §6.6 P3）。 - trace_service：task_traces 链式追踪读写 + 记分卡聚合。 - term |  |
| `publish_gate.py` | 236 | Canary 发布门禁（总纲 §1.3 第4条 / §6.6 P3 / E14）。 发布流程：Draft → 评估(Evaluation) → Canary(5/25/50/100 | PublishGate |
| `terminal_hook.py` | 240 | 终态钩子 — 任务终态接线至经验飞轮（总纲 §4.6-7 / §6.6 P3）。 触发时机：Pipeline / Hermes / DeerFlow 等执行到达终态（done/fa | promote_experience_stage, record_terminal_state |
| `trace_service.py` | 323 | 统一 Trace 服务 — 链式追踪的写入/读取与记分卡聚合（总纲 §4.6-7 / §8 085_traces）。 - start/complete/fail：任务执行生命周期落 | TaskTraceService |

## services/deepseek_harness · 3 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `__init__.py` | 18 | DeepSeek Harness 外层智能体运行时接入包。 把开源 "一切皆插件" Agent 运行时 DeepSeek Harness（dsh，github.com/deepse |  |
| `client.py` | 131 | DeepSeek Harness 客户端（懒加载官方 SDK，绝不污染导入期）。 对外暴露三个安全函数： - is_available() : SDK 与运行时二进制是否就绪 -  | is_available, runtime_path, health, run_turn, get_experience_suggestions, record_intent_re |
| `config.py` | 130 | DeepSeek Harness 接入配置（纯标准库，无重依赖，保证本包可随时安全导入）。 所有配置均可通过环境变量覆盖；未设置时使用与项目布局匹配的默认值。 关键路径： - re | DeepSeekHarnessSettings, get_settings |

## services/goodjob · 3 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `__init__.py` | 4 | GoodJob 附属桥服务（批次 B：customer_pool 投影 + 单证委派）。 |  |
| `customer_pool_projection.py` | 107 | customer_pool 投影同步 · UJ 真相 → GoodJob 工作副本. 设计出处：uj-annex-integration-design §10.5 / §10.19 | build_projection, projection_idempotency_key, sync_inquiry_to_pool |
| `trade_document_bridge.py` | 150 | trade-documents 桥 · 单证生成委派 GoodJob（批次 B）. 设计出处：uj-annex-integration-design §10.18（六件套缺口扫描） | document_idempotency_key, submit_document_task, poll_document_task, submit_stage_sync_task |

## services/matching_engine · 3 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `__init__.py` | 24 | Product Finder 匹配引擎包。 暴露 ``MatchingEngine`` 及请求/响应模型，供路由层调用。 |  |
| `engine.py` | 557 | Product Finder 匹配引擎（纯函数，不依赖 FastAPI / SQLAlchemy）。 三层算法： 第一层 硬条件过滤（Eligibility）：防火等级、导热系数上 | MatchingEngine |
| `schemas.py` | 99 | Product Finder 匹配引擎 — 请求 / 响应 Pydantic 模型。 这些模型仅描述数据结构，不包含任何业务逻辑，可被路由层与引擎层共用。 所有判定严格基于真实 P | ProductMatchRequest, DimensionScores, MatchItem, RejectedItem |

## services/site_builder · 3 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `__init__.py` | 8 | 一键建站编排服务 — 端到端站点生成流水线。 |  |
| `orchestrator.py` | 521 | 一键建站核心编排器。 串联 Vision 分析、结构生成、多语言内容、SEO 优化、站点组装五个步骤， 输出完整站点数据结构。 | SiteBuildError, SiteBuilderOrchestrator |
| `prompts.py` | 144 | 一键建站各步骤 Prompt 模板。 每个步骤有独立的 system / user prompt 组合，用于驱动 LLM 完成特定子任务。 | build_vision_user_prompt, build_structure_user_prompt, build_content_user_prompt, build_se |

## services/vault · 3 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `__init__.py` | 26 | 凭证库包（总纲 §8 迁移 087；轮20）。 |  |
| `credential_service.py` | 376 | 凭证库服务（总纲 §3.1/§8 迁移 087；轮20）。 统一密钥入库：store（加密+AAD 四元绑定）→ resolve（解密，校验绑定与 授权）→ rotate（轮换，旧 | VaultError, CredentialNotFoundError, CredentialRevokedError, GrantDeniedError, make_vault_ |
| `crypto.py` | 137 | 凭证库加密层（总纲 §3.1/§8 迁移 087；轮20）。 - 默认后端 aes_gcm：AES-256-GCM（复用 field_crypto 的 HKDF 派生模式）， AA | VaultCryptoError, AadMismatchError, aad_string, aad_fingerprint, encrypt_with_aad, decrypt |

## services/adapters · 2 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `__init__.py` | 10 | Adapter 层（Execution Plane 平级适配器集合，总纲 §3.1）。 本包只放外部能力的适配桥接，禁止业务逻辑；所有适配器必须： 1. 不持有链路状态（状态归 a |  |
| `__init__.py` | 242 | Trade AI Agent 适配器（总纲 §5.2：代码级嫁接，MIT）。 来源：Trade AI Agent（Gitee: LBones-li/agent_trade_b，RE | tenant_orchestrator, make_context, is_available |

## services/annex · 2 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `__init__.py` | 4 | 附属统一身份域：UJ 为唯一身份源（annex_ticket 短时票据，§9.3）。 |  |
| `ticket_service.py` | 236 | 附属统一登录票据服务 · UJ 为唯一身份源. 设计出处：uj-annex-integration-design §9.3（短时授权票据 annex_ticket）； 用户指令：附 | TicketRejected, annex_role_for, issue_annex_ticket, redeem_annex_ticket, bridge_token_matc |

## services/billing · 2 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `meter_event.py` | 577 | 统一计量埋点与账单对账（总纲 §4.6-8 / §6.6 P4 / §7.6） - emit*：7 类埋点动作，append-only 写入 meter_events（event_ | MeterEventService, emit_ai_generation_best_effort, record_meter_event |
| `subscription_countdown.py` | 89 | 订阅到期倒计时 · 纯函数服务（零迁移、零外部依赖）. 数据源均为既有字段：tenants.expires_at / tenants.trial_ends_at、 licenses | CountdownState, compute_subscription_countdown, due_dunning_action |

## services/calculators · 2 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `__init__.py` | 8 | Calculator 包 — 工程计算器（Thermal / Fire Protection / Quantity）。 所有计算均为确定性工程规则；输出必须显示假设、单位与适用范围 |  |
| `engine.py` | 142 | 工程计算器引擎 — 纯函数，无 Web 依赖，可单元测试。 包含： - thermal_calc 热工计算（U值/热损失/保温厚度估算） - fire_calc 防火计算（钢构件防 | thermal_calc, fire_calc, quantity_calc |

## services/orchestrator · 2 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `__init__.py` | 8 | 商业闭环编排器 — 串联从产品输入到成交的完整链路。 |  |
| `commercial_loop.py` | 288 | 商业闭环编排器。 从产品输入到成交的完整链路: 自然语言+产品图片 → AI建站 → 内容/视频 → SEO/GEO/AEO → 多平台分发 → 获客 → Lead评分 → CRM | CommercialLoopOrchestrator |

## services/policy · 2 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `__init__.py` | 8 | Policy Engine 包（总纲 §3.1/§6.6 P2；轮20）。 |  |
| `engine.py` | 253 | Policy Engine：统一策略裁决（总纲 §3.1/§7.2/§6.6 P2；轮20）。 升级 paperclip approval_gate（人审）+ budget_gua | PolicyDecision, PolicyEngine, evaluate_action |

## services/facade · 1 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `model_gateway_facade.py` | 54 | 大模型网关防腐层 (Anti-Corruption Layer) - 改造 10 应用 Strangler Fig 模式，在现有的大模型调用服务（如 OpenAI、Gemini 等 | ModelGatewayFacade |

## services/marketing · 1 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `gmc_feed_service.py` | 115 | Google Merchant Center (GMC) 官方规范商品 XML/RSS 2.0 数据流生成服务。 符合 Google 官方 Merchant Center 规范（命 | GmcFeedService |

## services/media · 1 文件

| 文件 | 行 | 说明 | 类/函数 |
|------|---:|------|---------|
| `platform_title_adapt.py` | 37 | VID-11：多平台标题/描述长度适配。 | adapt_title |

## core 基础设施 · 68 文件

| 文件 | 行 | 说明 |
|------|---:|------|
| `core/config.py` | 1112 | -*- coding: utf-8 -*- |
| `core/rate_limit.py` | 600 | API限流中间件 分层限流策略： 1. 登录接口: 5次/分钟/IP（防暴力破解） 2. 注册/验证码: 3次/分钟/IP（防短信轰炸） 3. 普通API: 100次/分钟/IP 4. 全局默认: 2 |
| `core/cache.py` | 569 | 缓存工具模块 — FIX-24: 三级缓存架构 L1: 进程内 LRU（<1ms，容量 1000 条，TTL 30s） L2: Redis（<5ms，容量无限制，TTL 可配置） L3: CDN（Cl |
| `core/waf.py` | 469 | WAF防火墙规则配置 提供SQL注入、XSS、路径遍历等常见攻击防护 |
| `core/event_bus.py` | 432 | 事件总线 + 事件驱动架构 — FIX-41 轻量级进程内事件总线，支持： - 同步/异步事件发布订阅 - 事件优先级 - 事件溯源（可选） - 通配符订阅 |
| `core/product_commerce.py` | 429 | 产品价值主张与计费体系 — FIX-32/33/34: 产品商业化核心 价值主张重新定位： 从"出海营销工具"升级为"AI驱动的出海增长操作系统" 精细化计费体系： 5档套餐 + 获客积分混合计费模型 |
| `core/tenant_middleware.py` | 420 | SaaS 租户中间件 - 从请求域名识别租户 工作流程: 1. 提取 Host 头部 (如 customer1.youding-saas.com) 2. 提取子域名前缀 (如 customer1) 3 |
| `core/repository.py` | 413 | Repository 层 — FIX-42 提供统一的数据访问抽象层，隔离业务逻辑与数据库操作。 支持： - 基础 CRUD 操作 - 分页查询 - 批量操作 - 事务管理 - 缓存集成 |
| `core/logging_config.py` | 402 | 日志轮转和监控告警配置 |
| `core/login_bruteforce.py` | 397 | 登录暴力破解防护：优先 Redis（多实例共享），失败降级进程内内存；接口与阈值行为保持不变。 |
| `core/jwt_key_rotation.py` | 366 | JWT 密钥轮换服务 支持多密钥版本管理，实现安全的密钥轮换策略： 1. 支持多个签名密钥（active + inactive） 2. 新令牌使用最新密钥签名 3. 旧令牌在过渡期内仍可使用旧密钥验证 |
| `core/security/claw_patrol.py` | 364 | Claw Patrol - AI安全防火墙 基于Deno 2.8 Claw Patrol设计，用于防护AI生成代码的恶意执行 功能： 1. 扫描AI生成的代码，检测恶意模式 2. 防止Prompt注入 |
| `core/security.py` | 352 | -*- coding: utf-8 -*- |
| `core/bootstrap.py` | 328 | 应用启动引导模块 — 从 main.py lifespan 中提取调度器启动逻辑，保持行为一致。 所有调度器启动失败不阻塞主进程，仅在日志中记录警告。 每个调度器对应一个注册项，包含：启用条件、工厂函 |
| `core/permissions.py` | 321 | -*- coding: utf-8 -*- |
| `core/exceptions.py` | 309 | -*- coding: utf-8 -*- |
| `core/security/rls.py` | 290 | PostgreSQL Row Level Security (RLS) — 数据库层租户隔离 通过 PostgreSQL 的 Row Level Security 机制，在数据库层面强制执行租户数据隔 |
| `core/admin_auth.py` | 268 | 超级管理员 RBAC 权限鉴权 |
| `core/database.py` | 253 | -*- coding: utf-8 -*- |
| `core/refresh_token_blacklist.py` | 252 | Refresh 令牌轮转黑名单：优先 Redis（多实例 / 重启后仍拒绝已吊销 refresh），失败降级进程内内存。 |
| `core/validation.py` | 248 | 输入验证模块 |
| `core/data_classification.py` | 239 | 数据安全分级分类 — FIX-26: 数据安全分级 + 字段级敏感标签 数据分级： L0 - 公开：无需认证即可访问（如产品列表、案例展示） L1 - 内部：需要认证但非敏感（如用户名、角色） L2  |
| `core/celery_app.py` | 233 | Celery 异步任务队列 — FIX-43 提供 Celery 集成配置和多队列支持： - 高优先级队列（email, lead_verification） - 默认队列（scoring, enri |
| `core/tenant_access.py` | 227 | 租户侧访问控制 — ROLE_PERMISSIONS + 超管 DB 权限码 + 路由守卫。 |
| `core/founder_debug_gate.py` | 226 | 创始人专属调试门禁：超管 + 微信唯一（优先）或开发令牌 + 可选 IP。 |
| `core/security_tools.py` | 225 | -*- coding: utf-8 -*- |
| `core/request_signature.py` | 220 | API 请求签名 + 防重放中间件 — FIX-29: 安全增强 防重放策略： - X-Request-Timestamp: 请求时间戳（允许 ±5 分钟窗口） - X-Request-Nonce:  |
| `core/ssl_config.py` | 219 | HTTPS证书配置和SSL中间件 支持Let's Encrypt自动证书管理 |
| `core/security/runtime_isolation.py` | 212 | 运行时租户隔离 — 应用层访问控制 作为租户隔离体系的最后一道防线，在应用运行时验证： - 当前请求的 tenant_id 与目标资源的 tenant_id 是否匹配 - 防止因代码缺陷或逻辑错误导致 |
| `core/jwt_cookie.py` | 210 | JWT HttpOnly Cookie 工具 — FIX-22: 安全升级，Token 不再暴露给 JavaScript。 生产环境 Cookie 属性： - access_token: HttpOn |
| `core/security_middleware.py` | 202 | 安全中间件模块 — 路径安全 + 限流 注意：SQL注入/XSS/路径遍历/命令注入检测已统一由 WAFMiddleware (waf.py) 处理， 本模块不再重复检测，避免规则冲突和性能开销翻倍。 |
| `core/unify_response_middleware.py` | 190 | 将 /api/v1 下「未带 code 字段」的 JSON 成功响应统一包装为 APIResponse， 与 docs/4-API接口定义.md 约定一致；已返回 { code, ... } 的响应原 |
| `core/gm_crypto.py` | 189 | 国密 SM2/SM3/SM4 工具（敏感字段加密、完整性校验、接口签名）。 依赖 gmssl；未安装时 encrypt/decrypt 会抛出明确错误，应用仍可启动。 |
| `core/security_headers.py` | 185 | HTTP安全响应头中间件 添加标准安全响应头防止常见Web攻击 OWASP 推荐安全头: - Content-Security-Policy (CSP) - X-Frame-Options: DENY |
| `core/opentelemetry_config.py` | 183 | OpenTelemetry配置 - 分布式追踪 (租户隔离增强) 所有 Span 强制携带 tenant_id attribute，确保： - 追踪数据可按租户维度过滤和分析 - 多租户环境下便于定位 |
| `core/csrf_middleware.py` | 182 | CSRF Protection Middleware Applies CSRF token validation to cookie-based (session) requests. Bearer- |
| `core/circuit_breaker.py` | 168 | -*- coding: utf-8 -*- |
| `core/cache_decorator.py` | 166 | -*- coding: utf-8 -*- |
| `core/prompt_injection_middleware.py` | 159 | Prompt 注入检测 ASGI 中间件。 功能： - 拦截 POST/PUT 请求，扫描 body 中的注入模式 - 命中则记录安全事件审计日志并返回 403 - 通过环境变量 PROMPT_INJ |
| `core/no_fake_delivery_guard.py` | 158 | 禁止假交付 — 出站响应扫描（生产路径硬拒绝）。 |

## models ORM · 94 文件

| 文件 | 行 | 说明 |
|------|---:|------|
| `models/registry.py` | 400 | 能力注册表持久化模型（总纲 §4.6-4 / §5.2.4 / §8；迁移 083）。 替代 agent_hub_service 进程内内存 list，使 Skill/MCP/Plugin/数据源 具 |
| `models/content.py` | 375 | -*- coding: utf-8 -*- |
| `models/__init__.py` | 299 | -*- coding: utf-8 -*- |
| `models/unified_lead.py` | 286 | 获客数据模型统一（六段式） — FIX-37 统一线索数据模型，将分散的字段合并为六段式标准结构： 1. 身份信息（Identity） - 姓名、邮箱、电话、LinkedIn 2. 公司信息（Comp |
| `models/evolution.py` | 256 | AI 进化引擎数据模型。 存储进化闭环产生的所有数据：任务执行记录、经验条目、Skill/SOP版本、 灰度发布状态、审批记录。 |
| `models/prospect_lead.py` | 203 | 统一线索数据模型 —— 所有渠道的线索收敛到单一模型 去重规则（优先级降序）： 1. 邮箱精确匹配（最高优先级） 2. 域名 + 公司名模糊匹配 3. LinkedIn URL 精确匹配 4. 电话精 |
| `models/region.py` | 200 | -*- coding: utf-8 -*- |
| `models/ab_test.py` | 193 | A/B 测试数据模型 |
| `models/email_outreach.py` | 182 | 邮件外联模型 —— 状态机 + 幂等 + 全链路追踪 状态流转： draft → queued → sending → sent → delivered → opened → clicked ↘ bo |
| `models/admin.py` | 171 | 超级管理员 RBAC 模型 |
| `models/egress.py` | 171 | 静态 IP 槽位与浏览器指纹环境 |
| `models/product.py` | 159 | 产品和分类模型 — 支持 JSON 规格参数、文档管理。 |
| `models/rfq.py` | 155 | RFQ Model - 买家需求单（B2B 询价请求，Finder→RFQ 核心转化闭环） |
| `models/ai_config.py` | 153 | -*- coding: utf-8 -*- |
| `models/trace.py` | 146 | 统一 Trace 与记分卡数据模型（总纲 §4.6-7 / §8 085_traces）。 - task_traces：链式追踪表（TASK-013）。prompt 正文只存对象存储引用，正文不入库； |
| `models/company.py` | 145 | Company 360 - B2B 公司主数据 + 联系人 + 采购信号（Phase 3 地基） |
| `models/paperclip.py` | 127 | Paperclip Agent 编排层数据模型。 融合 Paperclip 理念到现有 Hermes + DeerFlow 2.0 架构： - Company: 公司/租户级实体，对齐目标和预算 -  |
| `models/im_routing_and_specs.py` | 121 | 商家IM路由配置表和建材垂直参数表 - SQLAlchemy ORM模型 根据文档14.1章节： 1. MerchantIMRouting - 商家即时通讯分流配置表 2. BuildingMater |
| `models/geo_alert_models.py` | 119 | GEO Alert Models - 预警数据模型 从 sourcechain-geo-engine 的 models/alerts.py 转移而来 用于 GEO 排名监控、性能异常、询盘转化率等预警 |
| `models/nurture_cycle.py` | 119 | 持久化养号周期 + 平台养号规则模板（从 AiToEarn 互动管理模型合并）。 |
| `models/tenant.py` | 119 | SaaS多租户模型 |
| `models/geo_sourcechain_models.py` | 117 | GEO SourceChain Models - SourceChain GEO Engine database models (non-alert tables) This module defin |
| `models/vault.py` | 117 | 凭证库持久化模型（总纲 §1.2 / §4.6 / §8 迁移 087；轮20）。 credentials：统一密钥入库加密（AES-256-GCM 默认 / SM4 国密可选）， AAD 四元绑定（ |
| `models/enums.py` | 114 | 状态枚举定义 —— ORCH-08/09/10 修复 统一订单、支付、商机等核心实体的状态词汇，避免多套互斥词汇并存。 |
| `models/seo.py` | 114 | -*- coding: utf-8 -*- |
| `models/license.py` | 113 | License Model - 许可证管理模型（P1-5 扩展：设备指纹 + 授权码 + 套餐订单） |
| `models/ai_task.py` | 106 | 统一任务控制面模型（总纲 §4.6-1 / §8 082_unify_ai_tasks；轮23 补 ORM 映射）。 ai_tasks 表由迁移 082 建好（11 态状态机 + 幂等 + check |
| `models/ubrain_decision.py` | 105 | UBrain AI Agent 决策追踪模型 |
| `models/invoice_application.py` | 102 | 增值税发票开票申请（合规：申请≠已开票，须财务审核及税控开具）。 |
| `models/globalization.py` | 96 | 全球化多语言模型 - GlossaryTerm: 行业术语多语言标准化 - TranslationTask: 翻译任务与进度跟踪 - TranslationRecord: 逐条翻译记录 |
| `models/eeat.py` | 93 | -*- coding: utf-8 -*- |
| `models/ai_visibility.py` | 92 | GEO / AI Visibility 数据模型 — AI 搜索可见性监控（Phase 6） |
| `models/user.py` | 91 | 用户模型 — 支持多角色、第三方登录、AI 推荐等。 |
| `models/content_feedback.py` | 88 | Content Feedback Loop — DB models for feedback checks and industry patterns. Tables: - content_feedb |
| `models/payment.py` | 87 | 支付模块模型 - 支付订单与支付渠道配置 |
| `models/ubrain_commercial_os.py` | 86 | DeerFlow ↔ Accio 商业 OS：研究洞察、编排执行、效果回流。 |
| `models/agent_tree.py` | 85 | 代理层级关系树 代理组织树模型：定义 L1-L5 五级代理层级结构， 支持逐级向上汇总和向下钻取的数据聚合查询。 |
| `models/compliance.py` | 83 | 合规检查相关数据库模型 |
| `models/campaign.py` | 78 | Campaign / ABM 数据模型 — AI Outbound 序列（Phase 5） |
| `models/shipping_timeline.py` | 75 | -*- coding: utf-8 -*- |

## api 路由 · 255 文件

| 文件 | 行 | 说明 |
|------|---:|------|
| `api/v1/routes/seo_matrix.py` | 2372 | 全国县域建材SEO矩阵系统 API路由 |
| `api/v1/routes/hermes.py` | 1832 | Hermes 内部插件平台 API — 运维/编排；租户侧请用旺财插件市场。 |
| `api/v1/routes/tenants.py` | 1542 | SaaS多租户与商业化路由 - 真实数据库实现 |
| `api/v1/routes/media_factory.py` | 1435 | 多媒体内容工厂路由。 |
| `api/v1/routes/super_agent.py` | 1307 | UBrain 超级智能体 API 路由 集成 DeerFlow (研究) → UBrain (决策) → AccioWork (执行) 全链路 支持效果回流机制 |
| `api/v1/super_admin/geo_engine.py` | 1037 | GEO 引擎 API — 各大模型关键词收录查询 |
| `api/v1/orders.py` | 985 | Orders API Router - 订单API 鉴权模型（order-token + 登录态双因子）： - 买家（匿名）：凭订单访问令牌（X-Order-Token 头 / order_token |
| `api/v1/routes/egress.py` | 895 | 静态 IP 槽位与浏览器指纹 API |
| `api/v1/content.py` | 886 | -*- coding: utf-8 -*- |
| `api/v1/routes/foreign_trade.py` | 882 | 外贸 B2B 工具·技能·生态 API — 随源码部署。 |
| `api/v1/routes/products.py` | 840 | 产品管理路由 - 优化版 - 添加缓存和优化查询 |
| `api/v1/routes/cross_border.py` | 828 | 跨境语言桥 API — W1 中文片出海 / W2 询盘桥 / W3 报价+SEO。 |
| `api/v1/routes/inquiries.py` | 714 | 询盘管理路由 - 模块化架构 |
| `api/v1/routes/lead_generation.py` | 684 | 零成本获客 API —— 完全免费的客户开发能力 链路：Google CSE 搜索 → 抓取网站邮箱 → SMTP/MX 验证 → 返回结果 成本：$0（Google CSE 免费 100 次/天 + |
| `api/v1/routes/paperclip.py` | 671 | Paperclip Agent 编排 API — 公司 / Agent / 目标 / 任务 / 心跳 / 预算 / 审批 |
| `api/v1/routes/auth.py` | 653 | 认证模块路由 |
| `api/v1/routes/analytics.py` | 646 | 数据分析路由 - 流量埋点与运营看板 |
| `api/v1/routes/payment.py` | 645 | 支付路由 - 支付订单创建、查询、回调、套餐查询 |
| `api/v1/products.py` | 637 | -*- coding: utf-8 -*- |
| `api/v1/routes/finance.py` | 600 | 财务中台 MVP — 营收/成本流水 |
| `api/v1/routes/client.py` | 592 | SaaS 客户管理后台 - 仪表盘与品牌接口 |
| `api/v1/super_admin/ai_config.py` | 588 | AI 模型配置管理接口 |
| `api/v1/routes/content.py` | 586 | 内容管理路由 - 优化版 - 添加缓存和分页验证 |
| `api/v1/ab_test.py` | 584 | -*- coding: utf-8 -*- |
| `api/v1/routes/video_publish.py` | 578 | 统一视频发布 API — Hermes 编排，一个入口，真发到各视频平台。 |
| `api/v1/routes/ubrain.py` | 577 | UBrain 统一助手 API。 |
| `api/v1/evolution.py` | 545 | AI 进化引擎 API 路由。 提供进化闭环的管理接口：数据收集、经验沉淀、版本管理、灰度发布、审批流程。 |
| `api/v1/routes/content_master.py` | 534 | 统一发布母版 API |
| `api/v1/routes/platform.py` | 532 | 多平台分发 API 路由 - 平台账号管理、内容分发、会话保持 |
| `api/v1/routes/crm_pipeline.py` | 528 | CRM 销售管线路由 — 商机（Opportunity）管理 端点： - GET /api/v1/opportunities 商机列表（分页/筛选/排序） - POST /api/v1/opportu |
| `api/v1/routes/negotiation.py` | 519 | 自动谈单 - 谈判/报价审批与智能议价引擎。 重构升级： 1. 【多租户隔离】彻底淘汰全局可变字典，按 tenant_id 隔离配置、报价、审批状态与消息流。 2. 【黑客防注入】集成 Prompt  |
| `api/v1/routes/license.py` | 509 | License Management API - 许可证管理接口（P1-5 扩展：设备指纹 + 授权码 + 套餐订单） |
| `api/v1/routes/rfq.py` | 509 | RFQ 需求单路由 — 买家结构化的询价请求（公开提交 + 管理端管理）。 端点： - POST /api/v1/rfq 公开提交 RFQ（无需登录） - GET /api/v1/rfq 管理端列表  |
| `api/v1/compliance.py` | 500 | -*- coding: utf-8 -*- |
| `api/v1/seo/dashboard.py` | 488 | -*- coding: utf-8 -*- |
| `api/v1/deerflow.py` | 485 | DeerFlow 执行引擎 API 路由。 提供任务管理、状态转移、人工审核的 REST 接口。 |
| `api/v1/seo/eeat.py` | 482 | -*- coding: utf-8 -*- |
| `api/v1/routes/growth_tools.py` | 475 | 三大增长内置工具 API。 |
| `api/v1/routes/ubrain_commercial_os.py` | 467 | 商业 OS 飞轮 API — Mem0/n8n/PostHog 外挂槽位。 |
| `api/v1/routes/files.py` | 462 | 文件管理路由 - 上传、列表、删除（国内七牛 / 海外 R2 分轨） |

## tasks Celery · 13 文件

| 文件 | 行 | 说明 |
|------|---:|------|
| `tasks/ops_scheduler_tasks.py` | 436 | -*- coding: utf-8 -*- |
| `tasks/deerflow_tasks.py` | 206 | DeerFlow 执行引擎 Celery 任务。 提供 DeerFlow 任务的异步执行能力，与状态机协作完成完整的任务生命周期。 |
| `tasks/seo_tasks.py` | 200 | -*- coding: utf-8 -*- |
| `tasks/scheduled_publish_worker.py` | 125 | 定时发布调度器 — 借鉴 AiToEarn enqueue-publishing-task scheduler。 定期扫描 scheduled_publishes 表中 pending 状态且到达发布 |
| `tasks/publish_tasks.py` | 122 | Publish task definitions and enqueue functions. |
| `tasks/geo_tasks.py` | 112 | GEO Celery 任务 — 技术雷达 / Rank Guard / 竞品监控。 |
| `tasks/celery_app.py` | 103 | -*- coding: utf-8 -*- |
| `tasks/ubrain_tasks.py` | 98 | UBrain / DeerFlow Celery 任务。 |
| `tasks/cross_border_tasks.py` | 51 | 跨境语言桥 Celery 任务。 |
| `tasks/orchestration_tasks.py` | 38 | 编排任务消费（ai_tasks → Hermes 桥的 Celery 入口）。 由统一编排摄入路由 POST /orchestration/tasks 派发：create_task → process |
| `tasks/trade_intel_tasks.py` | 35 | Celery — 出海参谋海关数据定时刷新。 |
| `tasks/billing_tasks.py` | 32 | 轮22：计量周期汇总任务（总纲 §4.6-8：Celery beat 汇总进现有计费）。 仅将 meter_events 中未汇总事件并入既有计费账本（token_ledger / finance_l |
| `tasks/__init__.py` | 3 | -*- coding: utf-8 -*- |

## schemas · 24 文件

| 文件 | 行 | 说明 |
|------|---:|------|
| `schemas/tenant.py` | 261 | SaaS多租户Schema |
| `schemas/schema_markup_enhanced.py` | 228 | -*- coding: utf-8 -*- |
| `schemas/ab_test.py` | 220 | -*- coding: utf-8 -*- |
| `schemas/product.py` | 186 | -*- coding: utf-8 -*- |
| `schemas/im_routing_and_specs.py` | 185 | 商家IM路由配置和建材垂直参数的Pydantic Schemas 用于FastAPI请求/响应验证和序列化 |
| `schemas/globalization.py` | 154 | 全球化多语言 Schema |
| `schemas/__init__.py` | 144 | -*- coding: utf-8 -*- |
| `schemas/rfq.py` | 141 | RFQ 请求 / 响应 Pydantic 模型 — 买家需求单（B2B 询价）。 |
| `schemas/content.py` | 117 | -*- coding: utf-8 -*- |
| `schemas/ai_config.py` | 116 | -*- coding: utf-8 -*- |
| `schemas/compliance.py` | 112 | -*- coding: utf-8 -*- |
| `schemas/seo.py` | 102 | -*- coding: utf-8 -*- |
| `schemas/news.py` | 93 | -*- coding: utf-8 -*- |
| `schemas/international.py` | 91 | 国际询盘采集系统 Schema |
| `schemas/case_study.py` | 88 | -*- coding: utf-8 -*- |
| `schemas/auth.py` | 75 | -*- coding: utf-8 -*- |
| `schemas/user.py` | 74 | -*- coding: utf-8 -*- |
| `schemas/schema_markup.py` | 67 | -*- coding: utf-8 -*- |
| `schemas/hermes_orchestration.py` | 63 | Hermes TaskGraph and Intent Orchestration Schemas (Plan-as-Data). |
| `schemas/geo_schemas.py` | 53 | GEO Schemas - Pydantic models for GEO engine This module defines the Pydantic models used by the GEO |
| `schemas/referral.py` | 53 | 客户裂变推荐系统 Schema |
| `schemas/publish_task.py` | 50 | Pydantic schemas for PublishTask. |
| `schemas/ssl_certificate.py` | 48 | Pydantic schemas for SSLCertificate. |
| `schemas/inquiry.py` | 43 | -*- coding: utf-8 -*- |

## domains · 14 文件

| 文件 | 行 | 说明 |
|------|---:|------|
| `domains/lead/routes.py` | 345 | 获客引擎领域 API 路由 — FIX-31 统一管理所有获客相关端点： - 线索搜索、验证、抓取、发送 - 线索管理 CRUD - 邮件外展任务管理 - 异步搜索进度查询 |
| `domains/base.py` | 71 | 领域模块基类 — FIX-31: 模块单体架构 每个领域模块继承此基类，提供统一的接口： - name: 领域名称 - router: 领域 API 路由（自动注册） - register_model |
| `domains/__init__.py` | 59 | 领域模块注册中心 — FIX-31: 模块单体架构 架构原则： - 每个领域（domain）是自包含的模块，拥有自己的 models、routes、services、schemas - 领域间通过明确 |
| `domains/lead/__init__.py` | 42 | 获客引擎领域 — FIX-31: 首个完整领域模块迁移 包揽所有获客相关功能： - 零成本邮箱验证（MX + SMTP） - 网站邮箱抓取 - 邮件发送（Resend + SMTP） - 线索管理（P |
| `domains/ai/__init__.py` | 22 | AI智能领域 — stub（待从 routes/ai_*.py 迁移） |
| `domains/auth/__init__.py` | 22 | 认证授权领域 — stub（待从 routes/auth.py 迁移） |
| `domains/content/__init__.py` | 22 | 内容管理领域 — stub（待从 routes/content.py 迁移） |
| `domains/inquiry/__init__.py` | 22 | 询盘管理领域 — stub（待从 routes/inquiries.py 迁移） |
| `domains/payment/__init__.py` | 22 | 支付财务领域 — stub（待从 routes/payment.py, finance.py 迁移） |
| `domains/product/__init__.py` | 22 | 产品管理领域 — stub（待从 routes/products.py 迁移） |
| `domains/public/__init__.py` | 22 | 公开API领域 — stub（待从 routes/public_*.py 迁移） |
| `domains/seo/__init__.py` | 22 | SEO优化领域 — stub（待从 routes/seo_*.py 迁移） |
| `domains/system/__init__.py` | 22 | 系统管理领域 — stub（待从 routes/system.py, settings.py 迁移） |
| `domains/tenant/__init__.py` | 22 | 租户管理领域 — stub（待从 routes/tenants.py 迁移） |
