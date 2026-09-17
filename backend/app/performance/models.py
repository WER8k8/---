# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
性能预算配置模型
定义性能预算阈值和检查逻辑
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List
from enum import Enum


class BudgetMetric(str, Enum):
    """预算指标类型"""
    LCP = "lcp"  # Largest Contentful Paint
    FCP = "fcp"  # First Contentful Paint
    CLS = "cls"  # Cumulative Layout Shift
    FID = "fid"  # First Input Delay
    TBT = "tbt"  # Total Blocking Time
    TTI = "tti"  # Time to Interactive
    BUNDLE_SIZE = "bundle_size"  # JS Bundle Size
    TRANSFER_SIZE = "transfer_size"  # Total Transfer Size


class BudgetSeverity(str, Enum):
    """预算严重程度"""
    WARNING = "warning"  # 警告（不阻塞）
    ERROR = "error"  # 错误（阻塞发布）


@dataclass
class PerformanceBudget:
    """性能预算配置"""
    name: str  # 预算名称（如 "mobile-homepage"）
    description: str  # 描述
    metric: BudgetMetric  # 指标类型
    threshold: float  # 阈值
    severity: BudgetSeverity  # 严重程度
    device: str = "mobile"  # 设备类型（"mobile" 或 "desktop"）
    url_pattern: Optional[str] = None  # URL模式（正则，用于匹配特定页面）
    def check(self, value: float) -> tuple[bool, str]:
        """
        检查值是否超过预算
        
        Args:
            value: 实际值
            
        Returns:
            (是否通过, 消息)
        """
        passed = True
        message = ""
        if self.metric in [BudgetMetric.LCP, BudgetMetric.FCP, BudgetMetric.FID, 
                         BudgetMetric.TBT, BudgetMetric.TTI]:
            # 时间类指标：值越小越好
            if value > self.threshold:
                passed = False
                message = f"{self.metric.value.upper()} {value:.0f}ms 超过预算 {self.threshold:.0f}ms"
            else:
                message = f"{self.metric.value.upper()} {value:.0f}ms (预算 {self.threshold:.0f}ms)"
        elif self.metric == BudgetMetric.CLS:
            # CLS：值越小越好
            if value > self.threshold:
                passed = False
                message = f"CLS {value:.3f} 超过预算 {self.threshold:.3f}"
            else:
                message = f"CLS {value:.3f} (预算 {self.threshold:.3f})"
        elif self.metric in [BudgetMetric.BUNDLE_SIZE, BudgetMetric.TRANSFER_SIZE]:
            # 大小类指标：值越小越好
            if value > self.threshold:
                passed = False
                message = f"{self.metric.value} {value/1024:.1f}KB 超过预算 {self.threshold/1024:.1f}KB"
            else:
                message = f"{self.metric.value} {value/1024:.1f}KB (预算 {self.threshold/1024:.1f}KB)"
        
        return passed, message


# 默认性能预算配置（移动端）
DEFAULT_MOBILE_BUDGETS: List[PerformanceBudget] = [
    # LCP < 2.5s (Good)
    PerformanceBudget(
        name="mobile-lcp",
        description="移动端LCP预算",
        metric=BudgetMetric.LCP,
        threshold=2500,
        severity=BudgetSeverity.ERROR,
        device="mobile"
    ),
    # FCP < 1.8s (Good)
    PerformanceBudget(
        name="mobile-fcp",
        description="移动端FCP预算",
        metric=BudgetMetric.FCP,
        threshold=1800,
        severity=BudgetSeverity.WARNING,
        device="mobile"
    ),
    # CLS < 0.1 (Good)
    PerformanceBudget(
        name="mobile-cls",
        description="移动端CLS预算",
        metric=BudgetMetric.CLS,
        threshold=0.1,
        severity=BudgetSeverity.ERROR,
        device="mobile"
    ),
    # Bundle Size < 200KB (建议)
    PerformanceBudget(
        name="mobile-bundle",
        description="移动端JS Bundle大小预算",
        metric=BudgetMetric.BUNDLE_SIZE,
        threshold=200 * 1024,  # 200KB
        severity=BudgetSeverity.WARNING,
        device="mobile"
    ),
]


# 默认性能预算配置（桌面端）
DEFAULT_DESKTOP_BUDGETS: List[PerformanceBudget] = [
    # LCP < 2.0s (Good)
    PerformanceBudget(
        name="desktop-lcp",
        description="桌面端LCP预算",
        metric=BudgetMetric.LCP,
        threshold=2000,
        severity=BudgetSeverity.ERROR,
        device="desktop"
    ),
    # FCP < 1.0s (Good)
    PerformanceBudget(
        name="desktop-fcp",
        description="桌面端FCP预算",
        metric=BudgetMetric.FCP,
        threshold=1000,
        severity=BudgetSeverity.WARNING,
        device="desktop"
    ),
    # CLS < 0.1 (Good)
    PerformanceBudget(
        name="desktop-cls",
        description="桌面端CLS预算",
        metric=BudgetMetric.CLS,
        threshold=0.1,
        severity=BudgetSeverity.ERROR,
        device="desktop"
    ),
]


# 导出
__all__ = [
    "BudgetMetric", "BudgetSeverity", "PerformanceBudget",
    "DEFAULT_MOBILE_BUDGETS", "DEFAULT_DESKTOP_BUDGETS"
]
