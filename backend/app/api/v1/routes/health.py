# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
系统健康检查端点

提供三类健康检查：
- /health         基础存活检查（无需认证）
- /health/db      数据库连通性检查（无需认证）
- /health/ready   就绪检查（无需认证）

供 Kubernetes / Docker 健康探针、负载均衡器、监控系统使用。
"""

import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.response import APIResponse
from app.db.session import get_db

logger = logging.getLogger("uj-admin.health")


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(tags=["健康检查"])


@router.get("/health")
def health_check():
    """
    基础健康检查

    返回服务是否存活。不依赖任何外部资源，用于负载均衡器存活探针。
    仅返回公共状态字段，不暴露版本等指纹信息。
    """
    return APIResponse.success(
        data={
            "status": "ok",
        }
    )


@router.get("/health/db")
def db_health(db: Session = Depends(get_db)):
    """
    数据库健康检查

    执行 SELECT 1 验证数据库连接是否正常。
    用于 Kubernetes 就绪探针或数据库依赖监控。
    """
    try:
        db.execute(text("SELECT 1"))
        return APIResponse.success(
            data={
                "status": "ok",
                "database": "connected",
            }
        )
    except Exception as e:
        logger.error("数据库健康检查失败: %s", e)
        return APIResponse.error(
            code=503,
            message="数据库连接异常",
        )


@router.get("/health/ready")
def readiness(db: Session = Depends(get_db)):
    """
    就绪检查（含 DB + Redis + 关键配置）

    适用于 Kubernetes 就绪探针。
    任意关键依赖异常返回 503。
    """
    checks = {"db": "unknown", "redis": "unknown"}
    # ── PostgreSQL / DB check ──────────────────────────────────
    try:
        db.execute(text("SELECT 1"))
        checks["db"] = "ok"
    except Exception as e:
        logger.warning("数据库就绪检查失败: %s", e)
        checks["db"] = "fail"
    try:
        if settings.REDIS_ENABLED:
            import redis as _redis_mod  # type: ignore
            r = _redis_mod.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=getattr(settings, "REDIS_PASSWORD", None) or None,
                socket_timeout=2,
            )
            r.ping()
            checks["redis"] = "ok"
        else:
            checks["redis"] = "disabled"
    except Exception as e:
        logger.warning("Redis 就绪检查失败: %s", e)
        checks["redis"] = "fail"
    all_ok = all(v in ("ok", "disabled") for v in checks.values())
    if not all_ok:
        body = {
            "code": 503,
            "message": "服务未就绪",
            "data": {"status": "not_ready", "checks": checks},
        }
        return JSONResponse(status_code=503, content=body)

    return APIResponse.success(
        data={"status": "ready", "checks": checks},
    )
