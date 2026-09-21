# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""询盘管理路由 - 模块化架构"""

import csv
import hashlib
import re
import time
from collections import defaultdict
from io import StringIO
from typing import Optional, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator, model_validator

# ── 询盘防刷限流器（5条/10分钟/IP） ──
_inquiry_rate_store: dict[str, list[float]] = defaultdict(list)
_INQUIRY_RATE_LIMIT = 5
_INQUIRY_RATE_WINDOW = 600  # 10 minutes


def _check_inquiry_rate(ip: str) -> None:
    """
    处理 _check_inquiry_rate 相关业务逻辑。

    :param ip: 入参 (str)。

    :return: 返回 None 类型的结果。

    :raises HTTPException: 当相应错误条件触发时抛出。
    """
    now = time.time()
    window = _inquiry_rate_store[ip]
    # 清理过期记录
    _inquiry_rate_store[ip] = [t for t in window if now - t < _INQUIRY_RATE_WINDOW]
    if len(_inquiry_rate_store[ip]) >= _INQUIRY_RATE_LIMIT:
        raise HTTPException(429, "提交过于频繁，请 10 分钟后再试")
    _inquiry_rate_store[ip].append(now)


def _find_recent_duplicate_inquiry(db, email: Optional[str], phone: Optional[str], tenant_id: Optional[str] = None):
    """查找近期（30分钟内）相同邮箱或电话的现有询盘以供智能合并。"""
    if not email and not phone:
        return None
    from app.models.inquiry import Inquiry
    from datetime import datetime, timedelta, timezone
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)
    query = db.query(Inquiry).filter(Inquiry.created_at > cutoff)
    if tenant_id:
        cols = {c.key for c in Inquiry.__table__.columns}
        if "tenant_id" in cols:
            query = query.filter(Inquiry.tenant_id == tenant_id)

    filters = []
    if email:
        filters.append(Inquiry.email == email)
    if phone:
        filters.append(Inquiry.phone == phone)
    from sqlalchemy import or_
    return query.filter(or_(*filters)).first()

from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.inquiry import Inquiry
from app.models.user import User
from app.schemas import InquiryCreate, InquiryUpdate
from app.services.inquiries_portal_service import InquiriesPortalService
from app.services.inquiries_unified_service import InquiriesUnifiedService


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/inquiries"
ROUTE_TAGS = ["询盘管理"]

router = APIRouter()

CANONICAL_INQUIRIES_LIST = "/api/v1/inquiries/unified"


def _mark_inquiries_deprecated(response: Response) -> None:
    """
    处理 _mark_inquiries_deprecated 相关业务逻辑。

    :param response: 入参 (Response)。

    :return: 返回 None 类型的结果。
    """
    response.headers["Deprecation"] = "true"
    response.headers["Link"] = f'<{CANONICAL_INQUIRIES_LIST}>; rel="successor-version"'


@router.get("/portal")
def inquiries_portal(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """询盘 API 导航与统计（管理端接入用）。"""
    return success_response(data=InquiriesPortalService(db).portal_meta())


def _resolve_caller_tenant_id(db: Session, current_user: User) -> Optional[str]:
    """解析当前请求用户的 tenant_id；超管返回 None（全局）。"""
    if getattr(current_user, "role", None) in ("super_admin",):
        return None
    tid = getattr(current_user, "tenant_id", None)
    if tid:
        return str(tid)
    try:
        from app.models.tenant import UserTenant
        link = (
            db.query(UserTenant)
            .filter(UserTenant.user_id == str(current_user.id), UserTenant.is_active.is_(True))
            .first()
        )
        if link and link.tenant_id:
            return str(link.tenant_id)
    except Exception:
        pass
    return None


def _check_inquiry_tenant_access(inquiry: Inquiry, db: Session, current_user: User, action: str = "访问") -> Optional[Any]:
    """校验询盘租户归属：跨租户返回 403 错误响应，合法放行返回 None。"""
    if getattr(current_user, "role", None) in ("super_admin",):
        return None
    caller_tid = _resolve_caller_tenant_id(db, current_user)
    inq_tid = str(inquiry.tenant_id) if getattr(inquiry, "tenant_id", None) else None
    if inq_tid and caller_tid and inq_tid != caller_tid:
        return error_response(403, f"无权{action}其他租户的询盘")
    if inq_tid and not caller_tid:
        return error_response(403, f"无权{action}该租户的询盘")
    return None


@router.get("/unified")
def list_inquiries_unified(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    status: Optional[str] = None,
    search: Optional[str] = None,
    source_channel: Optional[str] = Query(None, description="来源渠道筛选 T3"),
    pipeline_stage: Optional[str] = Query(None, description="GW-L-PL-01 管道阶段 mql|sql|quote|pi|deposit"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """统一询盘列表（兼容 SEO 线索与 B2B 询盘列，强制租户隔离）。"""
    assigned_filter: Optional[str] = None
    if current_user.role == "sales":
        assigned_filter = str(current_user.id)
    caller_tid = _resolve_caller_tenant_id(db, current_user)
    data = InquiriesUnifiedService(db).list_page(
        page=page,
        page_size=page_size,
        status=status,
        search=search,
        tenant_id=caller_tid,
        source_channel=source_channel,
        assigned_to=assigned_filter,
        pipeline_stage=pipeline_stage,
    )
    return success_response(data=data)


class InquiryStatusUpdate(BaseModel):
    status: str = Field(..., min_length=1, max_length=20)


# 询盘状态白名单（避免任意字符串落库，ORCH-08/09/10 同类问题修复）
# 2026-09-13 对齐前端实际取值：views/inquiries/index.vue 的「标记处理中」发
# quoted、「完成」发 accepted；展示层还识别 new/processing。原白名单缺这四个
# 值导致按钮点击必 400（主链断点）。
_VALID_INQUIRY_STATUSES = frozenset({
    "pending", "in_progress", "resolved", "closed", "archived",
    "new", "quoted", "accepted", "processing",
})


class InquiryAssignRequest(BaseModel):
    assigned_to: str = Field(..., min_length=1, max_length=36)


class PublicInquiryCreate(BaseModel):
    """租户站公开询盘（StickyImBar / 产品页）。"""
    name: str = Field(..., min_length=1, max_length=120)
    email: Optional[str] = None
    message: str = Field(..., min_length=1)
    phone: Optional[str] = Field(None, max_length=30, description="手机或国际电话；与邮箱至少填一项")
    product: Optional[str] = None
    source_channel: Optional[str] = None
    merchant_id: Optional[str] = "default"
    session_id: Optional[str] = None
    landing_path: Optional[str] = None
    last_click_label: Optional[str] = None
    tenant_id: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_content: Optional[str] = None
    utm_term: Optional[str] = None
    publish_task_id: Optional[str] = Field(None, description="矩阵 publish_task 归因")
    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: Optional[str]) -> Optional[str]:
        """
        校验（validate_phone）：处理相关业务逻辑并返回结果。

        :param value: 入参 (Optional[str])。

        :return: 返回 Optional[str] 类型的结果。

        :raises ValueError: 当相应错误条件触发时抛出。
        """
        if value is None:
            return None
        phone = value.strip()
        if not phone:
            return None
        if re.fullmatch(r"1[3-9]\d{9}", phone):
            return phone
        digits = re.sub(r"\D", "", phone)
        if len(digits) >= 7:
            return phone[:30]
        raise ValueError("请填写有效的联系电话")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: Optional[str]) -> Optional[str]:
        """
        处理 normalize_email 相关业务逻辑。

        :param value: 入参 (Optional[str])。

        :return: 返回 Optional[str] 类型的结果。

        :raises ValueError: 当相应错误条件触发时抛出。
        """
        if value is None:
            return None
        email = value.strip().lower()
        if not email:
            return None
        # 基础邮箱格式验证
        if not re.fullmatch(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", email):
            raise ValueError("邮箱格式不正确")
        return email

    @model_validator(mode="after")
    def require_contact_channel(self):
        """
        处理 require_contact_channel 相关业务逻辑。

        :return: 返回处理结果（或 None）。

        :raises ValueError: 当相应错误条件触发时抛出。
        """
        if not self.phone and not self.email:
            raise ValueError("请至少填写手机号或邮箱")
        return self


@router.get("", include_in_schema=False)
@router.get("/")
def list_inquiries(
        response: Response,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        status_filter: Optional[str] = Query(
            None,
            description="与 status 等价，兼容前端参数名"),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取询盘列表（分页，已废弃 — 请用 /unified）。"""
    _mark_inquiries_deprecated(response)
    if page < 1:
        page = 1
    if page_size > 100:
        page_size = 100
    effective_status = status_filter or status
    caller_tid = _resolve_caller_tenant_id(db, current_user)
    data = InquiriesUnifiedService(db).list_page(
        page=page,
        page_size=page_size,
        status=effective_status,
        search=search,
        tenant_id=caller_tid,
    )
    data["deprecated"] = True
    data["use_instead"] = "/api/v1/inquiries/unified"
    return success_response(data=data)


@router.get("/export")
def export_inquiries_csv(
    request: Request,
    status: Optional[str] = None,
    status_filter: Optional[str] = Query(None),
    search: Optional[str] = None,
    source_channel: Optional[str] = Query(None, description="按来源导出 T3/T4"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """导出询盘为 CSV（需登录，强制当前租户隔离导出，含 source_channel）"""
    from app.core.data_export_guard import assert_export_allowed
    # 询盘导出按租户数据范围；避免 admin 走 platform 触发创始人门禁（T-P0-15）
    scope = "tenant"
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "sales"]:
        return error_response(403, "权限不足")
    effective_status = status_filter or status
    caller_tid = _resolve_caller_tenant_id(db, current_user)
    data = InquiriesUnifiedService(db).list_page(
        page=1,
        page_size=5000,
        status=effective_status,
        search=search,
        tenant_id=caller_tid,
        source_channel=source_channel,
    )
    rows = data["items"]
    assert_export_allowed(
        db,
        current_user,
        request,
        export_kind="inquiries_csv",
        scope=scope,
        row_count=len(rows),
    )
    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "id",
            "kind",
            "subject",
            "name",
            "phone",
            "source_channel",
            "message",
            "status",
            "created_at",
        ]
    )
    for r in rows:
        writer.writerow(
            [
                r.get("id"),
                r.get("kind"),
                r.get("subject") or "",
                r.get("name") or "",
                r.get("phone") or "",
                r.get("source_channel") or "",
                (r.get("message") or "").replace("\n", " ")[:2000],
                r.get("status"),
                r.get("created_at") or "",
            ]
        )
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="inquiries_export.csv"'},
    )


@router.get("/assignees")
def list_inquiry_assignees(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """可分配的销售/管理员列表（落地页线索 CRM）。"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "sales"]:
        return error_response(403, "权限不足")
    from app.services.inquiry_lead_assignment_service import list_assignee_candidates
    return success_response(data=list_assignee_candidates(db))


@router.get("/assignment-audit")
def list_assignment_audit(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source_channel: Optional[str] = Query(None, description="按来源渠道筛选"),
    actor_user_id: Optional[str] = Query(None, description="操作人 user_id"),
    to_assignee_id: Optional[str] = Query(None, description="改派目标 user_id"),
    start_at: Optional[str] = Query(None, description="起始时间 ISO 或 YYYY-MM-DD"),
    end_at: Optional[str] = Query(None, description="结束时间 ISO 或 YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """改派审计分页预览（admin/super_admin）。"""
    if current_user.role not in ["admin", "super_admin"]:
        return error_response(403, "权限不足")

    from app.services.inquiry_assignment_audit_service import (
        list_assignment_audit_page,
        parse_audit_datetime,
    )
    try:
        start_dt = parse_audit_datetime(start_at, end_of_day=False)
        end_dt = parse_audit_datetime(end_at, end_of_day=True)
    except ValueError as exc:
        return error_response(400, str(exc))

    data = list_assignment_audit_page(
        db,
        start_at=start_dt,
        end_at=end_dt,
        source_channel=source_channel,
        actor_user_id=actor_user_id,
        to_assignee_id=to_assignee_id,
        page=page,
        page_size=page_size,
    )
    return success_response(data=data)


@router.get("/assignment-audit/export")
def export_assignment_audit_csv(
    request: Request,
    source_channel: Optional[str] = Query(None, description="按来源渠道筛选"),
    actor_user_id: Optional[str] = Query(None, description="操作人 user_id"),
    to_assignee_id: Optional[str] = Query(None, description="改派目标 user_id"),
    start_at: Optional[str] = Query(None, description="起始时间 ISO 或 YYYY-MM-DD"),
    end_at: Optional[str] = Query(None, description="结束时间 ISO 或 YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """导出询盘改派/自动分配审计 CSV（admin/super_admin）。"""
    if current_user.role not in ["admin", "super_admin"]:
        return error_response(403, "权限不足")

    from app.core.data_export_guard import assert_export_allowed
    from app.services.inquiry_assignment_audit_service import (
        build_assignment_audit_csv,
        parse_audit_datetime,
        query_assignment_audit_rows,
    )
    try:
        start_dt = parse_audit_datetime(start_at, end_of_day=False)
        end_dt = parse_audit_datetime(end_at, end_of_day=True)
    except ValueError as exc:
        return error_response(400, str(exc))

    rows = query_assignment_audit_rows(
        db,
        start_at=start_dt,
        end_at=end_dt,
        source_channel=source_channel,
        actor_user_id=actor_user_id,
        to_assignee_id=to_assignee_id,
        limit=5000,
    )
    assert_export_allowed(
        db,
        current_user,
        request,
        export_kind="inquiry_assignment_audit_csv",
        scope="tenant",
        row_count=len(rows),
    )
    csv_text = build_assignment_audit_csv(rows)
    return StreamingResponse(
        iter([csv_text]),
        media_type="text/csv; charset=utf-8-sig",
        headers={
            "Content-Disposition": 'attachment; filename="inquiry_assignment_audit.csv"',
        },
    )


@router.put("/{inquiry_id}/assign")
def assign_inquiry_owner(
    inquiry_id: str,
    body: InquiryAssignRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """手动分配询盘负责人。"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    inquiry = db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
    if not inquiry:
        return error_response(404, "询盘不存在")
    denial = _check_inquiry_tenant_access(inquiry, db, current_user, "分配")
    if denial:
        return denial
    from app.services.inquiry_lead_assignment_service import assign_inquiry
    try:
        data = assign_inquiry(
            db,
            inquiry,
            body.assigned_to,
            notify=True,
            actor_user_id=str(current_user.id),
            mode="manual",
            request=request,
        )
    except ValueError as exc:
        return error_response(400, str(exc))
    return success_response(data=data, message="负责人已更新")


@router.get("/{inquiry_id}/assignment-history")
def inquiry_assignment_history(
    inquiry_id: str,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """询盘负责人变更审计（结构化 operation_logs）。"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "sales"]:
        return error_response(403, "权限不足")
    inquiry = db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
    if not inquiry:
        return error_response(404, "询盘不存在")
    denial = _check_inquiry_tenant_access(inquiry, db, current_user, "查看")
    if denial:
        return denial
    if current_user.role == "sales" and getattr(inquiry, "assigned_to", None) != str(current_user.id):
        return error_response(403, "仅可查看本人负责询盘的审计")

    from app.services.inquiry_assignment_audit_service import list_assignment_history
    return success_response(data=list_assignment_history(db, inquiry_id, limit=limit))


@router.get("/{inquiry_id}")
def get_inquiry(inquiry_id: str, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    """获取单个询盘详情（含意向分与 Discovery 追问，强制租户隔离）。"""
    inquiry = db.query(Inquiry).filter(
        Inquiry.id == inquiry_id,
        Inquiry.is_active).first()
    if not inquiry:
        return error_response(404, "询盘不存在")
    denial = _check_inquiry_tenant_access(inquiry, db, current_user, "查看")
    if denial:
        return denial

    from app.services.inquiries_unified_service import InquiriesUnifiedService, serialize_inquiry
    from app.services.ubrain.inquiry_intel_service import enrich_inquiry_intel
    svc = InquiriesUnifiedService(db)
    data = serialize_inquiry(inquiry, svc._cols)
    return success_response(data=enrich_inquiry_intel(data))


@router.post("/public")
def create_public_inquiry(body: PublicInquiryCreate, request: Request, db: Session = Depends(get_db)):
    """公开询盘（推荐：租户站 / IM 条表单，支持智能多渠道线索去重与追加合并）。"""
    client_ip = request.client.host if request.client else "unknown"
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        client_ip = fwd.split(",")[0].strip()
    _check_inquiry_rate(client_ip)

    # 智能去重合并：若同一买家在30分钟内再次提交，追加需求留言并提升意向权重
    existing = _find_recent_duplicate_inquiry(db, body.email, body.phone, body.tenant_id)
    if existing:
        try:
            old_msg = getattr(existing, "message", "") or ""
            new_msg = f"{old_msg}\n---\n[Follow-up Inquiry]: {body.message}"
            existing.message = new_msg
            if body.product and not getattr(existing, "product", None):
                existing.product = body.product
            db.commit()
            db.refresh(existing)
            data = InquiriesUnifiedService(db)._enrich_public_lead_row(existing)
            return success_response(data=data, message="已识别历史沟通记录，需求已成功追加合并")
        except Exception:
            db.rollback()

    try:
        data = InquiriesUnifiedService(db).create_public_lead(
            name=body.name,
            email=body.email,
            message=body.message,
            phone=body.phone,
            product=body.product,
            source_channel=body.source_channel,
            merchant_id=body.merchant_id,
            session_id=body.session_id,
            landing_path=body.landing_path,
            last_click_label=body.last_click_label,
            tenant_id=body.tenant_id,
            utm_source=body.utm_source,
            utm_medium=body.utm_medium,
            utm_campaign=body.utm_campaign,
            utm_content=body.utm_content,
            utm_term=body.utm_term,
            publish_task_id=body.publish_task_id,
        )
    except ValueError as exc:
        return error_response(400, str(exc))
    # P1-8 收尾：按邮箱域名自动建/补公司档案（内部用独立会话，任何失败都不影响询盘创建）。
    # 不做这一步，RFM 标签与 ABM 账号视图就永远挂不到 companies 上。
    try:
        from app.services.acquisition.company_autofill import autofill_from_lead

        autofill_from_lead(email=body.email, contact_name=body.name, tenant_id=body.tenant_id or "")
    except Exception:  # noqa: BLE001
        pass
    return success_response(data=data, message="询盘提交成功")



@router.post("/")
def create_inquiry(
    body: PublicInquiryCreate, db: Session = Depends(get_db)
):
    """创建询盘（公开接口，兼容 POST /inquiries）。"""
    return create_public_inquiry(body, db)


@router.put("/{inquiry_id}")
def update_inquiry(
        inquiry_id: str,
        req: InquiryUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """更新询盘（强制租户隔离）"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "sales"]:
        return error_response(403, "权限不足")

    inquiry = db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
    if not inquiry:
        return error_response(404, "询盘不存在")
    denial = _check_inquiry_tenant_access(inquiry, db, current_user, "修改")
    if denial:
        return denial

    # P0-9: 通用更新同样受漏斗状态机约束（防止经 PUT 绕过状态守卫）
    _put_status = getattr(req, "status", None)
    if _put_status is not None and str(_put_status).strip().lower() != inquiry.status:
        try:
            from app.services.inquiry_funnel_state_machine import can_transition as _ct
            _ok, _reason = _ct(inquiry.status, str(_put_status).strip().lower())
        except Exception:
            _ok, _reason = True, ""
        if not _ok:
            return error_response(
                400,
                f"状态流转被拒绝: {_reason}（当前: {inquiry.status} → 目标: {_put_status}）",
            )

    for k, v in req.items():
        if hasattr(inquiry, k):
            setattr(inquiry, k, v)
    db.commit()
    db.refresh(inquiry)
    return success_response(data=_safe_inquiry_dict(inquiry), message="询盘更新成功")


@router.put("/{inquiry_id}/status")
def update_inquiry_status(
    inquiry_id: str,
    body: InquiryStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新询盘状态（后台快捷接口，强制租户隔离）"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "sales"]:
        return error_response(403, "权限不足")
    inquiry = db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
    if not inquiry:
        return error_response(404, "询盘不存在")
    denial = _check_inquiry_tenant_access(inquiry, db, current_user, "修改")
    if denial:
        return denial
    # ORCH-08 修复：状态白名单校验，防止任意字符串落库
    new_status = body.status.strip().lower()
    if new_status not in _VALID_INQUIRY_STATUSES:
        return error_response(400, f"无效的询盘状态 '{body.status}'，允许值: {', '.join(sorted(_VALID_INQUIRY_STATUSES))}")
    # P0-9: 统一权威漏斗状态机守卫（前进-only + 显式重开，杜绝任意互跳）
    try:
        from app.services.inquiry_funnel_state_machine import can_transition
        ok, reason = can_transition(inquiry.status, new_status)
    except Exception:
        ok, reason = True, ""
    if not ok:
        return error_response(
            400,
            f"状态流转被拒绝: {reason}（当前: {inquiry.status} → 目标: {new_status}）",
        )
    inquiry.status = new_status
    db.commit()
    db.refresh(inquiry)

    # 挂接经验环 (Evolution Engine)：成单与流失沉淀
    try:
        from app.services.acquisition.experience_feed import record_ops_win, record_ops_loss
        if new_status in ("closed", "won", "deal"):
            record_ops_win(
                db,
                tenant_id=str(getattr(inquiry, "tenant_id", "") or ""),
                inquiry_id=str(inquiry.id),
                note=f"询盘状态推进至 {new_status}",
            )
        elif new_status in ("lost", "rejected", "spam"):
            record_ops_loss(
                db,
                tenant_id=str(getattr(inquiry, "tenant_id", "") or ""),
                inquiry_id=str(inquiry.id),
                reasons=[new_status],
                note=f"询盘标记为流失/无效 ({new_status})",
            )
    except Exception:
        pass

    return success_response(data=_safe_inquiry_dict(inquiry), message="状态已更新")


@router.delete("/{inquiry_id}")
def delete_inquiry(
        inquiry_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """删除询盘（强制租户隔离）"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")

    inquiry = db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
    if not inquiry:
        return error_response(404, "询盘不存在")
    denial = _check_inquiry_tenant_access(inquiry, db, current_user, "删除")
    if denial:
        return denial

    db.delete(inquiry)
    db.commit()
    return success_response(message="询盘删除成功")


def _safe_inquiry_dict(inquiry) -> dict:
    """安全序列化询盘 — 不暴露内部字段和敏感数据"""
    return {
        "id": inquiry.id,
        "name": inquiry.name,
        "phone": inquiry.phone,
        "email": inquiry.email,
        "product": inquiry.product,
        "message": inquiry.message[:200] if inquiry.message else None,
        "status": inquiry.status,
        "source_channel": inquiry.source_channel,
        "attribution_channel": inquiry.attribution_channel,
        "source_keyword": inquiry.source_keyword,
        "ai_search_engine": inquiry.ai_search_engine,
        "tenant_id": inquiry.tenant_id,
        "assigned_to": inquiry.assigned_to,
        "wechat": inquiry.wechat,
        "created_at": str(inquiry.created_at) if inquiry.created_at else None,
        "updated_at": str(inquiry.updated_at) if inquiry.updated_at else None,
    }


@router.post("/{inquiry_id}/create-quote", summary="从该询盘快速创建报价单")
def quick_create_quote(
    inquiry_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """外贸商业闭环快捷入口：为指定询盘一键创建报价单草稿。"""
    from app.api.v1.quotes import create_from_inquiry, QuoteFromInquiryRequest
    req = QuoteFromInquiryRequest(inquiry_id=inquiry_id)
    return create_from_inquiry(req=req, db=db, current_user=current_user)

