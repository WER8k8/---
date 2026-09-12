"""附属统一登录路由 · annex_ticket 签发与校验（§9.3）.

端点：
- POST /api/v1/annex/ticket  —— UJ 已认证用户签发短时票据（前端拼 iframe URL）
- POST /api/v1/annex/redeem   —— 附属后端持桥令牌回调校验，换取身份映射

附属本地密码登录由各附属侧闸门化停用（ANNEX_LOCAL_LOGIN_ENABLED），
身份唯一来源 = UJ 登录 + 票据握手。
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Body, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.annex import ticket_service


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter()


class AnnexTicketBody(BaseModel):
    annex: str = Field(..., description="目标附属：goodjob / trade-ai")


class AnnexRedeemBody(BaseModel):
    annex: str = Field(..., description="发起回调的附属标识")
    ticket: str = Field(..., min_length=20, max_length=4096)


def _extract_bearer(request: Request) -> str:
    header = request.headers.get("authorization") or ""
    if header.lower().startswith("bearer "):
        return header[7:].strip()
    return ""


@router.post("/annex/ticket")
def issue_annex_ticket(
    body: AnnexTicketBody,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """为当前登录用户签发附属短时票据（5 分钟、一次性）。"""
    annex = (body.annex or "").strip()
    if annex not in ticket_service.SUPPORTED_ANNEXES:
        return error_response(400, f"未知附属 {annex!r}")
    try:
        data = ticket_service.issue_annex_ticket(
            user_id=str(current_user.id),
            user_name=current_user.display_name or current_user.username,
            user_email=current_user.email,
            uj_role=current_user.role or "",
            annex=annex,
        )
    except ValueError as exc:
        return error_response(400, str(exc))
    return success_response(data=data, message="票据已签发，5 分钟内一次性有效")


@router.post("/annex/redeem")
def redeem_annex_ticket(
    body: AnnexRedeemBody,
    request: Request,
):
    """附属后端回调：校验票据并返回身份映射（服务间桥令牌认证）。"""
    if not ticket_service.bridge_token_matches(_extract_bearer(request)):
        return error_response(401, "附属回调认证失败（桥令牌无效或未配置）")
    annex = (body.annex or "").strip()
    try:
        data = ticket_service.redeem_annex_ticket(body.ticket, annex=annex)
    except ticket_service.TicketRejected as exc:
        return error_response(401, f"票据校验失败：{exc}")
    return success_response(data=data)
