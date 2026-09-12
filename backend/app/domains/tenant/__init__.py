"""租户管理领域 — stub（待从 routes/tenants.py 迁移）"""
from fastapi import APIRouter
from app.domains.base import DomainModule

router = APIRouter(tags=["租户管理"])

class TenantDomain(DomainModule):
    name = "tenant"
    label = "租户管理"
    @property
    def router(self):
        """router。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return router

__all__ = ["TenantDomain"]