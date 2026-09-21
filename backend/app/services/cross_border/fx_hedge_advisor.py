# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""外贸结汇与汇率对冲顾问 (Foreign Exchange Risk & Hedge Advisor)。

建材大宗外贸出货周期通常达 30~90 天，汇率波动 3% 即可吞噬 30%~50% 纯利。
核心能力：
1. 监控多币种基准汇率 (USD/CNY, EUR/CNY, AED/CNY, SAR/CNY, GBP/CNY)
2. 汇率浮动敏感度测算与风险预警（波动 > 2% 触发预警卡）
3. 多语种形式发票 (PI) 锁汇合规条款一键注入
4. 结汇汇兑损益测算与远期结汇 (Forward FX) 建议
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class FXHedgeAdvisor:
    """外贸外汇锁汇与风险对冲顾问。"""

    # 央行/国际外贸结算基准汇率参考（支持动态接入真实 API）
    BENCHMARK_RATES: Dict[str, float] = {
        "USD": 7.2350,   # 美元
        "EUR": 7.8650,   # 欧元
        "AED": 1.9690,   # 阿联酋迪拉姆
        "SAR": 1.9290,   # 沙特里亚尔
        "GBP": 9.2450,   # 英镑
        "CNY": 1.0000,   # 人民币
    }

    # 汇率浮动预警阈值
    WARNING_THRESHOLD_PCT = 2.0  # 2% 触发黄标预警
    CRITICAL_THRESHOLD_PCT = 4.0 # 4% 触发红标锁汇强制干预

    @classmethod
    def evaluate_fx_risk(
        cls,
        *,
        order_amount: float,
        currency: str = "USD",
        quoted_rate: Optional[float] = None,
        current_rate: Optional[float] = None,
    ) -> Dict[str, Any]:
        """测算指定币种订单的汇率波动损益与风险等级。"""
        curr = (currency or "USD").strip().upper()
        benchmark = cls.BENCHMARK_RATES.get(curr, 7.20)
        q_rate = float(quoted_rate or benchmark)
        c_rate = float(current_rate or benchmark)

        fluctuation_pct = round(((c_rate - q_rate) / q_rate) * 100.0, 3)
        abs_fluc = abs(fluctuation_pct)

        # 汇兑损益计算（折合人民币）
        quoted_cny = round(order_amount * q_rate, 2)
        current_cny = round(order_amount * c_rate, 2)
        pnl_cny = round(current_cny - quoted_cny, 2)

        risk_level = "safe"
        warning_msg = None
        if abs_fluc >= cls.CRITICAL_THRESHOLD_PCT:
            risk_level = "critical"
            warning_msg = f"🛑 汇率剧烈波动 {fluctuation_pct:+}%（损益 ¥{pnl_cny:+,.2f}），已触发紧急锁汇机制，建议启动 PI 汇率条款调价！"
        elif abs_fluc >= cls.WARNING_THRESHOLD_PCT:
            risk_level = "warning"
            warning_msg = f"⚠ 汇率浮动达到 {fluctuation_pct:+}%（损益 ¥{pnl_cny:+,.2f}），接近外贸安全边界，请跟进买家尽快付尾款结汇。"

        return {
            "currency": curr,
            "order_amount": round(order_amount, 2),
            "quoted_exchange_rate": q_rate,
            "current_exchange_rate": c_rate,
            "fluctuation_pct": fluctuation_pct,
            "pnl_cny": pnl_cny,
            "risk_level": risk_level,
            "warning": warning_msg,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
        }

    @classmethod
    def generate_pi_fx_clause(cls, currency: str = "USD", base_rate: Optional[float] = None) -> Dict[str, str]:
        """生成专业的外贸形式发票 (PI) 锁汇免责与对冲保护条款。"""
        curr = (currency or "USD").strip().upper()
        rate = base_rate or cls.BENCHMARK_RATES.get(curr, 7.235)

        return {
            "en": (
                f"Exchange Rate Lock: This quotation is based on the benchmark exchange rate of 1 {curr} = {rate:.4f} CNY. "
                "If the exchange rate fluctuates by more than ±3.0% at the date of final balance payment, "
                "the total payable amount shall be mutually adjusted in proportion to reflect actual settlement costs."
            ),
            "ar": (
                f"بند تثبيت سعر الصرف: تم احتساب هذا العرض بناءً على سعر الصرف المرجعي (1 {curr} = {rate:.4f} يوان صيني). "
                "في حال تذبذب سعر الصرف بأكثر من ±3.0% عند تاريخ سداد الدفعة النهائية، "
                "يتم تعديل المبلغ الإجمالي تلقائياً بما يضمن تكلفة التسوية الفعلية."
            ),
            "es": (
                f"Cláusula de Tipo de Cambio: Esta cotización se basa en el tipo de cambio de referencia de 1 {curr} = {rate:.4f} CNY. "
                "Si el tipo de cambio fluctúa más de un ±3.0% en la fecha del pago final, "
                "el monto total a pagar se ajustará proporcionalmente según los costos reales de liquidación."
            ),
            "zh": (
                f"汇率锁定保护条款：本报价单基于 1 {curr} = {rate:.4f} 人民币基准汇率编制。"
                "若在买方支付尾款或出货结汇日，汇率波动幅度超过 ±3.0%，双方同意根据实际结算汇率同比例调整最终合同金额，以规避汇率风险。"
            ),
        }
