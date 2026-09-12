"""邮件追踪服务（P1-3）—— 像素回调 + 发送追踪。"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.email_tracking_event import EmailTrackingEvent
from app.models.prospect_lead import ProspectLead


# 1x1 透明 PNG（最小字节）
PIXEL_BYTES = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
    b'\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
    b'\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01'
    b'\r\n\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
)


def record_open_event(
    db: Session,
    message_id: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> None:
    """记录邮件打开事件。"""
    event = EmailTrackingEvent(
        message_id=message_id,
        event_type="open",
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(event)
    # 更新 ProspectLead 的打开统计
    # 通过 message_id 关联 lead（message_id 格式：{lead_id}_{version}_{timestamp}）
    lead_id = _extract_lead_id(message_id)
    if lead_id:
        lead = db.query(ProspectLead).filter(ProspectLead.id == lead_id).first()
        if lead:
            lead.last_opened_at = datetime.now(timezone.utc)
            lead.open_count = (lead.open_count or 0) + 1
            db.flush()


def record_click_event(
    db: Session,
    message_id: str,
    clicked_url: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> None:
    """记录链接点击事件。"""
    event = EmailTrackingEvent(
        message_id=message_id,
        event_type="click",
        clicked_url=clicked_url,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(event)
    lead_id = _extract_lead_id(message_id)
    if lead_id:
        lead = db.query(ProspectLead).filter(ProspectLead.id == lead_id).first()
        if lead:
            lead.last_clicked_at = datetime.now(timezone.utc)
            lead.click_count = (lead.click_count or 0) + 1
            db.flush()


def send_tracked_email(
    db: Session,
    to: str,
    subject: str,
    body: str,
    lead_id: Optional[str] = None,
    user_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    track_opens: bool = True,
    track_clicks: bool = True,
) -> dict:
    """发送带追踪的邮件。

    注入追踪像素和链接追踪后调用邮件服务发送。
    """
    # 生成 message_id
    message_id = f"{lead_id or 'unknown'}_a_{uuid.uuid4().hex[:8]}"
    # 注入追踪像素
    from app.core.config import settings
    base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000').rstrip('/')
    html_body = body.replace("\n", "<br>")
    if track_opens:
        pixel_tag = (
            f'<img src="{base_url}/api/v1/tracking/pixel/{message_id}.png" '
            f'width="1" height="1" style="display:none" />'
        )
        html_body += pixel_tag

    # 调用现有邮件服务发送
    from app.services.email_service import EmailService
    email_service = EmailService()
    # 记录发送事件
    send_event = EmailTrackingEvent(
        message_id=message_id,
        lead_id=lead_id,
        tenant_id=tenant_id,
        user_id=user_id,
        event_type="sent",
        event_metadata={"to": to, "subject": subject},
    )
    db.add(send_event)
    # 实际发送（如果邮件服务已配置）
    sent = False
    if email_service.enabled:
        try:
            sent = email_service.send_raw(
                to=to,
                subject=subject,
                html=html_body,
            )
        except Exception:
            sent = False

    return {
        "message_id": message_id,
        "sent": sent,
        "to": to,
        "subject": subject,
    }


def _extract_lead_id(message_id: str) -> Optional[str]:
    """从 message_id 中提取 lead_id。格式：{lead_id}_{version}_{hash}"""
    parts = message_id.split("_")
    if len(parts) >= 1:
        candidate = parts[0]
        # 跳过无效前缀和非 UUID 格式
        if candidate in ("unknown", "", "test"):
            return None
        # UUID 格式校验（含横线或 32 位 hex）
        if len(candidate) >= 8 and all(c in "0123456789abcdef-" for c in candidate.lower()):
            return candidate
    return None
