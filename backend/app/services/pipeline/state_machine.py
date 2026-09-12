"""流水线状态机（总纲 §6.5：11 态）。

主链：generated→cleansing→cleansed→reviewing→approved→distributing→verifying→done
异常支路：任何活动态可转 failed / wait_human；reviewing/wait_human 可转 retrying；
retrying 回到 cleansing（重新过清洗关）或分发失败回 distributing。
红线：重试 ≤3 次，超限只能转 wait_human（§4.8/R6）；终态不可再转移。
"""

from __future__ import annotations

from typing import Dict, FrozenSet

# 与迁移 090 的 RUN_STATUSES 严格一致
GENERATED = "generated"
CLEANSING = "cleansing"
CLEANING = CLEANSING  # 别名：下文转移表使用 CLEANING 命名
CLEANSED = "cleansed"
REVIEWING = "reviewing"
APPROVED = "approved"
DISTRIBUTING = "distributing"
VERIFYING = "verifying"
DONE = "done"
FAILED = "failed"
WAIT_HUMAN = "wait_human"
RETRYING = "retrying"

ALL_STATUSES: FrozenSet[str] = frozenset(
    (GENERATED, CLEANING, CLEANSED, REVIEWING, APPROVED,
     DISTRIBUTING, VERIFYING, DONE, FAILED, WAIT_HUMAN, RETRYING)
)

TERMINAL_STATUSES: FrozenSet[str] = frozenset({DONE, FAILED})

TRANSITIONS: Dict[str, FrozenSet[str]] = {
    GENERATED: frozenset({CLEANSING, FAILED}),
    CLEANING: frozenset({CLEANSED, FAILED, WAIT_HUMAN}),
    CLEANSED: frozenset({REVIEWING, FAILED}),
    REVIEWING: frozenset({APPROVED, WAIT_HUMAN, FAILED}),
    WAIT_HUMAN: frozenset({APPROVED, FAILED, RETRYING}),
    APPROVED: frozenset({DISTRIBUTING, FAILED}),
    DISTRIBUTING: frozenset({VERIFYING, RETRYING, WAIT_HUMAN, FAILED}),
    RETRYING: frozenset({CLEANSING, DISTRIBUTING, WAIT_HUMAN, FAILED}),
    VERIFYING: frozenset({DONE, RETRYING, FAILED}),
    DONE: frozenset(),
    FAILED: frozenset(),
}

MAX_RETRY = 3  # §4.8/R6：有界重试


class InvalidTransition(Exception):
    """非法状态转移（含越权重试）。"""
    def __init__(self, current: str, target: str, reason: str = ""):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param current: 参数 current
        :param target: 参数 target
        :param reason: 参数 reason
        :return: 返回处理结果。
        """
        self.current = current
        self.target = target
        super().__init__(
            f"非法转移 {current} -> {target}" + (f"（{reason}）" if reason else "")
        )


def can_transition(current: str, target: str) -> bool:
    """can_transition。

    参数说明：
    :param current: 参数 current
    :param target: 参数 target
    :return: 返回处理结果。
    """
    if current not in TRANSITIONS:
        return False
    return target in TRANSITIONS[current]


def apply_transition(current: str, target: str, retry_count: int = 0) -> str:
    """校验并返回新状态；非法即抛 InvalidTransition。

    retry_count 语义：已经发生的重试次数。转入 RETRYING 前必须 < MAX_RETRY，
    否则只能走 WAIT_HUMAN（人工介入，禁止无限重试）。
    """
    if current not in TRANSITIONS:
        raise InvalidTransition(current, target, "未知状态")
    if target not in TRANSITIONS[current]:
        raise InvalidTransition(current, target)
    if target == RETRYING and retry_count >= MAX_RETRY:
        raise InvalidTransition(
            current, target, f"重试已达上限 {MAX_RETRY} 次，必须转 wait_human"
        )
    return target


def main_path() -> list:
    """主链顺序（供测试与文档一致性校验）。"""
    return [GENERATED, CLEANING, CLEANSED, REVIEWING, APPROVED,
            DISTRIBUTING, VERIFYING, DONE]
