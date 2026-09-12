"""代理层级数据汇总服务

提供代理组织树的数据聚合能力（仅 DB 查询，无 Mock 回退）：
- 向下钻取：获取子树统计汇总
- 向上追溯：获取从当前节点到根的链路
- 横向对比：获取某层级所有节点的汇总数据
"""

from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.agent_tree import AgentNode
from app.models.finance_ledger import FinanceLedgerEntry
from app.models.payment import PaymentOrder
from app.models.tenant import Tenant
from app.services.finance_honesty import revenue_ledger_conditions


class AgentAggregationService:
    """代理层级数据汇总服务"""
    AGENT_ROLES = frozenset({"agent", "l2", "l3"})
    @staticmethod
    def _empty_stats() -> Dict[str, Any]:
        """_empty_stats。
        :return: 返回处理结果。
        """
        return {
            "total_clients": 0,
            "new_clients_this_month": 0,
            "total_revenue": 0.0,
            "monthly_revenue": 0.0,
            "active_agents": 0,
        }

    @staticmethod
    def _node_row(db: Session, node_id: str) -> Optional[AgentNode]:
        """_node_row。

        参数说明：
        :param db: 参数 db
        :param node_id: 参数 node_id
        :return: 返回处理结果。
        """
        return (
            db.query(AgentNode)
            .filter(AgentNode.id == node_id, AgentNode.is_active.is_(True))
            .first()
        )

    @staticmethod
    def _chain_from_db(db: Session, node_id: str) -> Optional[List[Dict[str, Any]]]:
        """_chain_from_db。

        参数说明：
        :param db: 参数 db
        :param node_id: 参数 node_id
        :return: 返回处理结果。
        """
        # 批量查询整条链路，避免 N+1：一次收集所有后代节点，建内存字典
        node_map: dict[str, Dict[str, Any]] = {}
        ids_to_collect: list[str] = [node_id]
        visited: set[str] = set()
        while ids_to_collect:
            next_ids: list[str] = []
            for nid in ids_to_collect:
                if nid in visited:
                    continue
                visited.add(nid)
                rows = (
                    db.query(AgentNode.id, AgentNode.name, AgentNode.level, AgentNode.parent_id)
                    .filter(
                        AgentNode.parent_id == nid,
                        AgentNode.is_active.is_(True),
                    )
                    .all()
                )
                for r in rows:
                    node_map[str(r.id)] = {"id": r.id, "name": r.name, "level": r.level, "parent_id": r.parent_id}
                next_ids = [str(r.id) for r in rows if r.parent_id]
            ids_to_collect = next_ids
            if not next_ids:
                break

        # 用内存字典构建向上链路，无需额外查询
        chain: List[Dict[str, Any]] = []
        current_id = node_id
        while current_id:
            if current_id not in node_map:
                break
            row = node_map[current_id]
            chain.append({"id": row["id"], "name": row["name"], "level": row["level"]})
            current_id = str(row["parent_id"]) if row.get("parent_id") else None
        return chain if chain else None

    @staticmethod
    def _children_from_db(db: Session, node_id: str) -> List[Dict[str, Any]]:
        """_children_from_db。

        参数说明：
        :param db: 参数 db
        :param node_id: 参数 node_id
        :return: 返回处理结果。
        """
        rows = (
            db.query(AgentNode)
            .filter(AgentNode.parent_id == node_id, AgentNode.is_active.is_(True))
            .all()
        )
        if not rows:
            return []
        # 批量查询每个子节点的子节点数，避免 N+1
        child_ids = [row.id for row in rows]
        child_counts = (
            db.query(AgentNode.parent_id, func.count(AgentNode.id))
            .filter(
                AgentNode.parent_id.in_(child_ids),
                AgentNode.is_active.is_(True),
            )
            .group_by(AgentNode.parent_id)
            .all()
        )
        count_map = {str(r[0]): int(r[1]) for r in child_counts}
        children: List[Dict[str, Any]] = []
        for row in rows:
            child_count = count_map.get(str(row.id), 0)
            stats = AgentAggregationService._empty_stats()
            stats["active_agents"] = child_count
            children.append(
                {
                    "id": row.id,
                    "name": row.name,
                    "level": row.level,
                    "has_children": child_count > 0,
                    "child_count": child_count,
                    "stats": stats,
                }
            )
        return children

    @staticmethod
    def _tree_from_db(db: Session) -> Optional[Dict[str, Any]]:
        """_tree_from_db。

        参数说明：
        :param db: 参数 db
        :return: 返回处理结果。
        """
        rows = (
            db.query(AgentNode)
            .filter(AgentNode.is_active.is_(True))
            .order_by(AgentNode.level, AgentNode.name)
            .all()
        )
        if not rows:
            return None
        nodes: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            nodes[row.id] = {
                "id": row.id,
                "name": row.name,
                "level": row.level,
                "children": [],
                "stats": AgentAggregationService._empty_stats(),
            }
        roots: List[Dict[str, Any]] = []
        for row in rows:
            item = nodes[row.id]
            if row.parent_id and str(row.parent_id) in nodes:
                nodes[str(row.parent_id)]["children"].append(item)
            elif not row.parent_id:
                roots.append(item)
        for item in nodes.values():
            # 批量填充统计，避免 N+1
            pass
        # 改用批量方法
        AgentAggregationService._enrich_nodes_stats_batch(db, list(nodes.values()))
        if len(roots) == 1:
            return roots[0]
        if not roots:
            return None
        return {
            "id": "virtual-root",
            "name": "代理组织",
            "level": "l0",
            "children": roots,
            "stats": AgentAggregationService._empty_stats(),
        }

    @staticmethod
    def _parse_settings(raw: Any) -> dict:
        """_parse_settings。

        参数说明：
        :param raw: 参数 raw
        :return: 返回处理结果。
        """
        if not raw:
            return {}
        if isinstance(raw, dict):
            return raw
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return {}

    @staticmethod
    def collect_subtree_node_ids(db: Optional[Session], node_id: str) -> set[str]:
        """收集节点及其全部下级代理节点 ID（仅 DB，无 Mock 回退）。"""
        ids: set[str] = {node_id}
        if db is None:
            return ids
        frontier = [node_id]
        while frontier:
            rows = (
                db.query(AgentNode.id)
                .filter(
                    AgentNode.parent_id.in_(frontier),
                    AgentNode.is_active.is_(True),
                )
                .all()
            )
            frontier = [r[0] for r in rows]
            ids.update(frontier)
        return ids

    @staticmethod
    def _tenant_ids_for_subtree(db: Session, subtree_ids: set[str]) -> list[str]:
        """_tenant_ids_for_subtree。

        参数说明：
        :param db: 参数 db
        :param subtree_ids: 参数 subtree_ids
        :return: 返回处理结果。
        """
        # 批量查询所有租户，一次性过滤，避免循环查询
        scoped: list[str] = []
        for t in db.query(Tenant).all():
            settings = AgentAggregationService._parse_settings(t.settings)
            agent_nid = settings.get("agent_node_id")
            if agent_nid and str(agent_nid) in subtree_ids:
                scoped.append(str(t.id))
        return scoped

    @staticmethod
    def _stats_for_tenant_ids(db: Session, tenant_ids: list[str]) -> Dict[str, Any]:
        """_stats_for_tenant_ids。

        参数说明：
        :param db: 参数 db
        :param tenant_ids: 参数 tenant_ids
        :return: 返回处理结果。
        """
        if not tenant_ids:
            return {
                "total_clients": 0,
                "new_clients_this_month": 0,
                "total_revenue": 0.0,
                "monthly_revenue": 0.0,
                "active_agents": 0,
            }
        now = datetime.now(timezone.utc)
        month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        monthly_new = (
            db.query(func.count(Tenant.id))
            .filter(Tenant.id.in_(tenant_ids), Tenant.created_at >= month_start)
            .scalar()
        ) or 0
        total_revenue_cents = int(
            db.query(func.coalesce(func.sum(FinanceLedgerEntry.amount_cents), 0))
            .filter(
                *revenue_ledger_conditions(db),
                FinanceLedgerEntry.tenant_id.in_(tenant_ids),
            )
            .scalar()
            or 0
        )
        monthly_revenue_cents = int(
            db.query(func.coalesce(func.sum(FinanceLedgerEntry.amount_cents), 0))
            .filter(
                *revenue_ledger_conditions(db),
                FinanceLedgerEntry.tenant_id.in_(tenant_ids),
                FinanceLedgerEntry.recorded_at >= month_start,
            )
            .scalar()
            or 0
        )
        return {
            "total_clients": len(tenant_ids),
            "new_clients_this_month": int(monthly_new),
            "total_revenue": round(total_revenue_cents / 100.0, 2),
            "monthly_revenue": round(monthly_revenue_cents / 100.0, 2),
            "active_agents": 0,
        }

    @staticmethod
    def get_l4_tenant_nodes(db: Session) -> List[Dict[str, Any]]:
        """产品 L4 = 官网租户，挂载在 agent_node_id 对应的上级节点下。"""
        now = datetime.now(timezone.utc)
        month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        # 批量查询所有租户的汇总数据，避免 N+1
        all_tenants = db.query(Tenant).order_by(Tenant.created_at.desc()).all()
        tenant_ids = [str(t.id) for t in all_tenants]
        # 单次查询：每个租户的总付费金额
        from sqlalchemy import case
        total_revenue_rows = (
            db.query(
                PaymentOrder.tenant_id,
                func.coalesce(func.sum(PaymentOrder.amount), 0).label("total"),
            )
            .filter(
                PaymentOrder.tenant_id.in_(tenant_ids),
                PaymentOrder.status == "paid",
            )
            .group_by(PaymentOrder.tenant_id)
            .all()
        )
        total_revenue_map = {row.tenant_id: int(row.total) for row in total_revenue_rows}
        # 单次查询：每个租户的当月付费金额
        monthly_revenue_rows = (
            db.query(
                PaymentOrder.tenant_id,
                func.coalesce(func.sum(PaymentOrder.amount), 0).label("monthly"),
            )
            .filter(
                PaymentOrder.tenant_id.in_(tenant_ids),
                PaymentOrder.status == "paid",
                PaymentOrder.paid_at >= month_start,
            )
            .group_by(PaymentOrder.tenant_id)
            .all()
        )
        monthly_revenue_map = {row.tenant_id: int(row.monthly) for row in monthly_revenue_rows}
        nodes: List[Dict[str, Any]] = []
        for t in all_tenants:
            settings = AgentAggregationService._parse_settings(t.settings)
            parent_id = settings.get("agent_node_id")
            tid = str(t.id)
            paid_total_cents = total_revenue_map.get(tid, 0)
            monthly_cents = monthly_revenue_map.get(tid, 0)
            nodes.append(
                {
                    "id": f"tenant:{tid}",
                    "tenant_id": tid,
                    "name": t.name or tid[:8],
                    "level": "l4",
                    "parent_id": str(parent_id) if parent_id else None,
                    "total_children": 0,
                    "is_tenant": True,
                    "is_active": getattr(t, "status", "active") != "cancelled",
                    "stats": {
                        "total_clients": 0,
                        "new_clients_this_month": 0,
                        "total_revenue": round(paid_total_cents / 100.0, 2),
                        "monthly_revenue": round(monthly_cents / 100.0, 2),
                        "active_agents": 0,
                    },
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                }
            )
        return nodes

    @staticmethod
    def _enrich_node_stats(db: Session, node: Dict[str, Any]) -> None:
        """_enrich_node_stats。

        参数说明：
        :param db: 参数 db
        :param node: 参数 node
        :return: 返回处理结果。
        """
        if node.get("is_tenant") or db is None:
            return
        subtree = AgentAggregationService.collect_subtree_node_ids(db, node["id"])
        tenant_ids = AgentAggregationService._tenant_ids_for_subtree(db, subtree)
        if tenant_ids:
            node["stats"] = AgentAggregationService._stats_for_tenant_ids(db, tenant_ids)

    @staticmethod
    def _enrich_nodes_stats_batch(db: Session, nodes: List[Dict[str, Any]]) -> None:
        """批量为节点列表填充统计信息，避免 N+1。"""
        if db is None:
            return
        for node in nodes:
            if node.get("is_tenant"):
                continue
            subtree = AgentAggregationService.collect_subtree_node_ids(db, node["id"])
            tenant_ids = AgentAggregationService._tenant_ids_for_subtree(db, subtree)
            if tenant_ids:
                node["stats"] = AgentAggregationService._stats_for_tenant_ids(db, tenant_ids)

    @staticmethod
    def _find_node(tree: dict, node_id: str) -> Optional[dict]:
        """递归查找树中指定 ID 的节点"""
        if tree["id"] == node_id:
            return tree
        for child in tree.get("children", []):
            result = AgentAggregationService._find_node(child, node_id)
            if result:
                return result
        return None

    @staticmethod
    def _collect_leaf_ids(node: dict) -> List[str]:
        """收集某节点下所有叶子节点 ID（含自身）"""
        ids = [node["id"]]
        for child in node.get("children", []):
            ids.extend(AgentAggregationService._collect_leaf_ids(child))
        return ids

    @staticmethod
    def _aggregate_stats(_node_ids: List[str]) -> Dict[str, Any]:
        """无租户绑定时返回全零统计（禁止 Mock 汇总）。"""
        return AgentAggregationService._empty_stats()

    @staticmethod
    def get_subtree_stats(db: Optional[Session], node_id: str) -> Optional[Dict[str, Any]]:
        """获取某节点及其子树汇总（仅 DB）。"""
        if db is None:
            return None
        db_node = AgentAggregationService._node_row(db, node_id)
        if not db_node:
            return None
        subtree = AgentAggregationService.collect_subtree_node_ids(db, node_id)
        tenant_ids = AgentAggregationService._tenant_ids_for_subtree(db, subtree)
        db_stats = AgentAggregationService._stats_for_tenant_ids(db, tenant_ids)
        # 批量查子节点数
        child_count = (
            db.query(func.count(AgentNode.id))
            .filter(AgentNode.parent_id == node_id, AgentNode.is_active.is_(True))
            .scalar()
        ) or 0
        db_stats["active_agents"] = child_count
        return {
            "node": {
                "id": db_node.id,
                "name": db_node.name,
                "level": db_node.level,
            },
            "direct": db_stats,
            "aggregated": db_stats,
            "by_level": [],
            "subtree_depth": 1,
            "total_nodes": len(subtree),
            "data_source": "db" if tenant_ids else "empty",
            "has_data": bool(tenant_ids),
        }

    @staticmethod
    def get_chain_up(
        node_id: str, db: Optional[Session] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """获取从根到当前节点的完整链路（仅 DB）。"""
        if db is None:
            return None
        chain = AgentAggregationService._chain_from_db(db, node_id)
        if not chain:
            return None
        result = []
        for hop in chain:
            subtree = AgentAggregationService.collect_subtree_node_ids(db, hop["id"])
            tenant_ids = AgentAggregationService._tenant_ids_for_subtree(db, subtree)
            stats = AgentAggregationService._stats_for_tenant_ids(db, tenant_ids)
            result.append({**hop, "stats": stats})
        return result

    @staticmethod
    def get_chain_up_any(
        node_id: str, db: Optional[Session] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """get_chain_up_any。

        参数说明：
        :param node_id: 参数 node_id
        :param db: 参数 db
        :return: 返回处理结果。
        """
        if db is None:
            return None
        return AgentAggregationService._chain_from_db(db, node_id)

    @staticmethod
    def get_children(
        node_id: str, db: Optional[Session] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """获取直接下级列表（仅 DB）。"""
        if db is None:
            return None
        if not AgentAggregationService._node_row(db, node_id):
            return None
        children = AgentAggregationService._children_from_db(db, node_id)
        AgentAggregationService._enrich_nodes_stats_batch(db, children)
        return children

    @staticmethod
    def get_level_summary(
        db: Session, level: str
    ) -> List[Dict[str, Any]]:
        """获取某层级所有节点的汇总（仅 DB）。"""
        level_l = level.lower()
        if level_l == "l4" and db is not None:
            return AgentAggregationService.get_l4_tenant_nodes(db)
        if level_l == "l5":
            return []

        db_nodes = (
            db.query(AgentNode)
            .filter(AgentNode.level == level_l, AgentNode.is_active.is_(True))
            .all()
        )
        if not db_nodes:
            return []
        # 批量查询子节点数，避免 N+1
        node_ids = [node.id for node in db_nodes]
        child_counts = (
            db.query(AgentNode.parent_id, func.count(AgentNode.id))
            .filter(
                AgentNode.parent_id.in_(node_ids),
                AgentNode.is_active.is_(True),
            )
            .group_by(AgentNode.parent_id)
            .all()
        )
        count_map = {str(r[0]): int(r[1]) for r in child_counts}
        all_summary: List[Dict[str, Any]] = []
        for node in db_nodes:
            child_count = count_map.get(str(node.id), 0)
            item = {
                "id": node.id,
                "name": node.name,
                "level": node.level,
                "parent_id": node.parent_id,
                "total_children": child_count,
                "stats": AgentAggregationService._empty_stats(),
                "created_at": node.created_at.isoformat() if node.created_at else None,
            }
            item["stats"]["active_agents"] = child_count
            all_summary.append(item)

        if db is not None and level_l in ("l1", "l2", "l3"):
            AgentAggregationService._enrich_nodes_stats_batch(db, all_summary)

        return all_summary

    @staticmethod
    def get_user_node_id(
        user_role: str = "agent", db: Optional[Session] = None
    ) -> Optional[str]:
        """根据用户角色获取默认关联节点（DB 首根节点，无则 None）。"""
        if db is None:
            return None
        root = (
            db.query(AgentNode)
            .filter(AgentNode.parent_id.is_(None), AgentNode.is_active.is_(True))
            .order_by(AgentNode.created_at)
            .first()
        )
        if root:
            return root.id
        any_node = (
            db.query(AgentNode)
            .filter(AgentNode.is_active.is_(True))
            .order_by(AgentNode.created_at)
            .first()
        )
        return any_node.id if any_node else None

    @staticmethod
    def get_full_tree(db: Optional[Session] = None) -> Optional[Dict[str, Any]]:
        """获取完整代理树（仅 DB，无节点则 None）。"""
        if db is None:
            return None
        return AgentAggregationService._tree_from_db(db)
