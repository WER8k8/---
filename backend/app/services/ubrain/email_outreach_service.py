# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
邮件外联服务 —— 状态机 + 幂等 + 追踪

核心功能：
1. 幂等发送：同一 idempotency_key 只发送一次
2. 状态机管理：严格的 draft → queued → sending → sent → ... 流转
3. 打开/点击追踪：1x1 像素 + 链接重定向
4. 序列支持：Drip Campaign（Day 0 / Day 3 / Day 7 自动跟进）
"""

from __future__ import annotations

import hashlib
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.email_outreach import BounceType, EmailOutreach, EmailStatus
from app.services.ubrain.email_send_service import (
    EmailMessage, EmailSendResult, email_service_available, send_email,
)

logger = logging.getLogger(__name__)


# ── 幂等键生成 ──

def _make_idempotency_key(
    to_email: str,
    subject: str,
    tenant_id: Optional[str] = None,
    sequence_id: Optional[str] = None,
    sequence_step: Optional[int] = None,
) -> str:
    """生成幂等键。同一收件人+主题+序列Step的邮件只发一次。"""
    raw = f"{tenant_id or ''}:{to_email}:{subject}:{sequence_id or ''}:{sequence_step or 0}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


# ── 追踪 ID 生成 ──

def _make_tracking_id() -> str:
    """生成追踪 ID（用于像素和链接追踪）。"""
    return secrets.token_urlsafe(16)


# ── 邮件创建 ──

def create_email(
    db: Session,
    *,
    to_email: str,
    subject: str,
    html_body: str,
    from_email: Optional[str] = None,
    from_name: str = "优丁出海",
    reply_to: Optional[str] = None,
    tenant_id: Optional[str] = None,
    user_id: Optional[str] = None,
    sequence_id: Optional[str] = None,
    sequence_step: Optional[int] = None,
    sequence_total_steps: Optional[int] = None,
    tags: Optional[list[str]] = None,
    metadata: Optional[dict] = None,
    scheduled_at: Optional[datetime] = None,
) -> EmailOutreach:
    """创建邮件外联记录（草稿状态）。"""
    idempotency_key = _make_idempotency_key(
        to_email=to_email,
        subject=subject,
        tenant_id=tenant_id,
        sequence_id=sequence_id,
        sequence_step=sequence_step,
    )
    # 检查是否已存在（幂等）
    existing = (
        db.query(EmailOutreach)
        .filter(EmailOutreach.idempotency_key == idempotency_key)
        .first()
    )
    if existing:
        logger.info(f"幂等命中：邮件 {idempotency_key} 已存在，状态={existing.status.value}")
        return existing

    # 插入追踪像素和链接
    tracking_pixel_id = _make_tracking_id()
    html_with_tracking = _inject_tracking_pixel(html_body, tracking_pixel_id)
    email = EmailOutreach(
        idempotency_key=idempotency_key,
        tenant_id=tenant_id,
        user_id=user_id,
        from_email=from_email or settings.RESEND_FROM_EMAIL or settings.FROM_EMAIL or "noreply@youding.pro",
        from_name=from_name,
        to_email=to_email.lower().strip(),
        reply_to=reply_to,
        subject=subject,
        html_body=html_with_tracking,
        text_body=_html_to_text(html_body),
        status=EmailStatus.DRAFT,
        sequence_id=sequence_id,
        sequence_step=sequence_step,
        sequence_total_steps=sequence_total_steps,
        tracking_pixel_id=tracking_pixel_id,
        tags=tags or [],
        metadata=metadata or {},
        scheduled_at=scheduled_at,
    )
    db.add(email)
    db.commit()
    db.refresh(email)
    return email


# ── 邮件发送（带状态机 + 幂等） ──

def _outreach_gate_hold(db: Session, email: EmailOutreach) -> Optional[dict]:
    """首封开发信强制人审 + 邮件链路关卡（总纲 §6.4，既定规则）。

    基于 outreach_metadata 实现，不改表结构（零回归）：
    - review_approved=True → 已人审，放行；
    - 清洗关硬拦截        → gate_blocked（永不发送）；
    - 首封（sequence_step<=1）且需人审 → review_required（留在 DRAFT 等人审）。
    返回 None = 放行；返回 {"error", "meta"} = 扣留（不发送）。
    开关关 / 无租户 / 关卡异常 → 放行（零回归红线）。
    """
    if os.environ.get("PIPELINE_GATES_ENABLED", "0") != "1":
        return None
    tenant_id = str(getattr(email, "tenant_id", "") or "")
    if not tenant_id:
        return None
    meta_db = dict(email.outreach_metadata or {})
    is_first = (getattr(email, "sequence_step", None) or 0) <= 1
    try:
        from app.services.pipeline import chains  # noqa: PLC0415
        report = chains.gate_content(
            db,
            tenant_id=tenant_id,
            title=email.subject or "",
            content=email.text_body or email.html_body or "",
            chain="email",
            meta={"force_human": is_first},  # 首封强制人审（既定规则）
        )
        hold = chains.outreach_hold_decision(
            report,
            is_first=is_first,
            review_approved=bool(meta_db.get("review_approved")),
        )
    except Exception:  # noqa: BLE001 — 关卡故障不得阻断发送流（零回归）
        logger.warning("outreach gate 异常，视为 off（不改变原流程）")
        return None
    if hold is None and report.verdict != "off":
        meta_db["gate"] = report.to_meta()  # 放行也留痕（Evidence）
        email.outreach_metadata = meta_db
    return hold


# ── 人审操作入口（总纲 §6.4：开关启用前的必备通道） ──

def list_pending_review_outreach(
    db: Session,
    tenant_id: Optional[str] = None,
    limit: int = 50,
) -> list:
    """待人审的首封开发信列表（关卡扣留且未审批）。"""
    q = db.query(EmailOutreach).filter(EmailOutreach.status == EmailStatus.DRAFT)
    if tenant_id:
        q = q.filter(EmailOutreach.tenant_id == tenant_id)
    rows = q.order_by(EmailOutreach.created_at.desc()).limit(limit * 3).all()
    pending = []
    for e in rows:
        meta = dict(e.outreach_metadata or {})
        if meta.get("review_required") and not meta.get("review_approved") \
                and not meta.get("review_rejected"):
            pending.append(e)
        if len(pending) >= limit:
            break
    return pending


def approve_outreach_email(
    db: Session,
    email_id: str,
    reviewer_id: Optional[str] = None,
) -> dict:
    """人审批准被扣留的首封开发信（总纲 §6.4 人审入口）。

    仅 DRAFT 且 review_required 扣留中可批准；`gate_blocked` 硬拦截不允许批准。
    批准后由调用方重新走 send_outreach_email（review_approved 通道放行）。
    """
    email = db.query(EmailOutreach).filter(EmailOutreach.id == email_id).first()
    if not email:
        return {"approved": False, "error": "邮件不存在"}
    meta = dict(email.outreach_metadata or {})
    if email.status != EmailStatus.DRAFT:
        return {
            "approved": False,
            "error": f"仅待审草稿可批准（当前状态：{email.status.value}）",
        }
    if meta.get("gate_blocked"):
        return {"approved": False, "error": "清洗关硬拦截（品牌/合规风险），不允许批准"}
    if not meta.get("review_required"):
        return {"approved": False, "error": "该邮件不在待人审状态"}
    meta["review_approved"] = True
    meta["review_approved_at"] = datetime.now(timezone.utc).isoformat()
    if reviewer_id:
        meta["review_approved_by"] = str(reviewer_id)
    email.outreach_metadata = meta
    db.commit()
    return {"approved": True, "id": str(email.id), "status": email.status.value}


def reject_outreach_email(
    db: Session,
    email_id: str,
    reviewer_id: Optional[str] = None,
    reason: str = "",
) -> dict:
    """人审驳回被扣留的首封开发信 → CANCELLED（状态机既有流转）。"""
    email = db.query(EmailOutreach).filter(EmailOutreach.id == email_id).first()
    if not email:
        return {"rejected": False, "error": "邮件不存在"}
    meta = dict(email.outreach_metadata or {})
    if not meta.get("review_required"):
        return {"rejected": False, "error": "该邮件不在待人审状态"}
    if email.status == EmailStatus.DRAFT and email.can_transition_to(EmailStatus.CANCELLED):
        email.transition(EmailStatus.CANCELLED)
    meta["review_rejected"] = True
    meta["review_rejected_at"] = datetime.now(timezone.utc).isoformat()
    if reviewer_id:
        meta["review_rejected_by"] = str(reviewer_id)
    if reason:
        meta["review_rejected_reason"] = reason[:500]
    email.outreach_metadata = meta
    db.commit()
    return {"rejected": True, "id": str(email.id), "status": email.status.value}


async def send_outreach_email(
    db: Session,
    email_id: str,
) -> EmailSendResult:
    """发送单封邮件（幂等 + 状态机）。

    流程：
    1. 加载邮件记录
    2. 检查幂等（已 sent 的直接返回）
    3. draft → queued → sending
    4. 调用底层发送服务
    5. sending → sent / failed
    """
    email = db.query(EmailOutreach).filter(EmailOutreach.id == email_id).first()
    if not email:
        return EmailSendResult(success=False, error="邮件不存在")

    # 幂等检查：已发送成功的不再重发
    if email.status in (EmailStatus.SENT, EmailStatus.DELIVERED, EmailStatus.OPENED, EmailStatus.CLICKED):
        return EmailSendResult(
            success=True,
            message_id=email.provider_message_id,
            provider=email.provider,
        )

    # 检查邮件服务是否可用
    if not email_service_available():
        return EmailSendResult(
            success=False,
            error="邮件服务未配置（需要 RESEND_API_KEY 或 SMTP_SERVER）",
        )

    # ---- 首封开发信强制人审 + 邮件链路关卡（总纲 §6.4；开关默认关，零回归）----
    hold = _outreach_gate_hold(db, email)
    if hold:
        meta = dict(email.outreach_metadata or {})
        meta.update(hold["meta"])
        email.outreach_metadata = meta
        db.commit()
        return EmailSendResult(success=False, error=hold["error"])

    # 状态流转：draft → queued
    if email.status == EmailStatus.DRAFT:
        email.transition(EmailStatus.QUEUED)
        db.commit()

    # 状态流转：queued → sending
    if email.status == EmailStatus.QUEUED:
        email.transition(EmailStatus.SENDING)
        db.commit()

    # 执行发送
    try:
        msg = EmailMessage(
            to=[email.to_email],
            subject=email.subject,
            html_body=email.html_body,
            from_name=email.from_name,
            from_email=email.from_email,
            reply_to=email.reply_to,
        )
        result = await send_email(msg)
        if result.success:
            email.transition(EmailStatus.SENT)
            email.provider = result.provider
            email.provider_message_id = result.message_id
        else:
            email.transition(EmailStatus.FAILED)
            # 记录失败原因到 outreach_metadata
            meta = dict(email.outreach_metadata or {})
            meta["last_error"] = result.error
            meta["retry_count"] = meta.get("retry_count", 0) + 1
            email.outreach_metadata = meta

        db.commit()
        return result

    except Exception as e:
        logger.error(f"邮件发送异常: {e}")
        email.transition(EmailStatus.FAILED)
        meta = dict(email.outreach_metadata or {})
        meta["last_error"] = str(e)
        meta["retry_count"] = meta.get("retry_count", 0) + 1
        email.outreach_metadata = meta
        db.commit()
        return EmailSendResult(success=False, error=str(e))


# ── 追踪回调处理 ──

def record_open(db: Session, tracking_pixel_id: str) -> bool:
    """记录邮件打开（1x1 像素请求时调用）。"""
    email = (
        db.query(EmailOutreach)
        .filter(EmailOutreach.tracking_pixel_id == tracking_pixel_id)
        .first()
    )
    if not email:
        return False

    email.open_count += 1
    if email.status in (EmailStatus.SENT, EmailStatus.DELIVERED):
        email.transition(EmailStatus.OPENED)
    db.commit()
    return True


def record_click(db: Session, tracking_id: str) -> Optional[str]:
    """记录链接点击，返回原始 URL 用于重定向。

    Returns:
        原始 URL，如果找不到则返回 None
    """
    # tracking_id 格式：email_id:link_hash
    # 简化实现：通过 email_id 查找
    # 实际生产环境应该用 Redis 缓存映射
    email = (
        db.query(EmailOutreach)
        .filter(EmailOutreach.tracking_links.contains({"_": tracking_id}))
        .first()
    )
    if not email:
        return None

    email.click_count += 1
    if email.status in (EmailStatus.SENT, EmailStatus.DELIVERED, EmailStatus.OPENED):
        email.transition(EmailStatus.CLICKED)
    db.commit()
    # 从 tracking_links 中找原始 URL
    links = email.tracking_links or {}
    for url, tid in links.items():
        if tid == tracking_id:
            return url
    return None


def record_bounce(
    db: Session,
    email_id: str,
    bounce_type: BounceType,
    reason: str,
) -> bool:
    """记录邮件退回。"""
    email = db.query(EmailOutreach).filter(EmailOutreach.id == email_id).first()
    if not email:
        return False

    email.bounce_type = bounce_type
    email.bounce_reason = reason
    email.transition(EmailStatus.BOUNCED)
    db.commit()
    return True


# ── 序列（Drip Campaign） ──

def schedule_sequence(
    db: Session,
    *,
    to_email: str,
    subject_template: str,
    html_body_template: str,
    steps: list[dict],  # [{"day": 0, "subject": "...", "body": "..."}, ...]
    tenant_id: Optional[str] = None,
    user_id: Optional[str] = None,
    from_name: str = "优丁出海",
    tags: Optional[list[str]] = None,
) -> list[EmailOutreach]:
    """创建邮件序列（Drip Campaign）。

    Args:
        steps: 每步配置 [{"day": 0, "subject": "...", "body": "..."}, ...]

    Returns:
        创建的邮件记录列表
    """
    sequence_id = _make_tracking_id()
    total = len(steps)
    emails: list[EmailOutreach] = []
    for idx, step in enumerate(steps):
        scheduled_at = datetime.now(timezone.utc) + timedelta(days=step.get("day", idx * 3))
        email = create_email(
            db=db,
            to_email=to_email,
            subject=step.get("subject", subject_template),
            html_body=step.get("body", html_body_template),
            tenant_id=tenant_id,
            user_id=user_id,
            from_name=from_name,
            sequence_id=sequence_id,
            sequence_step=idx,
            sequence_total_steps=total,
            tags=tags or [],
            metadata={"sequence_name": step.get("name", f"Step {idx + 1}")},
            scheduled_at=scheduled_at,
        )
        emails.append(email)

    return emails


# ── 内部工具 ──

def _inject_tracking_pixel(html: str, pixel_id: str) -> str:
    """在 HTML 末尾插入 1x1 追踪像素。"""
    pixel_url = f"/api/v1/lead-generation/track-open/{pixel_id}"
    pixel_img = f'<img src="{pixel_url}" width="1" height="1" alt="" style="display:block;" />'
    if "</body>" in html:
        return html.replace("</body>", f"{pixel_img}</body>")
    return html + pixel_img


def _html_to_text(html: str) -> str:
    """简单 HTML 转纯文本（用于邮件备选内容）。"""
    import re
    text = re.sub(r"<[^>]+>", "", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text


class EmailOutreachService:
    """邮件外展与自动跟进服务类。"""

    def __init__(self, db: Session | None = None):
        self.db = db

    async def queue_send(self, outreach_id: str) -> bool:
        """将外展任务加入异步发送队列。"""
        if self.db:
            outreach = self.db.query(EmailOutreach).filter(EmailOutreach.id == outreach_id).first()
            if outreach:
                outreach.status = "queued"
                self.db.commit()
        return True
