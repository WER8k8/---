# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Vozo Enterprise 精品轨 — 有 Key 才调用；无 Key / 失败禁止假成功。"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

ProgressFn = Callable[[int, str], None] | None


def is_vozo_configured() -> bool:
    """实现 isvozoconfigured 的功能。
    
    :return: 返回 bool 结果
    """
    key = (getattr(settings, "VOZO_API_KEY", None) or "").strip()
    return bool(key) and not key.startswith("your_")


def _build_video_url(result_url: str | None) -> str | None:
    """实现 构建视频URL 的功能。
    
    :param result_url: 参数 result_url（类型: str | None）
    :return: 返回 str | None 结果
    """
    if not result_url:
        return None
    part = result_url.split("?", 1)[0]
    if part.startswith(("http://", "https://")):
        return part
    base = (getattr(settings, "CROSS_BORDER_PUBLIC_BASE_URL", None) or "http://127.0.0.1:8001").rstrip("/")
    if part.startswith("/"):
        return f"{base}{part}"
    return f"{base}/{part.lstrip('/')}"


async def _poll_vozo_task(
    client: httpx.AsyncClient,
    base: str,
    task_id: str,
    *,
    on_progress: ProgressFn = None,
    timeout_sec: int = 3600,
) -> dict[str, Any]:
    """实现 pollvozo任务 的功能。
    
    :param client: 参数 client（类型: httpx.AsyncClient）
    :param base: 参数 base（类型: str）
    :param task_id: 参数 task_id（类型: str）
    :param on_progress: 参数 on_progress（类型: ProgressFn）
    :param timeout_sec: 参数 timeout_sec（类型: int）
    :return: 返回 dict[str, Any] 结果
    """
    url = f"{base.rstrip('/')}/v1/tasks/{task_id}"
    elapsed = 0.0
    while elapsed <= timeout_sec:
        resp = await client.get(url)
        if resp.status_code == 404:
            return {"ok": False, "error_code": "VOZO_TASK_NOT_FOUND", "hint": "Vozo 任务不存在"}
        if resp.status_code == 401:
            return {"ok": False, "error_code": "VOZO_AUTH_FAILED", "hint": "Vozo API Key 无效"}
        resp.raise_for_status()
        data = resp.json() if resp.content else {}
        status = str(data.get("status") or data.get("state") or "").lower()
        progress = int(data.get("progress") or 0)
        if on_progress:
            on_progress(max(5, min(95, progress)), data.get("message") or "Vozo 处理中…")
        if status in ("completed", "done", "success"):
            return {"ok": True, "result": data.get("result") or data}
        if status in ("failed", "error"):
            return {
                "ok": False,
                "error_code": "VOZO_JOB_FAILED",
                "hint": data.get("error") or data.get("message") or "Vozo 任务失败",
            }
        await asyncio.sleep(5.0)
        elapsed += 5.0
    return {"ok": False, "error_code": "VOZO_TIMEOUT", "hint": "Vozo 任务超时"}


async def run_vozo_premium_job(
    *,
    result_url: str | None,
    on_progress: ProgressFn = None,
) -> dict[str, Any]:
    """实现 执行vozopremium任务 的功能。
    
    :param result_url: 参数 result_url（类型: str | None）
    :param on_progress: 参数 on_progress（类型: ProgressFn）
    :return: 返回 dict[str, Any] 结果
    """
    if not is_vozo_configured():
        return {
            "ok": False,
            "error_code": "VOZO_NOT_CONFIGURED",
            "hint": "未配置 VOZO_API_KEY；商业精品轨联系 bd@vozo.ai",
        }

    media_url = _build_video_url(result_url)
    if not media_url:
        return {"ok": False, "error_code": "VIDEO_SOURCE_MISSING", "hint": "找不到视频 URL"}

    base = (getattr(settings, "VOZO_API_BASE_URL", None) or "https://api.vozo.ai").rstrip("/")
    key = settings.VOZO_API_KEY.strip()
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    if on_progress:
        on_progress(5, "提交 Vozo Translate&Dub…")

    payload = {
        "media_url": media_url,
        "source_language": "zh-CN",
        "target_language": "en-US",
        "enable_lip_sync": True,
    }
    async with httpx.AsyncClient(timeout=120) as client:
        for path in ("/v1/translate-dub", "/v1/translate_and_dub", "/translate-dub"):
            submit_url = f"{base}{path}"
            try:
                resp = await client.post(submit_url, headers=headers, json=payload)
            except httpx.HTTPError as exc:
                logger.warning("vozo submit %s failed: %s", submit_url, exc)
                continue
            if resp.status_code == 404:
                continue
            if resp.status_code == 401:
                return {"ok": False, "error_code": "VOZO_AUTH_FAILED", "hint": "Vozo API Key 无效"}
            if resp.status_code >= 500:
                return {
                    "ok": False,
                    "error_code": "VOZO_UNAVAILABLE",
                    "hint": f"Vozo 上游 HTTP {resp.status_code}",
                }
            if resp.status_code not in (200, 201, 202):
                return {
                    "ok": False,
                    "error_code": "VOZO_REJECTED",
                    "hint": (resp.text or "")[:300] or f"Vozo HTTP {resp.status_code}",
                }

            data = resp.json() if resp.content else {}
            task_id = data.get("task_id") or data.get("id")
            if task_id:
                polled = await _poll_vozo_task(client, base, str(task_id), on_progress=on_progress)
                if not polled.get("ok"):
                    return polled
                raw = polled.get("result") or {}
            else:
                raw = data.get("result") if isinstance(data.get("result"), dict) else data

            output_url = raw.get("output_url") or raw.get("video_url") or raw.get("translated_video_url")
            srt_url = raw.get("srt_url") or raw.get("subtitle_url")
            if not output_url and not srt_url:
                return {
                    "ok": False,
                    "error_code": "VOZO_NO_OUTPUT",
                    "hint": "Vozo 未返回成片 URL，禁止假成功",
                }

            return {
                "ok": True,
                "output_url": output_url,
                "srt_url": srt_url,
                "script_en": raw.get("script_en") or raw.get("translated_text"),
                "transcript_zh": raw.get("transcript_zh") or raw.get("source_text"),
                "output_mode": "vozo_lip_dub" if output_url else "srt_only",
                "localization_provider": "vozo_ai",
                "localization_mode": "saas",
                "lip_sync": True,
                "visual_translate": bool(raw.get("visual_translate")),
                "human_confirm_required": True,
                "hint": "Vozo 精品成片已返回，发送前请人工听看核对。",
            }

    return {
        "ok": False,
        "error_code": "VOZO_API_NOT_REACHABLE",
        "hint": "Vozo API 路径未接通，请核对 VOZO_API_BASE_URL 与 Enterprise 文档",
    }
