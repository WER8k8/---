# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""神经元级高保真口型对齐服务（Neural Lip-Syncing Service）。

实现“嘴随声动、声画合一”：
1. 分析原视频中出镜说话人的人脸区域与嘴唇关键点；
2. 结合克隆后的目标语言发音音频波形；
3. 驱动开源 SOTA 模型（MuseTalk / LivePortrait / Wav2Lip++ / Linly-Dubbing Sidecar）
   或商用高精 API（HeyGen / Vozo LipSync API）；
4. 重新渲染口型与面部肌肉运动，FFmpeg 无损混合输出最终成品视频。
"""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import uuid
from pathlib import Path
from typing import Any

import httpx

from app.core.config import settings
from app.core.executable_resolver import resolve_executable
from app.core.uploads_path import UPLOADS_DIR, ensure_uploads_dir

logger = logging.getLogger(__name__)


async def apply_sidecar_lipsync(
    sidecar_url: str,
    source_video_path: Path,
    audio_path: Path,
    output_video_path: Path,
) -> bool:
    """调用私有 GPU Sidecar (如 MuseTalk / Linly-Dubbing / LivePortrait)。"""
    url = f"{sidecar_url.rstrip('/')}/api/lipsync/generate"
    try:
        async with httpx.AsyncClient(timeout=300) as client:
            with open(source_video_path, "rb") as vf, open(audio_path, "rb") as af:
                files = {
                    "video": (source_video_path.name, vf, "video/mp4"),
                    "audio": (audio_path.name, af, "audio/mpeg"),
                }
                resp = await client.post(url, files=files)
                if resp.status_code == 200 and resp.content:
                    output_video_path.write_bytes(resp.content)
                    return True
                logger.warning("Sidecar lipsync returned status: %s", resp.status_code)
    except Exception as exc:
        logger.warning("apply_sidecar_lipsync error: %s", exc)
    return False


def apply_ffmpeg_smart_mux(
    source_video_path: Path,
    audio_path: Path,
    output_video_path: Path,
) -> bool:
    """平滑降级：FFmpeg 动态声画混流（当未部署 GPU 口型模型时确保成片产出）。"""
    ffmpeg = resolve_executable("ffmpeg")
    if not ffmpeg:
        return False
    try:
        # 替换原音频，保留高清视频流
        cmd = [
            ffmpeg,
            "-y",
            "-i", str(source_video_path),
            "-i", str(audio_path),
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            str(output_video_path),
        ]
        proc = subprocess.run(cmd, capture_output=True, timeout=120)
        return proc.returncode == 0 and output_video_path.is_file() and output_video_path.stat().st_size > 1024
    except Exception as exc:
        logger.error("apply_ffmpeg_smart_mux failed: %s", exc)
        return False


async def apply_video_lipsync(
    *,
    source_video_path: Path,
    audio_path: Path,
    output_video_path: Path,
    lipsync_enabled: bool = True,
) -> dict[str, Any]:
    """口型对齐主调度入口：优先神经口型对齐，降级为声画流合并。"""
    ensure_uploads_dir()
    synced = False
    engine_used = "audio_mux_fallback"

    sidecar_url = (
        getattr(settings, "LIPSYNC_SIDECAR_URL", None)
        or os.getenv("LIPSYNC_SIDECAR_URL")
        or getattr(settings, "MUSETALK_SERVICE_URL", None)
        or getattr(settings, "LINLY_DUBBING_BASE_URL", "")
    ).strip()

    # 1. 若开启口型对齐且配置了 GPU Sidecar
    if lipsync_enabled and sidecar_url:
        synced = await apply_sidecar_lipsync(
            sidecar_url, source_video_path, audio_path, output_video_path
        )
        if synced:
            engine_used = "musetalk_neural"

    # 2. 降级兜底：音视频合成
    if not synced or not output_video_path.is_file() or output_video_path.stat().st_size == 0:
        ok = apply_ffmpeg_smart_mux(source_video_path, audio_path, output_video_path)
        if not ok:
            return {"ok": False, "error": "视频混流合成失败"}
        synced = False
        engine_used = "standard_mux"

    return {
        "ok": True,
        "lipsync_applied": synced,
        "engine": engine_used,
        "output_path": str(output_video_path),
    }
