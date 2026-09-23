# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""后台菜单接口 — 菜单树 / 缓存刷新 / 列表读写闭环

职责划分：本路由负责「当前用户可见菜单树 + 全量管理 CRUD + 缓存刷新」；
`/permissions/menus/*` 保留兼容写接口，逻辑同源 AdminMenu。
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.admin_auth import build_menu_tree, get_current_super_admin
from app.core.cache import delete_pattern
from app.core.database import get_db
from app.core.response import success_response
from app.models.admin import AdminMenu
from app.models.user import User

router = APIRouter()


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


def _menu_row(m: AdminMenu) -> dict:
    return {
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
        "created_at": m.created_at.isoformat() if m.created_at else None,
        "updated_at": m.updated_at.isoformat() if m.updated_at else None,
    }


@router.get("/tree")
def get_menu_tree(
    user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    """获取当前用户的菜单树"""
    tree = build_menu_tree(user, db)
    return success_response(data=tree)


@router.get("/all")
def list_all_menus(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_super_admin),
):
    """全部菜单（扁平，管理用）"""
    menus = db.query(AdminMenu).order_by(AdminMenu.sort_order, AdminMenu.created_at).all()
    return success_response(data=[_menu_row(m) for m in menus])


@router.get("/{menu_id}")
def get_menu_detail(
    menu_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_super_admin),
):
    """菜单详情"""
    menu = db.query(AdminMenu).filter(AdminMenu.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="菜单不存在")
    return success_response(data=_menu_row(menu))


@router.post("")
def create_menu(
    body: MenuCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_super_admin),
):
    """创建菜单"""
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
    db.refresh(menu)
    delete_pattern("menu:*")
    return success_response(data=_menu_row(menu), message="菜单创建成功")


@router.put("/{menu_id}")
def update_menu(
    menu_id: str,
    body: MenuUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_super_admin),
):
    """更新菜单"""
    menu = db.query(AdminMenu).filter(AdminMenu.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="菜单不存在")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(menu, key, value)
    db.commit()
    db.refresh(menu)
    delete_pattern("menu:*")
    return success_response(data=_menu_row(menu), message="菜单已更新")


@router.delete("/{menu_id}")
def delete_menu(
    menu_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_super_admin),
):
    """删除菜单（子节点上挂到被删节点的父级）"""
    menu = db.query(AdminMenu).filter(AdminMenu.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="菜单不存在")
    db.query(AdminMenu).filter(AdminMenu.parent_id == menu_id).update(
        {AdminMenu.parent_id: menu.parent_id}
    )
    db.delete(menu)
    db.commit()
    delete_pattern("menu:*")
    return success_response(message="菜单已删除")


@router.post("/refresh")
def refresh_menu_cache(
    user: User = Depends(get_current_super_admin),
):
    """刷新所有菜单缓存"""
    delete_pattern("menu:*")
    return success_response(message="菜单缓存已刷新")
