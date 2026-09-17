# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""智能 Follow-up API 路由 — FIX-57"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.security import get_current_user
from app.services.ubrain.follow_up_engine import (
    FollowUpChannel,
    FollowUpOutcome,
    FollowUpTrigger,
    FollowUpStage,
    FollowUpSequence,
    follow_up_engine,
)

ROUTE_PREFIX = ""
router = APIRouter(prefix="/follow-up", tags=["获客·智能跟进"])


@router.post("/sequence/build")
async def build_sequence(
    lead_id: str,
    lead_email: str = "",
    lead_name: str = "",
    lead_company: str = "",
    max_attempts: int = 5,
    user=Depends(get_current_user),
):
    """构建跟进序列"""
    sequence = follow_up_engine.build_sequence(
        lead_id=lead_id,
        lead_email=lead_email,
        lead_name=lead_name,
        lead_company=lead_company,
        max_attempts=max_attempts,
    )
    return {"code": 0, "data": sequence.to_dict()}


@router.post("/sequence/advance")
async def advance_sequence(
    lead_id: str,
    current_stage: str,
    trigger: str,
    outcome: str,
    lead_email: str = "",
    lead_name: str = "",
    lead_company: str = "",
    total_attempts: int = 0,
    max_attempts: int = 5,
    user=Depends(get_current_user),
):
    """推进跟进序列"""
    try:
        stage = FollowUpStage(current_stage)
        trg = FollowUpTrigger(trigger)
        out = FollowUpOutcome(outcome)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"参数错误: {e}")

    sequence = FollowUpSequence(
        lead_id=lead_id,
        lead_email=lead_email,
        lead_name=lead_name,
        lead_company=lead_company,
        current_stage=stage,
        total_attempts=total_attempts,
        max_attempts=max_attempts,
    )
    updated = follow_up_engine.advance_sequence(
        sequence=sequence,
        trigger=trg,
        outcome=out,
        lead_context={"company_name": lead_company},
    )
    return {"code": 0, "data": updated.to_dict()}


@router.post("/next-action")
async def determine_next_action(
    trigger: str,
    current_stage: str,
    company_name: str = "",
    original_subject: str = "",
    user=Depends(get_current_user),
):
    """确定下一步跟进动作"""
    try:
        trg = FollowUpTrigger(trigger)
        stage = FollowUpStage(current_stage)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"参数错误: {e}")

    action = follow_up_engine.determine_next_action(
        trigger=trg,
        current_stage=stage,
        lead_context={
            "company_name": company_name,
            "original_subject": original_subject,
        },
    )
    if action is None:
        return {"code": 0, "data": {"action": None, "message": "建议停止跟进"}}

    return {"code": 0, "data": action.to_dict()}


@router.get("/best-send-time")
async def calculate_best_time(
    lead_timezone: str = "default",
    user=Depends(get_current_user),
):
    """计算最佳发送时间"""
    best_time = follow_up_engine.calculate_best_send_time(lead_timezone=lead_timezone)
    return {
        "code": 0,
        "data": {
            "best_time_utc": best_time.isoformat(),
            "timezone": lead_timezone,
        },
    }


@router.post("/should-stop")
async def check_should_stop(
    current_stage: str,
    trigger: str,
    total_attempts: int = 0,
    max_attempts: int = 5,
    user=Depends(get_current_user),
):
    """判断是否应该停止跟进"""
    try:
        stage = FollowUpStage(current_stage)
        trg = FollowUpTrigger(trigger)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"参数错误: {e}")

    sequence = FollowUpSequence(
        lead_id="check",
        current_stage=stage,
        total_attempts=total_attempts,
        max_attempts=max_attempts,
    )
    should_stop, reason = follow_up_engine.should_stop_follow_up(sequence, trg)
    return {"code": 0, "data": {"should_stop": should_stop, "reason": reason}}


@router.post("/multi-channel-strategy")
async def get_multi_channel_strategy(
    current_stage: str,
    available_channels: Optional[list[str]] = None,
    user=Depends(get_current_user),
):
    """获取多渠道协同策略"""
    try:
        stage = FollowUpStage(current_stage)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"参数错误: {e}")

    channels = None
    if available_channels:
        channels = [FollowUpChannel(c) for c in available_channels if c in [e.value for e in FollowUpChannel]]

    sequence = FollowUpSequence(
        lead_id="multi",
        current_stage=stage,
    )
    actions = follow_up_engine.get_multi_channel_strategy(sequence, channels)
    return {"code": 0, "data": [a.to_dict() for a in actions]}


@router.post("/analyze")
async def analyze_performance(
    user=Depends(get_current_user),
):
    """分析跟进序列表现（需要传入序列数据）"""
    # 返回策略矩阵供前端参考
    from app.services.ubrain.follow_up_engine import FOLLOW_UP_STRATEGIES
    return {
        "code": 0,
        "data": {
            "strategies": {
                key: {
                    "label": val["label"],
                    "steps": len(val["sequence"]),
                    "total_effect": round(sum(s["expected_effect"] for s in val["sequence"]), 2),
                }
                for key, val in FOLLOW_UP_STRATEGIES.items()
            },
            "best_send_times": {
                tz: [f"{h:02d}:{m:02d}" for h, m in times]
                for tz, times in {
                    "US": [(8, 0), (10, 0), (14, 0), (15, 0)],
                    "UK": [(9, 0), (11, 0), (14, 0), (15, 0)],
                    "CN": [(9, 0), (10, 30), (14, 0), (16, 0)],
                }.items()
            },
        },
    }
