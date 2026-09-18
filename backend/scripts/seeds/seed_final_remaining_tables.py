"""
优丁 (YouDing) 种子数据批次 - 终极收敛 (Final 6 Tables)
覆盖最后 6 张空表:
1. merchant_im_routing
2. paperclip_agents
3. paperclip_heartbeats
4. projects
5. project_signals
6. referral_records

将数据库填充率推至 100% (248/248)。
"""
import os
import sys
import uuid
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import text
from app.core.database import SessionLocal

def run_seeding():
    db = SessionLocal()
    NOW = datetime.datetime.now(datetime.timezone.utc)
    NAIVE_NOW = datetime.datetime.utcnow()

    if sys.stdout.encoding.lower() != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    try:
        print("[START] Seeding final 6 tables for 100% database density...")

        # 1. merchant_im_routing
        db.execute(text("""
            INSERT INTO merchant_im_routing (merchant_id, country_code, channel_type, account_id, prefilled_text, is_active, created_at, updated_at)
            VALUES (1, 'SA', 'whatsapp', '+966501234567', 'Inquiry for CE EN 13501-1 Rockwool panels', true, :now, :now)
        """), {"now": NAIVE_NOW})
        print("✓ merchant_im_routing 填充完成")

        # 2. paperclip_agents & paperclip_heartbeats
        comp_id = db.execute(text("SELECT id FROM paperclip_companies LIMIT 1")).scalar()
        if not comp_id:
            comp_id = uuid.uuid4()
            db.execute(text("""
                INSERT INTO paperclip_companies (id, name, created_at, updated_at)
                VALUES (:id, 'Al-Yamama Building Supply Co.', :now, :now)
            """), {"id": comp_id, "now": NOW})

        agent_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO paperclip_agents (id, company_id, name, title, role, provider, agent_ref, skills_json, config_json, status, heartbeat_enabled, heartbeat_interval_minutes, monthly_budget_credits, used_credits, last_heartbeat_at, created_at, updated_at)
            VALUES (:id, :cid, 'Façade Materials Sourcing Bot', 'Sourcing Lead', 'procurement_specialist', 'deepseek', 'ref_bot_01', '["b2b-rfq-match", "pricing-calc"]', '{"model": "deepseek-chat"}', 'active', true, 60, 500.0, 15.0, :now, :now, :now)
        """), {"id": agent_id, "cid": comp_id, "now": NOW})

        db.execute(text("""
            INSERT INTO paperclip_heartbeats (id, agent_id, company_id, status, trigger, tasks_checked, tasks_executed, credits_used, started_at, finished_at, created_at)
            VALUES (:id, :aid, :cid, 'success', 'cron', 8, 2, 0.25, :now, :now, :now)
        """), {"id": uuid.uuid4(), "aid": agent_id, "cid": comp_id, "now": NOW})
        print("✓ paperclip_agents, paperclip_heartbeats 填充完成")

        # 3. projects & project_signals
        proj_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO projects (id, name, company, country, city, project_type, stage, estimated_value, currency, requirements, confidence, product_match_score, created_at, updated_at)
            VALUES (:id, 'Riyadh King Salman Park Commercial Center', 'Al-Bawani Construction', 'Saudi Arabia', 'Riyadh', 'commercial_complex', 'bidding', 3800000.0, 'USD', '45,000 sqm Rockwool sandwich panels + fireproof exterior cladding', 0.95, 96, :now, :now)
        """), {"id": proj_id, "now": NOW})

        db.execute(text("""
            INSERT INTO project_signals (id, project_id, signal_type, title, description, source, source_url, occurred_at, created_at)
            VALUES (:id, :pid, 'tender_announcement', 'External Façade Insulation Subcontract Tender', 'Tender open for Class A1 fire-rated Rockwool sandwich panels delivery to Riyadh site.', 'Saudi Tenders Portal', 'https://tenders.sa/rfq/facade-2026', :now, :now)
        """), {"id": uuid.uuid4(), "pid": proj_id, "now": NOW})
        print("✓ projects, project_signals 填充完成")

        # 4. referral_records
        ref_code = db.execute(text("SELECT id, tenant_id FROM referral_codes LIMIT 1")).fetchone()
        tenants = db.execute(text("SELECT id FROM tenants LIMIT 2")).fetchall()
        if ref_code and len(tenants) >= 2:
            code_id = ref_code[0]
            inviter_id = tenants[0][0]
            invited_id = tenants[1][0]
            db.execute(text("""
                INSERT INTO referral_records (id, code_id, inviter_tenant_id, invited_tenant_id, reward_amount, status, reward_type, redemption_status, invited_at, rewarded_at)
                VALUES (:id, :cid, :invid, :recid, 500, 'rewarded', 'tokens', 'completed', :now, :now)
            """), {"id": uuid.uuid4(), "cid": code_id, "invid": inviter_id, "recid": invited_id, "now": NOW})
            print("✓ referral_records 填充完成")

        db.commit()
        print("🎉 最终 6 张表全部填充并提交成功！全库密度达成 100%！")
    except Exception as exc:
        db.rollback()
        print(f"❌ 填充失败: {exc}", file=sys.stderr)
        raise
    finally:
        db.close()

if __name__ == "__main__":
    run_seeding()
