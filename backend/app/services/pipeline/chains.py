# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""四链路业务侧关卡接入（总纲 §6.4/§6.6：文章/视频/邮件/多平台分发）。

设计语义（对齐 §6.4 与 §6.6 风险规避）：
- **硬拦截仅发生在清洗关**（品牌风险/广告法违禁 = error）：blocked_cleanse，不得进入分发；
- 复核关裁决为**标记语义**（初接线不阻断既有发布流）：
  auto_pass → approved；human_review → needs_review（发布任务附带人审标记，
  由发布执行侧/人工处置；后续链路成熟后可升级为阻断）。
- 特性开关（默认关，零回归）：
  - `PIPELINE_GATES_ENABLED=1` 总开关；
  - `PIPELINE_GATES_CHAINS=article,video,...` 可选按链路灰度（空=全链路）。
- 接线纪律：业务服务只经 `gate_content()` 单函数；异常一律视为 'off'（不改变原流程）。
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

VERDICT_OFF = "off"                       # 开关未开/异常：不改变原流程
VERDICT_APPROVED = "approved"            # 清洗过 + 复核自动过
VERDICT_NEEDS_REVIEW = "needs_review"    # 清洗过 + 复核需人审（标记语义）
VERDICT_BLOCKED = "blocked_cleanse"      # 清洗未过：硬拦截


@dataclass
class ChainGateReport:
    verdict: str
    cleanse_passed: bool = True
    review_route: Optional[str] = None
    issues: List[Dict[str, str]] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)
    checker_versions: Dict[str, str] = field(default_factory=dict)
    score: Optional[float] = None
    @property
    def blocked(self) -> bool:
        """blocked。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return self.verdict == VERDICT_BLOCKED

    @property
    def review_required(self) -> bool:
        """review_required。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return self.verdict == VERDICT_NEEDS_REVIEW

    def to_meta(self) -> Dict[str, Any]:
        """供发布任务附带的精简元数据（Evidence 留痕）。"""
        return {
            "verdict": self.verdict,
            "review_required": self.review_required,
            "issues": [i.get("code") for i in self.issues][:5],
            "score": self.score,
        }


def gates_enabled(chain: str) -> bool:
    """总开关 + 按链路灰度（§6.6 特性开关按链路灰度）。"""
    if os.environ.get("PIPELINE_GATES_ENABLED", "0") != "1":
        return False
    chains = os.environ.get("PIPELINE_GATES_CHAINS", "").strip()
    if not chains:
        return True
    return chain in {c.strip() for c in chains.split(",") if c.strip()}


def gate_content(
    db,
    *,
    tenant_id: str,
    title: str,
    content: str,
    chain: str = "article",
    meta: Optional[Dict[str, Any]] = None,
) -> ChainGateReport:
    """关卡检查唯一入口。任何异常 → 'off'（不改变原发布流程，零回归红线）。"""
    if not gates_enabled(chain):
        return ChainGateReport(verdict=VERDICT_OFF)

    meta = dict(meta or {})
    meta.setdefault("title", title or "")
    meta.setdefault("chain", chain)
    meta.setdefault("tenant_id", tenant_id)
    try:
        from app.services.pipeline import wiring  # noqa: PLC0415
        # 关卡一：清洗（硬拦截）
        cleanse = wiring.build_cleanse_gate(db=db)
        creport = cleanse.run(content or "", meta)
        if not creport.passed:
            return ChainGateReport(
                verdict=VERDICT_BLOCKED,
                cleanse_passed=False,
                issues=[
                    {"code": i.code, "severity": i.severity, "message": i.message}
                    for i in creport.errors
                ],
                checker_versions=creport.checker_versions,
            )

        # 关卡二：复核（标记语义）
        review = wiring.build_review_gate()
        vreport = review.decide(content or "", meta)
        verdict = (
            VERDICT_APPROVED if vreport.route == "auto_pass" else VERDICT_NEEDS_REVIEW
        )
        return ChainGateReport(
            verdict=verdict,
            cleanse_passed=True,
            review_route=vreport.route,
            reasons=vreport.reasons,
            checker_versions=creport.checker_versions,
            score=vreport.score,
        )
    except Exception:  # noqa: BLE001 — 关卡故障不得阻断既有发布流（零回归）
        logger.exception("pipeline chain gate 异常，视为 off（不改变原流程）")
        return ChainGateReport(verdict=VERDICT_OFF)


def outreach_hold_decision(
    report: ChainGateReport,
    *,
    is_first: bool,
    review_approved: bool = False,
) -> Optional[Dict[str, Any]]:
    """首封开发信强制人审裁决（既定规则，总纲 §6.4）。

    返回 None = 放行；返回 {"error", "meta"} = 扣留（不发送）：
    - 清洗关硬拦截              → gate_blocked（永不发送，优先于已人审）；
    - review_approved=True      → 已人审，放行；
    - 首封且复核需人审（含 force_human）→ review_required（等人审）。
    非首封的 needs_review 不扣留（序列内后续邮件保持既有流转）。
    """
    if report.blocked:
        return {
            "error": "gate_blocked: 邮件链路清洗关拦截（品牌/合规风险）",
            "meta": {"gate_blocked": True, "gate": report.to_meta()},
        }
    if review_approved:
        return None
    if is_first and report.review_required:
        return {
            "error": "review_required: 首封开发信需人工审批（既定规则）",
            "meta": {"review_required": True, "gate": report.to_meta()},
        }
    return None
