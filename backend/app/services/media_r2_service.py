# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Cloudflare R2（S3 兼容）上传与预签名。"""

from __future__ import annotations

import logging
from datetime import timedelta
from pathlib import Path

from minio import Minio
from minio.error import S3Error

from app.core.config import settings

logger = logging.getLogger(__name__)


class MediaR2Error(Exception):
    pass


def r2_configured() -> bool:
    """r2_configured。
    :return: 返回处理结果。
    """
    return bool(
        settings.MEDIA_R2_ACCOUNT_ID
        and settings.MEDIA_R2_ACCESS_KEY_ID
        and settings.MEDIA_R2_SECRET_ACCESS_KEY
        and settings.MEDIA_R2_BUCKET
    )


def _client() -> Minio:
    """_client。
    :return: 返回处理结果。
    """
    if not r2_configured():
        raise MediaR2Error("R2 未配置（MEDIA_R2_*）")
    endpoint = f"{settings.MEDIA_R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
    return Minio(
        endpoint,
        access_key=settings.MEDIA_R2_ACCESS_KEY_ID,
        secret_key=settings.MEDIA_R2_SECRET_ACCESS_KEY,
        secure=True,
        region="auto",
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


def object_key_for_image(tenant_scope: str, file_id: str, filename: str) -> str:
    """object_key_for_image。

    参数说明：
    :param tenant_scope: 参数 tenant_scope
    :param file_id: 参数 file_id
    :param filename: 参数 filename
    :return: 返回处理结果。
    """
    safe = (filename or "file").replace("/", "_").replace("\\", "_")
    return f"tenants/{tenant_scope}/images/{file_id}_{safe}"


def object_key_for_tenant_media(
    tenant_scope: str,
    file_id: str,
    filename: str,
    *,
    subdir: str,
) -> str:
    """租户媒体对象键：images | videos | audio | uploads。"""
    safe = (filename or "file").replace("/", "_").replace("\\", "_")
    folder = (subdir or "uploads").strip("/") or "uploads"
    return f"tenants/{tenant_scope}/{folder}/{file_id}_{safe}"


def upload_bytes_to_r2(
    data: bytes,
    object_key: str,
    *,
    content_type: str = "application/octet-stream",
) -> str:
    """上传字节到 R2，返回 object_key。"""
    bucket = settings.MEDIA_R2_BUCKET or ""
    client = _client()
    from io import BytesIO
    try:
        client.put_object(
            bucket,
            object_key,
            BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
    except S3Error as exc:
        raise MediaR2Error(str(exc)) from exc
    return object_key


def delete_object_from_r2(object_key: str) -> None:
    """delete_object_from_r2。

    参数说明：
    :param object_key: 参数 object_key
    :return: 返回处理结果。
    """
    if not r2_configured():
        return
    bucket = settings.MEDIA_R2_BUCKET or ""
    client = _client()
    try:
        client.remove_object(bucket, object_key)
    except S3Error as exc:
        logger.warning("R2 删除失败 key=%s err=%s", object_key, exc)


def public_url_for_object(object_key: str) -> str:
    """公开或 CDN 直链；无 CDN 时返回较长时效预签名 URL。"""
    cdn = (settings.MEDIA_R2_CDN_BASE_URL or settings.MEDIA_R2_PUBLIC_BASE_URL or "").rstrip("/")
    if cdn:
        return f"{cdn}/{object_key.lstrip('/')}"
    return presigned_get_url(object_key)


def upload_file_to_r2(file_path: Path, object_key: str, *, content_type: str = "video/mp4") -> str:
    """上传文件到 R2，返回 object_key。"""
    if not file_path.is_file():
        raise MediaR2Error(f"文件不存在: {file_path}")
    bucket = settings.MEDIA_R2_BUCKET or ""
    client = _client()
    try:
        client.fput_object(bucket, object_key, str(file_path), content_type=content_type)
    except S3Error as exc:
        raise MediaR2Error(str(exc)) from exc
    return object_key


def presigned_get_url(object_key: str, expires_seconds: int | None = None) -> str:
    """生成预签名 GET URL；若配置了 CDN/公共域名则优先直链。"""
    cdn = (settings.MEDIA_R2_CDN_BASE_URL or settings.MEDIA_R2_PUBLIC_BASE_URL or "").rstrip("/")
    if cdn:
        return f"{cdn}/{object_key.lstrip('/')}"

    bucket = settings.MEDIA_R2_BUCKET or ""
    ttl = expires_seconds or int(settings.MEDIA_R2_PRESIGN_SECONDS or 3600)
    client = _client()
    try:
        return client.presigned_get_object(
            bucket,
            object_key,
            expires=timedelta(seconds=ttl),
        )
    except S3Error as exc:
        raise MediaR2Error(str(exc)) from exc
