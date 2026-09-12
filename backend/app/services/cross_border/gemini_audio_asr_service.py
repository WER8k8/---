"""Gemini 音频听写兜底（多模态 generateContent，非专用 ASR）。

使用已有 AI_GEMINI_API_KEY；小文件 inline base64，大文件走 Files API。
时间轴精度弱于 Whisper/讯飞，仅在前序引擎均失败时使用。
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Callable

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

ProgressFn = Callable[[int, str], None]

_INLINE_MAX_BYTES = 14 * 1024 * 1024
_TRANSCRIBE_PROMPT = (
    "请将这段中文口语音频逐字转写为简体中文。\n"
    "铁律：只输出实际听到的话，禁止摘要、补充、翻译或编造。\n"
    "输出 JSON（不要 markdown 代码块）：\n"
    '{"text":"完整转写正文","segments":[{"start":0.0,"end":0.0,"text":"可选分句"}]}'
)


def is_gemini_asr_configured() -> bool:
    """实现 isgeminiasrconfigured 的功能。
    
    :return: 返回 bool 结果
    """
    if os.getenv("AI_GEMINI_ASR_ENABLED", "").strip().lower() in ("0", "false", "no", "off"):
        return False
    key = (settings.AI_GEMINI_API_KEY or "").strip()
    if not key or key.startswith("your_"):
        return False
    return True


def _api_root() -> str:
    """实现 APIroot 的功能。
    
    :return: 返回 str 结果
    """
    base = (settings.AI_GEMINI_BASE_URL or "https://generativelanguage.googleapis.com").rstrip("/")
    if base.endswith("/v1beta"):
        return base
    if base.endswith("/v1"):
        return f"{base.rstrip('/v1')}/v1beta"
    return f"{base}/v1beta"


def _model_name() -> str:
    """实现 模型名称 的功能。
    
    :return: 返回 str 结果
    """
    raw = (getattr(settings, "AI_GEMINI_ASR_MODEL", None) or "gemini-2.0-flash").strip()
    return raw.removeprefix("models/")


def _api_key() -> str:
    """实现 API键 的功能。
    
    :return: 返回 str 结果
    """
    return (settings.AI_GEMINI_API_KEY or "").strip()


def parse_gemini_transcript_response(text: str) -> dict[str, Any]:
    """从模型输出提取 text / segments。"""
    raw = (text or "").strip()
    if not raw:
        return {"text": "", "segments": []}

    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if fence:
        raw = fence.group(1).strip()

    try:
        data = json.loads(raw)
        if isinstance(data, dict) and data.get("text"):
            segs = data.get("segments") if isinstance(data.get("segments"), list) else []
            return {"text": str(data["text"]).strip(), "segments": segs}
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\"text\"[\s\S]*\}", raw)
    if match:
        try:
            data = json.loads(match.group(0))
            if isinstance(data, dict) and data.get("text"):
                segs = data.get("segments") if isinstance(data.get("segments"), list) else []
                return {"text": str(data["text"]).strip(), "segments": segs}
        except json.JSONDecodeError:
            pass

    return {"text": raw.strip(), "segments": []}


def _generate_content(parts: list[dict[str, Any]], *, timeout: float = 120.0) -> str:
    """实现 生成内容 的功能。
    
    :param parts: 参数 parts（类型: list[dict[str, Any]]）
    :param timeout: 参数 timeout（类型: float）
    :return: 返回 str 结果
    :raises RuntimeError: 当操作失败时抛出 RuntimeError 异常
    """
    url = f"{_api_root()}/models/{_model_name()}:generateContent"
    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 8192},
    }
    with httpx.Client(timeout=timeout) as client:
        resp = client.post(url, params={"key": _api_key()}, json=payload)
        resp.raise_for_status()
        body = resp.json()
    candidates = body.get("candidates") or []
    if not candidates:
        raise RuntimeError(f"gemini asr empty candidates: {body.get('promptFeedback')}")
    parts_out = (candidates[0].get("content") or {}).get("parts") or []
    texts = [str(p.get("text") or "") for p in parts_out if p.get("text")]
    content = "".join(texts).strip()
    if not content:
        raise RuntimeError("gemini asr empty text")
    return content


def _upload_file_multipart(wav: Path) -> str:
    """multipart 上传，返回 file_uri。"""
    url = f"{_api_root().replace('/v1beta', '')}/upload/v1beta/files"
    metadata = json.dumps({"file": {"displayName": wav.name}})
    with wav.open("rb") as fh:
        files = {
            "metadata": ("metadata", metadata, "application/json"),
            "file": (wav.name, fh, "audio/wav"),
        }
        with httpx.Client(timeout=180.0) as client:
            resp = client.post(
                url,
                params={"key": _api_key()},
                headers={"X-Goog-Upload-Protocol": "multipart"},
                files=files,
            )
            resp.raise_for_status()
            body = resp.json()
    file_obj = body.get("file") or {}
    file_name = str(file_obj.get("name") or "")
    file_uri = str(file_obj.get("uri") or "")
    if not file_uri and file_name:
        file_uri = f"{_api_root()}/{file_name}"
    if not file_uri:
        raise RuntimeError("gemini file upload missing uri")
    return _wait_file_active(file_name or file_uri)


def _wait_file_active(file_ref: str, *, max_wait: int = 120) -> str:
    """轮询 Files API 直至 ACTIVE，返回 file_uri。"""
    if file_ref.startswith("http"):
        name = file_ref.rsplit("/", 1)[-1]
        if not name.startswith("files/"):
            name = f"files/{name}"
    else:
        name = file_ref if file_ref.startswith("files/") else f"files/{file_ref}"

    deadline = time.time() + max_wait
    get_url = f"{_api_root()}/{name}"
    while time.time() < deadline:
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(get_url, params={"key": _api_key()})
            resp.raise_for_status()
            body = resp.json()
        state = str(body.get("state") or "")
        uri = str(body.get("uri") or "")
        if state == "ACTIVE" and uri:
            return uri
        if state == "FAILED":
            raise RuntimeError(f"gemini file processing failed: {body.get('error')}")
        time.sleep(2.0)
    raise RuntimeError("gemini file processing timeout")


def transcribe_with_gemini_audio(
    audio_path: Path,
    *,
    on_progress: ProgressFn | None = None,
) -> dict[str, Any] | None:
    """Gemini 音频听写；未配置 AI_GEMINI_API_KEY 时返回 None。"""
    if not is_gemini_asr_configured():
        return None
    if not audio_path.is_file():
        return None

    file_size = audio_path.stat().st_size
    if file_size <= 44:
        return None

    if on_progress:
        on_progress(88, "Gemini 音频听写…")

    try:
        if file_size <= _INLINE_MAX_BYTES:
            data_b64 = base64.b64encode(audio_path.read_bytes()).decode("ascii")
            parts = [
                {"inline_data": {"mime_type": "audio/wav", "data": data_b64}},
                {"text": _TRANSCRIBE_PROMPT},
            ]
        else:
            if on_progress:
                on_progress(86, "Gemini 上传音频…")
            file_uri = _upload_file_multipart(audio_path)
            parts = [
                {"file_data": {"mime_type": "audio/wav", "file_uri": file_uri}},
                {"text": _TRANSCRIBE_PROMPT},
            ]

        raw = _generate_content(parts)
        parsed = parse_gemini_transcript_response(raw)
        text = (parsed.get("text") or "").strip()
        if not text:
            return None

        segments = parsed.get("segments") or []
        if not segments:
            segments = [{"start": 0.0, "end": 0.0, "text": text}]

        return {
            "text": text,
            "segments": segments,
            "backend": "gemini_audio",
        }
    except Exception as exc:
        logger.warning("gemini audio asr failed: %s", exc)
        return None
