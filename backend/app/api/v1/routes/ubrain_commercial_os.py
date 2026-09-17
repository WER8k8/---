# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""商业 OS 飞轮 API — Mem0/n8n/PostHog 外挂槽位。"""

import os
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.ubrain.accio_gap_handlers import (
    execute_gap_mvp,
    execute_gap_mvp_async,
    is_gap_execute_skill,
    is_gap_mvp_skill,
)
from app.services.ubrain.accio_skill_catalog import (
    catalog_summary,
    get_skill,
    list_gap_skills,
    list_partial_mvp_skills,
    load_skill_catalog,
)
from app.services.ubrain.commercial_os_bridge import (
    collect_sales_feedback,
    flywheel_status,
    list_recent_pipelines,
    retrieve_insights_for_accio,
    run_pipeline_after_deerflow,
)
from app.services.ubrain.deerflow_research_service import build_research_brief
from app.services.ubrain.action_audit_service import log_flywheel_action
from app.api.v1.routes.ubrain import _resolve_tenant_id


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/ubrain/commercial-os", tags=["商业OS飞轮"])


def _audit(
    db: Session,
    *,
    tenant_id: str,
    action_type: str,
    user_id: str | None = None,
    intent: str | None = None,
    message: str | None = None,
    outcome: str = "ok",
    meta: dict | None = None,
) -> None:
    """执行 audit 相关逻辑处理。
    
    :param db: 数据库会话
    :param tenant_id: 租户ID
    :param action_type: 参数 action_type
    :param user_id: 用户ID
    :param intent: 参数 intent
    :param message: 参数 message
    :param outcome: 参数 outcome
    :param meta: 参数 meta
    :return: 返回处理结果。
    """
    log_flywheel_action(
        db,
        tenant_id=tenant_id,
        action_type=action_type,
        user_id=user_id,
        intent=intent,
        message=message,
        outcome=outcome,
        meta=meta,
    )


@router.get("/gaps")
def accio_skill_gaps(current_user: User = Depends(get_current_user)):
    """Accio 对标目录中未完整实现的技能（不删条目，仅列 gap）。"""
    gaps = list_gap_skills()
    return success_response(
        data={
            "items": gaps,
            "total": len(gaps),
            "note": "已实现技能请走 POST /api/v1/ubrain/chat；partial MVP 见 /partial-skills",
        }
    )


@router.get("/partial-skills")
def accio_partial_mvp_skills(current_user: User = Depends(get_current_user)):
    """partial 且已有 MVP 端点的技能（副驾「可先试用」）。"""
    items = list_partial_mvp_skills()
    return success_response(
        data={
            "items": items,
            "total": len(items),
            "note": "GET /commercial-os/gap/{skill_id} 可查看 MVP 载荷",
        }
    )


@router.get("/gap/{skill_id}")
def accio_skill_gap_stub(
    skill_id: str,
    image_url: Optional[str] = Query(None, max_length=2000),
    keywords: Optional[str] = Query(None, max_length=500),
    product_hint: Optional[str] = Query(None, max_length=500),
    locale: str = Query("zh", max_length=10),
    budget_usd: Optional[float] = Query(None, ge=0, le=1_000_000),
    rfq_lines: Optional[str] = Query(None, max_length=4000),
    current_user: User = Depends(get_current_user),
):
    """
    gap 技能：T-ACCIO-1～4 走 MVP 200；其余未实现技能仍 501 + 说明。
    """
    sk = get_skill(skill_id)
    if not sk:
        return error_response(404, f"未知技能: {skill_id}")
    if sk.get("implemented") is True and not is_gap_execute_skill(skill_id):
        return error_response(
            400,
            f"技能 {skill_id} 已实现，请使用 {sk.get('api') or '/api/v1/ubrain/chat'}",
        )
    mvp = execute_gap_mvp(
        skill_id,
        image_url=image_url,
        keywords=keywords,
        product_hint=product_hint,
        locale=locale,
        budget_usd=budget_usd,
        rfq_lines=rfq_lines,
    )
    if mvp is not None:
        mvp.setdefault("gap", sk.get("gap"))
        mvp["group_name"] = sk.get("group_name")
        return success_response(
            data=mvp,
            message="该能力 MVP 已可用；完整能力见说明字段",
        )
    payload = success_response(
        data={
            "skill_id": skill_id,
            "accio_analog": sk.get("accio_analog"),
            "implemented": sk.get("implemented"),
            "gap": sk.get("gap"),
            "group_name": sk.get("group_name"),
            "use_instead": sk.get("api") if sk.get("implemented") == "partial" else None,
            "north_star": "深度市场研究 + 卖货智能执行",
        },
        message="该能力尚未完整实现；条目保留用于产品排期",
    )
    return JSONResponse(status_code=501, content=payload.model_dump())


class GapExecuteRequest(BaseModel):
    product_hint: Optional[str] = Field(None, max_length=500)
    locale: str = Field("zh", max_length=10)
    budget_usd: Optional[float] = Field(None, ge=0, le=1_000_000)
    message: str = Field("", max_length=2000)
    context: dict[str, Any] = Field(default_factory=dict)


@router.post("/gap/{skill_id}/execute")
async def accio_skill_gap_execute(
    skill_id: str,
    body: GapExecuteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """gap 技能真执行：矩阵发布、建站、广告创意等（须登录租户）。"""
    if not is_gap_execute_skill(skill_id):
        return error_response(404, f"技能 {skill_id} 不支持 execute")
    tenant_id = _resolve_tenant_id(current_user, db)
    if not tenant_id:
        return error_response(400, "未绑定租户")
    result = await execute_gap_mvp_async(
        skill_id,
        db=db,
        tenant_id=tenant_id,
        product_hint=body.product_hint,
        locale=body.locale,
        budget_usd=body.budget_usd,
        context=body.context,
        message=body.message or f"execute {skill_id}",
        user_id=str(current_user.id),
    )
    if result is None:
        return error_response(400, "执行失败")
    _audit(
        db,
        tenant_id=tenant_id,
        action_type="gap_execute",
        user_id=str(current_user.id),
        intent=skill_id,
        message=(body.message or skill_id)[:400],
        meta={"status": result.get("status"), "mode": result.get("mode")},
    )
    return success_response(data=result, message=f"{skill_id} 已执行")


@router.get("/skill-catalog")
def accio_skill_catalog(current_user: User = Depends(get_current_user)):
    """AccioWork 技能包对标目录 + 本系统实现覆盖率。"""
    return success_response(
        data={
            "catalog": load_skill_catalog(),
            "summary": catalog_summary(),
            "research_note": "多 Agent 市场研究；可接外部研究引擎 webhook 回写简报",
        }
    )


class ResearchBriefRequest(BaseModel):
    message: str = Field(..., min_length=2, max_length=2000)
    template_id: str | None = Field(default=None, max_length=64)


@router.get("/research-brief/templates")
def list_research_brief_templates(
    current_user: User = Depends(get_current_user),
):
    """DeerFlow 预制 Brief 模板（Hermes×AnySearch 对标沉淀）。"""
    from app.services.ubrain.deerflow_brief_templates_service import list_brief_templates
    _ = current_user
    return success_response(data=list_brief_templates())


@router.post("/research-brief")
def create_research_brief(
    body: ResearchBriefRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """生成标准化 Research Brief（DeerFlow → Accio 结构化指令）。"""
    tenant_id = _resolve_tenant_id(current_user, db)
    if not tenant_id:
        return error_response(400, "未绑定租户")
    brief = build_research_brief(
        db,
        tenant_id=tenant_id,
        message=body.message,
        template_id=body.template_id,
    )
    _audit(
        db,
        tenant_id=tenant_id,
        action_type="flywheel_brief",
        user_id=str(current_user.id) if current_user else None,
        intent="research_brief",
        message=body.message[:400],
        meta={
            "action_count": len(brief.get("accio_actions") or []),
        },
    )
    return success_response(data=brief)


@router.get("/integrations")
def commercial_os_integrations(current_user: User = Depends(get_current_user)):
    """P2 外挂槽位配置状态（Mem0 / PostHog / n8n / DeerFlow 旁路）。"""
    from app.services.ubrain.flywheel_integrations import flywheel_integrations_status
    return success_response(data=flywheel_integrations_status())


@router.get("/deerflow-sidecar")
def commercial_os_deerflow_sidecar(current_user: User = Depends(get_current_user)):
    """官方 DeerFlow 旁路可达性（未配置则仅本机 Lite）。"""
    from app.services.ubrain.deerflow_sidecar import deerflow_sidecar_status
    return success_response(data=deerflow_sidecar_status())


@router.get("/status")
def commercial_os_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 GET /status 请求，commercial相关资源。
    
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    tenant_id = _resolve_tenant_id(current_user, db)
    if not tenant_id:
        return error_response(400, "未绑定租户")
    return success_response(data=flywheel_status(db, tenant_id))


@router.get("/pro-research-terms")
def pro_research_terms(current_user: User = Depends(get_current_user)):
    """COMP-03：Pro 定时市场研究服务条款（租户可见 · 已脱敏）。"""
    from app.services.ubrain.pro_research_terms_service import build_pro_research_terms
    return success_response(data=build_pro_research_terms())


@router.get("/pipelines")
def list_pipelines(
    limit: int = Query(10, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """最近研究→Accio 编排记录。"""
    tenant_id = _resolve_tenant_id(current_user, db)
    if not tenant_id:
        return error_response(400, "未绑定租户")
    items = list_recent_pipelines(db, tenant_id, limit=limit)
    return success_response(data={"items": items, "total": len(items)})


@router.get("/insights")
def list_research_insights(
    region: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 GET /insights 请求，列出相关资源。
    
    :param region: 参数 region
    :param category: 分类
    :param limit: 返回条数上限
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    tenant_id = _resolve_tenant_id(current_user, db)
    if not tenant_id:
        return error_response(400, "未绑定租户")
    items = retrieve_insights_for_accio(
        db, tenant_id, region=region, category=category, limit=limit
    )
    return success_response(data={"items": items, "total": len(items)})


@router.post("/feedback/sync")
def sync_feedback(
    period_days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 POST /feedback/sync 请求，同步相关资源。
    
    :param period_days: 参数 period_days
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    tenant_id = _resolve_tenant_id(current_user, db)
    if not tenant_id:
        return error_response(400, "未绑定租户")
    data = collect_sales_feedback(db, tenant_id, period_days=period_days)
    _audit(
        db,
        tenant_id=tenant_id,
        action_type="flywheel_feedback",
        user_id=str(current_user.id) if current_user else None,
        intent="sync_feedback",
        message=f"period_days={period_days}",
        meta={"period_days": period_days},
    )
    return success_response(data=data)


class N8nWebhookBody(BaseModel):
    event: str = Field(..., description="deerflow_done | manual_pipeline | feedback")
    tenant_id: str
    job_id: Optional[str] = None
    intent: Optional[str] = None
    result: Optional[dict[str, Any]] = None
    auto_enqueue: bool = True


@router.get("/webhook/health")
def n8n_webhook_health():
    """INT-02：n8n 连通性探针（无需认证，仅返回公共状态，不暴露密钥存在性/内部路径）。"""
    return success_response(
        data={
            "ready": True,
            "status": "ok",
        }
    )


@router.post("/webhook")
def n8n_webhook(
    body: N8nWebhookBody,
    db: Session = Depends(get_db),
    x_n8n_secret: Optional[str] = Header(None, alias="X-N8N-Webhook-Secret"),
):
    """外部 n8n 编排回调（配置 N8N_WEBHOOK_SECRET）。"""
    secret = os.getenv("N8N_WEBHOOK_SECRET", "").strip()
    env = (settings.ENVIRONMENT or "").strip().lower()
    if not secret:
        if env not in ("testing", "development"):
            return error_response(503, "N8N_WEBHOOK_SECRET 未配置，拒绝写入")
    elif (x_n8n_secret or "").strip() != secret:
        return error_response(403, "webhook 密钥无效")

    if body.event == "feedback":
        data = collect_sales_feedback(db, body.tenant_id)
        _audit(
            db,
            tenant_id=body.tenant_id,
            action_type="flywheel_webhook",
            intent="feedback",
            message="n8n feedback",
            meta={"event": body.event},
        )
        return success_response(data=data, message="反馈已同步")

    if body.event in ("deerflow_done", "manual_pipeline") and body.job_id and body.result:
        from app.services.ubrain.commercial_os_bridge import (
            extract_insight_from_deerflow,
            on_deerflow_job_finished,
        )
        if body.event == "deerflow_done":
            data = on_deerflow_job_finished(
                db,
                job_id=body.job_id,
                tenant_id=body.tenant_id,
                intent=body.intent or "market_research",
                status="success",
                result=body.result,
            )
        else:
            insight = extract_insight_from_deerflow(
                db,
                tenant_id=body.tenant_id,
                job_id=body.job_id,
                intent=body.intent or "manual",
                result=body.result or {},
            )
            data = run_pipeline_after_deerflow(
                db,
                tenant_id=body.tenant_id,
                trigger_job_id=body.job_id,
                intent=body.intent or "manual",
                result=body.result or {},
                insight_id=insight.id,
                auto_enqueue=body.auto_enqueue,
            )
        _audit(
            db,
            tenant_id=body.tenant_id,
            action_type="flywheel_webhook",
            intent=body.intent or body.event,
            message=f"event={body.event} job={body.job_id}",
            meta={
                "event": body.event,
                "job_id": body.job_id,
                "pipeline_status": (data or {}).get("status"),
                "auto_enqueue": body.auto_enqueue,
            },
        )
        return success_response(data=data)

    return error_response(400, "未知 event 或缺少 job_id/result")
