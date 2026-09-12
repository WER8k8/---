"""询盘负责人变更 — 结构化审计（operation_logs）。"""

from __future__ import annotations

import csv
import json
import uuid
from datetime import datetime, timezone
from io import StringIO
from typing import Any, Literal, Optional

from fastapi import Request
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.user import OperationLog, User

INQUIRY_RESOURCE = "inquiry"
ACTION_ASSIGN = "inquiry.assign"
ACTION_AUTO_ASSIGN = "inquiry.auto_assign"
_ASSIGN_ACTIONS = (ACTION_ASSIGN, ACTION_AUTO_ASSIGN)
AssignMode = Literal["manual", "auto"]


def parse_audit_datetime(value: Optional[str], *, end_of_day: bool = False) -> Optional[datetime]:
    """解析导出筛选时间；纯日期 YYYY-MM-DD 按日边界。"""
    raw = (value or "").strip()
    if not raw:
        return None
    text = raw.replace("Z", "+00:00")
    try:
        if len(text) == 10 and text[4] == "-" and text[7] == "-":
            from datetime import date as date_cls
            d = date_cls.fromisoformat(text)
            if end_of_day:
                return datetime(d.year, d.month, d.day, 23, 59, 59, tzinfo=timezone.utc)
            return datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=timezone.utc)
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError as exc:
        raise ValueError(f"无效时间格式: {raw}") from exc


def _client_ip(request: Optional[Request]) -> Optional[str]:
    """_client_ip。

    参数说明：
    :param request: 参数 request
    :return: 返回处理结果。
    """
    if not request:
        return None
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def log_inquiry_assignment(
    db: Session,
    *,
    inquiry_id: str,
    to_assignee_id: str,
    mode: AssignMode,
    from_assignee_id: Optional[str] = None,
    actor_user_id: Optional[str] = None,
    inquiry_name: Optional[str] = None,
    source_channel: Optional[str] = None,
    request: Optional[Request] = None,
) -> OperationLog:
    """记录改派/自动分配；失败不抛出，避免影响主流程。"""
    action = ACTION_AUTO_ASSIGN if mode == "auto" else ACTION_ASSIGN
    to_user = db.query(User).filter(User.id == to_assignee_id).first()
    from_name = None
    if from_assignee_id:
        from_user = db.query(User).filter(User.id == from_assignee_id).first()
        from_name = from_user.username if from_user else from_assignee_id

    detail: dict[str, Any] = {
        "inquiry_id": inquiry_id,
        "inquiry_name": inquiry_name,
        "source_channel": source_channel,
        "mode": mode,
        "from_assignee_id": from_assignee_id,
        "from_assignee_name": from_name,
        "to_assignee_id": to_assignee_id,
        "to_assignee_name": to_user.username if to_user else to_assignee_id,
    }
    if request:
        detail["path"] = str(request.url.path)
        detail["method"] = request.method

    row = OperationLog(
        id=str(uuid.uuid4()),
        user_id=actor_user_id,
        action=action,
        resource_type=INQUIRY_RESOURCE,
        resource_id=inquiry_id,
        detail=json.dumps(detail, ensure_ascii=False)[:8000],
        ip_address=_client_ip(request),
        created_at=datetime.now(timezone.utc),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_assignment_history(
    db: Session,
    inquiry_id: str,
    *,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """list_assignment_history。

    参数说明：
    :param db: 参数 db
    :param inquiry_id: 参数 inquiry_id
    :param limit: 参数 limit
    :return: 返回处理结果。
    """
    rows = (
        db.query(OperationLog)
        .filter(
            OperationLog.resource_type == INQUIRY_RESOURCE,
            OperationLog.resource_id == inquiry_id,
            OperationLog.action.in_(_ASSIGN_ACTIONS),
        )
        .order_by(desc(OperationLog.created_at))
        .limit(min(max(limit, 1), 100))
        .all()
    )
    out: list[dict[str, Any]] = []
    for row in rows:
        try:
            detail = json.loads(row.detail) if row.detail else {}
        except json.JSONDecodeError:
            detail = {"raw": row.detail}
        out.append(
            {
                "id": str(row.id),
                "action": row.action,
                "actor_user_id": str(row.user_id) if row.user_id else None,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "ip_address": row.ip_address,
                **detail,
            }
        )
    return _enrich_actor_names(db, out)


def _enrich_actor_names(db: Session, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """批量 join User 表，补充操作人显示名。"""
    actor_ids = {str(r.get("actor_user_id") or "") for r in rows if r.get("actor_user_id")}
    if not actor_ids:
        for row in rows:
            row.setdefault("actor_user_name", "")
        return rows
    users = db.query(User.id, User.username).filter(User.id.in_(actor_ids)).all()
    name_map = {str(u.id): u.username for u in users}
    for row in rows:
        aid = str(row.get("actor_user_id") or "")
        row["actor_user_name"] = name_map.get(aid, aid)
    return rows


def query_assignment_audit_rows(
    db: Session,
    *,
    start_at: Optional[datetime] = None,
    end_at: Optional[datetime] = None,
    source_channel: Optional[str] = None,
    actor_user_id: Optional[str] = None,
    to_assignee_id: Optional[str] = None,
    limit: int = 5000,
) -> list[dict[str, Any]]:
    """跨询盘改派审计列表（供 CSV 导出 / 分页预览）。"""
    q = (
        db.query(OperationLog)
        .filter(
            OperationLog.resource_type == INQUIRY_RESOURCE,
            OperationLog.action.in_(_ASSIGN_ACTIONS),
        )
        .order_by(desc(OperationLog.created_at))
    )
    if start_at is not None:
        q = q.filter(OperationLog.created_at >= start_at)
    if end_at is not None:
        q = q.filter(OperationLog.created_at <= end_at)
    actor_filter = (actor_user_id or "").strip()
    if actor_filter:
        q = q.filter(OperationLog.user_id == actor_filter)
    cap = min(max(limit, 1), 10000)
    rows = q.limit(cap).all()
    channel_filter = (source_channel or "").strip()
    to_filter = (to_assignee_id or "").strip()
    out: list[dict[str, Any]] = []
    for row in rows:
        try:
            detail = json.loads(row.detail) if row.detail else {}
        except json.JSONDecodeError:
            detail = {"raw": row.detail}
        if channel_filter and detail.get("source_channel") != channel_filter:
            continue
        if to_filter and str(detail.get("to_assignee_id") or "") != to_filter:
            continue
        out.append(
            {
                "log_id": str(row.id),
                "action": row.action,
                "actor_user_id": str(row.user_id) if row.user_id else "",
                "created_at": row.created_at.isoformat() if row.created_at else "",
                "ip_address": row.ip_address or "",
                "inquiry_id": detail.get("inquiry_id") or row.resource_id or "",
                "inquiry_name": detail.get("inquiry_name") or "",
                "source_channel": detail.get("source_channel") or "",
                "mode": detail.get("mode") or "",
                "from_assignee_id": detail.get("from_assignee_id") or "",
                "from_assignee_name": detail.get("from_assignee_name") or "",
                "to_assignee_id": detail.get("to_assignee_id") or "",
                "to_assignee_name": detail.get("to_assignee_name") or "",
            }
        )
    return _enrich_actor_names(db, out)


def list_assignment_audit_page(
    db: Session,
    *,
    start_at: Optional[datetime] = None,
    end_at: Optional[datetime] = None,
    source_channel: Optional[str] = None,
    actor_user_id: Optional[str] = None,
    to_assignee_id: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """改派审计分页预览（与 CSV 导出同源筛选）。"""
    cap = 10000
    rows = query_assignment_audit_rows(
        db,
        start_at=start_at,
        end_at=end_at,
        source_channel=source_channel,
        actor_user_id=actor_user_id,
        to_assignee_id=to_assignee_id,
        limit=cap,
    )
    page = max(1, page)
    page_size = min(max(page_size, 1), 100)
    total = len(rows)
    start_idx = (page - 1) * page_size
    items = rows[start_idx : start_idx + page_size]
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


_CSV_HEADERS = [
    "log_id",
    "created_at",
    "action",
    "mode",
    "inquiry_id",
    "inquiry_name",
    "source_channel",
    "from_assignee_name",
    "to_assignee_name",
    "actor_user_name",
    "actor_user_id",
    "ip_address",
]


def _csv_row_values(row: dict[str, Any]) -> list[Any]:
    """CSV 行：操作人姓名优先于 ID。"""
    actor_name = (row.get("actor_user_name") or "").strip()
    actor_id = (row.get("actor_user_id") or "").strip()
    values = {**row, "actor_user_name": actor_name or actor_id, "actor_user_id": actor_id}
    return [values.get(col, "") for col in _CSV_HEADERS]


def build_assignment_audit_csv(rows: list[dict[str, Any]]) -> str:
    """build_assignment_audit_csv。

    参数说明：
    :param rows: 参数 rows
    :return: 返回处理结果。
    """
    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(_CSV_HEADERS)
    for row in rows:
        writer.writerow(_csv_row_values(row))
    return buf.getvalue()
