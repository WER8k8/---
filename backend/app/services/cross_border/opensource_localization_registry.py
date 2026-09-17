# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""开源视频本地化上游注册表 — 对标 Vozo / 山海智影；智能优先级见 OPTIMAL_PICK_ORDER。"""



from __future__ import annotations



import shutil

from pathlib import Path

from typing import Any

from urllib.parse import urlparse



from app.core.config import settings

from app.services.cross_border.sidecar_health import is_verified_sidecar_url

from app.services.cross_border.youding_self_hosted_provider import (
    PROVIDER_ID as YOUDING_SELF_HOSTED_ID,
    is_youding_self_hosted_configured,
    youding_self_hosted_provider_row,
)



# 中文带货片出海 · 智能选型顺序（全链路优先于纯组件）

OPTIMAL_PICK_ORDER: tuple[str, ...] = (

    "linly_dubbing",  # 口型+克隆，开源对标山海智影/Vozo 口型

    "youdub_webui",  # 中→英成熟、FastAPI sidecar，集成 ROI 最高

    "v2vt",  # 中英互译+口型一体

    "krillinai",  # CLI/Agent 全链路

    "videolingo",  # 字幕/术语精品

    "narrator_ai",  # 短剧硬字幕擦除

    "pyvideotrans",

    "youding_self_hosted",  # 内置真实链（无口型），sidecar 均不可用时仍可真实出片

    "musetalk",  # 仅口型组件，自动选型时跳过

)



RECOMMENDED_STACK: dict[str, str] = {

    "standard": "self_hosted",

    "open_premium_lip": "linly_dubbing",

    "open_premium_dub": "youdub_webui",

    "open_subtitle_premium": "videolingo",

    "open_short_drama": "narrator_ai",

    "saas_premium": "vozo_ai",

}





def _env_str(name: str) -> str:

    """实现 envstr 的功能。
    
    :param name: 参数 name（类型: str）
    :return: 返回 str 结果
    """
    return (getattr(settings, name, None) or "").strip()





def _path_configured(path_str: str) -> bool:

    """实现 pathconfigured 的功能。
    
    :param path_str: 参数 path_str（类型: str）
    :return: 返回 bool 结果
    """
    if not path_str or path_str.startswith("your_"):

        return False

    p = Path(path_str)
    return p.is_file() or (p.name and shutil.which(path_str) is not None)





def _url_configured(url: str) -> bool:

    """实现 URLconfigured 的功能。
    
    :param url: 参数 url（类型: str）
    :return: 返回 bool 结果
    """
    if not url or url.startswith("your_"):

        return False

    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)





def is_krillinai_configured() -> bool:

    """实现 iskrillinaiconfigured 的功能。
    
    :return: 返回 bool 结果
    """
    cli = _env_str("KRILLINAI_CLI_PATH")
    if _path_configured(cli):

        return True

    url = _env_str("KRILLINAI_SERVICE_URL")
    return _url_configured(url) and is_verified_sidecar_url(url)





def is_linly_dubbing_configured() -> bool:

    """实现 islinlydubbingconfigured 的功能。
    
    :return: 返回 bool 结果
    """
    url = _env_str("LINLY_DUBBING_BASE_URL")
    return _url_configured(url) and is_verified_sidecar_url(url)





def is_youdub_webui_configured() -> bool:

    """实现 isyoudubwebuiconfigured 的功能。
    
    :return: 返回 bool 结果
    """
    url = _env_str("YOUDUB_WEBUI_BASE_URL")
    return _url_configured(url) and is_verified_sidecar_url(url)





def is_videolingo_configured() -> bool:

    """实现 isvideolingoconfigured 的功能。
    
    :return: 返回 bool 结果
    """
    url = _env_str("VIDEOLINGO_BASE_URL")
    return _url_configured(url) and is_verified_sidecar_url(url)





def is_narrator_ai_configured() -> bool:

    """实现 isnarratoraiconfigured 的功能。
    
    :return: 返回 bool 结果
    """
    url = _env_str("NARRATOR_AI_BASE_URL")
    return _url_configured(url) and is_verified_sidecar_url(url)





def is_pyvideotrans_configured() -> bool:

    """实现 ispyvideotransconfigured 的功能。
    
    :return: 返回 bool 结果
    """
    cli = _env_str("PYVIDEOTRANS_CLI_PATH")
    if _path_configured(cli):

        return True

    url = _env_str("PYVIDEOTRANS_BASE_URL")
    return _url_configured(url) and is_verified_sidecar_url(url)





def is_musetalk_configured() -> bool:

    """实现 ismusetalkconfigured 的功能。
    
    :return: 返回 bool 结果
    """
    url = _env_str("MUSETALK_SERVICE_URL")
    return _url_configured(url) and is_verified_sidecar_url(url)





def is_v2vt_configured() -> bool:

    """实现 isv2vtconfigured 的功能。
    
    :return: 返回 bool 结果
    """
    url = _env_str("V2VT_SERVICE_URL")
    return _url_configured(url) and is_verified_sidecar_url(url)





def _rank(provider_id: str) -> int:

    """实现 排名 的功能。
    
    :param provider_id: 参数 provider_id（类型: str）
    :return: 返回 int 结果
    """
    try:

        return OPTIMAL_PICK_ORDER.index(provider_id)

    except ValueError:

        return 999





def _build_opensource_rows_a(linly_ok, youdub_ok, v2vt_ok):
    """开源本地化轨前 3 个 provider（口型/配音类）。"""
    return [
        {
            "id": "linly_dubbing",
            "label": "Linly-Dubbing（口型+克隆 · 开源精品首选）",
            "status": "integrated" if linly_ok else "eval",
            "configured": linly_ok,
            "mode": "opensource",
            "tier": "open_premium_lip",
            "recommended_rank": _rank("linly_dubbing"),
            "lip_sync": True,
            "voice_clone": True,
            "visual_translate": False,
            "subtitle_erase": False,
            "outputs": ["translated_video", "srt", "lip_sync"],
            "github": "https://github.com/Kedreamix/Linly-Dubbing",
            "access_note": "GPU sidecar + LINLY_DUBBING_BASE_URL",
            "comparable_to": ["vozo_lipreal", "shanhai_zhiying_workflow"],
        },
        {
            "id": "youdub_webui",
            "label": "YouDub-webui（中→英配音 · 集成首选）",
            "status": "integrated" if youdub_ok else "eval",
            "configured": youdub_ok,
            "mode": "opensource",
            "tier": "open_premium_dub",
            "recommended_rank": _rank("youdub_webui"),
            "lip_sync": False,
            "voice_clone": True,
            "visual_translate": False,
            "subtitle_erase": False,
            "outputs": ["translated_video", "srt", "voice_clone_dub"],
            "github": "https://github.com/liuzhao1225/YouDub-webui",
            "access_note": "FastAPI sidecar + YOUDUB_WEBUI_BASE_URL",
            "comparable_to": ["shanhai_zhiying_quick", "vozo_standard"],
        },
        {
            "id": "v2vt",
            "label": "v2vt（中英互译+克隆+口型）",
            "status": "integrated" if v2vt_ok else "eval",
            "configured": v2vt_ok,
            "mode": "opensource",
            "tier": "open_premium_lip",
            "recommended_rank": _rank("v2vt"),
            "lip_sync": True,
            "voice_clone": True,
            "visual_translate": False,
            "subtitle_erase": False,
            "outputs": ["translated_video", "srt", "lip_sync"],
            "github": "https://github.com/halfzm/v2vt",
            "access_note": "GPU sidecar + V2VT_SERVICE_URL",
            "comparable_to": ["vozo_lipreal", "shanhai_zhiying_workflow"],
        },
    ]


def _build_opensource_rows_b(krillin_ok, videolingo_ok, narrator_ok):
    """开源本地化轨中间 3 个 provider（全链路/字幕/短剧类）。"""
    return [
        {
            "id": "krillinai",
            "label": "KrillinAI（开源全链路 · CLI/Agent）",
            "status": "integrated" if krillin_ok else "eval",
            "configured": krillin_ok,
            "mode": "opensource",
            "tier": "open_premium_cli",
            "recommended_rank": _rank("krillinai"),
            "lip_sync": False,
            "voice_clone": True,
            "visual_translate": False,
            "subtitle_erase": False,
            "outputs": ["srt", "tts_dub", "bilingual_srt", "horizontal_render", "vertical_render"],
            "github": "https://github.com/krillinai/KrillinAI",
            "access_note": "KRILLINAI_CLI_PATH 或 KRILLINAI_SERVICE_URL",
            "comparable_to": ["vozo_standard", "shanhai_zhiying_workflow"],
        },
        {
            "id": "videolingo",
            "label": "VideoLingo（字幕精品 · 术语+克隆配音）",
            "status": "integrated" if videolingo_ok else "eval",
            "configured": videolingo_ok,
            "mode": "opensource",
            "tier": "open_subtitle_premium",
            "recommended_rank": _rank("videolingo"),
            "lip_sync": False,
            "voice_clone": True,
            "visual_translate": False,
            "subtitle_erase": False,
            "outputs": ["srt", "bilingual_srt", "tts_dub"],
            "github": "https://github.com/Huanshere/VideoLingo",
            "access_note": "sidecar + VIDEOLINGO_BASE_URL",
            "comparable_to": ["vozo_subtitle"],
        },
        {
            "id": "narrator_ai",
            "label": "NarratorAI（短剧译制 · 字幕擦除）",
            "status": "integrated" if narrator_ok else "eval",
            "configured": narrator_ok,
            "mode": "opensource",
            "tier": "open_short_drama",
            "recommended_rank": _rank("narrator_ai"),
            "lip_sync": False,
            "voice_clone": False,
            "visual_translate": False,
            "subtitle_erase": True,
            "outputs": ["srt", "translated_video", "hard_sub_erase"],
            "github": "https://github.com/Narrator-AI/NarratorAI",
            "access_note": "NARRATOR_AI_BASE_URL",
            "comparable_to": ["shanhai_zhiying_short_drama"],
        },
    ]


def _build_opensource_rows_c(pyvideo_ok, muse_ok):
    """开源本地化轨后 2 个 provider（标准替代/口型组件类）。"""
    return [
        {
            "id": "pyvideotrans",
            "label": "pyVideoTrans（ASR+翻译+克隆配音）",
            "status": "integrated" if pyvideo_ok else "eval",
            "configured": pyvideo_ok,
            "mode": "opensource",
            "tier": "open_standard_alt",
            "recommended_rank": _rank("pyvideotrans"),
            "lip_sync": False,
            "voice_clone": True,
            "visual_translate": False,
            "subtitle_erase": True,
            "outputs": ["srt", "tts_dub", "subtitle_burn"],
            "github": "https://github.com/jianchang512/pyvideotrans",
            "access_note": "PYVIDEOTRANS_CLI_PATH 或 PYVIDEOTRANS_BASE_URL",
            "comparable_to": ["vozo_standard"],
        },
        {
            "id": "musetalk",
            "label": "MuseTalk（口型组件 · 接其他轨后段）",
            "status": "integrated" if muse_ok else "eval",
            "configured": muse_ok,
            "mode": "opensource_component",
            "tier": "open_lipsync_component",
            "recommended_rank": _rank("musetalk"),
            "lip_sync": True,
            "voice_clone": False,
            "visual_translate": False,
            "subtitle_erase": False,
            "outputs": ["lip_sync_video"],
            "github": "https://github.com/TMElyralab/MuseTalk",
            "access_note": "MUSETALK_SERVICE_URL；YouDub/自研配音后再对口型",
            "comparable_to": ["vozo_lipreal"],
        },
    ]


def _list_opensource_localization_providers_extracted(r):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param r: 输入参数
    :return: 返回 rows 等计算结果
    """
    """

    开源本地化轨（MS-H）。configured 仅当 CLI 路径存在或 sidecar URL 已填。

    未部署 sidecar 时 status=eval，不得假成功出片。

    """
    krillin_ok = is_krillinai_configured()
    linly_ok = is_linly_dubbing_configured()
    youdub_ok = is_youdub_webui_configured()
    videolingo_ok = is_videolingo_configured()
    narrator_ok = is_narrator_ai_configured()
    pyvideo_ok = is_pyvideotrans_configured()
    muse_ok = is_musetalk_configured()
    v2vt_ok = is_v2vt_configured()
    rows = (
        _build_opensource_rows_a(linly_ok, youdub_ok, v2vt_ok)
        + _build_opensource_rows_b(krillin_ok, videolingo_ok, narrator_ok)
        + _build_opensource_rows_c(pyvideo_ok, muse_ok)
    )
    rows.sort(key=lambda r: r.get("recommended_rank", 999))
    rows.append(youding_self_hosted_provider_row())
    rows.sort(key=lambda r: r.get("recommended_rank", 999))
    return rows

def list_opensource_localization_providers() -> list[dict[str, Any]]:
    """list_opensource_localization_providers。
    :return: 返回处理结果。
    """
    rows = _list_opensource_localization_providers_extracted(r)
    return rows





def _is_full_pipeline_provider(row: dict[str, Any]) -> bool:

    """自动选型时排除仅口型组件（如 MuseTalk）。"""
    if row.get("id") == YOUDING_SELF_HOSTED_ID:

        return True

    outputs = set(row.get("outputs") or [])
    return bool(

        outputs
        & {

            "translated_video",
            "tts_dub",
            "srt",
            "voice_clone_dub",
            "english_dub_mux",

        }

    )





def pick_active_opensource_provider(preferred_id: str | None = None) -> dict[str, Any] | None:

    """按 OPENSOURCE_LOCALIZATION_PREFERRED 或 OPTIMAL_PICK_ORDER 返回已配置项。"""
    rows = list_opensource_localization_providers()
    by_id = {r["id"]: r for r in rows}
    explicit = (preferred_id or _env_str("OPENSOURCE_LOCALIZATION_PREFERRED")).strip()
    if explicit:

        row = by_id.get(explicit)
        if row and row.get("configured"):

            return row

        return None



    for pid in OPTIMAL_PICK_ORDER:

        row = by_id.get(pid)
        if row and row.get("configured") and row.get("status") == "integrated":

            if not _is_full_pipeline_provider(row):

                continue

            return row

    return None





def build_recommended_localization_stack() -> dict[str, Any]:

    """产品智能推荐栈 + 当前实际可激活的开源上游。"""
    active = pick_active_opensource_provider()
    return {

        **RECOMMENDED_STACK,
        "pick_order": list(OPTIMAL_PICK_ORDER),
        "active_opensource_id": active["id"] if active else None,
        "active_opensource_label": active["label"] if active else None,

    }

