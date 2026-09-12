#!/usr/bin/env python3
"""生成微信/支付宝 Native 收款二维码并跑通 mock 支付闭环。

import logging

logger = logging.getLogger(__name__)

用法:
  python scripts/payment_qrcode_demo.py
  python scripts/payment_qrcode_demo.py --base-url http://127.0.0.1:8001 --open

输出:
  backend/tmp/payment_qrcode_demo.html — 可在浏览器打开扫码（mock 码仅演示）
  stdout JSON 报告
"""

from __future__ import annotations

import argparse
import html
import json
import sys
import webbrowser
from pathlib import Path
from urllib.parse import quote

import httpx

BACKEND = Path(__file__).resolve().parents[1]
OUT_DIR = BACKEND / "tmp"
OUT_HTML = OUT_DIR / "payment_qrcode_demo.html"


def _login(client: httpx.Client, base: str, user: str, password: str) -> str:
    r = client.post(
        f"{base}/api/v1/auth/login",
        json={"username_or_email": user, "password": password},
    )
    r.raise_for_status()
    body = r.json()
    if body.get("code") != 0:
        raise RuntimeError(body.get("message") or "login failed")
    token = (body.get("data") or {}).get("access_token")
    if not token:
        raise RuntimeError("no access_token")
    return token


def _pick_plan(client: httpx.Client, base: str, headers: dict) -> dict:
    r = client.get(f"{base}/api/v1/payment/plans", headers=headers)
    r.raise_for_status()
    plans = r.json().get("data") or []
    for p in plans:
        if (p.get("price_monthly") or 0) > 0:
            return p
    raise RuntimeError("无付费套餐，请先 seed TenantPlan")


def _pick_tenant(client: httpx.Client, base: str, headers: dict) -> dict:
    r = client.get(f"{base}/api/v1/client/dashboard", headers=headers)
    if r.status_code < 400:
        body = r.json()
        tid = (body.get("data") or {}).get("tenant_id")
        if tid:
            return {"id": tid, "name": (body.get("data") or {}).get("brand", {}).get("company_name")}

    for path in ("/api/v1/tenants/", "/api/v1/tenants"):
        r = client.get(f"{base}{path}", headers=headers, params={"page_size": 10})
        if r.status_code >= 400:
            continue
        data = r.json().get("data") or {}
        items = (
            data.get("items")
            or data.get("tenants")
            or data.get("recent_tenants")
            or []
        )
        if isinstance(items, list) and items:
            active = next((t for t in items if t.get("is_active", True)), items[0])
            return active
    raise RuntimeError("无可用租户")


def _create_native(
    client: httpx.Client,
    base: str,
    headers: dict,
    *,
    tenant_id: str,
    plan_id: str,
    channel: str,
) -> dict:
    r = client.post(
        f"{base}/api/v1/payment/create-native",
        headers=headers,
        json={
            "tenant_id": tenant_id,
            "plan_id": plan_id,
            "billing_cycle": "monthly",
            "channel": channel,
        },
    )
    r.raise_for_status()
    body = r.json()
    if body.get("code") != 0:
        raise RuntimeError(body.get("message") or f"create-native {channel} failed")
    return body.get("data") or {}


def _mock_pay(client: httpx.Client, base: str, headers: dict, order_id: str) -> dict:
    r = client.post(
        f"{base}/api/v1/payment/mock-pay",
        headers=headers,
        json={"order_id": order_id},
    )
    r.raise_for_status()
    body = r.json()
    if body.get("code") != 0:
        raise RuntimeError(body.get("message") or "mock-pay failed")
    return body.get("data") or {}


def _order_status(client: httpx.Client, base: str, headers: dict, order_id: str) -> str:
    r = client.get(f"{base}/api/v1/payment/orders/{order_id}", headers=headers)
    r.raise_for_status()
    body = r.json()
    return ((body.get("data") or {}).get("status")) or ""


def _qr_img_url(code_url: str) -> str:
    return f"https://api.qrserver.com/v1/create-qr-code/?size=280x280&data={quote(code_url, safe='')}"


def _write_html(orders: list[dict]) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cards = []
    for item in orders:
        channel = item["channel"]
        data = item["order"]
        code_url = data.get("code_url") or ""
        mock = data.get("mock", False)
        paid = item.get("paid", False)
        cards.append(
            f"""
<section class="card">
  <h2>{html.escape(channel.upper())} Native 收款码</h2>
  <p class="meta">订单号：<code>{html.escape(data.get('order_no',''))}</code></p>
  <p class="meta">金额：¥{(data.get('amount',0)/100):.2f} · {'Mock 演示' if mock else 'Live'}</p>
  <p class="meta">支付后状态：<strong>{'paid ✓' if paid else data.get('status','')}</strong></p>
  {'<img alt="qr" src="' + html.escape(_qr_img_url(code_url)) + '" />' if code_url else '<p>无 code_url</p>'}
  <p class="url">{html.escape(code_url)}</p>
  <p class="hint">{'开发环境 mock 码无法用真 App 扫付；请用下方「模拟支付成功」或管理端 mock 按钮完成闭环。' if mock else '请用对应 App 扫码支付。'}</p>
</section>
"""
        )
    doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>支付二维码演示</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 960px; margin: 24px auto; padding: 0 16px; background: #f8fafc; }}
    h1 {{ font-size: 1.25rem; }}
    .card {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; margin: 16px 0; }}
    .meta {{ color: #64748b; font-size: 14px; }}
    .url {{ word-break: break-all; font-size: 12px; color: #475569; }}
    .hint {{ font-size: 13px; color: #b45309; background: #fffbeb; padding: 8px 12px; border-radius: 8px; }}
    img {{ display: block; margin: 12px 0; border: 1px solid #e2e8f0; border-radius: 8px; }}
  </style>
</head>
<body>
  <h1>微信 / 支付宝 Native 二维码（本地演示）</h1>
  <p>生成时间：本地脚本 payment_qrcode_demo.py</p>
  {''.join(cards)}
</body>
</html>
"""
    OUT_HTML.write_text(doc, encoding="utf-8")
    return OUT_HTML


def run_demo(
    base_url: str,
    admin_user: str,
    admin_pass: str,
    *,
    skip_mock_pay: bool = False,
) -> dict:
    base = base_url.rstrip("/")
    report: dict = {"base_url": base, "channels": [], "html": None, "ok": False}

    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        token = _login(client, base, admin_user, admin_pass)
        headers = {"Authorization": f"Bearer {token}"}
        plan = _pick_plan(client, base, headers)
        tenant = _pick_tenant(client, base, headers)
        tenant_id = str(tenant.get("id") or tenant.get("tenant_id") or "")
        if not tenant_id:
            raise RuntimeError("tenant id missing")

        report["tenant"] = {"id": tenant_id, "name": tenant.get("name")}
        report["plan"] = {"id": plan["id"], "name": plan.get("name"), "price_monthly": plan.get("price_monthly")}

        html_orders: list[dict] = []
        for channel in ("wechat", "alipay"):
            data = _create_native(
                client,
                base,
                headers,
                tenant_id=tenant_id,
                plan_id=plan["id"],
                channel=channel,
            )
            entry = {"channel": channel, "order": data, "paid": False}
            if not skip_mock_pay and data.get("mock") and data.get("id"):
                _mock_pay(client, base, headers, data["id"])
                status = _order_status(client, base, headers, data["id"])
                entry["paid"] = status == "paid"
                data["status"] = status
            html_orders.append(entry)
            report["channels"].append(
                {
                    "channel": channel,
                    "order_no": data.get("order_no"),
                    "order_id": data.get("id"),
                    "code_url": data.get("code_url"),
                    "mock": data.get("mock"),
                    "paid": entry["paid"],
                }
            )

        html_path = _write_html(html_orders)
        report["html"] = str(html_path)
        report["ok"] = all(c.get("code_url") for c in report["channels"]) and all(
            c.get("paid") for c in report["channels"]
        ) if not skip_mock_pay else all(c.get("code_url") for c in report["channels"])

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="微信/支付宝二维码演示 + mock 闭环")
    parser.add_argument("--base-url", default="http://127.0.0.1:8001")
    parser.add_argument("--admin-user", default="admin")
    parser.add_argument("--admin-pass", default="admin123")
    parser.add_argument("--skip-mock-pay", action="store_true", help="只生成二维码，不 mock 支付")
    parser.add_argument("--open", action="store_true", help="生成后打开 HTML")
    args = parser.parse_args()

    try:
        report = run_demo(
            args.base_url,
            args.admin_user,
            args.admin_pass,
            skip_mock_pay=args.skip_mock_pay,
        )
    except Exception as exc:
        logger.info(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1

    logger.info(json.dumps(report, ensure_ascii=False, indent=2))
    if args.open and report.get("html"):
        webbrowser.open(Path(report["html"]).as_uri())
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
