# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""棱束链（S3 兼容）灾备上传。"""

from __future__ import annotations

import logging
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlparse

from minio import Minio
from minio.error import S3Error

from app.core.config import settings

logger = logging.getLogger(__name__)


class MediaLenslinkError(Exception):
    pass


def lenslink_backup_enabled() -> bool:
    """lenslink_backup_enabled。
    :return: 返回处理结果。
    """
    return (settings.MEDIA_CLOUD_BACKUP or "none").strip().lower() == "lenslink"


def lenslink_configured() -> bool:
    """lenslink_configured。
    :return: 返回处理结果。
    """
    return bool(
        lenslink_backup_enabled()
        and settings.MEDIA_LENSLINK_ENDPOINT
        and settings.MEDIA_LENSLINK_ACCESS_KEY
        and settings.MEDIA_LENSLINK_SECRET_KEY
        and settings.MEDIA_LENSLINK_BUCKET
    )


def _parse_endpoint() -> tuple[str, bool]:
    """_parse_endpoint。
    :return: 返回处理结果。
    """
    raw = (settings.MEDIA_LENSLINK_ENDPOINT or "").strip()
    if not raw:
        raise MediaLenslinkError("MEDIA_LENSLINK_ENDPOINT 未配置")
    if raw.startswith("http://") or raw.startswith("https://"):
        parsed = urlparse(raw)
        host = parsed.netloc or parsed.path
        secure = parsed.scheme == "https"
        return host, secure
    return raw.lstrip("/"), bool(getattr(settings, "MEDIA_LENSLINK_SECURE", True))


def _client() -> Minio:
    """_client。
    :return: 返回处理结果。
    """
    if not lenslink_configured():
        raise MediaLenslinkError("棱束链未配置（MEDIA_LENSLINK_*）")
    host, secure = _parse_endpoint()
    return Minio(
        host,
        access_key=settings.MEDIA_LENSLINK_ACCESS_KEY,
        secret_key=settings.MEDIA_LENSLINK_SECRET_KEY,
        secure=secure,
        region=getattr(settings, "MEDIA_LENSLINK_REGION", None) or "us-east-1",
    )


def object_key_for_task(task_id: str, tenant_id: str | None) -> str:
    """object_key_for_task。

    参数说明：
    :param task_id: 参数 task_id
    :param tenant_id: 参数 tenant_id
    :return: 返回处理结果。
    """
    scope = tenant_id or "guest"
    return f"tenants/{scope}/videos/{task_id}.mp4"


def public_url_for_key(object_key: str) -> str | None:
    """public_url_for_key。

    参数说明：
    :param object_key: 参数 object_key
    :return: 返回处理结果。
    """
    base = (getattr(settings, "MEDIA_LENSLINK_PUBLIC_BASE_URL", None) or "").rstrip("/")
    if base:
        return f"{base}/{object_key.lstrip('/')}"
    return None


def upload_file_to_lenslink(
    file_path: Path,
    object_key: str,
    *,
    content_type: str = "video/mp4",
) -> dict[str, str]:
    """上传至棱束链，返回 object_key 与可访问 URL。"""
    if not file_path.is_file():
        raise MediaLenslinkError(f"文件不存在: {file_path}")
    bucket = settings.MEDIA_LENSLINK_BUCKET or ""
    client = _client()
    try:
        client.fput_object(bucket, object_key, str(file_path), content_type=content_type)
    except S3Error as exc:
        raise MediaLenslinkError(str(exc)) from exc

    direct = public_url_for_key(object_key)
    if direct:
        return {"key": object_key, "url": direct}

    ttl = int(getattr(settings, "MEDIA_LENSLINK_PRESIGN_SECONDS", 604800) or 604800)
    try:
        signed = client.presigned_get_object(
            bucket,
            object_key,
            expires=timedelta(seconds=ttl),
        )
    except S3Error as exc:
        raise MediaLenslinkError(str(exc)) from exc
    return {"key": object_key, "url": signed}


def upload_video_backup(
    file_path: Path,
    task_id: str,
    tenant_id: str | None,
) -> dict[str, str]:
    """upload_video_backup。

    参数说明：
    :param file_path: 参数 file_path
    :param task_id: 参数 task_id
    :param tenant_id: 参数 tenant_id
    :return: 返回处理结果。
    """
    key = object_key_for_task(task_id, tenant_id)
    return upload_file_to_lenslink(file_path, key)
