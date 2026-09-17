# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""AI 进化引擎 API 路由。

提供进化闭环的管理接口：数据收集、经验沉淀、版本管理、灰度发布、审批流程。
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import success_response
from app.core.security import require_admin
from app.models.evolution import ApprovalRecord
from app.services.evolution import (
    CanaryRelease,
    EvolutionEngine,
    ExperienceStore,
    VersionControl,
)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/evolution", tags=["AI进化引擎"])


# ═══════════════════════════════════════════════
# 概览
# ═══════════════════════════════════════════════


@router.get("/overview")
def evolution_overview(
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """获取进化引擎整体概览。"""
    engine = EvolutionEngine(db)
    return success_response(data=engine.get_overview())


# ═══════════════════════════════════════════════
# Stage 1: 数据收集
# ═══════════════════════════════════════════════


@router.post("/records", status_code=201)
def record_task_execution(
    req: dict[str, Any],
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """记录一次任务执行结果（数据收集入口）。"""
    engine = EvolutionEngine(db)
    try:
        record = engine.record_task_execution(
            task_type=req.get("task_type", ""),
            executor_type=req.get("executor_type", "skill"),
            executor_id=req.get("executor_id", ""),
            success=req.get("success", True),
            duration_ms=req.get("duration_ms", 0),
            cost=req.get("cost", 0.0),
            tokens_used=req.get("tokens_used", 0),
            tenant_id=req.get("tenant_id"),
            error_code=req.get("error_code"),
            error_message=req.get("error_message"),
            input_summary=req.get("input_summary"),
            output_summary=req.get("output_summary"),
            metadata=req.get("metadata"),
        )
        return success_response(data={"id": str(record.id), "status": "recorded"})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/records")
def list_task_records(
    task_type: Optional[str] = None,
    success: Optional[bool] = None,
    executor_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """获取任务执行记录列表。"""
    from app.models.evolution import EvolutionTaskRecord
    q = db.query(EvolutionTaskRecord)
    if task_type:
        q = q.filter(EvolutionTaskRecord.task_type == task_type)
    if success is not None:
        q = q.filter(EvolutionTaskRecord.success == success)
    if executor_id:
        q = q.filter(EvolutionTaskRecord.executor_id == executor_id)

    total = q.count()
    rows = (
        q.order_by(EvolutionTaskRecord.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return success_response(data={
        "data": [
            {
                "id": str(r.id),
                "task_type": r.task_type,
                "executor_type": r.executor_type,
                "executor_id": r.executor_id,
                "success": r.success,
                "duration_ms": r.duration_ms,
                "cost": r.cost,
                "tokens_used": r.tokens_used,
                "error_code": r.error_code,
                "tenant_id": str(r.tenant_id) if r.tenant_id else None,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    })


# ═══════════════════════════════════════════════
# Stage 2: 经验沉淀
# ═══════════════════════════════════════════════


@router.post("/experiences/extract")
def extract_experiences(
    req: dict[str, Any],
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """执行经验沉淀：从任务记录中提取可复用模式。"""
    engine = EvolutionEngine(db)
    result = engine.run_experience_extraction(
        task_type=req.get("task_type", ""),
        lookback_hours=req.get("lookback_hours", 24),
        min_samples=req.get("min_samples", 5),
    )
    return success_response(data=result)


@router.get("/experiences")
def list_experiences(
    task_type: Optional[str] = None,
    pattern_type: Optional[str] = None,
    unapplied_only: bool = False,
    min_confidence: float = 0.0,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """获取经验库列表。"""
    store = ExperienceStore(db)
    entries = store.find_applicable(
        task_type or "",
        pattern_type=pattern_type,
        min_confidence=min_confidence,
        unapplied_only=unapplied_only,
        limit=limit,
    )
    return success_response(data={
        "data": [
            {
                "id": str(e.id),
                "task_type": e.task_type,
                "pattern_type": e.pattern_type,
                "title": e.title,
                "description": e.description,
                "confidence": e.confidence,
                "occurrence_count": e.occurrence_count,
                "applied": e.applied,
                "pattern_data": e.pattern_data,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in entries
        ],
        "total": len(entries),
    })


@router.get("/experiences/stats")
def experience_stats(
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """获取经验库统计信息。"""
    store = ExperienceStore(db)
    return success_response(data=store.get_stats())


# ═══════════════════════════════════════════════
# Stage 3: Skill 版本管理
# ═══════════════════════════════════════════════


@router.post("/skills/{skill_id}/versions")
def create_skill_version(
    skill_id: str,
    req: dict[str, Any],
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """创建新的 Skill 版本。"""
    vc = VersionControl(db)
    try:
        version = vc.create_skill_version(
            skill_id=skill_id,
            skill_name=req.get("skill_name", skill_id),
            bump=req.get("bump", "patch"),
            prompt_template=req.get("prompt_template"),
            parameters=req.get("parameters"),
            changelog=req.get("changelog"),
            based_on_experience_ids=req.get("based_on_experience_ids"),
        )
        return success_response(data={
            "id": str(version.id),
            "skill_id": version.skill_id,
            "version": version.version,
            "status": version.status,
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/skills/{skill_id}/versions")
def list_skill_versions(
    skill_id: str,
    status: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """获取 Skill 版本列表。"""
    vc = VersionControl(db)
    versions = vc.get_skill_versions(skill_id, status=status, limit=limit)
    return success_response(data={
        "data": [
            {
                "id": str(v.id),
                "skill_id": v.skill_id,
                "version": v.version,
                "status": v.status,
                "success_rate": v.success_rate,
                "total_invocations": v.total_invocations,
                "canary_percentage": v.canary_percentage,
                "created_at": v.created_at.isoformat() if v.created_at else None,
            }
            for v in versions
        ],
        "total": len(versions),
    })


@router.post("/skills/{skill_id}/versions/{version_id}/transition")
def transition_skill_version(
    skill_id: str,
    version_id: str,
    req: dict[str, Any],
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """执行 Skill 版本状态跃迁。"""
    vc = VersionControl(db)
    try:
        new_status = req.get("new_status", "")
        version = vc.transition_skill(
            version_id,
            new_status,
            canary_percentage=req.get("canary_percentage"),
            canary_tenant_ids=req.get("canary_tenant_ids"),
        )
        return success_response(data={
            "id": str(version.id),
            "version": version.version,
            "status": version.status,
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/skills/{skill_id}/optimize")
def optimize_skill(
    skill_id: str,
    req: dict[str, Any],
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """执行 Skill 优化：基于经验自动调整 Prompt/参数。"""
    engine = EvolutionEngine(db)
    result = engine.run_skill_optimization(
        skill_id=skill_id,
        skill_name=req.get("skill_name", skill_id),
        task_type=req.get("task_type", ""),
        bump=req.get("bump", "patch"),
        prompt_template=req.get("prompt_template"),
        parameters=req.get("parameters"),
    )
    return success_response(data=result)


# ═══════════════════════════════════════════════
# Stage 4: SOP 版本管理
# ═══════════════════════════════════════════════


@router.post("/sops/{sop_id}/versions")
def create_sop_version(
    sop_id: str,
    req: dict[str, Any],
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """创建新的 SOP 版本。"""
    vc = VersionControl(db)
    try:
        version = vc.create_sop_version(
            sop_id=sop_id,
            sop_name=req.get("sop_name", sop_id),
            bump=req.get("bump", "patch"),
            steps=req.get("steps"),
            decision_tree=req.get("decision_tree"),
            exception_handling=req.get("exception_handling"),
            changelog=req.get("changelog"),
            based_on_experience_ids=req.get("based_on_experience_ids"),
        )
        return success_response(data={
            "id": str(version.id),
            "sop_id": version.sop_id,
            "version": version.version,
            "status": version.status,
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sops/{sop_id}/versions")
def list_sop_versions(
    sop_id: str,
    status: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """获取 SOP 版本列表。"""
    vc = VersionControl(db)
    versions = vc.get_sop_versions(sop_id, status=status, limit=limit)
    return success_response(data={
        "data": [
            {
                "id": str(v.id),
                "sop_id": v.sop_id,
                "version": v.version,
                "status": v.status,
                "completion_rate": v.completion_rate,
                "total_executions": v.total_executions,
                "created_at": v.created_at.isoformat() if v.created_at else None,
            }
            for v in versions
        ],
        "total": len(versions),
    })


@router.post("/sops/{sop_id}/optimize")
def optimize_sop(
    sop_id: str,
    req: dict[str, Any],
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """执行 SOP 优化：基于经验更新标准操作流程。"""
    engine = EvolutionEngine(db)
    result = engine.run_sop_optimization(
        sop_id=sop_id,
        sop_name=req.get("sop_name", sop_id),
        task_type=req.get("task_type", ""),
        bump=req.get("bump", "patch"),
    )
    return success_response(data=result)


# ═══════════════════════════════════════════════
# Stage 5: 灰度发布
# ═══════════════════════════════════════════════


@router.post("/skills/{skill_id}/deploy-canary")
def deploy_canary(
    skill_id: str,
    req: dict[str, Any],
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """将版本部署到灰度。"""
    engine = EvolutionEngine(db)
    try:
        result = engine.deploy_to_canary(
            skill_id=skill_id,
            version_id=req.get("version_id", ""),
            percentage=req.get("percentage", 5.0),
            tenant_ids=req.get("tenant_ids"),
            requester=req.get("requester", "admin"),
        )
        return success_response(data=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/skills/{skill_id}/promote")
def promote_to_production(
    skill_id: str,
    req: dict[str, Any],
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """提交灰度版本晋升到生产的审批请求。"""
    engine = EvolutionEngine(db)
    result = engine.promote_to_production(
        skill_id=skill_id,
        version_id=req.get("version_id", ""),
        requester=req.get("requester", "admin"),
    )
    return success_response(data=result)


# ═══════════════════════════════════════════════
# Stage 6: 效果验证
# ═══════════════════════════════════════════════


@router.get("/skills/{skill_id}/validate")
def validate_canary(
    skill_id: str,
    lookback_hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """验证灰度版本效果（A/B 对比）。"""
    engine = EvolutionEngine(db)
    result = engine.validate_canary(skill_id, lookback_hours=lookback_hours)
    return success_response(data=result)


# ═══════════════════════════════════════════════
# 审批流程
# ═══════════════════════════════════════════════


@router.get("/approvals")
def list_approvals(
    target_type: Optional[str] = None,
    status: Optional[str] = "pending",
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """获取审批列表。"""
    q = db.query(ApprovalRecord)
    if target_type:
        q = q.filter(ApprovalRecord.target_type == target_type)
    if status:
        q = q.filter(ApprovalRecord.status == status)
    rows = q.order_by(ApprovalRecord.submitted_at.asc()).limit(limit).all()
    return success_response(data={
        "data": [
            {
                "id": str(r.id),
                "target_type": r.target_type,
                "target_id": str(r.target_id),
                "action": r.action,
                "status": r.status,
                "requester": r.requester,
                "reviewer": r.reviewer,
                "evidence": r.evidence,
                "submitted_at": r.submitted_at.isoformat() if r.submitted_at else None,
                "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
            }
            for r in rows
        ],
        "total": len(rows),
    })


@router.post("/approvals/{approval_id}/review")
def review_approval(
    approval_id: str,
    req: dict[str, Any],
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """审批审批请求（人工审核）。"""
    canary = CanaryRelease(db)
    vc = VersionControl(db)
    try:
        result = canary.review_approval(
            approval_id,
            reviewer=req.get("reviewer", "admin"),
            approved=req.get("approved", False),
            comment=req.get("comment"),
            version_control=vc,
        )
        return success_response(data={
            "id": str(result.id),
            "status": result.status,
            "reviewer": result.reviewer,
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ═══════════════════════════════════════════════
# 全流程运行
# ═══════════════════════════════════════════════


@router.post("/run-cycle")
def run_full_cycle(
    req: dict[str, Any],
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """运行完整的进化闭环。"""
    engine = EvolutionEngine(db)
    result = engine.run_full_cycle(
        task_type=req.get("task_type", ""),
        skill_id=req.get("skill_id", ""),
        skill_name=req.get("skill_name", req.get("skill_id", "")),
        lookback_hours=req.get("lookback_hours", 24),
        deploy_canary=req.get("deploy_canary", False),
        canary_percentage=req.get("canary_percentage", 5.0),
        requester=req.get("requester", "admin"),
    )
    return success_response(data=result)
