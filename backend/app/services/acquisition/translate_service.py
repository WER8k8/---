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


def _try_llm_translate(text: str, from_lang: str, to_lang: str) -> Optional[dict[str, Any]]:
    """OpenAI 兼容 LLM 机翻真源（P1-1 接线）。未配置返回 None。"""
    from app.core.config import settings

    base = (settings.TRANSLATE_API_BASE_URL or "").rstrip("/")
    if not base:
        return None
    key = (settings.TRANSLATE_API_KEY or "").strip()
    if not key:
        return None
    model = (settings.TRANSLATE_MODEL or "").strip() or "Atria-Dawn-Preview"
    import httpx

    src = "auto" if from_lang in ("", "auto") else from_lang
    sys_prompt = (
        "You are a professional B2B trade translator. Translate the user's text from "
        f"'{src}' into '{to_lang}'. Preserve trade terms, units and numbers exactly. "
        "Return ONLY the translation, no explanations, no quotes, no extra text."
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": text},
        ],
        "temperature": 0,
    }
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
    try:
        # Atria-Dawn-Preview 为推理型模型（含 reasoning_content），耗时偏长；给足超时避免误判失败
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(f"{base}/chat/completions", json=payload, headers=headers)
        if resp.status_code >= 300:
            logger.warning("translate LLM HTTP %s: %s", resp.status_code, resp.text[:200])
            return None
        data = resp.json()
        choice = (data.get("choices") or [{}])[0]
        translated = ((choice.get("message") or {}).get("content") or "").strip()
        # 去掉 LLM 可能带的多余引号壳
        if len(translated) >= 2 and translated[0] == translated[-1] and translated[0] in "\"'“”":
            translated = translated[1:-1].strip()
        if translated and translated != text:
            return {
                "translated": translated,
                "provider": f"llm:{model}",
                "mock": False,
                "machine_translated": True,
                "evidence_url": "",
            }
    except Exception:  # noqa: BLE001
        logger.exception("translate LLM 调用失败")
        return None
    return None


def _try_external_translate(text: str, from_lang: str, to_lang: str) -> Optional[dict[str, Any]]:
    """尝试外部翻译引擎；未配置返回 None。禁止 stub 假译当真译。"""
    # 0) OpenAI 兼容 LLM 真源（P1-1）：已配置即真机翻，去 degraded
    llm = _try_llm_translate(text, from_lang, to_lang)
    if llm:
        return llm
    # 1) LibreTranslate sidecar（跨境文案机翻，须标注 machine）
    try:
        from app.services.cross_border.libretranslate_sidecar import (
            sidecar_base_url,
            sidecar_token,
        )
        import httpx

        base = (sidecar_base_url() or "").rstrip("/")
        if base:
            payload = {
                "q": text,
                "source": "auto" if from_lang in ("", "auto") else from_lang,
                "target": to_lang or "zh",
                "format": "text",
            }
            headers = {"Content-Type": "application/json"}
            token = (sidecar_token() or "").strip()
            if token:
                headers["Authorization"] = f"Bearer {token}"
            with httpx.Client(timeout=8.0) as client:
                resp = client.post(f"{base}/translate", json=payload, headers=headers)
            if resp.status_code < 300:
                data = resp.json() if resp.content else {}
                translated = ""
                provider = "libretranslate"
                mock = False
                if isinstance(data, dict):
                    translated = str(data.get("translatedText") or data.get("translated") or "")
                    if str(data.get("mode") or "") == "mock" or data.get("probe_mode") == "stub":
                        mock = True
                        provider = "libretranslate-mock"
                if translated and translated != text:
                    return {
                        "translated": translated,
                        "provider": provider,
                        "mock": mock,
                        "machine_translated": True,
                        "evidence_url": str(data.get("evidence_url") or "") if isinstance(data, dict) else "",
                    }
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
        mock = bool(ext.get("mock"))
        return {
            "original": original,
            "translated": ext.get("translated") or original,
            "from_lang": from_lang,
            "to_lang": to_lang,
            "provider": str(ext.get("provider") or "external"),
            # 引擎已接通：degraded=false；dev stub 标注 mock 但仍算接通
            "degraded": False,
            "machine_translated": True,
            "mock": mock,
            "message": (
                "开发桩机翻（mock），仅供联调；上线须接真 LibreTranslate/人工校对"
                if mock
                else "机翻仅供参考，对外发送前须人工校对"
            ),
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
