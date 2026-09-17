# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""n8n Webhook 接收服务。

接收 n8n 工作流的回调请求，提供：
- HMAC-SHA256 签名验证
- JSON 数据解析
- 事件类型路由分发
- 触发后续业务流程（通过事件总线）

Endpoint: POST /api/v1/n8n/webhook/{workflow_id}
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from typing import Any, Optional

from app.core.event_bus import Event, EventBus, EventTypes

log = logging.getLogger(__name__)


def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str,
    *,
    algorithm: str = "sha256",
) -> bool:
    """验证 n8n Webhook 签名（HMAC-SHA256）。

    n8n 使用 HMAC-SHA256(secret, body) 生成签名，
    放在请求头 X-N8n-Signature 中。

    Args:
        payload: 原始请求体字节。
        signature: 请求头中的签名值。
        secret: 签名密钥。
        algorithm: 哈希算法，默认 sha256。

    Returns:
        签名是否有效。
    """
    if not secret or not signature:
        return False

    try:
        expected = hmac.new(
            secret.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).hexdigest()
        # 使用 hmac.compare_digest 防止时序攻击
        return hmac.compare_digest(expected, signature)
    except Exception as exc:
        log.warning("Webhook 签名验证异常: %s", exc)
        return False


class N8nWebhookService:
    """n8n Webhook 接收服务。

    处理 n8n 回调请求，验证签名并分发到对应的业务处理器。

    用法:
        service = N8nWebhookService()
        result = await service.handle_webhook(
            workflow_id="wf_001",
            payload=raw_body,
            signature=request.headers.get("X-N8n-Signature", ""),
            secret="your-secret",
        )
    """
    def __init__(self, event_bus: Optional[EventBus] = None) -> None:
        """__init__。

        参数说明：
        :param self: 参数 self
        :param event_bus: 参数 event_bus
        :return: 返回处理结果。
        """
        self._event_bus = event_bus
        # 事件类型 → 业务处理器的映射
        self._handlers: dict[str, callable] = {}
        # 注册内置处理器
        self._register_builtin_handlers()

    def _register_builtin_handlers(self) -> None:
        """注册内置事件处理器。"""
        self._handlers["site_built"] = self._handle_site_built
        self._handlers["content_distributed"] = self._handle_content_distributed
        self._handlers["lead_notified"] = self._handle_lead_notified
        self._handlers["default"] = self._handle_default

    async def handle_webhook(
        self,
        workflow_id: str,
        payload: bytes,
        signature: str,
        secret: str = "",
        *,
        skip_signature_verify: bool = False,
    ) -> dict[str, Any]:
        """处理 n8n Webhook 回调。

        Args:
            workflow_id: 工作流 ID。
            payload: 原始请求体字节。
            signature: HMAC-SHA256 签名。
            secret: 签名密钥。
            skip_signature_verify: 是否跳过签名验证（调试用，生产勿用）。

        Returns:
            处理结果字典：{"success": bool, "workflow_id": str, "event_type": str}

        Raises:
            ValueError: 签名验证失败或数据解析错误。
        """
        start_time = time.monotonic()
        # Step 1: 验证签名
        if not skip_signature_verify and secret:
            if not verify_webhook_signature(payload, signature, secret):
                log.warning("n8n Webhook 签名验证失败: workflow=%s", workflow_id)
                raise ValueError("签名验证失败")

        # Step 2: 解析 JSON 数据
        try:
            data = json.loads(payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            log.error("n8n Webhook JSON 解析失败: workflow=%s, error=%s", workflow_id, exc)
            raise ValueError(f"JSON 解析失败: {exc}")

        # Step 3: 提取事件类型
        event_type = self._extract_event_type(data)
        log.info(
            "n8n Webhook 接收: workflow=%s, event_type=%s, data_keys=%s",
            workflow_id, event_type, list(data.keys()) if isinstance(data, dict) else "N/A",
        )
        # Step 4: 分发到对应处理器
        handler = self._handlers.get(event_type, self._handlers["default"])
        result = await handler(workflow_id=workflow_id, data=data, event_type=event_type)
        # Step 5: 发布事件到事件总线
        if self._event_bus:
            await self._event_bus.emit(Event(
                event_type=f"n8n.webhook.{event_type}",
                data={
                    "workflow_id": workflow_id,
                    "event_type": event_type,
                    "payload": data,
                    "result": result,
                },
                source="n8n_webhook",
            ))

        elapsed = time.monotonic() - start_time
        log.info("n8n Webhook 处理完成: workflow=%s, elapsed=%.3fs", workflow_id, elapsed)
        return {
            "success": True,
            "workflow_id": workflow_id,
            "event_type": event_type,
            "result": result,
            "elapsed_seconds": round(elapsed, 3),
        }

    def _extract_event_type(self, data: Any) -> str:
        """从请求数据中提取事件类型。

        支持多种格式：
        - {"event_type": "site_built", ...}
        - {"event": "site_built", ...}
        - [{"event_type": "site_built", ...}]  （n8n 批量模式）
        """
        if isinstance(data, dict):
            return data.get("event_type") or data.get("event") or "default"
        elif isinstance(data, list) and len(data) > 0:
            first = data[0]
            if isinstance(first, dict):
                return first.get("event_type") or first.get("event") or "default"
        return "default"

    # ============================================================
    # 内置事件处理器
    # ============================================================
    async def _handle_site_built(
        self,
        *,
        workflow_id: str,
        data: dict[str, Any],
        event_type: str,
    ) -> dict[str, Any]:
        """处理建站完成回调。

        n8n 自动建站流程完成后回调，更新产品/站点状态。
        """
        site_url = data.get("site_url") or data.get("url", "")
        product_id = data.get("product_id") or data.get("entity_id", "")
        log.info("建站完成回调: workflow=%s, site=%s, product=%s",
                 workflow_id, site_url, product_id)

        # 发布站点部署事件
        if self._event_bus:
            await self._event_bus.emit(Event(
                event_type=EventTypes.SITE_DEPLOYED,
                data={
                    "site_url": site_url,
                    "product_id": product_id,
                    "source": "n8n",
                    "workflow_id": workflow_id,
                },
                source="n8n_webhook",
            ))

        return {"action": "site_marked_deployed", "site_url": site_url}

    async def _handle_content_distributed(
        self,
        *,
        workflow_id: str,
        data: dict[str, Any],
        event_type: str,
    ) -> dict[str, Any]:
        """处理内容分发完成回调。"""
        platform = data.get("platform", "unknown")
        content_id = data.get("content_id") or data.get("entity_id", "")
        distribution_url = data.get("url") or data.get("distribution_url", "")
        log.info("内容分发完成回调: workflow=%s, platform=%s, content=%s",
                 workflow_id, platform, content_id)

        # 发布内容发布事件
        if self._event_bus:
            await self._event_bus.emit(Event(
                event_type=EventTypes.CONTENT_PUBLISHED,
                data={
                    "platform": platform,
                    "content_id": content_id,
                    "url": distribution_url,
                    "source": "n8n",
                    "workflow_id": workflow_id,
                },
                source="n8n_webhook",
            ))

        return {"action": "content_marked_distributed", "platform": platform}

    async def _handle_lead_notified(
        self,
        *,
        workflow_id: str,
        data: dict[str, Any],
        event_type: str,
    ) -> dict[str, Any]:
        """处理 Lead 通知完成回调。"""
        lead_id = data.get("lead_id") or data.get("entity_id", "")
        sales_rep = data.get("sales_rep") or data.get("assigned_to", "")
        notification_method = data.get("method", "email")
        log.info("Lead 通知完成回调: workflow=%s, lead=%s, rep=%s",
                 workflow_id, lead_id, sales_rep)

        # 发布 Lead 更新事件
        if self._event_bus:
            await self._event_bus.emit(Event(
                event_type=EventTypes.LEAD_UPDATED,
                data={
                    "lead_id": lead_id,
                    "sales_rep": sales_rep,
                    "notification_method": notification_method,
                    "source": "n8n",
                    "workflow_id": workflow_id,
                },
                source="n8n_webhook",
            ))

        return {"action": "lead_notified", "lead_id": lead_id}

    async def _handle_default(
        self,
        *,
        workflow_id: str,
        data: Any,
        event_type: str,
    ) -> dict[str, Any]:
        """默认处理器：记录未知的回调数据。"""
        log.info("n8n Webhook 默认处理: workflow=%s, event_type=%s", workflow_id, event_type)
        return {"action": "logged", "data_type": type(data).__name__}
