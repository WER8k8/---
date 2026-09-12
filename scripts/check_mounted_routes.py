#!/usr/bin/env python3
"""CI 门禁：关键 API 前缀必须已挂载到 FastAPI app。"""
from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND))

# 仅用于路由枚举，不要求真实生产密钥
os.environ.setdefault(
    "JWT_SECRET_KEY",
    "ci-route-check-only-" + ("x" * 32),
)

from app.main import app  # noqa: E402

REQUIRED_PREFIXES = [
    "/api/v1/referral",
    "/api/v1/super-admin",
    # 高级 SEO：至少存在审计或 batch 相关路径
    "/api/v1/seo/run-audit",
    "/api/v1/seo/site-audit",
    "/api/v1/seo/content-optimizer",
    "/api/v1/logistics/track",
    "/api/v1/hub/pages",
    "/api/v1/finance/commissions",
    "/api/v1/finance/cost-by-category",
    "/api/v1/token/balance",
    "/api/v1/inquiries/unified",
    "/api/v1/ops/tenants/enforce-expiry",
    "/api/v1/ops/jobs/run-all",
    "/api/v1/ops/publish-worker/run",
    "/api/v1/finance/reconciliation-template.csv",
    "/api/v1/ops/readiness",
    "/api/v1/ops/backup/status",
    "/api/v1/ops/alerts/readiness-notify",
    "/api/v1/auth/oauth/bindings",
    "/api/v1/finance/summary",
    "/api/v1/finance/export.csv",
    "/api/v1/hub/search-console/checklist",
    "/api/v1/inquiries/portal",
    "/api/v1/domains/resolve",
    "/api/v1/egress/overview",
    "/api/v1/egress/endpoints",
    "/api/v1/egress/my",
    "/api/v1/integrations/status",
    "/api/v1/payment/addon/egress-ip",
    "/api/v1/platforms/catalog",
    "/api/v1/content-masters",
    "/api/v1/analytics/event",
    "/api/v1/analytics/site-context",
    "/api/v1/analytics/traffic-board",
]

# 满足其一即可（SEO 挂载路径因合并策略可能不同）
SEO_ANY_OF = [
    "/api/v1/seo/run-audit",
    "/api/v1/seo/site-audit",
    "/api/v1/seo/content-optimizer",
    "/api/v1/seo/keyword-ranking",
]


def all_paths() -> list[str]:
    out: list[str] = []
    for r in app.routes:
        p = getattr(r, "path", "") or ""
        if p:
            out.append(p)
    return out


def main() -> int:
    paths = all_paths()
    missing: list[str] = []

    for prefix in REQUIRED_PREFIXES:
        if prefix in SEO_ANY_OF:
            continue
        if not any(p.startswith(prefix) or p == prefix.rstrip("/") for p in paths):
            missing.append(prefix)

    if not any(any(p.startswith(s) for p in paths) for s in SEO_ANY_OF):
        missing.append("SEO(advanced): one of " + ", ".join(SEO_ANY_OF))

    if missing:
        print("FAIL: missing mounted routes:")
        for m in missing:
            print(f"  - {m}")
        print(f"\nTotal /api routes: {len([p for p in paths if p.startswith('/api')])}")
        return 1

    print("OK: all required route prefixes are mounted.")
    print(f"Total /api routes: {len([p for p in paths if p.startswith('/api')])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
