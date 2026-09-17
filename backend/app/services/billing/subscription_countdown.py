# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""订阅到期倒计时 · 纯函数服务（零迁移、零外部依赖）.

数据源均为既有字段：tenants.expires_at / tenants.trial_ends_at、
licenses.expires_at（状态机 pending→activated→expired/revoked）。
付费下单复用既有 order / payment / invoice_application / license 五件套，
本模块只做三件事：剩余时间计算、阶段判定、催续触发点（供租户前台倒计时
展示与 n8n 催续工作流调用）。到期收敛由既有 TenantToggle 执行，不在本模块。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

PHASE_TRIAL = "trial"
PHASE_ACTIVE = "active"
PHASE_WARNING = "warning"
PHASE_CRITICAL = "critical"
PHASE_EXPIRED = "expired"
PHASE_OPEN_ENDED = "open_ended"

WARNING_DAYS_DEFAULT = 14
CRITICAL_DAYS_DEFAULT = 3
GRACE_DAYS_DEFAULT = 3


@dataclass(frozen=True)
class CountdownState:
    phase: str
    days_remaining: int | None
    message: str

    @property
    def dunning_trigger(self) -> bool:
        """是否应触发催续（n8n 催续工作流据此决定是否发提醒）。"""
        return self.phase in (PHASE_WARNING, PHASE_CRITICAL, PHASE_EXPIRED)


def _days_between(now: datetime, target: datetime) -> int:
    if (now.tzinfo is None) != (target.tzinfo is None):
        raise ValueError("now 与 target 必须同为 aware 或同为 naive datetime")
    return (target - now).days  # 未满 24h 记 0 天；过期首日记 -1


def compute_subscription_countdown(
    now: datetime,
    expires_at: datetime | None,
    trial_ends_at: datetime | None = None,
    warning_days: int = WARNING_DAYS_DEFAULT,
    critical_days: int = CRITICAL_DAYS_DEFAULT,
) -> CountdownState:
    """按到期时间判定订阅阶段。expires_at 为 None 视为未设置（不倒计时）。"""
    if expires_at is None:
        return CountdownState(PHASE_OPEN_ENDED, None, "未设置到期时间，不参与倒计时")
    if trial_ends_at is not None and now < trial_ends_at < expires_at:
        days = _days_between(now, trial_ends_at)
        return CountdownState(PHASE_TRIAL, days, f"试用剩余 {max(days, 0)} 天，结束后进入付费期")
    days = _days_between(now, expires_at)
    if days < 0:
        return CountdownState(PHASE_EXPIRED, days, f"已到期 {-days} 天，功能已按 TenantToggle 策略收敛")
    if days <= critical_days:
        return CountdownState(PHASE_CRITICAL, days, f"订阅即将到期（剩余 {days} 天），请立即续费")
    if days <= warning_days:
        return CountdownState(PHASE_WARNING, days, f"订阅剩余 {days} 天，建议续费")
    return CountdownState(PHASE_ACTIVE, days, f"订阅剩余 {days} 天")


def due_dunning_action(
    days_remaining: int | None,
    grace_days: int = GRACE_DAYS_DEFAULT,
) -> str | None:
    """当日应触发的催续动作（每日定时任务按精确天匹配，天然一次性不重发）。

    触发点：T-14 续费通知 / T-3 紧急提醒 / T-0 到期通知 / T-grace 宽限结束。
    """
    if days_remaining is None:
        return None
    if days_remaining == 14:
        return "renewal_notice"
    if days_remaining == 3:
        return "urgent_notice"
    if days_remaining == 0:
        return "expiry_notice"
    if days_remaining == -grace_days:
        return "grace_over_notice"
    return None
