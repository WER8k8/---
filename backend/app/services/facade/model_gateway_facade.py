"""大模型网关防腐层 (Anti-Corruption Layer) - 改造 10

应用 Strangler Fig 模式，在现有的大模型调用服务（如 OpenAI、Gemini 等直连）之上，
建立一个统一的接口外观（Facade）。

所有的核心业务逻辑（如 AI 任务处理、内容生成）应当依赖于这个抽象层，而不是直接引用
具体的 SDK。当未来需要将大模型调用拆分为独立的微服务（处理计费、限流、高并发排队）时，
只需要修改此处的底层实现，核心业务层无感。
"""
from typing import Any, Dict, List, Optional
import logging

log = logging.getLogger(__name__)

class ModelGatewayFacade:
    """大模型网关外观，所有业务侧的 AI 请求入口。"""

    @classmethod
    async def generate_completion(
        cls, 
        prompt: str, 
        model: str = "default", 
        tenant_id: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """统一的文本生成接口。
        
        未来如果架构演进为独立微服务，此处只需修改为 HTTP/gRPC 调用即可：
        # return await grpc_client.generate(prompt=prompt, model=model, tenant_id=tenant_id)
        """
        log.info("[Strangler] 通过防腐层请求模型: %s (tenant: %s)", model, tenant_id)
        
        # 现阶段：直接路由到单体内的具体实现服务
        # fallback 或 load balance 的策略也可以统一在防腐层内实现
        try:
            from app.services.llm_service import generate_text
            return await generate_text(prompt, model=model, **kwargs)
        except ImportError:
            # 临时 Mock
            return f"Mock response for: {prompt[:20]}..."

    @classmethod
    async def generate_embeddings(
        cls, 
        texts: List[str], 
        tenant_id: Optional[str] = None
    ) -> List[List[float]]:
        """统一的向量化接口。"""
        log.info("[Strangler] 通过防腐层请求向量化, batch=%d (tenant: %s)", len(texts), tenant_id)
        # 预留给外部微服务的插槽
        return [[0.0] * 1536 for _ in texts]
