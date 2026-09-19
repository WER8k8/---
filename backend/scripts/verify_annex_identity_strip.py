# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""P0 附属剥身份静态门禁（仓库相对路径，可移植）."""
from __future__ import annotations

from pathlib import Path

# scripts/ → backend → worktree → 上线网站.worktrees → workspace
WT = Path(__file__).resolve().parents[2]
WS = WT.parent.parent
GJ = WS / "_external" / "goodjob-crm" / "backend" / "src" / "server.ts"
TA_CORE = WS / "_external" / "trade-ai-agent" / "backend" / "app" / "core" / "annex_identity.py"
TA_AUTH = WS / "_external" / "trade-ai-agent" / "backend" / "app" / "api" / "v1" / "auth.py"
TA_MAIN = WS / "_external" / "trade-ai-agent" / "backend" / "app" / "main.py"
TA_ADMIN = WS / "_external" / "trade-ai-agent" / "backend" / "app" / "api" / "v1" / "admin.py"
UM = WT / "backend" / "app" / "services" / "hermes" / "annex_work_mode.py"

FAILS: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
    if not ok:
        FAILS.append(name)


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore") if p.is_file() else ""


def main() -> int:
    print("【P0 附属剥身份 · 静态门禁】")
    gj = read(GJ)
    check("GoodJob strip 中间件存在", "P0-ANNEX-STRIP" in gj and "annexIdentityStrip" in gj)
    check("GoodJob 管理台 410", "annex_console_retired" in gj)
    check("GoodJob 登录退役 410", "annex_login_retired" in gj)
    check("GoodJob 保留 annex-ticket", "/api/auth/annex-ticket" in gj)
    check("GoodJob 保留 uj-bridge", "/api/uj-bridge" in gj)
    check("GoodJob platform 默认挡", "/api/platform/" in gj)

    ta = read(TA_CORE)
    check("TradeAI annex_identity 模块", "ensure_annex_product_identity_disabled" in ta)
    check("TradeAI 登录 410", "annex_login_retired" in ta)
    check("TradeAI 管理台 410", "annex_console_retired" in ta)

    auth = read(TA_AUTH)
    check("TradeAI auth 调用闸门", "ensure_annex_product_identity_disabled" in auth)
    check("TradeAI login 被守卫", "login_json" in auth and "ensure_annex_product_identity_disabled" in auth)

    main_py = read(TA_MAIN)
    check("TradeAI HTTP 中间件", "annex_identity_middleware" in main_py)
    check("TradeAI 不默认种超管", "Skip TradeAI default admin seed" in main_py)

    admin = read(TA_ADMIN)
    check("TradeAI admin 引用闸门", "ensure_annex_product_identity_disabled" in admin)

    check("UJ annex_work_mode 契约文件", UM.is_file() and "GOLDEN_PATH_A" in read(UM))

    print("-" * 50)
    if FAILS:
        print(f"结果: 失败 {len(FAILS)}: {FAILS}")
        return 1
    print("结果: 全部通过（静态剥身份契约在位）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
