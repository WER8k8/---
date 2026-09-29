# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""计费预占/结算服务 —— 修正设计稿 模块18（幂等预占冲正）+ 模块10（轨2 Pay-per-use 底座）。

统一调用链（模块14.1）：业务动作 → Meter Event → Pricing Rule → **Reservation（本模块）**
→ Settlement → Finance Ledger → Invoice/Dashboard。

核心保证（Gate G9）：
- **幂等**：业务幂等身份 `tenant+meter_code+subject+event_version` 唯一约束落库；
  同键重复 create 返回既有记录（created=False），重试/回调重放不会形成第二个有效 charge；
- **状态机**：created → reserved → settled | released；settled → reversed；非法跃迁拒绝；
- **落账一次**：settle 写 finance_ledger 营收分录（append-only）一次；reverse 写负向冲正分录；
  released 不落账（未发生收费）；
- **留痕**：每次跃迁追加 history_json，不覆盖历史；关键跃迁写 Outbox（billing.* 事件）。

红线 R3：只写既有 finance_ledger，不新建账本；四表结构不动。
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.billing_reservation import LEGAL_TRANSITIONS, BillingReservation
from app.models.finance_ledger import FinanceLedgerEntry
from app.models.meter import METER_CODE_BY_TYPE, METER_CODES_PLANNED

logger = logging.getLogger(__name__)


class IllegalTransition(Exception):
    """非法状态跃迁（设计稿 §20：非法跃迁必须被 Service 层拒绝）。"""


class UnknownMeterCode(ValueError):
    """meter_code 不在稳定字符串词表内（禁止序号语义回潮）。"""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def known_meter_codes() -> frozenset[str]:
    """当前合法 meter_code 全集 = 七轨词表 ∪ 既有 7 类的稳定映射。"""
    return frozenset(set(METER_CODES_PLANNED) | set(METER_CODE_BY_TYPE.values()))


def build_idempotency_key(
    tenant_id: str,
    meter_code: str,
    subject_type: str,
    subject_id: str,
    event_version: int = 1,
) -> str:
    """业务幂等身份（设计稿 模块18.2 的规范拼装，全项目唯一定义处）。"""
    return f"bill:{tenant_id}:{meter_code}:{subject_type}:{subject_id}:v{event_version}"


def _append_history(reservation: BillingReservation, from_status: str, reason: Optional[str]) -> None:
    history = list(reservation.history_json or [])
    history.append(
        {
            "from": from_status,
            "to": reservation.status,
            "at": _utcnow().isoformat(),
            **({"reason": reason} if reason else {}),
        }
    )
    reservation.history_json = history


def _transition(db: Session, reservation: BillingReservation, to_status: str, reason: Optional[str]) -> None:
    from_status = reservation.status
    if to_status not in LEGAL_TRANSITIONS.get(from_status, ()):
        raise IllegalTransition(
            f"billing reservation {reservation.id}: {from_status} → {to_status} 非法跃迁（已被拒绝，"
            f"重复结算/重复扣费由此拦截）"
        )
    reservation.status = to_status
    reservation.last_reason = reason
    stamps = {
        "reserved": "reserved_at",
        "settled": "settled_at",
        "released": "released_at",
        "reversed": "reversed_at",
        "failed": "failed_at",
    }
    if to_status in stamps:
        setattr(reservation, stamps[to_status], _utcnow())
    _append_history(reservation, from_status, reason)
    db.add(reservation)


def _outbox(db: Session, reservation: BillingReservation, event_type: str) -> None:
    """关键跃迁写 Outbox（T17 通道；消费随 T10/T14 接线）。"""
    try:
        from app.services.outbox_service import record_outbox_event

        record_outbox_event(
            db,
            event_type=event_type,
            tenant_id=str(reservation.tenant_id),
            aggregate_type="billing_reservation",
            aggregate_id=str(reservation.id),
            payload={
                "meter_code": reservation.meter_code,
                "subject_type": reservation.subject_type,
                "subject_id": reservation.subject_id,
                "amount_cents": reservation.amount_cents,
                "status": reservation.status,
                "idempotency_key": reservation.idempotency_key,
            },
        )
    except Exception:  # noqa: BLE001 —— outbox 故障不阻断计费主链（幂等键仍是最后防线）
        logger.exception("billing outbox emit failed: %s", reservation.id)


# ── 创建（幂等） ─────────────────────────────────────────────


def create_reservation(
    db: Session,
    *,
    tenant_id: str,
    meter_code: str,
    subject_type: str,
    subject_id: str,
    amount_cents: int = 0,
    currency: str = "CNY",
    pricing_rule_version: str = "v0",
    pricing_snapshot: Optional[dict] = None,
    event_version: int = 1,
    idempotency_key: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> tuple[BillingReservation, bool]:
    """创建预占（幂等）。返回 (reservation, created)。

    同一幂等身份重复调用 → 返回既有记录且 created=False（绝不新建第二条）。
    不 commit —— 与调用方业务事务同 commit/rollback（outbox 同纪律）。
    """
    if meter_code not in known_meter_codes():
        raise UnknownMeterCode(
            f"meter_code={meter_code!r} 不在稳定词表（{sorted(known_meter_codes())}）；"
            "禁止引入'第 N 类'序号语义"
        )
    key = idempotency_key or build_idempotency_key(
        str(tenant_id), meter_code, subject_type, str(subject_id), event_version
    )
    existing = (
        db.query(BillingReservation).filter(BillingReservation.idempotency_key == key).first()
    )
    if existing is not None:
        return existing, False

    # 模块14.2：未显式给快照时，按 meter_code(+plan) 取当时生效规则生成快照；
    # 无规则 → 诚实默认 v0（no_active_pricing_rule）。取值在创建时点冻结。
    if pricing_snapshot is None:
        try:
            from app.services.billing.pricing_service import snapshot_for

            pricing_snapshot = snapshot_for(
                db, meter_code=meter_code, plan_id=None, at=_utcnow()
            )
            pricing_rule_version = pricing_snapshot.get("version") or pricing_rule_version
        except Exception:  # noqa: BLE001 —— 定价查询失败不阻断预占（快照走默认）
            pricing_snapshot = {"version": pricing_rule_version, "note": "pricing_lookup_failed"}

    reservation = BillingReservation(
        tenant_id=str(tenant_id),
        meter_code=meter_code,
        subject_type=subject_type,
        subject_id=str(subject_id),
        event_version=event_version,
        idempotency_key=key,
        amount_cents=int(amount_cents or 0),
        currency=currency,
        pricing_rule_version=pricing_rule_version,
        pricing_snapshot=pricing_snapshot or {"pricing_rule_version": pricing_rule_version},
        status="created",
        history_json=[{"from": None, "to": "created", "at": _utcnow().isoformat()}],
        trace_id=trace_id,
    )
    db.add(reservation)
    db.flush()
    return reservation, True


def get_by_idempotency_key(db: Session, key: str) -> Optional[BillingReservation]:
    return db.query(BillingReservation).filter(BillingReservation.idempotency_key == key).first()


# ── 跃迁 ─────────────────────────────────────────────────────


def reserve(db: Session, reservation: BillingReservation, *, reason: Optional[str] = None) -> BillingReservation:
    """created → reserved。预算检查钩子（plan_gate/wallet_guard）随 T10 接入。"""
    _transition(db, reservation, "reserved", reason or "reserve")
    _outbox(db, reservation, "billing.reserved")
    db.commit()
    return reservation


def settle(
    db: Session,
    reservation: BillingReservation,
    *,
    ledger_note: Optional[str] = None,
) -> BillingReservation:
    """reserved → settled，并落 finance_ledger 营收分录（恰好一条）。"""
    _transition(db, reservation, "settled", ledger_note or "settle")
    entry = FinanceLedgerEntry(
        entry_type="revenue",
        category=reservation.meter_code,
        amount_cents=int(reservation.amount_cents or 0),
        tenant_id=reservation.tenant_id,
        reference_id=str(reservation.id),
        note=ledger_note
        or f"{reservation.meter_code} {reservation.subject_type}/{reservation.subject_id} "
        f"@ {reservation.pricing_rule_version}",
    )
    db.add(entry)
    db.flush()
    reservation.finance_entry_id = entry.id
    db.add(reservation)
    _outbox(db, reservation, "billing.settled")
    db.commit()
    return reservation


def release(db: Session, reservation: BillingReservation, *, reason: str) -> BillingReservation:
    """reserved/created → released（执行失败/取消；未收费，不落账）。"""
    _transition(db, reservation, "released", reason)
    _outbox(db, reservation, "billing.released")
    db.commit()
    return reservation


def reverse(db: Session, reservation: BillingReservation, *, reason: str) -> BillingReservation:
    """settled → reversed，并写负向冲正分录（退款/取消）。"""
    _transition(db, reservation, "reversed", reason)
    entry = FinanceLedgerEntry(
        entry_type="revenue",
        category=f"{reservation.meter_code}:reversal",
        amount_cents=-int(reservation.amount_cents or 0),
        tenant_id=reservation.tenant_id,
        reference_id=str(reservation.id),
        note=f"reverse: {reason} (原分录 {reservation.finance_entry_id})",
    )
    db.add(entry)
    db.flush()
    reservation.reversal_entry_id = entry.id
    db.add(reservation)
    _outbox(db, reservation, "billing.reversed")
    db.commit()
    return reservation


def fail(db: Session, reservation: BillingReservation, *, reason: str) -> BillingReservation:
    """created/reserved → failed（终态；保留原因供运营排查）。"""
    _transition(db, reservation, "failed", reason)
    db.commit()
    return reservation
