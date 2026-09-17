# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, EmailStr
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import success_response
from app.core.field_crypto import decrypt_field, encrypt_field
from app.core.permissions import Role, get_role_label, has_permission
from app.core.security import get_password_hash, require_admin
from app.models.user import User

router = APIRouter()


def _try_decrypt(value: str) -> str:
    """尝试解密，兼容历史明文数据。"""
    try:
        return decrypt_field(value)
    except Exception:
        return value


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    display_name: Optional[str] = None
    role: str = "editor"


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    display_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    username: str
    email: str
    display_name: Optional[str]
    role: str
    role_label: str
    is_active: bool
    created_at: str


@router.get("/users", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db), admin=Depends(require_admin)):
    """list_users。

    参数说明：
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [
        UserResponse(
            id=str(u.id),
            username=u.username,
            email=_try_decrypt(u.email),
            display_name=u.display_name,
            role=u.role,
            role_label=get_role_label(u.role),
            is_active=u.is_active,
            created_at=u.created_at.isoformat() if u.created_at else "",
        )
        for u in users
    ]


@router.post("/users")
def create_user(
        req: UserCreate,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """create_user。

    参数说明：
    :param req: 参数 req
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    if not has_permission(admin.role, "users", "create"):
        raise HTTPException(status_code=403, detail="无权限")

    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    existing_email = db.query(User).filter(User.email == encrypt_field(req.email)).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="邮箱已被使用")

    user = User(
        username=req.username,
        email=encrypt_field(req.email),
        hashed_password=get_password_hash(req.password),
        display_name=req.display_name or req.username,
        role=req.role if req.role in [r.value for r in Role] else "editor",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return success_response(data={"id": str(user.id)}, message="用户创建成功")


@router.put("/users/{user_id}")
def update_user(
        user_id: str,
        req: UserUpdate,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """update_user。

    参数说明：
    :param user_id: 参数 user_id
    :param req: 参数 req
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    if not has_permission(admin.role, "users", "update"):
        raise HTTPException(status_code=403, detail="无权限")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if req.email:
        existing = db.query(User).filter(
            User.email == encrypt_field(req.email),
            User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="邮箱已被使用")
        user.email = encrypt_field(req.email)
    if req.display_name is not None:
        user.display_name = req.display_name
    if req.role and req.role in [r.value for r in Role]:
        user.role = req.role
    if req.is_active is not None:
        user.is_active = req.is_active
    if req.password:
        user.hashed_password = get_password_hash(req.password)

    db.commit()
    return success_response(message="用户更新成功")


@router.delete("/users/{user_id}")
def delete_user(
        user_id: str,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """delete_user。

    参数说明：
    :param user_id: 参数 user_id
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    if not has_permission(admin.role, "users", "delete"):
        raise HTTPException(status_code=403, detail="无权限")
    if str(admin.id) == user_id:
        raise HTTPException(status_code=400, detail="不能删除自己")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.is_active = False
    db.commit()
    return success_response(message="用户已禁用")


@router.get("/roles")
def list_roles(admin=Depends(require_admin)):
    """list_roles。

    参数说明：
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    return [{"value": r.value, "label": get_role_label(r.value)} for r in Role]
