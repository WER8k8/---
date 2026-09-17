# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""智能 Follow-up 策略引擎 — FIX-57

基于客户行为的多渠道智能跟进系统：
1. 时机优化：基于打开/点击时间的数据驱动最佳跟随时机
2. 内容自适应：根据前一次交互结果调整跟进内容
3. 多渠道协同：Email → WhatsApp → LinkedIn 逐级升级
4. 停止条件：自动识别无效线索并停止跟进
5. A/B 策略：不同跟进策略的效果对比

Follow-up 策略矩阵：
  - 无响应 → 3天后二次邮件（不同角度）
  - 已打开未回复 → 2天后跟进（聚焦价值）
  - 已点击未回复 → 1天后案例分享
  - 已回复 → 进入人工处理流程
  - 退信 → 尝试其他渠道
  - 退订 → 立即停止
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ── 枚举 ──────────────────────────────────────────────────

class FollowUpStage(str, Enum):
    """跟进阶段"""
    INITIAL = "initial"           # 首次触达
    FOLLOW_UP_1 = "follow_up_1"   # 第一次跟进
    FOLLOW_UP_2 = "follow_up_2"   # 第二次跟进
    FOLLOW_UP_3 = "follow_up_3"   # 第三次跟进
    BREAKUP = "breakup"           # 最后告别
    STOPPED = "stopped"           # 已停止


class FollowUpChannel(str, Enum):
    """跟进渠道"""
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    LINKEDIN = "linkedin"
    PHONE = "phone"


class FollowUpTrigger(str, Enum):
    """跟进触发条件"""
    NO_RESPONSE = "no_response"         # 无响应
    OPENED_NO_REPLY = "opened_no_reply" # 已打开未回复
    CLICKED_NO_REPLY = "clicked_no_reply"  # 已点击未回复
    REPLIED = "replied"                 # 已回复
    BOUNCED = "bounced"                 # 退信
    UNSUBSCRIBED = "unsubscribed"       # 退订
    SCHEDULED = "scheduled"             # 定时触发


class FollowUpOutcome(str, Enum):
    """跟进结果"""
    PENDING = "pending"
    SENT = "sent"
    OPENED = "opened"
    CLICKED = "clicked"
    REPLIED = "replied"
    BOUNCED = "bounced"
    UNSUBSCRIBED = "unsubscribed"
    CONVERTED = "converted"       # 已转化（预约会议/演示）


# ── 数据模型 ──────────────────────────────────────────────

@dataclass
class FollowUpAction:
    """跟进动作"""
    channel: FollowUpChannel
    subject: str = ""
    body_template: str = ""
    delay_days: int = 0
    delay_hours: int = 0
    priority: int = 0           # 1-5, 越高越优先
    reason: str = ""            # 为什么选择这个动作
    expected_effect: float = 0.0  # 预期效果概率
    def to_dict(self) -> dict:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "channel": self.channel.value,
            "subject": self.subject,
            "body_template": self.body_template[:200],
            "delay": f"{self.delay_days}d{self.delay_hours}h",
            "priority": self.priority,
            "reason": self.reason,
            "expected_effect": self.expected_effect,
        }


@dataclass
class FollowUpSequence:
    """跟进序列"""
    lead_id: str
    lead_email: str = ""
    lead_name: str = ""
    lead_company: str = ""
    current_stage: FollowUpStage = FollowUpStage.INITIAL
    next_action: Optional[FollowUpAction] = None
    history: list[dict] = field(default_factory=list)
    total_attempts: int = 0
    max_attempts: int = 5
    is_active: bool = True
    stop_reason: str = ""
    created_at: str = ""
    updated_at: str = ""
    def to_dict(self) -> dict:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "lead_id": self.lead_id,
            "lead_email": self.lead_email,
            "lead_name": self.lead_name,
            "lead_company": self.lead_company,
            "current_stage": self.current_stage.value,
            "next_action": self.next_action.to_dict() if self.next_action else None,
            "history": self.history[-5:],
            "total_attempts": self.total_attempts,
            "max_attempts": self.max_attempts,
            "is_active": self.is_active,
            "stop_reason": self.stop_reason,
        }


# ── 策略规则库 ────────────────────────────────────────────

# 最佳发送时间（基于行业数据）
BEST_SEND_TIMES: dict[str, list[tuple[int, int]]] = {
    "default": [(8, 0), (10, 0), (14, 0), (16, 0)],  # 默认
    "US": [(8, 0), (10, 0), (14, 0), (15, 0)],        # 美国东部时间
    "UK": [(9, 0), (11, 0), (14, 0), (15, 0)],        # 英国
    "DE": [(9, 0), (10, 0), (14, 0), (15, 0)],        # 德国
    "CN": [(9, 0), (10, 30), (14, 0), (16, 0)],       # 中国
    "JP": [(9, 0), (10, 0), (14, 0), (15, 0)],        # 日本
    "IN": [(10, 0), (11, 0), (14, 0), (16, 0)],       # 印度
    "AU": [(9, 0), (10, 0), (14, 0), (15, 0)],        # 澳大利亚
    "BR": [(9, 0), (10, 0), (14, 0), (15, 0)],        # 巴西
}


# Follow-up 策略矩阵
FOLLOW_UP_STRATEGIES: dict[str, dict[str, Any]] = {
    "no_response": {
        "label": "无响应",
        "sequence": [
            {
                "stage": FollowUpStage.FOLLOW_UP_1,
                "delay_days": 3,
                "channel": FollowUpChannel.EMAIL,
                "subject_templates": [
                    "Re: {original_subject}",
                    "Quick follow-up on my previous message",
                    "Did you get a chance to read my email?",
                ],
                "body_strategy": "different_angle",  # 换角度
                "body_hint": "从不同角度重新阐述价值主张，强调 ROI",
                "expected_effect": 0.18,
            },
            {
                "stage": FollowUpStage.FOLLOW_UP_2,
                "delay_days": 5,
                "channel": FollowUpChannel.EMAIL,
                "subject_templates": [
                    "A quick case study for {company_name}",
                    "How {similar_company} achieved {result}",
                ],
                "body_strategy": "social_proof",  # 社交证明
                "body_hint": "分享同行业案例，展示具体成果",
                "expected_effect": 0.12,
            },
            {
                "stage": FollowUpStage.FOLLOW_UP_3,
                "delay_days": 7,
                "channel": FollowUpChannel.LINKEDIN,
                "subject_templates": [],
                "body_strategy": "channel_switch",
                "body_hint": "切换到 LinkedIn 发送连接请求 + 简短消息",
                "expected_effect": 0.08,
            },
            {
                "stage": FollowUpStage.BREAKUP,
                "delay_days": 10,
                "channel": FollowUpChannel.EMAIL,
                "subject_templates": [
                    "Should I stop reaching out?",
                    "Closing the loop",
                ],
                "body_strategy": "breakup",
                "body_hint": "最后的告别邮件，给客户一个简单回复的台阶",
                "expected_effect": 0.05,
            },
        ],
    },
    "opened_no_reply": {
        "label": "已打开未回复",
        "sequence": [
            {
                "stage": FollowUpStage.FOLLOW_UP_1,
                "delay_days": 2,
                "channel": FollowUpChannel.EMAIL,
                "subject_templates": [
                    "Re: {original_subject}",
                    "Thoughts on my previous email?",
                ],
                "body_strategy": "value_focus",
                "body_hint": "聚焦核心价值主张，补充一个具体的数据点",
                "expected_effect": 0.25,
            },
            {
                "stage": FollowUpStage.FOLLOW_UP_2,
                "delay_days": 4,
                "channel": FollowUpChannel.EMAIL,
                "subject_templates": [
                    "A resource you might find useful",
                    "Thought this might help {company_name}",
                ],
                "body_strategy": "value_add",
                "body_hint": "分享有价值的内容（白皮书/案例/行业报告），不卖东西",
                "expected_effect": 0.15,
            },
            {
                "stage": FollowUpStage.FOLLOW_UP_3,
                "delay_days": 6,
                "channel": FollowUpChannel.WHATSAPP,
                "subject_templates": [],
                "body_strategy": "channel_switch",
                "body_hint": "WhatsApp 简短消息，提及之前邮件",
                "expected_effect": 0.10,
            },
        ],
    },
    "clicked_no_reply": {
        "label": "已点击未回复",
        "sequence": [
            {
                "stage": FollowUpStage.FOLLOW_UP_1,
                "delay_days": 1,
                "channel": FollowUpChannel.EMAIL,
                "subject_templates": [
                    "Re: {original_subject}",
                    "I noticed you checked out our case study",
                ],
                "body_strategy": "engagement_follow",
                "body_hint": "提及点击行为，提供更多相关内容",
                "expected_effect": 0.30,
            },
            {
                "stage": FollowUpStage.FOLLOW_UP_2,
                "delay_days": 3,
                "channel": FollowUpChannel.EMAIL,
                "subject_templates": [
                    "Quick question about your interest",
                    "Would a demo help?",
                ],
                "body_strategy": "direct_ask",
                "body_hint": "直接询问是否有兴趣安排演示",
                "expected_effect": 0.20,
            },
            {
                "stage": FollowUpStage.FOLLOW_UP_3,
                "delay_days": 5,
                "channel": FollowUpChannel.LINKEDIN,
                "subject_templates": [],
                "body_strategy": "social_touch",
                "body_hint": "LinkedIn 互动（点赞/评论）+ 私信",
                "expected_effect": 0.12,
            },
        ],
    },
    "bounced": {
        "label": "退信",
        "sequence": [
            {
                "stage": FollowUpStage.FOLLOW_UP_1,
                "delay_days": 1,
                "channel": FollowUpChannel.LINKEDIN,
                "subject_templates": [],
                "body_strategy": "channel_switch",
                "body_hint": "邮箱退信，尝试 LinkedIn 联系",
                "expected_effect": 0.15,
            },
            {
                "stage": FollowUpStage.FOLLOW_UP_2,
                "delay_days": 3,
                "channel": FollowUpChannel.WHATSAPP,
                "subject_templates": [],
                "body_strategy": "channel_switch",
                "body_hint": "尝试 WhatsApp 联系",
                "expected_effect": 0.10,
            },
        ],
    },
    "replied": {
        "label": "已回复",
        "sequence": [
            {
                "stage": FollowUpStage.FOLLOW_UP_1,
                "delay_days": 0,
                "delay_hours": 4,
                "channel": FollowUpChannel.EMAIL,
                "subject_templates": ["Re: {original_subject}"],
                "body_strategy": "human_handoff",
                "body_hint": "转人工处理，由销售代表跟进",
                "expected_effect": 0.50,
            },
        ],
    },
    "unsubscribed": {
        "label": "退订",
        "sequence": [],  # 立即停止
    },
}


# ── 智能 Follow-up 引擎 ──────────────────────────────────

class IntelligentFollowUpEngine:
    """智能 Follow-up 策略引擎。

    核心能力：
    1. 根据触发条件选择最佳跟进策略
    2. 计算最佳发送时间
    3. 多渠道协同升级
    4. 自动停止检测
    """
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._strategies = FOLLOW_UP_STRATEGIES

    def determine_next_action(
        self,
        trigger: FollowUpTrigger,
        current_stage: FollowUpStage,
        lead_context: dict[str, Any] | None = None,
        previous_interactions: list[dict] | None = None,
    ) -> Optional[FollowUpAction]:
        """根据触发条件确定下一步动作。

        Args:
            trigger: 触发条件
            current_stage: 当前阶段
            lead_context: 线索上下文（姓名、公司、行业等）
            previous_interactions: 之前的交互记录

        Returns:
            下一步跟进动作，或 None（停止跟进）
        """
        ctx = lead_context or {}
        # 退订 → 立即停止
        if trigger == FollowUpTrigger.UNSUBSCRIBED:
            return None

        # 已回复 → 转人工
        if trigger == FollowUpTrigger.REPLIED:
            return FollowUpAction(
                channel=FollowUpChannel.EMAIL,
                subject=f"Re: {ctx.get('original_subject', 'Your inquiry')}",
                body_template="human_handoff",
                delay_hours=4,
                priority=5,
                reason="客户已回复，转人工跟进",
                expected_effect=0.50,
            )

        # 获取策略
        strategy_key = trigger.value
        strategy = self._strategies.get(strategy_key, self._strategies["no_response"])
        # 根据当前阶段找到下一步
        sequence = strategy.get("sequence", [])
        next_step = None
        stage_order = [
            FollowUpStage.INITIAL,
            FollowUpStage.FOLLOW_UP_1,
            FollowUpStage.FOLLOW_UP_2,
            FollowUpStage.FOLLOW_UP_3,
            FollowUpStage.BREAKUP,
        ]
        current_idx = stage_order.index(current_stage) if current_stage in stage_order else 0
        next_idx = current_idx + 1
        if next_idx >= len(sequence) + 1:  # +1 for INITIAL
            # 已经走到最后
            if current_stage == FollowUpStage.BREAKUP:
                return None  # 彻底停止
            # 最后一次尝试 breakup
            return FollowUpAction(
                channel=FollowUpChannel.EMAIL,
                subject="Should I stop reaching out?",
                body_template="breakup",
                delay_days=10,
                priority=2,
                reason="最后一次尝试",
                expected_effect=0.05,
            )

        if next_idx - 1 < len(sequence):
            step = sequence[next_idx - 1]
            # 选择最佳主题行
            subject = ""
            if step.get("subject_templates"):
                subject = step["subject_templates"][0].format(
                    original_subject=ctx.get("original_subject", ""),
                    company_name=ctx.get("company_name", "your company"),
                    similar_company=ctx.get("similar_company", "similar companies"),
                    result=ctx.get("case_result", "3x growth"),
                )

            return FollowUpAction(
                channel=step.get("channel", FollowUpChannel.EMAIL),
                subject=subject,
                body_template=step.get("body_strategy", "default"),
                delay_days=step.get("delay_days", 3),
                delay_hours=step.get("delay_hours", 0),
                priority=4 - next_idx,
                reason=step.get("body_hint", ""),
                expected_effect=step.get("expected_effect", 0.1),
            )

        return None

    def calculate_best_send_time(
        self,
        lead_timezone: str = "default",
        previous_opens: list[dict] | None = None,
    ) -> datetime:
        """计算最佳发送时间。

        基于：
        1. 目标时区的最佳时间段
        2. 客户历史打开时间模式
        3. 避免周末和深夜

        Args:
            lead_timezone: 目标时区（如 US, UK, CN）
            previous_opens: 历史打开记录

        Returns:
            最佳发送时间（UTC）
        """
        # 获取时区最佳时段
        times = BEST_SEND_TIMES.get(lead_timezone, BEST_SEND_TIMES["default"])
        now = datetime.now(timezone.utc)
        # 如果有历史打开数据，使用客户偏好时间
        if previous_opens:
            open_hours = []
            for record in previous_opens:
                if record.get("opened_at"):
                    try:
                        opened = datetime.fromisoformat(record["opened_at"])
                        open_hours.append(opened.hour)
                    except (ValueError, TypeError):
                        pass

            if open_hours:
                # 计算最常打开的小时
                from collections import Counter
                best_hour = Counter(open_hours).most_common(1)[0][0]
                best_target = now.replace(hour=best_hour, minute=0, second=0, microsecond=0)
            else:
                best_hour, best_minute = times[0]
                best_target = now.replace(hour=best_hour, minute=best_minute, second=0, microsecond=0)
        else:
            best_hour, best_minute = times[0]
            best_target = now.replace(hour=best_hour, minute=best_minute, second=0, microsecond=0)

        # 如果最佳时间已过，移到明天
        if best_target <= now:
            best_target += timedelta(days=1)

        # 避免周末
        while best_target.weekday() >= 5:  # 5=周六, 6=周日
            best_target += timedelta(days=1)

        return best_target

    def should_stop_follow_up(
        self,
        sequence: FollowUpSequence,
        trigger: FollowUpTrigger,
    ) -> tuple[bool, str]:
        """判断是否应该停止跟进。

        Args:
            sequence: 跟进序列
            trigger: 最新触发条件

        Returns:
            (是否停止, 停止原因)
        """
        # 退订
        if trigger == FollowUpTrigger.UNSUBSCRIBED:
            return True, "客户退订"

        # 超过最大尝试次数
        if sequence.total_attempts >= sequence.max_attempts:
            return True, f"已达到最大跟进次数 ({sequence.max_attempts})"

        # 完成 breakup 阶段
        if sequence.current_stage == FollowUpStage.BREAKUP:
            return True, "已完成告别邮件"

        # 已回复 → 不停止，但转为人工
        if trigger == FollowUpTrigger.REPLIED:
            return False, ""

        # 退信且无其他渠道可用
        if trigger == FollowUpTrigger.BOUNCED:
            # 检查是否还有其他渠道尝试过
            channels_tried = {h.get("channel") for h in sequence.history}
            if FollowUpChannel.EMAIL.value in channels_tried and \
               FollowUpChannel.LINKEDIN.value in channels_tried and \
               FollowUpChannel.WHATSAPP.value in channels_tried:
                return True, "所有渠道均已尝试"

        return False, ""

    def build_sequence(
        self,
        lead_id: str,
        lead_email: str = "",
        lead_name: str = "",
        lead_company: str = "",
        lead_context: dict[str, Any] | None = None,
        max_attempts: int = 5,
    ) -> FollowUpSequence:
        """构建完整的跟进序列。

        Args:
            lead_id: 线索 ID
            lead_email: 邮箱
            lead_name: 姓名
            lead_company: 公司
            lead_context: 额外上下文
            max_attempts: 最大尝试次数
        """
        now = datetime.now(timezone.utc).isoformat()
        sequence = FollowUpSequence(
            lead_id=lead_id,
            lead_email=lead_email,
            lead_name=lead_name,
            lead_company=lead_company,
            current_stage=FollowUpStage.INITIAL,
            max_attempts=max_attempts,
            created_at=now,
            updated_at=now,
        )
        # 计算首次跟进时间
        best_time = self.calculate_best_send_time()
        sequence.next_action = FollowUpAction(
            channel=FollowUpChannel.EMAIL,
            subject="",
            body_template="initial_outreach",
            delay_days=0,
            delay_hours=max(0, int((best_time - datetime.now(timezone.utc)).total_seconds() // 3600)),
            priority=5,
            reason="首次触达",
            expected_effect=0.15,
        )
        return sequence

    def advance_sequence(
        self,
        sequence: FollowUpSequence,
        trigger: FollowUpTrigger,
        outcome: FollowUpOutcome,
        lead_context: dict[str, Any] | None = None,
    ) -> FollowUpSequence:
        """推进跟进序列。

        Args:
            sequence: 当前序列
            trigger: 触发条件
            outcome: 上次跟进结果
            lead_context: 线索上下文

        Returns:
            更新后的序列
        """
        now = datetime.now(timezone.utc).isoformat()
        # 记录本次交互
        sequence.history.append({
            "stage": sequence.current_stage.value,
            "trigger": trigger.value,
            "outcome": outcome.value,
            "channel": sequence.next_action.channel.value if sequence.next_action else "none",
            "timestamp": now,
        })
        sequence.total_attempts += 1
        sequence.updated_at = now
        # 判断是否停止
        should_stop, reason = self.should_stop_follow_up(sequence, trigger)
        if should_stop:
            sequence.is_active = False
            sequence.stop_reason = reason
            sequence.next_action = None
            return sequence

        # 推进阶段
        stage_order = [
            FollowUpStage.INITIAL,
            FollowUpStage.FOLLOW_UP_1,
            FollowUpStage.FOLLOW_UP_2,
            FollowUpStage.FOLLOW_UP_3,
            FollowUpStage.BREAKUP,
            FollowUpStage.STOPPED,
        ]
        current_idx = stage_order.index(sequence.current_stage)
        sequence.current_stage = stage_order[min(current_idx + 1, len(stage_order) - 1)]
        # 计算下一步动作
        sequence.next_action = self.determine_next_action(
            trigger=trigger,
            current_stage=sequence.current_stage,
            lead_context=lead_context,
            previous_interactions=sequence.history,
        )
        if sequence.next_action is None:
            sequence.is_active = False
            sequence.stop_reason = "策略引擎建议停止"

        return sequence

    def get_multi_channel_strategy(
        self,
        sequence: FollowUpSequence,
        available_channels: list[FollowUpChannel] | None = None,
    ) -> list[FollowUpAction]:
        """获取多渠道协同策略。

        根据当前阶段和可用渠道，生成多渠道跟进计划。

        Args:
            sequence: 跟进序列
            available_channels: 可用渠道列表

        Returns:
            多渠道跟进动作列表
        """
        if available_channels is None:
            available_channels = [
                FollowUpChannel.EMAIL,
                FollowUpChannel.LINKEDIN,
                FollowUpChannel.WHATSAPP,
            ]

        actions: list[FollowUpAction] = []
        # 主渠道：当前动作
        if sequence.next_action:
            actions.append(sequence.next_action)

        # 辅助渠道：根据阶段增加
        if sequence.current_stage in (FollowUpStage.FOLLOW_UP_2, FollowUpStage.FOLLOW_UP_3):
            # 第二阶段起，增加 LinkedIn 辅助
            if FollowUpChannel.LINKEDIN in available_channels:
                actions.append(FollowUpAction(
                    channel=FollowUpChannel.LINKEDIN,
                    subject="",
                    body_template="linkedin_connection_request",
                    delay_days=1,
                    priority=3,
                    reason="增强社交触点",
                    expected_effect=0.08,
                ))

        if sequence.current_stage == FollowUpStage.FOLLOW_UP_3:
            # 第三阶段，增加 WhatsApp
            if FollowUpChannel.WHATSAPP in available_channels:
                actions.append(FollowUpAction(
                    channel=FollowUpChannel.WHATSAPP,
                    subject="",
                    body_template="whatsapp_quick_check",
                    delay_days=2,
                    priority=2,
                    reason="多渠道触达",
                    expected_effect=0.06,
                ))

        return actions

    def analyze_sequence_performance(
        self,
        sequences: list[FollowUpSequence],
    ) -> dict[str, Any]:
        """分析跟进序列的表现。

        Args:
            sequences: 跟进序列列表

        Returns:
            表现分析数据
        """
        total = len(sequences)
        if total == 0:
            return {"total": 0}

        replied = sum(1 for s in sequences
                      if any(h.get("outcome") == FollowUpOutcome.REPLIED.value
                             for h in s.history))
        converted = sum(1 for s in sequences
                        if any(h.get("outcome") == FollowUpOutcome.CONVERTED.value
                               for h in s.history))
        stopped = sum(1 for s in sequences if not s.is_active)
        bounced = sum(1 for s in sequences
                      if any(h.get("trigger") == FollowUpTrigger.BOUNCED.value
                             for h in s.history))

        # 按阶段分析
        stage_stats = {}
        for stage in FollowUpStage:
            stage_seqs = [s for s in sequences if s.current_stage == stage]
            if stage_seqs:
                stage_stats[stage.value] = {
                    "count": len(stage_seqs),
                    "percentage": round(len(stage_seqs) / total * 100, 1),
                }

        # 按渠道分析
        channel_stats = {}
        for channel in FollowUpChannel:
            channel_actions = sum(
                1 for s in sequences
                for h in s.history
                if h.get("channel") == channel.value
            )
            if channel_actions:
                channel_stats[channel.value] = {
                    "total_actions": channel_actions,
                }

        return {
            "total": total,
            "active": total - stopped,
            "stopped": stopped,
            "replied": replied,
            "replied_rate": round(replied / total * 100, 1),
            "converted": converted,
            "conversion_rate": round(converted / total * 100, 1),
            "bounced": bounced,
            "bounce_rate": round(bounced / total * 100, 1),
            "stage_distribution": stage_stats,
            "channel_usage": channel_stats,
            "avg_attempts": round(
                sum(s.total_attempts for s in sequences) / total, 1
            ),
        }


# 单例
follow_up_engine = IntelligentFollowUpEngine()