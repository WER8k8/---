# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""GEO 出海国家矩阵路由汇聚层。"""

from fastapi import APIRouter
from app.api.v1.geo.country_matrix import router as country_matrix_router

router = APIRouter()
router.include_router(country_matrix_router)
