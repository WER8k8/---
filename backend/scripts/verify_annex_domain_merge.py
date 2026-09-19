# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Compose annex-domain-merge 验收脚本：黄金路径 API 契约 + 门禁串联."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

FAILS: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
    if not ok:
        FAILS.append(name)


def main() -> int:
    print("【annex-domain-merge 验收】")
    from app.api.v1.routes import orchestration as orch
    from app.services.hermes import planner_service
    from app.services.hermes.annex_work_mode import work_mode_report

    paths = [getattr(r, "path", "") for r in orch.router.routes]
    check("GP-A 路由", any("golden-path/fulfillment" in p for p in paths))
    check("GP-B 路由", any("golden-path/outreach" in p for p in paths))
    check("work-mode 路由", any("golden-path/work-mode" in p for p in paths))
    check("TradeAI 技能在白名单", "trade_ai.social_scraper" in planner_service.FALLBACK_CAPABILITIES)
    report = work_mode_report()
    check("DSH 非必经", report["dsh_required_every_task"] is False)
    check("功能域无特权", all(d["privileged"] is False for d in report["seamless_body"]["function_domains"]))
    check("S7 在册", any(s["id"] == "S7" for s in report["seamless_body"]["standards"]))
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    wt_root = os.path.dirname(backend_dir)
    audit = os.path.join(wt_root, "docs", "annex-protocol-audit-2026-09-19.md")
    check("协议审计文档", os.path.isfile(audit), audit)
    print("-" * 50)
    if FAILS:
        print(f"结果: 失败 {FAILS}")
        return 1
    print("结果: 全部通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
