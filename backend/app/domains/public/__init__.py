"""公开API领域 — stub（待从 routes/public_*.py 迁移）"""
from fastapi import APIRouter
from app.domains.base import DomainModule

router = APIRouter(tags=["公开API"])

class PublicDomain(DomainModule):
    name = "public"
    label = "公开API"
    @property
    def router(self):
        """router。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return router

__all__ = ["PublicDomain"]