# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""代理层级树路由

提供代理组织数据的树形结构查询接口：
  - GET /agent-tree/stats       获取当前用户的代理子树汇总
  - GET /agent-tree/chain       获取到根的链路
  - GET /agent-tree/children    获取直接下级列表
  - GET /agent-tree/all-levels  超管看所有级别的汇总
  - GET /agent-tree/full        获取完整树形结构（含统计数据）
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.agent_aggregation_service import AgentAggregationService
from app.services.agent_node_write_service import (
    create_agent_node,
    delete_agent_node,
    update_agent_node,
)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/agent-tree", tags=["代理层级树"])

AGENT_ACCESS_ROLES = frozenset(
    {"admin", "super_admin", "tenant_admin", "l2", "l3"}
)

LEVEL_MAP = {
    "l1": "超管",
    "l2": "省级代理",
    "l3": "市级代理",
    "l4": "官网租户",
}


class AgentNodeWriteBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    level: str = Field(..., description="l1-l5")
    parent_id: str | None = None
    is_active: bool = True


class AgentNodeUpdateBody(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    parent_id: str | None = None
    is_active: bool | None = None


def _require_tree_admin(user: User):
    """
    处理 _require_tree_admin 相关业务逻辑。

    :param user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if user.role not in ("super_admin", "admin"):
        return error_response(403, "权限不足，仅超管/管理员可维护层级节点")
    return None


@router.post("/nodes")
def create_hierarchy_node(
    body: AgentNodeWriteBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建代理层级节点（super_admin / admin）。"""
    denied = _require_tree_admin(current_user)
    if denied:
        return denied
    try:
        node = create_agent_node(
            db,
            name=body.name,
            level=body.level,
            parent_id=body.parent_id,
            is_active=body.is_active,
        )
    except ValueError as exc:
        return error_response(400, str(exc))
    return success_response(data=node, message="节点已创建")


@router.put("/nodes/{node_id}")
def update_hierarchy_node(
    node_id: str,
    body: AgentNodeUpdateBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新代理层级节点。"""
    denied = _require_tree_admin(current_user)
    if denied:
        return denied
    try:
        node = update_agent_node(
            db,
            node_id,
            name=body.name,
            parent_id=body.parent_id,
            is_active=body.is_active,
        )
    except LookupError as exc:
        return error_response(404, str(exc))
    except ValueError as exc:
        return error_response(400, str(exc))
    return success_response(data=node, message="节点已更新")


@router.delete("/nodes/{node_id}")
def delete_hierarchy_node(
    node_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """软删除代理层级节点（停用）。"""
    denied = _require_tree_admin(current_user)
    if denied:
        return denied
    try:
        result = delete_agent_node(db, node_id)
    except LookupError as exc:
        return error_response(404, str(exc))
    except ValueError as exc:
        return error_response(400, str(exc))
    return success_response(data=result, message="节点已停用")


@router.get("/stats")
def get_subtree_stats(
    node_id: str = Query(None, description="代理节点ID，不传则使用当前用户关联节点"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的代理子树汇总

    返回指定节点及其所有子节点的统计数据:
      - node: 当前节点基本信息
      - direct: 本级直接统计数据
      - aggregated: 含所有子节点的汇总数据
      - by_level: 按层级分组的统计数据
    """
    if current_user.role not in AGENT_ACCESS_ROLES:
        return error_response(403, "权限不足")

    target_node_id = node_id or AgentAggregationService.get_user_node_id(
        current_user.role, db
    )
    if not target_node_id:
        return error_response(404, "未配置代理节点")
    result = AgentAggregationService.get_subtree_stats(db, target_node_id)
    if not result:
        return error_response(404, "代理节点不存在")

    return success_response(data=result)


@router.get("/chain")
def get_chain_up(
    node_id: str = Query(..., description="当前代理节点ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取从当前节点到根节点的完整链路

    返回从 L1 到当前节点的逐级信息，每级含统计数据。
    用于面包屑导航或向上追溯场景。
    """
    if current_user.role not in AGENT_ACCESS_ROLES:
        return error_response(403, "权限不足")

    chain = AgentAggregationService.get_chain_up(node_id, db)
    if not chain:
        return error_response(404, "代理节点不存在或链路未找到")

    return success_response(
        data={
            "chain": chain,
            "hops": len(chain),
            "levels": [hop["level"] for hop in chain],
        }
    )


@router.get("/children")
def get_children(
    node_id: str = Query(..., description="父代理节点ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取直接下级列表

    返回指定节点的直接下级，每项含基础统计信息。
    用于树形结构展开下钻场景。
    """
    if current_user.role not in AGENT_ACCESS_ROLES:
        return error_response(403, "权限不足")

    children = AgentAggregationService.get_children(node_id, db)
    if children is None:
        return error_response(404, "代理节点不存在")

    return success_response(
        data={
            "children": children,
            "total": len(children),
        }
    )


@router.get("/all-levels")
def get_all_levels_summary(
    level: str = Query(
        None,
        description="层级编码(l1/l2/l3/l4/l5)，不传则返回所有层级汇总",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """超管查看所有级别的汇总

    支持按层级过滤，返回各层级所有代理节点的统计数据。
    仅 super_admin 和管理员可访问。
    """
    if current_user.role not in ["super_admin", "admin"]:
        return error_response(403, "权限不足，仅超管可查看全局层级汇总")

    valid_levels = ["l1", "l2", "l3", "l4", "l5"]
    if level:
        if level not in valid_levels:
            return error_response(400, f"无效的层级编码，可选: {', '.join(valid_levels)}")
        nodes = AgentAggregationService.get_level_summary(db, level)
        grand_total = _compute_grand_total(nodes)
        return success_response(
            data={
                "level": level,
                "level_label": LEVEL_MAP.get(level, level),
                "nodes": nodes,
                "total_nodes": len(nodes),
                "grand_total": grand_total,
            }
        )

    # 不传 level 时返回所有层级汇总
    all_levels = {}
    grand_totals = {}
    for lvl in valid_levels:
        nodes = AgentAggregationService.get_level_summary(db, lvl)
        total = _compute_grand_total(nodes)
        all_levels[lvl] = {
            "level": lvl,
            "level_label": LEVEL_MAP.get(lvl, lvl),
            "nodes": nodes,
            "total_nodes": len(nodes),
            "grand_total": total,
        }
        grand_totals[lvl] = total

    # 全量总计
    overall = {
        "total_clients": sum(gt["total_clients"] for gt in grand_totals.values()),
        "new_clients_this_month": sum(
            gt["new_clients_this_month"] for gt in grand_totals.values()
        ),
        "total_revenue": round(
            sum(gt["total_revenue"] for gt in grand_totals.values()), 2
        ),
        "monthly_revenue": round(
            sum(gt["monthly_revenue"] for gt in grand_totals.values()), 2
        ),
        "active_agents": sum(gt["active_agents"] for gt in grand_totals.values()),
    }
    return success_response(
        data={
            "levels": all_levels,
            "overall": overall,
        }
    )


@router.get("", include_in_schema=False)
@router.get("/")
@router.get("/full")
def get_full_tree(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取完整代理树形结构（含统计数据）

    返回从根节点开始的完整树结构，每层节点携带统计数据。
    适用于管理后台的完整组织树展示。
    """
    if current_user.role not in ["super_admin", "admin"]:
        return error_response(403, "权限不足，仅超管可查看完整代理树")

    tree = AgentAggregationService.get_full_tree(db)
    if not tree:
        return success_response(data={"has_data": False, "children": []})
    return success_response(data=tree)


def _compute_grand_total(nodes: list) -> dict:
    """计算节点列表的汇总总计"""
    total_clients = sum(n.get("stats", {}).get("total_clients", 0) for n in nodes)
    new_clients = sum(
        n.get("stats", {}).get("new_clients_this_month", 0) for n in nodes
    )
    total_revenue = sum(n.get("stats", {}).get("total_revenue", 0.0) for n in nodes)
    monthly_revenue = sum(
        n.get("stats", {}).get("monthly_revenue", 0.0) for n in nodes
    )
    active_agents = sum(n.get("stats", {}).get("active_agents", 0) for n in nodes)
    return {
        "total_clients": total_clients,
        "new_clients_this_month": new_clients,
        "total_revenue": round(total_revenue, 2),
        "monthly_revenue": round(monthly_revenue, 2),
        "active_agents": active_agents,
    }
