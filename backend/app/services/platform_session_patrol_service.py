# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""平台账号会话巡检（PC-04）—— 把 login_status="expired" 这个已有枚举真正写出来。

背景：platform_accounts.login_status 的注释枚举里有 expired，但全仓没有任何代码写过它，
`platform_credential_guide` 一度也宣称「过期后自动转 expired」，属假承诺（09-13 已订正文案）。
Cookie 会话失效是外贸群发最常见的静默故障：号看着在、发出去全是鉴权失败，
运营只能一个个手点才知道。本模块补两件事：

  1. 事前：按 token_expire_at 与 cookie 老化时限出账（纯 DB 判定，不发任何网络请求）；
  2. 事后：真发布链路报鉴权失败时回写 expired（见 classify_publish_failure 的调用点）。

诚实边界：本系统没有各平台的「会话有效性校验」接口凭据，因此不做在线探活，
也不承诺「巡检通过 = 一定能发」。巡检只负责把明显过期的号从 logged_in 摘下来，
并把缺什么如实写进报告的 missing_capabilities，供前端与运维看见。
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.content import Platform, PlatformAccount

logger = logging.getLogger(__name__)

# 判定「会话/鉴权类失败」的特征串：只用于把 login_status 置为 expired，
# 不改发布结果本身（结果仍按原错误抛出，禁止把失败洗成成功）。
_AUTH_FAILURE_MARKERS: tuple[str, ...] = (
    "invalid session",
    "session expired",
    "session_timeout",
    "token expired",
    "invalid_grant",
    "unauthorized",
    "not logged in",
    "login required",
    "relogin",
    "bad credential",
    "invalid credential",
    "cookie expired",
    "请重新登录",
    "登录已失效",
    "登录失效",
    "登录过期",
    "登录状态已过期",
    "未登录",
    "扫码登录",
    "重新扫码",
    "凭证已过期",
    "签名校验失败",
    "invalid access_token",
    "invalid appsecret",
    "accessdeny",
    "permission denied",
)

# 明确不属于会话问题的特征：这些即便字面相似也不能把号判死，避免误伤。
_AUTH_FAILURE_EXCLUSIONS: tuple[str, ...] = (
    "PLATFORM_NOT_CONFIGURED",
    "PLATFORM_NOT_IMPLEMENTED",
    "gate_blocked",
    "timeout",
    "timed out",
    "connection",
    "dns",
    "rate limit",
    "too many requests",
    "429",
)


def classify_publish_failure(error_text: str | None) -> Optional[str]:
    """把发布异常文案分成 auth / other；只有 auth 才允许把账号置为 expired。

    宁可漏判不可误判：命中排除词（没配凭证、没实现、网络/限流）一律归 other，
    因为这些跟「cookie 掉了」无关，误置 expired 会让租户白重绑一次号。
    """
    text = str(error_text or "").strip().lower()
    if not text:
        return None
    if any(token in text for token in _AUTH_FAILURE_EXCLUSIONS):
        return None
    if any(token in text for token in _AUTH_FAILURE_MARKERS):
        return "auth"
    return None


def _aware(value: datetime | None) -> Optional[datetime]:
    """DB 列可能是 naive UTC（SQLite）或 aware（PG），统一成 aware 再比较。"""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def mark_session_expired(
    db: Session,
    account: PlatformAccount | None,
    *,
    reason: str,
    commit: bool = False,
) -> bool:
    """把账号置为 expired。已经是 expired 则不重复写（返回 False，免得刷屏）。"""
    if account is None or (account.login_status or "") == "expired":
        return False
    account.login_status = "expired"
    logger.warning(
        "platform session expired: account=%s platform_id=%s reason=%s",
        getattr(account, "id", "?"),
        getattr(account, "platform_id", "?"),
        reason,
    )
    if commit:
        db.commit()
    return True


def note_publish_failure(
    db: Session,
    account: PlatformAccount | None,
    error_text: str | None,
    *,
    commit: bool = False,
) -> Optional[str]:
    """真发布报错时的统一入口：只在鉴权类失败时置 expired，返回分类结果或 None。

    只调 mark_session_expired，不改写异常本身；调用方照常把原始错误抛出。
    """
    if classify_publish_failure(error_text) != "auth":
        return None
    mark_session_expired(
        db,
        account,
        reason=f"publish_auth_failure:{str(error_text)[:160]}",
        commit=commit,
    )
    return "auth"


def patrol_platform_sessions(
    db: Session,
    *,
    cookie_stale_days: Optional[int] = None,
    dry_run: bool = False,
    limit: int = 500,
) -> dict[str, Any]:
    """会话巡检：token 到期 + cookie 老化两类判定，命中即置 login_status=expired。

    cookie_stale_days 取值依据：国内内容平台后台 cookie 普遍 7~30 天滑动过期，
    取 14 天是「宁可早提醒、不让租户在发布现场才发现」的折中，可由环境变量
    PLATFORM_COOKIE_STALE_DAYS 收紧（不传参时即取该配置）。
    dry_run 只出报告不改库，供前端「先看看会命中谁」与单测使用。
    """
    if cookie_stale_days is None:
        from app.core.config import settings

        cookie_stale_days = int(settings.PLATFORM_COOKIE_STALE_DAYS)
    now = datetime.now(timezone.utc)
    stale_cutoff = now - timedelta(days=max(int(cookie_stale_days), 1))

    accounts = (
        db.query(PlatformAccount, Platform)
        .join(Platform, Platform.id == PlatformAccount.platform_id)
        .filter(
            PlatformAccount.is_active.is_(True),
            PlatformAccount.login_status == "logged_in",
        )
        .limit(max(int(limit), 1))
        .all()
    )

    findings: list[dict[str, Any]] = []
    candidates = 0
    for acc, plat in accounts:
        reasons: list[str] = []
        expire_at = _aware(acc.token_expire_at)
        if expire_at is not None and expire_at <= now:
            reasons.append(f"token_expire_at={expire_at.isoformat()}")
        has_cookie = bool((acc.cookie_data or "").strip())
        if has_cookie:
            touched = _aware(acc.last_login_at) or _aware(acc.updated_at) or _aware(acc.created_at)
            if touched is not None and touched <= stale_cutoff:
                reasons.append(f"cookie_idle_days={(now - touched).days}")
        if not reasons:
            continue
        candidates += 1
        findings.append(
            {
                "account_id": str(acc.id),
                "tenant_id": str(acc.tenant_id or ""),
                "platform_name": plat.name,
                "reasons": reasons,
                # 只报「有没有凭证」，绝不回传 cookie / token 内容
                "has_cookie": has_cookie,
                "has_token_data": bool(acc.token_data),
                "marked": not dry_run,
            }
        )
        if not dry_run:
            acc.login_status = "expired"

    if not dry_run and candidates:
        db.commit()

    return {
        "checked_at": now.isoformat(),
        "dry_run": dry_run,
        "cookie_stale_days": int(cookie_stale_days),
        "logged_in_scanned": len(accounts),
        "expired_marked": candidates if not dry_run else 0,
        "expired_candidates": candidates,
        "findings": findings,
        # 如实声明能力边界，避免「巡检绿 = 一定能真发」的误读
        "missing_capabilities": [
            "无平台侧会话校验接口凭据，不做在线探活（只按到期时间与老化时限判定）",
            "expired 不会自动恢复：须运营重新绑定后手动置回 logged_in",
        ],
        "next_step": (
            "对 findings 里的账号逐个重新绑定 cookie/token；"
            "重绑走 PUT /seo-matrix/platform-accounts/{id}（带 cookie 或 token_data）"
        ),
    }
