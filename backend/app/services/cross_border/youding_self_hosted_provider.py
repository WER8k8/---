"""优丁内置真实出海链 — 无 sidecar、无 mock，走 video_dub_service 全链路。"""

from __future__ import annotations

from app.core.executable_resolver import is_executable_available
from typing import Any

from app.core.config import settings
from app.services.cross_border.gemini_audio_asr_service import is_gemini_asr_configured
from app.services.cross_border.tts_service import tts_status
from app.services.cross_border.xfyun_lfasr_service import is_xfyun_lfasr_configured

PROVIDER_ID = "youding_self_hosted"


def _faster_whisper_available() -> bool:
    """实现 fasterwhisperavailable 的功能。
    
    :return: 返回 bool 结果
    """
    if not is_executable_available("ffmpeg"):
        return False
    try:
        import faster_whisper  # noqa: F401
        return True
    except ImportError:
        return False


def _openai_asr_available() -> bool:
    """实现 openaiasravailable 的功能。
    
    :return: 返回 bool 结果
    """
    key = (settings.AI_OPENAI_API_KEY or "").strip()
    return bool(key) and not key.startswith("your_") and not key.startswith("sk-placeholder")


def is_youding_self_hosted_configured() -> bool:
    """ffmpeg + edge-tts + 至少一路真实 ASR。"""
    if not is_executable_available("ffmpeg"):
        return False
    tts = tts_status()
    if not (tts.get("available") or tts.get("edge_tts_available")):
        return False
    return (
        is_xfyun_lfasr_configured()
        or _faster_whisper_available()
        or _openai_asr_available()
        or is_gemini_asr_configured()
    )


def youding_self_hosted_provider_row() -> dict[str, Any]:
    """实现 youdingselfhosted提供商row 的功能。
    
    :return: 返回 dict[str, Any] 结果
    """
    ok = is_youding_self_hosted_configured()
    return {
        "id": PROVIDER_ID,
        "label": "优丁内置真实链（听写→英译→edge-tts 配音）",
        "status": "integrated" if ok else "eval",
        "configured": ok,
        "mode": "self_hosted_real",
        "tier": "real_standard_dub",
        "recommended_rank": 50,
        "lip_sync": False,
        "voice_clone": False,
        "visual_translate": False,
        "subtitle_erase": False,
        "outputs": ["srt", "tts_dub", "english_dub_mux"],
        "github": None,
        "access_note": None if ok else "需 ffmpeg、edge-tts 与讯飞/Whisper 等听写引擎",
        "comparable_to": ["vozo_standard"],
        "honesty_note": "非口型精品；产出真实 mp4/srt，禁止占位文案",
    }
