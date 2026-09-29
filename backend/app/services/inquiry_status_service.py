# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""询盘状态推进唯一汇聚点（模块 10 计费时点 · 模块 14 计量链）。

全仓 `inquiries.status` 的写入**必须**经本函数（禁止任何直写），职责严格按序：

1. 别名归一（pending→new、contacted→in_progress、won/deal→closed、lost/spam→archived 等）；
2. 归一后状态 ∈ VALID_STATUSES，否则 `ValueError`（可判定）；
3. 跃迁合法（复用 `can_transition`），非法 `IllegalTransition`；
4. 记录归一前旧状态，写 `inquiry.status = 归一后新状态`，commit；
5. **计费时点（模块 10 · 轨 2 Pay-per-use）**：归一后状态 ∈ `BILLABLE_QUALIFIED_STAGES`
   （显式集合，**不含 archived**；**严禁**用 `FUNNEL_STAGES.index` 下标比较 ——
    archived 下标 7 > in_progress 的 1，会把 spam/lost 误判为计费阶段）
   且此前无 `event_key=inquiry:{id}:qualified` 的计量行
   且 `tenant_id` 非空 且 联系方式（phone/email 至少一项）齐全
   → 写一条 `usage.qualified_inquiry` 计量（`event_key` 幂等）。
   显式集合覆盖 new→quoted 直跳（跳过 in_progress），修复漏收。
6. 条件不满足记**结构化日志**（含 `event_key` 与不满足的原因），**禁止静默失败**
   —— 漏收比报错更糟。

设计依据：`docs/模块9-11-14-计费与对账收口契约-2026-09-27.md` §6（唯一触发点）。
"""
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.models.inquiry import Inquiry
from app.models.meter import MeterEvent
from app.services.billing.meter_event import MeterEventService
from app.services.billing.reservation_service import IllegalTransition
from app.services.inquiry_funnel_state_machine import (
    VALID_STATUSES,
    can_transition,
    normalize,
)

logger = logging.getLogger("uj.billing.qualified_inquiry")

# 计费时点：归一后落在此集合内才视为「合格询盘」（设计 10.3 validation → qualification）。
# 显式列举、不含 archived —— 防止「下标比较」把归档态误判为计费阶段。
BILLABLE_QUALIFIED_STAGES = frozenset({
    "in_progress", "quoted", "accepted", "processing", "resolved", "closed",
})
_QUALIFIED_METER_CODE = "usage.qualified_inquiry"
_QUALIFIED_SUBJECT_TYPE = "inquiry"


def _has_contact_channel(inquiry: Inquiry) -> bool:
    """联系方式校验：手机或邮箱至少一项（与 PublicInquiryCreate.require_contact_channel 同口径）。"""
    phone = (getattr(inquiry, "phone", None) or "").strip()
    email = (getattr(inquiry, "email", None) or "").strip()
    return bool(phone or email)


def _emit_qualified_inquiry(
    db: Session,
    inquiry: Inquiry,
    *,
    source: str,
    actor_id: Optional[str],
    from_status: str,
    to_status: str,
) -> Optional[MeterEvent]:
    """计费时点判定 + 幂等计量写入。返回计量事件；未计费返回 None。"""
    event_key = f"inquiry:{inquiry.id}:qualified"

    if to_status not in BILLABLE_QUALIFIED_STAGES:
        # 非计费阶段（回退/重开为 new、归档 archived 等）：本就不应计费，非漏收
        logger.debug(
            "qualified_inquiry 跳过（非计费阶段） event_key=%s from=%s to=%s",
            event_key, from_status, to_status,
        )
        return None

    # 幂等：同一询盘只计一次（event_key 唯一约束为最后防线）
    existing = db.query(MeterEvent).filter(MeterEvent.event_key == event_key).first()
    if existing is not None:
        logger.info("qualified_inquiry 幂等命中（不重复计费） event_key=%s", event_key)
        return existing

    tenant_id = str(getattr(inquiry, "tenant_id", "") or "").strip()
    if not tenant_id:
        logger.warning(
            "qualified_inquiry 未计费：tenant_id 为空 event_key=%s inquiry_id=%s from=%s to=%s",
            event_key, inquiry.id, from_status, to_status,
        )
        return None
    if not _has_contact_channel(inquiry):
        logger.warning(
            "qualified_inquiry 未计费：无有效联系方式（phone/email 均空） event_key=%s inquiry_id=%s",
            event_key, inquiry.id,
        )
        return None

    try:
        event = MeterEventService(db).emit(
            meter_type="lead_generated",
            tenant_id=tenant_id,
            event_key=event_key,
            quantity=1,
            unit="lead",
            source_ref_type="lead",
            source_ref_id=str(inquiry.id),
            meter_code=_QUALIFIED_METER_CODE,
            subject_type=_QUALIFIED_SUBJECT_TYPE,
            subject_id=str(inquiry.id),
            bill_status="unlinked",
            metadata={
                "meter_code": _QUALIFIED_METER_CODE,
                "from": from_status,
                "to": to_status,
                "source": source,
                "actor_id": actor_id,
            },
        )
    except Exception:  # noqa: BLE001 —— 计量失败绝不静默：留证据供运维补齐（漏收比报错更糟）
        logger.exception(
            "qualified_inquiry 计量写入失败 event_key=%s inquiry_id=%s tenant_id=%s",
            event_key, inquiry.id, tenant_id,
        )
        return None

    logger.info(
        "qualified_inquiry 已计费 event_key=%s inquiry_id=%s tenant_id=%s event_id=%s "
        "from=%s to=%s source=%s",
        event_key, inquiry.id, tenant_id, getattr(event, "id", None),
        from_status, to_status, source,
    )

    # ── 轨2 预占（billing_reservations，契约 §8.2，09-28 接线）：
    # 由独立开关 BILLING_GATE_ENABLED（默认 False，R-3 备选解耦）控制，不复用
    # TASK_CONTROL_ENABLED（其同时门控 Trace/终态钩子，dev 实测为 True）。
    # 预占失败只留日志、不回滚计量（漏收比报错更糟；计量已落库）。
    _maybe_reserve_qualified_inquiry(db, inquiry, event=event, tenant_id=tenant_id)
    return event


def _maybe_reserve_qualified_inquiry(
    db: Session,
    inquiry: Inquiry,
    *,
    event: Optional[MeterEvent],
    tenant_id: str,
) -> None:
    """BILLING_GATE_ENABLED 开启时，为合格询盘创建计费预占（幂等）。

    幂等键 = bill:{tenant}:usage.qualified_inquiry:inquiry:{id}:v1
    （build_idempotency_key 规范拼装），同键重推返回既有行不增行；
    无 Pricing Rule 时 pricing_rule_version=v0、amount_cents=0（契约 §8.2 口径）。
    预占成功后把计量行 bill_status unlinked→reserved，建立 meter↔reservation 关联。
    失败面用 SAVEPOINT 包裹：只回滚预占本身，绝不波及已落库的询盘与计量。
    """
    from app.core.config import settings

    if not getattr(settings, "BILLING_GATE_ENABLED", False):
        return
    try:
        from app.services.billing.reservation_service import (
            build_idempotency_key,
            create_reservation,
        )

        with db.begin_nested():
            reservation, created = create_reservation(
                db,
                tenant_id=tenant_id,
                meter_code=_QUALIFIED_METER_CODE,
                subject_type=_QUALIFIED_SUBJECT_TYPE,
                subject_id=str(inquiry.id),
                idempotency_key=build_idempotency_key(
                    tenant_id, _QUALIFIED_METER_CODE, _QUALIFIED_SUBJECT_TYPE, str(inquiry.id),
                ),
            )
            if created and event is not None:
                event.bill_status = "reserved"
        db.commit()
        logger.info(
            "qualified_inquiry 预占%s reservation_id=%s inquiry_id=%s",
            "新建" if created else "幂等命中（不增行）",
            getattr(reservation, "id", None), inquiry.id,
        )
    except Exception:  # noqa: BLE001 —— 预占失败不阻断询盘主链路，留证据
        logger.exception(
            "qualified_inquiry 预占失败（不阻断主链路） inquiry_id=%s", inquiry.id
        )


def advance_inquiry_status(
    db: Session,
    inquiry: Inquiry,
    new_status: str,
    *,
    source: str,
    actor_id: Optional[str] = None,
) -> Inquiry:
    """询盘状态推进唯一入口（白名单 + 漏斗守卫 + 计费时点）。

    :raises ValueError: 归一后状态不在 VALID_STATUSES。
    :raises IllegalTransition: 漏斗跃迁非法（回退/跨跳）。
    """
    from_status_raw = inquiry.status
    from_status = normalize(from_status_raw)
    to_status = normalize(new_status)

    # 2. 白名单（归一后必须是漏斗已知状态）
    if to_status not in VALID_STATUSES:
        raise ValueError(
            f"无效的询盘状态 {new_status!r}，允许值: {', '.join(sorted(VALID_STATUSES))}"
        )

    # 3. 跃迁守卫（前进-only + 显式重开）
    ok, reason = can_transition(from_status_raw, to_status)
    if not ok:
        raise IllegalTransition(
            f"询盘状态流转被拒绝: {reason}（当前: {from_status_raw} → 目标: {new_status}）"
        )

    # 4. 落库归一后状态（记录归一前旧状态）
    inquiry.status = to_status
    db.commit()
    db.refresh(inquiry)

    # 5. 计费时点（模块 10 · 轨 2）
    _emit_qualified_inquiry(
        db, inquiry,
        source=source, actor_id=actor_id,
        from_status=from_status, to_status=to_status,
    )
    return inquiry
