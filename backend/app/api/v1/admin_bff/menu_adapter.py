# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""菜单 BFF — HTTP 薄层；DB 菜单优先，否则静态 seed"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.admin_bff.menu_seeds import seeds_for_shell
from app.api.v1.admin_bff.menu_transform import db_tree_to_routes, seed_nodes_to_routes
from app.api.v1.admin_bff.schemas import UacPermissionBundle
from app.api.v1.admin_bff.shell import resolve_home_path, resolve_shell
from app.core.admin_auth import build_menu_tree, get_user_permission_codes
from app.core.database import get_db
from app.core.response import success_response
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/routes")
async def get_menu_routes(
    shell: Optional[str] = Query(None, description="client|platform|partner|agent|ops（仅调试；生产以 JWT 为准）"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """get_menu_routes。

    参数说明：
    :param shell: 参数 shell
    :param user: 参数 user
    :param db: 参数 db
    :return: 返回处理结果。
    """
    active_shell = resolve_shell(user)
    if shell and shell == active_shell:
        active_shell = shell

    tree = build_menu_tree(user, db)
    if tree:
        routes = db_tree_to_routes(tree, active_shell)
    else:
        routes = seed_nodes_to_routes(seeds_for_shell(active_shell))

    return success_response(data=[r.model_dump() for r in routes])


@router.get("/permissions")
async def get_menu_permissions(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """get_menu_permissions。

    参数说明：
    :param user: 参数 user
    :param db: 参数 db
    :return: 返回处理结果。
    """
    shell = resolve_shell(user)
    codes = await get_user_permission_codes(user, db)
    roles = [user.role] if user.role else []
    bundle = UacPermissionBundle(
        shell=shell,
        roles=roles,
        codes=codes,
        homePath=resolve_home_path(shell),
    )
    return success_response(data=bundle.model_dump())
