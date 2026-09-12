"""租户级平台账号：列表、绑定 upsert、媒体发布解析。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.content import Platform, PlatformAccount, PlatformConfig
from app.models.user import User
from app.services.tenant_scenario_service import resolve_tenant_id_for_user


def resolve_tenant_scope(db: Session, user: User) -> str | None:
    """resolve_tenant_scope。

    参数说明：
    :param db: 参数 db
    :param user: 参数 user
    :return: 返回处理结果。
    """
    return resolve_tenant_id_for_user(db, user)


def list_active_accounts(
    db: Session,
    *,
    tenant_id: str | None,
) -> list[PlatformAccount]:
    """list_active_accounts。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :return: 返回处理结果。
    """
    q = db.query(PlatformAccount).filter(PlatformAccount.is_active.is_(True))
    if tenant_id:
        q = q.filter(PlatformAccount.tenant_id == tenant_id)
    return q.order_by(PlatformAccount.updated_at.desc()).all()


def list_platform_accounts(db: Session, tenant_id: str | None = None) -> list[PlatformAccount]:
    """兼容导出：list_active_accounts 的通用调用别名。"""
    return list_active_accounts(db, tenant_id=tenant_id)


def find_tenant_platform_account(
    db: Session,
    *,
    tenant_id: str | None,
    platform_id: str,
    prefer_logged_in: bool = True,
) -> PlatformAccount | None:
    """find_tenant_platform_account。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param platform_id: 参数 platform_id
    :param prefer_logged_in: 参数 prefer_logged_in
    :return: 返回处理结果。
    """
    q = db.query(PlatformAccount).filter(
        PlatformAccount.platform_id == platform_id,
        PlatformAccount.is_active.is_(True),
    )
    if tenant_id:
        q = q.filter(PlatformAccount.tenant_id == tenant_id)
    if prefer_logged_in:
        logged = q.filter(PlatformAccount.login_status == "logged_in").first()
        if logged:
            return logged
    return q.first()


def account_configs(db: Session, account: PlatformAccount) -> dict[str, str]:
    """account_configs。

    参数说明：
    :param db: 参数 db
    :param account: 参数 account
    :return: 返回处理结果。
    """
    rows = db.query(PlatformConfig).filter_by(account_id=account.id).all()
    return {row.config_key: row.config_value for row in rows}


def upsert_bound_account(
    db: Session,
    *,
    tenant_id: str | None,
    platform: Platform,
    payload: dict[str, Any],
) -> tuple[PlatformAccount, bool]:
    """绑定或更新平台账号；优先升级该租户的 stub。返回 (account, created)."""
    platform_id = str(platform.id)
    account_name = payload.get("account_name") or payload.get("username", "")
    username = payload.get("username") or account_name
    existing = find_tenant_platform_account(
        db, tenant_id=tenant_id, platform_id=platform_id, prefer_logged_in=False
    )
    if not existing and not tenant_id and (username or account_name):
        existing = (
            db.query(PlatformAccount)
            .filter_by(platform_id=platform_id, is_active=True)
            .filter(
                or_(
                    PlatformAccount.username == username,
                    PlatformAccount.account_name == account_name,
                )
            )
            .first()
        )
    created = existing is None
    if existing:
        acc = existing
        acc.username = username
        acc.account_name = account_name or username or platform.name
        acc.cookie_data = payload.get("cookie") or acc.cookie_data
        if payload.get("token_data") is not None:
            acc.token_data = payload.get("token_data")
        has_session = bool(
            payload.get("cookie")
            or payload.get("token_data")
            or payload.get("appid")
            or payload.get("password")
        )
        acc.login_status = "logged_in" if has_session else "bound"
        if has_session:
            acc.last_login_at = datetime.now(timezone.utc)
        if tenant_id and not acc.tenant_id:
            acc.tenant_id = tenant_id
        db.query(PlatformConfig).filter_by(account_id=acc.id).delete()
    else:
        has_session = bool(
            payload.get("cookie")
            or payload.get("token_data")
            or payload.get("appid")
            or payload.get("password")
        )
        acc = PlatformAccount(
            tenant_id=tenant_id,
            platform_id=platform_id,
            account_name=account_name or username or platform.name,
            username=username,
            email=payload.get("email"),
            cookie_data=payload.get("cookie"),
            token_data=payload.get("token_data"),
            login_status="logged_in" if has_session else "bound",
            last_login_at=datetime.now(timezone.utc) if has_session else None,
        )
        db.add(acc)
        db.flush()

    configs = dict(payload.get("configs", {}) or {})
    if payload.get("password"):
        configs["password"] = str(payload["password"])
    if payload.get("appid"):
        configs["appid"] = str(payload["appid"])
    if payload.get("appsecret"):
        configs["appsecret"] = str(payload["appsecret"])

    nurture = payload.get("nurture") or {}
    for key, val in nurture.items():
        if val is not None and val != "":
            configs[f"nurture_{key}"] = str(val)
    if payload.get("browser_profile_id"):
        configs["browser_profile_id"] = str(payload["browser_profile_id"])
    if payload.get("egress_endpoint_id"):
        configs["egress_endpoint_id"] = str(payload["egress_endpoint_id"])

    for key, value in configs.items():
        if value is not None and value != "":
            db.add(
                PlatformConfig(
                    platform_id=platform_id,
                    account_id=acc.id,
                    config_key=key,
                    config_value=str(value),
                )
            )

    return acc, created


def serialize_account_for_frontend(
    db: Session,
    acc: PlatformAccount,
) -> dict[str, Any]:
    """serialize_account_for_frontend。

    参数说明：
    :param db: 参数 db
    :param acc: 参数 acc
    :return: 返回处理结果。
    """
    configs = account_configs(db, acc)
    nurture = {
        "warmup_days": int(configs.get("nurture_warmup_days") or 14),
        "daily_posts": int(configs.get("nurture_daily_posts") or 1),
        "daily_likes": int(configs.get("nurture_daily_likes") or 5),
        "daily_comments": int(configs.get("nurture_daily_comments") or 2),
        "status": configs.get("nurture_status") or "warming",
    }
    return {
        "id": acc.id,
        "platform": acc.platform_id,
        "tenant_id": acc.tenant_id,
        "username": acc.username or acc.account_name,
        "status": "active" if acc.login_status == "logged_in" else "offline",
        "login_status": acc.login_status,
        "lastLogin": acc.last_login_at.isoformat() if acc.last_login_at else "",
        "cookie": acc.cookie_data or "",
        "appid": configs.get("appid", ""),
        "browser_profile_id": configs.get("browser_profile_id", ""),
        "egress_endpoint_id": configs.get("egress_endpoint_id", ""),
        "nurture": nurture,
    }


def resolve_platform_for_publish(
    db: Session,
    platform_ref: str,
) -> Platform | None:
    """platform_ref 可为 Platform UUID 或 PublishService 键名（youtube 等）。"""
    ref = (platform_ref or "").strip()
    if not ref:
        return None
    plat = db.query(Platform).filter(Platform.id == ref).first()
    if plat:
        return plat
    return db.query(Platform).filter(
        or_(
            Platform.name.ilike(ref),
            Platform.platform_type == ref,
        )
    ).first()
