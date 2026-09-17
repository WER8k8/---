# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Policy Engine：统一策略裁决（总纲 §3.1/§7.2/§6.6 P2；轮20）。

升级 paperclip approval_gate（人审）+ budget_guard（配额）为统一裁决入口。
四维规则（deny 优先于 require_approval 优先于 warn 优先于 allow）：

1. 合规 compliance：Hermes 禁用权限集（§4.6-5 Adapter 契约）一律 deny；
   数据源启用动作需评审通过（§5.2.4 裁决权归 Policy Engine）。
2. 窗口 window：营销类出站动作在安静时段（默认 22:00-07:00）deny；
   WhatsApp 24h 客服窗落地 092 后接入。
3. 配额 quota：Agent 预算复用 budget_guard.check_budget，不足即 deny。
4. 人审 human_review：敏感动作转审批单（复用 approval_gate），require_approval。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

DECISIONS = ("allow", "deny", "require_approval", "warn")

# Hermes 禁用权限集（总纲 §4.6-5）：任何执行面不得请求这些能力
HERMES_FORBIDDEN_ACTIONS = frozenset(
    {
        "raw_shell",
        "raw_db_write",
        "raw_host_filesystem",
        "unscoped_browser",
        "unscoped_credentials",
    }
)

# 敏感动作：必须人审（paperclip 动作 + 凭证轮换 + 数据源启用）
HUMAN_REVIEW_ACTIONS = frozenset(
    {
        "paperclip.hire_agent",
        "paperclip.fire_agent",
        "paperclip.budget_change",
        "paperclip.goal_change",
        "paperclip.task_execute",
        "credential.rotate",
        "datasource.enable",
    }
)

# 营销类出站动作：受安静时段窗口约束
MARKETING_ACTIONS = frozenset(
    {
        "email.send_campaign",
        "whatsapp.send_marketing",
        "content.publish",
        "multi_channel.distribute",
    }
)

# 安静时段（本地小时，含头不含尾）
DEFAULT_QUIET_HOURS = (22, 7)


@dataclass
class PolicyDecision:
    decision: str
    reasons: list[str] = field(default_factory=list)
    approval_id: str | None = None
    rule_hits: list[str] = field(default_factory=list)

    def allowed(self) -> bool:
        return self.decision in ("allow", "warn")


class PolicyEngine:
    """统一策略裁决引擎。

    evaluate() 是唯一入口；内部四维依次裁决，deny 最优先。
    现网行为兼容：paperclip.hire/fire 原走 approval_gate，
    接入后仍返回 require_approval + 审批单 ID。
    """

    def evaluate(
        self,
        db: Session,
        *,
        action: str,
        tenant_id: str | None = None,
        company_id: str | None = None,
        agent_id: str | None = None,
        context: dict[str, Any] | None = None,
        now: datetime | None = None,
        auto_create_approval: bool = True,
    ) -> PolicyDecision:
        ctx = dict(context or {})
        decision = "allow"
        reasons: list[str] = []
        hits: list[str] = []

        # ---- 1. 合规：禁用权限集 / 数据源评审门 ----
        if action in HERMES_FORBIDDEN_ACTIONS:
            return PolicyDecision(
                "deny", [f"forbidden_action: {action}（Hermes 禁用权限集）"], rule_hits=["compliance"]
            )
        if action == "datasource.enable":
            verdict = self._check_datasource_review(db, ctx)
            if verdict is not None:
                return PolicyDecision("deny", [verdict], rule_hits=["compliance"])

        # ---- 2. 窗口：营销类动作 × 安静时段 ----
        if action in MARKETING_ACTIONS and not ctx.get("skip_quiet_hours"):
            quiet = self._quiet_hours_hit(ctx, now)
            if quiet is not None:
                return PolicyDecision(
                    "deny",
                    [f"quiet_hours: 营销动作 {action} 禁止于 {quiet[0]}:00-{quiet[1]}:00 发出"],
                    rule_hits=["window"],
                )

        # ---- 3. 配额：Agent 预算（复用 budget_guard） ----
        if agent_id:
            budget = self._check_budget(db, agent_id)
            if budget is not None:
                if not budget.get("allowed"):
                    return PolicyDecision(
                        "deny",
                        [
                            f"budget_exhausted: agent={agent_id} "
                            f"used={budget.get('used')}/{budget.get('total')}"
                        ],
                        rule_hits=["quota"],
                    )
                if budget.get("alert"):
                    decision = "warn"
                    reasons.append(
                        f"budget_alert: agent={agent_id} 已用 {budget.get('ratio', 0):.0%}"
                    )
                    hits.append("quota")

        # ---- 4. 人审：敏感动作转审批单 ----
        if action in HUMAN_REVIEW_ACTIONS:
            approval_id = None
            if auto_create_approval and company_id:
                approval_id = self._create_approval(db, action, ctx, company_id, agent_id)
            return PolicyDecision(
                "require_approval",
                [f"human_review_required: {action}"],
                approval_id=approval_id,
                rule_hits=["human_review"],
            )

        return PolicyDecision(decision, reasons, rule_hits=hits)

    # ------------------------------------------------------------- 内部
    def _check_datasource_review(self, db: Session, ctx: dict[str, Any]) -> str | None:
        """数据源启用须评审通过（§5.2.4）。未提供 provider 视为信息不足拒绝。"""
        provider_id = ctx.get("data_provider_id")
        if not provider_id:
            return "datasource_review_missing: 启用数据源必须提供 data_provider_id"
        try:
            from app.models.registry import DataSourceProvider
        except ImportError:
            return None
        row = (
            db.query(DataSourceProvider)
            .filter(DataSourceProvider.id == str(provider_id))
            .first()
        )
        if not row:
            return f"datasource_not_found: {provider_id}"
        if getattr(row, "review_status", None) != "approved":
            return (
                f"datasource_not_approved: {provider_id} "
                f"review_status={getattr(row, 'review_status', None)}"
            )
        return None

    def _quiet_hours_hit(
        self, ctx: dict[str, Any], now: datetime | None
    ) -> tuple[int, int] | None:
        start, end = DEFAULT_QUIET_HOURS
        hour = ctx.get("local_hour")
        if hour is None:
            hour = (now or datetime.now(timezone.utc)).hour
        if start <= end:
            in_window = start <= hour < end
        else:  # 跨午夜（如 22-7）
            in_window = hour >= start or hour < end
        return (start, end) if in_window else None

    def _check_budget(self, db: Session, agent_id: str) -> dict | None:
        try:
            from app.services.paperclip.budget_guard import check_budget
        except ImportError:
            return None
        try:
            return check_budget(db, agent_id)
        except Exception:  # noqa: BLE001
            logger.exception("budget_guard 查询失败，按无配额信息处理")
            return None

    def _create_approval(
        self,
        db: Session,
        action: str,
        ctx: dict[str, Any],
        company_id: str,
        agent_id: str | None,
    ) -> str | None:
        try:
            from app.services.paperclip.approval_gate import create_approval
        except ImportError:
            return None
        # paperclip.hire_agent → hire_agent（approval_gate 既有 action_type 空间）
        approval_type = ctx.get("approval_action_type") or (
            action.split(".", 1)[1] if "." in action else action
        )
        approval = create_approval(
            db,
            company_id=company_id,
            agent_id=agent_id,
            action_type=approval_type,
            payload=ctx.get("payload") or {},
        )
        return str(approval.id)


def evaluate_action(
    db: Session,
    *,
    action: str,
    tenant_id: str | None = None,
    company_id: str | None = None,
    agent_id: str | None = None,
    context: dict[str, Any] | None = None,
    now: datetime | None = None,
    auto_create_approval: bool = True,
) -> PolicyDecision:
    """模块级便捷入口（首个调用方：paperclip orchestrator hire/fire）。"""
    return PolicyEngine().evaluate(
        db,
        action=action,
        tenant_id=tenant_id,
        company_id=company_id,
        agent_id=agent_id,
        context=context,
        now=now,
        auto_create_approval=auto_create_approval,
    )
