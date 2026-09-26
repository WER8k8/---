"""
Ollama 本地 LLM 推理适配器
零成本 AI 试用方案
"""
import os
import httpx
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class OllamaAdapter:
    """Ollama 本地 LLM 推理客户端"""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=120.0,  # 本地推理可能较慢
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def list_models(self) -> List[Dict[str, Any]]:
        """列出可用模型"""
        client = await self._get_client()
        try:
            response = await client.get("/api/tags")
            response.raise_for_status()
            return response.json().get("models", [])
        except Exception as e:
            logger.error(f"Ollama list models failed: {e}")
            return []

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "qwen2.5:7b",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """聊天补全"""
        client = await self._get_client()
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        try:
            response = await client.post("/api/chat", json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"Ollama chat failed: {e}")
            raise

    async def generate(
        self,
        prompt: str,
        model: str = "qwen2.5:7b",
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """文本生成"""
        client = await self._get_client()
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }
        if system:
            payload["system"] = system
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        try:
            response = await client.post("/api/generate", json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except Exception as e:
            logger.error(f"Ollama generate failed: {e}")
            raise

    async def embeddings(
        self,
        text: str,
        model: str = "nomic-embed-text",
    ) -> List[float]:
        """生成文本嵌入向量"""
        client = await self._get_client()
        payload = {
            "model": model,
            "prompt": text,
        }
        try:
            response = await client.post("/api/embeddings", json=payload)
            response.raise_for_status()
            return response.json().get("embedding", [])
        except Exception as e:
            logger.error(f"Ollama embeddings failed: {e}")
            raise

    async def health_check(self) -> bool:
        """健康检查"""
        client = await self._get_client()
        try:
            response = await client.get("/api/tags")
            return response.status_code == 200
        except Exception:
            return False


# 全局实例
_ollama_adapter: Optional[OllamaAdapter] = None


def get_ollama_adapter() -> OllamaAdapter:
    """获取 Ollama 全局实例"""
    global _ollama_adapter
    if _ollama_adapter is None:
        _ollama_adapter = OllamaAdapter()
    return _ollama_adapter
