"""系统健康与压测路由 - 模块化架构"""

import logging
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/system-health"
ROUTE_TAGS = ["系统健康压测"]

router = APIRouter()

_stress_history: list[dict] = []


def _read_resource_usage() -> dict[str, float]:
    """执行 read_resource_usage 相关逻辑处理。
    :return: 返回处理结果。
    """
    import psutil
    disk_path = "C:\\" if os.name == "nt" else "/"
    try:
        disk_pct = psutil.disk_usage(disk_path).percent
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning("获取磁盘使用率失败: %s", e)
        disk_pct = 0.0
    return {
        "cpu_usage_percent": round(psutil.cpu_percent(interval=0.1), 1),
        "memory_usage_percent": round(psutil.virtual_memory().percent, 1),
        "disk_usage_percent": round(disk_pct, 1),
    }


@router.get("/")
def get_system_health_overview(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """获取系统健康概览（真实探测）"""
    if current_user.role not in ["admin", "super_admin"]:
        return error_response(403, "权限不足")

    usage = _read_resource_usage()
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning("数据库健康检查失败: %s", e)
        db_ok = False

    return success_response(
        data={
            "status": "healthy" if db_ok else "degraded",
            "database": "ok" if db_ok else "fail",
            "environment": settings.ENVIRONMENT,
            **usage,
        }
    )


@router.get("/cache-stats")
def get_cache_stats(
        current_user: User = Depends(get_current_user)):
    """FIX-24: 三级缓存统计（L1 + L2 + L3 状态）"""
    if current_user.role not in ["admin", "super_admin"]:
        return error_response(403, "权限不足")

    from app.core.cache import l1_cache_stats, redis_available
    l1 = l1_cache_stats()
    l2 = redis_available(force_check=True)
    l3 = settings.CDN_ENABLED if hasattr(settings, "CDN_ENABLED") else False
    return success_response(
        data={
            "l1_process": {
                "enabled": True,
                "size": l1["size"],
                "active": l1["active"],
                "max": l1["max"],
                "latency": "<1ms",
            },
            "l2_redis": {
                "enabled": l2,
                "latency": "<5ms" if l2 else "N/A",
            },
            "l3_cdn": {
                "enabled": l3,
                "recommendation": "生产环境建议启用 Cloudflare CDN 全站加速",
            },
            "hierarchy": "L1(进程内 LRU) → L2(Redis) → L3(CDN) → DB",
        }
    )


@router.get("/audit-logs")
def get_audit_logs(
        limit: int = 100,
        current_user: User = Depends(get_current_user)):
    """FIX-26: 敏感数据访问审计日志"""
    if current_user.role not in ["admin", "super_admin"]:
        return error_response(403, "权限不足")

    from app.core.data_classification import get_recent_audit_logs
    logs = get_recent_audit_logs(limit=min(limit, 500))
    return success_response(data={
        "total": len(logs),
        "logs": logs,
        "note": "内存审计日志（生产环境需替换为数据库存储）",
    })


@router.get("/stress-test")
def get_stress_test_status(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """获取压测状态"""
    if current_user.role not in ["admin", "super_admin"]:
        return error_response(403, "权限不足")
    return success_response(
        data={
            "last_test_time": _stress_history[0]["time"] if _stress_history else None,
            "max_concurrent_users": 0,
            "avg_response_time_ms": 0,
            "error_rate_percent": 0,
            "test_history": _stress_history,
            "data_source": "history_only",
        }
    )


@router.post("/stress-test")
def run_stress_test(
        req: dict,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """启动压力测试（记录任务，真实压测由 Locust 执行）"""
    if current_user.role not in ["super_admin"]:
        return error_response(403, "权限不足")
    concurrency = int(req.get("concurrency") or 50)
    entry = {
        "id": len(_stress_history) + 1,
        "name": f"{req.get('method', 'GET')} {req.get('url', '/api/v1/health')}",
        "url": req.get("url", ""),
        "concurrency": concurrency,
        "time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "status": "queued",
        "result": None,
        "note": "已排队；真实压测请使用 Locust 脚本执行",
    }
    _stress_history.insert(0, entry)
    return success_response(
        data={"test_id": f"stress-{entry['id']}", "status": "queued", "config": req},
        message="压测任务已记录，请使用 Locust 执行真实压测")


@router.get("/resource-monitor")
def get_resource_monitor(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """获取资源监控数据"""
    if current_user.role not in ["admin", "super_admin"]:
        return error_response(403, "权限不足")
    usage = _read_resource_usage()
    return success_response(
        data={
            **usage,
            "cpu_history": [],
            "memory_history": [],
            "disk_history": [],
            "network_history": [],
            "data_source": "psutil_snapshot",
        })


@router.get("/backup")
def get_backup_status(db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    """获取备份状态"""
    if current_user.role not in ["admin", "super_admin"]:
        return error_response(403, "权限不足")
    return success_response(
        data={
            "last_backup_time": None,
            "backup_size_mb": 0,
            "backup_count": 0,
            "next_scheduled": None,
            "backups": [],
            "stats": [
                {"label": "成功备份", "value": 0, "suffix": "次", "color": "#22c55e"},
                {"label": "备份总大小", "value": 0, "suffix": "GB", "color": "#3b82f6"},
            ],
            "data_source": "empty",
        })


@router.post("/backup")
def trigger_backup(db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    """触发立即备份"""
    if current_user.role not in ["super_admin"]:
        return error_response(403, "权限不足")
    return success_response(data={"status": "not_configured"}, message="备份任务未配置，请联系运维")


@router.post("/backup/restore")
def restore_backup(req: dict, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    """回滚恢复"""
    if current_user.role not in ["super_admin"]:
        return error_response(403, "权限不足")
    return error_response(501, "备份恢复未接入")
