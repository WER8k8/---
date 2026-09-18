# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""AI 大模型、UBrain中枢、即时会话、合规风控与莫比乌斯进化总谱种子数据填充脚本。

覆盖表：
1. ai_model_providers, ai_model_configs, model_capabilities, llms_config, ai_generation_configs, ai_templates, ai_usage_logs
2. knowledge_bases, ai_knowledge_base
3. ai_queries, ai_query_runs, ai_citations, ai_mentions, ai_recommendations, ai_optimization_logs
4. ai_chat_sessions, ai_chat_messages, chat_sessions, chat_messages, im_sessions, im_messages
5. ubrain_decision_records, ubrain_execution_records, ubrain_feedback_records, ubrain_feedback_snapshots
6. wangcai_sessions, wangcai_qa_log, intent_engine_runs
7. compliance_rules, compliance_scan_results, compliance_violations, ad_law_keywords, risk_control_configs
8. evolution_experiences, evolution_skill_versions, evolution_sop_versions, evolution_approvals, evolution_canary_routes
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
        print("🌱 开始填充 [AI大模型 / UBrain / 聊天会话 / 合规风控 / 莫比乌斯自进化] 数据集...")

        # 0. 获取基础租户、用户、产品、企业画像、平台
        users = db.execute(text("SELECT id, username FROM users LIMIT 5")).fetchall()
        tenants = db.execute(text("SELECT id, name FROM tenants LIMIT 5")).fetchall()
        prods = db.execute(text("SELECT id, name FROM products LIMIT 5")).fetchall()
        companies = db.execute(text("SELECT id, name FROM companies LIMIT 5")).fetchall()
        platforms = db.execute(text("SELECT id, name FROM platforms LIMIT 5")).fetchall()

        if not users or not tenants:
            print("⚠️ 未找到基础 users 或 tenants")
            return

        u_id = users[0][0]
        u_id2 = users[1][0] if len(users) > 1 else u_id
        t_id = tenants[0][0]
        prod_id = prods[0][0] if prods else None
        comp_id = companies[0][0] if companies else None
        plat_id = platforms[0][0] if platforms else None

        # 1. ai_model_providers, ai_model_configs, model_capabilities, llms_config, ai_generation_configs, ai_templates, ai_usage_logs
        prov_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO ai_model_providers (id, name, provider_type, api_key, base_url, default_model, is_active, is_default, description, created_at, updated_at)
            VALUES (:id, 'DeepSeek Official', 'deepseek', 'sk-dsh-encrypted-token', 'https://api.deepseek.com/v1', 'deepseek-reasoner', true, true, 'DeepSeek R1 reasoning and V3 general model upstream', :now, :now)
        """), {"id": prov_id, "now": NOW})

        cfg_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO ai_model_configs (id, provider_id, model_name, model_type, temperature, max_tokens, context_window, is_active, is_default, sort_order, created_at, updated_at)
            VALUES (:id, :pid, 'deepseek-reasoner', 'reasoning', '0.6', '8192', '64k', true, true, 1, :now, :now)
        """), {"id": cfg_id, "pid": prov_id, "now": NOW})

        db.execute(text("""
            INSERT INTO model_capabilities (id, tenant_id, provider, model_name, capability_tag, priority, cost_per_1k_input, cost_per_1k_output, max_tokens, is_active, created_at, updated_at)
            VALUES (:id, :tid, 'deepseek', 'deepseek-reasoner', 'l1_planning', 1, 0.001, 0.002, 65536, true, :now, :now)
        """), {"id": uuid.uuid4(), "tid": t_id, "now": NOW})

        db.execute(text("""
            INSERT INTO llms_config (id, section, content, is_active, version, created_at, updated_at)
            VALUES (:id, 'system_instruction_prompt', 'You are YouDing AI B2B Trade Engine. Always output verified trade terms and CE/ASTM compliant specifications.', true, 'v2.6', :now, :now)
        """), {"id": uuid.uuid4(), "now": NOW})

        db.execute(text("""
            INSERT INTO ai_generation_configs (id, config_name, model_name, max_tokens, temperature, creativity_level, similarity_threshold, compliance_check, created_at, updated_at)
            VALUES (:id, 'B2B_Technical_Spec_Writer', 'deepseek-reasoner', 4000, 0.3, 'low', 0.85, true, :now, :now)
        """), {"id": uuid.uuid4(), "now": NOW})

        db.execute(text("""
            INSERT INTO ai_templates (id, name, task_type, system_prompt, user_prompt_template, variables_json, default_params_json, is_active, sort_order, created_at, updated_at)
            VALUES (:id, 'CE认证合规检验提示词', 'compliance', 'Check for EN 13501-1 and ASTM standards.', 'Analyze the following text: {content}', '[\"content\"]', '{\"temperature\": 0.2}', true, 1, :now, :now)
        """), {"id": uuid.uuid4(), "now": NOW})

        db.execute(text("""
            INSERT INTO ai_usage_logs (id, provider_id, model_name, task_type, prompt_tokens, completion_tokens, total_tokens, cost, duration_ms, success, created_at)
            VALUES (:id, :pid, 'deepseek-reasoner', 'dag_planning', '1500', '3200', '4700', '0.0094', '1240', true, :now)
        """), {"id": uuid.uuid4(), "pid": prov_id, "now": NOW})
        print("✓ ai_model_providers, configs, capabilities, templates, usage_logs 填充完成")

        # 2. knowledge_bases, ai_knowledge_base
        kb_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO knowledge_bases (id, tenant_id, name, description, kb_type, source, doc_count, is_active, created_at, updated_at)
            VALUES (:id, :tid, '外墙保温工程技术标准与问答库', '包含EN 13501、ASTM E84、国标GB/T 25975检测规程与工程答疑', 'technical_specs', 'internal_docs', 25, true, :now, :now)
        """), {"id": kb_id, "tid": t_id, "now": NOW})

        db.execute(text("""
            INSERT INTO ai_knowledge_base (id, merchant_id, title, content, content_type, language, is_active, created_at, updated_at)
            VALUES (:id, :uid, '高密度岩棉板外墙抗风压计算准则', '根据JGJ 144-2019规程，风荷载标准值Wk应大于等于基本风压的1.5倍...', 'text', 'zh', true, :now, :now)
        """), {"id": uuid.uuid4(), "uid": u_id, "now": NOW})
        print("✓ knowledge_bases, ai_knowledge_base 填充完成")

        # 3. ai_queries, ai_query_runs, ai_citations, ai_mentions, ai_recommendations, ai_optimization_logs
        query_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO ai_queries (id, query, language, category, target_entity, active, created_at)
            VALUES (:id, 'Who are the best rockwool insulation board manufacturers in China?', 'en', 'b2b_trade', 'YouDing', 'true', :now)
        """), {"id": query_id, "now": NOW})

        run_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO ai_query_runs (id, query_id, engine, raw_answer, entity_appeared, recommended, position, run_at)
            VALUES (:id, :qid, 'perplexity', 'Top manufacturers include YouDing Materials, Rockwool China, and Beipeng...', 'true', 'true', 1, :now)
        """), {"id": run_id, "qid": query_id, "now": NOW})

        db.execute(text("""
            INSERT INTO ai_citations (id, run_id, entity, cited_url, cited_page, relevance_score, occurred_at)
            VALUES (:id, :rid, 'YouDing', 'https://youding-materials.com/products/rockwool-board', 'Rockwool Specs', 0.95, :now)
        """), {"id": uuid.uuid4(), "rid": run_id, "now": NOW})

        db.execute(text("""
            INSERT INTO ai_mentions (id, query_id, run_id, entity, mentioned, recommended, snippet, occurred_at)
            VALUES (:id, :qid, :rid, 'YouDing', 'true', 'true', 'YouDing provides high-density A1 fireproof rockwool with direct shipping to Middle East.', :now)
        """), {"id": uuid.uuid4(), "qid": query_id, "rid": run_id, "now": NOW})

        if prod_id:
            db.execute(text("""
                INSERT INTO ai_recommendations (id, user_id, product_id, score, reason, algorithm, created_at)
                VALUES (:id, :uid, :pid, 0.9450, 'High inquiry match for Middle East thermal insulation projects', 'collaborative_filtering_v2', :now)
            """), {"id": uuid.uuid4(), "uid": u_id, "pid": prod_id, "now": NOW})

        db.execute(text("""
            INSERT INTO ai_optimization_logs (id, resource_type, resource_id, optimization_type, score_before, score_after, created_at)
            VALUES (:id, 'product_description', 'rockwool-board', 'eeat_scoring', 72.0, 94.0, :now)
        """), {"id": uuid.uuid4(), "now": NOW})
        print("✓ ai_queries, runs, citations, mentions, recommendations, optimization_logs 填充完成")

        # 4. ai_chat_sessions, ai_chat_messages, chat_sessions, chat_messages, im_sessions, im_messages
        ai_chat_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO ai_chat_sessions (id, merchant_id, buyer_ip, buyer_country, buyer_language, buyer_email, session_status, message_count, ai_mode, created_at, updated_at)
            VALUES (:id, :uid, '84.235.92.11', 'SA', 'en', 'procurement@al-hassan.sa', 'active', 4, true, :now, :now)
        """), {"id": ai_chat_id, "uid": u_id, "now": NOW})

        db.execute(text("""
            INSERT INTO ai_chat_messages (id, session_id, role, content, language, tokens_used, created_at)
            VALUES (:id, :sid, 'user', 'Do you have CE certificate for 50mm rockwool panel?', 'en', 25, :now)
        """), {"id": uuid.uuid4(), "sid": ai_chat_id, "now": NOW})

        db.execute(text("""
            INSERT INTO ai_chat_messages (id, session_id, role, content, language, tokens_used, created_at)
            VALUES (:id, :sid, 'assistant', 'Yes, our 50mm rockwool panel is certified EN 13501-1 Class A2-s1,d0. I can provide the Declaration of Performance and test reports.', 'en', 45, :now)
        """), {"id": uuid.uuid4(), "sid": ai_chat_id, "now": NOW})

        cs_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO chat_sessions (id, user_id, session_name, model_used, total_tokens, status, created_at, updated_at)
            VALUES (:id, :uid, '沙特利雅得商业中心幕墙造价答疑', 'deepseek-reasoner', 2850, 'active', :now, :now)
        """), {"id": cs_id, "uid": u_id, "now": NOW})

        db.execute(text("""
            INSERT INTO chat_messages (id, session_id, role, content, tokens, model, created_at)
            VALUES (:id, :sid, 'user', '帮我测算利雅得 42,000 平米一体板所需的海运柜数和FOB总价。', 40, 'deepseek-reasoner', :now)
        """), {"id": uuid.uuid4(), "sid": cs_id, "now": NOW})

        # IM 站内即时沟通会话
        im_msg_id = f"msg_{uuid.uuid4().hex[:12]}"
        im_sess_id = f"sess_{uuid.uuid4().hex[:12]}"
        db.execute(text("""
            INSERT INTO im_messages (id, sender_id, receiver_id, content, message_type, is_read, created_at, updated_at)
            VALUES (:mid, :uid, :uid2, '你好，沙特客户已确认PI草案，请审核定金核销记录。', 'text', false, :now, :now)
        """), {"mid": im_msg_id, "uid": u_id, "uid2": u_id2, "now": NOW})

        db.execute(text("""
            INSERT INTO im_sessions (id, user1_id, user2_id, last_message_id, unread_count, created_at, updated_at)
            VALUES (:sid, :uid, :uid2, :mid, 1, :now, :now)
        """), {"sid": im_sess_id, "uid": u_id, "uid2": u_id2, "mid": im_msg_id, "now": NOW})
        print("✓ ai_chat_sessions, chat_sessions, im_sessions 填充完成")

        # 5. ubrain_decision_records, ubrain_execution_records, ubrain_feedback_records, ubrain_feedback_snapshots
        dec_id = f"dec_{uuid.uuid4().hex[:12]}"
        exec_id = f"exec_{uuid.uuid4().hex[:12]}"
        db.execute(text("""
            INSERT INTO ubrain_decision_records (id, decision_id, agent_tree_node_id, decision_type, confidence_score, tenant_id, user_id, created_at, updated_at)
            VALUES (:id, :did, 'node_trade_acquisition_officer', 'outbound_contact_dispatch', 0.94, :tid, :uid, :now, :now)
        """), {"id": uuid.uuid4(), "did": dec_id, "tid": t_id, "uid": u_id, "now": NOW})

        db.execute(text("""
            INSERT INTO ubrain_execution_records (id, execution_id, decision_id, status, latency_ms, tenant_id, user_id, created_at, updated_at)
            VALUES (:id, :eid, :did, 'succeeded', 840.5, :tid, :uid, :now, :now)
        """), {"id": uuid.uuid4(), "eid": exec_id, "did": dec_id, "tid": t_id, "uid": u_id, "now": NOW})

        db.execute(text("""
            INSERT INTO ubrain_feedback_records (id, execution_id, feedback_score, feedback_text, tenant_id, user_id, created_at, updated_at)
            VALUES (:id, :eid, 1.0, 'Buyer replied positively to cold email draft within 4 hours', :tid, :uid, :now, :now)
        """), {"id": uuid.uuid4(), "eid": exec_id, "tid": t_id, "uid": u_id, "now": NOW})

        db.execute(text("""
            INSERT INTO ubrain_feedback_snapshots (id, tenant_id, period_days, metrics_json, recommendations_json, created_at)
            VALUES (:id, :tid, 7, '{\"reply_rate\": 0.28, \"accuracy\": 0.94}', '{\"action\": \"boost_whatsapp_outreach_in_saudi\"}', :now)
        """), {"id": uuid.uuid4(), "tid": t_id, "now": NOW})
        print("✓ ubrain_decision, execution, feedback, snapshots 填充完成")

        # 6. wangcai_sessions, wangcai_qa_log, intent_engine_runs
        wc_sess_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO wangcai_sessions (id, tenant_id, visitor_ref, language, summary, turn_count, created_at)
            VALUES (:id, :tid, 'VIS-SA-8821', 'ar', '询盘咨询利雅得岩棉一体板海关税率与HS编码', 3, :now)
        """), {"id": wc_sess_id, "tid": t_id, "now": NOW})

        db.execute(text("""
            INSERT INTO wangcai_qa_log (id, tenant_id, session_id, role, intent, content, lead_converted, created_at)
            VALUES (:id, :tid, :sid, 'assistant', 'hs_code_lookup', '岩棉制品HS编码为 6806.10.00，沙特关税税率为 5%，需 SASO 认证。', true, :now)
        """), {"id": uuid.uuid4(), "tid": t_id, "sid": wc_sess_id, "now": NOW})

        if comp_id:
            db.execute(text("""
                INSERT INTO intent_engine_runs (id, company_id, intent_score, icp_score, account_score, run_at)
                VALUES (:id, :cid, 92, 95, 93, :now)
            """), {"id": uuid.uuid4(), "cid": comp_id, "now": NOW})
        print("✓ wangcai_sessions, qa_log, intent_engine_runs 填充完成")

        # 7. compliance_rules, compliance_scan_results, compliance_violations, ad_law_keywords, risk_control_configs
        rule_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO compliance_rules (id, rule_name, rule_type, keywords, severity, description, is_active, created_at, updated_at)
            VALUES (:id, '新广告法绝对化用语检测', 'ad_law', '[\"国家级\", \"第一品牌\", \"绝无仅有\", \"全网最低\"]', 'high', '拦截绝对化违规用语以符合市场监管标准', true, :now, :now)
        """), {"id": rule_id, "now": NOW})

        scan_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO compliance_scan_results (id, content_id, content_type, scan_status, total_issues, high_severity_count, scanned_at, created_at)
            VALUES (:id, 'rockwool-landing-v1', 'page', 'passed_clean', 0, 0, :now, :now)
        """), {"id": scan_id, "now": NOW})

        db.execute(text("""
            INSERT INTO compliance_violations (id, scan_result_id, rule_id, rule_name, rule_type, severity, matched_text, is_resolved, created_at)
            VALUES (:id, :sid, :rid, '新广告法绝对化用语检测', 'ad_law', 'medium', '顶级品质', true, :now)
        """), {"id": uuid.uuid4(), "sid": str(scan_id), "rid": str(rule_id), "now": NOW})

        db.execute(text("""
            INSERT INTO ad_law_keywords (id, keyword, category, severity, alternative, is_active, created_at, updated_at)
            VALUES (:id, '顶级', 'advertising_law', 'high', '高品质 / 优质', true, :now, :now)
        """), {"id": uuid.uuid4(), "now": NOW})

        if plat_id:
            db.execute(text("""
                INSERT INTO risk_control_configs (id, platform_id, daily_limit, interval_seconds, enabled, created_at, updated_at)
                VALUES (:id, :platid, 100, 300, true, :now, :now)
            """), {"id": uuid.uuid4(), "platid": plat_id, "now": NOW})
        print("✓ compliance_rules, scan_results, violations, ad_law, risk_control 填充完成")

        # 8. evolution_experiences, evolution_skill_versions, evolution_sop_versions, evolution_approvals, evolution_canary_routes
        exp_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO evolution_experiences (
                id, task_type, pattern_type, title, description, confidence, occurrence_count, applied, applied_at, stage, created_at, updated_at
            ) VALUES (
                :id, 'b2b_cold_email', 'middle_east_arabic_greeting', '沙特买家邮件前置伊斯兰商务礼貌语转化率提升34%', '在邮件首段使用正式标准商务问候语显著提高开信与回复率', 0.94, 88, true, :now, 'verified', :now, :now
            )
        """), {"id": exp_id, "now": NOW})

        sk_ver_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO evolution_skill_versions (
                id, skill_id, skill_name, version, major, minor, patch, status, changelog, success_rate, avg_duration_ms, total_invocations, created_at, updated_at
            ) VALUES (
                :id, 'trade_outreach_arabia', '沙特阿联酋中东拓客定制技能', '2.1.0', 2, 1, 0, 'active', '融入沙特商会正式商务礼仪模板', 0.92, 1420, 240, :now, :now
            )
        """), {"id": sk_ver_id, "now": NOW})

        sop_ver_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO evolution_sop_versions (
                id, sop_id, sop_name, version, major, minor, patch, status, changelog, completion_rate, total_executions, created_at, updated_at
            ) VALUES (
                :id, 'sop_gcc_tender_bidding', '海湾大区工程招标投标全流程SOP', '1.3.0', 1, 3, 0, 'active', '追加SASO能效证书提前校验节点', 0.96, 58, :now, :now
            )
        """), {"id": sop_ver_id, "now": NOW})

        db.execute(text("""
            INSERT INTO evolution_approvals (
                id, target_type, target_id, action, status, requester, reviewer, review_comment, submitted_at, reviewed_at
            ) VALUES (
                :id, 'skill_version', :target_id, 'promote_to_production', 'approved', 'HermesExperienceEngine', 'SuperAdmin', 'Validated against 88 real outreach records. Approved.', :now, :now
            )
        """), {"id": uuid.uuid4(), "target_id": sk_ver_id, "now": NOW})

        db.execute(text("""
            INSERT INTO evolution_canary_routes (
                id, tenant_id, skill_id, routed_version, routed_version_id, is_canary, created_at
            ) VALUES (
                :id, :tid, 'trade_outreach_arabia', '2.1.0', :verid, false, :now
            )
        """), {"id": uuid.uuid4(), "tid": t_id, "verid": sk_ver_id, "now": NOW})
        print("✓ evolution_experiences, skill_versions, sop_versions, approvals, canary_routes 填充完成")

        db.commit()
        print("🎉 Batch 4 [AI大模型/UBrain/聊天会话/合规风控/莫比乌斯进化] 种子数据提交成功！")
    except Exception as exc:
        db.rollback()
        print(f"❌ 填充失败: {exc}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seeding()
