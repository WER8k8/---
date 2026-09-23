# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Publish Task API Routes - Unified Publishing Platform MVP."""
from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, update, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import get_logger
from app.core.security import get_current_user
from app.models.content import PublishLog, PublishTask
from app.models.user import User
from app.models.tenant import UserTenant

logger = get_logger(__name__)
router = APIRouter(prefix="", tags=["统一发布台"])

# 有向迁移：from → 允许的 to（禁止 frozenset 无序边表）
# pending_review → approved | rejected（超管/租户管理员审核门禁）
# approved → pending（入队）| cancelled
# pending → processing | failed | cancelled
# processing → success | failed
# failed → pending（重试）| failure_reviewed（失败归因复核标记）| cancelled
PUBLISH_TASK_TRANSITIONS: dict[str, frozenset[str]] = {
    "draft": frozenset({"pending_review", "cancelled"}),
    "pending_review": frozenset({"approved", "rejected", "cancelled"}),
    "approved": frozenset({"pending", "cancelled"}),
    "pending": frozenset({"processing", "failed", "cancelled", "pending_review"}),
    "processing": frozenset({"success", "failed"}),
    "success": frozenset(),
    "failed": frozenset({"pending", "failure_reviewed", "cancelled"}),
    "failure_reviewed": frozenset({"pending", "cancelled"}),
    "rejected": frozenset(),
    "cancelled": frozenset(),
}

REVIEWABLE_STATUSES = frozenset({"pending_review"})
ADMIN_ROLES = frozenset({"admin", "super_admin", "tenant_admin"})


def _publish_can_transition(from_status: str, to_status: str) -> bool:
    return to_status in PUBLISH_TASK_TRANSITIONS.get(from_status, frozenset())


def _assert_admin(user: User) -> None:
    if user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="仅超管/租户管理员可审核发布任务")


class PublishReviewBody(BaseModel):
    action: str = Field(..., pattern="^(approve|reject)$")
    reason: Optional[str] = Field(None, max_length=500)


class FailureReviewBody(BaseModel):
    attribution: str = Field(..., min_length=2, max_length=500, description="失败归因结论")
    note: Optional[str] = Field(None, max_length=500)


def _task_view(t: PublishTask) -> dict[str, Any]:
    return {
        "id": str(t.id),
        "status": t.status,
        "platform_id": str(t.platform_id),
        "error_message": t.error_message,
        "published_url": t.published_url,
        "retry_count": t.retry_count,
        "max_retries": t.max_retries,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "allowed_next": sorted(PUBLISH_TASK_TRANSITIONS.get(t.status or "", frozenset())),
    }


@router.get("")
def list_publish_tasks(
    tenant_id: Optional[UUID] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    platform_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取租户的发布任务列表。"""
    if not tenant_id:
        link = db.query(UserTenant).filter(
            UserTenant.user_id == current_user.id,
            UserTenant.is_active == True,
        ).first()
        if not link:
            raise HTTPException(status_code=403, detail="No active tenant found")
        tenant_id = link.tenant_id

    query = db.query(PublishTask).filter(PublishTask.tenant_id == str(tenant_id))
    if status_filter:
        query = query.filter(PublishTask.status == status_filter)
    if platform_id:
        query = query.filter(PublishTask.platform_id == platform_id)

    total = query.count()
    skip = (page - 1) * page_size
    tasks = query.order_by(PublishTask.created_at.desc()).offset(skip).limit(page_size).all()
    return {
        "code": 0,
        "message": "success",
        "data": [_task_view(t) for t in tasks],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/queue/stats")
def get_queue_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取发布队列统计信息。"""
    pending = db.query(func.count()).filter(PublishTask.status == "pending").scalar()
    processing = db.query(func.count()).filter(PublishTask.status == "processing").scalar()
    success = db.query(func.count()).filter(PublishTask.status == "success").scalar()
    failed = db.query(func.count()).filter(PublishTask.status == "failed").scalar()
    pending_review = db.query(func.count()).filter(PublishTask.status == "pending_review").scalar()
    failure_reviewed = db.query(func.count()).filter(PublishTask.status == "failure_reviewed").scalar()
    return {
        "code": 0,
        "message": "success",
        "data": {
            "pending": pending or 0,
            "processing": processing or 0,
            "success": success or 0,
            "failed": failed or 0,
            "pending_review": pending_review or 0,
            "failure_reviewed": failure_reviewed or 0,
        },
    }


@router.get("/{task_id}")
def get_publish_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """根据 ID 获取发布任务。"""
    result = db.query(PublishTask).filter(PublishTask.id == str(task_id)).first()
    if not result:
        raise HTTPException(status_code=404, detail="Publish task not found")
    return result


@router.put("/{task_id}")
def update_publish_task(
    task_id: UUID,
    task_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新发布任务（状态受有向状态机约束、计划时间等）。"""
    result = db.query(PublishTask).filter(PublishTask.id == str(task_id)).first()
    if not result:
        raise HTTPException(status_code=404, detail="Publish task not found")

    allowed_fields = {"status", "scheduled_time", "publish_type", "max_retries"}
    for field, value in task_data.items():
        if field not in allowed_fields or not hasattr(result, field):
            continue
        if field == "status":
            if not _publish_can_transition(result.status or "", str(value)):
                raise HTTPException(
                    status_code=400,
                    detail=f"illegal status transition {result.status} -> {value}",
                )
            # 审核态跃迁须走专用端点留痕，PUT 不允许直接审过
            if str(value) in ("approved", "rejected") and result.status == "pending_review":
                raise HTTPException(status_code=400, detail="请使用 /review 审核，禁止 PUT 直改审核态")
        setattr(result, field, value)

    db.commit()
    db.refresh(result)
    return result


@router.post("/{task_id}/review")
def review_publish_task(
    task_id: UUID,
    body: PublishReviewBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """发布审核门禁：pending_review → approved / rejected（超管/租户管理员）。"""
    _assert_admin(current_user)
    result = db.query(PublishTask).filter(PublishTask.id == str(task_id)).first()
    if not result:
        raise HTTPException(status_code=404, detail="Publish task not found")
    target = "approved" if body.action == "approve" else "rejected"
    if (result.status or "") not in REVIEWABLE_STATUSES:
        raise HTTPException(status_code=400, detail=f"Only pending_review tasks can be reviewed, got {result.status}")
    if not _publish_can_transition(result.status or "", target):
        raise HTTPException(status_code=400, detail=f"illegal status transition {result.status} -> {target}")
    result.status = target
    if body.reason:
        result.error_message = (f"[{target}] {body.reason}")[:500] if target == "rejected" else result.error_message
    if target == "approved":
        # 审过 → 入队等待执行
        if _publish_can_transition("approved", "pending"):
            result.status = "pending"
        db.add(PublishLog(task_id=str(result.id), level="info", message=f"approved by {current_user.username or current_user.id}"))
    else:
        db.add(PublishLog(task_id=str(result.id), level="warning", message=f"rejected: {body.reason or ''}"))
    db.commit()
    db.refresh(result)
    return {"code": 0, "message": "reviewed", "data": _task_view(result)}


@router.post("/{task_id}/failure-review")
def failure_review_publish_task(
    task_id: UUID,
    body: FailureReviewBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """失败归因复核标记：failed → failure_reviewed（禁止失败后无下文）。"""
    _assert_admin(current_user)
    result = db.query(PublishTask).filter(PublishTask.id == str(task_id)).first()
    if not result:
        raise HTTPException(status_code=404, detail="Publish task not found")
    if not _publish_can_transition(result.status or "", "failure_reviewed"):
        raise HTTPException(status_code=400, detail=f"当前状态 {result.status} 不可标记失败归因")
    result.status = "failure_reviewed"
    result.error_message = (f"[归因] {body.attribution}" + (f" | {body.note}" if body.note else ""))[:500]
    db.add(
        PublishLog(
            task_id=str(result.id),
            level="warning",
            message=f"failure_reviewed by {current_user.username or current_user.id}: {body.attribution}",
        )
    )
    db.commit()
    db.refresh(result)
    return {"code": 0, "message": "failure reviewed", "data": _task_view(result)}


@router.post("/{task_id}/retry")
def retry_publish_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """重试失败/已归因的发布任务。"""
    result = db.query(PublishTask).filter(PublishTask.id == str(task_id)).first()
    if not result:
        raise HTTPException(status_code=404, detail="Publish task not found")

    if not _publish_can_transition(result.status or "", "pending"):
        raise HTTPException(status_code=400, detail="Only failed/failure_reviewed tasks can be retried")

    result.status = "pending"
    result.retry_count = (result.retry_count or 0) + 1
    result.error_message = None
    db.commit()
    db.refresh(result)
    return result
