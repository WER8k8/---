#!/usr/bin/env python3
"""XF-C1/C2 询盘语言桥接线验证。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

os.environ.setdefault("SECRET_KEY", "verify-bridge-" + ("x" * 24))
os.environ.setdefault("JWT_SECRET_KEY", os.environ["SECRET_KEY"])
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("DB_TYPE", "sqlite")


def main() -> int:
    errors: list[str] = []

    try:
        from app.services.cross_border.inquiry_bridge_service import (
            draft_reply_en,
            inquiry_bridge_status,
            summarize_inquiry_zh,
        )
        from app.models.inquiry import Inquiry
        from app.models.tenant import Tenant

        assert summarize_inquiry_zh and draft_reply_en
        assert Inquiry.__tablename__ == "inquiries"
        assert Tenant.__tablename__ == "tenants"
        st = inquiry_bridge_status()
        if "mode" not in st or "configured" not in st:
            errors.append("inquiry_bridge_status missing mode/configured")
    except Exception as exc:
        errors.append(f"import: {exc}")

    routes = BACKEND / "app" / "api" / "v1" / "routes" / "cross_border.py"
    text = routes.read_text(encoding="utf-8")
    for needle in (
        "bridge-status",
        "imap-poll",
        "bridge-summary",
        "reply-draft",
        "summarize_inquiry_zh",
        "draft_reply_en",
        "inquiry_bridge_status",
        "poll_and_ingest_imap_inquiries",
    ):
        if needle not in text:
            errors.append(f"missing route/symbol: {needle}")

    ui = ROOT / "frontend" / "admin" / "src" / "views" / "client" / "queues" / "inquiries.vue"
    ui_text = ui.read_text(encoding="utf-8")
    if "inquiryBridgeSummary" not in ui_text:
        errors.append("inquiries.vue missing language bridge UI")
    if "inquiryBridgeStatus" not in ui_text:
        errors.append("inquiries.vue missing bridge status fetch")
    if "inquiryImapPoll" not in ui_text:
        errors.append("inquiries.vue missing IMAP poll UI")
    if "回复已发送（邮件功能集成中）" in ui_text:
        errors.append("inquiries.vue still has fake send success copy")

    api = ROOT / "frontend" / "admin" / "src" / "api" / "cross-border.ts"
    if "inquiryBridgeStatus" not in api.read_text(encoding="utf-8"):
        errors.append("cross-border.ts missing inquiryBridgeStatus")
    if "inquiryImapPoll" not in api.read_text(encoding="utf-8"):
        errors.append("cross-border.ts missing inquiryImapPoll")

    seed = ROOT / "scripts" / "seed_dev_tenant_demo.py"
    if "buyer.demo@example.com" not in seed.read_text(encoding="utf-8"):
        errors.append("seed_dev_tenant_demo missing English demo inquiry")

    if errors:
        print("FAIL verify-inquiry-bridge")
        for e in errors:
            print(" -", e)
        return 1
    print("OK inquiry language bridge XF-C1/C2 wiring")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())