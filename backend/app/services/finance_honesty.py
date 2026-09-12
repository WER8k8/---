"""财务实收与汇总诚实过滤 — 排除 mock-pay、种子询盘、探针埋点。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import func, or_
from sqlalchemy.orm import Query, Session

from app.models.finance_ledger import FinanceLedgerEntry
from app.models.inquiry import Inquiry
from app.models.payment import PaymentOrder

MOCK_REVENUE_CATEGORIES = frozenset({"mock_pay"})
MOCK_PAYMENT_CHANNELS = frozenset({"mock", "mock_pay"})
_EXCLUDED_INQUIRY_CHANNELS = frozenset(
    {"dev_seed", "demo", "smoke", "test", "verify", "mock", "seed", "e2e"}
)
_PROBE_SESSION_PREFIXES = ("probe-", "verify-", "smoke-", "dev-seed-", "test-")
_EXCLUDED_INQUIRY_NAMES = frozenset({"e2e", "l3", "l3 test"})


def revenue_ledger_conditions(db: Session) -> tuple:
    """返回 revenue 台账诚实统计用的 SQLAlchemy 条件元组。"""
    mock_refs = [
        row[0]
        for row in db.query(PaymentOrder.order_no)
        .filter(PaymentOrder.channel.in_(tuple(MOCK_PAYMENT_CHANNELS)))
        .all()
    ]
    conds = [
        FinanceLedgerEntry.entry_type == "revenue",
        FinanceLedgerEntry.category.notin_(list(MOCK_REVENUE_CATEGORIES)),
    ]
    if mock_refs:
        conds.append(
            or_(
                FinanceLedgerEntry.reference_id.is_(None),
                ~FinanceLedgerEntry.reference_id.in_(mock_refs),
            )
        )
    return tuple(conds)


def apply_real_revenue_ledger_filters(q: Query, db: Session) -> Query:
    """仅统计真实营收台账（排除 mock_pay 及 mock 渠道订单关联）。"""
    return q.filter(*revenue_ledger_conditions(db))


def apply_real_paid_order_filters(q: Query) -> Query:
    """apply_real_paid_order_filters。

    参数说明：
    :param q: 参数 q
    :return: 返回处理结果。
    """
    return q.filter(
        PaymentOrder.status == "paid",
        PaymentOrder.channel.notin_(list(MOCK_PAYMENT_CHANNELS)),
    )


def is_excluded_inquiry_source(source_channel: str | None) -> bool:
    """is_excluded_inquiry_source。

    参数说明：
    :param source_channel: 参数 source_channel
    :return: 返回处理结果。
    """
    return (source_channel or "").strip().lower() in _EXCLUDED_INQUIRY_CHANNELS


def is_excluded_inquiry_payload(item: dict[str, Any]) -> bool:
    """dict 版排除判断（unified 列表项）。"""
    return is_excluded_inquiry(
        type(
            "_InquiryLike",
            (),
            {
                "source_channel": item.get("source_channel"),
                "name": item.get("name"),
                "message": item.get("message"),
            },
        )()
    )


def is_excluded_inquiry(inquiry: Any) -> bool:
    """排除种子 / E2E / 冒烟询盘，避免数据中心误计转化。"""
    if is_excluded_inquiry_source(getattr(inquiry, "source_channel", None)):
        return True
    name = (getattr(inquiry, "name", None) or "").strip().lower()
    if name in _EXCLUDED_INQUIRY_NAMES or name.startswith("e2e "):
        return True
    message = (getattr(inquiry, "message", None) or "").strip().lower()
    if "e2e inquiry" in message or "自动化追问" in message:
        return True
    return False


def _excluded_inquiry_sql_or():
    """与 is_excluded_inquiry 等价的 SQL 排除条件（用于 COUNT，避免 .all() 拉全表）。"""
    channels = tuple(_EXCLUDED_INQUIRY_CHANNELS)
    names = tuple(_EXCLUDED_INQUIRY_NAMES)
    return or_(
        func.lower(func.coalesce(Inquiry.source_channel, "")).in_(channels),
        func.lower(func.coalesce(Inquiry.name, "")).in_(names),
        func.lower(func.coalesce(Inquiry.name, "")).like("e2e %"),
        func.lower(func.coalesce(Inquiry.message, "")).like("%e2e inquiry%"),
        func.coalesce(Inquiry.message, "").like("%自动化追问%"),
    )


def apply_real_inquiry_filters(q: Query) -> Query:
    """仅保留真实询盘（排除种子 / E2E / 冒烟）。"""
    return q.filter(Inquiry.is_active.is_(True), ~_excluded_inquiry_sql_or())


def count_real_inquiries(
    db: Session,
    *,
    tenant_id: str | None = None,
    status: str | None = None,
    today_start: datetime | None = None,
) -> int:
    """count_real_inquiries。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param status: 参数 status
    :param today_start: 参数 today_start
    :return: 返回处理结果。
    """
    q = apply_real_inquiry_filters(db.query(func.count(Inquiry.id)))
    if tenant_id is not None:
        q = q.filter(Inquiry.tenant_id == str(tenant_id))
    if status is not None:
        q = q.filter(Inquiry.status == status)
    if today_start is not None:
        q = q.filter(Inquiry.created_at >= today_start)
    return int(q.scalar() or 0)


def count_raw_inquiries(
    db: Session,
    *,
    tenant_id: str | None = None,
    status: str | None = None,
) -> int:
    """count_raw_inquiries。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param status: 参数 status
    :return: 返回处理结果。
    """
    q = db.query(func.count(Inquiry.id)).filter(Inquiry.is_active.is_(True))
    if tenant_id is not None:
        q = q.filter(Inquiry.tenant_id == str(tenant_id))
    if status is not None:
        q = q.filter(Inquiry.status == status)
    return int(q.scalar() or 0)


def is_probe_analytics_row(
    *,
    session_id: str | None,
    meta_json: str | None,
) -> bool:
    """is_probe_analytics_row。

    参数说明：
    :param session_id: 参数 session_id
    :param meta_json: 参数 meta_json
    :return: 返回处理结果。
    """
    sid = (session_id or "").strip().lower()
    if sid and any(sid.startswith(p) for p in _PROBE_SESSION_PREFIXES):
        return True
    if not meta_json:
        return False
    try:
        import json
        meta = json.loads(meta_json)
        if not isinstance(meta, dict):
            return False
        return bool(meta.get("probe") or meta.get("smoke") or meta.get("dev_only"))
    except (json.JSONDecodeError, TypeError):
        return False
