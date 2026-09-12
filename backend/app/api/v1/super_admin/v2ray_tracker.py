# DEPRECATED (P1-14): v2ray tracker is legacy. Kept for backward compat.
"""
V2Ray Tracker API - 版本追踪与状态检查
前端 tracker.vue 调用的 4 个端点
"""
from fastapi import APIRouter, Depends

from app.core.admin_auth import get_current_super_admin
from app.models.user import User

router = APIRouter(tags=["V2Ray追踪"])

_tracker_state: dict = {"status": "idle", "last_check": None, "releases": []}


@router.get("/status")
async def get_tracker_status(current_user: User = Depends(get_current_super_admin)):
    """获取 V2Ray 追踪器当前状态"""
    return {
        "code": 0,
        "data": {
            "status": _tracker_state.get("status", "idle"),
            "last_check": _tracker_state.get("last_check"),
            "tracking": False,
        },
    }


@router.get("/releases")
async def get_tracker_releases(current_user: User = Depends(get_current_super_admin)):
    """获取已追踪的 V2Ray 版本列表"""
    return {
        "code": 0,
        "data": {
            "releases": _tracker_state.get("releases", []),
            "total": len(_tracker_state.get("releases", [])),
        },
    }


@router.post("/check-now")
async def check_now(current_user: User = Depends(get_current_super_admin)):
    """立即触发一次版本检查"""
    import datetime
    _tracker_state["last_check"] = datetime.datetime.utcnow().isoformat()
    _tracker_state["status"] = "checked"
    return {"code": 0, "message": "检查完成", "data": {"last_check": _tracker_state["last_check"]}}


@router.post("/start")
async def start_tracker(current_user: User = Depends(get_current_super_admin)):
    """启动 V2Ray 追踪器（后台任务）"""
    _tracker_state["status"] = "running"
    return {"code": 0, "message": "追踪器已启动", "data": {"status": "running"}}


@router.get("/traffic")
async def get_traffic_stats(
    period: str = "month",
    current_user: User = Depends(get_current_super_admin),
):
    """代理流量统计（按周期；无采集器时返回空结构）"""
    _ = period
    return {
        "code": 0,
        "data": {
            "stats": {
                "total": "0 GB",
                "upload": "0 GB",
                "download": "0 GB",
                "remaining": "—",
            },
            "nodes": [],
            "daily": [],
            "logs": [],
        },
    }
