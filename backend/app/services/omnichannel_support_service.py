"""海外多渠道智能客服 Agent (WhatsApp / LiveChat Widget)。"""

from __future__ import annotations

import logging
from typing import Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class OmnichannelSupportService:
    def handle_visitor_inquiry(
        self,
        tenant_id: str,
        channel: str,
        sender_id: str,
        message: str,
    ) -> dict[str, Any]:
        msg_lower = message.lower()
        if "price" in msg_lower or "quote" in msg_lower or "cost" in msg_lower:
            reply = "Hello! Thank you for your interest. Our standard pricing starts from wholesale FOB rates. Could you please share your required quantity and target port so we can send an exact quote?"
            lead_captured = True
        elif "shipping" in msg_lower or "delivery" in msg_lower:
            reply = "We offer express air freight (5-7 days) and sea shipping (20-30 days) worldwide with full DDP door-to-door support."
            lead_captured = False
        else:
            reply = "Thank you for reaching out to us! An export specialist has been assigned to assist your inquiry."
            lead_captured = False

        return {
            "channel": channel,
            "sender_id": sender_id,
            "reply": reply,
            "lead_captured": lead_captured,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
