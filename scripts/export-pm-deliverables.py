#!/usr/bin/env python3
"""PM-01～07 交付物草稿（从代码/catalog 导出，待 PM 签字）。"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "pm-deliverables"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    sys_path = ROOT / "backend"
    import sys

    sys.path.insert(0, str(sys_path))
    from app.db.session import SessionLocal
    from app.services.platform_catalog import PLATFORMS_CN, PLATFORMS_GLOBAL, catalog_summary

    pilot = [p[0] for p in PLATFORMS_CN[:8]] + [p[0] for p in PLATFORMS_GLOBAL[:4]]
    (OUT / "PM-01-pilot-platforms.json").write_text(
        json.dumps({"pilot_platforms": pilot, "note": "试点名单草稿"}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    db = SessionLocal()
    try:
        summary = catalog_summary(db)
    finally:
        db.close()
    (OUT / "PM-02-40-platforms.json").write_text(
        json.dumps(
            {
                "summary": summary,
                "cn": [{"name": p[0], "type": p[1]} for p in PLATFORMS_CN],
                "global": [{"name": p[0], "type": p[1]} for p in PLATFORMS_GLOBAL],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (OUT / "PM-03-packages.json").write_text(
        json.dumps(
            {
                "plans": [
                    {"code": "starter", "max_sites": 1, "max_products": 50},
                    {"code": "growth", "max_sites": 3, "max_products": 500},
                    {"code": "enterprise", "max_sites": 10, "max_products": 5000},
                ],
                "note": "与 TenantPlan 对齐，PM 可调价",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (OUT / "PM-04-https-demo.md").write_text(
        "# HTTPS 演示域（PM-04）\n\n"
        "- 开发：`SSL_PROVIDER=dev_local` 自动签发 `.test.local`\n"
        "- 生产：配置 `SSL_PROVIDER=http` + `ACME_WEBHOOK_URL` 或 Cloudflare\n"
        "- 验收：`GET /api/v1/ssl-certificates`\n",
        encoding="utf-8",
    )
    (OUT / "PM-05-matrix.md").write_text(
        "# 出海参谋矩阵（PM-05）\n\n"
        "主链：优丁助手 → 商业飞轮 OS → 发布台 → 流量看板 → 询盘\n",
        encoding="utf-8",
    )
    (OUT / "PM-06-four-shells.md").write_text(
        "# 四壳菜单（PM-06）\n\n"
        "见 `docs/出海计/主链菜单-定稿.md`、`frontend/admin/src/layout/index.vue` labPaths\n",
        encoding="utf-8",
    )
    (OUT / "PM-07-legal.md").write_text(
        "# 法务免责（PM-07）\n\n"
        "飞轮/AI 输出页须展示 `disclaimer` 字段；Accio 技能页标注 partial/MVP。\n",
        encoding="utf-8",
    )
    print(f"Wrote PM deliverables to {OUT}")


if __name__ == "__main__":
    main()
