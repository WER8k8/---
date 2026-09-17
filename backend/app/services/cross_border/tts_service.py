# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""英文 TTS — edge-tts（无需 API Key）。"""

from __future__ import annotations

import logging
import re
import subprocess
import uuid
from pathlib import Path
from typing import Any

from app.core.executable_resolver import is_executable_available, resolve_executable
from app.core.uploads_path import UPLOADS_DIR, ensure_uploads_dir
from app.services.cross_border.audio_chunk_service import probe_media_duration_sec

logger = logging.getLogger(__name__)

DEFAULT_VOICE = "en-US-JennyNeural"
DEFAULT_VOICE_FEMALE = "en-US-JennyNeural"
DEFAULT_VOICE_MALE = "en-US-GuyNeural"
_SRT_TIME = re.compile(
    r"^(?:(\d+):)?(\d{1,2}):(\d{1,2})[,.](\d{1,3})$"
)


async def list_english_voices(limit: int = 12) -> list[dict[str, str]]:
    """实现 列出englishvoices 的功能。
    
    :param limit: 参数 limit（类型: int）
    :return: 返回 list[dict[str, str]] 结果
    """
    try:
        import edge_tts
        voices = await edge_tts.list_voices()
        en = [v for v in voices if str(v.get("Locale", "")).startswith("en-")]
        out: list[dict[str, str]] = []
        for v in en[:limit]:
            out.append(
                {
                    "id": str(v.get("ShortName") or ""),
                    "label": f"{v.get('FriendlyName', v.get('ShortName'))} ({v.get('Locale')})",
                    "gender": str(v.get("Gender") or ""),
                }
            )
        return out
    except Exception as exc:
        logger.warning("list_english_voices: %s", exc)
        return [{"id": DEFAULT_VOICE, "label": "Jenny (US English)", "gender": "Female"}]


def voice_id_to_gender(voice_id: str | None) -> str:
    """实现 voiceIDtogender 的功能。
    
    :param voice_id: 参数 voice_id（类型: str | None）
    :return: 返回 str 结果
    """
    vid = (voice_id or "").lower()
    if any(x in vid for x in ("guy", "andrew", "brian", "eric", "steffan", "davis", "jason", "tony")):
        return "male"
    if any(x in vid for x in ("jenny", "aria", "sara", "michelle", "emma", "ana", "sonia")):
        return "female"
    return "unknown"


def resolve_dub_voice(
    *,
    explicit_voice: str | None = None,
    gender_pref: str = "auto",
    source_path: Path | None = None,
) -> dict[str, Any]:
    """选择英文配音音色：显式 voice > 手动男女 > 原片基频推断。"""
    if (explicit_voice or "").strip():
        voice = explicit_voice.strip()
        return {
            "voice": voice,
            "gender": voice_id_to_gender(voice),
            "source": "explicit",
            "pitch_hz": None,
        }

    pref = (gender_pref or "auto").strip().lower()
    detected = "unknown"
    pitch_hz: float | None = None
    if pref == "auto" and source_path and source_path.is_file():
        from app.services.cross_border.voice_gender_infer import infer_voice_gender_from_media
        detected, pitch_hz = infer_voice_gender_from_media(source_path)

    if pref == "male" or detected == "male":
        return {
            "voice": DEFAULT_VOICE_MALE,
            "gender": "male",
            "source": "manual" if pref == "male" else "detected",
            "pitch_hz": pitch_hz,
        }
    if pref == "female" or detected == "female":
        return {
            "voice": DEFAULT_VOICE_FEMALE,
            "gender": "female",
            "source": "manual" if pref == "female" else "detected",
            "pitch_hz": pitch_hz,
        }

    return {
        "voice": DEFAULT_VOICE_MALE,
        "gender": "unknown",
        "source": "default_male",
        "pitch_hz": pitch_hz,
    }


async def synthesize_english_mp3(
    text: str,
    *,
    voice: str = DEFAULT_VOICE,
    output_path: Path | None = None,
) -> Path | None:
    """实现 synthesizeenglishmp3 的功能。
    
    :param text: 参数 text（类型: str）
    :param voice: 参数 voice（类型: str）
    :param output_path: 参数 output_path（类型: Path | None）
    :return: 返回 Path | None 结果
    """
    content = (text or "").strip()
    if not content:
        return None
    ensure_uploads_dir()
    out = output_path or (UPLOADS_DIR / f"tts_{uuid.uuid4().hex[:10]}.mp3")
    try:
        import edge_tts
        comm = edge_tts.Communicate(content[:8000], voice or DEFAULT_VOICE)
        await comm.save(str(out))
        return out if out.is_file() and out.stat().st_size > 0 else None
    except ImportError:
        logger.warning("edge-tts not installed")
        return None
    except Exception as exc:
        logger.warning("synthesize_english_mp3 failed: %s", exc)
        return None


def srt_time_to_seconds(value: str | float | int | None) -> float:
    """实现 srt时间toseconds 的功能。
    
    :param value: 参数 value（类型: str | float | int | None）
    :return: 返回 float 结果
    """
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    raw = str(value).strip()
    if not raw:
        return 0.0
    try:
        return float(raw)
    except ValueError:
        pass
    m = _SRT_TIME.match(raw)
    if not m:
        return 0.0
    h = int(m.group(1) or 0)
    mi = int(m.group(2))
    s = int(m.group(3))
    ms = int(m.group(4).ljust(3, "0")[:3])
    return h * 3600 + mi * 60 + s + ms / 1000.0


def _pad_audio_to_duration(audio: Path, target_sec: float, output: Path) -> bool:
    """短配音轨末尾补静音，避免合成时把整段视频裁成几秒。"""
    ffmpeg = resolve_executable("ffmpeg")
    if not ffmpeg or not audio.is_file() or target_sec <= 0:
        return False
    audio_dur = probe_media_duration_sec(audio) or 0.0
    if audio_dur >= target_sec - 0.25:
        if output.resolve() != audio.resolve():
            try:
                output.write_bytes(audio.read_bytes())
            except OSError:
                return False
        return output.is_file()
    pad_dur = max(0.0, target_sec - audio_dur)
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(audio),
        "-af",
        f"apad=pad_dur={pad_dur:.3f}",
        "-t",
        f"{target_sec:.3f}",
        "-c:a",
        "libmp3lame",
        "-b:a",
        "192k",
        str(output),
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=max(120, int(target_sec) + 30))
        if proc.returncode != 0:
            stderr = (proc.stderr or b"").decode("utf-8", errors="replace")[-400:]
            logger.warning("pad_audio_to_duration failed: %s", stderr)
            return False
        return output.is_file() and output.stat().st_size > 0
    except subprocess.TimeoutExpired:
        return False


async def synthesize_dub_mp3(
    *,
    script_en: str,
    segments: list[dict[str, Any]] | None = None,
    voice: str = DEFAULT_VOICE,
    target_duration_sec: float | None = None,
) -> Path | None:
    """按字幕分段合成英文配音；单段时退化为整段 TTS。"""
    segs = [s for s in (segments or []) if str(s.get("text_en") or s.get("text") or "").strip()]
    if len(segs) <= 1:
        out = await synthesize_english_mp3(script_en, voice=voice)
        if not out or not target_duration_sec:
            return out
        padded = UPLOADS_DIR / f"tts_pad_{uuid.uuid4().hex[:10]}.mp3"
        if _pad_audio_to_duration(out, target_duration_sec, padded):
            return padded
        return out

    ffmpeg = resolve_executable("ffmpeg")
    if not ffmpeg:
        return await synthesize_english_mp3(script_en, voice=voice)

    clip_paths: list[Path] = []
    list_file: Path | None = None
    try:
        for seg in segs:
            text = str(seg.get("text_en") or seg.get("text") or "").strip()
            if not text:
                continue
            clip = await synthesize_english_mp3(
                text,
                voice=voice,
                output_path=UPLOADS_DIR / f"tts_seg_{uuid.uuid4().hex[:8]}.mp3",
            )
            if clip:
                clip_paths.append(clip)

        if not clip_paths:
            return None
        if len(clip_paths) == 1:
            out = clip_paths[0]
            if target_duration_sec:
                padded = UPLOADS_DIR / f"tts_pad_{uuid.uuid4().hex[:10]}.mp3"
                if _pad_audio_to_duration(out, target_duration_sec, padded):
                    return padded
            return out

        list_file = UPLOADS_DIR / f"tts_concat_{uuid.uuid4().hex[:8]}.txt"
        lines = [f"file '{p.resolve().as_posix()}'" for p in clip_paths]
        list_file.write_text("\n".join(lines), encoding="utf-8")
        merged = UPLOADS_DIR / f"tts_merged_{uuid.uuid4().hex[:10]}.mp3"
        cmd = [
            ffmpeg,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-c:a",
            "libmp3lame",
            "-b:a",
            "192k",
            str(merged),
        ]
        proc = subprocess.run(cmd, capture_output=True, timeout=300)
        if proc.returncode != 0 or not merged.is_file():
            return await synthesize_english_mp3(script_en, voice=voice)
        if target_duration_sec:
            padded = UPLOADS_DIR / f"tts_pad_{uuid.uuid4().hex[:10]}.mp3"
            if _pad_audio_to_duration(merged, target_duration_sec, padded):
                return padded
        return merged
    finally:
        if list_file and list_file.is_file():
            try:
                list_file.unlink(missing_ok=True)
            except OSError:
                pass
        for p in clip_paths:
            try:
                if p.is_file():
                    p.unlink(missing_ok=True)
            except OSError:
                pass


def mux_video_with_audio(video: Path, audio: Path, output: Path) -> bool:
    """替换音轨为英文配音（保留原画面全长，不因短配音裁切视频）。"""
    ffmpeg = resolve_executable("ffmpeg")
    if not ffmpeg or not video.is_file() or not audio.is_file():
        return False

    video_dur = probe_media_duration_sec(video)
    audio_to_mux = audio
    padded_tmp: Path | None = None
    if video_dur and video_dur > 0:
        audio_dur = probe_media_duration_sec(audio) or 0.0
        if audio_dur < video_dur - 0.5:
            padded_tmp = UPLOADS_DIR / f"tts_mux_pad_{uuid.uuid4().hex[:10]}.mp3"
            if _pad_audio_to_duration(audio, video_dur, padded_tmp):
                audio_to_mux = padded_tmp
            else:
                logger.warning(
                    "mux_video_with_audio: audio %.1fs << video %.1fs, pad failed",
                    audio_dur,
                    video_dur,
                )

    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(video),
        "-i",
        str(audio_to_mux),
        "-map",
        "0:v:0",
        "-map",
        "-0:a",
        "-map",
        "1:a:0",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
    ]
    if video_dur and video_dur > 0:
        cmd.extend(["-t", f"{video_dur:.3f}"])
    cmd.append(str(output))
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=max(300, int((video_dur or 120)) + 60))
        if proc.returncode != 0:
            stderr = (proc.stderr or b"").decode("utf-8", errors="replace")[-500:]
            logger.warning("mux_video_with_audio failed rc=%s: %s", proc.returncode, stderr)
            return False
        return output.is_file() and output.stat().st_size > 0
    except subprocess.TimeoutExpired as exc:
        logger.warning("mux_video_with_audio timeout: %s", exc)
        return False
    finally:
        if padded_tmp and padded_tmp.is_file():
            try:
                padded_tmp.unlink(missing_ok=True)
            except OSError:
                pass


def tts_status() -> dict[str, Any]:
    """实现 tts状态 的功能。
    
    :return: 返回 dict[str, Any] 结果
    """
    try:
        import edge_tts  # noqa: F401
        available = True
    except ImportError:
        available = False
    return {
        "edge_tts_available": available,
        "default_voice": DEFAULT_VOICE,
        "default_voice_male": DEFAULT_VOICE_MALE,
        "default_voice_female": DEFAULT_VOICE_FEMALE,
        "ffmpeg_available": is_executable_available("ffmpeg"),
    }
