"""支付运维操作审计 — 探针 / 证书刷新 / staging 自检等落库。"""

from __future__ import annotations

import csv
import json
import uuid
from datetime import datetime, timezone
from io import StringIO
from typing import Any, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.payment import PaymentOpsAudit
from app.models.user import User

OPS_ACTION_ALIPAY_PROBE = "alipay_probe"
OPS_ACTION_WECHAT_PROBE = "wechat_probe"
OPS_ACTION_REFRESH_CERTS = "refresh_certs"
OPS_ACTION_STAGING_SELF_CHECK = "staging_self_check"
OPS_ACTION_PUBLIC_REACHABILITY = "public_reachability"
OPS_ACTION_PUBLIC_NOTIFY = "public_notify_check"

OPS_ACTION_LABELS: dict[str, str] = {
    OPS_ACTION_ALIPAY_PROBE: "支付宝探针",
    OPS_ACTION_WECHAT_PROBE: "微信探针",
    OPS_ACTION_REFRESH_CERTS: "刷新微信证书",
    OPS_ACTION_STAGING_SELF_CHECK: "Staging 自检",
    OPS_ACTION_PUBLIC_REACHABILITY: "公网可达性",
    OPS_ACTION_PUBLIC_NOTIFY: "公网 notify 验收",
}


def list_ops_audit_action_types() -> list[dict[str, str]]:
    """list_ops_audit_action_types。
    :return: 返回处理结果。
    """
    return [{"value": k, "label": v} for k, v in OPS_ACTION_LABELS.items()]


def get_payment_ops_audit(db: Session, audit_id: str) -> Optional[dict[str, Any]]:
    """单条运维审计详情。"""
    row = db.query(PaymentOpsAudit).filter(PaymentOpsAudit.id == audit_id).first()
    if not row:
        return None
    try:
        detail = json.loads(row.detail) if row.detail else {}
    except json.JSONDecodeError:
        detail = {"raw": row.detail}
    actor_id = str(row.actor_user_id) if row.actor_user_id else ""
    actor_name = ""
    if actor_id:
        user = db.query(User.username).filter(User.id == actor_id).first()
        actor_name = user.username if user else actor_id
    return {
        "id": str(row.id),
        "action": row.action,
        "action_label": OPS_ACTION_LABELS.get(row.action, row.action),
        "ok": row.ok,
        "actor_user_id": actor_id,
        "actor_user_name": actor_name,
        "created_at": row.created_at.isoformat() if row.created_at else "",
        "summary": _summarize_detail(row.action, detail),
        "detail": detail,
    }


def log_payment_ops_action(
    db: Session,
    *,
    action: str,
    result: dict[str, Any],
    actor_user_id: Optional[str] = None,
    ok: Optional[bool] = None,
) -> PaymentOpsAudit:
    """记录一次支付运维操作及其结果摘要。"""
    resolved_ok = ok if ok is not None else bool(result.get("ok"))
    row = PaymentOpsAudit(
        id=str(uuid.uuid4()),
        actor_user_id=actor_user_id,
        action=action,
        ok=resolved_ok,
        detail=json.dumps(result, ensure_ascii=False)[:16000],
        created_at=datetime.now(timezone.utc),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_payment_ops_audit_page(
    db: Session,
    *,
    action: Optional[str] = None,
    start_at: Optional[datetime] = None,
    end_at: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """分页查询支付运维审计记录。"""
    q = db.query(PaymentOpsAudit).order_by(desc(PaymentOpsAudit.created_at))
    action_filter = (action or "").strip()
    if action_filter:
        q = q.filter(PaymentOpsAudit.action == action_filter)
    if start_at is not None:
        q = q.filter(PaymentOpsAudit.created_at >= start_at)
    if end_at is not None:
        q = q.filter(PaymentOpsAudit.created_at <= end_at)

    page = max(1, page)
    page_size = min(max(page_size, 1), 100)
    total = q.count()
    rows = q.offset((page - 1) * page_size).limit(page_size).all()
    actor_ids = {str(r.actor_user_id) for r in rows if r.actor_user_id}
    name_map: dict[str, str] = {}
    if actor_ids:
        users = db.query(User.id, User.username).filter(User.id.in_(actor_ids)).all()
        name_map = {str(u.id): u.username for u in users}

    items: list[dict[str, Any]] = []
    for row in rows:
        try:
            detail = json.loads(row.detail) if row.detail else {}
        except json.JSONDecodeError:
            detail = {"raw": row.detail}
        actor_id = str(row.actor_user_id) if row.actor_user_id else ""
        items.append(
            {
                "id": str(row.id),
                "action": row.action,
                "action_label": OPS_ACTION_LABELS.get(row.action, row.action),
                "ok": row.ok,
                "actor_user_id": actor_id,
                "actor_user_name": name_map.get(actor_id, actor_id or ""),
                "created_at": row.created_at.isoformat() if row.created_at else "",
                "summary": _summarize_detail(row.action, detail),
                "detail": detail,
            }
        )

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def _summarize_detail(action: str, detail: dict[str, Any]) -> str:
    """_summarize_detail。

    参数说明：
    :param action: 参数 action
    :param detail: 参数 detail
    :return: 返回处理结果。
    """
    if action in (OPS_ACTION_ALIPAY_PROBE, OPS_ACTION_WECHAT_PROBE):
        pre = detail.get("precreate") or {}
        if isinstance(pre, dict) and pre.get("code_url"):
            return f"precreate ok order={pre.get('order_no', '')}"
        return detail.get("reason") or ("ok" if detail.get("ok") else "failed")
    if action == OPS_ACTION_REFRESH_CERTS:
        if detail.get("refreshed"):
            return f"refreshed serials={len(detail.get('serials') or [])}"
        return detail.get("reason") or "not refreshed"
    if action == OPS_ACTION_STAGING_SELF_CHECK:
        checks = detail.get("checks") or []
        passed = sum(1 for c in checks if c.get("ok"))
        return f"{passed}/{len(checks)} checks passed"
    if action == OPS_ACTION_PUBLIC_REACHABILITY:
        return detail.get("public_url") or detail.get("reason") or ""
    if action == OPS_ACTION_PUBLIC_NOTIFY:
        checks = detail.get("checks") or []
        passed = sum(1 for c in checks if c.get("ok"))
        mode = detail.get("verify_mode") or ""
        suffix = f" ({mode})" if mode else ""
        return f"{passed}/{len(checks)} notify via public{suffix}"
    return detail.get("reason") or ""


_OPS_CSV_HEADERS = [
    "id",
    "created_at",
    "action",
    "action_label",
    "actor_user_name",
    "actor_user_id",
    "ok",
    "summary",
]


def query_payment_ops_audit_rows(
    db: Session,
    *,
    action: Optional[str] = None,
    start_at: Optional[datetime] = None,
    end_at: Optional[datetime] = None,
    limit: int = 5000,
) -> list[dict[str, Any]]:
    """运维审计列表（供 CSV 导出）。"""
    page = list_payment_ops_audit_page(
        db,
        action=action,
        start_at=start_at,
        end_at=end_at,
        page=1,
        page_size=min(max(limit, 1), 10000),
    )
    return page["items"]


def build_payment_ops_audit_csv(rows: list[dict[str, Any]]) -> str:
    """build_payment_ops_audit_csv。

    参数说明：
    :param rows: 参数 rows
    :return: 返回处理结果。
    """
    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(_OPS_CSV_HEADERS)
    for row in rows:
        writer.writerow(
            [
                row.get("id", ""),
                row.get("created_at", ""),
                row.get("action", ""),
                row.get("action_label", ""),
                row.get("actor_user_name") or row.get("actor_user_id") or "",
                row.get("actor_user_id", ""),
                "yes" if row.get("ok") else "no",
                row.get("summary", ""),
            ]
        )
    return buf.getvalue()
