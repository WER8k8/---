# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
GDPR Data Deletion Endpoint

POST /api/v1/gdpr/delete-data  -- anonymizes inquiry records,
soft-deletes the user account, and clears analytics data.

Identity verification via email verification code (same flow as
the existing auth email-code system).
"""

import hashlib
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import APIResponse

logger = logging.getLogger("uj-admin.gdpr")

router = APIRouter(tags=["GDPR合规"])


# ── Request / Response schemas ─────────────────────────────────

class GDPRDeleteRequest(BaseModel):
    email: str = Field(..., description="Data subject email address")
    verification_code: str = Field(
        ..., min_length=4, max_length=10,
        description="Email verification code sent to the data subject",
    )


class GDPRDeleteResponse(BaseModel):
    message: str = "Data deletion completed"
    inquiries_anonymized: int = 0
    user_soft_deleted: bool = False
    analytics_cleared: bool = False


# ── Endpoint ───────────────────────────────────────────────────

@router.post("/delete-data")
def gdpr_delete_data(
    body: GDPRDeleteRequest,
    db: Session = Depends(get_db),
):
    """
    GDPR 被遗忘权（Right-to-Erasure）端点。

    处理步骤：
      1. 通过邮箱验证码校验调用者身份（复用 auth 邮件验证码流程）。
      2. 匿名化与该邮箱匹配的全部询盘记录。
      3. 软删除用户账户（若存在）。
      4. 清除与该邮箱关联的分析事件数据。
    """
    from app.models.user import EmailVerification
    email = body.email.strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    raw_email = body.email.strip()
    _gdpr_verify_code(db, raw_email, body.verification_code)
    anonymized_count = 0
    user_deleted = False
    analytics_cleared = False
    inquiries = _gdpr_anonymize_inquiries(db, email, raw_email)
    anonymized_count = len(inquiries)
    user_deleted = _gdpr_soft_delete_user(db, email, raw_email)
    try:
        analytics_cleared = _gdpr_clear_analytics(db, inquiries, email)
    except Exception as exc:
        logger.warning("GDPR analytics cleanup skipped: %s", exc)
        analytics_cleared = True

    db.commit()
    return APIResponse.success(
        data=GDPRDeleteResponse(
            inquiries_anonymized=anonymized_count,
            user_soft_deleted=user_deleted,
            analytics_cleared=analytics_cleared,
        ).model_dump(),
        message="Data deletion completed successfully",
    )


def _gdpr_verify_code(db: Session, raw_email: str, code: str):
    """校验邮箱验证码；无效或过期抛出 403，通过则返回验证记录。

    :param db: 数据库会话。
    :param raw_email: 原始（仅 strip）邮箱字符串。
    :param code: 用户输入的验证码明文。
    :return: 命中的 EmailVerification 记录。
    :raises HTTPException: 验证码无效或过期时抛出 403。
    """
    from app.models.user import EmailVerification
    input_code_hash = hashlib.sha256(code.encode()).hexdigest()
    verification = (
        db.query(EmailVerification)
        .filter(
            EmailVerification.email == raw_email,
            EmailVerification.code == input_code_hash,
            EmailVerification.used == False,  # noqa: E712
            EmailVerification.expires_at > datetime.now(timezone.utc),
        )
        .first()
    )
    if not verification:
        raise HTTPException(
            status_code=403,
            detail="Invalid or expired verification code",
        )
    verification.used = True
    db.flush()
    return verification


def _gdpr_anonymize_inquiries(db: Session, email: str, raw_email: str) -> list:
    """匿名化与邮箱关联的全部询盘记录，返回被匿名化的记录列表。

    :param db: 数据库会话。
    :param email: 小写归一化邮箱。
    :param raw_email: 原始（仅 strip）邮箱字符串。
    :return: 被匿名化的 Inquiry 记录列表。
    :raises HTTPException: 匿名化失败时抛出 500 并回滚事务。
    """
    from app.models.inquiry import Inquiry
    try:
        inquiries = (
            db.query(Inquiry)
            .filter(
                or_(
                    Inquiry.email == email,
                    Inquiry.email == raw_email,
                )
            )
            .all()
        )
        for inq in inquiries:
            inq.name = "已删除用户"
            inq.email = None
            inq.phone = "已删除"
            inq.message = "已删除"
            inq.wechat = None
            inq.product = None
            inq.source_utm = None
            inq.session_id = None
        db.flush()
        logger.info(
            "GDPR: anonymized %d inquiry records for %s",
            len(inquiries), email,
        )
        return inquiries
    except Exception as exc:
        logger.error("GDPR inquiry anonymization failed: %s", exc)
        db.rollback()
        raise HTTPException(
            status_code=500, detail="Inquiry anonymization failed",
        )


def _gdpr_soft_delete_user(db: Session, email: str, raw_email: str) -> bool:
    """软删除与该邮箱关联的用户账户，返回是否执行了删除。

    :param db: 数据库会话。
    :param email: 小写归一化邮箱。
    :param raw_email: 原始（仅 strip）邮箱字符串。
    :return: 是否成功软删除用户账户。
    :raises HTTPException: 删除失败时抛出 500 并回滚事务。
    """
    from app.models.user import User
    try:
        user = db.query(User).filter(
            or_(
                User.email == email,
                User.email == raw_email,
            )
        ).first()
        if not user:
            return False
        user.is_active = False
        user.username = f"deleted_{user.id[:8]}"
        user.email = f"deleted_{user.id[:8]}@anonymized.local"
        user.display_name = "已删除用户"
        user.hashed_password = "DELETED"
        db.flush()
        logger.info("GDPR: soft-deleted user %s", user.id)
        return True
    except Exception as exc:
        logger.error("GDPR user deletion failed: %s", exc)
        db.rollback()
        raise HTTPException(
            status_code=500, detail="User deletion failed",
        )


def _gdpr_clear_analytics(db: Session, inquiries: list, email: str) -> bool:
    """清除与邮箱相关的分析事件，返回是否完成清理。

    :param db: 数据库会话。
    :param inquiries: 已匿名化的询盘记录列表（用于提取 session_id）。
    :param email: 小写归一化邮箱。
    :return: 是否完成分析数据清理。
    """
    from app.models.site_analytics import SiteAnalyticsEvent
    email_session_ids = [
        inq.session_id for inq in inquiries if inq.session_id
    ]
    cleared = 0
    if email_session_ids:
        events = (
            db.query(SiteAnalyticsEvent)
            .filter(
                SiteAnalyticsEvent.session_id.in_(email_session_ids),
            )
            .all()
        )
        for ev in events:
            ev.meta_json = "{}"
            cleared += 1
    if not cleared:
        events = (
            db.query(SiteAnalyticsEvent)
            .filter(
                SiteAnalyticsEvent.meta_json.contains(email),
            )
            .all()
        )
        for ev in events:
            ev.meta_json = "{}"
            cleared += 1
    logger.info(
        "GDPR: cleared %d analytics events for %s", cleared, email,
    )
    return True
