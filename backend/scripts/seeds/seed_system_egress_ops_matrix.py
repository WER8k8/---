# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""系统配置、出口静态IP池、MCP工具、流水线调度、多平台运维与全链闭环种子数据填充脚本。

覆盖 45+ 运维与业务支撑表，将全库数据密度推升至 90%~95%：
1. system_config, platform_configs, tenant_capability_toggles, tenant_ai_provider_configs, cc_switch_configs
2. egress_endpoints, egress_cost_records, egress_provision_jobs, egress_pool_replenish_jobs
3. browser_profiles, device_fingerprints, app_devices, credentials, credential_grants
4. mcp_servers, mcp_tools, plugins, plugin_versions
5. n8n_workflows, pipeline_runs, pipeline_steps, step_evidence, review_tasks
6. notifications, alert_rules, alert_events, geo_alerts, geo_alert_rules, geo_alert_histories
7. super_admin_login_logs, user_status, feishu_bindings, feishu_message_logs, third_party_logins
8. campaign_recipients, campaign_events, email_verifications, email_tracking_events
9. ab_tests, ab_test_variants, ab_test_events, ab_test_conversions
10. translation_tasks, translation_records
11. growth_agent_runs, growth_keyword_entries, site_analytics_events, analytics_events, site_audits
12. reviews, release_guards, skill_performance, visibility_scores, inclusion_status
13. merchant_profiles, platform_survival_ledger_entries, platform_tenant_origins, international_crawl_logs, data_source_providers, competitor_mentions, engagement_records, push_events, ssl_certificates, building_material_specs
"""
from __future__ import annotations

import datetime
import io
import json
import sys
import uuid

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import text
from app.core.database import SessionLocal

NOW = datetime.datetime.now(datetime.timezone.utc)


def run_seeding() -> None:
    db = SessionLocal()
    try:
        print("🌱 开始填充 [系统底座 / 出口代理 / MCP / 观测流水线 / 运维大矩阵] 数据集...")

        # 0. 获取基础依赖实体
        tenants = db.execute(text("SELECT id, name FROM tenants LIMIT 5")).fetchall()
        users = db.execute(text("SELECT id, username FROM users LIMIT 5")).fetchall()
        platforms = db.execute(text("SELECT id, name FROM platforms LIMIT 5")).fetchall()
        accounts = db.execute(text("SELECT id, account_name FROM platform_accounts LIMIT 5")).fetchall()
        campaigns = db.execute(text("SELECT id, name FROM campaigns LIMIT 5")).fetchall()
        prospect_leads = db.execute(text("SELECT id, company_name FROM prospect_leads LIMIT 5")).fetchall()
        products = db.execute(text("SELECT id, name FROM products LIMIT 5")).fetchall()
        target_sites = db.execute(text("SELECT id, name FROM international_target_sites LIMIT 5")).fetchall()
        publish_tasks = db.execute(text("SELECT id FROM publish_tasks LIMIT 5")).fetchall()
        ai_tasks = db.execute(text("SELECT id FROM ai_tasks LIMIT 5")).fetchall()
        ai_queries = db.execute(text("SELECT id FROM ai_queries LIMIT 5")).fetchall()
        ai_query_runs = db.execute(text("SELECT id FROM ai_query_runs LIMIT 5")).fetchall()
        nurture_cycles = db.execute(text("SELECT id FROM nurture_cycles LIMIT 5")).fetchall()

        if not tenants or not users:
            print("⚠️ 未找到基础 tenants 或 users")
            return

        t_id = tenants[0][0]
        u_id = users[0][0]
        plat_id = platforms[0][0] if platforms else None
        acc_id = accounts[0][0] if accounts else None
        camp_id = campaigns[0][0] if campaigns else None
        lead_id = prospect_leads[0][0] if prospect_leads else None
        prod_id = products[0][0] if products else None
        site_id = target_sites[0][0] if target_sites else None
        pub_task_id = publish_tasks[0][0] if publish_tasks else None
        ai_task_id = ai_tasks[0][0] if ai_tasks else None
        query_id = ai_queries[0][0] if ai_queries else None
        run_id = ai_query_runs[0][0] if ai_query_runs else None
        nc_id = nurture_cycles[0][0] if nurture_cycles else None

        # 1. system_config, platform_configs, tenant_capability_toggles, tenant_ai_provider_configs, cc_switch_configs
        db.execute(text("""
            INSERT INTO system_config (id, key, value, value_type, description, is_public, created_at, updated_at)
            VALUES (:id, 'site_brand_name', '优丁 YouDing Global B2B SaaS', 'string', '平台全局展示名称', true, :now, :now)
        """), {"id": uuid.uuid4(), "now": NOW})

        if plat_id:
            db.execute(text("""
                INSERT INTO platform_configs (id, platform_id, account_id, config_key, config_value, created_at, updated_at)
                VALUES (:id, :pid, :accid, 'max_concurrent_uploads', '3', :now, :now)
            """), {"id": uuid.uuid4(), "pid": plat_id, "accid": acc_id, "now": NOW})

        db.execute(text("""
            INSERT INTO tenant_capability_toggles (tenant_id, capability_type, capability_id, enabled, updated_at)
            VALUES (:tid, 'subsystem', :cid, true, :now)
        """), {"id": uuid.uuid4(), "tid": t_id, "cid": uuid.uuid4(), "now": NOW})

        db.execute(text("""
            INSERT INTO tenant_ai_provider_configs (id, tenant_id, user_id, name, provider_id, protocol, model_name, enabled, created_at, updated_at)
            VALUES (:id, :tid, :uid, '租户专有DeepSeek通道', 'deepseek', 'rest', 'deepseek-chat', true, :now, :now)
        """), {"id": uuid.uuid4(), "tid": t_id, "uid": u_id, "now": NOW})

        db.execute(text("""
            INSERT INTO cc_switch_configs (id, name, provider_type, base_url, is_active, created_at, updated_at)
            VALUES (:id, 'Cloudflare AIGateway Switch', 'cloudflare', 'https://gateway.ai.cloudflare.com/v1/youding', true, :now, :now)
        """), {"id": uuid.uuid4(), "now": NOW})
        print("✓ system_config, platform_configs, toggles, switch_configs 填充完成")

        # 2. egress_endpoints, egress_cost_records, egress_provision_jobs, egress_pool_replenish_jobs
        ep_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO egress_endpoints (id, region, host, port, provider, slot_status, tenant_id, label, renew_count, created_at, updated_at)
            VALUES (:id, 'SA-RUH', '185.120.45.88', 8080, 'iproyal', 'allocated', :tid, '沙特利雅得住宅专线', 0, :now, :now)
        """), {"id": ep_id, "tid": t_id, "now": NOW})

        db.execute(text("""
            INSERT INTO egress_cost_records (id, endpoint_id, provider, operation, quantity, unit_price_cents, total_price_cents, currency, created_at)
            VALUES (:id, :epid, 'iproyal', 'provision', 1, 800, 800, 'USD', :now)
        """), {"id": uuid.uuid4(), "epid": ep_id, "now": NOW})

        db.execute(text("""
            INSERT INTO egress_provision_jobs (id, tenant_id, endpoint_id, provider, region, country, status, attempts, created_at, updated_at)
            VALUES (:id, :tid, :epid, 'iproyal', 'SA-RUH', 'SA', 'completed', 1, :now, :now)
        """), {"id": uuid.uuid4(), "tid": t_id, "epid": ep_id, "now": NOW})

        db.execute(text("""
            INSERT INTO egress_pool_replenish_jobs (id, status, batch_size, endpoints_created, created_at)
            VALUES (:id, 'completed', 5, 5, :now)
        """), {"id": uuid.uuid4(), "now": NOW})
        print("✓ egress_endpoints, cost_records, provision_jobs, replenish_jobs 填充完成")

        # 3. browser_profiles, device_fingerprints, app_devices, credentials, credential_grants
        bp_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO browser_profiles (id, tenant_id, egress_endpoint_id, name, platform_account_id, created_at, updated_at)
            VALUES (:id, :tid, :epid, '利雅得社媒指纹环境 (Chrome 122 / Win11)', :accid, :now, :now)
        """), {"id": bp_id, "tid": t_id, "epid": ep_id, "accid": acc_id, "now": NOW})

        db.execute(text("""
            INSERT INTO device_fingerprints (id, user_id, fingerprint_hash, device_info, first_seen_at, last_seen_at)
            VALUES (:id, :uid, 'fp_sha256_9a8b7c6d5e4f3a2b', '{\"browser\": \"Chrome\", \"os\": \"Windows 11\"}', :now, :now)
        """), {"id": uuid.uuid4(), "uid": u_id, "now": NOW})

        db.execute(text("""
            INSERT INTO app_devices (id, user_id, tenant_id, device_token, platform, created_at, updated_at)
            VALUES (:id, :uid_str, :tid_str, 'fcm_token_device_youding_2026', 'android', :now, :now)
        """), {"id": uuid.uuid4(), "uid_str": str(u_id), "tid_str": str(t_id), "now": NOW})

        cred_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO credentials (id, tenant_id, owner_type, owner_id, connection_type, connection_id, artifact_type, name, ciphertext, aad_fingerprint, crypto_backend, key_version, status, created_at, updated_at)
            VALUES (:id, :tid_str, 'tenant', :tid_str, 'whatsapp', 'wa_01', 'api_key', 'WhatsApp Business API Key', 'enc:v1:aes-gcm:sample', 'aad:01', 'aes_gcm', 1, 'active', :now, :now)
        """), {"id": cred_id, "tid_str": str(t_id), "now": NOW})

        db.execute(text("""
            INSERT INTO credential_grants (id, tenant_id, credential_id, grantee_type, grantee_id, granted_at, status)
            VALUES (:id, :tid_str, :cid_str, 'agent', 'trade_ai_agent', :now, 'active')
        """), {"id": uuid.uuid4(), "tid_str": str(t_id), "cid_str": str(cred_id), "now": NOW})
        print("✓ browser_profiles, device_fingerprints, app_devices, credentials 填充完成")

        # 4. mcp_servers, mcp_tools, plugins, plugin_versions
        mcp_srv_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO mcp_servers (id, tenant_id, name, status, stage, allow_insecure_loopback, authentication, max_tools, created_at, updated_at)
            VALUES (:id, :tid, 'Obsidian Knowledge Vault MCP', 'healthy', 'available', false, 'api_token', 20, :now, :now)
        """), {"id": mcp_srv_id, "tid": t_id, "now": NOW})

        db.execute(text("""
            INSERT INTO mcp_tools (id, server_id, name, permission, enabled, created_at)
            VALUES (:id, :sid, 'query_trade_kb', 'read', true, :now)
        """), {"id": uuid.uuid4(), "sid": mcp_srv_id, "now": NOW})

        plug_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO plugins (id, tenant_id, name, current_version, status, created_at, updated_at)
            VALUES (:id, :tid, 'GoodJob WhatsApp Translation Bridge', '1.2.0', 'active', :now, :now)
        """), {"id": plug_id, "tid": t_id, "now": NOW})

        db.execute(text("""
            INSERT INTO plugin_versions (id, plugin_id, version, status, created_at)
            VALUES (:id, :pid, '1.2.0', 'released', :now)
        """), {"id": uuid.uuid4(), "pid": plug_id, "now": NOW})
        print("✓ mcp_servers, mcp_tools, plugins, plugin_versions 填充完成")

        # 5. n8n_workflows, pipeline_runs, pipeline_steps, step_evidence, review_tasks
        db.execute(text("""
            INSERT INTO n8n_workflows (id, tenant_id, workflow_id, name, endpoint_url, enabled, created_at, updated_at)
            VALUES (:id, :tid, 'wf_site_publish_hook', '独立站一键分发与通知流', 'http://127.0.0.1:5678/webhook/site-publish', true, :now, :now)
        """), {"id": uuid.uuid4(), "tid": t_id, "now": NOW})

        pipe_run_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO pipeline_runs (id, tenant_id, pipeline_type, source_task_id, status, budget_used, retry_count, created_at, updated_at)
            VALUES (:id, :tid, 'multi_channel', :atid, 'distributing', 0.045, 0, :now, :now)
        """), {"id": pipe_run_id, "tid": t_id, "atid": ai_task_id, "now": NOW})

        pipe_step_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO pipeline_steps (id, run_id, seq, step_type, status, retry_count, started_at)
            VALUES (:id, :rid, 1, 'pi_sanctions_and_risk_screen', 'done', 0, :now)
        """), {"id": pipe_step_id, "rid": pipe_run_id, "now": NOW})

        db.execute(text("""
            INSERT INTO step_evidence (id, tenant_id, step_id, claim, evidence_type, verified, created_at)
            VALUES (:id, :tid, :sid, 'OFAC and EU Sanctions Clear', 'url_check', true, :now)
        """), {"id": uuid.uuid4(), "tid": t_id, "sid": pipe_step_id, "now": NOW})

        db.execute(text("""
            INSERT INTO review_tasks (id, tenant_id, run_id, step_id, decision, comments, created_at)
            VALUES (:id, :tid, :rid, :sid, 'approved', 'PI and Credit checked. Approved for production dispatch.', :now)
        """), {"id": uuid.uuid4(), "tid": t_id, "rid": pipe_run_id, "sid": pipe_step_id, "now": NOW})
        print("✓ n8n_workflows, pipeline_runs, pipeline_steps, step_evidence, review_tasks 填充完成")

        # 6. notifications, alert_rules, alert_events, geo_alerts, geo_alert_rules, geo_alert_histories
        db.execute(text("""
            INSERT INTO notifications (id, user_id, title, content, type, is_read, created_at)
            VALUES (:id, :uid, '沙特利雅得 42,000平米工程定金已核销', '买家 Al-Hassan Contracting 已汇出首期定金 35,000 USD，单据已归档。', 'trade_event', false, :now)
        """), {"id": uuid.uuid4(), "uid": u_id, "now": NOW})

        rule_alert_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO alert_rules (id, name, category, metric_key, operator, threshold, enabled, created_at, updated_at)
            VALUES (:id, 'AI Token 预算消耗超限预警', 'billing', 'token_wallet_burn_rate', 'gt', 500000.0, true, :now, :now)
        """), {"id": rule_alert_id, "now": NOW})

        db.execute(text("""
            INSERT INTO alert_events (id, rule_id, rule_name, category, level, title, status, created_at)
            VALUES (:id, :rid, 'AI Token 预算消耗超限预警', 'billing', 'info', '租户月度Token使用率达到 60%', 'resolved', :now)
        """), {"id": uuid.uuid4(), "rid": rule_alert_id, "now": NOW})

        geo_rule_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO geo_alert_rules (id, name, alert_type, severity, enabled, created_at, updated_at)
            VALUES (:id, '海湾大区建材需求突增监测', 'demand_surge', 'medium', true, :now, :now)
        """), {"id": geo_rule_id, "now": NOW})

        geo_alt_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO geo_alerts (id, rule_id, alert_type, severity, title, description, created_at, updated_at)
            VALUES (:id, :grid, 'demand_surge', 'medium', '沙特利雅得近7天岩棉板搜索量环比激增 145%', '可能与新公布的商业园区幕墙招标有关，建议提高开发信外发频率', :now, :now)
        """), {"id": geo_alt_id, "grid": geo_rule_id, "now": NOW})

        db.execute(text("""
            INSERT INTO geo_alert_histories (id, alert_id, action_type, action_notes, created_at)
            VALUES (:id, :gaid, 'auto_acknowledged', 'Dispatched lead campaign to Arabtec & SBG.', :now)
        """), {"id": uuid.uuid4(), "gaid": geo_alt_id, "now": NOW})
        print("✓ notifications, alert_rules, geo_alerts, histories 填充完成")

        # 7. super_admin_login_logs, user_status, feishu_bindings, feishu_message_logs, third_party_logins
        db.execute(text("""
            INSERT INTO super_admin_login_logs (id, user_id, username, ip_address, user_agent, success, created_at)
            VALUES (:id, :uid, 'admin', '127.0.0.1', 'Mozilla/5.0 Windows NT 10.0', true, :now)
        """), {"id": uuid.uuid4(), "uid": u_id, "now": NOW})

        db.execute(text("""
            INSERT INTO user_status (user_id, status, last_active_at, device_type)
            VALUES (:uid, 'online', :now, 'desktop')
            ON CONFLICT (user_id) DO UPDATE SET status='online'
        """), {"uid": u_id, "now": NOW})

        db.execute(text("""
            INSERT INTO feishu_bindings (id, feishu_open_id, feishu_user_name, bound_user_id, bound_username, is_active, created_at, updated_at)
            VALUES (:id, 'ou_youding_feishu_001', '吕博旺', :uid_str, 'admin', true, :now, :now)
        """), {"id": uuid.uuid4(), "uid_str": str(u_id), "now": NOW})

        db.execute(text("""
            INSERT INTO feishu_message_logs (id, feishu_open_id, message_type, content, direction, status, created_at)
            VALUES (:id, 'ou_youding_feishu_001', 'card', '【定金到账通知】沙特订单已成功核销', 'outgoing', 'sent', :now)
        """), {"id": uuid.uuid4(), "now": NOW})

        db.execute(text("""
            INSERT INTO third_party_logins (id, user_id, provider, provider_id, created_at, updated_at)
            VALUES (:id, :uid, 'google', 'oauth2_google_admin_2026', :now, :now)
        """), {"id": uuid.uuid4(), "uid": u_id, "now": NOW})
        print("✓ super_admin_login_logs, user_status, feishu, third_party_logins 填充完成")

        # 8. campaign_recipients, campaign_events, email_verifications, email_tracking_events
        if camp_id:
            recip_id = uuid.uuid4()
            db.execute(text("""
                INSERT INTO campaign_recipients (id, campaign_id, email, status, created_at, updated_at)
                VALUES (:id, :cid, 'procurement@binladin-group.sa', 'sent', :now, :now)
            """), {"id": recip_id, "cid": camp_id, "now": NOW})

            db.execute(text("""
                INSERT INTO campaign_events (id, campaign_id, recipient_id, event_type, occurred_at)
                VALUES (:id, :cid, :rid, 'email_delivered', :now)
            """), {"id": uuid.uuid4(), "cid": camp_id, "rid": recip_id, "now": NOW})

        db.execute(text("""
            INSERT INTO email_verifications (id, email, code, expires_at, used, created_at)
            VALUES (:id, 'admin@youding-materials.com', '882910', :exp, true, :now)
        """), {"id": uuid.uuid4(), "exp": NOW + datetime.timedelta(minutes=15), "now": NOW})

        if lead_id:
            db.execute(text("""
                INSERT INTO email_tracking_events (id, message_id, lead_id, tenant_id, user_id, event_type, created_at)
                VALUES (:id, 'msg_wa_tracked_001', :lid, :tid, :uid, 'OPEN', :now)
            """), {"id": uuid.uuid4(), "lid": lead_id, "tid": t_id, "uid": u_id, "now": NOW})
        print("✓ campaign_recipients, events, email_verifications, tracking 填充完成")

        # 9. ab_tests, ab_test_variants, ab_test_events, ab_test_conversions
        ab_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO ab_tests (id, name, target_url, variants_config, created_at, updated_at, created_by)
            VALUES (:id, '中东落地页询盘转化按钮文案测试', 'https://youding-materials.com/products/rockwool', '{\"variants\": [\"A\", \"B\"]}', :now, :now, :uid)
        """), {"id": ab_id, "now": NOW, "uid": u_id})

        var_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO ab_test_variants (id, experiment_id, variant_id, name, is_control, created_at)
            VALUES (:id, :expid, 'variant_b', '立即获取沙特专供工程报价 (FOB/CIF)', false, :now)
        """), {"id": var_id, "expid": ab_id, "now": NOW})

        db.execute(text("""
            INSERT INTO ab_test_events (id, experiment_id, session_id, user_id, variant_id, event_type, created_at)
            VALUES (:id, :expid, 'sess_ab_001', :uid, 'variant_b', 'click_cta', :now)
        """), {"id": uuid.uuid4(), "expid": ab_id, "uid": u_id, "now": NOW})

        db.execute(text("""
            INSERT INTO ab_test_conversions (id, experiment_id, variant_id, session_id, user_id, conversion_type, conversion_value, created_at)
            VALUES (:id, :expid, 'variant_b', 'sess_ab_001', :uid, 'rfq_submission', 1250.0, :now)
        """), {"id": uuid.uuid4(), "expid": ab_id, "uid": u_id, "now": NOW})
        print("✓ ab_tests, variants, events, conversions 填充完成")

        # 10. translation_tasks, translation_records
        trans_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO translation_tasks (id, name, source_lang, target_lang, total_items, completed_items, status, created_at, updated_at)
            VALUES (:id, '沙特商会技术规格书阿文翻译任务', 'en', 'ar', 15, 15, 'completed', :now, :now)
        """), {"id": trans_id, "now": NOW})

        db.execute(text("""
            INSERT INTO translation_records (id, task_id, source_text, translated_text, source_lang, target_lang, status, created_at)
            VALUES (:id, :tid, 'Rockwool panel non-combustible core Class A1', 'قلب لوح الصوف الصخري غير قابل للاحتراق فئة A1', 'en', 'ar', 'completed', :now)
        """), {"id": uuid.uuid4(), "tid": trans_id, "now": NOW})
        print("✓ translation_tasks, translation_records 填充完成")

        # 11. growth_agent_runs, growth_keyword_entries, site_analytics_events, analytics_events, site_audits
        db.execute(text("""
            INSERT INTO growth_agent_runs (id, tenant_id, workflow, goal, status, progress, created_at, updated_at)
            VALUES (:id, :tid, 'saudi_market_penetration', 'Reach 50 qualified contractors in Riyadh', 'completed', 100, :now, :now)
        """), {"id": uuid.uuid4(), "tid": t_id, "now": NOW})

        db.execute(text("""
            INSERT INTO growth_keyword_entries (id, tenant_id, keyword, word_class, search_volume, is_active, created_at, updated_at)
            VALUES (:id, :tid, 'exterior insulation composite panels manufacturer', 'commercial', 8500, true, :now, :now)
        """), {"id": uuid.uuid4(), "tid": t_id, "now": NOW})

        db.execute(text("""
            INSERT INTO site_analytics_events (id, tenant_id, session_id, event_type, page_path, created_at)
            VALUES (:id, :tid, 'sess_web_882', 'view_product_spec', '/products/youding-rockwool-board', :now)
        """), {"id": uuid.uuid4(), "tid": t_id, "now": NOW})

        if prod_id:
            db.execute(text("""
                INSERT INTO analytics_events (id, merchant_id, event_type, product_id, visitor_country, created_at)
                VALUES (:id, :uid, 'inquiry_click', :pid, 'SA', :now)
            """), {"id": uuid.uuid4(), "uid": u_id, "pid": prod_id, "now": NOW})

        db.execute(text("""
            INSERT INTO site_audits (id, url, status, audit_type, score, created_at)
            VALUES (:id, 'https://youding-materials.com', 'completed', 'lighthouse_seo', 98.0, :now)
        """), {"id": uuid.uuid4(), "now": NOW})
        print("✓ growth_agent_runs, keywords, site_analytics, audits 填充完成")

        # 12. reviews, release_guards, skill_performance, visibility_scores, inclusion_status
        if prod_id:
            db.execute(text("""
                INSERT INTO reviews (id, user_id, product_id, rating, content, status, created_at, updated_at)
                VALUES (:id, :uid, :pid, 5.0, 'Excellent high-density rockwool panels delivered on time to Dammam port.', 'approved', :now, :now)
            """), {"id": uuid.uuid4(), "uid": u_id, "pid": prod_id, "now": NOW})

        db.execute(text("""
            INSERT INTO release_guards (id, version, guard_type, status, metrics, created_at)
            VALUES (:id, 'v2.6.0', 'l_pro_release_gate', 'passed', '{\"unit_tests\": 866, \"pass_rate\": 1.0}', :now)
        """), {"id": uuid.uuid4(), "now": NOW})

        db.execute(text("""
            INSERT INTO skill_performance (id, tenant_id, skill_id, skill_version, window_start, window_end, total_invocations, success_count, failure_count, success_rate, avg_duration_ms, avg_cost, total_tokens, created_at, updated_at)
            VALUES (:id, :tid, 'customer-research', '1.0.0', :now, :now, 85, 82, 3, 0.964, 1200, 0.012, 142000, :now, :now)
        """), {"id": uuid.uuid4(), "tid": t_id, "now": NOW})

        db.execute(text("""
            INSERT INTO visibility_scores (id, entity, score, mention_count, recommendation_count, citation_count, query_coverage, competitor_count, computed_at)
            VALUES (:id, 'YouDing', 94, 150, 85, 42, 92, 4, :now)
        """), {"id": uuid.uuid4(), "now": NOW})

        if pub_task_id:
            db.execute(text("""
                INSERT INTO inclusion_status (id, task_id, url, keyword, is_included, ranking, search_engine, created_at, updated_at)
                VALUES (:id, :tid, 'https://youding-materials.com/products/rockwool-board', 'rockwool board manufacturer china', true, 3, 'google', :now, :now)
            """), {"id": uuid.uuid4(), "tid": pub_task_id, "now": NOW})
        print("✓ reviews, release_guards, skill_performance, visibility, inclusion 填充完成")

        # 13. merchant_profiles, platform_survival_ledger_entries, platform_tenant_origins, international_crawl_logs, data_source_providers, competitor_mentions, engagement_records, push_events, ssl_certificates, building_material_specs
        db.execute(text("""
            INSERT INTO merchant_profiles (id, user_id, company_name, country, city, verified, created_at, updated_at)
            VALUES (:id, :uid, '优丁全球外贸建材供应链', 'China', 'Shijiazhuang', true, :now, :now)
        """), {"id": uuid.uuid4(), "uid": u_id, "now": NOW})

        db.execute(text("""
            INSERT INTO platform_survival_ledger_entries (id, wallet_scope, entry_type, channel, amount_minor, currency, amount_base_minor, base_currency, fx_rate_to_base, status, recorded_at, created_at)
            VALUES (:id, 'tenant_sub_wallet', 'credit', 'stripe', 480000, 'USD', 480000, 'USD', '1.0', 'settled', :now, :now)
        """), {"id": uuid.uuid4(), "now": NOW})

        if plat_id:
            db.execute(text("""
                INSERT INTO platform_tenant_origins (id, tenant_id, platform_id, source, platform_name, is_new_platform, browser_profile_id, created_at)
                VALUES (:id, :tid, :pid, 'organic_nurture', 'LinkedIn', false, :bpid, :now)
            """), {"id": uuid.uuid4(), "tid": t_id, "pid": plat_id, "bpid": bp_id, "now": NOW})

        if site_id:
            db.execute(text("""
                INSERT INTO international_crawl_logs (id, site_id, status, pages_crawled, inquiries_found, created_at)
                VALUES (:id, :sid, 'success', 24, 6, :now)
            """), {"id": uuid.uuid4(), "sid": site_id, "now": NOW})

        db.execute(text("""
            INSERT INTO data_source_providers (id, name, data_class, license_basis, tos_verified, review_status, created_at, updated_at)
            VALUES (:id, 'Global Trade Atlas Customs Feed', 'public_corporate', 'licensed_service', true, 'approved', :now, :now)
        """), {"id": uuid.uuid4(), "now": NOW})

        if query_id and run_id:
            db.execute(text("""
                INSERT INTO competitor_mentions (id, query_id, run_id, competitor, mentioned, recommended, occurred_at)
                VALUES (:id, :qid, :rid, 'Rockwool International A/S', 'true', 'true', :now)
            """), {"id": uuid.uuid4(), "qid": query_id, "rid": run_id, "now": NOW})

        db.execute(text("""
            INSERT INTO engagement_records (id, tenant_id, platform, action_type, status, nurture_cycle_id, created_at)
            VALUES (:id, :tid_str, 'LinkedIn', 'invite_sent', 'success', :ncid, :now)
        """), {"id": uuid.uuid4(), "tid_str": str(t_id), "ncid": nc_id, "now": NOW})

        naive_now = datetime.datetime.utcnow()
        db.execute(text("""
            INSERT INTO push_events (id, tenant_id, event_type, ref_type, ref_id, channel, title, body, status, retry_count, created_at, updated_at)
            VALUES (:id, :tid_str, 'order_milestone', 'order', 'ORD-2026-001', 'websocket', '沙特订单生产完成', '一体板已装箱打托，等待海运验货', 'delivered', 0, :now, :now)
        """), {"id": uuid.uuid4(), "tid_str": str(t_id), "now": naive_now})

        db.execute(text("""
            INSERT INTO ssl_certificates (id, tenant_id, domain, is_active, created_at, updated_at)
            VALUES (:id, :tid, 'youding-materials.com', 'true', :now, :now)
        """), {"id": uuid.uuid4(), "tid": t_id, "now": NOW})

        db.execute(text("""
            INSERT INTO building_material_specs (product_id, spec_key, spec_value, metric_unit, created_at, updated_at)
            VALUES (1, 'thermal_conductivity', 0.038, 'W/(m·K)', :now, :now)
        """), {"now": naive_now})
        print("✓ merchant_profiles, survival_ledger, origins, crawl_logs, competitors, building_material_specs 填充完成")

        db.commit()
        print("🎉 Batch 5 [系统底座/出口代理/MCP/观测流水线/运维大矩阵] 种子数据全部提交成功！")
    except Exception as exc:
        db.rollback()
        print(f"❌ 填充失败: {exc}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seeding()
