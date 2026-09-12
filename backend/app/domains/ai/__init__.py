"""AI智能领域 — stub（待从 routes/ai_*.py 迁移）"""
from fastapi import APIRouter
from app.domains.base import DomainModule

router = APIRouter(tags=["AI智能"])

class AiDomain(DomainModule):
    name = "ai"
    label = "AI智能"
    @property
    def router(self):
        """router。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return router

__all__ = ["AiDomain"]