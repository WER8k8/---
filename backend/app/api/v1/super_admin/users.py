# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""管理员用户管理接口

PII 加密说明：email 字段以 AES-256-GCM 加密存储。
    读取时自动解密，写入时自动加密。
    contains 搜索对加密字段无效，仅按用户名和显示名模糊匹配。
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.admin_auth import (get_current_super_admin,
                                  invalidate_user_permission_cache)
from app.core.database import get_db
from app.core.field_crypto import decrypt_field, encrypt_field
from app.core.response import success_response
from app.core.security import get_password_hash
from app.models.admin import LoginLog
from app.models.user import User

router = APIRouter()


def _try_decrypt(value: str) -> str:
    """尝试解密，兼容历史明文数据。"""
    if not value:
        return value
    try:
        return decrypt_field(value)
    except Exception:
        return value


class AdminUserCreate(BaseModel):
    username: str
    password: str
    email: str = ""
    display_name: str = ""
    role: str = "admin"
    role_id: Optional[str] = None


class AdminUserUpdate(BaseModel):
    email: Optional[str] = None
    display_name: Optional[str] = None
    role: Optional[str] = None
    role_id: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("")
def list_admin_users(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
):
    """管理员用户列表"""
    query = db.query(User)
    if search:
        # 加密字段不支持 contains 模糊搜索，仅按用户名/显示名匹配
        query = query.filter(
            User.username.contains(search) | User.display_name.contains(search)
        )
    if role:
        query = query.filter(User.role == role)

    total = query.count()
    users = (
        query.order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    data = [{
        "id": str(u.id),
        "username": u.username,
        "email": _try_decrypt(u.email),
        "display_name": u.display_name,
        "role": u.role,
        "role_id": str(u.role_id) if u.role_id else None,
        "is_active": u.is_active,
        "created_at": u.created_at.isoformat() if u.created_at else None,
    } for u in users]
    return success_response(data=data, total=total, page=page, page_size=page_size)


@router.post("")
def create_admin_user(
    body: AdminUserCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """创建管理员用户"""
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")

    user = User(
        username=body.username,
        email=encrypt_field(body.email or f"{body.username}@admin.local"),
        hashed_password=get_password_hash(body.password),
        display_name=body.display_name or body.username,
        role=body.role,
        role_id=body.role_id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return success_response(
        data={"id": str(user.id), "username": user.username},
        message="用户创建成功",
    )


@router.put("/{user_id}")
def update_admin_user(
    user_id: str,
    body: AdminUserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """更新管理员用户"""
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")

    if body.email is not None:
        target.email = encrypt_field(body.email)
    if body.display_name is not None:
        target.display_name = body.display_name
    if body.role is not None:
        target.role = body.role
    if body.role_id is not None:
        target.role_id = body.role_id
    if body.is_active is not None:
        target.is_active = body.is_active

    db.commit()
    invalidate_user_permission_cache(user_id)
    return success_response(message="用户更新成功")


@router.delete("/{user_id}")
def delete_admin_user(
    user_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """删除管理员用户"""
    if str(admin.id) == user_id:
        raise HTTPException(status_code=400, detail="不能删除自己")

    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")

    db.delete(target)
    db.commit()
    invalidate_user_permission_cache(user_id)
    return success_response(message="用户已删除")


@router.post("/{user_id}/reset-password")
def reset_user_password(
    user_id: str,
    password: str = Query(..., min_length=6),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """重置用户密码"""
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")

    target.hashed_password = get_password_hash(password)
    db.commit()
    return success_response(message="密码已重置")


@router.get("/login-logs")
def list_login_logs(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    username: Optional[str] = Query(None),
):
    """登录日志列表"""
    query = db.query(LoginLog)
    if username:
        query = query.filter(LoginLog.username.contains(username))

    total = query.count()
    logs = (
        query.order_by(LoginLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    data = [{
        "id": str(log.id),
        "user_id": str(log.user_id) if log.user_id else None,
        "username": log.username,
        "ip_address": log.ip_address,
        "success": log.success,
        "fail_reason": log.fail_reason,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    } for log in logs]
    return success_response(data=data, total=total, page=page, page_size=page_size)
