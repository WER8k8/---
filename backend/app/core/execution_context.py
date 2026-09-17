# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Skill 执行上下文（移植自 Trade AI Agent `app/core/context.py`，MIT，保留出处）。

改造点（合并红线）：
- 注入 tenant_id（原版仅 user_id，全库 0 个 tenant_id）；适用 Counters/隔离查找。
- datetime 统一 timezone-aware（原版 utcnow naive），对齐本库模型约定。
- 保留 pause/resume（PAUSED 语义），供 ai_tasks 状态机扩展对照。
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Optional


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ExecutionContext:
    """在 Skill 与工作流步骤间传递的执行上下文。"""

    workflow_id: str
    execution_id: str
    user_id: Optional[int] = None
    tenant_id: Optional[str] = None  # 合并红线：租户隔离

    current_step: Optional[str] = None
    step_history: list = field(default_factory=list)

    input_data: dict = field(default_factory=dict)
    output_data: dict = field(default_factory=dict)
    shared_state: dict = field(default_factory=dict)

    started_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)
    completed_at: Optional[datetime] = None

    status: str = "running"  # running, paused, completed, failed
    error_message: Optional[str] = None
    error_stack: Optional[str] = None

    interrupted: bool = False
    interrupt_reason: Optional[str] = None

    metrics: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        data = asdict(self)
        for key in ("started_at", "updated_at", "completed_at"):
            v = data.get(key)
            if isinstance(v, datetime):
                data[key] = v.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "ExecutionContext":
        for key in ("started_at", "updated_at", "completed_at"):
            v = data.get(key)
            if v and isinstance(v, str):
                data[key] = datetime.fromisoformat(v)
        return cls(**data)

    def update_timestamp(self) -> None:
        self.updated_at = _now()

    def add_step(self, step_name: str) -> None:
        self.step_history.append({"step": step_name, "timestamp": _now().isoformat()})
        self.current_step = step_name
        self.update_timestamp()

    def set_input(self, key: str, value: Any) -> None:
        self.input_data[key] = value
        self.update_timestamp()

    def set_output(self, key: str, value: Any) -> None:
        self.output_data[key] = value
        self.update_timestamp()

    def set_state(self, key: str, value: Any) -> None:
        self.shared_state[key] = value
        self.update_timestamp()

    def get_state(self, key: str, default: Any = None) -> Any:
        return self.shared_state.get(key, default)

    def increment_metric(self, metric: str, value: int = 1) -> None:
        self.metrics[metric] = self.metrics.get(metric, 0) + value

    def set_error(self, message: str, stack: Optional[str] = None) -> None:
        self.status = "failed"
        self.error_message = message
        self.error_stack = stack
        self.update_timestamp()

    def complete(self) -> None:
        self.status = "completed"
        self.completed_at = _now()
        self.update_timestamp()

    def pause(self, reason: Optional[str] = None) -> None:
        self.status = "paused"
        self.interrupted = True
        self.interrupt_reason = reason
        self.update_timestamp()

    def resume(self) -> None:
        self.status = "running"
        self.interrupted = False
        self.interrupt_reason = None
        self.update_timestamp()

    def to_json(self) -> str:
        import json

        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)