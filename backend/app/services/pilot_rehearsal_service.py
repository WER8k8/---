"""保温厂试点：HTTPS 演示域与七步②彩排检查。"""

from __future__ import annotations

import socket
import ssl
from datetime import datetime, timezone
from typing import Any
import httpx

from app.core.config import settings


def _probe_https(domain: str, timeout: float = 12.0) -> dict[str, Any]:
    """_probe_https。

    参数说明：
    :param domain: 参数 domain
    :param timeout: 参数 timeout
    :return: 返回处理结果。
    """
    domain = domain.strip().lower()
    url = f"https://{domain}/"
    out: dict[str, Any] = {
        "domain": domain,
        "url": url,
        "https_ok": False,
        "status_code": None,
        "cert_valid": False,
        "error": None,
    }
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True, verify=True) as client:
            resp = client.get(url)
            out["status_code"] = resp.status_code
            out["https_ok"] = resp.status_code < 500
    except Exception as exc:
        out["error"] = str(exc)[:500]
        return out

    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                if cert:
                    out["cert_valid"] = True
                    out["cert_not_after"] = cert.get("notAfter")
    except Exception as exc:
        if not out.get("error"):
            out["cert_error"] = str(exc)[:300]

    out["ready_for_pilot"] = bool(
        out.get("https_ok") and out.get("status_code", 0) < 400 and out.get("cert_valid")
    )
    return out


def demo_https_rehearsal_report(domain: str | None = None) -> dict[str, Any]:
    """UBX-OPS-01 / P0-02：演示独立域 HTTPS 彩排结果。"""
    target = (domain or getattr(settings, "DEMO_HTTPS_DOMAIN", None) or "").strip()
    now = datetime.now(timezone.utc).isoformat()
    if not target:
        return {
            "checked_at": now,
            "configured": False,
            "message": "未配置 DEMO_HTTPS_DOMAIN，请在环境变量或请求参数传入演示域。",
            "checklist": _ops_checklist(),
        }
    probe = _probe_https(target)
    return {
        "checked_at": now,
        "configured": True,
        "domain": target,
        "probe": probe,
        "ready_for_pilot": probe.get("ready_for_pilot", False),
        "checklist": _ops_checklist(),
        "next_steps": _next_steps(probe),
    }


def _ops_checklist() -> list[dict[str, str]]:
    """_ops_checklist。
    :return: 返回处理结果。
    """
    return [
        {"id": "dns", "label": "域名 CNAME/A 已指向租户站或网关"},
        {"id": "https", "label": "HTTPS 可访问且无证书警告"},
        {"id": "phone", "label": "询盘表单手机号必填"},
        {"id": "source", "label": "source_channel 可在后台筛选"},
        {"id": "export", "label": "每周可导出 inquiries CSV 复盘"},
    ]


def _next_steps(probe: dict[str, Any]) -> list[str]:
    """_next_steps。

    参数说明：
    :param probe: 参数 probe
    :return: 返回处理结果。
    """
    steps = []
    if not probe.get("cert_valid"):
        steps.append("在「独立域」触发 SSL 签发：SSL_PROVIDER=acme|certbot 并配置 ACME_WEBHOOK_URL 或 CERTBOT_EMAIL")
    if int(probe.get("status_code") or 0) >= 400:
        steps.append("检查 Nuxt/API 反代与租户 Host 绑定（domain.py verify）")
    if probe.get("ready_for_pilot"):
        steps.append("彩排：访客提交询盘 → 后台 inquiries 出现带手机号记录")
    return steps
