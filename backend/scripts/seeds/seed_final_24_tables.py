# -*- coding: utf-8 -*-
"""
优丁 (YouDing) 种子数据收尾批次 - 填平最后 24 张空表，全库 253 张表达成 100% 数据密度
"""
import os
import sys
import uuid
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from sqlalchemy import text
from app.core.database import SessionLocal

def run_seeding():
    db = SessionLocal()
    NOW = datetime.datetime.now(datetime.timezone.utc)
    TODAY = datetime.date.today()

    try:
        print("🚀 [START] 注入最后 24 张空表，推进全库 253 张表 100% 密度...")

        # 预先获取基础关联实体
        tenant_row = db.execute(text("SELECT id FROM tenants LIMIT 1")).fetchone()
        t_id = tenant_row[0] if tenant_row else uuid.uuid4()

        user_row = db.execute(text("SELECT id FROM users LIMIT 1")).fetchone()
        u_id = user_row[0] if user_row else uuid.uuid4()

        order_row = db.execute(text("SELECT id, order_no FROM payment_orders LIMIT 1")).fetchone()
        order_id = order_row[0] if order_row else uuid.uuid4()
        order_no = order_row[1] if order_row else "PAY-ORD-202609-0001"

        # 1. acquisition_quote_wake & acquisition_sla_alerts
        db.execute(text("""
            INSERT INTO acquisition_quote_wake (tenant_id, inquiry_id, alert_date, created_at)
            VALUES (:tid, 'INQ-SA-2026-001', :today, :now)
            ON CONFLICT DO NOTHING
        """), {"tid": str(t_id), "today": TODAY, "now": NOW})

        db.execute(text("""
            INSERT INTO acquisition_sla_alerts (tenant_id, inquiry_id, alert_date, created_at)
            VALUES (:tid, 'INQ-SA-2026-001', :today, :now)
            ON CONFLICT DO NOTHING
        """), {"tid": str(t_id), "today": TODAY, "now": NOW})
        print("✓ acquisition_quote_wake, acquisition_sla_alerts 填充完成")

        # 2. ai_tasks & task_traces
        ai_task_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO ai_tasks (
                id, tenant_id, task_type, status, priority, budget_used, retry_count, input_json, output_json, created_at, updated_at
            ) VALUES (
                :id, :tid, 'hermes_node:arabic_cold_email_dispatch', 'done', 1, 0.0150, 0,
                '{"recipient": "procurement@al-bawani.sa", "intent": "quote_inquiry"}',
                '{"status": "dispatched", "message_id": "wa_msg_98821"}',
                :now, :now
            )
        """), {"id": ai_task_id, "tid": t_id, "now": NOW})

        db.execute(text("""
            INSERT INTO task_traces (
                id, tenant_id, trace_type, task_id, status, success, duration_ms, cost, tokens_used, input_summary, output_summary, created_at, updated_at
            ) VALUES (
                :id, :tid, 'agent_execution', :atid, 'success', true, 840, 0.0150, 1420,
                'Cold email generation in Arabic for Riyadh project',
                'Dispatched email via SMTP with high deliverability score 98%',
                :now, :now
            )
        """), {"id": uuid.uuid4(), "tid": t_id, "atid": ai_task_id, "now": NOW})
        print("✓ ai_tasks, task_traces 填充完成")

        # 3. campaigns & prospect_leads
        camp_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO campaigns (id, name, campaign_type, tier, status, target_count, sent_count, reply_count, positive_reply_count, tenant_id, created_at, updated_at)
            VALUES (:id, '2026沙特商业中心幕墙岩棉外贸拓客专项', 'outbound_email_whatsapp', 'tier_1', 'active', 200, 168, 42, 18, :tid, :now, :now)
        """), {"id": camp_id, "tid": str(t_id), "now": NOW})

        db.execute(text("""
            INSERT INTO prospect_leads (
                id, tenant_id, company_name, email, country, industry, source, status,
                fit_score, engagement_score, overall_score, score_match, score_email, score_evidence, score_contact,
                open_count, click_count, reply_count, contact_count, version, created_at, updated_at
            ) VALUES (
                :id, :tid, 'Al-Bawani Contracting Co.', 'tenders@albawani.sa', 'SA', 'Building Construction', 'linkedin', 'qualified',
                92, 88, 90, 95, 90, 85, 90,
                3, 2, 1, 4, 1, :now, :now
            )
        """), {"id": uuid.uuid4(), "tid": t_id, "now": NOW})
        print("✓ campaigns, prospect_leads 填充完成")

        # 4. content_masters & deerflow_jobs
        db.execute(text("""
            INSERT INTO content_masters (
                id, tenant_id, title, body, content_type, status, hub_slug, hub_summary, show_on_hub, created_at, updated_at
            ) VALUES (
                :id, :tid, '沙特NEOM新城岩棉保温工程规范与中国供应链出海白皮书',
                '详细分析海湾地区高热干燥气候下建筑围护结构保温装饰一体板的施工工艺与CE/SASO双认证...',
                'whitepaper', 'published', 'neom-rockwool-spec', '沙特高热环境下一体板最佳工程实践', true, :now, :now
            )
        """), {"id": uuid.uuid4(), "tid": t_id, "now": NOW})

        db.execute(text("""
            INSERT INTO deerflow_jobs (
                id, tenant_id, intent, status, payload_json, result_json, created_at, updated_at
            ) VALUES (
                :id, :tid, 'market_research_report', 'completed',
                '{"country": "SA", "category": "rockwool_panels"}',
                '{"market_size_usd": "450M", "annual_growth": "12.4%", "top_buyers": ["Al-Bawani", "Nesma", "El-Seif"]}',
                :now, :now
            )
        """), {"id": uuid.uuid4(), "tid": t_id, "now": NOW})
        print("✓ content_masters, deerflow_jobs 填充完成")

        # 5. domestic_inquiries & rfqs & opportunities
        db.execute(text("""
            INSERT INTO domestic_inquiries (
                id, tenant_id, buyer_name, buyer_type, quantity_m2, stage, currency, vat_type, vat_rate, created_at, updated_at
            ) VALUES (
                :id, :tid, '北京建工集团雄安项目部', 'general_contractor', 18500.0, 'negotiation', 'CNY', 'special_vat', 0.13, :now, :now
            )
        """), {"id": f"DINQ-{uuid.uuid4().hex[:8]}", "tid": str(t_id), "now": NOW})

        rfq_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO rfqs (
                id, company, country, application, contact_name, email, status, rfq_score, intent_score, tenant_id, created_at, updated_at
            ) VALUES (
                :id, 'Saudi Binladin Group', 'Saudi Arabia', 'External Wall Cladding & Insulation', 'Fahad Al-Harbi', 'procure@sbg.com.sa', 'quoting', 96, 95, :tid, :now, :now
            )
        """), {"id": rfq_id, "tid": str(t_id), "now": NOW})

        db.execute(text("""
            INSERT INTO opportunities (
                id, rfq_id, name, company, contact_name, contact_email, value, currency, stage, probability, country, tenant_id, created_at, updated_at
            ) VALUES (
                :id, :rfqid, '沙特红海旅游开发区度假村幕墙保温工程', 'Red Sea Global', 'Omar Khateeb', 'omar.k@redseaglobal.com', 420000.0, 'USD', 'proposal', 80, 'Saudi Arabia', :tid, :now, :now
            )
        """), {"id": uuid.uuid4(), "rfqid": rfq_id, "tid": str(t_id), "now": NOW})
        print("✓ domestic_inquiries, rfqs, opportunities 填充完成")

        # 6. email_tracking_events
        db.execute(text("""
            INSERT INTO email_tracking_events (
                id, message_id, event_type, tenant_id, user_id, ip_address, created_at
            ) VALUES (
                :id, 'msg_wa_track_final_01', 'OPEN', :tid, :uid, '84.235.92.11', :now
            )
        """), {"id": uuid.uuid4(), "tid": t_id, "uid": u_id, "now": NOW})
        print("✓ email_tracking_events 填充完成")

        # 7. hermes_plugin_installs & pipelines
        db.execute(text("""
            INSERT INTO hermes_plugin_installs (
                id, tenant_id, plugin_id, plugin_version, enabled, installed_at, updated_at
            ) VALUES (
                :id, :tid, 'plugin_goodjob_whatsapp_live_sync', '1.2.0', true, :now, :now
            )
        """), {"id": uuid.uuid4(), "tid": t_id, "now": NOW})

        db.execute(text("""
            INSERT INTO pipelines (
                id, tenant_id, name, pipeline_type, stage_count, is_default, is_active, created_at, updated_at
            ) VALUES (
                :id, :tid, '标准外贸七步履约全闭环调度管线', 'trade_fulfillment_7steps', 7, true, true, :now, :now
            )
        """), {"id": uuid.uuid4(), "tid": t_id, "now": NOW})
        print("✓ hermes_plugin_installs, pipelines 填充完成")

        # 8. invoices & payment_refunds
        orders_row = db.execute(text("SELECT id FROM orders LIMIT 1")).fetchone()
        real_order_id = orders_row[0] if orders_row else None

        pay_order_row = db.execute(text("SELECT id, order_no FROM payment_orders LIMIT 1")).fetchone()
        pay_order_id = pay_order_row[0] if pay_order_row else uuid.uuid4()
        pay_order_no = pay_order_row[1] if pay_order_row else "PAY-ORD-202609-0001"

        db.execute(text("""
            INSERT INTO invoices (
                id, tenant_id, order_id, invoice_no, invoice_type, buyer_name, amount, currency, status, created_at, updated_at
            ) VALUES (
                :id, :tid, :oid, 'INV-2026-YOUDING-001', 'commercial_invoice', 'Al-Yamama Building Supply Co.', 4800.00, 'USD', 'paid', :now, :now
            )
        """), {"id": uuid.uuid4(), "tid": t_id, "oid": real_order_id, "now": NOW})

        db.execute(text("""
            INSERT INTO payment_refunds (
                id, order_id, order_no, tenant_id, amount, currency, status, reason, created_at, updated_at
            ) VALUES (
                :id, :oid, :ord_no, :tid, 0, 'USD', 'completed', 'Sample test zero refund record', :now, :now
            )
        """), {"id": uuid.uuid4(), "oid": pay_order_id, "ord_no": pay_order_no, "tid": t_id, "now": NOW})
        print("✓ invoices, payment_refunds 填充完成")

        # 9. referral_codes & referral_records
        ref_code_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO referral_codes (
                id, tenant_id, code, is_active, total_referred, total_earned, created_at
            ) VALUES (
                :id, :tid, 'YDREF2026', true, 12, 6000, :now
            )
            ON CONFLICT DO NOTHING
        """), {"id": ref_code_id, "tid": t_id, "now": NOW})

        ref_code_id = db.execute(text("SELECT id FROM referral_codes WHERE code = 'YDREF2026'")).scalar() or ref_code_id

        db.execute(text("""
            INSERT INTO referral_records (
                id, code_id, inviter_tenant_id, invited_tenant_id, status, reward_type, reward_amount, invited_at, rewarded_at
            ) VALUES (
                :id, :cid, :tid, :tid, 'rewarded', 'tokens', 500, :now, :now
            )
        """), {"id": uuid.uuid4(), "cid": ref_code_id, "tid": t_id, "now": NOW})
        print("✓ referral_codes, referral_records 填充完成")

        # 10. tenant_wecom_push_configs & token_ledger_entries
        db.execute(text("""
            INSERT INTO tenant_wecom_push_configs (
                id, tenant_id, enabled, corp_id, agent_id, agent_secret, webhook_url, created_at, updated_at
            ) VALUES (
                :id, :tid, true, 'ww1982847120938', '1000002', 'sec_youding_wecom_key_2026', 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=mock-key', :now, :now
            )
        """), {"id": uuid.uuid4(), "tid": t_id, "now": NOW})

        db.execute(text("""
            INSERT INTO token_ledger_entries (
                id, tenant_id, delta, balance_after, reason, reference_id, created_at
            ) VALUES (
                :id, :tid, -120, 49880, 'Hermes AI Dag Dispatch Call', 'task_dag_exec_001', :now
            )
        """), {"id": uuid.uuid4(), "tid": t_id, "now": NOW})
        print("✓ tenant_wecom_push_configs, token_ledger_entries 填充完成")

        # 11. ubrain_action_audits, ubrain_pipeline_runs, ubrain_research_insights, ubrain_tenant_memory
        db.execute(text("""
            INSERT INTO ubrain_action_audits (
                id, tenant_id, user_id, action_type, intent, tool, message_preview, needs_confirmation, outcome, created_at
            ) VALUES (
                :id, :tid, :uid, 'tool_call', 'boq_pricing_calc', 'boq_cost_engine', '核算沙特 42,000 平米一体板FOB综合造价', 'false', 'success', :now
            )
        """), {"id": uuid.uuid4(), "tid": t_id, "uid": u_id, "now": NOW})

        insight_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO ubrain_research_insights (
                id, tenant_id, source, intent, title, summary, quality_score, created_at
            ) VALUES (
                :id, :tid, 'perplexity_deep_research', 'market_intelligence',
                '海湾地区外墙保温新防火法令（SBC 801）全面推行',
                '沙特民防总局自2026年起强制要求所有高层商业建筑外墙复合板达到Class A1级不燃标准...',
                0.97, :now
            )
        """), {"id": insight_id, "tid": t_id, "now": NOW})

        db.execute(text("""
            INSERT INTO ubrain_pipeline_runs (
                id, tenant_id, insight_id, status, steps_json, created_at
            ) VALUES (
                :id, :tid, :iid, 'completed', '["insight_extraction", "product_matching", "outreach_campaign_generation"]', :now
            )
        """), {"id": uuid.uuid4(), "tid": t_id, "iid": insight_id, "now": NOW})

        db.execute(text("""
            INSERT INTO ubrain_tenant_memory (
                tenant_id, memory_json, tool_use_count, updated_at
            ) VALUES (
                :tid, '{"preferred_incoterm": "CIF Dammam", "core_material": "rockwool", "target_region": "GCC"}', 48, :now
            )
            ON CONFLICT (tenant_id) DO UPDATE SET tool_use_count = 48
        """), {"tid": t_id, "now": NOW})
        print("✓ ubrain_action_audits, pipeline_runs, insights, tenant_memory 填充完成")

        db.commit()
        print("🎉 [SUCCESS] 24 张剩余空表全部成功注入并持久化！")
    except Exception as exc:
        db.rollback()
        print(f"❌ 填充失败: {exc}", file=sys.stderr)
        raise
    finally:
        db.close()

if __name__ == "__main__":
    run_seeding()
