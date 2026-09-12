"""租户独立域 SSL 申请状态机（mock / HTTP 委托）。"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.core.config import settings
from app.models.tenant import Tenant

_SSL_KEY = "domain_ssl"


def _load_settings(tenant: Tenant) -> dict[str, Any]:
    """_load_settings。

    参数说明：
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    if not tenant.settings:
        return {}
    try:
        data = json.loads(tenant.settings)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def _save_settings(tenant: Tenant, data: dict[str, Any]) -> None:
    """_save_settings。

    参数说明：
    :param tenant: 参数 tenant
    :param data: 参数 data
    :return: 返回处理结果。
    """
    tenant.settings = json.dumps(data, ensure_ascii=False)


def get_ssl_record(tenant: Tenant, domain: str) -> dict[str, Any]:
    """get_ssl_record。

    参数说明：
    :param tenant: 参数 tenant
    :param domain: 参数 domain
    :return: 返回处理结果。
    """
    data = _load_settings(tenant)
    records = data.get(_SSL_KEY, {})
    return records.get(domain.lower(), {"status": "none"})


def list_ssl_records(tenant: Tenant) -> dict[str, dict[str, Any]]:
    """list_ssl_records。

    参数说明：
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    return _load_settings(tenant).get(_SSL_KEY, {})


def _provider() -> str:
    """_provider。
    :return: 返回处理结果。
    """
    return (
        getattr(settings, "SSL_PROVIDER", None) or os.getenv("SSL_PROVIDER", "mock")
    ).lower()


def _certbot_issue(domain: str) -> dict[str, Any]:
    """本机 certbot 签发（生产机设置 SSL_PROVIDER=certbot + CERTBOT_EMAIL）。"""
    if not shutil.which("certbot"):
        return {"status": "failed", "error": "未找到 certbot 可执行文件"}
    email = os.getenv("CERTBOT_EMAIL", "").strip()
    if not email:
        return {"status": "failed", "error": "CERTBOT_EMAIL 未配置"}
    webroot = os.getenv("CERTBOT_WEBROOT", "").strip()
    cmd = [
        "certbot",
        "certonly",
        "--non-interactive",
        "--agree-tos",
        "--email",
        email,
        "-d",
        domain,
    ]
    if webroot:
        cmd.extend(["--webroot", "-w", webroot])
    else:
        cmd.extend(
            ["--preferred-challenges", os.getenv("CERTBOT_CHALLENGE", "http")]
        )
    if os.getenv("CERTBOT_DRY_RUN", "").lower() in ("1", "true", "yes"):
        cmd.append("--dry-run")
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=int(os.getenv("CERTBOT_TIMEOUT_SEC", "300")),
            check=False,
        )
        if proc.returncode != 0:
            return {
                "status": "failed",
                "error": (proc.stderr or proc.stdout or "certbot failed")[:500],
            }
        now = datetime.now(timezone.utc)
        return {
            "status": "active",
            "issued_at": now.isoformat(),
            "expires_at": (now + timedelta(days=90)).isoformat(),
            "provider": "certbot",
        }
    except subprocess.TimeoutExpired:
        return {"status": "failed", "error": "certbot 超时"}
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}


def request_certificate(tenant: Tenant, domain: str) -> dict[str, Any]:
    """提交证书申请。"""
    domain = domain.strip().lower()
    now = datetime.now(timezone.utc)
    data = _load_settings(tenant)
    records = data.setdefault(_SSL_KEY, {})
    provider = _provider()
    record: dict[str, Any] = {
        "status": "pending",
        "provider": provider,
        "requested_at": now.isoformat(),
        "expires_at": None,
        "error": None,
    }
    webhook = getattr(settings, "ACME_WEBHOOK_URL", None) or os.getenv("ACME_WEBHOOK_URL")
    if provider in ("http", "acme", "certbot") and webhook:
        try:
            with httpx.Client(timeout=20.0) as client:
                resp = client.post(
                    webhook,
                    json={
                        "action": "issue",
                        "provider": provider,
                        "domain": domain,
                        "tenant_id": str(tenant.id),
                    },
                )
                resp.raise_for_status()
                body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                record["status"] = body.get("status", "pending")
                record["job_id"] = body.get("job_id")
        except Exception as exc:
            record["status"] = "failed"
            record["error"] = str(exc)
    elif provider in ("mock", "dev_local"):
        if provider == "dev_local" or domain.endswith(".test.local") or domain.endswith(".localhost"):
            record["status"] = "active"
            record["issued_at"] = now.isoformat()
            record["expires_at"] = (now + timedelta(days=90)).isoformat()
            record["note"] = "dev_local 演示域即时签发"
        else:
            record["status"] = "pending"
            record["auto_activate_after_sec"] = 5
    elif provider in ("acme", "certbot"):
        if webhook:
            pass  # handled above
        else:
            bot = _certbot_issue(domain)
            record["status"] = bot.get("status", "failed")
            if bot.get("error"):
                record["error"] = bot["error"]
            if bot.get("status") == "active":
                record["issued_at"] = bot.get("issued_at")
                record["expires_at"] = bot.get("expires_at")
            elif provider == "acme" and record["status"] == "failed":
                record["hint"] = (
                    "配置 ACME_WEBHOOK_URL 或改用 SSL_PROVIDER=certbot 并设置 CERTBOT_EMAIL"
                )

    records[domain] = record
    _save_settings(tenant, data)
    return record


def refresh_pending(tenant: Tenant) -> list[dict[str, Any]]:
    """将到期的 pending 提升为 active（mock）。"""
    data = _load_settings(tenant)
    records = data.get(_SSL_KEY, {})
    changed: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc)
    for domain, rec in records.items():
        if rec.get("status") != "pending":
            continue
        requested = rec.get("requested_at")
        if not requested:
            continue
        try:
            req_dt = datetime.fromisoformat(requested.replace("Z", "+00:00"))
        except ValueError:
            continue
        auto_sec = int(rec.get("auto_activate_after_sec") or 300)
        prov = _provider()
        if prov == "mock" and (now - req_dt).total_seconds() >= auto_sec:
            rec["status"] = "active"
            rec["issued_at"] = now.isoformat()
            rec["expires_at"] = (now + timedelta(days=90)).isoformat()
            changed.append({"domain": domain, **rec})
            continue
        webhook = getattr(settings, "ACME_WEBHOOK_URL", None) or os.getenv("ACME_WEBHOOK_URL")
        job_id = rec.get("job_id")
        if prov in ("http", "acme", "certbot") and webhook and job_id:
            try:
                with httpx.Client(timeout=10.0) as client:
                    poll = client.get(
                        webhook.rstrip("/") + f"/status/{job_id}",
                    )
                    if poll.status_code == 200:
                        body = poll.json()
                        st = body.get("status")
                        if st == "active":
                            rec["status"] = "active"
                            rec["issued_at"] = body.get("issued_at") or now.isoformat()
                            rec["expires_at"] = body.get("expires_at")
                            changed.append({"domain": domain, **rec})
                        elif st == "failed":
                            rec["status"] = "failed"
                            rec["error"] = body.get("error")
                            changed.append({"domain": domain, **rec})
            except Exception:
                pass

    if changed:
        data[_SSL_KEY] = records
        _save_settings(tenant, data)
    return changed


def ssl_status_for_domain(tenant: Tenant, domain: str) -> str:
    """ssl_status_for_domain。

    参数说明：
    :param tenant: 参数 tenant
    :param domain: 参数 domain
    :return: 返回处理结果。
    """
    refresh_pending(tenant)
    return get_ssl_record(tenant, domain).get("status", "none")
