"""租户 RAG 销售话术 — 禁止脱离授权区间报价。"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

# 匹配 ¥123、123元、USD 99.5、$120 等
_PRICE_PATTERN = re.compile(
    r"(?:"
    r"(?:¥|￥|RMB|CNY)\s*(\d+(?:\.\d{1,2})?)"
    r"|(\d+(?:\.\d{1,2})?)\s*(?:元|块)"
    r"|(?:USD|\$)\s*(\d+(?:\.\d{1,2})?)"
    r")",
    re.IGNORECASE,
)

FORBIDDEN_PHRASES = (
    "保证最低价",
    "全网最低",
    "随便报价",
    "口头承诺价格",
    "无需合同即可成交",
)


@dataclass
class PricingGuardResult:
    allowed: bool
    violations: list[str]
    detected_prices: list[float]
    min_allowed: float | None
    max_allowed: float | None
    def to_dict(self) -> dict[str, Any]:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "allowed": self.allowed,
            "violations": self.violations,
            "detected_prices": self.detected_prices,
            "min_allowed": self.min_allowed,
            "max_allowed": self.max_allowed,
        }


def extract_prices(text: str) -> list[float]:
    """extract_prices。

    参数说明：
    :param text: 参数 text
    :return: 返回处理结果。
    """
    prices: list[float] = []
    for m in _PRICE_PATTERN.finditer(text):
        for g in m.groups():
            if g:
                prices.append(float(g))
                break
    return prices


def validate_sales_text(
    text: str,
    *,
    min_price: float | None = None,
    max_price: float | None = None,
    currency_hint: str = "CNY",
) -> PricingGuardResult:
    """校验 AI/销售输出是否含乱报价或违规承诺。"""
    violations: list[str] = []
    lowered = text.lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase in text:
            violations.append(f"含违规承诺：{phrase}")

    detected = extract_prices(text)
    if min_price is not None:
        for p in detected:
            if p < min_price:
                violations.append(
                    f"报价 {p} 低于授权下限 {min_price} ({currency_hint})"
                )
    if max_price is not None:
        for p in detected:
            if p > max_price:
                violations.append(
                    f"报价 {p} 高于授权上限 {max_price} ({currency_hint})"
                )

    if min_price is None and max_price is None and detected:
        violations.append(
            "检测到具体金额但未配置租户授权价区间，请先在后台设置 min/max"
        )

    return PricingGuardResult(
        allowed=len(violations) == 0,
        violations=violations,
        detected_prices=detected,
        min_allowed=min_price,
        max_allowed=max_price,
    )
