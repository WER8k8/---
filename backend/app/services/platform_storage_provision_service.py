# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""平台级产品图存储（七牛 / R2）开通、探测与验收 — 运维自动化。"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Any, Literal

import httpx
from minio import Minio
from minio.error import S3Error

from app.core.config import settings
from app.services.media_qiniu_service import qiniu_configured
from app.services.media_r2_service import r2_configured

logger = logging.getLogger(__name__)

ProbeTarget = Literal["qiniu", "r2", "all"]
ProbeStatus = Literal["pass", "fail", "skip", "warn"]

_PROBE_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


@dataclass(frozen=True)
class QiniuCredentials:
    access_key: str
    secret_key: str
    bucket: str
    public_base_url: str
    upload_host: str = "https://upload.qiniup.com"


@dataclass(frozen=True)
class R2Credentials:
    account_id: str
    access_key_id: str
    secret_access_key: str
    bucket: str
    public_base_url: str = ""


def mask_secret(value: str | None, *, visible: int = 4) -> str | None:
    """mask_secret。

    参数说明：
    :param value: 参数 value
    :param visible: 参数 visible
    :return: 返回处理结果。
    """
    text = (value or "").strip()
    if not text:
        return None
    if len(text) <= visible * 2:
        return "*" * len(text)
    return f"{text[:visible]}…{text[-visible:]}"


def qiniu_credentials_from_settings() -> QiniuCredentials | None:
    """qiniu_credentials_from_settings。
    :return: 返回处理结果。
    """
    if not qiniu_configured():
        return None
    return QiniuCredentials(
        access_key=settings.QINIU_ACCESS_KEY or "",
        secret_key=settings.QINIU_SECRET_KEY or "",
        bucket=settings.QINIU_BUCKET or "",
        public_base_url=settings.QINIU_PUBLIC_BASE_URL or "",
        upload_host=settings.QINIU_UPLOAD_HOST or "https://upload.qiniup.com",
    )


def r2_credentials_from_settings() -> R2Credentials | None:
    """r2_credentials_from_settings。
    :return: 返回处理结果。
    """
    if not r2_configured():
        return None
    return R2Credentials(
        account_id=settings.MEDIA_R2_ACCOUNT_ID or "",
        access_key_id=settings.MEDIA_R2_ACCESS_KEY_ID or "",
        secret_access_key=settings.MEDIA_R2_SECRET_ACCESS_KEY or "",
        bucket=settings.MEDIA_R2_BUCKET or "",
        public_base_url=settings.MEDIA_R2_PUBLIC_BASE_URL or "",
    )


def _qiniu_upload_token(creds: QiniuCredentials, object_key: str) -> str:
    """_qiniu_upload_token。

    参数说明：
    :param creds: 参数 creds
    :param object_key: 参数 object_key
    :return: 返回处理结果。
    """
    deadline = int(time.time()) + 3600
    policy = {"scope": f"{creds.bucket}:{object_key}", "deadline": deadline}
    encoded_policy = base64.urlsafe_b64encode(
        json.dumps(policy, separators=(",", ":")).encode()
    ).decode()
    sign = hmac.new(
        creds.secret_key.encode(),
        encoded_policy.encode(),
        hashlib.sha1,
    ).digest()
    encoded_sign = base64.urlsafe_b64encode(sign).decode()
    return f"{creds.access_key}:{encoded_sign}:{encoded_policy}"


def _qiniu_delete(creds: QiniuCredentials, object_key: str) -> None:
    """_qiniu_delete。

    参数说明：
    :param creds: 参数 creds
    :param object_key: 参数 object_key
    :return: 返回处理结果。
    """
    entry = base64.urlsafe_b64encode(f"{creds.bucket}:{object_key}".encode()).decode()
    path = f"/delete/{entry}"
    signing_str = f"{path}\n"
    sign = hmac.new(creds.secret_key.encode(), signing_str.encode(), hashlib.sha1).digest()
    token = f"{creds.access_key}:{base64.urlsafe_b64encode(sign).decode()}"
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(
            f"https://rs.qiniu.com{path}",
            headers={"Authorization": f"QBox {token}"},
        )
    if resp.status_code >= 400 and resp.status_code != 612:
        raise RuntimeError(f"七牛删除探测文件失败 HTTP {resp.status_code}: {resp.text[:160]}")


def verify_qiniu(creds: QiniuCredentials) -> dict[str, Any]:
    """上传 1×1 PNG 到 _platform-probe/ 并删除，验证 AK/SK/Bucket/域名。"""
    missing = [
        name
        for name, val in (
            ("access_key", creds.access_key),
            ("secret_key", creds.secret_key),
            ("bucket", creds.bucket),
            ("public_base_url", creds.public_base_url),
        )
        if not (val or "").strip()
    ]
    if missing:
        return {
            "target": "qiniu",
            "status": "fail",
            "message": f"缺少字段: {', '.join(missing)}",
        }

    object_key = f"_platform-probe/{int(time.time())}_{uuid.uuid4().hex[:8]}.png"
    token = _qiniu_upload_token(creds, object_key)
    upload_host = creds.upload_host.rstrip("/")
    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(
                upload_host,
                data={"token": token, "key": object_key},
                files={"file": ("probe.png", _PROBE_PNG, "image/png")},
            )
        if resp.status_code >= 400:
            hint = "检查 AK/SK、Bucket 名称、是否已完成实名认证"
            body = resp.text[:200]
            if "up-z1" in body or "up-z0" in body or "up-z2" in body:
                hint = "华北 Bucket 请设 QINIU_UPLOAD_HOST=https://up-z1.qiniup.com（见报错中的区域节点）"
            return {
                "target": "qiniu",
                "status": "fail",
                "message": f"上传失败 HTTP {resp.status_code}: {body}",
                "hint": hint,
            }
        public_url = f"{creds.public_base_url.rstrip('/')}/{object_key}"
        _qiniu_delete(creds, object_key)
        return {
            "target": "qiniu",
            "status": "pass",
            "message": "上传与删除探测成功",
            "sample_public_url": public_url,
            "bucket": creds.bucket,
        }
    except Exception as exc:
        logger.warning("七牛探测失败: %s", exc)
        return {
            "target": "qiniu",
            "status": "fail",
            "message": str(exc),
            "hint": "常见原因：未完成实名、Bucket 不存在、CDN 域名未绑定 HTTPS",
        }


def verify_r2(creds: R2Credentials) -> dict[str, Any]:
    """verify_r2。

    参数说明：
    :param creds: 参数 creds
    :return: 返回处理结果。
    """
    missing = [
        name
        for name, val in (
            ("account_id", creds.account_id),
            ("access_key_id", creds.access_key_id),
            ("secret_access_key", creds.secret_access_key),
            ("bucket", creds.bucket),
        )
        if not (val or "").strip()
    ]
    if missing:
        return {
            "target": "r2",
            "status": "fail",
            "message": f"缺少字段: {', '.join(missing)}",
        }

    object_key = f"_platform-probe/{int(time.time())}_{uuid.uuid4().hex[:8]}.png"
    endpoint = f"{creds.account_id}.r2.cloudflarestorage.com"
    try:
        client = Minio(
            endpoint,
            access_key=creds.access_key_id,
            secret_key=creds.secret_access_key,
            secure=True,
            region="auto",
        )
        from io import BytesIO
        client.put_object(
            creds.bucket,
            object_key,
            BytesIO(_PROBE_PNG),
            length=len(_PROBE_PNG),
            content_type="image/png",
        )
        client.remove_object(creds.bucket, object_key)
        public_base = (creds.public_base_url or "").rstrip("/")
        sample_url = f"{public_base}/{object_key}" if public_base else None
        return {
            "target": "r2",
            "status": "pass",
            "message": "上传与删除探测成功",
            "sample_public_url": sample_url,
            "bucket": creds.bucket,
            "public_base_configured": bool(public_base),
            "warn": None if public_base else "未配置 MEDIA_R2_PUBLIC_BASE_URL，外链需后续补 CDN 域名",
        }
    except S3Error as exc:
        return {
            "target": "r2",
            "status": "fail",
            "message": f"R2 S3 错误: {exc.code} — {exc.message}",
            "hint": "检查 Account ID、API Token（S3 兼容）、Bucket 名称",
        }
    except Exception as exc:
        logger.warning("R2 探测失败: %s", exc)
        return {
            "target": "r2",
            "status": "fail",
            "message": str(exc),
        }


def verify_current(*, target: ProbeTarget = "all") -> dict[str, Any]:
    """verify_current。

    参数说明：
    :param target: 参数 target
    :return: 返回处理结果。
    """
    results: list[dict[str, Any]] = []
    if target in ("qiniu", "all"):
        creds = qiniu_credentials_from_settings()
        if creds:
            results.append(verify_qiniu(creds))
        else:
            results.append(
                {
                    "target": "qiniu",
                    "status": "skip",
                    "message": "七牛未配置（QINIU_* 为空）",
                }
            )
    if target in ("r2", "all"):
        creds = r2_credentials_from_settings()
        if creds:
            r = verify_r2(creds)
            if r.get("status") == "pass" and r.get("warn"):
                r["status"] = "warn"
            results.append(r)
        else:
            results.append(
                {
                    "target": "r2",
                    "status": "skip",
                    "message": "R2 未配置（MEDIA_R2_* 为空）",
                }
            )
    overall = _aggregate_probe_status(results)
    return {"overall": overall, "results": results}


def _aggregate_probe_status(results: list[dict[str, Any]]) -> ProbeStatus:
    """_aggregate_probe_status。

    参数说明：
    :param results: 参数 results
    :return: 返回处理结果。
    """
    statuses = {r.get("status") for r in results}
    if "fail" in statuses:
        return "fail"
    if "warn" in statuses:
        return "warn"
    if statuses == {"skip"}:
        return "skip"
    if "pass" in statuses:
        return "pass"
    return "skip"


def build_platform_storage_status() -> dict[str, Any]:
    """build_platform_storage_status。
    :return: 返回处理结果。
    """
    qiniu_ok = qiniu_configured()
    r2_ok = r2_configured()
    default_region = (settings.FILE_STORAGE_DEFAULT_REGION or "cn").strip().lower()
    prod = (settings.ENVIRONMENT or "").strip().lower() == "production"
    cn_ready = qiniu_ok
    global_ready = r2_ok
    default_ready = cn_ready if default_region == "cn" else global_ready
    return {
        "environment": settings.ENVIRONMENT,
        "file_storage_default_region": default_region,
        "qiniu": {
            "configured": qiniu_ok,
            "access_key_masked": mask_secret(settings.QINIU_ACCESS_KEY),
            "bucket": settings.QINIU_BUCKET or None,
            "public_base_url": settings.QINIU_PUBLIC_BASE_URL or None,
            "upload_host": settings.QINIU_UPLOAD_HOST,
        },
        "r2": {
            "configured": r2_ok,
            "account_id_masked": mask_secret(settings.MEDIA_R2_ACCOUNT_ID),
            "access_key_id_masked": mask_secret(settings.MEDIA_R2_ACCESS_KEY_ID),
            "bucket": settings.MEDIA_R2_BUCKET or None,
            "public_base_url": settings.MEDIA_R2_PUBLIC_BASE_URL or None,
        },
        "readiness": {
            "cn_product_images": "ready" if cn_ready else "local_fallback",
            "global_product_images": "ready" if global_ready else "local_fallback",
            "default_region_ready": default_ready,
            "production_risk": prod and not default_ready,
        },
        "customer_note": "客户开户无需注册七牛/Cloudflare；平台配好 QINIU_* / MEDIA_R2_* 后租户直接上传。",
    }


def build_operator_checklist() -> list[dict[str, Any]]:
    """运维一次性清单：实名步骤需人工，其余可脚本/API 验收。"""
    qiniu_ok = qiniu_configured()
    r2_ok = r2_configured()
    has_public = bool((settings.QINIU_PUBLIC_BASE_URL or "").strip())
    return [
        {
            "id": "qiniu_signup",
            "title": "注册七牛云账号",
            "owner": "platform_ops",
            "automatable": False,
            "done": qiniu_ok,
            "url": "https://portal.qiniu.com/signup",
            "detail": "使用平台企业邮箱注册，勿用客户身份。",
        },
        {
            "id": "qiniu_kyc",
            "title": "七牛实名认证（企业/个人）",
            "owner": "platform_ops",
            "automatable": False,
            "done": qiniu_ok,
            "url": "https://portal.qiniu.com/user/profile",
            "detail": "未完成实名无法创建 Bucket / 上传。法律要求，无法代码代填。",
        },
        {
            "id": "qiniu_bucket",
            "title": "创建 Bucket + 绑定 CDN 域名（HTTPS）",
            "owner": "platform_ops",
            "automatable": False,
            "done": qiniu_ok and has_public,
            "url": "https://portal.qiniu.com/kodo/bucket",
            "detail": "记录 Bucket 名称与 CDN 域名，填入 QINIU_BUCKET / QINIU_PUBLIC_BASE_URL。",
        },
        {
            "id": "qiniu_keys",
            "title": "创建 AK/SK 并写入服务器 QINIU_*",
            "owner": "platform_ops",
            "automatable": True,
            "done": qiniu_ok,
            "url": "https://portal.qiniu.com/user/key",
            "detail": "运行 scripts/setup-platform-storage.ps1 或超管「存储开通」页验收。",
        },
        {
            "id": "qiniu_verify",
            "title": "七牛上传/删除探测通过",
            "owner": "platform_ops",
            "automatable": True,
            "done": False,
            "url": None,
            "detail": "POST /api/v1/super-admin/storage-provision/verify-current",
        },
        {
            "id": "r2_signup",
            "title": "注册 Cloudflare 并开通 R2",
            "owner": "platform_ops",
            "automatable": False,
            "done": r2_ok,
            "url": "https://dash.cloudflare.com/sign-up",
            "detail": "海外租户产品图；与视频工厂 MEDIA_R2_* 共用即可。",
        },
        {
            "id": "r2_keys",
            "title": "配置 MEDIA_R2_* 并验收",
            "owner": "platform_ops",
            "automatable": True,
            "done": r2_ok,
            "url": "https://dash.cloudflare.com/",
            "detail": "R2 → Manage R2 API Tokens → S3 兼容密钥。",
        },
    ]


def build_env_snippet(
    *,
    qiniu: QiniuCredentials | None = None,
    r2: R2Credentials | None = None,
    include_placeholders: bool = True,
) -> str:
    """build_env_snippet。

    参数说明：
    :param qiniu: 参数 qiniu
    :param r2: 参数 r2
    :param include_placeholders: 参数 include_placeholders
    :return: 返回处理结果。
    """
    lines = ["# 产品图片空间 — 平台一次性配置（勿提交 git）", f"FILE_STORAGE_DEFAULT_REGION={settings.FILE_STORAGE_DEFAULT_REGION or 'cn'}", ""]
    q = qiniu or qiniu_credentials_from_settings()
    if q or include_placeholders:
        lines.extend(
            [
                "QINIU_ACCESS_KEY=" + (q.access_key if q else ""),
                "QINIU_SECRET_KEY=" + (q.secret_key if q else ""),
                "QINIU_BUCKET=" + (q.bucket if q else ""),
                "QINIU_PUBLIC_BASE_URL=" + (q.public_base_url if q else ""),
                "QINIU_UPLOAD_HOST=" + ((q.upload_host if q else None) or "https://upload.qiniup.com"),
                "",
            ]
        )
    r = r2 or r2_credentials_from_settings()
    if r or include_placeholders:
        lines.extend(
            [
                "MEDIA_R2_ACCOUNT_ID=" + (r.account_id if r else ""),
                "MEDIA_R2_ACCESS_KEY_ID=" + (r.access_key_id if r else ""),
                "MEDIA_R2_SECRET_ACCESS_KEY=" + (r.secret_access_key if r else ""),
                "MEDIA_R2_BUCKET=" + (r.bucket if r else ""),
                "MEDIA_R2_PUBLIC_BASE_URL=" + (r.public_base_url if r else ""),
            ]
        )
    return "\n".join(lines)


def production_storage_startup_message() -> str | None:
    """生产环境若默认分区仍走本地磁盘，返回告警文案。"""
    if (settings.ENVIRONMENT or "").strip().lower() != "production":
        return None
    region = (settings.FILE_STORAGE_DEFAULT_REGION or "cn").strip().lower()
    if region == "cn" and not qiniu_configured():
        return (
            "【存储告警】生产环境 FILE_STORAGE_DEFAULT_REGION=cn 但 QINIU_* 未配置，"
            "产品图将落本地磁盘（重启可能丢失）。请运行 scripts/setup-platform-storage.ps1"
        )
    if region == "global" and not r2_configured():
        return (
            "【存储告警】生产环境 FILE_STORAGE_DEFAULT_REGION=global 但 MEDIA_R2_* 未配置，"
            "产品图将落本地磁盘。请配置 R2 或改默认分区为 cn。"
        )
    return None
