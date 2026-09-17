# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""酷播云（保利威点播）官方上传接口。"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class CuplayerUploadError(Exception):
    pass


def cuplayer_configured() -> bool:
    """cuplayer_configured。
    :return: 返回处理结果。
    """
    return bool(settings.MEDIA_CUPLAYER_WRITETOKEN)


def _build_sign(cataid: int, jsonrpc: str, writetoken: str, secretkey: str) -> str:
    """_build_sign。

    参数说明：
    :param cataid: 参数 cataid
    :param jsonrpc: 参数 jsonrpc
    :param writetoken: 参数 writetoken
    :param secretkey: 参数 secretkey
    :return: 返回处理结果。
    """
    raw = f"cataid={cataid}&JSONRPC={jsonrpc}&writetoken={writetoken}{secretkey}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _parse_upload_response(body: str) -> dict[str, Any]:
    """_parse_upload_response。

    参数说明：
    :param body: 参数 body
    :return: 返回处理结果。
    """
    text = (body or "").strip()
    if not text:
        raise CuplayerUploadError("酷播返回空响应")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CuplayerUploadError(f"酷播返回非 JSON: {text[:200]}") from exc

    if isinstance(payload, list) and payload:
        payload = payload[0]
    if not isinstance(payload, dict):
        raise CuplayerUploadError("酷播响应格式异常")

    err = payload.get("error")
    if err not in (0, "0", None):
        msg = payload.get("message") or payload.get("msg") or str(err)
        raise CuplayerUploadError(f"酷播上传失败: {msg}")

    data = payload.get("data")
    if isinstance(data, list) and data:
        return data[0] if isinstance(data[0], dict) else payload
    if isinstance(data, dict):
        return data
    return payload


def upload_video_file(
    file_path: Path,
    *,
    title: str,
    tag: str = "media-factory",
    desc: str = "",
    cataid: int | None = None,
    timeout: float = 300.0,
) -> dict[str, str]:
    """上传本地 mp4 到酷播，返回 vid 与播放地址。"""
    if not cuplayer_configured():
        raise CuplayerUploadError("未配置 MEDIA_CUPLAYER_WRITETOKEN")

    if not file_path.is_file():
        raise CuplayerUploadError(f"文件不存在: {file_path}")

    writetoken = settings.MEDIA_CUPLAYER_WRITETOKEN or ""
    secretkey = settings.MEDIA_CUPLAYER_SECRETKEY or ""
    cata = cataid if cataid is not None else int(settings.MEDIA_CUPLAYER_CATAID or 1)
    jsonrpc = json.dumps(
        {"title": title[:200] or file_path.stem, "tag": tag[:100], "desc": desc[:500]},
        ensure_ascii=False,
    )
    data: dict[str, str] = {
        "writetoken": writetoken,
        "JSONRPC": jsonrpc,
        "cataid": str(cata),
    }
    if secretkey:
        data["sign"] = _build_sign(cata, jsonrpc, writetoken, secretkey)

    url = settings.MEDIA_CUPLAYER_UPLOAD_URL
    with file_path.open("rb") as fh:
        files = {"Filedata": (file_path.name, fh, "video/mp4")}
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.post(url, data=data, files=files)

    if resp.status_code >= 400:
        raise CuplayerUploadError(f"HTTP {resp.status_code}: {resp.text[:300]}")

    row = _parse_upload_response(resp.text)
    vid = str(row.get("vid") or row.get("video_id") or "").strip()
    play_url = (
        str(row.get("mp4") or row.get("mp4url") or row.get("hls") or row.get("url") or "")
    ).strip()
    if not vid and not play_url:
        raise CuplayerUploadError(f"酷播未返回 vid/播放地址: {row}")

    return {
        "vid": vid,
        "play_url": play_url,
        "provider": "cuplayer",
    }
