# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""IP 槽位加购 — 支付成功后增加租户 egress_ip_quota。"""

from __future__ import annotations

import json
import logging
import re

from sqlalchemy.orm import Session

from app.models.payment import PaymentOrder
from app.models.tenant import Tenant
from app.services.egress_quota_service import auto_assign_slots_for_tenant

logger = logging.getLogger(__name__)

ADDON_SUBJECT_RE = re.compile(r"\[addon:egress_ip:(\d+)\]", re.I)

# 单价（分）/ 每槽位，演示环境
EGRESS_SLOT_PRICE_CENTS = 9900


def parse_addon_slots(subject: str) -> int | None:
    """parse_addon_slots。

    参数说明：
    :param subject: 参数 subject
    :return: 返回处理结果。
    """
    m = ADDON_SUBJECT_RE.search(subject or "")
    if not m:
        return None
    return max(1, min(50, int(m.group(1))))


def addon_subject(slots: int) -> str:
    """addon_subject。

    参数说明：
    :param slots: 参数 slots
    :return: 返回处理结果。
    """
    return f"[addon:egress_ip:{slots}] IP 槽位加购 x{slots}"


def _read_settings(tenant: Tenant) -> dict:
    """_read_settings。

    参数说明：
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    raw = tenant.settings or "{}"
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def bump_egress_quota(db: Session, tenant: Tenant, slots: int) -> dict:
    """增加租户 egress_ip_quota 并尝试分配槽位。"""
    cfg = _read_settings(tenant)
    current = int(cfg.get("egress_ip_quota") or 0)
    cfg["egress_ip_quota"] = current + slots
    tenant.settings = json.dumps(cfg, ensure_ascii=False)
    try:
        assigned = auto_assign_slots_for_tenant(db, tenant, count=slots)
        db.commit()
        return {"quota_before": current, "quota_after": current + slots, "slots_assigned": assigned}
    except Exception as exc:
        db.rollback()
        logger.error("自动分配 egress IP 槽位失败 tenant=%s slots=%d: %s", tenant.id, slots, exc, exc_info=True)
        raise


def apply_order_addon(db: Session, order: PaymentOrder) -> dict | None:
    """兼容旧 import 路径，转发至统一 order_addon_service。"""
    from app.services.order_addon_service import apply_order_addon as _apply
    return _apply(db, order)
