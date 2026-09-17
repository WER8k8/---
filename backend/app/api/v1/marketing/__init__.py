# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Marketing 聚合路由模块。"""

from fastapi import APIRouter
from app.api.v1.marketing.gmc import router as gmc_router
from app.api.v1.marketing.events import router as events_router

router = APIRouter()
router.include_router(gmc_router)
router.include_router(events_router)
