"""Vector Search Service - Qdrant 向量检索服务

提供基于 Qdrant 的高性能向量搜索能力。
降级策略：Qdrant 不可用时降级到 PostgreSQL pgvector（如果可用）。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)

# 延迟导入 Qdrant 和 Neo4j，避免启动时强依赖未安装的包
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance,
        FieldCondition,
        Filter,
        MatchValue,
        PointIdsList,
        PointStruct,
        Range,
        SearchParams,
        VectorParams,
    )

    _QDRANT_AVAILABLE = True
except ImportError:
    _QDRANT_AVAILABLE = False
    QdrantClient = None  # type: ignore[misc,assignment]
    Distance = None  # type: ignore[misc,assignment]
    FieldCondition = None  # type: ignore[misc,assignment]
    Filter = None  # type: ignore[misc,assignment]
    MatchValue = None  # type: ignore[misc,assignment]
    PointIdsList = None  # type: ignore[misc,assignment]
    PointStruct = None  # type: ignore[misc,assignment]
    Range = None  # type: ignore[misc,assignment]
    SearchParams = None  # type: ignore[misc,assignment]
    VectorParams = None  # type: ignore[misc,assignment]


try:
    from sqlalchemy import text
    from sqlalchemy.orm import Session

    _PGVECTOR_AVAILABLE = True
except ImportError:
    _PGVECTOR_AVAILABLE = False
    text = None  # type: ignore[misc,assignment]
    Session = None  # type: ignore[misc,assignment]

DEFAULT_VECTOR_SIZE = 768
DEFAULT_DISTANCE = "Cosine"

_DISTANCE_MAP = {
    "Cosine": Distance.COSINE if _QDRANT_AVAILABLE else None,
    "Euclidean": Distance.EUCLID if _QDRANT_AVAILABLE else None,
    "Dot": Distance.DOT if _QDRANT_AVAILABLE else None,
    "Manhattan": Distance.MANHATTAN if _QDRANT_AVAILABLE else None,
}


class VectorSearchService:
    """Qdrant 向量检索服务

    支持：
    - 集合管理（创建/删除/信息）
    - 向量增删改查
    - 相似度搜索
    - 混合搜索（关键词 + 向量）
    - pgvector 降级
    """
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._client: Optional[Any] = None
        self._connected = False
        self._pg_fallback_enabled = False
        self._pg_fallback_session_factory: Optional[Any] = None

    def connect(self) -> bool:
        """连接 Qdrant（通过 config.py 配置）

        Returns:
            是否连接成功
        """
        if not _QDRANT_AVAILABLE:
            logger.warning("qdrant-client 未安装，尝试启用 pgvector 降级")
            self._try_enable_pg_fallback()
            return False

        host = getattr(settings, "QDRANT_HOST", "localhost")
        port = getattr(settings, "QDRANT_PORT", 6333)
        api_key = getattr(settings, "QDRANT_API_KEY", None)
        try:
            kwargs: dict[str, Any] = {"host": host, "port": port}
            if api_key:
                kwargs["api_key"] = api_key
            self._client = QdrantClient(**kwargs)
            # 健康检查
            self._client.get_collections()
            self._connected = True
            logger.info("Qdrant 连接成功: %s:%s", host, port)
            return True
        except Exception as exc:
            logger.warning("Qdrant 连接失败: %s, host=%s:%s", exc, host, port)
            self._try_enable_pg_fallback()
            return False

    def _try_enable_pg_fallback(self) -> None:
        """尝试启用 PostgreSQL pgvector 降级"""
        if not _PGVECTOR_AVAILABLE:
            return
        db_url = getattr(settings, "DATABASE_URL", "")
        if "postgresql" in db_url.lower() or "postgres" in db_url.lower():
            self._pg_fallback_enabled = True
            logger.info("启用 pgvector 降级（PostgreSQL 已配置）")
            # 延迟导入避免循环依赖
            try:
                from app.core.database import SessionLocal
                self._pg_fallback_session_factory = SessionLocal
            except Exception as exc:
                logger.warning("无法加载 SessionLocal: %s", exc)
                self._pg_fallback_enabled = False
        else:
            logger.info("pgvector 降级不可用（未使用 PostgreSQL）")

    def _ensure_connection(self) -> bool:
        """_ensure_connection。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        if not self._connected:
            return self.connect()
        return True

    def _get_client(self) -> Any:
        """_get_client。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        if not self._ensure_connection():
            raise RuntimeError("Qdrant 未连接且降级不可用")
        return self._client

    # ── 集合管理 ──
    def create_collection(
        self,
        name: str,
        vector_size: int = DEFAULT_VECTOR_SIZE,
        distance: str = DEFAULT_DISTANCE,
    ) -> dict[str, Any]:
        """创建集合

        Args:
            name: 集合名称
            vector_size: 向量维度（默认 768，匹配 nv-embed-v1）
            distance: 距离度量，可选 Cosine/Euclidean/Dot/Manhattan

        Returns:
            操作结果
        """
        if self._pg_fallback_enabled and not self._connected:
            return self._pg_create_collection(name, vector_size, distance)

        client = self._get_client()
        dist = _DISTANCE_MAP.get(distance, Distance.COSINE if _QDRANT_AVAILABLE else None)
        try:
            client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=vector_size, distance=dist),
            )
            return {"success": True, "collection": name, "mode": "qdrant"}
        except Exception as exc:
            logger.error("创建 Qdrant 集合失败: %s", exc)
            raise

    def delete_collection(self, name: str) -> dict[str, Any]:
        """删除集合"""
        if self._pg_fallback_enabled and not self._connected:
            return self._pg_delete_collection(name)

        client = self._get_client()
        try:
            client.delete_collection(collection_name=name)
            return {"success": True, "collection": name, "mode": "qdrant"}
        except Exception as exc:
            logger.error("删除 Qdrant 集合失败: %s", exc)
            raise

    def collection_exists(self, name: str) -> bool:
        """检查集合是否存在"""
        if self._pg_fallback_enabled and not self._connected:
            return self._pg_collection_exists(name)

        client = self._get_client()
        try:
            return client.collection_exists(collection_name=name)
        except Exception:
            return False

    def get_collections(self) -> list[str]:
        """获取所有集合名称"""
        if self._pg_fallback_enabled and not self._connected:
            return self._pg_get_collections()

        client = self._get_client()
        try:
            collections = client.get_collections()
            return [c.name for c in collections.collections]
        except Exception as exc:
            logger.error("获取 Qdrant 集合列表失败: %s", exc)
            return []

    # ── 向量操作 ──
    def upsert_vectors(
        self,
        collection_name: str,
        vectors: list[list[float]],
        payloads: Optional[list[dict[str, Any]]] = None,
        ids: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """插入/更新向量

        Args:
            collection_name: 集合名称
            vectors: 向量列表
            payloads: 每条向量的附加数据（可选）
            ids: 自定义 ID（可选，默认自动生成 UUID）
        """
        if not vectors:
            return {"success": True, "upserted": 0}

        if self._pg_fallback_enabled and not self._connected:
            return self._pg_upsert_vectors(collection_name, vectors, payloads, ids)

        client = self._get_client()
        import uuid
        points = []
        for i, vec in enumerate(vectors):
            point_id = ids[i] if ids and i < len(ids) else str(uuid.uuid4())
            payload = payloads[i] if payloads and i < len(payloads) else {}
            points.append(PointStruct(id=point_id, vector=vec, payload=payload))

        try:
            client.upsert(collection_name=collection_name, points=points)
            return {"success": True, "upserted": len(points), "mode": "qdrant"}
        except Exception as exc:
            logger.error("Qdrant upsert 失败: %s", exc)
            raise

    def search(
        self,
        collection_name: str,
        query_vector: list[float],
        top_k: int = 10,
        filters: Optional[dict[str, Any]] = None,
        with_payload: bool = True,
    ) -> list[dict[str, Any]]:
        """向量相似度搜索

        Args:
            collection_name: 集合名称
            query_vector: 查询向量
            top_k: 返回结果数
            filters: 过滤条件，格式 {"field": "status", "value": "active"}
            with_payload: 是否返回 payload

        Returns:
            搜索结果列表，每项包含 id, score, payload
        """
        if self._pg_fallback_enabled and not self._connected:
            return self._pg_search(collection_name, query_vector, top_k, filters)

        client = self._get_client()
        qdrant_filter = self._build_qdrant_filter(filters) if filters else None
        try:
            results = client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=top_k,
                query_filter=qdrant_filter,
                with_payload=with_payload,
                search_params=SearchParams(hnsw_ef=128, exact=False),
            )
            return [
                {
                    "id": str(r.id),
                    "score": float(r.score),
                    "payload": r.payload if with_payload else None,
                }
                for r in results
            ]
        except Exception as exc:
            logger.error("Qdrant 搜索失败: %s", exc)
            raise

    def delete_vectors(
        self,
        collection_name: str,
        point_ids: list[str],
    ) -> dict[str, Any]:
        """删除指定向量

        Args:
            collection_name: 集合名称
            point_ids: 要删除的 point ID 列表
        """
        if not point_ids:
            return {"success": True, "deleted": 0}

        if self._pg_fallback_enabled and not self._connected:
            return self._pg_delete_vectors(collection_name, point_ids)

        client = self._get_client()
        try:
            client.delete(
                collection_name=collection_name,
                points_selector=PointIdsList(points=point_ids),
            )
            return {"success": True, "deleted": len(point_ids), "mode": "qdrant"}
        except Exception as exc:
            logger.error("Qdrant 删除向量失败: %s", exc)
            raise

    def hybrid_search(
        self,
        collection_name: str,
        query_text: str,
        query_vector: list[float],
        top_k: int = 10,
        text_boost: float = 0.3,
    ) -> list[dict[str, Any]]:
        """混合搜索：关键词 + 向量

        当前实现：先用向量搜索，然后在 payload 中匹配关键词做加权重排。
        未来可接入 Qdrant 原生 sparse vector 或 BM25。

        Args:
            collection_name: 集合名称
            query_text: 查询文本（用于关键词匹配）
            query_vector: 查询向量
            top_k: 返回结果数
            text_boost: 文本匹配得分在最终排序中的权重

        Returns:
            重排后的搜索结果
        """
        # 扩大搜索范围以便重排
        candidates = self.search(
            collection_name=collection_name,
            query_vector=query_vector,
            top_k=max(top_k * 3, 30),
            with_payload=True,
        )
        if not query_text or not query_text.strip():
            return candidates[:top_k]

        keywords = query_text.lower().split()
        scored = []
        for item in candidates:
            text_score = 0.0
            payload = item.get("payload") or {}
            # 在常见文本字段中匹配关键词
            for field in ("title", "content", "name", "description", "text"):
                val = payload.get(field)
                if isinstance(val, str):
                    val_lower = val.lower()
                    for kw in keywords:
                        if kw in val_lower:
                            text_score += 1.0
            # 混合得分 = 向量相似度 * (1 - text_boost) + 文本得分 * text_boost
            # 文本得分需要归一化到 [0, 1]
            max_text_score = max(len(keywords), 1)
            normalized_text = min(text_score / max_text_score, 1.0)
            combined = item["score"] * (1 - text_boost) + normalized_text * text_boost
            scored.append({**item, "hybrid_score": combined, "text_score": normalized_text})

        scored.sort(key=lambda x: x["hybrid_score"], reverse=True)
        return scored[:top_k]

    def _build_qdrant_filter(self, filters: dict[str, Any]) -> Any:
        """构建 Qdrant Filter"""
        conditions = []
        for key, value in filters.items():
            if isinstance(value, dict):
                # 范围过滤，如 {"gte": 0.5}
                range_spec = {}
                if "gte" in value:
                    range_spec["gte"] = value["gte"]
                if "lte" in value:
                    range_spec["lte"] = value["lte"]
                if "gt" in value:
                    range_spec["gt"] = value["gt"]
                if "lt" in value:
                    range_spec["lt"] = value["lt"]
                conditions.append(
                    FieldCondition(key=key, range=Range(**range_spec))
                )
            else:
                conditions.append(
                    FieldCondition(key=key, match=MatchValue(value=value))
                )
        return Filter(must=conditions)

    # ── pgvector 降级实现 ──
    def _pg_collection_exists(self, name: str) -> bool:
        """_pg_collection_exists。

        参数说明：
        :param self: 参数 self
        :param name: 参数 name
        :return: 返回处理结果。
        """
        try:
            with self._pg_fallback_session_factory() as db:  # type: ignore[call-arg]
                result = db.execute(
                    text("""
                        SELECT EXISTS (
                            SELECT 1 FROM pg_tables
                            WHERE schemaname = 'public' AND tablename = :name
                        )
                    """),
                    {"name": name},
                ).scalar()
                return bool(result)
        except Exception as exc:
            logger.warning("pgvector 检查集合失败: %s", exc)
            return False

    def _pg_get_collections(self) -> list[str]:
        """_pg_get_collections。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        try:
            with self._pg_fallback_session_factory() as db:  # type: ignore[call-arg]
                result = db.execute(
                    text("""
                        SELECT tablename FROM pg_tables
                        WHERE schemaname = 'public'
                        AND tablename LIKE 'qdrant_%'
                    """)
                ).fetchall()
                return [row[0] for row in result]
        except Exception as exc:
            logger.warning("pgvector 获取集合失败: %s", exc)
            return []

    def _pg_create_collection(
        self, name: str, vector_size: int, distance: str
    ) -> dict[str, Any]:
        """_pg_create_collection。

        参数说明：
        :param self: 参数 self
        :param name: 参数 name
        :param vector_size: 参数 vector_size
        :param distance: 参数 distance
        :return: 返回处理结果。
        """
        try:
            with self._pg_fallback_session_factory() as db:  # type: ignore[call-arg]
                # 确保 pgvector 扩展已启用
                db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                # 创建表（简化版）
                db.execute(
                    text(f"""
                        CREATE TABLE IF NOT EXISTS {name} (
                            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                            vector vector({vector_size}),
                            payload JSONB DEFAULT '{{}}',
                            created_at TIMESTAMP DEFAULT NOW()
                        )
                    """)
                )
                # 创建向量索引
                db.execute(
                    text(f"""
                        CREATE INDEX IF NOT EXISTS idx_{name}_vector
                        ON {name} USING ivfflat (vector vector_cosine_ops)
                    """)
                )
                db.commit()
                return {"success": True, "collection": name, "mode": "pgvector"}
        except Exception as exc:
            logger.error("pgvector 创建集合失败: %s", exc)
            raise

    def _pg_delete_collection(self, name: str) -> dict[str, Any]:
        """_pg_delete_collection。

        参数说明：
        :param self: 参数 self
        :param name: 参数 name
        :return: 返回处理结果。
        """
        try:
            with self._pg_fallback_session_factory() as db:  # type: ignore[call-arg]
                db.execute(text(f"DROP TABLE IF EXISTS {name}"))
                db.commit()
                return {"success": True, "collection": name, "mode": "pgvector"}
        except Exception as exc:
            logger.error("pgvector 删除集合失败: %s", exc)
            raise

    def _pg_upsert_vectors(
        self,
        collection_name: str,
        vectors: list[list[float]],
        payloads: Optional[list[dict[str, Any]]],
        ids: Optional[list[str]],
    ) -> dict[str, Any]:
        """_pg_upsert_vectors。

        参数说明：
        :param self: 参数 self
        :param collection_name: 参数 collection_name
        :param vectors: 参数 vectors
        :param payloads: 参数 payloads
        :param ids: 参数 ids
        :return: 返回处理结果。
        """
        import uuid
        import json
        try:
            with self._pg_fallback_session_factory() as db:  # type: ignore[call-arg]
                upserted = 0
                for i, vec in enumerate(vectors):
                    point_id = ids[i] if ids and i < len(ids) else str(uuid.uuid4())
                    payload = payloads[i] if payloads and i < len(payloads) else {}
                    db.execute(
                        text(f"""
                            INSERT INTO {collection_name} (id, vector, payload)
                            VALUES (:id, :vector, :payload)
                            ON CONFLICT (id) DO UPDATE SET
                                vector = EXCLUDED.vector,
                                payload = EXCLUDED.payload
                        """),
                        {
                            "id": point_id,
                            "vector": str(vec),
                            "payload": json.dumps(payload),
                        },
                    )
                    upserted += 1
                db.commit()
                return {"success": True, "upserted": upserted, "mode": "pgvector"}
        except Exception as exc:
            logger.error("pgvector upsert 失败: %s", exc)
            raise

    def _pg_search(
        self,
        collection_name: str,
        query_vector: list[float],
        top_k: int,
        filters: Optional[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """_pg_search。

        参数说明：
        :param self: 参数 self
        :param collection_name: 参数 collection_name
        :param query_vector: 参数 query_vector
        :param top_k: 参数 top_k
        :param filters: 参数 filters
        :return: 返回处理结果。
        """
        import json
        try:
            with self._pg_fallback_session_factory() as db:  # type: ignore[call-arg]
                where_clause = ""
                params: dict[str, Any] = {
                    "vector": str(query_vector),
                    "limit": top_k,
                }
                if filters:
                    # 简单支持 payload 字段等值过滤
                    filter_parts = []
                    for key, value in filters.items():
                        filter_parts.append(f"payload->>'{key}' = :f_{key}")
                        params[f"f_{key}"] = str(value)
                    if filter_parts:
                        where_clause = "WHERE " + " AND ".join(filter_parts)

                result = db.execute(
                    text(f"""
                        SELECT id, vector <=> :vector AS distance, payload
                        FROM {collection_name}
                        {where_clause}
                        ORDER BY vector <=> :vector
                        LIMIT :limit
                    """),
                    params,
                ).fetchall()
                return [
                    {
                        "id": str(row[0]),
                        "score": 1.0 - float(row[1]),  # distance -> similarity
                        "payload": json.loads(row[2]) if row[2] else None,
                    }
                    for row in result
                ]
        except Exception as exc:
            logger.error("pgvector 搜索失败: %s", exc)
            raise

    def _pg_delete_vectors(self, collection_name: str, point_ids: list[str]) -> dict[str, Any]:
        """_pg_delete_vectors。

        参数说明：
        :param self: 参数 self
        :param collection_name: 参数 collection_name
        :param point_ids: 参数 point_ids
        :return: 返回处理结果。
        """
        try:
            with self._pg_fallback_session_factory() as db:  # type: ignore[call-arg]
                db.execute(
                    text(f"""
                        DELETE FROM {collection_name}
                        WHERE id = ANY(:ids)
                    """),
                    {"ids": point_ids},
                )
                db.commit()
                return {"success": True, "deleted": len(point_ids), "mode": "pgvector"}
        except Exception as exc:
            logger.error("pgvector 删除向量失败: %s", exc)
            raise


# 模块级单例
_vector_search_service: Optional[VectorSearchService] = None


def get_vector_search_service() -> VectorSearchService:
    """获取全局 VectorSearchService 单例"""
    global _vector_search_service
    if _vector_search_service is None:
        _vector_search_service = VectorSearchService()
    return _vector_search_service
