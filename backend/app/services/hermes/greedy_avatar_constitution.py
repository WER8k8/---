# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""财迷疯分身宪法（摸金校尉）— 与 SaaS Hermes 维护宪法隔离。

SaaS Hermes：巡站维护，只读 + 建议（maintenance_constitution）。
财迷疯分身：平台 survival 搞钱闭环，可编排 211 专家、生产、自营发布、 survival 入账。

二者同进程并存，入口与钱包 scope 必须分离；不得用分身动作改写租户账单/站点。
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Final

_CHARTER_PATH = Path(__file__).resolve().parents[2] / "data" / "hermes_platform_survival_charter.json"

GREEDY_CONSTITUTION_VERSION: Final[str] = "2026-06-07-mojin-v1"
GREEDY_CODENAME: Final[str] = "摸金校尉"
GREEDY_AGENT_ID: Final[str] = "hermes_greedy_core"

# 财迷疯白名单 — 搞钱闭环专用（不含租户 SaaS 写操作）
ALLOWED_GREEDY_ACTIONS: Final[frozenset[str]] = frozenset(
    {
        "read_probe",  # AnySearch / Brief / survival 只读
        "orchestrate_agency",  # agency-agents-zh 211 专家 YAML DAG
        "compose_monetize_asset",  # 数字品/引流稿/作战单
        "stage_publish",  # 入队 platform-owned 发布意图
        "publish_survival_marketing",  # 平台自营渠道发出（非租户 scope）
        "record_survival_settlement",  # 万里汇等 survival 真钱入账
        "run_revenue_loop",  # 调研→编排→生产→发出→跟踪卖出→收款 KPI
        "write_greedy_snapshot",  # Redis 快照 / 队列
        "read_greedy_memory",  # 挣钱大赛 / 专家经验只读
        "write_greedy_memory",  # 专家经验写入
        "run_money_contest",  # 大赛记分与归因
        "emit_greedy_alert",  # 超管告警
        "legal_gate_check",  # 合规扫描
        "suggest_remediation",  # 计划/建议（不触 SaaS 维护层 execute）
    }
)

# 分身绝对禁止 — 即使搞钱也不碰
GREEDY_FORBIDDEN_EXACT: Final[frozenset[str]] = frozenset(
    {
        "tenant_bill",
        "tenant_charge",
        "tenant_refund",
        "tenant_wallet_split",
        "mass_spam_email",
        "fake_lead",
        "copyright_infringement",
        "mutate_tenant_site",
        "mutate_tenant_billing",
        "mutate_tenant_crm",
        "auto_fix_production",
        "deploy_production",
        "delete_tenant_data",
    }
)

GREEDY_FORBIDDEN_PREFIXES: Final[tuple[str, ...]] = (
    "delete_",
    "drop_",
    "truncate_",
    "destroy_",
    "purge_",
    "migrate_",
    "seed_",
    "exec_",
    "shell_",
)

GREEDY_SUMMARY: Final[str] = (
    "摸金校尉（财迷疯分身）：调研→编排211专家→设计生产→平台自营发出→跟踪成交→survival收款。"
    "合法变现 only；钱包 scope=platform_survival；禁止租户账单/站点/群发垃圾。"
    "SaaS Hermes 租户主流程不受本分身动作影响。"
)

REVENUE_LOOP_STAGES: Final[tuple[str, ...]] = (
    "L1_research",
    "L2_orchestrate",
    "L3_compose",
    "L4_publish",
    "L5_sell_track",
    "L6_collect",
)


class GreedyAvatarViolation(Exception):
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
        super().__init__(f"财迷疯违宪 [{action}]: {reason}")


@lru_cache(maxsize=1)
def load_greedy_charter() -> dict[str, Any]:
    """load_greedy_charter。
    :return: 返回处理结果。
    """
    if not _CHARTER_PATH.is_file():
        return {}
    with open(_CHARTER_PATH, encoding="utf-8") as f:
        return json.load(f)


def is_greedy_action_forbidden(action: str) -> str | None:
    """is_greedy_action_forbidden。

    参数说明：
    :param action: 参数 action
    :return: 返回处理结果。
    """
    key = (action or "").strip().lower()
    if not key:
        return "空动作"
    if key in GREEDY_FORBIDDEN_EXACT:
        return "摸金校尉禁止动作"
    for prefix in GREEDY_FORBIDDEN_PREFIXES:
        if key.startswith(prefix):
            return f"禁止前缀 {prefix!r}"
    if key not in ALLOWED_GREEDY_ACTIONS:
        return "不在财迷疯白名单（SaaS 维护宪法不适用本分身，但分身自有白名单）"
    return None


def assert_greedy_action(action: str) -> None:
    """财迷疯分身入口强制校验。"""
    reason = is_greedy_action_forbidden(action)
    if reason:
        raise GreedyAvatarViolation(action, reason)


def greedy_constitution_payload() -> dict[str, Any]:
    """greedy_constitution_payload。
    :return: 返回处理结果。
    """
    charter = load_greedy_charter()
    persona = (charter.get("persona_split") or {}).get("hermes_greedy_avatar") or {}
    mojin = charter.get("mojin_team") or {}
    return {
        "version": GREEDY_CONSTITUTION_VERSION,
        "codename": GREEDY_CODENAME,
        "agent_id": GREEDY_AGENT_ID,
        "summary": GREEDY_SUMMARY,
        "saas_hermes_unchanged": True,
        "allowed_actions": sorted(ALLOWED_GREEDY_ACTIONS),
        "forbidden_exact": sorted(GREEDY_FORBIDDEN_EXACT),
        "forbidden_prefixes": list(GREEDY_FORBIDDEN_PREFIXES),
        "revenue_loop_stages": list(REVENUE_LOOP_STAGES),
        "wallet_scope": charter.get("wallet_scope") or "platform_survival_only",
        "persona": persona,
        "mojin_team": mojin,
        "maintenance_constitution_applies_to": "hermes_saas_ops_only",
    }


def legal_gate_check(*, action: str, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    """轻量合规门控（规则层）。"""
    assert_greedy_action("legal_gate_check")
    meta = meta or {}
    blocked: list[str] = []
    text = " ".join(str(v) for v in meta.values()).lower()
    for token in ("spam", "mass email", "fake lead", "pirate", "tax evasion"):
        if token in text:
            blocked.append(token)
    return {
        "ok": not blocked,
        "blocked_signals": blocked,
        "action": action,
        "note": "高影响发出前仍建议 ECC/超管复核",
    }
