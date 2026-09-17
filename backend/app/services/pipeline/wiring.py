# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Pipeline S3 接线（总纲 §6.4 / V1.7 待办）：存量质量件注册入双关卡。

接线清单（全部惰性导入 + 故障隔离；组件不可用 → 跳过该检查器，关卡逻辑不变）：
- CleanseGate（清洗关）：
  - `brand_guard`：hermes/brand_guard.sanitize_public_copy 差异检测
    （净化会改写 = 含品牌风险措辞 → error，须改写后进复核，§6.4-1 聚合项）；
  - `compliance`：compliance_scanner.ComplianceScanner.scan_text（广告法违禁词）。
- ReviewGate（复核关）：
  - `content_scorer`：content_scorer.score_content(title, body) -> 0-100（§6.4-2 复用）；
  - `eeat`（可选，默认关）：EEATScorer.evaluate_eeat(meta['eeat_data'])，
    需结构化内容数据，随链路成熟后启用。

红线与纪律：
- 检查器/打分器带版本标记（CleanseReport.checker_versions 已有留痕，Evidence §1.2-5）；
- 阈值未来走 skills 表版本化 + Canary（迁移 083），本层不硬编码业务阈值来源；
- 组件导入失败不得阻断关卡：build_* 返回的关卡始终可用（内置检查器兜底）。
"""

from __future__ import annotations

import logging
from typing import Callable, Dict, List, Optional

from app.services.pipeline.gates.cleanse import (
    SEVERITY_ERROR,
    SEVERITY_WARNING,
    CleanseGate,
    CleanseIssue,
)
from app.services.pipeline.gates.review import DEFAULT_THRESHOLD, ReviewGate

logger = logging.getLogger(__name__)

Checker = Callable[[str, Dict], List[CleanseIssue]]
Scorer = Callable[[str, Dict], float]


# ---------------------------------------------------------------------------
# 清洗关检查器工厂
# ---------------------------------------------------------------------------

def brand_guard_checker(version: str = "brand_guard-1.0") -> Checker:
    """品牌措辞净化差异检测：净化器会改写 ⇒ 内容含风险措辞 ⇒ error。"""
    def _check(content: str, meta: Dict) -> List[CleanseIssue]:
        """_check。

        参数说明：
        :param content: 参数 content
        :param meta: 参数 meta
        :return: 返回处理结果。
        """
        from app.services.hermes.brand_guard import sanitize_public_copy  # noqa: PLC0415
        sanitized = sanitize_public_copy(content)
        if sanitized != content:
            return [
                CleanseIssue(
                    "brand_guard", SEVERITY_ERROR,
                    "检测到品牌风险措辞（净化器将改写），须修正后方可进入复核",
                )
            ]
        return []

    return _check


def compliance_checker(db, version: str = "compliance-1.0") -> Checker:
    """广告法合规扫描（违禁词）。scanner 惰性初始化一次。"""
    holder: Dict[str, object] = {}
    def _check(content: str, meta: Dict) -> List[CleanseIssue]:
        """_check。

        参数说明：
        :param content: 参数 content
        :param meta: 参数 meta
        :return: 返回处理结果。
        """
        if "scanner" not in holder:
            from app.services.compliance_scanner import ComplianceScanner  # noqa: PLC0415
            holder["scanner"] = ComplianceScanner(db)
        result = holder["scanner"].scan_text(content) or {}
        total = int(result.get("total_issues") or 0)
        if total <= 0:
            return []
        high = int(result.get("high_severity_count") or 0)
        sev = SEVERITY_ERROR if high > 0 else SEVERITY_WARNING
        return [
            CleanseIssue(
                "compliance", sev,
                f"合规扫描发现 {total} 处违规（高危 {high}），禁止进入分发",
            )
        ]

    return _check


def build_cleanse_gate(db=None, extra_checkers: Optional[Dict[str, Checker]] = None) -> CleanseGate:
    """组装清洗关：内置检查器 + 可用的存量检查器（组件故障则跳过并告警）。"""
    extras: Dict[str, Checker] = {}
    try:
        extras["brand_guard"] = brand_guard_checker()
        # 探测可用性（惰性导入在首次调用时才发生；此处仅登记）
    except Exception:  # pragma: no cover — 登记本身不应失败
        logger.warning("pipeline wiring: brand_guard 登记失败，跳过")
    if db is not None:
        try:
            extras["compliance"] = compliance_checker(db)
        except Exception:  # pragma: no cover
            logger.warning("pipeline wiring: compliance 登记失败，跳过")
    if extra_checkers:
        extras.update(extra_checkers)
    return CleanseGate(extra_checkers=extras)


# ---------------------------------------------------------------------------
# 复核关打分器工厂
# ---------------------------------------------------------------------------

def content_scorer_scorer() -> Scorer:
    """内容质量打分（0-100）：包装 content_scorer.score_content。"""
    def _score(content: str, meta: Dict) -> float:
        """_score。

        参数说明：
        :param content: 参数 content
        :param meta: 参数 meta
        :return: 返回处理结果。
        """
        from app.services.content_scorer import score_content  # noqa: PLC0415
        result = score_content(meta.get("title", ""), content, meta.get("keywords"))
        return float(result.get("score", 0) or 0)

    return _score


def eeat_scorer() -> Scorer:
    """EEAT 打分（可选）：需要 meta['eeat_data'] 结构化数据，缺失时报错
    （ReviewGate 会标记 scorer_fault 并阻断自动过——因此仅在启用且数据齐时使用）。"""
    def _score(content: str, meta: Dict) -> float:
        """_score。

        参数说明：
        :param content: 参数 content
        :param meta: 参数 meta
        :return: 返回处理结果。
        """
        from app.services.eeat_scorer import EEATScorer  # noqa: PLC0415
        data = meta.get("eeat_data")
        if not isinstance(data, dict):
            raise ValueError("eeat_data 缺失（启用 eeat 打分必须提供结构化内容数据）")
        result = EEATScorer().evaluate_eeat(data)
        total = result.get("total_score", result.get("total", 0))
        return float(total or 0)

    return _score


def build_review_gate(
    threshold: float = DEFAULT_THRESHOLD,
    include_eeat: bool = False,
    extra_scorers: Optional[Dict[str, Scorer]] = None,
) -> ReviewGate:
    """组装复核关：注册存量打分器。阈值未来走 skills 表版本化（迁移 083）。"""
    from app.services.pipeline.gates import review as review_mod  # noqa: PLC0415
    scorers: Dict[str, Scorer] = {"content_scorer": content_scorer_scorer()}
    if include_eeat:
        scorers["eeat"] = eeat_scorer()
    if extra_scorers:
        scorers.update(extra_scorers)
    for name, scorer in scorers.items():
        review_mod.register_scorer(name, scorer)
    return ReviewGate(threshold=threshold)
