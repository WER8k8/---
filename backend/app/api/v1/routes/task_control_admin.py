# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""统一任务控制面管理与人审干预 API 路由 (Human-in-the-Loop)。

对接 TaskControlService 与 AiTask：
- GET /api/v1/task-control/pending-reviews: 获取等待人审 (review / wait_human) 的任务列表
- POST /api/v1/task-control/{task_id}/resume: 人工审核放行 / 恢复执行
- POST /api/v1/task-control/{task_id}/cancel: 人工终止取消任务
- POST /api/v1/task-control/{task_id}/retry: 人工介入触发受控重试
- GET /api/v1/task-control/{task_id}: 查看任务详情与状态
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import get_logger
from app.core.security import get_current_user
from app.models.ai_task import AiTask
from app.models.tenant import UserTenant
from app.models.user import User
from app.services.tasks.task_control import (
    InvalidTaskTransition,
    REVIEW,
    TaskControlError,
    TaskControlService,
    TaskNotFound,
    WAIT_HUMAN,
)

logger = get_logger(__name__)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/task-control"
ROUTE_TAGS = ["任务控制面管理"]

router = APIRouter(prefix="", tags=["任务控制面管理"])


class TaskResumeRequest(BaseModel):
    comment: Optional[str] = Field(None, description="放行审批意见或备注")


class TaskCancelRequest(BaseModel):
    reason: Optional[str] = Field(None, description="取消原因")


def _resolve_tenant_id(
    db: Session,
    current_user: User,
    tenant_id: Optional[str] = None,
) -> str:
    """解析当前用户关联的租户 ID。超级管理员可显式指定租户，普通用户自动解析。"""
    if tenant_id:
        if getattr(current_user, "is_superuser", False) or getattr(current_user, "role", "") == "super_admin":
            return str(tenant_id)

    link = (
        db.query(UserTenant)
        .filter(
            UserTenant.user_id == current_user.id,
            UserTenant.is_active == True,
        )
        .first()
    )
    if link:
        return str(link.tenant_id)
    if tenant_id:
        return str(tenant_id)
    raise HTTPException(status_code=403, detail="No active tenant found for current user")


def _task_to_dict(task: AiTask) -> dict[str, Any]:
    return {
        "id": str(task.id),
        "tenant_id": str(task.tenant_id),
        "task_type": task.task_type,
        "status": task.status,
        "priority": task.priority,
        "retry_count": task.retry_count,
        "error_message": task.error_message,
        "input_json": task.input_json,
        "output_json": task.output_json,
        "trace_id": str(task.trace_id) if task.trace_id else None,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "finished_at": task.finished_at.isoformat() if task.finished_at else None,
    }


@router.get("/pending-reviews")
def list_pending_reviews(
    tenant_id: Optional[str] = Query(None, description="租户 ID（可选）"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取待人工审核或待干预的任务列表 (status in [review, wait_human])。"""
    t_id = _resolve_tenant_id(db, current_user, tenant_id)
    query = (
        db.query(AiTask)
        .filter(
            AiTask.tenant_id == t_id,
            AiTask.status.in_([REVIEW, WAIT_HUMAN]),
        )
        .order_by(AiTask.priority.asc(), AiTask.created_at.desc())
    )

    total = query.count()
    skip = (page - 1) * page_size
    items = query.offset(skip).limit(page_size).all()

    return {
        "code": 0,
        "message": "success",
        "data": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [_task_to_dict(t) for t in items],
        },
    }


@router.get("/{task_id}")
def get_task_detail(
    task_id: str,
    tenant_id: Optional[str] = Query(None, description="租户 ID（可选）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取单个任务详情。"""
    t_id = _resolve_tenant_id(db, current_user, tenant_id)
    svc = TaskControlService(db)
    task = svc.get_task(task_id, tenant_id=t_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    return {
        "code": 0,
        "message": "success",
        "data": _task_to_dict(task),
    }


@router.post("/{task_id}/resume")
def resume_task(
    task_id: str,
    payload: Optional[TaskResumeRequest] = None,
    tenant_id: Optional[str] = Query(None, description="租户 ID（可选）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """人工审核放行 / 恢复执行：将 paused 或 wait_human 状态的任务恢复为 executing。"""
    t_id = _resolve_tenant_id(db, current_user, tenant_id)
    svc = TaskControlService(db)
    try:
        task = svc.resume_task(task_id, tenant_id=t_id)
        # 编排 DAG 节点被人工放行后，必须真正重新入队执行，否则节点会永远停在
        # executing 空转（2026-09-10 端到端真跑实测：n4 publish.multi 命中审批闸
        # 挂起，放行后无人派发，n5/n6 随之永久 paused）。resume 已把状态合法地
        # 从 wait_human 推到 executing，这里清掉挂起原因并把任务重新交给 Celery。
        if str(task.task_type or "").startswith("hermes_node:"):
            import json as _json

            try:
                cfg = _json.loads(task.input_json or "{}") or {}
            except Exception:  # noqa: BLE001 — 配置解析失败不影响放行
                cfg = {}
            if cfg.pop("blocked_reason", None) is not None:
                task.input_json = _json.dumps(cfg, ensure_ascii=False)
                db.commit()
            task_id_for_retry = str(task.id)
            tenant_id_for_retry = str(task.tenant_id)
            db.refresh(task)
            try:
                from app.tasks.orchestration_tasks import process_ai_task

                process_ai_task.delay(task_id_for_retry)
                logger.info(
                    "Task resumed by user=%s task_id=%s 已重新派发 DAG 节点",
                    current_user.id, task_id_for_retry,
                )
            except Exception as dispatch_exc:  # noqa: BLE001
                logger.error(
                    "Task resumed by user=%s task_id=%s 但 Celery 入队失败: %s",
                    current_user.id, task_id_for_retry, dispatch_exc,
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"节点已放行但派发失败（Celery 不可用）: {dispatch_exc}",
                )
            return {
                "code": 0,
                "message": "task approved and re-dispatched",
                "data": _task_to_dict(task),
            }
        logger.info(
            "Task resumed by user=%s task_id=%s comment=%s",
            current_user.id, task_id, payload.comment if payload else None,
        )
        return {
            "code": 0,
            "message": "task resumed successfully",
            "data": _task_to_dict(task),
        }
    except TaskNotFound:
        raise HTTPException(status_code=404, detail="Task not found")
    except InvalidTaskTransition as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except TaskControlError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{task_id}/cancel")
def cancel_task(
    task_id: str,
    payload: Optional[TaskCancelRequest] = None,
    tenant_id: Optional[str] = Query(None, description="租户 ID（可选）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """人工终止取消任务：将非终态任务转为 cancelled。"""
    t_id = _resolve_tenant_id(db, current_user, tenant_id)
    svc = TaskControlService(db)
    try:
        task = svc.cancel_task(task_id, tenant_id=t_id)
        if payload and payload.reason:
            task.error_message = f"人工取消: {payload.reason}"[:2000]
            db.commit()
            db.refresh(task)
        logger.info(
            "Task cancelled by user=%s task_id=%s reason=%s",
            current_user.id, task_id, payload.reason if payload else None,
        )
        return {
            "code": 0,
            "message": "task cancelled successfully",
            "data": _task_to_dict(task),
        }
    except TaskNotFound:
        raise HTTPException(status_code=404, detail="Task not found")
    except InvalidTaskTransition as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except TaskControlError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{task_id}/retry")
def retry_task(
    task_id: str,
    tenant_id: Optional[str] = Query(None, description="租户 ID（可选）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """人工介入触发受控重试：转入 retrying 状态（有界重试 ≤3）。"""
    t_id = _resolve_tenant_id(db, current_user, tenant_id)
    svc = TaskControlService(db)
    try:
        task = svc.retry_task(task_id, tenant_id=t_id)
        logger.info("Task retry initiated by user=%s task_id=%s", current_user.id, task_id)
        return {
            "code": 0,
            "message": "task retry initiated",
            "data": _task_to_dict(task),
        }
    except TaskNotFound:
        raise HTTPException(status_code=404, detail="Task not found")
    except InvalidTaskTransition as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except TaskControlError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
