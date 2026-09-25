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
from app.core.response import error_response, success_response
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


@router.post("/experiences/{experience_id}/apply")
def apply_experience(
    experience_id: str,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """标记某条经验为已应用（委托 ExperienceStore.mark_applied，不编造行为）。"""
    store = ExperienceStore(db)
    applied = store.mark_applied(experience_id)
    return success_response(data={"id": experience_id, "applied": applied})


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


@router.get("/stats")
def evolution_stats(
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """进化引擎统计（`/stats` 便捷入口）。

    2026-09-25 补齐（缺失接口逐个修复）：
      前端 `views/evolution/Dashboard.vue:154` 调 `GET /api/v1/evolution/stats`，
      但后端只有 `/evolution/overview` → 零命中 → 页面统计区永远为空
      （该页 catch 里写着「接口可能未实现，不影响页面」，等于静默降级）。

    实现：与 `/overview` 同源，直接返回 `engine.get_overview()`，不另造一份数据。
    """
    engine = EvolutionEngine(db)
    return success_response(data=engine.get_overview())


@router.get("/skills")
def list_skills(
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """技能列表（`skills` 表）。

    2026-09-25 补齐：前端 `Dashboard.vue:172` 调 `GET /api/v1/evolution/skills`，
    期望 `data.items`，但后端只有 `/skills/{skill_id}/...` 单技能子路径，**无列表端点**
      → 零命中 → 技能区永远为空。
    """
    from app.models.registry import RegistrySkill

    rows = (
        db.query(RegistrySkill)
        .order_by(RegistrySkill.category.asc(), RegistrySkill.name.asc())
        .limit(500)
        .all()
    )
    items = [
        {
            "id": str(r.id),
            "name": r.name,
            "display_name": r.display_name or r.name,
            "category": r.category,
            "status": r.status,
            "current_version": r.current_version,
            "description": r.description,
            "priority": r.priority,
        }
        for r in rows
    ]
    return success_response(data={"items": items, "total": len(items)})


@router.post("/skills/optimize")
def optimize_all_skills(
    req: dict[str, Any] | None = None,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """**批量**技能优化：对 active 技能逐个执行既有单技能优化。

    2026-09-25 补齐：前端 `Dashboard.vue:199` 调 `POST /api/v1/evolution/skills/optimize`
    （**无参数**，语义 = 优化全部），但后端只有 `/skills/{skill_id}/optimize`（需 skill_id）
    → 零命中 → 「一键优化」按钮必失败。

    ⚠️ 语义假设（保守实现，可按需调整）：逐个对 `status='active'` 的技能调用
    `engine.run_skill_optimization(bump='patch')`；**单个失败不中断整批**，
    逐项返回结果，便于定位。批量上限 `limit`（默认 50，最大 200）以防一次性产生过多版本。
    """
    from app.models.registry import RegistrySkill

    req = req or {}
    limit = int(req.get("limit") or 50)
    limit = max(1, min(limit, 200))

    active_total = db.query(RegistrySkill).filter(RegistrySkill.status == "active").count()
    skills = (
        db.query(RegistrySkill)
        .filter(RegistrySkill.status == "active")
        .order_by(RegistrySkill.name.asc())
        .limit(limit)
        .all()
    )
    if not skills:
        return success_response(
            data={"total": 0, "succeeded": 0, "failed": 0, "results": []},
            message="没有 status=active 的技能可优化",
        )

    engine = EvolutionEngine(db)
    results: list[dict[str, Any]] = []
    ok = fail = 0
    for s in skills:
        try:
            out = engine.run_skill_optimization(
                skill_id=str(s.id),
                skill_name=s.display_name or s.name,
                task_type=req.get("task_type", ""),
                bump=req.get("bump", "patch"),
                prompt_template=req.get("prompt_template"),
                parameters=req.get("parameters"),
            )
            results.append({"skill_id": str(s.id), "name": s.name, "ok": True, "result": out})
            ok += 1
        except Exception as exc:  # noqa: BLE001
            results.append({
                "skill_id": str(s.id),
                "name": s.name,
                "ok": False,
                "error": f"{type(exc).__name__}: {exc}",
            })
            fail += 1

    # 求真：如实报出截断，避免「优化了 50 条却以为优化了全部」
    truncated = active_total > len(skills)
    return success_response(
        data={
            "total": len(skills),
            "active_total": active_total,
            "limit": limit,
            "truncated": truncated,
            "succeeded": ok,
            "failed": fail,
            "results": results,
        },
        message=(
            f"批量优化完成：成功 {ok} / 失败 {fail}"
            + (f"（active 共 {active_total} 条，本次仅处理前 {len(skills)} 条，可调 limit 继续）" if truncated else "")
        ),
    )


@router.post("/deploy-canary")
def deploy_canary_all(
    req: dict[str, Any] | None = None,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """**批量**灰度部署：对 active 技能逐个把其当前版本部署到灰度。

    2026-09-25 补齐：前端 `Dashboard.vue:204` 调 `POST /api/v1/evolution/deploy-canary`
    （body 为 canaryForm），但后端只有 `/skills/{skill_id}/deploy-canary`（需 skill_id）
    → 零命中 → 「灰度发布」按钮必失败。

    ⚠️ 语义假设（保守实现）：逐个对 `status='active'` 的技能调用
    `engine.deploy_to_canary(percentage=...)`；**单个失败不中断整批**，逐项返回。
    未提供 version_id 时依赖引擎自身解析当前版本（引擎内已有该逻辑）。
    """
    from app.models.registry import RegistrySkill

    req = req or {}
    limit = max(1, min(int(req.get("limit") or 50), 200))
    percentage = float(req.get("percentage") or 5.0)
    tenant_ids = req.get("tenant_ids")

    skills = (
        db.query(RegistrySkill)
        .filter(RegistrySkill.status == "active")
        .order_by(RegistrySkill.name.asc())
        .limit(limit)
        .all()
    )
    active_total = db.query(RegistrySkill).filter(RegistrySkill.status == "active").count()
    if not skills:
        return success_response(
            data={"total": 0, "succeeded": 0, "failed": 0, "results": []},
            message="没有 status=active 的技能可部署",
        )

    engine = EvolutionEngine(db)
    results: list[dict[str, Any]] = []
    ok = fail = 0
    for s in skills:
        try:
            out = engine.deploy_to_canary(
                skill_id=str(s.id),
                version_id=req.get("version_id", ""),
                percentage=percentage,
                tenant_ids=tenant_ids,
            )
            results.append({"skill_id": str(s.id), "name": s.name, "ok": True, "result": out})
            ok += 1
        except Exception as exc:  # noqa: BLE001
            results.append({
                "skill_id": str(s.id),
                "name": s.name,
                "ok": False,
                "error": f"{type(exc).__name__}: {exc}",
            })
            fail += 1

    # 求真：如实报出截断
    truncated = active_total > len(skills)
    return success_response(
        data={
            "total": len(skills),
            "active_total": active_total,
            "limit": limit,
            "truncated": truncated,
            "succeeded": ok,
            "failed": fail,
            "results": results,
        },
        message=(
            f"批量灰度部署完成：成功 {ok} / 失败 {fail}"
            + (f"（active 共 {active_total} 条，本次仅处理前 {len(skills)} 条，可调 limit 继续）" if truncated else "")
        ),
    )


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
