# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""DSH 沙箱治理服务 —— 修正设计稿 模块15（进程/网络/DB 三层隔离）/ Gate G10。

三层落点：
- **进程级**：resolve_mode() —— 开发可 in_process；生产（ENVIRONMENT=production）
  必须 DSH_SANDBOX_MODE=sandbox，否则 ensure_run_allowed 直接 503 fail-closed
  （SandboxContainer 的实际派发由 deploy/dsh-sandbox-compose.yml 拓扑承接）。
- **网络级**：check_network_target —— egress allowlist（DSH_EGRESS_ALLOWLIST，
  默认仅模型端点），未授权目标 → 审计 deny + 拒绝。
- **DB 级**：DSH 不发放任何 DB 凭据；沙箱只持有**短期执行令牌**
  （issue_task_token：HMAC 签名 + 过期时间 + tenant/task 绑定；verify_task_token 验签），
  数据访问只能经 Harness Gateway → validated service API。

审计：所有 allow/deny 决策写 harness_security_events（append-only，模块15.6）。

红线：本服务**绝不**把 DATABASE_URL / Redis 密码 / 长期凭据放入令牌或沙箱环境。
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.harness_security import HarnessSecurityEvent

logger = logging.getLogger(__name__)


class SandboxViolation(Exception):
    """沙箱治理拒绝（携带 HTTP 语义与审计码）。"""

    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


# ── 进程级：模式解析（fail-closed） ────────────────────────────


def resolve_mode(env: Optional[dict[str, str]] = None) -> tuple[str, str]:
    """返回 (mode, reason)。mode ∈ in_process / sandbox / forbidden。

    规则：DSH_SANDBOX_MODE 显式指定优先；生产环境未显式 sandbox 一律 forbidden
    （fail-closed：宁可 DSH 不可用，不可无沙箱裸跑）。
    """
    src = env if env is not None else os.environ
    environment = (src.get("ENVIRONMENT") or "").strip().lower()
    mode = (src.get("DSH_SANDBOX_MODE") or "").strip().lower()
    if not mode:
        mode = "sandbox" if environment == "production" else "in_process"
    if mode not in ("in_process", "sandbox"):
        return "forbidden", f"未知 DSH_SANDBOX_MODE={mode!r}"
    if environment == "production" and mode != "sandbox":
        return "forbidden", "生产环境必须 DSH_SANDBOX_MODE=sandbox（模块15.3）"
    return mode, "ok"


def ensure_run_allowed(env: Optional[dict[str, str]] = None) -> str:
    """模式放行检查；forbidden → 503 fail-closed。返回放行的 mode。"""
    mode, reason = resolve_mode(env)
    if mode == "forbidden":
        raise SandboxViolation(503, "sandbox_mode_required", reason)
    return mode


# ── 网络级：egress allowlist ─────────────────────────────────


def _default_allowlist() -> list[str]:
    raw = _env("DSH_EGRESS_ALLOWLIST", "api.deepseek.com,api.openai.com,harness-gateway.internal")
    return [h.strip().lower() for h in raw.split(",") if h.strip()]


def check_network_target(db: Session, target: str, *, tenant_id: Optional[str] = None,
                         task_id: Optional[str] = None, trace_id: Optional[str] = None) -> bool:
    """egress allowlist 校验；deny 时写审计并抛 403。"""
    allowlist = [h for h in _default_allowlist() if h]
    host = (target or "").strip().lower()
    host = host.split("://")[-1].split("/")[0].split(":")[0]
    allowed = any(host == a or host.endswith(f".{a}") for a in allowlist)
    decision = "allow" if allowed else "deny"
    audit_event(
        db,
        tenant_id=tenant_id,
        task_id=task_id,
        network_target=host,
        operation="egress_check",
        policy="egress_allowlist",
        decision=decision,
        detail=None if allowed else f"target not in allowlist {allowlist}",
        trace_id=trace_id,
    )
    if not allowed:
        raise SandboxViolation(403, "egress_denied", f"网络目标 {host} 不在沙箱 egress 白名单内")
    return True


# ── 令牌（短期执行凭据；不含任何 DB/Redis 凭据） ───────────────


def _signing_key() -> bytes:
    from app.core.config import settings

    return f"harness-sandbox:{settings.SECRET_KEY}".encode("utf-8")


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def issue_task_token(*, tenant_id: str, task_id: str, ttl_seconds: int = 300) -> str:
    """签发短期沙箱执行令牌（默认 5 分钟；载荷不含任何 DB/Redis 凭据）。"""
    payload = {
        "tenant_id": str(tenant_id),
        "task_id": str(task_id),
        "exp": int((_utcnow() + timedelta(seconds=ttl_seconds)).timestamp()),
        "jti": uuid.uuid4().hex[:12],
    }
    body = _b64(json.dumps(payload, separators=(",", ":")).encode())
    sig = hmac.new(_signing_key(), body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def verify_task_token(token: str) -> dict[str, Any]:
    """验签 + 过期校验；伪造/篡改/过期 → SandboxViolation(401)。"""
    try:
        body, sig = str(token).split(".", 1)
    except ValueError:
        raise SandboxViolation(401, "sandbox_token_invalid", "令牌格式非法")
    expect = hmac.new(_signing_key(), body.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expect, sig):
        raise SandboxViolation(401, "sandbox_token_invalid", "令牌签名校验失败（疑似伪造）")
    payload = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
    if int(payload.get("exp") or 0) < int(_utcnow().timestamp()):
        raise SandboxViolation(401, "sandbox_token_expired", "令牌已过期")
    return payload


# ── 审计 ─────────────────────────────────────────────────────


def audit_event(
    db: Optional[Session],
    *,
    operation: str,
    policy: str,
    decision: str,
    tenant_id: Optional[str] = None,
    task_id: Optional[str] = None,
    network_target: Optional[str] = None,
    detail: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> None:
    """写 harness_security_events（append-only）；审计失败只记日志，不阻断主链。"""
    try:
        if db is None:
            logger.warning("harness audit (no session): %s %s %s", operation, policy, decision)
            return
        db.add(
            HarnessSecurityEvent(
                tenant_id=str(tenant_id) if tenant_id else None,
                task_id=task_id,
                network_target=network_target,
                operation=operation,
                policy=policy,
                decision=decision,
                detail=detail,
                trace_id=trace_id,
            )
        )
        db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("harness audit write failed: %s", exc)


# ── 治理后的 run_turn 入口 ────────────────────────────────────


def governed_run_turn(
    db: Session,
    *,
    tenant_id: str,
    prompt: str,
    trace_id: Optional[str] = None,
    session_id: Optional[str] = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """带三层治理的 DSH turn 入口（routes 层改调本函数）。

    - 模式 fail-closed：生产未配 sandbox → 审计 deny + 503；
    - in_process（开发）：审计 allow 后调用既有 client.run_turn；
    - sandbox（生产）：签发短期令牌并要求容器 runner 承接；runner 未部署 → 503
      （诚实：不假装已沙箱执行）。
    """
    task_id = f"task_{uuid.uuid4().hex[:12]}"
    try:
        mode = ensure_run_allowed()
    except SandboxViolation as exc:
        audit_event(
            db, tenant_id=tenant_id, task_id=task_id, operation="mode_check",
            policy="sandbox_mode", decision="deny", detail=exc.message, trace_id=trace_id,
        )
        raise

    if mode == "in_process":
        audit_event(
            db, tenant_id=tenant_id, task_id=task_id, operation="mode_check",
            policy="sandbox_mode", decision="allow", detail="dev in_process", trace_id=trace_id,
        )
        from app.services.deepseek_harness.client import run_turn

        result = run_turn(prompt, session_id=session_id, **kwargs)
        return {"dispatch": "in_process", "task_token": None, **result}

    # mode == sandbox：容器派发拓扑由 deploy/dsh-sandbox-compose.yml 承接
    token = issue_task_token(tenant_id=tenant_id, task_id=task_id)
    audit_event(
        db, tenant_id=tenant_id, task_id=task_id, operation="mode_check",
        policy="sandbox_mode", decision="allow", detail="sandbox dispatch (signed task)", trace_id=trace_id,
    )
    raise SandboxViolation(
        503,
        "sandbox_runner_not_deployed",
        "沙箱模式已启用但容器 runner 未部署（见 deploy/dsh-sandbox-compose.yml）；"
        "拒绝在进程内直跑 DSH（fail-closed）",
    )
