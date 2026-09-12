"""支付回调验签严格模式 — 单一权威判定。

全仓所有验签 / 严验相关逻辑都必须通过本函数取数，禁止各模块自行用
``os.getenv("PAYMENT_STRICT_VERIFY") in ("1", "true", "yes")`` 重新计算，
否则会出现「路由层生产默认开、内部模块默认关」的语义错位，导致生产默认
配置下通用 ``/notify`` 被伪造支付（见 B-P0 安全止血清单 F1）。
"""
import os


def is_payment_strict() -> bool:
    """是否启用支付回调严验签。

    - 生产环境（``ENVIRONMENT=production``）：默认强制开启，
      除非显式设置 ``PAYMENT_STRICT_VERIFY=0/false/no``。
    - 非生产环境：沿用 ``PAYMENT_STRICT_VERIFY`` 显式开关（默认关闭）。
    """
    env = os.getenv("ENVIRONMENT", "").lower()
    if env == "production":
        return os.getenv("PAYMENT_STRICT_VERIFY", "").lower() not in ("0", "false", "no")
    return os.getenv("PAYMENT_STRICT_VERIFY", "").lower() in ("1", "true", "yes")
