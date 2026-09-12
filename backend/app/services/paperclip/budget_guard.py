"""Paperclip 预算控制服务。

管理 Agent 月度积分预算：余额检查、消费扣费、月初重置、预警。
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.paperclip import PaperclipAgent, PaperclipCompany

logger = logging.getLogger(__name__)

# 预算阈值常量
budget_alert_threshold = 0.8  # 80% 时预警
budget_hard_limit = 1.0  # 100% 时自动暂停 Agent


def check_budget(db: Session, agent_id: str) -> dict[str, Any]:
    """检查 Agent 是否还有预算余量。

    Args:
        db: 数据库 session
        agent_id: Agent ID

    Returns:
        预算状态字典 {allowed, remaining, used, total, ratio, alert, paused}
    """
    agent = db.query(PaperclipAgent).filter(PaperclipAgent.id == agent_id).first()
    if not agent:
        return {"allowed": False, "error": "agent_not_found"}

    total = float(agent.monthly_budget_credits or 0.0)
    used = float(agent.used_credits or 0.0)
    ratio = used / total if total > 0 else 1.0
    remaining = max(0.0, total - used)
    # 超限自动暂停
    if ratio >= budget_hard_limit and agent.status == "active":
        agent.status = "paused"
        agent.heartbeat_enabled = False
        db.commit()
        logger.warning(
            "Agent %s auto-paused: budget exhausted (%.1f/%.1f)",
            agent_id, used, total,
        )
        return {
            "allowed": False,
            "remaining": 0.0,
            "used": used,
            "total": total,
            "ratio": ratio,
            "alert": True,
            "paused": True,
            "reason": "budget_hard_limit",
        }

    alert = ratio >= budget_alert_threshold
    if alert:
        logger.info(
            "Agent %s budget alert: %.0f%% used (%.1f/%.1f)",
            agent_id, ratio * 100, used, total,
        )

    return {
        "allowed": ratio < budget_hard_limit,
        "remaining": remaining,
        "used": used,
        "total": total,
        "ratio": ratio,
        "alert": alert,
        "paused": False,
    }


def consume_credits(db: Session, agent_id: str, amount: float) -> dict[str, Any]:
    """消费 Agent 积分。

    Args:
        db: 数据库 session
        agent_id: Agent ID
        amount: 消费积分数量

    Returns:
        消费结果 {success, remaining, used, total}
    """
    if amount <= 0:
        return {"success": False, "error": "invalid_amount"}

    agent = db.query(PaperclipAgent).filter(PaperclipAgent.id == agent_id).first()
    if not agent:
        return {"success": False, "error": "agent_not_found"}

    total = float(agent.monthly_budget_credits or 0.0)
    used = float(agent.used_credits or 0.0)
    new_used = used + amount
    if new_used > total:
        # 超限：消费但标记为超额
        agent.used_credits = new_used
        db.commit()
        logger.warning(
            "Agent %s over-budget: consumed %.1f, used %.1f/%.1f",
            agent_id, amount, new_used, total,
        )
        # 触发自动暂停检查
        check_budget(db, agent_id)
        return {
            "success": True,
            "remaining": 0.0,
            "used": new_used,
            "total": total,
            "over_budget": True,
        }

    agent.used_credits = new_used
    db.commit()
    # 接近阈值时预警
    ratio = new_used / total if total > 0 else 1.0
    if ratio >= budget_alert_threshold:
        logger.info(
            "Agent %s budget alert after consume: %.0f%% (%.1f/%.1f)",
            agent_id, ratio * 100, new_used, total,
        )

    return {
        "success": True,
        "remaining": max(0.0, total - new_used),
        "used": new_used,
        "total": total,
        "over_budget": False,
    }


def reset_monthly_budgets(db: Session) -> int:
    """月初重置所有 Agent 的已用积分为 0，并恢复因预算耗尽暂停的 Agent。

    Args:
        db: 数据库 session

    Returns:
        重置数量
    """
    agents = db.query(PaperclipAgent).filter(
        PaperclipAgent.used_credits > 0,
    ).all()
    count = 0
    for agent in agents:
        agent.used_credits = 0.0
        # 恢复因预算耗尽而暂停的 Agent
        if agent.status == "paused":
            agent.status = "active"
            agent.heartbeat_enabled = True
        count += 1

    if count:
        db.commit()
        logger.info("Monthly budget reset: %d agents", count)
    return count


def get_budget_status(db: Session, company_id: str) -> list[dict[str, Any]]:
    """获取公司所有 Agent 的预算状态。

    Args:
        db: 数据库 session
        company_id: 公司 ID

    Returns:
        Agent 预算状态列表
    """
    agents = db.query(PaperclipAgent).filter(
        PaperclipAgent.company_id == company_id,
        PaperclipAgent.status != "terminated",
    ).all()
    result = []
    for agent in agents:
        total = float(agent.monthly_budget_credits or 0.0)
        used = float(agent.used_credits or 0.0)
        ratio = used / total if total > 0 else 1.0
        result.append({
            "agent_id": str(agent.id),
            "agent_name": agent.name,
            "total": total,
            "used": used,
            "remaining": max(0.0, total - used),
            "ratio": ratio,
            "alert": ratio >= budget_alert_threshold,
            "status": agent.status,
        })
    return result


# ---------------------------------------------------------------------------
# API route compatibility wrappers
# ---------------------------------------------------------------------------

def budget_overview(db: Session, company_id: str) -> list[dict[str, Any]]:
    """预算总览（API 兼容别名）。"""
    return get_budget_status(db, company_id)


def adjust_budget(
    db: Session,
    agent_id: str,
    monthly_budget_credits: int,
    reason: str | None = None,
    requested_by: str | None = None,
) -> dict[str, Any] | None:
    """调整 Agent 预算。"""
    agent = db.query(PaperclipAgent).filter(PaperclipAgent.id == agent_id).first()
    if not agent:
        return None
    old_budget = agent.monthly_budget_credits
    agent.monthly_budget_credits = float(monthly_budget_credits)
    db.commit()
    logger.info(
        "Budget adjusted for agent %s: %.1f -> %.1f (reason=%s, by=%s)",
        agent_id, old_budget, monthly_budget_credits, reason, requested_by,
    )
    return {
        "agent_id": agent_id,
        "old_budget": old_budget,
        "new_budget": float(monthly_budget_credits),
        "reason": reason,
    }


def run_monthly_reset(db: Session) -> dict[str, Any]:
    """月度预算重置（API 兼容包装）。"""
    count = reset_monthly_budgets(db)
    return {"reset_count": count}
