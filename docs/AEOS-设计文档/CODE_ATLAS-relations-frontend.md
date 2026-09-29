# CODE ATLAS · 关系摘要 + 前端 admin

## 1. 后端 app 内依赖枢纽（被 import 最多）

| 模块 | 被引用次数 | 说明 |
|------|----------:|------|
| `app.core.database` | 258 |  |
| `app.core.config` | 235 |  |
| `app.models.user` | 222 |  |
| `app.core.response` | 198 |  |
| `app.core.security` | 190 |  |
| `app.models.tenant` | 159 |  |
| `app.db.session` | 134 |  |
| `app.models.content` | 92 |  |
| `app.core.cache` | 84 |  |
| `app.models.inquiry` | 54 |  |
| `app.models.product` | 43 |  |
| `app.schemas.hermes_orchestration` | 32 |  |
| `app.core.admin_auth` | 30 |  |
| `app.core.no_fake_delivery` | 28 |  |
| `app.services.tenant_scenario_service` | 27 |  |
| `app.services.ai_engine` | 26 |  |
| `app.models.content_master` | 22 |  |
| `app.services.tenant_product_profile_service` | 22 |  |
| `app.models.nurture_cycle` | 22 |  |
| `app.services.hermes.ops_autopilot` | 22 |  |
| `app.services.paperclip.orchestrator` | 22 |  |
| `app.services.aitoearn_publish_adapter` | 21 |  |
| `app.services.scheduler_leader` | 21 |  |
| `app.services.hermes.greedy_contest_memory_service` | 21 |  |
| `app.models.email_outreach` | 20 |  |
| `app.models.ai_config` | 20 |  |
| `app.models.deerflow_job` | 20 |  |
| `app.models.payment` | 20 |  |
| `app.core.logging` | 20 |  |
| `app.services.ai_invocation_service` | 20 |  |
| `app.models.seo` | 18 |  |
| `app.services.publish_capability_registry` | 17 |  |
| `app.services.hermes.brand_guard` | 16 |  |
| `app.models.prospect_lead` | 16 |  |
| `app.models.media_factory` | 16 |  |
| `app.services.wechat_pay_v3` | 16 |  |
| `app.services.ubrain.tenant_memory_service` | 16 |  |
| `app.services.platform_account_service` | 15 |  |
| `app.services.order_addon_service` | 15 |  |
| `app.services.hermes.maintenance_constitution` | 15 |  |

## 2. 包级依赖热点（源包 → 目标）

| 源 | 目标 | 引用次数 |
|----|------|----------:|
| `api` | `core` | 645 |
| `api` | `models` | 404 |
| `api` | `app.db.session` | 110 |
| `api` | `services/hermes` | 104 |
| `core` | `core` | 97 |
| `models` | `models` | 96 |
| `models` | `core` | 90 |
| `api` | `services/ubrain` | 89 |
| `api` | `api` | 88 |
| `api` | `services/paperclip` | 37 |
| `api` | `services/foreign_trade` | 28 |
| `tasks` | `core` | 26 |
| `main.py` | `core` | 25 |
| `services/hermes/executors` | `app.schemas.hermes_orchestration` | 25 |
| `services/hermes/expert_inspection_registry.py` | `services/hermes` | 23 |
| `api` | `services/tenant_scenario_service` | 21 |
| `core` | `models` | 17 |
| `services/social_nurture_service.py` | `models` | 17 |
| `services/ubrain/super_agent_bridge.py` | `services/ubrain` | 17 |
| `services/foreign_trade/osint` | `services/foreign_trade` | 17 |
| `services/ubrain/orchestrator.py` | `services/ubrain` | 16 |
| `api` | `services/cross_border` | 15 |
| `api` | `services/geo` | 14 |
| `services/hermes/greedy_hub_service.py` | `services/hermes` | 13 |
| `domains` | `app.domains.base` | 12 |
| `tasks` | `services/deerflow` | 12 |
| `tasks` | `services/scheduler_leader` | 12 |
| `services/hermes/expert_execution_registry.py` | `services/hermes` | 11 |
| `services/hermes/greedy_agency_orchestrator_service.py` | `services/hermes` | 11 |
| `services/paperclip/tenant_context.py` | `models` | 11 |
| `main.py` | `api` | 10 |
| `api` | `services/seo` | 10 |
| `api` | `services/payment_ops_audit_service` | 10 |
| `services/hermes/command_center.py` | `services/hermes` | 10 |
| `services/ubrain/deerflow_job_service.py` | `services/ubrain` | 9 |
| `services/hermes/agency` | `services/hermes` | 9 |
| `orchestration` | `app.orchestration.interfaces` | 8 |
| `services/user_wallet_service.py` | `models` | 8 |
| `api` | `services/traffic_analytics_service` | 8 |
| `services/hermes/ops_autopilot.py` | `services/hermes` | 8 |
| `services/hermes/runtime.py` | `services/hermes` | 8 |
| `services/hermes/safe_remediation.py` | `services/hermes` | 8 |
| `services/ubrain/commercial_os_bridge.py` | `services/ubrain` | 8 |
| `services/hermes/executors` | `models` | 8 |
| `main.py` | `services/hermes` | 7 |
| `core` | `services/security_event_service` | 7 |
| `repositories` | `models` | 7 |
| `services/traffic_analytics_service.py` | `models` | 7 |
| `services/video_publish_orchestrator.py` | `services/publish_workers` | 7 |
| `tasks` | `services/hermes` | 7 |

## 3. 前端 admin 规模

- 文件：566（vue+ts）

| 顶层目录 | 文件数 | 总行数 |
|----------|------:|-------:|
| `views` | 321 | 106658 |
| `components` | 97 | 18961 |
| `composables` | 32 | 3818 |
| `utils` | 31 | 2777 |
| `api` | 24 | 4097 |
| `constants` | 21 | 3489 |
| `templates` | 13 | 2294 |
| `stores` | 10 | 1693 |
| `types` | 8 | 564 |
| `layout` | 2 | 1204 |
| `router` | 2 | 2132 |
| `App.vue` | 1 | 90 |
| `components.d.ts` | 1 | 185 |
| `main.ts` | 1 | 43 |
| `shims-vue.d.ts` | 1 | 9 |
| `vite-env.d.ts` | 1 | 60 |

## 4. views 按角色壳

### views/admin · 112 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/admin/aggregation.vue` | 949 | 按层级汇总卡片 |  |
| `views/admin/ai-center/analytics.vue` | 226 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/ai-center/article-generator.vue` | 890 | 步骤指示器 |  |
| `views/admin/ai-center/article-to-video.vue` | 935 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/ai-center/browser-companion-bridge.vue` | 149 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/ai-center/content.vue` | 527 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/ai-center/dashboard.vue` | 711 | AI引擎状态横幅 |  |
| `views/admin/ai-center/index.vue` | 18 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/ai-center/knowledge.vue` | 521 | Search Bar |  |
| `views/admin/ai-center/logs.vue` | 115 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/ai-center/models.vue` | 1274 | AI引擎状态横幅 |  |
| `views/admin/ai-center/provider-setup.vue` | 709 | 步骤条 |  |
| `views/admin/ai-center/scenario-models.vue` | 325 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/ai-center/usage.vue` | 367 | 统计卡 |  |
| `views/admin/ai-engine/analytics.vue` | 218 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/ai-engine/index.vue` | 17 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/ai-engine/models.vue` | 470 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/ai-engine/overview.vue` | 194 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/ai-engine/prompts.vue` | 506 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/ai-engine/tasks.vue` | 162 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/ai-engine/templates.vue` | 242 | 统计 |  |
| `views/admin/ai-engine/token.vue` | 220 | 统计卡片 |  |
| `views/admin/ai-engine/trade-intel.vue` | 234 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/attribution/index.vue` | 268 | KPI Cards |  |
| `views/admin/automation/index.vue` | 12 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/automation/overview.vue` | 128 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/automation/scheduler.vue` | 118 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/automation/scripts.vue` | 150 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/automation/workflows.vue` | 147 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/capability-hub.vue` | 230 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/code-tools/debug.vue` | 159 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/code-tools/format.vue` | 191 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/code-tools/generator.vue` | 157 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/code-tools/index.vue` | 17 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/code-tools/overview.vue` | 290 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/code-tools/refactor.vue` | 119 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/code-tools/review.vue` | 487 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/code-tools/scanner.vue` | 370 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/components/AdminModulePlaceholder.vue` | 110 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/dashboard.vue` | 340 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/demo-rehearsal.vue` | 1194 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/file-manager/history.vue` | 20 | 文件与对象变更历史 |  |
| `views/admin/file-manager/index.vue` | 14 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/file-manager/overview.vue` | 1095 | 统计卡片 |  |
| `views/admin/file-manager/scan.vue` | 129 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/file-manager/search.vue` | 71 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/finance/commission-rules.vue` | 119 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/finance/commissions.vue` | 175 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/finance/index.vue` | 228 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/finance/invoice-applications.vue` | 388 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/finance/ip-pool.vue` | 840 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/finance/payment-ops.vue` | 712 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/finance/payment-orders.vue` | 155 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/founder-diagnostics.vue` | 373 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. | founderOps, oauth |
| `views/admin/geo-engine/index.vue` | 232 | Hero |  |
| `views/admin/hierarchy/index.vue` | 850 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/hub/index.vue` | 56 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/index.vue` | 975 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/layout.vue` | 9 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/onboarding/index.vue` | 282 | Header |  |
| `views/admin/paperclip/approvals.vue` | 309 | 待审批列表 | paperclip |
| `views/admin/paperclip/dashboard.vue` | 429 | 公司使命卡片 | paperclip |
| `views/admin/paperclip/goals.vue` | 418 | 筛选栏 | paperclip |
| `views/admin/paperclip/heartbeats.vue` | 302 | 引擎状态卡片 | paperclip |
| `views/admin/paperclip/org-chart.vue` | 533 | 组织架构可视化树 | paperclip |
| `views/admin/platform-credentials.vue` | 396 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/platform-registry.vue` | 155 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/platform-zones.vue` | 256 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/projects/index.vue` | 17 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/projects/overview.vue` | 141 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/recycle-bin/index.vue` | 265 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/runtime/index.vue` | 17 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/runtime/overview.vue` | 548 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/scheduler/index.vue` | 17 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/scheduler/overview.vue` | 609 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/security/audit.vue` | 23 | 安全审计 |  |
| `views/admin/security/compliance.vue` | 134 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/security/index.vue` | 17 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/security/overview.vue` | 544 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/admin/security/vulnerability.vue` | 143 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| … | | 其余 32 个 | |

### views/client · 36 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/client/ai-config.vue` | 154 | 顶部提示 |  |
| `views/client/ai-scenarios.vue` | 159 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/client/aitoearn-engage.vue` | 448 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/client/assistant.vue` | 197 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/client/billing.vue` | 216 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/client/chuhaiji-app.vue` | 473 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/client/content-distribute.vue` | 494 |  | cross-border |
| `views/client/copilot.vue` | 2099 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. | foreign-trade |
| `views/client/dashboard.vue` | 898 | 核心业务中心：左 70% 询盘与外贸转化漏斗 + 右 30% 独立站与出海进展 |  |
| `views/client/egress.vue` | 325 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/client/export-quote.vue` | 109 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. | cross-border |
| `views/client/foreign-trade-team.vue` | 141 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. | foreign-trade |
| `views/client/forum-qa.vue` | 183 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. | forum |
| `views/client/geo-visibility.vue` | 198 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. | cross-border |
| `views/client/invoices.vue` | 290 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/client/layout.vue` | 12 | 租户轻量壳 — 实现见 layout/ClientShellLayout.vue |  |
| `views/client/onboarding.vue` | 868 | Step 0: 一键开业 |  |
| `views/client/plan-gate.vue` | 115 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. | admin-bff |
| `views/client/product-candidates.vue` | 116 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. | cross-border |
| `views/client/queues/fulfillment.vue` | 475 | 履约跟进与外贸7步操作抽屉 |  |
| `views/client/queues/inquiries.vue` | 598 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. | cross-border, foreign-trade |
| `views/client/queues/publish.vue` | 217 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/client/referral.vue` | 58 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/client/seo-keywords.vue` | 94 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. | cross-border |
| `views/client/site-editor-lab.vue` | 293 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. | admin-bff |
| `views/client/skills-market.vue` | 934 | 页面顶栏：给 Meoo 装上专属技能 |  |
| `views/client/templates-explore.vue` | 312 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/client/today-three.vue` | 27 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/client/tokens.vue` | 679 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/client/trade-tools.vue` | 1576 | 搜索框 |  |
| `views/client/traffic-board.vue` | 24 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/client/video-editor-embed.vue` | 240 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. | cross-border |
| `views/client/video-overseas.vue` | 797 | 顶部状态提示与能力徽标 | cross-border |
| `views/client/video-studio-project-panel.vue` | 139 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. | cross-border |
| `views/client/video-studio.vue` | 287 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. | cross-border |
| `views/client/wangcai-plugin-market.vue` | 454 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |

### views/seo · 12 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/seo/baidu-tools.vue` | 337 | 数据概览卡片 |  |
| `views/seo/batch-seo.vue` | 400 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/seo/building-wiki.vue` | 430 | 生成文章区域 |  |
| `views/seo/compliance.vue` | 415 | 内容扫描 |  |
| `views/seo/content-optimizer.vue` | 272 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/seo/eeat.vue` | 959 | 标签页切换 |  |
| `views/seo/index.vue` | 390 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/seo/keyword-ranking.vue` | 805 | 仪表盘卡片 |  |
| `views/seo/llms-txt.vue` | 355 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/seo/performance.vue` | 248 | 标签页切换 |  |
| `views/seo/schema-markup.vue` | 791 | Schema生成器 |  |
| `views/seo/site-audit.vue` | 345 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |

### views/_generated · 12 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/_generated/AbTestList.vue` | 79 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/_generated/AgentHubList.vue` | 79 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/_generated/AnalyticsList.vue` | 79 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/_generated/ComplianceList.vue` | 79 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/_generated/ContentList.vue` | 79 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/_generated/InquiriesList.vue` | 79 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/_generated/NewsList.vue` | 79 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/_generated/PaymentList.vue` | 79 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/_generated/ProductsList.vue` | 79 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/_generated/SeoList.vue` | 79 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/_generated/SettingsList.vue` | 79 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/_generated/UsersList.vue` | 79 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |

### views/sales · 10 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/sales/AutoNegotiator.vue` | 1240 | 统计卡片 |  |
| `views/sales/CompanyAccount360.vue` | 54 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/sales/CustomerFinder.vue` | 1028 | 统计卡片 |  |
| `views/sales/EmailAutomation.vue` | 1220 | 统计卡片 | ubrain/sales |
| `views/sales/OpportunityBoard.vue` | 109 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/sales/QuotesPanel.vue` | 56 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/sales/RfqPanel.vue` | 95 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/sales/SalesTaskCenter.vue` | 64 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/sales/dashboard.vue` | 282 | 顶部统计卡片 |  |
| `views/sales/index.vue` | 32 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |

### views/tenants · 10 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/tenants/billing.vue` | 533 | 租户选择器 |  |
| `views/tenants/dashboard.vue` | 881 | 统计卡片 |  |
| `views/tenants/domain.vue` | 312 | 主域名展示 |  |
| `views/tenants/index.vue` | 32 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/tenants/plans.vue` | 297 | ==================== 创建/编辑 Modal ==================== |  |
| `views/tenants/pricing.vue` | 609 | Header |  |
| `views/tenants/product-showcase.vue` | 938 | ==================== HERO ==================== |  |
| `views/tenants/register.vue` | 483 | Header |  |
| `views/tenants/site-editor.vue` | 2452 | Header：产品名 + 产品图 + AI 一键生成 |  |
| `views/tenants/white-label.vue` | 209 | 租户选择 |  |

### views/seo-matrix · 9 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/seo-matrix/content.vue` | 661 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/seo-matrix/dashboard.vue` | 424 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/seo-matrix/growth-tools.vue` | 885 | 总览 |  |
| `views/seo-matrix/inclusion.vue` | 570 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/seo-matrix/index.vue` | 49 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/seo-matrix/keywords.vue` | 619 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/seo-matrix/publish.vue` | 1526 | ========== 1. AI 内容生成区 ========== |  |
| `views/seo-matrix/regions.vue` | 527 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/seo-matrix/settings.vue` | 379 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |

### views/agent · 7 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/agent/account-opening.vue` | 513 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/agent/churn-warning.vue` | 598 | 统计卡片 |  |
| `views/agent/commission.vue` | 148 | 结算规则说明 | index |
| `views/agent/daily-report.vue` | 485 | 概览总结 |  |
| `views/agent/layout.vue` | 12 | @deprecated 已迁入 YoudingProLayout；保留文件避免旧引用 404 |  |
| `views/agent/performance.vue` | 520 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/agent/traffic-board.vue` | 118 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |

### views/ai-center · 7 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/ai-center/analytics.vue` | 378 | Tab 1: SEO Analysis |  |
| `views/ai-center/content.vue` | 338 | Left: Generation Form |  |
| `views/ai-center/dashboard.vue` | 298 | AI Engine Health Status |  |
| `views/ai-center/index.vue` | 18 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/ai-center/logs.vue` | 292 | Cost Summary Cards |  |
| `views/ai-center/models.vue` | 266 | Provider Cards |  |
| `views/ai-center/skill-store.vue` | 1185 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |

### views/system · 7 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/system/analytics.vue` | 438 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/system/drag-module.vue` | 379 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/system/effects.vue` | 462 | 背景装饰动画 |  |
| `views/system/performance.vue` | 407 | 标签页切换 |  |
| `views/system/settings-main.vue` | 348 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/system/settings.vue` | 116 | 侧边导航 |  |
| `views/system/users.vue` | 331 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |

### views/agent-hub · 6 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/agent-hub/dashboard.vue` | 95 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/agent-hub/execution-review.vue` | 164 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/agent-hub/index.vue` | 32 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/agent-hub/mcp-bridge.vue` | 148 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/agent-hub/task-graph.vue` | 334 | ① 提交编排任务 | orchestration |
| `views/agent-hub/task-orchestrator.vue` | 166 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |

### views/login · 6 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/login/LoginBrandColumn.vue` | 305 | decorative animated layers |  |
| `views/login/LoginOAuthRow.vue` | 137 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. | oauth |
| `views/login/LoginSocialButtons.vue` | 63 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. | oauth |
| `views/login/forgot-password.vue` | 164 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/login/index.vue` | 1024 | Right Form Column | emailAuth, oauth |
| `views/login/oauth-callback.vue` | 121 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. | oauth, oauthBindings |

### views/logistics · 6 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/logistics/dashboard.vue` | 128 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/logistics/freight-calc.vue` | 105 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/logistics/index.vue` | 32 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/logistics/lbs-routing.vue` | 130 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/logistics/orders-track.vue` | 272 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/logistics/quotation.vue` | 199 | Create Modal |  |

### views/templates · 6 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/templates/dashboard-data-cockpit.vue` | 1034 | Top Bar: Search + Actions |  |
| `views/templates/dashboard-data-screen.vue` | 821 | Top Header |  |
| `views/templates/dashboard-enterprise.vue` | 716 | Breadcrumb + User |  |
| `views/templates/dashboard-saas.vue` | 815 | SaaS Top Bar: Tenant Switcher + Global Actions |  |
| `views/templates/dashboard-tencent.vue` | 660 | Top Navigation |  |
| `views/templates/index.vue` | 358 | Header |  |

### views/ai-learning · 5 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/ai-learning/auto-ab-test.vue` | 156 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/ai-learning/behavior.vue` | 168 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/ai-learning/conversion-funnel.vue` | 113 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/ai-learning/dashboard.vue` | 80 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/ai-learning/index.vue` | 32 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |

### views/cognitive · 5 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/cognitive/dashboard.vue` | 51 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/cognitive/expert-system.vue` | 55 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/cognitive/index.vue` | 32 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/cognitive/qa-engine.vue` | 107 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/cognitive/semantic-index.vue` | 116 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |

### views/developer · 5 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/developer/dashboard.vue` | 44 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/developer/index.vue` | 32 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/developer/low-code.vue` | 155 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/developer/plugins.vue` | 131 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/developer/sdk.vue` | 114 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |

### views/edge-cdn · 5 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/edge-cdn/dashboard.vue` | 86 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/edge-cdn/index.vue` | 32 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/edge-cdn/nodes.vue` | 107 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/edge-cdn/preheat.vue` | 130 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/edge-cdn/protocol.vue` | 96 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |

### views/globalization · 5 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/globalization/culture-adapt.vue` | 125 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/globalization/dashboard.vue` | 117 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/globalization/glossary.vue` | 129 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/globalization/index.vue` | 32 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/globalization/translator.vue` | 56 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |

### views/media-factory · 5 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/media-factory/charts.vue` | 185 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/media-factory/dashboard.vue` | 615 | Stats |  |
| `views/media-factory/index.vue` | 32 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/media-factory/render-queue.vue` | 367 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/media-factory/tts.vue` | 143 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |

### views/system-health · 5 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/system-health/backup.vue` | 129 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/system-health/dashboard.vue` | 198 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/system-health/index.vue` | 84 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/system-health/resource-monitor.vue` | 129 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/system-health/stress-test.vue` | 149 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |

### views/international · 4 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/international/dashboard.vue` | 273 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/international/index.vue` | 7 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/international/inquiries.vue` | 254 | 筛选栏 |  |
| `views/international/sites.vue` | 384 | 添加/编辑弹窗 |  |

### views/referral · 4 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/referral/dashboard.vue` | 704 | ===== 顶部 Banner ===== |  |
| `views/referral/index.vue` | 11 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/referral/redemption-admin.vue` | 115 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/referral/rules.vue` | 259 | ===== 顶部 ===== |  |

### views/products · 3 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/products/categories.vue` | 399 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/products/edit.vue` | 497 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/products/index.vue` | 448 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |

### views/workspace · 3 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/workspace/OutreachEditor.vue` | 461 | 左侧：画像摘要 |  |
| `views/workspace/ProspectingWorkspace.vue` | 584 | 步骤条 |  |
| `views/workspace/SkillConsole.vue` | 346 | 技能卡片网格 |  |

### views/cases · 2 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/cases/edit.vue` | 246 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/cases/index.vue` | 279 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |

### views/content · 2 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/content/edit.vue` | 394 | 编辑器加载中 |  |
| `views/content/index.vue` | 314 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |

### views/inquiries · 2 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/inquiries/im-routing.vue` | 626 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/inquiries/index.vue` | 738 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. | cross-border |

### views/integrations · 2 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/integrations/AiConfig.vue` | 580 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |
| `views/integrations/Feishu.vue` | 130 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |

### views/access-denied.vue · 1 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/access-denied.vue` | 112 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |

### views/NotFound.vue · 1 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/NotFound.vue` | 43 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |

### views/PrivacyPolicy.vue · 1 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/PrivacyPolicy.vue` | 252 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |

### views/TermsOfService.vue · 1 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/TermsOfService.vue` | 116 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |

### views/annex · 1 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/annex/AnnexEmbedPage.vue` | 284 | 异常状态 1: 未配置或未部署 |  |

### views/compliance · 1 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/compliance/index.vue` | 131 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |

### views/cross-platform · 1 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/cross-platform/dashboard.vue` | 322 | 概览卡片 |  |

### views/dashboard · 1 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/dashboard/index.vue` | 724 | Alerts for degraded/empty states |  |

### views/deerflow · 1 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/deerflow/Monitor.vue` | 225 | 状态统计 |  |

### views/evolution · 1 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/evolution/Dashboard.vue` | 218 | 统计卡片 |  |

### views/experiments · 1 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/experiments/AbTest.vue` | 79 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |

### views/landing · 1 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/landing/index.vue` | 1079 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |

### views/n8n · 1 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/n8n/Workflows.vue` | 204 | 操作栏 |  |

### views/news · 1 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/news/index.vue` | 379 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |

### views/operations · 1 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/operations/traffic-board.vue` | 46 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |

### views/partner · 1 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/partner/performance.vue` | 295 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. |  |

### views/publish · 1 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/publish/unified.vue` | 852 | Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved. | foreign-trade |

### views/sites · 1 文件

| 文件 | 行 | 说明 | 调 API |
|------|---:|------|--------|
| `views/sites/SiteBuild.vue` | 297 | 步骤指示器 |  |

## 5. 其他前端关键目录（抽样说明）

### api/ · 24 文件

- `api/index.ts` (776) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `api/cross-border.ts` (709) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `api/hermesGreedy.ts` (479) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `api/ubrain/sales.ts` (279) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `api/paperclip.ts` (207) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `api/foreign-trade.ts` (206) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `api/orchestration.ts` (148) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `api/admin-bff.ts` (133) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `api/oauth.ts` (132) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `api/ubrain/invitation.ts` (124) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `api/founderOps.ts` (123) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `api/ubrain/task.ts` (113) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `api/ubrain/skill.ts` (103) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `api/ubrain/conversation.ts` (98) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `api/authRefresh.ts` (93) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `api/admin-bff.types.ts` (75) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `api/forum.ts` (58) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `api/emailAuth.ts` (54) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `api/fetchWrapper.ts` (53) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `api/oauthBindings.ts` (43) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `api/authPaths.ts` (29) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `api/analytics.ts` (26) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `api/response.ts` (18) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `api/system.ts` (18) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.

### stores/ · 10 文件

- `stores/auth.ts` (271) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `stores/workTabs.ts` (239) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `stores/uiPreferences.ts` (205) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `stores/task.ts` (180) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `stores/agentCapabilities.ts` (168) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `stores/conversation.ts` (161) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `stores/skill.ts` (151) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `stores/user.ts` (146) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `stores/websocket.ts` (144) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `stores/index.ts` (28) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.

### router/ · 2 文件

- `router/index.ts` (2051) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `router/generated-crud-routes.ts` (81) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.

### components/youding/ · 32 文件

- `components/youding/YdTodayWorkbench.vue` (261) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `components/youding/formily/siteEditorSchema.ts` (200) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `components/youding/YdFinanceNav.vue` (187) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `components/youding/TenantLoginPanel.vue` (170) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `components/youding/LoginOAuthButtons.vue` (168) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `components/youding/YdTodayQueue.vue` (142) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `components/youding/YdHonestDataBanner.vue` (130) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `components/youding/YdDataTable.vue` (125) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `components/youding/YdStatsCard.vue` (124) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `components/youding/YdClientPlanUsageBar.vue` (116) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `components/youding/YdReliefIcon.vue` (102) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `components/youding/formily/siteEditorSeoSchema.ts` (99) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `components/youding/YdTableToolbar.vue` (92) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `components/youding/YdSchemaForm.vue` (90) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `components/youding/YdUsageMeter.vue` (88) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `components/youding/YdTableColumnSettings.vue` (85) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `components/youding/YdWorkspaceHeader.vue` (82) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `components/youding/YdEmptyState.vue` (79) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `components/youding/YdOnboardingCard.vue` (73) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `components/youding/CoachProPageShell.vue` (67) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `components/youding/YdFormilyForm.vue` (66) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `components/youding/formily/antdv-bridge.ts` (66) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `components/youding/YdPageHeader.vue` (58) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `components/youding/LoginFeatureIcon.vue` (49) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `components/youding/YdCheckMark.vue` (48) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.

### utils/ · 31 文件

- `utils/api.ts` (323) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `utils/websocket.ts` (298) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `utils/tenantPlanDisplay.ts` (240) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `utils/siteEditorLabSync.ts` (226) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `utils/l-pro-publish-gate.ts` (182) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `utils/index.ts` (170) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `utils/shellNavKernel.ts` (104) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `utils/hermesSiteBuilder.ts` (92) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `utils/noFakeDelivery.ts` (92) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `utils/aiModelCapability.ts` (86) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `utils/sessionKick.ts` (77) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `utils/onboardingAutopilot.ts` (76) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `utils/jwtPayload.ts` (70) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `utils/flattenMenuNav.ts` (65) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `utils/prefetchPostLoginShell.ts` (62) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `utils/multipostBridge.ts` (60) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `utils/sessionKick.spec.ts` (59) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `utils/sessionAuth.ts` (56) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `utils/aiConfigHelpers.ts` (52) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `utils/siteProductImages.ts` (52) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `utils/ydTableUtils.ts` (51) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `utils/postLoginNavigation.ts` (47) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `utils/productAiPrompt.ts` (42) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `utils/mediaStudioHandoff.ts` (40) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `utils/ydTableUtils.spec.ts` (32) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.

### constants/ · 21 文件

- `constants/workbenchCapabilityRegistry.ts` (797) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `constants/stubVisibility.ts` (386) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `constants/antIconMap.ts` (308) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `constants/roleShellLock.ts` (246) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `constants/iconCatalog.ts` (227) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `constants/proShellMenus.ts` (195) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `constants/navRouteRegistry.ts` (192) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `constants/extModuleNav.ts` (169) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `constants/agentLevelBlueprint.ts` (159) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `constants/platformShellMenu.ts` (155) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `constants/workbenchIcons.ts` (132) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `constants/sales-assistant-brand.ts` (104) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `constants/annexModules.ts` (88) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `constants/tenantMediaSpace.ts` (77) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `constants/loginPortalCopy.ts` (63) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `constants/workbenchPathCapabilities.ts` (53) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `constants/platformRoleDisplay.ts` (48) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `constants/countryOptions.ts` (26) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `constants/lProTier1Locales.ts` (25) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `constants/productImageSpace.ts` (25) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
- `constants/assistant-mascot.ts` (14) — Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
