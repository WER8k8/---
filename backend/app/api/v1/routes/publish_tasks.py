"""Publish Task API Routes - Unified Publishing Platform MVP."""
from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, update, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import get_logger
from app.core.security import get_current_user
from app.models.content import PublishTask
from app.models.user import User
from app.models.tenant import UserTenant

logger = get_logger(__name__)
router = APIRouter(prefix="", tags=["统一发布台"])


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
        "data": [
            {
                "id": str(t.id),
                "status": t.status,
                "platform_id": str(t.platform_id),
                "error_message": t.error_message,
                "published_url": t.published_url,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in tasks
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/queue/stats")
def get_queue_stats(
    db: Session = Depends(get_db),
):
    """获取发布队列统计信息。"""
    pending = db.query(func.count()).filter(PublishTask.status == "pending").scalar()
    processing = db.query(func.count()).filter(PublishTask.status == "processing").scalar()
    success = db.query(func.count()).filter(PublishTask.status == "success").scalar()
    failed = db.query(func.count()).filter(PublishTask.status == "failed").scalar()
    return {
        "code": 0,
        "message": "success",
        "data": {
            "pending": pending or 0,
            "processing": processing or 0,
            "success": success or 0,
            "failed": failed or 0,
        },
    }


@router.get("/{task_id}")
def get_publish_task(
    task_id: UUID,
    db: Session = Depends(get_db),
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
):
    """更新发布任务（状态、计划时间等）。"""
    result = db.query(PublishTask).filter(PublishTask.id == str(task_id)).first()
    if not result:
        raise HTTPException(status_code=404, detail="Publish task not found")

    allowed_fields = {"status", "scheduled_time", "publish_type", "max_retries"}
    for field, value in task_data.items():
        if field in allowed_fields and hasattr(result, field):
            setattr(result, field, value)

    db.commit()
    db.refresh(result)
    return result


@router.post("/{task_id}/retry")
def retry_publish_task(
    task_id: UUID,
    db: Session = Depends(get_db),
):
    """重试失败的发布任务。"""
    result = db.query(PublishTask).filter(PublishTask.id == str(task_id)).first()
    if not result:
        raise HTTPException(status_code=404, detail="Publish task not found")

    if result.status != "failed":
        raise HTTPException(status_code=400, detail="Only failed tasks can be retried")

    result.status = "pending"
    result.retry_count = (result.retry_count or 0) + 1
    result.error_message = None
    db.commit()
    db.refresh(result)
    return result
