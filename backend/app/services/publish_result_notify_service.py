# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""矩阵发布结果通知 — 飞书 / Slack Webhook（诚实：仅汇报验真结果）。"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


def _webhook_url() -> str:
    """_webhook_url。
    :return: 返回处理结果。
    """
    return (
        (settings.PUBLISH_RESULT_WEBHOOK_URL or "").strip()
        or (settings.HERMES_ALERT_WEBHOOK_URL or "").strip()
        or (settings.FEISHU_WEBHOOK_URL or "").strip()
    )


def publish_notify_enabled() -> bool:
    """publish_notify_enabled。
    :return: 返回处理结果。
    """
    if not settings.PUBLISH_RESULT_NOTIFY_ENABLED:
        return False
    return bool(_webhook_url())


def notify_video_distribute_summary(
    *,
    tenant_id: str | None,
    media_task_id: str,
    summary: dict[str, Any],
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    """分发结束后推送摘要（不宣称未验真成功）。"""
    if not publish_notify_enabled():
        return {"sent": False, "reason": "disabled"}

    url = _webhook_url()
    ok = int(summary.get("succeeded") or 0)
    fail = int(summary.get("failed") or 0)
    scheduled = sum(1 for r in results if r.get("publish_state") == "scheduled" or r.get("pending"))
    lines = [
        f"**视频矩阵分发** · 租户 `{tenant_id or '-'}`",
        f"任务 `{media_task_id}`",
        f"验真成功 **{ok}** · 失败 **{fail}** · 定时待链 **{scheduled}**",
    ]
    for r in results[:8]:
        name = r.get("platform_name") or "?"
        if r.get("success") and r.get("platform_post_url"):
            lines.append(f"- ✅ {name}: {r.get('platform_post_url')}")
        elif r.get("pending") or r.get("publish_state") == "scheduled":
            lines.append(f"- ⏱ {name}: 已排期，待平台链接")
        else:
            err = (r.get("error_message") or "失败")[:80]
            lines.append(f"- ❌ {name}: {err}")

    body = "\n".join(lines)
    payload = {
        "msg_type": "text",
        "content": {"text": body},
    }
    # Slack 兼容
    if "hooks.slack.com" in url:
        payload = {"text": body}

    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(url, json=payload)
        sent = resp.status_code in (200, 201, 204)
        return {"sent": sent, "status_code": resp.status_code}
    except Exception as exc:
        logger.warning("publish notify failed: %s", exc)
        return {"sent": False, "error": str(exc)}
