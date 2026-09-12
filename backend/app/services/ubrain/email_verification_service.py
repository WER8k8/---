"""
零成本邮箱验证服务 — 无需付费 API

验证策略（从快到慢，从省钱到精准）：
1. 格式校验（正则）— 0 成本，毫秒级
2. 域名 MX 记录检查 — 0 成本，10-50ms
3. SMTP RCPT TO 验证 — 0 成本，200-1000ms，准确率 90%+

注意：
- SMTP RCPT TO 验证可能被某些邮件服务器反垃圾策略误判
- 部分服务器（如 Gmail）始终返回 250，无法验证
- 生产环境建议结合多策略打分，而非单一结果
"""

from __future__ import annotations

import asyncio
import logging
import re
import socket
from dataclasses import dataclass
from email.utils import parseaddr
from typing import Literal, Any

import dns.resolver

logger = logging.getLogger(__name__)

VerificationStatus = Literal["valid", "invalid", "unknown", "risky"]


@dataclass(frozen=True)
class EmailVerificationResult:
    """邮箱验证结果"""
    email: str
    status: VerificationStatus
    format_valid: bool
    mx_valid: bool
    smtp_valid: bool | None  # None 表示无法验证
    reason: str
    score: int  # 0-100，综合可信度分


# 简单但足够的邮箱正则（RFC 5322 简化版）
_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
)

# 始终返回 250 的域名（无法用 SMTP 验证）
_ALWAYS_ACCEPT_DOMAINS = {
    "gmail.com", "googlemail.com",
    "outlook.com", "hotmail.com", "live.com", "msn.com",
    "yahoo.com", "ymail.com",
    "icloud.com", "me.com", "mac.com",
}

# DNS 缓存（减少重复查询）
_mx_cache: dict[str, list[str]] = {}


async def verify_email(email: str, *, do_smtp_check: bool = True) -> EmailVerificationResult:
    """验证邮箱有效性。

    Args:
        email: 待验证邮箱
        do_smtp_check: 是否执行 SMTP RCPT TO 验证（较慢但更准）

    Returns:
        EmailVerificationResult
    """
    email = email.strip().lower()
    # Step 1: 格式校验
    if not _EMAIL_RE.match(email):
        return EmailVerificationResult(
            email=email, status="invalid",
            format_valid=False, mx_valid=False, smtp_valid=None,
            reason="邮箱格式不正确",
            score=0,
        )

    _, domain = parseaddr(email)
    if "@" in domain:
        domain = domain.split("@", 1)[1]
    else:
        domain = email.split("@", 1)[1]

    # Step 2: MX 记录检查
    mx_records = await _get_mx_records(domain)
    if not mx_records:
        return EmailVerificationResult(
            email=email, status="invalid",
            format_valid=True, mx_valid=False, smtp_valid=None,
            reason=f"域名 {domain} 无 MX 记录",
            score=10,
        )

    # Step 3: SMTP RCPT TO 验证（可选）
    smtp_valid: bool | None = None
    smtp_reason = ""
    if do_smtp_check:
        if domain in _ALWAYS_ACCEPT_DOMAINS:
            smtp_valid = None
            smtp_reason = f"{domain} 始终返回 250，无法用 SMTP 验证"
        else:
            try:
                smtp_valid = await _smtp_rcpt_check(email, mx_records)
            except Exception as e:
                smtp_valid = None
                smtp_reason = f"SMTP 验证失败: {e}"

    # 综合打分
    score = 40  # 格式正确 40 分
    score += 30  # MX 有效 +30
    if smtp_valid is True:
        score += 30  # SMTP 验证通过 +30
    elif smtp_valid is False:
        score = 10  # SMTP 验证失败，直接打低分

    # 状态判断
    if smtp_valid is True:
        status: VerificationStatus = "valid"
        reason = "SMTP 验证通过"
    elif smtp_valid is False:
        status = "invalid"
        reason = smtp_reason or "SMTP 验证失败"
    elif domain in _ALWAYS_ACCEPT_DOMAINS:
        status = "risky"
        reason = smtp_reason
    else:
        status = "unknown"
        reason = smtp_reason or "无法执行 SMTP 验证"

    return EmailVerificationResult(
        email=email, status=status,
        format_valid=True, mx_valid=True, smtp_valid=smtp_valid,
        reason=reason, score=score,
    )


async def _get_mx_records(domain: str) -> list[str]:
    """查询域名 MX 记录，带缓存。"""
    if domain in _mx_cache:
        return _mx_cache[domain]

    try:
        answers = await asyncio.to_thread(
            dns.resolver.resolve, domain, "MX"
        )
        records = [
            r.exchange.to_text().rstrip(".")
            for r in sorted(answers, key=lambda r: r.preference)
        ]
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.Timeout):
        records = []
    except Exception:
        records = []

    _mx_cache[domain] = records
    return records


async def _smtp_rcpt_check(email: str, mx_hosts: list[str]) -> bool:
    """通过 SMTP RCPT TO 命令验证邮箱是否存在。

    注意：这是零成本但有局限的方案：
    - 部分服务器反垃圾策略会拦截
    - Gmail 等始终返回 250
    - 频繁调用可能被拉黑
    """
    if not mx_hosts:
        return False

    domain = email.split("@", 1)[1]
    # 只试优先级最高的 2 个 MX
    for mx_host in mx_hosts[:2]:
        try:
            result = await asyncio.to_thread(
                _smtp_rcpt_sync, email, mx_host, domain
            )
            if result:
                return True
        except Exception:
            continue

    return False


def _smtp_rcpt_sync(email: str, mx_host: str, domain: str) -> bool:
    """同步版 SMTP RCPT TO 验证（在线程中执行）。"""
    import smtplib
    try:
        server = smtplib.SMTP(timeout=10)
        server.set_debuglevel(0)
        server.connect(mx_host, 25)
        server.helo("verify." + domain)
        server.mail("verify@" + domain)
        code, _ = server.rcpt(email)
        server.quit()
        return code == 250
    except (smtplib.SMTPException, socket.error, OSError):
        return False


class EmailVerificationService:
    """邮箱有效性验证服务类。"""

    def __init__(self, do_smtp_check: bool = True):
        self.do_smtp_check = do_smtp_check

    async def verify(self, email: str) -> dict[str, Any]:
        result = await verify_email(email, do_smtp_check=self.do_smtp_check)
        return {
            "email": result.email,
            "status": result.status,
            "format_valid": result.format_valid,
            "mx_valid": result.mx_valid,
            "smtp_valid": result.smtp_valid,
            "score": result.score,
            "reason": result.reason,
        }