"""讯飞「录音文件转写大模型」WebAPI（Ifasr LLM）。

文档：https://www.xfyun.cn/doc/spark/asr_llm/Ifasr_llm.html
接口：https://office-api-ist-dx.iflyaisol.com
鉴权：APPID + APIKey(accessKeyId) + APISecret(accessKeySecret)，与旧版 raasr signa 不同。
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import secrets
import string
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import quote, urlencode

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

ProgressFn = Callable[[int, str], None]

_CN_TZ = timezone(timedelta(hours=8))
_STATUS_DONE = 4
_STATUS_FAILED = -1


def build_ifasr_llm_signature(access_key_secret: str, params: dict[str, str]) -> str:
    """HMAC-SHA1(URL编码后的 key=value 串, APISecret) → Base64。"""
    items = sorted(
        (k, v)
        for k, v in params.items()
        if k != "signature" and v is not None and str(v) != ""
    )
    parts: list[str] = []
    for key, value in items:
        enc_key = quote(str(key), safe="")
        enc_val = quote(str(value), safe="")
        parts.append(f"{enc_key}={enc_val}")
    base_string = "&".join(parts)
    digest = hmac.new(
        access_key_secret.encode("utf-8"),
        base_string.encode("utf-8"),
        hashlib.sha1,
    ).digest()
    return base64.b64encode(digest).decode("ascii")


def _now_datetime_str() -> str:
    """实现 nowdatetimestr 的功能。

    :return: 返回 str 结果
    """
    return datetime.now(_CN_TZ).strftime("%Y-%m-%dT%H:%M:%S+0800")


def _random_signature_nonce() -> str:
    """实现 randomsignaturenonce 的功能。

    :return: 返回 str 结果
    """
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(16))


def _api_base() -> str:
    """实现 APIbase 的功能。

    :return: 返回 str 结果
    """
    return (settings.XFYUN_LFASR_BASE_URL or "https://office-api-ist-dx.iflyaisol.com").rstrip("/")


def parse_ifasr_llm_order_result(order_result_raw: str) -> dict[str, Any]:
    """解析 getResult 的 orderResult JSON 字符串。"""
    if not (order_result_raw or "").strip():
        return {"text": "", "segments": []}

    outer = json.loads(order_result_raw)
    lattice = outer.get("lattice") or outer.get("lattice2") or []
    if not isinstance(lattice, list):
        lattice = []

    parts: list[str] = []
    segments: list[dict[str, Any]] = []
    for item in lattice:
        if not isinstance(item, dict):
            continue
        j1b = item.get("json_1best")
        if isinstance(j1b, str):
            try:
                j1b = json.loads(j1b)
            except json.JSONDecodeError:
                continue
        if not isinstance(j1b, dict):
            continue
        st = j1b.get("st") or {}
        if not isinstance(st, dict):
            continue

        sent_parts: list[str] = []
        for rt in st.get("rt") or []:
            if not isinstance(rt, dict):
                continue
            for ws in rt.get("ws") or []:
                if not isinstance(ws, dict):
                    continue
                for cw in ws.get("cw") or []:
                    if not isinstance(cw, dict):
                        continue
                    w = str(cw.get("w") or "")
                    wp = str(cw.get("wp") or "n")
                    if not w or wp == "g":
                        continue
                    sent_parts.append(w)

        text = "".join(sent_parts).strip()
        if not text:
            continue
        parts.append(text)
        try:
            bg_ms = int(st.get("bg") or 0)
            ed_ms = int(st.get("ed") or bg_ms)
        except (TypeError, ValueError):
            bg_ms, ed_ms = 0, 0
        segments.append(
            {
                "start": bg_ms / 1000.0,
                "end": ed_ms / 1000.0,
                "text": text,
            }
        )

    return {"text": "".join(parts).strip(), "segments": segments}


def _load_ifasr_llm_credentials() -> tuple[str, str, str]:
    """读取讯飞大模型听写密钥三元组 (access_key_id, access_key_secret, app_id)。"""
    app_id = (settings.XFYUN_LFASR_APP_ID or "").strip()
    access_key_id = (settings.XFYUN_LFASR_API_KEY or "").strip()
    access_key_secret = (settings.XFYUN_LFASR_SECRET_KEY or "").strip()
    return access_key_id, access_key_secret, app_id


def _build_upload_params(
    access_key_id: str,
    app_id: str,
    signature_random: str,
    file_size: int,
    file_name: str,
) -> dict[str, str]:
    """构建 /v2/upload 请求参数（含 signatureRandom 与鉴权字段）。"""
    language = (getattr(settings, "XFYUN_LFASR_LANGUAGE", None) or "autodialect").strip()
    return {
        "appId": app_id,
        "accessKeyId": access_key_id,
        "dateTime": _now_datetime_str(),
        "signatureRandom": signature_random,
        "fileSize": str(file_size),
        "fileName": file_name,
        "language": language,
        "durationCheckDisable": "true",
    }


def _upload_audio_to_ifasr(
    audio_path: Path,
    upload_url: str,
    upload_sig: str,
    *,
    on_progress: ProgressFn | None,
) -> dict[str, Any] | None:
    """上传音频文件至讯飞服务器；失败返回 None。"""
    if on_progress:
        on_progress(42, "讯飞大模型听写：上传音频…")
    try:
        with audio_path.open("rb") as fh:
            with httpx.Client(timeout=300.0) as client:
                resp = client.post(
                    upload_url,
                    content=fh.read(),
                    headers={
                        "Content-Type": "application/octet-stream",
                        "signature": upload_sig,
                    },
                )
                resp.raise_for_status()
                body = resp.json()
    except Exception as exc:
        logger.warning("ifasr llm upload failed: %s", exc)
        return None
    return body


def _build_query_params(
    access_key_id: str,
    signature_random: str,
    order_id: str,
) -> dict[str, str]:
    """构建 /v2/getResult 查询参数（签名随机串 + 订单号）。"""
    return {
        "accessKeyId": access_key_id,
        "dateTime": _now_datetime_str(),
        "signatureRandom": signature_random,
        "orderId": order_id,
        "resultType": "transfer",
    }


def _fetch_ifasr_result(
    query_url: str,
    query_sig: str,
) -> dict[str, Any] | None:
    """请求一次 getResult；网络异常返回 None。"""
    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(
                query_url,
                content=b"{}",
                headers={
                    "Content-Type": "application/json",
                    "signature": query_sig,
                },
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("ifasr llm getResult failed: %s", exc)
        return None


def _poll_ifasr_llm_result(
    access_key_id: str,
    access_key_secret: str,
    signature_random: str,
    order_id: str,
    *,
    on_progress: ProgressFn | None,
) -> dict[str, Any] | None:
    """轮询 getResult 直至完成/失败/超时，返回转写结果 dict 或 None。"""
    poll_interval = max(2.0, float(settings.XFYUN_LFASR_POLL_INTERVAL_SEC or 5.0))
    max_wait = max(60, int(settings.XFYUN_LFASR_MAX_WAIT_SEC or 1800))
    deadline = time.time() + max_wait

    while time.time() < deadline:
        query_params = _build_query_params(access_key_id, signature_random, order_id)
        query_sig = build_ifasr_llm_signature(access_key_secret, query_params)
        query_url = f"{_api_base()}/v2/getResult?{urlencode(query_params)}"
        body = _fetch_ifasr_result(query_url, query_sig)
        if body is None:
            time.sleep(poll_interval)
            continue

        if str(body.get("code")) != "000000":
            logger.warning("ifasr llm getResult rejected: %s", body.get("descInfo"))
            time.sleep(poll_interval)
            continue

        content = body.get("content") or {}
        order_info = content.get("orderInfo") or {}
        try:
            status = int(order_info.get("status", 0))
        except (TypeError, ValueError):
            status = 0

        if status == _STATUS_FAILED:
            logger.warning("ifasr llm order failed: failType=%s", order_info.get("failType"))
            return None

        if status == _STATUS_DONE:
            raw_result = str(content.get("orderResult") or "")
            if raw_result:
                parsed = parse_ifasr_llm_order_result(raw_result)
                if parsed.get("text"):
                    if on_progress:
                        on_progress(88, "讯飞大模型听写：拉取结果…")
                    return {
                        "text": parsed["text"],
                        "segments": parsed.get("segments") or [],
                        "backend": "xfyun_ifasr_llm",
                        "order_id": order_id,
                    }
            return None

        if on_progress:
            on_progress(65, f"讯飞大模型转写中（status={status}）…")
        time.sleep(poll_interval)

    logger.warning("ifasr llm poll timeout after %ss", max_wait)
    return None


def transcribe_with_ifasr_llm(
    audio_path: Path,
    *,
    on_progress: ProgressFn | None = None,
) -> dict[str, Any] | None:
    """上传音频至讯飞录音文件转写大模型并轮询结果；未配置密钥返回 None。"""
    access_key_id, access_key_secret, app_id = _load_ifasr_llm_credentials()
    if not app_id or not access_key_id or not access_key_secret:
        return None
    if not audio_path.is_file():
        return None

    file_size = audio_path.stat().st_size
    if file_size <= 44:
        return None

    file_name = audio_path.name if audio_path.suffix else f"{audio_path.name}.wav"
    signature_random = _random_signature_nonce()
    upload_params = _build_upload_params(access_key_id, app_id, signature_random, file_size, file_name)
    upload_sig = build_ifasr_llm_signature(access_key_secret, upload_params)
    upload_url = f"{_api_base()}/v2/upload?{urlencode(upload_params)}"

    body = _upload_audio_to_ifasr(audio_path, upload_url, upload_sig, on_progress=on_progress)
    if body is None:
        return None
    if str(body.get("code")) != "000000":
        logger.warning("ifasr llm upload rejected: %s", body.get("descInfo"))
        return None

    content = body.get("content") or {}
    order_id = str(content.get("orderId") or "").strip()
    if not order_id:
        logger.warning("ifasr llm upload missing orderId")
        return None

    return _poll_ifasr_llm_result(
        access_key_id,
        access_key_secret,
        signature_random,
        order_id,
        on_progress=on_progress,
    )