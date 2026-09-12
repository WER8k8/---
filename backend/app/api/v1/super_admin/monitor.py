"""系统监控 & 运维接口"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.admin_auth import get_current_super_admin
from app.core.cache import (delete_pattern, invalidate_system_monitor_cache,
                             redis_client)
from app.core.database import get_db
from app.core.response import success_response
from app.models.user import User

router = APIRouter()


@router.get("/system")
def get_system_info(
    admin: User = Depends(get_current_super_admin),
):
    """系统信息"""
    import os
    import sys
    import platform
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
    except ImportError:
        cpu_percent = 0
        memory = type("obj", (object,), {"percent": 0, "total": 0, "used": 0})()
        disk = type("obj", (object,), {"percent": 0, "total": 0, "used": 0})()

    return success_response(data={
        "cpu": {
            "percent": cpu_percent,
            "cores": os.cpu_count(),
        },
        "memory": {
            "percent": memory.percent,
            "total_mb": round(memory.total / 1024 / 1024, 1),
            "used_mb": round(memory.used / 1024 / 1024, 1),
        },
        "disk": {
            "percent": disk.percent,
            "total_gb": round(disk.total / 1024 / 1024 / 1024, 1),
            "used_gb": round(disk.used / 1024 / 1024 / 1024, 1),
        },
        "python": {
            "version": sys.version,
            "platform": platform.platform(),
        },
    })


@router.get("/redis")
def get_redis_info(
    admin: User = Depends(get_current_super_admin),
):
    """Redis 状态"""
    if not redis_client:
        return success_response(data={"status": "未启用"})

    try:
        info = redis_client.info()
        return success_response(data={
            "status": "connected",
            "used_memory_mb": round(info.get("used_memory", 0) / 1024 / 1024, 1),
            "connected_clients": info.get("connected_clients", 0),
            "uptime_days": info.get("uptime_in_days", 0),
            "keys_count": redis_client.dbsize(),
            "version": info.get("redis_version", ""),
        })
    except Exception as e:
        return success_response(data={"status": "error", "error": str(e)})


@router.post("/cache/clear")
def clear_cache(
    admin: User = Depends(get_current_super_admin),
    pattern: Optional[str] = Query(None),
):
    """清除缓存（按模式匹配）"""
    if not redis_client:
        raise HTTPException(status_code=400, detail="Redis 未启用")

    if pattern:
        count = delete_pattern(pattern)
    else:
        # 清除所有管理后台缓存 (保留业务缓存)
        prefixes = ["perm:*", "menu:*", "admin:dashboard:*", "monitor:*", "rate:*"]
        count = 0
        for p in prefixes:
            count += delete_pattern(p)

    invalidate_system_monitor_cache()
    return success_response(data={"deleted_keys": count}, message=f"已清除 {count} 个缓存键")


@router.get("/cache/keys")
def list_cache_keys(
    admin: User = Depends(get_current_super_admin),
    pattern: str = Query("*"),
):
    """列出缓存键"""
    if not redis_client:
        return success_response(data=[])

    keys = list(redis_client.scan_iter(match=pattern, count=100))
    # 限制返回数量
    keys = keys[:100]
    return success_response(data=keys, total=len(keys))


@router.get("/ai-stats")
def get_ai_usage_detail(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
    days: int = Query(30, ge=1, le=365),
):
    """AI 用量详细统计"""
    from sqlalchemy import func
    from app.models.ai_config import AIUsageLog
    start = datetime.now(timezone.utc) - timedelta(days=days)
    # 按任务类型统计
    by_type = (
        db.query(
            AIUsageLog.task_type,
            func.count(AIUsageLog.id).label("count"),
            func.sum(AIUsageLog.success.cast(int)).label("success_count"),
        )
        .filter(AIUsageLog.created_at >= start)
        .group_by(AIUsageLog.task_type)
        .all()
    )
    # 按模型统计
    by_model = (
        db.query(
            AIUsageLog.model_name,
            func.count(AIUsageLog.id).label("count"),
        )
        .filter(AIUsageLog.created_at >= start)
        .group_by(AIUsageLog.model_name)
        .all()
    )
    return success_response(data={
        "period_days": days,
        "by_task_type": [
            {"type": r[0], "count": r[1], "success": r[2] or 0}
            for r in by_type
        ],
        "by_model": [
            {"model": r[0], "count": r[1]}
            for r in by_model
        ],
    })
