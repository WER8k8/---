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
    """尝试外部翻译引擎；未配置返回 None。"""
    # 预留：跨境语言桥 / DeepL / 云翻译 — 未接通时必须 None，禁止 stub 假译
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
