# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Lane I · 社媒评论/私信自动谈单 API。"""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends, Header, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.no_fake_delivery import NotConfiguredError
from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.core.tenant_access import (
    deny_unless_module,
    is_platform_admin,
)
from app.db.session import get_db
from app.models.user import User
from app.services import social_interaction_service as svc


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/social-interactions", tags=["社媒自动谈单"])


class DouyinWebhookBody(BaseModel):
    tenant_id: str = Field(..., min_length=1, max_length=36)
    platform_post_id: str = Field(..., min_length=1, max_length=128)
    platform_comment_id: str = Field(..., min_length=1, max_length=128)
    content: str = Field(..., min_length=1, max_length=4000)
    author_name: str = Field(default="抖音用户", max_length=120)
    author_platform_id: str | None = Field(default=None, max_length=128)
    interaction_type: str = Field(default="comment", pattern="^(comment|dm)$")
    phone: str | None = Field(default=None, max_length=20)


class ApproveBody(BaseModel):
    final_reply: str | None = Field(default=None, max_length=4000)
    auto_send_via_aitoearn: bool = Field(
        default=False,
        description="批准后经 AiToEarn 真发；无 Key 或未分配槽位则 503",
    )


class MarkSentBody(BaseModel):
    platform_receipt_id: str = Field(..., min_length=1, max_length=200)
    platform_message_id: str | None = Field(default=None, max_length=200)


class MarkFailedBody(BaseModel):
    error_code: str = Field(..., min_length=1, max_length=64)
    error_message: str = Field(..., min_length=1, max_length=500)


def _verify_webhook(secret_header: str | None) -> bool:
    """执行 verify_webhook 相关逻辑处理。
    
    :param secret_header: 参数 secret_header
    :return: 返回处理结果。
    """
    expected = os.getenv("SOCIAL_INTERACTION_WEBHOOK_SECRET", "").strip()
    if not expected:
        expected = os.getenv("INQUIRY_WEBHOOK_SECRET", "").strip()
    if not expected:
        return True
    return (secret_header or "").strip() == expected


def _resolve_tenant_id(db: Session, user: User, tenant_id: str | None) -> str | None:
    """执行 resolve_tenant_id 相关逻辑处理。
    
    :param db: 数据库会话
    :param user: 用户对象
    :param tenant_id: 租户ID
    :return: 返回处理结果。
    """
    if is_platform_admin(user):
        return tenant_id
    from app.services.tenant_scenario_service import resolve_tenant_id_for_user
    return resolve_tenant_id_for_user(db, user)


def _guard_inquiries_read(user: User):
    """执行 guard_inquiries_read 相关逻辑处理。
    
    :param user: 用户对象
    :return: 返回处理结果。
    """
    if (user.role or "") == "user":
        return None
    return deny_unless_module(user, "inquiries", "read")


def _guard_inquiries_write(user: User):
    """执行 guard_inquiries_write 相关逻辑处理。
    
    :param user: 用户对象
    :return: 返回处理结果。
    """
    if (user.role or "") == "user":
        return None
    return deny_unless_module(user, "inquiries", "update")


@router.get("/worker/config")
def worker_config(current_user: User = Depends(get_current_user)):
    """Worker 接入手册（不含密钥明文）。"""
    denied = deny_unless_module(current_user, "inquiries", "read")
    if denied:
        return denied
    import json
    import os
    from app.core.config import settings
    secret = (
        os.getenv("SOCIAL_INTERACTION_WEBHOOK_SECRET", "").strip()
        or os.getenv("INQUIRY_WEBHOOK_SECRET", "").strip()
    )
    api_base = os.getenv("PUBLIC_API_BASE", settings.SITE_URL.rstrip("/")).rstrip("/")
    webhook_url = f"{api_base}/api/v1/social-interactions/webhook/douyin"
    sample = {
        "tenant_id": "<tenant-uuid>",
        "platform_post_id": "7123456789",
        "platform_comment_id": "cmt_unique_001",
        "content": "岩棉板多少钱？",
        "author_name": "抖音用户",
    }
    return success_response(
        data={
            "webhook_url": webhook_url,
            "secret_configured": bool(secret),
            "secret_headers": ["X-Social-Webhook-Secret", "X-Inquiry-Webhook-Secret"],
            "batch_script": "python scripts/run-douyin-comment-worker.py --batch-file comments.json",
            "ops_sync_url": f"{api_base}/api/v1/ops/jobs/douyin-comment-sync",
            "ops_pull_url": f"{api_base}/api/v1/ops/jobs/douyin-comment-pull?tenant_id=<tenant-uuid>&source=auto",
            "client_pull_url": f"{api_base}/api/v1/client/douyin-comments/pull",
            "inbox_dir_env": "DOUYIN_COMMENT_INBOX_DIR",
            "aitoearn_comment_path_env": "AITOEARN_COMMENT_LIST_PATH",
            "sample_item": sample,
            "sample_json": json.dumps([sample], ensure_ascii=False),
        }
    )


@router.get("/summary")
def interaction_summary(
    tenant_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 GET /summary 请求，interaction相关资源。
    
    :param tenant_id: 租户ID
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    denied = _guard_inquiries_read(current_user)
    if denied:
        return denied
    tid = _resolve_tenant_id(db, current_user, tenant_id)
    return success_response(data=svc.get_summary(db, tenant_id=tid))


@router.get("/")
def list_interactions(
    platform: str | None = Query(None),
    status: str | None = Query(None),
    tenant_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 GET / 请求，列出相关资源。
    
    :param platform: 参数 platform
    :param status: 状态
    :param tenant_id: 租户ID
    :param limit: 返回条数上限
    :param skip: 参数 skip
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    denied = _guard_inquiries_read(current_user)
    if denied:
        return denied
    tid = _resolve_tenant_id(db, current_user, tenant_id)
    items = svc.list_interactions(
        db, tenant_id=tid, platform=platform, status=status, limit=limit, skip=skip
    )
    return success_response(data={"items": items, "total": len(items), "limit": limit, "skip": skip})


@router.get("/negotiations")
def list_negotiations(
    status: str | None = Query(None, description="pending|in_progress|completed|failed"),
    tenant_id: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """AutoNegotiator 兼容列表 — 数据来自 social_interactions 表。"""
    denied = _guard_inquiries_read(current_user)
    if denied:
        return denied
    tid = _resolve_tenant_id(db, current_user, tenant_id)
    data = svc.list_negotiations_view(db, tenant_id=tid, ui_status=status, limit=limit)
    return success_response(data=data)


@router.post("/webhook/douyin")
def douyin_comment_webhook(
    body: DouyinWebhookBody,
    db: Session = Depends(get_db),
    x_inquiry_webhook_secret: str | None = Header(None, alias="X-Inquiry-Webhook-Secret"),
    x_social_webhook_secret: str | None = Header(None, alias="X-Social-Webhook-Secret"),
):
    """抖音评论/私信 Worker 回调 — 入库并生成谈单草稿。"""
    secret = x_social_webhook_secret or x_inquiry_webhook_secret
    if not _verify_webhook(secret):
        return error_response(403, "webhook 密钥无效")
    try:
        row = svc.ingest_douyin_interaction(
            db,
            tenant_id=body.tenant_id,
            platform_post_id=body.platform_post_id,
            platform_comment_id=body.platform_comment_id,
            content=body.content,
            author_name=body.author_name,
            author_platform_id=body.author_platform_id,
            interaction_type=body.interaction_type,
            phone=body.phone,
        )
    except ValueError as exc:
        return error_response(400, str(exc))
    return success_response(data=row, message="互动已入库")


@router.post("/{interaction_id}/approve")
def approve_interaction(
    interaction_id: str,
    body: ApproveBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 POST /{interaction_id}/approve 请求，审批相关资源。
    
    :param interaction_id: 参数 interaction_id
    :param body: 请求体
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    :raises: KeyError 等异常在错误时抛出。
    """
    denied = _guard_inquiries_write(current_user)
    if denied:
        return denied
    try:
        if body.auto_send_via_aitoearn:
            from app.models.social_interaction import SocialInteraction
            from app.models.tenant import Tenant
            from app.services.aitoearn_engage_send_service import approve_and_send_via_aitoearn_sync
            row0 = db.query(SocialInteraction).filter(SocialInteraction.id == interaction_id).first()
            if not row0:
                raise KeyError("interaction_not_found")
            tenant = db.query(Tenant).filter(Tenant.id == str(row0.tenant_id)).first()
            if not tenant:
                return error_response(400, "互动记录缺少租户，无法 AiToEarn 发送")
            row = approve_and_send_via_aitoearn_sync(
                db,
                interaction_id=interaction_id,
                tenant=tenant,
                final_reply=body.final_reply,
            )
            return success_response(data=row, message="已通过 AiToEarn 发送并记录回执")
        row = svc.approve_draft(db, interaction_id, final_reply=body.final_reply)
    except KeyError:
        return error_response(404, "互动记录不存在")
    except ValueError as exc:
        return error_response(400, str(exc))
    return success_response(data=row, message="草稿已批准，请在平台发送后提交回执")


@router.post("/{interaction_id}/mark-sent")
def mark_interaction_sent(
    interaction_id: str,
    body: MarkSentBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 POST /{interaction_id}/mark-sent 请求，标记相关资源。
    
    :param interaction_id: 参数 interaction_id
    :param body: 请求体
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    denied = _guard_inquiries_write(current_user)
    if denied:
        return denied
    try:
        row = svc.mark_sent(
            db,
            interaction_id,
            platform_receipt_id=body.platform_receipt_id,
            platform_message_id=body.platform_message_id,
        )
    except KeyError:
        return error_response(404, "互动记录不存在")
    except ValueError as exc:
        return error_response(400, str(exc))
    except NotConfiguredError as exc:
        return error_response(503, f"{exc.code}: {exc}")
    return success_response(data=row, message="已记录平台发送回执")


@router.post("/{interaction_id}/mark-failed")
def mark_interaction_failed(
    interaction_id: str,
    body: MarkFailedBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 POST /{interaction_id}/mark-failed 请求，标记相关资源。
    
    :param interaction_id: 参数 interaction_id
    :param body: 请求体
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    denied = _guard_inquiries_write(current_user)
    if denied:
        return denied
    try:
        row = svc.mark_failed(
            db,
            interaction_id,
            error_code=body.error_code,
            error_message=body.error_message,
        )
    except KeyError:
        return error_response(404, "互动记录不存在")
    except ValueError as exc:
        return error_response(400, str(exc))
    return success_response(data=row, message="已标记发送失败")


@router.post("/{interaction_id}/regenerate-draft")
def regenerate_draft(
    interaction_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 POST /{interaction_id}/regenerate-draft 请求，regenerate相关资源。
    
    :param interaction_id: 参数 interaction_id
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    denied = _guard_inquiries_write(current_user)
    if denied:
        return denied
    try:
        row = svc.regenerate_draft(db, interaction_id)
    except KeyError:
        return error_response(404, "互动记录不存在")
    except ValueError as exc:
        return error_response(400, str(exc))
    return success_response(data=row, message="草稿已重新生成")
