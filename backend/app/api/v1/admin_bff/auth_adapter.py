# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""认证 BFF — HTTP 薄层；转发 legacy auth，输出 Vben 契约"""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from starlette.responses import JSONResponse

from app.api.v1.admin_bff.bridge import forward_success_or_legacy, to_vben_token_pair
from app.api.v1.admin_bff.tenant_lookup import search_tenants_for_login
from app.api.v1.routes.auth import login as auth_login
from app.api.v1.routes.auth import refresh_token as auth_refresh
from app.api.v1.routes.auth import LogoutResponse
from app.core.jwt_key_rotation import jwt_key_rotation_service
from app.core.jwt_cookie import clear_auth_cookies, extract_token_from_cookie
from app.core.access_token_blacklist import revoke_access_token
from app.core.response import success_response
from app.db.session import get_db
from app.schemas.auth import LoginRequest, TokenRefreshRequest

router = APIRouter()


class UacLoginBody(BaseModel):
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., min_length=1)
    tenant_code: str | None = None
    captcha_id: str | None = None
    captcha_code: str | None = None


@router.post("/login")
def bff_login(body: UacLoginBody, request: Request, db: Session = Depends(get_db)):
    """bff_login。

    参数说明：
    :param body: 参数 body
    :param request: 参数 request
    :param db: 参数 db
    :return: 返回处理结果。
    """
    login_data = LoginRequest(username_or_email=body.username, password=body.password)
    result = auth_login(login_data, request, db)
    return forward_success_or_legacy(result, to_vben_token_pair)


@router.post("/refresh")
def bff_refresh(body: TokenRefreshRequest, request: Request, db: Session = Depends(get_db)):
    """bff_refresh。

    参数说明：
    :param body: 参数 body
    :param request: 参数 request
    :param db: 参数 db
    :return: 返回处理结果。
    """
    result = auth_refresh(body, request, db)
    return forward_success_or_legacy(result, to_vben_token_pair)


@router.post("/logout")
def bff_logout(request: Request):
    """bff_logout。

    参数说明：
    :param request: 参数 request
    :return: 返回处理结果。
    """
    import logging
    logger = logging.getLogger(__name__)
    # 从 Cookie 提取 token（bff 不走 Bearer Header）
    token = extract_token_from_cookie(request)
    logger.info("bff_logout: token present=%s", bool(token))
    if token:
        try:
            payload = jwt_key_rotation_service.decode_token(token)
            jti = payload.get("jti")
            exp = payload.get("exp")
            if jti:
                exp_ts = float(exp) if isinstance(exp, (int, float)) else None
                revoke_access_token(str(jti), exp_ts)
                logger.info("bff_logout: revoked jti=%s", jti)
        except Exception as e:
            logger.warning("bff_logout: token decode/revoke failed: %s", e)
    resp = success_response(data=LogoutResponse(message="登出成功"))
    json_resp = JSONResponse(content=resp.model_dump(mode="json"))
    clear_auth_cookies(json_resp)
    logger.info("bff_logout: success")
    return json_resp


@router.get("/captcha")
def bff_captcha_stub():
    """bff_captcha_stub。
    :return: 返回处理结果。
    """
    return success_response(
        data={"captcha_id": "stub", "image": "", "enabled": False},
        message="验证码未启用",
    )


@router.get("/tenant/search")
def bff_tenant_search(code: str = "", db: Session = Depends(get_db)):
    """bff_tenant_search。

    参数说明：
    :param code: 参数 code
    :param db: 参数 db
    :return: 返回处理结果。
    """
    return success_response(data=search_tenants_for_login(db, code))
