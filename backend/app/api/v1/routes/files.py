# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""文件管理路由 - 上传、列表、删除（国内七牛 / 海外 R2 分轨）"""

import os
from typing import Optional
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.response import error_response, success_response
from app.core.security import get_current_user, get_current_user_optional
from app.core.tenant_access import is_platform_admin, is_tenant_staff
from app.core.uploads_path import migrate_legacy_uploads
from app.db.session import get_db
from app.models.user import User
from app.services.product_image_storage_service import (
    delete_stored_record,
    filter_meta_for_user,
    get_storage_profile,
    is_platform_media_admin,
    load_meta,
    save_meta,
    store_uploaded_bytes,
    tenant_scope_groups,
    validate_platform_tenant_id,
)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/files"
ROUTE_TAGS = ["文件管理"]

router = APIRouter()

migrate_legacy_uploads()

# 允许的文件类型（由文件扩展名决定）
ALLOWED_EXTENSIONS = {
    "jpg", "jpeg", "png", "webp", "gif", "svg",
    "pdf", "doc", "docx",
    "mp4", "webm", "avi", "mov", "mkv", "flv", "wmv",
}

FILE_TYPE_CATEGORY = {
    "jpg": "image", "jpeg": "image", "png": "image", "webp": "image",
    "gif": "image", "svg": "image",
    "pdf": "document", "doc": "document", "docx": "document",
    "mp4": "video", "webm": "video", "avi": "video", "mov": "video",
    "mkv": "video", "flv": "video", "wmv": "video",
}

MAX_UPLOAD_BYTES = max(1, int(getattr(settings, "MAX_UPLOAD_SIZE_MB", 50) or 50)) * 1024 * 1024
VIDEO_EXTENSIONS = {"mp4", "webm", "avi", "mov", "mkv", "flv", "wmv"}
MAX_VIDEO_UPLOAD_BYTES = max(
    MAX_UPLOAD_BYTES,
    int(getattr(settings, "MAX_VIDEO_UPLOAD_SIZE_MB", 500) or 500) * 1024 * 1024,
)


def _max_upload_bytes_for_ext(ext: str) -> int:
    """
    处理 _max_upload_bytes_for_ext 相关业务逻辑。

    :param ext: 入参 (str)。

    :return: 返回 int 类型的结果。
    """
    if ext in VIDEO_EXTENSIONS:
        return MAX_VIDEO_UPLOAD_BYTES
    return MAX_UPLOAD_BYTES


def _can_manage_files(user: User) -> bool:
    """
    处理 _can_manage_files 相关业务逻辑。

    :param user: 入参 (User)。

    :return: 返回 bool 类型的结果。
    """
    return is_tenant_staff(user)


def _validate_extension(filename: str) -> tuple[str, str | None]:
    """
    处理 _validate_extension 相关业务逻辑。

    :param filename: 入参 (str)。

    :return: 返回 tuple[str, str | None] 类型的结果。
    """
    # 路径遍历防护：拦截 ../ 或 \\ 等路径字符
    import re
    if re.search(r"[/\\\.]{2,}", filename) or ".." in filename:
        return "", "文件名包含非法路径字符"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        return ext, f"不支持的文件类型 .{ext}，允许: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
    return ext, None


@router.get("/storage-profile")
def file_storage_profile(
    storage_region: Optional[str] = Query(None, description="预览指定分区：cn | global"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """当前用户产品图存储分区（国内七牛 / 海外 R2）。"""
    if not _can_manage_files(current_user):
        return error_response(403, "权限不足")
    profile = get_storage_profile(db, current_user, explicit_region=storage_region)
    return success_response(data=profile)


@router.post("/upload")
def upload_file(
    file: UploadFile = File(...),
    storage_region: Optional[str] = Form(None, description="超管可选：cn | global"),
    tenant_id: Optional[str] = Form(None, description="超管可选：代指定租户上传"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """上传文件 — 按租户/区域写入国内（七牛）或海外（R2）存储。"""
    if not _can_manage_files(current_user):
        return error_response(403, "权限不足")

    original_filename = file.filename or "unnamed"
    ext, err = _validate_extension(original_filename)
    if err:
        return error_response(400, err)

    # P2-8: Content-Type 校验（防止客户端伪造）
    if file.content_type:
        import mimetypes
        expected_mime = mimetypes.guess_type(original_filename)[0]
        if expected_mime and file.content_type != expected_mime:
            return error_response(400, f"Content-Type 不匹配：期望 {expected_mime}，实际 {file.content_type}")

    if not is_platform_admin(current_user) and storage_region:
        return error_response(403, "仅平台超管可指定存储分区")

    tenant_err = validate_platform_tenant_id(db, current_user, tenant_id)
    if tenant_err:
        return error_response(400, tenant_err)

    try:
        # BUG-12 修复：流式读取，避免将整个文件加载到内存
        max_bytes = _max_upload_bytes_for_ext(ext)
        content_size = 0
        chunks = []
        while True:
            chunk = file.file.read(8192)  # 8KB chunks
            if not chunk:
                break
            content_size += len(chunk)
            if content_size > max_bytes:
                file.file.close()
                return error_response(400, f"文件大小超过 {max_bytes // (1024 * 1024)}MB 限制")
            chunks.append(chunk)
        content = b"".join(chunks)
    except Exception as e:
        return error_response(500, f"读取文件失败: {str(e)}")
    finally:
        if file.file.closed:
            pass
        else:
            file.file.close()

    file_meta = store_uploaded_bytes(
        db,
        current_user,
        content=content,
        original_filename=original_filename,
        content_type=file.content_type,
        explicit_region=storage_region,
        explicit_tenant_id=tenant_id.strip() if tenant_id else None,
    )
    meta = load_meta()
    meta.insert(0, file_meta)
    save_meta(meta)
    return success_response(data=file_meta, message="上传成功")


@router.post("/upload-multi")
def upload_files(
    files: list[UploadFile] = File(...),
    storage_region: Optional[str] = Form(None),
    tenant_id: Optional[str] = Form(None, description="超管可选：代指定租户上传"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量上传文件"""
    if not _can_manage_files(current_user):
        return error_response(403, "权限不足")

    if not is_platform_admin(current_user) and storage_region:
        return error_response(403, "仅平台超管可指定存储分区")

    tenant_err = validate_platform_tenant_id(db, current_user, tenant_id)
    if tenant_err:
        return error_response(400, tenant_err)

    results = []
    errors = []
    for file in files:
        original_filename = file.filename or "unnamed"
        ext, err = _validate_extension(original_filename)
        if err:
            errors.append({"filename": original_filename, "error": err})
            continue

        try:
            # BUG-12 修复：流式读取，避免将整个文件加载到内存
            max_bytes = _max_upload_bytes_for_ext(ext)
            content_size = 0
            chunks = []
            while True:
                chunk = file.file.read(8192)  # 8KB chunks
                if not chunk:
                    break
                content_size += len(chunk)
                if content_size > max_bytes:
                    file.file.close()
                    errors.append({"filename": original_filename, "error": f"超过 {max_bytes // (1024 * 1024)}MB 限制"})
                    continue
                chunks.append(chunk)
            content = b"".join(chunks)
        except Exception as e:
            errors.append({"filename": original_filename, "error": str(e)})
            continue
        finally:
            if file.file.closed:
                pass
            else:
                file.file.close()

        file_meta = store_uploaded_bytes(
            db,
            current_user,
            content=content,
            original_filename=original_filename,
            content_type=file.content_type,
            explicit_region=storage_region,
            explicit_tenant_id=tenant_id.strip() if tenant_id else None,
        )
        results.append(file_meta)

    if results:
        meta = load_meta()
        meta = results + meta
        save_meta(meta)

    return success_response(data={"success": results, "errors": errors})


@router.get("/")
def list_files(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    file_type: Optional[str] = Query(None, description="分类筛选: image/document/video/other"),
    storage_region: Optional[str] = Query(None, description="分区筛选: cn | global"),
    tenant_id: Optional[str] = Query(None, description="超管可选：按租户筛选"),
    search: Optional[str] = Query(None, description="按文件名搜索"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取文件列表 - 支持分页、分类筛选、搜索"""
    if not _can_manage_files(current_user):
        return error_response(403, "权限不足")

    tenant_err = validate_platform_tenant_id(db, current_user, tenant_id)
    if tenant_err:
        return error_response(400, tenant_err)

    meta = filter_meta_for_user(
        load_meta(),
        db,
        current_user,
        tenant_id=tenant_id.strip() if tenant_id else None,
    )
    if file_type and file_type in ("image", "document", "video", "other"):
        meta = [m for m in meta if m.get("category") == file_type]

    if storage_region in ("cn", "global"):
        meta = [m for m in meta if m.get("storage_region", "local") == storage_region]

    if search:
        keyword = search.lower()
        meta = [m for m in meta if keyword in m.get("original_name", "").lower()]

    total = len(meta)
    start = (page - 1) * page_size
    items = meta[start : start + page_size]
    return success_response(data=items, total=total, page=page, page_size=page_size)


@router.delete("/{file_id}")
def delete_file(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除文件 - 删除云对象/本地文件和元数据"""
    if not _can_manage_files(current_user):
        return error_response(403, "权限不足")

    meta = filter_meta_for_user(load_meta(), db, current_user)
    target = next((m for m in meta if m.get("id") == file_id), None)
    if not target:
        return error_response(404, "文件不存在")

    try:
        delete_stored_record(target)
    except OSError as e:
        return error_response(500, f"文件删除失败: {str(e)}")

    all_meta = load_meta()
    save_meta([m for m in all_meta if m.get("id") != file_id])
    return success_response(message="删除成功")


@router.get("/stats")
def get_file_stats(
    tenant_id: Optional[str] = Query(None, description="超管可选：按租户筛选"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取文件统计信息"""
    if not _can_manage_files(current_user):
        return error_response(403, "权限不足")

    tenant_err = validate_platform_tenant_id(db, current_user, tenant_id)
    if tenant_err:
        return error_response(400, tenant_err)

    meta = filter_meta_for_user(
        load_meta(),
        db,
        current_user,
        tenant_id=tenant_id.strip() if tenant_id else None,
    )
    total_files = len(meta)
    total_size = sum(m.get("size", 0) for m in meta)
    image_count = sum(1 for m in meta if m.get("category") == "image")
    document_count = sum(1 for m in meta if m.get("category") == "document")
    video_count = sum(1 for m in meta if m.get("category") == "video")
    other_count = sum(1 for m in meta if m.get("category") == "other")
    cn_count = sum(1 for m in meta if m.get("storage_region") == "cn")
    global_count = sum(1 for m in meta if m.get("storage_region") == "global")
    payload: dict = {
        "total_files": total_files,
        "total_size": total_size,
        "total_size_display": _format_size(total_size),
        "image_count": image_count,
        "document_count": document_count,
        "video_count": video_count,
        "other_count": other_count,
        "cn_count": cn_count,
        "global_count": global_count,
        "storage_profile": get_storage_profile(db, current_user),
    }
    if is_platform_media_admin(current_user):
        payload["tenant_scopes"] = tenant_scope_groups(load_meta())

    return success_response(data=payload)


def _format_size(size_bytes: int) -> str:
    """
    处理 _format_size 相关业务逻辑。

    :param size_bytes: 入参 (int)。

    :return: 返回 str 类型的结果。
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def _allowed_asset_proxy_hosts() -> set[str]:
    """
    处理 _allowed_asset_proxy_hosts 相关业务逻辑。

    :return: 返回 set[str] 类型的结果。
    """
    hosts: set[str] = set()
    for raw in (
        getattr(settings, "QINIU_PUBLIC_BASE_URL", None),
        getattr(settings, "MEDIA_R2_PUBLIC_BASE_URL", None),
    ):
        if not raw:
            continue
        try:
            hosts.add(urlparse(str(raw).strip()).hostname or "")
        except (ValueError, TypeError, Exception):
            continue
    hosts.update({"hb-bkt.clouddn.com", "clouddn.com", "qiniucdn.com", "qnssl.com"})
    return hosts


@router.get("/asset-proxy")
def file_asset_proxy(
    url: str = Query(..., min_length=8),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """同源代理外链媒体，避免 Admin WebView ORB 拦截七牛/CDN 图片。
    允许未认证访问（用于 <img>/<video> 标签），但限制允许的域名。

    SECURITY: 
    - 未认证用户只能访问白名单域名的媒体资源
    - 已认证用户需要文件管理权限才能访问非白名单域名
    - 限制文件大小和内容类型防止 SSRF 和恶意文件代理
    """
    try:
        parsed = urlparse(url.strip())
    except (ValueError, TypeError, Exception):
        return error_response(400, "无效 URL")

    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return error_response(400, "仅支持 http(s) 外链")

    host = parsed.hostname.lower()
    allowed = _allowed_asset_proxy_hosts()
    # SECURITY: 检查域名白名单
    is_allowed_host = host in allowed or any(host.endswith(f".{h}") for h in allowed if "." in h)
    if not is_allowed_host:
        # SECURITY: 非白名单域名需要认证且有文件管理权限
        if not current_user or not _can_manage_files(current_user):
            return error_response(403, "权限不足：无权访问该媒体资源")

    try:
        with httpx.Client(timeout=20.0, follow_redirects=True) as client:
            upstream = client.get(url.strip())
        if upstream.status_code >= 400:
            return error_response(upstream.status_code, "上游媒体不可达")
        
        # SECURITY: 验证内容类型，只允许媒体类型
        media_type = upstream.headers.get("content-type") or "application/octet-stream"
        allowed_types = ("image/", "video/", "audio/", "application/pdf")
        if not any(media_type.startswith(t) for t in allowed_types):
            return error_response(403, "不允许的媒体类型")
        
        # SECURITY: 限制文件大小（最大 10MB）
        content_length = int(upstream.headers.get("content-length", len(upstream.content)))
        if content_length > 10 * 1024 * 1024:
            return error_response(413, "文件大小超过限制")

        return Response(content=upstream.content, media_type=media_type)
    except httpx.HTTPError as exc:
        return error_response(502, f"媒体代理失败: {exc}")
