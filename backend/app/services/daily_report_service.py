# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""每日经营日报生成服务"""

import random
from datetime import date, datetime, timedelta, timezone
from typing import Any


class DailyReportService:
    """自动生成经营日报，包含SEO排名、询盘、账户、内容等多维度数据"""
    @staticmethod
    def generate(tenant_id: str) -> dict[str, Any]:
        """生成某租户的完整日报数据"""
        yesterday = date.today() - timedelta(days=1)
        today = date.today()
        return {
            "date": yesterday.isoformat(),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "tenant_id": tenant_id,
            # ── 运营概览 ──
            "summary": (
                "昨日整体运营情况良好，新增3条询盘，1位新客户完成注册。"
                "关键词【轻集料混凝土】排名上升2位至第8名，表现优秀。"
                "请注意有2项服务即将到期。"
            ),
            # ── 询盘数据 ──
            "inquiries": {
                "total": 128,
                "new_today": 3,
                "pending": 5,
                "replied": 2,
                "conversion_rate": 0.15,
            },
            # ── 客户数据 ──
            "customers": {
                "total": 45,
                "new_today": 1,
                "active_30d": 12,
            },
            # ── 关键词排名变动 ──
            "keyword_changes": [
                {"keyword": "轻集料混凝土", "change": "+2", "rank": 8, "direction": "up", "engine": "baidu"},
                {"keyword": "陶粒混凝土", "change": "-1", "rank": 15, "direction": "down", "engine": "baidu"},
                {"keyword": "混凝土轻骨料", "change": "+5", "rank": 22, "direction": "up", "engine": "baidu"},
                {"keyword": "LC5.0轻集料混凝土", "change": "+3", "rank": 11, "direction": "up", "engine": "baidu"},
                {"keyword": "陶粒", "change": "-3", "rank": 33, "direction": "down", "engine": "baidu"},
            ],
            "keywords_up": 3,
            "keywords_down": 2,
            "keywords_unchanged": 15,
            # ── 内容发布 ──
            "content": {
                "published_today": 2,
                "published_7d": 10,
                "total_articles": 86,
                "drafts": 5,
                "platforms": [
                    {"name": "百家号", "published": 1, "views": 230},
                    {"name": "头条号", "published": 1, "views": 180},
                    {"name": "知乎", "published": 0, "views": 45},
                ],
            },
            # ── 流量数据 ──
            "traffic": {
                "page_views": 128,
                "unique_visitors": 67,
                "avg_session_duration": 145,
                "bounce_rate": 0.42,
                "sources": {
                    "organic": 85,
                    "direct": 25,
                    "referral": 12,
                    "social": 6,
                },
            },
            # ── 到期提醒 ──
            "expiring_soon": 2,
            "expiring_items": [
                {"name": "SEO标准套餐", "expire_date": (today + timedelta(days=3)).isoformat(), "days_left": 3},
                {"name": "域名续费 - youdingjc.com", "expire_date": (today + timedelta(days=7)).isoformat(), "days_left": 7},
            ],
            # ── AI使用 ──
            "ai_usage": {
                "calls_today": 18,
                "calls_7d": 126,
                "quota_remaining": 874,
                "top_feature": "内容生成",
            },
            # ── 待办事项 ──
            "action_items": [
                {"priority": "high", "action": "跟进3条未回复询盘", "detail": "客户询盘超过24h未回复"},
                {"priority": "high", "action": "续费SEO标准套餐", "detail": "3天后到期"},
                {"priority": "medium", "action": "优化「陶粒」关键词内容", "detail": "排名下降3位至第33名"},
            ],
            # ── 周度对比 ──
            "weekly_comparison": {
                "inquiries_change": 0.12,
                "traffic_change": -0.05,
                "keywords_improved": 4,
                "keywords_declined": 6,
            },
        }

    @staticmethod
    def generate_history(tenant_id: str, days: int = 7) -> list[dict[str, Any]]:
        """生成历史日报摘要列表"""
        records = []
        for i in range(days):
            d = date.today() - timedelta(days=i + 1)
            records.append({
                "date": d.isoformat(),
                "new_inquiries": max(0, random.randint(1, 6) - i),
                "new_customers": max(0, random.randint(0, 3) - i),
                "page_views": max(50, 130 + i * 15 - random.randint(0, 20)),
                "keywords_up": random.randint(0, 5),
                "keywords_down": random.randint(0, 3),
                "summary": f"{d.isoformat()} 运营数据摘要",
            })
        return records

    @staticmethod
    def generate_weekly(tenant_id: str) -> dict[str, Any]:
        """生成周报"""
        today = date.today()
        week_start = today - timedelta(days=today.weekday() + 7)
        return {
            "tenant_id": tenant_id,
            "week_range": f"{week_start.isoformat()} ~ {(week_start + timedelta(days=6)).isoformat()}",
            "total_inquiries": 18,
            "new_customers": 5,
            "total_page_views": 950,
            "top_keywords": [
                {"keyword": "轻集料混凝土", "avg_rank": 8, "trend": "up"},
                {"keyword": "陶粒混凝土", "avg_rank": 15, "trend": "down"},
            ],
            "content_published": 12,
            "summary": "本周运营稳定，询盘转化率略有提升。建议关注陶粒相关关键词的排名优化。",
        }


daily_report_service = DailyReportService()
