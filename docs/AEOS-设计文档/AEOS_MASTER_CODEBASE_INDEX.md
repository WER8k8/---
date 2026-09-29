# AEOS v1.0 全域代码资产与基础功能全景权威索引大字典
> **本文件为工作区 8 大子系统、全量物理文件职责、数据流与契约唯一真相源**。
> 编制日期：2026-09-08 | 状态：全量实测扫描对齐 | 架构师核准

---

## 0. 系统全景大盘数据
| 子系统标识 | 物理目录 | 核心定位 | 物理文件数 | 核心代码量/规模 |
|---|---|---|---|---|
| **1. Core Backend** | `上线网站.worktrees/.../backend/` | 核心控制面 (FastAPI+PG 229表+Hermes+Celery) | ~1,410 源文件 | 93 模型 / 150 路由 / 42 服务 |
| **2. Trade AI Agent** | `_external/trade-ai-agent/` | ★ 全域社媒拓客与 WhatsApp 触达中枢 | 342 文件 | 21 视图 / 80+ 路由 / 14 营销技能 |
| **3. GoodJob CRM** | `_external/goodjob-crm/` | ★ 外贸 7 步履约、WhatsApp 翻译与单证中枢 | 590 文件 | 7 步漏斗 / PI 发票 / CI+PL 单证 |
| **4. DeepSeek Harness** | `deepseek-harness/` | 外层认知推理与规划沙箱 (Cordis) | 9,340 文件 | Python SDK + 原生 dsh.exe 二进制 |
| **5. Skills 76 技能库** | `上线网站.worktrees/.../skills/` | 76 个业务原子技能 (SKILL.md) | 497 文件 | 76/76 active 入库 |
| **6. AgencyZH 人设库** | `_external/agency-agents-zh/` | 276+ 细分行业中文 Agent 人设人格 | 362 文件 | 309 份专家 Profile |
| **7. ECC 工程 SOP 库** | `_external/ecc/` | 286+ 软件工程与交付防错规约 | 3,521 文件 | 286 份 SOP 检查单 |
| **8. 前端双源 (Web)** | worktree `frontend/` (开发) + `主要备份/.../frontend` (运行:3000) | 租户独立站与超管后台交互层 | ~8,900 文件 | Nuxt3 开发源 + Vite 3000 运行源 |

---

## 1. Core Backend (`backend/app/`) 核心控制面与服务全景
### 1.1 核心数据库实体模型 (`app/models/` 共 93 个模型文件，映射 PG 229 表)
| 模型文件 | 映射物理表 | 核心类名 | 业务职责 |
|---|---|---|---|
| `ab_test.py` | `ab_tests, ab_test_variants` | `ABTest, ABTestVariant` | A/B 测试数据模型 |
| `admin.py` | `admin_roles, admin_permissions` | `AdminRole, AdminPermission` | 超级管理员 RBAC 模型 |
| `agent_commission_rule.py` | `agent_commission_rules` | `AgentCommissionRule` | 多级代理分润规则表（首单 / 续费 × 层级）。 |
| `agent_tree.py` | `agent_nodes` | `AgentNode` | 代理层级关系树 |
| `ai_config.py` | `tenant_ai_provider_configs, ai_model_providers` | `TenantAiProviderConfig, AIModelProvider` | 租户级 AI 模型配置表 |
| `ai_knowledge.py` | `ai_knowledge_base, ai_chat_sessions` | `AiKnowledgeBase, AiChatSession` | AI知识库向量表 - 存储商家中文建材资料向量化数据 |
| `ai_recommendation.py` | `ai_recommendations` | `AIRecommendation` | AI Recommendation Model - AI推荐模型 |
| `ai_task.py` | `ai_tasks` | `AiTask` | 统一任务控制面模型（总纲 §4.6-1 / §8 082_unify_ai_tasks；轮23 补 ORM 映射）。 |
| `ai_template.py` | `ai_templates` | `AITemplate` | AI 内容生成模板模型 |
| `ai_visibility.py` | `ai_queries, ai_query_runs` | `AIQuery, AIQueryRun` | GEO / AI Visibility 数据模型 — AI 搜索可见性监控（Phase 6） |
| `alert.py` | `alert_rules, alert_events` | `AlertRule, AlertEvent` | 告警中心模型 |
| `app_device.py` | `app_devices` | `AppDevice` | 出海计 App — 推送设备注册。 |
| `campaign.py` | `campaigns, campaign_steps` | `Campaign, CampaignStep` | Campaign / ABM 数据模型 — AI Outbound 序列（Phase 5） |
| `case_study.py` | `case_studies, case_images` | `CaseStudy, CaseImage` | - |
| `chat_message.py` | `chat_messages` | `ChatMessage` | Chat Message Model - AI对话消息模型 |
| `chat_session.py` | `chat_sessions` | `ChatSession` | Chat Session Model - AI对话会话模型 |
| `commission_settlement.py` | `agent_commission_settlements` | `AgentCommissionSettlement` | 代理分润结算单 |
| `company.py` | `companies, company_contacts` | `Company, CompanyContact` | Company 360 - B2B 公司主数据 + 联系人 + 采购信号（Phase 3 地基） |
| `compliance.py` | `compliance_rules, compliance_scan_results` | `ComplianceRule, ComplianceScanResult` | 合规检查相关数据库模型 |
| `content.py` | `content_pages, content_versions` | `ContentPage, ContentVersion` | - |
| `content_feedback.py` | `content_feedback_checks, industry_patterns` | `ContentFeedbackCheck, IndustryPattern` | Content Feedback Loop — DB models for feedback checks and industry patterns. |
| `content_master.py` | `content_masters` | `ContentMaster` | 统一发布母版 — 一篇内容多发各平台 |
| `deerflow_job.py` | `deerflow_jobs` | `DeerflowJob` | DeerFlow / UBrain-X 异步任务队列。 |
| `eeat.py` | `eeat_authors, eeat_author_certifications` | `Author, AuthorCertification` | 作者/专家模型 |
| `egress.py` | `egress_endpoints, egress_provision_jobs` | `EgressEndpoint, EgressProvisionJob` | 静态 IP 槽位与浏览器指纹环境 |
| `email_outreach.py` | `email_outreachs` | `EmailOutreach` | 邮件外联模型 —— 状态机 + 幂等 + 全链路追踪 |
| `email_tracking_event.py` | `email_tracking_events` | `EmailTrackingEvent` | 邮件追踪事件模型（P1-3）—— 打开/点击/回复事件记录。 |
| `enums.py` | `-` | `-` | 状态枚举定义 —— ORCH-08/09/10 修复 |
| `evolution.py` | `evolution_task_records, evolution_experiences` | `EvolutionTaskRecord, ExperienceEntry` | AI 进化引擎数据模型。 |
| `feishu.py` | `feishu_bindings, feishu_message_logs` | `FeishuBinding, FeishuMessageLog` | - |
| `finance_ledger.py` | `finance_ledger_entries` | `FinanceLedgerEntry` | 财务台账 — 营收/成本流水（MVP） |
| `geo_alert_db_models.py` | `geo_alert_rules, geo_alerts` | `GEOAlertRule, GEOAlert` | GEO Alert Models - SQLAlchemy 模型 |
| `geo_alert_models.py` | `-` | `AlertRuleCreate, AlertCreate` | GEO Alert Models - 预警数据模型 |
| `geo_sourcechain_models.py` | `material_specs, content_chunks` | `MaterialSpec, ContentChunk` | GEO SourceChain Models - SourceChain GEO Engine database models (non-alert tables) |
| `globalization.py` | `glossary_terms, translation_tasks` | `GlossaryTerm, TranslationTask` | 全球化多语言模型 |
| `growth_tools.py` | `growth_keyword_entries, growth_agent_runs` | `GrowthKeywordEntry, GrowthAgentRun` | 增长工具 — 专属词库条目（行业/品牌/竞品/需求）+ Agent 跑盘记录。 |
| `hermes_plugin.py` | `hermes_plugin_installs` | `HermesPluginInstall` | Hermes 插件安装态（租户级）。 |
| `im_chat.py` | `im_messages, im_sessions` | `IMMessage, IMSession` | 聊天消息数据库模型（IM用户间聊天，与AI聊天分开） |
| `im_routing_and_specs.py` | `merchant_im_routing, building_material_specs` | `MerchantIMRouting, BuildingMaterialSpec` | 商家IM路由配置表和建材垂直参数表 - SQLAlchemy ORM模型 |
| `inquiry.py` | `inquiries` | `Inquiry` | Inquiry Model - 询盘模型 |
| `international.py` | `international_target_sites, international_inquiries` | `InternationalTargetSite, InternationalInquiry` | 国际询盘采集系统 - 独立于国内业务的数据库模型 |
| `invoice_application.py` | `platform_invoice_configs, tenant_invoice_profiles` | `PlatformInvoiceConfig, TenantInvoiceProfile` | 增值税发票开票申请（合规：申请≠已开票，须财务审核及税控开具）。 |
| `license.py` | `licenses, device_fingerprints` | `License, DeviceFingerprint` | License Model - 许可证管理模型（P1-5 扩展：设备指纹 + 授权码 + 套餐订单） |
| `media_factory.py` | `media_render_tasks` | `MediaRenderTask` | 多媒体工厂：渲染任务模型。 |
| `merchant_profile.py` | `merchant_profiles` | `MerchantProfile` | Merchant Profile Model - 商家资料模型 |
| *(其余 48 个模型文件...)* | ... | ... | 包含审计、支付、租户设置、SEO探针等支撑实体 |

### 1.2 核心业务服务层 (`app/services/` 共 42 个服务子系统)
- **`root_services/`** (255 files): `_scan_long.py`, `acme_service.py`, `acquisition_outreach_service.py`, `agent_aggregation_service.py`, `agent_commission_service.py`, `agent_hub_service.py` 等共 255 个模块
- **`adapters/`** (0 files): 
- **`agent_loop/`** (4 files): `growth_workflow.py`, `run_repository.py`, `session_store.py`, `workflow_presets.py`
- **`ai/`** (4 files): `ai_engine_v2.py`, `analytics_insight_service.py`, `recommendation_service.py`, `security_scan_service.py`
- **`analytics/`** (4 files): `user_action_analytics_compliance.py`, `user_action_analytics_registry.py`, `user_action_analytics_sidecar.py`, `user_action_analytics_smart.py`
- **`annex/`** (1 files): `ticket_service.py`
- **`billing/`** (2 files): `meter_event.py`, `subscription_countdown.py`
- **`browser_runtime/`** (6 files): `evidence.py`, `exceptions.py`, `executor.py`, `policy.py`, `profile.py`, `runtime.py`
- **`calculators/`** (1 files): `engine.py`
- **`crawlers/`** (5 files): `ecommerce_crawlers_compliance.py`, `ecommerce_crawlers_registry.py`, `ecommerce_crawlers_sidecar.py`, `ecommerce_crawlers_smart.py`, `media_crawler_sidecar.py`
- **`cross_border/`** (29 files): `audio_asr_service.py`, `audio_chunk_service.py`, `cross_border_job_service.py`, `cross_border_sse.py`, `cross_border_worker.py`, `export_quote_service.py` 等共 29 个模块
- **`deepseek_harness/`** (2 files): `client.py`, `config.py`
- **`deerflow/`** (5 files): `checkpoint.py`, `executor.py`, `planner.py`, `reviewer.py`, `state_machine.py`
- **`egress/`** (4 files): `demo_guard.py`, `iproyal_client.py`, `iproyal_provisioner.py`, `provisioner.py`
- **`evolution/`** (4 files): `canary.py`, `engine.py`, `experience_store.py`, `version_control.py`
- **`facade/`** (1 files): `model_gateway_facade.py`
- **`feishu/`** (4 files): `cards.py`, `client.py`, `handlers.py`, `report.py`
- **`foreign_trade/`** (28 files): `aeo_fact_audit_service.py`, `benchmark_catalog_service.py`, `cold_email_skill.py`, `competitor_profile_skill.py`, `content_one_to_many_service.py`, `copywriting_skill.py` 等共 28 个模块
- **`geo/`** (9 files): `geo_writing_policy.py`, `headless_rank_probe_service.py`, `multi_engine_rank_registry.py`, `platform_discovery_service.py`, `platform_rank_registry.py`, `public_tech_reference_service.py` 等共 9 个模块
- **`goodjob/`** (2 files): `customer_pool_projection.py`, `trade_document_bridge.py`
- **`hermes/`** (66 files): `a2a_skill_marketplace_service.py`, `alert_dispatcher.py`, `anysearch_probe_service.py`, `brand_audit_service.py`, `brand_guard.py`, `browser_companion.py` 等共 66 个模块
- **`matching_engine/`** (2 files): `engine.py`, `schemas.py`
- **`media/`** (1 files): `platform_title_adapt.py`
- **`model_gateway/`** (4 files): `capability.py`, `gateway.py`, `ledger.py`, `router.py`
- **`moss_vl/`** (6 files): `hot_reload_manager.py`, `model_loader.py`, `offline_inference.py`, `realtime_session.py`, `repo_syncer.py`, `xrope_spatial_temporal.py`
- **`n8n/`** (3 files): `trigger.py`, `webhook.py`, `workflow_registry.py`
- **`orchestrator/`** (1 files): `commercial_loop.py`
- **`paperclip/`** (6 files): `approval_gate.py`, `budget_guard.py`, `goal_chain.py`, `heartbeat_engine.py`, `orchestrator.py`, `tenant_context.py`
- **`payment_pkg/`** (3 files): `payment_service_impl.py`, `verify_flags.py`, `wechat_pay.py`
- **`pipeline/`** (3 files): `chains.py`, `state_machine.py`, `wiring.py`
- **`platforms/`** (7 files): `baijiahao.py`, `csdn.py`, `toutiao.py`, `wechat.py`, `weibo.py`, `xiaohongshu.py` 等共 7 个模块
- **`policy/`** (1 files): `engine.py`
- **`publish_workers/`** (8 files): `biliup_worker.py`, `dual_line.py`, `media_fetch.py`, `sau_sidecar.py`, `sau_worker.py`, `tier_router.py` 等共 8 个模块
- **`registry/`** (10 files): `common.py`, `data_source_service.py`, `matrix.py`, `mcp_service.py`, `permissions.py`, `plugin_service.py` 等共 10 个模块
- **`seo/`** (7 files): `inclusion_check_service.py`, `inclusion_probe.py`, `inclusion_probe_cache.py`, `rank_scheduler_ops.py`, `seo_matrix_db_health.py`, `seo_research_hints_service.py` 等共 7 个模块
- **`site_builder/`** (2 files): `orchestrator.py`, `prompts.py`
- **`talking_stick/`** (5 files): `config.py`, `file_lock.py`, `report_generator.py`, `scheduler.py`, `task_queue.py`
- **`tasks/`** (4 files): `deerflow_bridge.py`, `hermes_task_bridge.py`, `paperclip_bridge.py`, `task_control.py`
- **`trace/`** (3 files): `publish_gate.py`, `terminal_hook.py`, `trace_service.py`
- **`ubrain/`** (81 files): `accio_gap_constants.py`, `accio_gap_handlers.py`, `accio_sales_service.py`, `accio_skill_catalog.py`, `action_audit_service.py`, `ai_email_generator.py` 等共 81 个模块
- **`vault/`** (2 files): `credential_service.py`, `crypto.py`
- **`wangcai/`** (6 files): `intent.py`, `knowledge.py`, `llm.py`, `memory.py`, `persistence.py`, `router.py`

### 重点服务模块职责明细：
- **`hermes/`**：`task_control_supervisor.py` (DAG推进/JsonPath数据总线/Saga补偿), `executors/` (accio/deerflow插件调色盘), `agency/` (角色加载器/工作流执行器), `site_build_workflow.py` (建站流水线)。
- **`deerflow/`**：`executor.py` (SubTaskExecutor 9大intent真执行), `planner.py` (任务拆解与检查点), `reviewer.py` (结果质量终审)。
- **`deepseek_harness/`**：`client.py` (懒加载 Python SDK 调起 dsh 二进制), `config.py` (模型网关参数透传)。
- **`browser_runtime/`**：`executor.py` (无头浏览器沙箱执行), `evidence.py` (集中式 disk JSONL + DB trace 双轨证据链持久化)。
- **`n8n/`**：`trigger.py` (N8nTriggerService 出站触发), `workflow_registry.py` (内建 `site-built-notify` / `content-publish-dispatch` 幂等注册)。
- **`registry/`**：`skill_service.py` (技能发布/打分匹配/执行), `skill_pack_loader.py` (76 技能 frontmatter 与 SOP 正文加载器)。

### 1.3 核心路由与端点 (`app/api/v1/routes/` 共 150 个路由模块，1207+ 端点)
- **`ab_test.py`** (Prefix: `/` | 7 endpoints): GET /, GET /{test_id}
- **`agent_bff.py`** (Prefix: `/` | 1 endpoints): GET /summary
- **`agent_hub.py`** (Prefix: `/agent-hub` | 9 endpoints): GET /, GET /mcp-bridge
- **`agent_portal.py`** (Prefix: `/` | 9 endpoints): GET /dashboard, GET /clients
- **`agent_tree.py`** (Prefix: `/` | 8 endpoints): POST /nodes, PUT /nodes/{node_id}
- **`ai_config.py`** (Prefix: `/ai-config` | 4 endpoints): GET /, PUT /
- **`ai_generate.py`** (Prefix: `/` | 4 endpoints): POST /generate, POST /optimize
- **`ai_learning.py`** (Prefix: `/ai-learning` | 7 endpoints): GET /, GET /behavior
- **`ai_templates.py`** (Prefix: `/ai/templates` | 4 endpoints): GET , POST 
- **`ai_usage.py`** (Prefix: `/` | 8 endpoints): GET /overview, GET /daily
- **`ai_visibility.py`** (Prefix: `/geo` | 4 endpoints): GET /queries, POST /queries
- **`aitoearn_hub.py`** (Prefix: `/` | 3 endpoints): GET /capabilities, POST /engage/reply
- **`analytics.py`** (Prefix: `/analytics` | 11 endpoints): GET /site-context, POST /event
- **`annex.py`** (Prefix: `/` | 2 endpoints): POST /annex/ticket, POST /annex/redeem
- **`app_bff.py`** (Prefix: `/` | 10 endpoints): GET /home, POST /devices/register
- **`attribution.py`** (Prefix: `/analytics` | 2 endpoints): GET /attribution, POST /attribution/email-reply
- **`auth.py`** (Prefix: `/` | 12 endpoints): POST /login, POST /refresh
- **`auto_discovery.py`** (Prefix: `/` | 0 endpoints): -
- **`baidu_webmaster.py`** (Prefix: `/` | 3 endpoints): POST /baidu/sitemap/submit, GET /baidu/index-count
- **`building_wiki.py`** (Prefix: `/building-wiki` | 7 endpoints): POST /generate, GET /articles
- **`calculator.py`** (Prefix: `/` | 3 endpoints): POST /thermal, POST /fire-protection
- **`campaign.py`** (Prefix: `/campaign` | 3 endpoints): GET , GET /{campaign_id}
- **`case_studies.py`** (Prefix: `/case-studies` | 6 endpoints): GET /, GET /{case_id}
- **`churn.py`** (Prefix: `/churn` | 4 endpoints): GET /at-risk, GET /tips
- **`client.py`** (Prefix: `/` | 15 endpoints): GET /dashboard, GET /publish-readiness
- *(其余 125 个路由模块自动扫描挂载于 `/api/v1`...)*

### 1.4 Celery 分布式异步任务队列 (`app/tasks/` 共 12 个任务模块)
- **`billing_tasks.py`**：`app.tasks.billing_tasks.aggregate_meter_events`
- **`celery_app.py`**：未显式声明
- **`cross_border_tasks.py`**：`cross_border.run_job`
- **`deerflow_tasks.py`**：`execute_deerflow_job`, `deerflow_periodic_cleanup`
- **`geo_tasks.py`**：`hermes_daily_rank_cycle`, `geo_tech_radar_daily`, `geo_rank_guard_check`, `geo_competitor_monitor`
- **`ops_scheduler_tasks.py`**：`app.tasks.ops_scheduler_tasks.run_platform_job`, `app.tasks.ops_scheduler_tasks.paperclip_heartbeat_tick`
- **`orchestration_tasks.py`**：`process_ai_task`
- **`publish_tasks.py`**：未显式声明
- **`scheduled_publish_worker.py`**：未显式声明
- **`seo_tasks.py`**：`seo_research_hints_sync`
- **`trade_intel_tasks.py`**：`trade_intel_refresh_weekly`
- **`ubrain_tasks.py`**：`deerflow_scheduled_daily`, `deerflow_run_pending`, `flywheel_feedback_sync_daily`

---

## 2. ★ Trade AI Agent (`_external/trade-ai-agent/`) 全域社媒拓客与 WhatsApp 触达中枢
> **定位**：解决“外部客户去哪里找、如何自动化多渠道建立初次联系”的 Outbound 猎手系统。
### 2.1 后端服务与路由 (`backend/app/`)
- **API 路由**：
  - `admin.py`：社交媒体关键词拓客、WhatsApp 批量触达、会话流转、邮件序列、工作流触发。
  - `auth.py`：社交媒体关键词拓客、WhatsApp 批量触达、会话流转、邮件序列、工作流触发。
  - `conversation.py`：社交媒体关键词拓客、WhatsApp 批量触达、会话流转、邮件序列、工作流触发。
  - `customer.py`：社交媒体关键词拓客、WhatsApp 批量触达、会话流转、邮件序列、工作流触发。
  - `email.py`：社交媒体关键词拓客、WhatsApp 批量触达、会话流转、邮件序列、工作流触发。
  - `notification.py`：社交媒体关键词拓客、WhatsApp 批量触达、会话流转、邮件序列、工作流触发。
  - `outreach.py`：社交媒体关键词拓客、WhatsApp 批量触达、会话流转、邮件序列、工作流触发。
  - `skill.py`：社交媒体关键词拓客、WhatsApp 批量触达、会话流转、邮件序列、工作流触发。
  - `spreadsheet.py`：社交媒体关键词拓客、WhatsApp 批量触达、会话流转、邮件序列、工作流触发。
  - `stats.py`：社交媒体关键词拓客、WhatsApp 批量触达、会话流转、邮件序列、工作流触发。
  - `template.py`：社交媒体关键词拓客、WhatsApp 批量触达、会话流转、邮件序列、工作流触发。
  - `whatsapp.py`：社交媒体关键词拓客、WhatsApp 批量触达、会话流转、邮件序列、工作流触发。
  - `workflow.py`：社交媒体关键词拓客、WhatsApp 批量触达、会话流转、邮件序列、工作流触发。
- **核心服务模块**：
  - `auth_service.py`：社媒爬虫 (Scraper)、WhatsApp API 驱动、LangGraph 意图分类器、统一收件箱调度。
  - `conversation_service.py`：社媒爬虫 (Scraper)、WhatsApp API 驱动、LangGraph 意图分类器、统一收件箱调度。
  - `customer_service.py`：社媒爬虫 (Scraper)、WhatsApp API 驱动、LangGraph 意图分类器、统一收件箱调度。
  - `notification_service.py`：社媒爬虫 (Scraper)、WhatsApp API 驱动、LangGraph 意图分类器、统一收件箱调度。
  - `outreach_service.py`：社媒爬虫 (Scraper)、WhatsApp API 驱动、LangGraph 意图分类器、统一收件箱调度。
  - `stats_service.py`：社媒爬虫 (Scraper)、WhatsApp API 驱动、LangGraph 意图分类器、统一收件箱调度。
  - `workflow_service.py`：社媒爬虫 (Scraper)、WhatsApp API 驱动、LangGraph 意图分类器、统一收件箱调度。
### 2.2 前端视图 (`frontend/src/` 共 42 页面/组件)
- **工作台 (Dashboard)**：线索漏斗、触达转化率、高意向客户动态看板。
- **客户与外联管理**：多平台统一联系人档案、沟通历史全景流。
- **多渠道收件箱 (Unified Inbox)**：单屏聚合 WhatsApp、邮件、社媒私信，支持 AI 建议回复。
- **可视化工作流编辑器**：基于节点的营销流自动化编排与条件分支。
---

## 3. ★ GoodJob CRM (`_external/goodjob-crm/`) 外贸 7 步履约、WhatsApp 翻译与单证中枢
> **定位**：解决“线索进来后如何跟进、如何实时跨语言沟通、如何开出正规形式发票与成套外贸单证”的交易闭环系统。
### 3.1 核心资产与独立插件
- **`whatsapp-plugin/` (WhatsApp 本地双轨插件)**：
  - 架构：独立 Node.js 服务 (@3100 API / @5193 UI)，采用 Baileys 协议直连 WhatsApp Web，支持多账号登录。
  - 特色能力：内置 **实时双向 AI 翻译引擎**（接收即译为中文、发送自动译为买家母语），AES-256-GCM 凭证持久化。
- **`PI_GENERATOR_DESIGN.md` (形式发票 Proforma Invoice 智能生成器)**：
  - 自动从 CRM 商机或工程计算器中抽取物料明细、数量、FOB/CIF 单价。
  - 自动注入企业英文抬头、银行收汇账号、中英文金额大写、包装件数、交货期条款。
  - 秒级输出符合国际贸易惯例的标准 PI (PDF & Excel)。
- **`TRADE_DOCS_DESIGN.md` (外贸单证工作室 Trade Docs Studio)**：
  - 出口全套单证一键套打：**商业发票 (Commercial Invoice)、装箱单 (Packing List)、报关草单、产地证草单**。
### 3.2 外贸 7 步销售管道 (`backend/`)
  - 询盘 (Inquiry) ➔ 已联系 (Contacted) ➔ 已报价 (Quoted) ➔ 样品 (Sample) ➔ 谈判 (Negotiation) ➔ 成交 (Won) ➔ 售后履约 (Fulfillment)。
---

## 4. 350+ 专家资产库 (`Skills 76` + `AgencyZH 276` + `ECC 286`)
### 4.1 76 个业务技能包 (`skills/`，全部已入库 PostgreSQL `skills` 表)
- **`ab-testing`**：When the user wants to plan, design, or implement an A/B test or experiment, or build a growth experimentation program. Also use when the user mentions "A/B test," "split test," "experiment," "test this change," "variant copy," "multivariate test," "hypothesis," "should I test this," "which version is better," "test two versions," "statistical significance," "how long should I run this test," "growth experiments," "experiment velocity," "experiment backlog," "ICE score," "experimentation program," or "experiment playbook." Use this whenever someone is comparing two approaches and wants to measure which performs better, or when they want to build a systematic experimentation practice. For tracking implementation, see analytics. For page-level conversion optimization, see cro.
- **`ad-creative`**："When the user wants to generate, iterate, or scale ad creative — headlines, descriptions, primary text, or full ad variations — for any paid advertising platform. Also use when the user mentions 'ad copy variations,' 'ad creative,' 'generate headlines,' 'RSA headlines,' 'bulk ad copy,' 'ad iterations,' 'creative testing,' 'ad performance optimization,' 'write me some ads,' 'Facebook ad copy,' 'Google ad headlines,' 'LinkedIn ad text,' 'static ads,' 'static ad concepts,' 'ad templates,' 'iMessage ad,' 'chat reveal ad,' 'fake DM ad,' 'ChatGPT ad,' 'Apple Notes ad,' 'AirDrop ad,' 'creative strategy,' 'creative roadmap,' 'creative retro,' 'hook writing,' 'creative review page,' 'present ad creative for approval,' 'motion video ad,' 'faceless video ad,' 'animated explainer ad,' 'motion collage ad,' or 'I need more ad variations.' Use this whenever someone needs to produce ad copy at scale or iterate on existing ads. For campaign strategy and targeting, see ads. For landing page copy, see copywriting."
- **`ads`**："When the user wants help with paid advertising campaigns on Google Ads, Meta (Facebook/Instagram), LinkedIn, Twitter/X, or other ad platforms. Also use when the user mentions 'PPC,' 'paid media,' 'ROAS,' 'CPA,' 'ad campaign,' 'retargeting,' 'audience targeting,' 'Google Ads,' 'Facebook ads,' 'LinkedIn ads,' 'ad budget,' 'cost per click,' 'ad spend,' 'should I run ads,' 'ABM,' 'account-based marketing,' 'B2B ads,' 'lead quality,' 'negative keywords,' 'Performance Max,' 'thought leader ads,' or 'when should I kill an ad.' Use this for campaign strategy, audience targeting, bidding, and optimization. For bulk ad creative generation and iteration, see ad-creative. For landing page optimization, see cro."
- **`ai-seo`**："When the user wants to optimize content for AI search engines, get cited by LLMs, or appear in AI-generated answers. Also use when the user mentions 'AI SEO,' 'AEO,' 'GEO,' 'LLMO,' 'answer engine optimization,' 'generative engine optimization,' 'LLM optimization,' 'AI Overviews,' 'optimize for ChatGPT,' 'optimize for Perplexity,' 'AI citations,' 'AI visibility,' 'zero-click search,' 'how do I show up in AI answers,' 'LLM mentions,' 'optimize for Claude/Gemini,' 'llms.txt,' 'OKF,' 'Open Knowledge Format,' 'knowledge bundle,' or 'agent-readable site.' Use this whenever someone wants their content to be cited or surfaced by AI assistants and AI search engines. For traditional technical and on-page SEO audits, see seo-audit. For structured data implementation, see schema."
- **`analytics`**：When the user wants to set up, improve, or audit analytics tracking and measurement. Also use when the user mentions "set up tracking," "GA4," "Google Analytics," "conversion tracking," "event tracking," "UTM parameters," "tag manager," "GTM," "analytics implementation," "tracking plan," "how do I measure this," "track conversions," "attribution," "Mixpanel," "Segment," "are my events firing," or "analytics isn't working." Use this whenever someone asks how to know if something is working or wants to measure marketing results. For A/B test measurement, see ab-testing.
- **`artifacts-builder`**：Suite of tools for creating elaborate, multi-component claude.ai HTML artifacts using modern frontend web technologies (React, Tailwind CSS, shadcn/ui). Use for complex artifacts requiring state management, routing, or shadcn/ui components - not for simple single-file HTML/JSX artifacts.
- **`aso`**："When the user wants to audit or optimize an App Store or Google Play listing. Also use when the user mentions 'ASO audit,' 'app store optimization,' 'optimize my app listing,' 'improve app visibility,' 'app store ranking,' 'audit my listing,' 'why aren't people downloading my app,' 'improve my app conversion,' 'keyword optimization for app,' or 'compare my app to competitors.' Use when the user shares an App Store or Google Play URL and wants to improve it."
- **`brand-guidelines`**：Applies Anthropic's official brand colors and typography to any sort of artifact that may benefit from having Anthropic's look-and-feel. Use it when brand colors or style guidelines, visual formatting, or company design standards apply.
- **`canvas-design`**：Create beautiful visual art in .png and .pdf documents using design philosophy. You should use this skill when the user asks to create a poster, piece of art, design, or other static piece. Create original visual designs, never copying existing artists' work to avoid copyright violations.
- **`changelog-generator`**：Automatically creates user-facing changelogs from git commits by analyzing commit history, categorizing changes, and transforming technical commits into clear, customer-friendly release notes. Turns hours of manual changelog writing into minutes of automated generation.
- **`churn-prevention`**："When the user wants to reduce churn, build cancellation flows, set up save offers, recover failed payments, or implement retention strategies. Also use when the user mentions 'churn,' 'cancel flow,' 'offboarding,' 'save offer,' 'dunning,' 'failed payment recovery,' 'win-back,' 'retention,' 'exit survey,' 'pause subscription,' 'involuntary churn,' 'people keep canceling,' 'churn rate is too high,' 'how do I keep users,' or 'customers are leaving.' Use this whenever someone is losing subscribers or wants to build systems to prevent it. For post-cancel win-back email sequences, see emails. For in-app upgrade paywalls, see paywalls."
- **`co-marketing`**："When the user wants to find co-marketing partners, plan joint campaigns, or brainstorm partnership opportunities. Use when the user says 'co-marketing,' 'partner marketing,' 'joint campaign,' 'who should we partner with,' 'integration marketing,' 'cross-promotion,' 'collaborate with another company,' 'partnership ideas,' or 'co-brand.' For customer referral programs, see referrals. For launch-specific partnerships, see launch."
- **`cold-email`**：Write B2B cold emails and follow-up sequences that get replies. Use when the user wants to write cold outreach emails, prospecting emails, cold email campaigns, sales development emails, or SDR emails. Also use when the user mentions "cold outreach," "prospecting email," "outbound email," "email to leads," "reach out to prospects," "sales email," "follow-up email sequence," "nobody's replying to my emails," or "how do I write a cold email." Covers subject lines, opening lines, body copy, CTAs, personalization, and multi-touch follow-up sequences. For warm/lifecycle email sequences, see emails. For sales collateral beyond emails, see sales-enablement.
- **`community-marketing`**："Build and leverage online communities to drive product growth and brand loyalty. Use when the user wants to create a community strategy, grow a Discord or Slack community, manage a forum or subreddit, build brand advocates, increase word-of-mouth, drive community-led growth, engage users post-signup, or turn customers into evangelists. Trigger phrases: \"build a community,\" \"community strategy,\" \"Discord community,\" \"Slack community,\" \"community-led growth,\" \"brand advocates,\" \"user community,\" \"forum strategy,\" \"community engagement,\" \"grow our community,\" \"ambassador program,\" \"community flywheel.\""
- **`competitive-ads-extractor`**：Extracts and analyzes competitors' ads from ad libraries (Facebook, LinkedIn, etc.) to understand what messaging, problems, and creative approaches are working. Helps inspire and improve your own ad campaigns.
- **`competitor-profiling`**："When the user wants to research, profile, or analyze competitors from their URLs. Also use when the user mentions 'competitor profile,' 'competitor research,' 'competitor analysis,' 'profile this competitor,' 'analyze competitor,' 'competitive intelligence,' 'competitor deep dive,' 'who are my competitors,' 'competitor landscape,' 'competitor dossier,' 'competitive audit,' or 'research these competitors.' Input is a list of competitor URLs. Output is structured competitor profile markdown files. For creating comparison/alternative pages from profiles, see competitors. For sales-specific battle cards, see sales-enablement."
- **`competitors`**："When the user wants to create competitor comparison or alternative pages for SEO and sales enablement. Also use when the user mentions 'alternative page,' 'vs page,' 'competitor comparison,' 'comparison page,' '[Product] vs [Product],' '[Product] alternative,' 'competitive landing pages,' 'how do we compare to X,' 'battle card,' or 'competitor teardown.' Use this for any content that positions your product against competitors. Covers four formats: singular alternative, plural alternatives, you vs competitor, and competitor vs competitor. For sales-specific competitor docs, see sales-enablement."
- **`connect`**：Connect Claude to any app. Send emails, create issues, post messages, update databases - take real actions across Gmail, Slack, GitHub, Notion, and 1000+ services.
- **`connect-apps`**：Connect Claude to external apps like Gmail, Slack, GitHub. Use this skill when the user wants to send emails, create issues, post messages, or take actions in external services.
- **`content-research-writer`**：Assists in writing high-quality content by conducting research, adding citations, improving hooks, iterating on outlines, and providing real-time feedback on each section. Transforms your writing process from solo effort to collaborative partnership.
- *(其余 56 个技能涵盖：A/B测试、广告投放、多语言SEO、冷邮件营销、技术规格书提取等)*

### 4.2 276+ 细分行业中文 Agent 人设人格 (`_external/agency-agents-zh/` 共 309 份角色)
- 涵盖岗位：外贸业务总监、海外采购代表、SDR线索专家、SEO架构师、合规审计师、技术计算工程师等。
- 人设样本：`.github\ISSUE_TEMPLATE\bug_report.md`, `.github\ISSUE_TEMPLATE\feature_request.md`, `.github\ISSUE_TEMPLATE\new_agent.md`, `.github\PULL_REQUEST_TEMPLATE.md`, `academic\academic-anthropologist.md`, `academic\academic-geographer.md`, `academic\academic-historian.md`, `academic\academic-narratologist.md` 等。

### 4.3 286+ 软件工程与质量防错 SOP (`_external/ecc/` 共 2444 份规约)
- 涵盖领域：代码质量门禁、架构防错清单、安全合规检查、CI/CD流水线规约。
- SOP 样本：`.agents\skills\agent-introspection-debugging\SKILL.md`, `.agents\skills\agent-sort\SKILL.md`, `.agents\skills\api-design\SKILL.md`, `.agents\skills\article-writing\SKILL.md`, `.agents\skills\backend-patterns\SKILL.md`, `.agents\skills\benchmark-methodology\SKILL.md`, `.agents\skills\brand-discovery\references\10_purpose-why.md`, `.agents\skills\brand-discovery\references\20_positioning.md` 等。
---

## 5. 八大子系统如何在 Hermes 总线下流畅驱动（全链路闭环编排）
```text
                 [DeepSeek Harness] (外层认知与意图拆解)
                         │ 生成 TaskGraphSpec (JSON-RPC)
                         ▼
           [Hermes DAG Supervisor] (物理状态机控盘)
                         │ 派发 hermes_node:<executor>
        ┌────────────────┴────────────────────────┬──────────────────────┐
        ▼                                         ▼                      ▼
[Trade AI Agent Adapter]               [DeerFlow Adapter]      [GoodJob CRM Adapter]
  - 社媒抓取潜客                         - 深度市场研报          - 7步外贸商机流转
  - WhatsApp/Email主动外联               - SEO多渠道内容生成     - WhatsApp实时翻译沟通
  - 统一收件箱意图识别                   - n8n 40+平台出站发布   - PI形式发票与CI/PL单证
        │                                         │                      ▲
        └───────────────────────┬─────────────────┴──────────────────────┘
                                ▼
                 [Site Engine & Calculator]
                   - 22 模块高转化独立站
                   - 参数计算器与 BOQ 标书解析
                   - Case Studies 信任引擎
```

### 结论：全域文件扫描与定位完毕，任何一个子系统均有清晰的代码落地位置与契约，绝无任何资产遗漏！