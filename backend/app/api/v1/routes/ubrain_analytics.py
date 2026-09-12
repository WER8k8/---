"""UBrain AI Agent 决策追踪与效果归因 API

与 UBrain 助手路由（ubrain.py）解耦，专门承载 AI 决策闭环追踪能力。
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.ubrain_decision import (
    UBrainDecisionRecord,
    UBrainExecutionRecord,
    UBrainFeedbackRecord,
)
from app.models.user import User
from app.services.ubrain.ubrain_decision_tracker import UBrainDecisionTracker


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/ubrain", tags=["UBrain 效果追踪"])


# ── 请求模型 ──

class TrackDecisionRequest(BaseModel):
    decision_id: str = Field(..., min_length=1, max_length=64)
    agent_tree_node_id: str = Field(..., min_length=1, max_length=64)
    decision_type: str = Field(..., min_length=1, max_length=64)
    input_context: dict[str, Any] = Field(default_factory=dict)
    output_action: dict[str, Any] = Field(default_factory=dict)
    confidence_score: Optional[float] = Field(None, ge=0, le=1)


class TrackExecutionRequest(BaseModel):
    execution_id: str = Field(..., min_length=1, max_length=64)
    decision_id: str = Field(..., min_length=1, max_length=64)
    status: str = Field(..., min_length=1, max_length=32)
    result: Optional[dict[str, Any]] = None
    latency_ms: Optional[float] = Field(None, ge=0)


class TrackFeedbackRequest(BaseModel):
    execution_id: str = Field(..., min_length=1, max_length=64)
    feedback_score: Optional[float] = Field(None, ge=0, le=5)
    feedback_text: Optional[str] = Field(None, max_length=2000)


# ── 辅助函数 ──

def _resolve_tenant_id(user: User) -> Optional[str]:
    """执行 resolve_tenant_id 相关逻辑处理。
    
    :param user: 用户对象
    :return: 返回处理结果。
    """
    return getattr(user, "tenant_id", None)


# ── 路由 ──

@router.post("/track-decision")
def track_decision(
    body: TrackDecisionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """上报 AI Agent 决策"""
    tracker = UBrainDecisionTracker(db)
    record = tracker.track_decision(
        decision_id=body.decision_id,
        agent_tree_node_id=body.agent_tree_node_id,
        decision_type=body.decision_type,
        input_context=body.input_context,
        output_action=body.output_action,
        confidence_score=body.confidence_score,
        tenant_id=_resolve_tenant_id(current_user),
        user_id=str(current_user.id),
    )
    return success_response(
        data=UBrainDecisionTracker._serialize_decision(record),
        message="决策已记录",
    )


@router.post("/track-execution")
def track_execution(
    body: TrackExecutionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """上报决策执行结果"""
    tracker = UBrainDecisionTracker(db)
    record = tracker.track_execution(
        execution_id=body.execution_id,
        decision_id=body.decision_id,
        status=body.status,
        result=body.result,
        latency_ms=body.latency_ms,
        tenant_id=_resolve_tenant_id(current_user),
        user_id=str(current_user.id),
    )
    return success_response(
        data=UBrainDecisionTracker._serialize_execution(record),
        message="执行结果已记录",
    )


@router.post("/track-feedback")
def track_feedback(
    body: TrackFeedbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """上报用户反馈"""
    tracker = UBrainDecisionTracker(db)
    record = tracker.track_feedback(
        execution_id=body.execution_id,
        feedback_score=body.feedback_score,
        feedback_text=body.feedback_text,
        tenant_id=_resolve_tenant_id(current_user),
        user_id=str(current_user.id),
    )
    return success_response(
        data=UBrainDecisionTracker._serialize_feedback(record),
        message="反馈已记录",
    )


@router.get("/decision-chain/{decision_id}")
def get_decision_chain(
    decision_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查询完整决策链（决策 → 执行 → 反馈）"""
    tracker = UBrainDecisionTracker(db)
    chain = tracker.get_decision_chain(decision_id)
    if chain["decision"] is None:
        return error_response(404, "决策不存在")
    return success_response(data=chain)


@router.get("/agent-performance/{node_id}")
def get_agent_performance(
    node_id: str,
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查询 Agent 性能指标"""
    tracker = UBrainDecisionTracker(db)
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    perf = tracker.get_agent_performance(node_id, time_range=(start, end))
    return success_response(data=perf)


@router.get("/attribution")
def get_attribution(
    decision_type: Optional[str] = Query(None, description="决策类型过滤"),
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """AI 归因报告：决策 → 业务结果的关联"""
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    query = db.query(UBrainDecisionRecord).filter(
        UBrainDecisionRecord.created_at >= start,
        UBrainDecisionRecord.created_at <= end,
    )
    if decision_type:
        query = query.filter(UBrainDecisionRecord.decision_type == decision_type)

    decisions = query.all()
    decision_ids = [d.decision_id for d in decisions]
    # 执行状态分布
    exec_stats = (
        db.query(
            UBrainExecutionRecord.status,
            func.count(UBrainExecutionRecord.id).label("count"),
        )
        .filter(UBrainExecutionRecord.decision_id.in_(decision_ids))
        .group_by(UBrainExecutionRecord.status)
        .all()
    )
    # 反馈聚合
    feedback_agg = (
        db.query(
            func.avg(UBrainFeedbackRecord.feedback_score).label("avg_score"),
            func.count(UBrainFeedbackRecord.id).label("count"),
        )
        .filter(
            UBrainFeedbackRecord.execution_id.in_(
                db.query(UBrainExecutionRecord.execution_id).filter(
                    UBrainExecutionRecord.decision_id.in_(decision_ids)
                )
            )
        )
        .first()
    )
    # 按 decision_type 分组统计
    type_stats = (
        db.query(
            UBrainDecisionRecord.decision_type,
            func.count(UBrainDecisionRecord.id).label("decision_count"),
        )
        .filter(
            UBrainDecisionRecord.created_at >= start,
            UBrainDecisionRecord.created_at <= end,
        )
        .group_by(UBrainDecisionRecord.decision_type)
        .all()
    )
    return success_response(
        data={
            "time_range": {
                "start": start.isoformat(),
                "end": end.isoformat(),
            },
            "total_decisions": len(decisions),
            "execution_breakdown": {s.status: s.count for s in exec_stats},
            "feedback_avg_score": (
                round(feedback_agg.avg_score, 2)
                if feedback_agg and feedback_agg.avg_score is not None
                else 0.0
            ),
            "feedback_count": feedback_agg.count if feedback_agg else 0,
            "decision_type_breakdown": [
                {"type": t.decision_type, "count": t.decision_count}
                for t in type_stats
            ],
        }
    )
