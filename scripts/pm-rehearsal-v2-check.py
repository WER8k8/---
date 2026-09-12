#!/usr/bin/env python3
"""PM-03 · 送检脚本 v2 彩排自动检查（PNG + manifest + 路由清单）"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKLIST = ROOT / "docs" / "cert-screenshots-checklist.md"
MANIFEST = ROOT / "docs" / "cert-screenshots" / "manifest.json"
SHOT_DIR = ROOT / "docs" / "cert-screenshots"

# 鉴定面 12 步 · 对齐送检演示脚本 v2
STEPS = [
    ("1.1", "超管登录", "/login", "cert-01-login.png"),
    ("1.2", "租户总览", "/admin/tenants", "cert-02-tenants.png"),
    ("1.3", "层级管理", "/admin/hierarchy", "cert-03-hierarchy.png"),
    ("1.4", "数据中心", "/admin/aggregation", "cert-04-aggregation.png"),
    ("1.5", "系统健康", "/system-health/dashboard", "cert-05-health.png"),
    ("1.6", "商业发票", "/admin/finance", "cert-06-finance.png"),
    ("2.1", "产品管理", "/products", "cert-07-products.png"),
    ("2.2", "分类", "/products/categories", "cert-08-categories.png"),
    ("2.3", "国际询盘", "/international/inquiries", "cert-09-inquiries.png"),
    ("2.4", "SEO 发布", "/seo-matrix/publish", "cert-10-seo.png"),
    ("2.5", "AI 内容", "/admin/ai-center/content", "cert-11-ai-content.png"),
    ("2.6", "贸易情报", "/admin/ai-engine/trade-intel", "cert-12-trade-intel.png"),
]

BONUS = [
    ("3.1", "租户 Dashboard", "/client/dashboard", "ux-07-client-dashboard.png"),
    ("3.2", "代理 KPI", "/agent/performance", "ux-07-agent-performance.png"),
]


def main() -> int:
    fails = 0
    print("=== PM-03 Rehearsal Pre-check (30min script v2) ===\n")
    print("Timing guide: 10min 超管 · 10min 业务链 · 5min 租户+代理 · 5min Q&A\n")

    for step, title, route, png in STEPS + BONUS:
        ok = (SHOT_DIR / png).is_file()
        tag = "PASS" if ok else "FAIL"
        print(f"[{tag}] {step} {title} | {route} | {png}")
        if not ok:
            fails += 1

    if MANIFEST.exists():
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        mf_ok = data.get("fail", 1) == 0
        print(f"\n[{'PASS' if mf_ok else 'FAIL'}] manifest fail={data.get('fail')}")
        if not mf_ok:
            fails += 1
    else:
        print("\n[FAIL] manifest missing")
        fails += 1

    out = ROOT / "docs" / "pm-rehearsal-v2-check-latest.json"
    out.write_text(
        json.dumps(
            {
                "steps_total": len(STEPS) + len(BONUS),
                "fail_count": fails,
                "ready_for_rehearsal": fails == 0,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nWrote {out}")
    if fails:
        print(f"PM-03 pre-check: {fails} FAILED")
        return 1
    print("PM-03 pre-check: READY for live rehearsal")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
