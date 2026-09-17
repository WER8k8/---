# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""视频/音频 → 中文听写（Whisper 多后端 + 讯飞 LFASR 直传，长媒体分片扇出扇入）。"""




from __future__ import annotations




import logging

import shutil

import subprocess

import uuid

from pathlib import Path

from typing import Any, Callable



from app.core.config import settings

from app.core.uploads_path import UPLOADS_DIR

from app.services.cross_border.audio_chunk_service import (

    CHUNK_THRESHOLD_SEC,

    ProgressFn,

    cleanup_chunk_files,

    merge_chunk_transcripts,

    probe_media_duration_sec,

    split_wav_chunks,

    transcribe_chunks_parallel,

)

from app.services.cross_border.gemini_audio_asr_service import (

    is_gemini_asr_configured,

    transcribe_with_gemini_audio,

)

from app.services.cross_border.whisper_model_pool import get_faster_whisper_model

from app.services.cross_border.xfyun_lfasr_service import (

    is_xfyun_lfasr_configured,

    prefer_xfyun_lfasr_direct,

    transcribe_with_xfyun_lfasr,

)




logger = logging.getLogger(__name__)




TranscribeFn = Callable[..., dict[str, Any] | None]




def extract_audio_wav(source: Path, *, sample_rate: int = 16000) -> Path | None:

    """ffmpeg 提取 mono 16k wav，供 ASR 使用。"""

    ffmpeg = shutil.which("ffmpeg")

    if not ffmpeg or not source.is_file():

        return None

    out = UPLOADS_DIR / f"asr_{uuid.uuid4().hex[:10]}.wav"

    cmd = [

        ffmpeg,

        "-y",

        "-i",

        str(source),

        "-vn",

        "-ac",

        "1",

        "-ar",

        str(sample_rate),

        "-f",

        "wav",

        str(out),

    ]

    try:

        subprocess.run(cmd, check=True, capture_output=True, timeout=180)

        return out if out.is_file() and out.stat().st_size > 44 else None

    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:

        logger.warning("extract_audio_wav failed: %s", exc)

        return None




def _transcribe_openai(wav: Path) -> dict[str, Any] | None:

    key = (settings.AI_OPENAI_API_KEY or "").strip()

    if not key or key.startswith("your_") or key.startswith("sk-placeholder"):

        return None

    try:

        from openai import OpenAI



        client = OpenAI(api_key=key, base_url=settings.AI_OPENAI_BASE_URL or None)

        with wav.open("rb") as fh:

            resp = client.audio.transcriptions.create(

                model="whisper-1",

                file=fh,

                language="zh",

                response_format="verbose_json",

            )

        text = getattr(resp, "text", None) or (resp.get("text") if isinstance(resp, dict) else "")

        segments = getattr(resp, "segments", None) or (

            resp.get("segments") if isinstance(resp, dict) else []

        )

        return {

            "text": str(text or "").strip(),

            "segments": segments or [],

            "backend": "openai_whisper",

        }

    except Exception as exc:

        logger.warning("openai whisper failed: %s", exc)

        return None




def _transcribe_faster_whisper(wav: Path) -> dict[str, Any] | None:

    try:

        model = get_faster_whisper_model()

    except ImportError:

        return None

    except Exception as exc:

        logger.warning("faster_whisper model load failed: %s", exc)

        return None

    try:

        segments_iter, _info = model.transcribe(str(wav), language="zh")

        parts: list[str] = []

        segs: list[dict[str, Any]] = []

        for seg in segments_iter:

            t = (seg.text or "").strip()

            if t:

                parts.append(t)

                segs.append({"start": seg.start, "end": seg.end, "text": t})

        text = "".join(parts).strip()

        if not text:

            return None

        return {"text": text, "segments": segs, "backend": "faster_whisper"}

    except Exception as exc:

        logger.warning("faster_whisper failed: %s", exc)

        return None




def _transcribe_xfyun_lfasr(

    wav: Path,

    *,

    on_progress: ProgressFn | None = None,

) -> dict[str, Any] | None:

    if not is_xfyun_lfasr_configured():

        return None

    return transcribe_with_xfyun_lfasr(wav, on_progress=on_progress)




def _transcribe_gemini_audio(

    wav: Path,

    *,

    on_progress: ProgressFn | None = None,

) -> dict[str, Any] | None:

    if not is_gemini_asr_configured():

        return None

    return transcribe_with_gemini_audio(wav, on_progress=on_progress)




def _ok_result(result: dict[str, Any] | None, *, hint: str | None = None) -> dict[str, Any] | None:

    if not result or not result.get("text"):

        return None

    out = {

        "ok": True,

        "text": result["text"],

        "segments": result.get("segments") or [],

        "backend": result.get("backend"),

        "hint": hint or "听写完成，请核对后再生成英文字幕",

    }

    if result.get("chunk_count") is not None:

        out["chunk_count"] = result["chunk_count"]

    return out




def _transcribe_chain(*, xfyun_first: bool) -> list[tuple[str, TranscribeFn]]:

    chain: list[tuple[str, TranscribeFn]] = []

    if xfyun_first:

        chain.append(("xfyun_lfasr", _transcribe_xfyun_lfasr))

    chain.append(("faster_whisper", _transcribe_faster_whisper))

    if not xfyun_first:

        chain.append(("xfyun_lfasr", _transcribe_xfyun_lfasr))

    chain.extend(

        [

            ("openai_whisper", _transcribe_openai),

            ("gemini_audio", _transcribe_gemini_audio),

        ]

    )

    return chain




def transcribe_wav_file(

    wav: Path,

    *,

    on_progress: ProgressFn | None = None,

) -> dict[str, Any] | None:

    """单段 wav 听写；配讯飞时优先 LFASR，否则 faster-whisper 优先。"""

    xfyun_first = prefer_xfyun_lfasr_direct()

    for _name, fn in _transcribe_chain(xfyun_first=xfyun_first):

        if fn is _transcribe_faster_whisper:

            result = fn(wav)

        else:

            result = fn(wav, on_progress=on_progress)

        if result and result.get("text"):

            return result

    return None




def _try_xfyun_whole_file(

    wav: Path,

    *,

    duration: float | None,

    on_progress: ProgressFn | None,

) -> dict[str, Any] | None:

    """讯飞整段直传（最长约 5 小时，无需本地分片）。"""

    if not prefer_xfyun_lfasr_direct():

        return None

    if on_progress:

        if duration and duration > CHUNK_THRESHOLD_SEC:

            on_progress(20, f"讯飞云端听写（整段 {int(duration)} 秒）…")

        else:

            on_progress(22, "讯飞云端听写…")

    result = _transcribe_xfyun_lfasr(wav, on_progress=on_progress)

    return _ok_result(

        result,

        hint="听写完成（讯飞云端），请核对后再生成英文字幕",

    )




def _build_chunk_fallback_result(

    wav: Path,

    on_progress: ProgressFn | None,

) -> dict[str, Any]:
    """分片听写失败后的兜底：尝试讯飞整段和Gemini。"""
    xfyun = _transcribe_xfyun_lfasr(wav, on_progress=on_progress)
    hit = _ok_result(xfyun, hint="听写完成（讯飞云端），请核对后再生成英文字幕")
    if hit:
        if on_progress:
            on_progress(92, "讯飞听写完成")
        return hit

    if on_progress:
        on_progress(58, "尝试 Gemini 音频听写…")
    gemini = _transcribe_gemini_audio(wav, on_progress=on_progress)
    hit = _ok_result(gemini, hint="听写完成（Gemini 兜底，请人工核对原文与时间轴）")
    if hit:
        if on_progress:
            on_progress(92, "Gemini 听写完成")
        return hit

    return {
        "ok": False,
        "error": "分片听写均未成功",
        "hint": (
            "请手动粘贴中文解说词；或配置 XFYUN_LFASR_* / faster-whisper / "
            "AI_OPENAI_API_KEY / AI_GEMINI_API_KEY"
        ),
    }




def _transcribe_short_media(
    wav: Path,
    on_progress: ProgressFn | None,
) -> dict[str, Any] | None:
    """短媒体单段听写。"""
    if on_progress:
        on_progress(35, "听写中…")
    result = transcribe_wav_file(wav, on_progress=on_progress)
    hit = _ok_result(result)
    if hit:
        if on_progress:
            on_progress(90, "听写完成")
    return hit




def transcribe_zh_from_media(
    source: Path,
    *,
    on_progress: ProgressFn | None = None,
) -> dict[str, Any]:
    """听写中文；配讯飞时整段直传，否则长媒体分片扇出并行、扇入合并。"""
    if not source.is_file():
        return {"ok": False, "error": "视频文件不存在", "hint": "请重新上传"}

    if on_progress:
        on_progress(10, "提取音频…")
    wav = extract_audio_wav(source)
    if not wav:
        return {
            "ok": False,
            "error": "无法提取音频",
            "hint": "服务器需安装 ffmpeg；或手动粘贴中文解说词",
        }

    chunk_files: list[tuple[Path, float]] = []
    try:
        duration = probe_media_duration_sec(source) or probe_media_duration_sec(wav)

        xfyun_hit = _try_xfyun_whole_file(wav, duration=duration, on_progress=on_progress)
        if xfyun_hit:
            if on_progress:
                on_progress(92, "讯飞听写完成")
            return xfyun_hit

        use_chunks = duration is not None and duration > CHUNK_THRESHOLD_SEC
        if on_progress:
            on_progress(18, "准备听写…" if not use_chunks else f"长视频 {int(duration or 0)} 秒，分片听写…")

        if use_chunks:
            chunk_files = split_wav_chunks(wav)
            if on_progress:
                on_progress(22, f"分片 {len(chunk_files)} 段，并行听写…")
            parts, offsets = transcribe_chunks_parallel(chunk_files, transcribe_wav_file, on_progress=on_progress)
            merged = merge_chunk_transcripts(parts, offsets)

            if not merged.get("text"):
                return _build_chunk_fallback_result(wav, on_progress)

            if on_progress:
                on_progress(92, "合并听写结果…")
            return {
                "ok": True,
                "text": merged["text"],
                "segments": merged.get("segments") or [],
                "backend": merged.get("backend"),
                "chunk_count": merged.get("chunk_count"),
                "hint": "听写完成（分片合并），请核对后再生成英文字幕",
            }

        return _transcribe_short_media(wav, on_progress) or {
            "ok": False,
            "error": "未配置听写引擎",
            "hint": (
                "推荐配置讯飞 LFASR：XFYUN_LFASR_APP_ID + XFYUN_LFASR_SECRET_KEY（配齐即整段直传）；"
                "或本机 faster-whisper + ffmpeg；"
                "或 AI_OPENAI_API_KEY / AI_GEMINI_API_KEY；亦可手动粘贴中文解说词"
            ),
        }
    finally:
        cleanup_chunk_files(chunk_files, keep=wav)
        try:
            if wav.is_file():
                wav.unlink(missing_ok=True)
        except OSError:
            pass
