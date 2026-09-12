"""UBrain AI Agent 决策追踪服务

提供决策记录、执行追踪、反馈收集与性能归因的完整闭环。
数据同时写入 PostgreSQL（业务表）与 SiteAnalyticsEvent（Analytics 回流）。
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.site_analytics import SiteAnalyticsEvent
from app.models.ubrain_decision import (
    UBrainDecisionRecord,
    UBrainExecutionRecord,
    UBrainFeedbackRecord,
)

logger = logging.getLogger(__name__)


class UBrainDecisionTracker:
    """UBrain AI Agent 决策执行追踪器"""
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        self.db = db

    # ── 核心追踪方法 ──
    def track_decision(
        self,
        decision_id: str,
        agent_tree_node_id: str,
        decision_type: str,
        input_context: dict[str, Any],
        output_action: dict[str, Any],
        confidence_score: Optional[float] = None,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> UBrainDecisionRecord:
        """记录 AI Agent 决策"""
        record = UBrainDecisionRecord(
            decision_id=decision_id,
            agent_tree_node_id=agent_tree_node_id,
            decision_type=decision_type,
            input_context=input_context,
            output_action=output_action,
            confidence_score=confidence_score,
            tenant_id=tenant_id,
            user_id=user_id,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        self._emit_analytics_event(
            event_type="ubrain_decision",
            agent_node_id=agent_tree_node_id,
            tenant_id=tenant_id,
            meta={
                "decision_id": decision_id,
                "decision_type": decision_type,
                "confidence_score": confidence_score,
            },
        )
        return record

    def track_execution(
        self,
        execution_id: str,
        decision_id: str,
        status: str,
        result: Optional[dict[str, Any]] = None,
        latency_ms: Optional[float] = None,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> UBrainExecutionRecord:
        """记录决策执行结果"""
        record = UBrainExecutionRecord(
            execution_id=execution_id,
            decision_id=decision_id,
            status=status,
            result=result,
            latency_ms=latency_ms,
            tenant_id=tenant_id,
            user_id=user_id,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        self._emit_analytics_event(
            event_type="ubrain_execution",
            agent_node_id=None,
            tenant_id=tenant_id,
            meta={
                "execution_id": execution_id,
                "decision_id": decision_id,
                "status": status,
                "latency_ms": latency_ms,
            },
        )
        return record

    def track_feedback(
        self,
        execution_id: str,
        feedback_score: Optional[float] = None,
        feedback_text: Optional[str] = None,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> UBrainFeedbackRecord:
        """记录用户反馈"""
        record = UBrainFeedbackRecord(
            execution_id=execution_id,
            feedback_score=feedback_score,
            feedback_text=feedback_text,
            tenant_id=tenant_id,
            user_id=user_id,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        self._emit_analytics_event(
            event_type="ubrain_feedback",
            agent_node_id=None,
            tenant_id=tenant_id,
            meta={
                "execution_id": execution_id,
                "feedback_score": feedback_score,
            },
        )
        return record

    # ── 查询方法 ──
    def get_decision_chain(self, decision_id: str) -> dict[str, Any]:
        """查询完整决策链（决策 → 执行 → 反馈）"""
        decision = (
            self.db.query(UBrainDecisionRecord)
            .filter(UBrainDecisionRecord.decision_id == decision_id)
            .first()
        )
        if not decision:
            return {"decision": None, "executions": [], "feedbacks": []}

        executions = (
            self.db.query(UBrainExecutionRecord)
            .filter(UBrainExecutionRecord.decision_id == decision_id)
            .order_by(UBrainExecutionRecord.created_at.asc())
            .all()
        )
        execution_ids = [e.execution_id for e in executions]
        feedbacks: list[UBrainFeedbackRecord] = []
        if execution_ids:
            feedbacks = (
                self.db.query(UBrainFeedbackRecord)
                .filter(UBrainFeedbackRecord.execution_id.in_(execution_ids))
                .order_by(UBrainFeedbackRecord.created_at.asc())
                .all()
            )

        return {
            "decision": self._serialize_decision(decision),
            "executions": [self._serialize_execution(e) for e in executions],
            "feedbacks": [self._serialize_feedback(f) for f in feedbacks],
        }

    def get_agent_performance(
        self,
        agent_tree_node_id: str,
        time_range: Optional[tuple[datetime, datetime]] = None,
    ) -> dict[str, Any]:
        """查询 Agent 性能指标"""
        query = self.db.query(UBrainDecisionRecord).filter(
            UBrainDecisionRecord.agent_tree_node_id == agent_tree_node_id
        )
        if time_range:
            start, end = time_range
            query = query.filter(
                UBrainDecisionRecord.created_at >= start,
                UBrainDecisionRecord.created_at <= end,
            )

        decisions = query.all()
        decision_ids = [d.decision_id for d in decisions]
        executions = (
            self.db.query(UBrainExecutionRecord)
            .filter(UBrainExecutionRecord.decision_id.in_(decision_ids))
            .all()
        )
        total_decisions = len(decisions)
        total_executions = len(executions)
        success_count = sum(1 for e in executions if e.status == "success")
        failed_count = sum(1 for e in executions if e.status == "failed")
        timeout_count = sum(1 for e in executions if e.status == "timeout")
        latencies = [e.latency_ms for e in executions if e.latency_ms is not None]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        feedbacks = (
            self.db.query(UBrainFeedbackRecord)
            .filter(
                UBrainFeedbackRecord.execution_id.in_(
                    [e.execution_id for e in executions]
                )
            )
            .all()
        )
        scores = [f.feedback_score for f in feedbacks if f.feedback_score is not None]
        avg_feedback = sum(scores) / len(scores) if scores else 0.0
        return {
            "agent_tree_node_id": agent_tree_node_id,
            "total_decisions": total_decisions,
            "total_executions": total_executions,
            "success_count": success_count,
            "failed_count": failed_count,
            "timeout_count": timeout_count,
            "success_rate": (
                round(success_count / total_executions * 100, 2)
                if total_executions
                else 0.0
            ),
            "avg_latency_ms": round(avg_latency, 2),
            "avg_feedback_score": round(avg_feedback, 2),
            "feedback_count": len(scores),
        }

    # ── 内部工具 ──
    def _emit_analytics_event(
        self,
        event_type: str,
        agent_node_id: Optional[str],
        tenant_id: Optional[str],
        meta: dict[str, Any],
    ) -> None:
        """将事件同步写入 SiteAnalyticsEvent（Analytics 回流）"""
        try:
            event = SiteAnalyticsEvent(
                tenant_id=tenant_id,
                agent_node_id=agent_node_id,
                session_id=f"ubrain_{event_type}",
                event_type=event_type,
                meta_json=json.dumps(meta, ensure_ascii=False, default=str),
            )
            self.db.add(event)
            self.db.commit()
        except Exception as exc:
            logger.warning("UBrain analytics event write failed: %s", exc)
            self.db.rollback()

    # ── 序列化 ──
    @staticmethod
    def _serialize_decision(record: UBrainDecisionRecord) -> dict[str, Any]:
        """_serialize_decision。

        参数说明：
        :param record: 参数 record
        :return: 返回处理结果。
        """
        return {
            "id": str(record.id),
            "decision_id": record.decision_id,
            "agent_tree_node_id": record.agent_tree_node_id,
            "decision_type": record.decision_type,
            "input_context": record.input_context,
            "output_action": record.output_action,
            "confidence_score": record.confidence_score,
            "tenant_id": record.tenant_id,
            "user_id": record.user_id,
            "created_at": (
                record.created_at.isoformat() if record.created_at else None
            ),
            "updated_at": (
                record.updated_at.isoformat() if record.updated_at else None
            ),
        }

    @staticmethod
    def _serialize_execution(record: UBrainExecutionRecord) -> dict[str, Any]:
        """_serialize_execution。

        参数说明：
        :param record: 参数 record
        :return: 返回处理结果。
        """
        return {
            "id": str(record.id),
            "execution_id": record.execution_id,
            "decision_id": record.decision_id,
            "status": record.status,
            "result": record.result,
            "latency_ms": record.latency_ms,
            "tenant_id": record.tenant_id,
            "user_id": record.user_id,
            "created_at": (
                record.created_at.isoformat() if record.created_at else None
            ),
            "updated_at": (
                record.updated_at.isoformat() if record.updated_at else None
            ),
        }

    @staticmethod
    def _serialize_feedback(record: UBrainFeedbackRecord) -> dict[str, Any]:
        """_serialize_feedback。

        参数说明：
        :param record: 参数 record
        :return: 返回处理结果。
        """
        return {
            "id": str(record.id),
            "execution_id": record.execution_id,
            "feedback_score": record.feedback_score,
            "feedback_text": record.feedback_text,
            "tenant_id": record.tenant_id,
            "user_id": record.user_id,
            "created_at": (
                record.created_at.isoformat() if record.created_at else None
            ),
            "updated_at": (
                record.updated_at.isoformat() if record.updated_at else None
            ),
        }
