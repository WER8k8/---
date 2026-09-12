"""
Talking-Stick 任务队列
负责管理扫描任务的排队和执行
"""

import asyncio
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class TaskStatus(Enum):
    """任务状态"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """任务信息"""
    task_id: str
    target_path: str
    options: Dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.QUEUED
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class TaskQueue:
    """任务队列管理器"""
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._tasks: Dict[str, Task] = {}
        self._queue: asyncio.Queue = asyncio.Queue()
        self._running: bool = False
    
    async def enqueue(self, task_id: str, target_path: str, options: Dict[str, Any] = None) -> Task:
        """将任务加入队列"""
        task = Task(
            task_id=task_id,
            target_path=target_path,
            options=options or {}
        )
        self._tasks[task_id] = task
        await self._queue.put(task)
        return task
    
    async def dequeue(self) -> Optional[Task]:
        """从队列中取出任务"""
        try:
            task = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            return task
        except asyncio.TimeoutError:
            return None
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务信息"""
        return self._tasks.get(task_id)
    
    def update_task_status(self, task_id: str, status: TaskStatus, result: Dict[str, Any] = None, error: str = None) -> None:
        """更新任务状态"""
        if task_id not in self._tasks:
            raise ValueError(f"任务不存在: {task_id}")
        
        task = self._tasks[task_id]
        task.status = status
        if status == TaskStatus.RUNNING:
            task.started_at = datetime.now()
        elif status == TaskStatus.COMPLETED:
            task.completed_at = datetime.now()
            task.result = result
        elif status == TaskStatus.FAILED:
            task.completed_at = datetime.now()
            task.error = error
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        if task_id not in self._tasks:
            return {"error": "任务不存在"}
        
        task = self._tasks[task_id]
        return {
            "task_id": task.task_id,
            "status": task.status.value,
            "target_path": task.target_path,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "has_result": task.result is not None,
            "error": task.error
        }
    
    def get_all_tasks(self) -> list:
        """获取所有任务"""
        return [
            {
                "task_id": task.task_id,
                "status": task.status.value,
                "target_path": task.target_path,
                "created_at": task.created_at.isoformat()
            }
            for task in self._tasks.values()
        ]
    
    def clear_completed_tasks(self) -> int:
        """清理已完成的任务"""
        completed_tasks = [
            task_id for task_id, task in self._tasks.items()
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
        ]
        for task_id in completed_tasks:
            del self._tasks[task_id]
        
        return len(completed_tasks)
    
    @property
    def queue_size(self) -> int:
        """队列大小"""
        return self._queue.qsize()
    
    @property
    def task_count(self) -> int:
        """任务总数"""
        return len(self._tasks)
