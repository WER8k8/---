"""套餐功能矩阵 — 与 docs/marketing/plan-copy-deck.md §四 对齐（BFF 只读出口）"""

from __future__ import annotations

PLAN_FEATURES: dict[str, dict[str, object]] = {
    "trial": {
        "name": "体验版",
        "features": ["domain_bind", "publish_limited", "inquiry_limited", "geo_submit_limited"],
    },
    "starter": {
        "name": "启航版",
        "features": ["domain_bind", "publish", "inquiry", "geo_submit_limited"],
    },
    "pro": {
        "name": "专业版",
        "features": [
            "domain_bind",
            "publish",
            "inquiry",
            "im",
            "seo_matrix",
            "geo_engine",
            "geo_content_matrix",
            "geo_submit_pack",
            "media_factory",
            "video_matrix",
        ],
    },
    "enterprise": {
        "name": "企业版",
        "features": [
            "domain_bind",
            "publish",
            "inquiry",
            "im",
            "seo_matrix",
            "geo_engine",
            "geo_content_matrix",
            "geo_submit_pack",
            "geo_monitor",
            "media_factory",
            "video_matrix",
            "white_label",
            "audit_log",
        ],
    },
}
