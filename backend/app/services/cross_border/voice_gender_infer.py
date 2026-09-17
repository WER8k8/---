# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""从原片音轨粗估解说者性别（基频启发式），用于英文 TTS 音色匹配。"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Literal

import numpy as np

from app.core.executable_resolver import resolve_executable
from app.services.cross_border.audio_chunk_service import probe_media_duration_sec

logger = logging.getLogger(__name__)

VoiceGender = Literal["male", "female", "unknown"]

_SAMPLE_RATE = 16000
_MIN_PITCH_HZ = 75.0
_MAX_PITCH_HZ = 400.0
_MALE_CEILING_HZ = 165.0
_FEMALE_FLOOR_HZ = 175.0


def _extract_pcm_segment(media: Path, start_sec: float, duration_sec: float) -> np.ndarray | None:
    """实现 提取pcmsegment 的功能。
    
    :param media: 参数 media（类型: Path）
    :param start_sec: 参数 start_sec（类型: float）
    :param duration_sec: 参数 duration_sec（类型: float）
    :return: 返回 np.ndarray | None 结果
    """
    ffmpeg = resolve_executable("ffmpeg")
    if not ffmpeg or not media.is_file() or duration_sec <= 0:
        return None
    cmd = [
        ffmpeg,
        "-y",
        "-ss",
        f"{max(0.0, start_sec):.3f}",
        "-i",
        str(media),
        "-t",
        f"{duration_sec:.3f}",
        "-vn",
        "-ac",
        "1",
        "-ar",
        str(_SAMPLE_RATE),
        "-f",
        "s16le",
        "pipe:1",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=max(30, int(duration_sec) + 20))
        if proc.returncode != 0 or not proc.stdout:
            return None
        samples = np.frombuffer(proc.stdout, dtype=np.int16).astype(np.float32) / 32768.0
        return samples if samples.size else None
    except (subprocess.TimeoutExpired, ValueError, OSError) as exc:
        logger.debug("extract pcm for gender infer failed: %s", exc)
        return None


def _estimate_pitch_hz(frame: np.ndarray, sample_rate: int) -> float | None:
    """实现 估算pitchhz 的功能。
    
    :param frame: 参数 frame（类型: np.ndarray）
    :param sample_rate: 参数 sample_rate（类型: int）
    :return: 返回 float | None 结果
    """
    if frame.size < sample_rate // 20:
        return None
    rms = float(np.sqrt(np.mean(frame**2)))
    if rms < 0.012:
        return None
    min_lag = max(1, int(sample_rate / _MAX_PITCH_HZ))
    max_lag = min(len(frame) - 1, int(sample_rate / _MIN_PITCH_HZ))
    if max_lag <= min_lag:
        return None
    corr = np.correlate(frame, frame, mode="full")
    corr = corr[len(corr) // 2 :]
    segment = corr[min_lag : max_lag + 1]
    if segment.size == 0:
        return None
    lag = min_lag + int(np.argmax(segment))
    if lag <= 0:
        return None
    pitch = sample_rate / lag
    if _MIN_PITCH_HZ <= pitch <= _MAX_PITCH_HZ:
        return float(pitch)
    return None


def infer_voice_gender_from_media(media: Path) -> tuple[VoiceGender, float | None]:
    """返回 (gender, median_pitch_hz)。检测失败时 gender=unknown。"""
    duration = probe_media_duration_sec(media) or 0.0
    if duration <= 0:
        return "unknown", None

    if duration > 45:
        windows = [
            (duration * 0.08, min(8.0, duration * 0.12)),
            (duration * 0.42, min(8.0, duration * 0.12)),
            (duration * 0.72, min(8.0, duration * 0.12)),
        ]
    else:
        windows = [(0.0, min(15.0, duration))]

    pitches: list[float] = []
    hop = _SAMPLE_RATE // 2
    for start, length in windows:
        pcm = _extract_pcm_segment(media, start, length)
        if pcm is None:
            continue
        for i in range(0, len(pcm) - hop, hop):
            pitch = _estimate_pitch_hz(pcm[i : i + hop], _SAMPLE_RATE)
            if pitch:
                pitches.append(pitch)

    if not pitches:
        return "unknown", None

    median = float(np.median(pitches))
    if median < _MALE_CEILING_HZ:
        return "male", median
    if median > _FEMALE_FLOOR_HZ:
        return "female", median
    return "unknown", median
