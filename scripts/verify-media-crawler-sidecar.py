#!/usr/bin/env python3
"""MediaCrawler Sidecar 接线 + 合规 smoke。"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

_dev_env = BACKEND / "config" / "dev" / ".env"
if _dev_env.is_file():
    for line in _dev_env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        if key.strip() and key.strip() not in os.environ:
            os.environ[key.strip()] = val.strip().strip('"').strip("'")

os.environ.setdefault("SECRET_KEY", "verify-media-" + ("x" * 24))
os.environ.setdefault("JWT_SECRET_KEY", os.environ["SECRET_KEY"])
os.environ.setdefault("ENVIRONMENT", "development")


def main() -> int:
    errors: list[str] = []
    from app.services.crawlers.media_crawler_sidecar import media_crawler_sidecar_status, run_media_spider

    st = media_crawler_sidecar_status()
    print("status:", json.dumps(st, ensure_ascii=False, indent=2))

    reg = BACKEND / "app" / "services" / "crawlers" / "ecommerce_crawlers_registry.py"
    text = reg.read_text(encoding="utf-8")
    for sid in ("media_facebook", "media_instagram", "media_youtube", "media_europages"):
        if f'"{sid}"' not in text:
            errors.append(f"registry missing {sid}")

    if st.get("configured") and st.get("healthy") is not True:
        errors.append(f"unhealthy: {st.get('detail')}")
    elif st.get("configured"):
        os.environ.setdefault("ECOMMERCE_SOCIAL_SPIDERS_ENABLED", "1")
        os.environ.setdefault("ECOMMERCE_SPIDER_ENABLE_MEDIA_FACEBOOK", "1")
        out = run_media_spider(
            "media_facebook",
            params={"keyword": "insulation distributor"},
            purpose="dev wiring smoke — public page research only",
        )
        if out.get("ok") and (out.get("items") or out.get("evidence_url")):
            print(f"smoke: ok items={len(out.get('items') or [])} probe={out.get('probe_mode')}")
        else:
            errors.append(f"smoke failed: {out.get('error_code')}")

    if errors:
        print("FAIL")
        for e in errors:
            print(" -", e)
        return 1
    print("OK media-crawler sidecar")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
