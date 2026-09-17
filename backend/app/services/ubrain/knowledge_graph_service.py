# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Knowledge Graph Service - Neo4j 知识图谱服务

提供基于 Neo4j 的实体图谱构建、查询、最短路径、语义搜索能力。
降级策略：Neo4j 不可用时降级到内存图（networkx，可选）。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

try:
    from neo4j import GraphDatabase
    from neo4j.graph import Node, Relationship

    _NEO4J_AVAILABLE = True
except ImportError:
    _NEO4J_AVAILABLE = False
    GraphDatabase = None  # type: ignore[misc,assignment]
    Node = None  # type: ignore[misc,assignment]
    Relationship = None  # type: ignore[misc,assignment]


try:
    import networkx as nx

    _NETWORKX_AVAILABLE = True
except ImportError:
    _NETWORKX_AVAILABLE = False
    nx = None  # type: ignore[misc,assignment]


class KnowledgeGraphService:
    """Neo4j 知识图谱服务

    支持：
    - 节点/关系 CRUD
    - Cypher 查询
    - 最短路径
    - 邻居查询
    - 批量实体图谱构建
    - 基于实体的语义搜索
    """
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._driver: Optional[Any] = None
        self._connected = False
        self._memory_graph: Optional[Any] = None
        self._use_memory_fallback = False

    def connect(self) -> bool:
        """连接 Neo4j（bolt 协议）

        Returns:
            是否连接成功
        """
        if not _NEO4J_AVAILABLE:
            logger.warning("neo4j 驱动未安装，尝试启用内存图降级")
            self._enable_memory_fallback()
            return False

        uri = getattr(settings, "NEO4J_URI", "")
        user = getattr(settings, "NEO4J_USER", "")
        password = getattr(settings, "NEO4J_PASSWORD", "")
        if not uri or not user:
            logger.warning("Neo4j 配置不完整: uri=%s, user=%s", uri, user)
            self._enable_memory_fallback()
            return False

        try:
            self._driver = GraphDatabase.driver(uri, auth=(user, password))
            # 验证连接
            self._driver.verify_connectivity()
            self._connected = True
            logger.info("Neo4j 连接成功: %s", uri)
            return True
        except Exception as exc:
            logger.warning("Neo4j 连接失败: %s", exc)
            self._enable_memory_fallback()
            return False

    def _enable_memory_fallback(self) -> None:
        """启用内存图降级（networkx）"""
        if _NETWORKX_AVAILABLE:
            self._memory_graph = nx.DiGraph()
            self._use_memory_fallback = True
            logger.info("启用内存图降级（networkx）")
        else:
            logger.warning("networkx 未安装，内存图降级不可用")
            self._use_memory_fallback = False

    def _ensure_connection(self) -> bool:
        """_ensure_connection。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        if not self._connected and not self._use_memory_fallback:
            return self.connect()
        return self._connected or self._use_memory_fallback

    def _get_session(self):
        """_get_session。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        if not self._ensure_connection():
            raise RuntimeError("Neo4j 未连接且降级不可用")
        if self._use_memory_fallback:
            return None
        return self._driver.session(database=getattr(settings, "NEO4J_DATABASE", "neo4j"))

    def close(self) -> None:
        """关闭连接"""
        if self._driver:
            try:
                self._driver.close()
            except Exception as exc:
                logger.debug("Neo4j 关闭异常: %s", exc)
        self._connected = False
        self._use_memory_fallback = False
        self._memory_graph = None

    # ── 节点操作 ──
    def create_node(self, label: str, properties: dict[str, Any]) -> dict[str, Any]:
        """创建节点

        Args:
            label: 节点标签（如 Entity, Product, Concept）
            properties: 节点属性，应包含唯一标识字段（如 entity_id）

        Returns:
            创建结果，包含 node_id
        """
        if self._use_memory_fallback:
            return self._memory_create_node(label, properties)

        node_id = properties.get("entity_id") or properties.get("id")
        if not node_id:
            import uuid
            node_id = str(uuid.uuid4())
            properties["entity_id"] = node_id

        with self._get_session() as session:
            result = session.run(
                f"""
                MERGE (n:{label} {{entity_id: $node_id}})
                SET n += $props
                RETURN n.entity_id AS node_id
                """,
                node_id=node_id,
                props=properties,
            )
            record = result.single()
            return {
                "success": True,
                "node_id": record["node_id"] if record else node_id,
                "mode": "neo4j",
            }

    def get_node(self, label: str, node_id: str) -> Optional[dict[str, Any]]:
        """获取节点"""
        if self._use_memory_fallback:
            return self._memory_get_node(label, node_id)

        with self._get_session() as session:
            result = session.run(
                f"""
                MATCH (n:{label} {{entity_id: $node_id}})
                RETURN n AS node
                """,
                node_id=node_id,
            )
            record = result.single()
            if record:
                node = record["node"]
                return dict(node)
            return None

    def delete_node(self, label: str, node_id: str) -> dict[str, Any]:
        """删除节点及其关系"""
        if self._use_memory_fallback:
            return self._memory_delete_node(label, node_id)

        with self._get_session() as session:
            result = session.run(
                f"""
                MATCH (n:{label} {{entity_id: $node_id}})
                DETACH DELETE n
                RETURN count(n) AS deleted
                """,
                node_id=node_id,
            )
            record = result.single()
            return {
                "success": True,
                "deleted": record["deleted"] if record else 0,
                "mode": "neo4j",
            }

    # ── 关系操作 ──
    def create_relationship(
        self,
        from_id: str,
        to_id: str,
        rel_type: str,
        properties: Optional[dict[str, Any]] = None,
        from_label: str = "Entity",
        to_label: str = "Entity",
    ) -> dict[str, Any]:
        """创建关系

        Args:
            from_id: 起始节点 entity_id
            to_id: 目标节点 entity_id
            rel_type: 关系类型（如 BELONGS_TO, SIMILAR_TO, SUPPLIES）
            properties: 关系属性
            from_label: 起始节点标签
            to_label: 目标节点标签
        """
        if self._use_memory_fallback:
            return self._memory_create_relationship(from_id, to_id, rel_type, properties)

        props = properties or {}
        with self._get_session() as session:
            result = session.run(
                f"""
                MATCH (a:{from_label} {{entity_id: $from_id}})
                MATCH (b:{to_label} {{entity_id: $to_id}})
                MERGE (a)-[r:{rel_type}]->(b)
                SET r += $props
                RETURN id(r) AS rel_id
                """,
                from_id=from_id,
                to_id=to_id,
                props=props,
            )
            record = result.single()
            return {
                "success": True,
                "rel_id": record["rel_id"] if record else None,
                "mode": "neo4j",
            }

    # ── Cypher 查询 ──
    def query_cypher(
        self, cypher_query: str, parameters: Optional[dict[str, Any]] = None
    ) -> list[dict[str, Any]]:
        """执行 Cypher 查询

        Args:
            cypher_query: Cypher 语句
            parameters: 查询参数

        Returns:
            结果记录列表
        """
        if self._use_memory_fallback:
            raise RuntimeError("内存图降级不支持原始 Cypher 查询，请使用高级封装方法")

        params = parameters or {}
        with self._get_session() as session:
            result = session.run(cypher_query, **params)
            records = []
            for record in result:
                row: dict[str, Any] = {}
                for key in record.keys():
                    val = record[key]
                    if isinstance(val, Node):
                        row[key] = dict(val)
                    elif isinstance(val, Relationship):
                        row[key] = {
                            "id": val.id,
                            "type": val.type,
                            "start_node": val.start_node.get("entity_id"),
                            "end_node": val.end_node.get("entity_id"),
                            **dict(val),
                        }
                    elif hasattr(val, "__iter__") and not isinstance(val, (str, bytes)):
                        # 路径等可迭代对象
                        row[key] = list(val)
                    else:
                        row[key] = val
                records.append(row)
            return records

    # ── 图算法 ──
    def find_shortest_path(
        self,
        from_node_id: str,
        to_node_id: str,
        rel_types: Optional[list[str]] = None,
        max_depth: int = 10,
    ) -> list[dict[str, Any]]:
        """最短路径查询

        Args:
            from_node_id: 起始节点 entity_id
            to_node_id: 目标节点 entity_id
            rel_types: 允许的关系类型列表（None 表示全部）
            max_depth: 最大深度

        Returns:
            路径上的节点列表
        """
        if self._use_memory_fallback:
            return self._memory_shortest_path(from_node_id, to_node_id)

        rel_filter = ""
        if rel_types:
            rels = "|".join(f"`{r}`" for r in rel_types)
            rel_filter = f"[{rels}]"

        with self._get_session() as session:
            result = session.run(
                f"""
                MATCH path = shortestPath(
                    (a {{entity_id: $from_id}})-{rel_filter}*1..{max_depth}-(b {{entity_id: $to_id}})
                )
                RETURN [n IN nodes(path) | {{entity_id: n.entity_id, labels: labels(n), props: properties(n)}}] AS node_path,
                       [r IN relationships(path) | {{type: type(r), props: properties(r)}}] AS rel_path,
                       length(path) AS depth
                """,
                from_id=from_node_id,
                to_id=to_node_id,
            )
            record = result.single()
            if record:
                return {
                    "nodes": record["node_path"],
                    "relationships": record["rel_path"],
                    "depth": record["depth"],
                }
            return {"nodes": [], "relationships": [], "depth": 0}

    def get_neighbors(
        self,
        node_id: str,
        rel_types: Optional[list[str]] = None,
        direction: str = "both",
        node_label: str = "Entity",
    ) -> list[dict[str, Any]]:
        """获取邻居节点

        Args:
            node_id: 中心节点 entity_id
            rel_types: 关系类型过滤
            direction: 方向 both/out/in
            node_label: 节点标签

        Returns:
            邻居节点列表
        """
        if self._use_memory_fallback:
            return self._memory_get_neighbors(node_id, rel_types, direction)

        rel_filter = ""
        if rel_types:
            rels = "|".join(f"`{r}`" for r in rel_types)
            rel_filter = f"[r:{rels}]"
        else:
            rel_filter = "[r]"

        if direction == "out":
            pattern = f"(n:{node_label} {{entity_id: $node_id}})-{rel_filter}->(m)"
        elif direction == "in":
            pattern = f"(n:{node_label} {{entity_id: $node_id}})<-{rel_filter}-(m)"
        else:
            pattern = f"(n:{node_label} {{entity_id: $node_id}})-{rel_filter}-(m)"

        with self._get_session() as session:
            result = session.run(
                f"""
                MATCH {pattern}
                RETURN m AS neighbor, type(r) AS rel_type, r AS rel, startNode(r).entity_id AS from_id
                """,
                node_id=node_id,
            )
            neighbors = []
            for record in result:
                neighbor = dict(record["neighbor"])
                neighbor["_rel_type"] = record["rel_type"]
                neighbor["_rel_props"] = dict(record["rel"])
                neighbor["_from_id"] = record["from_id"]
                neighbors.append(neighbor)
            return neighbors

    def build_entity_graph(
        self,
        entities: list[dict[str, Any]],
        relations: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """批量构建实体图谱

        Args:
            entities: 实体列表，每项应包含 label 和 properties（含 entity_id）
            relations: 关系列表，每项包含 from_id, to_id, rel_type, properties

        Returns:
            构建结果统计
        """
        if self._use_memory_fallback:
            return self._memory_build_entity_graph(entities, relations)

        created_nodes = 0
        created_rels = 0
        # 批量创建节点
        for ent in entities:
            label = ent.get("label", "Entity")
            props = ent.get("properties", {})
            if "entity_id" not in props:
                import uuid
                props["entity_id"] = str(uuid.uuid4())
            try:
                self.create_node(label, props)
                created_nodes += 1
            except Exception as exc:
                logger.warning("创建节点失败: %s", exc)

        # 批量创建关系
        for rel in relations:
            try:
                self.create_relationship(
                    from_id=rel["from_id"],
                    to_id=rel["to_id"],
                    rel_type=rel["rel_type"],
                    properties=rel.get("properties", {}),
                    from_label=rel.get("from_label", "Entity"),
                    to_label=rel.get("to_label", "Entity"),
                )
                created_rels += 1
            except Exception as exc:
                logger.warning("创建关系失败: %s", exc)

        return {
            "success": True,
            "nodes_created": created_nodes,
            "relations_created": created_rels,
            "mode": "neo4j",
        }

    def semantic_search(
        self,
        query_text: str,
        top_k: int = 10,
        node_label: str = "Entity",
        search_fields: Optional[list[str]] = None,
    ) -> list[dict[str, Any]]:
        """基于实体的语义搜索

        在节点属性中做模糊匹配，返回最相关的实体。
        如需向量语义搜索，请结合 EmbeddingService + VectorSearchService。

        Args:
            query_text: 查询文本
            top_k: 返回结果数
            node_label: 节点标签
            search_fields: 搜索字段列表（默认 name, description, title）
        """
        if self._use_memory_fallback:
            return self._memory_semantic_search(query_text, top_k)

        # 防 Cypher 注入：节点标签/字段名只允许安全标识符（用户可控，直接拼进 MATCH/WHERE）
        import re as _re
        if not isinstance(node_label, str) or not _re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,63}", node_label):
            raise ValueError(f"非法节点标签: {node_label!r}")
        fields = search_fields or ["name", "description", "title"]
        for f in fields:
            if not isinstance(f, str) or not _re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,63}", f):
                raise ValueError(f"非法搜索字段: {f!r}")
        keywords = query_text.lower().split()
        if not keywords:
            return []

        # 构建 OR 条件
        conditions = []
        for field in fields:
            for kw in keywords:
                conditions.append(f"n.{field} CONTAINS $kw_{field}_{kw}")

        # 参数过多时简化
        if len(conditions) > 20:
            conditions = conditions[:20]

        where_clause = " OR ".join(conditions) if conditions else "1=1"
        params: dict[str, Any] = {"top_k": top_k}
        for field in fields:
            for kw in keywords[:5]:  # 限制参数数量
                params[f"kw_{field}_{kw}"] = kw

        with self._get_session() as session:
            result = session.run(
                f"""
                MATCH (n:{node_label})
                WHERE {where_clause}
                RETURN n AS entity, count {{ MATCH (n)--() }} AS degree
                LIMIT $top_k
                """,
                **params,
            )
            records = []
            for record in result:
                ent = dict(record["entity"])
                ent["_graph_degree"] = record["degree"]
                records.append(ent)
            return records

    # ── 内存图降级实现（networkx） ──
    def _memory_create_node(self, label: str, properties: dict[str, Any]) -> dict[str, Any]:
        """_memory_create_node。

        参数说明：
        :param self: 参数 self
        :param label: 参数 label
        :param properties: 参数 properties
        :return: 返回处理结果。
        """
        node_id = properties.get("entity_id") or properties.get("id")
        if not node_id:
            import uuid
            node_id = str(uuid.uuid4())
            properties["entity_id"] = node_id
        self._memory_graph.add_node(
            node_id,
            label=label,
            **properties,
        )
        return {"success": True, "node_id": node_id, "mode": "memory"}

    def _memory_get_node(self, label: str, node_id: str) -> Optional[dict[str, Any]]:
        """_memory_get_node。

        参数说明：
        :param self: 参数 self
        :param label: 参数 label
        :param node_id: 参数 node_id
        :return: 返回处理结果。
        """
        if node_id not in self._memory_graph:
            return None
        data = dict(self._memory_graph.nodes[node_id])
        data["entity_id"] = node_id
        return data

    def _memory_delete_node(self, label: str, node_id: str) -> dict[str, Any]:
        """_memory_delete_node。

        参数说明：
        :param self: 参数 self
        :param label: 参数 label
        :param node_id: 参数 node_id
        :return: 返回处理结果。
        """
        if node_id in self._memory_graph:
            self._memory_graph.remove_node(node_id)
            return {"success": True, "deleted": 1, "mode": "memory"}
        return {"success": True, "deleted": 0, "mode": "memory"}

    def _memory_create_relationship(
        self,
        from_id: str,
        to_id: str,
        rel_type: str,
        properties: Optional[dict[str, Any]],
    ) -> dict[str, Any]:
        """_memory_create_relationship。

        参数说明：
        :param self: 参数 self
        :param from_id: 参数 from_id
        :param to_id: 参数 to_id
        :param rel_type: 参数 rel_type
        :param properties: 参数 properties
        :return: 返回处理结果。
        """
        props = properties or {}
        self._memory_graph.add_edge(from_id, to_id, rel_type=rel_type, **props)
        return {"success": True, "rel_id": f"{from_id}-{rel_type}->{to_id}", "mode": "memory"}

    def _memory_shortest_path(
        self, from_node_id: str, to_node_id: str
    ) -> list[dict[str, Any]]:
        """_memory_shortest_path。

        参数说明：
        :param self: 参数 self
        :param from_node_id: 参数 from_node_id
        :param to_node_id: 参数 to_node_id
        :return: 返回处理结果。
        """
        if from_node_id not in self._memory_graph or to_node_id not in self._memory_graph:
            return {"nodes": [], "relationships": [], "depth": 0}
        try:
            path = nx.shortest_path(self._memory_graph, from_node_id, to_node_id)
            nodes = []
            rels = []
            for i, node_id in enumerate(path):
                data = dict(self._memory_graph.nodes[node_id])
                data["entity_id"] = node_id
                nodes.append(data)
                if i < len(path) - 1:
                    edge_data = self._memory_graph.get_edge_data(path[i], path[i + 1])
                    rels.append({
                        "type": edge_data.get("rel_type", "RELATED_TO"),
                        "props": {k: v for k, v in edge_data.items() if k != "rel_type"},
                    })
            return {"nodes": nodes, "relationships": rels, "depth": len(path) - 1}
        except nx.NetworkXNoPath:
            return {"nodes": [], "relationships": [], "depth": 0}

    def _memory_get_neighbors(
        self,
        node_id: str,
        rel_types: Optional[list[str]],
        direction: str,
    ) -> list[dict[str, Any]]:
        """_memory_get_neighbors。

        参数说明：
        :param self: 参数 self
        :param node_id: 参数 node_id
        :param rel_types: 参数 rel_types
        :param direction: 参数 direction
        :return: 返回处理结果。
        """
        if node_id not in self._memory_graph:
            return []
        neighbors = []
        if direction in ("both", "out"):
            for succ in self._memory_graph.successors(node_id):
                edge_data = self._memory_graph.get_edge_data(node_id, succ)
                if rel_types and edge_data.get("rel_type") not in rel_types:
                    continue
                data = dict(self._memory_graph.nodes[succ])
                data["entity_id"] = succ
                data["_rel_type"] = edge_data.get("rel_type", "RELATED_TO")
                data["_rel_props"] = edge_data
                data["_from_id"] = node_id
                neighbors.append(data)
        if direction in ("both", "in"):
            for pred in self._memory_graph.predecessors(node_id):
                edge_data = self._memory_graph.get_edge_data(pred, node_id)
                if rel_types and edge_data.get("rel_type") not in rel_types:
                    continue
                data = dict(self._memory_graph.nodes[pred])
                data["entity_id"] = pred
                data["_rel_type"] = edge_data.get("rel_type", "RELATED_TO")
                data["_rel_props"] = edge_data
                data["_from_id"] = pred
                neighbors.append(data)
        return neighbors

    def _memory_build_entity_graph(
        self,
        entities: list[dict[str, Any]],
        relations: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """_memory_build_entity_graph。

        参数说明：
        :param self: 参数 self
        :param entities: 参数 entities
        :param relations: 参数 relations
        :return: 返回处理结果。
        """
        created_nodes = 0
        created_rels = 0
        for ent in entities:
            label = ent.get("label", "Entity")
            props = ent.get("properties", {})
            if "entity_id" not in props:
                import uuid
                props["entity_id"] = str(uuid.uuid4())
            self._memory_graph.add_node(props["entity_id"], label=label, **props)
            created_nodes += 1
        for rel in relations:
            self._memory_graph.add_edge(
                rel["from_id"],
                rel["to_id"],
                rel_type=rel["rel_type"],
                **(rel.get("properties") or {}),
            )
            created_rels += 1
        return {
            "success": True,
            "nodes_created": created_nodes,
            "relations_created": created_rels,
            "mode": "memory",
        }

    def _memory_semantic_search(
        self, query_text: str, top_k: int
    ) -> list[dict[str, Any]]:
        """_memory_semantic_search。

        参数说明：
        :param self: 参数 self
        :param query_text: 参数 query_text
        :param top_k: 参数 top_k
        :return: 返回处理结果。
        """
        keywords = query_text.lower().split()
        scored = []
        for node_id in self._memory_graph.nodes:
            data = self._memory_graph.nodes[node_id]
            score = 0
            for kw in keywords:
                for val in data.values():
                    if isinstance(val, str) and kw in val.lower():
                        score += 1
            if score > 0:
                item = dict(data)
                item["entity_id"] = node_id
                item["_score"] = score
                scored.append(item)
        scored.sort(key=lambda x: x["_score"], reverse=True)
        return scored[:top_k]


# 模块级单例
_kg_service: Optional[KnowledgeGraphService] = None


def get_knowledge_graph_service() -> KnowledgeGraphService:
    """获取全局 KnowledgeGraphService 单例"""
    global _kg_service
    if _kg_service is None:
        _kg_service = KnowledgeGraphService()
    return _kg_service
