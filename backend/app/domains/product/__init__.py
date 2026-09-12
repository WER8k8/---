"""产品管理领域 — stub（待从 routes/products.py 迁移）"""
from fastapi import APIRouter
from app.domains.base import DomainModule

router = APIRouter(tags=["产品管理"])

class ProductDomain(DomainModule):
    name = "product"
    label = "产品管理"
    @property
    def router(self):
        """router。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return router

__all__ = ["ProductDomain"]