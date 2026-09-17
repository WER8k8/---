# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""获客窗口双向翻译 — 诚实降级插件。

契约：
    · 有引擎：返回译文 provider=引擎名, degraded=False
    · 无引擎：译文=原文, provider=identity, degraded=True
    · 禁止编造译文
"""
from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _try_external_translate(text: str, from_lang: str, to_lang: str) -> Optional[dict[str, Any]]:
    """尝试外部翻译引擎；未配置返回 None。禁止 stub 假译。"""
    # 1) LibreTranslate sidecar（跨境文案机翻，须标注 machine）
    try:
        from app.services.cross_border.libretranslate_sidecar import sidecar_base_url
        import httpx

        base = (sidecar_base_url() or "").rstrip("/")
        if base:
            payload = {
                "q": text,
                "source": "auto" if from_lang in ("", "auto") else from_lang,
                "target": to_lang or "zh",
                "format": "text",
            }
            with httpx.Client(timeout=8.0) as client:
                resp = client.post(f"{base}/translate", json=payload)
            if resp.status_code < 300:
                data = resp.json() if resp.content else {}
                translated = ""
                if isinstance(data, dict):
                    translated = str(data.get("translatedText") or data.get("translated") or "")
                if translated and translated != text:
                    return {"translated": translated, "provider": "libretranslate"}
    except Exception:  # noqa: BLE001
        pass
    return None


def translate_text(
    text: str,
    from_lang: str = "auto",
    to_lang: str = "zh",
) -> dict[str, Any]:
    """翻译入口。无引擎时诚实 identity 降级。"""
    original = (text or "").strip()
    if not original:
        return {
            "original": "",
            "translated": "",
            "from_lang": from_lang,
            "to_lang": to_lang,
            "provider": "identity",
            "degraded": True,
            "message": "空文本",
        }
    if from_lang and to_lang and from_lang == to_lang:
        return {
            "original": original,
            "translated": original,
            "from_lang": from_lang,
            "to_lang": to_lang,
            "provider": "identity",
            "degraded": False,
            "message": "源语言与目标语言相同",
        }
    ext = _try_external_translate(original, from_lang, to_lang)
    if ext:
        return {
            "original": original,
            "translated": ext.get("translated") or original,
            "from_lang": from_lang,
            "to_lang": to_lang,
            "provider": str(ext.get("provider") or "external"),
            "degraded": False,
            "message": "",
        }
    return {
        "original": original,
        "translated": original,
        "from_lang": from_lang,
        "to_lang": to_lang,
        "provider": "identity",
        "degraded": True,
        "message": "翻译引擎未配置，暂显示原文；已记录待接语言桥",
    }
