# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""超管：平台产品图存储（七牛 / R2）开通与验收。"""

import uuid
from typing import Literal, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.admin_auth import get_current_super_admin
from app.core.config import settings
from app.core.database import get_db
from app.core.response import success_response
from app.models.system_config import SystemConfig
from app.models.user import User
from app.services.platform_storage_provision_service import (
    ProbeTarget,
    QiniuCredentials,
    R2Credentials,
    build_env_snippet,
    build_operator_checklist,
    build_platform_storage_status,
    mask_secret,
    verify_current,
    verify_qiniu,
    verify_r2,
)

router = APIRouter()

_SECRET_KEYS = frozenset({
    "QINIU_ACCESS_KEY",
    "QINIU_SECRET_KEY",
    "MEDIA_R2_ACCOUNT_ID",
    "MEDIA_R2_ACCESS_KEY_ID",
    "MEDIA_R2_SECRET_ACCESS_KEY",
})


class QiniuVerifyBody(BaseModel):
    access_key: str = Field(..., min_length=1)
    secret_key: str = Field(..., min_length=1)
    bucket: str = Field(..., min_length=1)
    public_base_url: str = Field(..., min_length=1)
    upload_host: str = "https://upload.qiniup.com"


class R2VerifyBody(BaseModel):
    account_id: str = Field(..., min_length=1)
    access_key_id: str = Field(..., min_length=1)
    secret_access_key: str = Field(..., min_length=1)
    bucket: str = Field(..., min_length=1)
    public_base_url: Optional[str] = None


class VerifyRequest(BaseModel):
    target: Literal["qiniu", "r2", "all"] = "all"
    qiniu: Optional[QiniuVerifyBody] = None
    r2: Optional[R2VerifyBody] = None


class ApplyRequest(BaseModel):
    target: Literal["qiniu", "r2", "all"] = "all"
    file_storage_default_region: Optional[Literal["cn", "global"]] = None
    qiniu: Optional[QiniuVerifyBody] = None
    r2: Optional[R2VerifyBody] = None
    verify: bool = True


def _mask_env_snippet(snippet: str) -> str:
    lines = []
    for line in snippet.splitlines():
        key, sep, value = line.partition("=")
        if sep and key.strip() in _SECRET_KEYS and value.strip():
            lines.append(f"{key}={mask_secret(value) or '****'}")
        else:
            lines.append(line)
    return "\n".join(lines)


def _upsert_system_config(db: Session, key: str, value: str) -> None:
    row = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if row:
        row.value = value
    else:
        db.add(SystemConfig(
            id=str(uuid.uuid4()),
            key=key,
            value=value,
            value_type="string",
            description="platform storage provision",
            is_public=False,
        ))


def _apply_qiniu(body: QiniuVerifyBody) -> dict:
    settings.QINIU_ACCESS_KEY = body.access_key.strip()
    settings.QINIU_SECRET_KEY = body.secret_key.strip()
    settings.QINIU_BUCKET = body.bucket.strip()
    settings.QINIU_PUBLIC_BASE_URL = body.public_base_url.strip()
    settings.QINIU_UPLOAD_HOST = (body.upload_host or "https://upload.qiniup.com").strip()
    return {
        "QINIU_ACCESS_KEY": body.access_key.strip(),
        "QINIU_SECRET_KEY": body.secret_key.strip(),
        "QINIU_BUCKET": body.bucket.strip(),
        "QINIU_PUBLIC_BASE_URL": body.public_base_url.strip(),
        "QINIU_UPLOAD_HOST": settings.QINIU_UPLOAD_HOST,
    }


def _apply_r2(body: R2VerifyBody) -> dict:
    settings.MEDIA_R2_ACCOUNT_ID = body.account_id.strip()
    settings.MEDIA_R2_ACCESS_KEY_ID = body.access_key_id.strip()
    settings.MEDIA_R2_SECRET_ACCESS_KEY = body.secret_access_key.strip()
    settings.MEDIA_R2_BUCKET = body.bucket.strip()
    settings.MEDIA_R2_PUBLIC_BASE_URL = (body.public_base_url or "").strip()
    return {
        "MEDIA_R2_ACCOUNT_ID": body.account_id.strip(),
        "MEDIA_R2_ACCESS_KEY_ID": body.access_key_id.strip(),
        "MEDIA_R2_SECRET_ACCESS_KEY": body.secret_access_key.strip(),
        "MEDIA_R2_BUCKET": body.bucket.strip(),
        "MEDIA_R2_PUBLIC_BASE_URL": settings.MEDIA_R2_PUBLIC_BASE_URL,
    }


def _masked_keys(applied: dict) -> dict:
    out = {}
    for k, v in applied.items():
        out[k] = mask_secret(v) if k in _SECRET_KEYS else v
    return out


@router.get("/status")
def storage_provision_status(admin: User = Depends(get_current_super_admin)):
    """storage_provision_status。

    参数说明：
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    _ = admin
    return success_response(build_platform_storage_status())


@router.get("/checklist")
def storage_provision_checklist(admin: User = Depends(get_current_super_admin)):
    """storage_provision_checklist。

    参数说明：
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    _ = admin
    return success_response({"items": build_operator_checklist()})


@router.get("/env-snippet")
def storage_provision_env_snippet(admin: User = Depends(get_current_super_admin)):
    """返回当前已加载配置的 env 片段（密钥打码）。"""
    _ = admin
    return success_response(
        {
            "snippet": _mask_env_snippet(build_env_snippet(include_placeholders=True)),
            "warning": "密钥已打码；完整密钥仅写入服务器 env，勿转发客户或提交 git",
        }
    )


@router.post("/verify-current")
def verify_current_storage(
    target: ProbeTarget = "all",
    admin: User = Depends(get_current_super_admin),
):
    """verify_current_storage。

    参数说明：
    :param target: 参数 target
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    _ = admin
    report = verify_current(target=target)
    return success_response(report)


@router.post("/verify")
def verify_storage_credentials(
    body: VerifyRequest,
    admin: User = Depends(get_current_super_admin),
):
    """用提交的密钥做上传探测（不落库）；配好 env 前可先验再写服务器。"""
    _ = admin
    results: list[dict] = []
    if body.target in ("qiniu", "all"):
        if body.qiniu:
            creds = QiniuCredentials(
                access_key=body.qiniu.access_key.strip(),
                secret_key=body.qiniu.secret_key.strip(),
                bucket=body.qiniu.bucket.strip(),
                public_base_url=body.qiniu.public_base_url.strip(),
                upload_host=(body.qiniu.upload_host or "https://upload.qiniup.com").strip(),
            )
            results.append(verify_qiniu(creds))
        else:
            results.append(
                {
                    "target": "qiniu",
                    "status": "skip",
                    "message": "未提交 qiniu 字段",
                }
            )

    if body.target in ("r2", "all"):
        if body.r2:
            creds = R2Credentials(
                account_id=body.r2.account_id.strip(),
                access_key_id=body.r2.access_key_id.strip(),
                secret_access_key=body.r2.secret_access_key.strip(),
                bucket=body.r2.bucket.strip(),
                public_base_url=(body.r2.public_base_url or "").strip(),
            )
            results.append(verify_r2(creds))
        else:
            results.append(
                {
                    "target": "r2",
                    "status": "skip",
                    "message": "未提交 r2 字段",
                }
            )

    statuses = {r.get("status") for r in results}
    overall = "fail" if "fail" in statuses else ("pass" if "pass" in statuses else "skip")
    return success_response({"overall": overall, "results": results})


@router.post("/apply")
def apply_storage_config(
    body: ApplyRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """写闭环：把存储配置落入 SystemConfig + 运行时 settings，可选复验。"""
    _ = admin
    applied: dict[str, str] = {}
    notes: list[str] = []

    if body.file_storage_default_region:
        settings.FILE_STORAGE_DEFAULT_REGION = body.file_storage_default_region
        applied["FILE_STORAGE_DEFAULT_REGION"] = body.file_storage_default_region
        notes.append("已设置默认分区")

    if body.target in ("qiniu", "all"):
        if body.qiniu:
            applied.update(_apply_qiniu(body.qiniu))
            notes.append("七牛配置已写入")
        elif body.target == "qiniu":
            notes.append("未提交 qiniu 字段")

    if body.target in ("r2", "all"):
        if body.r2:
            applied.update(_apply_r2(body.r2))
            notes.append("R2 配置已写入")
        elif body.target == "r2":
            notes.append("未提交 r2 字段")

    if not applied:
        return success_response(
            data={"applied": {}, "notes": notes},
            message="未提交可写入的配置",
        )

    for key, value in applied.items():
        _upsert_system_config(db, key, value)
    db.commit()

    verify_report = None
    if body.verify:
        verify_report = verify_current(target=body.target)

    return success_response(
        data={
            "applied": _masked_keys(applied),
            "notes": notes,
            "verify": verify_report,
            "env_snippet_masked": _mask_env_snippet(build_env_snippet(include_placeholders=True)),
        },
        message="存储配置已保存",
    )
