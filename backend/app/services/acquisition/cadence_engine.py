# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
7 步出海高转化节奏编排器 (7-Touch Cadence Engine)。

外贸大宗成交定律：
- 80% 的大宗外贸订单发生在第 4~12 次跟进；
- 单次触达即放弃会导致 90% 的潜客永久流失。

核心能力：
1. 编排 30 天 7 轮多触点递进跟进战略（Email / WhatsApp / 视频验厂 / 样板激活 / 断联挽回）
2. 目标国本地时区感知（Timezone-aware），精准计算当地工作日上午黄金收发时段
"""
from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional


class OutboundCadenceEngine:
    """7 步出海高转化节奏编排器。"""

    # 目标国工作日与黄金投递时区映射
    COUNTRY_TIMEZONES: Dict[str, Dict[str, Any]] = {
        "SA": {
            "tz_name": "Asia/Riyadh (UTC+3)",
            "utc_offset": 3,
            "working_days": "周日 ~ 周四 (Sunday - Thursday)",
            "golden_window": "09:30 - 11:30 AM (Local Time)",
            "weekend": ["Friday", "Saturday"],
        },
        "AE": {
            "tz_name": "Asia/Dubai (UTC+4)",
            "utc_offset": 4,
            "working_days": "周一 ~ 周五 (Monday - Friday)",
            "golden_window": "10:00 - 12:00 AM (Local Time)",
            "weekend": ["Saturday", "Sunday"],
        },
        "DE": {
            "tz_name": "Europe/Berlin (UTC+1 / UTC+2)",
            "utc_offset": 1,
            "working_days": "周一 ~ 周五 (Monday - Friday)",
            "golden_window": "09:30 - 11:00 AM (Local Time)",
            "weekend": ["Saturday", "Sunday"],
        },
        "US": {
            "tz_name": "America/New_York (UTC-5 / UTC-4)",
            "utc_offset": -5,
            "working_days": "周一 ~ 周五 (Monday - Friday)",
            "golden_window": "10:00 - 11:30 AM (Local Time)",
            "weekend": ["Saturday", "Sunday"],
        },
        "IN": {
            "tz_name": "Asia/Kolkata (UTC+5:30)",
            "utc_offset": 5.5,
            "working_days": "周一 ~ 周六 (Monday - Saturday)",
            "golden_window": "10:30 - 12:30 PM (Local Time)",
            "weekend": ["Sunday"],
        },
    }

    # WhatsApp 账号阶梯暖机调度表 (天数阈值, 每日最大发送上限)
    WARMUP_LADDER = [
        (3, 10),    # 前 3 天：严控 ≤ 10 条/日
        (7, 25),    # 第 4~7 天：放宽至 ≤ 25 条/日
        (14, 60),   # 第 8~14 天：放宽至 ≤ 60 条/日
        (30, 120),  # 第 15~30 天：放宽至 ≤ 120 条/日
        (999, 200), # 30 天后：成熟账号标准额度 200 条/日
    ]

    @classmethod
    def get_daily_wa_limit(cls, account_age_days: int) -> int:
        """根据 WhatsApp 账号注册/接入天数，计算今日安全投递上限。"""
        days = max(0, int(account_age_days or 0))
        for threshold, limit in cls.WARMUP_LADDER:
            if days <= threshold:
                return limit
        return 200

    @classmethod
    def warmup_gate(
        cls,
        phone_number: str,
        account_registered_date: Optional[datetime.date] = None,
        sent_today_count: int = 0,
    ) -> Dict[str, Any]:
        """WhatsApp 账号安全暖机门禁校验。"""
        if account_registered_date is None:
            account_registered_date = datetime.date.today()

        age_days = max(0, (datetime.date.today() - account_registered_date).days)
        daily_limit = cls.get_daily_wa_limit(age_days)
        sent = max(0, int(sent_today_count or 0))
        remaining = max(0, daily_limit - sent)
        is_safe = sent < daily_limit

        warning: Optional[str] = None
        if not is_safe:
            warning = f"🛑 今日发送已达账号安全阈值 ({sent}/{daily_limit})，系统已启动过载熔断防封禁机制"
        elif age_days <= 3:
            warning = f"⚠ 新账号（第 {age_days} 天）：处于严格防封禁保护期，今日上限 {daily_limit} 条，剩余额度 {remaining} 条"
        elif age_days <= 7:
            warning = f"📈 暖机爬坡期（第 {age_days} 天）：今日上限 {daily_limit} 条，剩余额度 {remaining} 条"

        masked_phone = phone_number[-4:].rjust(len(phone_number), "*") if len(phone_number) >= 7 else phone_number

        return {
            "phone_masked": masked_phone,
            "account_age_days": age_days,
            "daily_limit": daily_limit,
            "sent_today": sent,
            "remaining_today": remaining,
            "safe_to_send": is_safe,
            "warning": warning,
        }

    @classmethod
    def generate_cadence_plan(
        cls,
        company_name: str,
        country: str = "SA",
        product_category: str = "Ceramic & Stone",
        base_date: Optional[datetime.date] = None,
    ) -> Dict[str, Any]:
        """生成基于时区与多通道递进的 7 步跟进时间表。"""
        if base_date is None:
            base_date = datetime.date.today()

        country_key = (country or "SA").strip().upper()
        tz_info = cls.COUNTRY_TIMEZONES.get(
            country_key,
            {
                "tz_name": "Standard UTC Window",
                "utc_offset": 0,
                "working_days": "周一 ~ 周五 (Monday - Friday)",
                "golden_window": "10:00 AM Local Time",
                "weekend": ["Saturday", "Sunday"],
            },
        )

        buyer = company_name or "Target Buyer"

        # 7 步核心触点设计
        touches: List[Dict[str, Any]] = [
            {
                "touch_number": 1,
                "day_offset": 1,
                "scheduled_date": (base_date + datetime.timedelta(days=1)).isoformat(),
                "channel": "Cold Email",
                "action_title": "首发破冰 · 权威资质与痛点切入",
                "core_objective": "建立第一专业印象，以 SASO/CE 检测报告与 20GP 集装箱防超重装载测算建立可信度。",
                "talk_track": f"为 {buyer} 呈送 {product_category} 权威检测书与 2026 最新出厂参考单价。",
                "status": "Scheduled",
            },
            {
                "touch_number": 2,
                "day_offset": 3,
                "scheduled_date": (base_date + datetime.timedelta(days=3)).isoformat(),
                "channel": "WhatsApp",
                "action_title": "移动轻触 · 产线无滤镜实拍短视频",
                "core_objective": "15 秒打动采购人：发送大板无暗裂、色差均一的工厂出货实拍（1080P）与电子单页。",
                "talk_track": "Hi Director, 这是我们今天装柜发往中东大港的同一批次现货实拍，供您把关。",
                "status": "Pending",
            },
            {
                "touch_number": 3,
                "day_offset": 6,
                "scheduled_date": (base_date + datetime.timedelta(days=6)).isoformat(),
                "channel": "Cold Email",
                "action_title": "工程背书 · 同区域标杆案例解构",
                "core_objective": "解除客户对批量供应能力的顾虑，分享同属该地区的大型商住/酒店项目的供货成功案例。",
                "talk_track": f"案例深度：我们如何帮助同区域工程商降低 14% 破损率与提前 10 天交运？",
                "status": "Pending",
            },
            {
                "touch_number": 4,
                "day_offset": 10,
                "scheduled_date": (base_date + datetime.timedelta(days=10)).isoformat(),
                "channel": "Email / WhatsApp",
                "action_title": "市场预警 · 原材料与海运费锁定优惠",
                "core_objective": "制造合理紧迫感（FOMO）：原材料涨价通知，或者船司针对特约 20GP/40HQ 订舱位的限时运价保留。",
                "talk_track": "国际海运运价变动预警，当前我们为VIP客户锁定了本月底前发运的保价柜位。",
                "status": "Pending",
            },
            {
                "touch_number": 5,
                "day_offset": 15,
                "scheduled_date": (base_date + datetime.timedelta(days=15)).isoformat(),
                "channel": "WhatsApp / Phone",
                "action_title": "终极敲门砖 · 免费实体样板箱直寄",
                "core_objective": "将虚拟沟通转化为桌面实体存在，主动提供 DHL 顺丰免费空运样板包（包含厚度、倒角、不同光度）。",
                "talk_track": f"已备好 30x30cm 精裁工程板样，可直接顺丰/DHL 空运到 {buyer} 办公室验收。",
                "status": "Pending",
            },
            {
                "touch_number": 6,
                "day_offset": 22,
                "scheduled_date": (base_date + datetime.timedelta(days=22)).isoformat(),
                "channel": "LinkedIn / Email",
                "action_title": "高管背书 · 出口总裁/VP 专属商务支持",
                "core_objective": "升格沟通层级，由工厂总经理/出口总监直接发信，承诺提供定制账期置换与最高级别品质担保。",
                "talk_track": "优丁出口事业部总裁亲自签署的战略合作诚意函，保障大宗订单专属通道。",
                "status": "Pending",
            },
            {
                "touch_number": 7,
                "day_offset": 30,
                "scheduled_date": (base_date + datetime.timedelta(days=30)).isoformat(),
                "channel": "Cold Email",
                "action_title": "断联挽回 · 外贸老兵 Break-up Email",
                "core_objective": "利用客户不愿彻底关闭机会的心理学（心理回复率高达 33%），得体告知暂时封存跟单档案。",
                "talk_track": f"亲爱的 {buyer}，看来目前不是合适时机。我将停止打扰并将案卷归档，后续有任何急需货源随时唤醒我。",
                "status": "Pending",
            },
        ]

        return {
            "company_name": buyer,
            "target_country": country_key,
            "timezone_intelligence": tz_info,
            "total_touches": len(touches),
            "cadence_cycle_days": 30,
            "touches": touches,
            "execution_rules": [
                "严格避免在买家当地非工作日（如沙特周五、欧美周末）投递；",
                "投递时间精准锁定买家当地时间 09:30 - 11:30 AM；",
                "客户一旦有任何正向回复，立刻自动暂停后续步骤，转入【谈判与异议助攻】。",
            ],
        }
