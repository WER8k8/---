# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""产品 API — 材料规格查询"""

from fastapi import APIRouter, Depends
from app.core.admin_auth import get_current_super_admin
from app.core.response import success_response
from app.models.user import User

router = APIRouter()


@router.get("")
async def get_products(user: User = Depends(get_current_super_admin)):
    """列出所有产品（材料规格）"""
    from app.geo_engine.repositories import list_products
    products = await list_products()
    return success_response(data=products)


@router.get("/{slug}")
async def get_product(slug: str, user: User = Depends(get_current_super_admin)):
    """获取单个产品详情"""
    from app.geo_engine.repositories import get_product_by_slug
    product = await get_product_by_slug(slug)
    return success_response(data=product)
