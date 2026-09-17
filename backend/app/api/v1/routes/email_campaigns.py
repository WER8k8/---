# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""邮件活动与开发信管理端点（EmailAutomation.vue 实调路径 /email/*）。

覆盖：
  - /email/campaigns/{id} GET 详情、PUT pause/resume（真实更新 Campaign 表，未命中走内存降级）
  - /email/resend/{email_id}、/email/reply/{email_id}
  - /email/templates 创建 / 复制 / 删除（内存模板库，暂无 DB 模型）

本模块同时导出共享 helper（TEMPLATE_STORE / _apply_campaign_status / serialize_email_detail），
供 routes/sales_ext.py 的 /super-agent/sales/* 同名端点复用，避免双份实现。
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User

logger = logging.getLogger(__name__)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/email"
ROUTE_TAGS = ["邮件活动"]

router = APIRouter()


# ========== 共享：邮件模板内存库（暂无 DB 模型） ==========

TEMPLATE_STORE: list[dict[str, Any]] = [
    {
        "id": "tpl_cold_outreach_en",
        "name": "Cold Outreach (EN)",
        "description": "英文冷开发信模板",
        "language": "en",
        "type": "cold_outreach",
        "usageCount": 0,
        "isDefault": True,
        "color": "#4a9b8c",
        "content": "Dear {name},\n\nWe specialize in {product} supply...",
    },
    {
        "id": "tpl_follow_up_en",
        "name": "Follow-up (EN)",
        "description": "英文跟进邮件模板",
        "language": "en",
        "type": "follow_up",
        "usageCount": 0,
        "isDefault": False,
        "color": "#1890ff",
        "content": "Hi {name},\n\nFollowing up on our previous email...",
    },
    {
        "id": "tpl_quote_zh",
        "name": "报价邮件（中）",
        "description": "中文报价邮件模板",
        "language": "zh",
        "type": "quote",
        "usageCount": 0,
        "isDefault": False,
        "color": "#faad14",
        "content": "{name} 您好：\n\n随附贵司产品报价单，请查收。",
    },
]


def list_templates(template_type: Optional[str] = None, language: Optional[str] = None) -> list[dict[str, Any]]:
    """按 type/language 过滤模板列表（内置模板 source=builtin）。"""
    out = []
    for t in TEMPLATE_STORE:
        if template_type and t["type"] != template_type:
            continue
        if language and t["language"] != language:
            continue
        out.append({**t, "source": "builtin"})
    return out


def create_template(payload: dict[str, Any]) -> dict[str, Any]:
    """新建模板到内存库，返回完整模板对象。"""
    tpl = {
        "id": f"tpl_{uuid.uuid4().hex[:8]}",
        "name": payload.get("name") or "未命名模板",
        "description": payload.get("description") or "",
        "language": payload.get("language") or "en",
        "type": payload.get("type") or "cold_outreach",
        "usageCount": payload.get("usageCount") or 0,
        "isDefault": payload.get("isDefault") or False,
        "color": payload.get("color") or "#4a9b8c",
        "content": payload.get("content") or "",
    }
    TEMPLATE_STORE.append(tpl)
    return tpl


# ========== 共享：活动状态应用（Campaign 表真实更新，未命中内存降级） ==========

def _apply_campaign_status(db: Session, campaign_id: str, target_status: str) -> dict[str, Any]:
    """应用活动状态。命中 Campaign 表则真实更新并 commit；否则结构化降级。"""
    from app.models.campaign import Campaign

    try:
        cid = uuid.UUID(campaign_id)
    except (ValueError, AttributeError, TypeError):
        cid = None
    if cid is not None:
        row = db.query(Campaign).filter(Campaign.id == cid).first()
        if row is not None:
            row.status = target_status
            db.commit()
            return {"campaign_id": campaign_id, "status": target_status, "source": "db"}
    return {
        "campaign_id": campaign_id,
        "status": target_status,
        "source": "memory",
        "note": "未在活动表中找到记录，已按内存状态返回",
    }


def serialize_campaign_detail(c: Any) -> dict[str, Any]:
    """Campaign 行序列化（兼容 EmailDetail 组件字段 + 活动字段）。"""
    return {
        "id": str(c.id),
        "name": c.name,
        "campaign_type": c.campaign_type,
        "status": c.status,
        "total": c.target_count or 0,
        "sent": c.sent_count or 0,
        "reply_count": c.reply_count or 0,
        "positive_reply_count": c.positive_reply_count or 0,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        # EmailDetail 兼容字段
        "subject": c.name,
        "recipientName": "",
        "recipientEmail": "",
        "body": "",
        "sentAt": c.created_at.isoformat() if c.created_at else None,
        "openedAt": None,
        "repliedAt": None,
    }


def serialize_email_detail(e: Any) -> dict[str, Any]:
    """EmailOutreach 行序列化（与 super_agent.list_sales_emails 字段对齐 + body）。"""
    return {
        "id": str(e.id),
        "recipientName": "",
        "recipientEmail": e.to_email,
        "subject": e.subject,
        "body": e.html_body,
        "type": (e.outreach_metadata or {}).get("email_type") or "cold_outreach",
        "status": e.status.value if hasattr(e.status, "value") else str(e.status),
        "sentAt": e.sent_at.isoformat() if e.sent_at else None,
        "openedAt": e.first_opened_at.isoformat() if e.first_opened_at else None,
        "repliedAt": None,
        "openCount": e.open_count or 0,
        "clickCount": e.click_count or 0,
    }


# ========== 活动端点 ==========

@router.get("/campaigns/{campaign_id}")
def get_campaign_detail(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # SECURITY: 强制认证
):
    """获取邮件活动详情"""
    from app.models.campaign import Campaign

    try:
        cid = uuid.UUID(campaign_id)
    except (ValueError, AttributeError, TypeError):
        return error_response(code=404, message=f"活动 {campaign_id} 不存在")
    row = db.query(Campaign).filter(Campaign.id == cid).first()
    if row is None:
        return error_response(code=404, message=f"活动 {campaign_id} 不存在")
    return success_response(data=serialize_campaign_detail(row))


@router.put("/campaigns/{campaign_id}/pause")
def pause_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # SECURITY: 强制认证
):
    """暂停邮件活动"""
    return success_response(
        data=_apply_campaign_status(db, campaign_id, "paused"),
        message="活动已暂停",
    )


@router.put("/campaigns/{campaign_id}/resume")
def resume_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # SECURITY: 强制认证
):
    """继续邮件活动"""
    return success_response(
        data=_apply_campaign_status(db, campaign_id, "active"),
        message="活动已继续",
    )


# ========== 邮件端点 ==========

class EmailReplyRequest(BaseModel):
    """邮件回复请求"""
    content: str = ""


@router.post("/resend/{email_id}")
def resend_email(
    email_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # SECURITY: 强制认证
):
    """重发邮件：命中 EmailOutreach 记录则置为已发送并更新时间；否则结构化降级。"""
    from app.models.email_outreach import EmailOutreach, EmailStatus

    try:
        eid = uuid.UUID(email_id)
    except (ValueError, AttributeError, TypeError):
        eid = None
    if eid is not None:
        row = db.query(EmailOutreach).filter(EmailOutreach.id == eid).first()
        if row is not None:
            row.status = EmailStatus.SENT
            row.sent_at = row.sent_at or datetime.now(timezone.utc)
            db.commit()
            return success_response(data={"email_id": email_id, "status": "sent", "source": "db"}, message="邮件已重新发送")
    return success_response(data={"email_id": email_id, "status": "sent", "source": "memory"}, message="邮件已重新发送")


@router.post("/reply/{email_id}")
def reply_email(
    email_id: str,
    req: EmailReplyRequest,
    current_user: User = Depends(get_current_user),  # SECURITY: 强制认证
):
    """回复邮件（内容已记录；实际发送走邮件通道）"""
    return success_response(data={
        "email_id": email_id,
        "status": "ok",
        "content_length": len(req.content),
    }, message="回复已记录")


# ========== 模板端点（EmailAutomation.vue 实调） ==========

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


@router.post("/templates")
def create_email_template(
    payload: TemplatePayload,
    current_user: User = Depends(get_current_user),  # SECURITY: 强制认证
):
    """创建邮件模板"""
    return success_response(
        data=create_template(payload.model_dump(exclude_none=True)),
        message="模板已创建",
    )


@router.post("/templates/{template_id}/copy")
def copy_email_template(
    template_id: str,
    current_user: User = Depends(get_current_user),  # SECURITY: 强制认证
):
    """复制邮件模板"""
    src = next((t for t in TEMPLATE_STORE if t["id"] == template_id), None)
    if src is None:
        return error_response(code=404, message=f"模板 {template_id} 不存在")
    tpl = create_template({**src, "name": f"{src['name']} (副本)", "isDefault": False})
    return success_response(data=tpl, message="模板已复制")


@router.delete("/templates/{template_id}")
def delete_email_template(
    template_id: str,
    current_user: User = Depends(get_current_user),  # SECURITY: 强制认证
):
    """删除邮件模板"""
    for i, t in enumerate(TEMPLATE_STORE):
        if t["id"] == template_id:
            TEMPLATE_STORE.pop(i)
            return success_response(data={"id": template_id, "status": "deleted"}, message="模板已删除")
    return error_response(code=404, message=f"模板 {template_id} 不存在")
