"""生产就绪失败时推送运维告警（飞书 Webhook）。"""

from __future__ import annotations

import os
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.production_readiness_service import (
    check_mounted_routes,
    run_readiness_checks,
)


def _webhook_url(override: str | None = None) -> str:
    """_webhook_url。

    参数说明：
    :param override: 参数 override
    :return: 返回处理结果。
    """
    return (
        (override or "").strip()
        or os.getenv("OPS_READINESS_WEBHOOK_URL", "").strip()
        or (settings.FEISHU_WEBHOOK_URL or "").strip()
    )


def notify_readiness_if_unready(
    db: Session | None,
    *,
    webhook_url: str | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """未就绪时发送飞书卡片；就绪则跳过（除非 force）。"""
    report = run_readiness_checks(db)
    report.add(check_mounted_routes())
    data = report.to_dict()
    if data["ready"] and not force:
        return {"sent": False, "ready": True, "report": data}

    url = _webhook_url(webhook_url)
    if not url:
        return {
            "sent": False,
            "ready": data["ready"],
            "reason": "no_webhook_configured",
            "report": data,
        }

    failed = [c for c in data["checks"] if c["status"] == "fail"]
    warn = [c for c in data["checks"] if c["status"] == "warn"]
    lines = []
    for c in failed[:8]:
        lines.append(f"- **[FAIL]** {c['title']}: {c['message']}")
    for c in warn[:5]:
        lines.append(f"- [warn] {c['title']}: {c['message']}")
    body = "\n".join(lines) or "就绪检查未通过，详见 score"
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "⚠️ 生产就绪检查未通过",
                },
                "template": "red" if failed else "yellow",
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": (
                            f"环境: **{data['environment']}**\n"
                            f"得分: pass={data['score']['pass']} "
                            f"warn={data['score']['warn']} "
                            f"fail={data['score']['fail']}\n\n{body}"
                        ),
                    },
                },
            ],
        },
    }
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.post(url, json=payload)
            ok = resp.status_code < 400
    except Exception as exc:
        return {
            "sent": False,
            "ready": data["ready"],
            "reason": str(exc),
            "report": data,
        }

    return {"sent": ok, "ready": data["ready"], "report": data}
