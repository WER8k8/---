# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""精品出海轨编排 — 开源 sidecar / Vozo / 回退禁止假成功。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.models.user import User
from app.services.cross_border.opensource_localization_registry import (
    pick_active_opensource_provider,
)
from app.services.cross_border.opensource_localization_service import run_opensource_premium_job
from app.services.cross_border.vozo_localization_service import (
    is_vozo_configured,
    run_vozo_premium_job,
)
from app.services.cross_border.video_dub_service import run_video_dub_job
from app.services.media_factory_service import get_render_task_for_user
from app.services.media_video_edit_service import load_edit_config, save_edit_config

ProgressFn = Callable[[int, str], None] | None

TrackId = str  # standard | opensource_premium | vozo


async def _run_premium_opensource_track(
    db: Session,
    tenant: Tenant,
    user: User,
    media_task_id: str,
    transcript_zh: str | None,
    voice_consent: bool,
    output_mode: str,
    dub_voice_gender: str,
    localization_provider: str | None,
    track_norm: str,
    task: Any,
    on_progress: ProgressFn,
    target_lang: str = "en",
    voice_clone: bool = True,
    lip_sync: bool = True,
    distribute_platforms: list[str] | None = None,
) -> dict[str, Any]:
    """开源精品轨：选择可用 provider 并执行配音/字幕生成。"""
    active = pick_active_opensource_provider(localization_provider)
    if not active:
        return {
            "ok": False,
            "error_code": "OPENSOURCE_NOT_CONFIGURED",
            "hint": (
                "无可用的真实本地化上游。请配置听写+ffmpeg+edge-tts，"
                "或部署通过健康探测的 Linly/CosyVoice/MuseTalk sidecar。"
            ),
        }
    if active["id"] == "youding_self_hosted":
        result = await run_video_dub_job(
            db,
            tenant,
            user,
            media_task_id=media_task_id,
            transcript_zh=transcript_zh,
            voice_consent=voice_consent,
            output_mode=output_mode,
            auto_asr=not (transcript_zh or "").strip(),
            dub_voice_gender=dub_voice_gender,
            target_lang=target_lang,
            voice_clone=voice_clone,
            lip_sync=lip_sync,
            distribute_platforms=distribute_platforms,
            on_progress=on_progress,
        )
        if result.get("ok"):
            result["localization_provider"] = "youding_self_hosted"
            result["localization_mode"] = "self_hosted_real"
            result["track"] = track_norm
        return result
    else:
        return await run_opensource_premium_job(
            result_url=task.result_url,
            provider_id=localization_provider or active["id"],
            on_progress=on_progress,
        )


async def run_premium_overseas_job(
    db: Session,
    tenant: Tenant,
    user: User,
    *,
    media_task_id: str,
    track: TrackId = "opensource_premium",
    localization_provider: str | None = None,
    transcript_zh: str | None = None,
    voice_consent: bool = False,
    output_mode: str = "dub",
    dub_voice_gender: str = "auto",
    target_lang: str = "en",
    voice_clone: bool = True,
    lip_sync: bool = True,
    distribute_platforms: list[str] | None = None,
    on_progress: ProgressFn = None,
) -> dict[str, Any]:
    """精品出海轨执行入口。"""
    task = get_render_task_for_user(db, media_task_id, user)
    if not task or str(task.tenant_id or "") != str(tenant.id):
        return {"ok": False, "error": "找不到该视频，请先上传中文产品片"}

    if output_mode == "dub" and not voice_consent:
        return {
            "ok": False,
            "error": "未勾选配音确认",
            "hint": "精品出海生成配音前请勾选确认框",
        }

    track_norm = (track or "opensource_premium").strip().lower()
    if track_norm == "vozo":
        if not is_vozo_configured():
            return {
                "ok": False,
                "error_code": "VOZO_NOT_CONFIGURED",
                "hint": "Vozo 商业精品轨未配置 VOZO_API_KEY",
            }
        result = await run_vozo_premium_job(
            result_url=task.result_url,
            on_progress=on_progress,
        )
    elif track_norm in ("opensource_premium", "opensource", "premium"):
        result = await _run_premium_opensource_track(
            db,
            tenant,
            user,
            media_task_id,
            transcript_zh,
            voice_consent,
            output_mode,
            dub_voice_gender,
            localization_provider,
            track_norm,
            task,
            on_progress,
            target_lang=target_lang,
            voice_clone=voice_clone,
            lip_sync=lip_sync,
            distribute_platforms=distribute_platforms,
        )
    elif track_norm == "standard":
        return await run_video_dub_job(
            db,
            tenant,
            user,
            media_task_id=media_task_id,
            transcript_zh=transcript_zh,
            voice_consent=voice_consent,
            output_mode=output_mode,
            auto_asr=not (transcript_zh or "").strip(),
            dub_voice_gender=dub_voice_gender,
            target_lang=target_lang,
            voice_clone=voice_clone,
            lip_sync=lip_sync,
            distribute_platforms=distribute_platforms,
            on_progress=on_progress,
        )
    else:
        return {
            "ok": False,
            "error_code": "UNKNOWN_TRACK",
            "hint": f"未知 track: {track}",
        }

    if not result.get("ok"):
        result.setdefault("media_task_id", str(task.id))
        result.setdefault("track", track_norm)
        return result

    cfg = load_edit_config(task)
    cfg["cross_border_premium"] = {
        **result,
        "track": track_norm,
        "media_task_id": str(task.id),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    save_edit_config(db, task, cfg)
    result["media_task_id"] = str(task.id)
    result["track"] = track_norm
    return result
