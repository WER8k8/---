"""产品图片空间 — 国内（七牛）/ 国外（R2）分轨存储。"""

from __future__ import annotations

import json
import mimetypes
import os
import uuid
from datetime import datetime
from typing import Any, Literal, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.uploads_path import ensure_uploads_dir, uploads_dir
from app.models.tenant import Tenant, UserTenant
from app.models.user import User
from app.services.media_qiniu_service import (
    MediaQiniuError,
    delete_object_from_qiniu,
    public_url_for_key as qiniu_public_url,
    qiniu_configured,
    upload_bytes_to_qiniu,
)
from app.services.media_r2_service import (
    MediaR2Error,
    delete_object_from_r2,
    object_key_for_image,
    object_key_for_tenant_media,
    public_url_for_object as r2_public_url,
    r2_configured,
    upload_bytes_to_r2,
)
from app.services.tenant_scenario_service import resolve_tenant_id_for_user

StorageRegion = Literal["cn", "global"]
StorageBackend = Literal["qiniu", "r2", "local"]

META_FILE = os.path.join(uploads_dir(), "_files_meta.json")

_FILE_TYPE_CATEGORY = {
    "jpg": "image", "jpeg": "image", "png": "image", "webp": "image",
    "gif": "image", "svg": "image",
    "pdf": "document", "doc": "document", "docx": "document",
    "mp4": "video", "webm": "video", "avi": "video", "mov": "video",
    "mkv": "video", "flv": "video", "wmv": "video",
    "mp3": "audio", "wav": "audio", "m4a": "audio", "aac": "audio", "ogg": "audio",
}

_MEDIA_SUBDIR = {
    "image": "images",
    "video": "videos",
    "audio": "audio",
    "document": "uploads",
    "other": "uploads",
}

REGION_LABELS = {
    "cn": "国内（七牛云）",
    "global": "海外（Cloudflare R2）",
}
BACKEND_LABELS = {
    "qiniu": "七牛云",
    "r2": "Cloudflare R2",
    "local": "本地磁盘（待配置云存储）",
}


def _safe_tenant_settings(raw: str | None) -> dict[str, Any]:
    """_safe_tenant_settings。

    参数说明：
    :param raw: 参数 raw
    :return: 返回处理结果。
    """
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def _plan_features(tenant: Tenant) -> list[str]:
    """_plan_features。

    参数说明：
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    if not tenant.plan or not tenant.plan.features:
        return []
    try:
        raw = json.loads(tenant.plan.features)
        return raw if isinstance(raw, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def resolve_tenant_for_user(db: Session, user: User) -> Tenant | None:
    """resolve_tenant_for_user。

    参数说明：
    :param db: 参数 db
    :param user: 参数 user
    :return: 返回处理结果。
    """
    if user.role in ("admin", "super_admin"):
        return None
    link = (
        db.query(UserTenant)
        .filter(UserTenant.user_id == user.id, UserTenant.is_active.is_(True))
        .first()
    )
    if not link:
        return None
    return (
        db.query(Tenant)
        .filter(Tenant.id == link.tenant_id, Tenant.is_active.is_(True))
        .first()
    )


def resolve_storage_region(
    db: Session,
    user: User,
    *,
    explicit: str | None = None,
) -> StorageRegion:
    """resolve_storage_region。

    参数说明：
    :param db: 参数 db
    :param user: 参数 user
    :param explicit: 参数 explicit
    :return: 返回处理结果。
    """
    if explicit in ("cn", "global"):
        return explicit  # type: ignore[return-value]

    tenant = resolve_tenant_for_user(db, user)
    if tenant:
        ts = _safe_tenant_settings(tenant.settings)
        region = ts.get("storage_region")
        if region in ("cn", "global"):
            return region  # type: ignore[return-value]
        features = _plan_features(tenant)
        if "globalization" in features or "international" in features:
            return "global"
        return "cn"

    default = (settings.FILE_STORAGE_DEFAULT_REGION or "cn").strip().lower()
    return "global" if default == "global" else "cn"


def resolve_tenant_scope(
    db: Session,
    user: User,
    *,
    explicit_tenant_id: str | None = None,
) -> str:
    """resolve_tenant_scope。

    参数说明：
    :param db: 参数 db
    :param user: 参数 user
    :param explicit_tenant_id: 参数 explicit_tenant_id
    :return: 返回处理结果。
    """
    if explicit_tenant_id and user.role in ("admin", "super_admin"):
        return explicit_tenant_id.strip()
    tenant_id = resolve_tenant_id_for_user(db, user)
    return tenant_id or "platform"


def is_platform_media_admin(user: User) -> bool:
    """is_platform_media_admin。

    参数说明：
    :param user: 参数 user
    :return: 返回处理结果。
    """
    return user.role in ("admin", "super_admin")


def validate_platform_tenant_id(
    db: Session,
    user: User,
    tenant_id: str | None,
) -> str | None:
    """平台超管指定租户时校验；返回错误文案或 None。"""
    if not tenant_id:
        return None
    if not is_platform_media_admin(user):
        return "仅平台超管可指定租户"
    tid = tenant_id.strip()
    if tid == "platform":
        return None
    exists = db.query(Tenant.id).filter(Tenant.id == tid).first()
    if not exists:
        return f"租户不存在: {tid}"
    return None


def media_subdir_for_category(category: str) -> str:
    """media_subdir_for_category。

    参数说明：
    :param category: 参数 category
    :return: 返回处理结果。
    """
    return _MEDIA_SUBDIR.get(category, "uploads")


def object_key_for_upload(
    tenant_scope: str,
    file_id: str,
    filename: str,
    category: str,
) -> str:
    """object_key_for_upload。

    参数说明：
    :param tenant_scope: 参数 tenant_scope
    :param file_id: 参数 file_id
    :param filename: 参数 filename
    :param category: 参数 category
    :return: 返回处理结果。
    """
    subdir = media_subdir_for_category(category)
    if subdir == "images":
        return object_key_for_image(tenant_scope, file_id, filename)
    return object_key_for_tenant_media(tenant_scope, file_id, filename, subdir=subdir)


def _pick_backend(region: StorageRegion) -> StorageBackend:
    """_pick_backend。

    参数说明：
    :param region: 参数 region
    :return: 返回处理结果。
    """
    if region == "cn":
        return "qiniu" if qiniu_configured() else "local"
    return "r2" if r2_configured() else "local"


def get_storage_profile(
    db: Session,
    user: User,
    *,
    explicit_region: str | None = None,
) -> dict[str, Any]:
    """get_storage_profile。

    参数说明：
    :param db: 参数 db
    :param user: 参数 user
    :param explicit_region: 参数 explicit_region
    :return: 返回处理结果。
    """
    region = resolve_storage_region(db, user, explicit=explicit_region)
    backend = _pick_backend(region)
    cloud_ok = backend != "local"
    return {
        "storage_region": region,
        "storage_region_label": REGION_LABELS.get(region, region),
        "storage_backend": backend,
        "storage_backend_label": BACKEND_LABELS.get(backend, backend),
        "cloud_configured": cloud_ok,
        "tenant_scope": resolve_tenant_scope(db, user),
        "cn_available": qiniu_configured(),
        "global_available": r2_configured(),
    }


def load_meta() -> list[dict]:
    """load_meta。
    :return: 返回处理结果。
    """
    ensure_uploads_dir()
    if not os.path.exists(META_FILE):
        return []
    try:
        with open(META_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_meta(meta: list[dict]) -> None:
    """save_meta。

    参数说明：
    :param meta: 参数 meta
    :return: 返回处理结果。
    """
    ensure_uploads_dir()
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def filter_meta_for_user(
    meta: list[dict],
    db: Session,
    user: User,
    *,
    tenant_id: str | None = None,
) -> list[dict]:
    """按租户隔离文件元数据；平台超管可选 tenant_id 筛选。"""
    if user.role in ("admin", "super_admin"):
        if tenant_id:
            scope = tenant_id.strip()
            return [m for m in meta if str(m.get("tenant_id") or "") == scope]
        return meta
    scope = resolve_tenant_scope(db, user)
    return [m for m in meta if str(m.get("tenant_id") or "") == scope]


def tenant_scope_groups(meta: list[dict]) -> list[dict[str, Any]]:
    """汇总各租户前缀下的文件数量（供超管筛选）。"""
    counts: dict[str, int] = {}
    for row in meta:
        tid = str(row.get("tenant_id") or "").strip() or "unknown"
        counts[tid] = counts.get(tid, 0) + 1
    return [
        {"tenant_id": tid, "file_count": count}
        for tid, count in sorted(counts.items(), key=lambda x: (-x[1], x[0]))
    ]


def generate_file_id() -> str:
    """generate_file_id。
    :return: 返回处理结果。
    """
    return uuid.uuid4().hex[:12]


def _format_size(size_bytes: int) -> str:
    """_format_size。

    参数说明：
    :param size_bytes: 参数 size_bytes
    :return: 返回处理结果。
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    if size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def store_uploaded_bytes(
    db: Session,
    user: User,
    *,
    content: bytes,
    original_filename: str,
    content_type: str | None,
    file_id: str | None = None,
    explicit_region: str | None = None,
    explicit_tenant_id: str | None = None,
    prefer_local_storage: bool = False,
) -> dict[str, Any]:
    """store_uploaded_bytes。

    参数说明：
    :param db: 参数 db
    :param user: 参数 user
    :param content: 参数 content
    :param original_filename: 参数 original_filename
    :param content_type: 参数 content_type
    :param file_id: 参数 file_id
    :param explicit_region: 参数 explicit_region
    :param explicit_tenant_id: 参数 explicit_tenant_id
    :param prefer_local_storage: 参数 prefer_local_storage
    :return: 返回处理结果。
    """
    file_id = file_id or generate_file_id()
    region = resolve_storage_region(db, user, explicit=explicit_region)
    tenant_scope = resolve_tenant_scope(db, user, explicit_tenant_id=explicit_tenant_id)
    ext = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else ""
    mime = content_type or mimetypes.guess_type(original_filename)[0] or "application/octet-stream"
    category = _FILE_TYPE_CATEGORY.get(ext, "other")
    object_key = object_key_for_upload(tenant_scope, file_id, original_filename, category)
    now = datetime.utcnow().isoformat() + "Z"
    backend: StorageBackend = "local"
    url = ""
    saved_name = ""
    if not prefer_local_storage and region == "cn" and qiniu_configured():
        try:
            upload_bytes_to_qiniu(content, object_key, content_type=mime)
            url = qiniu_public_url(object_key)
            backend = "qiniu"
        except MediaQiniuError:
            backend = "local"
    elif not prefer_local_storage and region == "global" and r2_configured():
        try:
            upload_bytes_to_r2(content, object_key, content_type=mime)
            url = r2_public_url(object_key)
            backend = "r2"
        except MediaR2Error:
            backend = "local"

    if backend == "local":
        safe_filename = f"{file_id}_{original_filename.replace('/', '_')}"
        file_path = os.path.join(uploads_dir(), safe_filename)
        ensure_uploads_dir()
        with open(file_path, "wb") as f:
            f.write(content)
        saved_name = safe_filename
        url = f"/uploads/{safe_filename}"

    file_meta = {
        "id": file_id,
        "original_name": original_filename,
        "saved_name": saved_name,
        "object_key": object_key if backend != "local" else "",
        "size": len(content),
        "size_display": _format_size(len(content)),
        "mime_type": mime,
        "extension": ext,
        "category": _FILE_TYPE_CATEGORY.get(ext, "other"),
        "url": url,
        "storage_region": region,
        "storage_backend": backend,
        "storage_region_label": REGION_LABELS.get(region, region),
        "tenant_id": tenant_scope,
        "uploaded_by": user.username,
        "uploaded_at": now,
        "updated_at": now,
    }
    return file_meta


def delete_stored_record(record: dict[str, Any]) -> None:
    """delete_stored_record。

    参数说明：
    :param record: 参数 record
    :return: 返回处理结果。
    """
    backend = record.get("storage_backend") or "local"
    object_key = record.get("object_key") or ""
    saved_name = record.get("saved_name") or ""
    if backend == "qiniu" and object_key:
        delete_object_from_qiniu(object_key)
    elif backend == "r2" and object_key:
        delete_object_from_r2(object_key)

    if saved_name:
        file_path = os.path.join(uploads_dir(), saved_name)
        if os.path.exists(file_path):
            os.remove(file_path)
