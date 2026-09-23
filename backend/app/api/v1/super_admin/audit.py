# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""操作日志接口"""

import csv
import io
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.admin_auth import get_current_super_admin
from app.core.database import get_db
from app.core.response import success_response
from app.models.user import OperationLog, User

router = APIRouter()


def _parse_detail_diff(detail: Optional[str]) -> dict:
    if not detail:
        return {"before": None, "after": None, "diff": None}
    try:
        obj = json.loads(detail)
    except (TypeError, ValueError):
        return {"before": None, "after": None, "diff": None}
    if not isinstance(obj, dict):
        return {"before": None, "after": None, "diff": None}
    before = obj.get("before")
    after = obj.get("after")
    diff = obj.get("diff")
    if diff is None and isinstance(before, dict) and isinstance(after, dict):
        keys = set(before) | set(after)
        diff = {
            k: {"before": before.get(k), "after": after.get(k)}
            for k in sorted(keys)
            if before.get(k) != after.get(k)
        }
    return {"before": before, "after": after, "diff": diff}


def _log_row(log: OperationLog) -> dict:
    parsed = _parse_detail_diff(log.detail)
    return {
        "id": str(log.id),
        "user_id": str(log.user_id) if log.user_id else None,
        "action": log.action,
        "resource_type": log.resource_type,
        "resource_id": log.resource_id,
        "detail": log.detail,
        "before": parsed["before"],
        "after": parsed["after"],
        "diff": parsed["diff"],
        "ip_address": log.ip_address,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }


@router.get("")
def list_audit_logs(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
):
    """操作日志列表"""
    query = db.query(OperationLog).order_by(desc(OperationLog.created_at))
    if user_id:
        query = query.filter(OperationLog.user_id == user_id)
    if action:
        query = query.filter(OperationLog.action == action)
    if resource_type:
        query = query.filter(OperationLog.resource_type == resource_type)
    if start_time:
        query = query.filter(
            OperationLog.created_at >= start_time.replace(tzinfo=timezone.utc)
        )
    if end_time:
        query = query.filter(
            OperationLog.created_at <= end_time.replace(tzinfo=timezone.utc)
        )

    total = query.count()
    logs = query.offset((page - 1) * page_size).limit(page_size).all()
    rows = [_log_row(log) for log in logs]
    return success_response(data=rows, total=total, page=page, page_size=page_size)


@router.get("/actions")
def list_audit_actions(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """获取所有操作类型列表（用于筛选器）"""
    from sqlalchemy import distinct
    actions = db.query(distinct(OperationLog.action)).order_by(OperationLog.action).all()
    resource_types = db.query(distinct(OperationLog.resource_type)).order_by(OperationLog.resource_type).all()
    return success_response(data={
        "actions": [a[0] for a in actions if a[0]],
        "resource_types": [r[0] for r in resource_types if r[0]],
    })


@router.get("/export")
def export_audit_logs_csv(
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
    user_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    limit: int = Query(5000, ge=1, le=20000),
):
    """导出操作日志 CSV"""
    from app.core.data_export_guard import assert_export_allowed
    assert_export_allowed(
        db,
        admin,
        request,
        export_kind="super_admin_audit_csv",
        scope="platform",
    )
    query = db.query(OperationLog).order_by(desc(OperationLog.created_at))
    if user_id:
        query = query.filter(OperationLog.user_id == user_id)
    if action:
        query = query.filter(OperationLog.action == action)
    if resource_type:
        query = query.filter(OperationLog.resource_type == resource_type)
    if start_time:
        query = query.filter(
            OperationLog.created_at >= start_time.replace(tzinfo=timezone.utc)
        )
    if end_time:
        query = query.filter(
            OperationLog.created_at <= end_time.replace(tzinfo=timezone.utc)
        )
    logs = query.limit(limit).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "用户ID", "操作", "资源类型", "资源ID",
        "详情", "Before", "After", "IP", "时间",
    ])
    for log in logs:
        parsed = _parse_detail_diff(log.detail)
        writer.writerow([
            str(log.id),
            str(log.user_id) if log.user_id else "",
            log.action,
            log.resource_type,
            log.resource_id or "",
            (log.detail or "").replace("\n", " "),
            json.dumps(parsed["before"], ensure_ascii=False) if parsed["before"] is not None else "",
            json.dumps(parsed["after"], ensure_ascii=False) if parsed["after"] is not None else "",
            log.ip_address or "",
            log.created_at.isoformat() if log.created_at else "",
        ])
    csv_text = output.getvalue()
    return StreamingResponse(
        iter([csv_text]),
        media_type="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": 'attachment; filename="audit_logs_export.csv"'},
    )


@router.get("/{log_id}")
def get_audit_log(
    log_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """操作日志详情（含 before/after diff）"""
    log = db.query(OperationLog).filter(OperationLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="日志不存在")
    return success_response(data=_log_row(log))


@router.post("")
def create_audit_log(
    body: dict,
    request: Request = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """写入操作日志（替代前端 localStorage 存储）"""
    log = OperationLog(
        id=str(uuid.uuid4()),
        user_id=admin.id,
        action=body.get("action", "custom"),
        resource_type=body.get("resource_type", "ui_state"),
        resource_id=body.get("resource_id", ""),
        detail=body.get("detail", ""),
        ip_address=request.client.host if request and request.client else None,
    )
    db.add(log)
    db.commit()
    return success_response(data={"id": str(log.id)}, message="日志已记录")


@router.delete("")
def clear_audit_logs(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
    before_date: Optional[datetime] = Query(None),
):
    """批量清除操作日志"""
    query = db.query(OperationLog)
    if before_date:
        query = query.filter(
            OperationLog.created_at <= before_date.replace(tzinfo=timezone.utc)
        )

    deleted = query.delete()
    db.commit()
    return success_response(message=f"已删除 {deleted} 条日志")


@router.delete("/{log_id}")
def delete_audit_log(
    log_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """删除单条操作日志"""
    log = db.query(OperationLog).filter(OperationLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="日志不存在")
    db.delete(log)
    db.commit()
    return success_response(message="日志已删除")
