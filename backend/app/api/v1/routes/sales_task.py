# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Sales Task 路由 — 销售任务队列（管理端）。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.sales_task import SalesTask
from app.models.user import User


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/tasks"
ROUTE_TAGS = ["销售任务"]

router = APIRouter()

# 销售任务状态：单一真相 = SalesTask 模型（open / done / cancelled）
# 写入时接受历史别名并归一，避免前后端枚举分裂导致改状态 400
_STATUS_ALIAS = {
    "pending": "open",
    "in_progress": "open",
    "completed": "done",
    "archived": "cancelled",
}

_CANONICAL_TASK_STATUSES = frozenset({"open", "done", "cancelled"})


def _normalize_task_status(raw: str) -> str | None:
    s = (raw or "").strip().lower()
    if not s:
        return None
    if s in _STATUS_ALIAS:
        return _STATUS_ALIAS[s]
    if s in _CANONICAL_TASK_STATUSES:
        return s
    return None



def _serialize(t: SalesTask) -> dict[str, Any]:
    """执行 serialize 相关逻辑处理。
    
    :param t: 参数 t
    :return: 返回处理结果。
    """
    return {
        "id": str(t.id),
        "title": t.title,
        "description": t.description,
        "task_type": t.task_type,
        "priority": t.priority,
        "status": t.status,
        "due_at": t.due_at.isoformat() if t.due_at else None,
        "assigned_to": t.assigned_to,
        "rfq_id": str(t.rfq_id) if t.rfq_id else None,
        "opportunity_id": t.opportunity_id,
        "company_id": t.company_id,
        "lead_id": t.lead_id,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }


@router.get("", summary="任务列表（管理端）")
def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    task_type: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """执行 list_tasks 相关数据处理。
    
    :param page: 页码
    :param page_size: 每页条数
    :param status: 状态
    :param task_type: 参数 task_type
    :param assigned_to: 参数 assigned_to
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "sales"]:
        return error_response(403, "权限不足")
    q = db.query(SalesTask).filter(SalesTask.deleted_at.is_(None))
    if current_user.role == "sales":
        q = q.filter(SalesTask.assigned_to == str(current_user.id))
    if status:
        normalized = _normalize_task_status(status)
        if normalized is None:
            return error_response(400, f"无效的任务状态 '{status}'，允许值: open, done, cancelled（及别名 pending/completed 等）")
        q = q.filter(SalesTask.status == normalized)
    if task_type:
        q = q.filter(SalesTask.task_type == task_type)
    if assigned_to:
        q = q.filter(SalesTask.assigned_to == assigned_to)
    total = q.count()
    items = (
        q.order_by(SalesTask.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return success_response(
        data={"items": [_serialize(t) for t in items], "total": total, "page": page, "page_size": page_size},
        total=total, page=page, page_size=page_size,
    )


@router.get("/{task_id}", summary="任务详情")
def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 GET /{task_id} 请求，获取相关资源。
    
    :param task_id: 任务ID
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "sales"]:
        return error_response(403, "权限不足")
    t = db.query(SalesTask).filter(SalesTask.id == task_id, SalesTask.deleted_at.is_(None)).first()
    if not t:
        return error_response(404, "任务不存在")
    return success_response(data=_serialize(t))


from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    task_type: Optional[str] = Field("followup", max_length=50)
    priority: Optional[str] = Field("normal", max_length=20)
    due_at: Optional[str] = None
    assigned_to: Optional[str] = Field(None, max_length=36)
    rfq_id: Optional[str] = Field(None, max_length=36)
    opportunity_id: Optional[str] = Field(None, max_length=36)
    company_id: Optional[str] = Field(None, max_length=36)
    lead_id: Optional[str] = Field(None, max_length=36)


@router.post("", summary="创建任务（管理端）")
def create_task(
    body: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """执行 create_task 相关数据处理。
    
    :param body: 请求体
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    due = None
    if body.due_at:
        try:
            due = datetime.fromisoformat(body.due_at.replace("Z", "+00:00"))
        except ValueError:
            due = None
    t = SalesTask(
        title=body.title,
        description=body.description,
        task_type=body.task_type or "followup",
        priority=body.priority or "normal",
        due_at=due,
        assigned_to=body.assigned_to,
        rfq_id=body.rfq_id,
        opportunity_id=body.opportunity_id,
        company_id=body.company_id,
        lead_id=body.lead_id,
        created_by=str(current_user.id),
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return success_response(data=_serialize(t), message="任务已创建")


class TaskStatusUpdate(BaseModel):
    status: str = Field(..., min_length=1, max_length=50)


@router.put("/{task_id}/status", summary="更新任务状态")
def update_task_status(
    task_id: str,
    body: TaskStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 PUT /{task_id}/status 请求，更新相关资源。
    
    :param task_id: 任务ID
    :param body: 请求体
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "sales"]:
        return error_response(403, "权限不足")
    t = db.query(SalesTask).filter(SalesTask.id == task_id, SalesTask.deleted_at.is_(None)).first()
    if not t:
        return error_response(404, "任务不存在")
    new_status = _normalize_task_status(body.status)
    if new_status is None:
        return error_response(400, f"无效的任务状态 '{body.status}'，允许值: open, done, cancelled（及别名 pending/in_progress/completed/archived）")
    t.status = new_status
    db.commit()
    db.refresh(t)
    return success_response(data=_serialize(t), message="任务状态已更新")
