"""AiToEarn 能力 Hub API — 对齐 Create/Publish/Engage/Analytics。"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.core.tenant_access import deny_unless_module
from app.db.session import get_db
from app.models.tenant import Tenant
from app.models.user import User
from app.services.aitoearn_hub_service import (
    build_aitoearn_capabilities,
    engage_list_comments,
    engage_reply_via_aitoearn,
)
from app.services.aitoearn_publish_adapter import _safe_asyncio_run
from app.services.tenant_scenario_service import resolve_tenant_id_for_user


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/aitoearn/hub", tags=["AiToEarn Hub"])


def _tenant_or_403(db: Session, user: User) -> tuple[Tenant | None, Any]:
    """
    处理 _tenant_or_403 相关业务逻辑。

    :param db: 入参 (Session)。
    :param user: 入参 (User)。

    :return: 返回 tuple[Tenant | None, Any] 类型的结果。
    """
    tid = resolve_tenant_id_for_user(db, user)
    if not tid:
        return None, error_response(403, "未关联租户")
    tenant = db.query(Tenant).filter(Tenant.id == tid).first()
    if not tenant:
        return None, error_response(404, "租户不存在")
    return tenant, None


class EngageReplyBody(BaseModel):
    comment_id: str = Field(..., min_length=1, max_length=128)
    content: str = Field(..., min_length=1, max_length=4000)
    post_id: str = Field(default="", max_length=128)
    account_id: str | None = Field(default=None, max_length=64)


class EngageListBody(BaseModel):
    post_id: str = Field(..., min_length=1, max_length=128)
    platform: str = Field(default="douyin", max_length=32)
    account_id: str | None = Field(default=None, max_length=64)


@router.get("/capabilities")
async def aitoearn_capabilities(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    处理 aitoearn_capabilities 相关业务逻辑。

    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    denied = deny_unless_module(current_user, "content", "read")
    if denied:
        return denied
    tenant, err = _tenant_or_403(db, current_user)
    if err:
        if current_user.role in ("admin", "super_admin"):
            return success_response(data=build_aitoearn_capabilities(tenant=None))
        return err
    return success_response(data=build_aitoearn_capabilities(tenant=tenant))


@router.post("/engage/reply")
async def aitoearn_engage_reply(
    body: EngageReplyBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    处理 aitoearn_engage_reply 相关业务逻辑。

    :param body: 入参 (EngageReplyBody)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    denied = deny_unless_module(current_user, "inquiries", "update")
    if denied:
        return denied
    tenant, err = _tenant_or_403(db, current_user)
    if err:
        return err
    result = await engage_reply_via_aitoearn(
        tenant=tenant,
        account_id=body.account_id,
        comment_id=body.comment_id,
        content=body.content,
        post_id=body.post_id,
    )
    if not result.get("ok"):
        return error_response(503, result.get("message") or "发送失败")
    return success_response(data=result, message="评论已通过 AiToEarn 回复")


@router.post("/engage/comments")
async def aitoearn_engage_comments(
    body: EngageListBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    处理 aitoearn_engage_comments 相关业务逻辑。

    :param body: 入参 (EngageListBody)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    denied = deny_unless_module(current_user, "inquiries", "read")
    if denied:
        return denied
    tenant, err = _tenant_or_403(db, current_user)
    if err:
        return err
    items = await engage_list_comments(
        tenant=tenant,
        post_id=body.post_id,
        platform=body.platform,
        account_id=body.account_id,
    )
    return success_response(
        data={
            "items": items,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
    )
