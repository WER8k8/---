"""全媒体工作室能力注册表 — ASR / 剪辑适配器 / TTS，供前端枢纽页与运维探测。"""

from __future__ import annotations

from app.core.executable_resolver import is_executable_available
from typing import Any

from app.core.config import settings
from app.services.cross_border.gemini_audio_asr_service import is_gemini_asr_configured
from app.services.cross_border.tts_service import tts_status
from app.services.cross_border.opensource_localization_registry import (
    build_recommended_localization_stack,
    list_opensource_localization_providers,
)
from app.services.cross_border.xfyun_lfasr_service import (
    is_xfyun_lfasr_configured,
    prefer_xfyun_lfasr_direct,
    use_ifasr_llm_api,
)
from app.services.cross_border.youding_self_hosted_provider import is_youding_self_hosted_configured


def _openai_configured() -> bool:
    """实现 openaiconfigured 的功能。
    
    :return: 返回 bool 结果
    """
    key = (settings.AI_OPENAI_API_KEY or "").strip()
    return bool(key) and not key.startswith("your_") and not key.startswith("sk-placeholder")


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


def list_asr_capabilities() -> dict[str, Any]:
    """听写引擎清单（按产品优先级；configured 仅反映真实密钥/依赖）。"""
    xfyun_ok = is_xfyun_lfasr_configured()
    ifasr = xfyun_ok and use_ifasr_llm_api()
    items: list[dict[str, Any]] = [
        {
            "id": "xfyun_ifasr_llm",
            "label": "讯飞录音文件转写大模型",
            "mode": "cloud",
            "configured": ifasr,
            "preferred": prefer_xfyun_lfasr_direct() and ifasr,
            "doc": "https://www.xfyun.cn/doc/spark/asr_llm/Ifasr_llm.html",
        },
        {
            "id": "xfyun_lfasr",
            "label": "讯飞 LFASR（raasr 旧版）",
            "mode": "cloud",
            "configured": xfyun_ok and not ifasr,
            "preferred": False,
            "doc": "https://www.xfyun.cn/doc/asr/lfasr/API.html",
        },
        {
            "id": "faster_whisper",
            "label": "本机 faster-whisper",
            "mode": "local",
            "configured": _faster_whisper_available(),
            "preferred": not prefer_xfyun_lfasr_direct(),
            "doc": None,
        },
        {
            "id": "openai_whisper",
            "label": "OpenAI Whisper API",
            "mode": "cloud",
            "configured": _openai_configured(),
            "preferred": False,
            "doc": None,
        },
        {
            "id": "gemini_audio",
            "label": "Gemini 音频听写（兜底）",
            "mode": "cloud",
            "configured": is_gemini_asr_configured(),
            "preferred": False,
            "doc": None,
        },
        {
            "id": "browser_whisper",
            "label": "浏览器 Whisper（OpenCut/Fly-Cut）",
            "mode": "browser",
            "configured": False,
            "preferred": False,
            "status": "planned",
            "doc": "https://opencut.dev/docs/transcription/",
        },
    ]
    active = [x for x in items if x.get("configured")]
    for row in items:
        row["active_in_chain"] = row.get("configured") or row.get("status") == "planned"
    return {
        "engines": items,
        "primary": active[0]["id"] if active else None,
        "chain_order": [x["id"] for x in items if x.get("configured")] or ["none"],
    }


def list_editor_adapters() -> list[dict[str, Any]]:
    """Web 剪辑适配器（集成状态；ref 仅 _ref/ 对照，不进 admin 主包）。"""
    fly_url = (getattr(settings, "FLY_CUT_EMBED_URL", None) or "").strip()
    opencut_url = (getattr(settings, "OPENCUT_EMBED_URL", None) or "").strip()
    fly_ok = bool(fly_url)
    opencut_ok = bool(opencut_url)
    return [
        {
            "id": "native_preview",
            "label": "优丁预览 + 一键出海",
            "status": "integrated",
            "stack": "vue3",
            "route": "/client/video-overseas",
        },
        {
            "id": "video_studio_hub",
            "label": "全媒体剪辑台枢纽",
            "status": "integrated",
            "stack": "vue3",
            "route": "/client/video-studio",
        },
        {
            "id": "fly_cut",
            "label": "Fly-Cut（Vue3 剪映克隆）",
            "status": "integrated" if fly_ok else "planned",
            "stack": "vue3",
            "github": "https://github.com/x007xyz/fly-cut",
            "ref_path": "_ref/fly-cut",
            "route": "/client/video-editor/fly-cut",
            "embed_url": fly_url or None,
            "configured": fly_ok,
            "access_note": None if fly_ok else "设置 FLY_CUT_EMBED_URL 后可用 iframe 嵌入",
        },
        {
            "id": "opencut",
            "label": "OpenCut",
            "status": "integrated" if opencut_ok else "planned",
            "stack": "react",
            "github": "https://github.com/OpenCut-app/OpenCut",
            "ref_path": "_ref/opencut",
            "route": "/client/video-editor/opencut",
            "embed_url": opencut_url or None,
            "configured": opencut_ok,
            "access_note": None if opencut_ok else "设置 OPENCUT_EMBED_URL 后可用 iframe 嵌入",
        },
        {
            "id": "twick_sdk",
            "label": "Twick SDK",
            "status": "planned",
            "stack": "react",
            "github": "https://github.com/ncounterspecialist/twick",
        },
        {
            "id": "openreel",
            "label": "OpenReel Video",
            "status": "eval",
            "stack": "react",
            "github": "https://github.com/Augani/openreel-video",
        },
    ]


def list_localization_providers() -> list[dict[str, Any]]:
    """整片本地化上游（自研链 / 开源 sidecar / 第三方 SaaS）。"""
    vozo_key = (getattr(settings, "VOZO_API_KEY", None) or "").strip()
    vozo_ok = bool(vozo_key) and not vozo_key.startswith("your_")
    self_hosted_ok = is_youding_self_hosted_configured()
    opensource = list_opensource_localization_providers()
    return [
        {
            "id": "self_hosted",
            "label": "自研链（讯飞/Whisper → LLM → edge-tts）",
            "status": "integrated",
            "configured": self_hosted_ok,
            "mode": "self_hosted",
            "outputs": ["srt", "tts_mp3", "subtitle_burn", "english_dub_mux"],
            "lip_sync": False,
            "doc": "docs/cross-border-async-jobs-design.md",
        },
        *opensource,
        {
            "id": "vozo_ai",
            "label": "Vozo AI（翻译+配音+口型）",
            "status": "eval",
            "configured": vozo_ok,
            "mode": "saas",
            "outputs": ["translated_video", "srt", "lip_sync", "visual_translate"],
            "lip_sync": True,
            "api_doc": "https://www.vozo.ai/docs/api_reference/get_started",
            "access_note": "Enterprise/API Key 联系 bd@vozo.ai",
        },
    ]


def build_media_studio_capabilities() -> dict[str, Any]:
    """实现 构建mediastudiocapabilities 的功能。
    
    :return: 返回 dict[str, Any] 结果
    """
    asr = list_asr_capabilities()
    editors = list_editor_adapters()
    tts = tts_status()
    localization = list_localization_providers()
    recommended = build_recommended_localization_stack()
    return {
        "product_id": "CROSS-BORDER-MEDIA-STUDIO-01",
        "pipeline": [
            {"step": "upload", "label": "上传中文片", "route": "/client/video-overseas"},
            {"step": "one_click", "label": "一键出海", "route": "/client/video-overseas"},
            {"step": "studio", "label": "进阶剪辑", "route": "/client/video-studio"},
            {"step": "distribute", "label": "内容分发", "route": "/client/distribute"},
        ],
        "asr": asr,
        "localization": localization,
        "recommended": recommended,
        "editors": editors,
        "tts": tts,
        "integrated_editor_count": sum(1 for e in editors if e.get("status") == "integrated"),
        "planned_editor_count": sum(1 for e in editors if e.get("status") == "planned"),
    }
