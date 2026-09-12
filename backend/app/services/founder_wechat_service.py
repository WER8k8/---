"""创始人微信唯一绑定校验。"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import ThirdPartyLogin, User
from app.services.oauth_binding_service import mask_provider_id


def normalize_founder_wechat_id(raw: str) -> str:
    """与 OAuth 入库格式一致：wechat_{unionid|openid|微信号}。"""
    s = (raw or "").strip()
    if not s:
        return ""
    if s.startswith("wechat_"):
        return s
    return f"wechat_{s}"


def expected_founder_wechat_provider_id() -> str:
    """服务器配置的创始人微信 provider_id（绑死目标）。"""
    for candidate in (
        getattr(settings, "FOUNDER_WECHAT_OPENID", "") or "",
        getattr(settings, "FOUNDER_WECHAT_BIND_KEY", "") or "",
    ):
        normalized = normalize_founder_wechat_id(candidate)
        if normalized:
            return normalized
    return ""


def founder_wechat_configured() -> bool:
    """founder_wechat_configured。
    :return: 返回处理结果。
    """
    return bool(expected_founder_wechat_provider_id())


def get_user_wechat_provider_id(db: Session, user_id: str) -> Optional[str]:
    """get_user_wechat_provider_id。

    参数说明：
    :param db: 参数 db
    :param user_id: 参数 user_id
    :return: 返回处理结果。
    """
    row = (
        db.query(ThirdPartyLogin)
        .filter(
            ThirdPartyLogin.user_id == user_id,
            ThirdPartyLogin.provider == "wechat",
        )
        .first()
    )
    return row.provider_id if row else None


def user_matches_founder_username(user: User) -> bool:
    """user_matches_founder_username。

    参数说明：
    :param user: 参数 user
    :return: 返回处理结果。
    """
    bind_user = (getattr(settings, "FOUNDER_ADMIN_USERNAME", "") or "").strip()
    if not bind_user:
        bind_user = (getattr(settings, "FOUNDER_WECHAT_BIND_KEY", "") or "").strip()
    if not bind_user:
        return False
    return (user.username or "").strip().lower() == bind_user.lower()


def user_is_founder_wechat(db: Session, user_id: str) -> bool:
    """user_is_founder_wechat。

    参数说明：
    :param db: 参数 db
    :param user_id: 参数 user_id
    :return: 返回处理结果。
    """
    expected = expected_founder_wechat_provider_id()
    if not expected:
        return False
    actual = get_user_wechat_provider_id(db, user_id)
    return bool(actual) and actual == expected


def user_is_founder(db: Session, user: User) -> bool:
    """创始人：微信 provider_id 匹配，或超管用户名与 BIND_KEY/ADMIN_USERNAME 一致。"""
    if user_is_founder_wechat(db, str(user.id)):
        return True
    if (user.role or "") not in ("super_admin", "admin"):
        return False
    return user_matches_founder_username(user)


def wechat_oauth_configured() -> bool:
    """wechat_oauth_configured。
    :return: 返回处理结果。
    """
    return bool(
        (settings.WECHAT_OPEN_APP_ID or "").strip()
        and (settings.WECHAT_OPEN_APP_SECRET or "").strip()
    )


def founder_bind_key_display() -> Optional[str]:
    """展示用微信号（去掉 wechat_ 前缀）。"""
    expected = expected_founder_wechat_provider_id()
    if not expected:
        return None
    return expected.replace("wechat_", "", 1)
