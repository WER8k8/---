"""邮件追踪服务 — FIX-47

提供邮件打开/点击/回复追踪功能：
- 追踪像素（1x1 透明图片）
- 链接重写（点击追踪）
- 回复检测
- 追踪数据聚合
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime
from typing import Optional
import uuid

log = logging.getLogger(__name__)

# 追踪域名（生产环境替换为实际域名）
TRACKING_BASE_URL = "https://uj-china.com/track"


class EmailTrackingService:
    """邮件追踪服务。"""
    @staticmethod
    def generate_tracking_pixel(outreach_id: str) -> str:
        """生成追踪像素 URL。

        1x1 透明图片，当收件人打开邮件时加载，记录打开事件。
        """
        token = _generate_tracking_token(outreach_id, "open")
        return f'<img src="{TRACKING_BASE_URL}/pixel/{token}" width="1" height="1" alt="" style="display:none" />'

    @staticmethod
    def rewrite_links(
        body_html: str,
        outreach_id: str,
    ) -> str:
        """重写邮件中的链接，添加点击追踪。

        将原始链接替换为追踪链接，点击时先记录再跳转。
        """
        import re
        def replace_link(match):
            """replace_link。

            参数说明：
            :param match: 参数 match
            :return: 返回处理结果。
            """
            original_url = match.group(1)
            if TRACKING_BASE_URL in original_url:
                return match.group(0)  # 已经是追踪链接，跳过
            if "unsubscribe" in original_url.lower():
                return match.group(0)  # 不追踪退订链接

            token = _generate_tracking_token(outreach_id, "click", original_url)
            tracking_url = f"{TRACKING_BASE_URL}/click/{token}"
            return match.group(0).replace(original_url, tracking_url)

        # 匹配 href 属性中的链接
        body_html = re.sub(
            r'href=["\']([^"\']+)["\']',
            replace_link,
            body_html,
        )
        return body_html

    @staticmethod
    def inject_tracking(
        body_html: str,
        outreach_id: str,
    ) -> str:
        """注入所有追踪元素到邮件 HTML 中。

        包括：追踪像素 + 链接重写
        """
        # 先重写链接
        body_html = EmailTrackingService.rewrite_links(body_html, outreach_id)
        # 在 </body> 前插入追踪像素
        pixel = EmailTrackingService.generate_tracking_pixel(outreach_id)
        if "</body>" in body_html:
            body_html = body_html.replace("</body>", f"{pixel}</body>")
        else:
            body_html += pixel

        return body_html

    @staticmethod
    async def record_open(outreach_id: str, metadata: dict | None = None) -> dict:
        """记录邮件打开事件。"""
        try:
            from app.db.session import SessionLocal
            from app.models.email_outreach import EmailOutreach
            db = SessionLocal()
            try:
                outreach = db.query(EmailOutreach).filter(
                    EmailOutreach.id == outreach_id
                ).first()
                if outreach:
                    outreach.status = "opened"
                    outreach.opened_at = outreach.opened_at or datetime.utcnow()
                    outreach.open_count = (outreach.open_count or 0) + 1
                    if metadata:
                        outreach.outreach_metadata = outreach.outreach_metadata or {}
                        outreach.outreach_metadata["last_open"] = metadata
                    db.commit()
                    # 发送事件
                    from app.core.event_bus import event_bus, Event, EventTypes
                    await event_bus.emit(Event(
                        event_type=EventTypes.EMAIL_OPENED,
                        data={
                            "outreach_id": outreach_id,
                            "prospect_id": outreach.prospect_id,
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    ))
                    return {"status": "recorded", "outreach_id": outreach_id}
            finally:
                db.close()
        except Exception as e:
            log.error("[Tracking] 记录打开失败: %s", e)

        return {"status": "error", "outreach_id": outreach_id}

    @staticmethod
    async def record_click(
        outreach_id: str,
        original_url: str,
        metadata: dict | None = None,
    ) -> dict:
        """记录邮件点击事件，返回原始 URL 用于跳转。"""
        try:
            from app.db.session import SessionLocal
            from app.models.email_outreach import EmailOutreach
            db = SessionLocal()
            try:
                outreach = db.query(EmailOutreach).filter(
                    EmailOutreach.id == outreach_id
                ).first()
                if outreach:
                    outreach.status = "clicked"
                    outreach.clicked_at = outreach.clicked_at or datetime.utcnow()
                    outreach.click_count = (outreach.click_count or 0) + 1
                    if metadata:
                        outreach.outreach_metadata = outreach.outreach_metadata or {}
                        clicks = outreach.outreach_metadata.get("clicks", [])
                        clicks.append({
                            "url": original_url,
                            "timestamp": datetime.utcnow().isoformat(),
                            **metadata,
                        })
                        outreach.outreach_metadata["clicks"] = clicks
                    db.commit()
                    # 发送事件
                    from app.core.event_bus import event_bus, Event, EventTypes
                    await event_bus.emit(Event(
                        event_type=EventTypes.EMAIL_CLICKED,
                        data={
                            "outreach_id": outreach_id,
                            "prospect_id": outreach.prospect_id,
                            "url": original_url,
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    ))
                    return {"status": "recorded", "redirect_url": original_url}
            finally:
                db.close()
        except Exception as e:
            log.error("[Tracking] 记录点击失败: %s", e)

        return {"status": "error", "redirect_url": original_url}

    @staticmethod
    async def get_tracking_stats(
        outreach_id: Optional[str] = None,
        prospect_id: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> dict:
        """获取追踪统计。"""
        try:
            from app.db.session import SessionLocal
            from app.models.email_outreach import EmailOutreach
            from sqlalchemy import func
            db = SessionLocal()
            try:
                query = db.query(EmailOutreach)
                if outreach_id:
                    query = query.filter(EmailOutreach.id == outreach_id)
                if prospect_id:
                    query = query.filter(EmailOutreach.prospect_id == prospect_id)
                if since:
                    query = query.filter(EmailOutreach.created_at >= since)

                total = query.count()
                sent = query.filter(
                    EmailOutreach.status.in_(["sent", "delivered", "opened", "clicked", "replied"])
                ).count()
                opened = query.filter(
                    EmailOutreach.status.in_(["opened", "clicked", "replied"])
                ).count()
                clicked = query.filter(
                    EmailOutreach.status.in_(["clicked", "replied"])
                ).count()
                replied = query.filter(
                    EmailOutreach.status == "replied"
                ).count()
                bounced = query.filter(
                    EmailOutreach.status == "bounced"
                ).count()
                return {
                    "total": total,
                    "sent": sent,
                    "opened": opened,
                    "clicked": clicked,
                    "replied": replied,
                    "bounced": bounced,
                    "open_rate": round(opened / max(1, sent) * 100, 1),
                    "click_rate": round(clicked / max(1, sent) * 100, 1),
                    "reply_rate": round(replied / max(1, sent) * 100, 1),
                    "bounce_rate": round(bounced / max(1, total) * 100, 1),
                }
            finally:
                db.close()
        except Exception as e:
            log.error("[Tracking] 获取统计失败: %s", e)
            return {"error": str(e)}


def _generate_tracking_token(outreach_id: str, event_type: str, url: str = "") -> str:
    """生成追踪 token。"""
    raw = f"{outreach_id}:{event_type}:{url}:{uuid.uuid4()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]