# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
import json
import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.feishu import FeishuBinding, FeishuMessageLog
from app.models.inquiry import Inquiry
from app.models.product import Product
from app.services.feishu.cards import FeishuCardBuilder
from app.services.feishu.client import FeishuClient

logger = logging.getLogger(__name__)


class FeishuMessageHandler:
    def __init__(self, client: FeishuClient, card_builder: FeishuCardBuilder):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param client: 参数 client
        :param card_builder: 参数 card_builder
        :return: 返回处理结果。
        """
        self.client = client
        self.card_builder = card_builder

    async def handle_event(self, event: dict) -> dict:
        """handle_event。

        参数说明：
        :param self: 参数 self
        :param event: 参数 event
        :return: 返回处理结果。
        """
        event_type = event.get("type", "")
        if event_type == "im.message.receive_v1":
            return await self._handle_message(event)
        elif event_type == "card.action.trigger":
            return await self._handle_card_action(event)
        elif event_type == "url_preview":
            return {"challenge": event.get("challenge", "")}
        elif event_type == "event_callback":
            return await self._handle_event_callback(event)
        return {}

    async def _handle_message(self, event: dict) -> dict:
        """_handle_message。

        参数说明：
        :param self: 参数 self
        :param event: 参数 event
        :return: 返回处理结果。
        """
        sender = event.get("event", {}).get("sender", {})
        sender_id = sender.get("sender_id", {}).get("open_id", "")
        message = event.get("event", {}).get("message", {})
        message_type = message.get("message_type", "")
        content_str = message.get("content", "{}")
        message_id = message.get("message_id", "")
        if not sender_id:
            return {}

        if message_type == "text":
            try:
                content = json.loads(content_str)
                text = content.get("text", "").strip()
            except (json.JSONDecodeError, KeyError):
                text = ""

            await self._log_message(sender_id, "text", text, "receive")
            await self._process_text_command(sender_id, text, message_id)
        elif message_type == "image":
            await self.client.send_text_message(
                sender_id, "已收到您的图片，但暂不支持图片识别功能。请输入文字指令，输入 help 查看可用命令。"
            )

        return {}

    async def _handle_card_action(self, event: dict) -> dict:
        """_handle_card_action。

        参数说明：
        :param self: 参数 self
        :param event: 参数 event
        :return: 返回处理结果。
        """
        action = event.get("event", {}).get("action", {})
        value = action.get("value", {})
        action_type = value.get("action", "")
        open_id = event.get(
            "event",
            {}).get(
            "operator",
            {}).get(
            "operator_id",
            {}).get(
                "open_id",
            "")
        user_name = event.get("event", {}).get("operator", {}).get("name", "")
        if action_type == "mark_contacted":
            inquiry_id = value.get("inquiry_id", "")
            await self._mark_inquiry_contacted(inquiry_id, open_id)
        elif action_type == "view_detail":
            inquiry_id = value.get("inquiry_id", "")
            await self._send_inquiry_detail(inquiry_id, open_id)
        elif action_type == "list_products":
            await self._send_product_list(open_id)
        elif action_type == "list_inquiries":
            await self._send_recent_inquiries(open_id)

        return {}

    async def _handle_event_callback(self, event: dict) -> dict:
        """_handle_event_callback。

        参数说明：
        :param self: 参数 self
        :param event: 参数 event
        :return: 返回处理结果。
        """
        event_type = event.get("event", {}).get("type", "")
        if event_type == "im.message.receive_v1":
            return await self._handle_message(event)
        return {}

    async def _process_text_command(
            self,
            open_id: str,
            text: str,
            message_id: str):
        """_process_text_command。

        参数说明：
        :param self: 参数 self
        :param open_id: 参数 open_id
        :param text: 参数 text
        :param message_id: 参数 message_id
        :return: 返回处理结果。
        """
        if not text:
            return

        command_map = {
            ("help", "帮助", "h"): self._send_help,
            ("hi", "你好", "hello", "嗨"): self._send_welcome,
        }
        for keywords, handler in command_map.items():
            if text.lower() in keywords or text in keywords:
                await handler(open_id)
                return

        if text.startswith("产品查询") or text.startswith("搜索产品"):
            keyword = text.replace("产品查询", "").replace("搜索产品", "").strip()
            await self._search_product(open_id, keyword)
            return

        if text in ("产品列表", "产品"):
            await self._send_product_list(open_id)
            return

        if text in ("询盘列表", "最新询盘", "询盘"):
            await self._send_recent_inquiries(open_id)
            return

        if text in ("询盘统计", "统计"):
            await self._send_inquiry_stats(open_id)
            return

        if text in ("绑定账号", "绑定"):
            await self._send_bind_instructions(open_id)
            return

        if text in ("解绑", "解绑账号"):
            await self._unbind_account(open_id)
            return

        await self.client.send_text_message(open_id, f"抱歉，我不理解「{text}」。输入 `help` 查看可用命令。")

    async def _send_welcome(self, open_id: str):
        """_send_welcome。

        参数说明：
        :param self: 参数 self
        :param open_id: 参数 open_id
        :return: 返回处理结果。
        """
        db = SessionLocal()
        try:
            binding = (
                db.query(FeishuBinding)
                .filter(
                    FeishuBinding.feishu_open_id == open_id,
                    FeishuBinding.is_active,
                )
                .first()
            )
            user_name = binding.feishu_user_name if binding else "用户"
            card = self.card_builder.build_welcome_card(user_name)
            await self.client.send_card_message(open_id, card)
        finally:
            db.close()

    async def _send_help(self, open_id: str):
        """_send_help。

        参数说明：
        :param self: 参数 self
        :param open_id: 参数 open_id
        :return: 返回处理结果。
        """
        card = self.card_builder.build_help_card()
        await self.client.send_card_message(open_id, card)

    async def _search_product(self, open_id: str, keyword: str):
        """_search_product。

        参数说明：
        :param self: 参数 self
        :param open_id: 参数 open_id
        :param keyword: 参数 keyword
        :return: 返回处理结果。
        """
        db = SessionLocal()
        try:
            products = (
                db.query(Product)
                .filter(
                    Product.name.ilike(f"%{keyword}%"),
                    Product.is_active,
                )
                .limit(5)
                .all()
            )
            if not products:
                await self.client.send_text_message(open_id, f"未找到与「{keyword}」相关的产品。")
                return

            for product in products:
                product_dict = {
                    "id": str(product.id),
                    "name": product.name,
                    "code": getattr(product, "code", ""),
                    "category": getattr(product, "category", ""),
                    "description": getattr(product, "description", ""),
                    "specifications": getattr(product, "specifications", ""),
                    "price": getattr(product, "price", "面议"),
                }
                card = self.card_builder.build_product_card(product_dict)
                await self.client.send_card_message(open_id, card)
        finally:
            db.close()

    async def _send_product_list(self, open_id: str):
        """_send_product_list。

        参数说明：
        :param self: 参数 self
        :param open_id: 参数 open_id
        :return: 返回处理结果。
        """
        db = SessionLocal()
        try:
            products = db.query(Product).filter(
                Product.is_active).limit(10).all()
            if not products:
                await self.client.send_text_message(open_id, "暂无产品数据。")
                return

            lines = ["📦 **产品列表**\n"]
            for i, p in enumerate(products, 1):
                lines.append(
                    f"{i}. **{p.name}** - {getattr(p, 'price', '面议')}")
            lines.append("\n发送 `产品查询 [名称]` 查看详细产品信息。")
            await self.client.send_text_message(open_id, "\n".join(lines))
        finally:
            db.close()

    async def _send_recent_inquiries(self, open_id: str):
        """_send_recent_inquiries。

        参数说明：
        :param self: 参数 self
        :param open_id: 参数 open_id
        :return: 返回处理结果。
        """
        db = SessionLocal()
        try:
            inquiries = (
                db.query(Inquiry)
                .filter(
                    Inquiry.is_active,
                )
                .order_by(Inquiry.created_at.desc())
                .limit(5)
                .all()
            )
            if not inquiries:
                await self.client.send_text_message(open_id, "暂无询盘记录。")
                return

            await self.client.send_text_message(open_id, f"📩 最近 {len(inquiries)} 条询盘：")
            for i, inquiry in enumerate(inquiries, 1):
                inquiry_dict = {
                    "id": str(inquiry.id),
                    "name": inquiry.name,
                    "phone": inquiry.phone,
                    "email": inquiry.email or "",
                    "product": inquiry.product or "",
                    "message": inquiry.message,
                    "status": inquiry.status,
                    "created_at": inquiry.created_at,
                }
                card = self.card_builder.build_inquiry_notification(
                    inquiry_dict)
                await self.client.send_card_message(open_id, card)
        finally:
            db.close()

    async def _send_inquiry_stats(self, open_id: str):
        """_send_inquiry_stats。

        参数说明：
        :param self: 参数 self
        :param open_id: 参数 open_id
        :return: 返回处理结果。
        """
        db = SessionLocal()
        try:
            total = db.query(Inquiry).filter(Inquiry.is_active).count()
            pending = db.query(Inquiry).filter(
                Inquiry.is_active, Inquiry.status == "pending").count()
            contacted = db.query(Inquiry).filter(
                Inquiry.is_active, Inquiry.status == "contacted").count()
            closed = db.query(Inquiry).filter(
                Inquiry.is_active, Inquiry.status == "closed").count()

            card = self.card_builder.build_inquiry_stats_card(
                {
                    "total": total,
                    "pending": pending,
                    "contacted": contacted,
                    "closed": closed,
                }
            )
            await self.client.send_card_message(open_id, card)
        finally:
            db.close()

    async def _mark_inquiry_contacted(self, inquiry_id: str, open_id: str):
        """_mark_inquiry_contacted。

        参数说明：
        :param self: 参数 self
        :param inquiry_id: 参数 inquiry_id
        :param open_id: 参数 open_id
        :return: 返回处理结果。
        """
        db = SessionLocal()
        try:
            inquiry = db.query(Inquiry).filter(
                Inquiry.id == inquiry_id).first()
            if inquiry:
                inquiry.status = "contacted"
                db.commit()
                await self.client.send_text_message(open_id, f'✅ 已将 {inquiry.name} 的询盘标记为"已联系"。')
            else:
                await self.client.send_text_message(open_id, "未找到该询盘记录。")
        finally:
            db.close()

    async def _send_inquiry_detail(self, inquiry_id: str, open_id: str):
        """_send_inquiry_detail。

        参数说明：
        :param self: 参数 self
        :param inquiry_id: 参数 inquiry_id
        :param open_id: 参数 open_id
        :return: 返回处理结果。
        """
        db = SessionLocal()
        try:
            inquiry = db.query(Inquiry).filter(
                Inquiry.id == inquiry_id).first()
            if inquiry:
                inquiry_dict = {
                    "id": str(inquiry.id),
                    "name": inquiry.name,
                    "phone": inquiry.phone,
                    "email": inquiry.email or "",
                    "product": inquiry.product or "",
                    "message": inquiry.message,
                    "status": inquiry.status,
                    "created_at": inquiry.created_at,
                }
                card = self.card_builder.build_inquiry_notification(
                    inquiry_dict)
                await self.client.send_card_message(open_id, card)
            else:
                await self.client.send_text_message(open_id, "未找到该询盘记录。")
        finally:
            db.close()

    async def _send_bind_instructions(self, open_id: str):
        """_send_bind_instructions。

        参数说明：
        :param self: 参数 self
        :param open_id: 参数 open_id
        :return: 返回处理结果。
        """
        text = (
            "🔗 **账号绑定说明**\n\n"
            "将飞书账号与系统账号绑定后，您可以：\n"
            "✅ 实时接收新询盘通知\n"
            "✅ 通过飞书处理询盘\n"
            "✅ 查询产品信息和统计数据\n\n"
            "请提供您的系统用户名或邮箱进行绑定，格式：\n"
            "`绑定 [用户名/邮箱]`"
        )
        await self.client.send_text_message(open_id, text)

    async def bind_account(
            self,
            open_id: str,
            open_name: str,
            identifier: str) -> bool:
        """bind_account。

        参数说明：
        :param self: 参数 self
        :param open_id: 参数 open_id
        :param open_name: 参数 open_name
        :param identifier: 参数 identifier
        :return: 返回处理结果。
        """
        db = SessionLocal()
        try:
            existing = (
                db.query(FeishuBinding)
                .filter(
                    FeishuBinding.feishu_open_id == open_id,
                    FeishuBinding.is_active,
                )
                .first()
            )
            if existing:
                await self.client.send_text_message(open_id, f"您已绑定账号：{existing.bound_username}")
                return False

            from app.models.user import User
            from app.core.field_crypto import encrypt_field
            user = (
                db.query(User)
                .filter(
                    (User.username == identifier) | (User.email == encrypt_field(identifier)),
                    User.is_active,
                )
                .first()
            )
            if not user:
                await self.client.send_text_message(
                    open_id, f"未找到系统用户「{identifier}」，请检查用户名或邮箱是否正确。"
                )
                return False

            binding = FeishuBinding(
                feishu_open_id=open_id,
                feishu_user_name=open_name or identifier,
                bound_user_id=str(user.id),
                bound_username=user.username,
            )
            db.add(binding)
            db.commit()
            await self.client.send_text_message(open_id, f"✅ 绑定成功！您已绑定系统账号：{user.username}")
            return True
        finally:
            db.close()

    async def _unbind_account(self, open_id: str):
        """_unbind_account。

        参数说明：
        :param self: 参数 self
        :param open_id: 参数 open_id
        :return: 返回处理结果。
        """
        db = SessionLocal()
        try:
            binding = (
                db.query(FeishuBinding)
                .filter(
                    FeishuBinding.feishu_open_id == open_id,
                    FeishuBinding.is_active,
                )
                .first()
            )
            if not binding:
                await self.client.send_text_message(open_id, "您尚未绑定任何账号。")
                return
            binding.is_active = False
            db.commit()
            await self.client.send_text_message(open_id, "✅ 已成功解绑账号。")
        finally:
            db.close()

    async def _log_message(
            self,
            open_id: str,
            msg_type: str,
            content: str,
            direction: str):
        """_log_message。

        参数说明：
        :param self: 参数 self
        :param open_id: 参数 open_id
        :param msg_type: 参数 msg_type
        :param content: 参数 content
        :param direction: 参数 direction
        :return: 返回处理结果。
        """
        db = SessionLocal()
        try:
            log = FeishuMessageLog(
                feishu_open_id=open_id,
                message_type=msg_type,
                content=content[:500],
                direction=direction,
            )
            db.add(log)
            db.commit()
        except Exception as e:
            logger.error(f"记录飞书消息日志失败: {e}")
        finally:
            db.close()
