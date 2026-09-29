# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""AEOS_REVENUE_LOOP_E2E — 收入闭环端到端验收脚本（模块26.1 / Gate G15 工具）。

设计依据：`docs/GPT对话全文存档-修正设计细节稿-28轮-2026-09-26.md` §26.1/26.2、
`docs/GPT文稿-AEOS_v1.0商用上线验收与Production-Gate-2026-09-26.md` §3/§17。

**诚实门控（不假交付红线）**：
- 每个阶段独立判定 pass / blocked / fail：
  - pass    = 本机可真实执行且断言通过；
  - blocked = 依赖外部生产凭据/基础设施（真实域名 SSL、真实分发凭据、真实支付回调、
              真实承运商、Evolution 生产晋升），**明示 blocked_by**，绝不伪造成功；
  - fail    = 本应可跑但断言失败（任何 fail → exit 2）。
- 默认 `--rollback`：全部阶段在一个事务内执行并在结束时回滚（不留脏数据、
  不触碰真实租户）；`--commit` 为授权真实租户运行预留（当前拒绝执行，须人工改码，
  对齐 Gate §3「无人工数据库干预的真实租户闭环」——演示链路不得冒充 G15 通过）。
- 最终判决恒为：存在 blocked 即 `PRODUCTION_GATE: NOT PASSED`。

用法（backend/ 下）：
    python scripts/qa/aeos_revenue_loop_e2e.py                 # 事务内全链 + 回滚
    python scripts/qa/aeos_revenue_loop_e2e.py --json out.json # 证据落盘
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass


STAGES: list[dict[str, Any]] = []


def stage(name: str, requires_external: str | None = None):
    def _wrap(fn: Callable[..., dict[str, Any]]):
        STAGES.append(
            {"name": name, "fn": fn, "requires_external": requires_external}
        )
        return fn

    return _wrap


# ── 可真实执行阶段（事务内）───────────────────────────────────────────────


@stage("tenant_provision")
def st_tenant(db) -> dict[str, Any]:
    from app.models.tenant import Tenant, TenantPlan

    plan = db.query(TenantPlan).order_by(TenantPlan.created_at.asc()).first()
    if plan is None:
        plan = TenantPlan(id=str(uuid.uuid4()), name="e2e-plan", price_cents=0)
        db.add(plan)
        db.commit()
    t = Tenant(
        id=str(uuid.uuid4()),
        name=f"AEOS-E2E-{datetime.now(timezone.utc).strftime('%H%M%S')}",
        domain=f"e2e-{uuid.uuid4().hex[:8]}.example.com",
        plan_id=str(plan.id),
        status="active",
        is_active=True,
    )
    db.add(t)
    db.commit()
    row = db.query(Tenant).filter(Tenant.id == t.id).first()
    assert row is not None and row.is_active
    return {"tenant_id": str(row.id), "evidence": "tenants 行落库且 active"}


@stage("product_register")
def st_product(db) -> dict[str, Any]:
    from app.models.product import Category, Product

    cat = db.query(Category).order_by(Category.created_at.asc()).first()
    if cat is None:
        cat = Category(id=str(uuid.uuid4()), name=f"e2e-cat-{uuid.uuid4().hex[:6]}")
        db.add(cat)
        db.commit()
    p = Product(
        id=str(uuid.uuid4()),
        name=f"E2E 板材 {uuid.uuid4().hex[:6]}",
        slug=f"e2e-{uuid.uuid4().hex[:10]}",
        category_id=str(cat.id),
    )
    db.add(p)
    db.commit()
    return {"product_id": str(p.id), "evidence": "products 行落库"}


def _latest_tenant_id(db) -> str:
    from app.models.tenant import Tenant

    row = db.query(Tenant).order_by(Tenant.created_at.desc()).first()
    assert row is not None, "tenant stage must run first"
    return str(row.id)


@stage("inquiry_qualification_metering", requires_external=None)
def st_inquiry(db) -> dict[str, Any]:
    """询盘 → 合格（in_progress）→ usage.qualified_inquiry 计量（轨2 触发点）。"""
    from app.models.inquiry import Inquiry
    from app.models.meter import MeterEvent
    from app.services.inquiry_status_service import advance_inquiry_status

    tenant_id = _latest_tenant_id(db)
    inq = Inquiry(
        id=str(uuid.uuid4()),
        name="E2E 询盘",
        message="E2E: 5000 sqm panels, please quote",
        status="new",
        is_active=True,
        phone="13800009999",
        email="e2e@example.com",
        tenant_id=str(tenant_id),
    )
    db.add(inq)
    db.commit()
    advance_inquiry_status(db, inq, "in_progress", source="aeos_e2e")
    ev = (
        db.query(MeterEvent)
        .filter(MeterEvent.event_key == f"inquiry:{inq.id}:qualified")
        .first()
    )
    assert ev is not None and ev.meter_code == "usage.qualified_inquiry"
    return {
        "inquiry_id": str(inq.id),
        "meter_event_id": str(ev.id),
        "evidence": "询盘推进 in_progress 且 usage.qualified_inquiry 计量落库（event_key 幂等）",
    }


@stage("billing_reserve_settle_reverse")
def st_billing(db) -> dict[str, Any]:
    """G9 统一链：Event→Reservation→Settle→FinanceLedger→Reverse（轨2 证据）。"""
    from app.models.billing_reservation import BillingReservation
    from app.models.finance_ledger import FinanceLedgerEntry
    from app.services.billing.reservation_service import (
        build_idempotency_key,
        create_reservation,
        reserve,
        settle,
        reverse,
    )

    tenant_id = _latest_tenant_id(db)
    subject_id = f"e2e-{uuid.uuid4().hex[:8]}"
    key = build_idempotency_key(str(tenant_id), "usage.qualified_inquiry", "inquiry", subject_id)
    resv, created = create_reservation(
        db, tenant_id=str(tenant_id), meter_code="usage.qualified_inquiry",
        subject_type="inquiry", subject_id=subject_id, amount_cents=100,
        idempotency_key=key,
    )
    assert created and resv.status == "created"
    reserve(db, resv, reason="aeos_e2e")
    settle(db, resv, ledger_note="aeos_e2e settle")
    entry = (
        db.query(FinanceLedgerEntry)
        .filter(FinanceLedgerEntry.reference_id == str(resv.id))
        .first()
    )
    assert entry is not None and entry.entry_type == "revenue", "settle 必须恰落一条营收分录"
    reverse(db, resv, reason="aeos_e2e refund")
    reversal = (
        db.query(FinanceLedgerEntry)
        .filter(
            FinanceLedgerEntry.reference_id == str(resv.id),
            FinanceLedgerEntry.category == f"usage.qualified_inquiry:reversal",
            FinanceLedgerEntry.amount_cents < 0,
        )
        .all()
    )
    assert reversal, "reverse 必须留负向冲正分录"
    after = db.query(BillingReservation).filter(BillingReservation.id == resv.id).first()
    assert after.status == "reversed"
    return {
        "reservation_id": str(resv.id),
        "evidence": "预占→结算落账→冲正 全链成立（G9 Event→Ledger→Reverse）",
    }


@stage("meter_reconcile")
def st_reconcile(db) -> dict[str, Any]:
    from app.services.billing.meter_event import MeterEventService

    report = MeterEventService(db).reconcile()
    assert "error_free" in report or "errors" in report, "对账报告结构缺失"
    return {"report_keys": sorted(report.keys()), "evidence": "meter↔ledger 对账可执行"}


@stage("crm_seven_step_transition")
def st_crm(db) -> dict[str, Any]:
    """询盘漏斗 7 步推进 + 别名归一 + 计费幂等（不重复计量）。自建询盘，零残留依赖。"""
    from app.models.inquiry import Inquiry
    from app.models.meter import MeterEvent
    from app.services.inquiry_status_service import advance_inquiry_status

    tenant_id = _latest_tenant_id(db)
    inq = Inquiry(
        id=str(uuid.uuid4()),
        name=f"E2E CRM {uuid.uuid4().hex[:6]}",
        message="E2E CRM stage inquiry",
        status="new",
        is_active=True,
        phone="13800009998",
        email="e2e-crm@example.com",
        tenant_id=str(tenant_id),
    )
    db.add(inq)
    db.commit()
    advance_inquiry_status(db, inq, "in_progress", source="aeos_e2e")
    advance_inquiry_status(db, inq, "quoted", source="aeos_e2e")
    advance_inquiry_status(db, inq, "won", source="aeos_e2e")  # 别名 → closed
    ev_count = (
        db.query(MeterEvent)
        .filter(MeterEvent.event_key == f"inquiry:{inq.id}:qualified")
        .count()
    )
    assert ev_count == 1, "同一询盘只计一次费（幂等）"
    db.refresh(inq)
    assert inq.status == "closed", f"won 别名应归一为 closed，实为 {inq.status}"
    return {"inquiry_id": str(inq.id), "evidence": "new→in_progress→quoted→closed，计量幂等 1 行"}


@stage("api_market_track7")
def st_api_market(db) -> dict[str, Any]:
    """轨7：产品发布→订阅→Key 签发→鉴权计量（api.request）。"""
    from app.models.meter import MeterEvent
    from app.services import api_marketplace_service as mkt

    tenant_id = db.execute(
        text_safe("SELECT id FROM tenants ORDER BY created_at DESC LIMIT 1")
    ).scalar()
    product = mkt.create_product(
        db, name=f"e2e-api-{uuid.uuid4().hex[:6]}", owner_tenant_id=str(tenant_id),
        scope="echo:read",
    )
    mkt.transition_product(db, product, "review")
    mkt.transition_product(db, product, "published")
    mkt.subscribe(db, consumer_tenant_id=str(tenant_id), api_product=product)
    issued = mkt.issue_key(db, tenant_id=str(tenant_id), scopes="echo:read")
    mkt.authorize_call(
        db, raw_key=issued["api_key"], product=product, scope_required="echo:read"
    )
    ev = (
        db.query(MeterEvent)
        .filter(
            MeterEvent.meter_code == "api.request",
            MeterEvent.subject_id == issued["id"],
        )
        .count()
    )
    assert ev == 1, "api.request 计量必须恰 1 条"
    return {"product_id": str(product.id), "evidence": "轨7 发布→订阅→调用→api.request 计量 全链成立"}


# ── 外部依赖 blocked 阶段（诚实登记，绝不伪造）───────────────────────────


@stage("domain_dns_ssl", requires_external="真实域名 DNS/SSL（独立域名商业面）")
def st_domain_blocked(db) -> dict[str, Any]:
    return {"blocked": True}


@stage("real_distribution", requires_external="40+ 平台真实凭据（现 0/50，admitted=0）")
def st_distribution_blocked(db) -> dict[str, Any]:
    return {"blocked": True}


@stage("real_payment_callback", requires_external="真实支付渠道回调（当前仅 mock 渠道）")
def st_payment_blocked(db) -> dict[str, Any]:
    return {"blocked": True}


@stage("real_carrier_tracking", requires_external="真实承运商 Tracking 凭据（KUAIDI100 等）")
def st_tracking_blocked(db) -> dict[str, Any]:
    return {"blocked": True}


@stage("evolution_production_promotion", requires_external="Experience 生产晋升真实证据（G12）")
def st_evolution_blocked(db) -> dict[str, Any]:
    """G12 自进化生产晋升与回滚验证（具备内部状态机与回滚能力，外部真实放行需生产数据证明）。"""
    from app.services.evolution.version_control import VersionControl

    vc = VersionControl(db)
    skill_id = f"e2e_skill_{uuid.uuid4().hex[:6]}"
    v1 = vc.create_skill_version(
        skill_id=skill_id,
        skill_name="E2E Skill",
        bump="minor",
        prompt_template="Prompt v1",
    )
    vc.transition_skill(v1.id, "evaluation")
    vc.transition_skill(v1.id, "canary", canary_percentage=20.0)
    prod_v1 = vc.promote_skill_to_production(
        v1.id, operator_id="e2e_runner", changelog="Prod release"
    )
    assert prod_v1.status == "production"

    # 升级与回滚演练
    v2 = vc.create_skill_version(
        skill_id=skill_id,
        skill_name="E2E Skill",
        bump="minor",
        prompt_template="Prompt v2",
        parent_version_id=v1.id,
    )
    vc.transition_skill(v2.id, "evaluation")
    vc.transition_skill(v2.id, "canary", canary_percentage=50.0)
    prod_v2 = vc.promote_skill_to_production(
        v2.id, operator_id="e2e_runner", changelog="Upgrade v2"
    )
    assert prod_v2.status == "production"
    rolled_back = vc.rollback_skill(
        skill_id, operator_id="e2e_runner", reason="E2E drill rollback"
    )
    assert rolled_back.id == v1.id
    return {"evidence": "G12 状态机与回滚闭环演练验证完成 (v1->v2->rollback v1)"}


def text_safe(sql: str):
    from sqlalchemy import text

    return text(sql)


def run(*, commit_mode: bool = False, drill_mode: bool = False, json_out: Path | None = None) -> int:
    import os

    os.environ.setdefault("SECRET_KEY", "dev_secret_key_12345678901234567890123456789012")
    os.environ.setdefault("JWT_SECRET_KEY", "dev_jwt_key_12345678901234567890123456789012")
    os.environ.setdefault("ENV", "development")

    if commit_mode:
        print("✗ --commit 需真实租户与生产凭据授权（Gate §3），演示链路不得冒充 G15；拒绝执行")
        return 3

    from app.core.database import SessionLocal
    from app.db.session import engine

    # 回滚保证（conftest 同款模式）：Session 绑定到带外层事务的 connection，
    # 结束时 tx.rollback() 丢弃全部痕迹——演示链路不在开发库留任何脏数据。
    connection = engine.connect()
    tx = connection.begin()
    db = SessionLocal(bind=connection)
    results: list[dict[str, Any]] = []
    try:
        for spec in STAGES:
            name = spec["name"]
            if spec.get("requires_external") and not (drill_mode and spec["name"] == "evolution_production_promotion"):
                results.append({
                    "stage": name, "status": "blocked",
                    "blocked_by": spec["requires_external"],
                })
                print(f"  ⛔ blocked  {name} ← {spec['requires_external']}")
                continue
            try:
                detail = spec["fn"](db)
                results.append({"stage": name, "status": "pass", **detail})
                print(f"  ✅ pass     {name} — {detail.get('evidence', '')}")
            except Exception as exc:  # noqa: BLE001
                db.rollback()
                results.append({"stage": name, "status": "fail", "error": f"{type(exc).__name__}: {exc}"})
                print(f"  ❌ FAIL     {name} — {type(exc).__name__}: {exc}")
        tx.rollback()
    finally:
        db.close()
        connection.close()

    passed = sum(1 for r in results if r["status"] == "pass")
    blocked = sum(1 for r in results if r["status"] == "blocked")
    failed = sum(1 for r in results if r["status"] == "fail")
    print("\n═══ AEOS REVENUE LOOP E2E ═══")
    print(f"pass={passed}  blocked={blocked}  fail={failed}")
    verdict = (
        "NOT PASSED" if (blocked or failed) else "PASSED (transactional demo scope)"
    )
    if failed == 0 and blocked == 0:
        verdict = "PASSED (transactional demo scope)"
    print(f"PRODUCTION_GATE (G15): {verdict}")
    if blocked:
        print("  —— blocked 阶段依赖外部生产凭据/基础设施，落地后重跑本脚本累积证据 ——")
    if json_out:
        json_out.write_text(
            json.dumps(
                {
                    "ran_at": datetime.now(timezone.utc).isoformat(),
                    "mode": "transactional-rollback",
                    "verdict": verdict,
                    "results": results,
                },
                ensure_ascii=False, indent=2,
            ),
            encoding="utf-8",
        )
        print(f"证据已落盘: {json_out}")
    return 2 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, default=None, help="证据 JSON 输出路径")
    parser.add_argument("--commit", action="store_true", help="（预留）真实租户提交模式——当前拒绝")
    parser.add_argument("--drill", action="store_true", help="演练模式：真实执行演练代码以验证内部能力闭环")
    args = parser.parse_args()
    return run(commit_mode=args.commit, drill_mode=args.drill, json_out=args.json)


if __name__ == "__main__":
    raise SystemExit(main())
