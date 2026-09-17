# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Paperclip 审批门服务。

管理 Agent 雇佣、任务执行等关键操作的审批流程。
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.paperclip import PaperclipApproval

logger = logging.getLogger(__name__)


def create_approval(
    db: Session,
    *,
    company_id: str,
    agent_id: str | None,
    action_type: str,
    payload: dict[str, Any],
) -> PaperclipApproval:
    """创建审批请求。

    Args:
        db: 数据库 session
        company_id: 公司 ID
        agent_id: 关联 Agent ID（可选）
        action_type: 操作类型 (hire_agent | fire_agent | budget_change | goal_change | task_execute)
        payload: 操作载荷

    Returns:
        新创建的审批记录
    """
    approval = PaperclipApproval(
        company_id=company_id,
        agent_id=agent_id,
        action_type=action_type,
        action_payload_json=json.dumps(payload, ensure_ascii=False),
        status="pending",
    )
    db.add(approval)
    db.commit()
    db.refresh(approval)
    logger.info(
        "Approval created: id=%s type=%s company=%s",
        approval.id, action_type, company_id,
    )
    return approval


def approve(
    db: Session,
    approval_id: str,
    reviewer_id: str,
    comment: str | None = None,
) -> dict[str, Any]:
    """批准审批请求。

    Args:
        db: 数据库 session
        approval_id: 审批 ID
        reviewer_id: 审核人 ID
        comment: 审核意见

    Returns:
        审批结果

    Raises:
        ValueError: 审批不存在或状态非法
    """
    approval = db.query(PaperclipApproval).filter(
        PaperclipApproval.id == approval_id,
    ).first()
    if not approval:
        raise ValueError(f"approval_not_found: {approval_id}")
    if approval.status != "pending":
        raise ValueError(f"approval_not_pending: {approval.status}")

    approval.status = "approved"
    approval.reviewer_id = reviewer_id
    approval.review_comment = comment
    approval.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(approval)
    logger.info("Approval approved: id=%s reviewer=%s", approval_id, reviewer_id)
    # 审批通过后执行关联操作
    result = _execute_approved_action(db, approval)
    return {
        "approval_id": str(approval.id),
        "status": "approved",
        "action_result": result,
    }


def reject(
    db: Session,
    approval_id: str,
    reviewer_id: str,
    comment: str | None = None,
) -> dict[str, Any]:
    """拒绝审批请求。

    Args:
        db: 数据库 session
        approval_id: 审批 ID
        reviewer_id: 审核人 ID
        comment: 拒绝理由

    Returns:
        拒绝结果

    Raises:
        ValueError: 审批不存在或状态非法
    """
    approval = db.query(PaperclipApproval).filter(
        PaperclipApproval.id == approval_id,
    ).first()
    if not approval:
        raise ValueError(f"approval_not_found: {approval_id}")
    if approval.status != "pending":
        raise ValueError(f"approval_not_pending: {approval.status}")

    approval.status = "rejected"
    approval.reviewer_id = reviewer_id
    approval.review_comment = comment
    approval.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(approval)
    logger.info("Approval rejected: id=%s reviewer=%s", approval_id, reviewer_id)

    if approval.action_type == "hermes_node_approval":
        from app.services.tasks.paperclip_approval_bridge import cancel_rejected_task

        cancel_rejected_task(db, approval, comment)

    return {
        "approval_id": str(approval.id),
        "status": "rejected",
    }


def get_pending_approvals(
    db: Session,
    company_id: str,
) -> list[dict[str, Any]]:
    """获取公司待审批列表。

    Args:
        db: 数据库 session
        company_id: 公司 ID

    Returns:
        待审批记录列表
    """
    rows = (
        db.query(PaperclipApproval)
        .filter(
            PaperclipApproval.company_id == company_id,
            PaperclipApproval.status == "pending",
        )
        .order_by(PaperclipApproval.created_at.asc())
        .all()
    )
    return [_serialize_approval(r) for r in rows]


def auto_expire(db: Session, max_age_hours: int = 72) -> int:
    """自动过期超时未处理的审批。

    Args:
        db: 数据库 session
        max_age_hours: 最大存活小时数（默认 72 小时）

    Returns:
        过期数量
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
    expired = (
        db.query(PaperclipApproval)
        .filter(
            PaperclipApproval.status == "pending",
            PaperclipApproval.created_at < cutoff,
        )
        .all()
    )
    count = 0
    for approval in expired:
        approval.status = "expired"
        approval.reviewed_at = datetime.now(timezone.utc)
        count += 1
    if count:
        db.commit()
        logger.info("Auto-expired %d approvals older than %dh", count, max_age_hours)
    return count


def _execute_approved_action(db: Session, approval: PaperclipApproval) -> dict[str, Any]:
    """审批通过后执行关联操作。

    根据 action_type 执行对应逻辑（如创建 Agent）。
    """
    action = approval.action_type
    try:
        payload = json.loads(approval.action_payload_json or "{}")
    except json.JSONDecodeError:
        payload = {}

    if action == "hire_agent":
        return _execute_hire_agent(db, approval.company_id, payload)
    elif action == "fire_agent":
        return _execute_fire_agent(db, payload)
    elif action == "budget_change":
        return {"action": "budget_change", "status": "acknowledged"}
    elif action == "hermes_node_approval":
        from app.services.tasks.paperclip_approval_bridge import resume_approved_task

        return resume_approved_task(db, approval)
    else:
        logger.debug("No auto-execute for action_type=%s", action)
        return {"action": action, "status": "acknowledged"}


def _execute_hire_agent(
    db: Session, company_id: str, payload: dict[str, Any],
) -> dict[str, Any]:
    """审批通过后创建 Agent。"""
    from app.models.paperclip import PaperclipAgent
    agent = PaperclipAgent(
        company_id=company_id,
        name=payload.get("name", "Unnamed Agent"),
        title=payload.get("title", ""),
        role=payload.get("role", "worker"),
        provider=payload.get("provider", "hermes"),
        agent_ref=payload.get("agent_ref", ""),
        parent_id=payload.get("parent_id"),
        heartbeat_interval_minutes=int(payload.get("heartbeat_interval_minutes", 240)),
        monthly_budget_credits=float(payload.get("monthly_budget_credits", 1000.0)),
        status="active",
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    logger.info("Agent hired via approval: id=%s name=%s", agent.id, agent.name)
    return {"action": "hire_agent", "status": "created", "agent_id": str(agent.id)}


def _execute_fire_agent(
    db: Session, payload: dict[str, Any],
) -> dict[str, Any]:
    """审批通过后终止 Agent。"""
    from app.models.paperclip import PaperclipAgent
    agent_id = payload.get("agent_id")
    if not agent_id:
        return {"action": "fire_agent", "status": "skipped", "reason": "missing agent_id"}

    agent = db.query(PaperclipAgent).filter(PaperclipAgent.id == agent_id).first()
    if not agent:
        return {"action": "fire_agent", "status": "skipped", "reason": "agent_not_found"}

    agent.status = "terminated"
    agent.heartbeat_enabled = False
    db.commit()
    logger.info("Agent terminated via approval: id=%s", agent_id)
    return {"action": "fire_agent", "status": "terminated", "agent_id": str(agent_id)}


def _serialize_approval(row: PaperclipApproval) -> dict[str, Any]:
    """序列化审批记录。"""
    payload = {}
    try:
        payload = json.loads(row.action_payload_json or "{}")
    except json.JSONDecodeError:
        payload = {}
    return {
        "id": str(row.id),
        "company_id": str(row.company_id),
        "agent_id": str(row.agent_id) if row.agent_id else None,
        "action_type": row.action_type,
        "payload": payload,
        "status": row.status,
        "reviewer_id": str(row.reviewer_id) if row.reviewer_id else None,
        "review_comment": row.review_comment,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "reviewed_at": row.reviewed_at.isoformat() if row.reviewed_at else None,
    }


# ---------------------------------------------------------------------------
# Policy Engine 放行路径复用的公共执行入口（轮20）
# ---------------------------------------------------------------------------

def execute_hire_agent(db: Session, company_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """按雇佣载荷直接创建 Agent（Policy Engine allow 路径复用）。"""
    return _execute_hire_agent(db, company_id, payload)


def execute_fire_agent(db: Session, payload: dict[str, Any]) -> dict[str, Any]:
    """按载荷直接终止 Agent（Policy Engine allow 路径复用）。"""
    return _execute_fire_agent(db, payload)


# ---------------------------------------------------------------------------
# API route compatibility wrappers
# ---------------------------------------------------------------------------

def list_company_approvals(
    db: Session,
    company_id: str,
    status: str | None = None,
) -> list[dict[str, Any]]:
    """列出公司审批记录（支持状态筛选）。"""
    q = db.query(PaperclipApproval).filter(PaperclipApproval.company_id == company_id)
    if status:
        q = q.filter(PaperclipApproval.status == status)
    rows = q.order_by(PaperclipApproval.created_at.desc()).all()
    return [_serialize_approval(r) for r in rows]


def approve_request(
    db: Session,
    approval_id: str,
    approved_by: str,
    comment: str | None = None,
) -> dict[str, Any] | None:
    """批准审批请求（API 兼容包装）。"""
    try:
        return approve(db, approval_id, reviewer_id=approved_by, comment=comment)
    except ValueError:
        return None


def reject_request(
    db: Session,
    approval_id: str,
    rejected_by: str,
    comment: str | None = None,
) -> dict[str, Any] | None:
    """拒绝审批请求（API 兼容包装）。"""
    try:
        return reject(db, approval_id, reviewer_id=rejected_by, comment=comment)
    except ValueError:
        return None
