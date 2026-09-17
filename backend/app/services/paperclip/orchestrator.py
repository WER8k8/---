# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Paperclip 核心编排服务。

管理公司、Agent、目标、任务的全生命周期。
融合 Hermes + DeerFlow 架构，为 Agent 提供心跳驱动的自动执行能力。
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.paperclip import (
    PaperclipAgent,
    PaperclipCompany,
    PaperclipGoal,
    PaperclipHeartbeat,
    PaperclipTask,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Company CRUD
# ---------------------------------------------------------------------------

def create_company(
    db: Session,
    *,
    name: str,
    mission: str = "",
    tenant_id: str | None = None,
    created_by: str | None = None,
    **kwargs,
) -> dict[str, Any]:
    """创建公司。

    Args:
        db: 数据库 session
        name: 公司名称
        mission: 公司使命
        tenant_id: 绑定的租户 ID（可选）
        created_by: 创建者 ID（可选，tenant_id 为空时回退）

    Returns:
        新创建的公司记录字典
    """
    if not tenant_id:
        tenant_id = created_by or "00000000-0000-0000-0000-000000000000"
    company = PaperclipCompany(
        tenant_id=tenant_id,
        name=name,
        mission=mission,
        status="active",
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    logger.info("Company created: id=%s name=%s tenant=%s", company.id, name, tenant_id)
    return {
        "id": str(company.id),
        "tenant_id": str(company.tenant_id),
        "name": company.name,
        "mission": company.mission,
        "status": company.status,
        "created_at": company.created_at.isoformat() if company.created_at else None,
        "updated_at": company.updated_at.isoformat() if company.updated_at else None,
    }


# ---------------------------------------------------------------------------
# Agent CRUD
# ---------------------------------------------------------------------------

def hire_agent(
    db: Session,
    *,
    company_id: str,
    name: str,
    title: str = "",
    role: str = "worker",
    provider: str = "hermes",
    agent_ref: str = "",
    parent_id: str | None = None,
    manager_agent_id: str | None = None,
    heartbeat_interval: int = 240,
    heartbeat_interval_sec: int | None = None,
    budget: float = 1000.0,
    budget_cents: int | None = None,
    requested_by: str | None = None,
    **kwargs,
) -> dict[str, Any]:
    """雇佣 Agent（创建审批门，审批通过后创建）。

    雇佣请求经 Policy Engine 裁决（轮20）：人审维度 → 创建审批单，
    审批通过后自动创建 Agent；政策放行（规则自定义）时直接创建。
    """
    from app.services.policy.engine import evaluate_action
    # 参数别名解析
    if manager_agent_id and not parent_id:
        parent_id = manager_agent_id
    if heartbeat_interval_sec:
        heartbeat_interval = heartbeat_interval_sec // 60
    if budget_cents:
        budget = float(budget_cents)

    payload = {
        "name": name,
        "title": title,
        "role": role,
        "provider": provider,
        "agent_ref": agent_ref,
        "parent_id": parent_id,
        "heartbeat_interval_minutes": heartbeat_interval,
        "monthly_budget_credits": budget,
    }
    decision = evaluate_action(
        db,
        action="paperclip.hire_agent",
        company_id=company_id,
        context={
            "approval_action_type": "hire_agent",
            "payload": payload,
            "agent_id": None,
        },
    )
    if decision.decision == "deny":
        logger.warning("Hire denied by policy: %s", decision.reasons)
        return {
            "status": "policy_denied",
            "reasons": decision.reasons,
            "agent_name": name,
        }
    if decision.decision == "require_approval":
        logger.info(
            "Hire request created as approval: id=%s agent=%s",
            decision.approval_id, name,
        )
        return {
            "status": "pending_approval",
            "approval_id": decision.approval_id,
            "agent_name": name,
        }
    # allow：政策放行（默认规则下 hire 必走人审，此路径供规则自定义）
    from app.services.paperclip.approval_gate import execute_hire_agent
    result = execute_hire_agent(db, company_id, payload)
    return {
        "status": "hired",
        "agent_id": result.get("agent_id"),
        "agent_name": name,
    }


def fire_agent(db: Session, agent_id: str) -> dict[str, Any]:
    """终止 Agent（经 Policy Engine 裁决，创建审批门）。

    Args:
        db: 数据库 session
        agent_id: Agent ID

    Returns:
        裁决结果（默认人审 → pending_approval）
    """
    from app.services.policy.engine import evaluate_action
    agent = db.query(PaperclipAgent).filter(PaperclipAgent.id == agent_id).first()
    if not agent:
        return {"error": "agent_not_found"}

    if agent.status == "terminated":
        return {"error": "agent_already_terminated"}

    decision = evaluate_action(
        db,
        action="paperclip.fire_agent",
        company_id=str(agent.company_id),
        agent_id=agent_id,
        context={
            "approval_action_type": "fire_agent",
            "payload": {"agent_id": agent_id, "agent_name": agent.name},
        },
    )
    if decision.decision == "deny":
        logger.warning("Fire denied by policy: %s", decision.reasons)
        return {"status": "policy_denied", "reasons": decision.reasons, "agent_id": agent_id}
    if decision.decision == "require_approval":
        logger.info(
            "Fire request created as approval: id=%s agent=%s",
            decision.approval_id, agent.name,
        )
        return {
            "status": "pending_approval",
            "approval_id": decision.approval_id,
            "agent_id": agent_id,
        }
    # allow：政策放行（规则自定义）
    from app.services.paperclip.approval_gate import execute_fire_agent
    result = execute_fire_agent(db, {"agent_id": agent_id})
    return {"status": result.get("status", "terminated"), "agent_id": agent_id}


# ---------------------------------------------------------------------------
# Goal management
# ---------------------------------------------------------------------------

def assign_goal(
    db: Session,
    *,
    company_id: str,
    title: str,
    description: str = "",
    level: str = "goal",
    parent_id: str | None = None,
    owner_agent_id: str | None = None,
) -> PaperclipGoal:
    """分配目标。

    Args:
        db: 数据库 session
        company_id: 公司 ID
        title: 目标标题
        description: 目标描述
        level: 层级 (mission | project | goal | task)
        parent_id: 上级目标 ID
        owner_agent_id: 负责 Agent ID

    Returns:
        新创建的目标记录
    """
    goal = PaperclipGoal(
        company_id=company_id,
        parent_id=parent_id,
        owner_agent_id=owner_agent_id,
        title=title,
        description=description,
        level=level,
        status="active",
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    logger.info("Goal assigned: id=%s title=%s level=%s", goal.id, title, level)
    return goal


# ---------------------------------------------------------------------------
# Task management
# ---------------------------------------------------------------------------

def create_task(
    db: Session,
    *,
    company_id: str,
    goal_id: str | None = None,
    agent_id: str | None = None,
    title: str,
    description: str = "",
    intent: str = "",
    priority: int | str = 0,
) -> dict[str, Any]:
    """创建任务并分派给 Agent。

    任务创建后进入 queued 状态，等待 Agent 心跳时执行。

    Args:
        db: 数据库 session
        company_id: 公司 ID
        goal_id: 关联目标 ID
        agent_id: 分派给的 Agent ID
        title: 任务标题
        description: 任务描述
        intent: DeerFlow intent 或 Hermes plugin kind
        priority: 优先级（数字或字符串 critical/high/normal/low）

    Returns:
        新创建的任务记录字典
    """
    _priority_map = {"critical": -2, "high": -1, "normal": 0, "low": 1}
    priority_val = _priority_map.get(str(priority).lower(), 0) if isinstance(priority, str) else int(priority or 0)
    task = PaperclipTask(
        company_id=company_id,
        goal_id=goal_id,
        assigned_agent_id=agent_id,
        title=title,
        description=description,
        intent=intent,
        priority=priority_val,
        status="queued",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    logger.info(
        "Task created: id=%s title=%s intent=%s agent=%s",
        task.id, title, intent, agent_id,
    )
    _bridge(db).on_task_created(task)
    return _serialize_task(task)


def _bridge(db: Session):
    """影子双写桥（轮24-B）：TASK_CONTROL_ENABLED 关时完全旁路，桥内自吞异常。"""
    from app.services.tasks.paperclip_bridge import PaperclipTaskBridge
    return PaperclipTaskBridge(db)


def delegate_task(db: Session, task_id: str, agent_id: str) -> dict[str, Any]:
    """委派任务给另一个 Agent。

    Args:
        db: 数据库 session
        task_id: 任务 ID
        agent_id: 目标 Agent ID

    Returns:
        委派结果
    """
    task = db.query(PaperclipTask).filter(PaperclipTask.id == task_id).first()
    if not task:
        return {"error": "task_not_found"}

    agent = db.query(PaperclipAgent).filter(PaperclipAgent.id == agent_id).first()
    if not agent:
        return {"error": "agent_not_found"}

    old_agent = str(task.assigned_agent_id) if task.assigned_agent_id else None
    task.assigned_agent_id = agent_id
    if task.status in ("blocked",):
        task.status = "queued"
    db.commit()
    logger.info("Task %s delegated from %s to %s", task_id, old_agent, agent_id)
    return {
        "status": "delegated",
        "task_id": task_id,
        "from_agent": old_agent,
        "to_agent": agent_id,
    }


# ---------------------------------------------------------------------------
# Organization & Dashboard
# ---------------------------------------------------------------------------

def get_org_chart(db: Session, company_id: str) -> dict[str, Any]:
    """获取组织架构树。

    以树形结构返回所有 Agent 及其上下级关系。

    Args:
        db: 数据库 session
        company_id: 公司 ID

    Returns:
        组织架构树
    """
    agents = db.query(PaperclipAgent).filter(
        PaperclipAgent.company_id == company_id,
        PaperclipAgent.status != "terminated",
    ).all()
    agent_map: dict[str, dict[str, Any]] = {}
    roots: list[dict[str, Any]] = []
    for a in agents:
        node = {
            "id": str(a.id),
            "name": a.name,
            "title": a.title,
            "role": a.role,
            "provider": a.provider,
            "status": a.status,
            "heartbeat_enabled": a.heartbeat_enabled,
            "children": [],
        }
        agent_map[str(a.id)] = node

    for a in agents:
        node = agent_map[str(a.id)]
        if a.parent_id and str(a.parent_id) in agent_map:
            agent_map[str(a.parent_id)]["children"].append(node)
        else:
            roots.append(node)

    return {
        "company_id": company_id,
        "total_agents": len(agents),
        "org_tree": roots,
    }


def get_company_dashboard(db: Session, company_id: str) -> dict[str, Any]:
    """获取公司仪表盘数据。

    包含：Agent 状态分布、预算总览、目标进度、最近心跳。

    Args:
        db: 数据库 session
        company_id: 公司 ID

    Returns:
        仪表盘数据
    """
    # Agent 状态分布
    agents = db.query(PaperclipAgent).filter(
        PaperclipAgent.company_id == company_id,
    ).all()
    agent_status: dict[str, int] = {}
    total_budget = 0.0
    total_used = 0.0
    for a in agents:
        agent_status[a.status] = agent_status.get(a.status, 0) + 1
        total_budget += float(a.monthly_budget_credits or 0.0)
        total_used += float(a.used_credits or 0.0)

    # 目标进度
    goals = db.query(PaperclipGoal).filter(
        PaperclipGoal.company_id == company_id,
    ).all()
    goal_status: dict[str, int] = {}
    total_progress = 0.0
    for g in goals:
        goal_status[g.status] = goal_status.get(g.status, 0) + 1
        total_progress += float(g.progress or 0.0)
    avg_progress = total_progress / len(goals) if goals else 0.0
    # 最近心跳
    recent_heartbeats = (
        db.query(PaperclipHeartbeat)
        .filter(PaperclipHeartbeat.company_id == company_id)
        .order_by(PaperclipHeartbeat.created_at.desc())
        .limit(10)
        .all()
    )
    heartbeat_summaries = []
    for hb in recent_heartbeats:
        heartbeat_summaries.append({
            "id": str(hb.id),
            "agent_id": str(hb.agent_id),
            "status": hb.status,
            "tasks_checked": hb.tasks_checked,
            "tasks_executed": hb.tasks_executed,
            "credits_used": hb.credits_used,
            "created_at": hb.created_at.isoformat() if hb.created_at else None,
        })

    # 待处理任务
    pending_tasks = db.query(PaperclipTask).filter(
        PaperclipTask.company_id == company_id,
        PaperclipTask.status.in_(["queued", "running"]),
    ).count()
    return {
        "company_id": company_id,
        "agents": {
            "total": len(agents),
            "by_status": agent_status,
        },
        "budget": {
            "total": total_budget,
            "used": total_used,
            "remaining": max(0.0, total_budget - total_used),
            "ratio": total_used / total_budget if total_budget > 0 else 0.0,
        },
        "goals": {
            "total": len(goals),
            "by_status": goal_status,
            "avg_progress": round(avg_progress, 3),
        },
        "pending_tasks": pending_tasks,
        "recent_heartbeats": heartbeat_summaries,
    }


# ---------------------------------------------------------------------------
# tenant → company 映射
# ---------------------------------------------------------------------------

def get_or_create_company_for_tenant(db: Session, tenant_id: str) -> str:
    """根据 tenant_id 查找或自动创建 Paperclip 公司，返回 company_id。

    新公司自动：1) 设置使命 2) 同步 220 个专家 Agent。
    """
    company = db.query(PaperclipCompany).filter(
        PaperclipCompany.tenant_id == tenant_id,
    ).first()
    if company:
        return str(company.id)
    # 查 Tenant 表拿名称
    company_name = f"Tenant {tenant_id[:8]}"
    try:
        from app.models.tenant import Tenant
        t = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if t and t.name:
            company_name = t.name
    except Exception:
        pass
    company = PaperclipCompany(
        tenant_id=tenant_id,
        name=company_name,
        mission="全力获取询盘：通过产品展示、内容营销、客户开发、视频矩阵等多渠道帮客户拿到高质量询盘",
        status="active",
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    logger.info("Auto-created PaperclipCompany id=%s tenant_id=%s name=%s", company.id, tenant_id, company_name)
    # 自动同步 220 个专家 Agent
    try:
        _auto_sync_agents(db, str(company.id))
    except Exception as exc:
        logger.warning("Auto-sync agents failed for company %s: %s", company.id, exc)
    # 自动创建默认目标链
    try:
        _auto_create_default_goals(db, str(company.id))
    except Exception as exc:
        logger.warning("Auto-create goals failed for company %s: %s", company.id, exc)
    return str(company.id)


def _auto_sync_agents(db: Session, company_id: str) -> int:
    """为新公司自动同步 Hermes 220 个专家 Agent，返回创建数量。"""
    from app.services.hermes.agency.role_loader import list_roles
    existing_refs = {
        a.agent_ref for a in
        db.query(PaperclipAgent).filter(PaperclipAgent.company_id == company_id).all()
        if a.agent_ref
    }
    roles = list_roles()
    created = 0
    # 角色映射：marketing/sales/strategy → 管理层，其余 → 工人
    _manager_categories = {"marketing", "sales", "strategy", "product"}
    for role in roles:
        role_id = role.get("role_id", "")
        if not role_id or role_id in existing_refs:
            continue
        category = role_id.split("/")[0] if "/" in role_id else ""
        paperclip_role = "cto" if category == "engineering" else "cmo" if category == "marketing" else "worker"
        try:
            agent = PaperclipAgent(
                company_id=company_id,
                name=role.get("name") or role_id.split("/")[-1],
                title=(role.get("description") or "")[:128],
                role=paperclip_role,
                provider="hermes",
                agent_ref=role_id,
                heartbeat_interval_minutes=240,
                monthly_budget_credits=1000.0,
                status="active",
                skills_json=json.dumps(
                    [role.get("emoji", "")] if role.get("emoji") else [],
                    ensure_ascii=False,
                ),
            )
            db.add(agent)
            created += 1
        except Exception:
            pass

    if created:
        db.commit()
        logger.info("Auto-synced %d agents for company %s", created, company_id)
    return created


def _auto_create_default_goals(db: Session, company_id: str) -> None:
    """为新公司自动创建询盘驱动的 4 级目标链。

    Mission → Projects → Goals → Tasks
    所有目标都围绕"帮客户获取询盘"展开。
    """
    from app.models.paperclip import PaperclipGoal as PG, PaperclipTask as PT
    # ── Mission（使命） ──
    mission = PG(
        company_id=company_id,
        title="全力获取高质量询盘",
        description="通过产品展示、内容营销、视频矩阵、客户开发等多渠道，帮客户拿到尽可能多的高质量询盘",
        level="mission",
        status="active",
        priority=0,
    )
    db.add(mission)
    db.flush()
    # ── Projects（项目） ──
    projects = [
        ("产品曝光引流", "让客户的产品在搜索引擎、社交媒体、B2B平台获得最大曝光", 1),
        ("内容营销获客", "通过高质量内容（文章、视频、社交媒体）吸引潜在买家", 2),
        ("主动客户开发", "通过开发信、国际询盘采集、LinkedIn等渠道主动触达买家", 3),
        ("询盘转化跟进", "快速响应询盘、专业报价、持续跟进直到成交", 4),
    ]
    project_ids = []
    for title, desc, pri in projects:
        p = PG(
            company_id=company_id,
            parent_id=str(mission.id),
            title=title,
            description=desc,
            level="project",
            status="active",
            priority=pri,
        )
        db.add(p)
        db.flush()
        project_ids.append(str(p.id))

    # ── Goals（目标） ──
    goals_data = [
        # (parent_project_idx, title, desc, priority)
        (0, "SEO 产品页优化", "确保每个产品页都有完整的 title/meta/结构化数据，提升搜索引擎排名", 1),
        (0, "GEO 地理定向优化", "针对目标出口市场（中东/非洲/东南亚）优化产品页地理相关内容", 2),
        (1, "每周发布行业内容", "每周至少发布 2 篇行业相关内容（产品知识、应用案例、市场趋势）", 1),
        (1, "视频矩阵发布", "将产品视频发布到抖音/快手/TikTok/YouTube等平台，获取视频流量", 2),
        (2, "开发信精准触达", "基于产品画像生成多语言开发信，精准触达目标市场买家", 1),
        (2, "国际询盘采集", "从国际B2B平台、行业展会名录采集潜在买家信息", 2),
        (3, "询盘 5 分钟响应", "确保新询盘在 5 分钟内得到专业回复", 1),
        (3, "报价单自动生成", "基于询盘内容自动生成专业报价单（含MOQ、交期、付款方式）", 2),
    ]
    goal_ids = []
    for pi, title, desc, pri in goals_data:
        g = PG(
            company_id=company_id,
            parent_id=project_ids[pi],
            title=title,
            description=desc,
            level="goal",
            status="active",
            priority=pri,
        )
        db.add(g)
        db.flush()
        goal_ids.append(str(g.id))

    # ── Tasks（自动任务，绑定到对应 Agent） ──
    # 为每个目标创建一个初始任务，由对应角色的 Agent 执行
    _batch_tasks: list = []
    tasks_data = [
        # (goal_idx, title, intent, agent_category_hint)
        (0, "扫描所有产品页 SEO 质量并生成优化建议", "geo_content_matrix", "marketing"),
        (1, "为目标市场生成地理定向内容", "geo_content_matrix", "marketing"),
        (2, "基于客户产品生成本周行业文章", "lead_content_pack", "marketing"),
        (3, "将最新产品视频推送到视频矩阵", "matrix_publish", "marketing"),
        (4, "为目标市场买家生成开发信", "outreach_letter_pack", "sales"),
        (5, "采集国际B2B平台潜在买家", "find_buyers", "sales"),
        (6, "检查并回复待处理询盘", "flywheel_loop", "sales"),
        (7, "为最新询盘生成报价单", "outreach_letter_pack", "sales"),
    ]
    for gi, title, intent, _cat in tasks_data:
        t = PT(
            company_id=company_id,
            goal_id=goal_ids[gi],
            title=title,
            description=f"自动创建的初始任务：{title}",
            intent=intent,
            status="queued",
            priority=1,
        )
        db.add(t)
        _batch_tasks.append(t)

    db.commit()
    for t in _batch_tasks:
        _bridge(db).on_task_created(t)
    logger.info("Auto-created default goals and tasks for company %s", company_id)


# ---------------------------------------------------------------------------
# Hermes sync
# ---------------------------------------------------------------------------

def sync_from_hermes(db: Session, tenant_id: str) -> dict[str, Any]:
    """从现有 Hermes agency roles 同步为 Paperclip Agents。

    扫描 agency_roles 目录，将每个角色映射为 PaperclipAgent。
    已存在的 agent_ref 会跳过，避免重复创建。

    Args:
        db: 数据库 session
        tenant_id: 租户 ID（用于关联公司）

    Returns:
        同步结果
    """
    from app.services.hermes.agency.role_loader import list_roles
    # 查找或创建公司
    company = db.query(PaperclipCompany).filter(
        PaperclipCompany.tenant_id == tenant_id,
    ).first()
    if not company:
        company = PaperclipCompany(
            tenant_id=tenant_id,
            name=f"Hermes Sync ({tenant_id[:8]})",
            mission="",
            status="active",
        )
        db.add(company)
        db.commit()
        db.refresh(company)

    company_id = str(company.id)
    # 收集已有 agent_ref
    existing = db.query(PaperclipAgent).filter(
        PaperclipAgent.company_id == company_id,
    ).all()
    existing_refs = {a.agent_ref for a in existing if a.agent_ref}
    # 加载 Hermes roles
    roles = list_roles()
    created = 0
    skipped = 0
    errors = 0
    for role in roles:
        role_id = role.get("role_id", "")
        if not role_id or role_id in existing_refs:
            skipped += 1
            continue

        try:
            # 根据角色类别推断 role
            category = role_id.split("/")[0] if "/" in role_id else "other"
            paperclip_role = {
                "marketing": "cmo",
                "tech": "cto",
                "ops": "worker",
                "sales": "worker",
                "content": "worker",
            }.get(category, "worker")
            agent = PaperclipAgent(
                company_id=company_id,
                name=role.get("name") or role_id.split("/")[-1],
                title=role.get("description", "")[:128],
                role=paperclip_role,
                provider="hermes",
                agent_ref=role_id,
                heartbeat_interval_minutes=240,
                monthly_budget_credits=1000.0,
                status="active",
                skills_json=json.dumps(
                    [role.get("emoji", "")] if role.get("emoji") else [],
                    ensure_ascii=False,
                ),
            )
            db.add(agent)
            created += 1
        except Exception as exc:
            errors += 1
            logger.warning("Hermes sync failed for role %s: %s", role_id, exc)

    if created:
        db.commit()

    logger.info(
        "Hermes sync: company=%s created=%d skipped=%d errors=%d",
        company_id, created, skipped, errors,
    )
    return {
        "company_id": company_id,
        "tenant_id": tenant_id,
        "roles_found": len(roles),
        "agents_created": created,
        "agents_skipped": skipped,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# API route compatibility: additional CRUD functions
# ---------------------------------------------------------------------------

def list_companies(db: Session) -> list[dict[str, Any]]:
    """列出所有公司。"""
    companies = db.query(PaperclipCompany).order_by(PaperclipCompany.created_at.desc()).all()
    return [
        {
            "id": str(c.id),
            "tenant_id": str(c.tenant_id),
            "name": c.name,
            "mission": c.mission,
            "status": c.status,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        }
        for c in companies
    ]


def get_company_detail(db: Session, company_id: str) -> dict[str, Any] | None:
    """获取公司详情。"""
    company = db.query(PaperclipCompany).filter(PaperclipCompany.id == company_id).first()
    if not company:
        return None
    agents_count = db.query(PaperclipAgent).filter(PaperclipAgent.company_id == company_id).count()
    goals_count = db.query(PaperclipGoal).filter(PaperclipGoal.company_id == company_id).count()
    return {
        "id": str(company.id),
        "tenant_id": str(company.tenant_id),
        "name": company.name,
        "mission": company.mission,
        "status": company.status,
        "agents_count": agents_count,
        "goals_count": goals_count,
        "created_at": company.created_at.isoformat() if company.created_at else None,
        "updated_at": company.updated_at.isoformat() if company.updated_at else None,
    }


def update_company(db: Session, company_id: str, name: str | None = None, mission: str | None = None, status: str | None = None) -> dict[str, Any] | None:
    """更新公司信息。"""
    company = db.query(PaperclipCompany).filter(PaperclipCompany.id == company_id).first()
    if not company:
        return None
    if name is not None:
        company.name = name
    if mission is not None:
        company.mission = mission
    if status is not None:
        company.status = status
    db.commit()
    db.refresh(company)
    return get_company_detail(db, company_id)


def list_company_agents(db: Session, company_id: str) -> list[dict[str, Any]]:
    """列出公司所有 Agent。"""
    agents = db.query(PaperclipAgent).filter(
        PaperclipAgent.company_id == company_id,
    ).order_by(PaperclipAgent.created_at.desc()).all()
    return [_serialize_agent(a) for a in agents]


def get_agent_detail(db: Session, agent_id: str) -> dict[str, Any] | None:
    """获取 Agent 详情。"""
    agent = db.query(PaperclipAgent).filter(PaperclipAgent.id == agent_id).first()
    if not agent:
        return None
    return _serialize_agent(agent)


def update_agent(db: Session, agent_id: str, title: str | None = None, budget_credits: int | None = None, budget_cents: int | None = None, heartbeat_interval_sec: int | None = None, **kwargs) -> dict[str, Any] | None:
    """更新 Agent 信息。"""
    agent = db.query(PaperclipAgent).filter(PaperclipAgent.id == agent_id).first()
    if not agent:
        return None
    if title is not None:
        agent.title = title
    budget_val = budget_cents if budget_cents is not None else budget_credits
    if budget_val is not None:
        agent.monthly_budget_credits = float(budget_val)
    if heartbeat_interval_sec is not None:
        agent.heartbeat_interval_minutes = int(heartbeat_interval_sec) // 60
    db.commit()
    db.refresh(agent)
    return _serialize_agent(agent)


def pause_agent(db: Session, agent_id: str) -> dict[str, Any] | None:
    """暂停 Agent。"""
    agent = db.query(PaperclipAgent).filter(PaperclipAgent.id == agent_id).first()
    if not agent:
        return None
    agent.status = "paused"
    agent.heartbeat_enabled = False
    db.commit()
    return _serialize_agent(agent)


def resume_agent(db: Session, agent_id: str) -> dict[str, Any] | None:
    """恢复 Agent。"""
    agent = db.query(PaperclipAgent).filter(PaperclipAgent.id == agent_id).first()
    if not agent:
        return None
    agent.status = "active"
    agent.heartbeat_enabled = True
    db.commit()
    return _serialize_agent(agent)


def terminate_agent(db: Session, agent_id: str) -> dict[str, Any] | None:
    """终止 Agent。"""
    agent = db.query(PaperclipAgent).filter(PaperclipAgent.id == agent_id).first()
    if not agent:
        return None
    agent.status = "terminated"
    agent.heartbeat_enabled = False
    db.commit()
    return _serialize_agent(agent)


def build_org_chart(db: Session, company_id: str) -> dict[str, Any]:
    """组织架构树（API 兼容别名）。"""
    return get_org_chart(db, company_id)


def list_company_tasks(db: Session, company_id: str, status: str | None = None, agent_id: str | None = None) -> list[dict[str, Any]]:
    """列出公司任务。"""
    q = db.query(PaperclipTask).filter(PaperclipTask.company_id == company_id)
    if status:
        q = q.filter(PaperclipTask.status == status)
    if agent_id:
        q = q.filter(PaperclipTask.assigned_agent_id == agent_id)
    tasks = q.order_by(PaperclipTask.created_at.desc()).all()
    return [_serialize_task(t) for t in tasks]


def assign_task(db: Session, task_id: str, agent_id: str, instructions: str | None = None) -> dict[str, Any] | None:
    """委派任务给 Agent（API 兼容包装）。"""
    result = delegate_task(db, task_id, agent_id)
    if "error" in result:
        return None
    return result


def execute_task_now(db: Session, task_id: str) -> dict[str, Any] | None:
    """立即执行任务。"""
    task = db.query(PaperclipTask).filter(PaperclipTask.id == task_id).first()
    if not task:
        return None
    agent = None
    if task.assigned_agent_id:
        agent = db.query(PaperclipAgent).filter(PaperclipAgent.id == task.assigned_agent_id).first()
    if not agent:
        task.status = "blocked"
        db.commit()
        return {"task_id": task_id, "status": "blocked", "reason": "no_agent_assigned"}
    from app.services.paperclip.heartbeat_engine import PaperclipHeartbeatEngine
    engine = PaperclipHeartbeatEngine()
    task.status = "running"
    task.started_at = datetime.now(timezone.utc)
    db.commit()
    try:
        result = engine._dispatch_task(db, agent, task)
        return {"task_id": task_id, "status": "success", "result": result}
    except Exception as exc:
        return {"task_id": task_id, "status": "failed", "error": str(exc)[:200]}


def build_company_dashboard(db: Session, company_id: str) -> dict[str, Any]:
    """综合仪表盘（API 兼容别名）。"""
    return get_company_dashboard(db, company_id)


def sync_agents_from_hermes(db: Session, tenant_id: str | None = None) -> dict[str, Any]:
    """从 Hermes 同步 Agent（自动查找/创建公司）。

    优先使用传入的 tenant_id，其次从已有公司推断，
    若公司不存在则使用默认 tenant_id，由 sync_from_hermes 自动创建公司。
    """
    if not tenant_id:
        company = db.query(PaperclipCompany).first()
        tenant_id = str(company.tenant_id) if company else "00000000-0000-0000-0000-000000000000"
    return sync_from_hermes(db, tenant_id)


def _serialize_agent(a: PaperclipAgent) -> dict[str, Any]:
    """序列化 Agent 记录。"""
    skills = []
    try:
        skills = json.loads(a.skills_json or "[]")
    except (json.JSONDecodeError, TypeError):
        pass
    return {
        "id": str(a.id),
        "company_id": str(a.company_id),
        "name": a.name,
        "title": a.title,
        "role": a.role,
        "provider": a.provider,
        "agent_ref": a.agent_ref,
        "parent_id": str(a.parent_id) if a.parent_id else None,
        "heartbeat_interval_minutes": a.heartbeat_interval_minutes,
        "heartbeat_enabled": a.heartbeat_enabled,
        "monthly_budget_credits": a.monthly_budget_credits,
        "used_credits": a.used_credits,
        "status": a.status,
        "skills": skills,
        "last_heartbeat_at": a.last_heartbeat_at.isoformat() if a.last_heartbeat_at else None,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "updated_at": a.updated_at.isoformat() if a.updated_at else None,
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
        "deerflow_job_id": str(t.deerflow_job_id) if t.deerflow_job_id else None,
        "result_json": t.result_json,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
        "started_at": t.started_at.isoformat() if t.started_at else None,
        "finished_at": t.finished_at.isoformat() if t.finished_at else None,
    }
