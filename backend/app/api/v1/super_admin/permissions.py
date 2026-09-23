# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""角色 & 权限管理接口"""

import json
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.admin_auth import (get_current_super_admin,
                                  invalidate_user_permission_cache)
from app.core.cache import delete_pattern
from app.core.database import get_db
from app.core.response import success_response
from app.models.admin import AdminMenu, AdminPermission, AdminRole, RolePermission
from app.models.user import User

router = APIRouter()

DEFAULT_AGENT_ROLE_NAME = "agent_capabilities"


class RoleCreate(BaseModel):
    name: str = ""
    description: str = ""
    permission_ids: Optional[List[str]] = None
    grants: Optional[dict[str, List[str]]] = None


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permission_ids: Optional[List[str]] = None
    grants: Optional[dict[str, List[str]]] = None


class PermissionCodeCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=100)
    group_name: str = "default"
    description: str = ""


class PermissionCodeUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=100)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    group_name: Optional[str] = None
    description: Optional[str] = None


class MenuCreate(BaseModel):
    parent_id: Optional[str] = None
    title: str
    icon: Optional[str] = None
    path: Optional[str] = None
    permission_code: Optional[str] = None
    sort_order: int = 0
    visible: bool = True
    component_path: Optional[str] = None
    meta_json: Optional[str] = None


class MenuUpdate(BaseModel):
    parent_id: Optional[str] = None
    title: Optional[str] = None
    icon: Optional[str] = None
    path: Optional[str] = None
    permission_code: Optional[str] = None
    sort_order: Optional[int] = None
    visible: Optional[bool] = None
    component_path: Optional[str] = None
    meta_json: Optional[str] = None


def _grants_to_permission_ids(db: Session, grants: dict[str, List[str]]) -> List[str]:
    codes: list[str] = []
    seen: set[str] = set()
    for values in grants.values():
        if not isinstance(values, list):
            continue
        for code in values:
            if isinstance(code, str) and code and code not in seen:
                seen.add(code)
                codes.append(code)
    ids: list[str] = []
    for code in codes:
        perm = db.query(AdminPermission).filter(AdminPermission.code == code).first()
        if not perm:
            perm = AdminPermission(
                id=str(uuid.uuid4()),
                code=code,
                name=code,
                group_name="agent_capability",
            )
            db.add(perm)
            db.flush()
        ids.append(str(perm.id))
    return ids


def _resolve_permission_ids(
    db: Session,
    permission_ids: Optional[List[str]],
    grants: Optional[dict[str, List[str]]],
) -> List[str]:
    if grants is not None:
        return _grants_to_permission_ids(db, grants)
    return list(permission_ids or [])


def _replace_role_permissions(db: Session, role_id: str, permission_ids: List[str]) -> None:
    db.query(RolePermission).filter(RolePermission.role_id == role_id).delete()
    for pid in permission_ids:
        db.add(RolePermission(
            id=str(uuid.uuid4()),
            role_id=role_id,
            permission_id=pid,
        ))


def _invalidate_role_cache(db: Session, role_id: str) -> None:
    affected_users = db.query(User).filter(User.role_id == role_id).all()
    for u in affected_users:
        invalidate_user_permission_cache(str(u.id))
    delete_pattern("perm:*")


# === 角色管理 ===

@router.get("/roles")
def list_roles(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_super_admin),
):
    """角色列表"""
    roles = db.query(AdminRole).order_by(AdminRole.sort_order).all()
    data = []
    for role in roles:
        perm_ids = [
            str(rp.permission_id)
            for rp in db.query(RolePermission)
            .filter(RolePermission.role_id == role.id)
            .all()
        ]
        data.append({
            "id": str(role.id),
            "name": role.name,
            "description": role.description,
            "is_system": role.is_system,
            "sort_order": role.sort_order,
            "permission_ids": perm_ids,
            "user_count": db.query(User).filter(User.role_id == role.id).count(),
            "created_at": role.created_at.isoformat() if role.created_at else None,
        })
    return success_response(data=data)


@router.post("/roles")
def create_role(
    body: RoleCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_super_admin),
):
    """创建角色；兼容前端 agentCapabilities 的 {grants} 载荷"""
    grants_only = body.grants is not None and not body.name and not body.permission_ids
    name = body.name or (DEFAULT_AGENT_ROLE_NAME if grants_only else "")
    if not name:
        raise HTTPException(status_code=400, detail="角色名不能为空")

    permission_ids = _resolve_permission_ids(db, body.permission_ids, body.grants)

    exists = db.query(AdminRole).filter(AdminRole.name == name).first()
    if grants_only and exists:
        _replace_role_permissions(db, str(exists.id), permission_ids)
        db.commit()
        _invalidate_role_cache(db, str(exists.id))
        return success_response(data={"id": str(exists.id)}, message="代理能力已同步")

    if exists:
        raise HTTPException(status_code=400, detail="角色名已存在")

    role = AdminRole(
        id=str(uuid.uuid4()),
        name=name,
        description=body.description,
        is_system=False,
        sort_order=99,
    )
    db.add(role)
    db.flush()
    _replace_role_permissions(db, str(role.id), permission_ids)
    db.commit()
    delete_pattern("perm:*")
    return success_response(data={"id": str(role.id)}, message="角色创建成功")


@router.put("/roles/{role_id}")
def update_role(
    role_id: str,
    body: RoleUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_super_admin),
):
    """更新角色"""
    role = db.query(AdminRole).filter(AdminRole.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    if role.is_system:
        raise HTTPException(status_code=400, detail="系统角色不可编辑")

    if body.name is not None:
        role.name = body.name
    if body.description is not None:
        role.description = body.description

    if body.permission_ids is not None or body.grants is not None:
        permission_ids = _resolve_permission_ids(db, body.permission_ids, body.grants)
        _replace_role_permissions(db, role_id, permission_ids)

    db.commit()
    _invalidate_role_cache(db, role_id)
    return success_response(message="角色更新成功")


@router.delete("/roles/{role_id}")
def delete_role(
    role_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_super_admin),
):
    """删除角色"""
    role = db.query(AdminRole).filter(AdminRole.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    if role.is_system:
        raise HTTPException(status_code=400, detail="系统角色不可删除")

    db.query(User).filter(User.role_id == role_id).update({User.role_id: None})
    db.delete(role)
    db.commit()
    delete_pattern("perm:*")
    return success_response(message="角色已删除")


# === 权限码管理 ===

@router.get("/codes")
def list_permissions(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_super_admin),
):
    """全部权限码列表"""
    perms = db.query(AdminPermission).order_by(AdminPermission.group_name, AdminPermission.code).all()
    data = [{
        "id": str(p.id),
        "code": p.code,
        "name": p.name,
        "group_name": p.group_name,
        "description": p.description,
    } for p in perms]
    return success_response(data=data)


@router.get("/codes/groups")
def list_permission_groups(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_super_admin),
):
    """权限分组列表"""
    from sqlalchemy import distinct
    groups = db.query(distinct(AdminPermission.group_name)).order_by(AdminPermission.group_name).all()
    return success_response(data=[g[0] for g in groups])


@router.post("/codes")
def create_permission_code(
    body: PermissionCodeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_super_admin),
):
    """创建权限码"""
    exists = db.query(AdminPermission).filter(AdminPermission.code == body.code).first()
    if exists:
        raise HTTPException(status_code=400, detail="权限码已存在")
    perm = AdminPermission(
        id=str(uuid.uuid4()),
        code=body.code,
        name=body.name,
        group_name=body.group_name,
        description=body.description,
    )
    db.add(perm)
    db.commit()
    delete_pattern("perm:*")
    return success_response(data={"id": str(perm.id)}, message="权限码创建成功")


@router.put("/codes/{code_id}")
def update_permission_code(
    code_id: str,
    body: PermissionCodeUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_super_admin),
):
    """更新权限码"""
    perm = db.query(AdminPermission).filter(AdminPermission.id == code_id).first()
    if not perm:
        raise HTTPException(status_code=404, detail="权限码不存在")
    if body.code is not None and body.code != perm.code:
        exists = db.query(AdminPermission).filter(AdminPermission.code == body.code).first()
        if exists:
            raise HTTPException(status_code=400, detail="权限码已存在")
        perm.code = body.code
    if body.name is not None:
        perm.name = body.name
    if body.group_name is not None:
        perm.group_name = body.group_name
    if body.description is not None:
        perm.description = body.description
    db.commit()
    delete_pattern("perm:*")
    return success_response(message="权限码已更新")


@router.delete("/codes/{code_id}")
def delete_permission_code(
    code_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_super_admin),
):
    """删除权限码"""
    perm = db.query(AdminPermission).filter(AdminPermission.id == code_id).first()
    if not perm:
        raise HTTPException(status_code=404, detail="权限码不存在")
    db.query(RolePermission).filter(RolePermission.permission_id == code_id).delete()
    db.delete(perm)
    db.commit()
    delete_pattern("perm:*")
    return success_response(message="权限码已删除")


# === 菜单管理（职责：permissions 挂菜单写接口兼容旧前端；树/刷新见 /menus） ===

@router.get("/menus/all")
def list_all_menus(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_super_admin),
):
    """全部菜单列表（管理用）"""
    menus = db.query(AdminMenu).order_by(AdminMenu.sort_order).all()
    data = [{
        "id": str(m.id),
        "parent_id": str(m.parent_id) if m.parent_id else None,
        "title": m.title,
        "icon": m.icon,
        "path": m.path,
        "permission_code": m.permission_code,
        "sort_order": m.sort_order,
        "visible": m.visible,
        "component_path": m.component_path,
        "meta_json": m.meta_json,
    } for m in menus]
    return success_response(data=data)


@router.post("/menus")
def create_menu(
    body: MenuCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_super_admin),
):
    """创建菜单项"""
    menu = AdminMenu(
        id=str(uuid.uuid4()),
        parent_id=body.parent_id,
        title=body.title,
        icon=body.icon,
        path=body.path,
        permission_code=body.permission_code,
        sort_order=body.sort_order,
        visible=body.visible,
        component_path=body.component_path,
        meta_json=body.meta_json,
    )
    db.add(menu)
    db.commit()
    delete_pattern("menu:*")
    return success_response(data={"id": str(menu.id)}, message="菜单创建成功")


@router.put("/menus/{menu_id}")
def update_menu(
    menu_id: str,
    body: MenuUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_super_admin),
):
    """更新菜单项"""
    menu = db.query(AdminMenu).filter(AdminMenu.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="菜单不存在")
    payload = body.model_dump(exclude_unset=True)
    if "meta_json" in payload and payload["meta_json"]:
        try:
            json.loads(payload["meta_json"])
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="meta_json 必须是合法 JSON 字符串")
    for key, value in payload.items():
        setattr(menu, key, value)
    db.commit()
    delete_pattern("menu:*")
    return success_response(message="菜单已更新")


@router.delete("/menus/{menu_id}")
def delete_menu(
    menu_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_super_admin),
):
    """删除菜单项"""
    menu = db.query(AdminMenu).filter(AdminMenu.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="菜单不存在")
    db.query(AdminMenu).filter(AdminMenu.parent_id == menu_id).update({AdminMenu.parent_id: menu.parent_id})
    db.delete(menu)
    db.commit()
    delete_pattern("menu:*")
    return success_response(message="菜单已删除")
