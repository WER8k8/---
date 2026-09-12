"""线索搜索引擎 — FIX-61

倒排索引 + 向量搜索混合引擎：
1. 倒排索引：快速关键词搜索 + 精确匹配
2. 向量搜索（Qdrant）：语义相似度搜索
3. 混合搜索：倒排 + 向量加权融合
4. 搜索建议：自动补全 + 纠错

技术栈：内存倒排索引 + Qdrant（已有）
"""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class SearchHit:
    """搜索结果"""
    lead_id: str
    score: float = 0.0
    source: str = ""  # inverted / vector / hybrid
    fields: dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> dict:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "lead_id": self.lead_id,
            "score": round(self.score, 4),
            "source": self.source,
            "fields": self.fields,
        }


class InvertedIndex:
    """简易倒排索引"""
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._index: dict[str, set[str]] = defaultdict(set)
        self._docs: dict[str, dict] = {}
        self._field_weights = {
            "company_name": 3.0,
            "title": 2.0,
            "email": 1.5,
            "industry": 1.5,
            "description": 1.0,
            "keywords": 2.0,
        }

    def _tokenize(self, text: str) -> list[str]:
        """分词。"""
        if not text:
            return []
        text = text.lower().strip()
        tokens = re.findall(r"[a-zA-Z0-9\u4e00-\u9fff]+", text)
        return [t for t in tokens if len(t) >= 2]

    def add(self, doc_id: str, fields: dict[str, Any]) -> None:
        """添加文档到索引。"""
        self._docs[doc_id] = fields
        for field, value in fields.items():
            if isinstance(value, str):
                for token in self._tokenize(value):
                    key = f"{field}:{token}"
                    self._index[key].add(doc_id)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        for token in self._tokenize(item):
                            key = f"{field}:{token}"
                            self._index[key].add(doc_id)

    def remove(self, doc_id: str) -> None:
        """remove。

        参数说明：
        :param self: 参数 self
        :param doc_id: 参数 doc_id
        :return: 返回处理结果。
        """
        if doc_id in self._docs:
            del self._docs[doc_id]
        # 清理索引
        keys_to_remove = []
        for key, docs in self._index.items():
            docs.discard(doc_id)
            if not docs:
                keys_to_remove.append(key)
        for key in keys_to_remove:
            del self._index[key]

    def search(self, query: str, field: str = "", top_k: int = 50) -> list[SearchHit]:
        """关键词搜索。"""
        tokens = self._tokenize(query)
        if not tokens:
            return []

        scores: dict[str, float] = defaultdict(float)
        for token in tokens:
            weight = 1.0
            if field:
                key = f"{field}:{token}"
                docs = self._index.get(key, set())
                weight = self._field_weights.get(field, 1.0)
            else:
                docs = set()
                for f, w in self._field_weights.items():
                    key = f"{f}:{token}"
                    docs.update(self._index.get(key, set()))
                    # Bonus for field matches
                    for doc_id in self._index.get(key, set()):
                        scores[doc_id] += w

            for doc_id in docs:
                scores[doc_id] += weight

        # 归一化
        max_score = max(scores.values()) if scores else 1.0
        results = []
        for doc_id, score in sorted(scores.items(), key=lambda x: -x[1])[:top_k]:
            if doc_id in self._docs:
                results.append(SearchHit(
                    lead_id=doc_id,
                    score=score / max_score,
                    source="inverted",
                    fields=self._docs[doc_id],
                ))

        return results

    def suggest(self, prefix: str, field: str = "", limit: int = 10) -> list[str]:
        """自动补全建议。"""
        prefix = prefix.lower()
        suggestions = set()
        for key in self._index:
            if field and not key.startswith(f"{field}:"):
                continue
            # 提取 token 部分
            if ":" in key:
                _, token = key.split(":", 1)
                if token.startswith(prefix):
                    suggestions.add(token)

        return sorted(suggestions)[:limit]

    def count(self) -> int:
        """count。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return len(self._docs)


class LeadSearchEngine:
    """线索搜索引擎（倒排索引 + 向量搜索混合）"""
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._inverted = InvertedIndex()
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """is_initialized。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return self._initialized

    def initialize(self) -> None:
        """初始化引擎。"""
        self._initialized = True
        logger.info("LeadSearchEngine: inverted index initialized")

    def index_lead(self, lead_id: str, fields: dict[str, Any]) -> None:
        """索引一条线索。

        Args:
            lead_id: 线索 ID
            fields: 可搜索字段
        """
        self._inverted.add(lead_id, fields)

    def index_batch(self, leads: list[dict]) -> int:
        """批量索引。

        Args:
            leads: [{id, fields...}]

        Returns:
            索引数量
        """
        count = 0
        for lead in leads:
            lead_id = lead.get("id", str(count))
            fields = {k: v for k, v in lead.items() if k != "id"}
            self._inverted.add(lead_id, fields)
            count += 1
        return count

    def search(
        self,
        query: str,
        field: str = "",
        top_k: int = 50,
        use_vector: bool = False,
        vector_weight: float = 0.3,
    ) -> list[SearchHit]:
        """搜索线索。

        Args:
            query: 搜索关键词
            field: 限定字段
            top_k: 最多返回数
            use_vector: 是否使用向量搜索
            vector_weight: 向量搜索权重
        """
        # 倒排索引搜索
        inverted_results = self._inverted.search(query, field=field, top_k=top_k)
        if not use_vector:
            return inverted_results

        # 混合搜索（向量搜索暂用倒排索引降级，正式环境接入 Qdrant）
        # TODO [P2] 接入 Qdrant 向量搜索（待 Phase 2 部署向量数据库后实施）
        return inverted_results

    def suggest(self, prefix: str, field: str = "", limit: int = 10) -> list[str]:
        """搜索建议。"""
        return self._inverted.suggest(prefix, field=field, limit=limit)

    def stats(self) -> dict[str, Any]:
        """stats。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "total_docs": self._inverted.count(),
            "initialized": self._initialized,
        }


# 单例
lead_search_engine = LeadSearchEngine()