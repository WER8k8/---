#!/usr/bin/env python3
"""支付宝沙箱 / 本地 E2E — 边界可控的一键联调。

import logging

logger = logging.getLogger(__name__)

职责范围（刻意不做）：
  - 不自动启动 ngrok / 隧道
  - 不驱动沙箱 App 真实扫码（需人工）
  - 不在 production 环境执行（ENVIRONMENT=production 时拒绝）

默认模式 --in-process：直接调用 PaymentService，无需后端进程。
可选 --http：向已运行的后端 POST notify（集成测试）。

用法:
  python scripts/alipay_sandbox_e2e.py
  python scripts/alipay_sandbox_e2e.py --http --base-url http://127.0.0.1:8001
  python scripts/alipay_sandbox_e2e.py --public-url https://xxxx.ngrok-free.app
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
os.environ.setdefault("JWT_SECRET_KEY", "alipay-e2e-" + "x" * 24)


def _guard_environment() -> None:
    if os.getenv("ENVIRONMENT", "").lower() == "production":
        raise SystemExit("拒绝在 production 环境运行 alipay_sandbox_e2e")


def _create_pending_order() -> tuple[str, str, int]:
    from app.db.session import SessionLocal
    from app.models.tenant import Tenant, TenantPlan
    from app.services.payment_service import PaymentService

    db = SessionLocal()
    try:
        plan = TenantPlan(
            id=str(uuid.uuid4()),
            name="E2E基础",
            code=f"e2e-{uuid.uuid4().hex[:4]}",
            price_monthly=9900,
            max_ai_quota=5000,
            is_active=True,
        )
        db.add(plan)
        tenant = Tenant(
            id=str(uuid.uuid4()),
            name="E2E租户",
            domain=f"e2e-{uuid.uuid4().hex[:6]}.local",
            plan_id=plan.id,
            status="active",
            is_active=True,
        )
        db.add(tenant)
        db.commit()

        result = PaymentService(db).create_token_pack_native(
            tenant_id=str(tenant.id),
            pack_id="pack_10k",
            channel="alipay",
        )
        order = result["order"]
        return str(order.id), order.order_no, int(order.amount)
    finally:
        db.close()


def _notify_payload(order_no: str, amount_cents: int) -> dict[str, str]:
    return {
        "out_trade_no": order_no,
        "trade_status": "TRADE_SUCCESS",
        "total_amount": f"{amount_cents / 100:.2f}",
        "app_id": os.getenv("ALIPAY_APP_ID") or "mock_app",
    }


def _process_in_process(payload: dict[str, str]) -> dict:
    from app.db.session import SessionLocal
    from app.services.payment_service import PaymentService

    db = SessionLocal()
    try:
        order = PaymentService(db).process_alipay_notify(payload)
        return {"ok": order is not None, "mode": "in-process"}
    finally:
        db.close()


def _process_http(base_url: str, payload: dict[str, str]) -> dict:
    notify_url = f"{base_url.rstrip('/')}/api/v1/payment/notify/alipay"
    with httpx.Client(timeout=20.0) as http:
        resp = http.post(notify_url, data=payload)
    return {
        "ok": resp.status_code == 200 and resp.text.strip() == "success",
        "mode": "http",
        "status_code": resp.status_code,
        "body": resp.text.strip(),
        "notify_url": notify_url,
    }


def _verify_order_paid(order_id: str) -> dict:
    from app.db.session import SessionLocal
    from app.models.payment import PaymentOrder

    db = SessionLocal()
    try:
        order = db.query(PaymentOrder).filter(PaymentOrder.id == order_id).first()
        if not order:
            return {"ok": False, "reason": "order_not_found"}
        return {
            "ok": order.status == "paid",
            "status": order.status,
            "order_no": order.order_no,
        }
    finally:
        db.close()


def run_e2e(*, base_url: str, public_url: str, use_http: bool) -> dict:
    _guard_environment()
    os.environ.setdefault("PAYMENT_STRICT_VERIFY", "0")

    from scripts import alipay_sandbox_probe as probe

    config_ok = probe.cmd_check() == 0
    order_id, order_no, amount_cents = _create_pending_order()
    payload = _notify_payload(order_no, amount_cents)

    notify_result = _process_http(base_url, payload) if use_http else _process_in_process(payload)
    verify = _verify_order_paid(order_id)

    return {
        "config_ok": config_ok,
        "order_id": order_id,
        "order_no": order_no,
        "notify": notify_result,
        "order_paid": verify,
        "public_notify_hint": (
            f"{public_url.rstrip('/')}/api/v1/payment/notify/alipay"
            if public_url
            else None
        ),
        "next_manual_steps": [
            "沙箱真实扫码：ALIPAY_GATEWAY=https://openapi.alipaydev.com/gateway.do",
            "python scripts/alipay_sandbox_probe.py --precreate",
            "ngrok 暴露后设置 ALIPAY_NOTIFY_URL=public_notify_hint",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="支付宝本地 E2E")
    parser.add_argument("--http", action="store_true", help="经 HTTP 调 notify（需后端运行）")
    parser.add_argument("--base-url", default="http://127.0.0.1:8001")
    parser.add_argument("--public-url", default="", help="仅输出建议公网 notify，不启动隧道")
    args = parser.parse_args()

    report = run_e2e(
        base_url=args.base_url,
        public_url=args.public_url,
        use_http=args.http,
    )
    logger.info(json.dumps(report, ensure_ascii=False, indent=2))
    ok = report.get("notify", {}).get("ok") and report.get("order_paid", {}).get("ok")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
