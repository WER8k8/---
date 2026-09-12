"""Embedding Service - 文本向量生成服务

支持多种模型源：
- NVIDIA NIM (nv-embed-v1)
- OpenAI (text-embedding-3-small/large)
- HuggingFace 本地模型
- 降级：随机向量（测试用）
"""

from __future__ import annotations

import logging
import math
import random
from typing import Optional

import httpx
import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)

DEFAULT_VECTOR_SIZE = 768


class EmbeddingService:
    """文本 Embedding 生成服务"""
    def __init__(self, model: Optional[str] = None):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param model: 参数 model
        :return: 返回处理结果。
        """
        self.model = model or settings.AI_NVIDIA_MODELS.get("embedding", "nvidia/nv-embed-v1")
        self._client: Optional[httpx.Client] = None
        self._dimension = DEFAULT_VECTOR_SIZE

    def _get_http_client(self) -> httpx.Client:
        """_get_http_client。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        if self._client is None:
            self._client = httpx.Client(timeout=60.0)
        return self._client

    def _resolve_provider(self) -> tuple[str, str, Optional[str]]:
        """解析模型所属提供商，返回 (provider, base_url, api_key)"""
        if self.model.startswith("nvidia/") or "nv-embed" in self.model:
            return (
                "nvidia",
                settings.AI_NVIDIA_BASE_URL,
                settings.AI_NVIDIA_API_KEY,
            )
        if self.model.startswith("text-embedding-") or self.model.startswith("openai/"):
            return (
                "openai",
                settings.AI_OPENAI_BASE_URL,
                settings.AI_OPENAI_API_KEY,
            )
        if self.model.startswith("BAAI/") or self.model.startswith("sentence-") or "/" in self.model:
            # 优先尝试 HuggingFace / 本地兼容 endpoint
            return (
                "huggingface",
                settings.AI_OPENAI_BASE_URL,  # 兼容 OpenAI 接口的本地服务
                settings.AI_OPENAI_API_KEY,
            )
        # 默认回退到 NVIDIA
        return (
            "nvidia",
            settings.AI_NVIDIA_BASE_URL,
            settings.AI_NVIDIA_API_KEY,
        )

    def generate_embedding(self, text: str, model: Optional[str] = None) -> list[float]:
        """生成单条文本的 Embedding 向量

        Args:
            text: 输入文本
            model: 可选覆盖模型名

        Returns:
            向量列表（长度为 768 或模型指定维度）

        Raises:
            RuntimeError: 模型服务不可用且未允许降级时
        """
        if not text or not text.strip():
            return self._zero_vector()

        target_model = model or self.model
        provider, base_url, api_key = self._resolve_provider()
        # 如果配置了具体模型覆盖
        if model:
            provider, base_url, api_key = self._resolve_provider_for_model(model)

        # 优先调用远程 API
        if api_key and base_url:
            try:
                return self._call_remote_embedding(text, target_model, base_url, api_key)
            except Exception as exc:
                logger.warning("Embedding API 调用失败: %s, provider=%s", exc, provider)
                # 继续降级
        else:
            logger.warning("Embedding 未配置 API Key，provider=%s", provider)

        # 降级策略
        return self._fallback_embedding(text)

    def generate_batch_embeddings(
        self, texts: list[str], model: Optional[str] = None
    ) -> list[list[float]]:
        """批量生成文本 Embedding

        Args:
            texts: 文本列表
            model: 可选覆盖模型名

        Returns:
            向量列表的列表
        """
        if not texts:
            return []

        target_model = model or self.model
        provider, base_url, api_key = self._resolve_provider()
        if model:
            provider, base_url, api_key = self._resolve_provider_for_model(model)

        if api_key and base_url:
            try:
                return self._call_remote_batch_embedding(texts, target_model, base_url, api_key)
            except Exception as exc:
                logger.warning("批量 Embedding API 调用失败: %s", exc)

        # 降级到逐条生成（本地/随机）
        return [self._fallback_embedding(t) for t in texts]

    def _call_remote_embedding(
        self, text: str, model: str, base_url: str, api_key: str
    ) -> list[float]:
        """调用远程 Embedding API（OpenAI 兼容格式）"""
        client = self._get_http_client()
        url = f"{base_url.rstrip('/')}/embeddings"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "input": text,
            "encoding_format": "float",
        }
        resp = client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        # OpenAI 兼容格式: data[0].embedding
        embedding = data["data"][0]["embedding"]
        self._dimension = len(embedding)
        return embedding

    def _call_remote_batch_embedding(
        self, texts: list[str], model: str, base_url: str, api_key: str
    ) -> list[list[float]]:
        """调用远程批量 Embedding API"""
        client = self._get_http_client()
        url = f"{base_url.rstrip('/')}/embeddings"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "input": texts,
            "encoding_format": "float",
        }
        resp = client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        embeddings = [item["embedding"] for item in data["data"]]
        if embeddings:
            self._dimension = len(embeddings[0])
        return embeddings

    def _resolve_provider_for_model(self, model: str) -> tuple[str, str, Optional[str]]:
        """根据具体模型名解析提供商"""
        if model.startswith("nvidia/") or "nv-embed" in model:
            return "nvidia", settings.AI_NVIDIA_BASE_URL, settings.AI_NVIDIA_API_KEY
        if model.startswith("text-embedding-") or model.startswith("openai/"):
            return "openai", settings.AI_OPENAI_BASE_URL, settings.AI_OPENAI_API_KEY
        return "nvidia", settings.AI_NVIDIA_BASE_URL, settings.AI_NVIDIA_API_KEY

    def _fallback_embedding(self, text: str) -> list[float]:
        """降级 Embedding：优先本地模型，其次随机向量（测试用）"""
        # 环境变量控制是否允许随机降级
        allow_random = (settings.ENVIRONMENT or "").strip().lower() in ("development", "test")
        if allow_random:
            logger.debug("Embedding 降级为随机向量（dev/test 环境）")
            return self._random_vector()
        raise RuntimeError(
            f"Embedding 服务不可用: model={self.model}, "
            "且当前环境不允许随机降级。请配置有效的 AI API Key。"
        )

    def _random_vector(self) -> list[float]:
        """生成随机单位向量（仅用于测试/降级）"""
        vec = np.random.randn(self._dimension).astype(np.float32)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def _zero_vector(self) -> list[float]:
        """零向量"""
        return [0.0] * self._dimension

    @staticmethod
    def calculate_similarity(vec1: list[float], vec2: list[float]) -> float:
        """计算两个向量的余弦相似度

        Args:
            vec1: 向量1
            vec2: 向量2

        Returns:
            余弦相似度，范围 [-1, 1]
        """
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        a = np.array(vec1, dtype=np.float32)
        b = np.array(vec2, dtype=np.float32)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def cosine_distance(self, vec1: list[float], vec2: list[float]) -> float:
        """余弦距离 = 1 - 余弦相似度"""
        return 1.0 - self.calculate_similarity(vec1, vec2)


# 模块级单例
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """获取全局 EmbeddingService 单例"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
