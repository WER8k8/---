# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
import json
from datetime import datetime
from typing import Optional


class FeishuCardBuilder:

    @staticmethod
    def build_inquiry_notification(inquiry: dict) -> dict:
        """build_inquiry_notification。

        参数说明：
        :param inquiry: 参数 inquiry
        :return: 返回处理结果。
        """
        created_at = inquiry.get("created_at", "")
        if isinstance(created_at, datetime):
            created_at = created_at.strftime("%Y-%m-%d %H:%M")
        status_map = {
            "pending": "待处理",
            "contacted": "已联系",
            "closed": "已关闭",
        }
        status = status_map.get(
            inquiry.get(
                "status", "pending"), inquiry.get(
                "status", "pending"))

        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": "📩 新询盘通知"},
                "template": "red",
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**客户姓名：** {inquiry.get('name', '未知')}\n**联系电话：** {inquiry.get('phone', '无')}\n**电子邮箱：** {inquiry.get('email', '无')}\n**感兴趣产品：** {inquiry.get('product', '未指定')}\n**提交时间：** {created_at}\n**状态：** {status}",
                    },
                },
                {"tag": "hr"},
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**咨询内容：**\n{inquiry.get('message', '无')}",
                    },
                },
                {"tag": "hr"},
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "✅ 标为已联系"},
                            "type": "primary",
                            "value": {"action": "mark_contacted", "inquiry_id": str(inquiry.get("id", ""))},
                        },
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "🔗 查看详情"},
                            "type": "default",
                            "value": {"action": "view_detail", "inquiry_id": str(inquiry.get("id", ""))},
                        },
                    ],
                },
            ],
        }

    @staticmethod
    def build_product_card(product: dict) -> dict:
        """build_product_card。

        参数说明：
        :param product: 参数 product
        :return: 返回处理结果。
        """
        return {"config": {"wide_screen_mode": True},
                "header": {"title": {"tag": "plain_text",
                                     "content": f"📦 {product.get('name', '产品信息')}"},
                           "template": "blue",
                           },
                "elements": [{"tag": "div",
                              "text": {"tag": "lark_md",
                                       "content": f"**产品名称：** {product.get('name', '未知')}\n**产品编号：** {product.get('code', '无')}\n**类别：** {product.get('category', '未分类')}",
                                       },
                              },
                             {"tag": "hr"},
                             {"tag": "div",
                              "text": {"tag": "lark_md",
                                       "content": f"**产品描述：**\n{product.get('description', '暂无描述')}",
                                       },
                              },
                             {"tag": "hr"},
                             {"tag": "div",
                              "text": {"tag": "lark_md",
                                       "content": f"**规格参数：** {product.get('specifications', '无')}\n**价格：** {product.get('price', '面议')}",
                                       },
                              },
                             ],
                }

    @staticmethod
    def build_welcome_card(user_name: str = "用户") -> dict:
        """build_welcome_card。

        参数说明：
        :param user_name: 参数 user_name
        :return: 返回处理结果。
        """
        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": f"👋 欢迎使用优丁建材助手"},
                "template": "green",
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"你好，{user_name}！我是优丁建材智能助手，可以为你提供以下服务：",
                    },
                },
                {"tag": "hr"},
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "📋 **可用命令：**\n- `help` - 查看帮助信息\n- `产品查询 [关键词]` - 查询产品信息\n- `询盘列表` - 查看最新询盘\n- `绑定账号` - 绑定系统账号接收通知",
                    },
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "📋 查看产品"},
                            "type": "primary",
                            "value": {"action": "list_products"},
                        },
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "📩 最新询盘"},
                            "type": "default",
                            "value": {"action": "list_inquiries"},
                        },
                    ],
                },
            ],
        }

    @staticmethod
    def build_help_card() -> dict:
        """build_help_card。
        :return: 返回处理结果。
        """
        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": "📖 帮助中心"},
                "template": "blue",
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "**优丁建材助手 - 完整命令列表**\n\n"
                        "🔹 **基础命令**\n"
                        "- `help` - 显示帮助信息\n"
                        "- `hi` / `你好` - 获取欢迎信息\n\n"
                        "🔹 **产品相关**\n"
                        "- `产品查询 [名称]` - 搜索产品\n"
                        "- `产品列表` - 查看所有产品\n"
                        "- `产品分类` - 查看分类\n\n"
                        "🔹 **询盘相关**\n"
                        "- `询盘列表` - 查看最新询盘\n"
                        "- `询盘统计` - 查看统计数据\n\n"
                        "🔹 **账号绑定**\n"
                        "- `绑定账号` - 绑定系统账号\n"
                        "- `解绑` - 解绑账号",
                    },
                },
            ],
        }

    @staticmethod
    def build_inquiry_stats_card(stats: dict) -> dict:
        """build_inquiry_stats_card。

        参数说明：
        :param stats: 参数 stats
        :return: 返回处理结果。
        """
        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": "📊 询盘统计"},
                "template": "blue",
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**总询盘数：** {stats.get('total', 0)}\n"
                        f"**待处理：** {stats.get('pending', 0)}\n"
                        f"**已联系：** {stats.get('contacted', 0)}\n"
                        f"**已关闭：** {stats.get('closed', 0)}",
                    },
                },
            ],
        }

    @staticmethod
    def build_text_card(
            title: str,
            content: str,
            template: str = "blue") -> dict:
        """build_text_card。

        参数说明：
        :param title: 参数 title
        :param content: 参数 content
        :param template: 参数 template
        :return: 返回处理结果。
        """
        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": title},
                "template": template,
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": content},
                },
            ],
        }
