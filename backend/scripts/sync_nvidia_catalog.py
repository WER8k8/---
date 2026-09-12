"""从 NVIDIA /v1/models 同步并生成分类目录 JSON（可入库/送检）。"""

from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / "config" / "dev" / ".env", override=True)
os.environ.setdefault("JWT_SECRET_KEY", "sync-" + "x" * 28)

from app.services.nvidia_catalog_service import build_nvidia_catalog

OUT = ROOT / "app" / "data" / "nvidia_nim_catalog.json"


def main() -> int:
    catalog = build_nvidia_catalog()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Wrote {OUT} ({catalog['total_models']} models, {len(catalog['categories'])} categories)", OUT, catalog['total_models'], len(catalog['categories']))
    for cat in catalog["categories"]:
        logger.info("  - {cat['label']}: {cat['count']}", cat['label'], cat['count'])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
