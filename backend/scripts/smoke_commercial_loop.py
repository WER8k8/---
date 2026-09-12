#!/usr/bin/env python3
"""商业闭环冒烟 — 验证 P0–P6 关键 API 是否可用。

import logging

logger = logging.getLogger(__name__)

用法:
  python scripts/smoke_commercial_loop.py
  python scripts/smoke_commercial_loop.py --base-url http://127.0.0.1:8001
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

import httpx

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))


def _ok(name: str, passed: bool, detail: str = "") -> dict:
    return {"name": name, "ok": passed, "detail": detail}


def run_smoke(base_url: str, admin_user: str, admin_pass: str) -> dict:
    base = base_url.rstrip("/")
    results: list[dict] = []

    with httpx.Client(timeout=20.0, follow_redirects=True) as client:
        # 1. 健康检查
        try:
            r = client.get(f"{base}/api/v1/health")
            results.append(_ok("health", r.status_code == 200, r.text[:80]))
        except Exception as exc:
            results.append(_ok("health", False, str(exc)))
            return {"ok": False, "results": results, "error": "backend unreachable"}

        # 2. 落地页公开询盘
        phone = f"138{uuid.uuid4().int % 100_000_000:08d}"
        try:
            r = client.post(
                f"{base}/api/v1/inquiries/public",
                json={
                    "name": "冒烟测试",
                    "phone": phone,
                    "message": "P6 smoke inquiry",
                    "product": "测试公司",
                    "source_channel": "platform_landing",
                    "landing_path": "/landing",
                },
            )
            body = r.json()
            inquiry_id = (body.get("data") or {}).get("id")
            results.append(
                _ok(
                    "landing_inquiry",
                    r.status_code == 200 and body.get("code") == 0 and bool(inquiry_id),
                    f"id={inquiry_id}",
                )
            )
        except Exception as exc:
            inquiry_id = None
            results.append(_ok("landing_inquiry", False, str(exc)))

        # 3. 管理员登录
        token = ""
        try:
            r = client.post(
                f"{base}/api/v1/auth/login",
                json={"username_or_email": admin_user, "password": admin_pass},
            )
            body = r.json()
            token = (body.get("data") or {}).get("access_token") or ""
            results.append(_ok("admin_login", bool(token), admin_user))
        except Exception as exc:
            results.append(_ok("admin_login", False, str(exc)))

        headers = {"Authorization": f"Bearer {token}"} if token else {}

        # 4. 询盘 unified 列表
        try:
            r = client.get(f"{base}/api/v1/inquiries/unified?page_size=5", headers=headers)
            body = r.json()
            items = (body.get("data") or {}).get("items") or []
            results.append(
                _ok("inquiries_unified", r.status_code == 200 and body.get("code") == 0, f"count={len(items)}")
            )
        except Exception as exc:
            results.append(_ok("inquiries_unified", False, str(exc)))

        # 5. 改派候选人
        try:
            r = client.get(f"{base}/api/v1/inquiries/assignees", headers=headers)
            body = r.json()
            assignees = body.get("data") or []
            results.append(
                _ok("inquiry_assignees", r.status_code == 200 and body.get("code") == 0, f"pool={len(assignees)}")
            )
        except Exception as exc:
            assignees = []
            results.append(_ok("inquiry_assignees", False, str(exc)))

        # 6. 改派 + 审计历史
        if inquiry_id and token and assignees:
            target = assignees[0]["id"]
            try:
                r = client.put(
                    f"{base}/api/v1/inquiries/{inquiry_id}/assign",
                    headers=headers,
                    json={"assigned_to": target},
                )
                body = r.json()
                assign_ok = r.status_code == 200 and body.get("code") == 0
                results.append(_ok("inquiry_assign", assign_ok, body.get("message", "")))

                r2 = client.get(
                    f"{base}/api/v1/inquiries/{inquiry_id}/assignment-history",
                    headers=headers,
                )
                body2 = r2.json()
                hist = body2.get("data") or []
                results.append(
                    _ok(
                        "assignment_history",
                        r2.status_code == 200 and body2.get("code") == 0 and len(hist) >= 1,
                        f"records={len(hist)}",
                    )
                )
            except Exception as exc:
                results.append(_ok("inquiry_assign", False, str(exc)))
                results.append(_ok("assignment_history", False, str(exc)))
        else:
            results.append(_ok("inquiry_assign", False, "skipped: missing inquiry/token/assignees"))
            results.append(_ok("assignment_history", False, "skipped"))

        # 7. 支付渠道状态
        try:
            r = client.get(f"{base}/api/v1/payment/channels/status", headers=headers)
            body = r.json()
            data = body.get("data") or {}
            results.append(
                _ok(
                    "payment_channels",
                    r.status_code == 200 and body.get("code") == 0 and "wechat" in data,
                    json.dumps(data, ensure_ascii=False)[:120],
                )
            )
        except Exception as exc:
            results.append(_ok("payment_channels", False, str(exc)))

        # 8. 支付宝 mock notify（HTTP）
        order_no = f"SMK-{uuid.uuid4().hex[:10].upper()}"
        try:
            sys.path.insert(0, str(BACKEND))
            from app.db.session import SessionLocal
            from app.models.payment import PaymentOrder
            from app.models.tenant import Tenant, TenantPlan

            db = SessionLocal()
            try:
                plan = db.query(TenantPlan).filter(TenantPlan.is_active.is_(True)).first()
                if not plan:
                    results.append(_ok("alipay_notify", False, "no active plan"))
                else:
                    tenant = db.query(Tenant).filter(Tenant.is_active.is_(True)).first()
                    if not tenant:
                        results.append(_ok("alipay_notify", False, "no active tenant"))
                    else:
                        order = PaymentOrder(
                            id=str(uuid.uuid4()),
                            tenant_id=str(tenant.id),
                            order_no=order_no,
                            amount=9900,
                            channel="alipay",
                            subject="smoke",
                            status="pending",
                        )
                        db.add(order)
                        db.commit()
                        r = client.post(
                            f"{base}/api/v1/payment/notify/alipay",
                            data={
                                "out_trade_no": order_no,
                                "trade_status": "TRADE_SUCCESS",
                                "total_amount": "99.00",
                            },
                        )
                        db.refresh(order)
                        results.append(
                            _ok(
                                "alipay_notify",
                                r.text.strip() == "success" and order.status == "paid",
                                f"body={r.text.strip()} status={order.status}",
                            )
                        )
            finally:
                db.close()
        except Exception as exc:
            results.append(_ok("alipay_notify", False, str(exc)))

        # 9. 微信 notify JSON
        order_no_wx = f"WXS-{uuid.uuid4().hex[:10].upper()}"
        try:
            from app.db.session import SessionLocal
            from app.models.payment import PaymentOrder
            from app.models.tenant import Tenant

            db = SessionLocal()
            try:
                tenant = db.query(Tenant).filter(Tenant.is_active.is_(True)).first()
                if not tenant:
                    results.append(_ok("wechat_notify", False, "no tenant"))
                else:
                    order = PaymentOrder(
                        id=str(uuid.uuid4()),
                        tenant_id=str(tenant.id),
                        order_no=order_no_wx,
                        amount=9900,
                        channel="wechat",
                        subject="smoke wx",
                        status="pending",
                    )
                    db.add(order)
                    db.commit()
                    r = client.post(
                        f"{base}/api/v1/payment/notify/wechat",
                        json={
                            "out_trade_no": order_no_wx,
                            "trade_state": "SUCCESS",
                            "amount": {"total": 9900},
                        },
                    )
                    db.refresh(order)
                    body = r.json()
                    results.append(
                        _ok(
                            "wechat_notify",
                            body.get("code") == "SUCCESS" and order.status == "paid",
                            f"code={body.get('code')} status={order.status}",
                        )
                    )
            finally:
                db.close()
        except Exception as exc:
            results.append(_ok("wechat_notify", False, str(exc)))

    passed = sum(1 for x in results if x["ok"])
    return {
        "ok": passed == len(results),
        "passed": passed,
        "total": len(results),
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="商业闭环冒烟")
    parser.add_argument("--base-url", default="http://127.0.0.1:8001")
    parser.add_argument("--admin-user", default="admin")
    parser.add_argument("--admin-pass", default="admin123")
    args = parser.parse_args()

    report = run_smoke(args.base_url, args.admin_user, args.admin_pass)
    logger.info(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
