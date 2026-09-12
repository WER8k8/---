"""UBrain 统一助手 API。"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.tenant import UserTenant
from app.models.user import User
from app.services.ubrain import ubrain_orchestrator
from app.services.ubrain.chat_task_service import UBrainChatTaskError, run_chat_task
from app.services.ubrain.accio_sales_service import (
    confirm_outreach_send,
    list_prospects,
)
from app.services.ubrain.deerflow_job_service import (
    list_jobs,
    run_job,
    run_pending_jobs,
)
from app.services.ubrain.prospect_export_service import (
    export_prospects_csv,
    mark_prospect_contacted,
)
from app.services.ubrain.brand_guard_bff import public_serialize_job
from app.services.hermes.brand_guard import sanitize_public_data
from app.services.ubrain.action_audit_service import (
    list_action_audits,
    log_action,
    summarize_action_audits,
)
from app.services.ubrain.tenant_memory_service import get_memory, merge_memory
from app.models.deerflow_job import DeerflowJob


def _resolve_tenant_id(user: User | None, db: Session) -> str | None:
    """执行 resolve_tenant_id 相关逻辑处理。
    
    :param user: 用户对象
    :param db: 数据库会话
    :return: 返回处理结果。
    """
    if user is None:
        return None
    tid = getattr(user, "tenant_id", None)
    if tid:
        return str(tid)
    link = (
        db.query(UserTenant)
        .filter(UserTenant.user_id == user.id, UserTenant.is_active.is_(True))
        .first()
    )
    if link:
        return str(link.tenant_id)
    if (user.role or "") in ("admin", "super_admin"):
        from app.models.tenant import Tenant
        first = db.query(Tenant).order_by(Tenant.created_at.asc()).first()
        if first:
            return str(first.id)
    return None


def _job_tenant_access(user: User, tenant_id: str, db: Session) -> bool:
    """执行 job_tenant_access 相关逻辑处理。
    
    :param user: 用户对象
    :param tenant_id: 租户ID
    :param db: 数据库会话
    :return: 返回处理结果。
    """
    if user.role in ("admin", "super_admin"):
        return True
    link = (
        db.query(UserTenant)
        .filter(
            UserTenant.user_id == user.id,
            UserTenant.tenant_id == tenant_id,
            UserTenant.is_active.is_(True),
        )
        .first()
    )
    return link is not None



# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/ubrain", tags=["UBrain助手"])


class UBrainChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    context: dict | None = None
    async_job: bool = Field(
        True,
        description="长任务默认仅入队（DeerFlow 队列）；传 sync=true 可强制同步",
    )


class GeoContentMatrixRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=2,
        max_length=2000,
        description="如：岩棉保温 GEO 内容矩阵",
    )
    domain: Optional[str] = Field(None, max_length=200)
    target_keywords: Optional[str] = Field(None, max_length=500)
    platforms: Optional[list[str]] = Field(None, max_length=8)
    article_count: int = Field(1, ge=1, le=3)
    async_job: bool = Field(True, description="True=入队；False=同步执行")


@router.post("/chat")
def ubrain_chat(
    body: UBrainChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 POST /chat 请求，ubrain相关资源。
    
    :param body: 请求体
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    tenant_id = _resolve_tenant_id(current_user, db) if current_user else None
    if not tenant_id:
        return error_response(400, "未绑定租户")
    ctx = dict(body.context or {})
    if tenant_id and "tenant_id" not in ctx:
        ctx["tenant_id"] = tenant_id
    if current_user and "user_id" not in ctx:
        ctx["user_id"] = str(current_user.id)
    if current_user and "user_role" not in ctx:
        ctx["user_role"] = str(current_user.role or "")
    if body.async_job:
        ctx["async"] = True
    if isinstance(ctx.get("sync"), str):
        ctx["sync"] = ctx["sync"].lower() in ("1", "true", "yes")
    try:
        _task, data = run_chat_task(
            db,
            tenant_id=str(tenant_id),
            message=body.message,
            context=ctx,
            user_id=str(current_user.id) if current_user else None,
        )
    except UBrainChatTaskError as exc:
        return error_response(500, str(exc))
    from app.services.hermes.brand_guard import sanitize_public_data
    data = sanitize_public_data(data)
    if db is not None and tenant_id:
        try:
            meta: dict = {"async_job": bool(body.async_job)}
            job_id = (data.get("tool_result") or {}).get("job_id")
            if job_id:
                meta["job_id"] = str(job_id)
            log_action(
                db,
                tenant_id=str(tenant_id),
                user_id=str(current_user.id) if current_user else None,
                action_type="chat",
                intent=data.get("intent"),
                tool=data.get("tool"),
                message=body.message,
                needs_confirmation=bool(data.get("needs_confirmation")),
                outcome="ok",
                meta=meta,
            )
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning("UBrain 查询失败: %s", e)
            pass

    # FIX-UBRAIN-NULL: 原实现漏写 return，FastAPI 把响应体序列化成 null，
    # 前端拿不到 reply 只能兜底"暂时无法回答"。
    return success_response(data=data)


@router.post("/geo-content-matrix")
def ubrain_geo_content_matrix(
    body: GeoContentMatrixRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """GEO/SEO 内容矩阵：关键词 → 母版 → 多平台变体 → 写入 content_masters。"""
    from app.services.ubrain.deerflow_job_service import enqueue_job, run_job
    tenant_id = _resolve_tenant_id(current_user, db)
    if not tenant_id:
        return error_response(400, "未绑定租户")
    ctx: dict = {
        "tenant_id": tenant_id,
        "user_id": str(current_user.id),
        "article_count": body.article_count,
    }
    if body.domain:
        ctx["domain"] = body.domain.strip()
    if body.target_keywords:
        ctx["target_keywords"] = body.target_keywords.strip()
    if body.platforms:
        ctx["platforms"] = [p.strip() for p in body.platforms if p and p.strip()]
    if not body.async_job:
        ctx["sync"] = True

    job = enqueue_job(
        db,
        tenant_id=str(tenant_id),
        intent="geo_content_matrix",
        payload={"message": body.message, "context": ctx},
        created_by=str(current_user.id),
    )
    data: dict = {
        "job_id": job.id,
        "job_status": "queued",
        "intent": "geo_content_matrix",
    }
    if not body.async_job:
        ran = run_job(db, job.id)
        data["job_status"] = ran.get("status")
        if ran.get("result"):
            data.update(ran["result"])
        if ran.get("status") == "failed":
            return error_response(500, ran.get("error_message") or "任务失败")
    else:
        try:
            run_pending_jobs(db, tenant_id=str(tenant_id), limit=3)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning("执行挂起任务失败: %s", e)
            pass
    return success_response(
        data=sanitize_public_data(data),
        message="GEO 内容矩阵任务已创建",
    )


@router.get("/inquiries/latest")
def ubrain_latest_inquiry(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """租户最新一条询盘（Accio A2 上下文）。"""
    tenant_id = _resolve_tenant_id(current_user, db)
    if not tenant_id:
        return error_response(400, "未绑定租户")
    from app.services.ubrain.inquiry_context_service import get_latest_inquiry
    row = get_latest_inquiry(db, tenant_id)
    if not row:
        return success_response(data=None, message="暂无询盘")
    return success_response(data=row)


@router.get("/ops-snapshot")
def ubrain_ops_snapshot(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """经营快照（Accio A4 只读）。"""
    tenant_id = _resolve_tenant_id(current_user, db)
    if not tenant_id:
        return error_response(400, "未绑定租户")
    from app.services.ubrain.inquiry_context_service import tenant_ops_snapshot
    return success_response(data=tenant_ops_snapshot(db, tenant_id))


@router.get("/action-audit")
def ubrain_action_audit(
    limit: int = Query(30, ge=1, le=100),
    action_type: Optional[str] = Query(None, description="chat | confirm_send"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Accio A5：租户副驾动作审计（最近 N 条）。"""
    tenant_id = _resolve_tenant_id(current_user, db)
    if not tenant_id:
        return error_response(400, "未绑定租户")
    return success_response(
        data=list_action_audits(db, tenant_id, limit=limit, action_type=action_type)
    )


@router.get("/action-audit/summary")
def ubrain_action_audit_summary(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """销售教练：近 N 天能力使用复盘（固定维度摘要）。"""
    tenant_id = _resolve_tenant_id(current_user, db)
    if not tenant_id:
        return error_response(400, "未绑定租户")
    return success_response(data=summarize_action_audits(db, tenant_id, days=days))


@router.get("/tools")
def ubrain_tools():
    """处理 GET /tools 请求，ubrain相关资源。
    :return: 返回处理结果。
    """
    return success_response(
        data={
            "tools": ubrain_orchestrator.TOOLS,
            "version": "v1",
            "execution_skills": [
                {
                    "id": "find_buyers",
                    "label": "自动找客",
                    "hint": "按区域生成采购商候选画像",
                },
                {
                    "id": "outreach_letter_pack",
                    "label": "开发信",
                    "hint": "中英开发信草稿，发送前确认",
                },
                {
                    "id": "negotiation_draft",
                    "label": "谈单话术",
                    "hint": "报价/压价/临门三轮话术",
                },
            ],
        }
    )


@router.get("/memory")
def ubrain_get_memory(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 GET /memory 请求，ubrain相关资源。
    
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    tenant_id = _resolve_tenant_id(current_user, db)
    if not tenant_id:
        return error_response(400, "未绑定租户")
    return success_response(data=get_memory(db, tenant_id))


class UBrainMemoryPatch(BaseModel):
    product_category: Optional[str] = None
    preferred_regions: Optional[list[str]] = None
    letter_language: Optional[str] = None
    tone: Optional[str] = None
    brand_name: Optional[str] = None
    site_cta: Optional[str] = None


@router.patch("/memory")
def ubrain_patch_memory(
    body: UBrainMemoryPatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 PATCH /memory 请求，ubrain相关资源。
    
    :param body: 请求体
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    tenant_id = _resolve_tenant_id(current_user, db)
    if not tenant_id:
        return error_response(400, "未绑定租户")
    patch = body.model_dump(exclude_none=True)
    return success_response(data=merge_memory(db, tenant_id, patch))


@router.get("/prospects")
def ubrain_list_prospects(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 GET /prospects 请求，ubrain相关资源。
    
    :param limit: 返回条数上限
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    tenant_id = _resolve_tenant_id(current_user, db)
    if not tenant_id:
        return error_response(400, "未绑定租户")
    return success_response(data=list_prospects(db, tenant_id, limit=limit))


@router.get("/prospects/export")
def ubrain_export_prospects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """导出采购商候选 CSV（待核实 → 人工跟进）。"""
    tenant_id = _resolve_tenant_id(current_user, db)
    if not tenant_id:
        return error_response(400, "未绑定租户")
    csv_text = export_prospects_csv(db, tenant_id)
    filename = f"prospects_{tenant_id[:8]}.csv"
    return Response(
        content="\ufeff" + csv_text,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


class MarkProspectContactedBody(BaseModel):
    note: Optional[str] = Field(None, max_length=500)


@router.post("/prospects/{prospect_id}/mark-contacted")
def ubrain_mark_prospect_contacted(
    prospect_id: str,
    body: MarkProspectContactedBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 POST /prospects/{prospect_id}/mark-contacted 请求，ubrain相关资源。
    
    :param prospect_id: 潜在客户ID
    :param body: 请求体
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    tenant_id = _resolve_tenant_id(current_user, db)
    if not tenant_id:
        return error_response(400, "未绑定租户")
    try:
        data = mark_prospect_contacted(
            db,
            tenant_id=tenant_id,
            prospect_id=prospect_id,
            note=body.note,
        )
    except ValueError:
        return error_response(404, "候选客户不存在")
    return success_response(data=data, message="已标记为已联系")


class ConfirmOutreachBody(BaseModel):
    prospect_id: str
    channel: str = Field(default="email", max_length=40)


@router.post("/prospects/confirm-send")
def ubrain_confirm_outreach(
    body: ConfirmOutreachBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """记录用户已人工发送开发信（审计，非真实 SMTP）。"""
    tenant_id = _resolve_tenant_id(current_user, db)
    if not tenant_id:
        return error_response(400, "未绑定租户")
    try:
        data = confirm_outreach_send(
            db,
            tenant_id=tenant_id,
            prospect_id=body.prospect_id,
            channel=body.channel,
        )
    except ValueError:
        return error_response(404, "候选客户不存在")
    try:
        log_action(
            db,
            tenant_id=str(tenant_id),
            user_id=str(current_user.id) if current_user else None,
            action_type="confirm_send",
            intent="outreach_letter_pack",
            tool="confirm_send",
            message=f"prospect={body.prospect_id}",
            needs_confirmation=False,
            outcome="confirmed",
            meta={"prospect_id": body.prospect_id, "channel": body.channel},
        )
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning("记录发送确认失败: %s", e)
        pass


@router.get("/jobs")
def ubrain_list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 GET /jobs 请求，ubrain相关资源。
    
    :param page: 页码
    :param page_size: 每页条数
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    tenant_id = _resolve_tenant_id(current_user, db)
    if not tenant_id:
        return error_response(400, "未绑定租户，无法查看任务")
    data = list_jobs(db, tenant_id=tenant_id, page=page, page_size=page_size)
    return success_response(data=sanitize_public_data(data))


@router.get("/jobs/{job_id}")
def ubrain_get_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 GET /jobs/{job_id} 请求，ubrain相关资源。
    
    :param job_id: 任务ID
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    job = db.query(DeerflowJob).filter(DeerflowJob.id == job_id).first()
    if not job:
        return error_response(404, "任务不存在")
    if not _job_tenant_access(current_user, str(job.tenant_id), db):
        return error_response(403, "无权查看该任务")
    return success_response(data=public_serialize_job(job, with_steps=True))


@router.post("/jobs/{job_id}/run")
def ubrain_run_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 POST /jobs/{job_id}/run 请求，ubrain相关资源。
    
    :param job_id: 任务ID
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    job = db.query(DeerflowJob).filter(DeerflowJob.id == job_id).first()
    if not job:
        return error_response(404, "任务不存在")
    if not _job_tenant_access(current_user, str(job.tenant_id), db):
        return error_response(403, "无权执行该任务")
    try:
        data = run_job(db, job_id)
    except ValueError:
        return error_response(404, "任务不存在")
    return success_response(data=sanitize_public_data(data), message="任务已执行")


@router.post("/jobs/run-pending")
def ubrain_run_pending(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理本租户 queued 任务（副驾轮询或 cron 调用）。"""
    tenant_id = _resolve_tenant_id(current_user, db)
    if not tenant_id:
        return error_response(400, "未绑定租户")
    items = run_pending_jobs(db, tenant_id=tenant_id, limit=limit)
    return success_response(
        data=sanitize_public_data({"processed": len(items), "items": items})
    )
