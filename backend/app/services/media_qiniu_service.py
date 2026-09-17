# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""七牛云 Kodo — 国内产品图存储（S3 类对象存储 + CDN 域名）。"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import time

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class MediaQiniuError(Exception):
    pass


def qiniu_configured() -> bool:
    """qiniu_configured。
    :return: 返回处理结果。
    """
    return bool(
        settings.QINIU_ACCESS_KEY
        and settings.QINIU_SECRET_KEY
        and settings.QINIU_BUCKET
    )


def _upload_token(object_key: str, *, expires_seconds: int = 3600) -> str:
    """_upload_token。

    参数说明：
    :param object_key: 参数 object_key
    :param expires_seconds: 参数 expires_seconds
    :return: 返回处理结果。
    """
    if not qiniu_configured():
        raise MediaQiniuError("七牛未配置（QINIU_*）")
    bucket = settings.QINIU_BUCKET or ""
    deadline = int(time.time()) + expires_seconds
    policy = {"scope": f"{bucket}:{object_key}", "deadline": deadline}
    encoded_policy = base64.urlsafe_b64encode(
        json.dumps(policy, separators=(",", ":")).encode()
    ).decode()
    sign = hmac.new(
        (settings.QINIU_SECRET_KEY or "").encode(),
        encoded_policy.encode(),
        hashlib.sha1,
    ).digest()
    encoded_sign = base64.urlsafe_b64encode(sign).decode()
    return f"{settings.QINIU_ACCESS_KEY}:{encoded_sign}:{encoded_policy}"


def public_url_for_key(object_key: str) -> str:
    """public_url_for_key。

    参数说明：
    :param object_key: 参数 object_key
    :return: 返回处理结果。
    """
    base = (settings.QINIU_PUBLIC_BASE_URL or "").rstrip("/")
    if not base:
        raise MediaQiniuError("七牛公开域名未配置（QINIU_PUBLIC_BASE_URL）")
    return f"{base}/{object_key.lstrip('/')}"


def upload_bytes_to_qiniu(
    data: bytes,
    object_key: str,
    *,
    content_type: str = "application/octet-stream",
) -> str:
    """上传字节到七牛，返回 object_key。"""
    token = _upload_token(object_key)
    upload_host = (settings.QINIU_UPLOAD_HOST or "https://upload.qiniup.com").rstrip("/")
    with httpx.Client(timeout=120.0) as client:
        resp = client.post(
            upload_host,
            data={"token": token, "key": object_key},
            files={"file": (object_key.rsplit("/", 1)[-1], data, content_type)},
        )
    if resp.status_code >= 400:
        raise MediaQiniuError(f"七牛上传失败 HTTP {resp.status_code}: {resp.text[:200]}")
    return object_key


def delete_object_from_qiniu(object_key: str) -> None:
    """delete_object_from_qiniu。

    参数说明：
    :param object_key: 参数 object_key
    :return: 返回处理结果。
    """
    if not qiniu_configured():
        return
    entry = base64.urlsafe_b64encode(
        f"{settings.QINIU_BUCKET}:{object_key}".encode()
    ).decode()
    path = f"/delete/{entry}"
    signing_str = f"{path}\n"
    sign = hmac.new(
        (settings.QINIU_SECRET_KEY or "").encode(),
        signing_str.encode(),
        hashlib.sha1,
    ).digest()
    token = f"{settings.QINIU_ACCESS_KEY}:{base64.urlsafe_b64encode(sign).decode()}"
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(f"https://rs.qiniu.com{path}", headers={"Authorization": f"QBox {token}"})
    if resp.status_code >= 400 and resp.status_code != 612:
        logger.warning("七牛删除失败 key=%s status=%s", object_key, resp.status_code)
