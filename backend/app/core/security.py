# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
import time
import uuid
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.permissions import ROLE_PERMISSIONS, Role, has_permission
from app.models.user import User


def _patch_bcrypt_for_passlib() -> None:
    """passlib 1.7.4 + bcrypt 4.1+ 兼容（消除 trapped __about__ 告警）。"""
    try:
        import bcrypt as _bcrypt
        if not hasattr(_bcrypt, "__about__"):
            _bcrypt.__about__ = type(  # type: ignore[attr-defined]
                "_About",
                (),
                {"__version__": getattr(_bcrypt, "__version__", "4.0.0")},
            )()
    except Exception:
        pass


_patch_bcrypt_for_passlib()

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__min_rounds=12,
    bcrypt__default_rounds=14,
)
security_scheme = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """verify_password。

    参数说明：
    :param plain_password: 参数 plain_password
    :param hashed_password: 参数 hashed_password
    :return: 返回处理结果。
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """get_password_hash。

    参数说明：
    :param password: 参数 password
    :return: 返回处理结果。
    """
    return pwd_context.hash(password)


def create_access_token(
        data: dict,
        expires_delta: Optional[timedelta] = None) -> str:
    """create_access_token。

    参数说明：
    :param data: 参数 data
    :param expires_delta: 参数 expires_delta
    :return: 返回处理结果。
    """
    to_encode = data.copy()
    if "jti" not in to_encode:
        to_encode["jti"] = str(uuid.uuid4())
    expire_seconds = time.time() + (
        expires_delta.total_seconds() if expires_delta 
        else settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    expire = datetime.fromtimestamp(expire_seconds)
    to_encode.update({"exp": expire})
    from app.core.jwt_key_rotation import jwt_key_rotation_service
    return jwt_key_rotation_service.sign_token(to_encode)


def decode_refresh_payload(token: str) -> Optional[Dict[str, Any]]:
    """校验 refresh JWT：含 refresh scope、未过期；返回 payload。"""
    from app.core.jwt_key_rotation import jwt_key_rotation_service
    payload = jwt_key_rotation_service.decode_token(token)
    if payload is None:
        return None
    scopes = payload.get("scopes") or []
    if isinstance(scopes, str):
        scopes = [scopes]
    if "refresh" not in scopes:
        return None
    return payload


def decode_refresh_token(token: str) -> Optional[str]:
    """从 refresh token 解析用户 id（sub），无效则 None。"""
    payload = decode_refresh_payload(token)
    if not payload or payload.get("sub") is None:
        return None
    return str(payload.get("sub"))


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db),
    request: Request = None,
) -> User:
    """get_current_user。

    参数说明：
    :param credentials: 参数 credentials
    :param db: 参数 db
    :param request: 参数 request
    :return: 返回处理结果。
    """
    # FIX-22: 从 Header 或 HttpOnly Cookie 提取 token
    token = None
    if credentials is not None:
        token = credentials.credentials
    elif request is not None:
        from app.core.jwt_cookie import extract_token_from_cookie
        token = extract_token_from_cookie(request)

    if not token:
        # TEMP-DEBUG: 401 现场取证（cookie 解析诊断），验证后删除
        try:
            import logging as _logging
            _logging.getLogger("uj.debug401").warning(
                "401-no-token path=%s raw_cookie_len=%s raw_cookie=%s",
                request.url.path if request else "?",
                len(request.headers.get("cookie", "")) if request else -1,
                request.headers.get("cookie", "")[:600] if request else "",
            )
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    from app.core.jwt_key_rotation import jwt_key_rotation_service
    payload = jwt_key_rotation_service.decode_token(token)
    if payload is None and credentials is not None and request is not None:
        # Bearer 携带的是残留旧 token（或哨兵值 'cookie'）时，
        # 回退到 HttpOnly Cookie 里的最新 token，避免浏览器会话被误杀。
        # 注意：不能用 extract_token_from_cookie——它优先读 Authorization，
        # 会把同一个坏值再取回来。
        try:
            from app.core.jwt_cookie import _pick_latest_valid_cookie
            from app.core.config import settings as _settings
            cookie_token = _pick_latest_valid_cookie(request, _settings.JWT_COOKIE_NAME)
            if cookie_token and cookie_token != token:
                payload = jwt_key_rotation_service.decode_token(cookie_token)
                if payload is not None:
                    token = cookie_token
        except Exception:
            pass
    if payload is None:
        # TEMP-DEBUG: 无效令牌取证，验证后删除
        try:
            import logging as _logging
            _logging.getLogger("uj.debug401").warning(
                "401-invalid-token path=%s src=%s token=%s",
                request.url.path if request else "?",
                "header" if credentials is not None else "cookie",
                token[:24] if token else "None",
            )
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
        )
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
        )

    # 检查 access token 是否已被登出撤销（jti 黑名单）
    from app.core.access_token_blacklist import is_access_token_revoked
    jti = payload.get("jti")
    if jti and is_access_token_revoked(str(jti)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌已失效，请重新登录",
        )

    # 检查 Redis admin_session_revoked（对齐 get_current_super_admin）
    try:
        from app.core.cache import redis_client
        if redis_client and jti and user_id:
            revoked = redis_client.get(f"admin_session_revoked:{user_id}:{jti}")
            if revoked:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="会话已失效，请重新登录",
                )
    except Exception:
        # Redis 不可用时记录告警但仍然拒绝（安全优先于可用性）
        import logging as _logging
        _logging.getLogger("uj-admin.security").warning(
            "Redis 不可用，无法校验 session 撤销状态 (user=%s, jti=%s)",
            user_id[:8] if user_id else "None",
            jti[:8] if jti else "None",
        )

    user = db.query(User).filter(User.id == user_id, User.is_active).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已禁用",
        )
    from app.core.tenant_access import assert_user_tenant_active
    assert_user_tenant_active(user, db)
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    """require_admin。

    参数说明：
    :param user: 参数 user
    :return: 返回处理结果。
    """
    if user.role not in (Role.ADMIN.value, Role.SUPER_ADMIN.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    return user


def require_role(required_role: str):
    """验证用户是否具有指定角色"""
    def role_checker(user: User = Depends(get_current_user)) -> User:
        """role_checker。

        参数说明：
        :param user: 参数 user
        :return: 返回处理结果。
        """
        if user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要{required_role}角色权限",
            )
        return user

    return role_checker


def require_permission(resource: str, action: str):
    """验证用户是否具有指定资源的操作权限"""
    def permission_checker(user: User = Depends(get_current_user)) -> User:
        """permission_checker。

        参数说明：
        :param user: 参数 user
        :return: 返回处理结果。
        """
        if not has_permission(user.role, resource, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"无权执行此操作：{resource}.{action}",
            )
        return user

    return permission_checker


def require_any_role(allowed_roles: List[str]):
    """验证用户是否具有允许的角色之一"""
    def role_checker(user: User = Depends(get_current_user)) -> User:
        """role_checker。

        参数说明：
        :param user: 参数 user
        :return: 返回处理结果。
        """
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要以下角色之一：{', '.join(allowed_roles)}",
            )
        return user

    return role_checker


def resolve_user_from_bearer_token(token: str, db: Session) -> Optional[User]:
    """从 Bearer JWT 解析用户（供中间件等非 Depends 场景）。"""
    if not token:
        return None
    from app.core.jwt_key_rotation import jwt_key_rotation_service
    payload = jwt_key_rotation_service.decode_token(token)
    if payload is None:
        return None
    user_id: str | None = payload.get("sub")
    if user_id is None:
        return None
    return db.query(User).filter(User.id == user_id, User.is_active).first()


def resolve_user_from_request(request: Request, db: Session) -> Optional[User]:
    """从 Request Authorization 头解析用户。"""
    auth = request.headers.get("authorization") or request.headers.get(
        "Authorization"
    )
    if not auth or not auth.lower().startswith("bearer "):
        return None
    return resolve_user_from_bearer_token(auth[7:].strip(), db)


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db),
    request: Request = None,
) -> Optional[User]:
    """可选的用户获取，不强制要求认证。FIX-22: 支持 Cookie 提取。"""
    token = None
    if credentials is not None:
        token = credentials.credentials
    elif request is not None:
        from app.core.jwt_cookie import extract_token_from_cookie
        token = extract_token_from_cookie(request)
    
    if not token:
        return None
    return resolve_user_from_bearer_token(token, db)


def optional_auth(credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        security_scheme), db: Session = Depends(get_db), ) -> Optional[User]:
    """
    可选认证装饰器 - 在开发/测试环境中允许匿名访问，生产环境强制认证
    """
    if not settings.DEBUG:
        return get_current_user(credentials, db)
    return get_current_user_optional(credentials, db)



