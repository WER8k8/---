"""GW-G-SM-04 — 平台账号 login_status 超时告警。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.content import Platform, PlatformAccount


def scan_offline_accounts(
    db: Session,
    *,
    tenant_id: str | None = None,
    hours: int = 24,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """实现 扫描offline账户 的功能。
    
    :param db: 参数 db（类型: Session）
    :param tenant_id: 参数 tenant_id（类型: str | None）
    :param hours: 参数 hours（类型: int）
    :param limit: 参数 limit（类型: int）
    :return: 返回 list[dict[str, Any]] 结果
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=max(hours, 1))
    q = db.query(PlatformAccount, Platform).join(Platform, Platform.id == PlatformAccount.platform_id)
    q = q.filter(
        PlatformAccount.is_active.is_(True),
        PlatformAccount.login_status.in_(("logged_out", "expired")),
    )
    if tenant_id:
        q = q.filter(PlatformAccount.tenant_id == tenant_id)

    alerts: list[dict[str, Any]] = []
    for acc, plat in q.limit(limit).all():
        updated = acc.updated_at or acc.created_at
        if updated and updated.tzinfo is None:
            updated = updated.replace(tzinfo=timezone.utc)
        if updated and updated > cutoff:
            continue
        alerts.append(
            {
                "account_id": str(acc.id),
                "tenant_id": str(acc.tenant_id),
                "platform_name": plat.name,
                "login_status": acc.login_status,
                "last_updated": updated.isoformat() if updated else None,
                "hours_offline": hours,
            }
        )
    return alerts


def run_platform_health_alert_cycle(
    db: Session,
    *,
    hours: int = 24,
    notify: bool = True,
) -> dict[str, Any]:
    """实现 执行平台healthalertcycle 的功能。
    
    :param db: 参数 db（类型: Session）
    :param hours: 参数 hours（类型: int）
    :param notify: 参数 notify（类型: bool）
    :return: 返回 dict[str, Any] 结果
    """
    alerts = scan_offline_accounts(db, hours=hours)
    alert_result: dict[str, Any] = {"sent": False}
    if notify and alerts:
        try:
            from app.services.hermes.alert_dispatcher import send_feishu_card
            lines = [
                f"- {a['platform_name']} tenant={a['tenant_id'][:8]}… status={a['login_status']}"
                for a in alerts[:15]
            ]
            body = "\n".join(lines)
            if len(alerts) > 15:
                body += f"\n… 另有 {len(alerts) - 15} 条"
            alert_result = send_feishu_card(
                title=f"平台账号健康告警（>{hours}h 未登录）",
                body_md=body,
                template="orange",
                event_type="platform_health",
                fingerprint=f"platform_health:{len(alerts)}:{hours}",
            )
        except Exception as exc:
            alert_result = {"sent": False, "error": str(exc)[:200]}

    return {
        "gw_task": "GW-G-SM-04",
        "alerts_count": len(alerts),
        "alerts": alerts,
        "notify": alert_result,
        "ok": len(alerts) == 0,
    }
