# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
GEO Rank Guard — 发布前五维质量门禁
移植自 sourcechain-geo-engine/backend/app/services/rank_guard.py
适配 UJ 项目：与现有 SEO 排名系统、site_audit 联动
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from app.core.config import settings
from app.core.cache import redis_client


@dataclass(frozen=True)
class GuardMetrics:
    """
    质量门禁评估指标
    与 UJ 现有 rank_checker.py + site_audit.py 数据联动
    """
    lcp_ms: int           # LCP 最大内容绘制（毫秒）< 2500 通过
    inp_ms: int           # INP 交互延迟（毫秒）< 200 通过
    error_rate: float     # 错误率（0~1）< 0.01 通过
    inquiry_rate_delta: float   # 询盘率变化（负值表示下降）> -0.05 通过
    rank_signal_delta: float    # 排名信号变化（负值表示下降）> -0.03 通过
    # 扩展指标（UJ 特有）
    seo_audit_score: Optional[float] = None   # SEO 审计评分（0~100）
    geo_indexed_rate: Optional[float] = None  # GEO 收录率（0~1）


@dataclass
class GuardResult:
    """门禁评估结果"""
    passed: bool              # 是否通过门禁
    blocked_reasons: list[str]  # 未通过原因（触发回滚/拦截）
    warning_reasons: list[str]  # 警告（不拦截但记录）
    metrics: GuardMetrics      # 原始指标
    checked_at: str           # 检查时间 ISO 格式


class GEORankGuard:
    """
    GEO 发布质量门禁
    在内容发布前自动评估，不通过则拦截/回滚
    """
    # 门禁阈值（与 sourcechain 对齐，适配 UJ 业务）
    MAX_LCP_MS: int = 2500
    MAX_INP_MS: int = 200
    MAX_ERROR_RATE: float = 0.01
    MAX_NEGATIVE_INQUIRY_DELTA: float = -0.05
    MAX_NEGATIVE_RANK_DELTA: float = -0.03
    # UJ 扩展阈值
    MIN_SEO_AUDIT_SCORE: float = 60.0   # SEO 审计最低分
    MIN_GEO_INDEXED_RATE: float = 0.3     # GEO 最低收录率（30%）
    def __init__(
        self,
        max_lcp_ms: int = 2500,
        max_inp_ms: int = 200,
        max_error_rate: float = 0.01,
    ):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param max_lcp_ms: 参数 max_lcp_ms
        :param max_inp_ms: 参数 max_inp_ms
        :param max_error_rate: 参数 max_error_rate
        :return: 返回处理结果。
        """
        self.MAX_LCP_MS = max_lcp_ms
        self.MAX_INP_MS = max_inp_ms
        self.MAX_ERROR_RATE = max_error_rate

    def evaluate(self, metrics: GuardMetrics) -> GuardResult:
        """
        评估指标是否通过门禁

        Returns:
            GuardResult: 评估结果，passed=False 时触发拦截
        """
        blocked: list[str] = []
        warnings: list[str] = []
        # 核心五维检查（sourcechain 原始逻辑）
        if metrics.lcp_ms > self.MAX_LCP_MS:
            blocked.append("mobile_lcp_regression")
        if metrics.inp_ms > self.MAX_INP_MS:
            blocked.append("mobile_inp_regression")
        if metrics.error_rate > self.MAX_ERROR_RATE:
            blocked.append("error_rate_regression")
        if metrics.inquiry_rate_delta < self.MAX_NEGATIVE_INQUIRY_DELTA:
            blocked.append("inquiry_rate_drop")
        if metrics.rank_signal_delta < self.MAX_NEGATIVE_RANK_DELTA:
            blocked.append("rank_signal_drop")

        # UJ 扩展检查
        if metrics.seo_audit_score is not None:
            if metrics.seo_audit_score < self.MIN_SEO_AUDIT_SCORE:
                warnings.append("seo_audit_score_low")
            elif metrics.seo_audit_score < 40:
                blocked.append("seo_audit_score_critical")

        if metrics.geo_indexed_rate is not None:
            if metrics.geo_indexed_rate < self.MIN_GEO_INDEXED_RATE:
                warnings.append("geo_indexed_rate_low")

        return GuardResult(
            passed=len(blocked) == 0,
            blocked_reasons=blocked,
            warning_reasons=warnings,
            metrics=metrics,
            checked_at=datetime.now(timezone.utc).isoformat(),
        )

    async def evaluate_from_monitoring(
        self,
        page_url: str,
        lcp_ms: int,
        inp_ms: int,
        error_rate: float,
        inquiry_rate: float,
        baseline_inquiry_rate: float,
        rank_signal: float,
        baseline_rank_signal: float,
        seo_audit_score: Optional[float] = None,
        geo_indexed_rate: Optional[float] = None,
    ) -> GuardResult:
        """
        从实时监控数据评估（与 UJ 监控系统联动）

        Args:
            page_url: 页面 URL
            lcp_ms: LCP 实测值
            inp_ms: INP 实测值
            error_rate: 错误率
            inquiry_rate: 当前询盘率
            baseline_inquiry_rate: 基准询盘率
            rank_signal: 当前排名信号
            baseline_rank_signal: 基准排名信号
            seo_audit_score: SEO 审计评分（可选）
            geo_indexed_rate: GEO 收录率（可选）

        Returns:
            GuardResult: 评估结果
        """
        metrics = GuardMetrics(
            lcp_ms=lcp_ms,
            inp_ms=inp_ms,
            error_rate=error_rate,
            inquiry_rate_delta=(inquiry_rate - baseline_inquiry_rate) / max(baseline_inquiry_rate, 0.001),
            rank_signal_delta=(rank_signal - baseline_rank_signal) / max(abs(baseline_rank_signal), 0.001),
            seo_audit_score=seo_audit_score,
            geo_indexed_rate=geo_indexed_rate,
        )
        return self.evaluate(metrics)

    def format_blocked_message(self, result: GuardResult) -> str:
        """格式化拦截原因，用于告警通知"""
        if result.passed:
            return "✅ 质量门禁通过"

        lines = ["🚨 发布被质量门禁拦截："]
        reason_labels = {
            "mobile_lcp_regression": "移动端 LCP 超标（>2.5s）",
            "mobile_inp_regression": "移动端 INP 超标（>200ms）",
            "error_rate_regression": "错误率超标（>1%）",
            "inquiry_rate_drop": "询盘率下降超过 5%",
            "rank_signal_drop": "排名信号下降超过 3%",
            "seo_audit_score_critical": "SEO 审计评分严重不足（<40）",
        }
        for reason in result.blocked_reasons:
            label = reason_labels.get(reason, reason)
            lines.append(f"  ❌ {label}")
        if result.warning_reasons:
            lines.append("⚠️ 警告项：")
            for w in result.warning_reasons:
                lines.append(f"  ⚠️ {w}")
        return "\n".join(lines)


def get_rank_guard() -> GEORankGuard:
    """工厂函数：获取门禁实例"""
    return GEORankGuard()
