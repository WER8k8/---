# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""认证模块路由"""

import hashlib
import logging
import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials
import jwt
from sqlalchemy.orm import Session

from app.core.access_token_blacklist import (is_access_token_revoked,
                                              revoke_access_token)
from app.core.config import settings
from app.core.login_bruteforce import (check_login_allowed,
                                       client_ip_from_request,
                                       record_login_failure,
                                       record_login_success)
from app.core.refresh_token_blacklist import (is_refresh_key_revoked,
                                              refresh_token_revocation_key,
                                              revoke_refresh_key)
from app.core.response import APIResponse, error_response, success_response
from app.core.security import (create_access_token, decode_refresh_payload,
                               get_current_user, get_password_hash,
                               security_scheme, verify_password)
from app.core.jwt_cookie import clear_auth_cookies, set_auth_cookies
from app.db.session import get_db
from app.models.user import EmailVerification, ThirdPartyLogin, User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (EmailLoginRequest, EmailVerificationRequest,
                              EmailVerificationResponse, LoginRequest,
                              LogoutResponse, OAuthAuthorizeResponse,
                              ThirdPartyLoginRequest, ThirdPartyLoginResponse,
                              TokenRefreshRequest, TokenResponse)
from app.schemas.user import ChangePasswordRequest, UserResponse
from app.services.oauth_binding_service import (bind_oauth_account,
                                                list_user_bindings,
                                                unbind_oauth_account)
from app.services.oauth_login import (SUPPORTED_OAUTH_PROVIDERS,
                                      build_oauth_authorize,
                                      oauth_providers_status,
                                      resolve_oauth_identity)
from app.services.email_service import email_service
from app.services.unified_admin_login import resolve_user_for_unified_login


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/auth", tags=["认证"])
logger = logging.getLogger("uj-admin.auth")

# ── Per-email rate limit for verification codes (3/hour) ──
# BUG-13 修复：从内存 dict 迁移到 Redis，支持多 worker 环境
import time
from collections import defaultdict

_email_code_store: dict[str, list[float]] = defaultdict(list)
_email_code_ttl_store: dict[str, float] = {}
_EMAIL_CODE_LIMIT = 3
_EMAIL_CODE_WINDOW = 3600  # 1 hour

# Redis-backed rate limit (BUG-13)
try:
    from app.core.cache import redis_client
    _EMAIL_CODE_REDIS_KEY_PREFIX = "rate:email_code:"
    _EMAIL_CODE_REDIS_TTL = 3600 * 4  # 4小时过期
    _use_redis_rate_limit = redis_client is not None
except (ImportError, Exception) as exc:
    logger = logging.getLogger(__name__)
    logger.warning("Redis rate limit 初始化失败，降级到内存计数: %s", exc)
    _use_redis_rate_limit = False


def _check_email_code_rate(email: str) -> None:
    """
    处理 _check_email_code_rate 相关业务逻辑。

    :param email: 入参 (str)。

    :return: 返回 None 类型的结果。

    :raises HTTPException: 当相应错误条件触发时抛出。
    """
    if _use_redis_rate_limit:
        key = f"{_EMAIL_CODE_REDIS_KEY_PREFIX}{email}"
        try:
            count = redis_client.incr(key)
            if count == 1:
                redis_client.expire(key, _EMAIL_CODE_REDIS_TTL)
            if count > _EMAIL_CODE_LIMIT:
                raise HTTPException(429, "验证码发送过于频繁，请 1 小时后再试")
            return
        except HTTPException:
            raise
        except Exception as redis_exc:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("Redis 限流故障，降级到内存计数: %s (%s)", email, redis_exc)

    now = time.time()
    window = _email_code_store.get(email, [])
    _email_code_store[email] = [t for t in window if now - t < _EMAIL_CODE_WINDOW]
    # 内存回退：用窗口内条数限流，禁止引用未定义的 count
    if len(_email_code_store[email]) >= _EMAIL_CODE_LIMIT:
        raise HTTPException(429, "验证码发送过于频繁，请 1 小时后再试")
    _email_code_store[email].append(now)


def _build_token_pair(user: User, matrix_admin_id: int = None):
    """构建 access + refresh token 对，返回 TokenResponse 数据"""
    access_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    access_body = {"sub": str(user.id), "role": user.role, "scopes": [user.role]}
    refresh_body = {"sub": str(user.id), "scopes": ["refresh"]}
    if matrix_admin_id is not None:
        access_body["mid"] = matrix_admin_id
        refresh_body["mid"] = matrix_admin_id

    return TokenResponse(
        access_token=create_access_token(data=access_body, expires_delta=access_expires),
        refresh_token=create_access_token(data=refresh_body, expires_delta=refresh_expires),
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )


def _token_json_response(token_resp: TokenResponse, user: User) -> JSONResponse:
    """
    处理 _token_json_response 相关业务逻辑。

    :param token_resp: 入参 (TokenResponse)。
    :param user: 入参 (User)。

    :return: 返回 JSONResponse 类型的结果。
    """
    resp = JSONResponse(
        content={"code": 0, "message": "success",
                 "data": token_resp.model_dump(mode="json")},
    )
    set_auth_cookies(resp, token_resp.access_token, token_resp.refresh_token, user)
    return resp


@router.post("/login", response_model=APIResponse[TokenResponse])
def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """统一管理员登录：主库 users + 可选 SEO 矩阵 admin_users（SQLite）贯通，签发同一 JWT。"""
    ip = client_ip_from_request(request)
    blocked = check_login_allowed(ip, login_data.username_or_email)
    if blocked:
        return error_response(blocked[0], blocked[1])

    user, matrix_admin_id = resolve_user_for_unified_login(
        db, login_data.username_or_email, login_data.password)
    if not user or not user.is_active:
        record_login_failure(ip, login_data.username_or_email)
        from app.core.i18n import resolve_locale, t
        locale = resolve_locale(request.headers.get("accept-language"))
        return error_response(401, t("auth.bad_credentials", locale))

    record_login_success(ip, login_data.username_or_email)
    token_resp = _build_token_pair(user, matrix_admin_id)
    token_resp.portals = None
    token_resp.force_password_change = bool(getattr(user, "is_default_password", False))
    # FIX-22: 返回 JSONResponse + 设置 HttpOnly Cookie
    return _token_json_response(token_resp, user)


def _normalized_auth_login_path() -> str:
    """
    处理 _normalized_auth_login_path 相关业务逻辑。

    :return: 返回 str 类型的结果。
    """
    seg = (settings.AUTH_LOGIN_ROUTE or "login").strip().strip("/")
    if not seg or ".." in seg or not re.fullmatch(r"[A-Za-z0-9/_-]+", seg):
        return "/login"
    return f"/{seg}"


_AUTH_LOGIN_ALIAS = _normalized_auth_login_path()
if _AUTH_LOGIN_ALIAS != "/login":
    router.add_api_route(
        _AUTH_LOGIN_ALIAS,
        login,
        methods=["POST"],
        response_model=APIResponse[TokenResponse],
        operation_id="auth_unified_login_alias",
        include_in_schema=False,
    )


@router.post("/refresh", response_model=APIResponse[TokenResponse])
def refresh_token(
        refresh_data: TokenRefreshRequest,
        request: Request,
        db: Session = Depends(get_db)):
    """刷新访问令牌（轮转 refresh，旧 refresh 一次性作废）。

    支持两种方式传入 refresh_token：
    1. JSON Body: {"refresh_token": "..."}
    2. HttpOnly Cookie: uj_refresh_token
    """
    refresh_token_value = refresh_data.refresh_token
    if not refresh_token_value:
        # FIX-22: 从 HttpOnly Cookie 读取
        from app.core.jwt_cookie import extract_refresh_token_from_cookie
        refresh_token_value = extract_refresh_token_from_cookie(request)
    if not refresh_token_value:
        return error_response(401, "无效的刷新令牌")

    payload = decode_refresh_payload(refresh_token_value)
    key, exp_ts = (None, None)
    if payload:
        key, exp_ts = refresh_token_revocation_key(refresh_token_value, payload)
    body_token_dead = not payload or is_refresh_key_revoked(key)
    if body_token_dead and refresh_data.refresh_token:
        # Body 携带的 refresh_token 已轮换/撤销（前端 sessionStorage 残留旧值）时，
        # 回退尝试 HttpOnly Cookie 里的最新 token，避免误杀会话
        from app.core.jwt_cookie import extract_refresh_token_from_cookie
        cookie_token = extract_refresh_token_from_cookie(request)
        if cookie_token and cookie_token != refresh_token_value:
            cookie_payload = decode_refresh_payload(cookie_token)
            if cookie_payload:
                c_key, c_exp = refresh_token_revocation_key(cookie_token, cookie_payload)
                if not is_refresh_key_revoked(c_key):
                    refresh_token_value, payload, key, exp_ts = cookie_token, cookie_payload, c_key, c_exp
                    body_token_dead = False
    if body_token_dead or not payload:
        return error_response(401, "无效的刷新令牌")
    if is_refresh_key_revoked(key):
        return error_response(401, "刷新令牌已失效")

    user_id = str(payload.get("sub"))
    matrix_admin_id = payload.get("mid")
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    if not user or not user.is_active:
        return error_response(401, "登录状态无效，请重新登录")

    revoke_refresh_key(key, exp_ts)
    token_resp = _build_token_pair(user, matrix_admin_id)
    token_resp.portals = None
    # FIX-22: 设置新的 HttpOnly Cookie
    return _token_json_response(token_resp, user)


@router.post("/logout", response_model=APIResponse[LogoutResponse])
def logout(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    request: Request = None,
):
    """用户登出：将当前 access token 的 jti 加入黑名单使其即时失效。"""
    # 从 Header 或 Cookie 提取 token
    token = credentials.credentials if credentials else None
    if not token and request:
        from app.core.jwt_cookie import extract_token_from_cookie
        token = extract_token_from_cookie(request)
    
    if token:
        try:
            from app.core.jwt_key_rotation import jwt_key_rotation_service
            payload = jwt_key_rotation_service.decode_token(token)
            jti = payload.get("jti")
            exp = payload.get("exp")
            if jti:
                exp_ts = float(exp) if isinstance(exp, (int, float)) else None
                revoke_access_token(str(jti), exp_ts)
                logger.info("登出: jti=%s 已加入黑名单", jti)
        except (jwt.InvalidTokenError, Exception) as exc:
            logger = logging.getLogger(__name__)
            logger.warning("JWT 处理失败（可能是无效令牌）: %s", exc)
    
    # FIX-22: 清除 HttpOnly Cookies
    resp = success_response(data=LogoutResponse(message="登出成功"))
    clear_auth_cookies(resp)
    return resp


@router.post("/change-password", response_model=APIResponse)
def change_password(
    password_data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """修改密码（首次登录强制改密码时使用）"""
    if not verify_password(password_data.old_password, current_user.hashed_password):
        return error_response(400, "旧密码不正确")

    current_user.hashed_password = get_password_hash(password_data.new_password)
    current_user.is_default_password = False
    db.commit()
    return success_response(message="密码修改成功")


@router.post("/send-email-code",
             response_model=APIResponse[EmailVerificationResponse])
def send_email_code(
        request: EmailVerificationRequest,
        db: Session = Depends(get_db)):
    """发送邮箱验证码"""
    email = request.email
    # Per-email rate limit: 3 codes per hour
    _check_email_code_rate(email)
    expire_time = datetime.now(timezone.utc) + timedelta(minutes=5)
    code = "".join(secrets.choice("0123456789ABCDEFGHJKLMNPQRSTUVWXYZ") for _ in range(8))
    code_hash = hashlib.sha256(code.encode()).hexdigest()
    existing_verification = (
        db.query(EmailVerification).filter(
            EmailVerification.email == email,
            EmailVerification.used == False).first())

    if existing_verification:
        db.delete(existing_verification)

    new_verification = EmailVerification(
        email=email, code=code_hash, expires_at=expire_time)
    db.add(new_verification)
    db.commit()
    mailed = email_service.send_verification_code(email, code)
    dev_code = None
    if settings.ENVIRONMENT == "development" or settings.DEBUG:
        dev_code = code

    if not mailed and settings.ENVIRONMENT == "production":
        return error_response(503, "邮件服务未配置，无法发送验证码（请配置 SMTP_*）")

    msg = "验证码已发送至邮箱" if mailed else "验证码已生成（开发环境或未配置 SMTP）"
    return success_response(
        data=EmailVerificationResponse(
            message=msg,
            expires_in=300,
            dev_code=dev_code,
        )
    )


@router.post("/login-by-email", response_model=APIResponse[TokenResponse])
def login_by_email(request: EmailLoginRequest, db: Session = Depends(get_db)):
    """邮箱验证码登录"""
    input_code_hash = hashlib.sha256(request.code.encode()).hexdigest()
    verification = (
        db.query(EmailVerification)
        .filter(
            EmailVerification.email == request.email,
            EmailVerification.code == input_code_hash,
            EmailVerification.used == False,
            EmailVerification.expires_at > datetime.now(timezone.utc),
        )
        .with_for_update()
        .first()
    )
    if not verification:
        return error_response(401, "验证码无效或已过期")

    verification.used = True
    db.commit()
    user_repo = UserRepository(db)
    user = user_repo.get_by_email(request.email)
    if not user:
        # 安全策略：不再自动创建用户，防止任意邮箱注册获取后台访问权限
        logger.warning(
            "[Email Login] 邮箱 %s 未关联任何用户，拒绝自动创建",
            request.email,
        )
        return error_response(
            403,
            "该邮箱尚未注册，请先联系管理员创建账户后再使用邮箱登录",
        )

    # FIX-22: 设置 HttpOnly Cookie
    token_resp = _build_token_pair(user)
    resp = JSONResponse(
        content={"code": 0, "message": "success", "data": token_resp.model_dump(mode="json")},
    )
    set_auth_cookies(resp, token_resp.access_token, token_resp.refresh_token, user)
    return resp


def _token_response_for_user(user: User, new_user: bool = False):
    """
    处理 _token_response_for_user 相关业务逻辑。

    :param user: 入参 (User)。
    :param new_user: 入参 (bool)。

    :return: 返回处理结果（或 None）。
    """
    token_resp = _build_token_pair(user)
    third_party_data = ThirdPartyLoginResponse(
        access_token=token_resp.access_token,
        refresh_token=token_resp.refresh_token,
        token_type=token_resp.token_type,
        expires_in=token_resp.expires_in,
        user=token_resp.user,
        new_user=new_user,
    )
    resp = JSONResponse(
        content={"code": 0, "message": "success", "data": third_party_data.model_dump(mode="json")},
    )
    # FIX-22: 设置 HttpOnly Cookie
    set_auth_cookies(resp, token_resp.access_token, token_resp.refresh_token, user)
    return resp


@router.get("/oauth/providers")
def list_oauth_providers():
    """管理端登录页：展示各第三方登录是否已配置。"""
    from app.services.oauth_login import oauth_providers_status_detail

    detail = oauth_providers_status_detail()
    return success_response(
        data={
            "providers": {k: bool(v.get("enabled")) for k, v in detail.items()},
            "detail": detail,
            "redirect_uri": (settings.OAUTH_REDIRECT_URI or "").strip() or None,
            "dev_bypass": False if settings.is_production else bool(
                settings.OAUTH_DEV_BYPASS
                or settings.ENVIRONMENT == "development"
            ),
            "checklist": "docs/ops/external-integration-keys-checklist.md",
        }
    )


@router.get("/oauth/{provider}/authorize",
            response_model=APIResponse[OAuthAuthorizeResponse])
def oauth_authorize(provider: str, state: Optional[str] = None):
    """获取第三方 OAuth 授权跳转地址（QQ / 微信 / 飞书 / 钉钉）。"""
    p = provider.lower()
    if p not in SUPPORTED_OAUTH_PROVIDERS:
        return error_response(400, "不支持的第三方登录方式")
    try:
        url, st = build_oauth_authorize(p, state)
    except ValueError as e:
        key = str(e)
        if key == "oauth_not_configured":
            return error_response(
                503, "该登录方式尚未配置，请在 backend/.env 填写对应 AppId/Secret")
        return error_response(400, "无法生成授权链接")
    return success_response(
        data=OAuthAuthorizeResponse(
            authorize_url=url,
            state=st,
            provider=p))


@router.post("/third-party-login",
             response_model=APIResponse[ThirdPartyLoginResponse])
def third_party_login(
    request: ThirdPartyLoginRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):
    """第三方登录（QQ / 微信 / 飞书 / 钉钉）。

    流程：
    1. 校验 provider 合法性
    2. 用 code 从平台换取 provider_id + 用户昵称
    3. 查找绑定记录 → 签发 JWT
    4. 开发模式：自动绑定 admin 账号
    5. 生产模式：未绑定则拒绝，引导用户先登录后绑定
    """
    provider = request.provider.lower()
    ip = client_ip_from_request(http_request)
    # ── 限流：第三方登录 5次/分钟/IP（防暴力尝试）──
    blocked = check_login_allowed(ip, f"oauth:{provider}")
    if blocked:
        return error_response(blocked[0], blocked[1])

    if provider not in SUPPORTED_OAUTH_PROVIDERS:
        return error_response(400, "不支持的第三方登录方式")

    # ── code → 身份解析 ──
    try:
        provider_id, nickname_hint = resolve_oauth_identity(provider, request.code)
    except ValueError as e:
        record_login_failure(ip, f"oauth:{provider}")
        key = str(e)
        if key == "oauth_not_configured":
            return error_response(503, "该登录方式尚未配置 OAuth 应用")
        if key == "missing_code":
            return error_response(400, "缺少授权码")
        # 包含平台错误描述的透传
        if ": " in key:
            _, detail = key.split(": ", 1)
            return error_response(401, f"第三方授权失败: {detail}")
        return error_response(401, "第三方授权失败，请重试")

    now = datetime.now(timezone.utc)
    existing = _handle_existing_binding(db, provider, provider_id, ip, now)
    if existing is not None:
        return existing

    dev_resp = _handle_dev_auto_bind(db, provider, provider_id, now, ip)
    if dev_resp is not None:
        return dev_resp

    # 未绑定：拒绝登录
    record_login_failure(ip, f"oauth:{provider}")
    logger.warning(
        "[OAuth Login] 未绑定 %s 账号 %s... 拒绝登录",
        provider, provider_id[:12],
    )
    return error_response(
        403,
        "该第三方账号尚未绑定管理后台用户，请先用用户名密码登录后进入「个人设置→账号绑定」完成关联",
    )


def _handle_existing_binding(
    db: Session,
    provider: str,
    provider_id: str,
    ip: str,
    now,
) -> object:
    """查找已有绑定并直接签发令牌；无绑定返回 None，用户异常时返回错误响应。

    :param db: 数据库会话。
    :param provider: 第三方平台标识。
    :param provider_id: 平台返回的用户唯一标识。
    :param ip: 客户端 IP，用于登录成功记录。
    :param now: 当前 UTC 时间，用于更新绑定记录。
    :return: 命中绑定返回令牌响应；用户异常返回错误响应；未命中返回 None。
    """
    binding = (
        db.query(ThirdPartyLogin)
        .filter(
            ThirdPartyLogin.provider == provider,
            ThirdPartyLogin.provider_id == provider_id,
        )
        .first()
    )
    if not binding:
        return None
    user = db.query(User).filter(User.id == binding.user_id).first()
    if not user or not user.is_active:
        return error_response(401, "用户不存在或已被禁用")
    binding.updated_at = now
    db.commit()
    record_login_success(ip, f"oauth:{provider}")
    logger.info(
        "[OAuth Login] 用户 %s 通过 %s 登录 (provider_id=%s...)",
        user.username[:1] + "***", provider, provider_id[:12],
    )
    return _token_response_for_user(user, new_user=False)


def _handle_dev_auto_bind(
    db: Session,
    provider: str,
    provider_id: str,
    now,
    ip: str,
):
    """开发模式下将 dev_ 前缀身份自动绑定并登录 admin；未命中返回 None。

    :param db: 数据库会话。
    :param provider: 第三方平台标识。
    :param provider_id: 平台返回的用户唯一标识。
    :param now: 当前 UTC 时间。
    :param ip: 客户端 IP，用于登录成功记录。
    :return: 命中开发模式自动绑定时返回令牌响应；否则返回 None。
    """
    admin_link = db.query(User).filter(User.username == "admin").first()
    if (
        admin_link
        and admin_link.is_active
        and provider_id.startswith("dev_")
        and not settings.is_production
        and (
            settings.OAUTH_DEV_BYPASS
            or settings.ENVIRONMENT == "development"
        )
    ):
        db.add(
            ThirdPartyLogin(
                id=str(uuid.uuid4()),
                user_id=admin_link.id,
                provider=provider,
                provider_id=provider_id,
                created_at=now,
                updated_at=now,
            )
        )
        db.commit()
        record_login_success(ip, f"oauth:{provider}")
        logger.info(
            "[OAuth Login] dev 模式自动绑定 admin ← %s",
            provider,
        )
        return _token_response_for_user(admin_link, new_user=False)
    return None


@router.get("/oauth/bindings")
def get_oauth_bindings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """当前用户已绑定的第三方账号。"""
    return success_response(data=list_user_bindings(db, str(current_user.id)))


@router.post("/oauth/bind")
def post_oauth_bind(
    request: ThirdPartyLoginRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """登录状态下绑定第三方账号（QQ / 微信 / 飞书 / 钉钉）。"""
    try:
        row = bind_oauth_account(db, current_user, request.provider, request.code)
    except ValueError as exc:
        key = str(exc)
        if key == "unsupported_provider":
            return error_response(400, "不支持的第三方登录方式")
        if key == "already_bound_other":
            return error_response(409, "该第三方账号已绑定其他用户，请先解绑原账号")
        if key == "oauth_not_configured":
            return error_response(503, "该登录方式尚未配置 OAuth 应用")
        if key == "missing_code":
            return error_response(400, "缺少授权码")
        # 透传平台错误描述
        if ": " in key:
            _, detail = key.split(": ", 1)
            return error_response(401, f"第三方授权失败: {detail}")
        return error_response(401, "第三方授权失败，请重试")
    return success_response(
        data={"provider": row.provider},
        message="绑定成功",
    )


@router.delete("/oauth/bindings/{provider}")
def delete_oauth_binding(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """解绑第三方账号。"""
    p = provider.lower()
    if p not in SUPPORTED_OAUTH_PROVIDERS:
        return error_response(400, "不支持的第三方登录方式")
    if not unbind_oauth_account(db, str(current_user.id), p):
        return error_response(404, "未找到绑定记录")
    return success_response(message="已解绑")
