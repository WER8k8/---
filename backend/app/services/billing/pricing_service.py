# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""定价服务（修正设计稿 模块14.2 / 第二层缺口 A）。

- effective_rule：按 meter_code（+可选 plan）取**当时生效**的最新版本
  （status=active 且 effective_from<=at<effective_to，版本号最大者优先）。
- snapshot_for：生成结算快照（写入 billing_reservations.pricing_snapshot，
  模块14.2：规则后续修改不影响已生成快照）。
- amount_for：单价×数量，clamp 到 [minimum, maximum]，先扣 free_quota。

无生效规则时返回诚实默认快照（rule_code=None, version="v0"）——不伪造定价依据。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.pricing_rule import PricingRule


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: Optional[datetime]) -> Optional[datetime]:
    """dialect 容错：sqlite 读回 naive → 视为 UTC；PG 读回 aware 原样。"""
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def effective_rule(
    db: Session,
    *,
    meter_code: str,
    plan_id: Optional[str] = None,
    at: Optional[datetime] = None,
) -> Optional[PricingRule]:
    """当时生效的规则版本：active + 生效窗口命中 + plan 匹配（精确优先于通用），版本号最大。"""
    at = _aware(at or _utcnow())
    rows = (
        db.query(PricingRule)
        .filter(
            PricingRule.meter_code == meter_code,
            PricingRule.status == "active",
        )
        .order_by(PricingRule.version.desc())
        .all()
    )
    best: Optional[PricingRule] = None
    for row in rows:
        eff_from = _aware(row.effective_from)
        eff_to = _aware(row.effective_to)
        if eff_from and eff_from > at:
            continue
        if eff_to and eff_to <= at:
            continue
        if row.plan_id and plan_id and str(row.plan_id) != str(plan_id):
            continue
        if row.plan_id is None and plan_id and best and best.plan_id:
            continue  # 已有套餐专属命中，通用价不覆盖
        if best is None or (row.plan_id is not None and best.plan_id is None):
            best = row
        elif (row.plan_id is not None) == (best.plan_id is not None):
            best = row if row.version >= best.version else best
    return best


def snapshot_for(
    db: Session,
    *,
    meter_code: str,
    plan_id: Optional[str] = None,
    at: Optional[datetime] = None,
) -> dict:
    """生成结算快照（进 reservation.pricing_snapshot；无规则 → 诚实默认 v0）。"""
    rule = effective_rule(db, meter_code=meter_code, plan_id=plan_id, at=at)
    if rule is None:
        return {
            "rule_code": None,
            "version": "v0",
            "unit_price_cents": 0,
            "currency": "CNY",
            "effective_from": None,
            "generated_at": _utcnow().isoformat(),
            "note": "no_active_pricing_rule",
        }
    return {
        "rule_code": rule.rule_code,
        "version": f"v{rule.version}",
        "unit_price_cents": rule.unit_price_cents,
        "currency": rule.currency,
        "free_quota": rule.free_quota,
        "minimum_charge_cents": rule.minimum_charge_cents,
        "maximum_charge_cents": rule.maximum_charge_cents,
        "effective_from": rule.effective_from.isoformat() if rule.effective_from else None,
        "plan_id": str(rule.plan_id) if rule.plan_id else None,
        "generated_at": _utcnow().isoformat(),
    }


def amount_for(snapshot: dict, quantity: int = 1) -> int:
    """按快照计价：单价×数量，先扣免费额度，clamp 到 [min, max]。"""
    unit = int(snapshot.get("unit_price_cents") or 0)
    free = int(snapshot.get("free_quota") or 0)
    billable = max(0, int(quantity or 0) - free)
    amount = unit * billable
    minimum = snapshot.get("minimum_charge_cents")
    maximum = snapshot.get("maximum_charge_cents")
    if minimum is not None and amount < int(minimum):
        amount = int(minimum)
    if maximum is not None and amount > int(maximum):
        amount = int(maximum)
    return amount
