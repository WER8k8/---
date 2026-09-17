# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""讯飞语音转写（LFASR / raasr）— 云端听写兜底。

文档：https://www.xfyun.cn/doc/asr/lfasr/API.html
与星火 LLM（AI_XUNFEI_*）密钥独立，须单独开通「语音转写」并配置 APP_ID + SECRET_KEY。
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import time
from pathlib import Path
from typing import Any, Callable

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

ProgressFn = Callable[[int, str], None]

_SLICE_BYTES = 10 * 1024 * 1024  # 官方建议 10M
_STATUS_DONE = 9


class _SliceIdGenerator:
    """讯飞 slice_id 生成器（官方 demo）。"""

    def __init__(self) -> None:
        self._ch = "aaaaaaaaa`"

    def next_id(self) -> str:
        ch = self._ch
        j = len(ch) - 1
        while j >= 0:
            cj = ch[j]
            if cj != "z":
                ch = ch[:j] + chr(ord(cj) + 1) + ch[j + 1 :]
                break
            ch = ch[:j] + "a" + ch[j + 1 :]
            j -= 1
        self._ch = ch
        return self._ch


def use_ifasr_llm_api() -> bool:
    """控制台「非实时语音转写大模型」WebAPI（office-api-ist-dx.iflyaisol.com）。"""
    base = (settings.XFYUN_LFASR_BASE_URL or "").lower()
    if "iflyaisol" in base or "office-api-ist" in base:
        return True
    return bool((settings.XFYUN_LFASR_API_KEY or "").strip())


def is_xfyun_lfasr_configured() -> bool:
    """是否已配置讯飞听写（大模型 WebAPI 或旧版 raasr）。"""
    import os

    if os.getenv("XFYUN_LFASR_ENABLED", "").strip().lower() in ("0", "false", "no", "off"):
        return False
    app_id = (settings.XFYUN_LFASR_APP_ID or "").strip()
    secret = (settings.XFYUN_LFASR_SECRET_KEY or "").strip()
    if not app_id or not secret:
        return False
    if app_id.startswith("your_") or secret.startswith("your_"):
        return False
    if use_ifasr_llm_api():
        api_key = (settings.XFYUN_LFASR_API_KEY or "").strip()
        if not api_key or api_key.startswith("your_"):
            return False
    return True


def prefer_xfyun_lfasr_direct() -> bool:
    """配齐讯飞密钥时默认整段直传 LFASR（跳过分片/本地 Whisper 优先）。"""
    if not is_xfyun_lfasr_configured():
        return False
    import os

    raw = os.getenv("XFYUN_LFASR_PREFERRED", "1").strip().lower()
    return raw not in ("0", "false", "no", "off")


def build_lfasr_signa(app_id: str, secret_key: str, ts: str) -> str:
    """signa = base64(HmacSHA1(MD5(app_id + ts), secret_key))。"""
    base_string = f"{app_id}{ts}"
    md5_hex = hashlib.md5(base_string.encode("utf-8")).hexdigest()
    digest = hmac.new(
        secret_key.encode("utf-8"),
        md5_hex.encode("utf-8"),
        hashlib.sha1,
    ).digest()
    return base64.b64encode(digest).decode("utf-8")


def _auth_params() -> dict[str, str]:
    """构建带时间戳与 signa 的认证参数。"""
    ts = str(int(time.time()))
    app_id = settings.XFYUN_LFASR_APP_ID.strip()
    secret = settings.XFYUN_LFASR_SECRET_KEY.strip()
    return {
        "app_id": app_id,
        "ts": ts,
        "signa": build_lfasr_signa(app_id, secret, ts),
    }


def _api_base() -> str:
    """讯飞 LFASR 接口基地址。"""
    base = (settings.XFYUN_LFASR_BASE_URL or "https://raasr.xfyun.cn/api").rstrip("/")
    return base


def _post_form(path: str, data: dict[str, Any], *, timeout: float = 60.0) -> dict[str, Any]:
    """POST 表单到 LFASR，校验业务 ok 码，失败抛 RuntimeError。"""
    url = f"{_api_base()}/{path.lstrip('/')}"
    with httpx.Client(timeout=timeout) as client:
        resp = client.post(url, data=data)
        resp.raise_for_status()
        body = resp.json()
    if not isinstance(body, dict):
        raise RuntimeError(f"lfasr {path} 响应非 JSON")
    if body.get("ok") != 0:
        raise RuntimeError(
            f"lfasr {path} 失败: err_no={body.get('err_no')} failed={body.get('failed')}"
        )
    return body


def _parse_lfasr_result_data(data: str) -> dict[str, Any]:
    """解析 getResult 的 data 字段为 text + segments。"""
    raw = json.loads(data)
    items: list[dict[str, Any]]
    if isinstance(raw, list):
        items = raw
    elif isinstance(raw, dict):
        items = raw.get("lattice") or raw.get("lattice2") or raw.get("result") or []
        if isinstance(items, dict):
            items = [items]
    else:
        items = []

    parts: list[str] = []
    segments: list[dict[str, Any]] = []
    for row in items:
        if not isinstance(row, dict):
            continue
        text = str(row.get("onebest") or row.get("text") or "").strip()
        if not text:
            continue
        parts.append(text)
        try:
            bg_ms = int(row.get("bg") or 0)
            ed_ms = int(row.get("ed") or bg_ms)
        except (TypeError, ValueError):
            bg_ms, ed_ms = 0, 0
        segments.append(
            {
                "start": bg_ms / 1000.0,
                "end": ed_ms / 1000.0,
                "text": text,
            }
        )
    text = "".join(parts).strip()
    return {"text": text, "segments": segments}


def _prepare_lfasr_task(file_size: int, file_name: str, slice_num: int) -> dict[str, str]:
    """构建 prepare 表单数据（认证 + 文件元信息）。"""
    return {
        **_auth_params(),
        "file_len": str(file_size),
        "file_name": file_name,
        "slice_num": str(slice_num),
        "lfasr_type": "0",
        "language": "cn",
    }


def _upload_lfasr_slices(
    audio_path: Path,
    task_id: str,
    slice_num: int,
    *,
    on_progress: ProgressFn | None,
) -> bool:
    """按 10M 分片上传音频；成功返回 True，失败返回 False。"""
    if on_progress:
        on_progress(45, "讯飞云端听写：上传音频…")

    slice_gen = _SliceIdGenerator()
    try:
        with audio_path.open("rb") as fh:
            for idx in range(slice_num):
                chunk = fh.read(_SLICE_BYTES)
                if not chunk:
                    break
                upload_data = {
                    **_auth_params(),
                    "task_id": task_id,
                    "slice_id": slice_gen.next_id(),
                }
                url = f"{_api_base()}/upload"
                with httpx.Client(timeout=120.0) as client:
                    resp = client.post(
                        url,
                        data=upload_data,
                        files={"content": ("slice", chunk, "application/octet-stream")},
                    )
                    resp.raise_for_status()
                    body = resp.json()
                if body.get("ok") != 0:
                    raise RuntimeError(
                        f"upload slice {idx + 1}/{slice_num}: {body.get('failed')}"
                    )
                if on_progress and slice_num > 1:
                    pct = 45 + int(15 * (idx + 1) / slice_num)
                    on_progress(pct, f"讯飞上传 {idx + 1}/{slice_num}…")
    except Exception as exc:
        logger.warning("xfyun lfasr upload failed: %s", exc)
        return False
    return True


def _merge_lfasr_task(task_id: str) -> bool:
    """合并已上传分片；成功返回 True，失败返回 False。"""
    try:
        _post_form("merge", {**_auth_params(), "task_id": task_id})
    except Exception as exc:
        logger.warning("xfyun lfasr merge failed: %s", exc)
        return False
    return True


def _poll_lfasr_progress(
    task_id: str,
    *,
    on_progress: ProgressFn | None,
) -> int | None:
    """轮询 getProgress 直到完成或超时；返回最终 status，超时返回 None。"""
    poll_interval = max(2.0, float(settings.XFYUN_LFASR_POLL_INTERVAL_SEC or 5.0))
    max_wait = max(60, int(settings.XFYUN_LFASR_MAX_WAIT_SEC or 1800))
    deadline = time.time() + max_wait
    status = -1

    while time.time() < deadline:
        try:
            prog = _post_form("getProgress", {**_auth_params(), "task_id": task_id}, timeout=30.0)
            prog_data = json.loads(prog.get("data") or "{}")
            status = int(prog_data.get("status", -1))
        except Exception as exc:
            logger.warning("xfyun lfasr getProgress failed: %s", exc)
            time.sleep(poll_interval)
            continue

        if status == _STATUS_DONE:
            break
        if on_progress:
            hint = prog_data.get("desc") if isinstance(prog_data, dict) else ""
            on_progress(65, f"讯飞转写中（{hint or status}）…")
        time.sleep(poll_interval)
    else:
        logger.warning("xfyun lfasr poll timeout after %ss", max_wait)
        return None
    return status


def _fetch_lfasr_result(task_id: str, *, on_progress: ProgressFn | None) -> dict[str, Any] | None:
    """拉取转写结果；解析失败返回 None。"""
    if on_progress:
        on_progress(85, "讯飞云端听写：拉取结果…")
    try:
        result = _post_form("getResult", {**_auth_params(), "task_id": task_id}, timeout=60.0)
        parsed = _parse_lfasr_result_data(str(result.get("data") or "[]"))
    except Exception as exc:
        logger.warning("xfyun lfasr getResult failed: %s", exc)
        return None
    return parsed


def _prepare_lfasr_session(
    audio_path: Path,
    file_size: int,
    *,
    on_progress: ProgressFn | None,
) -> tuple[str, int, str] | None:
    """调用 prepare 建立任务；返回 (task_id, slice_num, file_name) 或 None。"""
    slice_num = max(1, (file_size + _SLICE_BYTES - 1) // _SLICE_BYTES)
    file_name = audio_path.name if audio_path.suffix else f"{audio_path.name}.wav"

    if on_progress:
        on_progress(40, "讯飞云端听写：预处理…")

    try:
        prep = _post_form("prepare", _prepare_lfasr_task(file_size, file_name, slice_num))
    except Exception as exc:
        logger.warning("xfyun lfasr prepare failed: %s", exc)
        return None

    task_id = str(prep.get("data") or "").strip()
    if not task_id:
        logger.warning("xfyun lfasr prepare missing task_id")
        return None
    return task_id, slice_num, file_name


def transcribe_with_xfyun_lfasr(
    audio_path: Path,
    *,
    on_progress: ProgressFn | None = None,
) -> dict[str, Any] | None:
    """上传音频至讯飞听写并轮询结果；未配置密钥时返回 None。"""
    if not is_xfyun_lfasr_configured():
        return None
    if not audio_path.is_file():
        return None

    if use_ifasr_llm_api():
        from app.services.cross_border.xfyun_ifasr_llm_service import transcribe_with_ifasr_llm

        return transcribe_with_ifasr_llm(audio_path, on_progress=on_progress)

    file_size = audio_path.stat().st_size
    if file_size <= 44:
        return None

    session = _prepare_lfasr_session(audio_path, file_size, on_progress=on_progress)
    if session is None:
        return None
    task_id, slice_num, _file_name = session

    if not _upload_lfasr_slices(audio_path, task_id, slice_num, on_progress=on_progress):
        return None

    if on_progress:
        on_progress(62, "讯飞云端听写：合并排队…")

    if not _merge_lfasr_task(task_id):
        return None

    status = _poll_lfasr_progress(task_id, on_progress=on_progress)
    if status is None:
        return None
    if status != _STATUS_DONE:
        logger.warning("xfyun lfasr ended with status=%s", status)
        return None

    parsed = _fetch_lfasr_result(task_id, on_progress=on_progress)
    if parsed is None:
        return None
    if not parsed.get("text"):
        return None

    return {
        "text": parsed["text"],
        "segments": parsed.get("segments") or [],
        "backend": "xfyun_lfasr",
        "task_id": task_id,
    }