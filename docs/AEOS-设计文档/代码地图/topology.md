# 代码关系拓扑图 · 复核报告（2026-09-11）

> 数据来源：`docs/代码地图/atlas.json`（由 `tools/code_atlas_gen.py` 真扫 worktree + 运行源 + `_external/aionui` 生成）
> 范围：4,608 个源码文件，不含 `.git/node_modules/__pycache__/dist/build/.venv` 等制品目录。
> 本拓扑只抽取 **内部 import / include_router** 关系，函数级调用链需额外静态/运行时分析。

## 一、总体统计

| 指标 | 值 |
|---|---|
| 分析文件数 | 4,608 |
| 有效内部依赖边 | 3,050 |
| 包（前 5 段路径） | 1,752 |
| 子系统 | 343 |
| FastAPI 路由 | 1,895 |
| ORM 表名 | 237 |
| 解析失败文件 | 4 |

## 二、子系统节点分布

| 子系统 | 文件数 |
|---|---|
| 其他 | 2191 |
| 前端 admin | 561 |
| 前端 web | 254 |
| Skills 资产 | 254 |
| API 路由层 | 240 |
| ORM 模型层 | 94 |
| Hermes 编排 | 91 |
| backend/services/ubrain | 83 |
| SEO backend | 73 |
| 核心配置与安全 | 67 |
| AionUi 外部应用 | 66 |
| backend/services/foreign_trade | 38 |
| backend/services/cross_border | 30 |
| SEO admin | 29 |
| Pydantic Schema 层 | 24 |
| backend/services/talking_stick | 19 |
| Celery 任务 | 13 |
| backend/services/registry | 11 |
| backend/services/geo | 9 |
| backend/services/publish_workers | 9 |
| backend/services/platforms | 8 |
| backend/orchestration/executors | 7 |
| Browser Runtime 取证 | 7 |
| backend/services/moss_vl | 7 |
| backend/services/paperclip | 7 |
| backend/services/pipeline | 7 |
| backend/services/seo | 7 |
| backend/services/wangcai | 7 |
| backend/services/crawlers | 6 |
| DeerFlow 深研 | 6 |
| backend/services/tasks | 6 |
| 数据库引擎 | 5 |
| 数据访问层 | 5 |
| backend/services/agent_loop | 5 |
| backend/services/analytics | 5 |
| backend/services/egress | 5 |
| backend/services/evolution | 5 |
| backend/services/feishu | 5 |
| backend/services/model_gateway | 5 |
| Cloudflare Workers | 5 |
| backend/services/ai | 4 |
| n8n 出站 | 4 |
| backend/services/payment_pkg | 4 |
| backend/services/trace | 4 |
| backend/services/deepseek_harness | 3 |
| GoodJob CRM 桥 | 3 |
| backend/services/matching_engine | 3 |
| backend/services/site_builder | 3 |
| backend/services/vault | 3 |
| backend/domains/lead | 2 |
| backend/services/adapters | 2 |
| backend/services/annex | 2 |
| backend/services/billing | 2 |
| backend/services/calculators | 2 |
| backend/services/orchestrator | 2 |
| backend/services/policy | 2 |
| backend/__init__.py | 1 |
| backend/data/__init__.py | 1 |
| backend/domains/__init__.py | 1 |
| backend/domains/ai | 1 |
| backend/domains/auth | 1 |
| backend/domains/base.py | 1 |
| backend/domains/content | 1 |
| backend/domains/inquiry | 1 |
| backend/domains/payment | 1 |
| backend/domains/product | 1 |
| backend/domains/public | 1 |
| backend/domains/seo | 1 |
| backend/domains/system | 1 |
| backend/domains/tenant | 1 |
| backend/geo_engine/database_new.py | 1 |
| backend/geo_engine/geo_optimizer.py | 1 |
| backend/geo_engine/rank_monitor.py | 1 |
| backend/geo_engine/repositories.py | 1 |
| backend/graduation/manager.py | 1 |
| backend/graduation/models.py | 1 |
| FastAPI 入口 | 1 |
| backend/orchestration/__init__.py | 1 |
| backend/orchestration/interfaces.py | 1 |
| backend/orchestration/registry.py | 1 |
| backend/performance/alert_trigger.py | 1 |
| backend/performance/models.py | 1 |
| backend/performance/monitor.py | 1 |
| backend/services/__init__.py | 1 |
| backend/services/_scan_long.py | 1 |
| backend/services/acme_service.py | 1 |
| backend/services/acquisition_outreach_service.py | 1 |
| backend/services/agent_aggregation_service.py | 1 |
| backend/services/agent_commission_service.py | 1 |
| backend/services/agent_hub_service.py | 1 |
| backend/services/agent_node_write_service.py | 1 |
| backend/services/agent_portal_service.py | 1 |
| backend/services/ai_config_service.py | 1 |
| backend/services/ai_engine.py | 1 |
| backend/services/ai_invocation_service.py | 1 |
| backend/services/ai_key_probe.py | 1 |
| backend/services/ai_learning_service.py | 1 |
| backend/services/ai_model_capability_service.py | 1 |
| backend/services/ai_multimodal_studio.py | 1 |
| backend/services/ai_recommendation_service.py | 1 |
| backend/services/ai_search_probe_service.py | 1 |
| backend/services/ai_site_engine.py | 1 |
| backend/services/ai_traffic_connect_service.py | 1 |
| backend/services/ai_traffic_provider_service.py | 1 |
| backend/services/aitoearn_engage_send_service.py | 1 |
| backend/services/aitoearn_hub_service.py | 1 |
| backend/services/aitoearn_local_proxy.py | 1 |
| backend/services/aitoearn_publish_adapter.py | 1 |
| backend/services/alert_service.py | 1 |
| backend/services/alipay_client.py | 1 |
| backend/services/attribution_service.py | 1 |
| backend/services/auto_backup.py | 1 |
| backend/services/backup_service.py | 1 |
| backend/services/baidu_webmaster_service.py | 1 |
| backend/services/bff_cache_service.py | 1 |
| backend/services/cache_service.py | 1 |
| backend/services/churn_service.py | 1 |
| backend/services/client_bff_service.py | 1 |
| backend/services/client_today_service.py | 1 |
| backend/services/client_today_three_service.py | 1 |
| backend/services/cognitive_service.py | 1 |
| backend/services/commission_rule_service.py | 1 |
| backend/services/compliance_scanner.py | 1 |
| backend/services/content_feedback_loop.py | 1 |
| backend/services/content_master_publish_service.py | 1 |
| backend/services/content_optimizer.py | 1 |
| backend/services/content_scorer.py | 1 |
| backend/services/content_service.py | 1 |
| backend/services/cosmos_infer_service.py | 1 |
| backend/services/cross_platform_dashboard_service.py | 1 |
| backend/services/dacheng_keyword_seed_service.py | 1 |
| backend/services/daily_report_service.py | 1 |
| backend/services/developer_service.py | 1 |
| backend/services/douyin_comment_pull_service.py | 1 |
| backend/services/douyin_comment_sync_service.py | 1 |
| backend/services/eeat_scorer.py | 1 |
| backend/services/egress_addon_service.py | 1 |
| backend/services/egress_jit_provision_service.py | 1 |
| backend/services/egress_quota_service.py | 1 |
| backend/services/egress_replenish_service.py | 1 |
| backend/services/egress_supplier_service.py | 1 |
| backend/services/einvoice_provider.py | 1 |
| backend/services/email_recovery_service.py | 1 |
| backend/services/email_service.py | 1 |
| backend/services/email_tracking_service.py | 1 |
| backend/services/facade | 1 |
| backend/services/finance_honesty.py | 1 |
| backend/services/finance_service.py | 1 |
| backend/services/foreign_trade_ecosystem_service.py | 1 |
| backend/services/forum_sidecar_service.py | 1 |
| backend/services/forum_webhook_service.py | 1 |
| backend/services/founder_wechat_service.py | 1 |
| backend/services/gdpr_compliance.py | 1 |
| backend/services/gdpr_compliance_service.py | 1 |
| backend/services/geo_agents.py | 1 |
| backend/services/geo_alert_service.py | 1 |
| backend/services/geo_engine_service.py | 1 |
| backend/services/geo_lead_service.py | 1 |
| backend/services/geo_rag_evaluator.py | 1 |
| backend/services/geo_rank_guard.py | 1 |
| backend/services/geo_rank_guard_probe.py | 1 |
| backend/services/globalization_service.py | 1 |
| backend/services/growth_loop_service.py | 1 |
| backend/services/growth_services.py | 1 |
| backend/services/growth_tools_service.py | 1 |
| backend/services/hub_urls.py | 1 |
| backend/services/im_channel_webhook_service.py | 1 |
| backend/services/im_locale_service.py | 1 |
| backend/services/industry_pattern_service.py | 1 |
| backend/services/inquiries_portal_service.py | 1 |
| backend/services/inquiries_unified_service.py | 1 |
| backend/services/inquiry_assignment_audit_service.py | 1 |
| backend/services/inquiry_lead_assignment_service.py | 1 |
| backend/services/inquiry_push_service.py | 1 |
| backend/services/inquiry_weekly_service.py | 1 |
| backend/services/integrations_status_service.py | 1 |
| backend/services/invoice_application_service.py | 1 |
| backend/services/invoice_pdf_service.py | 1 |
| backend/services/journey_health_service.py | 1 |
| backend/services/jtbd_site_service.py | 1 |
| backend/services/keyword_tracker.py | 1 |
| backend/services/knowledge_ingestion.py | 1 |
| backend/services/knowledge_service.py | 1 |
| backend/services/lab_site_editor_service.py | 1 |
| backend/services/langchain_service.py | 1 |
| backend/services/license_service.py | 1 |
| backend/services/logistics_access.py | 1 |
| backend/services/logistics_dashboard_service.py | 1 |
| backend/services/logistics_provider.py | 1 |
| backend/services/logistics_tracking_service.py | 1 |
| backend/services/matrix_admin_bridge.py | 1 |
| backend/services/media | 1 |
| backend/services/media_cleanup_scheduler.py | 1 |
| backend/services/media_cloud_upload_service.py | 1 |
| backend/services/media_cuplayer_service.py | 1 |
| backend/services/media_factory_service.py | 1 |
| backend/services/media_guest_service.py | 1 |
| backend/services/media_lenslink_service.py | 1 |
| backend/services/media_publish_service.py | 1 |
| backend/services/media_qiniu_service.py | 1 |
| backend/services/media_r2_service.py | 1 |
| backend/services/media_render_worker.py | 1 |
| backend/services/media_retention_service.py | 1 |
| backend/services/media_seo_service.py | 1 |
| backend/services/media_tenant_traffic_service.py | 1 |
| backend/services/media_video_edit_service.py | 1 |
| backend/services/minio_service.py | 1 |
| backend/services/moss_auto_clip_pipeline.py | 1 |
| backend/services/moss_clip_and_publish_workflow.py | 1 |
| backend/services/moss_vl_service.py | 1 |
| backend/services/nurture_execution_scheduler.py | 1 |
| backend/services/nurture_execution_worker.py | 1 |
| backend/services/nvidia_catalog_service.py | 1 |
| backend/services/nvidia_customer_probe_scheduler.py | 1 |
| backend/services/nvidia_customer_probe_service.py | 1 |
| backend/services/nvidia_customer_probe_store.py | 1 |
| backend/services/nvidia_scenario_health_service.py | 1 |
| backend/services/nvidia_scenario_service.py | 1 |
| backend/services/oauth_binding_service.py | 1 |
| backend/services/oauth_login.py | 1 |
| backend/services/omnichannel_support_service.py | 1 |
| backend/services/onboarding_autopilot_job.py | 1 |
| backend/services/onboarding_autopilot_service.py | 1 |
| backend/services/onboarding_chain_service.py | 1 |
| backend/services/onboarding_external_accounts.py | 1 |
| backend/services/onboarding_im_contacts_service.py | 1 |
| backend/services/onboarding_platform_service.py | 1 |
| backend/services/onboarding_progress_service.py | 1 |
| backend/services/onboarding_publish_service.py | 1 |
| backend/services/onboarding_service.py | 1 |
| backend/services/ops_autopilot_scheduler.py | 1 |
| backend/services/ops_backup_service.py | 1 |
| backend/services/ops_expert_autonomy_service.py | 1 |
| backend/services/ops_readiness_alert_service.py | 1 |
| backend/services/order_addon_service.py | 1 |
| backend/services/order_payment_sync_service.py | 1 |
| backend/services/outreach_batch_compensate_service.py | 1 |
| backend/services/payment_balance_service.py | 1 |
| backend/services/payment_compensation_service.py | 1 |
| backend/services/payment_ops_audit_service.py | 1 |
| backend/services/payment_ops_service.py | 1 |
| backend/services/payment_service.py | 1 |
| backend/services/paypal_pay_service.py | 1 |
| backend/services/performance_monitor.py | 1 |
| backend/services/pilot_rehearsal_service.py | 1 |
| backend/services/plan_gate_service.py | 1 |
| backend/services/platform_account_service.py | 1 |
| backend/services/platform_alignment_service.py | 1 |
| backend/services/platform_catalog.py | 1 |
| backend/services/platform_storage_provision_service.py | 1 |
| backend/services/platform_sync_service.py | 1 |
| backend/services/product_content_ai_service.py | 1 |
| backend/services/product_image_storage_service.py | 1 |
| backend/services/product_service.py | 1 |
| backend/services/production_readiness_service.py | 1 |
| backend/services/prospect_scorer.py | 1 |
| backend/services/provisioning_service.py | 1 |
| backend/services/publish_capability_registry.py | 1 |
| backend/services/publish_dispatch_service.py | 1 |
| backend/services/publish_queue_service.py | 1 |
| backend/services/publish_readiness_service.py | 1 |
| backend/services/publish_result_notify_service.py | 1 |
| backend/services/publish_service.py | 1 |
| backend/services/push_notification_service.py | 1 |
| backend/services/rag_pricing_guard.py | 1 |
| backend/services/rank_checker.py | 1 |
| backend/services/rank_scheduler.py | 1 |
| backend/services/referral_redeem_service.py | 1 |
| backend/services/referral_reward_service.py | 1 |
| backend/services/referral_service.py | 1 |
| backend/services/refund_service.py | 1 |
| backend/services/rfq_service.py | 1 |
| backend/services/rum_metrics_service.py | 1 |
| backend/services/sales_channel_rehearsal_service.py | 1 |
| backend/services/sales_push_service.py | 1 |
| backend/services/scenario_health_scheduler.py | 1 |
| backend/services/scenario_health_store.py | 1 |
| backend/services/scheduled_publish_retry_service.py | 1 |
| backend/services/scheduler_leader.py | 1 |
| backend/services/schema_generator.py | 1 |
| backend/services/security_auditor.py | 1 |
| backend/services/security_event_service.py | 1 |
| backend/services/seo_analyzer.py | 1 |
| backend/services/seo_report_service.py | 1 |
| backend/services/seven_step_framework_service.py | 1 |
| backend/services/site_ai_service.py | 1 |
| backend/services/site_audit.py | 1 |
| backend/services/site_content_array_i18n.py | 1 |
| backend/services/site_content_bridge.py | 1 |
| backend/services/site_content_i18n_ai_service.py | 1 |
| backend/services/site_content_i18n_service.py | 1 |
| backend/services/site_content_locale_service.py | 1 |
| backend/services/site_l_pro_service.py | 1 |
| backend/services/site_product_assets.py | 1 |
| backend/services/social_interaction_service.py | 1 |
| backend/services/social_nurture_service.py | 1 |
| backend/services/ssl_certificate_service.py | 1 |
| backend/services/stripe_pay_service.py | 1 |
| backend/services/stripe_service.py | 1 |
| backend/services/super_admin_path_audit.py | 1 |
| backend/services/technical_qna_service.py | 1 |
| backend/services/tenant_aitoearn_slot_service.py | 1 |
| backend/services/tenant_lifecycle_service.py | 1 |
| backend/services/tenant_llms_txt_service.py | 1 |
| backend/services/tenant_onboarding_service.py | 1 |
| backend/services/tenant_product_context.py | 1 |
| backend/services/tenant_product_profile_service.py | 1 |
| backend/services/tenant_renewal_notify_service.py | 1 |
| backend/services/tenant_scenario_service.py | 1 |
| backend/services/tenant_service.py | 1 |
| backend/services/tenant_settings_service.py | 1 |
| backend/services/tenant_site_persistence.py | 1 |
| backend/services/tenant_wangcai_service.py | 1 |
| backend/services/tenant_wecom_config_service.py | 1 |
| backend/services/token_service.py | 1 |
| backend/services/trade_intel_commercial_service.py | 1 |
| backend/services/trade_intel_comtrade_client.py | 1 |
| backend/services/trade_intel_customs_service.py | 1 |
| backend/services/trade_intel_data.py | 1 |
| backend/services/trade_intel_refresh_service.py | 1 |
| backend/services/trade_intel_scheduler.py | 1 |
| backend/services/trade_intel_seed.py | 1 |
| backend/services/trade_intel_service.py | 1 |
| backend/services/trade_platform_meta.py | 1 |
| backend/services/traffic_analytics_service.py | 1 |
| backend/services/tts_synthesis_service.py | 1 |
| backend/services/unified_admin_login.py | 1 |
| backend/services/unified_geo_score_service.py | 1 |
| backend/services/user_service.py | 1 |
| backend/services/user_wallet_service.py | 1 |
| backend/services/video_bind_hub_service.py | 1 |
| backend/services/video_publish_orchestrator.py | 1 |
| backend/services/video_publish_router.py | 1 |
| backend/services/video_seo_geo_aao_optimizer.py | 1 |
| backend/services/visitor_locale_service.py | 1 |
| backend/services/wangcai_reply_locale.py | 1 |
| backend/services/wangcai_trade_service.py | 1 |
| backend/services/wechat_pay_v3.py | 1 |
| backend/services/wechat_platform_cert_service.py | 1 |
| backend/services/wecom_push_service.py | 1 |
| backend/services/workflow_canvas_service.py | 1 |
| backend/workers/__init__.py | 1 |
| backend/workers/publish_worker.py | 1 |

## 三、子系统间调用拓扑（Top 80）

| 从 | 到 | 权重（import 次数）|
|---|---|---|
| 其他 | 其他 | 2265 |
| 前端 admin | 其他 | 1121 |
| API 路由层 | 核心配置与安全 | 529 |
| API 路由层 | ORM 模型层 | 305 |
| 前端 admin | 前端 admin | 112 |
| API 路由层 | 数据库引擎 | 102 |
| ORM 模型层 | 核心配置与安全 | 89 |
| Hermes 编排 | Hermes 编排 | 66 |
| API 路由层 | API 路由层 | 65 |
| 核心配置与安全 | 核心配置与安全 | 57 |
| 前端 web | 其他 | 48 |
| AionUi 外部应用 | AionUi 外部应用 | 48 |
| 其他 | 核心配置与安全 | 44 |
| backend/services/ubrain | backend/services/ubrain | 39 |
| Hermes 编排 | 核心配置与安全 | 37 |
| 其他 | ORM 模型层 | 36 |
| API 路由层 | backend/services/ubrain | 35 |
| backend/services/cross_border | backend/services/cross_border | 34 |
| backend/services/ubrain | ORM 模型层 | 33 |
| backend/services/foreign_trade | backend/services/foreign_trade | 32 |
| API 路由层 | Pydantic Schema 层 | 31 |
| 前端 web | 前端 web | 28 |
| AionUi 外部应用 | 其他 | 27 |
| backend/services/cross_border | 核心配置与安全 | 21 |
| backend/services/cross_border | ORM 模型层 | 21 |
| Hermes 编排 | Pydantic Schema 层 | 19 |
| backend/services/ubrain | 核心配置与安全 | 18 |
| 其他 | Hermes 编排 | 17 |
| Hermes 编排 | ORM 模型层 | 16 |
| API 路由层 | Hermes 编排 | 15 |
| FastAPI 入口 | 核心配置与安全 | 15 |
| SEO admin | 其他 | 15 |
| backend/services/foreign_trade | ORM 模型层 | 14 |
| ORM 模型层 | ORM 模型层 | 13 |
| backend/services/moss_vl | backend/services/moss_vl | 13 |
| SEO admin | SEO admin | 13 |
| API 路由层 | backend/services/foreign_trade | 12 |
| backend/services/publish_workers | backend/services/publish_workers | 12 |
| API 路由层 | backend/services/cross_border | 11 |
| 核心配置与安全 | ORM 模型层 | 11 |
| backend/services/registry | backend/services/registry | 11 |
| 其他 | backend/orchestration/executors | 11 |
| API 路由层 | backend/services/tenant_scenario_service.py | 10 |
| Pydantic Schema 层 | Pydantic Schema 层 | 10 |
| 其他 | 数据库引擎 | 10 |
| 其他 | Pydantic Schema 层 | 9 |
| Browser Runtime 取证 | Browser Runtime 取证 | 8 |
| backend/services/model_gateway | backend/services/model_gateway | 8 |
| 其他 | backend/services/moss_vl | 8 |
| 数据访问层 | ORM 模型层 | 7 |
| DeerFlow 深研 | DeerFlow 深研 | 7 |
| backend/services/evolution | backend/services/evolution | 7 |
| backend/services/platforms | backend/services/platforms | 7 |
| backend/services/platforms | ORM 模型层 | 7 |
| backend/services/publish_workers | 核心配置与安全 | 7 |
| backend/services/video_publish_orchestrator.py | backend/services/publish_workers | 7 |
| Celery 任务 | 核心配置与安全 | 7 |
| API 路由层 | backend/services/traffic_analytics_service.py | 6 |
| backend/orchestration/executors | backend/orchestration/executors | 6 |
| backend/orchestration/executors | backend/orchestration/interfaces.py | 6 |
| backend/services/crawlers | backend/services/crawlers | 6 |
| backend/services/feishu | backend/services/feishu | 6 |
| Hermes 编排 | backend/services/ubrain | 6 |
| backend/services/onboarding_progress_service.py | ORM 模型层 | 6 |
| Cloudflare Workers | 其他 | 6 |
| API 路由层 | DeerFlow 深研 | 5 |
| API 路由层 | backend/services/finance_honesty.py | 5 |
| API 路由层 | backend/services/media_tenant_traffic_service.py | 5 |
| backend/services/agent_loop | backend/services/agent_loop | 5 |
| backend/services/agent_portal_service.py | ORM 模型层 | 5 |
| backend/services/analytics | backend/services/analytics | 5 |
| backend/services/cross_border | backend/services/media_factory_service.py | 5 |
| backend/services/cross_border | backend/services/tenant_product_profile_service.py | 5 |
| DeerFlow 深研 | ORM 模型层 | 5 |
| backend/services/feishu | ORM 模型层 | 5 |
| backend/services/paperclip | ORM 模型层 | 5 |
| backend/services/registry | ORM 模型层 | 5 |
| backend/services/seo | ORM 模型层 | 5 |
| backend/services/traffic_analytics_service.py | ORM 模型层 | 5 |
| backend/services/ubrain | Hermes 编排 | 5 |

## 四、包级循环依赖（双向 import）

| 包 A | 包 B | A→B | B→A |
|---|---|---|---|
| `backend/app` | `backend/app/api/v1/routes` | 1 | 8 |
| `backend/app/api/v1/admin_bff` | `backend/app/services` | 4 | 1 |
| `backend/app/core` | `backend/app/db` | 1 | 1 |
| `backend/app/core` | `backend/app/models` | 11 | 89 |
| `backend/app/core` | `backend/app/repositories` | 2 | 2 |
| `backend/app/core` | `backend/app/services` | 5 | 114 |
| `backend/app/geo_engine` | `backend/app/services` | 1 | 1 |
| `backend/app/repositories` | `backend/app/services` | 1 | 7 |
| `backend/app/services` | `backend/app/services/publish_workers/dual_line.py` | 2 | 1 |
| `backend/app/services` | `backend/app/services/publish_workers/tier_router.py` | 5 | 1 |

## 五、被引用最多的文件（Top 30）

| 文件 | 被 import 次数 |
|---|---|
| `backend/app/core/database.py` | 212 |
| `backend/app/models/user.py` | 195 |
| `backend/app/core/response.py` | 187 |
| `backend/app/core/config.py` | 180 |
| `backend/app/core/security.py` | 169 |
| `backend/app/db/session.py` | 113 |
| `backend/app/models/tenant.py` | 106 |
| `backend/app/models/content.py` | 64 |
| `backend/app/core/cache.py` | 53 |
| `backend/app/models/inquiry.py` | 35 |
| `backend/app/schemas/hermes_orchestration.py` | 29 |
| `backend/app/core/admin_auth.py` | 28 |
| `backend/app/models/product.py` | 25 |
| `backend/app/core/no_fake_delivery.py` | 22 |
| `backend/app/core/logging.py` | 18 |
| `backend/app/models/payment.py` | 18 |
| `backend/app/models/content_master.py` | 17 |
| `backend/app/services/tenant_scenario_service.py` | 15 |
| `backend/app/models/deerflow_job.py` | 15 |
| `backend/app/models/ai_config.py` | 15 |
| `backend/app/models/seo.py` | 15 |
| `backend/app/services/ubrain/tenant_memory_service.py` | 14 |
| `backend/app/services/hermes/maintenance_constitution.py` | 14 |
| `backend/app/services/ai_invocation_service.py` | 13 |
| `backend/app/services/hermes/brand_guard.py` | 12 |
| `backend/app/domains/base.py` | 12 |
| `backend/app/models/media_factory.py` | 12 |
| `backend/app/core/tenant_access.py` | 11 |
| `backend/app/orchestration/interfaces.py` | 11 |
| `backend/app/services/ai_engine.py` | 10 |

## 六、引用他人最多的文件（Top 30）

| 文件 | import 次数 |
|---|---|
| `backend/app/api/v1/super_admin/__init__.py` | 25 |
| `backend/app/api/v1/routes/foreign_trade.py` | 18 |
| `backend/app/main.py` | 17 |
| `backend/app/api/v1/routes/auth.py` | 16 |
| `backend/app/api/v1/routes/cross_border.py` | 15 |
| `backend/app/api/v1/seo/__init__.py` | 15 |
| `backend/app/api/v1/routes/app_bff.py` | 14 |
| `backend/app/api/v1/routes/media_factory.py` | 14 |
| `backend/app/api/v1/routes/ops_jobs.py` | 14 |
| `backend/app/api/v1/routes/ubrain.py` | 14 |
| `backend/app/api/v1/routes/video_publish.py` | 14 |
| `backend/app/api/v1/routes/client.py` | 13 |
| `backend/app/api/v1/routes/hermes.py` | 13 |
| `backend/app/api/v1/seo/dashboard.py` | 12 |
| `backend/app/api/v1/super_admin/ai_config.py` | 12 |
| `backend/app/services/cross_border/video_dub_service.py` | 12 |
| `backend/app/api/v1/routes/ubrain_commercial_os.py` | 11 |
| `backend/app/api/v1/super_admin/aggregation.py` | 11 |
| `backend/app/api/v1/super_admin/auth.py` | 11 |
| `backend/app/api/v1/routes/content_master.py` | 10 |
| `backend/app/api/v1/routes/founder_ops.py` | 10 |
| `backend/app/api/v1/routes/growth_tools.py` | 10 |
| `backend/app/api/v1/routes/system.py` | 10 |
| `backend/app/api/v1/routes/tenants.py` | 10 |
| `backend/app/api/v1/routes/trade_intel.py` | 10 |
| `backend/app/api/v1/routes/wangcai_marketplace.py` | 10 |
| `backend/app/schemas/__init__.py` | 10 |
| `backend/app/services/media_factory_service.py` | 10 |
| `backend/app/services/media_publish_service.py` | 10 |
| `backend/app/services/ubrain/orchestrator.py` | 10 |

## 七、未解析到的 import 目标（Top 20）

| 目标路径 | 引用次数 | 说明 |
|---|---|---|
| `@/components/youding` | 585 | 相对导入/包级 import/解析截断 |
| `@/utils/api` | 531 | 相对导入/包级 import/解析截断 |
| `@/api` | 118 | 相对导入/包级 import/解析截断 |
| `@/stores/uiPreferences` | 88 | 相对导入/包级 import/解析截断 |
| `@/components/common/SkeletonCard.vue` | 84 | 相对导入/包级 import/解析截断 |
| `@/composables/useBoardDetailDrawer` | 73 | 相对导入/包级 import/解析截断 |
| `admin/src//core.py` | 63 | 相对导入/包级 import/解析截断 |
| `@/utils/apiError` | 57 | 相对导入/包级 import/解析截断 |
| `@/stores/auth` | 52 | 相对导入/包级 import/解析截断 |
| `@/composables/useYoudingTableBridge` | 37 | 相对导入/包级 import/解析截断 |
| `@/composables/useModuleTabSync` | 26 | 相对导入/包级 import/解析截断 |
| `@/utils/ydModal` | 25 | 相对导入/包级 import/解析截断 |
| `@/utils/uiDisplayLabels` | 24 | 相对导入/包级 import/解析截断 |
| `@/api/cross-border` | 23 | 相对导入/包级 import/解析截断 |
| `@/types/sales` | 21 | 相对导入/包级 import/解析截断 |
| `@/composables/useAdminWorkspace` | 20 | 相对导入/包级 import/解析截断 |
| `@/utils/sessionAuth` | 19 | 相对导入/包级 import/解析截断 |
| `@/api/oauth` | 18 | 相对导入/包级 import/解析截断 |
| `@/constants/roleShellLock` | 18 | 相对导入/包级 import/解析截断 |
| `@/constants/stubVisibility` | 18 | 相对导入/包级 import/解析截断 |

## 八、与昨天审计的对照

- 昨天 `asset_audit_scan.py` 覆盖 45,350 个源码文件（跨 worktree + _external + docs + tools + 技能包等）。
- 本次 `code_atlas_gen.py` 分析 4,608 个核心源码文件（含 `_external/aionui`），深入抽取 import、路由、表名。
- 两者口径不同：前者重「规模/完成度标记」，后者重「模块关系」。互补。

## 九、局限与下一步

1. 函数级调用链未抽取（需要 AST 遍历 Call 节点或运行时 profiling）。
2. TypeScript/Vue 的组件引用、事件总线、pinia store 调用未完全解析。
3. 外部子系统（Trade AI / GoodJob）在 `_external/` 中，本次只分析了其内部结构，与主仓的 adapter 关系需单独桥接。

*报告生成时间：2026-09-11T03:40:58.077505+00:00*