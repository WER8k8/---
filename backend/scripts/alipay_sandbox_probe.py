#!/usr/bin/env python3
"""支付宝沙箱 / 本地联调探针。

import logging

logger = logging.getLogger(__name__)

用法:
  # 检查配置是否齐全
  python scripts/alipay_sandbox_probe.py --check

  # 沙箱 precreate（需 .env 中 ALIPAY_* 与 ALIPAY_GATEWAY=沙箱地址）
  python scripts/alipay_sandbox_probe.py --precreate --amount 99 --subject "联调测试"

  # 向本地回调 POST 模拟通知（PAYMENT_STRICT_VERIFY=0 时无需真实签名）
  python scripts/alipay_sandbox_probe.py --mock-notify \\
      --notify-url http://127.0.0.1:8001/api/v1/payment/notify/alipay \\
      --order-no ORD123 --amount 99.00
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

import httpx

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("JWT_SECRET_KEY", "alipay-probe-" + "x" * 24)


def _load_client():
    from app.services.alipay_client import AlipayClient, load_alipay_config

    cfg = load_alipay_config()
    return AlipayClient(cfg), cfg


def cmd_check() -> int:
    client, cfg = _load_client()
    report = {
        "app_id": bool(cfg.app_id),
        "private_key": bool(cfg.private_key_pem),
        "alipay_public_key": bool(cfg.alipay_public_key_pem),
        "notify_url": cfg.notify_url or "(未设置)",
        "gateway": cfg.gateway,
        "is_live": client.is_live,
    }
    logger.info(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if client.is_live else 1


def cmd_precreate(amount_yuan: float, subject: str) -> int:
    client, cfg = _load_client()
    if not client.is_live:
        logger.info('"支付宝未配置完整，无法 precreate",')
        return 1
    order_no = f"PROBE-{uuid.uuid4().hex[:12].upper()}"
    cents = int(round(amount_yuan * 100))
    try:
        result = client.create_precreate(order_no, cents, subject)
    except Exception as exc:
        logger.info(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    logger.info(
        json.dumps(
            {
                "ok": True,
                "order_no": order_no,
                "gateway": cfg.gateway,
                "mock": result.get("mock", False),
                "code_url": result.get("code_url"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def cmd_mock_notify(notify_url: str, order_no: str, amount: str) -> int:
    """向本地 notify 端点发送模拟 TRADE_SUCCESS（开发环境 strict=0）。"""
    client, cfg = _load_client()
    params = {
        "notify_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "notify_type": "trade_status_sync",
        "notify_id": uuid.uuid4().hex,
        "app_id": cfg.app_id or "mock_app",
        "charset": "utf-8",
        "version": "1.0",
        "sign_type": "RSA2",
        "out_trade_no": order_no,
        "total_amount": amount,
        "trade_status": "TRADE_SUCCESS",
    }
    if client.is_live and cfg.private_key_pem:
        from app.services.alipay_client import _rsa2_sign, _sign_content

        params["sign"] = _rsa2_sign(cfg.private_key_pem, _sign_content(params))
    else:
        params["sign"] = "MOCK_SIGN"

    with httpx.Client(timeout=15.0) as http:
        resp = http.post(notify_url, data=params)
    logger.info(
        json.dumps(
            {
                "status_code": resp.status_code,
                "body": resp.text,
                "order_no": order_no,
                "notify_url": notify_url,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if resp.status_code == 200 and resp.text.strip() == "success" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="支付宝沙箱 / 本地联调探针")
    parser.add_argument("--check", action="store_true", help="检查 ALIPAY_* 配置")
    parser.add_argument("--precreate", action="store_true", help="沙箱 precreate 下单")
    parser.add_argument("--mock-notify", action="store_true", help="POST 模拟异步通知")
    parser.add_argument("--amount", type=float, default=99.0, help="precreate 金额（元）")
    parser.add_argument("--subject", default="沙箱联调", help="precreate 标题")
    parser.add_argument("--notify-url", default="http://127.0.0.1:8001/api/v1/payment/notify/alipay")
    parser.add_argument("--order-no", default="", help="mock-notify 商户订单号")
    args = parser.parse_args()

    if args.check:
        return cmd_check()
    if args.precreate:
        return cmd_precreate(args.amount, args.subject)
    if args.mock_notify:
        order_no = args.order_no or f"MOCK-{uuid.uuid4().hex[:10].upper()}"
        return cmd_mock_notify(args.notify_url, order_no, f"{args.amount:.2f}")
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
