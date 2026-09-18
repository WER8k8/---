# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""第三方 OAuth 登录：授权 URL 生成与 code 换身份。

支持平台：QQ互联 | 微信开放平台 | 飞书 | 钉钉

QQ 互联 OAuth2.0 文档：https://wiki.connect.qq.com/
微信开放平台 文档：https://developers.weixin.qq.com/doc/oplatform/

v2 增强：
- QQ: 完善 token 交换（兼容 text/plain 回调格式）、获取用户信息（昵称/头像）
- 微信: 完善 token 交换、获取用户信息（昵称/头像/unionid）、错误码映射
- 飞书/钉钉: 保持原有逻辑不变
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import re
import secrets
import urllib.parse
from typing import Optional, Tuple

import httpx

from app.core.config import settings

logger = logging.getLogger("uj-admin.oauth")

# ── 常量 ──────────────────────────────────────────────────

SUPPORTED_OAUTH_PROVIDERS = frozenset({"qq", "wechat", "feishu", "dingtalk"})

# QQ 互联错误码 → 中文描述
_QQ_ERROR_MAP: dict[int, str] = {
    100000: "缺少参数 response_type 或 response_type 非法",
    100001: "缺少参数 client_id",
    100002: "缺少参数 client_secret",
    100003: "http head 中缺少 Authorization",
    100004: "缺少参数 grant_type",
    100005: "缺少参数 code",
    100006: "缺少 refresh token",
    100007: "缺少 access token",
    100009: "client_secret 非法",
    100010: "回调地址不匹配",
    100011: "APP ID 不存在",
    100012: "client_secret 未经授权",
    100013: "access_token 过期",
    100014: "access_token 无效",
    100015: "access_token 未授权",
    100016: "grant_type 不是 authorization_code/refresh_token",
}

# 微信开放平台错误码 → 中文描述
_WECHAT_ERROR_MAP: dict[int, str] = {
    -1: "系统繁忙，请稍后重试",
    0: "请求成功",
    40001: "AppSecret 错误或 access_token 无效",
    40002: "不合法的凭证类型",
    40003: "不合法的 OpenID",
    40029: "code 无效或已过期",
    40030: "refresh_token 无效",
    40163: "code 已被使用",
    40125: "AppSecret 错误",
    41001: "缺少 access_token 参数",
    41002: "缺少 appid 参数",
    41003: "缺少 refresh_token 参数",
    42001: "access_token 超时",
    42002: "refresh_token 超时",
    48001: "API 未授权",
}


# ── 日志脱敏 ──────────────────────────────────────────────

_SENSITIVE_BODY_KEYS = frozenset(
    {"access_token", "accessToken", "refresh_token", "openid", "unionid", "token", "secret", "app_secret"}
)


def _mask_body(body) -> dict:
    """对 OAuth 响应体脱敏：敏感键只保留是否存在，其余原样返回，防止日志泄露 token/openid。"""
    if not isinstance(body, dict):
        return {"<type>": type(body).__name__}
    return {k: ("<masked>" if k in _SENSITIVE_BODY_KEYS else v) for k, v in body.items()}


# ── 重定向 URI ────────────────────────────────────────────

def _redirect_uri() -> str:
    """_redirect_uri。
    :return: 返回处理结果。
    """
    base = (settings.OAUTH_REDIRECT_URI or "").strip()
    if base:
        return base.rstrip("/")
    front = (settings.FRONTEND_URL or "http://localhost:5173").rstrip("/")
    return f"{front}/login/oauth-callback"


def _oauth_dev_mode_enabled() -> bool:
    """开发模式仅在非生产环境下允许。生产环境强制禁用，即使 .env 误配。"""
    if settings.is_production:
        return False
    return bool(
        settings.OAUTH_DEV_BYPASS
        or settings.ENVIRONMENT == "development"
    )


def _dev_authorize_url(provider: str, state: str) -> str:
    """_dev_authorize_url。

    参数说明：
    :param provider: 参数 provider
    :param state: 参数 state
    :return: 返回处理结果。
    """
    q = urllib.parse.urlencode(
        {
            "provider": provider,
            "code": f"dev:{provider}",
            "state": state,
        }
    )
    return f"{_redirect_uri()}?{q}"


# ── 渠道配置检查 ──────────────────────────────────────────

def _provider_configured(provider: str) -> bool:
    """_provider_configured。

    参数说明：
    :param provider: 参数 provider
    :return: 返回处理结果。
    """
    if provider == "feishu":
        return bool(settings.FEISHU_APP_ID.strip() and settings.FEISHU_APP_SECRET.strip())
    if provider == "dingtalk":
        return bool(settings.DINGTALK_APP_ID.strip() and settings.DINGTALK_APP_SECRET.strip())
    if provider == "qq":
        return bool(settings.QQ_APP_ID.strip() and settings.QQ_APP_KEY.strip())
    if provider == "wechat":
        return bool(settings.WECHAT_OPEN_APP_ID.strip() and settings.WECHAT_OPEN_APP_SECRET.strip())
    return False


def oauth_providers_status() -> dict[str, bool]:
    """各渠道是否已配置（开发环境未配凭据时也可点击走 dev 回调）。"""
    dev_ok = _oauth_dev_mode_enabled()
    return {
        p: _provider_configured(p) or dev_ok
        for p in sorted(SUPPORTED_OAUTH_PROVIDERS)
    }


# ── 授权 URL 构建 ─────────────────────────────────────────

def build_oauth_authorize(
    provider: str, state: Optional[str] = None
) -> Tuple[str, str]:
    """返回 (authorize_url, state)。

    Raises:
        ValueError("unsupported_provider"): 不支持的渠道
        ValueError("oauth_not_configured"): 渠道未配置
    """
    p = provider.lower()
    if p not in SUPPORTED_OAUTH_PROVIDERS:
        raise ValueError("unsupported_provider")

    st = (state or "").strip() or secrets.token_urlsafe(24)
    if settings.OAUTH_DEV_BYPASS or (
        settings.ENVIRONMENT == "development" and not _provider_configured(p)
    ):
        return _dev_authorize_url(p, st), st

    redirect = urllib.parse.quote(_redirect_uri(), safe="")
    if p == "feishu":
        app_id = settings.FEISHU_APP_ID.strip()
        if not app_id:
            raise ValueError("oauth_not_configured")
        url = (
            "https://accounts.feishu.cn/open-apis/authen/v1/authorize"
            f"?app_id={urllib.parse.quote(app_id)}"
            f"&redirect_uri={redirect}"
            f"&state={urllib.parse.quote(st)}"
        )
        return url, st

    if p == "dingtalk":
        app_id = settings.DINGTALK_APP_ID.strip()
        if not app_id:
            raise ValueError("oauth_not_configured")
        url = (
            "https://login.dingtalk.com/oauth2/auth"
            f"?client_id={urllib.parse.quote(app_id)}"
            "&response_type=code"
            "&scope=openid"
            f"&state={urllib.parse.quote(st)}"
            f"&redirect_uri={redirect}"
        )
        return url, st

    if p == "qq":
        app_id = settings.QQ_APP_ID.strip()
        if not app_id:
            raise ValueError("oauth_not_configured")
        # QQ 互联：scope=get_user_info 获取用户昵称和头像
        url = (
            "https://graph.qq.com/oauth2.0/authorize"
            "?response_type=code"
            f"&client_id={urllib.parse.quote(app_id)}"
            f"&redirect_uri={redirect}"
            f"&state={urllib.parse.quote(st)}"
            "&scope=get_user_info"
        )
        return url, st

    if p == "wechat":
        app_id = settings.WECHAT_OPEN_APP_ID.strip()
        if not app_id:
            raise ValueError("oauth_not_configured")
        # 微信开放平台：scope=snsapi_login（网站应用）
        url = (
            "https://open.weixin.qq.com/connect/qrconnect"
            f"?appid={urllib.parse.quote(app_id)}"
            f"&redirect_uri={redirect}"
            "&response_type=code"
            "&scope=snsapi_login"
            f"&state={urllib.parse.quote(st)}#wechat_redirect"
        )
        return url, st

    raise ValueError("oauth_not_configured")


# ── 身份解析（code → provider_id）────────────────────────
#
# 注意：以下 exchange 函数每次调用创建独立的 httpx.Client(timeout=20.0)。
# 对于 OAuth 登录这种低频场景这是可接受的。如果是高频 API 调用，
# 应使用共享的 httpx.Client（模块级或通过依赖注入），以复用连接池、
# 减少 TCP 握手开销。

def resolve_oauth_identity(
    provider: str, code: str
) -> Tuple[str, Optional[str]]:
    """用授权 code 解析第三方唯一 ID。

    Returns:
        (provider_id, email_hint) — email_hint 仅部分平台支持

    Raises:
        ValueError("missing_code"): code 为空
        ValueError("oauth_not_configured"): 渠道未配置
        ValueError("qq_token_failed" / "wechat_token_failed" / ...): 平台返回错误
    """
    p = provider.lower()
    raw_code = (code or "").strip()
    if not raw_code:
        raise ValueError("missing_code")

    if raw_code.startswith("dev:"):
        if not _oauth_dev_mode_enabled():
            raise ValueError("dev_oauth_disabled")
        suffix = raw_code.split(":", 1)[1] if ":" in raw_code else p
        if p == "wechat":
            try:
                from app.services.founder_wechat_service import (
                    expected_founder_wechat_provider_id,
                    normalize_founder_wechat_id,
                )
                expected = expected_founder_wechat_provider_id()
                if expected and normalize_founder_wechat_id(suffix) == expected:
                    return expected, None
            except Exception:
                pass
        return f"dev_{p}_{suffix}", None

    # 生产模式
    if p == "feishu":
        return _exchange_feishu(raw_code)
    if p == "dingtalk":
        return _exchange_dingtalk(raw_code)
    if p == "qq":
        return _exchange_qq(raw_code)
    if p == "wechat":
        return _exchange_wechat(raw_code)

    raise ValueError("unsupported_provider")


# ═══════════════════════════════════════════════════════════
# 飞书（保持原有逻辑）
# ═══════════════════════════════════════════════════════════

def _exchange_feishu(code: str) -> Tuple[str, Optional[str]]:
    """_exchange_feishu。

    参数说明：
    :param code: 参数 code
    :return: 返回处理结果。
    """
    app_id = settings.FEISHU_APP_ID.strip()
    secret = settings.FEISHU_APP_SECRET.strip()
    if not app_id or not secret:
        raise ValueError("oauth_not_configured")

    redirect = _redirect_uri()
    with httpx.Client(timeout=20.0) as client:
        r = client.post(
            f"{settings.FEISHU_API_BASE_URL.rstrip('/')}/authen/v1/oidc/access_token",
            json={
                "grant_type": "authorization_code",
                "code": code,
                "app_id": app_id,
                "app_secret": secret,
                "redirect_uri": redirect,
            },
        )
        r.raise_for_status()
        body = r.json()
    if body.get("code") != 0:
        raise ValueError(body.get("msg") or "feishu_token_failed")
    data = body.get("data") or {}
    open_id = data.get("open_id") or data.get("union_id")
    if not open_id:
        raise ValueError("feishu_open_id_missing")
    return f"feishu_{open_id}", data.get("email")


# ═══════════════════════════════════════════════════════════
# 钉钉（保持原有逻辑）
# ═══════════════════════════════════════════════════════════

def _exchange_dingtalk(code: str) -> Tuple[str, Optional[str]]:
    """_exchange_dingtalk。

    参数说明：
    :param code: 参数 code
    :return: 返回处理结果。
    """
    app_id = settings.DINGTALK_APP_ID.strip()
    secret = settings.DINGTALK_APP_SECRET.strip()
    if not app_id or not secret:
        raise ValueError("oauth_not_configured")

    redirect = _redirect_uri()
    with httpx.Client(timeout=20.0) as client:
        tr = client.post(
            "https://api.dingtalk.com/v1.0/oauth2/userAccessToken",
            json={
                "clientId": app_id,
                "clientSecret": secret,
                "code": code,
                "grantType": "authorization_code",
                "redirectUri": redirect,
            },
        )
        tr.raise_for_status()
        token_body = tr.json()
        access = token_body.get("accessToken")
        if not access:
            raise ValueError("dingtalk_token_failed")
        ur = client.get(
            "https://api.dingtalk.com/v1.0/contact/users/me",
            headers={"x-acs-dingtalk-access-token": access},
        )
        ur.raise_for_status()
        user = ur.json()
    union_id = user.get("unionId") or user.get("openId")
    if not union_id:
        raise ValueError("dingtalk_union_id_missing")
    return f"dingtalk_{union_id}", user.get("email")


# ═══════════════════════════════════════════════════════════
# QQ 互联 OAuth2.0（v2 增强版）
# ═══════════════════════════════════════════════════════════

def _exchange_qq(code: str) -> Tuple[str, Optional[str]]:
    """QQ 互联 code → access_token → openid → 用户信息。

    QQ 互联响应格式特殊：
    - token 接口可能返回 JSON（fmt=json）或 text/plain callback 包装
    - openid 接口同样可能返回 callback 包装
    """
    app_id = settings.QQ_APP_ID.strip()
    key = settings.QQ_APP_KEY.strip()
    if not app_id or not key:
        raise ValueError("oauth_not_configured")

    redirect = urllib.parse.quote(_redirect_uri(), safe="")
    with httpx.Client(timeout=20.0) as client:
        # ── Step 1: code → access_token ──
        logger.info("[QQ OAuth] Exchanging code for access_token...")
        tr = client.get(
            "https://graph.qq.com/oauth2.0/token",
            params={
                "grant_type": "authorization_code",
                "client_id": app_id,
                "client_secret": key,
                "code": code,
                "redirect_uri": _redirect_uri(),
                "fmt": "json",
            },
        )
        tr.raise_for_status()
        token_body = _parse_qq_response(tr.text)
        # 检查错误
        if "error" in token_body:
            err_code = token_body.get("error")
            err_desc = token_body.get("error_description", "")
            err_cn = _QQ_ERROR_MAP.get(err_code, f"未知错误({err_code})")
            logger.error("[QQ OAuth] Token 交换失败: code=%s desc=%s", err_code, err_desc)
            raise ValueError(f"qq_token_failed: {err_cn}")

        access = token_body.get("access_token")
        if not access:
            logger.error("[QQ OAuth] Token 响应缺少 access_token: %s", _mask_body(token_body))
            raise ValueError("qq_token_failed: 未获取到 access_token")

        logger.info(
            "[QQ OAuth] Token 获取成功 (expires_in=%ss)",
            token_body.get("expires_in", "?"),
        )
        # ── Step 2: access_token → openid ──
        logger.info("[QQ OAuth] Fetching openid...")
        openid_r = client.get(
            "https://graph.qq.com/oauth2.0/me",
            params={"access_token": access, "fmt": "json"},
        )
        openid_r.raise_for_status()
        openid_body = _parse_qq_response(openid_r.text)
        if "error" in openid_body:
            err_code = openid_body.get("error")
            err_desc = openid_body.get("error_description", "")
            logger.error("[QQ OAuth] OpenID 获取失败: code=%s desc=%s", err_code, err_desc)
            raise ValueError(f"qq_openid_failed: {err_desc or err_code}")

        openid = openid_body.get("openid")
        if not openid:
            logger.error("[QQ OAuth] OpenID 响应缺少 openid: %s", _mask_body(openid_body))
            raise ValueError("qq_openid_missing")

        logger.info("[QQ OAuth] OpenID: %s...", openid[:8])
        # ── Step 3: openid + access_token → 用户信息（昵称+头像）──
        nickname = _fetch_qq_user_info(client, access, openid, app_id)

    provider_id = f"qq_{openid}"
    return provider_id, nickname


def _parse_qq_response(text: str) -> dict:
    """解析 QQ 互联响应（兼容 callback+JSON 和纯 JSON 两种格式）。

    QQ 互联部分接口返回: callback( {...} );
    而非纯 JSON。
    """
    text = (text or "").strip()
    # 去掉 callback 包装
    m = re.match(r"^\s*\w+\s*\(\s*(.+)\s*\)\s*;?\s*$", text, re.DOTALL)
    if m:
        text = m.group(1).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # 兼容 URL 参数格式: access_token=XXX&expires_in=7776000&refresh_token=XXX
        if "=" in text and not text.startswith("{"):
            result = {}
            for part in text.split("&"):
                if "=" in part:
                    k, v = part.split("=", 1)
                    result[k.strip()] = urllib.parse.unquote(v.strip())
            if result:
                return result
        logger.error("[QQ OAuth] 无法解析响应: %.200s", text)
        raise ValueError("qq_parse_failed: 无法解析 QQ 响应")


def _fetch_qq_user_info(
    client: httpx.Client, access_token: str, openid: str, app_id: str
) -> Optional[str]:
    """调用 QQ get_user_info API 获取昵称和头像 URL。

    参考: https://wiki.connect.qq.com/get_user_info
    """
    try:
        r = client.get(
            "https://graph.qq.com/user/get_user_info",
            params={
                "access_token": access_token,
                "oauth_consumer_key": app_id,
                "openid": openid,
            },
        )
        r.raise_for_status()
        body = r.json()
        if body.get("ret") == 0:
            nickname = body.get("nickname", "")
            figure_url = body.get("figureurl_qq_2") or body.get("figureurl_qq_1") or body.get("figureurl")
            logger.info(
                "[QQ OAuth] 用户信息: nickname=%s avatar=%s",
                nickname,
                figure_url or "(无)",
            )
            return nickname.strip() or None
        else:
            logger.warning(
                "[QQ OAuth] get_user_info 返回错误: ret=%s msg=%s",
                body.get("ret"),
                body.get("msg", ""),
            )
    except Exception as exc:
        logger.warning("[QQ OAuth] 获取用户信息失败（不影响登录）: %s", exc)

    return None


# ═══════════════════════════════════════════════════════════
# 微信开放平台 OAuth2.0（v2 增强版）
# ═══════════════════════════════════════════════════════════

def _exchange_wechat(code: str) -> Tuple[str, Optional[str]]:
    """微信开放平台 code → access_token + openid → 用户信息。

    微信开放平台文档: https://developers.weixin.qq.com/doc/oplatform/Website_App/WeChat_Login/Wechat_Login.html
    """
    app_id = settings.WECHAT_OPEN_APP_ID.strip()
    secret = settings.WECHAT_OPEN_APP_SECRET.strip()
    if not app_id or not secret:
        raise ValueError("oauth_not_configured")

    with httpx.Client(timeout=20.0) as client:
        # ── Step 1: code → access_token + openid ──
        logger.info("[WeChat OAuth] Exchanging code for access_token...")
        tr = client.get(
            "https://api.weixin.qq.com/sns/oauth2/access_token",
            params={
                "appid": app_id,
                "secret": secret,
                "code": code,
                "grant_type": "authorization_code",
            },
        )
        tr.raise_for_status()
        token_body = tr.json()
        errcode = token_body.get("errcode", 0)
        if errcode:
            errmsg = token_body.get("errmsg", "")
            err_cn = _WECHAT_ERROR_MAP.get(errcode, f"未知错误({errcode})")
            logger.error(
                "[WeChat OAuth] Token 交换失败: errcode=%s errmsg=%s",
                errcode, errmsg,
            )
            raise ValueError(f"wechat_token_failed: {err_cn}")

        access_token = token_body.get("access_token")
        openid = token_body.get("openid")
        unionid = token_body.get("unionid")
        refresh_token = token_body.get("refresh_token")
        scope = token_body.get("scope", "")
        if not openid or not access_token:
            logger.error("[WeChat OAuth] Token 响应不完整: %s", _mask_body(token_body))
            raise ValueError("wechat_openid_missing")

        logger.info(
            "[WeChat OAuth] Token 获取成功: openid=%s... scope=%s unionid=%s",
            openid[:8], scope, "yes" if unionid else "no",
        )
        # ── Step 2: access_token + openid → 用户信息 ──
        nickname = _fetch_wechat_user_info(client, access_token, openid)

    # 优先使用 unionid（多应用统一标识），其次 openid
    pid = unionid or openid
    return f"wechat_{pid}", nickname


def _fetch_wechat_user_info(
    client: httpx.Client, access_token: str, openid: str
) -> Optional[str]:
    """调用微信 sns/userinfo API 获取用户信息。

    参考: https://developers.weixin.qq.com/doc/oplatform/Website_App/WeChat_Login/Authorized_Interface_Calling_UnionID.html
    """
    try:
        r = client.get(
            "https://api.weixin.qq.com/sns/userinfo",
            params={
                "access_token": access_token,
                "openid": openid,
                "lang": "zh_CN",
            },
        )
        r.raise_for_status()
        body = r.json()
        errcode = body.get("errcode", 0)
        if errcode:
            err_cn = _WECHAT_ERROR_MAP.get(errcode, f"未知错误({errcode})")
            logger.warning(
                "[WeChat OAuth] userinfo 返回错误: errcode=%s errmsg=%s",
                errcode, body.get("errmsg", ""),
            )
            # 不影响登录流程，仅无昵称
            return None

        nickname = body.get("nickname", "")
        headimgurl = body.get("headimgurl", "")
        sex = body.get("sex", 0)
        province = body.get("province", "")
        city = body.get("city", "")
        logger.info(
            "[WeChat OAuth] 用户信息: nickname=%s avatar=%s sex=%s location=%s/%s",
            nickname, headimgurl, sex, province, city,
        )
        return nickname.strip() or None

    except Exception as exc:
        logger.warning("[WeChat OAuth] 获取用户信息失败（不影响登录）: %s", exc)
        return None


# ── 微信 access_token 刷新 ─────────────────────────────────

def refresh_wechat_token(refresh_token: str) -> dict:
    """刷新微信 access_token。

    Returns: {"access_token": "...", "expires_in": 7200, "refresh_token": "...", "openid": "..."}

    Raises: ValueError 当 refresh_token 无效
    """
    app_id = settings.WECHAT_OPEN_APP_ID.strip()
    if not app_id:
        raise ValueError("oauth_not_configured")

    with httpx.Client(timeout=20.0) as client:
        r = client.get(
            "https://api.weixin.qq.com/sns/oauth2/refresh_token",
            params={
                "appid": app_id,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
        )
        r.raise_for_status()
        body = r.json()
        errcode = body.get("errcode", 0)
        if errcode:
            err_cn = _WECHAT_ERROR_MAP.get(errcode, f"未知错误({errcode})")
            logger.error("[WeChat OAuth] Token 刷新失败: errcode=%s", errcode)
            raise ValueError(f"wechat_refresh_failed: {err_cn}")

        logger.info(
            "[WeChat OAuth] Token 刷新成功: openid=%s... expires_in=%s",
            (body.get("openid") or "?")[:8],
            body.get("expires_in"),
        )
        return body


# ── 验证微信服务器签名 ────────────────────────────────────

def verify_wechat_signature(signature: str, timestamp: str, nonce: str) -> bool:
    """验证微信服务器推送的签名（用于事件回调）。

    必须使用微信配置的 Token，禁止误用飞书 Verification Token。
    未配置时诚实拒绝（返回 False），不降级为「看起来像验过」。
    """
    token = (getattr(settings, "WECHAT_VERIFICATION_TOKEN", "") or "").strip()
    if not token:
        logger.warning("WECHAT_VERIFICATION_TOKEN 未配置，拒绝微信回调验签（禁止复用飞书 Token）")
        return False
    if not signature or not timestamp or not nonce:
        return False
    parts = sorted([token, str(timestamp), str(nonce)])
    expected = hashlib.sha1("".join(parts).encode("utf-8")).hexdigest()
    return hmac.compare_digest(signature.strip(), expected)


# ── 工具函数 ──────────────────────────────────────────────

def stable_state_digest(state: str) -> str:
    """为 OAuth state 生成短摘要，用于 session 校验。"""
    return hashlib.sha256(state.encode("utf-8")).hexdigest()[:16]
