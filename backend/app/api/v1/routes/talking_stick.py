"""
Talking-Stick 安全扫描API
提供漏洞扫描任务的提交、状态查询、结果获取等接口
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from ....services.talking_stick.config import ConfigManager
from ....services.talking_stick.scheduler import Scheduler

router = APIRouter()

# 全局调度器实例
_scheduler: Optional[Scheduler] = None


def get_scheduler() -> Scheduler:
    """获取调度器实例"""
    global _scheduler
    if _scheduler is None:
        config_manager = ConfigManager()
        _scheduler = Scheduler(config_manager)
    return _scheduler


class ScanRequest(BaseModel):
    """扫描请求"""
    target_path: str = Field(..., description="扫描目标路径")
    options: Optional[Dict[str, Any]] = Field(default=None, description="扫描选项")


class ScanResponse(BaseModel):
    """扫描响应"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    message: str = Field(..., description="消息")


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    status: str
    target_path: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    has_result: bool = False
    error: Optional[str] = None


@router.post("/scan", response_model=ScanResponse, tags=["Talking-Stick安全扫描"])
async def submit_scan_task(request: ScanRequest, background_tasks: BackgroundTasks):
    """提交安全扫描任务"""
    try:
        scheduler = get_scheduler()
        task_id = await scheduler.submit_scan_task(request.target_path, request.options)
        return ScanResponse(
            task_id=task_id,
            status="queued",
            message=f"扫描任务已提交，任务ID: {task_id}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提交扫描任务失败: {str(e)}")


@router.get("/scan/{task_id}/status", response_model=TaskStatusResponse, tags=["Talking-Stick安全扫描"])
async def get_scan_status(task_id: str):
    """获取扫描任务状态"""
    try:
        scheduler = get_scheduler()
        status = await scheduler.get_task_status(task_id)
        if "error" in status:
            raise HTTPException(status_code=404, detail=status["error"])
        
        return TaskStatusResponse(**status)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务状态失败: {str(e)}")


@router.get("/scan/{task_id}/result", tags=["Talking-Stick安全扫描"])
async def get_scan_result(task_id: str):
    """获取扫描任务结果"""
    try:
        scheduler = get_scheduler()
        result = await scheduler.get_task_result(task_id)
        if result is None:
            raise HTTPException(status_code=404, detail="任务未完成或不存在")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务结果失败: {str(e)}")


@router.delete("/scan/{task_id}", tags=["Talking-Stick安全扫描"])
async def cancel_scan_task(task_id: str):
    """取消扫描任务"""
    try:
        scheduler = get_scheduler()
        success = await scheduler.cancel_task(task_id)
        if not success:
            raise HTTPException(status_code=400, detail="任务无法取消（可能已开始执行或不存在）")
        
        return {"message": "任务已取消", "task_id": task_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取消任务失败: {str(e)}")


@router.get("/scans", tags=["Talking-Stick安全扫描"])
async def list_all_scans():
    """列出所有扫描任务"""
    try:
        scheduler = get_scheduler()
        tasks = await scheduler.get_all_tasks()
        return {"tasks": tasks, "total": len(tasks)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")


@router.delete("/scans/completed", tags=["Talking-Stick安全扫描"])
async def clear_completed_scans():
    """清理已完成的扫描任务"""
    try:
        scheduler = get_scheduler()
        cleared = await scheduler.clear_completed_tasks()
        return {"message": f"已清理 {cleared} 个已完成任务", "cleared_count": cleared}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理任务失败: {str(e)}")


@router.get("/health", tags=["Talking-Stick安全扫描"])
async def health_check():
    """Talking-Stick健康检查"""
    return {
        "status": "healthy",
        "service": "talking-stick",
        "version": "1.0.0"
    }


ROUTE_PREFIX = "/talking-stick"
ROUTE_TAGS = ["Talking-Stick安全扫描"]