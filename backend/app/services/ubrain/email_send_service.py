"""
零成本邮件发送服务

支持两种发送方式（零成本策略）：
1. Resend API — 免费额度 3000 封/月，配置了 RESEND_API_KEY 时优先使用
2. SMTP — 用户自有邮箱/SMTP 服务器，零额外成本

为什么选 Resend 作为免费方案：
- 3000 封/月免费额度足够早期验证
- 自动配置 DKIM/SPF（减少进垃圾箱）
- API 简单，几行代码就能用
- 有打开/点击追踪（免费版也有）

如果不想注册 Resend，也可以：
- 用公司邮箱 SMTP 发送（零成本，但进垃圾箱率高）
- 用 Gmail App Password（有被风控风险）
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional, Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class EmailSendResult:
    """邮件发送结果"""
    success: bool
    message_id: Optional[str] = None
    provider: Optional[str] = None  # "resend" / "smtp"
    error: Optional[str] = None


@dataclass
class EmailMessage:
    """待发送邮件"""
    to: list[str]
    subject: str
    html_body: str
    from_name: str = "优丁出海"
    from_email: Optional[str] = None  # 不填则用配置的默认发件人
    reply_to: Optional[str] = None
    cc: list[str] = field(default_factory=list)
    bcc: list[str] = field(default_factory=list)


def email_service_available() -> bool:
    """检查邮件服务是否可用。"""
    return bool(settings.RESEND_API_KEY) or bool(settings.SMTP_HOST)


async def send_email(msg: EmailMessage) -> EmailSendResult:
    """发送邮件，自动选择可用的发送方式。

    优先级：Resend > SMTP
    """
    # 优先用 Resend
    if settings.RESEND_API_KEY:
        return await _send_via_resend(msg)

    # 降级到 SMTP
    if settings.SMTP_HOST:
        return await _send_via_smtp(msg)

    return EmailSendResult(
        success=False,
        error="未配置邮件服务（需要 RESEND_API_KEY 或 SMTP_HOST）",
    )


async def _send_via_resend(msg: EmailMessage) -> EmailSendResult:
    """通过 Resend API 发送邮件。"""
    from_email = msg.from_email or settings.RESEND_FROM_EMAIL
    if not from_email:
        return EmailSendResult(
            success=False, provider="resend",
            error="未配置 RESEND_FROM_EMAIL",
        )

    payload = {
        "from": f"{msg.from_name} <{from_email}>",
        "to": msg.to,
        "subject": msg.subject,
        "html": msg.html_body,
    }
    if msg.reply_to:
        payload["reply_to"] = msg.reply_to
    if msg.cc:
        payload["cc"] = msg.cc
    if msg.bcc:
        payload["bcc"] = msg.bcc

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            data = resp.json()
            if resp.status_code in (200, 201) and data.get("id"):
                return EmailSendResult(
                    success=True,
                    message_id=data["id"],
                    provider="resend",
                )
            else:
                return EmailSendResult(
                    success=False,
                    provider="resend",
                    error=data.get("message", f"HTTP {resp.status_code}"),
                )
    except Exception as e:
        logger.error(f"Resend 发送失败: {e}")
        return EmailSendResult(
            success=False, provider="resend", error=str(e),
        )


async def _send_via_smtp(msg: EmailMessage) -> EmailSendResult:
    """通过 SMTP 发送邮件（零成本降级方案）。"""
    import asyncio
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from_email = msg.from_email or settings.SMTP_USER
    if not from_email:
        return EmailSendResult(
            success=False, provider="smtp",
            error="未配置 SMTP 发件人",
        )

    def _send_sync() -> EmailSendResult:
        """_send_sync。
        :return: 返回处理结果。
        """
        try:
            msg_obj = MIMEMultipart("alternative")
            msg_obj["Subject"] = msg.subject
            msg_obj["From"] = f"{msg.from_name} <{from_email}>"
            msg_obj["To"] = ", ".join(msg.to)
            if msg.reply_to:
                msg_obj["Reply-To"] = msg.reply_to

            msg_obj.attach(MIMEText(msg.html_body, "html", "utf-8"))
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT or 587) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(from_email, msg.to, msg_obj.as_string())

            return EmailSendResult(success=True, provider="smtp")
        except Exception as e:
            return EmailSendResult(success=False, provider="smtp", error=str(e))

    return await asyncio.to_thread(_send_sync)


class EmailSendService:
    """邮件发送服务类封装。"""

    async def send(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_name: Optional[str] = None,
    ) -> dict[str, Any]:
        msg = EmailMessage(
            to=[to_email],
            subject=subject,
            html_body=body,
            from_name=from_name or "优丁出海",
        )
        res = await send_email(msg)
        return {
            "success": res.success,
            "message_id": res.message_id,
            "provider": res.provider,
            "error": res.error,
        }