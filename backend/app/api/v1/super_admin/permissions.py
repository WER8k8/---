# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""角色 & 权限管理接口"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.admin_auth import (get_current_super_admin,
                                  invalidate_user_permission_cache)
from app.core.cache import ADMIN_CACHE_KEYS, delete_pattern
from app.core.database import get_db
from app.core.response import success_response
from app.models.admin import AdminMenu, AdminPermission, AdminRole, RolePermission
from app.models.user import User

router = APIRouter()


# === 角色管理 ===

class RoleCreate(BaseModel):
    name: str
    description: str = ""
    permission_ids: List[str] = []


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permission_ids: Optional[List[str]] = None


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
    """创建角色"""
    exists = db.query(AdminRole).filter(AdminRole.name == body.name).first()
    if exists:
        raise HTTPException(status_code=400, detail="角色名已存在")

    import uuid
    role = AdminRole(
        id=str(uuid.uuid4()),
        name=body.name,
        description=body.description,
        is_system=False,
        sort_order=99,
    )
    db.add(role)
    db.flush()
    # 分配权限
    for pid in body.permission_ids:
        db.add(RolePermission(
            id=str(uuid.uuid4()),
            role_id=role.id,
            permission_id=pid,
        ))

    db.commit()
    delete_pattern(f"perm:*")
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

    if body.permission_ids is not None:
        # 清除旧权限
        db.query(RolePermission).filter(RolePermission.role_id == role_id).delete()
        # 分配新权限
        import uuid
        for pid in body.permission_ids:
            db.add(RolePermission(
                id=str(uuid.uuid4()),
                role_id=role_id,
                permission_id=pid,
            ))

    db.commit()
    # 清除所有关联用户的权限缓存
    affected_users = db.query(User).filter(User.role_id == role_id).all()
    for u in affected_users:
        invalidate_user_permission_cache(str(u.id))
    delete_pattern(f"perm:*")
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

    # 清除关联用户
    db.query(User).filter(User.role_id == role_id).update({User.role_id: None})
    db.delete(role)
    db.commit()
    delete_pattern(f"perm:*")
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


# === 菜单管理 ===

class MenuCreate(BaseModel):
    parent_id: Optional[str] = None
    title: str
    icon: Optional[str] = None
    path: Optional[str] = None
    permission_code: Optional[str] = None
    sort_order: int = 0
    visible: bool = True
    component_path: Optional[str] = None


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
    import uuid, json
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
    )
    db.add(menu)
    db.commit()
    delete_pattern("menu:*")
    return success_response(data={"id": str(menu.id)}, message="菜单创建成功")


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
    db.delete(menu)
    db.commit()
    delete_pattern("menu:*")
    return success_response(message="菜单已删除")
