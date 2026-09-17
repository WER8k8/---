# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.models.content import GeneratedContent, InclusionStatus, PublishTask
from app.models.region import GeneratedKeyword
from app.services.feishu.client import FeishuClient


class FeishuReportService:
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        self.db = db
        self.feishu_client = FeishuClient()

    def _generate_report_card(self, data: Dict[str, Any]) -> dict:
        """生成飞书消息卡片。"""
        return {"config": {"wide_screen_mode": True,
                           "enable_forward": True},
                "header": {"title": {"content": "🏗️ SEO矩阵系统每日报告",
                                     "tag": "plain_text"},
                           "template": "blue"},
                "elements": [{"tag": "div",
                              "text": {"content": f"📅 报告时间：{data['report_date']}",
                                       "tag": "plain_text"}},
                             {"tag": "div",
                              "text": {"content": "\n📊 【关键词统计】",
                                       "tag": "plain_text"}},
                             {"tag": "div",
                              "fields": [{"is_short": True,
                                          "text": {"content": f"• 总关键词数\n**{data['keyword_stats']['total']}**",
                                                   "tag": "lark_md",
                                                   },
                                          },
                                         {"is_short": True,
                                          "text": {"content": f"• 已使用\n**{data['keyword_stats']['used']}**",
                                                   "tag": "lark_md"},
                                          },
                                         {"is_short": True,
                                          "text": {"content": f"• 有效关键词\n**{data['keyword_stats']['valid']}**",
                                                   "tag": "lark_md",
                                                   },
                                          },
                                         {"is_short": True,
                                          "text": {"content": f"• 使用率\n**{data['keyword_stats']['usage_rate']}%**",
                                                   "tag": "lark_md",
                                                   },
                                          },
                                         ],
                              },
                             {"tag": "div",
                              "text": {"content": "\n📝 【文案统计】",
                                       "tag": "plain_text"}},
                             {"tag": "div",
                              "fields": [{"is_short": True,
                                          "text": {"content": f"• 已生成\n**{data['content_stats']['total']}**",
                                                   "tag": "lark_md"},
                                          },
                                         {"is_short": True,
                                          "text": {"content": f"• 已发布\n**{data['content_stats']['published']}**",
                                                   "tag": "lark_md",
                                                   },
                                          },
                                         {"is_short": True,
                                          "text": {"content": f"• 待发布\n**{data['content_stats']['pending']}**",
                                                   "tag": "lark_md"},
                                          },
                                         {"is_short": True,
                                          "text": {"content": f"• 发布率\n**{data['content_stats']['publish_rate']}%**",
                                                   "tag": "lark_md",
                                                   },
                                          },
                                         ],
                              },
                             {"tag": "div",
                              "text": {"content": "\n🚀 【发布任务】",
                                       "tag": "plain_text"}},
                             {"tag": "div",
                              "fields": [{"is_short": True,
                                          "text": {"content": f"• 总任务\n**{data['publish_stats']['total']}**",
                                                   "tag": "lark_md"},
                                          },
                                         {"is_short": True,
                                          "text": {"content": f"• 成功\n**{data['publish_stats']['success']}**",
                                                   "tag": "lark_md"},
                                          },
                                         {"is_short": True,
                                          "text": {"content": f"• 失败\n**{data['publish_stats']['failed']}**",
                                                   "tag": "lark_md"},
                                          },
                                         {"is_short": True,
                                          "text": {"content": f"• 成功率\n**{data['publish_stats']['success_rate']}%**",
                                                   "tag": "lark_md",
                                                   },
                                          },
                                         ],
                              },
                             {"tag": "div",
                              "text": {"content": "\n🔍 【收录监控】",
                                       "tag": "plain_text"}},
                             {"tag": "div",
                              "fields": [{"is_short": True,
                                          "text": {"content": f"• 监控总数\n**{data['inclusion_stats']['total']}**",
                                                   "tag": "lark_md",
                                                   },
                                          },
                                         {"is_short": True,
                                          "text": {"content": f"• 已收录\n**{data['inclusion_stats']['included']}**",
                                                   "tag": "lark_md",
                                                   },
                                          },
                                         {"is_short": True,
                                          "text": {"content": f"• 未收录\n**{data['inclusion_stats']['not_included']}**",
                                                   "tag": "lark_md",
                                                   },
                                          },
                                         {"is_short": True,
                                          "text": {"content": f"• 收录率\n**{data['inclusion_stats']['inclusion_rate']}%**",
                                                   "tag": "lark_md",
                                                   },
                                          },
                                         ],
                              },
                             {"tag": "div",
                              "text": {"content": "\n✨ 【今日亮点】",
                                       "tag": "plain_text"}},
                             {"tag": "div",
                              "text": {"content": data["highlights"],
                                       "tag": "plain_text"}},
                             ],
                }

    def _get_today_data(self) -> Dict[str, Any]:
        """获取今日数据统计"""
        today_start = datetime.now(
            timezone.utc).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0)
        today_end = today_start + timedelta(days=1)
        # 关键词统计
        total_keywords = self.db.query(
            GeneratedKeyword).filter_by(is_valid=True).count()
        used_keywords = self.db.query(
            GeneratedKeyword).filter_by(is_used=True).count()
        valid_keywords = self.db.query(
            GeneratedKeyword).filter_by(is_valid=True).count()
        usage_rate = round(
            (used_keywords / total_keywords) * 100,
            1) if total_keywords > 0 else 0

        # 文案统计
        total_contents = self.db.query(GeneratedContent).count()
        published_contents = self.db.query(
            GeneratedContent).filter_by(status="published").count()
        pending_contents = self.db.query(
            GeneratedContent).filter_by(status="pending").count()
        publish_rate = round(
            (published_contents / total_contents) * 100,
            1) if total_contents > 0 else 0

        # 发布任务统计
        total_tasks = self.db.query(PublishTask).count()
        success_tasks = self.db.query(
            PublishTask).filter_by(status="success").count()
        failed_tasks = self.db.query(
            PublishTask).filter_by(status="failed").count()
        success_rate = round(
            (success_tasks / total_tasks) * 100,
            1) if total_tasks > 0 else 0

        # 收录统计
        total_inclusion = self.db.query(InclusionStatus).count()
        included_count = self.db.query(
            InclusionStatus).filter_by(is_included=True).count()
        not_included_count = total_inclusion - included_count
        inclusion_rate = round(
            (included_count / total_inclusion) * 100,
            1) if total_inclusion > 0 else 0

        # 今日新增
        today_keywords = self.db.query(GeneratedKeyword).filter(
            GeneratedKeyword.created_at >= today_start).count()
        today_contents = self.db.query(GeneratedContent).filter(
            GeneratedContent.created_at >= today_start).count()
        today_tasks = self.db.query(PublishTask).filter(
            PublishTask.created_at >= today_start).count()

        # 生成亮点
        highlights = [
            f"• 今日新增关键词 {today_keywords} 个",
            f"• 今日生成文案 {today_contents} 篇",
            f"• 今日发布任务 {today_tasks} 个",
        ]
        if success_rate >= 90:
            highlights.append("• ✅ 发布成功率优秀！")
        if inclusion_rate >= 70:
            highlights.append("• 🎉 收录率持续提升！")
        if pending_contents > 0:
            highlights.append(f"• ⚠️ 还有 {pending_contents} 篇文案待发布")

        return {
            "report_date": datetime.now(timezone.utc).strftime("%Y年%m月%d日"),
            "keyword_stats": {
                "total": total_keywords,
                "used": used_keywords,
                "valid": valid_keywords,
                "usage_rate": usage_rate,
            },
            "content_stats": {
                "total": total_contents,
                "published": published_contents,
                "pending": pending_contents,
                "publish_rate": publish_rate,
            },
            "publish_stats": {
                "total": total_tasks,
                "success": success_tasks,
                "failed": failed_tasks,
                "success_rate": success_rate,
            },
            "inclusion_stats": {
                "total": total_inclusion,
                "included": included_count,
                "not_included": not_included_count,
                "inclusion_rate": inclusion_rate,
            },
            "highlights": "\n".join(highlights),
        }

    async def send_daily_report(self, open_id: str) -> dict:
        """发送每日报告"""
        data = self._get_today_data()
        card = self._generate_report_card(data)
        return await self.feishu_client.send_card_message(open_id, card)

    async def send_daily_report_by_email(self, email: str) -> dict:
        """通过邮箱发送每日报告"""
        data = self._get_today_data()
        card = self._generate_report_card(data)
        # 先获取用户open_id，然后发送卡片消息
        await self.feishu_client._ensure_token()
        return await self.feishu_client.send_text_to_user_by_email(
            email,
            f"📊 SEO矩阵系统每日报告\n\n关键词: {data['keyword_stats']['total']}个\n文案: {data['content_stats']['total']}篇\n发布任务: {data['publish_stats']['total']}个\n收录率: {data['inclusion_stats']['inclusion_rate']}%",
        )

    def get_report_data(self) -> Dict[str, Any]:
        """获取报告数据（用于API返回）"""
        return self._get_today_data()
