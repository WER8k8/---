# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""DeerFlow 结果审核器。

对执行结果进行审核，决定是否需要人工确认或打回重做。
支持基于规则的自动审核和基于质量评分的智能审核。
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.deerflow_job import DeerflowJob
from app.services.deerflow.executor import SubTaskResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 审核决策常量
# ---------------------------------------------------------------------------

class ReviewDecision:
    """审核决策常量。"""
    APPROVED = "approved"
    REJECTED = "rejected"
    WAIT_HUMAN = "wait_human"


# ---------------------------------------------------------------------------
# 审核结果
# ---------------------------------------------------------------------------

@dataclass
class ReviewResult:
    """审核结果。"""
    decision: str = ReviewDecision.APPROVED
    score: float = 0.0  # 0.0 ~ 1.0
    reasons: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    checked_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    reviewer: str = "auto"  # auto | human
    def to_dict(self) -> dict[str, Any]:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "decision": self.decision,
            "score": self.score,
            "reasons": self.reasons,
            "suggestions": self.suggestions,
            "checked_at": self.checked_at,
            "reviewer": self.reviewer,
        }

    @property
    def is_approved(self) -> bool:
        """is_approved。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return self.decision == ReviewDecision.APPROVED

    @property
    def needs_human(self) -> bool:
        """needs_human。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return self.decision == ReviewDecision.WAIT_HUMAN


# ---------------------------------------------------------------------------
# 审核规则
# ---------------------------------------------------------------------------

@dataclass
class ReviewRule:
    """审核规则。"""
    name: str
    description: str
    check_fn: callable
    is_blocking: bool = True  # 阻塞性规则：不通过则拒绝
    weight: float = 1.0


# ---------------------------------------------------------------------------
# 结果审核器
# ---------------------------------------------------------------------------

class ResultReviewer:
    """结果审核器。

    对子任务执行结果进行审核，输出审核决策。
    支持自定义审核规则和阈值配置。
    """
    # 默认质量阈值
    DEFAULT_QUALITY_THRESHOLD = 0.6
    DEFAULT_AUTO_APPROVE_THRESHOLD = 0.85
    def __init__(
        self,
        db: Session,
        job: DeerflowJob,
        *,
        quality_threshold: float = DEFAULT_QUALITY_THRESHOLD,
        auto_approve_threshold: float = DEFAULT_AUTO_APPROVE_THRESHOLD,
        custom_rules: Optional[list[ReviewRule]] = None,
    ):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :param job: 参数 job
        :param quality_threshold: 参数 quality_threshold
        :param auto_approve_threshold: 参数 auto_approve_threshold
        :param custom_rules: 参数 custom_rules
        :return: 返回处理结果。
        """
        self.db = db
        self.job = job
        self.quality_threshold = quality_threshold
        self.auto_approve_threshold = auto_approve_threshold
        self.custom_rules = custom_rules or []
        self._tracer = None

    @property
    def tracer(self):
        """延迟初始化 tracer。"""
        if self._tracer is None:
            try:
                from opentelemetry import trace
                self._tracer = trace.get_tracer("deerflow-reviewer")
            except Exception:
                logger.debug("OpenTelemetry tracer not available")
        return self._tracer

    def review(
        self,
        subtask_results: list[SubTaskResult],
    ) -> ReviewResult:
        """执行审核。

        综合所有子任务结果，应用审核规则，给出最终决策。

        Args:
            subtask_results: 所有子任务的执行结果

        Returns:
            ReviewResult 审核结果
        """
        logger.info(
            "Reviewing results: job=%s subtasks=%d",
            self.job.id, len(subtask_results),
        )
        review_result = ReviewResult()
        all_reasons: list[str] = []
        all_suggestions: list[str] = []
        total_score = 0.0
        # 1. 基础检查：所有子任务是否成功
        failed_results = [r for r in subtask_results if not r.success]
        if failed_results:
            all_reasons.append(f"{len(failed_results)} 个子任务执行失败")
        else:
            total_score += 0.4  # 基础分

        # 2. 执行质量评分
        quality_score = self._evaluate_quality(subtask_results)
        total_score += quality_score * 0.3
        if quality_score < self.quality_threshold:
            all_reasons.append(f"执行质量评分不足: {quality_score:.2f} < {self.quality_threshold}")

        # 3. 输出完整性检查
        completeness_score = self._evaluate_completeness(subtask_results)
        total_score += completeness_score * 0.3
        if completeness_score < 0.5:
            all_reasons.append(f"输出完整度不足: {completeness_score:.2f}")

        # 4. 应用自定义规则
        for rule in self.custom_rules:
            try:
                passed, reason = rule.check_fn(self.job, subtask_results)
                if not passed:
                    all_reasons.append(f"[{rule.name}] {reason}")
                    if rule.is_blocking:
                        total_score *= 0.5  # 阻塞性规则不通过，分数减半
            except Exception as exc:
                logger.warning("Review rule error: rule=%s exc=%s", rule.name, exc)

        # 5. 决策判定
        review_result.score = min(1.0, max(0.0, total_score))
        review_result.reasons = all_reasons
        review_result.suggestions = all_suggestions
        if review_result.score >= self.auto_approve_threshold and not failed_results:
            review_result.decision = ReviewDecision.APPROVED
        elif review_result.score < self.quality_threshold:
            if review_result.score < 0.3:
                review_result.decision = ReviewDecision.REJECTED
                all_suggestions.append("质量过低，建议重新执行")
            else:
                review_result.decision = ReviewDecision.WAIT_HUMAN
                all_suggestions.append("需要人工确认执行质量")
        else:
            review_result.decision = ReviewDecision.WAIT_HUMAN
            all_suggestions.append("建议人工复核后确认")

        # 保存审核结果
        self._save_review_result(review_result, subtask_results)
        logger.info(
            "Review complete: job=%s decision=%s score=%.2f",
            self.job.id, review_result.decision, review_result.score,
        )
        return review_result

    # ------------------------------------------------------------------
    # 评估函数
    # ------------------------------------------------------------------
    def _evaluate_quality(self, results: list[SubTaskResult]) -> float:
        """评估执行质量。

        基于子任务输出的丰富度、执行时长等因素综合评分。
        """
        if not results:
            return 0.0

        scores = []
        for r in results:
            score = 0.0
            # 成功执行得基础分
            if r.success:
                score += 0.5
            # 有输出内容加分
            if r.output:
                output_size = len(str(r.output))
                score += min(0.3, output_size / 10000)
            # 执行时长合理加分（30s ~ 300s 为合理区间）
            if 30 <= r.duration_ms <= 300000:
                score += 0.2
            scores.append(min(1.0, score))

        return sum(scores) / len(scores) if scores else 0.0

    def _evaluate_completeness(self, results: list[SubTaskResult]) -> float:
        """评估输出完整度。"""
        if not results:
            return 0.0

        complete_count = sum(
            1 for r in results
            if r.success and r.output and r.output.get("status") == "completed"
        )
        return complete_count / len(results)

    # ------------------------------------------------------------------
    # Checkpoint 持久化
    # ------------------------------------------------------------------
    def _save_review_result(
        self,
        review_result: ReviewResult,
        subtask_results: list[SubTaskResult],
    ) -> None:
        """保存审核结果到 checkpoint。"""
        checkpoint = self._load_checkpoint()
        checkpoint["review"] = {
            **review_result.to_dict(),
            "subtask_results_summary": [
                {
                    "subtask_id": r.subtask_id,
                    "success": r.success,
                    "intent": r.intent,
                    "duration_ms": r.duration_ms,
                }
                for r in subtask_results
            ],
        }
        self._save_checkpoint(checkpoint)

    def _load_checkpoint(self) -> dict[str, Any]:
        """加载 checkpoint 数据。"""
        if self.job.payload_json:
            try:
                data = json.loads(self.job.payload_json)
                return data.get("checkpoint", {})
            except (json.JSONDecodeError, TypeError):
                pass
        return {}

    def _save_checkpoint(self, checkpoint: dict[str, Any]) -> None:
        """保存 checkpoint 到任务 payload_json。"""
        payload: dict[str, Any] = {}
        if self.job.payload_json:
            try:
                payload = json.loads(self.job.payload_json)
            except (json.JSONDecodeError, TypeError):
                pass
        payload["checkpoint"] = checkpoint
        self.job.payload_json = json.dumps(payload, ensure_ascii=False)
        self.db.commit()
