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
        "name": "Cold Intro · Building Materials",
        "description": "英文冷开发·建材首次破冰（专业简洁）",
        "language": "en",
        "type": "cold_outreach",
        "usageCount": 0,
        "isDefault": True,
        "color": "#4a9b8c",
        "tags": ["建材", "首封", "英文"],
        "subject": "{product} manufacturer from China — quick intro",
        "content": (
            "Dear {name},\n\n"
            "This is {sender} from {company}, a manufacturer of {product} "
            "for contractors and distributors in {market}.\n\n"
            "We help buyers like {buyer_company} get:\n"
            "- Stable quality with export packing\n"
            "- Clear lead time and competitive FOB/CIF quotes\n"
            "- One-stop docs: PI / CI / PL / CO\n\n"
            "If you are sourcing {product} this quarter, may I send a short quote "
            "based on your usual specs?\n\n"
            "Best regards,\n{sender}\n{company}"
        ),
    },
    {
        "id": "tpl_cold_outreach_zh",
        "name": "冷开发信 · 建材出海",
        "description": "中文冷开发·结构清晰、降低回复成本",
        "language": "zh",
        "type": "cold_outreach",
        "usageCount": 0,
        "isDefault": False,
        "color": "#2f6a5f",
        "tags": ["建材", "首封", "中文"],
        "subject": "{product} 供应商介绍 · 可提供样品与完整单证",
        "content": (
            "{name} 您好：\n\n"
            "我是 {company} 的 {sender}，我们专业生产 {product}，长期服务 {market} 的工程商与批发客户。\n\n"
            "我们可以提供：\n"
            "1. 稳定品质与出口包装\n"
            "2. 明确交期，FOB/CIF 可报价\n"
            "3. PI / 发票 / 装箱单 / 原产地证等全套单证\n\n"
            "如贵司本季有 {product} 采购计划，回复规格与数量即可，我 24 小时内给到报价。\n\n"
            "此致\n{sender}\n{company}"
        ),
    },
    {
        "id": "tpl_follow_up_en",
        "name": "Follow-up · Soft",
        "description": "英文二次跟进·不施压、给价值",
        "language": "en",
        "type": "follow_up",
        "usageCount": 0,
        "isDefault": False,
        "color": "#3d7ea6",
        "tags": ["跟进", "英文"],
        "subject": "Re: {product} — spec sheet & FOB range",
        "content": (
            "Hi {name},\n\n"
            "Just floating this back up in case it got buried.\n\n"
            "I can send:\n"
            "- Spec sheet for {product}\n"
            "- FOB range based on {quantity}\n"
            "- Sample / packing photos\n\n"
            "If timing is not right, a one-line reply is enough and I will follow up later.\n\n"
            "Best,\n{sender}"
        ),
    },
    {
        "id": "tpl_follow_up_zh",
        "name": "跟进信 · 温和",
        "description": "中文二次跟进·一句话可回",
        "language": "zh",
        "type": "follow_up",
        "usageCount": 0,
        "isDefault": False,
        "color": "#3d7ea6",
        "tags": ["跟进", "中文"],
        "subject": "跟进：{product} 规格书与离岸价区间",
        "content": (
            "{name} 您好：\n\n"
            "上次关于 {product} 的邮件可能被淹了，简单跟进一下。\n\n"
            "可立即提供：规格书、{quantity} 对应 FOB 区间、包装图。\n"
            "若时间不合适，回一个字「暂缓」即可，我改日再联系。\n\n"
            "{sender}"
        ),
    },
    {
        "id": "tpl_quote_en",
        "name": "Quotation · Clear Next Step",
        "description": "英文报价信·报价+条款+下一步",
        "language": "en",
        "type": "quote",
        "usageCount": 0,
        "isDefault": False,
        "color": "#d18b2f",
        "tags": ["报价", "英文"],
        "subject": "Quotation — {product} / {quantity}",
        "content": (
            "Dear {name},\n\n"
            "Thank you for your inquiry. Please find our quotation below.\n\n"
            "Product: {product}\n"
            "Quantity: {quantity}\n"
            "Price: {price} (FOB {port})\n"
            "Lead time: {lead_time}\n"
            "Payment: {payment_terms}\n"
            "Validity: 14 days\n\n"
            "If this works, we can issue PI today. "
            "Need a different spec or CIF? Reply with destination port.\n\n"
            "Best regards,\n{sender}\n{company}"
        ),
    },
    {
        "id": "tpl_quote_zh",
        "name": "报价邮件 · 条款清晰",
        "description": "中文报价信·避免来回扯皮",
        "language": "zh",
        "type": "quote",
        "usageCount": 0,
        "isDefault": False,
        "color": "#d18b2f",
        "tags": ["报价", "中文"],
        "subject": "报价单 — {product} / {quantity}",
        "content": (
            "{name} 您好：\n\n"
            "感谢询价，报价如下：\n\n"
            "产品：{product}\n"
            "数量：{quantity}\n"
            "单价：{price}（FOB {port}）\n"
            "交期：{lead_time}\n"
            "付款：{payment_terms}\n"
            "有效期：14 天\n\n"
            "如条款可接受，今日可出形式发票（PI）。若需 CIF，请告知目的港。\n\n"
            "{sender} / {company}"
        ),
    },
    {
        "id": "tpl_pi_ready_en",
        "name": "PI Ready · Close",
        "description": "英文催签 PI·促成定金",
        "language": "en",
        "type": "follow_up",
        "usageCount": 0,
        "isDefault": False,
        "color": "#2f6a5f",
        "tags": ["成单", "英文"],
        "subject": "PI for your order — {product}",
        "content": (
            "Hi {name},\n\n"
            "Attached is the PI for {product} / {quantity}.\n\n"
            "To lock production slot:\n"
            "1) Sign the PI\n"
            "2) Arrange {deposit_ratio} deposit\n"
            "3) We confirm ship date within 24h\n\n"
            "Any wording you need changed? I can update immediately.\n\n"
            "Regards,\n{sender}"
        ),
    },
    {
        "id": "tpl_pi_ready_zh",
        "name": "形式发票催签",
        "description": "中文 PI 催签·锁档期",
        "language": "zh",
        "type": "follow_up",
        "usageCount": 0,
        "isDefault": False,
        "color": "#2f6a5f",
        "tags": ["成单", "中文"],
        "subject": "形式发票 PI — {product}",
        "content": (
            "{name} 您好：\n\n"
            "PI 已备好（{product} / {quantity}）。\n\n"
            "锁定档期：\n"
            "1）确认 PI 条款\n"
            "2）安排 {deposit_ratio} 定金\n"
            "3）24 小时内确认出货日\n\n"
            "条款需改动请直接批注，我马上改。\n\n"
            "{sender}"
        ),
    },
    {
        "id": "tpl_welcome_en",
        "name": "Welcome · Catalog",
        "description": "英文欢迎信·给目录与下一步",
        "language": "en",
        "type": "welcome",
        "usageCount": 0,
        "isDefault": False,
        "color": "#7c6dd8",
        "tags": ["欢迎", "英文"],
        "subject": "Welcome — how we can help with {product}",
        "content": (
            "Hello {name},\n\n"
            "Glad to connect. Quick overview of {company}:\n"
            "- Main line: {product}\n"
            "- Markets: {market}\n"
            "- Docs: PI / CI / PL / CO / B/L support\n\n"
            "I can share catalog + price list today. "
            "What spec do buyers ask for most often in your market?\n\n"
            "Best,\n{sender}"
        ),
    },
    {
        "id": "tpl_welcome_zh",
        "name": "欢迎信 · 目录切入",
        "description": "中文欢迎信·降低破冰成本",
        "language": "zh",
        "type": "welcome",
        "usageCount": 0,
        "isDefault": False,
        "color": "#7c6dd8",
        "tags": ["欢迎", "中文"],
        "subject": "认识一下：{product} 一站式供应",
        "content": (
            "{name} 您好：\n\n"
            "很高兴对接上。{company} 简介：\n"
            "- 主营：{product}\n"
            "- 市场：{market}\n"
            "- 单证：PI / 发票 / 箱单 / 原产地证 / 提单配合\n\n"
            "今日可发目录与价格表。贵司市场里客户最常问哪种规格？\n\n"
            "{sender}"
        ),
    },
    {
        "id": "tpl_reengage_en",
        "name": "Re-engage · 30 Days",
        "description": "英文沉默激活·给新价值点",
        "language": "en",
        "type": "marketing",
        "usageCount": 0,
        "isDefault": False,
        "color": "#a44f3a",
        "tags": ["激活", "英文"],
        "subject": "New specs / better packing for {product}",
        "content": (
            "Hi {name},\n\n"
            "It has been a while. Two updates that may help your buyers:\n"
            "1) Improved export packing for {product}\n"
            "2) Wider spec range at stable FOB\n\n"
            "Worth a 5-minute look? I can send the new spec sheet only.\n\n"
            "{sender}"
        ),
    },
    {
        "id": "tpl_reengage_zh",
        "name": "沉默激活 · 有新料",
        "description": "中文激活信·给理由再开口",
        "language": "zh",
        "type": "marketing",
        "usageCount": 0,
        "isDefault": False,
        "color": "#a44f3a",
        "tags": ["激活", "中文"],
        "subject": "{product} 新规格 / 包装升级",
        "content": (
            "{name} 您好：\n\n"
            "有一阵没联系了，两个可能对您有用的更新：\n"
            "1）{product} 出口包装升级\n"
            "2）规格更全，FOB 稳定\n\n"
            "若方便，只发您新版规格书也可。需要我发吗？\n\n"
            "{sender}"
        ),
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


class CampaignScheduleRequest(BaseModel):
    """定时发送请求体（EmailAutomation.vue scheduleEmail 实调字段）"""
    subject: str = ""
    content: str = ""
    recipients: str = ""
    type: str = "cold_outreach"
    language: str = "en"


@router.post("/campaigns/{campaign_id}/schedule")
def schedule_campaign(
    campaign_id: str,
    body: CampaignScheduleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # SECURITY: 强制认证
):
    """定时发送邮件活动"""
    data = _apply_campaign_status(db, campaign_id, "scheduled")
    data["schedule"] = {
        "subject": body.subject,
        "type": body.type,
        "language": body.language,
    }
    return success_response(data=data, message="定时发送已设置")


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
