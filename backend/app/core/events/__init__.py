"""
领域事件定义模块。
"""
from app.core.events.task_events import (
    TaskEventPayload,
    TaskCompletedPayload,
    TaskFailedPayload,
)

__all__ = [
    "TaskEventPayload",
    "TaskCompletedPayload",
    "TaskFailedPayload",
]
