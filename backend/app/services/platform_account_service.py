# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""租户级平台账号：列表、绑定 upsert、媒体发布解析。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.content import Platform, PlatformAccount, PlatformConfig
from app.models.user import User
from app.services.platform_credential_guide import (
    CREDENTIAL_STORAGE,
    all_credential_fields,
    guide_for_platform,
    missing_from,
    required_platform_key,
)
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


# ===========================================================================
# 凭证落地：读（合并三处存放位）/ 写（token_data + cookie_data + configs）/ 脱敏状态
# 铁律：任何出参只给字段名与掩码，绝不回传密钥原文（用户级规则：输出必脱敏）。
# ===========================================================================

# payload 里允许直接出现的凭证键（其余业务字段由调用方自己处理）
_CREDENTIAL_KEYS = frozenset(
    {
        "cookie",
        "cookie_data",
        "token_data",
        "credentials",
        "configs",
        "appid",
        "appsecret",
        "password",
        "access_token",
        "x_zse_93",
        "x_zse_96",
        "x_zse_99",
        "column_id",
        "tags",
    }
)

# 明确不属于「凭证」的配置键（脱敏状态里不展示，避免把运营参数当密钥）
_NON_SECRET_CONFIG_KEYS = frozenset(
    {
        "column_id",
        "tags",
        "browser_profile_id",
        "egress_endpoint_id",
    }
)


def _mask(value: Any) -> str:
    """密钥掩码：只露首尾各 2 位，中间以 * 代替；短值整体打码。"""
    text = str(value or "")
    if len(text) <= 4:
        return "*" * max(len(text), 1)
    return f"{text[:2]}{'*' * 6}{text[-2:]}"


def collect_credentials(
    db: Session,
    account: PlatformAccount,
    platform: Platform | None = None,
) -> dict[str, str]:
    """汇总某账号可用凭证：token_data(JSON) + cookie_data + PlatformConfig。

    取值优先级：PlatformConfig < cookie_data < token_data（token_data 是结构化真源）。
    返回 {字段名: 原值}，仅供服务端内部使用，禁止直接序列化给前端。
    """
    out: dict[str, str] = {}
    try:
        rows = db.query(PlatformConfig).filter_by(account_id=account.id).all()
        for row in rows:
            if row.config_value:
                out[str(row.config_key)] = str(row.config_value)
    except Exception:  # noqa: BLE001 — 配置表读取失败不阻断，退回列上的凭证
        pass

    cookie = (account.cookie_data or "").strip()
    if cookie:
        out["cookie"] = cookie
        plat_name = getattr(platform, "name", None)
        req_key = required_platform_key(plat_name)
        for field in all_credential_fields(req_key):
            if CREDENTIAL_STORAGE.get(field) == "cookie":
                out.setdefault(field, cookie)

    token_data = account.token_data if isinstance(account.token_data, dict) else {}
    for key, value in token_data.items():
        if value is None or str(value) == "":
            continue
        out[str(key)] = str(value)
    return out


def apply_credentials(
    db: Session,
    *,
    account: PlatformAccount,
    platform: Platform,
    payload: dict[str, Any],
) -> int:
    """把 payload 里的凭证写进三处存放位（不 commit，由调用方管事务）。

    支持三种写法，前端与 curl 都能用：
      · {"cookie": "..."} / {"cookie_data": "..."}      → cookie_data（并镜像到该平台的 *_cookie 字段）
      · {"token_data": {...}} / {"credentials": {...}}  → token_data（按键合并，不整体覆盖）
      · {"configs": {...}} 或平铺 appid/appsecret/...    → platform_configs 键值
    返回写入的凭证字段数（0 表示本次没带凭证，保持原值不动）。
    """
    written = 0
    token_data = dict(account.token_data or {}) if isinstance(account.token_data, dict) else {}
    configs: dict[str, str] = {}
    req_key = required_platform_key(getattr(platform, "name", None))
    guide_fields = set(all_credential_fields(req_key))

    raw_token = payload.get("token_data")
    if raw_token is None:
        raw_token = payload.get("credentials")
    if isinstance(raw_token, dict):
        for key, value in raw_token.items():
            if value is None or str(value).strip() == "":
                continue
            token_data[str(key)] = str(value)
            written += 1

    cookie_in = payload.get("cookie")
    if cookie_in is None:
        cookie_in = payload.get("cookie_data")
    if cookie_in is not None and str(cookie_in).strip():
        cookie = str(cookie_in).strip()
        account.cookie_data = cookie
        mirrored = False
        for field in all_credential_fields(req_key):
            if CREDENTIAL_STORAGE.get(field) == "cookie":
                token_data[field] = cookie
                mirrored = True
        if not mirrored:
            token_data.setdefault("cookie", cookie)
        written += 1

    raw_configs = payload.get("configs")
    if isinstance(raw_configs, dict):
        for key, value in raw_configs.items():
            if value is None or str(value).strip() == "":
                continue
            configs[str(key)] = str(value)
    for key, value in payload.items():
        if key in {"token_data", "credentials", "cookie", "cookie_data", "configs"}:
            continue
        if value is None or str(value).strip() == "":
            continue
        text = str(value).strip()
        # 指引登记的凭证字段（如 alibaba_member_id）平铺传入时按字段路由，
        # cookie 类同时写 cookie_data，其余进 token_data
        if key in guide_fields:
            if CREDENTIAL_STORAGE.get(key) == "cookie":
                account.cookie_data = text
            token_data[key] = text
            written += 1
        elif key in _CREDENTIAL_KEYS:
            if CREDENTIAL_STORAGE.get(key) == "cookie":
                account.cookie_data = text
                token_data[key] = text
            else:
                configs[key] = text
            written += 1

    if token_data:
        account.token_data = token_data

    # 先落库再查：autoflush=False 的会话里，未 flush 的新行查不到，会重复插同键配置
    db.flush()
    for key, value in configs.items():
        row = (
            db.query(PlatformConfig)
            .filter_by(account_id=account.id, config_key=key)
            .first()
        )
        if row:
            row.config_value = value
        else:
            db.add(
                PlatformConfig(
                    platform_id=str(platform.id),
                    account_id=account.id,
                    config_key=key,
                    config_value=value,
                )
            )
    return written


def credential_status(
    db: Session,
    account: PlatformAccount,
    platform: Platform | None = None,
) -> dict[str, Any]:
    """凭证状态（脱敏）。给列表/详情页判断「这个号到底能不能真发」。

    - has_credentials：是否存有任何非运营参数类凭证
    - credential_fields：已有字段名 + 掩码值（绝不回原文）
    - missing_fields：按必填组算出的缺项（空即具备真发前置）
    - publish_ready：字段级门禁通过与否；无门禁的平台以 has_credentials 判定
    """
    merged = collect_credentials(db, account, platform)
    secret_keys = [
        key
        for key in merged
        if key not in _NON_SECRET_CONFIG_KEYS and not key.startswith("nurture_")
    ]
    req_key = required_platform_key(getattr(platform, "name", None))
    missing = missing_from(merged, req_key) if req_key else []
    guide = guide_for_platform(getattr(platform, "name", None))
    return {
        "has_credentials": bool(secret_keys),
        "credential_fields": [
            {"name": key, "masked": _mask(merged.get(key))} for key in sorted(secret_keys)
        ],
        "missing_fields": missing,
        "publish_ready": (not missing) if req_key else bool(secret_keys),
        "guide_key": (guide or {}).get("key") if guide else None,
        "credential_source": (guide or {}).get("storage") if guide else None,
    }
