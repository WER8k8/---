"""支付服务子包（单一职责拆分）

- wechat_pay: 微信支付 Native / 验签 / 退款底层能力
- payment_service_impl: 支付订单管理、渠道下单、回调与入账

原文件 app.services.payment_service 已改为兼容薄壳，仅 re-export 本包符号，
调用方无需改动。
"""

from .payment_service_impl import PaymentService
from .wechat_pay import WeChatPayService

__all__ = [
    "PaymentService",
    "WeChatPayService",
]
