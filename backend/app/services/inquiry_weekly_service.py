"""租户询盘周报 — P0-5 honest 报表（数字可为 0，不可假）。"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.models.tenant import Tenant

_PHONE_RE = re.compile(r"1[3-9]\d{9}")


def _week_start_utc(now: datetime | None = None) -> datetime:
    """_week_start_utc。

    参数说明：
    :param now: 参数 now
    :return: 返回处理结果。
    """
    now = now or datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    # Monday as week start
    start = start - timedelta(days=start.weekday())
    return start


def build_inquiry_weekly_report(db: Session, tenant: Tenant) -> dict[str, Any]:
    """build_inquiry_weekly_report。

    参数说明：
    :param db: 参数 db
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    from app.models.inquiry import Inquiry
    tid = str(tenant.id)
    week_start = _week_start_utc()
    base = db.query(Inquiry).filter(Inquiry.is_active, Inquiry.tenant_id == tid)
    week_rows = base.filter(Inquiry.created_at >= week_start).all()
    received = len(week_rows)
    pending = sum(1 for i in week_rows if (i.status or "pending") == "pending")
    followed = received - pending
    with_phone = sum(1 for i in week_rows if _PHONE_RE.search(str(i.phone or "")))
    all_pending = base.filter(Inquiry.status == "pending").count()
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    today_received = base.filter(Inquiry.created_at >= today_start).count()
    return {
        "week_start": week_start.date().isoformat(),
        "week_label": f"{week_start.strftime('%m-%d')} 起",
        "received": received,
        "followed": followed,
        "pending": pending,
        "with_phone": with_phone,
        "all_pending": all_pending,
        "today_received": today_received,
        "honest_note": "数字来自本租户真实询盘；0 表示本周暂无，不是系统故障。",
        "north_star": "有效跟进 = 已处理（非待处理）且尽量拿到可回拨电话。",
    }
