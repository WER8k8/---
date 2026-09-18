# -*- coding: utf-8 -*-
"""Slice A: PG empty tables by business domain (code+SQL only)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\Administrator\Documents\上线网站开发完成\上线网站.worktrees\agents-install-vscode-cline-deploy-strix")
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy import text

from app.core.database import SessionLocal, engine

# domain keywords → business meaning
DOMAIN_RULES: list[tuple[str, list[str]]] = [
    ("获客主链", ["inquir", "prospect", "lead", "buyer", "acquisition", "ops_card", "outreach", "campaign", "rfq", "opportunity", "quote", "follow", "sales_task", "nps", "suppression"]),
    ("履约交易", ["order", "payment", "invoice", "shipping", "logistics", "wallet", "token", "meter", "billing", "license", "customs", "boq", "hs_code", "exchange"]),
    ("内容SEO", ["content", "seo", "keyword", "eeat", "schema", "serp", "news", "case_stud", "wiki", "llms", "inclusion", "rank", "publish", "media", "video"]),
    ("平台租户", ["tenant", "user", "admin", "role", "permission", "system_config", "platform", "ssl", "domain", "onboarding", "capability", "menu"]),
    ("编排AI", ["ai_", "hermes", "paperclip", "evolution", "ubrain", "skill", "mcp", "orchestr", "pipeline", "task_trace", "agent", "model_"]),
    ("出站渠道", ["egress", "email", "feishu", "im_", "push", "whatsapp", "social", "nurture", "browser", "device", "n8n", "publish_task", "scheduled"]),
    ("合规安全", ["compliance", "gdpr", "security", "alert", "risk", "credential", "ssl", "audit", "operation_log", "super_admin_login"]),
    ("代理分销", ["agent_", "referral", "commission", "finance"]),
    ("国际化", ["international", "geo_", "glossary", "translation", "global"]),
]


def classify(table: str) -> str:
    t = table.lower()
    for domain, keys in DOMAIN_RULES:
        if any(k in t for k in keys):
            return domain
    return "其他"


# Acquisition main-chain tables that matter for 询盘→跟进→成交
MAIN_CHAIN = {
    "inquiries",
    "inquiry_extended",
    "prospect_leads",
    "buyer_prospect_leads",
    "lead_inquiries",
    "opportunities",
    "opportunity_stages",
    "quotes",
    "quote_items",
    "rfqs",
    "orders",
    "order_items",
    "payment_orders",
    "wallet_accounts",
    "wallet_transactions",
    "token_ledger_entries",
    "meter_events",
    "sales_tasks",
    "campaigns",
    "campaign_steps",
    "email_outreachs",
    "outreach_records",
    "shipping_timeline",
    "invoice_applications",
    "acquisition_ops_cards",
}


def main() -> None:
    if engine.dialect.name != "postgresql":
        print("ERROR not postgres", engine.url)
        return
    db = SessionLocal()
    try:
        names = [
            r[0]
            for r in db.execute(
                text(
                    "select table_name from information_schema.tables "
                    "where table_schema='public' and table_type='BASE TABLE' order by table_name"
                )
            ).fetchall()
        ]
        rows = []
        for t in names:
            try:
                n = db.execute(text(f'select count(*) from "{t}"')).scalar()
            except Exception as exc:  # noqa: BLE001
                rows.append({"table": t, "rows": None, "error": str(exc)[:80], "domain": classify(t)})
                continue
            rows.append({"table": t, "rows": n, "error": None, "domain": classify(t)})

        empty = [r for r in rows if r["rows"] == 0]
        nonempty = [r for r in rows if isinstance(r["rows"], int) and r["rows"] > 0]

        by_domain_empty: dict[str, list[str]] = {}
        by_domain_nonempty: dict[str, list[str]] = {}
        for r in empty:
            by_domain_empty.setdefault(r["domain"], []).append(r["table"])
        for r in sorted(nonempty, key=lambda x: -x["rows"]):
            by_domain_nonempty.setdefault(r["domain"], []).append(f"{r['table']}={r['rows']}")

        main_empty = sorted(t for t in MAIN_CHAIN if any(e["table"] == t and e["rows"] == 0 for e in empty))
        main_filled = sorted(
            f"{t}={next(r['rows'] for r in rows if r['table']==t)}"
            for t in MAIN_CHAIN
            if any(r["table"] == t and isinstance(r["rows"], int) and r["rows"] > 0 for r in rows)
        )
        main_missing = sorted(t for t in MAIN_CHAIN if not any(r["table"] == t for r in rows))

        report = {
            "engine": str(engine.url),
            "public_tables": len(names),
            "empty_count": len(empty),
            "nonempty_count": len(nonempty),
            "by_domain_empty_count": {k: len(v) for k, v in sorted(by_domain_empty.items(), key=lambda x: -len(x[1]))},
            "by_domain_empty": {k: sorted(v) for k, v in sorted(by_domain_empty.items())},
            "by_domain_nonempty": by_domain_nonempty,
            "acquisition_main_chain": {
                "definition": sorted(MAIN_CHAIN),
                "filled": main_filled,
                "empty": main_empty,
                "missing_in_pg": main_missing,
                "plain": (
                    f"主链表有数 {len(main_filled)} / 空 {len(main_empty)} / 库中不存在 {len(main_missing)}"
                ),
            },
        }
        out = ROOT / "docs" / "probe_empty_tables_by_domain.json"
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(report["acquisition_main_chain"], ensure_ascii=False, indent=2))
        print("EMPTY_BY_DOMAIN", report["by_domain_empty_count"])
        print("written", out)
    finally:
        db.close()


if __name__ == "__main__":
    main()
