# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""生产就绪度检查路由（`/ops/readiness`）。

接线背景（2026-09-24 全域孤岛普查发现并修复的自指缺陷）：
    `production_readiness_service.check_mounted_routes()` 把
        /api/v1/ops/readiness
    列为**期望挂载的关键路由**（`required` 清单第 4 项），
    前端 `views/admin/platform-zones.vue:182` 也在 `fetch` 它 ——
    但**全仓没有任何路由文件定义它**（`openapi()` 零命中）。

    → 即：**那个「检查别人有没有挂载」的服务，自己没挂载。**
      前端拿到的是 404，`catch {}` 静默吞掉，页面上就绪度永远是空。

    本模块补齐这条断链。

返回结构（前端按 `data.checks` / `data.ready` 消费）：
    {ready, checks:[{key, group, title, status, message, required}], ...}
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.models.user import User
from app.services.production_readiness_service import run_readiness_checks

logger = logging.getLogger(__name__)

ROUTE_PREFIX = "/ops"
ROUTE_TAGS = ["运维聚合"]

router = APIRouter(tags=["运维聚合"])


@router.get("/readiness")
def ops_readiness(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """生产就绪度全量检查（JWT / 存储 / 支付 / 邮件 / 路由挂载 / UBrain 等）。

    求真：各项状态由真实探测得出；探测不到就如实 fail/warn，不伪造 pass。
    """
    try:
        report = run_readiness_checks(db)
        return success_response(data=report.to_dict())
    except Exception as exc:  # noqa: BLE001
        logger.exception("就绪度检查执行失败")
        return error_response(500, f"就绪度检查执行失败：{type(exc).__name__}: {exc}")


@router.get("/router-mount-failures")
def router_mount_failures(
    current_user: User = Depends(get_current_user),
):
    """路由挂载失败清单（P1-c 可观测性）。

    返回 register_routes() 期间所有被捕获的挂载异常明细，
    让「子包导入失败 → 整段路由静默 404」从不可见变为可探测。
    """
    from app.api.v1.routes import ROUTER_MOUNT_FAILURES

    return success_response(
        data={
            "failures": ROUTER_MOUNT_FAILURES,
            "count": len(ROUTER_MOUNT_FAILURES),
            "healthy": len(ROUTER_MOUNT_FAILURES) == 0,
        }
    )
