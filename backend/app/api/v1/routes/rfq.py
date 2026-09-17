# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""RFQ 需求单路由 — 买家结构化的询价请求（公开提交 + 管理端管理）。

端点：
- POST   /api/v1/rfq                 公开提交 RFQ（无需登录）
- GET    /api/v1/rfq                 管理端列表
- GET    /api/v1/rfq/{rfq_id}        管理端详情
- PUT    /api/v1/rfq/{rfq_id}/status 管理端更新状态
- PUT    /api/v1/rfq/{rfq_id}/assign 管理端分配负责人

CHAIN-03/04: Redis限流替代进程内限流，支持分布式部署。
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.rfq import RFQ, RFQDocument, RFQItem, RFQRequirement
from app.models.user import User
from app.schemas.rfq import RFQAssignRequest, RFQCreate, RFQStatusUpdate
from app.services.rfq_service import RFQ_SCORE_RULES, score_rfq, score_to_label
from app.core.cache import redis_client, set_cache, get_cache
import logging
logger = logging.getLogger(__name__)

router = APIRouter()

# CHAIN-03: Redis限流配置（5条 / 10分钟 / IP）
_RFQ_RATE_LIMIT = 5
_RFQ_RATE_WINDOW = 600  # 600秒 = 10分钟
_RFQ_RATE_TTL = _RFQ_RATE_WINDOW + 60  # 多加60秒安全余量

# RFQ 状态白名单（避免任意字符串落库，BUG-21 修复）
_VALID_RFQ_STATUSES = frozenset({
    "pending", "quoted", "negotiating", "won", "lost", "closed",
})


def _check_rfq_rate(ip: str) -> None:
    """检查RFQ提交频率限制（Redis分布式限流）。"""
    if not redis_client:
        # Redis不可用时，降级到内存限流（兜底）
        return _check_rfq_rate_in_memory(ip)

    rate_key = f"rfq:rate:{ip}"
    try:
        # 使用Redis原子计数器
        current = redis_client.incr(rate_key)
        if current == 1:
            # 首次请求，设置TTL
            redis_client.expire(rate_key, _RFQ_RATE_TTL)
        if current > _RFQ_RATE_LIMIT:
            raise HTTPException(429, "提交过于频繁，请 10 分钟后再试")
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.warning("RFQ rate limit check failed: %s", exc)
        # 降级到内存限流
        _check_rfq_rate_in_memory(ip)


def _check_rfq_rate_in_memory(ip: str) -> None:
    """进程内限流兜底（Redis不可用时使用）。"""
    rate_key = f"rfq:rate:{ip}"
    now = time.time()
    # 获取现有记录
    records = get_cache(rate_key) or []
    if not isinstance(records, list):
        records = []

    # 清理过期记录
    records = [t for t in records if now - t < _RFQ_RATE_WINDOW]
    # 检查限制
    if len(records) >= _RFQ_RATE_LIMIT:
        raise HTTPException(429, "提交过于频繁，请 10 分钟后再试")

    # 添加新记录
    records.append(now)
    # 保存回缓存（TTL 11分钟）
    set_cache(rate_key, records, timedelta(seconds=_RFQ_RATE_TTL))


def _check_rfq_duplicate(db: Session, email: str, company: str, application: str) -> None:
    """30 分钟内相同 email+公司+应用视为重复提交。"""
    if not email:
        return
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)
    dup = (
        db.query(RFQ)
        .filter(
            RFQ.email == email,
            RFQ.company == company,
            RFQ.application == application,
            RFQ.created_at > cutoff,
            RFQ.deleted_at.is_(None),
        )
        .first()
    )
    if dup:
        raise HTTPException(429, "您已提交过相似需求，我们将尽快联系您")


def _parse_date(value: Optional[str]) -> Any:
    """执行 parse_date 相关逻辑处理。
    
    :param value: 值
    :return: 返回处理结果。
    :raises: ValueError 等异常在错误时抛出。
    """
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("期望交期格式应为 YYYY-MM-DD")


def _serialize_rfq(rfq: RFQ) -> dict[str, Any]:
    """序列化 RFQ（含明细、技术要求、来源归因）。"""
    items = []
    for it in (rfq.items or []):
        if getattr(it, "deleted_at", None) is not None:
            continue
        items.append({
            "product_id": it.product_id,
            "product_name": it.product_name,
            "product_slug": it.product_slug,
            "quantity": it.quantity,
            "unit": it.unit,
            "dimensions": _safe_json(it.dimensions),
            "notes": it.notes,
        })

    requirements = []
    for r in (rfq.requirements or []):
        if getattr(r, "deleted_at", None) is not None:
            continue
        requirements.append({
            "req_key": r.req_key,
            "req_label": r.req_label,
            "req_value": r.req_value,
            "required": bool(r.required),
        })

    return {
        "id": str(rfq.id),
        "company": rfq.company,
        "company_domain": rfq.company_domain,
        "country": rfq.country,
        "city": rfq.city,
        "project": rfq.project,
        "project_type": rfq.project_type,
        "project_stage": rfq.project_stage,
        "application": rfq.application,
        "contact_name": rfq.contact_name,
        "email": rfq.email,
        "phone": rfq.phone,
        "wechat": rfq.wechat,
        "quantity": rfq.quantity,
        "quantity_unit": rfq.quantity_unit,
        "delivery_date": rfq.delivery_date.isoformat() if rfq.delivery_date else None,
        "incoterm": rfq.incoterm,
        "currency": rfq.currency,
        "status": rfq.status,
        "rfq_score": rfq.rfq_score,
        "score_label": rfq.score_label or score_to_label(rfq.rfq_score or 0),
        "intent_score": rfq.intent_score,
        "source": rfq.source,
        "source_channel": rfq.source_channel,
        "source_url": rfq.source_url,
        "session_id": rfq.session_id,
        "tenant_id": rfq.tenant_id,
        "assigned_to": rfq.assigned_to,
        "matched_product_ids": _safe_json(rfq.matched_product_ids),
        "notes": rfq.notes,
        "items": items,
        "requirements": requirements,
        "created_at": rfq.created_at.isoformat() if rfq.created_at else None,
        "updated_at": rfq.updated_at.isoformat() if rfq.updated_at else None,
        "submitted_at": rfq.submitted_at.isoformat() if rfq.submitted_at else None,
    }


def _safe_json(value: Optional[str]) -> Any:
    """执行 safe_json 相关逻辑处理。
    
    :param value: 值
    :return: 返回处理结果。
    """
    if not value:
        return []
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []


def _build_rfq_object(body, scored, delivery_date):
    """根据请求体与评分构建 RFQ 持久化对象。"""
    return RFQ(
        company=body.company,
        company_domain=body.company_domain,
        country=body.country,
        city=body.city,
        project=body.project,
        project_type=body.project_type,
        project_stage=body.project_stage,
        application=body.application,
        contact_name=body.contact_name,
        email=body.email,
        phone=body.phone,
        wechat=body.wechat,
        quantity=body.quantity,
        quantity_unit=body.quantity_unit,
        delivery_date=delivery_date,
        incoterm=body.incoterm,
        currency=body.currency,
        notes=body.notes,
        source=body.source,
        source_channel=body.source_channel,
        source_url=body.source_url,
        session_id=body.session_id,
        tenant_id=body.tenant_id,
        matched_product_ids=json.dumps(body.matched_product_ids) if body.matched_product_ids else None,
        requirements_json=json.dumps(
            [r.model_dump() for r in body.requirements] if body.requirements else [],
            ensure_ascii=False,
        ),
        rfq_score=scored["score"],
        score_label=score_to_label(scored["score"]),
        status="pending",
        submitted_at=datetime.now(timezone.utc),
    )


def _persist_rfq_items(db: Session, rfq, body):
    """写入 RFQ 条目子表。"""
    for it in body.items or []:
        db.add(RFQItem(
            rfq_id=rfq.id,
            product_id=it.product_id,
            product_name=it.product_name,
            product_slug=it.product_slug,
            quantity=it.quantity,
            unit=it.unit,
            dimensions=json.dumps(it.dimensions, ensure_ascii=False) if it.dimensions else None,
            notes=it.notes,
        ))


def _persist_rfq_requirements(db: Session, rfq, body):
    """写入 RFQ 需求子表。"""
    for req in body.requirements or []:
        db.add(RFQRequirement(
            rfq_id=rfq.id,
            req_key=req.req_key,
            req_label=req.req_label,
            req_value=req.req_value,
            required=req.required,
        ))


def _create_rfq_sales_task(db: Session, rfq, body, scored):
    """创建 RFQ 关联的销售跟进任务。"""
    from app.models.sales_task import SalesTask
    priority = "high" if scored["score"] >= 60 else ("normal" if scored["score"] >= 40 else "low")
    db.add(SalesTask(
        title=f"跟进 RFQ：{body.company} - {body.application}",
        description=(f"RFQ Score={scored['score']}；联系人 {body.contact_name}（{body.email}）；"
                    f"项目：{body.project or '\\u2014'}；国家：{body.country}；数量：{body.quantity or '\\u2014'} {body.quantity_unit or ''}"),
        task_type="rfq_response",
        priority=priority,
        rfq_id=rfq.id,
        tenant_id=rfq.tenant_id,
        created_by="system",
    ))
    db.commit()


@router.post("", summary="\\u516c\\u5f00\\u63d0\\u4ea4 RFQ\\uff08\\u65e0\\u9700\\u767b\\u5f55\\uff09")
def create_rfq(body: RFQCreate, request: Request, db: Session = Depends(get_db)):
    """\\u521b\\u5efa RFQ \\u9700\\u6c42\\u5355\\uff1a\\u6821\\u9a8c \\u2192 \\u53bb\\u91cd \\u2192 \\u516c\\u53f8\\u89e3\\u6790 \\u2192 \\u4ea7\\u54c1\\u6821\\u9a8c \\u2192 \\u8bc4\\u5206 \\u2192 \\u6301\\u4e45\\u5316\\u3002

    \\u516c\\u5f00\\u7aef\\u70b9\\uff0c\\u5df2\\u5728 CSRF \\u4e2d\\u95f4\\u4ef6\\u767d\\u540d\\u5355\\u3002
    """
    client_ip = request.client.host if request.client else "unknown"
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        client_ip = fwd.split(",")[0].strip()

    # CHAIN-03: Redis\\u5206\\u5e03\\u5f0f\\u9650\\u6d41
    try:
        _check_rfq_rate(client_ip)
    except HTTPException as exc:
        raise exc

    try:
        _check_rfq_duplicate(db, body.email, body.company, body.application)
    except HTTPException as exc:
        raise exc

    # \\u89e3\\u6790\\u671f\\u671b\\u4ea4\\u671f
    try:
        delivery_date = _parse_date(body.delivery_date)
    except ValueError as exc:
        return error_response(400, str(exc))

    # \\u786e\\u5b9a\\u6027\\u8bc4\\u5206
    payload = body.model_dump()
    scored = score_rfq(payload)
    rfq = _build_rfq_object(body, scored, delivery_date)
    db.add(rfq)
    db.flush()
    _persist_rfq_items(db, rfq, body)
    _persist_rfq_requirements(db, rfq, body)
    db.commit()
    db.refresh(rfq)
    # \\u521b\\u5efa\\u9500\\u552e\\u8ddf\\u8fdb\\u4efb\\u52a1\\uff08RFQ \\u2192 Sales Task \\u95ed\\u73af\\uff09
    try:
        _create_rfq_sales_task(db, rfq, body, scored)
    except Exception as exc:  # noqa: BLE001
        logger.warning("\\u521b\\u5efa RFQ \\u9500\\u552e\\u4efb\\u52a1\\u5931\\u8d25: %s", exc)

    data = _serialize_rfq(rfq)
    data["score_details"] = scored["details"]
    data["score_rules"] = RFQ_SCORE_RULES
    return success_response(data=data, message="RFQ \\u63d0\\u4ea4\\u6210\\u529f")


@router.get("", summary="RFQ 列表（管理端）")
def list_rfqs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    min_score: Optional[int] = Query(None, ge=0, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """分页列出 RFQ（管理端）。sales 仅看本人负责；admin/super_admin 看全部。"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "sales"]:
        return error_response(403, "权限不足")

    q = db.query(RFQ).filter(RFQ.deleted_at.is_(None))
    from app.core.tenant_scope import scope_tenant_query
    q = scope_tenant_query(q, RFQ, db, current_user)
    if current_user.role == "sales":
        q = q.filter(RFQ.assigned_to == str(current_user.id))

    if status:
        q = q.filter(RFQ.status == status)
    if country:
        q = q.filter(RFQ.country.ilike(f"%{country}%"))
    if min_score is not None:
        q = q.filter(RFQ.rfq_score >= min_score)
    if search:
        like = f"%{search}%"
        q = q.filter(
            (RFQ.company.ilike(like))
            | (RFQ.email.ilike(like))
            | (RFQ.application.ilike(like))
            | (RFQ.contact_name.ilike(like))
        )

    total = q.count()
    items = (
        q.order_by(RFQ.rfq_score.desc(), RFQ.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return success_response(
        data={
            "items": [_serialize_rfq(r) for r in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/stats", summary="RFQ 统计（管理端看板）")
def rfq_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """按状态与评分区间统计 RFQ（供后台 Dashboard 使用）。"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "sales"]:
        return error_response(403, "权限不足")

    from sqlalchemy import func as sa_func
    q = db.query(RFQ).filter(RFQ.deleted_at.is_(None))
    if current_user.role == "sales":
        q = q.filter(RFQ.assigned_to == str(current_user.id))

    total = q.count()
    by_status = dict(
        db.query(RFQ.status, sa_func.count(RFQ.id))
        .filter(RFQ.deleted_at.is_(None))
        .group_by(RFQ.status)
        .all()
    )
    high_intent = q.filter(RFQ.rfq_score >= 60).count()
    unassigned = q.filter(RFQ.assigned_to.is_(None)).count()
    return success_response(
        data={
            "total": total,
            "by_status": {k: int(v) for k, v in by_status.items()},
            "high_intent": high_intent,
            "unassigned": unassigned,
        }
    )


@router.get("/{rfq_id}", summary="RFQ 详情（管理端）")
def get_rfq(
    rfq_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 GET /{rfq_id} 请求，获取相关资源。
    
    :param rfq_id: 参数 rfq_id
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "sales"]:
        return error_response(403, "权限不足")
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id, RFQ.deleted_at.is_(None)).first()
    if not rfq:
        return error_response(404, "RFQ 不存在")
    from app.core.tenant_scope import tenant_can_access
    if not tenant_can_access(db, current_user, rfq.tenant_id):
        return error_response(404, "RFQ 不存在")  # 跨租户按不存在处理，不泄露存在性
    if current_user.role == "sales" and rfq.assigned_to != str(current_user.id):
        return error_response(403, "仅可查看本人负责的 RFQ")
    return success_response(data=_serialize_rfq(rfq))


@router.put("/{rfq_id}/status", summary="更新 RFQ 状态（管理端）")
def update_rfq_status(
    rfq_id: str,
    body: RFQStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 PUT /{rfq_id}/status 请求，更新相关资源。
    
    :param rfq_id: 参数 rfq_id
    :param body: 请求体
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    if current_user.role not in ["admin", "super_admin", "tenant_admin", "sales"]:
        return error_response(403, "权限不足")
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id, RFQ.deleted_at.is_(None)).first()
    if not rfq:
        return error_response(404, "RFQ 不存在")
    new_status = body.status.strip().lower()
    if new_status not in _VALID_RFQ_STATUSES:
        return error_response(400, f"无效的RFQ状态 '{body.status}'，允许值: {', '.join(sorted(_VALID_RFQ_STATUSES))}")
    rfq.status = new_status
    db.commit()
    db.refresh(rfq)
    return success_response(data=_serialize_rfq(rfq), message="状态已更新")


@router.put("/{rfq_id}/assign", summary="分配 RFQ 负责人（管理端）")
def assign_rfq_owner(
    rfq_id: str,
    body: RFQAssignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 PUT /{rfq_id}/assign 请求，assign相关资源。
    
    :param rfq_id: 参数 rfq_id
    :param body: 请求体
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id, RFQ.deleted_at.is_(None)).first()
    if not rfq:
        return error_response(404, "RFQ 不存在")
    rfq.assigned_to = body.assigned_to
    db.commit()
    db.refresh(rfq)
    return success_response(data=_serialize_rfq(rfq), message="负责人已更新")
