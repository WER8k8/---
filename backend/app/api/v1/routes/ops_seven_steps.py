# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""商用七步主链 · 框架级自动验收路由（`/ops/seven-steps/audit`）。

接线背景（2026-09-24 全域孤岛普查发现并修复的断链）：
    前端 `frontend/admin/src/views/admin/demo-rehearsal.vue:740` 一直在调
        GET /api/v1/ops/seven-steps/audit?demo_domain=...
    `backend/app/services/production_readiness_service.py:846` 也把该路径
    列进「期望挂载路由清单」；
    实现 `seven_step_framework_service.run_seven_step_audit` 早已存在，
    但**全仓没有任何路由文件定义它** —— 前端恒 404、七步验收器从未被调用。

    本模块补齐这条断链。返回结构（前端按 `data.steps` / `data.summary` 消费）：
        {framework, environment, steps[], summary{pass,warn,fail,ready_for_recording},
         readiness, routes_mounted, demo_https, demo_domain_override}
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.models.user import User
from app.services.seven_step_framework_service import run_seven_step_audit

logger = logging.getLogger(__name__)

ROUTE_PREFIX = "/ops"
ROUTE_TAGS = ["运维聚合"]

router = APIRouter(tags=["运维聚合"])


@router.get("/seven-steps/audit")
def seven_steps_audit(
    demo_domain: str | None = Query(
        None, description="演示域，用于第 ② 步「独立域 HTTPS」探测；留空则读环境配置"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """按产品七步 1→7 返回每步 pass/warn/fail（框架最重要验收）。

    求真：各步状态由真实探测得出（路由是否挂载 / HTTPS 可达性 / 队列统计），
    探测失败按 fail/warn 诚实呈现，不伪造 pass。
    """
    try:
        report = run_seven_step_audit(db, demo_domain)
    except Exception as exc:  # noqa: BLE001
        logger.exception("七步验收执行失败")
        return error_response(500, f"七步验收执行失败：{type(exc).__name__}: {exc}")
    return success_response(data=report)
