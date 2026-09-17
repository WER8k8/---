# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""超级管理员认证接口"""

import logging
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.admin_auth import get_current_super_admin, invalidate_user_permission_cache
from app.core.cache import (ADMIN_CACHE_KEYS, ADMIN_CACHE_TTL, invalidate_admin_session,
                             redis_client, set_cache)
from app.core.config import settings
from app.core.database import get_db
from app.core.field_crypto import decrypt_field, encrypt_field
from app.core.login_bruteforce import (check_login_allowed,
                                       client_ip_from_request,
                                       record_login_failure,
                                       record_login_success)
from app.core.response import error_response, success_response
from app.core.security import (create_access_token, get_current_user,
                                get_password_hash, verify_password)
from app.models.admin import LoginLog
from app.models.user import User
from app.services.unified_admin_login import resolve_user_for_unified_login

router = APIRouter()


from pydantic import Field


def _try_decrypt(value: str) -> str:
    """尝试解密，兼容历史明文数据。"""
    if not value:
        return value
    try:
        return decrypt_field(value)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning("解密字段失败，返回原始值: %s", e)
        return value


class AdminLoginRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50, pattern=r'^[a-zA-Z0-9_\-\.@]+$')
    password: str = Field(..., min_length=6, max_length=128)


class AdminCreateRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)
    email: str = ""
    display_name: str = ""


class AdminPasswordReset(BaseModel):
    user_id: str
    new_password: str = Field(..., min_length=6, max_length=128)


@router.post("/login")
def super_admin_login(
    req: AdminLoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """超级管理员登录（带暴力破解防护）"""
    # 暴力破解防护
    ip = client_ip_from_request(request)
    blocked = check_login_allowed(ip, req.username)
    if blocked:
        return error_response(blocked[0], blocked[1])

    # 使用统一登录服务解析用户
    user, matrix_admin_id = resolve_user_for_unified_login(
        db, req.username, req.password)
    
    if not user or not user.is_active:
        record_login_failure(ip, req.username)
        # 记录失败日志
        db.add(LoginLog(
            username=req.username,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent", ""),
            success=False,
            fail_reason="用户名或密码错误",
        ))
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    # 检查超级管理员权限
    if user.role != "super_admin":
        record_login_failure(ip, req.username)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限",
        )

    record_login_success(ip, req.username)
    # 生成 JWT（包含矩阵管理员ID）
    access_body = {"sub": str(user.id), "role": user.role, "scopes": [user.role]}
    if matrix_admin_id is not None:
        access_body["mid"] = matrix_admin_id
    
    access_token = create_access_token(
        data=access_body,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    # 记录登录日志
    db.add(LoginLog(
        user_id=user.id,
        username=user.username,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent", ""),
        success=True,
    ))
    db.commit()
    return success_response(data={
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "username": user.username,
            "display_name": user.display_name,
            "email": _try_decrypt(user.email),
            "role": user.role,
        },
    })


@router.post("/logout")
def super_admin_logout(
    request: Request,
    user: User = Depends(get_current_super_admin),
):
    """超级管理员登出"""
    auth = request.headers.get("Authorization", "")
    token = auth[7:] if auth.startswith("Bearer ") else None
    if token and redis_client:
        import jwt
        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
                options={"verify_exp": False},
            )
            jti = payload.get("jti", "")
            invalidate_admin_session(str(user.id), jti)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning("清理JWT黑名单失败，尝试兜底: %s", e)
            invalidate_admin_session(str(user.id))

    invalidate_user_permission_cache(str(user.id))
    return success_response(message="已登出")


@router.get("/me")
async def get_admin_profile(
    user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    """获取当前管理员信息"""
    from app.core.admin_auth import get_user_permission_codes
    codes = await get_user_permission_codes(user, db)
    return success_response(data={
        "id": str(user.id),
        "username": user.username,
        "display_name": user.display_name,
        "email": user.email,
        "role": user.role,
        "permission_codes": codes,
    })


@router.post("/create-first-admin")
def create_first_super_admin(
    req: AdminCreateRequest,
    db: Session = Depends(get_db),
):
    """创建首个超级管理员（仅当系统中无超管时可用）"""
    existing = db.query(User).filter(User.role == "super_admin").first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已存在超级管理员，请通过后台管理界面创建",
        )

    # 检查用户名唯一性
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")

    user = User(
        username=req.username,
        email=encrypt_field(req.email or f"{req.username}@admin.local"),
        hashed_password=get_password_hash(req.password),
        display_name=req.display_name or req.username,
        role="super_admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return success_response(
        data={"id": str(user.id), "username": user.username},
        message="超级管理员创建成功",
    )
