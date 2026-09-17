# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Hermes 巡站维护宪法 — 底层写死：只维护、不破坏。

任何维护动作须经 assert_maintenance_action 校验；禁止类动作在编译期常量中冻结。
"""

from __future__ import annotations

from typing import Any, Final

# ── 允许的动作（白名单，不可运行时扩展）────────────────────────────
ALLOWED_MAINTENANCE_ACTIONS: Final[frozenset[str]] = frozenset(
    {
        "read_probe",  # 只读探测（DB SELECT / GET 健康端点 / 加载快照）
        "write_patrol_snapshot",  # 仅写入巡站快照键（SystemSetting 单键）
        "emit_alert",  # 日志 / 内存告警队列（不写业务表）
        "suggest_remediation",  # 文本建议，不执行
    }
)

# ── 禁止的动作前缀（黑名单，命中即违宪）────────────────────────────
FORBIDDEN_ACTION_PREFIXES: Final[tuple[str, ...]] = (
    "delete_",
    "drop_",
    "truncate_",
    "remove_",
    "destroy_",
    "purge_",
    "update_",
    "mutate_",
    "patch_",
    "insert_",
    "create_",
    "send_",
    "publish_",
    "post_",
    "put_",
    "bill_",
    "charge_",
    "refund_",
    "freeze_",
    "unfreeze_",
    "migrate_",
    "seed_",
    "exec_",
    "shell_",
    "run_worker_",
    "auto_fix_",
    "auto_repair_",
)

FORBIDDEN_EXACT_ACTIONS: Final[frozenset[str]] = frozenset(
    {
        "write",
        "execute",
        "deploy",
        "restart",
        "rollback",
        "reboot",
        "flush",
        "kill",
    }
)

CONSTITUTION_VERSION: Final[str] = "2026-06-03-v1"

CONSTITUTION_SUMMARY: Final[str] = (
    "Hermes 巡站仅允许：只读探测、写入巡站快照、记录告警、输出修复建议。"
    "禁止：删改业务数据、改配置、发信/发布/扣费、执行迁移或任何自动修代码。"
)


class HermesMaintenanceViolation(Exception):
    """违反维护宪法。"""
    def __init__(self, action: str, reason: str):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param action: 参数 action
        :param reason: 参数 reason
        :return: 返回处理结果。
        """
        self.action = action
        self.reason = reason
        super().__init__(f"维护违宪 [{action}]: {reason}")


def is_action_forbidden(action: str) -> str | None:
    """若禁止则返回原因，否则 None。"""
    key = (action or "").strip().lower()
    if not key:
        return "空动作"
    if key in FORBIDDEN_EXACT_ACTIONS:
        return "精确禁止动作"
    for prefix in FORBIDDEN_ACTION_PREFIXES:
        if key.startswith(prefix):
            return f"禁止前缀 {prefix!r}"
    if key not in ALLOWED_MAINTENANCE_ACTIONS:
        return "不在维护白名单"
    return None


def assert_maintenance_action(action: str) -> None:
    """执行前强制校验；违宪抛 HermesMaintenanceViolation。"""
    reason = is_action_forbidden(action)
    if reason:
        raise HermesMaintenanceViolation(action, reason)


def constitution_payload() -> dict[str, Any]:
    """constitution_payload。
    :return: 返回处理结果。
    """
    return {
        "version": CONSTITUTION_VERSION,
        "summary": CONSTITUTION_SUMMARY,
        "allowed_actions": sorted(ALLOWED_MAINTENANCE_ACTIONS),
        "forbidden_prefixes": list(FORBIDDEN_ACTION_PREFIXES),
        "forbidden_exact": sorted(FORBIDDEN_EXACT_ACTIONS),
        "immutable": True,
    }
