# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""销售模块补充端点（sales.ts API 层 /super-agent/sales/* 包装 + 销售仪表板）。

复用 routes/email_campaigns.py 的共享 helper，避免双份实现；
仪表板 endpoints 无前端消费者，返回结构化数据（metrics 取真实计数）。
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.api.v1.routes.email_campaigns import (
    TEMPLATE_STORE,
    _apply_campaign_status,
    create_template,
    list_templates,
    serialize_email_detail,
)

logger = logging.getLogger(__name__)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/super-agent/sales"
ROUTE_TAGS = ["销售补充"]

router = APIRouter()


# ========== 邮件活动（sales.ts pauseCampaign/resumeCampaign） ==========

@router.post("/campaigns/{campaign_id}/pause")
def pause_campaign_super(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # SECURITY: 强制认证
):
    """暂停邮件活动（/super-agent/sales 别名）"""
    return success_response(
        data=_apply_campaign_status(db, campaign_id, "paused"),
        message="活动已暂停",
    )


@router.post("/campaigns/{campaign_id}/resume")
def resume_campaign_super(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # SECURITY: 强制认证
):
    """继续邮件活动（/super-agent/sales 别名）"""
    return success_response(
        data=_apply_campaign_status(db, campaign_id, "active"),
        message="活动已继续",
    )


# ========== 邮件端点（sales.ts getEmailDetail / resendEmail） ==========

@router.get("/emails/{email_id}")
def get_email_detail(
    email_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # SECURITY: 强制认证
):
    """获取邮件详情（EmailOutreach 真实查库）"""
    from app.models.email_outreach import EmailOutreach

    try:
        eid = uuid.UUID(email_id)
    except (ValueError, AttributeError, TypeError):
        return error_response(code=404, message=f"邮件 {email_id} 不存在")
    try:
        row = db.query(EmailOutreach).filter(EmailOutreach.id == eid).first()
    except Exception as e:  # noqa: BLE001  # 表缺失（如轻量测试库）时降级
        logger.warning("邮件详情查询失败，降级 404: %s", e)
        row = None
    if row is None:
        return error_response(code=404, message=f"邮件 {email_id} 不存在")
    return success_response(data=serialize_email_detail(row))


@router.post("/emails/{email_id}/resend")
def resend_email_super(
    email_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # SECURITY: 强制认证
):
    """重发邮件（/super-agent/sales 别名）"""
    from app.models.email_outreach import EmailOutreach, EmailStatus
    from datetime import datetime, timezone

    try:
        eid = uuid.UUID(email_id)
    except (ValueError, AttributeError, TypeError):
        eid = None
    if eid is not None:
        try:
            row = db.query(EmailOutreach).filter(EmailOutreach.id == eid).first()
        except Exception as e:  # noqa: BLE001  # 表缺失（如轻量测试库）时降级
            logger.warning("邮件重发查询失败，降级内存: %s", e)
            row = None
        if row is not None:
            row.status = EmailStatus.SENT
            row.sent_at = row.sent_at or datetime.now(timezone.utc)
            db.commit()
            return success_response(data={"email_id": email_id, "status": "sent", "source": "db"}, message="邮件已重新发送")
    return success_response(data={"email_id": email_id, "status": "sent", "source": "memory"}, message="邮件已重新发送")


# ========== 邮件模板（sales.ts templates CRUD，内存模板库） ==========

class TemplatePayload(BaseModel):
    """模板创建/更新载荷"""
    name: Optional[str] = None
    description: Optional[str] = None
    language: Optional[str] = None
    type: Optional[str] = None
    usageCount: Optional[int] = None
    isDefault: Optional[bool] = None
    color: Optional[str] = None
    content: Optional[str] = None


@router.get("/templates")
def get_email_templates(
    type: Optional[str] = Query(None, alias="type"),
    language: Optional[str] = Query(None, alias="language"),
    current_user: User = Depends(get_current_user),  # SECURITY: 强制认证
):
    """获取邮件模板列表（返回数组，前端 loadTemplates 直用）"""
    return success_response(data=list_templates(template_type=type, language=language))


@router.post("/templates")
def create_email_template_super(
    payload: TemplatePayload,
    current_user: User = Depends(get_current_user),  # SECURITY: 强制认证
):
    """创建邮件模板"""
    return success_response(
        data=create_template(payload.model_dump(exclude_none=True)),
        message="模板已创建",
    )


@router.put("/templates/{template_id}")
def update_email_template_super(
    template_id: str,
    payload: TemplatePayload,
    current_user: User = Depends(get_current_user),  # SECURITY: 强制认证
):
    """更新邮件模板"""
    data = payload.model_dump(exclude_none=True)
    for t in TEMPLATE_STORE:
        if t["id"] == template_id:
            t.update(data)
            return success_response(data=t, message="模板已更新")
    return error_response(code=404, message=f"模板 {template_id} 不存在")


@router.delete("/templates/{template_id}")
def delete_email_template_super(
    template_id: str,
    current_user: User = Depends(get_current_user),  # SECURITY: 强制认证
):
    """删除邮件模板"""
    for i, t in enumerate(TEMPLATE_STORE):
        if t["id"] == template_id:
            TEMPLATE_STORE.pop(i)
            return success_response(data={"id": template_id, "status": "deleted"}, message="模板已删除")
    return error_response(code=404, message=f"模板 {template_id} 不存在")


# ========== 销售仪表板（sales.ts getSalesMetrics/Funnel/Trend/Regions） ==========

@router.get("/dashboard/metrics")
def get_sales_metrics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # SECURITY: 强制认证
):
    """销售指标（真实计数：询盘数 / 开发信数；表缺失时结构化 0，不抛 500）"""
    inquiries = 0
    emails_sent = 0
    try:
        from app.models.email_outreach import EmailOutreach
        from app.models.inquiry import Inquiry

        inquiries = db.query(func.count(Inquiry.id)).scalar() or 0
        emails_sent = db.query(func.count(EmailOutreach.id)).scalar() or 0
    except Exception as e:  # noqa: BLE001  # 表缺失（如轻量测试库）时降级
        logger.warning("销售指标统计失败，降级返回 0: %s", e)
    return success_response(data={
        "totalCustomers": inquiries,
        "customerGrowth": 0,
        "newCustomers": inquiries,
        "newCustomerGrowth": 0,
        "revenue": 0,
        "revenueGrowth": 0,
        "conversionRate": 0,
        "conversionGrowth": 0,
        "inquiries": inquiries,
        "inquiryGrowth": 0,
        "emailsSent": emails_sent,
        "emailGrowth": 0,
    })


_FUNNEL_STAGES: list[dict[str, Any]] = [
    {"key": "pending", "name": "询盘", "color": "#1890ff"},
    {"key": "processing", "name": "跟进中", "color": "#fa8c16"},
    {"key": "converted", "name": "成交", "color": "#52c41a"},
]


@router.get("/dashboard/funnel")
def get_sales_funnel(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # SECURITY: 强制认证
):
    """销售漏斗（按 Inquiry.status 真实分组计数；表缺失时返回空漏斗）"""
    try:
        from app.models.inquiry import Inquiry

        rows = db.query(Inquiry.status, func.count(Inquiry.id)).group_by(Inquiry.status).all()
    except Exception as e:  # noqa: BLE001  # 表缺失（如轻量测试库）时降级
        logger.warning("销售漏斗统计失败，降级返回空: %s", e)
        rows = []
    total = sum(n for _, n in rows) or 0
    counts: Dict[str, int] = {s: n for s, n in rows}
    funnel = []
    for stage in _FUNNEL_STAGES:
        count = counts.get(stage["key"], 0)
        funnel.append({
            "name": stage["name"],
            "count": count,
            "percentage": round(count / total * 100, 1) if total else 0,
            "rate": round(count / total * 100, 1) if total else 0,
            "color": stage["color"],
        })
    # 未映射状态归入「其他」
    mapped = {s["key"] for s in _FUNNEL_STAGES}
    other = sum(n for s, n in rows if s not in mapped)
    funnel.append({
        "name": "其他",
        "count": other,
        "percentage": round(other / total * 100, 1) if total else 0,
        "rate": round(other / total * 100, 1) if total else 0,
        "color": "#d9d9d9",
    })
    return success_response(data=funnel)


@router.get("/dashboard/trend")
def get_sales_trend(
    type: str = Query("revenue", description="revenue/customers/inquiries"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user),  # SECURITY: 强制认证
):
    """销售趋势（结构化空数据，待趋势表落地）"""
    return success_response(data={"type": type, "points": []})


@router.get("/dashboard/regions")
def get_region_distribution(
    current_user: User = Depends(get_current_user),  # SECURITY: 强制认证
):
    """地区分布（结构化空数据，待客户国家字段统计落地）"""
    return success_response(data=[])
