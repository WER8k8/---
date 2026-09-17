# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""长媒体听写分片：ffmpeg 切段、并行转写、扇入合并。"""

from __future__ import annotations

import logging
import shutil
import subprocess
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable

from app.core.uploads_path import UPLOADS_DIR, ensure_uploads_dir

logger = logging.getLogger(__name__)

# 超过此时长（秒）启用分片扇出
CHUNK_THRESHOLD_SEC = 360
CHUNK_DURATION_SEC = 300
MAX_CHUNK_WORKERS = 4

ProgressFn = Callable[[int, str], None]


def probe_media_duration_sec(path: Path) -> float | None:
    """实现 探测mediadurationsec 的功能。
    
    :param path: 参数 path（类型: Path）
    :return: 返回 float | None 结果
    """
    ffprobe = shutil.which("ffprobe")
    if not ffprobe or not path.is_file():
        return None
    cmd = [
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    try:
        out = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=30)
        return float(out.stdout.strip())
    except (subprocess.CalledProcessError, ValueError, subprocess.TimeoutExpired):
        return None


def split_wav_chunks(wav: Path, *, chunk_sec: int = CHUNK_DURATION_SEC) -> list[tuple[Path, float]]:
    """将 wav 切为若干段，返回 (分片路径, 时间偏移秒)。"""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg or not wav.is_file():
        return [(wav, 0.0)]

    duration = probe_media_duration_sec(wav)
    if duration is None or duration <= chunk_sec:
        return [(wav, 0.0)]

    ensure_uploads_dir()
    prefix = UPLOADS_DIR / f"asr_chunk_{uuid.uuid4().hex[:8]}"
    pattern = str(prefix) + "_%03d.wav"
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(wav),
        "-f",
        "segment",
        "-segment_time",
        str(chunk_sec),
        "-c",
        "copy",
        pattern,
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=max(180, int(duration) + 60))
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        logger.warning("split_wav_chunks failed, use whole file: %s", exc)
        return [(wav, 0.0)]

    chunks: list[tuple[Path, float]] = []
    idx = 0
    while True:
        part = Path(f"{prefix}_{idx:03d}.wav")
        if not part.is_file():
            break
        chunks.append((part, float(idx * chunk_sec)))
        idx += 1
    return chunks or [(wav, 0.0)]


def merge_chunk_transcripts(
    parts: list[dict[str, Any]],
    offsets: list[float],
) -> dict[str, Any]:
    """扇入：合并各分片听写结果，时间轴按 offset 平移。"""
    texts: list[str] = []
    segments: list[dict[str, Any]] = []
    backend = None
    for item, offset in zip(parts, offsets, strict=False):
        if not item or not item.get("text"):
            continue
        texts.append(str(item["text"]).strip())
        backend = backend or item.get("backend")
        for seg in item.get("segments") or []:
            if not isinstance(seg, dict):
                continue
            start = seg.get("start")
            end = seg.get("end")
            try:
                start_f = float(start) + offset if start is not None else offset
                end_f = float(end) + offset if end is not None else offset
            except (TypeError, ValueError):
                start_f, end_f = offset, offset
            segments.append(
                {
                    "start": start_f,
                    "end": end_f,
                    "text": str(seg.get("text") or "").strip(),
                }
            )
    text = "".join(texts).strip()
    return {
        "text": text,
        "segments": segments,
        "backend": backend,
        "chunk_count": len(parts),
    }


def transcribe_chunks_parallel(
    chunks: list[tuple[Path, float]],
    transcribe_fn: Callable[[Path], dict[str, Any] | None],
    *,
    on_progress: ProgressFn | None = None,
) -> tuple[list[dict[str, Any]], list[float]]:
    """扇出：并行听写各分片。"""
    if len(chunks) <= 1:
        path, offset = chunks[0]
        on_progress and on_progress(40, "听写中…")
        result = transcribe_fn(path) or {}
        return [result], [offset]

    results: list[dict[str, Any] | None] = [None] * len(chunks)
    offsets = [off for _, off in chunks]
    workers = min(MAX_CHUNK_WORKERS, len(chunks))
    done = 0
    def _one(idx: int, path: Path) -> tuple[int, dict[str, Any] | None]:
        """实现 one 的功能。
        
        :param idx: 参数 idx（类型: int）
        :param path: 参数 path（类型: Path）
        :return: 返回 tuple[int, dict[str, Any] | None] 结果
        """
        return idx, transcribe_fn(path)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(_one, i, path): i for i, (path, _) in enumerate(chunks)
        }
        for fut in as_completed(futures):
            idx, res = fut.result()
            results[idx] = res or {}
            done += 1
            if on_progress:
                pct = 25 + int(55 * done / len(chunks))
                on_progress(pct, f"听写分片 {done}/{len(chunks)}")

    return [r or {} for r in results], offsets


def cleanup_chunk_files(chunks: list[tuple[Path, float]], *, keep: Path | None = None) -> None:
    """实现 清理chunk文件 的功能。
    
    :param chunks: 参数 chunks（类型: list[tuple[Path, float]]）
    :param keep: 参数 keep（类型: Path | None）
    :return: 返回 None 结果
    """
    seen: set[str] = set()
    if keep:
        seen.add(str(keep.resolve()))
    for path, _ in chunks:
        key = str(path.resolve())
        if key in seen:
            continue
        seen.add(key)
        try:
            if path.is_file():
                path.unlink(missing_ok=True)
        except OSError:
            pass
