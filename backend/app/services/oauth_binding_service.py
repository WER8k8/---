"""第三方账号绑定（已登录用户）。"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.user import ThirdPartyLogin, User
from app.services.oauth_login import SUPPORTED_OAUTH_PROVIDERS, resolve_oauth_identity


def mask_provider_id(provider_id: str) -> str:
    """mask_provider_id。

    参数说明：
    :param provider_id: 参数 provider_id
    :return: 返回处理结果。
    """
    if len(provider_id) <= 8:
        return "***"
    return f"{provider_id[:4]}***{provider_id[-4:]}"


def list_user_bindings(db: Session, user_id: str) -> list[dict]:
    """list_user_bindings。

    参数说明：
    :param db: 参数 db
    :param user_id: 参数 user_id
    :return: 返回处理结果。
    """
    rows = (
        db.query(ThirdPartyLogin)
        .filter(ThirdPartyLogin.user_id == user_id)
        .order_by(ThirdPartyLogin.created_at.desc())
        .all()
    )
    return [
        {
            "provider": r.provider,
            "provider_id_masked": mask_provider_id(r.provider_id),
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


def bind_oauth_account(db: Session, user: User, provider: str, code: str) -> ThirdPartyLogin:
    """bind_oauth_account。

    参数说明：
    :param db: 参数 db
    :param user: 参数 user
    :param provider: 参数 provider
    :param code: 参数 code
    :return: 返回处理结果。
    """
    p = provider.lower()
    if p not in SUPPORTED_OAUTH_PROVIDERS:
        raise ValueError("unsupported_provider")

    provider_id, _ = resolve_oauth_identity(p, code)
    conflict = (
        db.query(ThirdPartyLogin)
        .filter(
            ThirdPartyLogin.provider == p,
            ThirdPartyLogin.provider_id == provider_id,
        )
        .first()
    )
    if conflict and conflict.user_id != user.id:
        raise ValueError("already_bound_other")

    if conflict and conflict.user_id == user.id:
        return conflict

    now = datetime.now(timezone.utc)
    row = ThirdPartyLogin(
        id=str(uuid.uuid4()),
        user_id=user.id,
        provider=p,
        provider_id=provider_id,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def unbind_oauth_account(db: Session, user_id: str, provider: str) -> bool:
    """unbind_oauth_account。

    参数说明：
    :param db: 参数 db
    :param user_id: 参数 user_id
    :param provider: 参数 provider
    :return: 返回处理结果。
    """
    p = provider.lower()
    row = (
        db.query(ThirdPartyLogin)
        .filter(ThirdPartyLogin.user_id == user_id, ThirdPartyLogin.provider == p)
        .first()
    )
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True
