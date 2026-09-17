# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""统一 Trace / 经验飞轮接线（总纲 §4.6-7 / §6.6 P3）。

- trace_service：task_traces 链式追踪读写 + 记分卡聚合。
- terminal_hook：终态钩子 → EvolutionTaskRecord + 失败经验分级入库 + 记分卡。
- publish_gate：Canary 发布门禁（Draft→评估→Canary 5/25/50/100%→人审→Production）。
"""

from app.services.trace.trace_service import TaskTraceService
from app.services.trace.terminal_hook import (
    EXPERIENCE_STAGE_ORDER,
    promote_experience_stage,
    record_terminal_state,
)
from app.services.trace.publish_gate import CANARY_STEPS, PublishGate

__all__ = [
    "TaskTraceService",
    "record_terminal_state",
    "promote_experience_stage",
    "EXPERIENCE_STAGE_ORDER",
    "PublishGate",
    "CANARY_STEPS",
]
