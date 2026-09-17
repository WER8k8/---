# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""操作日志接口"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.admin_auth import get_current_super_admin
from app.core.database import get_db
from app.core.response import success_response
from app.models.user import OperationLog, User

router = APIRouter()


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
    rows = [{
        "id": str(log.id),
        "user_id": str(log.user_id) if log.user_id else None,
        "action": log.action,
        "resource_type": log.resource_type,
        "resource_id": log.resource_id,
        "detail": log.detail,
        "ip_address": log.ip_address,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    } for log in logs]
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


@router.post("")
def create_audit_log(
    body: dict,
    request: Request = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """写入操作日志（替代前端 localStorage 存储）"""
    import uuid
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
