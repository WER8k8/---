# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""事件总线 + 事件驱动架构 — FIX-41

轻量级进程内事件总线，支持：
- 同步/异步事件发布订阅
- 事件优先级
- 事件溯源（可选）
- 通配符订阅
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

log = logging.getLogger(__name__)


class EventPriority(str, Enum):
    """事件优先级。"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Event:
    """事件基类。"""
    event_type: str
    data: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    priority: EventPriority = EventPriority.NORMAL
    source: str = ""
    trace_id: str = ""
    tenant_id: str = ""  # 租户隔离字段 — 多租户环境下标识事件归属


@dataclass
class EventEnvelope:
    """事件信封 — 包装事件并强制携带 tenant_id。

    用于跨服务/跨进程事件传递场景，确保事件的租户上下文不丢失。
    内部事件可直接使用 Event(tenant_id=...)，跨边界时使用 EventEnvelope。

    Example:
        envelope = EventEnvelope(
            event=Event(EventTypes.LEAD_CREATED, {"email": "a@b.com"}),
            tenant_id="tenant-uuid-123",
        )
    """
    event: Event
    tenant_id: str = ""
    def __post_init__(self):
        """同步 tenant_id 到内部 Event。"""
        if self.tenant_id and not self.event.tenant_id:
            self.event.tenant_id = self.tenant_id

    @property
    def event_type(self) -> str:
        """event_type。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return self.event.event_type

    @property
    def data(self) -> dict[str, Any]:
        """data。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return self.event.data

    @property
    def event_id(self) -> str:
        """event_id。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return self.event.event_id

    @property
    def timestamp(self) -> datetime:
        """timestamp。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return self.event.timestamp

    @property
    def priority(self) -> EventPriority:
        """priority。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return self.event.priority


# 事件类型常量
class EventTypes:
    """系统事件类型定义。"""
    # 获客事件
    LEAD_CREATED = "lead.created"
    LEAD_UPDATED = "lead.updated"
    LEAD_SCORED = "lead.scored"
    LEAD_VERIFIED = "lead.verified"
    LEAD_CONVERTED = "lead.converted"
    # 邮件事件
    EMAIL_SENT = "email.sent"
    EMAIL_OPENED = "email.opened"
    EMAIL_CLICKED = "email.clicked"
    EMAIL_REPLIED = "email.replied"
    EMAIL_BOUNCED = "email.bounced"
    # 用户事件
    USER_REGISTERED = "user.registered"
    USER_LOGIN = "user.login"
    USER_UPGRADED = "user.upgraded"
    USER_CHURNED = "user.churned"
    # 内容事件
    CONTENT_PUBLISHED = "content.published"
    SEO_UPDATED = "seo.updated"
    SITE_DEPLOYED = "site.deployed"
    # 任务生命周期事件
    TASK_CREATED = "task.created"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_RETRIED = "task.retried"
    TASK_CANCELLED = "task.cancelled"
    TASK_TIMEOUT = "task.timeout"
    TASK_PAUSED = "task.paused"
    TASK_RESUMED = "task.resumed"
    # 租户事件
    TENANT_CREATED = "tenant.created"
    TENANT_SUSPENDED = "tenant.suspended"
    TENANT_ACTIVATED = "tenant.activated"
    # 支付事件
    PAYMENT_SUCCEEDED = "payment.succeeded"
    PAYMENT_FAILED = "payment.failed"
    REFUND_PROCESSED = "refund.processed"
    # 系统事件
    SYSTEM_ERROR = "system.error"
    SYSTEM_WARNING = "system.warning"
    QUOTA_EXCEEDED = "quota.exceeded"
    CREDIT_LOW = "credit.low"


class EventBus:
    """轻量级事件总线。

    支持同步和异步处理器，按优先级排序执行。
    线程安全。

    用法:
        bus = EventBus()

        @bus.on(EventTypes.LEAD_CREATED)
        async def handle_new_lead(event: Event):
            await send_notification(event)

        await bus.emit(Event(EventTypes.LEAD_CREATED, {"email": "..."}))
    """
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._handlers: dict[str, list[tuple[Callable, str]]] = defaultdict(list)
        self._wildcard_handlers: list[tuple[str, Callable, str]] = []
        self._history: list[Event] = []  # 事件溯源
        self._max_history = 1000
        self._dead_letters: list[Event] = []  # 死信队列
        self._max_dlq = 1000

    def on(self, event_type: str, priority: int = 0, tenant_id: str = ""):
        """装饰器：注册事件处理器。

        Args:
            event_type: 事件类型，支持通配符 * 和 ?
            priority: 处理器优先级（越大越先执行）
            tenant_id: 租户 ID。为空则接收所有租户事件，非空则仅接收该租户事件。
        """
        def decorator(handler: Callable):
            """decorator。

            参数说明：
            :param handler: 参数 handler
            :return: 返回处理结果。
            """
            handler._event_priority = getattr(handler, "_event_priority", 0) + priority
            if "*" in event_type or "?" in event_type:
                self._wildcard_handlers.append((event_type, handler, tenant_id))
            else:
                self._handlers[event_type].append((handler, tenant_id))
            return handler
        return decorator

    def subscribe(self, event_type: str, handler: Callable, tenant_id: str = ""):
        """编程方式订阅事件。

        Args:
            event_type: 事件类型
            handler: 处理函数
            tenant_id: 租户 ID。为空则接收所有租户事件，非空则仅接收该租户事件。
        """
        self._handlers[event_type].append((handler, tenant_id))

    def unsubscribe(self, event_type: str, handler: Callable):
        """取消订阅。"""
        self._handlers[event_type] = [
            (h, tid) for (h, tid) in self._handlers[event_type] if h != handler
        ]
        self._wildcard_handlers = [
            (p, h, tid) for (p, h, tid) in self._wildcard_handlers if h != handler
        ]

    def _filter_handlers_by_tenant(
        self,
        handlers_with_tenant: list,
        event_tenant_id: str,
    ) -> list[Callable]:
        """根据 tenant_id 过滤处理器。

        规则:
        - 处理器 tenant_id 为空 -> 接收所有事件（平台级处理器）
        - 处理器 tenant_id 非空且与事件 tenant_id 匹配 -> 接收
        - 处理器 tenant_id 非空但不匹配 -> 过滤掉
        - 事件 tenant_id 为空 -> 仅平台级处理器接收
        """
        result = []
        for item in handlers_with_tenant:
            handler, handler_tenant_id = item[0], item[1] if len(item) > 1 else ""
            if not handler_tenant_id:
                # 平台级处理器：接收所有事件
                result.append(handler)
            elif not event_tenant_id:
                # 事件无租户上下文，仅平台级处理器接收
                continue
            elif handler_tenant_id == event_tenant_id:
                # 租户匹配
                result.append(handler)
        return result

    async def emit(self, event: Event) -> None:
        """发布事件（异步执行所有处理器，按租户过滤，handler 级失败隔离）。"""
        # 记录历史
        if len(self._history) >= self._max_history:
            self._history = self._history[-self._max_history // 2:]
        self._history.append(event)
        # 收集处理器（含 tenant_id 元组）
        raw_handlers = list(self._handlers.get(event.event_type, []))
        # 通配符匹配
        import fnmatch
        for pattern, handler, tid in self._wildcard_handlers:
            if fnmatch.fnmatch(event.event_type, pattern):
                raw_handlers.append((handler, tid))

        # 按租户过滤
        handlers = self._filter_handlers_by_tenant(raw_handlers, event.tenant_id)
        # 按 handler 自身优先级排序（越高越先执行）
        handlers.sort(key=lambda h: getattr(h, "_event_priority", 0), reverse=True)

        # 逐个执行，独立隔离（单个 handler 失败不影响其他）
        failed_count = 0
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                failed_count += 1
                handler_name = getattr(handler, "__name__", repr(handler))
                log.error(
                    "[EventBus] handler '%s' 处理事件 '%s' 失败 (event_id=%s): %s",
                    handler_name, event.event_type, event.event_id, e,
                    exc_info=True,
                )
                # 加入死信队列
                if len(self._dead_letters) >= self._max_dlq:
                    self._dead_letters.pop(0)
                self._dead_letters.append(event)

        if failed_count:
            log.warning(
                "[EventBus] 事件 '%s' (id=%s) 共 %d/%d handler 失败",
                event.event_type, event.event_id, failed_count, len(handlers),
            )

    def emit_sync(self, event: Event) -> None:
        """同步发布事件。"""
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(self.emit(event))
        else:
            loop.run_until_complete(self.emit(event))

    def get_dead_letters(self) -> list[Event]:
        """获取死信队列中的事件。"""
        return list(self._dead_letters)

    async def retry_dead_letters(self) -> dict[str, int]:
        """尝试重新处理死信队列中的事件。

        Returns:
            {"retried": int, "failed": int, "cleared": int}
        """
        if not self._dead_letters:
            return {"retried": 0, "failed": 0, "cleared": 0}

        retried = 0
        failed = 0
        still_failed = []
        for event in self._dead_letters:
            raw_handlers = list(self._handlers.get(event.event_type, []))
            import fnmatch
            for pattern, handler, tid in self._wildcard_handlers:
                if fnmatch.fnmatch(event.event_type, pattern):
                    raw_handlers.append((handler, tid))
            handlers = self._filter_handlers_by_tenant(raw_handlers, event.tenant_id)
            handlers.sort(key=lambda h: getattr(h, "_event_priority", 0), reverse=True)
            success = True
            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                except Exception as e:
                    log.error("[EventBus] 死信重试处理器 %s 失败: %s", handler.__name__, e)
                    success = False

            if success and handlers:
                retried += 1
            else:
                failed += 1
                still_failed.append(event)

        self._dead_letters = still_failed
        return {"retried": retried, "failed": failed, "cleared": len(still_failed)}

    def get_history(self, event_type: Optional[str] = None, limit: int = 50) -> list[Event]:
        """获取事件历史。"""
        if event_type:
            return [e for e in self._history if e.event_type == event_type][-limit:]
        return self._history[-limit:]

    def clear_history(self):
        """清空事件历史。"""
        self._history.clear()

    @property
    def handler_count(self) -> int:
        """处理器总数。"""
        return sum(len(h) for h in self._handlers.values()) + len(self._wildcard_handlers)


# 全局事件总线实例
event_bus = EventBus()


# ============================================================
# 预注册的系统事件处理器
# ============================================================

@event_bus.on(EventTypes.LEAD_CREATED)
async def _on_lead_created(event: Event):
    """新线索创建 → 自动评分。"""
    try:
        from app.services.ubrain.lead_scoring_engine import score_lead
        result = await score_lead(event.data)
        log.info("[EventBus] 新线索自动评分: %s → %.1f (%s)",
                 event.data.get("email"), result["score"], result["grade"])
    except Exception as e:
        log.warning("[EventBus] 自动评分失败: %s", e)


@event_bus.on(EventTypes.EMAIL_BOUNCED)
async def _on_email_bounced(event: Event):
    """邮件退信 → 标记线索无效。"""
    email = event.data.get("email", "")
    log.info("[EventBus] 邮件退信: %s, 原因: %s", email, event.data.get("reason", "unknown"))


@event_bus.on(EventTypes.CREDIT_LOW)
async def _on_credit_low(event: Event):
    """积分不足 → 提醒用户。"""
    user_id = event.data.get("user_id", "")
    remaining = event.data.get("remaining", 0)
    log.warning("[EventBus] 积分不足提醒: user=%s, remaining=%s", user_id, remaining)


@event_bus.on(EventTypes.USER_UPGRADED)
async def _on_user_upgraded(event: Event):
    """用户升级 → 发放欢迎积分。"""
    user_id = event.data.get("user_id", "")
    plan = event.data.get("plan", "")
    log.info("[EventBus] 用户升级: %s → %s", user_id, plan)


@event_bus.on(EventTypes.SYSTEM_ERROR, priority=100)
def handle_system_error(event: Event) -> None:
    """系统错误处理兜底。"""
    log.critical(
        "[System] 系统错误: %s, 详情: %s",
        event.data.get("message", "unknown"),
        event.data.get("error_code", "unknown"),
    )


# 为了更优雅的装饰器语法暴露的别名
subscribe = event_bus.on