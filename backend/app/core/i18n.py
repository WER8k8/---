"""后端 i18n 脚手架（M7，ADR-002 附带交付）。

设计：消息目录 + `t(key, locale)` + `resolve_locale(request)`。
- 缺 key/缺 locale → 回退 zh 原文（零行为变更）。
- 迁移策略：按模块增量把 `error_response(401, "中文")` 换成
  `error_response(401, t("auth.bad_credentials", locale))`；本批仅代表 auth 登录两条。
- 未覆盖的调用点保持中文字面量，不阻塞。
"""
from __future__ import annotations
import re
from typing import Optional

MESSAGES: dict[str, dict[str, str]] = {
    # key: {"zh": 原文, "en": 英文}
    "auth.bad_credentials": {
        "zh": "账号或密码错误",
        "en": "Invalid username or password",
    },
    "auth.no_token": {
        "zh": "未提供认证令牌",
        "en": "Authentication token missing",
    },
    "auth.invalid_token": {
        "zh": "无效的认证令牌",
        "en": "Invalid authentication token",
    },
    "auth.forbidden": {
        "zh": "权限不足",
        "en": "Insufficient permissions",
    },
}

_LOCALE_RE = re.compile(r"^[a-zA-Z]{2}(?:-[a-zA-Z]{2})?$")
SUPPORTED = ("zh", "en")
DEFAULT_LOCALE = "zh"


def resolve_locale(accept_language: Optional[str]) -> str:
    """从 Accept-Language 头解析受支持 locale（缺省 zh）。"""
    if not accept_language:
        return DEFAULT_LOCALE
    for part in accept_language.split(","):
        code = part.split(";")[0].strip().lower()
        lang = code.split("-")[0]
        if lang in SUPPORTED:
            return lang
    return DEFAULT_LOCALE


def t(key: str, locale: str = DEFAULT_LOCALE) -> str:
    """查消息目录；未收录 key/locale 一律回退 zh 原文（找不到则返回 key 本身）。"""
    entry = MESSAGES.get(key)
    if not entry:
        return key
    return entry.get(locale) or entry.get(DEFAULT_LOCALE) or key
