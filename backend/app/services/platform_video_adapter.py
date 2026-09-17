# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""视频平台格式自适应 —— §2 缺口补齐。

各平台对视频时长/体积/画幅有硬性边界（TikTok 600s、IG Reels 90s、
YouTube Shorts 60s …）。上传前按目标平台规格自动裁剪/转码/加黑边，
避免发布时被平台拒收或降级。

设计原则（对齐项目 no_fake_delivery 约定）：
- 纯规则判定 + ffmpeg/ffprobe 落地，无 ffmpeg 时降级返回 ffmpeg_missing，禁止假成功。
- 判定逻辑（_should_reencode / _plan_adaptation）是纯函数，可无 ffmpeg 直接单测。
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


# ── 平台规格常量（frozen dataclass） ─────────────────────────────
@dataclass(frozen=True)
class VideoSpec:
    platform: str
    max_duration_sec: int
    max_size_mb: int
    preferred_ratio: str  # "9:16" 竖屏 / "16:9" 横屏 / "1:1" 方屏
    codec: str = "h264"
    max_width: int = 1080


PLATFORM_VIDEO_SPECS: dict[str, VideoSpec] = {
    "tiktok": VideoSpec("tiktok", 600, 288, "9:16"),
    "douyin": VideoSpec("douyin", 580, 512, "9:16"),
    "instagram_reels": VideoSpec("instagram_reels", 90, 4096, "9:16"),
    "instagram": VideoSpec("instagram", 90, 4096, "9:16"),
    "youtube_shorts": VideoSpec("youtube_shorts", 60, 10240, "9:16"),
    "youtube": VideoSpec("youtube", 2592000, 262144, "16:9"),
    "facebook": VideoSpec("facebook", 43200, 4096, "16:9"),
    "kuaishou": VideoSpec("kuaishou", 1800, 1024, "9:16"),
}

_RATIO_TO_ASPECT = {
    "9:16": "9/16",
    "16:9": "16/9",
    "1:1": "1/1",
    "4:3": "4/3",
}


@dataclass
class AdaptResult:
    adapted: bool
    output_path: Optional[Path]
    changes: list = field(default_factory=list)
    ffmpeg_ok: bool = True
    reason: str = ""
    target_platform: str = ""
    source: dict = field(default_factory=dict)


def _which(binary: str) -> Optional[str]:
    return shutil.which(binary)


def _probe(path: Path) -> Optional[dict]:
    """ffprobe 读取时长/宽高/文件大小。缺 ffprobe 或失败返回 None。"""
    ffprobe = _which("ffprobe")
    if not ffprobe or not path.is_file():
        return None
    cmd = [
        ffprobe, "-v", "error",
        "-show_entries", "format=duration:stream=width,height",
        "-of", "json", str(path),
    ]
    try:
        out = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=60)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return None
    import json
    try:
        data = json.loads(out.stdout or "{}")
    except json.JSONDecodeError:
        return None
    duration = float((data.get("format") or {}).get("duration") or 0.0)
    width = height = 0
    for s in data.get("streams") or []:
        if s.get("codec_type") == "video" or (s.get("width") and s.get("height")):
            width = int(s.get("width") or 0)
            height = int(s.get("height") or 0)
            break
    try:
        size_mb = path.stat().st_size / (1024 * 1024)
    except OSError:
        size_mb = 0.0
    return {"duration_sec": round(duration, 3), "width": width, "height": height, "size_mb": round(size_mb, 2)}


def _is_portrait(spec: VideoSpec, src: dict) -> bool:
    """源是否已符合竖屏目标（9:16）或比例匹配。"""
    if spec.preferred_ratio != "9:16":
        return True
    w, h = src.get("width", 0), src.get("height", 0)
    if not w or not h:
        return True
    return h >= w  # 竖屏 = 高 >= 宽


def _plan_adaptation(spec: VideoSpec, src: dict) -> list[str]:
    """纯函数：判定需要做哪些改动，返回改动描述列表（可单测，不碰 ffmpeg）。"""
    plans: list[str] = []
    max_dur = spec.max_duration_sec
    max_size = spec.max_size_mb
    duration = float(src.get("duration_sec") or 0.0)
    size_mb = float(src.get("size_mb") or 0.0)

    if duration > 0 and max_dur > 0 and duration > max_dur:
        plans.append(f"trim_duration_to_{max_dur}s")
    if size_mb > 0 and max_size > 0 and size_mb > max_size:
        plans.append("reencode_compress")
    if spec.preferred_ratio == "9:16" and not _is_portrait(spec, src):
        plans.append("pad_to_9x16")
    return plans


def _build_ffmpeg_cmd(spec: VideoSpec, src: dict, source: Path, out: Path) -> list[str]:
    """按改动计划构造 ffmpeg 命令（复用 media_video_edit_service 的编码约定）。"""
    plans = _plan_adaptation(spec, src)
    max_dur = spec.max_duration_sec
    need_trim = f"trim_duration_to_{max_dur}s" in plans
    need_compress = "reencode_compress" in plans
    need_pad = "pad_to_9x16" in plans

    # 竖屏黑边（优先级最高，直接返回）
    if need_pad:
        aspect = _RATIO_TO_ASPECT.get(spec.preferred_ratio, "9/16")
        vw = spec.max_width
        vh = int(round(vw * 16 / 9)) if aspect == "9/16" else vw
        pad = (
            f"scale={vw}:{vh}:force_original_aspect_ratio=decrease,"
            f"pad={vw}:{vh}:(ow-iw)/2:(oh-ih)/2:color=black"
        )
        cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", "0", "-i", str(source)]
        if need_trim:
            cmd += ["-t", str(max_dur)]
        cmd += ["-vf", pad, "-c:v", spec.codec, "-c:a", "aac", "-movflags", "+faststart", str(out)]
        return cmd

    # 压缩重编码（体积超限）
    if need_compress:
        max_size = spec.max_size_mb
        target_bitrate = int((max_size * 800) / max(1.0, float(src.get("duration_sec") or max_dur)))
        cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", "0", "-i", str(source)]
        if need_trim:
            cmd += ["-t", str(max_dur)]
        cmd += [
            "-vf", f"scale=-2:{spec.max_width}", "-c:v", spec.codec,
            "-b:v", f"{target_bitrate}k", "-maxrate", f"{int(target_bitrate * 1.2)}k",
            "-bufsize", f"{target_bitrate * 2}k", "-c:a", "aac", "-movflags", "+faststart", str(out),
        ]
        return cmd

    # 仅裁剪（未超体积/未超画幅）
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", "0", "-i", str(source)]
    if need_trim:
        cmd += ["-t", str(max_dur)]
    cmd += ["-c:v", spec.codec, "-c:a", "aac", "-movflags", "+faststart", str(out)]
    return cmd


def auto_adapt(
    video_path: Path,
    platform: str,
    output_dir: Optional[Path] = None,
) -> AdaptResult:
    """按目标平台规格自适应视频（裁剪/转码/加黑边）。

    返回 AdaptResult；无 ffmpeg 或探测失败时 ffmpeg_ok=False + adapted=False，
    绝不谎报成功。
    """
    spec = PLATFORM_VIDEO_SPECS.get(platform)
    if spec is None:
        return AdaptResult(adapted=False, output_path=None,
                           reason=f"unsupported_platform:{platform}", target_platform=platform)

    ffmpeg = _which("ffmpeg")
    src = _probe(video_path)
    if src is None:
        return AdaptResult(
            adapted=False, output_path=None, ffmpeg_ok=False,
            reason="ffprobe_missing_or_failed", target_platform=platform,
        )

    plans = _plan_adaptation(spec, src)
    if not plans:
        return AdaptResult(adapted=False, output_path=video_path, changes=[],
                           ffmpeg_ok=True, reason="no_change_needed",
                           target_platform=platform, source=src)

    if not ffmpeg:
        return AdaptResult(adapted=False, output_path=None, ffmpeg_ok=False,
                           changes=plans, reason="ffmpeg_missing",
                           target_platform=platform, source=src)

    out_dir = Path(output_dir or video_path.parent)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{platform}_{uuid.uuid4().hex[:8]}{video_path.suffix or '.mp4'}"
    cmd = _build_ffmpeg_cmd(spec, src, video_path, out)
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=600)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
        detail = (exc.stderr or b"").decode("utf-8", errors="ignore")[:300] if exc.stderr else str(exc)
        return AdaptResult(adapted=False, output_path=None, ffmpeg_ok=False,
                           changes=plans, reason=f"ffmpeg_failed:{detail}",
                           target_platform=platform, source=src)
    if not out.is_file():
        return AdaptResult(adapted=False, output_path=None, ffmpeg_ok=False,
                           changes=plans, reason="output_missing",
                           target_platform=platform, source=src)
    return AdaptResult(adapted=True, output_path=out, changes=plans, ffmpeg_ok=True,
                       reason="ok", target_platform=platform, source=src)


def adapt_in_place(
    video_path: Path,
    platform: str,
    tmp_root: Optional[Path] = None,
) -> AdaptResult:
    """裁剪后把结果临时文件写回同一目录（供 orchestrator 临时视频流复用），用完由调用方清理。"""
    out_dir = Path(tmp_root or tempfile.mkdtemp(prefix="vdadapt_"))
    return auto_adapt(video_path, platform, output_dir=out_dir)
