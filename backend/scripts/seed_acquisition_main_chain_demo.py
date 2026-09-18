# -*- coding: utf-8 -*-
"""Honest demo seed for acquisition main-chain empty tables.

Rules:
- Only insert when target table count == 0 (idempotent).
- Reuse real tenant/user/product IDs from PG.
- Mark all rows with DEMO_SEED in notes/subject where possible.
- Never claim paid/shipped production success without evidence:
  orders start at draft/pending; payment_orders status=pending (unpaid demo).
- cwd must be backend so PG loads.
"""
from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(r"C:\Users\Administrator\Documents\上线网站开发完成\上线网站.worktrees\agents-install-vscode-cline-deploy-strix")
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy import text

from app.core.database import SessionLocal
from app.core import config as app_config

if app_config.settings.DB_TYPE != "postgresql":
    raise SystemExit(f"abort: DB_TYPE={app_config.settings.DB_TYPE} (need cwd=backend + PG env)")

TABLES = [
    "opportunities",
    "opportunity_stages",
    "quotes",
    "quote_items",
    "orders",
    "order_items",
    "payment_orders",
    "wallet_accounts",
    "wallet_transactions",
    "sales_tasks",
    "campaigns",
    "campaign_steps",
    "email_outreachs",
    "rfqs",
    "shipping_timeline",
]


def count(db, table: str) -> int:
    return int(db.execute(text(f'select count(*) from "{table}"')).scalar() or 0)


def main() -> None:
    db = SessionLocal()
    before = {t: count(db, t) for t in TABLES}
    print("BEFORE", before)

    try:
        tenant = db.execute(
            text("select id, name, domain from tenants order by created_at limit 1")
        ).fetchone()
        if not tenant:
            raise SystemExit("no tenant in PG — cannot seed FK-safe demo data")
        tenant_id, tenant_name, tenant_domain = str(tenant[0]), tenant[1], tenant[2]

        users = db.execute(text("select id, username, email from users limit 5")).fetchall()
        if len(users) < 1:
            raise SystemExit("no users in PG")
        merchant_id = str(users[0][0])
        buyer_id = str(users[1][0]) if len(users) > 1 else merchant_id

        product = db.execute(text("select id, name from products limit 1")).fetchone()
        product_id = str(product[0]) if product else None
        product_name = (product[1] if product else "Rock Wool Board DEMO_SEED")

        # quotes.inquiry_id 在 PG 上 NOT NULL（与模型 nullable 声明不一致）——必须挂真实询盘
        inq = db.execute(text("select id from inquiries order by created_at desc limit 1")).fetchone()
        inquiry_id = str(inq[0]) if inq else None
        if not inquiry_id:
            # 没有询盘则先写一条 DEMO 询盘，避免外键/非空失败
            inquiry_id = str(uuid.uuid4())
            db.execute(
                text(
                    """
                    insert into inquiries (id, tenant_id, name, email, message, status, created_at, updated_at)
                    select :id, :tid, :name, :email, :msg, 'new', :now, :now
                    where not exists (select 1 from inquiries limit 1)
                    """
                ),
                {
                    "id": inquiry_id,
                    "tid": tenant_id,
                    "name": "DEMO_SEED Buyer",
                    "email": "demo.seed.buyer@example.com",
                    "msg": "DEMO_SEED inquiry for insulation quote",
                    "now": now,
                },
            )
            # 若 inquiries 已有其它结构导致 insert 未生效，再取一次
            inq2 = db.execute(text("select id from inquiries limit 1")).fetchone()
            if inq2:
                inquiry_id = str(inq2[0])

        now = datetime.now(timezone.utc)
        report: dict = {"tenant_id": tenant_id, "tenant": tenant_name, "domain": tenant_domain, "inquiry_id": inquiry_id}

        # skip if any already filled — still seed remaining empty tables only
        def empty(t: str) -> bool:
            return before.get(t, 0) == 0

        # RFQ
        rfq_id = str(uuid.uuid4())
        if empty("rfqs"):
            db.execute(
                text(
                    """
                    insert into rfqs (
                      id, company, country, application, contact_name, email,
                      project, quantity, currency, status, rfq_score, intent_score, source, notes,
                      tenant_id, created_at, updated_at
                    ) values (
                      :id, :company, :country, :application, :contact_name, :email,
                      :project, :quantity, :currency, :status, :score, :intent_score, :source, :notes,
                      :tenant_id, :now, :now
                    )
                    """
                ),
                {
                    "id": rfq_id,
                    "company": "DEMO_SEED Gulf Insulation Co.",
                    "country": "SA",
                    "application": "External wall insulation",
                    "contact_name": "DEMO_SEED Buyer",
                    "email": "demo.seed.buyer@example.com",
                    "project": "DEMO_SEED warehouse retrofit",
                    "quantity": 1200,
                    "currency": "USD",
                    "status": "pending",
                    "score": 62,
                    "intent_score": 55,
                    "source": "demo_seed",
                    "notes": "DEMO_SEED 演示询价，非真实成交",
                    "tenant_id": tenant_id,
                    "now": now,
                },
            )
        else:
            row = db.execute(text("select id from rfqs limit 1")).fetchone()
            rfq_id = str(row[0]) if row else rfq_id

        # Opportunity + stages
        opp_id = str(uuid.uuid4())
        if empty("opportunities"):
            db.execute(
                text(
                    """
                    insert into opportunities (
                      id, rfq_id, name, company, contact_name, contact_email,
                      value, currency, stage, probability, country, application,
                      notes, tenant_id, assigned_to, source, created_at, updated_at
                    ) values (
                      :id, :rfq_id, :name, :company, :contact_name, :contact_email,
                      :value, :currency, :stage, :probability, :country, :application,
                      :notes, :tenant_id, :assigned_to, :source, :now, :now
                    )
                    """
                ),
                {
                    "id": opp_id,
                    "rfq_id": rfq_id,
                    "name": "DEMO_SEED SA warehouse insulation",
                    "company": "DEMO_SEED Gulf Insulation Co.",
                    "contact_name": "DEMO_SEED Buyer",
                    "contact_email": "demo.seed.buyer@example.com",
                    "value": 48000,
                    "currency": "USD",
                    "stage": "Quote",
                    "probability": 35,
                    "country": "SA",
                    "application": "External wall insulation",
                    "notes": "DEMO_SEED 商机演示数据",
                    "tenant_id": tenant_id,
                    "assigned_to": merchant_id,
                    "source": "rfq",
                    "now": now,
                },
            )
            for stage, note in [
                ("Lead", "DEMO_SEED 线索建档"),
                ("Qualified", "DEMO_SEED 需求核验通过"),
                ("Quote", "DEMO_SEED 已出报价草稿（未成交）"),
            ]:
                db.execute(
                    text(
                        """
                        insert into opportunity_stages (id, opportunity_id, stage, changed_by, notes, changed_at)
                        values (:id, :opp, :stage, :by, :notes, :now)
                        """
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "opp": opp_id,
                        "stage": stage,
                        "by": merchant_id,
                        "notes": note,
                        "now": now,
                    },
                )
        else:
            row = db.execute(text("select id from opportunities limit 1")).fetchone()
            opp_id = str(row[0]) if row else opp_id

        # Quote + items
        quote_id = str(uuid.uuid4())
        if empty("quotes"):
            db.execute(
                text(
                    """
                    insert into quotes (
                      id, tenant_id, inquiry_id, merchant_id, rfq_id, opportunity_id,
                      version, total_amount, currency, valid_until, payment_terms,
                      delivery_terms, status, created_at, updated_at
                    ) values (
                      :id, :tenant_id, :inquiry_id, :merchant_id, :rfq_id, :opp_id,
                      1, :total, 'USD', :valid_until, :pay, :delivery, 'draft', :now, :now
                    )
                    """
                ),
                {
                    "id": quote_id,
                    "tenant_id": tenant_id,
                    "inquiry_id": inquiry_id,
                    "merchant_id": merchant_id,
                    "rfq_id": rfq_id,
                    "opp_id": opp_id,
                    "total": 48000,
                    "valid_until": (now + timedelta(days=14)).date(),
                    "pay": "DEMO_SEED T/T 30% deposit, balance before shipment",
                    "delivery": "DEMO_SEED FOB Qingdao, 25-30 days after deposit",
                    "now": now,
                },
            )
            db.execute(
                text(
                    """
                    insert into quote_items (
                      id, quote_id, product_id, product_name, quantity, unit,
                      unit_price, total_price, notes, created_at
                    ) values (
                      :id, :qid, :pid, :pname, 1200, 'm2', 40, 48000,
                      'DEMO_SEED 报价行', :now
                    )
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "qid": quote_id,
                    "pid": product_id,
                    "pname": product_name,
                    "now": now,
                },
            )
        else:
            row = db.execute(text("select id from quotes limit 1")).fetchone()
            quote_id = str(row[0]) if row else quote_id

        # Order (NOT paid) + item
        order_id = str(uuid.uuid4())
        order_no = f"DEMO-SEED-{now.strftime('%Y%m%d')}-001"
        if empty("orders"):
            db.execute(
                text(
                    """
                    insert into orders (
                      id, tenant_id, buyer_id, merchant_id, quote_id, order_number,
                      total_amount, currency, status, payment_status,
                      shipping_address, incoterms, payment_terms, deposit_ratio,
                      deposit_amount, port_of_loading, port_of_discharge,
                      created_at, updated_at
                    ) values (
                      :id, :tenant_id, :buyer_id, :merchant_id, :quote_id, :order_no,
                      48000, 'USD', 'pending', 'pending',
                      :addr, 'FOB', 'T/T 30% deposit', 30, 14400,
                      'Qingdao', 'Dammam', :now, :now
                    )
                    """
                ),
                {
                    "id": order_id,
                    "tenant_id": tenant_id,
                    "buyer_id": buyer_id,
                    "merchant_id": merchant_id,
                    "quote_id": quote_id,
                    "order_no": order_no,
                    "addr": "DEMO_SEED Dammam warehouse, SA",
                    "now": now,
                },
            )
            if product_id:
                db.execute(
                    text(
                        """
                        insert into order_items (
                          id, order_id, product_id, quantity, unit_price, total_price,
                          specifications, created_at
                        ) values (
                          :id, :oid, :pid, 1200, 40, 48000,
                          '{"demo_seed": true}', :now
                        )
                        """
                    ),
                    {"id": str(uuid.uuid4()), "oid": order_id, "pid": product_id, "now": now},
                )
        else:
            row = db.execute(text("select id from orders limit 1")).fetchone()
            order_id = str(row[0]) if row else order_id
            rown = db.execute(text("select order_number from orders limit 1")).fetchone()
            order_no = rown[0] if rown else order_no

        # Payment order — pending, not paid
        if empty("payment_orders"):
            db.execute(
                text(
                    """
                    insert into payment_orders (
                      id, tenant_id, order_no, amount, currency, channel, subject,
                      status, created_at, updated_at
                    ) values (
                      :id, :tenant_id, :order_no, 1440000, 'CNY', 'alipay',
                      'DEMO_SEED 套餐/定金演示订单（未支付）', 'pending', :now, :now
                    )
                    """
                ),
                {"id": str(uuid.uuid4()), "tenant_id": tenant_id, "order_no": f"PAY-{order_no}", "now": now},
            )

        # Wallet — demo balance with ledger note
        if empty("wallet_accounts"):
            db.execute(
                text(
                    """
                    insert into wallet_accounts (id, user_id, currency, balance, created_at, updated_at)
                    values (:id, :uid, 'CNY', 100000, :now, :now)
                    """
                ),
                {"id": str(uuid.uuid4()), "uid": merchant_id, "now": now},
            )
        if empty("wallet_transactions"):
            bal = 100000
            for i, (op, amt, ref) in enumerate(
                [
                    ("deposit", 200000, "DEMO_SEED 初始演示充值"),
                    ("consume", -100000, "DEMO_SEED Token/动作计量演示"),
                ]
            ):
                bal = bal if i == 0 else 100000
                after = 200000 if i == 0 else 100000
                db.execute(
                    text(
                        """
                        insert into wallet_transactions (
                          id, tx_id, user_id, operation, amount, currency,
                          balance_after, ref_type, ref_id, created_at
                        ) values (
                          :id, :tx, :uid, :op, :amt, 'CNY', :after,
                          'demo_seed', :ref, :now
                        )
                        """
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "tx": f"DEMOSEED{i+1:04d}{uuid.uuid4().hex[:8]}",
                        "uid": merchant_id,
                        "op": op,
                        "amt": amt,
                        "after": after,
                        "ref": ref,
                        "now": now,
                    },
                )

        # Sales tasks
        if empty("sales_tasks"):
            for title, ttype, prio in [
                ("DEMO_SEED 跟进 SA 仓库保温项目报价确认", "quote_approval", "high"),
                ("DEMO_SEED 回访 DEMO_SEED Buyer 交期与认证", "followup", "normal"),
                ("DEMO_SEED 准备 PI 草稿（人审后发出）", "rfq_response", "normal"),
            ]:
                db.execute(
                    text(
                        """
                        insert into sales_tasks (
                          id, title, description, task_type, priority, status,
                          due_at, assigned_to, rfq_id, opportunity_id, tenant_id,
                          created_by, created_at, updated_at
                        ) values (
                          :id, :title, :desc, :ttype, :prio, 'open',
                          :due, :uid, :rfq, :opp, :tid, :uid, :now, :now
                        )
                        """
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "title": title,
                        "desc": "DEMO_SEED 演示待办，非真实客户任务",
                        "ttype": ttype,
                        "prio": prio,
                        "due": now + timedelta(days=2),
                        "uid": merchant_id,
                        "rfq": rfq_id,
                        "opp": opp_id,
                        "tid": tenant_id,
                        "now": now,
                    },
                )

        # Campaign + steps (draft, sent_count=0 — no fake send)
        camp_id = str(uuid.uuid4())
        if empty("campaigns"):
            db.execute(
                text(
                    """
                    insert into campaigns (
                      id, name, campaign_type, tier, status, target_count,
                      sent_count, reply_count, positive_reply_count, tenant_id,
                      created_at, updated_at
                    ) values (
                      :id, :name, 'outbound', 'B', 'draft', 20,
                      0, 0, 0, :tid, :now, :now
                    )
                    """
                ),
                {
                    "id": camp_id,
                    "name": "DEMO_SEED 建材中东拓客序列（草稿未发送）",
                    "tid": tenant_id,
                    "now": now,
                },
            )
        if empty("campaign_steps"):
            steps = [
                (1, 0, "Introduction: insulation supply for Gulf projects", "email"),
                (2, 3, "Follow-up: certifications & lead time", "followup"),
                (3, 7, "Case study: warehouse retrofit", "case_study"),
            ]
            for order_i, delay, subj, action in steps:
                db.execute(
                    text(
                        """
                        insert into campaign_steps (
                          id, campaign_id, step_order, day_delay, subject,
                          content_template, action_type, created_at
                        ) values (
                          :id, :cid, :ord, :delay, :subj,
                          :body, :action, :now
                        )
                        """
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "cid": camp_id,
                        "ord": order_i,
                        "delay": delay,
                        "subj": subj,
                        "body": f"DEMO_SEED template step {order_i} — 人审后才可发送",
                        "action": action,
                        "now": now,
                    },
                )

        # Email outreach — draft only
        if empty("email_outreachs"):
            db.execute(
                text(
                    """
                    insert into email_outreachs (
                      id, idempotency_key, tenant_id, user_id, from_email, from_name,
                      to_email, subject, html_body, text_body, status,
                      sequence_id, sequence_step, sequence_total_steps,
                      open_count, click_count, outreach_metadata, tags,
                      created_at, updated_at
                    ) values (
                      :id, :key, :tid, :uid, 'sales@demo.local', 'DEMO_SEED Seller',
                      :to_email, :subject, :html, :text, 'draft',
                      'demo-seq-1', 0, 3,
                      0, 0, :meta, :tags, :now, :now
                    )
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "key": f"demo-seed-{uuid.uuid4().hex[:16]}",
                    "tid": tenant_id,
                    "uid": merchant_id,
                    "to_email": "demo.seed.buyer@example.com",
                    "subject": "DEMO_SEED Inquiry follow-up — insulation supply",
                    "html": "<p>DEMO_SEED 草稿邮件，未经人审未发送。</p>",
                    "text": "DEMO_SEED draft email, not sent.",
                    "meta": json.dumps({"demo_seed": True, "note": "draft only"}),
                    "tags": json.dumps(["demo_seed"]),
                    "now": now,
                },
            )

        # Shipping timeline config (country template, not tracking success)
        if empty("shipping_timeline"):
            for country, badge in [("SA", "Support SABER"), ("NG", "Support SONCAP"), ("KE", "Support PVOC")]:
                db.execute(
                    text(
                        """
                        insert into shipping_timeline (
                          id, merchant_id, country_code,
                          step_1_title, step_1_desc, step_1_days,
                          step_2_title, step_2_desc, step_2_days, step_2_badge,
                          step_3_title, step_3_desc, step_3_days,
                          step_4_title, step_4_desc, step_4_days,
                          is_active, sort_order, created_at, updated_at
                        ) values (
                          :id, :mid, :cc,
                          'Custom Production', 'DEMO_SEED 确认规格后排产', '3-5 Days',
                          'Compliance & Packing', 'DEMO_SEED 质检与证书准备', '2 Days', :badge,
                          'Ocean Shipping', 'DEMO_SEED 订舱装箱', 'Guaranteed Space',
                          'Destination Assistance', 'DEMO_SEED 到岸协助清关', '-',
                          true, 0, :now, :now
                        )
                        """
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "mid": merchant_id,
                        "cc": country,
                        "badge": badge,
                        "now": now,
                    },
                )

        db.commit()
        after = {t: count(db, t) for t in TABLES}
        print("AFTER", after)
        report.update(
            {
                "before": before,
                "after": after,
                "seeded_tables": [t for t in TABLES if after.get(t, 0) > before.get(t, 0)],
                "still_empty": [t for t in TABLES if after.get(t, 0) == 0],
                "plain": (
                    "演示注水完成：商机/报价/订单/钱包/任务/活动/邮件草稿/物流模板。"
                    "订单与支付均为 pending/未发送，不表示已成交或已到账。"
                ),
            }
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))
        out = ROOT / "docs" / "probe_main_chain_seed_report.json"
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print("written", out)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
