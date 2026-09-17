# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""TTS 配音合成 — 开发显式 mock；生产无上游时 503。"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.no_fake_delivery import mock_allowed, stamp_mock

_VOICE_LABELS: dict[str, str] = {
    "male": "男声",
    "female": "女声",
    "loli": "萝莉",
    "uncle": "大叔",
}

# user_id -> recent synthesis records (newest first)
_history: dict[str, list[dict[str, Any]]] = {}
_MAX_HISTORY = 50


def _tts_provider_configured() -> bool:
    """_tts_provider_configured。
    :return: 返回处理结果。
    """
    return bool(
        os.getenv("TTS_API_URL", "").strip()
        or os.getenv("EDGE_TTS_ENABLED", "").strip().lower() in ("1", "true", "yes")
    )


def _estimate_duration_sec(text: str, speed: float) -> str:
    """_estimate_duration_sec。

    参数说明：
    :param text: 参数 text
    :param speed: 参数 speed
    :return: 返回处理结果。
    """
    chars = max(len(text.strip()), 1)
    base = chars / 4.5 / max(speed, 0.5)
    sec = max(1, int(round(base)))
    m, s = divmod(sec, 60)
    return f"{m:02d}:{s:02d}"


def list_tts_history(user_id: str) -> list[dict[str, Any]]:
    """list_tts_history。

    参数说明：
    :param user_id: 参数 user_id
    :return: 返回处理结果。
    """
    return list(_history.get(str(user_id), []))


def synthesize_tts(
    *,
    user_id: str,
    text: str,
    voice: str = "female",
    speed: float = 1.0,
    volume: int = 80,
) -> dict[str, Any]:
    """synthesize_tts。

    参数说明：
    :param user_id: 参数 user_id
    :param text: 参数 text
    :param voice: 参数 voice
    :param speed: 参数 speed
    :param volume: 参数 volume
    :return: 返回处理结果。
    """
    text = (text or "").strip()
    if not text:
        raise ValueError("文本不能为空")

    voice_key = voice if voice in _VOICE_LABELS else "female"
    now = datetime.now(timezone.utc)
    record_id = str(uuid.uuid4())
    summary = text[:40] + ("…" if len(text) > 40 else "")
    if _tts_provider_configured():
        # 真实上游接入点：配置 TTS_API_URL 后在此调用并返回 audio_url
        raise NotImplementedError("TTS_API_URL 已配置但合成适配器尚未接入")

    if not mock_allowed("MEDIA_FACTORY_ALLOW_MOCK"):
        from app.core.no_fake_delivery import NotConfiguredError
        raise NotConfiguredError("TTS_NOT_CONFIGURED", "TTS 合成未配置，请设置 TTS_API_URL")

    payload = stamp_mock(
        {
            "id": record_id,
            "text": summary,
            "voice": _VOICE_LABELS[voice_key],
            "speed": speed,
            "volume": volume,
            "len": _estimate_duration_sec(text, speed),
            "time": now.strftime("%Y-%m-%d %H:%M"),
            "audio_url": None,
            "url": None,
            "probe_mode": "stub",
        },
        reason="tts_synthesis_dev_stub",
    )
    uid = str(user_id)
    bucket = _history.setdefault(uid, [])
    bucket.insert(0, payload)
    del bucket[_MAX_HISTORY:]
    return payload
