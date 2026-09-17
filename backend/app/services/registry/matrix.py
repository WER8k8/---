# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Skill 运行态 × 发布态 映射矩阵（轮17-5）。

Trade AI BaseSkill 使用运行态（SKILL_STATUS，5 态：pending/running/success/
failed/skipped），skills 表使用发布态（status，5 态：draft/testing/active/
disabled/rollback）。二者正交：运行态描述"某次执行的当前阶段"，发布态描述
"该 Skill 版本是否已发布且允许被调度"。

- 仅 active 的发布态允许创建运行实例；
- 运行态 success/failed/skipped 是终态；running/pending 是执行中；
- rollback 发布态强制终止运行实例。
"""

from __future__ import annotations

from enum import Enum

# Trade AI BaseSkill 运行态（skill_base.py SkillStatus 对齐）
class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

    @classmethod
    def terminal(cls) -> set[str]:
        return {cls.SUCCESS.value, cls.FAILED.value, cls.SKIPPED.value}

    @classmethod
    def active(cls) -> set[str]:
        return {cls.PENDING.value, cls.RUNNING.value}


# 发布态（skills.status / Skill 生命周期，§1.2-4：Draft→评估→Canary→人审）
class PublishStatus(str, Enum):
    DRAFT = "draft"
    TESTING = "testing"
    ACTIVE = "active"
    DISABLED = "disabled"
    ROLLBACK = "rollback"

    @classmethod
    def schedulable(cls) -> set[str]:
        return {cls.ACTIVE.value, cls.TESTING.value}


# ---------------------------------------------------------------------------
# 映射矩阵
# ---------------------------------------------------------------------------

# 运行态 → 是否允许在给定发布态下创建新执行
# 规则：
#   - pending/running 之外的发布态，允许启动新执行；
#   - active/testing 才允许调度；draft/disabled 不允许；rollback 终止。
_ALLOW_START_BY_PUBLISH: dict[str, bool] = {
    PublishStatus.ACTIVE.value: True,
    PublishStatus.TESTING.value: True,
    PublishStatus.DRAFT.value: False,
    PublishStatus.DISABLED.value: False,
    PublishStatus.ROLLBACK.value: False,
}

# 发布态 → 对"正在运行实例"的处置
#   - rollback/disabled：强制终止运行（run → skipped，模拟取消）；
#   - active/testing：保留；
#   - draft：仅测试性运行可保留，生产运行视为非法。
_ACTION_ON_RUNNING: dict[str, str] = {
    PublishStatus.ACTIVE.value: "keep",
    PublishStatus.TESTING.value: "keep",
    PublishStatus.DRAFT.value: "testing_only",
    PublishStatus.DISABLED.value: "terminate",
    PublishStatus.ROLLBACK.value: "terminate",
}


def _allow(pub: str, run: RunStatus) -> bool:
    """发布态下运行态是否合法。

    规则：
    - success/failed/skipped（终态）在 roleback/disabled/draft 下不合法
      （终态只该出现在 active/testing 执行完成之后）。
    - pending/running 仅在 active/testing 下启动（start 判定单独走
      ALLOW_START_BY_PUBLISH）。
    """
    if run.value in RunStatus.terminal():
        return pub in (PublishStatus.ACTIVE.value, PublishStatus.TESTING.value)
    return _ALLOW_START_BY_PUBLISH.get(pub, False)


# SkillStatus × Status 12 格矩阵（含"是否允许"判定）
MATRIX: dict[str, dict[str, bool]] = {
    pub: {run: _allow(pub, run) for run in RunStatus}
    for pub in PublishStatus
}


def can_start(publish_status: str) -> bool:
    """给定发布态是否允许创建新执行实例。"""
    return _ALLOW_START_BY_PUBLISH.get(publish_status, False)


def action_on_running(publish_status: str) -> str:
    """返回对运行实例的处置动作：keep / testing_only / terminate。"""
    return _ACTION_ON_RUNNING.get(publish_status, "testing_only")


def publish_transition(current: str, target: str) -> bool:
    """发布态合法跃迁校验（§1.2-4）：

    draft -> testing -> active；active -> disabled；disabled -> active；
    active -> rollback；rollback -> disabled 后回收。
    """
    transitions = {
        PublishStatus.DRAFT.value: {PublishStatus.TESTING.value},
        PublishStatus.TESTING.value: {PublishStatus.ACTIVE.value, PublishStatus.DISABLED.value},
        PublishStatus.ACTIVE.value: {PublishStatus.DISABLED.value, PublishStatus.ROLLBACK.value},
        PublishStatus.DISABLED.value: {PublishStatus.ACTIVE.value},
        PublishStatus.ROLLBACK.value: set(),
    }
    return target in transitions.get(current, set())


__all__ = ["RunStatus", "PublishStatus", "MATRIX", "can_start", "action_on_running", "publish_transition"]