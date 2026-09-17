# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""支付运维 — 渠道状态与微信平台证书缓存（超管/运维）。"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.core.no_fake_delivery import stamp_mock
from app.models.payment import PaymentOrder
from app.models.tenant import Tenant
from app.services.alipay_client import AlipayClient, load_alipay_config
from app.services.payment_service import PaymentService
from app.services.wechat_pay_v3 import (
    WeChatPayV3Client,
    load_wechat_pay_v3_config,
    payment_mock_allowed,
)
from app.services.wechat_platform_cert_service import (
    WeChatPlatformCertStore,
    _cache_ttl_seconds,
    _env_platform_pem,
    _env_platform_serial,
    build_cert_store,
)


def _strict_verify_enabled() -> bool:
    """_strict_verify_enabled。
    :return: 返回处理结果。
    """
    return os.getenv("PAYMENT_STRICT_VERIFY", "").lower() in ("1", "true", "yes")


def get_payment_ops_status(db: Session) -> dict[str, Any]:
    """聚合支付渠道与微信证书缓存快照（只读）。"""
    svc = PaymentService(db)
    wx_cfg = load_wechat_pay_v3_config(
        appid=svc.wechat.appid,
        mchid=svc.wechat.mchid,
        api_v3_key=svc.wechat.api_v3_key,
        serial_no=svc.wechat.serial_no,
        notify_url=svc.wechat.notify_url,
    )
    ali = AlipayClient(load_alipay_config())
    env_serial = _env_platform_serial()
    env_pem_configured = bool(_env_platform_pem())
    return {
        "environment": os.getenv("ENVIRONMENT", ""),
        "strict_verify": _strict_verify_enabled(),
        "mock_allowed": payment_mock_allowed(),
        "wechat": {
            "configured": wx_cfg.is_live or svc.wechat.is_configured,
            "v3_live": wx_cfg.is_live,
            "notify_url": wx_cfg.notify_url or "",
            "merchant_serial": wx_cfg.serial_no or "",
            "env_platform_serial": env_serial,
            "env_platform_pem_configured": env_pem_configured,
            "cert_cache_ttl_seconds": _cache_ttl_seconds(),
            "cert_cache": WeChatPlatformCertStore.cache_snapshot(),
        },
        "alipay": {
            "configured": ali.is_live,
            "gateway": ali.config.gateway if ali.config else "",
            "notify_url": (ali.config.notify_url if ali.config else "") or "",
        },
    }


def refresh_wechat_platform_certs() -> dict[str, Any]:
    """强制刷新微信平台证书缓存；未配置 live 密钥时仅清缓存并返回说明。"""
    store = build_cert_store()
    cleared_at = datetime.now(timezone.utc).isoformat()
    if not store.client.is_live:
        WeChatPlatformCertStore.clear_cache()
        return {
            "refreshed": False,
            "reason": "wechat_v3_not_live",
            "cleared_at": cleared_at,
            "cert_cache": WeChatPlatformCertStore.cache_snapshot(),
        }

    try:
        serials = list(store.fetch_certificates(force=True).keys())
    except Exception as exc:
        return {
            "refreshed": False,
            "reason": str(exc)[:300],
            "cleared_at": cleared_at,
            "cert_cache": WeChatPlatformCertStore.cache_snapshot(),
        }

    return {
        "refreshed": True,
        "serials": serials,
        "refreshed_at": datetime.now(timezone.utc).isoformat(),
        "cert_cache": WeChatPlatformCertStore.cache_snapshot(),
    }


def probe_alipay_sandbox(
    *,
    amount_yuan: float = 0.01,
    subject: str = "支付运维探针",
    run_precreate: bool = True,
) -> dict[str, Any]:
    """检查支付宝配置；live 时可选发起沙箱/生产 precreate（不落库）。"""
    client = AlipayClient(load_alipay_config())
    cfg = client.config
    report: dict[str, Any] = {
        "configured": client.is_live,
        "gateway": cfg.gateway if cfg else "",
        "notify_url": (cfg.notify_url if cfg else "") or "",
        "app_id_set": bool(cfg.app_id) if cfg else False,
        "precreate": None,
        "ok": client.is_live,
    }
    if not client.is_live:
        report["reason"] = "alipay_not_live"
        return report

    if not run_precreate:
        return report

    order_no = f"PROBE-{uuid.uuid4().hex[:12].upper()}"
    cents = max(1, int(round(amount_yuan * 100)))
    try:
        result = client.create_precreate(order_no, cents, subject[:256])
    except Exception as exc:
        report["ok"] = False
        report["precreate"] = {"ok": False, "error": str(exc)[:300]}
        return report

    report["precreate"] = {
        "ok": True,
        "order_no": order_no,
        "mock": bool(result.get("mock")),
        "code_url": result.get("code_url") or "",
        "qr_code": result.get("qr_code") or result.get("code_url") or "",
    }
    return report


def probe_wechat_native(
    *,
    amount_yuan: float = 0.01,
    subject: str = "支付运维探针",
    run_precreate: bool = True,
) -> dict[str, Any]:
    """检查微信 V3 配置；live 时可选 Native 预下单（不落库）。"""
    cfg = load_wechat_pay_v3_config()
    client = WeChatPayV3Client(cfg)
    report: dict[str, Any] = {
        "configured": cfg.is_live,
        "notify_url": cfg.notify_url or "",
        "appid_set": bool(cfg.appid),
        "mchid_set": bool(cfg.mchid),
        "precreate": None,
        "ok": cfg.is_live or payment_mock_allowed(),
    }
    if not cfg.is_live:
        if not payment_mock_allowed():
            report["ok"] = False
            report["reason"] = "wechat_not_live"
            return report
        if run_precreate:
            order_no = f"WXPROBE-{uuid.uuid4().hex[:12].upper()}"
            report["precreate"] = stamp_mock(
                {
                    "ok": True,
                    "order_no": order_no,
                    "code_url": f"weixin://wxpay/bizpayurl?pr=MOCK_{order_no}",
                },
                reason="wechat_probe_mock",
            )
        report["reason"] = "wechat_mock_mode"
        return report

    if not run_precreate:
        return report

    order_no = f"WXPROBE-{uuid.uuid4().hex[:12].upper()}"
    cents = max(1, int(round(amount_yuan * 100)))
    try:
        result = client.create_native(order_no, cents, subject[:127])
    except Exception as exc:
        report["ok"] = False
        report["precreate"] = {"ok": False, "error": str(exc)[:300]}
        return report

    report["precreate"] = {
        "ok": True,
        "order_no": order_no,
        "mock": bool(result.get("mock")),
        "code_url": result.get("code_url") or "",
    }
    return report


def _build_payment_check_payload(channel: str, order_no: str) -> dict[str, Any]:
    """构造模拟支付回调通知数据（alipay/wechat 两渠道）。"""
    if channel == "alipay":
        return {
            "out_trade_no": order_no,
            "trade_status": "TRADE_SUCCESS",
            "total_amount": "1.00",
        }
    return {
        "out_trade_no": order_no,
        "trade_state": "SUCCESS",
        "amount": {"total": 100},
    }


def _process_in_process_notify(
    svc: PaymentService,
    channel: str,
    order_no: str,
) -> bool:
    """进程内直接调用支付回调处理函数，返回是否入账成功。"""
    data = _build_payment_check_payload(channel, order_no)
    if channel == "alipay":
        paid = svc.process_alipay_notify(data)
    else:
        paid = svc.process_wechat_notify(data)
    return paid is not None


def _run_single_self_check_channel(
    db: Session,
    tenant: Tenant,
    channel: str,
) -> dict[str, Any]:
    """执行单个渠道的进程内支付闭环自检。"""
    order_no = f"STG-{channel.upper()}-{uuid.uuid4().hex[:8].upper()}"
    order = PaymentOrder(
        id=str(uuid.uuid4()),
        tenant_id=str(tenant.id),
        order_no=order_no,
        amount=100,
        channel=channel,
        subject="staging self-check",
        status="pending",
    )
    db.add(order)
    db.commit()
    svc = PaymentService(db)
    paid = _process_in_process_notify(svc, channel, order_no)
    db.refresh(order)
    ok = paid and order.status == "paid"
    return {
        "name": f"{channel}_notify_in_process",
        "ok": ok,
        "detail": f"order_no={order_no} status={order.status}",
    }


def run_staging_payment_self_check(db: Session) -> dict[str, Any]:
    """Staging 自检：配置 + 微信证书拉取 + 进程内 notify 闭环（不依赖外网回调）。"""
    checks: list[dict[str, Any]] = []
    svc = PaymentService(db)
    wx_cfg = load_wechat_pay_v3_config(
        appid=svc.wechat.appid,
        mchid=svc.wechat.mchid,
        api_v3_key=svc.wechat.api_v3_key,
        serial_no=svc.wechat.serial_no,
        notify_url=svc.wechat.notify_url,
    )
    ali = AlipayClient(load_alipay_config())
    checks.append(
        {
            "name": "wechat_v3_configured",
            "ok": wx_cfg.is_live,
            "detail": wx_cfg.notify_url or "missing notify_url",
        }
    )
    checks.append(
        {
            "name": "alipay_configured",
            "ok": ali.is_live,
            "detail": (ali.config.gateway if ali.config else "") or "not live",
        }
    )
    cert_result = refresh_wechat_platform_certs()
    checks.append(
        {
            "name": "wechat_cert_refresh",
            "ok": cert_result.get("refreshed") or cert_result.get("reason") == "wechat_v3_not_live",
            "detail": cert_result.get("reason") or f"serials={cert_result.get('serials', [])}",
        }
    )
    tenant = db.query(Tenant).filter(Tenant.is_active.is_(True)).first()
    if not tenant:
        checks.append({"name": "notify_loop", "ok": False, "detail": "no active tenant"})
        return {"ok": False, "checks": checks, "strict_verify": _strict_verify_enabled()}

    for channel in ("alipay", "wechat"):
        checks.append(_run_single_self_check_channel(db, tenant, channel))

    notify_ok = all(
        c["ok"] for c in checks if c["name"].endswith("_notify_in_process")
    )
    return {
        "ok": notify_ok,
        "checks": checks,
        "strict_verify": _strict_verify_enabled(),
        "mock_allowed": payment_mock_allowed(),
        "public_notify_hint": {
            "wechat": wx_cfg.notify_url or "设置 WECHAT_PAY_NOTIFY_URL 并暴露 HTTPS",
            "alipay": (ali.config.notify_url if ali.config else "") or "设置 ALIPAY_NOTIFY_URL 并暴露 HTTPS",
        },
    }


def discover_ngrok_public_url(
    *,
    api_base: str = "http://127.0.0.1:4040",
) -> Optional[str]:
    """读取本机 ngrok agent API，返回首个 https 公网 URL。"""
    import httpx
    try:
        with httpx.Client(timeout=3.0) as client:
            resp = client.get(f"{api_base.rstrip('/')}/api/tunnels")
        if resp.status_code >= 400:
            return None
        tunnels = resp.json().get("tunnels") or []
        for tunnel in tunnels:
            if tunnel.get("proto") == "https" and tunnel.get("public_url"):
                return str(tunnel["public_url"]).rstrip("/")
        for tunnel in tunnels:
            if tunnel.get("public_url"):
                return str(tunnel["public_url"]).rstrip("/")
    except Exception:
        return None
    return None


def check_public_health(public_url: str) -> dict[str, Any]:
    """探测公网根路径 /api/v1/health 是否可达。"""
    import httpx
    base = public_url.rstrip("/")
    url = f"{base}/api/v1/health"
    try:
        with httpx.Client(timeout=12.0, follow_redirects=True) as client:
            resp = client.get(url)
        body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        ok = resp.status_code == 200 and (body.get("code") == 0 or body.get("data", {}).get("status") == "ok")
        return {"ok": ok, "status_code": resp.status_code, "url": url}
    except Exception as exc:
        return {"ok": False, "url": url, "error": str(exc)[:300]}


def run_public_reachability_check(public_url: str = "") -> dict[str, Any]:
    """发现 ngrok（可选）并探测公网 health + 输出 notify 完整 URL。"""
    discovered = (public_url or "").strip().rstrip("/") or discover_ngrok_public_url() or ""
    if not discovered:
        return {
            "ok": False,
            "reason": "no_public_url",
            "discovered_from_ngrok": False,
            "hint": "启动 ngrok http 8001 或传入 public_url",
        }

    health = check_public_health(discovered)
    notify_urls = {
        "alipay": f"{discovered}/api/v1/payment/notify/alipay",
        "wechat": f"{discovered}/api/v1/payment/notify/wechat",
    }
    return {
        "ok": health.get("ok", False),
        "public_url": discovered,
        "discovered_from_ngrok": not bool((public_url or "").strip()),
        "health": health,
        "notify_urls": notify_urls,
    }


def compute_webhook_hmac_signature(order_no: str, amount: str, secret: str) -> str:
    """P0-07 通用回调 HMAC 签名（order_no:amount）。"""
    import hashlib
    import hmac
    payload = f"{order_no}:{amount}"
    return hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _webhook_secret() -> str:
    """_webhook_secret。
    :return: 返回处理结果。
    """
    return (os.getenv("PAYMENT_WEBHOOK_SECRET") or "").strip()


def _post_signed_public_notify(
    client: Any,
    *,
    base: str,
    channel: str,
    order_no: str,
    path_suffix: str,
) -> tuple[Any, str, str]:
    """返回 (response, notify_url, mode)。"""
    from app.services.alipay_client import AlipayClient, load_alipay_config
    url = f"{base.rstrip('/')}{path_suffix}"
    secret = _webhook_secret()
    ali = AlipayClient(load_alipay_config())
    if channel == "alipay" and ali.is_live:
        data = ali.sign_notify_payload(
            {
                "out_trade_no": order_no,
                "trade_status": "TRADE_SUCCESS",
                "total_amount": "1.00",
            }
        )
        return client.post(url, data=data), url, "strict_alipay_rsa_signed"

    if secret:
        if channel == "alipay":
            data = {
                "out_trade_no": order_no,
                "trade_status": "TRADE_SUCCESS",
                "total_amount": "1.00",
            }
            amount = "1.00"
        else:
            data = {
                "out_trade_no": order_no,
                "trade_state": "SUCCESS",
                "amount": "100",
            }
            amount = "100"
        sig = compute_webhook_hmac_signature(order_no, amount, secret)
        generic_url = f"{base.rstrip('/')}/api/v1/payment/notify"
        resp = client.post(
            generic_url,
            json={"channel": channel, "data": data, "signature": sig},
        )
        return resp, generic_url, "strict_webhook_hmac_signed"

    return None, url, "signed_skipped"


def _prepare_public_e2e_base(public_url: str, discover_ngrok: bool) -> tuple[str, dict[str, Any] | None]:
    """解析公网 base URL，失败时返回 (base, error_result)。"""
    base = (public_url or "").strip().rstrip("/")
    if not base and discover_ngrok:
        base = discover_ngrok_public_url() or ""
    if not base:
        return "", {
            "ok": False,
            "reason": "no_public_url",
            "discovered_from_ngrok": discover_ngrok,
            "hint": "启动 ngrok http 8001 或传入 public_url",
            "checks": [],
        }
    return base, None


def _require_active_tenant(db: Session, base: str) -> tuple[Tenant | None, dict[str, Any] | None]:
    """获取首个启用租户，缺失时返回错误结果。"""
    tenant = db.query(Tenant).filter(Tenant.is_active.is_(True)).first()
    if not tenant:
        return None, {
            "ok": False,
            "public_url": base,
            "reason": "no active tenant",
            "checks": [],
        }
    return tenant, None


def _create_public_notify_order(
    db: Session,
    tenant: Tenant,
    channel: str,
    prefix: str,
    subject: str,
) -> PaymentOrder:
    """创建公网 notify 探针订单并落库。"""
    order_no = f"{prefix}-{channel.upper()}-{uuid.uuid4().hex[:8].upper()}"
    order = PaymentOrder(
        id=str(uuid.uuid4()),
        tenant_id=str(tenant.id),
        order_no=order_no,
        amount=100,
        channel=channel,
        subject=subject,
        status="pending",
    )
    db.add(order)
    db.commit()
    return order


def _run_unsigned_notify_check(
    db: Session,
    tenant: Tenant,
    client: Any,
    *,
    base: str,
    channel: str,
    path_suffix: str,
    payload_builder,
    strict: bool,
    checks: list[dict[str, Any]],
) -> None:
    """执行单个渠道的未签名公网 notify 探测。"""
    order = _create_public_notify_order(
        db, tenant, channel, "PUB", "public notify e2e"
    )
    url = f"{base.rstrip('/')}{path_suffix}"
    try:
        if channel == "alipay":
            resp = client.post(url, data=payload_builder(order.order_no))
        else:
            resp = client.post(url, json=payload_builder(order.order_no))
    except Exception as exc:
        db.refresh(order)
        checks.append(
            {
                "channel": channel,
                "notify_url": url,
                "ok": False,
                "error": str(exc)[:300],
                "order_status": order.status,
            }
        )
        return

    db.refresh(order)
    if strict:
        if channel == "alipay":
            accepted = resp.text.strip() == "success" and order.status == "paid"
        else:
            body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
            accepted = body.get("code") == "SUCCESS" and order.status == "paid"
        checks.append(
            {
                "channel": channel,
                "notify_url": url,
                "mode": "strict_unsigned_reject",
                "status_code": resp.status_code,
                "order_status": order.status,
                "ok": not accepted,
            }
        )
    else:
        if channel == "alipay":
            body_ok = resp.text.strip() == "success"
        else:
            body_ok = resp.json().get("code") == "SUCCESS"
        checks.append(
            {
                "channel": channel,
                "notify_url": url,
                "mode": "relaxed_accept_unsigned",
                "status_code": resp.status_code,
                "body_ok": body_ok,
                "order_status": order.status,
                "ok": resp.status_code == 200 and body_ok and order.status == "paid",
            }
        )


def _run_signed_notify_check(
    db: Session,
    tenant: Tenant,
    client: Any,
    *,
    base: str,
    channel: str,
    path_suffix: str,
    signed_checks: list[dict[str, Any]],
) -> None:
    """执行单个渠道的已签名公网 notify 探测（RSA/HMAC）。"""
    order = _create_public_notify_order(
        db, tenant, channel, "SIG", "public notify signed e2e"
    )
    resp, notify_url, mode = _post_signed_public_notify(
        client,
        base=base,
        channel=channel,
        order_no=order.order_no,
        path_suffix=path_suffix,
    )
    if resp is None:
        signed_checks.append(
            {
                "channel": channel,
                "mode": mode,
                "ok": False,
                "skipped": True,
                "reason": "no_signing_material",
            }
        )
        return

    db.refresh(order)
    if mode == "strict_alipay_rsa_signed":
        body_ok = resp.text.strip() == "success"
    elif mode == "strict_webhook_hmac_signed":
        body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        body_ok = resp.status_code == 200 and body.get("code") == 0
    else:
        body_ok = False

    signed_checks.append(
        {
            "channel": channel,
            "notify_url": notify_url,
            "mode": mode,
            "status_code": resp.status_code,
            "body_ok": body_ok,
            "order_status": order.status,
            "ok": body_ok and order.status == "paid",
        }
    )


def _summarize_public_notify_result(
    *,
    strict: bool,
    checks: list[dict[str, Any]],
    signed_checks: list[dict[str, Any]],
) -> tuple[bool, str]:
    """汇总未签名/已签名检查结果，得出最终通过状态与验证模式。"""
    unsigned_ok = all(c.get("ok") for c in checks) and len(checks) == 2
    if strict:
        active_signed = [c for c in signed_checks if not c.get("skipped")]
        if active_signed:
            signed_ok = all(c.get("ok") for c in active_signed)
            return unsigned_ok and signed_ok, "strict_unsigned_reject+signed_accept"
        return unsigned_ok, "strict_unsigned_reject"
    return unsigned_ok, "relaxed_accept_unsigned"


def run_public_notify_e2e_check(
    db: Session,
    *,
    public_url: str = "",
    discover_ngrok: bool = False,
    try_signed: bool = False,
) -> dict[str, Any]:
    """经 ngrok 公网 URL 端到端 POST notify（验证隧道 + 回调路由 + 订单入账）。"""
    import httpx
    base, error = _prepare_public_e2e_base(public_url, discover_ngrok)
    if error is not None:
        return error

    reachability = run_public_reachability_check(base)
    if not reachability.get("ok"):
        return {
            "ok": False,
            "public_url": base,
            "discovered_from_ngrok": discover_ngrok and not bool((public_url or "").strip()),
            "health": reachability.get("health"),
            "reason": "public_health_failed",
            "checks": [],
        }

    tenant, tenant_error = _require_active_tenant(db, base)
    if tenant_error is not None:
        return tenant_error

    checks: list[dict[str, Any]] = []
    signed_checks: list[dict[str, Any]] = []
    strict = _strict_verify_enabled()
    with httpx.Client(timeout=25.0, follow_redirects=True) as client:
        for channel, path_suffix, payload_builder in (
            (
                "alipay",
                "/api/v1/payment/notify/alipay",
                lambda order_no: {
                    "out_trade_no": order_no,
                    "trade_status": "TRADE_SUCCESS",
                    "total_amount": "1.00",
                },
            ),
            (
                "wechat",
                "/api/v1/payment/notify/wechat",
                lambda order_no: {
                    "out_trade_no": order_no,
                    "trade_state": "SUCCESS",
                    "amount": {"total": 100},
                },
            ),
        ):
            _run_unsigned_notify_check(
                db, tenant, client,
                base=base,
                channel=channel,
                path_suffix=path_suffix,
                payload_builder=payload_builder,
                strict=strict,
                checks=checks,
            )

        can_sign = bool(_webhook_secret()) or AlipayClient(load_alipay_config()).is_live
        if strict and (try_signed or can_sign):
            for channel, path_suffix in (
                ("alipay", "/api/v1/payment/notify/alipay"),
                ("wechat", "/api/v1/payment/notify/wechat"),
            ):
                _run_signed_notify_check(
                    db, tenant, client,
                    base=base,
                    channel=channel,
                    path_suffix=path_suffix,
                    signed_checks=signed_checks,
                )

    notify_ok, verify_mode = _summarize_public_notify_result(
        strict=strict,
        checks=checks,
        signed_checks=signed_checks,
    )
    result: dict[str, Any] = {
        "ok": notify_ok,
        "strict_verify": strict,
        "verify_mode": verify_mode,
        "public_url": base,
        "discovered_from_ngrok": discover_ngrok and not bool((public_url or "").strip()),
        "health": reachability.get("health"),
        "notify_urls": reachability.get("notify_urls"),
        "checks": checks,
        "signed_checks": signed_checks,
    }
    if strict and not can_sign:
        result["signed_hint"] = "配置 PAYMENT_WEBHOOK_SECRET 或支付宝沙箱密钥以验收签名正向路径"
    return result

