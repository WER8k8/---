# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""邮件序列 Drip Campaign — FIX-44

自动跟进邮件序列管理：
- 预置序列模板（3封/5封/7封）
- 自定义序列
- 触发条件（打开/点击/未回复/时间）
- 序列状态追踪
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional
import uuid


class SequenceTrigger(str, Enum):
    """序列触发条件。"""
    IMMEDIATELY = "immediately"         # 立即发送
    AFTER_SEND = "after_send"           # 上封发送后
    AFTER_OPEN = "after_open"           # 上封打开后
    AFTER_CLICK = "after_click"         # 上封点击后
    NO_REPLY = "no_reply"               # 未回复时
    NO_OPEN = "no_open"                 # 未打开时
    MANUAL = "manual"                   # 手动触发


@dataclass
class SequenceStep:
    """序列中的单步邮件。"""
    step: int
    subject: str
    body_template: str
    trigger: SequenceTrigger = SequenceTrigger.AFTER_SEND
    delay_days: int = 2          # 上一步后延迟天数
    delay_hours: int = 0
    variables: list[str] = field(default_factory=list)  # 模板变量


@dataclass
class DripSequence:
    """邮件序列定义。"""
    id: str
    name: str
    name_cn: str
    description: str
    steps: list[SequenceStep]
    total_days: int = 0
    category: str = "general"


# ============================================================
# 预置序列模板
# ============================================================

# 3封序列 — 快速跟进
SEQUENCE_3_STEP = DripSequence(
    id="seq-3-step",
    name="3-Step Quick Follow-up",
    name_cn="3封快速跟进",
    description="3封邮件，7天内完成首轮跟进",
    total_days=7,
    category="quick",
    steps=[
        SequenceStep(
            step=1,
            subject="Quick question about {company_name}",
            body_template="""Hi {first_name},

I came across {company_name} and was impressed by your work in {industry}.

I'm reaching out because we help companies like yours {value_proposition}.

Would you be open to a quick chat this week?

Best,
{sender_name}""",
            trigger=SequenceTrigger.IMMEDIATELY,
            delay_days=0,
            variables=["company_name", "industry", "value_proposition", "first_name", "sender_name"],
        ),
        SequenceStep(
            step=2,
            subject="Following up: {company_name}",
            body_template="""Hi {first_name},

Just following up on my previous email. I know you're busy, so I'll keep this brief.

We've helped {similar_companies} achieve {results}. I'd love to explore if we can do the same for {company_name}.

Any interest in a 15-minute call?

Best,
{sender_name}""",
            trigger=SequenceTrigger.NO_REPLY,
            delay_days=3,
            variables=["first_name", "company_name", "similar_companies", "results", "sender_name"],
        ),
        SequenceStep(
            step=3,
            subject="Last try: {pain_point} solution for {company_name}",
            body_template="""Hi {first_name},

This will be my last email — I don't want to clutter your inbox.

If {pain_point} is something you're thinking about, here's a quick case study: {case_study_link}

If not, no worries at all. Wishing you and {company_name} all the best!

Best,
{sender_name}""",
            trigger=SequenceTrigger.NO_REPLY,
            delay_days=4,
            variables=["first_name", "company_name", "pain_point", "case_study_link", "sender_name"],
        ),
    ],
)


# 5封序列 — 标准跟进
SEQUENCE_5_STEP = DripSequence(
    id="seq-5-step",
    name="5-Step Standard Follow-up",
    name_cn="5封标准跟进",
    description="5封邮件，14天内建立关系并转化",
    total_days=14,
    category="standard",
    steps=[
        SequenceStep(
            step=1,
            subject="Introduction: helping {industry} companies grow",
            body_template="""Hi {first_name},

I've been following {company_name} and noticed you're doing great work in {industry}.

I specialize in helping {industry} companies {value_proposition}. Would you be interested in learning how we could support {company_name}?

Best,
{sender_name}""",
            trigger=SequenceTrigger.IMMEDIATELY,
            delay_days=0,
            variables=["first_name", "company_name", "industry", "value_proposition", "sender_name"],
        ),
        SequenceStep(
            step=2,
            subject="Re: {industry} growth strategy",
            body_template="""Hi {first_name},

Following up — I put together a quick analysis of how {company_name} could {benefit}. 

Would you be open to a 10-minute call to discuss?

{sender_name}""",
            trigger=SequenceTrigger.NO_REPLY,
            delay_days=3,
            variables=["first_name", "company_name", "industry", "benefit", "sender_name"],
        ),
        SequenceStep(
            step=3,
            subject="Case study: how we helped {similar_company}",
            body_template="""Hi {first_name},

I thought you might find this relevant — we recently helped {similar_company} achieve {specific_result}.

Here's a quick overview: {case_study_summary}

Could we schedule a call to discuss how this applies to {company_name}?

{sender_name}""",
            trigger=SequenceTrigger.NO_REPLY,
            delay_days=3,
            variables=["first_name", "company_name", "similar_company", "specific_result", "case_study_summary", "sender_name"],
        ),
        SequenceStep(
            step=4,
            subject="Question about {company_name}'s {pain_point}",
            body_template="""Hi {first_name},

How is {company_name} currently handling {pain_point}?

We've found that most {industry} companies struggle with this, and we've developed a solution that typically {outcome}.

Worth a quick chat?

{sender_name}""",
            trigger=SequenceTrigger.NO_OPEN,
            delay_days=4,
            variables=["first_name", "company_name", "industry", "pain_point", "outcome", "sender_name"],
        ),
        SequenceStep(
            step=5,
            subject="Final follow-up: {company_name}",
            body_template="""Hi {first_name},

I've tried reaching out a few times and haven't heard back — totally understand, you're busy.

If {pain_point} ever becomes a priority, here's a helpful resource I put together: {resource_link}

No need to reply. Wishing {company_name} continued success!

{sender_name}""",
            trigger=SequenceTrigger.NO_REPLY,
            delay_days=4,
            variables=["first_name", "company_name", "pain_point", "resource_link", "sender_name"],
        ),
    ],
)


# 7封序列 — 深度培育
SEQUENCE_7_STEP = DripSequence(
    id="seq-7-step",
    name="7-Step Deep Nurture",
    name_cn="7封深度培育",
    description="7封邮件，30天内深度培育高价值线索",
    total_days=30,
    category="deep",
    steps=[
        SequenceStep(
            step=1,
            subject="Quick intro: {industry} growth",
            body_template="""Hi {first_name},

I came across {company_name} and wanted to introduce myself. I work with {industry} companies to help them {value_proposition}.

Would love to learn more about what you're working on.

{sender_name}""",
            trigger=SequenceTrigger.IMMEDIATELY,
            delay_days=0,
            variables=["first_name", "company_name", "industry", "value_proposition", "sender_name"],
        ),
        SequenceStep(
            step=2,
            subject="Industry insight: {industry_trend}",
            body_template="""Hi {first_name},

I recently published an analysis on {industry_trend} that I think {company_name} would find valuable.

Here's the key takeaway: {key_insight}

Would love to hear your thoughts on this.

{sender_name}""",
            trigger=SequenceTrigger.NO_REPLY,
            delay_days=4,
            variables=["first_name", "company_name", "industry_trend", "key_insight", "sender_name"],
        ),
        SequenceStep(
            step=3,
            subject="Re: {industry_trend}",
            body_template="""Hi {first_name},

Just following up on the {industry_trend} insight I shared. 

I also put together a quick benchmark for {company_name} against competitors: {benchmark_link}

{sender_name}""",
            trigger=SequenceTrigger.NO_REPLY,
            delay_days=4,
            variables=["first_name", "company_name", "industry_trend", "benchmark_link", "sender_name"],
        ),
        SequenceStep(
            step=4,
            subject="Customer story: {customer_name}",
            body_template="""Hi {first_name},

I thought you'd be interested in how {customer_name} used our platform to {customer_result}.

Full case study: {case_study_link}

{sender_name}""",
            trigger=SequenceTrigger.NO_REPLY,
            delay_days=5,
            variables=["first_name", "customer_name", "customer_result", "case_study_link", "sender_name"],
        ),
        SequenceStep(
            step=5,
            subject="Free resource: {resource_name}",
            body_template="""Hi {first_name},

I put together a free {resource_type} specifically for {industry} companies: {resource_name}

It covers {resource_topics}. No strings attached — just thought it might be helpful.

Download here: {resource_link}

{sender_name}""",
            trigger=SequenceTrigger.NO_REPLY,
            delay_days=5,
            variables=["first_name", "industry", "resource_name", "resource_type", "resource_topics", "resource_link", "sender_name"],
        ),
        SequenceStep(
            step=6,
            subject="Invitation: {event_name}",
            body_template="""Hi {first_name},

We're hosting a {event_type} on {event_topic} next {event_date}. I'd love to invite you as our guest.

Spots are limited, so let me know if you're interested!

{sender_name}""",
            trigger=SequenceTrigger.NO_REPLY,
            delay_days=7,
            variables=["first_name", "event_name", "event_type", "event_topic", "event_date", "sender_name"],
        ),
        SequenceStep(
            step=7,
            subject="Final note: {company_name}",
            body_template="""Hi {first_name},

I've shared several resources over the past few weeks. If any of them were helpful, I'd love to know.

And if {pain_point} ever becomes a priority, I'm here to help. No pressure.

Wishing you and {company_name} all the best!

{sender_name}""",
            trigger=SequenceTrigger.NO_REPLY,
            delay_days=5,
            variables=["first_name", "company_name", "pain_point", "sender_name"],
        ),
    ],
)


# 所有预置序列
PRESET_SEQUENCES: dict[str, DripSequence] = {
    "seq-3-step": SEQUENCE_3_STEP,
    "seq-5-step": SEQUENCE_5_STEP,
    "seq-7-step": SEQUENCE_7_STEP,
}


# ============================================================
# 序列服务
# ============================================================

class DripSequenceService:
    """邮件序列服务。"""
    @staticmethod
    def get_sequence(sequence_id: str) -> Optional[DripSequence]:
        """获取序列定义。"""
        return PRESET_SEQUENCES.get(sequence_id)

    @staticmethod
    def get_all_sequences() -> list[dict]:
        """获取所有序列。"""
        return [
            {
                "id": seq.id,
                "name": seq.name,
                "name_cn": seq.name_cn,
                "description": seq.description,
                "steps": len(seq.steps),
                "total_days": seq.total_days,
                "category": seq.category,
            }
            for seq in PRESET_SEQUENCES.values()
        ]

    @staticmethod
    def get_next_step(
        sequence_id: str,
        current_step: int,
        trigger_event: Optional[str] = None,
    ) -> Optional[SequenceStep]:
        """获取序列下一步。"""
        seq = PRESET_SEQUENCES.get(sequence_id)
        if not seq:
            return None

        next_step_num = current_step + 1
        for step in seq.steps:
            if step.step == next_step_num:
                # 检查触发条件
                if trigger_event and step.trigger != SequenceTrigger.MANUAL:
                    if step.trigger == SequenceTrigger.NO_REPLY and trigger_event != "no_reply":
                        continue
                    if step.trigger == SequenceTrigger.NO_OPEN and trigger_event != "no_open":
                        continue
                    if step.trigger == SequenceTrigger.AFTER_OPEN and trigger_event != "opened":
                        continue
                    if step.trigger == SequenceTrigger.AFTER_CLICK and trigger_event != "clicked":
                        continue
                return step

        return None  # 序列结束

    @staticmethod
    def render_template(
        template: str,
        variables: dict[str, str],
    ) -> str:
        """渲染邮件模板。"""
        result = template
        for key, value in variables.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result

    @staticmethod
    def get_next_send_time(
        step: SequenceStep,
        from_time: Optional[datetime] = None,
    ) -> datetime:
        """计算下一步发送时间。"""
        base = from_time or datetime.utcnow()
        delay = timedelta(days=step.delay_days, hours=step.delay_hours)
        return base + delay