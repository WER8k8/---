"""附属统一登录票据服务 · UJ 为唯一身份源.

设计出处：uj-annex-integration-design §9.3（短时授权票据 annex_ticket）；
用户指令：附属（GoodJob / TradeAI）登录系统删除，超管后台与主体共用一个登录。

协议（图 9-1）：
1. UJ 用户在超管后台打开附属嵌入页 → 前端 POST /api/v1/annex/ticket 换取票据；
2. 前端把票据拼到 iframe URL（?annex_ticket=...），主 JWT 不出 UJ 域；
3. 附属前端拿票据调本地 /api/auth/annex-ticket；
4. 附属后端持票据 + 桥令牌回调 UJ POST /api/v1/annex/redeem 换身份；
5. UJ 校验票据（验签 + 一次性消费）返回身份映射，附属据此映射本地会话。

铁律：
- 票据短时（默认 300 秒）且一次性（jti 消费即失效，防重放）；
- 凭证最小半径：主 JWT 不进 iframe URL，附属不持有 UJ 密钥；
- 附属身份映射唯一真相在 UJ（email + annex_role），附属侧密码登录闸门化停用；
- 算法锁死 HS256（手写 JWT 装配，拒绝任何其他 alg，防 alg 混淆攻击）；
- 密钥：ANNEX_TICKET_SECRET 优先，缺省回落 JWT_SECRET_KEY（密钥独立更佳）。
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
import uuid
from typing import Any, Mapping

TICKET_PURPOSE = "annex_ticket"
TICKET_ISSUER = "uj-master"
TICKET_TTL_SECONDS = 300
SUPPORTED_ANNEXES = frozenset({"goodjob", "trade-ai"})

# 附属角色映射：UJ 角色 → 附属本地角色（附属侧按 email 匹配已有账号优先，
# 本映射仅作自动建号时的默认角色；GoodJob 的 super_admin 是平台运维身份
# （强制 MFA 链路），业务管理员映射为 admin 更贴合其权限模型）
ANNEX_ROLE_MAP: dict[str, dict[str, str]] = {
    "goodjob": {"super_admin": "admin", "*": "sales"},
    "trade-ai": {"super_admin": "admin", "*": "agent"},
}

# 一次性 jti 存储：优先 Redis（跨进程一致），降级进程内存（带过期清扫）
_memory_consumed: dict[str, float] = {}
_MEMORY_LIMIT = 10_000
_JTI_GRACE_SECONDS = 600


def _ticket_secret() -> str:
    secret = (os.environ.get("ANNEX_TICKET_SECRET") or "").strip()
    if secret:
        return secret
    from app.core.config import settings

    return str(settings.JWT_SECRET_KEY)


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(segment: str) -> bytes:
    padding = "=" * (-len(segment) % 4)
    return base64.urlsafe_b64decode(segment + padding)


def annex_role_for(annex: str, uj_role: str) -> str:
    mapping = ANNEX_ROLE_MAP.get(annex)
    if not mapping:
        raise ValueError(f"未知附属 {annex!r}，白名单: {sorted(SUPPORTED_ANNEXES)}")
    return mapping.get(uj_role) or mapping["*"]


def _redis_client():
    try:
        from app.core.cache import redis_client

        return redis_client
    except Exception:
        return None


def _consume_jti(jti: str) -> bool:
    """消费一次性 jti；已被消费（重放）返回 False。"""
    now = time.time()
    redis_client = _redis_client()
    if redis_client is not None:
        try:
            if redis_client.set(f"annex_ticket_used:{jti}", "1", ex=_JTI_GRACE_SECONDS, nx=True):
                return True
            return False
        except Exception:
            pass  # Redis 异常降级内存（安全侧：宁可两处都记一次）
    for key, expires in list(_memory_consumed.items()):
        if expires < now:
            _memory_consumed.pop(key, None)
    if jti in _memory_consumed:
        return False
    if len(_memory_consumed) >= _MEMORY_LIMIT:
        oldest = min(_memory_consumed.values())
        for key in list(_memory_consumed):
            if _memory_consumed.get(key) == oldest:
                _memory_consumed.pop(key, None)
                break
    _memory_consumed[jti] = now + _JTI_GRACE_SECONDS
    return True


def issue_annex_ticket(
    *,
    user_id: str,
    user_name: str,
    user_email: str,
    uj_role: str,
    annex: str,
    tenant_id: str = "",
) -> dict[str, Any]:
    """为已认证的 UJ 用户签发指定附属的短时票据。"""
    if annex not in SUPPORTED_ANNEXES:
        raise ValueError(f"未知附属 {annex!r}，白名单: {sorted(SUPPORTED_ANNEXES)}")
    if not str(user_id or "").strip():
        raise ValueError("签发票据缺 user_id")
    if not str(user_email or "").strip():
        raise ValueError("签发票据缺 user_email（附属侧 email 匹配依赖此字段）")
    now = int(time.time())
    expires_at = now + TICKET_TTL_SECONDS
    payload: dict[str, Any] = {
        "iss": TICKET_ISSUER,
        "aud": f"annex:{annex}",
        "sub": str(user_id),
        "name": str(user_name or ""),
        "email": str(user_email),
        "uj_role": str(uj_role or ""),
        "tenant_id": str(tenant_id or ""),
        "annex": annex,
        "annex_role": annex_role_for(annex, str(uj_role or "")),
        "purpose": TICKET_PURPOSE,
        "jti": uuid.uuid4().hex,
        "iat": now,
        "exp": expires_at,
    }
    header = {"alg": "HS256", "typ": "JWT"}
    signing_input = (
        _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
        + "."
        + _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    )
    signature = hmac.new(
        _ticket_secret().encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256
    ).digest()
    return {
        "annex_ticket": f"{signing_input}.{_b64url_encode(signature)}",
        "annex": annex,
        "expires_in": TICKET_TTL_SECONDS,
    }


class TicketRejected(Exception):
    """票据无效（验签失败 / 过期 / 重放 / 声明不符）。"""


def redeem_annex_ticket(token: str, *, annex: str) -> dict[str, Any]:
    """校验并一次性消费票据，返回身份映射；无效抛 TicketRejected。"""
    if annex not in SUPPORTED_ANNEXES:
        raise TicketRejected(f"未知附属 {annex!r}")
    segments = str(token or "").split(".")
    if len(segments) != 3:
        raise TicketRejected("票据格式非法")
    header_b64, payload_b64, signature_b64 = segments
    try:
        header = json.loads(_b64url_decode(header_b64))
        payload = json.loads(_b64url_decode(payload_b64))
        supplied = _b64url_decode(signature_b64)
    except (ValueError, json.JSONDecodeError):
        raise TicketRejected("票据编码非法") from None
    if not isinstance(header, dict) or header.get("alg") != "HS256":
        raise TicketRejected("票据算法非法（锁死 HS256）")
    if not isinstance(payload, dict):
        raise TicketRejected("票据载荷非法")
    expected = hmac.new(
        _ticket_secret().encode("utf-8"),
        f"{header_b64}.{payload_b64}".encode("ascii"),
        hashlib.sha256,
    ).digest()
    if len(supplied) != len(expected) or not hmac.compare_digest(supplied, expected):
        raise TicketRejected("票据验签失败")
    if payload.get("iss") != TICKET_ISSUER:
        raise TicketRejected("票据签发方不符")
    if payload.get("aud") != f"annex:{annex}":
        raise TicketRejected("票据受众不符")
    if payload.get("purpose") != TICKET_PURPOSE:
        raise TicketRejected("票据用途不符（拒收主 JWT 冒充票据）")
    expires = payload.get("exp")
    if not isinstance(expires, (int, float)) or time.time() > float(expires):
        raise TicketRejected("票据已过期")
    jti = str(payload.get("jti") or "")
    if not jti or not _consume_jti(jti):
        raise TicketRejected("票据已使用（一次性防重放）")
    if payload.get("annex") != annex:
        raise TicketRejected("票据附属声明不符")
    return {
        "ok": True,
        "user": {
            "uj_user_id": str(payload.get("sub") or ""),
            "name": str(payload.get("name") or ""),
            "email": str(payload.get("email") or ""),
            "uj_role": str(payload.get("uj_role") or ""),
            "tenant_id": str(payload.get("tenant_id") or ""),
        },
        "annex": annex,
        "annex_role": str(payload.get("annex_role") or ""),
    }


def bridge_token_matches(supplied: str) -> bool:
    """附属回叫 redeem 的服务间认证：常量时间比较桥令牌。"""
    # uvicorn reload 子进程不经过 run.py 的 load_dotenv；pydantic env_file
    # 只填模型字段不写回 os.environ，故 env 为空时回落 pydantic settings。
    from app.core.config import settings

    expected = str(
        os.environ.get("GOODJOB_BRIDGE_TOKEN")
        or getattr(settings, "ANNEX_BRIDGE_TOKEN", "")
        or ""
    ).strip()
    if not expected:
        return False
    supplied = str(supplied or "").strip()
    a = supplied.encode("utf-8")
    b = expected.encode("utf-8")
    return len(a) == len(b) and hmac.compare_digest(a, b)
