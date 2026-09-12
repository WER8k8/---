"""Knowledge Graph API - 知识图谱路由

端点：
- POST /kg/query           Cypher 查询
- POST /kg/entity-search   实体语义搜索
- GET  /kg/path/{from_id}/{to_id}  最短路径
- POST /kg/build           批量构建图谱
- POST /kg/node            创建节点
- POST /kg/relationship    创建关系
- GET  /kg/neighbors/{node_id}     获取邻居节点
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.response import success_response
from app.core.security import get_current_user
from app.models.user import User
from app.services.ubrain.knowledge_graph_service import get_knowledge_graph_service

logger = logging.getLogger(__name__)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""
ROUTE_TAGS = ["知识图谱"]

router = APIRouter(prefix="/kg", tags=["知识图谱"])

# ── 请求/响应模型 ──


class CypherQueryRequest(BaseModel):
    """Cypher 查询请求"""
    query: str = Field(..., description="Cypher 查询语句")
    parameters: Optional[dict[str, Any]] = Field(None, description="查询参数")


class EntitySearchRequest(BaseModel):
    """实体语义搜索请求"""
    query_text: str = Field(..., description="查询文本")
    top_k: int = Field(10, ge=1, le=100, description="返回结果数")
    node_label: str = Field("Entity", description="节点标签")
    search_fields: Optional[list[str]] = Field(None, description="搜索字段列表")


class PathRequest(BaseModel):
    """最短路径请求（兼容 POST）"""
    from_id: str = Field(..., description="起始节点 entity_id")
    to_id: str = Field(..., description="目标节点 entity_id")
    rel_types: Optional[list[str]] = Field(None, description="允许的关系类型")
    max_depth: int = Field(10, ge=1, le=50, description="最大深度")


class BuildGraphRequest(BaseModel):
    """批量构建图谱请求"""
    entities: list[dict[str, Any]] = Field(
        ...,
        description="实体列表，每项含 label 和 properties（需含 entity_id）",
    )
    relations: list[dict[str, Any]] = Field(
        ...,
        description="关系列表，每项含 from_id, to_id, rel_type, properties",
    )


class CreateNodeRequest(BaseModel):
    """创建节点请求"""
    label: str = Field("Entity", description="节点标签")
    properties: dict[str, Any] = Field(..., description="节点属性（建议包含 entity_id）")


class CreateRelationshipRequest(BaseModel):
    """创建关系请求"""
    from_id: str = Field(..., description="起始节点 entity_id")
    to_id: str = Field(..., description="目标节点 entity_id")
    rel_type: str = Field(..., description="关系类型，如 BELONGS_TO, SIMILAR_TO")
    properties: Optional[dict[str, Any]] = Field(None, description="关系属性")
    from_label: str = Field("Entity", description="起始节点标签")
    to_label: str = Field("Entity", description="目标节点标签")


class NeighborsRequest(BaseModel):
    """邻居查询请求（兼容 POST）"""
    node_id: str = Field(..., description="中心节点 entity_id")
    rel_types: Optional[list[str]] = Field(None, description="关系类型过滤")
    direction: str = Field("both", description="方向: both/out/in")
    node_label: str = Field("Entity", description="节点标签")


# ── 路由端点 ──


@router.post("/query")
def kg_query(
    req: CypherQueryRequest,
    user: User = Depends(get_current_user),
):
    """执行 Cypher 查询

    注意：需要 Neo4j 连接可用。降级模式下不支持原始 Cypher。
    """
    service = get_knowledge_graph_service()
    try:
        results = service.query_cypher(
            cypher_query=req.query,
            parameters=req.parameters,
        )
        return success_response(data={"results": results})
    except HTTPException:
        raise
    except RuntimeError as exc:
        logger.warning("KG 查询降级限制: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        logger.error("Cypher 查询失败: %s", exc)
        raise HTTPException(status_code=500, detail=f"Cypher 查询失败: {exc}")


@router.post("/entity-search")
def kg_entity_search(
    req: EntitySearchRequest,
    user: User = Depends(get_current_user),
):
    """实体语义搜索

    在节点属性中做关键词模糊匹配，返回最相关的实体。
    """
    service = get_knowledge_graph_service()
    try:
        results = service.semantic_search(
            query_text=req.query_text,
            top_k=req.top_k,
            node_label=req.node_label,
            search_fields=req.search_fields,
        )
        return success_response(
            data={
                "results": results,
                "query_text": req.query_text,
                "top_k": req.top_k,
            }
        )
    except Exception as exc:
        logger.error("实体搜索失败: %s", exc)
        raise HTTPException(status_code=500, detail=f"实体搜索失败: {exc}")


@router.get("/path/{from_id}/{to_id}")
def kg_path(
    from_id: str,
    to_id: str,
    rel_types: Optional[str] = None,
    max_depth: int = 10,
    user: User = Depends(get_current_user),
):
    """最短路径查询

    返回两个节点之间的最短路径。
    rel_types 可传入逗号分隔的关系类型，如 BELONGS_TO,SIMILAR_TO。
    """
    service = get_knowledge_graph_service()
    parsed_rel_types = None
    if rel_types:
        parsed_rel_types = [r.strip() for r in rel_types.split(",") if r.strip()]

    try:
        result = service.find_shortest_path(
            from_node_id=from_id,
            to_node_id=to_id,
            rel_types=parsed_rel_types,
            max_depth=max_depth,
        )
        return success_response(data=result)
    except Exception as exc:
        logger.error("最短路径查询失败: %s", exc)
        raise HTTPException(status_code=500, detail=f"最短路径查询失败: {exc}")


@router.post("/path")
def kg_path_post(
    req: PathRequest,
    user: User = Depends(get_current_user),
):
    """最短路径查询（POST 版本，支持复杂参数）"""
    service = get_knowledge_graph_service()
    try:
        result = service.find_shortest_path(
            from_node_id=req.from_id,
            to_node_id=req.to_id,
            rel_types=req.rel_types,
            max_depth=req.max_depth,
        )
        return success_response(data=result)
    except Exception as exc:
        logger.error("最短路径查询失败: %s", exc)
        raise HTTPException(status_code=500, detail=f"最短路径查询失败: {exc}")


@router.post("/build")
def kg_build(
    req: BuildGraphRequest,
    user: User = Depends(get_current_user),
):
    """批量构建实体图谱

    一次性创建多个节点和关系，适合知识图谱初始化或批量导入。
    """
    service = get_knowledge_graph_service()
    try:
        result = service.build_entity_graph(
            entities=req.entities,
            relations=req.relations,
        )
        return success_response(data=result)
    except Exception as exc:
        logger.error("批量构建图谱失败: %s", exc)
        raise HTTPException(status_code=500, detail=f"批量构建图谱失败: {exc}")


@router.post("/node")
def kg_create_node(
    req: CreateNodeRequest,
    user: User = Depends(get_current_user),
):
    """创建单个节点"""
    service = get_knowledge_graph_service()
    try:
        result = service.create_node(
            label=req.label,
            properties=req.properties,
        )
        return success_response(data=result)
    except Exception as exc:
        logger.error("创建节点失败: %s", exc)
        raise HTTPException(status_code=500, detail=f"创建节点失败: {exc}")


@router.post("/relationship")
def kg_create_relationship(
    req: CreateRelationshipRequest,
    user: User = Depends(get_current_user),
):
    """创建两个节点之间的关系"""
    service = get_knowledge_graph_service()
    try:
        result = service.create_relationship(
            from_id=req.from_id,
            to_id=req.to_id,
            rel_type=req.rel_type,
            properties=req.properties,
            from_label=req.from_label,
            to_label=req.to_label,
        )
        return success_response(data=result)
    except Exception as exc:
        logger.error("创建关系失败: %s", exc)
        raise HTTPException(status_code=500, detail=f"创建关系失败: {exc}")


@router.get("/neighbors/{node_id}")
def kg_neighbors_get(
    node_id: str,
    rel_types: Optional[str] = None,
    direction: str = "both",
    node_label: str = "Entity",
    user: User = Depends(get_current_user),
):
    """获取邻居节点

    rel_types 可传入逗号分隔的关系类型。
    """
    service = get_knowledge_graph_service()
    parsed_rel_types = None
    if rel_types:
        parsed_rel_types = [r.strip() for r in rel_types.split(",") if r.strip()]

    try:
        results = service.get_neighbors(
            node_id=node_id,
            rel_types=parsed_rel_types,
            direction=direction,
            node_label=node_label,
        )
        return success_response(
            data={
                "node_id": node_id,
                "neighbors": results,
                "count": len(results),
            }
        )
    except Exception as exc:
        logger.error("获取邻居节点失败: %s", exc)
        raise HTTPException(status_code=500, detail=f"获取邻居节点失败: {exc}")


@router.post("/neighbors")
def kg_neighbors_post(
    req: NeighborsRequest,
    user: User = Depends(get_current_user),
):
    """获取邻居节点（POST 版本）"""
    service = get_knowledge_graph_service()
    try:
        results = service.get_neighbors(
            node_id=req.node_id,
            rel_types=req.rel_types,
            direction=req.direction,
            node_label=req.node_label,
        )
        return success_response(
            data={
                "node_id": req.node_id,
                "neighbors": results,
                "count": len(results),
            }
        )
    except Exception as exc:
        logger.error("获取邻居节点失败: %s", exc)
        raise HTTPException(status_code=500, detail=f"获取邻居节点失败: {exc}")


@router.get("/node/{label}/{node_id}")
def kg_get_node(
    label: str,
    node_id: str,
    user: User = Depends(get_current_user),
):
    """获取单个节点详情"""
    service = get_knowledge_graph_service()
    try:
        node = service.get_node(label=label, node_id=node_id)
        if node is None:
            raise HTTPException(status_code=404, detail="节点不存在")
        return success_response(data={"node": node})
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("获取节点失败: %s", exc)
        raise HTTPException(status_code=500, detail=f"获取节点失败: {exc}")


@router.delete("/node/{label}/{node_id}")
def kg_delete_node(
    label: str,
    node_id: str,
    user: User = Depends(get_current_user),
):
    """删除节点及其关系"""
    service = get_knowledge_graph_service()
    try:
        result = service.delete_node(label=label, node_id=node_id)
        return success_response(data=result)
    except Exception as exc:
        logger.error("删除节点失败: %s", exc)
        raise HTTPException(status_code=500, detail=f"删除节点失败: {exc}")
