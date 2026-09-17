# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
任务控制相关的领域事件定义。

此模块提供强类型的事件数据类（dataclass）及其转换逻辑，
使得事件消费者能通过标准数据结构获取上下文，而不是操作原始的 dict。
"""
from typing import Any, Dict, Optional
from dataclasses import dataclass
from app.core.event_bus import Event, EventTypes, subscribe

@dataclass
class TaskEventPayload:
    task_id: str
    task_type: str
    status: str
    tenant_id: str
    trace_id: Optional[str] = None
    
    @classmethod
    def from_event(cls, event: Event) -> "TaskEventPayload":
        return cls(
            task_id=event.data.get("task_id", ""),
            task_type=event.data.get("task_type", ""),
            status=event.data.get("status", ""),
            tenant_id=event.data.get("tenant_id", ""),
            trace_id=event.trace_id,
        )

@dataclass
class TaskCompletedPayload(TaskEventPayload):
    tokens_used: int = 0
    cost: float = 0.0
    duration_ms: int = 0
    model_name: Optional[str] = None
    
    @classmethod
    def from_event(cls, event: Event) -> "TaskCompletedPayload":
        return cls(
            task_id=event.data.get("task_id", ""),
            task_type=event.data.get("task_type", ""),
            status=event.data.get("status", ""),
            tenant_id=event.data.get("tenant_id", ""),
            trace_id=event.trace_id,
            tokens_used=event.data.get("tokens_used", 0),
            cost=event.data.get("cost", 0.0),
            duration_ms=event.data.get("duration_ms", 0),
            model_name=event.data.get("model_name"),
        )

@dataclass
class TaskFailedPayload(TaskEventPayload):
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    duration_ms: int = 0
    
    @classmethod
    def from_event(cls, event: Event) -> "TaskFailedPayload":
        return cls(
            task_id=event.data.get("task_id", ""),
            task_type=event.data.get("task_type", ""),
            status=event.data.get("status", ""),
            tenant_id=event.data.get("tenant_id", ""),
            trace_id=event.trace_id,
            error_code=event.data.get("error_code"),
            error_message=event.data.get("error_message"),
            duration_ms=event.data.get("duration_ms", 0),
        )

# =====================================================================
# 示例：解耦的消费者（后续可将此类逻辑剥离出 TaskControlService）
# =====================================================================
import logging

log = logging.getLogger(__name__)

@subscribe(EventTypes.TASK_COMPLETED)
async def on_task_completed(event: Event) -> None:
    """任务完成事件的独立处理器，示范事件驱动解耦。"""
    payload = TaskCompletedPayload.from_event(event)
    log.info(
        "[TaskEvents] 任务已完成：task_id=%s, type=%s, tokens=%s, cost=%s", 
        payload.task_id, payload.task_type, payload.tokens_used, payload.cost
    )
    # 在这里可以解耦地触发：通知服务、后续数据处理管线、Webhook 回调等

@subscribe(EventTypes.TASK_FAILED)
async def on_task_failed(event: Event) -> None:
    """任务失败事件的独立处理器，示范事件驱动解耦。"""
    payload = TaskFailedPayload.from_event(event)
    log.warning(
        "[TaskEvents] 任务执行失败：task_id=%s, error=%s, msg=%s",
        payload.task_id, payload.error_code, payload.error_message
    )
