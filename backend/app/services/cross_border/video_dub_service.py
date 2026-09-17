# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""出海视音频数字人工厂 — 听写 / 多语种翻译 / 原声克隆 / 嘴型对齐 / 矩阵分发。

支持中出海 12 语种（英、阿、西、俄、葡、法、德、日、韩、越、印尼、泰）：
1. 工业级建材专业翻译与语速对齐（Duration Warping）；
2. 零样本原声克隆（Zero-Shot Voice Cloning）：提取原视频干音声纹，用客户本人音色流利讲目标语言；
3. 神经元级嘴型对齐（Neural Lip-Syncing）：驱动出镜人脸嘴唇关键点，声画合一；
4. 全网社媒矩阵分发元数据自动化（YouTube, TikTok, Reels, Facebook, LinkedIn）。
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.executable_resolver import resolve_executable
from app.core.uploads_path import UPLOADS_DIR, ensure_uploads_dir
from app.models.tenant import Tenant
from app.models.user import User
from app.services.ai_invocation_service import invoke_llm
from app.services.cross_border.audio_asr_service import transcribe_zh_from_media
from app.services.cross_border.audio_chunk_service import probe_media_duration_sec
from app.services.cross_border.glossary_helper import build_glossary_prompt_block
from app.services.cross_border.lipsync_service import apply_video_lipsync
from app.services.cross_border.tts_service import (
    mux_video_with_audio,
    resolve_dub_voice,
    synthesize_dub_mp3,
    tts_status,
)
from app.services.cross_border.voice_cloning_service import (
    TARGET_LANG_MAP,
    synthesize_voice_cloned_audio,
)
from app.services.media_factory_service import get_render_task_for_user, ingest_uploaded_media_file
from app.services.media_video_edit_service import load_edit_config, save_edit_config
from app.services.tenant_product_profile_service import get_tenant_product_profile

_JSON_BLOCK = re.compile(r"\{[\s\S]*\}")
logger = logging.getLogger(__name__)

# 长视频若高级区只有寥寥几句，视为过期片段，改走整段听写
_STALE_MANUAL_VIDEO_SEC = 90
_STALE_MANUAL_MAX_CHARS = 150


def _estimate_max_tokens(transcript_zh: str) -> int:
    """估算 LLM 翻译最大 Token 数。"""
    n = len((transcript_zh or "").strip())
    return min(8000, max(2000, n * 3))


def _manual_transcript_too_short_for_video(
    transcript_zh: str,
    video_dur_sec: float | None,
) -> bool:
    """检测手动输入的解说词是否显著短于视频时长。"""
    text = (transcript_zh or "").strip()
    if not text or not video_dur_sec or video_dur_sec <= _STALE_MANUAL_VIDEO_SEC:
        return False
    if len(text) < _STALE_MANUAL_MAX_CHARS:
        return True
    chars_per_sec = len(text) / video_dur_sec
    return chars_per_sec < 0.6


def _parse_json(text: str) -> dict[str, Any]:
    """安全解析 LLM 返回的 JSON。"""
    raw = (text or "").strip()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        pass
    match = _JSON_BLOCK.search(raw)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return {}


def _url_to_local_path(url: str | None) -> Path | None:
    """把 /uploads/ 相对 URL 转为本地绝对路径。"""
    if not url:
        return None
    path_part = url.split("?", 1)[0]
    if path_part.startswith("/uploads/"):
        candidate = UPLOADS_DIR / path_part.removeprefix("/uploads/")
        return candidate if candidate.is_file() else None
    return None


def _resolve_media_source_path(url: str | None) -> tuple[Path | None, Path | None]:
    """解析可听写/烧录的本地媒体路径；云端 URL 会临时下载。返回 (path, temp_to_cleanup)。"""
    local = _url_to_local_path(url)
    if local:
        return local, None
    if not url:
        return None, None
    path_part = url.split("?", 1)[0]
    if not path_part.startswith(("http://", "https://")):
        return None, None
    suffix = Path(path_part).suffix.lower()
    if suffix not in {".mp4", ".webm", ".mov", ".avi", ".mkv", ".mp3", ".wav", ".m4a"}:
        suffix = ".mp4"
    tmp = UPLOADS_DIR / f"asr_fetch_{uuid.uuid4().hex[:10]}{suffix}"
    try:
        ensure_uploads_dir()
        with httpx.Client(timeout=180, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
            if not resp.content:
                return None, None
            tmp.write_bytes(resp.content)
        return (tmp, tmp) if tmp.is_file() else (None, None)
    except Exception as exc:
        logger.warning("download media for asr failed: %s", exc)
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        return None, None


def _format_srt(segments: list[dict[str, Any]], target_lang: str = "en") -> str:
    """把分段列表格式化为标准 SRT 字幕格式。"""
    lines: list[str] = []
    for i, seg in enumerate(segments, start=1):
        start = seg.get("start") or "00:00:00,000"
        end = seg.get("end") or "00:00:05,000"
        text = str(
            seg.get(f"text_{target_lang}")
            or seg.get("text_translated")
            or seg.get("text_en")
            or seg.get("text")
            or ""
        ).strip()
        if not text:
            continue
        lines.extend([str(i), f"{start} --> {end}", text, ""])
    return "\n".join(lines).strip()


async def transcribe_video_task(
    db: Session,
    tenant: Tenant,
    user: User,
    *,
    media_task_id: str,
    on_progress: Any | None = None,
) -> dict[str, Any]:
    """对视频任务进行 ASR 中文解说转写。"""
    task = get_render_task_for_user(db, media_task_id, user)
    if not task or str(task.tenant_id or "") != str(tenant.id):
        return {"ok": False, "error": "找不到该视频"}
    source_path, temp_path = _resolve_media_source_path(task.result_url)
    if not source_path:
        return {
            "ok": False,
            "error": "无法读取视频文件",
            "hint": "请重新上传，或手动粘贴中文解说词",
        }
    try:
        result = await asyncio.to_thread(
            transcribe_zh_from_media,
            source_path,
            on_progress=on_progress,
        )
    finally:
        if temp_path and temp_path.is_file():
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
    if result.get("ok"):
        cfg = load_edit_config(task)
        cfg["cross_border_asr"] = {
            "text": result.get("text"),
            "backend": result.get("backend"),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        save_edit_config(db, task, cfg)
    return result


async def _translate_script(
    db: Session,
    tenant: Tenant,
    *,
    transcript_zh: str,
    product_hint: str,
    target_lang: str = "en",
) -> dict[str, Any]:
    """将中文解说词精准译为目标语言配音稿，并产出海外社媒分发文案与分段时间戳。"""
    glossary = build_glossary_prompt_block(db)
    lang_info = TARGET_LANG_MAP.get(target_lang, TARGET_LANG_MAP["en"])
    lang_name = lang_info["name"]
    lang_en_name = lang_info["en_name"]

    prompt = (
        f"你是资深跨国外贸专家与顶级视音频本土化译配导演。\n"
        f"请把下方中文视频解说词翻译成地道、专业的【{lang_name}（{lang_en_name}）】配音解说稿与字幕。\n"
        f"受众是海外专业建材工程承包商、建材分销商与批发采购商。\n\n"
        "【严格执行原则】：\n"
        "1. 忠实翻译：精准表达中文原文核心事实，保持带货感染力与工厂真实感，禁止虚假空泛套话；\n"
        "2. 术语专业：精准应用建材行业与外贸术语（尺寸、材质、测试认证、装箱装柜配载）；\n"
        "3. 语速与口型贴合：译文长度需适配口型对齐与真人朗读节奏，避免语句过长造成音画不同步；\n"
        "4. 社媒爆款矩阵：同步生成适配 YouTube Shorts / TikTok / Reels / LinkedIn 的海外爆款英文标题、帖子简介与标签。\n\n"
        f"工厂参考信息: {product_hint}\n"
        f"建材外贸词库: {glossary}\n\n"
        f"中文原文:\n{transcript_zh.strip()}\n\n"
        "必须严格输出纯 JSON（不要多余说明）：\n"
        "{\n"
        f'  "script_translated": "完整{lang_name}配音解说稿",\n'
        '  "script_en": "完整英文对照译文",\n'
        f'  "target_lang": "{target_lang}",\n'
        '  "segments": [\n'
        f'    {{"start": "00:00:00,000", "end": "00:00:04,000", "text_translated": "...", "text_{target_lang}": "...", "text_en": "..."}}\n'
        '  ],\n'
        '  "social_copy": {\n'
        '    "title": "海外社媒爆款标题（英文，含核心建材品类关键词）",\n'
        '    "description": "社媒引流文案（介绍产品亮点、工厂实力与询盘 CTA 引导）",\n'
        '    "tags": ["BuildingMaterials", "DirectFactory", "Wholesale", "ExportSupplier"],\n'
        '    "hashtags": "#BuildingMaterials #FactoryWholesale #CustomFabrication"\n'
        '  },\n'
        '  "notes_zh": "中文要点说明与商务建议"\n'
        "}"
    )

    result = await invoke_llm(
        db,
        prompt=prompt,
        scenario="inference",
        max_tokens=_estimate_max_tokens(transcript_zh),
        tenant_id=str(tenant.id),
        lane="customer",
    )
    parsed = _parse_json(str(result.get("content") or ""))

    # 兜底规范
    trans_text = parsed.get("script_translated") or parsed.get("script_en") or str(result.get("content") or "")
    parsed["script_translated"] = trans_text
    parsed["script_en"] = parsed.get("script_en") or trans_text
    parsed["target_lang"] = target_lang

    if not parsed.get("segments") or not isinstance(parsed.get("segments"), list):
        parsed["segments"] = [
            {
                "start": "00:00:00,000",
                "end": "00:00:08,000",
                "text_translated": trans_text[:200],
                f"text_{target_lang}": trans_text[:200],
                "text_en": parsed["script_en"][:200],
            }
        ]
    if not parsed.get("social_copy") or not isinstance(parsed.get("social_copy"), dict):
        parsed["social_copy"] = {
            "title": f"High Quality {product_hint} Factory Tour & Production",
            "description": f"Direct manufacturer for {product_hint}. OEM/ODM customization available. Inquire today for catalogs and quotation.",
            "tags": ["BuildingMaterials", "FactoryDirect", "ExportSupplier"],
            "hashtags": "#BuildingMaterials #FactoryDirect #GlobalExport",
        }
    parsed["model"] = result.get("model")
    return parsed


def _burn_subtitles(source: Path, srt_path: Path, output: Path) -> bool:
    """使用 FFmpeg 把 SRT 硬字幕烧录到视频中。"""
    ffmpeg = resolve_executable("ffmpeg")
    if not ffmpeg or not source.is_file() or not srt_path.is_file():
        return False
    srt_esc = str(srt_path).replace("\\", "/").replace(":", "\\:")
    cmd = [
        ffmpeg,
        "-y",
        "-i", str(source),
        "-vf", f"subtitles='{srt_esc}'",
        "-c:a", "copy",
        str(output),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=300)
        return output.is_file()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


async def _resolve_transcript(
    db: Session,
    task: Any,
    zh_text: str,
    source_path: Path | None,
    video_dur_sec: float | None,
    auto_asr: bool,
    on_progress: Any | None,
) -> tuple[str, dict[str, Any] | None, list[str]]:
    """解析/听写中文解说词，返回 (zh_text, asr_meta, warnings)。"""
    warnings: list[str] = []
    asr_meta: dict[str, Any] | None = None
    manual_chars = len(zh_text)

    if (
        source_path
        and zh_text
        and not auto_asr
        and _manual_transcript_too_short_for_video(zh_text, video_dur_sec)
    ):
        if on_progress:
            on_progress(12, "高级区解说过短，正在整段听写…")
        asr = await asyncio.to_thread(
            transcribe_zh_from_media,
            source_path,
            on_progress=on_progress,
        )
        asr_meta = asr
        if asr.get("ok") and asr.get("text"):
            zh_text = str(asr["text"]).strip()
            warnings.append(
                f"检测到高级区仅 {manual_chars} 字，已对约 {int(video_dur_sec or 0)} 秒视频整段听写。"
            )
        else:
            warnings.append(
                f"高级区仅 {manual_chars} 字，与约 {int(video_dur_sec or 0)} 秒视频不匹配；"
                "自动听写未成功，成片可能只有部分配音。"
            )

    if not zh_text and (auto_asr or not zh_text) and source_path:
        if on_progress:
            on_progress(15, "正在自动听写原片中文解说词…")
        asr = await asyncio.to_thread(
            transcribe_zh_from_media,
            source_path,
            on_progress=on_progress,
        )
        asr_meta = asr
        if asr.get("ok") and asr.get("text"):
            zh_text = str(asr["text"]).strip()

    return zh_text, asr_meta, warnings


async def run_video_dub_job(
    db: Session,
    tenant: Tenant,
    user: User,
    *,
    media_task_id: str,
    transcript_zh: str | None = None,
    voice_consent: bool = False,
    output_mode: str = "dub",
    auto_asr: bool = False,
    tts_voice: str | None = None,
    dub_voice_gender: str = "auto",
    target_lang: str = "en",
    voice_clone: bool = True,
    lip_sync: bool = True,
    distribute_platforms: list[str] | None = None,
    on_progress: Any | None = None,
) -> dict[str, Any]:
    """主执行流水线：中文产品片 → 听写 → 12 语种翻译 → 原声克隆 → 嘴型对齐 → 矩阵分发。"""
    task = get_render_task_for_user(db, media_task_id, user)
    if not task or str(task.tenant_id or "") != str(tenant.id):
        return {"ok": False, "error": "找不到该视频，请先上传中文产品片"}

    profile = get_tenant_product_profile(db, str(tenant.id))
    product_hint = profile.get("primary_product") or task.title or tenant.name
    source_path, temp_path = _resolve_media_source_path(task.result_url)
    video_dur_sec = probe_media_duration_sec(source_path) if source_path else None
    warnings: list[str] = []
    ensure_uploads_dir()
    dub_id = uuid.uuid4().hex[:12]

    try:
        # 1. 中文解说词识别与听写
        zh_text, asr_meta, asr_warnings = await _resolve_transcript(
            db, task, (transcript_zh or "").strip(), source_path, video_dur_sec, auto_asr, on_progress
        )
        warnings.extend(asr_warnings)
        if not zh_text:
            return {
                "ok": False,
                "error": "缺少中文解说词",
                "error_code": "TRANSCRIPT_REQUIRED",
                "hint": "自动听写未成功。请配置 Whisper/讯飞听写，或手动输入中文解说词后重试。",
                "media_task_id": str(task.id),
                "asr": asr_meta,
            }

        # 2. 目标语言大模型翻译与社媒爆款文案生成
        target_lang_clean = (target_lang or "en").lower().strip()
        lang_info = TARGET_LANG_MAP.get(target_lang_clean, TARGET_LANG_MAP["en"])
        if on_progress:
            on_progress(45, f"翻译成【{lang_info['name']}】专业出海配音稿与社媒文案…")

        translation = await _translate_script(
            db, tenant, transcript_zh=zh_text, product_hint=str(product_hint), target_lang=target_lang_clean
        )
        segments = translation.get("segments") or []
        script_to_speak = str(translation.get("script_translated") or translation.get("script_en") or "").strip()

        # 3. 产出 SRT 字幕文件
        srt_body = _format_srt(segments, target_lang=target_lang_clean)
        srt_name = f"dub_{dub_id}_{target_lang_clean}.srt"
        srt_path = UPLOADS_DIR / srt_name
        srt_path.write_text(srt_body, encoding="utf-8")

        output_url: str | None = None
        audio_url: str | None = None
        output_mode_used = "srt_only"
        voice_clone_applied = False
        lipsync_applied = False
        tts_info = tts_status()
        social_copy = translation.get("social_copy") or {}

        # 4. 配音合成（原声克隆优先，平滑降级多语种神经语音）
        if output_mode in ("dub", "burn", "video"):
            if not voice_consent:
                return {
                    "ok": False,
                    "error": "未勾选配音确认",
                    "hint": "生成出海配音前请勾选确认框",
                    "media_task_id": str(task.id),
                    "transcript_zh": zh_text,
                    "script_en": translation.get("script_en"),
                    "script_translated": script_to_speak,
                    "target_lang": target_lang_clean,
                }
            if not source_path or not source_path.is_file():
                return {
                    "ok": False,
                    "error": "找不到视频源文件",
                    "hint": "请重新上传视频后再生成出海成片",
                }

            mp3_name = f"dub_{dub_id}_{target_lang_clean}.mp3"
            mp3_path = UPLOADS_DIR / mp3_name

            if on_progress:
                on_progress(65, f"提取干音声纹特征，合成【{lang_info['name']}】原声音色…")

            # 调用声线克隆调度器
            clone_res = await synthesize_voice_cloned_audio(
                text=script_to_speak,
                source_media_path=source_path,
                target_lang=target_lang_clean,
                output_mp3_path=mp3_path,
                voice_clone_enabled=voice_clone,
            )
            voice_clone_applied = bool(clone_res.get("cloned"))
            if voice_clone_applied:
                warnings.append(f"成功克隆客户本人音色与发音语调，生成{lang_info['name']}原声。")
            else:
                warnings.append(f"已选用{lang_info['name']}超拟真神经网络语音（{clone_res.get('provider')}）。")

            if mp3_path.is_file() and mp3_path.stat().st_size > 0:
                audio_url = f"/uploads/{mp3_name}"
            else:
                # 再次兜底系统 edge-tts
                fallback_mp3 = await synthesize_dub_mp3(
                    script_en=script_to_speak,
                    segments=segments,
                    voice=lang_info.get("edge_tts"),
                    target_duration_sec=video_dur_sec,
                )
                if fallback_mp3 and fallback_mp3.is_file():
                    audio_url = f"/uploads/{fallback_mp3.name}"
                    mp3_path = fallback_mp3

            # 5. 嘴型对齐与视频合成（Neural Lip-Sync 优先，降级 Smart Mux）
            if mp3_path.is_file() and mp3_path.stat().st_size > 0:
                if on_progress:
                    on_progress(80, "神经元级人脸嘴型对齐驱动与声画渲染…")

                final_mp4_name = f"dub_{dub_id}_{target_lang_clean}_out.mp4"
                final_mp4_path = UPLOADS_DIR / final_mp4_name

                sync_res = await apply_video_lipsync(
                    source_video_path=source_path,
                    audio_path=mp3_path,
                    output_video_path=final_mp4_path,
                    lipsync_enabled=lip_sync,
                )

                if sync_res.get("synced"):
                    lipsync_applied = True
                    output_mode_used = "neural_lipsync_dub"
                    warnings.append("嘴型对齐完成：出镜人口型已精准吻合目标语发音。")
                elif sync_res.get("ok"):
                    output_mode_used = "multilingual_dub"
                else:
                    # 尝试基础声画混合
                    if mux_video_with_audio(source_path, mp3_path, final_mp4_path):
                        output_mode_used = "multilingual_dub"
                    else:
                        output_mode_used = "tts_audio_only"

                if final_mp4_path.is_file() and final_mp4_path.stat().st_size > 0:
                    output_url = f"/uploads/{final_mp4_name}"

        # 6. 字幕烧录模式处理
        if output_mode == "burn" and output_url and Path(UPLOADS_DIR / final_mp4_name).is_file():
            burned_name = f"dub_{dub_id}_{target_lang_clean}_burned.mp4"
            burned_path = UPLOADS_DIR / burned_name
            if _burn_subtitles(final_mp4_path, srt_path, burned_path):
                output_url = f"/uploads/{burned_name}"
                output_mode_used = "dub_with_burned_subtitles"

        # 7. 全网社媒矩阵分发准备
        distribution_results: dict[str, Any] = {}
        if distribute_platforms and output_url:
            if on_progress:
                on_progress(92, "正在准备多平台全网出海分发矩阵…")
            for plat in distribute_platforms:
                distribution_results[plat] = {
                    "platform": plat,
                    "status": "ready_for_dispatch",
                    "title": social_copy.get("title"),
                    "description": social_copy.get("description"),
                    "hashtags": social_copy.get("hashtags"),
                    "video_url": output_url,
                    "queued_at": datetime.now(timezone.utc).isoformat(),
                }
            warnings.append(f"已生成 {len(distribute_platforms)} 个海外平台的矩阵分发草稿与 SEO 元数据。")

        # 8. 保存编辑配置与历史记录
        cfg = load_edit_config(task)
        cfg["cross_border_dub"] = {
            "dub_id": dub_id,
            "transcript_zh": zh_text,
            "script_translated": script_to_speak,
            "script_en": translation.get("script_en"),
            "target_lang": target_lang_clean,
            "target_lang_name": lang_info["name"],
            "notes_zh": translation.get("notes_zh"),
            "social_copy": social_copy,
            "segments": segments,
            "srt_url": f"/uploads/{srt_name}",
            "output_url": output_url,
            "audio_url": audio_url,
            "output_mode": output_mode_used,
            "voice_consent": voice_consent,
            "voice_clone": voice_clone_applied,
            "lip_sync": lipsync_applied,
            "distribution": distribution_results,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if output_url:
            task.edited_result_url = output_url
        save_edit_config(db, task, cfg)

        hint = f"已生成【{lang_info['name']}】出海成片"
        if lipsync_applied and voice_clone_applied:
            hint += "（原声音色克隆 + 神经嘴型对齐已生效），音画完全自然！"
        elif voice_clone_applied:
            hint += "（原声音色克隆已生效），发送前请人工试听核对。"
        else:
            hint += "，发送前请人工听看一遍。"

        return {
            "ok": True,
            "media_task_id": str(task.id),
            "dub_id": dub_id,
            "transcript_zh": zh_text,
            "script_translated": script_to_speak,
            "script_en": translation.get("script_en"),
            "target_lang": target_lang_clean,
            "target_lang_name": lang_info["name"],
            "target_lang_flag": lang_info["flag"],
            "notes_zh": translation.get("notes_zh"),
            "social_copy": social_copy,
            "segments": segments,
            "srt_url": f"/uploads/{srt_name}",
            "output_url": output_url,
            "audio_url": audio_url,
            "output_mode": output_mode_used,
            "voice_consent": voice_consent,
            "voice_clone": voice_clone_applied,
            "lip_sync": lipsync_applied,
            "distribute_platforms": distribute_platforms or [],
            "distribution_status": distribution_results,
            "asr": asr_meta,
            "tts": tts_info,
            "tts_available": True,
            "hint": hint,
            "warnings": warnings,
            "video_duration_sec": video_dur_sec,
        }
    finally:
        if temp_path and temp_path.is_file():
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass


def ingest_client_video(
    db: Session,
    user: User,
    *,
    content: bytes,
    original_filename: str,
    content_type: str | None,
    tenant_id: str,
) -> dict[str, Any]:
    """租户上传中文产品片到媒体存储。"""
    return ingest_uploaded_media_file(
        db,
        user,
        content=content,
        original_filename=original_filename,
        content_type=content_type,
        explicit_tenant_id=tenant_id,
        prefer_local_storage=True,
    )
