"""视频剪辑与调试（ffmpeg + 脚本重渲）。"""

from __future__ import annotations

import json
import logging
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.models.media_factory import MediaRenderTask
from app.services.cosmos_infer_service import script_to_video_prompt
from app.services.media_retention_service import apply_render_complete_metadata

logger = logging.getLogger(__name__)

SHOT_LINE = re.compile(
    r"^\s*(?:镜头|镜|Scene|scene)\s*(\d+)\s*[|｜:：\-—]\s*(.+?)(?:\s*[|｜:：\-—]\s*(.+))?\s*$",
    re.IGNORECASE,
)


def _utcnow() -> datetime:
    """_utcnow。
    :return: 返回处理结果。
    """
    return datetime.now(timezone.utc)


def probe_video_duration(path: Path) -> float | None:
    """probe_video_duration。

    参数说明：
    :param path: 参数 path
    :return: 返回处理结果。
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


def parse_script_shots(script: str) -> list[dict[str, Any]]:
    """将分镜脚本解析为可编辑镜头列表。"""
    shots: list[dict[str, Any]] = []
    for idx, line in enumerate((script or "").splitlines(), start=1):
        text = line.strip()
        if not text:
            continue
        match = SHOT_LINE.match(text)
        if match:
            shots.append(
                {
                    "index": int(match.group(1)),
                    "visual": match.group(2).strip(),
                    "narration": (match.group(3) or "").strip(),
                    "raw": text,
                }
            )
        else:
            shots.append({"index": idx, "visual": text, "narration": "", "raw": text})
    return shots


def shots_to_script(shots: list[dict[str, Any]]) -> str:
    """shots_to_script。

    参数说明：
    :param shots: 参数 shots
    :return: 返回处理结果。
    """
    lines: list[str] = []
    for i, shot in enumerate(shots, start=1):
        idx = shot.get("index") or i
        visual = str(shot.get("visual") or "").strip()
        narration = str(shot.get("narration") or "").strip()
        if narration:
            lines.append(f"镜头{idx} | {visual} | {narration}")
        elif visual:
            lines.append(f"镜头{idx} | {visual}")
    return "\n".join(lines)


def load_edit_config(task: MediaRenderTask) -> dict[str, Any]:
    """load_edit_config。

    参数说明：
    :param task: 参数 task
    :return: 返回处理结果。
    """
    raw = task.edit_config or ""
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def save_edit_config(db: Session, task: MediaRenderTask, config: dict[str, Any]) -> None:
    """save_edit_config。

    参数说明：
    :param db: 参数 db
    :param task: 参数 task
    :param config: 参数 config
    :return: 返回处理结果。
    """
    task.edit_config = json.dumps(config, ensure_ascii=False)
    task.updated_at = _utcnow()
    db.add(task)
    db.commit()
    db.refresh(task)


def effective_preview_url(task: MediaRenderTask) -> str | None:
    """effective_preview_url。

    参数说明：
    :param task: 参数 task
    :return: 返回处理结果。
    """
    if task.file_purged:
        return None
    if task.edited_result_url:
        return task.edited_result_url
    from app.services.media_cloud_upload_service import playback_url_for_task
    cloud = playback_url_for_task(task)
    if cloud:
        return cloud
    return task.result_url


def effective_preview_path(task: MediaRenderTask) -> Path | None:
    """effective_preview_path。

    参数说明：
    :param task: 参数 task
    :return: 返回处理结果。
    """
    path_str = task.edited_result_path or task.result_path
    if not path_str:
        return None
    path = Path(path_str)
    return path if path.is_file() else None


def build_edit_payload(db: Session, task: MediaRenderTask) -> dict[str, Any]:
    """build_edit_payload。

    参数说明：
    :param db: 参数 db
    :param task: 参数 task
    :return: 返回处理结果。
    """
    cfg = load_edit_config(task)
    source_path = Path(task.result_path) if task.result_path else None
    duration = cfg.get("source_duration_sec")
    if duration is None and source_path and source_path.is_file():
        duration = probe_video_duration(source_path)
        if duration is not None:
            cfg["source_duration_sec"] = round(duration, 3)
            save_edit_config(db, task, cfg)

    clip_start = float(cfg.get("clip_start_sec") or 0)
    clip_end = float(cfg.get("clip_end_sec") or duration or 0)
    if duration and clip_end <= 0:
        clip_end = duration

    return {
        "preview_url": effective_preview_url(task),
        "source_url": None if task.file_purged else task.result_url,
        "edited_url": None if task.file_purged else task.edited_result_url,
        "source_duration_sec": duration,
        "clip_start_sec": clip_start,
        "clip_end_sec": clip_end,
        "has_clip": bool(task.edited_result_path),
        "script": task.script,
        "prompt_text": task.prompt_text,
        "shots": parse_script_shots(task.script or ""),
        "mock_render": cfg.get("mock_render"),
    }


def apply_video_clip(
    db: Session,
    task: MediaRenderTask,
    *,
    start_sec: float,
    end_sec: float,
) -> MediaRenderTask:
    """apply_video_clip。

    参数说明：
    :param db: 参数 db
    :param task: 参数 task
    :param start_sec: 参数 start_sec
    :param end_sec: 参数 end_sec
    :return: 返回处理结果。
    """
    if task.file_purged or not task.result_path:
        raise ValueError("原片不存在或已过期，无法剪辑")
    if task.status not in {"done", "expired"}:
        raise ValueError("请等待渲染完成后再剪辑")

    source = Path(task.result_path)
    if not source.is_file():
        raise ValueError("原片文件缺失")

    duration = probe_video_duration(source)
    if duration is None:
        raise ValueError("无法读取视频时长，请确认已安装 ffmpeg/ffprobe")

    start = max(0.0, float(start_sec))
    end = min(float(end_sec), duration)
    if end - start < 0.3:
        raise ValueError("剪辑区间至少 0.3 秒")

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise ValueError("服务器未安装 ffmpeg，无法剪辑")

    output = source.parent / f"{task.id}_clip.mp4"
    cmd = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        f"{start:.3f}",
        "-to",
        f"{end:.3f}",
        "-i",
        str(source),
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-movflags",
        "+faststart",
        str(output),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or b"").decode("utf-8", errors="ignore")[:300]
        raise ValueError(f"剪辑失败: {detail or exc}") from exc

    if task.edited_result_path and task.edited_result_path != str(output):
        old = Path(task.edited_result_path)
        if old.is_file() and old != source:
            try:
                old.unlink()
            except OSError:
                pass

    task.edited_result_path = str(output)
    task.edited_result_url = f"/uploads/media_factory/{output.name}"
    apply_render_complete_metadata(db, task, output)
    cfg = load_edit_config(task)
    cfg.update(
        {
            "clip_start_sec": round(start, 3),
            "clip_end_sec": round(end, 3),
            "source_duration_sec": round(duration, 3),
            "clip_applied_at": _utcnow().isoformat(),
        }
    )
    save_edit_config(db, task, cfg)
    return task


def update_task_script(
    db: Session,
    task: MediaRenderTask,
    *,
    script: str,
    shots: list[dict[str, Any]] | None = None,
) -> MediaRenderTask:
    """update_task_script。

    参数说明：
    :param db: 参数 db
    :param task: 参数 task
    :param script: 参数 script
    :param shots: 参数 shots
    :return: 返回处理结果。
    """
    new_script = (script or "").strip()
    if shots:
        new_script = shots_to_script(shots).strip()
    if not new_script:
        raise ValueError("脚本不能为空")

    task.script = new_script
    task.prompt_text = script_to_video_prompt(new_script)
    task.updated_at = _utcnow()
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def prepare_task_rerender(db: Session, task: MediaRenderTask) -> MediaRenderTask:
    """重置为 queued，清除旧成片与剪辑，供重新渲染。"""
    for path_str in (task.result_path, task.edited_result_path):
        if not path_str:
            continue
        path = Path(path_str)
        if path.is_file():
            try:
                path.unlink()
            except OSError as exc:
                logger.warning("Failed to remove %s: %s", path, exc)

    task.status = "queued"
    task.progress = 0
    task.error_message = None
    task.result_url = None
    task.result_path = None
    task.edited_result_url = None
    task.edited_result_path = None
    task.file_purged = 0
    task.file_size_bytes = 0
    task.expires_at = None
    task.purge_at = None
    task.handoff_type = None
    task.handoff_at = None
    task.handoff_external_url = None
    task.started_at = None
    task.finished_at = None
    task.edit_config = None
    task.updated_at = _utcnow()
    db.add(task)
    db.commit()
    db.refresh(task)
    return task
