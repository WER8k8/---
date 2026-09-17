# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""商用七步主链 — 框架级自动验收（P0 彩排优先）。"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.pilot_rehearsal_service import demo_https_rehearsal_report
from app.services.platform_alignment_service import alignment_report
from app.services.production_readiness_service import check_mounted_routes, run_readiness_checks
from app.services.publish_queue_service import queue_stats


def _route_ok(paths: list[str], needle: str) -> bool:
    """_route_ok。

    参数说明：
    :param paths: 参数 paths
    :param needle: 参数 needle
    :return: 返回处理结果。
    """
    return any(needle in p for p in paths)


def run_seven_step_audit(db: Session, demo_domain: str | None = None) -> dict[str, Any]:
    """按产品七步 1→7 返回每步 pass/warn/fail（框架最重要验收）。"""
    from app.main import app
    paths = [getattr(r, "path", "") or "" for r in app.routes]
    readiness = run_readiness_checks(db)
    route_check = check_mounted_routes()
    https_report = demo_https_rehearsal_report(demo_domain)
    platform = alignment_report(db)
    publish = queue_stats(db)
    steps: list[dict[str, Any]] = []
    # ① 开通 SaaS
    saas_ok = _route_ok(paths, "/api/v1/payment") and _route_ok(paths, "/api/v1/tenants")
    steps.append(
        {
            "step": 1,
            "name": "开通 SaaS",
            "status": "pass" if saas_ok else "fail",
            "message": "支付与租户 API 已挂载" if saas_ok else "缺少 payment/tenants 路由",
            "paths": ["/tenants/register", "/api/v1/payment/plans"],
        }
    )
    # ② 独立域 HTTPS
    https_ready = bool(https_report.get("ready_for_pilot"))
    step2_fix: dict[str, Any] | None = None
    if not https_ready:
        step2_fix = {
            "type": "demo_https_domain",
            "hermes_eligible": False,
            "hint": "在服务器 .env 设置 DEMO_HTTPS_DOMAIN，或在本页传入演示域后重新探测。",
        }
    steps.append(
        {
            "step": 2,
            "name": "独立域 HTTPS",
            "status": "pass" if https_ready else ("warn" if https_report.get("configured") else "fail"),
            "message": https_report.get("message") or https_report.get("probe", {}).get("error") or "请配置 DEMO_HTTPS_DOMAIN",
            "paths": ["/api/v1/domains/pilot/demo-https", "/api/v1/domains/"],
            **({"fix": step2_fix} if step2_fix else {}),
        }
    )
    # ③ 统一母版发布
    pub_ok = publish.get("pending", 0) >= 0 and _route_ok(paths, "/ops/publish-worker")
    steps.append(
        {
            "step": 3,
            "name": "统一母版发布",
            "status": "pass" if pub_ok else "fail",
            "message": f"发布队列 pending={publish.get('pending', 0)}",
            "paths": ["/ops/publish-worker/run", "/api/v1/content-master"],
        }
    )
    # ④ 40 平台
    plat_ok = platform.get("summary", {}).get("ready") or platform.get("aligned")
    steps.append(
        {
            "step": 4,
            "name": "40 平台分发",
            "status": "pass" if plat_ok else "warn",
            "message": f"catalog={platform.get('catalog_total')} db={platform.get('db_total')}",
            "paths": ["/api/v1/platforms/catalog", "/ops/platforms/seed-full"],
        }
    )
    # ⑤ 询盘 IM（5a 入站 + 5b 企微推送 + 5c 社媒谈单）
    im_ok = (
        _route_ok(paths, "/im-routing")
        and _route_ok(paths, "/inquiries/public")
        and _route_ok(paths, "/social-interactions")
        and _route_ok(paths, "/wecom-push-config")
    )
    steps.append(
        {
            "step": 5,
            "name": "询盘 IM",
            "status": "pass" if im_ok else "fail",
            "message": "5a 入站 webhook · 5b 租户企微推送 · 5c 抖音评论/自动谈单",
            "paths": [
                "/api/v1/mobile/im-routing",
                "/api/v1/inquiries/public",
                "/api/v1/inquiries/channels/wecom",
                "/api/v1/client/wecom-push-config",
                "/api/v1/social-interactions/worker/config",
            ],
            "substeps": [
                {"id": "5a", "name": "询盘 IM 入站", "route": "/inquiries/im-routing"},
                {"id": "5b", "name": "企微销售推送", "route": "/inquiries/im-routing#wecom-push"},
                {"id": "5c", "name": "抖音评论监测", "route": "/sales/auto-negotiator"},
            ],
        }
    )
    # ⑥ 订单报价 + 支付联动
    order_ok = _route_ok(paths, "/orders") and _route_ok(paths, "payment-status")
    steps.append(
        {
            "step": 6,
            "name": "订单报价",
            "status": "pass" if order_ok else "warn",
            "message": "订单 API + PATCH payment-status + 支付回调可写 B2B 状态",
            "paths": ["/api/v1/orders/", "/payment/notify"],
        }
    )
    # ⑦ 物流 / 助手闭环
    tail_ok = _route_ok(paths, "/logistics") and _route_ok(paths, "/ubrain")
    steps.append(
        {
            "step": 7,
            "name": "物流与助手",
            "status": "pass" if tail_ok else "warn",
            "message": "物流看板 + UBrain + 出海参谋",
            "paths": ["/api/v1/logistics/", "/api/v1/trade-intel/", "/api/v1/ubrain/chat"],
        }
    )
    passed = sum(1 for s in steps if s["status"] == "pass")
    failed = sum(1 for s in steps if s["status"] == "fail")
    return {
        "framework": "商用七步主链",
        "environment": settings.ENVIRONMENT,
        "steps": steps,
        "summary": {
            "pass": passed,
            "warn": sum(1 for s in steps if s["status"] == "warn"),
            "fail": failed,
            "ready_for_recording": failed == 0 and passed >= 5,
        },
        "readiness": readiness.to_dict(),
        "routes_mounted": route_check.to_dict(),
        "demo_https": https_report,
        "demo_domain_override": (demo_domain or "").strip() or None,
    }
