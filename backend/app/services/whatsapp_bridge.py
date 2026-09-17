# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""WhatsApp Baileys 翻译桥接"""
import os
import httpx


class WhatsAppBridge:
    def __init__(self):
        self.base_url = os.getenv("WHATSAPP_BRIDGE_URL", "")

    async def send_message(self, phone: str, message: str, translate_to: str | None = None) -> dict:
        """发送 WhatsApp 消息，可选自动翻译"""
        if not self.base_url:
            return {"error": "WHATSAPP_BRIDGE_URL not configured", "sent": False}

        final_message = message
        if translate_to:
            final_message = await self._translate(message, translate_to)

        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self.base_url}/send", json={"phone": phone, "message": final_message})
            return {"sent": resp.status_code == 200, "phone": phone, "translated": translate_to is not None}

    async def _translate(self, text: str, target_lang: str) -> str:
        """调用 AI 引擎翻译"""
        try:
            from app.services.ai_engine import get_ai_engine
            engine = get_ai_engine()
            res = await engine.generate_text(f"Translate into {target_lang}. Only return translated text:\n\n{text}")
            return res.strip() if res else text
        except Exception:
            return text
