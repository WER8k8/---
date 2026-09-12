"""创始人运维 / 国密调试（国密 + 微信唯一，浏览器可用，不返回源码）。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.founder_debug_gate import (
    founder_debug_configured,
    founder_gate_mode,
    require_founder_debug,
    require_super_admin,
)
from app.core.gm_crypto import (
    GMCryptoError,
    gmssl_available,
    resolve_sm4_key,
    seal_secret,
    self_test,
    unseal_secret,
)
from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.founder_wechat_service import (
    expected_founder_wechat_provider_id,
    founder_bind_key_display,
    founder_wechat_configured,
    get_user_wechat_provider_id,
    mask_provider_id,
    user_is_founder,
    user_matches_founder_username,
    wechat_oauth_configured,
)
from app.services.production_readiness_service import run_readiness_checks
from app.services.security_event_service import (
    list_security_events,
    protection_summary,
)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(
    prefix="/founder-ops",
    tags=["创始人调试"],
    include_in_schema=False,
)


class SealRequest(BaseModel):
    plaintext: str = Field(..., min_length=1, max_length=4096)


class UnsealRequest(BaseModel):
    ciphertext: str
    sm3: str


@router.get("/preflight")
def founder_preflight(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """超管预检：微信绑定与创始人门禁状态（无需创始人令牌）。"""
    require_super_admin(current_user)
    wechat_id = get_user_wechat_provider_id(db, str(current_user.id))
    founder_cfg = founder_wechat_configured()
    locked = founder_bind_key_display()
    data = {
        "gate_mode": founder_gate_mode(),
        "founder_debug_enabled": founder_debug_configured(),
        "founder_wechat_configured": founder_cfg,
        "founder_wechat_locked": locked,
        "expected_provider_id": expected_founder_wechat_provider_id() or None,
        "username_is_founder": user_matches_founder_username(current_user),
        "oauth_wechat_enabled": wechat_oauth_configured(),
        "wechat_bound": bool(wechat_id),
        "wechat_id_masked": mask_provider_id(wechat_id) if wechat_id else None,
        "wechat_is_founder": user_is_founder(db, current_user) if founder_cfg else None,
        "gmssl_installed": gmssl_available(),
        "steps": [
            "1. 服务器已配置创始人微信号（绑死）",
            "2. 超管登录名与微信号一致，或在本页绑定微信",
            "3. 绑定微信：扫码；开发可用 dev:你的微信号 作为授权 code",
            "4. 重启后端后点「运行诊断」",
        ],
    }
    if locked:
        data["env_line"] = f"FOUNDER_WECHAT_BIND_KEY={locked}"
        data["expected_bind_id"] = f"wechat_{locked}"
    if wechat_id and wechat_id != expected_founder_wechat_provider_id():
        data["wechat_provider_id_for_env"] = wechat_id
        data["env_line_real_openid"] = f"FOUNDER_WECHAT_OPENID={wechat_id}"
    return success_response(data=data)


@router.get("/status")
def founder_ops_status(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """调试快照：环境、国密、就绪分数（无源码）。"""
    require_founder_debug(request, current_user, db)
    report = run_readiness_checks(db)
    return success_response(
        data={
            "gate_mode": founder_gate_mode(),
            "founder_debug_enabled": founder_debug_configured(),
            "wechat_is_founder": user_is_founder(db, current_user),
            "founder_wechat_locked": founder_bind_key_display(),
            "gmssl_installed": gmssl_available(),
            "environment": settings.ENVIRONMENT,
            "debug_swagger": settings.DEBUG,
            "readiness": report.to_dict(),
            "hint": "源码在私有 Git/服务器；日常请用本页诊断，无需 SSH",
        }
    )


@router.get("/crypto/self-test")
def founder_crypto_self_test(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    处理 founder_crypto_self_test 相关业务逻辑。

    :param request: 入参 (Request)。
    :param current_user: 入参 (User)。
    :param db: 入参 (Session)。

    :return: 返回处理结果（或 None）。
    """
    require_founder_debug(request, current_user, db)
    try:
        key = resolve_sm4_key(
            getattr(settings, "GM_SM4_KEY", None),
            settings.SECRET_KEY,
        )
    except GMCryptoError as exc:
        return error_response(500, str(exc))
    result = self_test(
        key,
        sm2_pub=(getattr(settings, "GM_SM2_PUBLIC_KEY", "") or "").strip(),
        sm2_priv=(getattr(settings, "GM_SM2_PRIVATE_KEY", "") or "").strip(),
    )
    return success_response(data=result)


@router.post("/crypto/seal")
def founder_crypto_seal(
    body: SealRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    处理 founder_crypto_seal 相关业务逻辑。

    :param body: 入参 (SealRequest)。
    :param request: 入参 (Request)。
    :param current_user: 入参 (User)。
    :param db: 入参 (Session)。

    :return: 返回处理结果（或 None）。
    """
    require_founder_debug(request, current_user, db)
    try:
        key = resolve_sm4_key(
            getattr(settings, "GM_SM4_KEY", None),
            settings.SECRET_KEY,
        )
        return success_response(data=seal_secret(body.plaintext, key))
    except GMCryptoError as exc:
        return error_response(400, str(exc))


@router.post("/crypto/unseal")
def founder_crypto_unseal(
    body: UnsealRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    处理 founder_crypto_unseal 相关业务逻辑。

    :param body: 入参 (UnsealRequest)。
    :param request: 入参 (Request)。
    :param current_user: 入参 (User)。
    :param db: 入参 (Session)。

    :return: 返回处理结果（或 None）。
    """
    require_founder_debug(request, current_user, db)
    try:
        key = resolve_sm4_key(
            getattr(settings, "GM_SM4_KEY", None),
            settings.SECRET_KEY,
        )
        plain = unseal_secret(
            {"ciphertext": body.ciphertext, "sm3": body.sm3},
            key,
        )
        return success_response(data={"plaintext": plain})
    except GMCryptoError as exc:
        return error_response(400, str(exc))


@router.get("/security-events")
def founder_security_events(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50,
):
    """成果保护：导出/创始人访问留痕（供鉴定截图）。"""
    require_founder_debug(request, current_user, db)
    return success_response(data=list_security_events(db, limit=limit))


@router.get("/protection-summary")
def founder_protection_summary(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """第三方鉴定用一页摘要（无源码、无客户明细）。"""
    require_founder_debug(request, current_user, db)
    return success_response(data=protection_summary(db))
