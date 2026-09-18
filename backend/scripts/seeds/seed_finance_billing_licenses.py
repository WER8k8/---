# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""B2B 财务流水、AI模型计费、三轨结算与代理分佣种子数据填充脚本。

覆盖表：
1. payment_channels
2. payment_orders
3. payments
4. meter_events
5. model_call_ledger
6. finance_ledger_entries
7. tenant_invoices
8. tenant_invoice_profiles
9. invoice_applications
10. platform_invoice_configs
11. payment_ops_audit
12. payment_compensation_tasks
13. licenses
14. license_codes
15. license_orders
16. agent_nodes
17. agent_scorecards
18. agent_commission_settlements
"""
from __future__ import annotations

import datetime
import io
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
        print("🌱 开始填充 [财务 / 账单 / 计量 / 授权 / 代理] 数据集...")

        # 0. 获取基础租户与用户与订单
        tenants = db.execute(text("SELECT id, name FROM tenants LIMIT 10")).fetchall()
        users = db.execute(text("SELECT id, username FROM users LIMIT 10")).fetchall()
        orders = db.execute(text("SELECT id, order_number, total_amount FROM orders LIMIT 10")).fetchall()
        invoices = db.execute(text("SELECT id, invoice_no FROM invoices LIMIT 10")).fetchall()
        subscriptions = db.execute(text("SELECT id, tenant_id FROM tenant_subscriptions LIMIT 5")).fetchall()

        if not tenants or not users:
            print("⚠️ 未找到基础 tenants 或 users，请先确认基础环境")
            return

        t_id = tenants[0][0]
        u_id = users[0][0]
        sub_id = subscriptions[0][0] if subscriptions else None

        # 1. payment_channels (4个主流结算渠道)
        channels = [
            ("stripe_global", '{"publishable_key": "pk_live_youding_global", "webhook_enabled": true}'),
            ("bank_wire_tt", '{"bank_name": "Standard Chartered Hong Kong", "swift": "SCBLHKHHXXX", "currency": ["USD", "EUR", "AED"]}'),
            ("alipay_intl", '{"app_id": "20260919001", "gateway": "https://intl.alipay.com/gateway"}'),
            ("wechat_pay", '{"mch_id": "1900012345", "sub_mch_enabled": true}'),
        ]
        for ch, cfg in channels:
            existing = db.execute(text("SELECT id FROM payment_channels WHERE channel=:ch"), {"ch": ch}).scalar()
            if not existing:
                db.execute(text("""
                    INSERT INTO payment_channels (id, channel, config, is_active, created_at)
                    VALUES (:id, :ch, :cfg, true, :now)
                """), {"id": uuid.uuid4(), "ch": ch, "cfg": cfg, "now": NOW})
        print("✓ payment_channels 填充完成")

        # 2. payment_orders (10条支付订单)
        created_payment_order_ids = []
        for idx in range(1, 11):
            ord_no = f"PAY-ORD-202609-{idx:04d}"
            existing = db.execute(text("SELECT id FROM payment_orders WHERE order_no=:no"), {"no": ord_no}).scalar()
            if not existing:
                poid = uuid.uuid4()
                db.execute(text("""
                    INSERT INTO payment_orders (
                        id, tenant_id, subscription_id, order_no, amount, currency, channel, subject, status, paid_at, created_at, updated_at
                    ) VALUES (
                        :id, :tid, :subid, :no, :amt, 'USD', 'bank_wire_tt', 'YouDing SaaS Professional Annual', 'paid', :now, :now, :now
                    )
                """), {
                    "id": poid, "tid": t_id, "subid": sub_id, "no": ord_no,
                    "amt": 480000, "now": NOW - datetime.timedelta(days=idx*2)
                })
                created_payment_order_ids.append(poid)
            else:
                created_payment_order_ids.append(existing)
        print("✓ payment_orders 填充完成")

        # 3. payments (真实资金结转表)
        for idx, poid in enumerate(created_payment_order_ids[:8], start=1):
            ord_ref = orders[idx % len(orders)][0] if orders else None
            inv_ref = invoices[idx % len(invoices)][0] if invoices else None
            ref_no = f"TT-WIRE-{20260900 + idx}"
            existing = db.execute(text("SELECT id FROM payments WHERE reference_no=:ref"), {"ref": ref_no}).scalar()
            if not existing:
                db.execute(text("""
                    INSERT INTO payments (
                        id, tenant_id, order_id, invoice_id, amount, currency, method, status, paid_at, reference_no, notes, created_at, updated_at
                    ) VALUES (
                        :id, :tid, :oid, :invid, 12500.00, 'USD', 'T/T Wire Transfer', 'completed', :now, :ref, '30% deposit received via Standard Chartered', :now, :now
                    )
                """), {
                    "id": uuid.uuid4(), "tid": t_id, "oid": ord_ref, "invid": inv_ref,
                    "ref": ref_no, "now": NOW - datetime.timedelta(days=idx)
                })
        print("✓ payments 填充完成")

        # 4. meter_events (全域 Token/节点/指纹计量事件)
        meter_samples = [
            ("ai_generation", "ai_tokens", 8500, "tokens", 8500, 17, "USD", "ai_task", "deepseek-reasoner"),
            ("api_call", "sop_exec", 1, "call", 2400, 5, "USD", "sop_pipeline", "claude-3-7-sonnet"),
            ("lead_generated", "prospect_lead", 1, "lead", 120, 1, "USD", "whatsapp_campaign", "none"),
            ("export", "boq_export", 1, "file", 3500, 7, "USD", "boq_export", "qwen-2.5-72b"),
            ("content_publish", "site_page", 1, "page", 4000, 8, "USD", "publish_pipeline", "gpt-4o"),
        ]
        for mtype, unit_name, qty, unit_str, delta, cost, curr, src_type, mname in meter_samples:
            db.execute(text("""
                INSERT INTO meter_events (
                    id, tenant_id, event_key, meter_type, quantity, unit, token_delta, cost_cents, currency,
                    source_ref_type, source_ref_id, model_name, occurred_at, created_at
                ) VALUES (
                    :id, :tid, :key, :mtype, :qty, :unit, :delta, :cost, :curr,
                    :srctype, 'AUTO-SEEDED', :mname, :now, :now
                )
            """), {
                "id": uuid.uuid4(), "tid": t_id, "key": f"EVT-{uuid.uuid4().hex[:8]}",
                "mtype": mtype, "qty": qty, "unit": unit_str, "delta": delta,
                "cost": cost, "curr": curr, "srctype": src_type, "mname": mname, "now": NOW
            })
        print("✓ meter_events 填充完成")

        # 5. model_call_ledger (工业级模型调用流水账单)
        model_calls = [
            ("deepseek", "deepseek-reasoner", "l1_dag_planning", 1520, 3840, 5360, 0.015, 1250),
            ("anthropic", "claude-3-7-sonnet-20250219", "ecc_sop_orchestration", 2400, 4200, 6600, 0.035, 1820),
            ("openai", "gpt-4o-2024-08-06", "whatsapp_translation_arabic", 850, 620, 1470, 0.008, 640),
            ("aliyun", "qwen2.5-72b-instruct", "boq_cost_breakdown", 3100, 2900, 6000, 0.012, 1100),
        ]
        for prov, mname, cap, ptok, ctok, tot, cost, lat in model_calls:
            db.execute(text("""
                INSERT INTO model_call_ledger (
                    id, tenant_id, provider, model_name, capability_tag, prompt_tokens, completion_tokens,
                    total_tokens, cost_usd, latency_ms, status, called_at, request_id
                ) VALUES (
                    :id, :tid, :prov, :mname, :cap, :ptok, :ctok, :tot, :cost, :lat, 'success', :now, :reqid
                )
            """), {
                "id": uuid.uuid4(), "tid": t_id, "prov": prov, "mname": mname, "cap": cap,
                "ptok": ptok, "ctok": ctok, "tot": tot, "cost": cost, "lat": lat,
                "now": NOW, "reqid": f"req_{uuid.uuid4().hex[:12]}"
            })
        print("✓ model_call_ledger 填充完成")

        # 6. finance_ledger_entries (总账财务科目明细)
        ledger_entries = [
            ("income", "saas_subscription", 480000, "YouDing Annual Pro Subscription"),
            ("income", "ai_token_pack", 50000, "Prepaid 50M AI Tokens Pack"),
            ("income", "ip_slot_rental", 24000, "Dedicated Static Residential IP Slot 30-Day"),
            ("expense", "llm_api_cogs", 4500, "DeepSeek & Claude Upstream Billing"),
            ("expense", "proxy_traffic_cogs", 2800, "Oxylabs Residential Proxy Bandwidth"),
        ]
        for etype, cat, amt, note in ledger_entries:
            db.execute(text("""
                INSERT INTO finance_ledger_entries (
                    id, entry_type, category, amount_cents, tenant_id, reference_id, note, recorded_at, created_at
                ) VALUES (
                    :id, :etype, :cat, :amt, :tid, :ref, :note, :now, :now
                )
            """), {
                "id": uuid.uuid4(), "etype": etype, "cat": cat, "amt": amt,
                "tid": t_id, "ref": f"FIN-{uuid.uuid4().hex[:8]}", "note": note, "now": NOW
            })
        print("✓ finance_ledger_entries 填充完成")

        # 7. tenant_invoices & tenant_invoice_profiles & platform_invoice_configs
        # 平台官方开票主体配置
        plat_cfg = db.execute(text("SELECT id FROM platform_invoice_configs WHERE seller_tax_id='91130100MAD1234567'")).scalar()
        if not plat_cfg:
            db.execute(text("""
                INSERT INTO platform_invoice_configs (
                    id, seller_name, seller_tax_id, seller_address, seller_phone, seller_bank_name, seller_bank_account, service_category, disclaimer, is_active, updated_at
                ) VALUES (
                    :id, '河北优丁智能数字科技有限公司', '91130100MAD1234567', '河北省石家庄市高新区长江大道88号', '+86-0311-88889999',
                    '中国建设银行石家庄高新支行', '13050161500800001234', '*信息技术服务*SaaS软件订阅服务', '本发票为增值税电子普通发票，受国家税法保护', true, :now
                )
            """), {"id": uuid.uuid4(), "now": NOW})

        # 租户发票抬头
        prof_id = db.execute(text("SELECT id FROM tenant_invoice_profiles WHERE tenant_id=:tid"), {"tid": t_id}).scalar()
        if not prof_id:
            prof_id = uuid.uuid4()
            db.execute(text("""
                INSERT INTO tenant_invoice_profiles (
                    id, tenant_id, buyer_type, invoice_type, title, tax_id, company_address, company_phone,
                    bank_name, bank_account, recipient_email, is_default, created_at
                ) VALUES (
                    :id, :tid, 'enterprise', 'vat_special', '河北正定绿色新型建材有限公司', '91130123MA0899999X',
                    '河北省正定县科技工业园区6号', '+86-0311-87654321', '中国工商银行正定支行', '0402021009100012345',
                    'finance@zhengding-materials.com', true, :now
                )
            """), {"id": prof_id, "tid": t_id, "now": NOW})

        # 租户SaaS账单
        db.execute(text("""
            INSERT INTO tenant_invoices (id, tenant_id, subscription_id, amount, status, paid_at, due_at, created_at)
            VALUES (:id, :tid, :subid, 480000, 'paid', :now, :due, :now)
        """), {
            "id": uuid.uuid4(), "tid": t_id, "subid": sub_id,
            "now": NOW, "due": NOW + datetime.timedelta(days=30)
        })

        # 发票开具申请
        if created_payment_order_ids:
            db.execute(text("""
                INSERT INTO invoice_applications (
                    id, tenant_id, payment_order_id, applicant_user_id, buyer_type, invoice_type, title,
                    tax_id, recipient_email, amount_cents, order_no, status, disclaimer_ack, issued_at,
                    invoice_code, invoice_number, created_at, updated_at
                ) VALUES (
                    :id, :tid, :poid, :uid, 'enterprise', 'vat_special', '河北正定绿色新型建材有限公司',
                    '91130123MA0899999X', 'finance@zhengding-materials.com', 480000, 'PAY-ORD-202609-0001',
                    'issued', true, :now, '1300261130', '26113088', :now, :now
                )
            """), {
                "id": uuid.uuid4(), "tid": t_id, "poid": created_payment_order_ids[0],
                "uid": u_id, "now": NOW
            })
        print("✓ tenant_invoices, profiles, configs, applications 填充完成")

        # 8. payment_ops_audit & payment_compensation_tasks
        db.execute(text("""
            INSERT INTO payment_ops_audit (id, actor_user_id, action, ok, detail, created_at)
            VALUES (:id, :uid, 'payment_verified', true, 'T/T Wire 12500 USD verified against bank MT103', :now)
        """), {"id": uuid.uuid4(), "uid": u_id, "now": NOW})

        db.execute(text("""
            INSERT INTO payment_compensation_tasks (
                id, order_no, source, status, attempts, max_attempts, scheduled_at, completed_at, created_at, updated_at
            ) VALUES (
                :id, 'PAY-ORD-202609-0001', 'stripe_webhook_reconcile', 'success', 1, 3, :now, :now, :now, :now
            )
        """), {"id": uuid.uuid4(), "now": NOW})
        print("✓ payment_ops_audit, payment_compensation_tasks 填充完成")

        # 9. licenses, license_codes, license_orders
        lic_code_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO license_codes (id, code, plan_type, user_id, status, created_at)
            VALUES (:id, 'YD-PRO-2026-SAAS-KEY', 'enterprise', :uid, 'activated', :now)
        """), {"id": lic_code_id, "uid": u_id, "now": NOW})

        db.execute(text("""
            INSERT INTO licenses (
                id, license_key, tenant_id, plan_code, status, activated_at, expires_at, max_devices, ai_quota, created_by, created_at, updated_at
            ) VALUES (
                :id, 'LIC-YOUDING-GLOBAL-ENT-2026', :tid, 'enterprise', 'active', :now, :exp, 10, 50000000, :uid, :now, :now
            )
        """), {
            "id": uuid.uuid4(), "tid": t_id, "exp": NOW + datetime.timedelta(days=365),
            "uid": u_id, "now": NOW
        })

        db.execute(text("""
            INSERT INTO license_orders (
                id, user_id, license_code_id, plan_type, amount_cents, payment_method, status, created_at, updated_at
            ) VALUES (
                :id, :uid, :lcid, 'enterprise', 480000, 'bank_wire', 'completed', :now, :now
            )
        """), {"id": uuid.uuid4(), "uid": u_id, "lcid": lic_code_id, "now": NOW})
        print("✓ licenses, license_codes, license_orders 填充完成")

        # 10. agent_nodes & agent_scorecards & agent_commission_settlements
        # 建立两级代理树 (中东大区总代 -> 利雅得市级代理)
        root_agent_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO agent_nodes (id, name, level, agent_user_id, status, is_active, created_at, updated_at)
            VALUES (:id, '中东海湾大区总代 (GCC Regional Partner)', 'partner', :uid, 'active', true, :now, :now)
        """), {"id": root_agent_id, "uid": u_id, "now": NOW})

        city_agent_id = uuid.uuid4()
        db.execute(text("""
            INSERT INTO agent_nodes (id, name, level, parent_id, root_id, agent_user_id, status, is_active, created_at, updated_at)
            VALUES (:id, '沙特利雅得城市合伙人 (Riyadh City Agent)', 'agent', :pid, :rid, :uid, 'active', true, :now, :now)
        """), {"id": city_agent_id, "pid": root_agent_id, "rid": root_agent_id, "uid": u_id, "now": NOW})

        # 代理人业绩积分卡 (Agent Scorecard)
        db.execute(text("""
            INSERT INTO agent_scorecards (
                id, tenant_id, agent_id, agent_name, task_type, total_invocations, success_count,
                success_rate, avg_duration_ms, avg_cost, revenue_impact, conversion_rate, efficiency, roi,
                evaluation_window_days, created_at, updated_at
            ) VALUES (
                :id, :tid, 'gcc_partner_01', 'GCC General Partner', 'b2b_trade_acquisition', 150, 142,
                0.947, 1850, 0.45, 128000.00, 0.38, 0.92, 4.85, 30, :now, :now
            )
        """), {"id": uuid.uuid4(), "tid": t_id, "now": NOW})

        # 代理月度分佣结算单 (Commission Settlement)
        db.execute(text("""
            INSERT INTO agent_commission_settlements (
                id, agent_node_id, period, revenue_cents, commission_cents, commission_rate_bp, status, note, settled_at, created_at
            ) VALUES (
                :id, :anid, '2026-08', 35000000, 7000000, 2000, 'settled', '2026年8月建材外贸成单分佣（20%分成比例）', :now, :now
            )
        """), {"id": uuid.uuid4(), "anid": root_agent_id, "now": NOW})
        print("✓ agent_nodes, agent_scorecards, agent_commission_settlements 填充完成")

        db.commit()
        print("🎉 Batch 2 [财务/账单/计量/授权/代理] 种子数据提交成功！")
    except Exception as exc:
        db.rollback()
        print(f"❌ 填充失败: {exc}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seeding()
