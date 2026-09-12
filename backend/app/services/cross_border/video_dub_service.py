"""中文产品片 → 听写 / 英文字幕 / 英文配音出海（W1 / LV-07~10）。"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from app.core.executable_resolver import resolve_executable
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.uploads_path import UPLOADS_DIR, ensure_uploads_dir
from app.models.tenant import Tenant
from app.models.user import User
from app.services.ai_invocation_service import invoke_llm
from app.services.cross_border.audio_asr_service import transcribe_zh_from_media
from app.services.cross_border.audio_chunk_service import probe_media_duration_sec
from app.services.cross_border.glossary_helper import build_glossary_prompt_block
from app.services.cross_border.tts_service import (
    mux_video_with_audio,
    resolve_dub_voice,
    synthesize_dub_mp3,
    tts_status,
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
    """实现 估算最大值令牌 的功能。
    
    :param transcript_zh: 参数 transcript_zh（类型: str）
    :return: 返回 int 结果
    """
    n = len((transcript_zh or "").strip())
    return min(8000, max(1800, n * 2))


def _manual_transcript_too_short_for_video(
    transcript_zh: str,
    video_dur_sec: float | None,
) -> bool:
    """实现 manualtranscripttooshortfor视频 的功能。
    
    :param transcript_zh: 参数 transcript_zh（类型: str）
    :param video_dur_sec: 参数 video_dur_sec（类型: float | None）
    :return: 返回 bool 结果
    """
    text = (transcript_zh or "").strip()
    if not text or not video_dur_sec or video_dur_sec <= _STALE_MANUAL_VIDEO_SEC:
        return False
    if len(text) < _STALE_MANUAL_MAX_CHARS:
        return True
    chars_per_sec = len(text) / video_dur_sec
    return chars_per_sec < 0.6


def _parse_json(text: str) -> dict[str, Any]:
    """实现 解析JSON 的功能。
    
    :param text: 参数 text（类型: str）
    :return: 返回 dict[str, Any] 结果
    """
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
    """实现 URLtolocalpath 的功能。
    
    :param url: 参数 url（类型: str | None）
    :return: 返回 Path | None 结果
    """
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


def _format_srt(segments: list[dict[str, Any]]) -> str:
    """实现 格式化srt 的功能。
    
    :param segments: 参数 segments（类型: list[dict[str, Any]]）
    :return: 返回 str 结果
    """
    lines: list[str] = []
    for i, seg in enumerate(segments, start=1):
        start = seg.get("start") or "00:00:00,000"
        end = seg.get("end") or "00:00:05,000"
        text = str(seg.get("text_en") or seg.get("text") or "").strip()
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
    """实现 transcribe视频任务 的功能。
    
    :param db: 参数 db（类型: Session）
    :param tenant: 参数 tenant（类型: Tenant）
    :param user: 参数 user（类型: User）
    :param media_task_id: 参数 media_task_id（类型: str）
    :param on_progress: 参数 on_progress（类型: Any | None）
    :return: 返回 dict[str, Any] 结果
    """
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
) -> dict[str, Any]:
    """实现 translatescript 的功能。
    
    :param db: 参数 db（类型: Session）
    :param tenant: 参数 tenant（类型: Tenant）
    :param transcript_zh: 参数 transcript_zh（类型: str）
    :param product_hint: 参数 product_hint（类型: str）
    :return: 返回 dict[str, Any] 结果
    """
    glossary = build_glossary_prompt_block(db)
    prompt = (
        "把下方中文视频解说词译成英文配音稿。受众是海外采购商。\n"
        "铁律：必须忠实翻译中文原文，禁止编造与原文无关的工厂介绍、产品宣传或 MOQ/FOB 套话。\n"
        "原文是口语就译成口语，是带货/转铺就保留同等信息量。\n"
        f"工厂产品（仅作术语参考）: {product_hint}\n"
        f"术语: {glossary}\n\n"
        f"中文原文:\n{transcript_zh.strip()}\n\n"
        "输出 JSON:\n"
        '{"script_en":"完整英文解说（忠实对应中文）","segments":['
        '{"start":"00:00:00,000","end":"00:00:04,000","text_en":"..."}],'
        '"notes_zh":"给老板看的中文说明"}'
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
    if not parsed.get("script_en"):
        parsed["script_en"] = str(result.get("content") or "")
    if not parsed.get("segments"):
        parsed["segments"] = [
            {"start": "00:00:00,000", "end": "00:00:08,000", "text_en": parsed["script_en"][:200]}
        ]
    parsed["model"] = result.get("model")
    return parsed


def _burn_subtitles(source: Path, srt_path: Path, output: Path) -> bool:
    """实现 burnsubtitles 的功能。
    
    :param source: 参数 source（类型: Path）
    :param srt_path: 参数 srt_path（类型: Path）
    :param output: 参数 output（类型: Path）
    :return: 返回 bool 结果
    """
    ffmpeg = resolve_executable("ffmpeg")
    if not ffmpeg or not source.is_file() or not srt_path.is_file():
        return False
    srt_esc = str(srt_path).replace("\\", "/").replace(":", "\\:")
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(source),
        "-vf",
        f"subtitles='{srt_esc}'",
        "-c:a",
        "copy",
        str(output),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=300)
        return output.is_file()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


def _run_video_dub_job_extracted(task):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param task: 输入参数
    :return: 返回 video_dur_sec, temp_path, source_path, warnings, product_hint 等计算结果
    """
    profile = get_tenant_product_profile(db, str(tenant.id))
    product_hint = profile.get("primary_product") or task.title or tenant.name
    source_path, temp_path = _resolve_media_source_path(task.result_url)
    video_dur_sec = probe_media_duration_sec(source_path) if source_path else None
    warnings: list[str] = []
    return video_dur_sec, temp_path, source_path, warnings, product_hint

def _run_video_dub_job_extracted1():
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param self: 输入参数
    :return: 返回 task 等计算结果
    """
    """中→英脚本 + SRT；可选烧录字幕或 edge-tts 英文配音。"""
    task = get_render_task_for_user(db, media_task_id, user)
    return task

def _run_video_dub_job_extracted2(_run_video_dub_job_extracted1):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_video_dub_job_extracted1: 输入参数
    :return: 返回 task 等计算结果
    """
    task = _run_video_dub_job_extracted1()
    return task

def _run_video_dub_job_extracted3(_run_video_dub_job_extracted1, _run_video_dub_job_extracted2):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_video_dub_job_extracted1, _run_video_dub_job_extracted2: 输入参数
    :return: 返回 task 等计算结果
    """
    task = _run_video_dub_job_extracted2(_run_video_dub_job_extracted1)
    return task

def _run_video_dub_job_extracted4(_run_video_dub_job_extracted1, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_video_dub_job_extracted1, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3: 输入参数
    :return: 返回 task 等计算结果
    """
    task = _run_video_dub_job_extracted3(_run_video_dub_job_extracted1, _run_video_dub_job_extracted2)
    return task

def _run_video_dub_job_extracted5(_run_video_dub_job_extracted1, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_video_dub_job_extracted1, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4: 输入参数
    :return: 返回 task 等计算结果
    """
    task = _run_video_dub_job_extracted4(_run_video_dub_job_extracted1, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3)
    return task

def _run_video_dub_job_extracted6(_run_video_dub_job_extracted1, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_video_dub_job_extracted1, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5: 输入参数
    :return: 返回 task 等计算结果
    """
    task = _run_video_dub_job_extracted5(_run_video_dub_job_extracted1, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4)
    return task

def _run_video_dub_job_extracted7(_run_video_dub_job_extracted1, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5, _run_video_dub_job_extracted6):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_video_dub_job_extracted1, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5, _run_video_dub_job_extracted6: 输入参数
    :return: 返回 task 等计算结果
    """
    task = _run_video_dub_job_extracted6(_run_video_dub_job_extracted1, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5)
    return task

def _run_video_dub_job_extracted8(_run_video_dub_job_extracted1, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5, _run_video_dub_job_extracted6, _run_video_dub_job_extracted7):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_video_dub_job_extracted1, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5, _run_video_dub_job_extracted6, _run_video_dub_job_extracted7: 输入参数
    :return: 返回 task 等计算结果
    """
    task = _run_video_dub_job_extracted7(_run_video_dub_job_extracted1, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5, _run_video_dub_job_extracted6)
    return task

def _run_video_dub_job_extracted9(_run_video_dub_job_extracted1, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5, _run_video_dub_job_extracted6, _run_video_dub_job_extracted7, _run_video_dub_job_extracted8):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_video_dub_job_extracted1, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5, _run_video_dub_job_extracted6, _run_video_dub_job_extracted7, _run_video_dub_job_extracted8: 输入参数
    :return: 返回 task 等计算结果
    """
    task = _run_video_dub_job_extracted8(_run_video_dub_job_extracted1, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5, _run_video_dub_job_extracted6, _run_video_dub_job_extracted7)
    return task

def _run_video_dub_job_extracted10(_run_video_dub_job_extracted1, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5, _run_video_dub_job_extracted6, _run_video_dub_job_extracted7, _run_video_dub_job_extracted8, _run_video_dub_job_extracted9):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_video_dub_job_extracted1, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5, _run_video_dub_job_extracted6, _run_video_dub_job_extracted7, _run_video_dub_job_extracted8, _run_video_dub_job_extracted9: 输入参数
    :return: 返回 task 等计算结果
    """
    task = _run_video_dub_job_extracted9(_run_video_dub_job_extracted1, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5, _run_video_dub_job_extracted6, _run_video_dub_job_extracted7, _run_video_dub_job_extracted8)
    return task

def _run_video_dub_job_extracted11(_run_video_dub_job_extracted1, _run_video_dub_job_extracted10, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5, _run_video_dub_job_extracted6, _run_video_dub_job_extracted7, _run_video_dub_job_extracted8, _run_video_dub_job_extracted9):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_video_dub_job_extracted1, _run_video_dub_job_extracted10, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5, _run_video_dub_job_extracted6, _run_video_dub_job_extracted7, _run_video_dub_job_extracted8, _run_video_dub_job_extracted9: 输入参数
    :return: 返回 task 等计算结果
    """
    task = _run_video_dub_job_extracted10(_run_video_dub_job_extracted1, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5, _run_video_dub_job_extracted6, _run_video_dub_job_extracted7, _run_video_dub_job_extracted8, _run_video_dub_job_extracted9)
    return task

def _run_video_dub_job_extracted12(_run_video_dub_job_extracted1, _run_video_dub_job_extracted10, _run_video_dub_job_extracted11, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5, _run_video_dub_job_extracted6, _run_video_dub_job_extracted7, _run_video_dub_job_extracted8, _run_video_dub_job_extracted9):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_video_dub_job_extracted1, _run_video_dub_job_extracted10, _run_video_dub_job_extracted11, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5, _run_video_dub_job_extracted6, _run_video_dub_job_extracted7, _run_video_dub_job_extracted8, _run_video_dub_job_extracted9: 输入参数
    :return: 返回 task 等计算结果
    """
    task = _run_video_dub_job_extracted11(_run_video_dub_job_extracted1, _run_video_dub_job_extracted10, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5, _run_video_dub_job_extracted6, _run_video_dub_job_extracted7, _run_video_dub_job_extracted8, _run_video_dub_job_extracted9)
    return task

def _run_video_dub_job_extracted13(_run_video_dub_job_extracted1, _run_video_dub_job_extracted10, _run_video_dub_job_extracted11, _run_video_dub_job_extracted12, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5, _run_video_dub_job_extracted6, _run_video_dub_job_extracted7, _run_video_dub_job_extracted8, _run_video_dub_job_extracted9):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_video_dub_job_extracted1, _run_video_dub_job_extracted10, _run_video_dub_job_extracted11, _run_video_dub_job_extracted12, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5, _run_video_dub_job_extracted6, _run_video_dub_job_extracted7, _run_video_dub_job_extracted8, _run_video_dub_job_extracted9: 输入参数
    :return: 返回 task 等计算结果
    """
    task = _run_video_dub_job_extracted12(_run_video_dub_job_extracted1, _run_video_dub_job_extracted10, _run_video_dub_job_extracted11, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5, _run_video_dub_job_extracted6, _run_video_dub_job_extracted7, _run_video_dub_job_extracted8, _run_video_dub_job_extracted9)
    return task

def _run_video_dub_job_extracted14(_run_video_dub_job_extracted1, _run_video_dub_job_extracted10, _run_video_dub_job_extracted11, _run_video_dub_job_extracted12, _run_video_dub_job_extracted13, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5, _run_video_dub_job_extracted6, _run_video_dub_job_extracted7, _run_video_dub_job_extracted8, _run_video_dub_job_extracted9):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_video_dub_job_extracted1, _run_video_dub_job_extracted10, _run_video_dub_job_extracted11, _run_video_dub_job_extracted12, _run_video_dub_job_extracted13, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5, _run_video_dub_job_extracted6, _run_video_dub_job_extracted7, _run_video_dub_job_extracted8, _run_video_dub_job_extracted9: 输入参数
    :return: 返回 task 等计算结果
    """
    task = _run_video_dub_job_extracted13(_run_video_dub_job_extracted1, _run_video_dub_job_extracted10, _run_video_dub_job_extracted11, _run_video_dub_job_extracted12, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5, _run_video_dub_job_extracted6, _run_video_dub_job_extracted7, _run_video_dub_job_extracted8, _run_video_dub_job_extracted9)
    return task

def _run_video_dub_job_extracted15(_run_video_dub_job_extracted1, _run_video_dub_job_extracted10, _run_video_dub_job_extracted11, _run_video_dub_job_extracted12, _run_video_dub_job_extracted13, _run_video_dub_job_extracted14, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5, _run_video_dub_job_extracted6, _run_video_dub_job_extracted7, _run_video_dub_job_extracted8, _run_video_dub_job_extracted9):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_video_dub_job_extracted1, _run_video_dub_job_extracted10, _run_video_dub_job_extracted11, _run_video_dub_job_extracted12, _run_video_dub_job_extracted13, _run_video_dub_job_extracted14, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5, _run_video_dub_job_extracted6, _run_video_dub_job_extracted7, _run_video_dub_job_extracted8, _run_video_dub_job_extracted9: 输入参数
    :return: 返回 task 等计算结果
    """
    task = _run_video_dub_job_extracted14(_run_video_dub_job_extracted1, _run_video_dub_job_extracted10, _run_video_dub_job_extracted11, _run_video_dub_job_extracted12, _run_video_dub_job_extracted13, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5, _run_video_dub_job_extracted6, _run_video_dub_job_extracted7, _run_video_dub_job_extracted8, _run_video_dub_job_extracted9)
    return task

def _run_video_dub_job_extracted16(_run_video_dub_job_extracted1, _run_video_dub_job_extracted10, _run_video_dub_job_extracted11, _run_video_dub_job_extracted12, _run_video_dub_job_extracted13, _run_video_dub_job_extracted14, _run_video_dub_job_extracted15, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5, _run_video_dub_job_extracted6, _run_video_dub_job_extracted7, _run_video_dub_job_extracted8, _run_video_dub_job_extracted9):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_video_dub_job_extracted1, _run_video_dub_job_extracted10, _run_video_dub_job_extracted11, _run_video_dub_job_extracted12, _run_video_dub_job_extracted13, _run_video_dub_job_extracted14, _run_video_dub_job_extracted15, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5, _run_video_dub_job_extracted6, _run_video_dub_job_extracted7, _run_video_dub_job_extracted8, _run_video_dub_job_extracted9: 输入参数
    :return: 返回 task 等计算结果
    """
    task = _run_video_dub_job_extracted15(_run_video_dub_job_extracted1, _run_video_dub_job_extracted10, _run_video_dub_job_extracted11, _run_video_dub_job_extracted12, _run_video_dub_job_extracted13, _run_video_dub_job_extracted14, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5, _run_video_dub_job_extracted6, _run_video_dub_job_extracted7, _run_video_dub_job_extracted8, _run_video_dub_job_extracted9)
    return task

def _run_video_dub_job_extracted17(_run_video_dub_job_extracted1, _run_video_dub_job_extracted10, _run_video_dub_job_extracted11, _run_video_dub_job_extracted12, _run_video_dub_job_extracted13, _run_video_dub_job_extracted14, _run_video_dub_job_extracted15, _run_video_dub_job_extracted16, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5, _run_video_dub_job_extracted6, _run_video_dub_job_extracted7, _run_video_dub_job_extracted8, _run_video_dub_job_extracted9):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_video_dub_job_extracted1, _run_video_dub_job_extracted10, _run_video_dub_job_extracted11, _run_video_dub_job_extracted12, _run_video_dub_job_extracted13, _run_video_dub_job_extracted14, _run_video_dub_job_extracted15, _run_video_dub_job_extracted16, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5, _run_video_dub_job_extracted6, _run_video_dub_job_extracted7, _run_video_dub_job_extracted8, _run_video_dub_job_extracted9: 输入参数
    :return: 返回 task 等计算结果
    """
    task = _run_video_dub_job_extracted16(_run_video_dub_job_extracted1, _run_video_dub_job_extracted10, _run_video_dub_job_extracted11, _run_video_dub_job_extracted12, _run_video_dub_job_extracted13, _run_video_dub_job_extracted14, _run_video_dub_job_extracted15, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5, _run_video_dub_job_extracted6, _run_video_dub_job_extracted7, _run_video_dub_job_extracted8, _run_video_dub_job_extracted9)
    return task

def _run_video_dub_job_extracted18(_run_video_dub_job_extracted1, _run_video_dub_job_extracted10, _run_video_dub_job_extracted11, _run_video_dub_job_extracted12, _run_video_dub_job_extracted13, _run_video_dub_job_extracted14, _run_video_dub_job_extracted15, _run_video_dub_job_extracted16, _run_video_dub_job_extracted17, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5, _run_video_dub_job_extracted6, _run_video_dub_job_extracted7, _run_video_dub_job_extracted8, _run_video_dub_job_extracted9):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_video_dub_job_extracted1, _run_video_dub_job_extracted10, _run_video_dub_job_extracted11, _run_video_dub_job_extracted12, _run_video_dub_job_extracted13, _run_video_dub_job_extracted14, _run_video_dub_job_extracted15, _run_video_dub_job_extracted16, _run_video_dub_job_extracted17, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5, _run_video_dub_job_extracted6, _run_video_dub_job_extracted7, _run_video_dub_job_extracted8, _run_video_dub_job_extracted9: 输入参数
    :return: 返回 task 等计算结果
    """
    task = _run_video_dub_job_extracted17(_run_video_dub_job_extracted1, _run_video_dub_job_extracted10, _run_video_dub_job_extracted11, _run_video_dub_job_extracted12, _run_video_dub_job_extracted13, _run_video_dub_job_extracted14, _run_video_dub_job_extracted15, _run_video_dub_job_extracted16, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5, _run_video_dub_job_extracted6, _run_video_dub_job_extracted7, _run_video_dub_job_extracted8, _run_video_dub_job_extracted9)
    return task

def _run_video_dub_job_extracted19(_run_video_dub_job_extracted1, _run_video_dub_job_extracted10, _run_video_dub_job_extracted11, _run_video_dub_job_extracted12, _run_video_dub_job_extracted13, _run_video_dub_job_extracted14, _run_video_dub_job_extracted15, _run_video_dub_job_extracted16, _run_video_dub_job_extracted17, _run_video_dub_job_extracted18, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5, _run_video_dub_job_extracted6, _run_video_dub_job_extracted7, _run_video_dub_job_extracted8, _run_video_dub_job_extracted9):
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param _run_video_dub_job_extracted1, _run_video_dub_job_extracted10, _run_video_dub_job_extracted11, _run_video_dub_job_extracted12, _run_video_dub_job_extracted13, _run_video_dub_job_extracted14, _run_video_dub_job_extracted15, _run_video_dub_job_extracted16, _run_video_dub_job_extracted17, _run_video_dub_job_extracted18, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5, _run_video_dub_job_extracted6, _run_video_dub_job_extracted7, _run_video_dub_job_extracted8, _run_video_dub_job_extracted9: 输入参数
    :return: 返回 task 等计算结果
    """
    task = _run_video_dub_job_extracted18(_run_video_dub_job_extracted1, _run_video_dub_job_extracted10, _run_video_dub_job_extracted11, _run_video_dub_job_extracted12, _run_video_dub_job_extracted13, _run_video_dub_job_extracted14, _run_video_dub_job_extracted15, _run_video_dub_job_extracted16, _run_video_dub_job_extracted17, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5, _run_video_dub_job_extracted6, _run_video_dub_job_extracted7, _run_video_dub_job_extracted8, _run_video_dub_job_extracted9)
    return task

async def run_video_dub_job(
    db: Session,
    tenant: Tenant,
    user: User,
    *,
    media_task_id: str,
    transcript_zh: str | None = None,
    voice_consent: bool = False,
    output_mode: str = "subtitle",
    auto_asr: bool = False,
    tts_voice: str | None = None,
    dub_voice_gender: str = "auto",
    on_progress: Any | None = None,
) -> dict[str, Any]:
    """run_video_dub_job。

    参数说明：
    :param db: 参数 db
    :param tenant: 参数 tenant
    :param user: 参数 user
    :param media_task_id: 参数 media_task_id
    :param transcript_zh: 参数 transcript_zh
    :param voice_consent: 参数 voice_consent
    :param output_mode: 参数 output_mode
    :param auto_asr: 参数 auto_asr
    :param tts_voice: 参数 tts_voice
    :param dub_voice_gender: 参数 dub_voice_gender
    :param on_progress: 参数 on_progress
    :return: 返回处理结果。
    """
    task = _run_video_dub_job_extracted19(_run_video_dub_job_extracted1, _run_video_dub_job_extracted10, _run_video_dub_job_extracted11, _run_video_dub_job_extracted12, _run_video_dub_job_extracted13, _run_video_dub_job_extracted14, _run_video_dub_job_extracted15, _run_video_dub_job_extracted16, _run_video_dub_job_extracted17, _run_video_dub_job_extracted18, _run_video_dub_job_extracted2, _run_video_dub_job_extracted3, _run_video_dub_job_extracted4, _run_video_dub_job_extracted5, _run_video_dub_job_extracted6, _run_video_dub_job_extracted7, _run_video_dub_job_extracted8, _run_video_dub_job_extracted9)
    if not task or str(task.tenant_id or "") != str(tenant.id):
        return {"ok": False, "error": "找不到该视频，请先上传中文产品片"}

    video_dur_sec, temp_path, source_path, warnings, product_hint = _run_video_dub_job_extracted(task)
    try:
        zh_text, asr_meta = await _resolve_video_dub_transcript(
            source_path, transcript_zh, auto_asr, video_dur_sec, warnings, on_progress
        )
        if not zh_text:
            return {
                "ok": False,
                "error": "缺少中文解说词",
                "error_code": "TRANSCRIPT_REQUIRED",
                "hint": (
                    "自动听写未成功。请配置讯飞/Whisper 听写，或在「高级」中粘贴中文解说词后重试。"
                ),
                "media_task_id": str(task.id),
                "asr": asr_meta,
            }

        if on_progress:
            on_progress(55, "翻译英文解说稿…")
        translation = await _translate_script(
            db, tenant, transcript_zh=zh_text, product_hint=str(product_hint)
        )
        segments = translation.get("segments") or []
        srt_body = _format_srt(segments if isinstance(segments, list) else [])
        ensure_uploads_dir()
        dub_id = uuid.uuid4().hex[:12]
        srt_name = f"dub_{dub_id}.srt"
        srt_path = UPLOADS_DIR / srt_name
        srt_path.write_text(srt_body, encoding="utf-8")
        fail, output_url, audio_url, output_mode_used, tts_info, voice_pick, picked_voice = _prepare_dub_outputs(
            db, tenant, task, translation, segments, source_path, output_mode,
            voice_consent, tts_voice, dub_voice_gender, video_dur_sec, zh_text,
            dub_id, srt_path, UPLOADS_DIR, warnings, on_progress,
        )
        if fail is not None:
            return fail

        return _finalize_video_dub_result(
            db, task, zh_text, translation, segments, srt_name, output_url,
            audio_url, output_mode_used, voice_consent, voice_pick, picked_voice,
            asr_meta, tts_info, warnings, video_dur_sec,
        )
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
    """实现 ingest客户端视频 的功能。
    
    :param db: 参数 db（类型: Session）
    :param user: 参数 user（类型: User）
    :param content: 参数 content（类型: bytes）
    :param original_filename: 参数 original_filename（类型: str）
    :param content_type: 参数 content_type（类型: str | None）
    :param tenant_id: 参数 tenant_id（类型: str）
    :return: 返回 dict[str, Any] 结果
    """
    return ingest_uploaded_media_file(
        db,
        user,
        content=content,
        original_filename=original_filename,
        content_type=content_type,
        explicit_tenant_id=tenant_id,
        prefer_local_storage=True,
    )
