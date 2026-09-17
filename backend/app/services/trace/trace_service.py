# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""统一 Trace 服务 — 链式追踪的写入/读取与记分卡聚合（总纲 §4.6-7 / §8 085_traces）。

- start/complete/fail：任务执行生命周期落 Trace（prompt 正文只存引用）。
- get_chain：按 parent_trace_id 回溯整条执行链。
- aggregate_*：从终态 Trace 聚合 Skill/Agent 记分卡（供 §4.6 路由与 §040 业务指标）。
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.trace import AgentScorecard, SkillPerformance, TaskTrace

logger = logging.getLogger("uj-admin.trace")

TRACE_RUNNING = "running"
TRACE_SUCCESS = "success"
TRACE_FAILED = "failed"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TaskTraceService:
    """统一 Trace 服务。"""
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        self.db = db

    # ──────────────────────────────────────────────
    # 生命周期
    # ──────────────────────────────────────────────
    def start_trace(
        self,
        *,
        tenant_id: Optional[str] = None,
        parent_trace_id: Optional[str] = None,
        trace_type: str,
        source_id: Optional[str] = None,
        task_id: Optional[str] = None,
        run_id: Optional[str] = None,
        skill_id: Optional[str] = None,
        skill_version: Optional[str] = None,
        model_name: Optional[str] = None,
        prompt_ref: Optional[str] = None,
        input_summary: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> TaskTrace:
        """开启一条 Trace（status=running）。prompt 正文只传对象存储引用，正文不入库。"""
        trace = TaskTrace(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            parent_trace_id=parent_trace_id,
            trace_type=trace_type,
            source_id=source_id,
            task_id=task_id,
            run_id=run_id,
            skill_id=skill_id,
            skill_version=skill_version,
            model_name=model_name,
            prompt_ref=prompt_ref,
            input_summary=input_summary,
            status=TRACE_RUNNING,
            metadata_json=_merge_metadata(None, metadata),
        )
        self.db.add(trace)
        self.db.commit()
        self.db.refresh(trace)
        logger.info(
            "Trace started: id=%s type=%s source=%s skill=%s/%s",
            trace.id, trace_type, source_id, skill_id, skill_version,
        )
        return trace

    def complete_trace(
        self,
        trace_id: str,
        *,
        output_summary: Optional[str] = None,
        artifacts: Optional[list[dict[str, Any]]] = None,
        validation_results: Optional[list[dict[str, Any]]] = None,
        duration_ms: int = 0,
        cost: float = 0.0,
        tokens_used: int = 0,
        feedback: Optional[dict[str, Any]] = None,
    ) -> Optional[TaskTrace]:
        """标记 Trace 成功完成。"""
        trace = self._get(trace_id)
        if not trace:
            return None
        now = _utcnow()
        trace.status = TRACE_SUCCESS
        trace.success = True
        trace.output_summary = output_summary
        trace.artifacts = list(artifacts or [])
        trace.validation_results = list(validation_results or [])
        trace.duration_ms = duration_ms
        trace.cost = cost
        trace.tokens_used = tokens_used
        trace.feedback = feedback
        trace.finished_at = now
        trace.updated_at = now
        self.db.commit()
        self.db.refresh(trace)
        return trace

    def fail_trace(
        self,
        trace_id: str,
        *,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        duration_ms: int = 0,
        cost: float = 0.0,
    ) -> Optional[TaskTrace]:
        """标记 Trace 失败。"""
        trace = self._get(trace_id)
        if not trace:
            return None
        now = _utcnow()
        trace.status = TRACE_FAILED
        trace.success = False
        trace.error_code = error_code
        trace.error_message = error_message
        trace.duration_ms = duration_ms
        trace.cost = cost
        trace.finished_at = now
        trace.updated_at = now
        self.db.commit()
        self.db.refresh(trace)
        return trace

    def record_feedback(
        self,
        trace_id: str,
        feedback: dict[str, Any],
    ) -> Optional[TaskTrace]:
        """人工反馈留证（§3.4：每次 AI 回复留证，含人工反馈）。"""
        trace = self._get(trace_id)
        if not trace:
            return None
        trace.feedback = feedback
        trace.updated_at = _utcnow()
        self.db.commit()
        self.db.refresh(trace)
        return trace

    # ──────────────────────────────────────────────
    # 链式读取
    # ──────────────────────────────────────────────
    def get_chain(self, trace_id: str) -> list[TaskTrace]:
        """按 parent_trace_id 从叶子回溯到根，返回整条执行链（根在前）。"""
        chain: list[TaskTrace] = []
        seen: set[str] = set()
        cur_id: Optional[str] = trace_id
        while cur_id and cur_id not in seen:
            seen.add(cur_id)
            node = self._get(cur_id)
            if not node:
                break
            chain.append(node)
            cur_id = node.parent_trace_id
        chain.reverse()
        return chain

    def get_trace(self, trace_id: str) -> Optional[TaskTrace]:
        """获取单条 Trace。"""
        return self._get(trace_id)

    # ──────────────────────────────────────────────
    # 记分卡聚合（终态 Trace → 记分卡）
    # ──────────────────────────────────────────────
    def aggregate_skill_performance(
        self,
        skill_id: str,
        *,
        skill_version: str = "",
        window_start: Optional[datetime] = None,
        window_end: Optional[datetime] = None,
        tenant_id: Optional[str] = None,
    ) -> Optional[SkillPerformance]:
        """从终态 Trace 聚合 Skill 版本记分卡（幂等 upsert 到窗口行）。"""
        end = window_end or _utcnow()
        start = window_start or (end - timedelta(hours=24))
        rows = (
            self.db.query(TaskTrace)
            .filter(
                TaskTrace.skill_id == skill_id,
                TaskTrace.skill_version == skill_version,
                TaskTrace.status.in_((TRACE_SUCCESS, TRACE_FAILED)),
                TaskTrace.finished_at >= start,
                TaskTrace.finished_at <= end,
            )
            .all()
        )
        if not rows:
            return None

        total = len(rows)
        successes = sum(1 for r in rows if r.success)
        perf = (
            self.db.query(SkillPerformance)
            .filter(
                SkillPerformance.tenant_id == tenant_id,
                SkillPerformance.skill_id == skill_id,
                SkillPerformance.skill_version == skill_version,
                SkillPerformance.window_start == start,
            )
            .first()
        )
        if not perf:
            perf = SkillPerformance(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                skill_id=skill_id,
                skill_version=skill_version,
                window_start=start,
                window_end=end,
            )
            self.db.add(perf)
        perf.total_invocations = total
        perf.success_count = successes
        perf.failure_count = total - successes
        perf.success_rate = round(successes / total, 4)
        perf.avg_duration_ms = int(sum(r.duration_ms for r in rows) / total)
        perf.avg_cost = round(sum(r.cost for r in rows) / total, 6)
        perf.total_tokens = sum(r.tokens_used for r in rows)
        perf.updated_at = _utcnow()
        self.db.commit()
        self.db.refresh(perf)
        return perf

    def aggregate_agent_scorecard(
        self,
        agent_id: str,
        task_type: str,
        *,
        window_days: int = 7,
        tenant_id: Optional[str] = None,
        business_metrics: Optional[dict[str, Any]] = None,
    ) -> Optional[AgentScorecard]:
        """从终态 Trace 聚合 Agent 记分卡（含 §040 业务指标）。"""
        end = _utcnow()
        start = end - timedelta(days=window_days)
        rows = (
            self.db.query(TaskTrace)
            .filter(
                TaskTrace.source_id == agent_id,
                TaskTrace.trace_type == task_type,
                TaskTrace.status.in_((TRACE_SUCCESS, TRACE_FAILED)),
                TaskTrace.finished_at >= start,
            )
            .all()
        )
        if not rows:
            return None

        total = len(rows)
        successes = sum(1 for r in rows if r.success)
        card = (
            self.db.query(AgentScorecard)
            .filter(
                AgentScorecard.tenant_id == tenant_id,
                AgentScorecard.agent_id == agent_id,
                AgentScorecard.task_type == task_type,
            )
            .first()
        )
        if not card:
            card = AgentScorecard(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                agent_id=agent_id,
                task_type=task_type,
            )
            self.db.add(card)
        card.agent_name = card.agent_name or agent_id
        card.total_invocations = total
        card.success_count = successes
        card.success_rate = round(successes / total, 4)
        card.avg_duration_ms = int(sum(r.duration_ms for r in rows) / total)
        card.avg_cost = round(sum(r.cost for r in rows) / total, 6)
        card.evaluation_window_days = window_days
        if business_metrics:
            card.revenue_impact = float(business_metrics.get("revenue_impact", card.revenue_impact or 0))
            card.conversion_rate = float(business_metrics.get("conversion_rate", card.conversion_rate or 0))
            card.efficiency = float(business_metrics.get("efficiency", card.efficiency or 0))
            card.roi = float(business_metrics.get("roi", card.roi or 0))
        card.updated_at = _utcnow()
        self.db.commit()
        self.db.refresh(card)
        return card

    def _get(self, trace_id: str) -> Optional[TaskTrace]:
        return (
            self.db.query(TaskTrace)
            .filter(TaskTrace.id == trace_id)
            .first()
        )


def _merge_metadata(existing: Any, incoming: Optional[dict[str, Any]]) -> dict[str, Any]:
    """合并扩展元数据到 Trace.metadata_json（避免 None 覆盖）。"""
    base = dict(existing or {})
    if incoming:
        base.update(incoming)
    return base
