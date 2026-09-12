#!/usr/bin/env python3
"""Staging 外网 notify 验收 — 经 HTTP 打本地/公网回调端点（模拟网关 POST）。

import logging

logger = logging.getLogger(__name__)

用法:
  # 本机 HTTP（无需 ngrok，验证路由可达）
  python scripts/staging_notify_http_check.py --base-url http://127.0.0.1:8001

  # 经 ngrok 公网 URL 端到端 POST notify（需 ngrok 指向 base-url）
  python scripts/staging_notify_http_check.py \\
      --base-url http://127.0.0.1:8001 \\
      --discover-ngrok --via-public

生产/沙箱真实回调：将 ALIPAY_NOTIFY_URL / WECHAT_PAY_NOTIFY_URL 指到
  {public-url}/api/v1/payment/notify/alipay|wechat
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from pathlib import Path

import httpx

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("JWT_SECRET_KEY", "staging-notify-" + "x" * 24)


def run_http_notify_check(
    base_url: str,
    public_url: str = "",
    *,
    discover_ngrok: bool = False,
    via_public: bool = False,
    try_signed: bool = False,
) -> dict[str, object]:
    base = base_url.rstrip("/")
    public = (public_url or "").strip().rstrip("/")
    reachability: dict[str, object] | None = None

    from app.services.payment_ops_service import (
        discover_ngrok_public_url,
        run_public_notify_e2e_check,
        run_public_reachability_check,
    )

    if discover_ngrok and not public:
        public = discover_ngrok_public_url() or ""
    if public:
        reachability = run_public_reachability_check(public)

    if via_public and public:
        from app.db.session import SessionLocal

        db = SessionLocal()
        try:
            report = run_public_notify_e2e_check(
                db,
                public_url=public,
                discover_ngrok=False,
                try_signed=try_signed,
            )
        finally:
            db.close()
        report["base_url"] = base
        report["via_public"] = True
        report["public_reachability"] = reachability
        if reachability and reachability.get("notify_urls"):
            report["public_notify_hint"] = dict(reachability["notify_urls"])  # type: ignore[arg-type]
        if report.get("strict_verify"):
            report["hint"] = "严验签模式：验收标准为未签名回调被拒绝（ok=true 表示拒绝生效）"
        return report

    checks: list[dict[str, object]] = []

    from app.db.session import SessionLocal
    from app.models.payment import PaymentOrder
    from app.models.tenant import Tenant

    db = SessionLocal()
    try:
        tenant = db.query(Tenant).filter(Tenant.is_active.is_(True)).first()
        if not tenant:
            return {"ok": False, "error": "no active tenant", "checks": checks}

        with httpx.Client(timeout=20.0, follow_redirects=True) as client:
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
                order_no = f"HTTP-{channel.upper()}-{uuid.uuid4().hex[:8].upper()}"
                order = PaymentOrder(
                    id=str(uuid.uuid4()),
                    tenant_id=str(tenant.id),
                    order_no=order_no,
                    amount=100,
                    channel=channel,
                    subject="http notify check",
                    status="pending",
                )
                db.add(order)
                db.commit()

                url = f"{base}{path_suffix}"
                if channel == "alipay":
                    resp = client.post(url, data=payload_builder(order_no))
                    body_ok = resp.text.strip() == "success"
                else:
                    resp = client.post(url, json=payload_builder(order_no))
                    body_ok = resp.json().get("code") == "SUCCESS"

                db.refresh(order)
                checks.append(
                    {
                        "channel": channel,
                        "notify_url": url,
                        "status_code": resp.status_code,
                        "body_ok": body_ok,
                        "order_status": order.status,
                        "ok": resp.status_code == 200 and body_ok and order.status == "paid",
                    }
                )
    finally:
        db.close()

    ok = all(c.get("ok") for c in checks) and len(checks) == 2
    hint: dict[str, object] = {}
    if reachability and reachability.get("notify_urls"):
        hint = dict(reachability["notify_urls"])  # type: ignore[arg-type]
    elif public:
        hint = {
            "alipay": f"{public}/api/v1/payment/notify/alipay",
            "wechat": f"{public}/api/v1/payment/notify/wechat",
        }
    else:
        hint = {
            "ngrok_example": "ngrok http 8001",
            "then_set_env": [
                "ALIPAY_NOTIFY_URL=https://<host>/api/v1/payment/notify/alipay",
                "WECHAT_PAY_NOTIFY_URL=https://<host>/api/v1/payment/notify/wechat",
            ],
        }

    return {
        "ok": ok,
        "base_url": base,
        "public_url": public or None,
        "via_public": False,
        "public_reachability": reachability,
        "checks": checks,
        "public_notify_hint": hint,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Staging HTTP notify 验收")
    parser.add_argument("--base-url", default="http://127.0.0.1:8001")
    parser.add_argument("--public-url", default="", help="ngrok 公网根 URL（写入报告）")
    parser.add_argument(
        "--discover-ngrok",
        action="store_true",
        help="从本机 ngrok API (127.0.0.1:4040) 自动发现 public URL",
    )
    parser.add_argument(
        "--via-public",
        action="store_true",
        help="经公网 URL（ngrok）POST notify，验证隧道端到端",
    )
    parser.add_argument(
        "--try-signed",
        action="store_true",
        help="严验签时额外验收签名正向路径（PAYMENT_WEBHOOK_SECRET / 支付宝密钥）",
    )
    args = parser.parse_args()

    try:
        report = run_http_notify_check(
            args.base_url,
            args.public_url,
            discover_ngrok=args.discover_ngrok,
            via_public=args.via_public,
            try_signed=args.try_signed,
        )
    except Exception as exc:
        logger.info(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1

    logger.info(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
