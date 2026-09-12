"""支付财务领域 — stub（待从 routes/payment.py, finance.py 迁移）"""
from fastapi import APIRouter
from app.domains.base import DomainModule

router = APIRouter(tags=["支付财务"])

class PaymentDomain(DomainModule):
    name = "payment"
    label = "支付财务"
    @property
    def router(self):
        """router。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return router

__all__ = ["PaymentDomain"]