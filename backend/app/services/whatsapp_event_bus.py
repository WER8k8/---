# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""WhatsApp 入站事件总线 — Plugin → 核心后端实时同步。

补齐原架构缺口「WhatsApp Plugin → 核心后端缺少事件总线」：

- Plugin（Baileys @3100）POST 入站消息到本服务
- 归一化后发布到进程内 `event_bus`（CRM/线索/编排可订阅）
- 可选落库 `whatsapp_messages(direction=inbound)`
- 支持可选共享密钥 `WHATSAPP_INBOUND_TOKEN`（Header: X-WhatsApp-Token）

设计约束（与原生直驱模型一致）：
- 本模块是 **系统内通道总线**，不是外挂业务桥
- 持久化失败只记日志 + 如实返回 `persisted:false`，不阻断事件发布
- 无 DB 时仍发布事件，保证订阅方可实时感知
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional

from app.core.event_bus import Event, EventPriority, EventTypes, event_bus

logger = logging.getLogger("uj-admin.whatsapp_event_bus")

SOURCE_PLUGIN = "whatsapp_plugin"
SOURCE_API = "whatsapp_api"
SOURCE_BRIDGE = "whatsapp_bridge"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm_phone(raw: Any) -> str:
    s = str(raw or "").strip()
    if not s:
        return ""
    keep = "".join(ch for ch in s if ch.isdigit() or ch == "+")
    return keep or s


def normalize_inbound_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """归一化 Plugin / Cloud API / 内部桥 三种入站形态。

    支持字段（任选）：
    - 通用: phone/from/from_phone, body/text/text_body/message, msg_id/message_id
    - Baileys 风格: {key:{remoteJid,id}, message:{conversation|extendedTextMessage.text}}
    - Cloud API 风格: {entry:[{changes:[{value:{messages:[...]}}]}]}
    """
    if not isinstance(payload, dict):
        return {
            "phone": "",
            "body": "",
            "msg_id": "",
            "from_name": "",
            "message_type": "text",
            "raw_type": "invalid",
        }

    phone = _norm_phone(
        payload.get("phone")
        or payload.get("from")
        or payload.get("from_phone")
        or payload.get("sender")
    )
    raw_body = (
        payload.get("body")
        if payload.get("body") is not None and not isinstance(payload.get("body"), (dict, list))
        else None
    )
    if raw_body is None:
        raw_body = (
            payload.get("text")
            if payload.get("text") is not None and not isinstance(payload.get("text"), (dict, list))
            else None
        )
    if raw_body is None:
        raw_body = (
            payload.get("text_body")
            if payload.get("text_body") is not None and not isinstance(payload.get("text_body"), (dict, list))
            else None
        )
    body = str(raw_body or "")
    msg_id = str(payload.get("msg_id") or payload.get("message_id") or payload.get("id") or "")
    from_name = str(payload.get("from_name") or payload.get("pushName") or payload.get("name") or "")
    message_type = str(payload.get("message_type") or payload.get("type") or "text")

    # Baileys 形态
    key = payload.get("key")
    msg = payload.get("message")
    if isinstance(key, dict):
        jid = str(key.get("remoteJid") or key.get("jid") or "")
        if jid and not phone:
            phone = _norm_phone(jid.split("@")[0])
        if not msg_id:
            msg_id = str(key.get("id") or "")
    if isinstance(msg, dict) and not body:
        body = str(
            msg.get("conversation")
            or (msg.get("extendedTextMessage") or {}).get("text")
            or (msg.get("imageMessage") or {}).get("caption")
            or ""
        )
        if message_type in {"", "text"}:
            if msg.get("imageMessage"):
                message_type = "image"
            elif msg.get("documentMessage"):
                message_type = "document"
            elif msg.get("audioMessage"):
                message_type = "audio"
            elif msg.get("videoMessage"):
                message_type = "video"
    elif isinstance(payload.get("message"), str) and not body:
        body = str(payload.get("message") or "")

    # Cloud API 形态（whatsapp_business_service 风格）
    if not phone or not body:
        try:
            entries = payload.get("entry") or []
            if isinstance(entries, list):
                for ent in entries:
                    for ch in (ent or {}).get("changes") or []:
                        value = (ch or {}).get("value") or {}
                        for m in value.get("messages") or []:
                            phone = phone or _norm_phone(
                                m.get("from") or (value.get("contacts") or [{}])[0].get("wa_id")
                            )
                            msg_id = msg_id or str(m.get("id") or "")
                            message_type = message_type if message_type != "text" else str(m.get("type") or "text")
                            if not body:
                                body = str(
                                    (m.get("text") or {}).get("body")
                                    or m.get("body")
                                    or ""
                                )
        except Exception:  # noqa: BLE001
            pass

    return {
        "phone": phone,
        "body": body,
        "msg_id": msg_id,
        "from_name": from_name,
        "message_type": message_type or "text",
        "raw_type": "dict",
        "tenant_id": str(payload.get("tenant_id") or ""),
        "account_id": str(payload.get("account_id") or payload.get("accountId") or ""),
        "lead_id": str(payload.get("lead_id") or ""),
        "inquiry_id": str(payload.get("inquiry_id") or ""),
        "timestamp": str(payload.get("timestamp") or payload.get("ts") or _now_iso()),
        "source": str(payload.get("source") or SOURCE_PLUGIN),
    }


class WhatsAppInboundEventBus:
    """WhatsApp 入站事件总线（系统内通道，非外挂业务桥）。"""

    def __init__(self) -> None:
        self._received = 0
        self._emitted = 0
        self._persisted = 0
        self._failed_emit = 0
        self._recent: list[dict[str, Any]] = []

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "received": self._received,
            "emitted": self._emitted,
            "persisted": self._persisted,
            "failed_emit": self._failed_emit,
            "recent_count": len(self._recent),
        }

    def recent(self, limit: int = 20) -> list[dict[str, Any]]:
        return list(self._recent[-int(limit or 20) :])

    def _remember(self, item: dict[str, Any]) -> None:
        self._recent.append(item)
        if len(self._recent) > 200:
            self._recent = self._recent[-200:]

    def publish_inbound(
        self,
        payload: dict[str, Any],
        *,
        db: Any = None,
        persist: bool = True,
        priority: EventPriority = EventPriority.HIGH,
    ) -> dict[str, Any]:
        """接收入站消息：归一化 → 落库（可选）→ 发布 event_bus。

        Returns:
            {
              "accepted": bool,
              "event_id": str,
              "event_type": str,
              "normalized": {...},
              "persisted": {...}|None,
              "emitted": bool,
              "error": str|None,
            }
        """
        self._received += 1
        norm = normalize_inbound_payload(payload)
        phone = norm.get("phone") or ""
        body = (norm.get("body") or "").strip()

        result: dict[str, Any] = {
            "accepted": False,
            "event_id": "",
            "event_type": EventTypes.WHATSAPP_MESSAGE_RECEIVED,
            "normalized": norm,
            "persisted": None,
            "emitted": False,
            "error": None,
            "stats": self.stats,
        }

        if not phone and not body:
            result["error"] = "empty_inbound_payload"
            self._remember({"ok": False, "error": result["error"], "at": _now_iso()})
            return result

        persist_result = None
        if persist and db is not None:
            try:
                from app.services.trade_fulfillment_store import persist_whatsapp_message

                persist_result = persist_whatsapp_message(
                    db,
                    tenant_id=norm.get("tenant_id") or None,
                    phone_e164=phone or "unknown",
                    message_body=body,
                    direction="inbound",
                    status="received",
                    inquiry_id=norm.get("inquiry_id") or None,
                    lead_id=norm.get("lead_id") or None,
                    external_msg_id=norm.get("msg_id") or None,
                    provenance_metadata={
                        "source": norm.get("source") or SOURCE_PLUGIN,
                        "message_type": norm.get("message_type"),
                        "from_name": norm.get("from_name"),
                        "account_id": norm.get("account_id"),
                        "bus": "whatsapp_inbound_event_bus",
                        "received_at": norm.get("timestamp"),
                    },
                )
            except Exception as exc:  # noqa: BLE001
                persist_result = {"persisted": False, "error": str(exc)}
                logger.warning("whatsapp inbound persist failed: %s", exc)
        result["persisted"] = persist_result
        if isinstance(persist_result, dict) and persist_result.get("persisted"):
            self._persisted += 1

        event = Event(
            event_type=EventTypes.WHATSAPP_MESSAGE_RECEIVED,
            data={
                "phone": phone,
                "body": body[:4000],
                "msg_id": norm.get("msg_id"),
                "message_type": norm.get("message_type"),
                "from_name": norm.get("from_name"),
                "tenant_id": norm.get("tenant_id"),
                "account_id": norm.get("account_id"),
                "lead_id": norm.get("lead_id"),
                "inquiry_id": norm.get("inquiry_id"),
                "source": norm.get("source") or SOURCE_PLUGIN,
                "timestamp": norm.get("timestamp"),
                "persisted": bool(isinstance(persist_result, dict) and persist_result.get("persisted")),
            },
            priority=priority,
            source=SOURCE_PLUGIN,
            tenant_id=norm.get("tenant_id") or "",
        )

        emitted = False
        try:
            # EventBus 同步/异步处理器均支持；此处用 emit_sync 保证 webhook 返回前事件已入总线
            if hasattr(event_bus, "emit_sync"):
                event_bus.emit_sync(event)
            else:
                event_bus.emit(event)
            emitted = True
            self._emitted += 1
        except Exception as exc:  # noqa: BLE001
            self._failed_emit += 1
            result["error"] = f"emit_failed: {exc}"
            logger.warning("whatsapp inbound emit failed: %s", exc)

        # W3 · P0-7：入站 → 可跟进询盘（同步、可靠、幂等；不再依赖事件循环时序）
        if db is not None:
            try:
                from app.services.acquisition.inbound_bridge import handle_inbound_message

                result["inbound"] = handle_inbound_message(
                    db,
                    tenant_id=norm.get("tenant_id") or "",
                    channel="whatsapp",
                    phone=phone,
                    email=norm.get("email") or "",
                    body=body,
                    sender_name=norm.get("from_name") or "",
                    external_msg_id=norm.get("msg_id") or "",
                    source=norm.get("source") or SOURCE_PLUGIN,
                    payload={
                        "message_type": norm.get("message_type"),
                        "account_id": norm.get("account_id"),
                    },
                )
            except Exception as exc:  # noqa: BLE001
                result["error"] = f"inbound_bridge_failed: {exc}"
                logger.warning("whatsapp inbound bridge failed: %s", exc)

        result["accepted"] = True
        result["emitted"] = emitted
        result["event_id"] = event.event_id
        self._remember(
            {
                "ok": emitted,
                "event_id": event.event_id,
                "phone": phone,
                "body_len": len(body),
                "persisted": bool(isinstance(persist_result, dict) and persist_result.get("persisted")),
                "at": _now_iso(),
            }
        )
        return result

    def publish_ack(
        self,
        *,
        phone: str,
        msg_id: str = "",
        ack_type: str = "delivered",
        tenant_id: str = "",
        db: Any = None,
        payload_extra: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """发布消息回执/状态事件（delivered/read/failed）。"""
        event_type = EventTypes.WHATSAPP_MESSAGE_ACK
        status = str(ack_type or "delivered").lower()
        if status in {"failed", "error"}:
            event_type = EventTypes.WHATSAPP_MESSAGE_FAILED
        data = {
            "phone": _norm_phone(phone),
            "msg_id": msg_id,
            "ack_type": status,
            "tenant_id": tenant_id,
            "source": SOURCE_PLUGIN,
            "timestamp": _now_iso(),
            **(payload_extra or {}),
        }
        event = Event(
            event_type=event_type,
            data=data,
            priority=EventPriority.NORMAL,
            source=SOURCE_PLUGIN,
            tenant_id=tenant_id,
        )
        emitted = False
        try:
            if hasattr(event_bus, "emit_sync"):
                event_bus.emit_sync(event)
            else:
                event_bus.emit(event)
            emitted = True
        except Exception as exc:  # noqa: BLE001
            logger.warning("whatsapp ack emit failed: %s", exc)
        return {
            "accepted": True,
            "emitted": emitted,
            "event_id": event.event_id,
            "event_type": event_type,
            "data": data,
        }

    def publish_connection_state(
        self,
        *,
        state: str,
        account_id: str = "",
        tenant_id: str = "",
        detail: str = "",
    ) -> dict[str, Any]:
        """发布 WhatsApp 连接状态变化（open/close/connecting）。"""
        event = Event(
            event_type=EventTypes.WHATSAPP_CONNECTION_STATE,
            data={
                "state": str(state or "unknown"),
                "account_id": account_id,
                "tenant_id": tenant_id,
                "detail": detail,
                "source": SOURCE_PLUGIN,
                "timestamp": _now_iso(),
            },
            priority=EventPriority.NORMAL,
            source=SOURCE_PLUGIN,
            tenant_id=tenant_id,
        )
        emitted = False
        try:
            if hasattr(event_bus, "emit_sync"):
                event_bus.emit_sync(event)
            else:
                event_bus.emit(event)
            emitted = True
        except Exception as exc:  # noqa: BLE001
            logger.warning("whatsapp connection emit failed: %s", exc)
        return {
            "accepted": True,
            "emitted": emitted,
            "event_id": event.event_id,
            "event_type": EventTypes.WHATSAPP_CONNECTION_STATE,
        }


# 全局单例
whatsapp_inbound_event_bus = WhatsAppInboundEventBus()


def verify_inbound_token(token: Optional[str]) -> bool:
    """校验 Plugin 入站共享密钥。

    - 未配置 `WHATSAPP_INBOUND_TOKEN` → 开放接收（开发/内网默认）
    - 已配置 → Header 必须匹配
    """
    expected = os.getenv("WHATSAPP_INBOUND_TOKEN", "").strip()
    if not expected:
        return True
    return (token or "").strip() == expected
