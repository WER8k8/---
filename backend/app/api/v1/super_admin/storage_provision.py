# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""超管：平台产品图存储（七牛 / R2）开通与验收。"""

from typing import Literal, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.admin_auth import get_current_super_admin
from app.core.response import success_response
from app.models.user import User
from app.services.platform_storage_provision_service import (
    ProbeTarget,
    QiniuCredentials,
    R2Credentials,
    build_env_snippet,
    build_operator_checklist,
    build_platform_storage_status,
    verify_current,
    verify_qiniu,
    verify_r2,
)

router = APIRouter()


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
    """返回当前已加载配置的 env 片段（含明文密钥，仅超管）。"""
    _ = admin
    return success_response(
        {
            "snippet": build_env_snippet(include_placeholders=True),
            "warning": "含密钥明文，勿转发客户或提交 git",
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
