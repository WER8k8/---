"""Paperclip 目标对齐链服务。

构建使命 → 项目 → 目标 → 任务的完整链路，支持进度冒泡更新。
"""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.models.paperclip import PaperclipAgent, PaperclipCompany, PaperclipGoal, PaperclipTask

logger = logging.getLogger(__name__)


def build_goal_chain(db: Session, goal_id: str) -> list[dict[str, Any]]:
    """构建从当前目标到公司使命的完整链路。

    从给定 goal 向上遍历 parent_id，直到没有上级为止。
    链路顺序：[公司使命, 项目目标, ..., 当前目标]

    Args:
        db: 数据库 session
        goal_id: 目标 ID

    Returns:
        从顶层到当前目标的链路列表
    """
    chain: list[dict[str, Any]] = []
    visited: set[str] = set()
    current_id = goal_id
    while current_id and current_id not in visited:
        visited.add(current_id)
        goal = db.query(PaperclipGoal).filter(PaperclipGoal.id == current_id).first()
        if not goal:
            break
        chain.append(_serialize_goal(goal))
        current_id = str(goal.parent_id) if goal.parent_id else None

    chain.reverse()
    return chain


def get_agent_context(
    db: Session,
    agent_id: str,
    task_id: str | None = None,
) -> dict[str, Any]:
    """获取 Agent 执行任务时的完整上下文。

    上下文包含：公司使命 → 所属目标链 → 当前任务。
    Agent 可以在执行任务时参考此上下文保持目标对齐。

    Args:
        db: 数据库 session
        agent_id: Agent ID
        task_id: 任务 ID（可选，不传则取 Agent 最近的任务）

    Returns:
        完整上下文字典
    """
    agent = db.query(PaperclipAgent).filter(PaperclipAgent.id == agent_id).first()
    if not agent:
        return {"error": "agent_not_found"}

    company = db.query(PaperclipCompany).filter(
        PaperclipCompany.id == agent.company_id,
    ).first()
    context: dict[str, Any] = {
        "agent": {
            "id": str(agent.id),
            "name": agent.name,
            "title": agent.title,
            "role": agent.role,
        },
        "company": {
            "id": str(company.id) if company else None,
            "name": company.name if company else "",
            "mission": company.mission if company else "",
        },
        "goal_chain": [],
        "task": None,
        "business_context": {},
    }
    # 注入租户业务上下文（产品/询盘/行业/认知）
    if company and company.tenant_id:
        try:
            from app.services.paperclip.tenant_context import build_tenant_business_context
            context["business_context"] = build_tenant_business_context(db, str(company.tenant_id))
        except Exception:
            pass

    # 找到当前任务
    task = None
    if task_id:
        task = db.query(PaperclipTask).filter(PaperclipTask.id == task_id).first()
    if not task:
        task = (
            db.query(PaperclipTask)
            .filter(
                PaperclipTask.assigned_agent_id == agent_id,
                PaperclipTask.status.in_(["queued", "running"]),
            )
            .order_by(PaperclipTask.created_at.desc())
            .first()
        )

    if task:
        context["task"] = _serialize_task(task)
        if task.goal_id:
            context["goal_chain"] = build_goal_chain(db, str(task.goal_id))

    return context


def update_progress(db: Session, goal_id: str) -> dict[str, Any]:
    """从子目标/任务进度向上冒泡更新。

    递归计算当前目标下所有子目标和任务的平均进度，
    然后向上冒泡更新所有祖先目标。

    Args:
        db: 数据库 session
        goal_id: 目标 ID

    Returns:
        更新后的进度信息
    """
    goal = db.query(PaperclipGoal).filter(PaperclipGoal.id == goal_id).first()
    if not goal:
        return {"error": "goal_not_found"}

    # 收集子目标进度
    child_goals = db.query(PaperclipGoal).filter(
        PaperclipGoal.parent_id == goal_id,
    ).all()
    # 收集直接任务进度
    tasks = db.query(PaperclipTask).filter(
        PaperclipTask.goal_id == goal_id,
    ).all()
    progresses: list[float] = []
    for child in child_goals:
        child_update = update_progress(db, str(child.id))
        if "progress" in child_update:
            progresses.append(child_update["progress"])

    for task in tasks:
        if task.status == "success":
            progresses.append(1.0)
        elif task.status == "running":
            progresses.append(0.5)
        elif task.status == "queued":
            progresses.append(0.0)
        elif task.status == "failed":
            progresses.append(0.0)

    avg_progress = sum(progresses) / len(progresses) if progresses else goal.progress
    goal.progress = min(1.0, max(0.0, avg_progress))
    # 自动更新状态
    if progresses and all(p >= 1.0 for p in progresses):
        goal.status = "completed"

    db.commit()
    # 向上冒泡
    if goal.parent_id:
        update_progress(db, str(goal.parent_id))

    return {
        "goal_id": str(goal.id),
        "progress": goal.progress,
        "status": goal.status,
        "children_count": len(child_goals),
        "tasks_count": len(tasks),
    }


def get_goal_tree(db: Session, company_id: str) -> dict[str, Any]:
    """获取完整目标树。

    Args:
        db: 数据库 session
        company_id: 公司 ID

    Returns:
        目标树（嵌套结构）
    """
    goals = db.query(PaperclipGoal).filter(
        PaperclipGoal.company_id == company_id,
    ).order_by(PaperclipGoal.priority.asc(), PaperclipGoal.created_at.asc()).all()
    goal_map: dict[str, dict[str, Any]] = {}
    roots: list[dict[str, Any]] = []
    for g in goals:
        node = _serialize_goal(g)
        node["children"] = []
        goal_map[str(g.id)] = node

    for g in goals:
        node = goal_map[str(g.id)]
        if g.parent_id and str(g.parent_id) in goal_map:
            goal_map[str(g.parent_id)]["children"].append(node)
        else:
            roots.append(node)

    return {
        "company_id": company_id,
        "total_goals": len(goals),
        "roots": roots,
    }


def _serialize_goal(g: PaperclipGoal) -> dict[str, Any]:
    """序列化目标记录。"""
    return {
        "id": str(g.id),
        "company_id": str(g.company_id),
        "parent_id": str(g.parent_id) if g.parent_id else None,
        "owner_agent_id": str(g.owner_agent_id) if g.owner_agent_id else None,
        "title": g.title,
        "description": g.description,
        "level": g.level,
        "status": g.status,
        "priority": g.priority,
        "progress": g.progress,
        "created_at": g.created_at.isoformat() if g.created_at else None,
    }


def _serialize_task(t: PaperclipTask) -> dict[str, Any]:
    """序列化任务记录。"""
    return {
        "id": str(t.id),
        "company_id": str(t.company_id),
        "goal_id": str(t.goal_id) if t.goal_id else None,
        "assigned_agent_id": str(t.assigned_agent_id) if t.assigned_agent_id else None,
        "title": t.title,
        "description": t.description,
        "intent": t.intent,
        "status": t.status,
        "priority": t.priority,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }


# ---------------------------------------------------------------------------
# API route compatibility: CRUD functions
# ---------------------------------------------------------------------------

def create_goal(
    db: Session,
    *,
    company_id: str,
    title: str,
    description: str | None = None,
    level: str = "company",
    parent_goal_id: str | None = None,
    owner_agent_id: str | None = None,
    metric_target: float | None = None,
    deadline: str | None = None,
) -> dict[str, Any]:
    """创建目标。"""
    goal = PaperclipGoal(
        company_id=company_id,
        parent_id=parent_goal_id,
        owner_agent_id=owner_agent_id,
        title=title,
        description=description or "",
        level=level,
        status="active",
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    logger.info("Goal created: id=%s title=%s level=%s", goal.id, title, level)
    return _serialize_goal(goal)


def list_company_goals(
    db: Session,
    company_id: str,
    level: str | None = None,
) -> list[dict[str, Any]]:
    """列出公司目标。"""
    q = db.query(PaperclipGoal).filter(PaperclipGoal.company_id == company_id)
    if level:
        q = q.filter(PaperclipGoal.level == level)
    goals = q.order_by(PaperclipGoal.priority.asc(), PaperclipGoal.created_at.asc()).all()
    return [_serialize_goal(g) for g in goals]


def get_goal_detail(db: Session, goal_id: str) -> dict[str, Any] | None:
    """获取目标详情（含对齐链）。"""
    goal = db.query(PaperclipGoal).filter(PaperclipGoal.id == goal_id).first()
    if not goal:
        return None
    detail = _serialize_goal(goal)
    detail["alignment_chain"] = build_goal_chain(db, goal_id)
    return detail


def update_goal(
    db: Session,
    goal_id: str,
    title: str | None = None,
    description: str | None = None,
    status: str | None = None,
    metric_target: float | None = None,
    deadline: str | None = None,
) -> dict[str, Any] | None:
    """更新目标。"""
    goal = db.query(PaperclipGoal).filter(PaperclipGoal.id == goal_id).first()
    if not goal:
        return None
    if title is not None:
        goal.title = title
    if description is not None:
        goal.description = description
    if status is not None:
        goal.status = status
    db.commit()
    db.refresh(goal)
    return _serialize_goal(goal)


def get_alignment_chain(db: Session, goal_id: str) -> list[dict[str, Any]] | None:
    """获取目标对齐链（API 兼容别名）。"""
    goal = db.query(PaperclipGoal).filter(PaperclipGoal.id == goal_id).first()
    if not goal:
        return None
    return build_goal_chain(db, goal_id)
