#!/usr/bin/env python3
"""W1–W3 跨境语言桥 — 路由与模块 smoke（无需 AI 密钥）。"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))


def main() -> int:
    errors: list[str] = []

    try:
        from app.api.v1.routes.cross_border import router

        paths = {getattr(r, "path", "") for r in router.routes}
        required = {
            "/cross-border/inquiries/{inquiry_id}/bridge-summary",
            "/cross-border/inquiries/{inquiry_id}/reply-draft",
            "/cross-border/export-quote",
            "/cross-border/video-dub/upload",
            "/cross-border/video-dub/jobs",
            "/cross-border/video-dub/transcribe",
            "/cross-border/video-dub/tts-status",
            "/cross-border/product-candidates",
            "/cross-border/product-candidates/import",
            "/cross-border/seo-keywords/preview",
            "/cross-border/seo-keywords/seed",
        }
        missing = required - paths
        if missing:
            errors.append(f"missing routes: {sorted(missing)}")
    except Exception as exc:
        errors.append(f"import cross_border router: {exc}")

    try:
        from app.services.cross_border.export_quote_service import build_export_quote_onepager
        from app.services.cross_border.glossary_helper import build_glossary_prompt_block
        from app.services.cross_border.seo_belt_service import preview_belt_keywords
        from app.services.cross_border.video_dub_service import _format_srt

        from app.services.cross_border.industry_belt_product_import_service import list_product_candidates
        from app.services.cross_border.tts_service import tts_status

        pack = list_product_candidates(page_size=5)
        if pack.get("total", 0) < 1:
            errors.append("product candidates empty")
        srt = _format_srt([{"start": "00:00:00,000", "end": "00:00:03,000", "text_en": "Hello"}])
        if "Hello" not in srt:
            errors.append("srt formatter failed")
    except Exception as exc:
        errors.append(f"import services: {exc}")

    try:
        from app.api.v1.routes import router as v1

        route_paths = []
        for r in v1.routes:
            p = getattr(r, "path", "") or ""
            if "cross-border" in p:
                route_paths.append(p)
        if not route_paths:
            errors.append("cross-border not mounted on v1 router")
    except Exception as exc:
        errors.append(f"v1 router check: {exc}")

    if errors:
        print("FAIL")
        for e in errors:
            print(" -", e)
        return 1

    print("OK cross-border W1-W3 smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
