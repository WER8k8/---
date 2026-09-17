# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""代理层级节点写操作（超管/管理员）。"""

from __future__ import annotations

import uuid
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.agent_tree import AgentNode

VALID_LEVELS = ("l1", "l2", "l3", "l4", "l5")
LEVEL_RANK = {lvl: idx for idx, lvl in enumerate(VALID_LEVELS)}


def _norm_level(level: str) -> str:
    """_norm_level。

    参数说明：
    :param level: 参数 level
    :return: 返回处理结果。
    """
    return (level or "").strip().lower()


def _node_summary(db: Session, node: AgentNode) -> dict[str, Any]:
    """_node_summary。

    参数说明：
    :param db: 参数 db
    :param node: 参数 node
    :return: 返回处理结果。
    """
    child_count = (
        db.query(AgentNode)
        .filter(AgentNode.parent_id == node.id, AgentNode.is_active.is_(True))
        .count()
    )
    return {
        "id": node.id,
        "name": node.name,
        "level": node.level,
        "parent_id": node.parent_id,
        "root_id": node.root_id,
        "is_active": node.is_active,
        "status": node.status,
        "total_children": child_count,
        "stats": {
            "total_clients": 0,
            "new_clients_this_month": 0,
            "total_revenue": 0.0,
            "monthly_revenue": 0.0,
            "active_agents": child_count,
        },
        "created_at": node.created_at.isoformat() if node.created_at else None,
        "updated_at": node.updated_at.isoformat() if node.updated_at else None,
    }


def _validate_parent(level: str, parent_id: Optional[str], db: Session) -> AgentNode:
    """_validate_parent。

    参数说明：
    :param level: 参数 level
    :param parent_id: 参数 parent_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    rank = LEVEL_RANK[level]
    if rank == 0:
        if parent_id:
            raise ValueError("L1 节点不可指定上级")
        return None  # type: ignore[return-value]
    if not parent_id:
        raise ValueError(f"{level.upper()} 节点必须指定上级")
    parent = db.query(AgentNode).filter(AgentNode.id == parent_id).first()
    if not parent or not parent.is_active:
        raise ValueError("上级节点不存在或已停用")
    parent_level = _norm_level(parent.level)
    if LEVEL_RANK.get(parent_level, -1) != rank - 1:
        raise ValueError(f"上级必须是 {VALID_LEVELS[rank - 1].upper()} 层级")
    return parent


def create_agent_node(
    db: Session,
    *,
    name: str,
    level: str,
    parent_id: Optional[str] = None,
    is_active: bool = True,
) -> dict[str, Any]:
    """create_agent_node。

    参数说明：
    :param db: 参数 db
    :param name: 参数 name
    :param level: 参数 level
    :param parent_id: 参数 parent_id
    :param is_active: 参数 is_active
    :return: 返回处理结果。
    """
    lvl = _norm_level(level)
    if lvl not in VALID_LEVELS:
        raise ValueError(f"无效层级，可选: {', '.join(VALID_LEVELS)}")
    title = (name or "").strip()
    if not title:
        raise ValueError("节点名称不能为空")

    parent = _validate_parent(lvl, parent_id, db)
    node = AgentNode(
        id=str(uuid.uuid4()),
        name=title,
        level=lvl,
        parent_id=parent.id if parent else None,
        root_id=None,
        status="active" if is_active else "closed",
        is_active=is_active,
    )
    db.add(node)
    db.flush()
    if parent:
        node.root_id = parent.root_id or parent.id
    else:
        node.root_id = node.id
    db.commit()
    db.refresh(node)
    return _node_summary(db, node)


def update_agent_node(
    db: Session,
    node_id: str,
    *,
    name: Optional[str] = None,
    parent_id: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> dict[str, Any]:
    """update_agent_node。

    参数说明：
    :param db: 参数 db
    :param node_id: 参数 node_id
    :param name: 参数 name
    :param parent_id: 参数 parent_id
    :param is_active: 参数 is_active
    :return: 返回处理结果。
    """
    node = db.query(AgentNode).filter(AgentNode.id == node_id).first()
    if not node:
        raise LookupError("节点不存在")

    if name is not None:
        title = name.strip()
        if not title:
            raise ValueError("节点名称不能为空")
        node.name = title

    if parent_id is not None:
        parent = _validate_parent(_norm_level(node.level), parent_id, db)
        if parent and parent.id == node.id:
            raise ValueError("不可将节点设为自己的上级")
        node.parent_id = parent.id if parent else None
        node.root_id = (parent.root_id or parent.id) if parent else node.id

    if is_active is not None:
        node.is_active = is_active
        node.status = "active" if is_active else "closed"

    db.commit()
    db.refresh(node)
    return _node_summary(db, node)


def delete_agent_node(db: Session, node_id: str) -> dict[str, Any]:
    """delete_agent_node。

    参数说明：
    :param db: 参数 db
    :param node_id: 参数 node_id
    :return: 返回处理结果。
    """
    node = db.query(AgentNode).filter(AgentNode.id == node_id).first()
    if not node:
        raise LookupError("节点不存在")

    active_children = (
        db.query(AgentNode)
        .filter(AgentNode.parent_id == node.id, AgentNode.is_active.is_(True))
        .count()
    )
    if active_children:
        raise ValueError("存在活跃下级节点，请先停用或删除下级")

    node.is_active = False
    node.status = "closed"
    db.commit()
    return {"id": node.id, "deleted": True, "soft": True}
