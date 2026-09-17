# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""后台菜单接口"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.admin_auth import build_menu_tree, get_current_super_admin
from app.core.cache import ADMIN_CACHE_KEYS, delete_pattern, set_cache
from app.core.database import get_db
from app.core.response import success_response
from app.models.user import User

router = APIRouter()


@router.get("/tree")
def get_menu_tree(
    user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    """获取当前用户的菜单树"""
    tree = build_menu_tree(user, db)
    return success_response(data=tree)


@router.post("/refresh")
def refresh_menu_cache(
    user: User = Depends(get_current_super_admin),
):
    """刷新所有菜单缓存"""
    delete_pattern("menu:*")
    return success_response(message="菜单缓存已刷新")
