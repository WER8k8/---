# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
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
