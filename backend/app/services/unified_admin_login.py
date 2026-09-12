"""主站 users 与 SEO 矩阵 admin_users 的统一登录解析（不丢数据、可签发同一 JWT）。"""

from __future__ import annotations

from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.matrix_admin_bridge import (
    matrix_credentials_source_configured, verify_matrix_admin)

ADMIN_ROLES = frozenset({"admin", "super_admin"})


def resolve_user_for_unified_login(
    db: Session, username_or_email: str, password: str
) -> Tuple[Optional[User], Optional[int]]:
    """
    返回 (User, seo_matrix_admin_id)。
    - 主库密码正确：直接返回，并尽量解析矩阵侧 id 写入 JWT（供 Node 矩阵 API 使用）。
    - 主库失败但矩阵库密码正确：同步更新或创建主库用户，再返回。
    """
    raw = (username_or_email or "").strip()
    if not raw or not password:
        return None, None

    matrix_on = matrix_credentials_source_configured(settings)
    user_repo = UserRepository(db)
    user = user_repo.get_by_username_or_email(raw)
    def matrix_admin_id_for_user(u: User) -> Optional[int]:
        """matrix_admin_id_for_user。

        参数说明：
        :param u: 参数 u
        :return: 返回处理结果。
        """
        if not matrix_on:
            return None
        candidates = [u.username]
        if "@" in raw:
            candidates.append(raw.split("@", 1)[0])
        for key in candidates:
            mp = verify_matrix_admin(settings, key, password)
            if mp:
                return mp[0]
        return None

    if user and verify_password(password, user.hashed_password):
        return user, matrix_admin_id_for_user(user)

    matrix_pair = verify_matrix_admin(
        settings, raw, password) if matrix_on else None

    if not matrix_pair:
        return None, None

    mid, canon = matrix_pair
    target = user_repo.get_by_username(
        canon) or user_repo.get_by_username(raw) or user
    new_hash = get_password_hash(password)
    if target:
        target.hashed_password = new_hash
        target.is_active = True
        if target.role not in ADMIN_ROLES:
            target.role = "super_admin"
        db.add(target)
        db.commit()
        db.refresh(target)
        return target, mid

    email = f"seo_matrix_{mid}@youding.integration"
    n = 0
    while user_repo.exists_by_email(email) and n < 8:
        n += 1
        email = f"seo_matrix_{mid}_{n}@youding.integration"

    u = User(
        username=canon[:50],
        email=email[:100],
        hashed_password=new_hash,
        display_name=f"SEO:{canon}"[:100],
        role="super_admin",
        is_active=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u, mid
