"""出海计 Push — FCM Legacy HTTP（配置 FCM_SERVER_KEY 后真推送）。"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.models.app_device import AppDevice

logger = logging.getLogger(__name__)


def fcm_enabled() -> bool:
    """fcm_enabled。
    :return: 返回处理结果。
    """
    return bool(os.getenv("FCM_SERVER_KEY", "").strip())


def _fcm_enabled() -> bool:
    """_fcm_enabled。
    :return: 返回处理结果。
    """
    return fcm_enabled()


def _send_fcm(device_token: str, title: str, body: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    """_send_fcm。

    参数说明：
    :param device_token: 参数 device_token
    :param title: 参数 title
    :param body: 参数 body
    :param data: 参数 data
    :return: 返回处理结果。
    """
    key = os.getenv("FCM_SERVER_KEY", "").strip()
    if not key:
        return {"ok": False, "mode": "stub", "reason": "FCM_SERVER_KEY unset"}

    payload = {
        "to": device_token,
        "notification": {"title": title, "body": body},
        "data": {k: str(v) for k, v in (data or {}).items()},
        "priority": "high",
    }
    try:
        resp = httpx.post(
            "https://fcm.googleapis.com/fcm/send",
            json=payload,
            headers={
                "Authorization": f"key={key}",
                "Content-Type": "application/json",
            },
            timeout=10.0,
        )
        ok = resp.status_code == 200
        return {"ok": ok, "mode": "fcm", "status": resp.status_code, "body": resp.text[:200]}
    except Exception as exc:
        logger.warning("FCM send failed: %s", exc)
        return {"ok": False, "mode": "fcm", "error": str(exc)}


def send_to_user(
    db: Session,
    *,
    user_id: str,
    title: str,
    body: str,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """send_to_user。

    参数说明：
    :param db: 参数 db
    :param user_id: 参数 user_id
    :param title: 参数 title
    :param body: 参数 body
    :param data: 参数 data
    :return: 返回处理结果。
    """
    devices = (
        db.query(AppDevice)
        .filter(AppDevice.user_id == user_id)
        .limit(50)
        .all()
    )
    if not devices:
        return {"sent": 0, "skipped": True, "reason": "no_devices"}

    results = []
    sent = 0
    for d in devices:
        if _fcm_enabled() and d.platform in ("android", "ios"):
            r = _send_fcm(d.device_token, title, body, data)
            results.append(r)
            if r.get("ok"):
                sent += 1
        else:
            logger.info(
                "push_stub user=%s platform=%s token=%s title=%s",
                user_id,
                d.platform,
                d.device_token[:16],
                title,
            )
            results.append({"ok": True, "mode": "stub"})
            if not _fcm_enabled():
                sent += 1
    return {
        "sent": sent,
        "devices": len(devices),
        "mode": "fcm" if _fcm_enabled() else "stub",
        "fcm_configured": _fcm_enabled(),
        "results": results[:5],
    }


def notify_inquiry_pending(db: Session, user_id: str, count: int) -> dict[str, Any]:
    """notify_inquiry_pending。

    参数说明：
    :param db: 参数 db
    :param user_id: 参数 user_id
    :param count: 参数 count
    :return: 返回处理结果。
    """
    return send_to_user(
        db,
        user_id=user_id,
        title="出海计 · 新询盘",
        body=f"您有 {count} 条待回复询盘",
        data={"type": "inquiry_pending", "count": str(count)},
    )


def notify_publish_failed(db: Session, user_id: str, task_id: str) -> dict[str, Any]:
    """notify_publish_failed。

    参数说明：
    :param db: 参数 db
    :param user_id: 参数 user_id
    :param task_id: 参数 task_id
    :return: 返回处理结果。
    """
    return send_to_user(
        db,
        user_id=user_id,
        title="出海计 · 发布提醒",
        body="有一条发布任务失败，请查看",
        data={"type": "publish_failed", "task_id": task_id},
    )
