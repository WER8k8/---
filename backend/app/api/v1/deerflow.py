# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""DeerFlow 执行引擎 API 路由。

提供任务管理、状态转移、人工审核的 REST 接口。
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import error_json_response, success_response
from app.core.security import get_current_user
from app.models.deerflow_job import DeerflowJob
from app.models.user import User
from app.services.deerflow.checkpoint import CheckpointManager
from app.services.deerflow.executor import SubTaskExecutionError
from app.services.deerflow.planner import TaskPlanner
from app.services.deerflow.reviewer import ResultReviewer, ReviewDecision
from app.services.deerflow.state_machine import (
    DeerFlowJobNotFoundError,
    DeerFlowStateMachine,
    DeerFlowStatus,
)

logger = logging.getLogger(__name__)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/deerflow", tags=["DeerFlow"])


# ---------------------------------------------------------------------------
# 请求/响应模型
# --------------------------------------------------------------------------|

class CreateJobRequest(BaseModel):
    """创建 DeerFlow 任务请求。"""
    tenant_id: str = Field(..., description="租户 ID")
    intent: str = Field(..., description="任务意图/类型")
    payload: dict[str, Any] = Field(default_factory=dict, description="任务载荷")
    strategy: str = Field(default="sequential", description="执行策略: sequential | parallel | dag")
    max_retries: int = Field(default=3, ge=0, le=10, description="最大重试次数")
    custom_subtasks: Optional[list[dict[str, Any]]] = Field(None, description="自定义子任务列表")
    created_by: Optional[str] = Field(None, description="创建者用户 ID")


class TransitionRequest(BaseModel):
    """状态转移请求。"""
    message: str = Field(default="", description="转移附注")


class HumanDecisionRequest(BaseModel):
    """人工决策请求。"""
    decision: str = Field(..., description="approve | cancel")
    reason: str = Field(default="", description="决策原因")


class ApiResponse(BaseModel):
    """标准响应。"""
    code: int = 0
    message: str = "success"
    data: Optional[Any] = None


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

def _serialize_job(job: DeerflowJob) -> dict[str, Any]:
    """序列化任务记录。"""
    return {
        "id": str(job.id),
        "tenant_id": str(job.tenant_id),
        "intent": job.intent,
        "status": job.status,
        "payload_json": job.payload_json,
        "result_json": job.result_json,
        "error_message": job.error_message,
        "log_text": job.log_text,
        "created_by": str(job.created_by) if job.created_by else None,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
        "retry_count": getattr(job, "retry_count", 0),
    }


def _get_machine(
    job_id: str,
    db: Session,
    max_retries: int = 3,
) -> DeerFlowStateMachine:
    """获取状态机实例。"""
    return DeerFlowStateMachine(db, job_id, max_retries=max_retries)


# ---------------------------------------------------------------------------
# 任务 CRUD
# ---------------------------------------------------------------------------


@router.post("/jobs")
def create_job(
    request: CreateJobRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建 DeerFlow 任务。

    创建后任务处于 CREATED 状态，需要调用 /{jobId}/start 开始执行。
    """
    job = DeerflowJob(
        id=str(uuid.uuid4()),
        tenant_id=request.tenant_id,
        intent=request.intent,
        status=DeerFlowStatus.CREATED.value,
        payload_json="{}",
        created_by=request.created_by,
        retry_count=0,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    logger.info(
        "DeerFlow job created: id=%s tenant=%s intent=%s",
        job.id, request.tenant_id, request.intent,
    )
    return success_response(_serialize_job(job), message="任务创建成功")


@router.get("/jobs")
def list_jobs(
    tenant_id: Optional[str] = Query(None, description="租户 ID 过滤"),
    status_filter: Optional[str] = Query(None, alias="status", description="状态过滤"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """列出 DeerFlow 任务。"""
    query = db.query(DeerflowJob)
    if tenant_id:
        query = query.filter(DeerflowJob.tenant_id == tenant_id)
    if status_filter:
        query = query.filter(DeerflowJob.status == status_filter)

    total = query.count()
    jobs = query.order_by(desc(DeerflowJob.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    return success_response(
        [_serialize_job(j) for j in jobs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/jobs/{job_id}")
def get_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取任务详情。"""
    job = db.query(DeerflowJob).filter(DeerflowJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")
    return success_response(_serialize_job(job))


@router.delete("/jobs/{job_id}")
def delete_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除任务。"""
    job = db.query(DeerflowJob).filter(DeerflowJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")
    db.delete(job)
    db.commit()
    return success_response(message="任务已删除")


# ---------------------------------------------------------------------------
# 状态机控制
# ---------------------------------------------------------------------------


@router.post("/jobs/{job_id}/start")
def start_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """开始执行任务：CREATED -> PLANNING。"""
    try:
        machine = _get_machine(job_id, db)
        result = machine.start_planning()
        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)

        # 创建执行计划
        job = db.query(DeerflowJob).filter(DeerflowJob.id == job_id).first()
        planner = TaskPlanner(db)
        plan = planner.create_plan(job, strategy="sequential")
        planner.save_plan(job, plan)
        return success_response(
            {**_serialize_job(job), "plan": plan.to_dict()},
            message="任务已开始规划",
        )
    except DeerFlowJobNotFoundError:
        raise HTTPException(status_code=404, detail="任务不存在")


@router.post("/jobs/{job_id}/execute")
def execute_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """触发执行：PLANNING -> EXECUTING。

    将任务提交到 Celery 队列异步执行。
    """
    try:
        machine = _get_machine(job_id, db)
        result = machine.finish_planning()
        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)

        # 提交到 Celery
        from app.tasks.deerflow_tasks import execute_deerflow_job
        execute_deerflow_job.delay(job_id)
        return success_response(machine_id=job_id, message="任务已提交执行")
    except DeerFlowJobNotFoundError:
        raise HTTPException(status_code=404, detail="任务不存在")


@router.post("/jobs/{job_id}/cancel")
def cancel_job(
    job_id: str,
    request: TransitionRequest = TransitionRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取消任务。"""
    try:
        machine = _get_machine(job_id, db)
        result = machine.cancel()
        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)
        return success_response(result.to_dict(), message="任务已取消")
    except DeerFlowJobNotFoundError:
        raise HTTPException(status_code=404, detail="任务不存在")


@router.post("/jobs/{job_id}/retry")
def retry_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """重试失败任务：FAILED -> RETRY -> EXECUTING。"""
    try:
        machine = _get_machine(job_id, db)
        # FAILED -> RETRY
        retry_result = machine.trigger_retry()
        if not retry_result.success:
            raise HTTPException(status_code=400, detail=retry_result.message)

        # RETRY -> EXECUTING
        exec_result = machine.retry_execute()
        if not exec_result.success:
            raise HTTPException(status_code=400, detail=exec_result.message)

        # 提交到 Celery
        from app.tasks.deerflow_tasks import execute_deerflow_job
        execute_deerflow_job.delay(job_id)
        return success_response(message="任务已触发重试")
    except DeerFlowJobNotFoundError:
        raise HTTPException(status_code=404, detail="任务不存在")


# ---------------------------------------------------------------------------
# 人工审核
# ---------------------------------------------------------------------------


@router.get("/jobs/{job_id}/review")
def get_review_result(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取审核结果。"""
    job = db.query(DeerflowJob).filter(DeerflowJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")

    checkpoint_mgr = CheckpointManager(db, job)
    checkpoint = checkpoint_mgr.load()
    review_data = checkpoint.review if checkpoint else None
    if not review_data:
        return success_response(message="暂无审核结果")

    return success_response(review_data)


@router.post("/jobs/{job_id}/human-decision")
def human_decision(
    job_id: str,
    request: HumanDecisionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """人工决策（WAIT_HUMAN 状态）。

    decision: approve 或 cancel
    """
    try:
        machine = _get_machine(job_id, db)
        if request.decision == "approve":
            result = machine.human_approve()
        elif request.decision == "cancel":
            result = machine.human_cancel()
        else:
            raise HTTPException(
                status_code=400,
                detail="无效决策，仅支持 approve 或 cancel",
            )

        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)

        return success_response(result.to_dict(), message="人工决策已执行")
    except DeerFlowJobNotFoundError:
        raise HTTPException(status_code=404, detail="任务不存在")


# ---------------------------------------------------------------------------
# Checkpoint 管理
# ---------------------------------------------------------------------------


@router.get("/jobs/{job_id}/checkpoint")
def get_checkpoint(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取任务 checkpoint。"""
    job = db.query(DeerflowJob).filter(DeerflowJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")

    checkpoint_mgr = CheckpointManager(db, job)
    checkpoint = checkpoint_mgr.load()
    if not checkpoint:
        return success_response(message="暂无 checkpoint")

    return success_response(checkpoint.to_dict())


@router.get("/jobs/{job_id}/checkpoint/snapshots")
def list_snapshots(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """列出 checkpoint 快照。"""
    job = db.query(DeerflowJob).filter(DeerflowJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")

    checkpoint_mgr = CheckpointManager(db, job)
    snapshots = checkpoint_mgr.list_snapshots()
    return success_response(snapshots)


@router.post("/jobs/{job_id}/checkpoint/rollback")
def rollback_checkpoint(
    job_id: str,
    steps: int = Query(1, ge=1, le=10, description="回滚步数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """回滚 checkpoint 到历史快照。"""
    job = db.query(DeerflowJob).filter(DeerflowJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")

    checkpoint_mgr = CheckpointManager(db, job)
    restored = checkpoint_mgr.rollback(steps)
    if not restored:
        raise HTTPException(status_code=400, detail="没有足够的快照可以回滚")

    return success_response(restored.to_dict(), message=f"已回滚 {steps} 步")


@router.get("/jobs/{job_id}/resume-info")
def get_resume_info(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取任务恢复点信息。"""
    job = db.query(DeerflowJob).filter(DeerflowJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")

    checkpoint_mgr = CheckpointManager(db, job)
    can_resume = checkpoint_mgr.can_resume()
    batch_idx, subtask_idx = checkpoint_mgr.get_resume_point()
    pending = checkpoint_mgr.get_pending_subtasks()
    return success_response({
        "can_resume": can_resume,
        "batch_index": batch_idx,
        "subtask_index": subtask_idx,
        "pending_subtask_ids": pending,
    })


# ---------------------------------------------------------------------------
# 状态查询
# ---------------------------------------------------------------------------


@router.get("/jobs/{job_id}/status")
def get_job_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取任务当前状态。"""
    try:
        machine = _get_machine(job_id, db)
        current = machine.get_status()
        can_list = sorted(
            [s.value for s in _TRANSITIONS.get(current, set())],
        )
        return success_response({
            "job_id": job_id,
            "status": current.value,
            "is_terminal": current in (DeerFlowStatus.DONE, DeerFlowStatus.CANCELLED),
            "available_transitions": can_list,
        })
    except DeerFlowJobNotFoundError:
        raise HTTPException(status_code=404, detail="任务不存在")


@router.get("/statuses")
def list_statuses(
    current_user: User = Depends(get_current_user),
):
    """列出所有可用状态和转移规则。"""
    transitions = {}
    for from_status, to_statuses in _TRANSITIONS.items():
        transitions[from_status.value] = sorted([s.value for s in to_statuses])

    return success_response({
        "statuses": [s.value for s in DeerFlowStatus],
        "transitions": transitions,
    })


# ---------------------------------------------------------------------------
# 导入 _TRANSITIONS
# ---------------------------------------------------------------------------

from app.services.deerflow.state_machine import _TRANSITIONS
