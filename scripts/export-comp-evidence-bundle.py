#!/usr/bin/env python3

"""COMP-04 · 证据包一键导出（git log + manifest + PRD 索引）"""



from __future__ import annotations



import json

import subprocess

from datetime import datetime, timezone

from pathlib import Path



ROOT = Path(__file__).resolve().parents[1]

OUT = ROOT / "docs" / "compliance" / "comp-evidence-bundle.json"

GIT_LOG = ROOT / "docs" / "compliance" / "git-log-export.txt"



PRD_LINKS = [

    "docs/pm-master-schedule-kpi-20260601.md",

    "docs/思维导图-优丁SaaS改造全员对齐.md",

    "docs/ecc-saas-enterprise-value-framework.md",

    "docs/送检演示脚本-v2-鉴定面.md",

    "docs/cert-screenshots-checklist.md",

]





def git_log(max_count: int = 200) -> str:

    try:

        r = subprocess.run(

            ["git", "log", f"--max-count={max_count}", "--oneline", "--decorate"],

            cwd=ROOT,

            capture_output=True,

            text=True,

            encoding="utf-8",

            errors="replace",

            check=False,

        )

        return r.stdout or r.stderr or "(no git log)"

    except Exception as exc:

        return f"(git unavailable: {exc})"





def main() -> None:

    log_text = git_log()

    GIT_LOG.write_text(log_text, encoding="utf-8")



    cert_dir = ROOT / "docs" / "cert-screenshots"

    pngs = sorted(p.name for p in cert_dir.glob("*.png")) if cert_dir.is_dir() else []



    payload = {

        "generated_at": datetime.now(timezone.utc).isoformat(),

        "open_source_notices": "OPEN-SOURCE-NOTICES.md",

        "soft_copyright_catalog": "docs/compliance/soft-copyright-code-catalog-v1.md",

        "rz_60_pages": "docs/compliance/rz-60-pages/",

        "git_log_file": str(GIT_LOG.relative_to(ROOT)).replace("\\", "/"),

        "git_log_lines": len(log_text.splitlines()),

        "prd_links": [p for p in PRD_LINKS if (ROOT / p).exists()],

        "cert_screenshots": pngs,

        "forbidden_list": "docs/compliance/ip-02-forbidden-list.md",

    }

    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote {OUT}")

    print(f"Wrote {GIT_LOG} ({payload['git_log_lines']} lines)")





if __name__ == "__main__":

    main()

